"""SocialRadar Web UI — beautiful search interface."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse

from .client import TikHubClient
from .platforms import load_platforms, get_api_key
from .aggregator import (
    normalize_xiaohongshu,
    normalize_zhihu,
    aggregate,
    SearchResult,
)
from .config import MAX_PAGE_SIZE, LOG_LEVEL, LOG_PATH, ensure_data_dir
from .store import get_store
from .detail import fetch_xiaohongshu_detail, fetch_zhihu_detail, extract_xiaohongshu_note_id

ensure_data_dir()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_PATH), encoding="utf-8"),
    ],
)
logger = logging.getLogger("socialradar.web")

app = FastAPI(title="SocialRadar", version="0.1.0")

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"
_CONTENT_TEMPLATE_PATH = Path(__file__).parent / "templates" / "content.html"


@app.get("/", response_class=HTMLResponse)
async def index():
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


@app.get("/content", response_class=HTMLResponse)
async def content_page():
    return _CONTENT_TEMPLATE_PATH.read_text(encoding="utf-8")


def _init_client(platform_cfg, api_key: str) -> TikHubClient:
    """Initialize TikHubClient (sync — called via asyncio.to_thread)."""
    client = TikHubClient(platform_cfg.endpoint, api_key)
    client.initialize()
    return client


def _result_to_dict(r: SearchResult) -> dict:
    return {
        "platform": r.platform,
        "platform_name": r.platform_name,
        "title": r.title,
        "url": r.url,
        "summary": r.summary,
        "author": r.author,
        "likes": r.likes,
        "comments": r.comments,
        "collect_count": r.collect_count,
        "published_at": r.published_at,
    }


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    platforms: str = Query("all", description="Comma-separated platform keys"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    api_key = get_api_key()
    if not api_key:
        return JSONResponse({"error": "TIKHUB_API_KEY not configured"}, status_code=500)

    store = get_store()
    all_platforms = load_platforms()
    if platforms != "all":
        allowed = {p.strip() for p in platforms.split(",")}
        all_platforms = [p for p in all_platforms if p.key in allowed]
    platform_keys = ",".join(p.key for p in all_platforms)

    # Check cache first
    cached = store.get_cached_query(q, platform_keys)
    if cached is not None:
        logger.info("Cache hit: query=%r platforms=%r total=%d", q, platform_keys, len(cached))
        total = len(cached)
        start = (page - 1) * page_size
        end = start + page_size
        page_results = cached[start:end]
        return {
            "query": q,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": end < total,
            "cached": True,
            "results": page_results,
            "errors": [],
        }

    # Live search — run sync TikHubClient in thread pool
    logger.info("Live search: query=%r platforms=%r", q, platform_keys)
    normalizers = {
        "xiaohongshu": normalize_xiaohongshu,
        "zhihu": normalize_zhihu,
    }

    async def search_platforms() -> tuple[list[SearchResult], list[dict]]:
        all_results: list[SearchResult] = []
        errors: list[dict] = []
        for platform_cfg in all_platforms:
            try:
                client = await asyncio.to_thread(_init_client, platform_cfg, api_key)
                # Main keyword search
                resp = await asyncio.to_thread(
                    client.search, platform_cfg.search_tool, q,
                    platform_cfg.make_search_args(q),
                )
                raw = json.loads(resp)
                normalize_fn = normalizers.get(platform_cfg.key)
                if normalize_fn:
                    results = normalize_fn(raw, platform_cfg)
                    all_results.extend(results)

                # AI semantic search for zhihu
                if platform_cfg.key == "zhihu" and platform_cfg.ai_search_tool:
                    try:
                        ai_resp = await asyncio.to_thread(
                            client.search, platform_cfg.ai_search_tool, q,
                            platform_cfg.ai_search_params,
                        )
                        ai_raw = json.loads(ai_resp)
                        if normalize_fn:
                            ai_results = normalize_fn(ai_raw, platform_cfg)
                            all_results.extend(ai_results)
                    except Exception:
                        pass  # AI search is supplementary; ignore failures

                await asyncio.to_thread(client.close)
            except Exception as e:
                logger.warning("Platform %s failed: %s", platform_cfg.key, e)
                errors.append({"platform": platform_cfg.key, "error": str(e)})
        return all_results, errors

    all_results, errors = await search_platforms()

    sorted_results = aggregate(all_results, sort_by="likes")
    result_dicts = [_result_to_dict(r) for r in sorted_results]

    # Cache full result set
    if result_dicts:
        store.set_cached_query(q, platform_keys, result_dicts)
    store.add_search_history(q, platform_keys, len(result_dicts))

    # Paginate
    total = len(result_dicts)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = result_dicts[start:end]

    return {
        "query": q,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "cached": False,
        "results": page_results,
        "errors": errors,
    }


@app.get("/api/detail/{platform}/{content_id:path}")
async def content_detail(
    platform: str,
    content_id: str,
    url: str = Query(...),
):
    api_key = get_api_key()
    if not api_key:
        return JSONResponse({"error": "TIKHUB_API_KEY not configured"}, status_code=500)

    store = get_store()
    cached = store.get_cached_content(platform, content_id)
    if cached:
        return {"cached": True, **cached}

    # Use direct REST API fetchers
    detail = None
    if platform == "xiaohongshu":
        note_id = extract_xiaohongshu_note_id(url) or content_id
        if note_id:
            detail = await asyncio.to_thread(fetch_xiaohongshu_detail, note_id, api_key)
    elif platform == "zhihu":
        detail = await asyncio.to_thread(fetch_zhihu_detail, url, api_key)

    if detail is None:
        return JSONResponse({"error": "Failed to fetch detail content"}, status_code=502)

    if content_id:
        store.set_cached_content(platform, content_id, detail)
    return {"cached": False, **detail}


@app.get("/api/bookmarks")
async def list_bookmarks(
    tag: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    store = get_store()
    bookmarks, total = store.get_bookmarks(tag=tag, page=page, page_size=page_size)
    for b in bookmarks:
        b["tags"] = store.get_bookmark_tags(b["id"])
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (page * page_size) < total,
        "results": bookmarks,
    }


@app.post("/api/bookmarks")
async def create_bookmark(body: dict = Body(...)):
    store = get_store()
    bid = store.add_bookmark(body)
    return {"id": bid, "ok": True}


@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: int):
    store = get_store()
    store.remove_bookmark(bookmark_id)
    return {"ok": True}


@app.get("/api/bookmarks/{bookmark_id}/annotations")
async def list_annotations(bookmark_id: int):
    store = get_store()
    return {"results": store.get_annotations(bookmark_id)}


@app.post("/api/bookmarks/{bookmark_id}/annotations")
async def create_annotation(bookmark_id: int, body: dict = Body(...)):
    store = get_store()
    note_id = store.add_annotation(bookmark_id, body["note_text"])
    return {"id": note_id, "ok": True}


@app.put("/api/annotations/{annotation_id}")
async def update_annotation(annotation_id: int, body: dict = Body(...)):
    store = get_store()
    store.update_annotation(annotation_id, body["note_text"])
    return {"ok": True}


@app.delete("/api/annotations/{annotation_id}")
async def delete_annotation(annotation_id: int):
    store = get_store()
    store.delete_annotation(annotation_id)
    return {"ok": True}


@app.get("/api/tags")
async def list_tags():
    store = get_store()
    return {"results": store.get_all_tags()}


@app.post("/api/tags")
async def create_tag(body: dict = Body(...)):
    store = get_store()
    tid = store.add_tag(body["name"], body.get("color", "#4f46e5"))
    return {"id": tid, "ok": True}


@app.delete("/api/tags/{tag_id}")
async def delete_tag(tag_id: int):
    store = get_store()
    store.delete_tag(tag_id)
    return {"ok": True}


@app.post("/api/bookmarks/{bookmark_id}/tags")
async def assign_tag(bookmark_id: int, body: dict = Body(...)):
    store = get_store()
    store.assign_tag(bookmark_id, body["tag_id"])
    return {"ok": True}


@app.delete("/api/bookmarks/{bookmark_id}/tags/{tag_id}")
async def remove_tag(bookmark_id: int, tag_id: int):
    store = get_store()
    store.remove_tag(bookmark_id, tag_id)
    return {"ok": True}


@app.get("/api/search/history")
async def search_history(limit: int = Query(20)):
    store = get_store()
    return {"results": store.get_search_history(limit)}


@app.get("/api/bookmarks/check")
async def check_bookmark(url: str = Query(...)):
    store = get_store()
    return {"bookmarked": store.is_bookmarked(url)}


# ── Startup / Shutdown ──────────────────────────────────────

@app.on_event("startup")
async def startup():
    store = get_store()
    q, c = store.evict_all_expired()
    if q or c:
        logger.info("Evicted %d query + %d content cache entries", q, c)


def main():
    import uvicorn
    from .config import HOST, PORT
    uvicorn.run("social_radar.web:app", host=HOST, port=PORT, reload=True)


if __name__ == "__main__":
    main()
