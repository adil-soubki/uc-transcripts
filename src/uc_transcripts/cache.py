"""File caching utilities for JSON data."""

import json
from pathlib import Path
from typing import Optional, Callable, Any


def load_json(path: Path) -> Optional[dict]:
    """
    Load JSON file if it exists.

    Args:
        path: Path to JSON file

    Returns:
        Loaded JSON data as dict, or None if file doesn't exist
    """
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    """
    Save data to JSON file with pretty printing.

    Args:
        path: Path to save JSON file
        data: Data to serialize to JSON
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def with_cache(
    cache_path: Path,
    fetch_fn: Callable[[], Any],
    force: bool = False,
) -> Any:
    """
    Generic caching wrapper for expensive operations.

    Args:
        cache_path: Path to cache file
        fetch_fn: Function to call if cache miss or force refresh
        force: If True, bypass cache and re-fetch

    Returns:
        Cached or freshly fetched data
    """
    if not force:
        cached = load_json(cache_path)
        if cached is not None:
            return cached

    data = fetch_fn()
    save_json(cache_path, data)
    return data
