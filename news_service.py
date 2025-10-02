"""News collection utilities for the Streamlit application."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests


DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_NEWS_PATH = DATA_DIR / "sample_news.json"


def search_news(keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve news articles related to ``keyword``.

    This function attempts to call the GNews API when an API key is provided
    via the ``GNEWS_API_KEY`` environment variable. If the key is not found or
    the request fails, a curated offline sample dataset is returned instead.
    """

    keyword = (keyword or "").strip()
    if not keyword:
        return []

    api_key = os.getenv("GNEWS_API_KEY")
    if api_key:
        params = {
            "q": keyword,
            "token": api_key,
            "lang": "ko",
            "max": str(max_results),
        }
        try:
            response = requests.get("https://gnews.io/api/v4/search", params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return _transform_gnews_response(payload, max_results)
        except Exception:
            # Fall back to the offline dataset below.
            pass

    return _load_sample_news(keyword, max_results)


def _transform_gnews_response(payload: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
    articles = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(articles, list):
        return []

    transformed: List[Dict[str, Any]] = []
    for article in articles[:max_results]:
        transformed.append(
            {
                "title": article.get("title"),
                "summary": article.get("description"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "source": (article.get("source") or {}).get("name"),
            }
        )

    return transformed


def _load_sample_news(keyword: str, max_results: int) -> List[Dict[str, Any]]:
    if not SAMPLE_NEWS_PATH.exists():
        return []

    with SAMPLE_NEWS_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    keyword_lower = keyword.lower()
    matches = [
        item
        for item in data
        if keyword_lower in (item.get("title", "") + item.get("summary", "")).lower()
    ]

    if not matches:
        matches = data

    return matches[:max_results]


__all__ = ["search_news"]

