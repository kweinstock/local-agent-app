# Local Coding Assistant - Phase 4: Quality & Reliability

## 1. Model Swap — Qwen2.5-Coder-7B (Highest Leverage)
The single biggest improvement available. Same size, same format, same prompt
template as current model. Fine-tuned specifically on code and tool calling.
Fixes placeholder code, bad tool calls, and quote errors at the source.

**Change in `config.py`:**
- Swap model filename to `qwen2.5-coder-7b-instruct-q4_k_m.gguf`
- [Qwen 2.5 coder, 7B Q4](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/blob/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf)
- Zero other changes needed

**Test with 5 standard prompts before and after:**
1. "write a hangman game in python and save it"
2. "read app.tsx and summarize what it does"
3. paste a syntax error, say "fix this"
4. "write a fibonacci function, test it, save it"
5. "what files do I have"

---

## 2. Grammar Sampling — Force Valid Tool Calls
Constrain model output so it physically cannot produce malformed tool calls.
Eliminates the entire class of JSON parse failures, hallucinated tool names,
and raw tool call leaks without any prompt engineering.

**In `llm.py`:**
- Use llama-cpp-python `grammar` parameter on tool-detection calls
- Define a GBNF grammar that only allows valid TOOL/ARGS format
- Switch to unconstrained generation for final answer streaming
- Only applies during tool selection phase, not content generation

**Eliminates:**
- write_file JSON parse failures
- Hallucinated tool names like `write_typescript_method`
- Raw tool calls leaking as final assistant message

---

## 3. Context Window Management
Model loses coherence on large tasks. Tool results eat context fast.

**In `llm.py`:**
- Add `estimate_tokens(prompt)` — rough char/4 estimate
- If estimated tokens > 80% of n_ctx, trim oldest tool result messages first
- Keep user/assistant pairs, drop intermediate tool results
- Compress used tool results to one-line summaries in history
- Dynamically reduce MAX_HISTORY when prompt is large

---

## 4. Syntax Validation on write_file
Model saves broken files silently. User discovers the error only when running.

**In `tools.py` `write_file`:**
- Run `ast.parse` on all `.py` files before saving
- For `.ts`/`.js` files use a basic brace/bracket balance check
- If validation fails, return error with line number and description
- Model must fix and retry before file is saved
- Never save a file that fails validation

---

## 5. Implementation Quality Skill
Model writes skeleton code with `pass`, placeholder comments, and incomplete logic.

**New `implementation.md` skill:**
- Never use `pass` as a method body unless explicitly asked for a stub
- Never write placeholder comments like `# implementation here`
- Every method must have working logic
- Test with `run_python` before calling `write_file`
- If a file has more than one function, verify all of them before saving

**Add to `BASE_PROMPT`:**
- "Write complete working implementations. Never use placeholders or stubs."

---

## 6. Encrypted PDF Crash Fix
Server hard crashes on encrypted PDFs. Should never happen.

**In `embeddings.py` `parse_pdf`:**
- Catch `pypdf.errors.FileNotDecryptedError` and all PDF exceptions
- Return a single chunk flagging the file as encrypted/unreadable
- Log the error server-side
- Never let a bad file crash the server

---

## 7. Multi-File Awareness
Model loses track of what files exist across a session and writes files that
import others without verifying those others exist.

**In `llm.py` `build_system_prompt`:**
- When any files exist in uploads or workspace, inject a compact file list
  into the system prompt header automatically
- Format: `Available files: hangman.py [workspace], App.tsx [uploaded]`
- Model always knows what exists without needing to call list_files first
- When creating a file that imports another, model checks list before writing

---

## 8. append_file Tool
Large files hit token limits mid-write and get truncated. Splitting into
write + append avoids the problem without needing larger token budgets.

**New tool in `tools.py`:**
- `append_file(filename, content)` — appends to existing workspace file
- Same validation as write_file
- Model uses write_file for the first section, append_file for the rest
- Add to TOOL descriptions so model knows when to use it

---

## 9. Better Error Recovery
Model loops on the same failing tool call or gives up without explanation.

**In `llm.py`:**
- Track tool call history per session — name + args hash
- If identical tool call appears twice, inject: "This call already failed.
  Try a different approach or explain what is blocking you."
- On EXECUTION FAILED, model must read the error before retrying
- Max 2 retries per unique tool call, then surface a clear explanation

---

## 10. Dynamic Token Budget
Model does not know how large its output budget is and truncates silently.

**In `llm.py`:**
- Estimate file size before generation starts
- For large write_file tasks, tell the model the approximate line count
  expected and set max_tokens accordingly
- Small responses (tool calls, short answers): 256 tokens
- Medium responses (explanations, short files): 512 tokens  
- Large responses (full file writes): 1024 tokens
- Set dynamically based on task type detected from query

---

## Priority Order
1. Model swap to Qwen2.5-Coder-7B — zero code change, biggest quality jump
2. Grammar sampling — eliminates tool call failures permanently
3. Syntax validation on write_file — stops broken files being saved
4. Implementation quality skill — fixes placeholder code pattern
5. Context window management — fixes long session degradation
6. Encrypted PDF crash fix — server stability
7. Multi-file awareness — fixes cross-file confusion
8. Dynamic token budget — fixes silent truncation
9. append_file tool — fixes large file truncation
10. Better error recovery — fixes looping behavior