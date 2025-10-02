# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A CLI application for generating synthetic sales datasets using LangChain and OpenAI's GPT models.

## Setup and Environment

1. **Virtual environment setup:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e .
   ```
   Dependencies are managed in `pyproject.toml` - always use this file for dependency management.

3. **Environment configuration:**
   - Copy `.env.example` to `.env`
   - Add OpenAI API key to `.env`: `OPENAI_API_KEY=your-key`

## Running the Application

**Run CLI:**
```bash
python main.py --help
```

**Generate dataset:**
```bash
python main.py generate
```

## Development Notes

- Python >= 3.12 required
- The application expects LLM output in pipe-separated format with headers
- Output file location controlled by `OUTPUT_FILE` in `config.py`
- No test suite currently exists
