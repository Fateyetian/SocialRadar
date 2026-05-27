<p align="center">[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE) [![MCP](https://img.shields.io/badge/MCP-2024--11--05-purple?style=flat-square&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io) [![Platforms](https://img.shields.io/badge/platforms-Xiaohongshu_|_Zhihu-red?style=flat-square)]() [![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)]()</p>

<br>

<div align="center">
  <pre style="font-size: 12px; line-height: 1.2; color: #6366f1; background: none; border: none; margin: 0; padding: 0;">
 ██████╗  ██████╗  ██████╗██╗ █████╗ ██╗     ██████╗  █████╗ ██████╗  █████╗ ██████╗ 
██╔════╝ ██╔═══██╗██╔════╝██║██╔══██╗██║     ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔══██╗
╚█████╗  ██║   ██║██║     ██║███████║██║     ██████╔╝███████║██║  ██║███████║██████╔╝
 ╚═══██╗ ██║   ██║██║     ██║██╔══██║██║     ██╔══██╗██╔══██║██║  ██║██╔══██║██╔══██╗
██████╔╝ ╚██████╔╝╚██████╗██║██║  ██║███████╗██║  ██║██║  ██║██████╔╝██║  ██║██║  ██║
╚═════╝   ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
  </pre>
</div>

<p align="center">
  <strong>One sentence, scan multiple social platforms.</strong><br>
  <sub>AI-native cross-platform social search engine — powered by <a href="https://modelcontextprotocol.io">MCP</a> & <a href="https://tikhub.io">TikHub</a></sub>
</p>

<p align="right">
  🌐 <a href="README_CN.md">中文文档</a> &nbsp;|&nbsp; <b>English</b>
</p>

<br>

---

## 💡 Why SocialRadar?

Searching for tech interview experiences, industry trends, or community discussions across Chinese social platforms is painful:

- **Fragmented** — Xiaohongshu, Zhihu, Bilibili... each has its own search box and result format
- **Repetitive** — Same keyword typed 3+ times, same content scrolled past on different platforms
- **Ephemeral** — Tabs get closed, results get lost, no persistent record

SocialRadar solves this with a **single unified search interface** that plugs directly into your AI-powered workflow.

> *"Search Xiaohongshu and Zhihu for Agentic RL interview experiences."*  
> *"Find the latest discussions about DeepSeek-R1 training pipeline."*  
> *"What are people saying about LLM algorithm job market in 2025?"*

One sentence. Cross-platform search. Structured results. Right inside your IDE.

<table>
<tr>
<td width="50%" align="center" style="padding: 12px;"><b>🔄 Traditional Workflow</b></td>
<td width="50%" align="center" style="padding: 12px;"><b>⚡ With SocialRadar</b></td>
</tr>
<tr>
<td style="padding: 8px 16px; vertical-align: top;">
<p>❌ Open 2+ apps / websites manually</p>
<p>❌ Copy & paste results by hand</p>
<p>❌ Switch tabs and lose context</p>
<p>❌ No AI integration</p>
<p>❌ Search one platform at a time</p>
<p>❌ Results scattered, hard to compare</p>
</td>
<td style="padding: 8px 16px; vertical-align: top;">
<p>✅ One natural-language sentence</p>
<p>✅ Auto cross-platform aggregation</p>
<p>✅ Results persisted in conversation</p>
<p>✅ Native Claude Code MCP support</p>
<p>✅ All platforms in one request</p>
<p>✅ Normalized, ranked, deduped output</p>
</td>
</tr>
</table>

<br>

<table align="center">
<tr>
<td align="center" width="25%"><h3>🔍</h3><b>Multi-Platform</b><br><sub>Unified search across<br>Xiaohongshu & Zhihu<br>with one query</sub></td>
<td align="center" width="25%"><h3>🧠</h3><b>AI-Native</b><br><sub>Claude Code MCP<br>deep integration<br>speak, don't type</sub></td>
<td align="center" width="25%"><h3>🔌</h3><b>Hot-Pluggable</b><br><sub>Add any platform via<br>YAML config +<br>one normalizer function</sub></td>
<td align="center" width="25%"><h3>📊</h3><b>Structured Output</b><br><sub>Schema normalization<br>cross-platform dedup<br>engagement-based ranking</sub></td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.11+ | `asyncio`, type hints support |
| **TikHub API Key** | — | [Register for free](https://tikhub.io) |

### Installation

```bash
git clone https://github.com/your-username/SocialRadar.git && cd SocialRadar
pip install -e .
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# TikHub API Key — get it from https://tikhub.io
TIKHUB_API_KEY=tikhub_xxxxxxxxxxxxx
```

Verify the installation:

```bash
social-radar platforms
# Should list: Xiaohongshu (小红书), Zhihu (知乎)
```

---

## 📖 Usage

### 🧠 Method 1: Claude Code MCP *(Recommended)*

Add to Claude Code `settings.json`:

```json
{
  "mcpServers": {
    "social-radar": {
      "command": "python",
      "args": ["-m", "social_radar.server"],
      "env": { "TIKHUB_API_KEY": "tikhub_xxxxxxxxxxxxx" }
    }
  }
}
```

Restart Claude Code. Now you have **3 new tools** available via natural conversation:

| Tool | Description | When to Use |
|---|---|---|
| `social_radar_search` | Cross-platform search | General queries across all platforms |
| `social_radar_xiaohongshu` | Xiaohongshu-only search | Interview experiences, career tips |
| `social_radar_zhihu` | Zhihu-only search | Deep technical discussions, Q&A |

**Example conversations:**

```
> Search Xiaohongshu for LLM algorithm interview preparation tips.

> What are the latest discussions on Zhihu about GRPO vs PPO training?

> Find me Xiaohongshu posts about agentic RL jobs in China, and also
  search Zhihu for technical discussions on the same topic.
```

### ⌨️ Method 2: CLI

```bash
# Basic cross-platform search
social-radar search "agentic RL interview"

# Platform-specific
social-radar search "RLHF training pipeline" -p zhihu
social-radar search "大模型面试经验" -p xiaohongshu

# Advanced
social-radar search "DeepSeek-R1 architecture" -p xiaohongshu -n 20
social-radar search "MCP protocol" --json | jq '.[] | {title, url, likes}'
social-radar search "reward hacking" -p zhihu,xiaohongshu

# Utility
social-radar platforms              # list all supported platforms
social-radar search --help          # full CLI reference
```

<details open>
<summary><b>📟 Terminal Preview</b></summary>

```
╭─────────────────── Search Results: 「agentic RL interview」 ───────────────────╮
│ # │ Platform     │ Title                           │ Author      │ Likes │
│ 1 │ Xiaohongshu  │ Agent方向大模型面试总结…          │ AI求职笔记   │ 1.2k  │
│ 2 │ Zhihu        │ 如何看待 agentic RL 成为新热点？  │ Wang XX     │ 856   │
│ 3 │ Xiaohongshu  │ RL算法岗面试经验全分享            │ ML_Engineer │ 623   │
│ 4 │ Zhihu        │ GRPO 算法原理解析与面试题整理      │ Li-Paper   │ 491   │
│ 5 │ Xiaohongshu  │ 字节跳动AML面试回顾               │ OfferCat   │ 387   │
└──────────────────────────────────────────────────────────────────────────────┘
15 results total · deduped from 23 raw across 2 platforms
```

</details>

---

## 🔧 Configuration

### Platform Config (`config/platforms.yaml`)

Each platform is defined as a YAML block. Here's the anatomy:

```yaml
xiaohongshu:                          # platform key (used in -p flag)
  name: 小红书                          # display name
  endpoint: https://mcp.tikhub.io/...  # TikHub MCP endpoint
  search_tool: xiaohongshu_app_v2_search_notes  # primary search tool
  search_params:                       # default parameters
    keyword: "{query}"                 # {query} = user input placeholder
    page: 1
    sort_type: general
    note_type: 不限
    time_filter: 不限
  note_link_template: "https://www.xiaohongshu.com/explore/{note_id}"
  max_results: 20
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TIKHUB_API_KEY` | Yes | TikHub API authentication key |
| `SOCIAL_RADAR_CONFIG` | No | Custom YAML config path (default: `config/platforms.yaml`) |
| `SOCIAL_RADAR_MAX_RESULTS` | No | Override max results per platform (default: 20) |

### Adding a New Platform

**Step 1** — Add config block in `config/platforms.yaml`:

```yaml
bilibili:
  name: B站
  endpoint: https://mcp.tikhub.io/bilibili/mcp
  search_tool: bilibili_web_search_videos
  search_params:
    keyword: "{query}"
    page: 1
```

**Step 2** — Add a normalizer in `src/social_radar/aggregator.py`:

```python
def normalize_bilibili(raw: dict, platform_cfg) -> list[SearchResult]:
    """Parse Bilibili search response into unified SearchResult."""
    results = []
    items = raw.get("data", {}).get("items", [])
    for item in items:
        results.append(SearchResult(
            platform="bilibili",
            platform_name="B站",
            title=item.get("title", ""),
            url=item.get("url", ""),
            summary=item.get("description", ""),
            author=item.get("owner", {}).get("name", ""),
            likes=item.get("stat", {}).get("like", 0),
        ))
    return results
```

That's it. The new platform appears automatically in CLI and MCP tools.

---

## 🏗 Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="SocialRadar System Architecture" width="900">
</p>

### Three-Layer Design

| Layer | Modules | Responsibility |
|---|---|---|
| **Interface** | `server.py` · `cli.py` | Dual entrypoints: MCP stdio server for Claude Code + standalone Typer CLI |
| **Engine** | `platforms.py` · `client.py` · `aggregator.py` | YAML-driven platform registry, SSE protocol client, cross-platform result merging |
| **Gateway** | TikHub MCP endpoints | Per-platform MCP servers exposing search tools via standardized SSE protocol |

### Data Flow

<p align="center">
  <img src="docs/images/search-flow.png" alt="Search Flow" width="900">
</p>

```
User Input → [server.py / cli.py] → [platforms.py] → [client.py] → TikHub MCP
                                                    ↳ Xiaohongshu API
                                                    ↳ Zhihu API
Result ← [aggregator.py] ← normalize ← dedup ← rank ← [client.py]
```

### Key Design Decisions

- **Why SSE over WebSocket?** — TikHub uses standard MCP SSE protocol. Single-direction streaming is sufficient for request-response search patterns; bidirectional channels add complexity with no benefit here.
- **Why separate normalizer per platform?** — Each platform returns different JSON schemas. Isolating normalizers keeps them testable and replaceable without touching the core engine.
- **Why YAML for platform config?** — Human-readable, diff-friendly, no code change needed to adjust parameters. Users can customize search defaults without touching Python.

---

## 🌐 Supported Platforms

> Focused on Chinese tech-community platforms where AI practitioners share knowledge.  
> All 16 TikHub platforms are extensible — [see how to add one](#adding-a-new-platform).

<table>
<tr>
<td align="center" width="50%">
  <img src="https://www.xiaohongshu.com/favicon.ico" width="20">
  &nbsp;<b>Xiaohongshu</b> &nbsp; <code>xiaohongshu</code>
  <br><br>
  <b>Search tools:</b> <code>app_v2_search_notes</code> · <code>web_v2_fetch_search_notes</code><br>
  <b>Content types:</b> Notes, images, video notes<br>
  <b>Best for:</b> Interview experiences · career tips · tech explainers · industry gossip<br>
  <b>Notes:</b> Results favor engagement metrics (likes, saves, comments)
</td>
<td align="center" width="50%">
  <img src="https://www.zhihu.com/favicon.ico" width="20">
  &nbsp;<b>Zhihu</b> &nbsp; <code>zhihu</code>
  <br><br>
  <b>Search tools:</b> <code>article_search_v3</code> · <code>ai_search</code> · <code>topic_search_v3</code><br>
  <b>Content types:</b> Articles, answers, columns, topics<br>
  <b>Best for:</b> Deep technical discussions · Q&A · paper analysis · industry analysis<br>
  <b>Notes:</b> <code>ai_search</code> provides LLM-summarized answers with citations
</td>
</tr>
</table>

<p align="center">
  <sub>
    <b>Available via TikHub (config-ready):</b><br>
    Douyin · Bilibili · Weibo · YouTube · Reddit · Twitter · LinkedIn · Kuaishou · Threads · WeChat
  </sub>
</p>

---

## 📁 Project Structure

```
SocialRadar/
├── src/social_radar/
│   ├── __init__.py           # Package metadata (v0.1.0)
│   ├── server.py             # MCP Server — Claude Code entrypoint
│   ├── cli.py                 # CLI — standalone Typer entrypoint
│   ├── client.py              # TikHub SSE client (init → tools/call)
│   ├── platforms.py           # YAML config loader + platform data model
│   └── aggregator.py          # Schema normalization + dedup + ranking
├── config/
│   └── platforms.yaml         # Platform definitions (hot-pluggable)
├── docs/
│   └── images/                # Architecture & flow diagrams
├── pyproject.toml              # Python project metadata
├── .env.example                # API key template
├── .gitignore                  # Excludes .env, __pycache__, etc.
├── LICENSE                     # MIT License
├── README.md                   # English docs (this file)
└── README_CN.md                # 中文文档
```

---

## 🗺️ Roadmap

| Milestone | Status | Description |
|---|---|---|
| **v0.1** — Core | ✅ Done | Xiaohongshu + Zhihu search, MCP Server, CLI, result aggregation |
| **v0.2** — Richer Output | 🚧 Planned | Note detail fetching, comment extraction, author profile enrichment |
| **v0.3** — More Platforms | 📋 Planned | Bilibili, Weibo, Douyin normalizer support |
| **v0.4** — Smart Search | 💡 Idea | AI-powered query expansion, search term suggestions, multi-round refinement |
| **v0.5** — Persistence | 💡 Idea | Search history, saved queries, Markdown/JSON export |
| **v1.0** — Production | 🎯 Target | Test coverage >80%, CI/CD, Docker image, comprehensive docs |

---

## ❓ FAQ

<details>
<summary><b>How is SocialRadar different from using TikHub MCP directly?</b></summary>
<br>
TikHub exposes <b>one MCP endpoint per platform</b>. You would need to configure 16 separate MCP servers and remember 200+ tool names. SocialRadar provides a <b>single unified entrypoint</b> with 3 intuitive tools: search all platforms, or target a specific one. Cross-platform dedup, format normalization, and ranking happen automatically.
</details>

<details>
<summary><b>What affects search result quality?</b></summary>
<br>
SocialRadar is a client-side aggregation layer. Result <b>quality depends on TikHub's upstream APIs</b> and each platform's native search algorithm. We add value by:
<br><br>
<b>(1)</b> Normalizing heterogeneous response formats into a unified schema<br>
<b>(2)</b> Cross-platform dedup by title similarity<br>
<b>(3)</b> Engagement-based default ranking (likes, comments, collects)<br>
<b>(4)</b> Preserving raw response data for advanced users
</details>

<details>
<summary><b>Is my personal data involved?</b></summary>
<br>
<b>No.</b> SocialRadar calls TikHub's public API endpoints. No social media account login, no browser cookies, no personal data access. Your API key is the only credential and is stored locally in <code>.env</code> (excluded from git by <code>.gitignore</code>).
</details>

<details>
<summary><b>Can I use it without Claude Code?</b></summary>
<br>
<b>Yes.</b> The CLI mode (<code>social-radar search ...</code>) works independently in any terminal. The MCP server is optional — it's an additional entrypoint for Claude Code users who want AI-integrated search.
</details>

<details>
<summary><b>What's the rate limit?</b></summary>
<br>
Rate limits are determined by your <a href="https://tikhub.io">TikHub</a> subscription plan. SocialRadar itself adds no additional throttling. The free tier typically supports dozens of searches per minute — more than enough for individual use.
</details>

<details>
<summary><b>How do I debug a failed search?</b></summary>
<br>
Checklist:<br>
<b>1.</b> Verify <code>TIKHUB_API_KEY</code> is set correctly in <code>.env</code><br>
<b>2.</b> Run <code>social-radar platforms</code> to confirm config loading<br>
<b>3.</b> Check your TikHub dashboard for API quota status<br>
<b>4.</b> Run with <code>--json</code> flag to inspect raw API responses
</details>

---

## 🤝 Contributing

All contributions are welcome — from bug reports to new platform normalizers.

| Type | How | Example |
|---|---|---|
| 🐛 **Bug** | Open an Issue | Search returns empty / crash on specific keyword |
| 🔌 **Platform** | PR a normalizer | Add Weibo / Bilibili / Douyin support |
| 📝 **Docs** | PR the README | Fix typos, add usage examples, translate |
| ✨ **Feature** | Discuss in Issue first | Scheduled search, Markdown export, etc. |

Before submitting a PR: ensure `pip install -e .` succeeds and the CLI works with your changes.

---

## 📄 License

<p align="center">
  MIT License © 2026
</p>

<br>

<div align="center">
  <a href="https://github.com/your-username/SocialRadar">
    <img src="https://img.shields.io/github/stars/your-username/SocialRadar?style=social" alt="GitHub stars">
  </a>
</div>

<p align="center">
  <sub>Built with ❤️ for the AI community · Powered by <a href="https://tikhub.io">TikHub MCP</a></sub>
</p>
