# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A CLI application for generating synthetic datasets using LangChain and OpenAI's GPT models. The application uses a LangGraph ReAct agent to intelligently generate data based on natural language requests with support for data quality degradation and multi-table relationships.

## Architecture Overview

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
CSV Output (pandas DataFrame)
```

### ReAct Agent Workflow
The agent in `src/data_generation/core/agent.py` uses a ReAct (Reasoning + Acting) pattern:

1. **Reasoning Phase**: Agent analyzes the user's natural language request
2. **Schema Inference**: Calls `infer_schema_tool` to generate YAML schema
3. **Validation**: Schema validated against rules in `schema_validation.py`
4. **Generation**: Calls `generate_data_tool` with schema and row count
5. **Output**: Returns absolute path to generated CSV file

**Key Agent Behaviors:**
- Uses `gpt-4o-mini` with temperature=0 for deterministic responses
- Defaults to 100 rows if not specified
- Generates parent tables before child tables (for references)
- Detects and handles multi-table relationships

## Project Structure

The project follows the src-layout pattern for better organization and packaging:

```
data_generation/
├── src/data_generation/     # Main package
│   ├── __init__.py
│   ├── __main__.py          # Allows: python -m data_generation
│   ├── cli.py               # CLI interface (Click)
│   ├── config.py            # Configuration settings
│   ├── core/                # Core business logic
│   │   ├── agent.py         # LangGraph ReAct agent
│   │   ├── generator.py     # Data generation engine (17+ types)
│   │   ├── quality.py       # Data quality degradation module
│   │   └── target_generation.py  # Target variable generation (ML use cases)
│   ├── tools/               # LangChain tools
│   │   ├── schema_inference.py      # LLM-based schema inference
│   │   ├── data_generation.py       # Data generation tool
│   │   └── schema_validation.py     # Schema validation rules
│   └── utils/               # Utilities
│       └── logging.py
├── tests/                   # Tests mirror src structure
│   ├── test_generator.py              # 30+ generator tests
│   ├── test_schema_validation.py      # 10+ validation tests
│   ├── test_quality_validation.py     # 40+ quality tests
│   ├── test_statistical_validation.py # 20+ statistical tests
│   ├── test_ml_validation.py          # 20+ ML fitness tests
│   ├── test_model_training.py         # 30+ model training tests
│   └── test_target_generation.py      # 23 target generation tests
├── examples/                # Usage examples
│   └── related_tables.md    # Foreign key documentation
└── pyproject.toml          # Project configuration
```

## Setup and Environment

1. **Virtual environment setup:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/macOS
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```
   Dependencies are managed in `pyproject.toml` - always use this file for dependency management.

3. **Environment configuration:**
   - Copy `.env.example` to `.env`
   - Add OpenAI API key to `.env`: `OPENAI_API_KEY=your-key`

## Running the Application

After installation, you can run the CLI in several ways:

```bash
# Using the installed command
data-generation "Generate 100 users with names and emails"

# Using python module
python -m data_generation "Generate 100 users with names and emails"

# From the old main.py (still works for backward compatibility)
python main.py "Generate 100 users with names and emails"
```

## Data Types & Schema Format

### Supported Data Types (17+)

The generator in `src/data_generation/core/generator.py` supports:

| Category | Types | Configuration Options |
|----------|-------|----------------------|
| **Numeric** | `int`, `float`, `currency`, `percentage` | `min`, `max`, `precision` |
| **Date/Time** | `date`, `datetime` | `start_date`, `end_date` |
| **Text** | `text`, `name`, `address`, `company`, `product` | `text_type` (for name/address variants) |
| **Contact** | `email`, `phone` | None |
| **Identifiers** | `uuid` | None |
| **Logical** | `bool`, `category` | `categories` (list for category type) |
| **Relationships** | `reference` | `reference_file`, `reference_column` |

### YAML Schema Format

Schemas are defined as YAML lists with the following structure:

```yaml
- name: column_name          # Required: column name in output
  type: data_type            # Required: one of the supported types
  config:                    # Optional: type-specific configuration
    # Configuration options vary by type (see below)
    quality_config:          # Optional: data quality degradation
      null_rate: 0.0         # Probability of null values (0.0-1.0)
      duplicate_rate: 0.0    # Probability of duplicate values (0.0-1.0)
      similar_rate: 0.0      # Probability of typos/variations (0.0-1.0)
      outlier_rate: 0.0      # Probability of outliers (0.0-1.0)
      invalid_format_rate: 0.0  # Probability of format errors (0.0-1.0)
```

### Type-Specific Configuration Examples

**Numeric Types:**
```yaml
- name: age
  type: int
  config:
    min: 18
    max: 80

- name: price
  type: float
  config:
    min: 9.99
    max: 999.99
    precision: 2

- name: amount
  type: currency
  config:
    min: 10.0
    max: 1000.0
```

**Date/Time Types:**
```yaml
- name: birth_date
  type: date
  config:
    start_date: "1950-01-01"
    end_date: "2005-12-31"

- name: created_at
  type: datetime
  # Defaults to reasonable range if not specified
```

**Category Type:**
```yaml
- name: status
  type: category
  config:
    categories: [pending, completed, cancelled, refunded]
```

**Text Type Variants:**
```yaml
- name: first_name
  type: name
  config:
    text_type: first_name  # Options: first_name, last_name, full_name

- name: street_address
  type: address
  config:
    text_type: street  # Options: street, city, state, zip, country, full
```

**Reference Type (Foreign Keys):**
```yaml
- name: user_id
  type: reference
  config:
    reference_file: users.csv        # Path to parent CSV file
    reference_column: user_id        # Column to reference from parent
```

**Important Reference Type Notes:**
- Always generate parent tables BEFORE child tables
- Reference files are cached by `{file}:{column}` to optimize performance
- Multiple columns can reference the same file (shared cache)
- Values are randomly selected from the reference column

### Target Variable Generation (ML Use Cases)

For machine learning use cases, you can configure target variables to depend on feature values. This enables generating datasets suitable for training and evaluating ML models.

**Key Concepts:**
- **Feature columns**: Regular columns generated independently (must be defined first)
- **Target columns**: Columns with `target_config` that depend on feature values
- **Two-phase generation**: Features are generated first, then targets can access feature values
- **Single mode per schema**: All target columns must use the same `generation_mode`

#### Mode 1: Rule-Based (Classification)

Generate boolean targets based on simple threshold rules. Best for fraud detection, anomaly detection, or any binary classification with clear decision boundaries.

```yaml
# Features (generated first)
- name: transaction_amount
  type: currency
  config:
    min: 10.0
    max: 10000.0

- name: hour_of_day
  type: int
  config:
    min: 0
    max: 23

# Target (generated second, can reference features)
- name: is_fraud
  type: bool
  config:
    target_config:
      generation_mode: "rule_based"
      rules:
        - conditions:
            - feature: transaction_amount
              operator: ">"
              value: 5000
            - feature: hour_of_day
              operator: ">="
              value: 22
          probability: 0.8  # 80% fraud when ALL conditions match
        - conditions:
            - feature: transaction_amount
              operator: ">"
              value: 5000
          probability: 0.6  # 60% fraud (if previous rule didn't match)
      default_probability: 0.05  # 5% fraud otherwise
```

**Behavior:**
- Rules evaluated in order (first match wins)
- Each rule has a list of `conditions` (ALL must be true - AND logic) and a `probability`
- Supported operators: `>`, `<`, `>=`, `<=`, `==`, `!=`
- If all conditions match, generate target with that probability
- If no rules match, use `default_probability`

**Example CLI request:**
```bash
data-generation "Generate 1000 transactions. Flag as fraud if amount > 5000 and hour >= 22"
```

#### Mode 2: Probabilistic (Weighted Features)

Generate binary targets using weighted feature influence. Best for churn prediction, conversion likelihood, or any binary outcome with multiple contributing factors.

```yaml
# Features
- name: tenure_months
  type: int
  config:
    min: 1
    max: 120

- name: support_tickets
  type: int
  config:
    min: 0
    max: 20

- name: monthly_charges
  type: currency
  config:
    min: 20.0
    max: 200.0

# Target
- name: will_churn
  type: bool
  config:
    target_config:
      generation_mode: "probabilistic"
      base_probability: 0.25  # 25% base churn rate
      feature_weights:
        tenure_months: -0.002    # -0.2% per month (longer tenure = less churn)
        support_tickets: 0.03     # +3% per ticket
        monthly_charges: 0.001    # +0.1% per dollar
      min_probability: 0.05  # Clamp minimum to 5%
      max_probability: 0.90  # Clamp maximum to 90%
```

**Behavior:**
- Start with `base_probability`
- Add weighted contribution from each feature: `probability += weight * feature_value`
- Clamp to `[min_probability, max_probability]`
- Generate boolean based on final probability

**Example CLI request:**
```bash
data-generation "Generate 2000 customers. Churn probability increases with support tickets and decreases with tenure"
```

#### Target Generation Important Notes

**Schema Structure:**
- Feature columns MUST be defined BEFORE target columns
- All target columns in a schema MUST use the SAME `generation_mode`
- Targets can reference any feature column by name in conditions

**Quality Degradation:**
- Targets support all quality_config parameters (null_rate, duplicate_rate, etc.)
- Quality degradation applied AFTER target value generation

**Safe Implementation:**
- No code evaluation - uses simple dictionary comparisons
- Zero security risk - pure data structure operations
- Conditions are structured data (not string expressions)
- Invalid operators or missing features cause condition to evaluate to False

**Supported Operators:**
- `>` - greater than
- `<` - less than
- `>=` - greater than or equal
- `<=` - less than or equal
- `==` - equal to
- `!=` - not equal to

**V1 Limitations:**
- Only boolean targets for both modes
- Only AND logic within a rule (all conditions must be true)
- No OR logic between conditions (use multiple rules as workaround)
- No multi-level dependencies (targets can't depend on other targets)
- No multi-class categorical targets (future enhancement)

**LLM Mode Selection:**
The schema inference tool automatically selects the appropriate mode based on:
- Explicit conditions ("if amount > 5000") → `rule_based`
- Probability language ("churn increases with tickets") → `probabilistic`
- Users never need to specify the mode explicitly

## Data Quality Degradation

The `src/data_generation/core/quality.py` module provides sophisticated data quality degradation to simulate real-world messy data.

### QualityConfig Parameters

```python
@dataclass
class QualityConfig:
    null_rate: float = 0.0              # Probability of None/null values
    duplicate_rate: float = 0.0         # Exact duplicates from previous values
    similar_rate: float = 0.0           # Typos and whitespace variations
    outlier_rate: float = 0.0           # Statistical anomalies
    invalid_format_rate: float = 0.0    # Format violations
```

All rates must be between 0.0 and 1.0 (validated by schema validation).

### Quality Degradation Application Order

Quality issues are applied in this specific order:
1. **Null** - If applied, short-circuits other transformations
2. **Duplicate** - Replaces with random previous value
3. **Similar** - Applies typos OR whitespace issues (for strings)
4. **Outlier** - Type-specific statistical anomalies
5. **Format** - Type-specific format violations

### Type-Specific Quality Degradation

**Typo Generation (similar_rate for strings):**
- Character swap: "hello" → "hlelo"
- Character deletion: "hello" → "helo"
- Character insertion: "hello" → "helllo"
- Character replacement: "hello" → "hxllo"

**Whitespace Issues (similar_rate for strings):**
- Leading spaces: "hello" → "  hello"
- Trailing spaces: "hello" → "hello  "
- Double spaces: "hello world" → "hello  world"
- Mixed: combination of above

**Outlier Generation (outlier_rate):**
- Numeric: multiply by [10, 100, 1000, -1]
- Percentage: returns [150.0, 200.0, -10.0, -50.0]

**Format Issues (invalid_format_rate):**
- Email: remove @, double @, double dots, missing domain
- Phone: truncate digits or add extra digits
- UUID: truncate or remove hyphens

### Schema Example with Quality Degradation

```yaml
- name: user_id
  type: uuid

- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1           # 10% null values
      duplicate_rate: 0.05     # 5% duplicates
      similar_rate: 0.03       # 3% typos/whitespace
      invalid_format_rate: 0.02  # 2% format errors

- name: age
  type: int
  config:
    min: 18
    max: 80
    quality_config:
      null_rate: 0.05
      outlier_rate: 0.02       # 2% statistical outliers

- name: amount
  type: currency
  config:
    min: 10.0
    max: 1000.0
    quality_config:
      null_rate: 0.08
      duplicate_rate: 0.04
      outlier_rate: 0.03
```

## Schema Validation Rules

The `src/data_generation/tools/schema_validation.py` module enforces these rules:

### Required Fields
- Schema must be a non-empty list
- Each column must have `name` and `type` fields
- No duplicate column names allowed

### Type Validation
- Type must be one of the supported types (see Data Types section)
- Invalid types raise `SchemaValidationError`

### Type-Specific Validation

**Numeric Types (int, float, currency, percentage):**
- If `min` and `max` specified, `min` must be ≤ `max`

**Category Type:**
- Must have `categories` list in config
- Categories list must be non-empty

**Reference Type:**
- Must have `reference_file` in config
- Must have `reference_column` in config
- File must exist at generation time
- Column must exist in reference file

**Text Type Variants:**
- `text_type` must be valid for the base type
- Name variants: `first_name`, `last_name`, `full_name`
- Address variants: `street`, `city`, `state`, `zip`, `country`, `full`

### Quality Config Validation
- All rate values must be between 0.0 and 1.0
- Applies to: `null_rate`, `duplicate_rate`, `similar_rate`, `outlier_rate`, `invalid_format_rate`

### Common Validation Errors

```python
# SchemaValidationError examples:
- "Schema must be a list"
- "Schema cannot be empty"
- "Column {name}: missing required field 'type'"
- "Column {name}: invalid type '{type}'"
- "Column {name}: min value must be less than or equal to max"
- "Column {name}: categories must be a non-empty list"
- "Column {name}: reference type requires 'reference_file' in config"
- "Quality config {rate_name} must be between 0 and 1"
```

## Tools Documentation

### 1. Schema Inference Tool (`tools/schema_inference.py`)

```python
@tool
def infer_schema_tool(description: str) -> str:
    """Convert natural language description to YAML schema"""
```

**Behavior:**
- Uses ChatOpenAI with temperature=0.2 (low variance for consistency)
- Returns raw YAML string (no markdown code blocks)
- Guided by detailed prompt template with examples
- Supports all 17+ data types and configuration options

**Usage by Agent:**
```
Input: "100 users with email and age between 18-80"
Output: YAML schema with email and int columns configured
```

### 2. Data Generation Tool (`tools/data_generation.py`)

```python
@tool
def generate_data_tool(schema_yaml: str, num_rows: int,
                       output_file: str = "generated_data.csv") -> str:
    """Generate synthetic data from schema and save to CSV"""
```

**Process:**
1. Parse YAML schema
2. Validate schema (raises SchemaValidationError if invalid)
3. Call `generate_data(schema, num_rows)` from generator.py
4. Convert to pandas DataFrame
5. Save as CSV (index=False, UTF-8)
6. Return absolute file path

**Error Handling:**
- `yaml.YAMLError` → ValueError
- `SchemaValidationError` → ValueError
- File/reference errors → ValueError

### 3. Schema Validation (`tools/schema_validation.py`)

```python
def validate_schema(schema: list) -> None:
    """Validate schema structure and rules"""
    # Raises SchemaValidationError if invalid
```

**Validates:**
- Schema structure (list, non-empty)
- Required fields (name, type)
- Type validity
- Type-specific configurations
- Quality config ranges
- No duplicate columns

## Testing & Validation

The project includes 150+ tests across 6 test suites ensuring correctness and reliability.

### Test Suites

**1. Generator Tests (`tests/test_generator.py` - 30+ tests)**
- Basic generation (correct row count, column names)
- Each data type individually (int, float, date, email, uuid, etc.)
- Type-specific configurations (min/max, precision, categories)
- Complex multi-column schemas
- Reference type (basic, caching, error cases)
- Edge cases (zero rows, missing files/columns)

**2. Schema Validation Tests (`tests/test_schema_validation.py` - 10+ tests)**
- Valid schemas pass validation
- Empty/non-list schemas rejected
- Missing required fields detected
- Invalid types rejected
- Duplicate columns detected
- Min > max validation
- Category and reference config validation

**3. Quality Validation Tests (`tests/test_quality_validation.py` - 40+ tests)**
- Quality config validation (0.0-1.0 range enforcement)
- Null rate accuracy (within ±3% tolerance)
- Duplicate rate accuracy
- Similar rate (typos and whitespace)
- Outlier rate accuracy
- Format issue rate accuracy
- Combined quality issues
- Complex schemas with mixed quality settings

**4. Statistical Validation Tests (`tests/test_statistical_validation.py` - 20+ tests)**
- Numeric ranges (min/max boundaries)
- Distribution coverage (sufficient unique values)
- Mean near expected center
- Standard deviation checks
- Date range validation
- Category membership validation
- Reference value validation

**5. ML Validation Tests (`tests/test_ml_validation.py` - 20+ tests)**
- Binary classification class balance (30-70% range)
- Multiclass classification (all classes represented)
- Imbalanced class feasibility (minority ≥50 samples)
- Stratified split feasibility
- Feature correlation testing
- Feature-target relationship validation
- Data split feasibility

**6. Model Training Tests (`tests/test_model_training.py` - 30+ tests)**
- Requires scikit-learn (optional dependency)
- LogisticRegression training (binary classification)
- RandomForest training (binary + multiclass)
- RandomForest regression
- AUC/ROC metrics validation
- F1 score ranges
- R² score validation

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

**Pre-approved pytest commands** (no user confirmation needed):
- `python -m pytest tests/test_quality_validation.py -v`
- `python -m pytest tests/ -v --tb=short`
- `python -m pytest tests/test_ml_validation.py -v`
- `python -m pytest tests/test_model_training.py -v`

### Statistical Tolerance

Quality degradation tests use ±3% tolerance for rate validation:
- Configured rate: 0.10 (10%)
- Acceptable range: 7-13%
- Rationale: Randomness + statistical variation in small samples

## Common Patterns & Examples

### Pattern 1: Related Tables (Foreign Keys)

**Step 1: Generate Parent Table**
```bash
data-generation "Generate 50 users with user_id (uuid), name, and email, save to users.csv"
```

**Step 2: Generate Child Table**
```bash
data-generation "Generate 200 transactions with transaction_id (uuid), user_id referencing users.csv, amount (currency between 10 and 1000), and date, save to transactions.csv"
```

**Manual Schema Example:**
```yaml
# users.csv schema
- name: user_id
  type: uuid
- name: name
  type: name
- name: email
  type: email

# transactions.csv schema
- name: transaction_id
  type: uuid
- name: user_id
  type: reference
  config:
    reference_file: users.csv
    reference_column: user_id
- name: amount
  type: currency
  config:
    min: 10.0
    max: 1000.0
- name: status
  type: category
  config:
    categories: [pending, completed, cancelled]
```

**Key Principles:**
- Generate parent tables FIRST (before any child tables)
- Child tables use `reference` type with `reference_file` and `reference_column`
- Reference caching optimizes multiple references to the same file
- Natural many-to-one distribution (child rows reference random parent rows)

### Pattern 2: Multi-Column Schema with Quality Issues

```yaml
- name: user_id
  type: uuid

- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1
      duplicate_rate: 0.05
      similar_rate: 0.03
      invalid_format_rate: 0.02

- name: name
  type: name
  config:
    text_type: full_name
    quality_config:
      null_rate: 0.05
      similar_rate: 0.08  # Typos in names

- name: age
  type: int
  config:
    min: 18
    max: 80
    quality_config:
      null_rate: 0.03
      outlier_rate: 0.02

- name: registration_date
  type: datetime
  config:
    start_date: "2020-01-01"
    end_date: "2024-12-31"

- name: account_type
  type: category
  config:
    categories: [free, premium, enterprise]
```

### Pattern 3: Reference Caching Behavior

When multiple columns reference the same file:
```yaml
- name: customer_id
  type: reference
  config:
    reference_file: customers.csv
    reference_column: customer_id

- name: customer_name
  type: reference
  config:
    reference_file: customers.csv  # Same file - uses cached data
    reference_column: name
```

The generator caches by `{file}:{column}` key, so:
- `customers.csv:customer_id` loaded once
- `customers.csv:name` loaded once
- No redundant file I/O

## Development Notes

- Python >= 3.12 required
- The project uses src-layout for better import handling and testing
- Import paths use absolute imports: `from data_generation.core import agent`
- Configuration is centralized in `src/data_generation/config.py`
- The agent supports generating related tables using the `reference` type

### Configuration Settings (`src/data_generation/config.py`)

```python
LLM_MODEL = "gpt-4o-mini"                    # LLM for agent and inference
SCHEMA_INFERENCE_TEMPERATURE = 0.2          # Low temp for consistency
AGENT_VERBOSE = True                         # Enable detailed logging
```

### Import Patterns

```python
# Correct (absolute imports)
from data_generation.core.agent import run_agent
from data_generation.core.generator import generate_data
from data_generation.tools.schema_validation import validate_schema

# Incorrect (relative imports - avoid)
from ..core.agent import run_agent
```

## Code Quality

Ruff is used for linting and formatting:

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

Configuration is in `pyproject.toml` under `[tool.ruff]`

## Key Features Summary

- **17+ Data Types**: Comprehensive coverage from primitives to references
- **LangGraph ReAct Agent**: Autonomous workflow orchestration with multi-table support
- **Data Quality Degradation**: 5 quality dimensions (null, duplicate, similar, outlier, format)
- **Reference Type**: Foreign key relationships with intelligent caching
- **Schema Validation**: Comprehensive validation with detailed error messages
- **Statistical Testing**: 150+ tests ensuring correctness and ML readiness
- **Flexible Output**: CSV format with pandas DataFrame integration
- **Natural Language Interface**: Generate complex datasets from simple descriptions

## Error Handling Patterns

When working with this codebase, expect these error types:

```python
# Schema validation errors
SchemaValidationError  # Invalid schema structure/configuration

# File operation errors
FileNotFoundError      # Reference file doesn't exist

# Data generation errors
ValueError             # YAML parsing, invalid config, missing reference column

# CLI errors
click.Abort           # CLI execution failure
```

All errors include descriptive messages for debugging.
