# File: backend/api.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              FastAPI to call in the frontend

import shutil
import psutil
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.responses import FileResponse

from backend.llm import generate_with_stream, llm_stream
from backend.skills import build_skill_index
from backend.embeddings import index_file
from backend.config import get_hardware_config
from typing import List
from pathlib import Path

app = FastAPI()

HISTORY_FILE = Path("data/conversations.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

WORKSPACE_DIR = Path("data/workspace")
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def load_conversations():
    if HISTORY_FILE.exists():
        return json.load(open(HISTORY_FILE))
    return []


def save_conversations(data):
    HISTORY_FILE.write_text(json.dumps(data, indent=2))


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class SaveHistoryRequest(BaseModel):
    conversations: list


@app.post("/chat")
def chat(req: ChatRequest):
    def stream():
        try:
            final_prompt = None
            for event in generate_with_stream(req.messages):
                if event["type"] == "tool":
                    yield f"data: {json.dumps({'tool': event['name'], 'args': event['args']})}\n\n"
                elif event["type"] == "final":
                    final_prompt = event["prompt"]

            if final_prompt:
                for token in llm_stream(final_prompt):
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/history")
def get_history():
    return load_conversations()


@app.post("/history")
def post_history(data: SaveHistoryRequest):
    save_conversations(data.conversations)
    return {"ok": True}


@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    index_file(file.filename, str(dest))
    return {"filename": file.filename, "path": str(dest)}


@app.get("/uploads")
def list_uploads():
    if not UPLOAD_DIR.exists():
        return []
    return [f.name for f in UPLOAD_DIR.iterdir() if f.is_file()]


@app.delete("/uploads/{filename}")
def delete_upload(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        return {"ok": False, "error": "File not found"}
    file_path.unlink()

    stem = Path(filename).stem
    index_path = Path("data/vectors") / f"{stem}.index"
    meta_path = Path("data/vectors") / f"{stem}.meta.json"
    if index_path.exists(): index_path.unlink()
    if meta_path.exists(): meta_path.unlink()

    return {"ok": True}


@app.get("/stats")
def get_stats():
    mem = psutil.virtual_memory()
    hw = get_hardware_config()
    return {
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "tier": hw["tier"],
        "n_ctx": hw["n_ctx"],
    }


@app.post("/skills/rebuild")
def rebuild_skills():
    build_skill_index()
    return {"ok": True}


@app.get("/workspace")
def list_workspace():
    if not WORKSPACE_DIR.exists():
        return []
    return [
        {
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "ext": f.suffix.lower(),
        }
        for f in sorted(WORKSPACE_DIR.iterdir()) if f.is_file()
    ]


@app.get("/workspace/{filename}")
def download_workspace_file(filename: str):
    file_path = WORKSPACE_DIR / filename
    if not file_path.exists():
        return {"error": "File not found"}
    return FileResponse(path=str(file_path), filename=filename)


@app.delete("/workspace/{filename}")
def delete_workspace_file(filename: str):
    file_path = WORKSPACE_DIR / filename
    if not file_path.exists():
        return {"ok": False, "error": "File not found"}
    file_path.unlink()
    return {"ok": True}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
