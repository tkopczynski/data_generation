# Developer Guide

Technical documentation for the makeitup library.

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

## Project Structure

```
makeitup/
├── src/makeitup/            # Main package
│   ├── __init__.py          # Package exports
│   ├── api.py               # Public API: make()
│   ├── config.py            # LLM configuration
│   ├── core/
│   │   ├── generator.py     # LLM-based data generation
│   │   └── output_formats.py  # CSV/JSON/Parquet/Excel writers
│   └── utils/
│       └── logging.py
├── tests/
│   ├── test_api.py          # API tests (with mocks + integration)
│   └── test_output_formats.py  # Output format tests
└── pyproject.toml
```

## API Reference

### `make()`

```python
def make(
    columns: dict[str, str],
    num_rows: int,
    *,
    target: dict[str, str] | None = None,
    output_path: str | Path | None = None,
    quality_issues: list[str] | None = None,
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `columns` | `dict[str, str]` | Column names mapped to natural language descriptions |
| `num_rows` | `int` | Number of rows to generate |
| `target` | `dict` (optional) | Target column with `name` and `prompt` keys |
| `output_path` | `str \| Path` (optional) | Path to save output (format inferred from extension) |
| `quality_issues` | `list[str]` (optional) | Data quality issues to introduce: `"nulls"`, `"outliers"`, `"typos"`, `"duplicates"` |

**Returns:** `pandas.DataFrame`

**Examples:**

```python
from makeitup import make

# Basic generation
df = make(
    columns={
        "age": "Age of working professionals, 25-55",
        "salary": "Annual salary in USD, tech industry",
    },
    num_rows=100
)

# With target column for ML
df = make(
    columns={
        "tenure": "Months as customer, 1-60",
        "monthly_spend": "Monthly spending in USD",
    },
    target={
        "name": "churned",
        "prompt": "Boolean: true if customer left"
    },
    num_rows=500,
    output_path="customers.parquet"
)

# With data quality issues for testing data pipelines
df = make(
    columns={
        "name": "Person's full name",
        "age": "Age between 20 and 60",
        "salary": "Annual salary in USD",
    },
    num_rows=100,
    quality_issues=["nulls", "outliers"]
)
```

## Output Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| CSV | `.csv` | Universal compatibility |
| JSON | `.json` | APIs, web applications |
| Parquet | `.parquet` | Big data, analytics |
| Excel | `.xlsx` | Business users, spreadsheets |

Format is automatically detected from the file extension in `output_path`.

## Configuration

Settings in `src/makeitup/config.py`:

```python
LLM_MODEL = "gpt-4o-mini"           # Model for generation
DATA_GENERATION_TEMPERATURE = 0.7   # Higher = more variety
```

## How It Works

```
Python API Call
    ↓
make(columns, target, num_rows)
    ↓
Single LLM Call (generates entire table as JSON)
    ↓
Parse & Validate Response
    ↓
DataFrame / File Output (CSV/JSON/Parquet/Excel)
```

1. **Prompt Building**: Column descriptions are formatted into a prompt asking for JSON array
2. **LLM Call**: Single call to OpenAI generates all rows
3. **Response Parsing**: JSON response is parsed and validated
4. **DataFrame Creation**: Data converted to pandas DataFrame
5. **File Output**: Optional save to CSV/JSON/Parquet/Excel

### Example LLM Interaction

**Prompt sent:**
```
Generate a dataset with exactly 5 rows containing the following columns:

- name: Person's full name
- age: Age between 25 and 55
- churned (target): Boolean indicating if customer churned

Return ONLY a valid JSON array of objects. No explanation, no markdown, just the JSON array.
```

**LLM Response:**
```json
[
  {"name": "John Smith", "age": 34, "churned": false},
  {"name": "Sarah Johnson", "age": 28, "churned": true},
  ...
]
```

## Testing

```bash
# Run all tests (excluding integration)
pytest tests/ -v -m "not integration"

# Run integration tests (requires OPENAI_API_KEY)
pytest tests/ -v -m integration

# Run all tests
pytest tests/ -v

# Run with short traceback
pytest tests/ -v --tb=short
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

### Import Patterns

Use absolute imports:

```python
# Correct
from makeitup.core.generator import generate_dataset_with_llm
from makeitup.core.output_formats import write_dataframe

# Incorrect (avoid relative imports)
from ..core.generator import generate_dataset_with_llm
```

## Key Files

| File | Purpose |
|------|---------|
| `api.py` | Public `make()` function |
| `core/generator.py` | LLM prompt building and response parsing |
| `core/output_formats.py` | File format writers |
| `config.py` | LLM model and temperature settings |

## Dependencies

- `langchain-openai`: OpenAI LLM integration
- `pandas`: DataFrame handling
- `pyarrow`: Parquet format support
- `openpyxl`: Excel format support
