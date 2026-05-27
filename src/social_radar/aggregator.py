"""Result normalization and aggregation across platforms."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime


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


def normalize_xiaohongshu(raw: dict, platform_cfg) -> list[SearchResult]:
    """Parse xiaohongshu search response into results."""
    results = []
    try:
        result_data = raw.get("result", raw)
        # Try different response formats
        if isinstance(result_data, str):
            result_data = json.loads(result_data)

        items = (
            result_data.get("data", {}).get("items", [])
            or result_data.get("items", [])
            or result_data.get("notes", [])
            or []
        )
        for item in items:
            note_card = item.get("note_card") or item
            note_id = note_card.get("note_id") or item.get("id", "")
            title = note_card.get("display_title", "") or note_card.get("title", "")
            desc = note_card.get("desc", "") or note_card.get("description", "")
            author_info = note_card.get("user", {}) or note_card.get("author", {})
            author_name = author_info.get("nickname", "") or author_info.get("nick_name", "")
            interact = note_card.get("interact_info", {})
            results.append(
                SearchResult(
                    platform="xiaohongshu",
                    platform_name="小红书",
                    title=title or desc[:60],
                    url=platform_cfg.note_link_template.format(note_id=note_id) if note_id else "",
                    summary=desc,
                    author=author_name,
                    likes=interact.get("liked_count", 0) or note_card.get("likes", 0),
                    comments=interact.get("comment_count", 0),
                    collect_count=interact.get("collected_count", 0),
                    published_at=note_card.get("time", ""),
                    raw=item,
                )
            )
    except Exception:
        pass
    return results


def normalize_zhihu(raw: dict, platform_cfg) -> list[SearchResult]:
    """Parse zhihu article search response into results."""
    results = []
    try:
        result_data = raw.get("result", raw)
        if isinstance(result_data, str):
            result_data = json.loads(result_data)

        items = (
            result_data.get("data", {}).get("list", [])
            or result_data.get("data", [])
            or result_data.get("results", [])
            or []
        )
        for item in items:
            obj = item.get("object", item)
            title = obj.get("title", "") or item.get("title", "")
            excerpt = obj.get("excerpt", "") or item.get("excerpt", "") or obj.get("content", "")[:200]
            url = obj.get("url", "") or item.get("url", "")
            author_name = obj.get("author", {}).get("name", "") or item.get("author", {}).get("name", "")
            vote_count = obj.get("voteup_count", 0) or item.get("voteup_count", 0)
            comment_count = obj.get("comment_count", 0) or item.get("comment_count", 0)
            qid = item.get("question", {}).get("id", "") if isinstance(item.get("question"), dict) else ""
            aid = obj.get("id", "") or item.get("id", "")

            results.append(
                SearchResult(
                    platform="zhihu",
                    platform_name="知乎",
                    title=title,
                    url=url or platform_cfg.answer_link_template.format(question_id=qid, answer_id=aid),
                    summary=excerpt,
                    author=author_name,
                    likes=vote_count,
                    comments=comment_count,
                    raw=item,
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
