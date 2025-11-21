"""Configuration for dataset generation."""

import os

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Base URL for OpenAI-compatible API (None = OpenAI default)
# Examples:
#   - Ollama: "http://localhost:11434/v1"
#   - vLLM: "http://localhost:8000/v1"
#   - LMStudio: "http://localhost:1234/v1"
LLM_BASE_URL = os.getenv("LLM_BASE_URL")

# API key (None = use OPENAI_API_KEY env var)
# For local servers that don't require auth, set to any non-empty string
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Temperature for data generation (higher = more creative/varied)
DATA_GENERATION_TEMPERATURE = float(os.getenv("DATA_GENERATION_TEMPERATURE", "0.7"))
