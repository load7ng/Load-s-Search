"""
Launch Load's Search GUI from project root (no install).
"""
import sys
from pathlib import Path

src = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src))

from loads_search.gui import run_gui

if __name__ == "__main__":
    run_gui()
