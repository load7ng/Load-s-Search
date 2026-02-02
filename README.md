# Load's Search

A fast, local search engine for your files and documents. Index folders with full-text search support for PDFs, Word documents, and text files. Perfect for personal knowledge management and document discovery.

## ✨ Features

- **🔍 Full-text search** across multiple file formats
- **📄 PDF support** with Turkish character compatibility  
- **📝 Word documents** (.docx) text extraction
- **🌐 Turkish character support** in search and content
- **🎨 Dark/Light themes** with toggle
- **⚡ Fast indexing** with optimized PDF processing
- **💾 Local-only** - no cloud, privacy-first
- **🔄 Cross-device sync** via Syncthing (optional)

## Requirements

- Python 3.8+
- (Optional) [Syncthing](https://syncthing.net/) to sync data across devices

## Install

Install dependencies:

```bash
cd "Load's Search"
pip install -r requirements.txt
```

## 🚀 Quick Start

1. **Launch the GUI:**
   ```bash
   python run_gui.py
   ```

2. **Add folders** to index using "Add folder…" button

3. **Click "Re-index"** to build your search database

4. **Start searching!** Type in the search bar to find content instantly

**Tips:**
- Use **Toggle Theme** for dark/light mode
- **Open config folder** to access your data directory
- Large PDFs (>10MB or >50 pages) are optimized for performance

## 📁 Data Folder

All app data lives in `LoadsSearch/`:

```
LoadsSearch/
├── config.json          # Your settings and folders
├── logs/                # Activity logs (synced)  
├── file_index_data/     # File metadata (synced)
└── search_index/        # Search index (local only)
```

**For Syncthing users:** Sync the entire `LoadsSearch/` folder except `search_index/` (local per device).

## 📄 Supported File Types

**Documents:** `.txt`, `.md`, `.docx`, `.pdf`, `.rst`, `.tex`, `.org`, `.adoc`, `.asciidoc`

**Data & Config:** `.json`, `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.xml`, `.csv`

**Web:** `.html`, `.htm`, `.css`, `.scss`, `.sass`, `.less`

**Code:** `.js`, `.jsx`, `.mjs`, `.ts`, `.tsx`, `.vue`, `.py`, `.pyw`, `.pyi`, `.c`, `.h`, `.cpp`, `.java`, `.kt`, `.rs`, `.go`, `.rb`, `.php`, `.swift`, `.sql`, `.sh`, `.bat`, `.ps1`, `.r`, `.R`, `.log`, `.diff`, `.patch`, `.svg`, `.graphql`

**PDF support:** Uses `pdfplumber` (primary) and `PyPDF2` (fallback) for text extraction. PDFs up to 10 MB are supported (first 50 pages for large files).

## ⚙️ Configuration

Edit `LoadsSearch/config.json` to customize:

```json
{
  "folders_to_index": [
    "C:\\Users\\You\\Documents",
    "C:\\Users\\You\\projects"
  ],
  "dark_mode": false,
  "log_terminal_history": true
}
```

## 🏗️ Development

Load's Search is built with:
- **Whoosh** - Full-text search indexing
- **Tkinter** - Cross-platform GUI  
- **pdfplumber/PyPDF2** - PDF text extraction
- **python-docx** - Word document processing

## 📜 License

MIT License - feel free to use and modify.

---

**Version 1.0** - Fast local search with PDF and Turkish support.
