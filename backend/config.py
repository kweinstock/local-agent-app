# File: backend/api.py
# Name: Keagan Weinstock
# Description: This file is used to configure what llm
#              Model to use

import psutil
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIER_CONFIG = {
    "low": {
        "model":   "qwen-2.5-3B-instruct-gguf-Q4-K-M.gguf",
        "n_ctx":   4096,
        "n_batch": 64,
    },
    "medium": {
        "model":   "qwen-2.5-7B-instruct-gguf-Q4-K-M.gguf",
        "n_ctx":   8192,
        "n_batch": 128,
    },
    "high": {
        "model":   "qwen-2.5-7B-instruct-gguf-Q4-K-M.gguf",
        "n_ctx":   16384,
        "n_batch": 256,
    },
}


def get_ram_gb() -> float:
    return psutil.virtual_memory().total / (1024 ** 3)


def get_cpu_cores() -> int:
    return psutil.cpu_count(logical=False) or 2


def get_tier() -> str:
    ram = get_ram_gb()
    if ram < 8:
        return "low"
    elif ram < 16:
        return "medium"
    else:
        return "high"


def get_hardware_config() -> dict:
    tier = get_tier()
    cfg = TIER_CONFIG[tier].copy()
    cfg["n_threads"] = max(2, get_cpu_cores() - 1)  # Leaved one core free
    cfg["model_path"] = os.path.join(BASE_DIR, "models", cfg.pop("model"))
    cfg["tier"] = tier
    return cfg


def select_model():
    return get_hardware_config()["model_path"]


def get_embed_model_path():
    return os.path.join(BASE_DIR, "models", "BAAI", "bge-small-en-v1.5")
