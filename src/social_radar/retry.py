"""Retry with exponential backoff for unreliable API calls."""

from __future__ import annotations

import time
import logging

logger = logging.getLogger("socialradar.retry")


def retry_with_backoff(fn, max_retries: int = 3, base_delay: float = 1.0):
    """Call fn() with exponential backoff on failure.

    Only retries on connection/timeout errors, not logic errors.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning("Attempt %d/%d failed: %s. Retrying in %.1fs...",
                               attempt + 1, max_retries, e, delay)
                time.sleep(delay)
    raise last_error
