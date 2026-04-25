# Local LLM Agent — Phase 2 Planner (Performance → Claude-Like Behavior)

## Goal

1. **Make the system fast enough to be usable daily**
2. **Then upgrade behavior to feel like Claude**

---

# Phase 2A — Performance First (DO THIS BEFORE ANYTHING ELSE)

## 1. Enable GPU Acceleration (BIGGEST WIN)

You have an RTX 4060 — not using it is your bottleneck.

### Steps

* Rebuild/install `llama.cpp` with CUDA:

  ```
  cmake -DLLAMA_CUBLAS=ON ...
  ```
* Use `--n-gpu-layers` (or equivalent in Python wrapper)

### Target

* Offload **20–40 layers** to GPU (tune this)
* Monitor VRAM usage (~8GB usable on 4060)

### Result

* 2x–10x speedup depending on model

---

## 2. Tune Model Size vs Speed (Don’t Overkill)

Your current:

```
14B @ Q4 + CPU = slow
```

### Strategy

* Use **7B as default**
* Use **14B only when needed**

### Add dynamic routing:

```python
if task == "simple":
    model = "7B"
else:
    model = "14B"
```

### Result

* Massive latency reduction
* Keeps quality when needed

---

## 3. Optimize n_batch + n_ctx

### Current issue

* Large `n_ctx` slows everything
* Large `n_batch` can bottleneck CPU/GPU sync

### Fix

* Start with:

  ```
  n_ctx: 4096–8192
  n_batch: 64–128
  ```
* Only increase when needed

### Rule

> Bigger ≠ better if you don’t use it

---

## 4. Reduce Prompt Size (Hidden Performance Killer)

You currently stack:

* SYSTEM
* SKILLS
* MEMORY
* USER

This grows fast.

### Fix

* Trim aggressively:

  * Limit memory results (top 3–5)
  * Limit skills (only relevant ones)
* Add token budgeting:

```python
max_prompt_tokens = 3000
```

---

## 5. Cache Everything You Can

### Add caching for:

* File reads
* Vector search results
* Previous tool outputs

### Example

```python
if query in cache:
    return cache[query]
```

---

## 6. Streaming + Early Exit

### Improve UX + speed perception:

* Stream tokens immediately
* Allow early stopping if answer is “good enough”

---

## 7. Parallelize Where Possible

### Easy wins:

* Run FAISS search async
* Preload files while model thinks

---

## 8. Model Settings Tuning

Start with:

```
temperature: 0.2–0.4
top_p: 0.9
repeat_penalty: 1.1–1.2
```

Lower temperature = faster + more stable

---

## Phase 2A Result

* GPU utilized
* 2–10x faster responses
* Lower latency agent loop

---

# Phase 2B — Claude-Like Behavior (After Speed is Fixed)

## 1. Structured Tool Calling (CRITICAL)

### Replace:

```
TOOL: run_python
ARGS: ...
```

### With:

```json
{
  "tool": "run_python",
  "args": {...}
}
```

### Add:

* validation
* retry on failure

---

## 2. Proper Agent Loop (Think → Act → Observe)

### Upgrade loop:

```python
for step in range(max_steps):
    response = model(prompt)

    if tool_call:
        result = run_tool(...)
        prompt += f"TOOL RESULT:\n{result}"
    else:
        break
```

### Add:

* max steps (3–5)
* tool reflection

---

## 3. Code Execution Feedback Loop

### Behavior:

1. Generate code
2. Run code
3. Capture errors
4. Fix automatically

---

## 4. Memory That Feels Smart

### Add layers:

* short-term (recent messages)
* long-term (FAISS)
* summarized memory

### Add:

* auto summarization every N turns
* importance scoring

---

## 5. Better File Understanding

### Upgrade from:

* search → read

### To:

* search → expand → follow imports → build context

---

## 6. Strong System Prompt (Claude Style)

### Add rules:

* Prefer tools over guessing
* Never hallucinate file contents
* Explain actions briefly
* Think step-by-step when needed

---

## 7. Planning Mode

### Example:

```
PLAN:
1. Search files
2. Read code
3. Modify function
4. Test
```

Then execute step-by-step

---

## 8. Self-Critique / Self-Repair

### Add optional second pass:

```python
critique = model("Critique the response")
fix = model("Improve based on critique")
```

---

## 9. Tool Transparency (UX)

Show:

```
🔧 Reading file: app.py
🐍 Running Python code
```

---

## 10. Stability Over Cleverness

Claude feels good because:

* it’s consistent
* it doesn’t break flow
* it recovers from errors

Focus on:

* fewer failures
* cleaner outputs
* predictable behavior

---

# Final Priority Order

## Do FIRST (Performance)

1. GPU acceleration (CUDA + n_gpu_layers)
2. Use 7B by default, 14B selectively
3. Reduce prompt size
4. Tune n_ctx + n_batch
5. Add caching

## THEN (Behavior)

6. Structured tool calling
7. Proper agent loop
8. Code execution feedback
9. Memory improvements
10. Prompt + planning upgrades

---

# End State

You’ll have:

* Fast local assistant (usable daily)
* Tool-using coding agent
* Memory-aware system
* Claude-like reasoning behavior

---
