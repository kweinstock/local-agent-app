# File: backend/api.py
# Name: Keagan Weinstock
# Description: This file is used to configure what llm
#              Model to use

import psutil
import os

def get_ram_gb():
    return psutil.virtual_memory().total / (1024 ** 3)

def select_model():
    ram = get_ram_gb()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model = ""

    if ram < 8:
        model = "Phi-3.1-mini-128k-instruct-Q4_K_M.gguf"
    elif ram < 16:
        model = "Phi-3.1-mini-128k-instruct-Q4_K_M.gguf"
    else:
        model = "Phi-3.1-mini-128k-instruct-Q4_K_M.gguf"

    return os.path.join(BASE_DIR, "models", model)

def get_embed_model_path():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(BASE_DIR, "models", "BAAI", "bge-small-en-v1.5")