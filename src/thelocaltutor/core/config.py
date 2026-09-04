"""Application-wide configuration and paths."""

from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "TheLocalTutor"
APP_VERSION = "1.0.0"

# User data lives in ~/.thelocaltutor on all platforms
DATA_DIR = Path.home() / ".thelocaltutor"
DB_PATH = DATA_DIR / "thelocaltutor.db"
MATERIALS_DIR = DATA_DIR / "materials"
GENERATED_DIR = DATA_DIR / "generated"
LOGS_DIR = DATA_DIR / "logs"
SETTINGS_FILE = DATA_DIR / "settings.json"

_DEFAULTS: dict = {
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "default_question_count": 10,
    "default_question_types": ["mcq", "true_false", "short_answer"],
    "default_difficulty": "mixed",
    "chunk_size": 3000,
    "chunk_overlap": 200,
    "max_chunks_per_generation": 6,
    "theme": "light",
}


def _ensure_dirs() -> None:
    for d in (DATA_DIR, MATERIALS_DIR, GENERATED_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure_dirs()
    if not SETTINGS_FILE.exists():
        return dict(_DEFAULTS)
    try:
        with SETTINGS_FILE.open() as f:
            saved = json.load(f)
        return {**_DEFAULTS, **saved}
    except Exception:
        return dict(_DEFAULTS)


def save_settings(settings: dict) -> None:
    _ensure_dirs()
    with SETTINGS_FILE.open("w") as f:
        json.dump(settings, f, indent=2)


# Module-level settings cache (refreshed by save_settings)
_settings: dict | None = None


def get(key: str):
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings.get(key, _DEFAULTS.get(key))


def set(key: str, value) -> None:
    global _settings
    if _settings is None:
        _settings = load_settings()
    _settings[key] = value
    save_settings(_settings)
