"""Content detail fetching via TikHub MCP detail tools."""

from __future__ import annotations

import json
import re
import logging

from .client import TikHubClient
from .platforms import PlatformConfig
from .store import get_store

logger = logging.getLogger("socialradar.detail")


def fetch_detail(platform_cfg: PlatformConfig, url: str, api_key: str) -> dict | None:
    """Fetch full content detail for a given URL. Returns dict or None on failure."""
    store = get_store()

    # Determine content ID for cache lookup
    if platform_cfg.key == "xiaohongshu":
        content_id = _extract_xiaohongshu_note_id(url)
    elif platform_cfg.key == "zhihu":
        content_id = _extract_zhihu_ids(url) or url
    else:
        content_id = url

    # Check cache
    cached = store.get_cached_content(platform_cfg.key, content_id)
    if cached is not None:
        logger.info("Content cache hit: %s/%s", platform_cfg.key, content_id)
        return cached

    # Fetch from TikHub
    try:
        client = TikHubClient(platform_cfg.endpoint, api_key)
        client.initialize()

        if platform_cfg.key == "xiaohongshu":
            result = _fetch_xiaohongshu_detail(client, platform_cfg, url, content_id)
        elif platform_cfg.key == "zhihu":
            result = _fetch_zhihu_detail(client, platform_cfg, url)
        else:
            result = None

        client.close()

        if result:
            store.set_cached_content(platform_cfg.key, content_id, result)
        return result
    except Exception as e:
        logger.warning("Detail fetch failed for %s/%s: %s", platform_cfg.key, url, e)
        return None


def _fetch_xiaohongshu_detail(client: TikHubClient, cfg: PlatformConfig, url: str, note_id: str) -> dict | None:
    if not note_id or not cfg.detail_tool:
        return None
    resp = client.call_tool(cfg.detail_tool, {"note_id": note_id})
    raw = json.loads(resp)

    # Parse response: data.data.data....
    try:
        data = raw.get("data", {}).get("data", raw.get("data", {}))
        note = data.get("note", data)
        title = note.get("title", "") or note.get("display_title", "")
        desc = note.get("desc", "")
        user = note.get("user", {})
        author = user.get("nickname", "") if isinstance(user, dict) else ""
        images = []
        image_list = note.get("image_list", []) or note.get("images", [])
        for img in image_list:
            if isinstance(img, dict):
                img_url = img.get("url", "") or img.get("url_default", "") or img.get("info_list", [{}])[0].get("url", "")
                if img_url:
                    images.append(img_url)

        return {
            "platform": "xiaohongshu",
            "platform_name": "小红书",
            "title": title,
            "full_text": desc,
            "author": author,
            "images": images,
            "source_url": url,
        }
    except Exception:
        return None


def _fetch_zhihu_detail(client: TikHubClient, cfg: PlatformConfig, url: str) -> dict | None:
    ids = _extract_zhihu_ids(url)
    if not ids or not cfg.question_answers_tool:
        return _fallback_zhihu_detail(client, cfg, url)

    qid, aid = ids
    question_id = qid or aid  # fall back to answer_id as question_id
    try:
        resp = client.call_tool(
            cfg.question_answers_tool,
            {"question_id": question_id, "limit": 5, "offset": 0},
        )
    except Exception:
        return _fallback_zhihu_detail(client, cfg, url)

    raw = json.loads(resp)
    try:
        data_list = raw.get("data", {}).get("data", [])
        if not data_list:
            return _fallback_zhihu_detail(client, cfg, url)

        # Take the first/or specified answer
        target = None
        for item in data_list:
            obj = item.get("object", item)
            obj_id = str(obj.get("id", ""))
            if aid and obj_id == aid:
                target = obj
                break
        if not target:
            target = data_list[0].get("object", data_list[0])

        title = obj.get("question", {}).get("title", "") if not aid else ""
        content = target.get("content", "") or target.get("excerpt", "")
        author = target.get("author", {})
        author_name = author.get("name", "") if isinstance(author, dict) else ""

        return {
            "platform": "zhihu",
            "platform_name": "知乎",
            "title": title,
            "full_text": _strip_html(content)[:5000],
            "author": author_name,
            "images": [],
            "source_url": url,
        }
    except Exception:
        return _fallback_zhihu_detail(client, cfg, url)


def _fallback_zhihu_detail(client: TikHubClient, cfg: PlatformConfig, url: str) -> dict | None:
    """Try AI search as fallback for article detail."""
    if not cfg.ai_search_tool:
        return None
    try:
        resp = client.call_tool(cfg.ai_search_tool, {"message_content": url})
        raw = json.loads(resp)
        text = raw.get("data", {}).get("data", {}).get("text", "")
        return {
            "platform": "zhihu",
            "platform_name": "知乎",
            "title": "",
            "full_text": text[:5000] if text else "",
            "author": "",
            "images": [],
            "source_url": url,
        }
    except Exception:
        return None


def _extract_xiaohongshu_note_id(url: str) -> str:
    m = re.search(r"/explore/([a-zA-Z0-9]+)", url)
    return m.group(1) if m else ""


def _extract_zhihu_ids(url: str) -> tuple[str, str] | None:
    """Extract (question_id, answer_id) from a Zhihu URL."""
    qm = re.search(r"/question/(\d+)", url)
    qid = qm.group(1) if qm else ""
    am = re.search(r"/answer/(\d+)", url)
    aid = am.group(1) if am else ""
    if qid or aid:
        return qid, aid
    return None


def _strip_html(text: str) -> str:
    import re as _re
    return _re.sub(r"<[^>]+>", "", text)
