"""
File crawler: scan configured folders with excludes and size limits.
Yields file metadata (path, mtime, size) for indexable text files only.
"""
from pathlib import Path
from typing import Any, Iterator

# Extensions we index (text content). Used by crawl() — not just .txt.
# If you only see .txt after Re-index, delete src/loads_search/__pycache__ and run again.
INDEXABLE_EXTENSIONS = frozenset({
    # Documents & notes
    ".txt", ".md", ".rst", ".tex", ".latex", ".org", ".adoc", ".asciidoc", ".docx", ".pdf",
    # Data & config
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".xml", ".csv",
    # Web
    ".html", ".htm", ".xhtml", ".css", ".scss", ".sass", ".less",
    # JavaScript / TypeScript
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue",
    # Python
    ".py", ".pyw", ".pyi",
    # Other languages (common text-based source)
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".java", ".kt", ".kts", ".rs",
    ".go", ".r", ".R", ".rb", ".php", ".swift", ".sql", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".rq", ".sparql",
    # Other
    ".log", ".diff", ".patch", ".svg", ".graphql", ".gql",
})

# Extensions that often exceed 512 KB; use a higher size limit so they're not skipped
LARGE_FILE_EXTENSIONS = frozenset({".docx", ".pdf"})
LARGE_FILE_MAX_KB = 10 * 1024  # 10 MB for .docx, .pdf (more conservative for e-books)


def crawl(
    folders: list[str],
    exclude_patterns: list[str],
    max_file_size_kb: int,
) -> Iterator[dict[str, Any]]:
    """
    Walk folders and yield one dict per file: path (str), mtime (iso), size (int).
    Skips dirs whose name is in exclude_patterns, files over max_file_size_kb, non-indexable extensions.
    """
    max_bytes = max_file_size_kb * 1024
    exclude_set = {p.strip().lower() for p in exclude_patterns if p}

    for folder in folders:
        root = Path(folder)
        if not root.is_dir():
            continue
        try:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in INDEXABLE_EXTENSIONS:
                    continue
                # Skip if any parent dir name matches exclude
                skip = False
                for part in path.relative_to(root).parts:
                    if part.lower() in exclude_set:
                        skip = True
                        break
                if skip:
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                limit = LARGE_FILE_MAX_KB * 1024 if path.suffix.lower() in LARGE_FILE_EXTENSIONS else max_bytes
                if stat.st_size > limit:
                    continue
                yield {
                    "path": str(path.resolve()),
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
        except (PermissionError, OSError):
            continue
