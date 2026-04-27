# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama

from backend.api import upload_file
from backend.tools import get_tool_descriptions, call_tool
from backend.skills import get_relevant_skills, format_skills, build_skill_index, get_skills_for_context, \
    get_languages_from_uploads
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
    n_gpu_layers=22,
    verbose=False
)

# Prompt formatting
BASE_PROMPT = """You are a tool-calling agent. You have access to tools and must use them when needed.

## Output rules
- If calling a tool: output ONLY the two TOOL/ARGS lines. Nothing else.
- For complex tasks, think through the steps before acting.
- After using a tool, briefly explain what you found before continuing.
- If giving a final answer: output plain text only. No TOOL lines.
- Never mix explanation and tool calls in the same response.
When calling a tool you MUST output ONLY these two lines, nothing else:
TOOL: <name>
ARGS: {"key": "value"}

No preamble. No explanation. No code blocks. No numbering. Just those two lines.

When giving a final answer, output plain text only. No TOOL: lines.

## Tool rules
- If the user is greeting or making small talk, respond directly. NEVER use tools for greetings.
- Call ONE tool per turn.
- For uploaded files: always call search_context first, then read_file with the returned line range.
- For running code: call run_python with the code as a string.
- Use search_context ONLY when the user explicitly asks about an uploaded file or document.
- Never describe what you would do. Do it.
- Never invent tool results."""

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
    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text).strip()

    match = re.search(
        r"TOOL:\s*(\w+)\s*\nARGS:\s*(\{.*?\})",
        cleaned,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        name = match.group(1)
        raw = match.group(2)
        # Try JSON first
        try:
            return name, json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Fall back to ast.literal_eval for Python-style dicts (mixed quotes etc.)
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
        temperature=0.2,
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
        max_tokens=512,
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


    for step in range(MAX_STEPS):
        prompt = format_messages_from_dicts(convo, query, uploaded_filenames)
        response = llm_call(prompt, max_tokens=128)
        print(f"[step {step}] raw: {response}")
        tool_call = parse_tool_call(response)

        if not tool_call:
            yield {"type": "final", "prompt": prompt}
            return

        name, args = tool_call
        yield {"type": "tool", "name": name, "args": args}

        try:
            result = call_tool(name, args)
        except Exception as e:
            result = f"Tool error: {e}"

        print(f"[step {step}] tool result: {result}")
        convo.append({"role": "assistant", "content": response})
        convo.append({"role": "user", "content": f"Tool result for {name}:\n{result}"})

    yield {"type": "final", "prompt": format_messages_from_dicts(convo, query)}


def _get_uploaded_filenames():
    upload_dir = Path("data/uploads")
    if not upload_dir.exists():
        return []
    return [f.name for f in upload_dir.iterdir() if f.is_file()]
