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
    n_ctx = 16384, # 32768 / 4096
    n_threads=4,
    verbose = False
)

MAX_STEPS = 8

# Prompt formatting
SYSTEM_PROMPT = f"""You are a concise helpful assistant with access to tools.

RULES:
- Always use search_context FIRST to find relevant line ranges before calling read_file.
- Use the line ranges returned by search_context when calling read_file — do NOT default to start_line=0.
- If search_context returns no results or read_file chunk doesn't answer the question, call search_context again with a different query.
- Never conclude something doesn't exist after reading only one chunk.
- Only give a final answer once you have either found the answer or exhausted search_context results.
- You may only call ONE tool per response
- After receiving tool results, decide next step
- Do NOT chain multiple tool calls in one message

If you need a tool, respond with ONLY this — no other text before or after:
- Output EXACTLY in this format when using a tool:
TOOL: tool_name
ARGS: {{"key": "value"}}

- Do NOT use JSON format
- Do NOT use markdown code blocks
- Do NOT include explanations

Example of correct tool usage:
TOOL: search_context
ARGS: {{"query": "AI feedback"}}

Example of INCORRECT tool usage (never do this):
```json
{{"tool": "search_context", "args": {{"query": "AI feedback"}}}}
```

Do not explain what you are doing. Do not add any text before TOOL:.

Available tools:
{get_tool_descriptions()}

When you have the tool result, use it to give a final answer.
If no tool is needed, just answer directly without the formatting."""

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