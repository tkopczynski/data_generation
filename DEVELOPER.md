# Developer Guide

This guide contains technical setup instructions and development information for the Dataset Generation CLI.

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

## Requirements

- Python >= 3.12
- OpenAI API key
- Dependencies managed via `pyproject.toml`

## Running the Application

After installation, you can run the CLI in several ways:

```bash
# Using the installed command
data-generation "Generate 100 users with names and emails"

# Using python module
python -m data_generation "Generate 100 users with names and emails"

# Using main.py (backward compatibility)
python main.py "Generate 100 users with names and emails"
```

Get help:
```bash
data-generation --help
# or
python -m data_generation --help
```

## Project Structure

The project follows the src-layout pattern:

```
data_generation/
├── src/data_generation/     # Main package
│   ├── __init__.py
│   ├── __main__.py          # Allows: python -m data_generation
│   ├── cli.py               # CLI interface (Click)
│   ├── config.py            # Configuration settings
│   ├── core/                # Core business logic
│   │   ├── agent.py         # LangGraph ReAct agent
│   │   ├── generator.py     # Data generation engine
│   │   ├── quality.py       # Data quality degradation
│   │   ├── output_formats.py  # Multi-format output
│   │   └── target_generation.py  # Target variable generation
│   ├── tools/               # LangChain tools
│   │   ├── schema_inference.py
│   │   ├── data_generation.py
│   │   └── schema_validation.py
│   └── utils/
│       └── logging.py
├── tests/                   # Tests mirror src structure
└── pyproject.toml          # Project configuration
```

## Development

### Code Quality

Ruff is used for linting and formatting:

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_generator.py -v
pytest tests/test_quality_validation.py -v
pytest tests/test_ml_validation.py -v
pytest tests/test_model_training.py -v

# Run with short traceback
pytest tests/ -v --tb=short
```

### Import Patterns

Use absolute imports:

```python
# Correct
from data_generation.core.agent import run_agent
from data_generation.core.generator import generate_data
from data_generation.tools.schema_validation import validate_schema

# Incorrect (avoid relative imports)
from ..core.agent import run_agent
```

## Architecture

### Core Components Flow
```
User Request (CLI)
    ↓
LangGraph ReAct Agent (core/agent.py)
    ↓
Tools: infer_schema_tool → generate_data_tool
    ↓
Schema Validation (tools/schema_validation.py)
    ↓
Data Generation Engine (core/generator.py)
    ↓
Quality Degradation (core/quality.py)
    ↓
Output Format Writer (core/output_formats.py)
    ↓
File Output (CSV/JSON/Parquet/Excel)
```

### ReAct Agent Workflow

The agent uses a ReAct (Reasoning + Acting) pattern:

1. **Reasoning Phase**: Analyzes natural language request
2. **Format Detection**: Detects desired output format
3. **Schema Inference**: Calls `infer_schema_tool` to generate YAML schema
4. **Validation**: Schema validated against rules
5. **Generation**: Calls `generate_data_tool` with schema, row count, and format
6. **Output**: Returns absolute path to generated file

**Key Agent Behaviors:**
- Uses `gpt-4o-mini` with temperature=0 for deterministic responses
- Defaults to 100 rows if not specified
- Defaults to CSV format if not specified
- Generates parent tables before child tables
- Detects and handles multi-table relationships

## Configuration

Settings in `src/data_generation/config.py`:

```python
LLM_MODEL = "gpt-4o-mini"
SCHEMA_INFERENCE_TEMPERATURE = 0.2
AGENT_VERBOSE = True
```

## Testing

The project includes 150+ tests across 6 test suites:

1. **Generator Tests** - Basic generation and data types
2. **Schema Validation Tests** - Schema structure and rules
3. **Quality Validation Tests** - Data quality degradation
4. **Statistical Validation Tests** - Statistical properties
5. **ML Validation Tests** - ML readiness
6. **Model Training Tests** - Actual model training

## Error Handling

Common error types:

```python
SchemaValidationError  # Invalid schema structure/configuration
FileNotFoundError      # Reference file doesn't exist
ValueError             # YAML parsing, invalid config
click.Abort           # CLI execution failure
```

All errors include descriptive messages for debugging.

## For More Details

See [CLAUDE.md](CLAUDE.md) for comprehensive technical documentation including:
- Complete data type reference (17+ types)
- Schema format specification
- Quality degradation details
- Target variable generation
- Reference type documentation
