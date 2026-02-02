"""
Read/write file_metadata.json (synced). Handle missing files gracefully.
"""
import json
from pathlib import Path
from typing import Any

from .paths import get_file_index_data_dir


def get_metadata_path() -> Path:
    return get_file_index_data_dir() / "file_metadata.json"


def load_metadata() -> list[dict[str, Any]]:
    """Load file_metadata.json. Returns [] if missing or invalid."""
    path = get_metadata_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_metadata(entries: list[dict[str, Any]]) -> None:
    """Write file_metadata.json. Ensures dir exists."""
    get_file_index_data_dir().mkdir(parents=True, exist_ok=True)
    path = get_metadata_path()
    # Normalize: path as str, mtime as number, size as int
    out = []
    for e in entries:
        out.append({
            "path": str(e.get("path", "")),
            "mtime": float(e.get("mtime", 0)),
            "size": int(e.get("size", 0)),
        })
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
