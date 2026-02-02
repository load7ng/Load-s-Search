"""
Load and validate config.json. Ensure data dir and subdirs exist.
"""
import json
from pathlib import Path
from typing import Any

from .paths import (
    get_config_path,
    get_data_dir,
    get_file_index_data_dir,
    get_logs_dir,
    get_search_index_dir,
)

# Default config used when none exists
DEFAULT_CONFIG: dict[str, Any] = {
    "folders_to_index": [],
    "log_terminal_history": True,
    "log_file_activity": True,
    "exclude_patterns": [".git", "__pycache__", "node_modules", ".venv", "venv"],
    "max_file_size_kb": 512,
    "dark_mode": False,
}


def ensure_data_dirs() -> Path:
    """Create LoadsSearch/, logs/, file_index_data/, search_index/ if missing. Returns data dir."""
    data = get_data_dir()
    data.mkdir(parents=True, exist_ok=True)
    get_logs_dir().mkdir(parents=True, exist_ok=True)
    get_file_index_data_dir().mkdir(parents=True, exist_ok=True)
    get_search_index_dir().mkdir(parents=True, exist_ok=True)
    return data


def ensure_config() -> Path:
    """Create default config.json if missing. Returns path to config."""
    path = get_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return path


def load_config() -> dict[str, Any]:
    """
    Load config.json. Ensures data dirs and config exist first.
    Validates required keys and types; fills missing optional keys from defaults.
    """
    ensure_data_dirs()
    ensure_config()
    path = get_config_path()
    raw = json.loads(path.read_text(encoding="utf-8"))

    # Required
    if "folders_to_index" not in raw:
        raw["folders_to_index"] = []
    if not isinstance(raw["folders_to_index"], list):
        raw["folders_to_index"] = []

    # Optional with defaults
    for key, default in DEFAULT_CONFIG.items():
        if key not in raw:
            raw[key] = default
        elif key == "folders_to_index":
            raw[key] = [str(p) for p in raw[key]]
        elif key == "exclude_patterns" and isinstance(raw[key], list):
            raw[key] = [str(x) for x in raw[key]]
        elif key == "max_file_size_kb":
            try:
                raw[key] = int(raw[key])
            except (TypeError, ValueError):
                raw[key] = default
        elif key == "dark_mode":
            raw[key] = bool(raw[key]) if isinstance(raw[key], (bool, int, str)) else default

    return raw


def save_config(cfg: dict[str, Any]) -> None:
    """Write config.json. Ensures data dir exists. Preserves all keys including last_indexed_iso."""
    ensure_data_dirs()
    path = get_config_path()
    out = {k: cfg.get(k, DEFAULT_CONFIG.get(k)) for k in DEFAULT_CONFIG}
    out["folders_to_index"] = [str(p) for p in cfg.get("folders_to_index", [])]
    if cfg.get("last_indexed_iso") is not None:
        out["last_indexed_iso"] = cfg["last_indexed_iso"]
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
