"""
Configuration module for the Smart Diet & Nutrition MAS.
Centralizes all configurable parameters for the system.
"""

import os
from pathlib import Path

# ── Project Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Ollama / LLM Settings ─────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TEMPERATURE = 0.3  # Low temperature for deterministic nutrition advice

# ── Nutrition Defaults ─────────────────────────────────────────────────────────
DEFAULT_ACTIVITY_MULTIPLIER = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

# Macronutrient split ratios (percentage of total calories)
MACRO_RATIOS = {
    "weight_loss": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
    "muscle_gain": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
    "maintenance": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
    "healthy_eating": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
}

# ── Supported Cultures ─────────────────────────────────────────────────────────
SUPPORTED_CULTURES = [
    "sri_lankan",
    "indian_north",
    "indian_south",
    "western",
    "mediterranean",
    "east_asian",
]

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "7 days"
