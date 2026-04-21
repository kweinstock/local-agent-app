# File: backend/llm.py
# Name: Keagan Weinstock
# Description: This file is used to set up the
#              llm to generate text

from llama_cpp import Llama
from backend.config import select_model

MODEL_PATH = select_model()

llm = Llama(
    model_path = MODEL_PATH,
    n_ctx = 2048,
    n_threads=4,
    verbose = False
)

def format_messages(messages):
    prompt = ""
    for m in messages:
        if m.role == "user":
            prompt += f"<|user|>\n{m.content}<|end|>\n"
        else:
            prompt += f"<|assistant|>\n{m.content}<|end|>"
    prompt += "<|assistant|>\n"
    return prompt

def generate(messages):
    prompt = format_messages(messages)

    output = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": prompt},
        ],
        max_tokens=256,
        temperature=0.7,
        stop=["</s>"]
    )
    return output["choices"][0]["message"]["content"]