# Local LLM Agent App

A fully local AI assistant with a FastAPI backend and React frontend.
Runs entirely offline using a quantized GGUF model via `llama.cpp`.

## Features

* Local LLM (no internet required after setup)
* FastAPI backend
* React chat UI (Vite + TypeScript)

## Installation
### 1. Clone the repo
```
git clone https://github.com/YOUR_USERNAME/local-agent-app.git
cd local-agent-app
```

## Model Setup

This project uses a **GGUF quantized model**.

### Download a model (example):

* `microsoft/Phi-3-mini-4k-instruct-gguf`

Place the file in:

```
models/
```

Example:

```
models/phi3-mini-q4.gguf
```

> Models are NOT included in the repo (too large)

## Backend Setup (FastAPI)
### 1. Create virtual environment (recommended)

```
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run backend
```
python backend/api.py
```
Backend runs on:
```
http://127.0.0.1:8000
```

## Frontend Setup (React + Vite)
### 1. Navigate to frontend
```
cd frontend
```

### 2. Install dependencies
```
npm install
```

### 3. Run dev server
```
npm run dev
```

Frontend runs on:
```
http://localhost:5173
```


## Connecting Frontend ↔ Backend

Make sure your API URL is set correctly:

```
http://127.0.0.1:8000/chat
```

CORS is already enabled in the backend.


## Usage

1. Start backend
2. Start frontend
3. Open browser at:

```
http://localhost:5173
```

## Requirements

* Python 3.10+
* Node.js 18+
* 4GB RAM minimum (for small models)
* CPU-only supported (GPU optional)

## License

MIT