"""
Resolve the LoadsSearch data folder and subpaths.
Uses environment variable LOADS_SEARCH_DATA or default in user home.
"""
import os
from pathlib import Path


def get_data_dir() -> Path:
    """Root data directory (synced via Syncthing)."""
    env = os.environ.get("LOADS_SEARCH_DATA")
    if env:
        return Path(env).resolve()
    home = Path.home()
    return home / "LoadsSearch"


def get_logs_dir() -> Path:
    """logs/ — raw activity logs (synced)."""
    return get_data_dir() / "logs"


def get_file_index_data_dir() -> Path:
    """file_index_data/ — metadata about scanned files (synced)."""
    return get_data_dir() / "file_index_data"


def get_search_index_dir() -> Path:
    """search_index/ — Whoosh index (local only, not synced)."""
    return get_data_dir() / "search_index"


def get_config_path() -> Path:
    """config.json path."""
    return get_data_dir() / "config.json"
