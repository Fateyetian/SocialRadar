"""SocialRadar MCP Server — exposes search tools to Claude Code via stdio."""

from __future__ import annotations

import json
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import TikHubClient
from .platforms import load_platforms, get_api_key
from .aggregator import (
    normalize_xiaohongshu,
    normalize_zhihu,
    aggregate,
    SearchResult,
)

server = Server("social-radar")


def _build_output(results: list[SearchResult], query: str) -> str:
    """Format results as readable markdown for Claude."""
    if not results:
        return f"未找到与「{query}」相关的结果。"

    lines = [f"## 搜索结果: 「{query}」\n"]
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. **[{r.platform_name}]** [{r.title}]({r.url})\n"
            f"   {r.summary[:150]}\n"
            f"   作者: {r.author} | 点赞: {r.likes} | 评论: {r.comments}\n"
        )
    return "\n".join(lines)


async def _do_search(query: str, platforms_filter: str = "all") -> str:
    """Core search logic."""
    api_key = get_api_key()
    if not api_key:
        return "错误: 未设置 TIKHUB_API_KEY，请在 .env 文件中配置"

    all_platforms = load_platforms()
    if platforms_filter != "all":
        allowed = {p.strip() for p in platforms_filter.split(",")}
        all_platforms = [p for p in all_platforms if p.key in allowed]

    if not all_platforms:
        return f"错误: 未找到匹配的平台 「{platforms_filter}」"

    normalizers = {
        "xiaohongshu": normalize_xiaohongshu,
        "zhihu": normalize_zhihu,
    }

    all_results: list[SearchResult] = []

    for platform_cfg in all_platforms:
        try:
            client = TikHubClient(platform_cfg.endpoint, api_key)
            client.initialize()

            raw_json = client.search(platform_cfg.search_tool, query,
                                     platform_cfg.make_search_args(query))
            raw = json.loads(raw_json)

            normalize_fn = normalizers.get(platform_cfg.key)
            if normalize_fn:
                results = normalize_fn(raw, platform_cfg)
                all_results.extend(results)

            client.close()
        except Exception as e:
            all_results.append(
                SearchResult(
                    platform=platform_cfg.key,
                    platform_name=platform_cfg.name,
                    title=f"[错误] {platform_cfg.name} 搜索失败: {e}",
                    url="",
                    summary=str(e),
                )
            )

    sorted_results = aggregate(all_results)
    return _build_output(sorted_results, query)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="social_radar_search",
            description="跨平台搜索社交媒体内容（支持小红书、知乎）。搜索求职面经、技术话题、行业动态。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如 'agentic RL 面试' 或 '大模型算法求职'",
                    },
                    "platforms": {
                        "type": "string",
                        "description": "目标平台，用逗号分隔。可选: xiaohongshu, zhihu, all。默认 all",
                        "default": "all",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="social_radar_xiaohongshu",
            description="仅在小红书搜索内容，适合搜索面经、经验帖、求职分享",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="social_radar_zhihu",
            description="仅在知乎搜索内容，适合搜索深度讨论、技术问答、行业分析",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    query = arguments.get("query", "")

    if name == "social_radar_search":
        platforms = arguments.get("platforms", "all")
        result = await _do_search(query, platforms)
    elif name == "social_radar_xiaohongshu":
        result = await _do_search(query, "xiaohongshu")
    elif name == "social_radar_zhihu":
        result = await _do_search(query, "zhihu")
    else:
        result = f"未知工具: {name}"

    return [TextContent(type="text", text=result)]


def main():
    asyncio.run(run())


async def run():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    main()
