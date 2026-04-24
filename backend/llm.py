# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama
from backend.tools import get_tool_descriptions, call_tool
from backend.skills import get_relevant_skills, format_skills, build_skill_index
from backend.config import get_hardware_config
import json
import re

HW = get_hardware_config()
MAX_STEPS = 8

LLM = Llama(
    model_path=HW["model_path"],
    n_ctx=HW["n_ctx"],  # 32768 / 4096
    n_threads=HW["n_threads"],
    n_batch=HW["n_batch"],
    verbose=False
)

# Prompt formatting
BASE_PROMPT = """You are a tool-calling agent. You have access to tools and must use them when needed.

## Output rules
When calling a tool you MUST output ONLY these two lines, nothing else:
TOOL: <name>
ARGS: {"key": "value"}

No preamble. No explanation. No code blocks. No numbering. Just those two lines.

When giving a final answer, output plain text only. No TOOL: lines.

## Tool rules
- Call ONE tool per turn.
- For uploaded files: always call search_context first, then read_file with the returned line range.
- For running code: call run_python with the code as a string.
- Never describe what you would do. Do it.
- Never invent tool results."""

build_skill_index()


def build_system_prompt(query: str) -> str:
    # Skills
    skills = get_relevant_skills(query)
    skill_block = format_skills(skills)
    skill_section = f"\n\n## Skills\n{skill_block}" if skill_block else ""

    # Tools
    tool_section = f"\n\n## Available tools:\n{get_tool_descriptions()}"

    return BASE_PROMPT + skill_section + tool_section


def format_messages(messages) -> str:
    return format_messages_from_dicts([
        {"role": m.role, "content": m.content} for m in messages
    ])


def format_messages_from_dicts(messages: list[dict], query: str = "") -> str:
    system = build_system_prompt(query)
    prompt = f"<|system|>\n{system}<|end|>\n"
    for m in messages:
        if m["role"] == "user":
            prompt += f"<|user|>\n{m['content']}<|end|>\n"
        elif m["role"] == "assistant":
            prompt += f"<|assistant|>\n{m['content']}<|end|>\n"
    prompt += "<|assistant|>\n"
    return prompt


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


def llm_call(prompt: str) -> str:
    output = LLM(
        prompt,
        max_tokens=512,
        temperature=0.5,
        stop=["<|end|>", "<|user|>"]
    )
    return output["choices"][0]["text"].strip()


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
