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
        model = "phi3-mini-q4.gguf"
    elif ram < 16:
        model = "phi3-mini-q4.gguf"
    else:
        model = "phi3-mini-q4.gguf"

    return os.path.join(BASE_DIR, "models", model)