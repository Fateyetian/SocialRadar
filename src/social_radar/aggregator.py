"""Result normalization and aggregation across platforms."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SearchResult:
    """Unified search result across all platforms."""

    platform: str          # "xiaohongshu" | "zhihu"
    platform_name: str     # "小红书" | "知乎"
    title: str
    url: str
    summary: str = ""
    author: str = ""
    likes: int = 0
    comments: int = 0
    collect_count: int = 0
    published_at: str = ""
    raw: dict = field(default_factory=dict)


def _format_time(value) -> str:
    """Convert Unix timestamp (seconds/milliseconds) or ISO string to readable date."""
    if not value:
        return ""
    try:
        if isinstance(value, (int, float)):
            ts = value if value < 1e12 else value / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        if isinstance(value, str):
            # Try Unix timestamp string
            try:
                ts = float(value)
                ts = ts if ts < 1e12 else ts / 1000.0
                return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            except ValueError:
                pass
            # Try ISO format
            for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(value.replace("Z", "+0000"), fmt.replace("Z", "+0000")).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return value[:10] if len(value) >= 10 else value
    except Exception:
        return str(value)[:10] if len(str(value)) >= 10 else str(value)


def normalize_xiaohongshu(raw: dict, platform_cfg) -> list[SearchResult]:
    """Parse xiaohongshu search response into results.

    Actual API response path: data.data.data.items[] → item.note.{title,desc,user,...}
    """
    results = []
    try:
        items = raw.get("data", {}).get("data", {}).get("items", [])
        for item in items:
            note = item.get("note", item)
            note_id = note.get("id", "") or item.get("id", "")
            title = note.get("title", "") or note.get("display_title", "")
            desc = note.get("desc", "")
            user = note.get("user", {})
            author_name = user.get("nickname", "") or user.get("nick_name", "")
            interact = note.get("interact_info", {})
            results.append(
                SearchResult(
                    platform="xiaohongshu",
                    platform_name="小红书",
                    title=title or desc[:60],
                    url=platform_cfg.note_link_template.format(note_id=note_id) if note_id else "",
                    summary=desc,
                    author=author_name,
                    likes=int(interact.get("liked_count", 0)),
                    comments=int(note.get("comments_count", 0)),
                    collect_count=int(interact.get("collected_count", 0)),
                    published_at=_format_time(note.get("time") or note.get("timestamp") or ""),
                    raw=note,
                )
            )
    except Exception:
        pass
    return results


def normalize_zhihu(raw: dict, platform_cfg) -> list[SearchResult]:
    """Parse zhihu article search response into results.

    Actual API response path: data.data[] → item.object.{title,excerpt,url,voteup_count,...}
    """
    results = []
    try:
        items = raw.get("data", {}).get("data", [])
        for item in items:
            obj = item.get("object", item)
            obj_type = item.get("type", "")

            title = obj.get("title", "")
            excerpt = obj.get("excerpt", "") or obj.get("content", "") or ""
            if isinstance(excerpt, str):
                excerpt = excerpt[:200]
            url = obj.get("url", "")
            author = obj.get("author", {})
            author_name = author.get("name", "") if isinstance(author, dict) else ""
            vote_count = int(obj.get("voteup_count", 0))
            comment_count = int(obj.get("comment_count", 0))
            qid = ""
            question = obj.get("question", {})
            if isinstance(question, dict):
                qid = str(question.get("id", ""))
            aid = str(obj.get("id", ""))

            if not title and not excerpt:
                continue

            published_at = _format_time(
                obj.get("created_time") or obj.get("created") or
                obj.get("updated_time") or item.get("created_time") or ""
            )
            results.append(
                SearchResult(
                    platform="zhihu",
                    platform_name="知乎",
                    title=title or excerpt[:60],
                    url=url or platform_cfg.answer_link_template.format(question_id=qid, answer_id=aid),
                    summary=excerpt,
                    author=author_name,
                    likes=vote_count,
                    comments=comment_count,
                    published_at=published_at,
                    raw=obj,
                )
            )
    except Exception:
        pass
    return results


def aggregate(all_results: list[SearchResult], sort_by: str = "default") -> list[SearchResult]:
    """Deduplicate and sort results."""
    seen = set()
    unique = []
    for r in all_results:
        key = (r.title[:30], r.url[:50])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    if sort_by == "likes":
        unique.sort(key=lambda x: x.likes, reverse=True)
    return unique
