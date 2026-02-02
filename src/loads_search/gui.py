"""
Load's Search GUI: one window, search bar, result list, open on double-click, Re-index button.
Folder selection to choose what to index. Logo and "last indexed" from recommendations.
"""
import base64
import locale
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any

# Set system encoding for proper Turkish character support
if sys.platform == "win32":
    import ctypes
    try:
        # Set console code page to UTF-8 on Windows
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except:
        pass

# Set locale for proper UTF-8 handling (important for Turkish characters)
try:
    locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')  # Windows Turkish locale
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')  # Linux/macOS Turkish locale
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, '')  # System default
        except locale.Error:
            pass  # Use default locale

# Minimal 1x1 PNG (for fallback icon when assets/logo.png is missing)
_FALLBACK_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="

# Require Whoosh at import so we fail early with a clear message
try:
    import whoosh  # noqa: F401
except ImportError:
    whoosh = None

# Debounce search while typing
_after_id = None

# Dark theme colors
DARK_THEME: Dict[str, str] = {
    'bg': '#2b2b2b',
    'fg': '#ffffff',
    'select_bg': '#404040',
    'select_fg': '#ffffff',
    'button_bg': '#404040',
    'button_fg': '#ffffff',
    'entry_bg': '#404040',
    'entry_fg': '#ffffff',
    'frame_bg': '#333333',
    'label_fg': '#cccccc',
    'disabled_fg': '#888888',
}

# Light theme colors (default)
LIGHT_THEME: Dict[str, str] = {
    'bg': '#ffffff',
    'fg': '#000000',
    'select_bg': '#0078d4',
    'select_fg': '#ffffff',
    'button_bg': '#f0f0f0',
    'button_fg': '#000000',
    'entry_bg': '#ffffff',
    'entry_fg': '#000000',
    'frame_bg': '#f8f8f8',
    'label_fg': '#000000',
    'disabled_fg': '#888888',
}


def apply_theme(root: tk.Tk, theme: Dict[str, str]) -> None:
    """Apply theme colors to root window and configure ttk styles."""
    root.configure(bg=theme['bg'])
    
    # Font for Turkish character support
    turkish_font = ("Tahoma", 9) if sys.platform == "win32" else ("Segoe UI", 9)
    
    # Configure ttk styles
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure TButton style with Turkish font
    style.configure('TButton', 
                   background=theme['button_bg'],
                   foreground=theme['button_fg'],
                   borderwidth=1,
                   focuscolor='none',
                   font=turkish_font)
    style.map('TButton',
              background=[('active', theme['select_bg'])])
    
    # Configure TEntry style with Turkish font
    style.configure('TEntry',
                   fieldbackground=theme['entry_bg'],
                   foreground=theme['entry_fg'],
                   borderwidth=1,
                   font=turkish_font)
    
    # Configure TLabel style with Turkish font
    style.configure('TLabel',
                   background=theme['bg'],
                   foreground=theme['label_fg'],
                   font=turkish_font)
    
    # Configure TFrame style
    style.configure('TFrame',
                   background=theme['frame_bg'])
    
    # Configure TLabelframe style
    style.configure('TLabelframe',
                   background=theme['frame_bg'],
                   foreground=theme['label_fg'])
    style.configure('TLabelframe.Label',
                   background=theme['frame_bg'],
                   foreground=theme['label_fg'],
                   font=turkish_font)


def _open_file(path: str) -> None:
    """Open path in system default app."""
    path = path.strip()
    if not path or not Path(path).exists():
        return
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def _open_folder(path: str) -> None:
    """Open folder in system file manager."""
    p = Path(path)
    if not p.is_dir():
        return
    path_str = str(p.resolve())
    if sys.platform == "win32":
        os.startfile(path_str)
    elif sys.platform == "darwin":
        subprocess.run(["open", path_str], check=False)
    else:
        subprocess.run(["xdg-open", path_str], check=False)


def _format_last_indexed(iso_str: str | None) -> str:
    """Turn last_indexed_iso into 'Index from 2 hours ago' or similar."""
    if not iso_str or not iso_str.strip():
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        now = datetime.now()
        delta = now - dt
        secs = max(0, int(delta.total_seconds()))
        if secs < 60:
            return "Index from just now"
        if secs < 3600:
            m = secs // 60
            return f"Index from {m} minute{'s' if m != 1 else ''} ago"
        if secs < 86400:
            h = secs // 3600
            return f"Index from {h} hour{'s' if h != 1 else ''} ago"
        d = secs // 86400
        return f"Index from {d} day{'s' if d != 1 else ''} ago"
    except Exception:
        return ""


def run_gui() -> None:
    if whoosh is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Load's Search",
            "The Whoosh library is not installed.\n\n"
            "Install it with:\n  pip install Whoosh\n\n"
            "Or install all dependencies:\n  pip install -r requirements.txt",
        )
        sys.exit(1)

    from .config import load_config, save_config
    from .paths import get_data_dir
    from .indexer import full_index, search_index, get_index

    root = tk.Tk()
    root.title("Load's Search")
    root.minsize(620, 420)
    root.geometry("750x520")

    # Load config and apply theme
    cfg = load_config()
    theme = DARK_THEME if cfg.get("dark_mode", False) else LIGHT_THEME
    apply_theme(root, theme)

    # Logo: window icon + header (from file or fallback). Keep ref on root so image isn't garbage-collected.
    root._logo_img = None  # type: ignore[attr-defined]
    _logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if _logo_path.exists():
        try:
            _raw = tk.PhotoImage(file=str(_logo_path))
            # Subsample if too large so header doesn't blow up (max 64px)
            w, h = _raw.width(), _raw.height()
            if w > 64 or h > 64:
                dx = max(1, w // 64)
                dy = max(1, h // 64)
                root._logo_img = _raw.subsample(dx, dy)  # type: ignore[attr-defined]
            else:
                root._logo_img = _raw  # type: ignore[attr-defined]
        except Exception:
            pass
    if root._logo_img is None:  # type: ignore[attr-defined]
        try:
            root._logo_img = tk.PhotoImage(data=base64.b64decode(_FALLBACK_ICON_B64), format="png")  # type: ignore[attr-defined]
        except Exception:
            pass
    if root._logo_img is not None:  # type: ignore[attr-defined]
        root.iconphoto(True, root._logo_img)  # type: ignore[attr-defined]

    status_var = tk.StringVar(value="Ready. Add folders below and click Re-index.")

    # --- Header: logo (if any) + title ---
    header = ttk.Frame(root, padding=(8, 8, 8, 4))
    header.pack(fill=tk.X)
    if root._logo_img is not None:  # type: ignore[attr-defined]
        _logo_label = ttk.Label(header, image=root._logo_img)  # type: ignore[attr-defined]
        _logo_label.pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(header, text="Load's Search", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

    # --- Folders to index (collapsible feel: frame with list + Add/Remove) ---
    folders_frame = ttk.LabelFrame(root, text="Folders to index", padding=6)
    folders_frame.pack(fill=tk.X, padx=8, pady=(4, 4))

    folders_inner = ttk.Frame(folders_frame)
    folders_inner.pack(fill=tk.X)
    folders_listbox = tk.Listbox(folders_inner, height=3, font=("Segoe UI", 9), selectmode=tk.SINGLE,
                                 bg=theme['entry_bg'], fg=theme['entry_fg'],
                                 selectbackground=theme['select_bg'], selectforeground=theme['select_fg'])
    folders_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
    folders_btns = ttk.Frame(folders_inner)
    folders_btns.pack(side=tk.RIGHT, padx=(8, 0))
    ttk.Button(folders_btns, text="Add folder…", width=12, command=lambda: _add_folder()).pack(side=tk.TOP, pady=2)
    ttk.Button(folders_btns, text="Remove", width=12, command=lambda: _remove_folder()).pack(side=tk.TOP, pady=2)

    def refresh_folders_list() -> None:
        folders_listbox.delete(0, tk.END)
        cfg = load_config()
        for p in cfg.get("folders_to_index", []):
            folders_listbox.insert(tk.END, p)

    def _add_folder() -> None:
        path = filedialog.askdirectory(title="Select folder to index")
        if not path:
            return
        path = str(Path(path).resolve())
        cfg = load_config()
        folders = list(cfg.get("folders_to_index", []))
        if path in folders:
            messagebox.showinfo("Load's Search", "That folder is already in the list.")
            return
        folders.append(path)
        cfg["folders_to_index"] = folders
        save_config(cfg)
        refresh_folders_list()
        status_var.set("Folder added. Click Re-index to update the search index.")

    def _remove_folder() -> None:
        sel = folders_listbox.curselection()
        if not sel:
            messagebox.showinfo("Load's Search", "Select a folder in the list to remove it.")
            return
        idx = int(sel[0])
        cfg = load_config()
        folders = list(cfg.get("folders_to_index", []))
        if 0 <= idx < len(folders):
            folders.pop(idx)
            cfg["folders_to_index"] = folders
            save_config(cfg)
            refresh_folders_list()
            status_var.set("Folder removed. Click Re-index to update the search index.")

    # Top: search entry
    top = ttk.Frame(root, padding=8)
    top.pack(fill=tk.X)
    
    # Font selection for Turkish character support
    fonts_to_try = [("Segoe UI", 10), ("Tahoma", 10), ("Arial", 10), ("Calibri", 10)]
    # Use Tahoma as it has better Turkish character support on Windows
    selected_font = ("Tahoma", 10) if sys.platform == "win32" else fonts_to_try[0]
    
    ttk.Label(top, text="Search:", font=selected_font).pack(side=tk.LEFT, padx=(0, 6))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(top, textvariable=search_var, width=50, font=selected_font)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
    search_entry.focus_set()

    # Results: listbox with path + snippet (height = visible rows; keep small so bottom buttons stay on screen)
    results_frame = ttk.Frame(root, padding=8)
    results_frame.pack(fill=tk.BOTH, expand=True)
    results_list = tk.Listbox(
        results_frame,
        height=10,
        font=selected_font,
        selectmode=tk.SINGLE,
        activestyle=tk.NONE,
        bg=theme['entry_bg'],
        fg=theme['entry_fg'],
        selectbackground=theme['select_bg'],
        selectforeground=theme['select_fg'],
    )
    scroll = ttk.Scrollbar(results_frame)
    results_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    results_list.config(yscrollcommand=scroll.set)
    scroll.config(command=results_list.yview)

    # Store (path, snippet, result_type, copy_text) for each list index
    result_data: list[tuple[str, str, str, str | None]] = []

    def do_search(*args: object) -> None:
        global _after_id
        if _after_id:
            root.after_cancel(_after_id)

        def run() -> None:
            q = search_var.get().strip()
            # Normalize Unicode for better Turkish character matching
            if q:
                import unicodedata
                q = unicodedata.normalize('NFC', q)
            
            result_data.clear()
            results_list.delete(0, tk.END)
            if not q:
                return
            hits = search_index(q, limit=50)
            for path, snippet, result_type, copy_text in hits:
                result_data.append((path, snippet, result_type, copy_text))
                if result_type == "command":
                    badge = "[Command]"
                    display = f"{badge}  {snippet[:80]}{'…' if len(snippet) > 80 else ''}"
                else:
                    badge = "[File]"
                    name = Path(path).name
                    display = f"{badge}  {name}  —  {path}"
                results_list.insert(tk.END, display)

        _after_id = root.after(300, run)

    search_var.trace_add("write", do_search)

    def on_double_click(event: tk.Event) -> None:
        sel = results_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(result_data):
            path, _, result_type, copy_text = result_data[idx]
            if result_type == "command" and copy_text:
                root.clipboard_clear()
                root.clipboard_append(copy_text)
                status_var.set("Command copied to clipboard.")
            else:
                _open_file(path)

    results_list.bind("<Double-Button-1>", on_double_click)

    # Bottom: status packed first (RIGHT) so buttons (LEFT) stay visible when window is narrow
    bottom = ttk.Frame(root, padding=8)
    bottom.pack(fill=tk.X)
    status_label = ttk.Label(bottom, textvariable=status_var, foreground=theme['disabled_fg'])
    status_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)
    bottom_btns = ttk.Frame(bottom)
    bottom_btns.pack(side=tk.LEFT)

    def run_reindex() -> None:
        status_var.set("Scanning files...")
        root.update_idletasks()
        try:
            cfg = load_config()
            folders = cfg.get("folders_to_index", [])
            if not folders:
                status_var.set("No folders to index. Use 'Add folder…' above.")
                messagebox.showinfo("Load's Search", "Add at least one folder using 'Add folder…' above.")
                return
            
            status_var.set("Indexing files (may take time for large PDFs)...")
            root.update_idletasks()
            
            n = full_index(cfg)
            cfg["last_indexed_iso"] = datetime.now().isoformat()
            save_config(cfg)
            ago = _format_last_indexed(cfg["last_indexed_iso"])
            status_var.set(f"Indexed {n} files. {ago}" if ago else f"Indexed {n} files. Try searching.")
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "large" in error_msg.lower():
                status_var.set("Indexing completed with some large files skipped")
                messagebox.showwarning("Load's Search", 
                    "Indexing completed, but some very large PDFs were skipped to prevent crashes.\n"
                    "Try splitting large e-books into smaller files.")
            else:
                status_var.set(f"Error: {error_msg}")
                messagebox.showerror("Load's Search", error_msg)
        else:
            do_search()

    def open_config_folder() -> None:
        _open_folder(str(get_data_dir()))

    def toggle_theme() -> None:
        """Toggle between light and dark themes."""
        cfg = load_config()
        current_dark = cfg.get("dark_mode", False)
        new_dark = not current_dark
        cfg["dark_mode"] = new_dark
        save_config(cfg)
        
        # Apply new theme
        new_theme = DARK_THEME if new_dark else LIGHT_THEME
        apply_theme(root, new_theme)
        
        # Update listbox colors
        folders_listbox.configure(bg=new_theme['entry_bg'], fg=new_theme['entry_fg'],
                                  selectbackground=new_theme['select_bg'], selectforeground=new_theme['select_fg'])
        results_list.configure(bg=new_theme['entry_bg'], fg=new_theme['entry_fg'],
                              selectbackground=new_theme['select_bg'], selectforeground=new_theme['select_fg'])
        status_label.configure(foreground=new_theme['disabled_fg'])
        
        status_var.set(f"Switched to {'dark' if new_dark else 'light'} mode.")

    reindex_btn = ttk.Button(bottom_btns, text="Re-index", command=run_reindex)
    reindex_btn.pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(bottom_btns, text="Toggle Theme", command=toggle_theme, width=12).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(bottom_btns, text="Open config folder", command=open_config_folder, width=16).pack(side=tk.LEFT, padx=(0, 12))

    # Load folders list and set initial status
    refresh_folders_list()
    cfg = load_config()
    if get_index() is not None and cfg.get("last_indexed_iso"):
        status_var.set(_format_last_indexed(cfg["last_indexed_iso"]) or "Ready. Search or Re-index.")
    elif get_index() is None:
        status_var.set("No index yet. Add folders above and click Re-index.")

    root.mainloop()


if __name__ == "__main__":
    run_gui()
