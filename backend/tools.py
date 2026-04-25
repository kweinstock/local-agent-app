# File: backend/tools.py
# Name: Keagan Weinstock
# Description: Tool registry, add new tools here,
#              nothing else needs to change

import subprocess
import json
import sys
from pathlib import Path
from backend.embeddings import search_all

UPLOAD_DIR = Path("data/uploads")


# Tool implementations
def read_file(path: str, start_line: int = 0, end_line: int = None) -> str:
    try:
        resolved = UPLOAD_DIR / Path(path).name
        lines = resolved.read_text().splitlines()
        chunk = lines[start_line:end_line] if end_line else lines[start_line:]
        total = len(lines)
        result = "\n".join(chunk)
        return f"[Lines {start_line}-{end_line or total} of {total}]\n{result}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def run_python(code: str):
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout or result.stderr
        return output.strip() or "No output."
    except subprocess.TimeoutExpired:
        return "Error: code timed out after 10 seconds."
    except Exception as e:
        return f"Error running code: {e}"


def search_context(query: str) -> str:
    results = search_all(query, top_k=3)
    if not results:
        return "No relevant context found in uploaded files."
    out = []
    for r in results:
        filename = Path(r["path"]).name
        out.append(
            f"File: {filename} | Lines {r['start']}-{r['end']}\n{r['text']}"
        )
    return "\n\n---\n\n".join(out)


TOOLS = {
    "read_file": {
        "fn": read_file,
        "description": (
            "Read lines from an uploaded file. "
            "Args: path (string), start_line (int, optional), end_line (int, optional). "
            "Use search_context first to find the relevant line range."
        ),
    },
    "run_python": {
        "fn": run_python,
        "description": (
            'Execute Python code and return stdout. '
            'Args: {"code": "string"}. '
            'IMPORTANT: always use print() to output results, '
            'return values are not shown. '
            'Example: TOOL: run_python\nARGS: {"code": "print(sorted([3,1,2]))"}'
        ),
    },
    "search_context": {
        "fn": search_context,
        "description": (
            "Search uploaded files for content relevant to a query using vector similarity. "
            "Returns the most relevant chunks with their line ranges. "
            "Args: query (string). Use this before read_file to find where to look."
        ),
    },
}


def get_tool_descriptions() -> str:
    return "\n".join(f"- {name}: {meta['description']}" for name, meta in TOOLS.items())


def call_tool(name: str, args: dict):
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    return TOOLS[name]["fn"](**args)