# File backend/embeddings.py
# Name: Keagan Weinstock
# Description: Chunking and FAISS vector store
#              for long-term memory

import faiss
import numpy as np
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from backend.config import get_embed_model_path

EMBED_MODEL = SentenceTransformer(get_embed_model_path())
VECTOR_DIR = Path("data/vectors")
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 40
CHUNK_OVERLAP = 5

def chunk_file(path: str) -> list[dict]:
    lines = Path(path).read_text().splitlines()
    chunks = []
    i = 0
    while i < len(lines):
        end = min(i + CHUNK_SIZE, len(lines))
        chunks.append({
            "path": path,
            "start": i,
            "end": end,
            "text": "\n".join(lines[i:end]),
        })
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def embed(texts: list[str]) -> np.ndarray:
    return EMBED_MODEL.encode(texts, convert_to_numpy=True).astype("float32")

def index_file(filename: str, filepath: str):
    chunks = chunk_file(filepath)
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    vectors = embed(texts)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    stem = Path(filename).stem
    faiss.write_index(index, str(VECTOR_DIR / f"{stem}.index"))
    (VECTOR_DIR / f"{stem}.meta.json").write_text(json.dumps(chunks, indent=2))

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
        chunks = json.load(open(meta_path.read_text()))

        q_vec = embed([query])
        distances, indices = index.search(q_vec, top_k)

        for dist, i in zip(distances[0], indices[0]):
            if i < len(chunks):
                all_results.append({**chunks[i], "score": float(dist)})

    all_results.sort(key=lambda x: x["score"])
    return all_results[:top_k]

