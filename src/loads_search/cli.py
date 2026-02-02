"""
CLI for Load's Search: ensure dirs + config, or launch GUI.
"""
import sys


def main() -> int:
    args = sys.argv[1:]
    if args and args[0].lower() in ("--config", "-c"):
        from .config import ensure_data_dirs, load_config
        data_dir = ensure_data_dirs()
        print(f"Data dir: {data_dir}")
        cfg = load_config()
        print(f"Config: {len(cfg.get('folders_to_index', []))} folders to index")
        return 0

    # Default: launch GUI
    from .gui import run_gui
    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
