# File backend/embeddings.py
# Name: Keagan Weinstock
# Description: Chunking and FAISS vector store
#              for long-term memory

import faiss
import numpy as np
import json
import nbformat
import pandas as pd
from pypdf import PdfReader
from docx import Document
from pathlib import Path
from sentence_transformers import SentenceTransformer
from backend.config import get_embed_model_path

EMBED_MODEL = SentenceTransformer(get_embed_model_path())
VECTOR_DIR = Path("data/vectors")
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 40
CHUNK_OVERLAP = 5

EXT_TO_LANGUAGE = {
    ".py": "python",
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript",
    ".java": "java",
    ".cs": "csharp",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    ".c": "c", ".h": "c",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
}

EXT_TO_CATEGORY = {
    ".py": "code", ".ts": "code", ".tsx": "code",
    ".js": "code", ".jsx": "code", ".cs": "code",
    ".java": "code", ".cpp": "code", ".cc": "code",
    ".cxx": "code", ".c": "code", ".h": "code",
    ".html": "code", ".css": "code", ".json": "code",
    ".yaml": "code", ".toml": "code", ".md": "code",
    ".ipynb": "notebook",
    ".pdf": "document", ".docx": "document",
    ".csv": "data",
}


def detect_language(filename: str) -> str:
    return EXT_TO_LANGUAGE.get(Path(filename).suffix.lower())


def detect_category(filename: str) -> str:
    return EXT_TO_CATEGORY.get(Path(filename).suffix.lower(), "code")


# Parsers
def parse_text (path: str) -> list[dict]:
    language = detect_language(path)
    category = detect_category(path)
    lines = Path(path).read_text(errors="replace").splitlines()
    chunks = []
    i = 0
    while i < len(lines):
        end = min(i + CHUNK_SIZE, len(lines))
        chunks.append({
            "path": path,
            "start": i,
            "end": end,
            "text": "\n".join(lines[i:end]),
            "language": language,
            "category": category,
            "file_type": Path(path).suffix.lower(),
            "line_count": len(lines),
        })
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def parse_pdf(path: str) -> list[dict]:
    reader = PdfReader(path)
    chunks = []
    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            text = text.strip()
        except Exception:
            text = ""

        # skip image-only pages
        if not text:
            continue

        chunks.append({
            "path": path,
            "page": page_num + 1,
            "total_pages": len(reader.pages),
            "text": text,
            "language": None,
            "category": "document",
            "file_type": ".pdf",
        })
    return chunks


def parse_docx(path: str) -> list[dict]:
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    chunks = []
    i = 0
    while i < len(paragraphs):
        end = min(i + CHUNK_SIZE, len(paragraphs))
        chunks.append({
            "path": path,
            "start": i,
            "end": end,
            "text": "\n".join(paragraphs[i:end]),
            "language": None,
            "category": "document",
            "file_type": ".docx",
            "paragraph_count": len(paragraphs),
        })
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def parse_csv(path: str) -> list[dict]:
    try:
        df = pd.read_csv(path)
        shape = df.shape
        columns = list(df.columns)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        preview = df.head(5).to_string(index=False)
        sample_stats = df.describe(include='all').to_string()

        text = (
            f"CSV File: {Path(path).name}\n"
            f"Shape: {shape[0]} rows x {shape[1]} columns\n"
            f"Columns: {', '.join(columns)}\n"
            f"Types:\n{json.dumps(dtypes, indent=2)}\n\n"
            f"Preview (first 5 rows):\n{preview}\n\n"
            f"Stats:\n{sample_stats}"
        )
        return [{
            "path": path,
            "text": text,
            "language": None,
            "category": "data",
            "file_type": ".csv",
            "row_count": shape[0],
            "col_count": shape[1],
            "columns": columns,
        }]
    except Exception as e:
        return [{
            "path": path,
            "text": f"CSV parse error: {e}",
            "language": None,
            "category": "data",
            "file_type": ".csv",
        }]



def parse_ipynb(path: str) -> list[dict]:
    nb = nbformat.read(open(path), as_version=4)
    chunks = []
    for i, cell in enumerate(nb.cells):
        source = cell.source.strip()
        if not source:
            continue
        cell_type = cell.cell_type  # Code or Markdown
        chunks.append({
            "path": path,
            "cell_index": i,
            "cell_type": cell_type,
            "text": f"[Cell {i} - {cell_type}]\n{source}",
            "language": "python" if cell_type == "code" else "markdown",
            "category": "notebook",
            "file_type": ".ipynb",
            "total_cells": len(nb.cells),
        })
    return chunks


# Router
def parse_file(path: str) -> list[dict]:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    elif ext == ".docx":
        return parse_docx(path)
    elif ext == ".csv":
        return parse_csv(path)
    elif ext == ".ipynb":
        return parse_ipynb(path)
    else:
        return parse_text(path)


# Indexing
def embed(texts: list[str]) -> np.ndarray:
    return EMBED_MODEL.encode(texts, convert_to_numpy=True).astype("float32")


def index_file(filename: str, filepath: str):
    chunks = parse_file(filepath)
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    vectors = embed(texts)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    stem = Path(filename).stem
    faiss.write_index(index, str(VECTOR_DIR / f"{stem}.index"))
    (VECTOR_DIR / f"{stem}.meta.json").write_text(json.dumps(chunks, indent=2))


def get_file_language(filename: str) -> str | None:
    stem = Path(filename).stem
    meta_path = VECTOR_DIR / f"{stem}.meta.json"
    if not meta_path.exists():
        return None
    with open(meta_path, "r") as f:
        chunks = json.load(f)
    if chunks:
        return chunks[0].get("language")
    return None


def get_file_metadata(filename: str) -> dict:
    stem = Path(filename).stem
    meta_path = VECTOR_DIR / f"{stem}.meta.json"
    if not meta_path.exists():
        return {}
    with open(meta_path, "r") as f:
        chunks = json.load(f)
    if not chunks:
        return {}
    first = chunks[0]
    return {
        "language": first.get("language"),
        "category": first.get("category"),
        "file_type": first.get("file_type"),
        "chunk_count": len(chunks),
        "total_pages": first.get("total_pages"),
        "row_count": first.get("row_count"),
        "col_count": first.get("col_count"),
        "columns": first.get("columns"),
        "total_cells": first.get("total_cells"),
        "line_count": first.get("line_count"),
    }


# Search
def search(query: str, filename: str, top_k: int = 3) -> list[dict]:
    stem = Path(filename).stem
    index_path = VECTOR_DIR / f"{stem}.index"
    meta_path = VECTOR_DIR / f"{stem}.meta.json"

    if not index_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    chunks = json.load(open(meta_path.read_text()))

    q_vec = embed([query])
    _, indices = index.search(q_vec, top_k)

    return [chunks[i] for i in indices[0] if i < len(chunks)]


def search_all(query: str, top_k: int = 3) -> list[dict]:
    all_results = []
    for index_file_path in VECTOR_DIR.glob("*.index"):
        stem = index_file_path.stem
        meta_path = VECTOR_DIR / f"{stem}.meta.json"
        if not meta_path.exists():
            continue

        index = faiss.read_index(str(index_file_path))
        chunks = json.loads(meta_path.read_text())

        q_vec = embed([query])
        distances, indices = index.search(q_vec, top_k)

        for dist, i in zip(distances[0], indices[0]):
            if i < len(chunks):
                all_results.append({**chunks[i], "score": float(dist)})

    all_results.sort(key=lambda x: x["score"])
    return all_results[:top_k]
