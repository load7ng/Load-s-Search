"""
Activity logging (Phase 2): read shell history and append to logs/device_<hostname>_<date>.json.
Format: { "type": "command", "timestamp": "ISO", "command": "...", "cwd": "..." }
"""
import json
import os
import socket
from datetime import datetime
from pathlib import Path


def _hostname() -> str:
    try:
        return socket.gethostname() or "unknown"
    except Exception:
        return "unknown"


def _today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _log_path(logs_dir: Path) -> Path:
    return logs_dir / f"device_{_hostname()}_{_today_iso()}.json"


def _read_lines(path: Path, encoding: str = "utf-8", errors: str = "replace") -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding=encoding, errors=errors).strip().splitlines()
    except OSError:
        return []


def _shell_history_paths() -> list[Path]:
    """Paths to shell history files (newest first for dedup)."""
    home = Path.home()
    paths = []
    # Unix: .zsh_history, .bash_history
    paths.append(home / ".zsh_history")
    paths.append(home / ".bash_history")
    # Windows: PowerShell PSReadLine history
    appdata = os.environ.get("APPDATA")
    if appdata:
        paths.append(Path(appdata) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt")
    return [p for p in paths if p.exists()]


def _existing_commands(log_path: Path) -> set[str]:
    """Set of already-logged command strings (for dedup)."""
    if not log_path.exists():
        return set()
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {item.get("command", "").strip() for item in data if isinstance(item, dict)}
        return set()
    except Exception:
        return set()


def sync_terminal_history(logs_dir: Path, cwd_fallback: str = "") -> int:
    """
    Read shell history files, append new commands to logs/device_<hostname>_<date>.json.
    Returns number of new commands appended. Deduplicates by command text.
    """
    log_path = _log_path(logs_dir)
    existing = _existing_commands(log_path)
    new_entries = []
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for hist_path in _shell_history_paths():
        for line in _read_lines(hist_path):
            cmd = line.strip()
            # Skip empty and very long lines; skip if already logged
            if not cmd or len(cmd) > 2000:
                continue
            # Some shells prefix with timestamp (e.g. zsh); use last part as command for dedup
            if cmd.startswith(": ") and ":" in cmd[2:]:
                # zsh format: ": 1234567890:0;command"
                idx = cmd.find(";")
                if idx != -1:
                    cmd = cmd[idx + 1 :].strip()
            if cmd in existing:
                continue
            existing.add(cmd)
            new_entries.append({
                "type": "command",
                "timestamp": now_iso,
                "command": cmd,
                "cwd": cwd_fallback or str(Path.cwd()),
            })

    if not new_entries:
        return 0

    logs_dir.mkdir(parents=True, exist_ok=True)
    # Append to existing log or create new
    try:
        if log_path.exists():
            data = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        else:
            data = []
        data.extend(new_entries)
        log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        log_path.write_text(json.dumps(new_entries, indent=2), encoding="utf-8")
    return len(new_entries)


def load_commands_from_logs(logs_dir: Path) -> list[dict]:
    """Load all command entries from logs/*.json for indexing."""
    if not logs_dir.exists():
        return []
    entries = []
    for path in logs_dir.glob("device_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "command":
                        entries.append(item)
        except Exception:
            continue
    return entries
