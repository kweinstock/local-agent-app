# Local Coding Assistant Tools Planner - Phase 3

## 1. File Type Support
Expand `read_file` and `index_file` to handle:

**Code files** (already work, just need skills):
- `.py`, `.ts`, `.tsx`, `.js`, `.jsx`
- `.cs`, `.java`, `.cpp`, `.c`, `.h`
- `.html`, `.css`, `.json`, `.yaml`, `.toml`, `.md`

**Rich files (need new parsers):**
- `.ipynb` — extract cells (code + markdown separately)
- `.pdf` — extract text per page
- `.docx` — extract paragraphs
- `.csv` — preview + shape info

**Metadata to store per file:**
- detected language
- file type category (code, notebook, document, data)
- line count / page count

---

## 2. New Tools

**`list_files`**
- Show all uploaded files with type, size, language
- Model calls this first when user says "look at my project"

**`write_file`**
- Create or overwrite a file in workspace
- Args: filename, content
- Saves to `data/workspace/`

**`search_files`**
- Search across all uploaded files for a symbol, function, pattern
- Args: query, optional filename filter

**`run_code`**
- Replace `run_python` with language-aware execution
- Detect language from file extension or explicit arg
- Support: Python, JavaScript (node), TypeScript (ts-node)
- C, C++, C#, Java — compile then run

---

## 3. File Save from UI

**Backend:**
- `GET /workspace` — list created files
- `GET /workspace/{filename}` — download file
- `DELETE /workspace/{filename}` — delete file

**Frontend:**
- Download button on assistant messages that contain code blocks
- Workspace panel in sidebar alongside uploaded files
- Save button that calls `write_file` tool directly

---

## 4. Language Skills (Complete)

One `.md` skill file per language:

**`typescript.md`** — types, interfaces, async/await, imports  
**`javascript.md`** — modern ES6+, avoid common pitfalls  
**`csharp.md`** — classes, LINQ, async patterns, namespaces  
**`java.md`** — OOP patterns, streams, exceptions  
**`cpp.md`** — memory management, pointers, RAII  
**`c.md`** — manual memory, structs, header files  
**`html.md`** — semantic markup, accessibility  

**Skill matching improvement:**
- Tag each skill with file extensions
- When a file is uploaded, force-match its language skill
- Inject matched skill even if query text doesn't trigger it

---

## 5. Language Detection

On file upload in `embeddings.py`:
- Detect language from extension
- Store in chunk metadata
- Pass to system prompt as: `Working language: TypeScript`

On message in `llm.py`:
- Scan recent convo for uploaded file context
- Inject detected language into prompt header
- Lock skill matching to that language for the session

---

## 6. Notebook Support (.ipynb)

Special handling:
- Parse JSON structure
- Separate code cells from markdown cells
- Index each cell individually with cell number metadata
- Show cell type in search results

---

## 7. PDF Support

- Extract text per page using `pypdf` or `pdfplumber`
- Index page by page instead of line by line
- Store page number in chunk metadata
- Handle scanned PDFs gracefully (flag as image-based, skip)

---

## Priority Order

1. PDF + ipynb parsers (highest impact, you likely have these now)
2. `write_file` tool + workspace UI (core coding assistant feature)
3. Language skills (low effort, high model quality gain)
4. `list_files` + `search_files` tools
5. `run_code` language expansion
6. Language detection + skill locking