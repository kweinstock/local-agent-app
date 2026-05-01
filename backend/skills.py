# File: backend/skills.py
# Name: Keagan Weinstock
# Description: Skill retrieval, injects relevant
#              context into the prompt

import os
from pathlib import Path
from backend.embeddings import embed, get_file_language
import faiss
import numpy as np
import json

SKILLS_DIR = Path("backend/skills")
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

SKILLS_BASE_DIR = Path("data/skills")
SKILLS_BASE_DIR.mkdir(parents=True, exist_ok=True)

SKILL_INDEX_PATH = Path(os.path.join(SKILLS_BASE_DIR, "skill_index.json"))
SKILL_META_PATH = Path(os.path.join(SKILLS_BASE_DIR, "skill_meta.json"))

UPLOAD_DIR = Path("data/uploads")


def load_skills() -> list[dict]:
    skills = []
    for f in SKILLS_DIR.glob("*.md"):
        skills.append({
            "name": f.stem,
            "content": f.read_text(encoding="utf-8"),
        })
    return skills


def build_skill_index():
    skills = load_skills()
    if not skills:
        return
    texts = [s["content"] for s in skills]
    vectors = embed(texts)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(SKILL_INDEX_PATH))
    SKILL_META_PATH.write_text(json.dumps(skills, indent=2))


def get_skill_by_language(language: str) -> dict | None:
    if not SKILL_META_PATH.exists():
        return None
    meta = json.loads(SKILL_META_PATH.read_text())
    for skill in meta:
        if skill["name"].lower() == language.lower():
            return skill
    return None


def get_languages_from_uploads(filenames: list[str]) -> list[str]:
    languages = []
    for filename in filenames:
        lang = get_file_language(filename)
        if lang and lang not in languages:
            languages.append(lang)
    return languages


def get_relevant_skills(query: str, top_k: int = 2, threshold: float = 1.0) -> list[dict]:
    if not SKILL_INDEX_PATH.exists():
        build_skill_index()
    if not SKILL_INDEX_PATH.exists():
        return []

    index = faiss.read_index(str(SKILL_INDEX_PATH))
    meta = json.loads(SKILL_META_PATH.read_text())
    q_vectors = embed([query])
    distances, indices = index.search(q_vectors, top_k)

    results = []
    seen = set()
    for dist, i in zip(distances[0], indices[0]):
        if i < len(meta) and dist < threshold:
            skill = meta[i]
            if skill["name"] not in seen:
                results.append(skill)
                seen.add(skill["name"])
            results.append(meta[i])
    return results


def get_skills_for_context(query: str, uploaded_filenames: list[str]) -> list[dict]:
    seen = set()
    results = []

    languages = get_languages_from_uploads(uploaded_filenames)
    for lang in languages:
        skill = get_skill_by_language(lang)
        if skill and skill["name"] not in seen:
            results.append(skill)
            seen.add(skill["name"])

    query_skills = get_relevant_skills(query)
    for skill in query_skills:
        if skill["name"] not in seen:
            results.append(skill)
            seen.add(skill["name"])

    return results


def format_skills(skills: list[dict]) -> str:
    if not skills:
        return ""
    parts = [s["content"] for s in skills]
    return "\n\n---\n\n".join(parts)
