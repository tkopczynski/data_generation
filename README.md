# Synthetic Dataset Generator

A powerful tool for generating synthetic datasets using LangChain and OpenAI's GPT models. Available as both a **CLI application** and a **web interface** (Gradio). The application uses a LangGraph ReAct agent to intelligently generate data based on natural language requests.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e ".[dev]"
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

### Web Interface (Recommended for most users) 🌐

Launch the Gradio web interface:

```bash
# Using the installed command
data-generation-web

# Or using python module
python -m data_generation.web.app
```

Then open your browser to http://localhost:7860

**Features:**
- 📱 Mobile responsive design
- 💬 Natural language interface
- 🔍 Schema preview
- ⚙️ Advanced YAML editor
- 📥 Direct file download

See [WEB_README.md](WEB_README.md) for detailed web interface documentation.

### CLI Interface 💻

For automation and scripting:

```bash
# Using the installed command
data-generation "Generate 100 users with names and emails"

# Using python module
python -m data_generation "Generate 100 users with names and emails"
```

Get help:
```bash
data-generation --help
# or
python -m data_generation --help
```

## Requirements

- Python >= 3.12
- OpenAI API key

## Key Features

- **🌐 Web Interface**: Modern Gradio UI with mobile support
- **💬 Natural Language**: Describe data in plain English
- **🤖 LangGraph Agent**: Autonomous agent that plans and executes generation
- **🔗 Related Tables**: Foreign key relationships with reference type
- **📊 17+ Data Types**: Numeric, text, dates, categories, and more
- **🎯 Data Quality**: Configurable null rates, duplicates, outliers
- **📱 Mobile Friendly**: Responsive design works on any device
