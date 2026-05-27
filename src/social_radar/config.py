"""Centralized configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = Path(os.getenv("SOCIALRADAR_DATA_DIR", str(PROJECT_ROOT / "data")))

# Server
HOST = os.getenv("SOCIALRADAR_HOST", "127.0.0.1")
PORT = int(os.getenv("SOCIALRADAR_PORT", "8765"))

# Cache TTL (seconds)
CACHE_TTL_QUERY = int(os.getenv("SOCIALRADAR_CACHE_TTL_QUERY", "1800"))       # 30 min
CACHE_TTL_CONTENT = int(os.getenv("SOCIALRADAR_CACHE_TTL_CONTENT", "86400"))  # 24 hr

# Request
REQUEST_TIMEOUT = int(os.getenv("SOCIALRADAR_REQUEST_TIMEOUT", "15"))
MAX_PAGE_SIZE = int(os.getenv("SOCIALRADAR_MAX_PAGE_SIZE", "20"))
MAX_RETRIES = int(os.getenv("SOCIALRADAR_MAX_RETRIES", "3"))

# Logging
LOG_LEVEL = os.getenv("SOCIALRADAR_LOG_LEVEL", "INFO")

# Database
DB_PATH = DATA_DIR / "social_radar.db"
LOG_PATH = DATA_DIR / "social_radar.log"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
