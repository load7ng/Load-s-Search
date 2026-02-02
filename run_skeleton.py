"""
Run Load's Search from project root (no install).
Launches the GUI by default.
"""
import sys
from pathlib import Path

# Allow running without installing: add src to path
src = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src))

from loads_search.cli import main

if __name__ == "__main__":
    sys.exit(main())
