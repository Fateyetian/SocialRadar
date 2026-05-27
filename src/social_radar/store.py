"""SQLite database layer — caching, bookmarks, tags, annotations."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta

from .config import DB_PATH, CACHE_TTL_QUERY, CACHE_TTL_CONTENT, ensure_data_dir

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS query_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT NOT NULL UNIQUE,
    query_text TEXT NOT NULL,
    platforms TEXT NOT NULL,
    results_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_query_hash ON query_cache(query_hash);

CREATE TABLE IF NOT EXISTS content_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    content_id TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    UNIQUE(platform, content_id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    platform TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    author TEXT DEFAULT '',
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#4f46e5'
);

CREATE TABLE IF NOT EXISTS bookmark_tags (
    bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, tag_id)
);

CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    platforms TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    searched_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, db_path: str | None = None):
        ensure_data_dir()
        self.db_path = str(db_path or DB_PATH)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._init_schema()
        return self._conn

    def _init_schema(self):
        self.conn.executescript(_SCHEMA)
        cur = self.conn.execute("SELECT version FROM schema_version")
        if cur.fetchone() is None:
            self.conn.execute("INSERT INTO schema_version (version) VALUES (1)")
        self.conn.commit()

    # ── Query Cache ──────────────────────────────────────────

    @staticmethod
    def _query_hash(query: str, platforms: str) -> str:
        return hashlib.sha256(f"{query}|{platforms}".encode()).hexdigest()

    def get_cached_query(self, query: str, platforms: str) -> dict | None:
        h = self._query_hash(query, platforms)
        row = self.conn.execute(
            "SELECT results_json, expires_at FROM query_cache WHERE query_hash=?",
            (h,),
        ).fetchone()
        if row and row["expires_at"] > _now():
            return json.loads(row["results_json"])
        return None

    def set_cached_query(self, query: str, platforms: str, results: list[dict]):
        h = self._query_hash(query, platforms)
        ttl = CACHE_TTL_QUERY
        self.conn.execute(
            """INSERT OR REPLACE INTO query_cache
               (query_hash, query_text, platforms, results_json, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (h, query, platforms, json.dumps(results, ensure_ascii=False),
             _now(), _later(ttl)),
        )
        self.conn.commit()

    def evict_expired_queries(self) -> int:
        cur = self.conn.execute("DELETE FROM query_cache WHERE expires_at < ?", (_now(),))
        self.conn.commit()
        return cur.rowcount

    # ── Content Cache ────────────────────────────────────────

    def get_cached_content(self, platform: str, content_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT detail_json, expires_at FROM content_cache WHERE platform=? AND content_id=?",
            (platform, content_id),
        ).fetchone()
        if row and row["expires_at"] > _now():
            return json.loads(row["detail_json"])
        return None

    def set_cached_content(self, platform: str, content_id: str, detail: dict):
        self.conn.execute(
            """INSERT OR REPLACE INTO content_cache
               (platform, content_id, detail_json, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (platform, content_id, json.dumps(detail, ensure_ascii=False),
             _now(), _later(CACHE_TTL_CONTENT)),
        )
        self.conn.commit()

    # ── Bookmarks ────────────────────────────────────────────

    def add_bookmark(self, result: dict) -> int:
        cur = self.conn.execute(
            """INSERT OR REPLACE INTO bookmarks
               (url, platform, title, summary, author, result_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (result["url"], result["platform"], result["title"],
             result.get("summary", ""), result.get("author", ""),
             json.dumps(result, ensure_ascii=False), _now()),
        )
        self.conn.commit()
        return cur.lastrowid

    def remove_bookmark(self, bookmark_id: int):
        self.conn.execute("DELETE FROM bookmarks WHERE id=?", (bookmark_id,))
        self.conn.commit()

    def get_bookmarks(self, tag: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        if tag:
            rows = self.conn.execute(
                """SELECT DISTINCT b.* FROM bookmarks b
                   JOIN bookmark_tags bt ON b.id = bt.bookmark_id
                   JOIN tags t ON bt.tag_id = t.id
                   WHERE t.name = ?
                   ORDER BY b.created_at DESC LIMIT ? OFFSET ?""",
                (tag, page_size, (page - 1) * page_size),
            ).fetchall()
            total = self.conn.execute(
                """SELECT COUNT(DISTINCT b.id) FROM bookmarks b
                   JOIN bookmark_tags bt ON b.id = bt.bookmark_id
                   JOIN tags t ON bt.tag_id = t.id
                   WHERE t.name = ?""",
                (tag,),
            ).fetchone()[0]
        else:
            rows = self.conn.execute(
                "SELECT * FROM bookmarks ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (page_size, (page - 1) * page_size),
            ).fetchall()
            total = self.conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
        return [_row_to_dict(r) for r in rows], total

    def is_bookmarked(self, url: str) -> bool:
        row = self.conn.execute("SELECT id FROM bookmarks WHERE url=?", (url,)).fetchone()
        return row is not None

    def get_bookmark_tags(self, bookmark_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT t.* FROM tags t JOIN bookmark_tags bt ON t.id = bt.tag_id WHERE bt.bookmark_id=?",
            (bookmark_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    # ── Tags ─────────────────────────────────────────────────

    def add_tag(self, name: str, color: str = "#4f46e5") -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)", (name, color),
        )
        self.conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = self.conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
        return row["id"]

    def get_all_tags(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [_row_to_dict(r) for r in rows]

    def delete_tag(self, tag_id: int):
        self.conn.execute("DELETE FROM tags WHERE id=?", (tag_id,))
        self.conn.commit()

    def assign_tag(self, bookmark_id: int, tag_id: int):
        self.conn.execute(
            "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id) VALUES (?, ?)",
            (bookmark_id, tag_id),
        )
        self.conn.commit()

    def remove_tag(self, bookmark_id: int, tag_id: int):
        self.conn.execute(
            "DELETE FROM bookmark_tags WHERE bookmark_id=? AND tag_id=?",
            (bookmark_id, tag_id),
        )
        self.conn.commit()

    # ── Annotations ──────────────────────────────────────────

    def add_annotation(self, bookmark_id: int, note_text: str) -> int:
        now = _now()
        cur = self.conn.execute(
            "INSERT INTO annotations (bookmark_id, note_text, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (bookmark_id, note_text, now, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_annotation(self, annotation_id: int, note_text: str):
        self.conn.execute(
            "UPDATE annotations SET note_text=?, updated_at=? WHERE id=?",
            (note_text, _now(), annotation_id),
        )
        self.conn.commit()

    def delete_annotation(self, annotation_id: int):
        self.conn.execute("DELETE FROM annotations WHERE id=?", (annotation_id,))
        self.conn.commit()

    def get_annotations(self, bookmark_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM annotations WHERE bookmark_id=? ORDER BY updated_at DESC",
            (bookmark_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    # ── Search History ───────────────────────────────────────

    def add_search_history(self, query: str, platforms: str, count: int):
        self.conn.execute(
            "INSERT INTO search_history (query_text, platforms, result_count, searched_at) VALUES (?, ?, ?, ?)",
            (query, platforms, count, _now()),
        )
        self.conn.commit()

    def get_search_history(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ?", (limit,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    # ── Maintenance ──────────────────────────────────────────

    def evict_all_expired(self) -> tuple[int, int]:
        q = self.conn.execute("DELETE FROM query_cache WHERE expires_at < ?", (_now(),))
        c = self.conn.execute("DELETE FROM content_cache WHERE expires_at < ?", (_now(),))
        self.conn.commit()
        return q.rowcount, c.rowcount

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _later(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)
