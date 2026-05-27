"""SocialRadar CLI — standalone command-line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .client import TikHubClient
from .platforms import load_platforms, get_api_key
from .aggregator import normalize_xiaohongshu, normalize_zhihu, aggregate

app = typer.Typer(name="social-radar", help="多平台社交媒体搜索工具")
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    platforms: str = typer.Option("all", "--platforms", "-p", help="目标平台 (xiaohongshu,zhihu,all)"),
    limit: int = typer.Option(10, "--limit", "-n", help="显示结果数量"),
    json_output: bool = typer.Option(False, "--json", help="JSON 格式输出"),
):
    """跨平台搜索社交媒体内容。"""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]错误: 未设置 TIKHUB_API_KEY[/red]")
        console.print("请在项目根目录创建 .env 文件: TIKHUB_API_KEY=your_key")
        raise typer.Exit(1)

    all_platforms = load_platforms()
    if platforms != "all":
        allowed = {p.strip() for p in platforms.split(",")}
        all_platforms = [p for p in all_platforms if p.key in allowed]

    normalizers = {
        "xiaohongshu": normalize_xiaohongshu,
        "zhihu": normalize_zhihu,
    }

    all_results = []

    for platform_cfg in all_platforms:
        console.print(f"[dim]正在搜索 {platform_cfg.name}...[/dim]")
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
            console.print(f"[red]{platform_cfg.name} 搜索失败: {e}[/red]")

    sorted_results = aggregate(all_results)[:limit]

    if json_output:
        import json as _json
        print(_json.dumps(
            [{"platform": r.platform, "title": r.title, "url": r.url,
              "summary": r.summary, "author": r.author, "likes": r.likes}
             for r in sorted_results],
            ensure_ascii=False, indent=2,
        ))
        return

    if not sorted_results:
        console.print(f"[yellow]未找到与「{query}」相关的结果[/yellow]")
        return

    table = Table(title=f"搜索结果: 「{query}」")
    table.add_column("#", style="dim")
    table.add_column("平台")
    table.add_column("标题")
    table.add_column("作者")
    table.add_column("点赞", justify="right")

    for i, r in enumerate(sorted_results, 1):
        table.add_row(str(i), r.platform_name, r.title[:50], r.author, str(r.likes))

    console.print(table)
    console.print(f"\n[dim]共 {len(sorted_results)} 条结果[/dim]")


@app.command()
def platforms_list():
    """列出所有支持的平台。"""
    platforms = load_platforms()
    table = Table(title="支持的平台")
    table.add_column("Key")
    table.add_column("名称")
    table.add_column("搜索工具")
    for p in platforms:
        table.add_row(p.key, p.name, p.search_tool)
    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
