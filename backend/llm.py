# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama
from backend.config import select_model
from backend.tools import get_tool_descriptions, call_tool
from backend.skills import get_relevant_skills, format_skills, build_skill_index
import json
import re

MODEL_PATH = select_model()
MAX_STEPS = 8

LLM = Llama(
    model_path=MODEL_PATH,
    n_ctx=32768,  # 32768 / 4096
    n_threads=8,
    n_batch=128,
    verbose=False
)

# Prompt formatting
BASE_PROMPT = """You are a concise helpful assistant with access to tools.

RULES:

GENERAL:
- Use tools only when necessary.
- If the question can be answered directly, do NOT use a tool.
- NEVER assume files or data exist unless provided.
- NEVER invent tool results.

TOOL USAGE:
- You may call ONLY ONE tool per response.
- After receiving a tool result, decide the next step.
- Do NOT chain multiple tools in a single message.

WHEN TO USE TOOLS:
- Use search_context ONLY for questions about uploaded documents.
- Use read_file ONLY after search_context identifies relevant line ranges.
- Use run_python when the user asks to execute code or compute results.

DOCUMENT SEARCH RULES (only when using search_context/read_file):
- Always use search_context FIRST before read_file.
- Use the returned line ranges when calling read_file.
- If no results, try a different query before concluding.
- Do NOT conclude something doesn't exist after one attempt.

OUTPUT FORMAT (CRITICAL):
If you use a tool, respond with EXACTLY:

TOOL: tool_name
ARGS: {"key": "value"}

- No extra text before or after
- No explanations
- No markdown
- No JSON wrappers

Example (correct):
TOOL: search_context
ARGS: {"query": "AI feedback"}

Example (incorrect):
{"tool": "search_context", "args": {"query": "AI feedback"}}

FINAL ANSWERS:
- Once you have enough information, respond normally.
- Do NOT include TOOL formatting in final answers."""

build_skill_index()

def build_system_prompt(query: str) -> str:
    skills = get_relevant_skills(query)
    skill_block = format_skills(skills)
    skill_section = f"\n\n# Relevant Skills\n{skill_block}" if skill_block else ""
    tool_section = f"\n\nAvailable tools:\n{get_tool_descriptions()}"
    return BASE_PROMPT + skill_section + tool_section

def llm_call(prompt: str) -> str:
    output = LLM(
        prompt,
        max_tokens=512,
        temperature=0.5,
        stop=["<|end|>", "<|user|>"]
    )
    return output["choices"][0]["text"].strip()

def parse_tool_call(text: str):
    # Remove markdown fences
    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", text).strip()

    # 1. Try TOOL/ARGS format
    match = re.search(
        r"TOOL:\s*(\w+)\s*ARGS:\s*(\{.*?\})",
        cleaned,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        name = match.group(1)
        try:
            args = json.loads(match.group(2))
            return name, args
        except json.JSONDecodeError:
            pass

    # 2. Fallback: try JSON tool call
    json_matches = re.findall(r"\{.*?\}", cleaned, re.DOTALL)

    for jm in json_matches:
        try:
            data = json.loads(jm)
            if "tool" in data and "args" in data:
                return data["tool"], data["args"]
        except:
            continue

    return None

def format_messages(messages) -> str:
    return format_messages_from_dicts([
        {"role": m.role, "content": m.content} for m in messages
    ])

def format_messages_from_dicts(messages: list[dict], query: str = "") -> str:
    system_prompt = build_system_prompt(query)
    prompt = f"<|system|>\n{system_prompt}<|end|>\n"
    for m in messages:
        if m["role"] == "user":
            prompt += f"<|user|>\n{m['content']}<|end|>\n"
        elif m["role"] == "assistant":
            prompt += f"<|assistant|>\n{m['content']}<|end|>\n"
    prompt += "<|assistant|>\n"
    return prompt

def generate(messages):
    convo = [{"role": m.role, "content": m.content} for m in messages]
    query = convo[-1]["content"] if convo else ""

    for step in range(MAX_STEPS):
        prompt = format_messages_from_dicts(convo, query)
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

        print(f"[step {step}] tool result:\n{result}\n")

        convo.append({"role": "assistant", "content": response})
        convo.append({"role": "user", "content": f"Tool result for {name}:\n{result}"})

    return "Max steps reached without final answer."