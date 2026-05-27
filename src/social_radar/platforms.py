"""Platform definitions and configuration loading."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class PlatformConfig:
    key: str
    name: str
    endpoint: str
    search_tool: str
    search_params: dict
    note_link_template: str = ""
    max_results: int = 20
    # Extra tools
    detail_tool: str = ""
    ai_search_tool: str = ""
    ai_search_params: dict = field(default_factory=dict)
    question_answers_tool: str = ""
    question_answers_params: dict = field(default_factory=dict)
    answer_link_template: str = ""

    def make_search_args(self, query: str, **overrides) -> dict:
        """Build search arguments dict with {query} placeholder filled."""
        args = {}
        for k, v in self.search_params.items():
            if isinstance(v, str) and "{query}" in v:
                args[k] = v.replace("{query}", query)
            else:
                args[k] = v
        args.update(overrides)
        return args


_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
_CONFIG_PATH = _CONFIG_DIR / "platforms.yaml"


def load_platforms() -> list[PlatformConfig]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    platforms = []
    for key, data in raw.items():
        platforms.append(
            PlatformConfig(
                key=key,
                name=data["name"],
                endpoint=data["endpoint"],
                search_tool=data["search_tool"],
                search_params=data.get("search_params", {}),
                note_link_template=data.get("note_link_template", ""),
                max_results=data.get("max_results", 20),
                detail_tool=data.get("detail_tool", ""),
                ai_search_tool=data.get("ai_search_tool", ""),
                ai_search_params=data.get("ai_search_params", {}),
                question_answers_tool=data.get("question_answers_tool", ""),
                question_answers_params=data.get("question_answers_params", {}),
                answer_link_template=data.get("answer_link_template", ""),
            )
        )
    return platforms


def get_api_key() -> str:
    """Load TikHub API key from env or .env file."""
    # Try direct env first
    key = os.getenv("TIKHUB_API_KEY", "")
    if key:
        return key

    # Try dotenv
    try:
        from dotenv import load_dotenv

        load_dotenv()
        key = os.getenv("TIKHUB_API_KEY", "")
    except ImportError:
        pass

    return key
