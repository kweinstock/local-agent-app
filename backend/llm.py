# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama
from backend.config import select_model
from backend.tools import get_tool_descriptions, call_tool
import json
import re

MODEL_PATH = select_model()

LLM = Llama(
    model_path = MODEL_PATH,
    n_ctx = 32768, # 32768 / 4096
    n_threads=4,
    verbose = False
)

MAX_STEPS = 8

# Prompt formatting
SYSTEM_PROMPT = f"""You are a concise helpful assistant with access to tools.

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
ARGS: {{"key": "value"}}

- No extra text before or after
- No explanations
- No markdown
- No JSON wrappers

Example (correct):
TOOL: search_context
ARGS: {{"query": "AI feedback"}}

Example (incorrect):
{{"tool": "search_context", "args": {{"query": "AI feedback"}}}}

FINAL ANSWERS:
- Once you have enough information, respond normally.
- Do NOT include TOOL formatting in final answers.

Available tools:
{get_tool_descriptions()}
"""

def format_messages(messages):
    prompt = f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"

    for m in messages:
        role = m["role"] if isinstance(m, dict) else m.role
        content = m["content"] if isinstance(m, dict) else m.content

        if role == "user":
            prompt += f"<|user|>\n{content}<|end|>\n"
        elif role == "assistant":
            prompt += f"<|assistant|>\n{content}<|end|>\n"
        elif role == "tool":
            prompt += f"<|user|>\nTool result:\n{content}<|end|>\n"

    prompt += "<|assistant|>\n"
    return prompt

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

def generate(messages):
    convo = [{"role": m.role, "content": m.content} for m in messages]

    for step in range(MAX_STEPS):
        response = llm_call(format_messages(messages))
        print(f"[step {step}] raw response:\n{response}\n")
        tool_call = parse_tool_call(response)
        print(f"[step {step}] parsed tool call: {tool_call}\n")
        if not tool_call:
            return response
        name, args = tool_call
        try:
            result = call_tool(name, args)
        except Exception as e:
            result = f"Tool error: {str(e)}"

        convo.append({
            "role": "assistant",
            "content": response
        })
        convo.append({
            "role": "user",
            "content": f"Tool result for {name}:\n{result}"
        })
        messages = [type("Msg", (), m) for m in convo]

    return "Max steps reached without final answer."