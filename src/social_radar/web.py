"""SocialRadar Web UI — beautiful search interface."""

from __future__ import annotations

import json
import asyncio
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .client import TikHubClient
from .platforms import load_platforms, get_api_key
from .aggregator import (
    normalize_xiaohongshu,
    normalize_zhihu,
    aggregate,
    SearchResult,
)

app = FastAPI(title="SocialRadar", version="0.1.0")

_TEMPLATE = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index():
    return _TEMPLATE


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    platforms: str = Query("all", description="Comma-separated platform keys"),
):
    api_key = get_api_key()
    if not api_key:
        return JSONResponse({"error": "TIKHUB_API_KEY not configured"}, status_code=500)

    all_platforms = load_platforms()
    if platforms != "all":
        allowed = {p.strip() for p in platforms.split(",")}
        all_platforms = [p for p in all_platforms if p.key in allowed]

    normalizers = {
        "xiaohongshu": normalize_xiaohongshu,
        "zhihu": normalize_zhihu,
    }

    all_results: list[SearchResult] = []
    errors = []

    for platform_cfg in all_platforms:
        try:
            client = TikHubClient(platform_cfg.endpoint, api_key)
            client.initialize()
            resp = client.search(platform_cfg.search_tool, q,
                                 platform_cfg.make_search_args(q))
            raw = json.loads(resp)
            normalize_fn = normalizers.get(platform_cfg.key)
            if normalize_fn:
                results = normalize_fn(raw, platform_cfg)
                all_results.extend(results)
            client.close()
        except Exception as e:
            errors.append({"platform": platform_cfg.key, "error": str(e)})

    sorted_results = aggregate(all_results, sort_by="likes")

    return {
        "query": q,
        "total": len(sorted_results),
        "results": [
            {
                "platform": r.platform,
                "platform_name": r.platform_name,
                "title": r.title,
                "url": r.url,
                "summary": r.summary,
                "author": r.author,
                "likes": r.likes,
                "comments": r.comments,
                "collect_count": r.collect_count,
            }
            for r in sorted_results
        ],
        "errors": errors,
    }


def main():
    import uvicorn
    uvicorn.run("social_radar.web:app", host="127.0.0.1", port=8765, reload=True)


if __name__ == "__main__":
    main()
