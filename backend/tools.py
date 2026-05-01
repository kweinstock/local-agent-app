# File: backend/tools.py
# Name: Keagan Weinstock
# Description: Tool registry, add new tools here,
#              nothing else needs to change

import subprocess
import json
import sys
import re
from pathlib import Path
from pypdf import PdfReader
import nbformat
import pandas as pd
from backend.embeddings import search_all, get_file_metadata, index_file

WORKSPACE_DIR = Path("data/workspace")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALL_DIRS = [UPLOAD_DIR, WORKSPACE_DIR]


# Helpers
def _resolve_file(filename: str) -> Path | None:
    name = Path(filename).name
    for d in ALL_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def _format_code_chunk(path: Path, start: int, end: int) -> str:
    try:
        lines = path.read_text(errors="replace").splitlines()
        total = len(lines)
        chunk = lines[start:end] if end else lines[start:]
        return f"[Lines {start}-{end or total} of {total}]\n" + "\n".join(chunk)
    except Exception as e:
        return f"Error reading {path}: {e}"


def _format_pdf_chunk(path: Path, page: int) -> str:
    try:
        reader = PdfReader(str(path))
        if page < 1 or page > len(reader.pages):
            return f"Page {page} out of range. Document has {len(reader.pages)} pages."
        text = reader.pages[page - 1].extract_text() or ""
        return f"[Page {page} of {len(reader.pages)}]\n{text.strip()}"
    except Exception as e:
        return f"Error reading PDF {path}: {e}"


def _format_ipynb_chunk(path: Path, cell_index: int) -> str:
    try:
        nb = nbformat.read(open(str(path)), as_version=4)
        if cell_index < 0 or cell_index >= len(nb.cells):
            return f"Cell {cell_index} out of range. Notebook has {len(nb.cells)} cells."
        cell = nb.cells[cell_index]
        return f"[Cell {cell_index} - {cell.cell_type}]\n{cell.source.strip()}"
    except Exception as e:
        return f"Error reading notebook {path}: {e}"


def _format_csv_chunk(path: Path) -> str:
    try:
        df = pd.read_csv(str(path))
        return (
            f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
            f"Columns: {', '.join(df.columns)}\n\n"
            f"Preview:\n{df.head(10).to_string(index=False)}"
        )
    except Exception as e:
        return f"Error reading CSV {path}: {e}"


# Tool implementations
def read_file(path: str = None, filename: str = None, start_line: int = 0,
              end_line: int = None, page: int = None, cell_index: int = None) -> str:
    resolved = _resolve_file(path or filename or "")
    if not resolved:
        return f"File not found: {path or filename}. Use list_files to see available files."

    ext = resolved.suffix.lower()

    if ext == ".pdf":
        return _format_pdf_chunk(resolved, page or 1)
    if ext == ".ipynb":
        return _format_ipynb_chunk(resolved, cell_index if cell_index is not None else 0)
    if ext == ".csv":
        return _format_csv_chunk(resolved)
    return _format_code_chunk(resolved, start_line, end_line)


def list_files() -> str:
    lines = []
    for d, label in [(UPLOAD_DIR, "uploaded"), (WORKSPACE_DIR, "workspace")]:
        if not d.exists():
            continue
        files = [f for f in sorted(d.iterdir()) if f.is_file()]
        for f in files:
            meta = get_file_metadata(f.name) if label == "uploaded" else {}
            category = meta.get("category", "code")
            language = meta.get("language", "")
            lang_str = f" [{language}]" if language else ""

            if category == "document":
                detail = f"{meta.get('total_pages', '?')} pages"
            elif category == "notebook":
                detail = f"{meta.get('total_cells', '?')} cells"
            elif category == "data":
                detail = f"{meta.get('row_count', '?')} rows x {meta.get('col_count', '?')} cols"
            else:
                detail = f"{meta.get('line_count', '?')} lines" if meta else f"{f.stat().st_size} bytes"

            size_kb = round(f.stat().st_size / 1024, 1)
            lines.append(f"- {f.name}{lang_str} [{label}] | {category} | {detail} | {size_kb}kb")

    return "Files:\n" + "\n".join(lines) if lines else "No files available."


def run_python(code: str) -> str:
    code = code.replace("\\n", "\n").replace("\\t", "\t")
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return f"EXECUTION FAILED:\n{result.stderr.strip()}\nFix the error and retry."
        output = result.stdout.strip()
        return output or "No output. Add print() to show results."
    except subprocess.TimeoutExpired:
        return "EXECUTION FAILED: timed out after 10 seconds. Simplify the code."
    except Exception as e:
        return f"EXECUTION FAILED: {e}"


def search_context(query: str) -> str:
    results = search_all(query, top_k=3)
    if not results:
        return "No relevant context found in uploaded files."
    out = []
    for r in results:
        filename = Path(r["path"]).name
        category = r.get("category", "code")

        if category == "document" and "page" in r:
            header = f"File: {filename} | Page {r['page']}"
        elif category == "notebook" and "cell_index" in r:
            header = f"File: {filename} | Cell {r['cell_index']} ({r.get('cell_type', 'code')})"
        elif category == "data":
            header = f"File: {filename} | CSV data"
        else:
            header = f"File: {filename} | Lines {r.get('start', '?')}-{r.get('end', '?')}"

        out.append(f"{header}\n{r['text']}")
    return "\n\n---\n\n".join(out)


def write_file(filename: str, content: str) -> str:
    try:
        content = content.replace("\\n", "\n")
        content = content.replace("\\t", "\t")
        content = content.replace("\\'", "'")
        content = content.replace('\\"', '"')

        dest = WORKSPACE_DIR / Path(filename).name
        dest.write_text(content, encoding="utf-8")

        # Index the file so search_context and read_file can find it
        index_file(dest.name, str(dest))

        return f"File saved: {dest.name} ({len(content.splitlines())} lines)"
    except Exception as e:
        return f"Error writing file: {e}"


def search_files(query: str, filename: str = None) -> str:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []

    if filename:
        resolved = _resolve_file(filename)
        files = [resolved] if resolved else []
    else:
        files = []
        for d in ALL_DIRS:
            if d.exists():
                files.extend(d.iterdir())

    for filepath in files:
        if not filepath or not filepath.is_file():
            continue
        ext = filepath.suffix.lower()
        if ext in (".pdf", ".csv"):
            continue
        try:
            lines = filepath.read_text(errors="replace").splitlines()
            for i, line in enumerate(lines):
                if pattern.search(line):
                    results.append(f"{filepath.name}:{i + 1}: {line.strip()}")
        except Exception:
            continue

    if not results:
        return f"No matches found for '{query}'."
    if len(results) > 30:
        results = results[:30]
        results.append("... truncated to 30 results.")
    return "\n".join(results)


TOOLS = {
    "read_file": {
        "fn": read_file,
        "description": (
            "Read content from an uploaded or workspace file. "
            "For code files: args: path (string), start_line (int), end_line (int). "
            "For PDFs: args: path (string), page (int) — reads one page at a time. "
            "For notebooks: args: path (string), cell_index (int) — reads one cell. "
            "For CSVs: args: path (string) — returns shape, columns, and preview. "
            "Use list_files to see all available files. Use search_context first to find what to read."
        ),
    },
    "list_files": {
        "fn": list_files,
        "description": (
            "List all available files — both uploaded and workspace files. "
            "Call this when the user asks about files, their project, or workspace. "
            "No args required."
        ),
    },
    "run_python": {
        "fn": run_python,
        "description": (
            "Execute Python code and return stdout. "
            "Args: {\"code\": \"string\"}. "
            "Always use print() to output results. "
            "For CSV analysis, use pandas — the file is at data/uploads/<filename>. "
            "For workspace files use data/workspace/<filename>."
        ),
    },
    "search_context": {
        "fn": search_context,
        "description": (
            "Search uploaded and workspace files for content relevant to a query using vector similarity. "
            "Returns relevant chunks with location info (lines, pages, or cells). "
            "Args: query (string). Use this before read_file to find where to look."
        ),
    },
    "write_file": {
        "fn": write_file,
        "description": (
            "Create or overwrite a file in the workspace. "
            "Args: filename (string), content (string). "
            "IMPORTANT: Use this exact format when calling write_file:\n"
            "TOOL: write_file\n"
            "FILENAME: example.py\n"
            "```python\n"
            "<complete file content here>\n"
            "```\n"
            "Never put file content in ARGS JSON. Always include complete file content. "
            "Use double quotes in Python strings to avoid quote conflicts. "
            "The file will be readable and downloadable from the UI."
        ),
    },
    "search_files": {
        "fn": search_files,
        "description": (
            "Search uploaded and workspace files for a symbol, function name, or pattern. "
            "Args: query (string), filename (string, optional). "
            "Use search_context for semantic search, use search_files for exact symbol search."
        ),
    },
}


def get_tool_descriptions() -> str:
    return "\n".join(f"- {name}: {meta['description']}" for name, meta in TOOLS.items())


def call_tool(name: str, args: dict):
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    return TOOLS[name]["fn"](**args)
