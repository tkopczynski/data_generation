# Dataset Generation CLI

A CLI application for generating datasets using LangChain and OpenAI.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-actual-api-key
   ```

## Usage

Run the CLI:
```bash
python main.py --help
```

Generate a dataset:
```bash
python main.py generate
```

## Requirements

- Python >= 3.12
- OpenAI API key
