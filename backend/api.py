# File: backend/api.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              FastAPI to call in the frontend

import shutil
import psutil
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.llm import generate
from typing import List
from pathlib import Path
import json
from backend.embeddings import index_file

app = FastAPI()

HISTORY_FILE = Path("data/conversations.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def load_conversations():
    if HISTORY_FILE.exists():
        return json.load(open(HISTORY_FILE))
    return []

def save_conversations(data):
    HISTORY_FILE.write_text(json.dumps(data, indent=2))

# Message schema
class Message(BaseModel):
    role: str
    content: str

# Request schema
class ChatRequest(BaseModel):
    messages: List[Message]

# Response schema
class ChatResponse(BaseModel):
    response: str

# History schema
class SaveHistoryRequest(BaseModel):
    conversations: list


# /chat endpoint
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    response = generate(req.messages)
    return ChatResponse(response=response)

# /history endpoint
@app.get("/history")
def get_history():
    return load_conversations()

@app.post("/history")
def post_history(data: SaveHistoryRequest):
    save_conversations(data.conversations)
    return {"ok": True}

# /upload endpoint
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

# /stats endpoint
@app.get("/stats")
def get_stats():
    mem = psutil.virtual_memory()
    return {
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
