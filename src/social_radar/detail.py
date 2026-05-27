"""Content detail via TikHub REST API — gets full article/note body text."""

from __future__ import annotations

import re
import logging

import httpx

from .store import get_store

logger = logging.getLogger("socialradar.detail")

TIKHUB_API = "https://api.tikhub.io"
TIMEOUT = 20.0


def fetch_xiaohongshu_detail(note_id: str, api_key: str) -> dict | None:
    """Fetch full Xiaohongshu note detail via REST API (Web V2)."""
    with httpx.Client(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TIMEOUT,
    ) as c:
        try:
            resp = c.get(
                f"{TIKHUB_API}/api/v1/xiaohongshu/web_v2/fetch_feed_notes_v2",
                params={"note_id": note_id},
            )
            if resp.status_code != 200:
                logger.warning("XHS Web V2 returned %d", resp.status_code)
                return None
            data = resp.json()
        except Exception as e:
            logger.warning("XHS detail request failed: %s", e)
            return None

    return _parse_xhs_v2(data, note_id)


def _parse_xhs_v2(data: dict, note_id: str) -> dict | None:
    try:
        inner = data.get("data", {})
        items = inner.get("data", [inner])
        if isinstance(items, list):
            first_block = items[0] if items else {}
        else:
            first_block = items
        note_list = first_block.get("note_list", [first_block])
        note = note_list[0] if note_list else {}
    except Exception:
        return None

    try:
        title = note.get("title", "") or note.get("display_title", "")
        desc = note.get("desc", "")
        user = note.get("user", {}) or {}
        author = user.get("nickname", "") if isinstance(user, dict) else ""
        return {
            "platform": "xiaohongshu",
            "platform_name": "小红书",
            "title": title,
            "full_text": desc,
            "author": author,
            "images": [],
            "source_url": f"https://www.xiaohongshu.com/explore/{note_id}",
        }
    except Exception:
        return None


def fetch_zhihu_detail(url: str, api_key: str) -> dict | None:
    """Fetch full Zhihu article or answer detail via REST API."""
    article_m = re.search(r"/articles/(\d+)", url)
    q_m = re.search(r"/question/(\d+)", url)
    a_m = re.search(r"/answer/(\d+)", url)

    with httpx.Client(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TIMEOUT,
    ) as c:
        # Article detail
        if article_m:
            try:
                resp = c.get(
                    f"{TIKHUB_API}/api/v1/zhihu/web/fetch_column_article_detail",
                    params={"article_id": article_m.group(1)},
                )
                if resp.status_code == 200:
                    return _parse_zhihu_article(resp.json(), url)
            except Exception as e:
                logger.warning("Zhihu article detail failed: %s", e)

        # Question answers
        if q_m:
            try:
                resp = c.get(
                    f"{TIKHUB_API}/api/v1/zhihu/web/fetch_question_answers",
                    params={"question_id": q_m.group(1), "limit": 5, "offset": 0, "order": "default"},
                )
                if resp.status_code == 200:
                    return _parse_zhihu_answer(resp.json(), a_m.group(1) if a_m else "", url)
            except Exception as e:
                logger.warning("Zhihu answer detail failed: %s", e)

    return None


def _parse_zhihu_article(data: dict, url: str) -> dict | None:
    try:
        d = data.get("data", {})
        title = d.get("title", "")
        content = d.get("content", "") or d.get("body", "")
        author_info = d.get("author", {})
        author = author_info.get("name", "") if isinstance(author_info, dict) else ""
        return {
            "platform": "zhihu",
            "platform_name": "知乎",
            "title": title,
            "full_text": _strip_html(content)[:10000],
            "author": author,
            "images": [],
            "source_url": url,
        }
    except Exception:
        return None


def _parse_zhihu_answer(data: dict, target_aid: str, url: str) -> dict | None:
    try:
        items = data.get("data", {}).get("data", data.get("data", []))
        if not isinstance(items, list):
            items = [items] if items else []

        target = None
        for item in items:
            obj = item.get("object", item) if isinstance(item, dict) else {}
            aid = str(obj.get("id", ""))
            if target_aid and aid == target_aid:
                target = obj
                break
        if not target and items:
            first = items[0]
            target = first.get("object", first) if isinstance(first, dict) else {}

        if not target:
            return None

        question = target.get("question", {})
        title = question.get("title", "") if isinstance(question, dict) else ""
        content = target.get("content", "") or target.get("excerpt", "")
        author_info = target.get("author", {})
        author = author_info.get("name", "") if isinstance(author_info, dict) else ""

        return {
            "platform": "zhihu",
            "platform_name": "知乎",
            "title": title,
            "full_text": _strip_html(content)[:10000],
            "author": author,
            "images": [],
            "source_url": url,
        }
    except Exception:
        return None


def extract_xiaohongshu_note_id(url: str) -> str:
    m = re.search(r"/explore/([a-zA-Z0-9]+)", url)
    if m: return m.group(1)
    m = re.search(r"/discovery/item/([a-zA-Z0-9]+)", url)
    if m: return m.group(1)
    return ""


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)
