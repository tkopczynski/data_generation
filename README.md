# data-generation

Generate synthetic datasets using LLM. Describe your columns in plain English and get realistic data back.

```python
from data_generation import generate_dataset

df = generate_dataset(
    columns={
        "name": "Person's full name",
        "age": "Age between 25 and 55",
        "email": "Work email address",
    },
    num_rows=100
)
```

## Quick Start

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure
cp .env.example .env
# Add your OpenAI API key to .env
```

## Examples

### Basic Data

```python
from data_generation import generate_dataset

# Customer data
df = generate_dataset(
    columns={
        "customer_id": "Unique customer identifier",
        "name": "Customer full name",
        "email": "Email address",
        "signup_date": "Date when customer signed up, 2020-2024",
    },
    num_rows=100
)
```

### ML Dataset with Target Column

```python
df = generate_dataset(
    columns={
        "tenure_months": "Months as customer, 1-60",
        "monthly_spend": "Monthly spending in USD, 10-500",
        "support_tickets": "Number of support tickets, 0-10",
    },
    target={
        "name": "churned",
        "prompt": "Boolean indicating if customer churned"
    },
    num_rows=500
)
```

### Save to File

```python
# CSV, JSON, Parquet, or Excel - format detected from extension
df = generate_dataset(
    columns={"name": "Product name", "price": "Price in USD, 10-1000"},
    num_rows=200,
    output_path="products.csv"
)
```

## Output Formats

| Format | Extension |
|--------|-----------|
| CSV | `.csv` |
| JSON | `.json` |
| Parquet | `.parquet` |
| Excel | `.xlsx` |

## Requirements

- Python >= 3.12
- OpenAI API key

## Documentation

See [DEVELOPER.md](DEVELOPER.md) for technical details, API reference, and development setup.

## License

See LICENSE file for details.
