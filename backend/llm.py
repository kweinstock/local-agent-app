# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama

from backend.tools import get_tool_descriptions, call_tool
from backend.skills import format_skills, build_skill_index, get_skills_for_context, get_languages_from_uploads
from backend.config import get_hardware_config
from pathlib import Path
import json
import ast
import re

HW = get_hardware_config()
MAX_STEPS = 8
MAX_HISTORY = 20

LLM = Llama(
    model_path=HW["model_path"],
    n_ctx=HW["n_ctx"],
    n_threads=HW["n_threads"],
    n_batch=HW["n_batch"],
    n_gpu_layers=-1,
    verbose=False
)

# Prompt formatting
BASE_PROMPT = """You are a general coding assistant with access to tools. Use them correctly.

## Available tool names ONLY
You may ONLY call tools from the list in ## Available tools below.
Never invent tool names. If a tool does not exist, answer directly.

## When to use which tool
- User asks what files are uploaded / "what files do I have" / "look at my project" → call list_files (no args)
- User asks to find a function, symbol, or pattern in a file → call search_files
- User asks about content of an uploaded file → call search_context first, then read_file
- User asks to save / create / write a file → call write_file with filename and full content
- User asks to run code or calculate something → call run_python
- User asks a general question, greets you, or asks about code concepts → answer directly, NO tools
- "save", "save it", "save to a file", "put it in a file" → ALWAYS call write_file immediately. Never describe how to save manually.
- Never include Python docstrings (triple-quoted strings) in file content passed to write_file.
- Replace docstrings with regular comments using # instead.
- Never describe code and ask the user to save it. Always call write_file directly.
- If asked to create multiple files, call write_file once per file in sequence.
- "what files do I have", "show my files", "where are my files" → ALWAYS call list_files, never answer from memory

## Tool call format
When calling a tool output ONLY these two lines, nothing else:
TOOL: <name>
ARGS: {"key": "value"}

No explanation before or after. No markdown. No preamble. Just those two lines.

## ARGS format rules
- ARGS must be valid JSON. Use double quotes only.
- For multi-line content use \\n not triple quotes or actual newlines inside strings.
- Correct example: ARGS: {\"filename\": \"x.py\", \"content\": \"line1\\nline2\\nline3\"}
- Wrong example: ARGS: {\"filename\": \"x.py\", \"content\": use triple quotes}

## Output rules
- Final answers are plain text or markdown. No TOOL lines in final answers.
- Never call the same tool twice with the same args in the same conversation turn.
- If a tool returns an error, try a different approach — do not repeat the same call.
- If search_context returns file content, use it to answer directly. Do not call it again.
- When writing a file: include the COMPLETE file content in write_file. Never truncate.
- Never hallucinate file contents. Only describe what you actually read from a tool result.
- Keep responses complete. Never cut off mid-sentence or mid-code block.
- Keep the responses concise and informative. do not add a large amount of fluff"""

build_skill_index()


def build_system_prompt(query: str, uploaded_filenames: list[str] = None) -> str:
    uploaded_filenames = uploaded_filenames or []

    # Skills
    skills = get_skills_for_context(query, uploaded_filenames)
    print(f"[skills] matched: {[s['name'] for s in skills]}")
    skill_block = format_skills(skills)
    skill_section = f"\n\n## Skills\n{skill_block}" if skill_block else ""

    languages = get_languages_from_uploads(uploaded_filenames)
    lang_section = ""
    if languages:
        lang_list = ", ".join(languages)
        lang_section = f"\n\n## Working Language\nThe uploaded files use: {lang_list}. Stick to these languages unless asked otherwise."

    # Tools
    tool_section = f"\n\n## Available tools:\n{get_tool_descriptions()}"

    return BASE_PROMPT + lang_section + skill_section + tool_section


def format_messages(messages) -> str:
    return format_messages_from_dicts([
        {"role": m.role, "content": m.content} for m in messages
    ])


def format_messages_from_dicts(messages: list[dict], query: str = "", uploaded_filenames: list[str] = None) -> str:
    system = build_system_prompt(query, uploaded_filenames or [])
    prompt = f"<|im_start|>system\n{system}<|im_end|>\n"
    for m in messages:
        if m["role"] == "user":
            prompt += f"<|im_start|>user\n{m['content']}<|im_end|>\n"
        elif m["role"] == "assistant":
            prompt += f"<|im_start|>assistant\n{m['content']}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt


def parse_tool_call(text: str):
    write_match = re.search(
        r"TOOL:\s*write_file\s*\nFILENAME:\s*(.+?)\s*\n```(?:\w+)?\n(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if write_match:
        filename = write_match.group(1).strip()
        content = write_match.group(2)
        return "write_file", {"filename": filename, "content": content}

    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text).strip()

    # Normalize triple quotes
    cleaned = re.sub(r'"""(.*?)"""', lambda m: json.dumps(m.group(1)), cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"'''(.*?)'''", lambda m: json.dumps(m.group(1)), cleaned, flags=re.DOTALL)
    cleaned = cleaned.replace('"""', '"').replace("'''", "'")

    match = re.search(
        r"TOOL:\s*(\w+)\s*\nARGS:\s*(\{.*)",
        cleaned,
        re.DOTALL | re.IGNORECASE
    )

    if not match:
        return None

    name = match.group(1)
    raw = match.group(2).strip()

    # Try clean JSON first
    try:
        return name, json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Extract filename and content separately using regex
    # This bypasses JSON parsing entirely for write_file
    filename_match = re.search(r'"filename"\s*:\s*"([^"]+)"', raw)
    content_match = re.search(r'"content"\s*:\s*"(.*?)(?:"\s*\}|"\s*$)', raw, re.DOTALL)

    if filename_match and content_match:
        filename = filename_match.group(1)
        content = content_match.group(1)
        # Unescape standard JSON escapes
        content = content.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
        return name, {"filename": filename, "content": content}

    # Try ast.literal_eval fallback
    try:
        args = ast.literal_eval(raw)
        if isinstance(args, dict):
            return name, args
    except (ValueError, SyntaxError):
        pass

    # Fallback: bare JSON object with tool/args keys
    for jm in re.findall(r"\{.*?\}", cleaned, re.DOTALL):
        try:
            data = json.loads(jm)
            if "tool" in data and "args" in data:
                return data["tool"], data["args"]
        except:
            continue

    return None


def llm_call(prompt: str, max_tokens: int = 512) -> str:
    output = LLM(
        prompt,
        max_tokens=max_tokens,
        temperature=0.1,
        repeat_penalty=1.15,
        stop=["<|im_end|>", "<|im_start|>"]
    )
    choice = output["choices"][0]
    if choice["finish_reason"] == "length":
        print("[warning] response hit max_tokens — may be truncated")
    return choice["text"].strip()


def llm_stream(prompt: str):
    stream = LLM(
        prompt,
        max_tokens=1024,
        temperature=0.2,
        repeat_penalty=1.15,
        stop=["<|im_end|>", "<|im_start|>"],
        stream=True,
    )
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            yield token


def generate(messages):
    convo = [{"role": m.role, "content": m.content} for m in messages]
    convo = convo[-MAX_HISTORY:]
    query = convo[-1]["content"] if convo else ""
    uploaded_filenames = _get_uploaded_filenames()

    for step in range(MAX_STEPS):
        prompt = format_messages_from_dicts(convo, query, uploaded_filenames)
        response = llm_call(prompt)
        print(f"[step {step}] raw response:\n{response}\n")
        tool_call = parse_tool_call(response)
        print(f"[step {step}] parsed: {tool_call}\n")

        if not tool_call:
            return response

        name, args = tool_call
        try:
            result = call_tool(name, args)
        except Exception as e:
            result = f"Tool error: {e}"

        if any(result.startswith(p) for p in ("Tool error:", "Error", "Unknown tool")):
            result = (
                f"{result}\n"
                f"Reflect: wrong tool or args? Try a different approach."
            )

        print(f"[step {step}] tool result:\n{result}\n")

        if step == MAX_STEPS - 2:
            convo.append({"role": "user", "content": "1 step remaining. Give your final answer now."})

        convo.append({"role": "assistant", "content": response})
        convo.append({"role": "user", "content": f"Tool result for {name}:\n{result}"})

    return "Max steps reached without final answer."


def generate_with_stream(messages):
    convo = [{"role": m.role, "content": m.content} for m in messages]
    convo = convo[-MAX_HISTORY:]
    query = convo[-1]["content"] if convo else ""
    uploaded_filenames = _get_uploaded_filenames()

    seen_calls = set()

    for step in range(MAX_STEPS):
        prompt = format_messages_from_dicts(convo, query, uploaded_filenames)
        response = llm_call(prompt, max_tokens=1024)
        print(f"[step {step}] raw: {response}")
        tool_call = parse_tool_call(response)

        if not tool_call:
            yield {"type": "final", "prompt": prompt}
            return

        name, args = tool_call
        call_sig = f"{name}:{json.dumps(args, sort_keys=True)}"
        if call_sig in seen_calls:
            yield {"type": "final", "prompt": prompt}
            return
        seen_calls.add(call_sig)
        yield {"type": "tool", "name": name, "args": args}

        try:
            result = call_tool(name, args)
        except Exception as e:
            result = f"Tool error: {e}"

        print(f"[step {step}] tool result: {result}")
        convo.append({"role": "assistant", "content": response})
        convo.append({"role": "user", "content": f"Tool result for {name}:\n{result}"})

    yield {"type": "final", "prompt": format_messages_from_dicts(convo, query)}


def _get_uploaded_filenames() -> list[str]:
    names = []
    for d in [Path("data/uploads"), Path("data/workspace")]:
        if d.exists():
            names.extend(f.name for f in d.iterdir() if f.is_file())
    return names
