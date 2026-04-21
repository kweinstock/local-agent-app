# Local LLM Agent — Phase 1 Planner

## Overview
Build a fully offline, low-memory LLM agent with:
- Chat + UI
- Tool usage (code + files)
- Long-term memory
- Dynamic skills
- Hardware-aware model selection

---

## Build Order
Core Chat → Tools → File Handling → Memory → Skills → Hardware Awareness → Polish

---

## Step 1 — Local Model Setup (Complete)
- Install llama.cpp
- Download GGUF model (Phi-3 Mini Q4 recommended)
- Run model via CLI
- Wrap in Python

**Goal:** Model responds locally

---

## Step 2 — Backend API (FastAPI) (Complete)
- Create `/chat` endpoint
- Connect to model wrapper

**Goal:** API returns responses

---

## Step 3 — Chat UI (Complete)
- Simple React interface
- Input + chat history
- Create `/history` endpoint
- Markdown rendering

**Goal:** Usable chat interface

---

## Step 4 — Agent + Tools
- Implement agent loop
- Add tools:
  - read_file(path)
  - run_python(code)

**Goal:** Model can execute actions

---

## Step 5 — File Handling
- Load files into prompt
- Handle large files (basic chunking)

**Goal:** Code understanding + editing

---

## Step 6 — Long-Term Memory
- Setup FAISS
- Store important facts
- Retrieve relevant context

**Goal:** Persistent memory

---

## Step 7 — Dynamic Skills
- Create skills folder
- Tag + retrieve relevant skills

**Goal:** Smarter responses without bigger models

---

## Step 8 — Hardware-Aware Models
- Detect RAM/CPU
- Assign tier (low/medium/high)
- Select model accordingly

**Goal:** Runs efficiently on any machine

---

## Step 9 — Prompt Builder
Structure:
SYSTEM
SKILLS
MEMORY
USER

**Goal:** Stable, consistent outputs

---

## Step 10 — Polish
- Streaming responses
- Better UI
- Error handling
- Settings (performance modes)

---

## Notes
- Keep everything offline
- Keep prompts small
- Don’t overengineer early
- Test each step before moving on

---

## Final Result
- Local coding assistant
- File-aware agent
- Tool-using system
- Memory + skills enabled
- Hardware adaptive

