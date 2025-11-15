# Dataset Generation CLI

Generate realistic synthetic datasets with just a simple English description. Perfect for testing, demos, machine learning experiments, and development.

```bash
data-generation "Generate 1000 customers with names, emails, and purchase history"
```

That's it. The AI agent figures out the rest.

## Why Use This?

- **No code required** - Just describe what you need in plain English
- **Realistic data** - Uses GPT models to generate believable synthetic data
- **Multiple formats** - Output to CSV, JSON, Parquet, or Excel
- **Quality control** - Add realistic messiness (nulls, duplicates, typos, outliers)
- **Relationships** - Generate related tables with foreign keys
- **Reproducible** - Get the same data every time with reproducibility codes
- **ML-ready** - Generate datasets with target variables for classification/regression

## Quick Start

**1. Install:**
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**2. Configure:**
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

**3. Generate:**
```bash
data-generation "Generate 100 users with names and emails"
```

See [DEVELOPER.md](DEVELOPER.md) for detailed setup instructions.

## Features & Examples

### 1. Simple Datasets

Generate basic datasets with common data types:

```bash
# Customer data
data-generation "100 customers with names, emails, and phone numbers"

# Product catalog
data-generation "500 products with names, prices between $10 and $500, and categories"

# Event logs
data-generation "1000 events with timestamps, user IDs, and event types"
```

**Supported data types:** int, float, currency, percentage, date, datetime, text, name, address, company, product, email, phone, uuid, bool, category, reference

### 2. Multiple Output Formats

Choose your preferred format - just mention it in your request:

```bash
# JSON format
data-generation "200 users with names and emails as JSON"

# Parquet (great for analytics)
data-generation "10000 transactions in parquet format"

# Excel (for business users)
data-generation "500 products save as excel"

# Or use the --format flag
data-generation "100 users" --format json
data-generation "100 users" --format parquet
data-generation "100 users" --format xlsx
```

### 3. Related Tables (Foreign Keys)

Generate parent and child tables with relationships in a **single request**:

```bash
# Generate both tables together - the agent handles the relationship
data-generation "Generate 50 users with user_id (uuid), name, and email saved to users.csv,
  and 500 orders with order_id (uuid), user_id referencing users.csv,
  amount between $10 and $500, and order date saved to orders.csv"
```

The agent automatically:
- Generates the parent table (users) first
- Then generates the child table (orders) with `user_id` values that match users from `users.csv`
- Handles the relationship using the reference type internally

**Important:** Request both tables in one command - the agent cannot reference files from previous separate commands.

### 4. Messy Data (Quality Degradation)

Real data is messy. Add realistic quality issues:

```bash
# Add null values
data-generation "1000 users with emails (10% null)"

# Multiple quality issues
data-generation "1000 users with
  emails (15% null, 5% duplicates, 3% typos, 2% invalid format) and
  ages (5% null, 2% outliers)"
```

**Quality options:**
- **null_rate**: Missing values (e.g., `None`, `null`)
- **duplicate_rate**: Exact duplicates from previous rows
- **similar_rate**: Typos and whitespace issues (for text)
- **outlier_rate**: Statistical anomalies (numbers multiplied by 10, 100, 1000)
- **invalid_format_rate**: Format violations (malformed emails, phone numbers, UUIDs)

### 5. Reproducibility

Get the exact same dataset every time using reproducibility codes:

```bash
# First generation - you get a 6-digit code
$ data-generation "100 users with names and emails"
Generated: generated_data.csv
Reproducibility Code: 456789

# Regenerate the exact same data later
$ data-generation "100 users with names and emails" --seed 456789
```

Perfect for:
- Testing and CI/CD (consistent test data)
- Documentation (reproducible examples)
- Debugging (share exact datasets)
- Experiments (compare algorithms on identical data)

### 6. Machine Learning Datasets

Generate datasets with target variables for ML experiments:

**Classification (fraud detection):**
```bash
data-generation "1000 transactions with amount, hour_of_day, merchant_type.
  Flag as fraud if amount > $5000 and hour >= 22"
```

**Classification (customer churn):**
```bash
data-generation "2000 customers with tenure_months, support_tickets, monthly_charges.
  Churn probability increases with support tickets and decreases with tenure"
```

The agent automatically creates appropriate target variables based on your rules.

### 7. Date Ranges and Time-Based Data

Generate time-series or dated data:

```bash
# Specific date range
data-generation "365 daily sales records with dates from 2023-01-01 to 2023-12-31
  and revenue between $1000 and $10000"

# Timestamps for events
data-generation "10000 log entries with timestamps, user IDs, and event types"
```

### 8. Categories and Enumerations

Define specific categorical values:

```bash
data-generation "500 support tickets with
  status (pending, in_progress, resolved, closed) and
  priority (low, medium, high, critical)"
```

### 9. Complex Multi-Column Schemas

Combine multiple data types and configurations:

```bash
data-generation "1000 employees with
  employee_id (uuid),
  first_name, last_name,
  email (5% null, 2% invalid format),
  hire_date between 2015-01-01 and 2024-12-31,
  salary between $30000 and $150000,
  department (engineering, sales, marketing, hr, finance),
  performance_rating between 1 and 5,
  is_remote (bool)"
```

### 10. Batch Generation with Same Seed

Generate multiple related datasets with consistent randomness:

```bash
# Training data
data-generation "10000 transactions with transaction_id, customer_id, amount between $10 and $5000,
  timestamp, and status (pending, completed, failed)" --seed 123456 --format parquet

# Sample for review
data-generation "100 transactions with transaction_id, customer_id, amount between $10 and $5000,
  timestamp, and status (pending, completed, failed)" --seed 123456 --format xlsx

# API response format
data-generation "20 transactions with transaction_id, customer_id, amount between $10 and $5000,
  timestamp, and status (pending, completed, failed)" --seed 123456 --format json
```

All three files will have the same underlying data (just different row counts/formats).

## Real-World Use Cases

### Testing & Development
```bash
# Generate test users for authentication testing
data-generation "50 test users with usernames, hashed passwords, emails,
  and registration dates"

# API response mocking
data-generation "100 API response records as JSON with status codes,
  response times, and endpoints"
```

### Data Science & ML
```bash
# Binary classification dataset
data-generation "5000 loan applications with income, credit_score, loan_amount,
  employment_years. Approve if credit_score > 700 and income > $50000"
  --seed 777888

# Regression dataset
data-generation "3000 houses with bedrooms, bathrooms, sqft, year_built,
  and price between $100000 and $1000000" --format parquet
```

### Demos & Presentations
```bash
# Sales dashboard data
data-generation "365 daily sales records for 2024 with revenue, units_sold,
  product_category" --format excel

# User analytics
data-generation "10000 user sessions with session_id, user_id, duration_minutes,
  pages_viewed, converted (bool)" --format json
```

### Database Seeding
```bash
# Generate all related tables in one request
data-generation "Generate 1000 users with user_id (uuid), username, email, created_at saved to users.csv,
  5000 posts with post_id (uuid), user_id referencing users.csv, title, content, created_at saved to posts.csv,
  and 20000 comments with comment_id (uuid), post_id referencing posts.csv,
  user_id referencing users.csv, content, created_at saved to comments.csv"
```

## Command Options

```bash
data-generation [OPTIONS] DESCRIPTION

Options:
  -f, --format [csv|json|parquet|xlsx]  Output format (default: csv)
  --seed INTEGER                         6-digit reproducibility code
  --reproducibility-code INTEGER        Alias for --seed
  --output PATH                          Output file path
  --help                                 Show help message
```

## Tips & Tricks

**1. Be specific about ranges:**
```bash
# Good
data-generation "100 products with prices between $9.99 and $99.99"

# Less specific (agent will infer reasonable defaults)
data-generation "100 products with prices"
```

**2. Mention quality issues naturally:**
```bash
data-generation "500 customer records with emails, some may have typos (3%)
  and missing values (10%)"
```

**3. Generate related tables together:**
```bash
# Request all related tables in a single command
data-generation "Generate 100 customers saved to customers.csv,
  1000 orders with customer_id referencing customers.csv saved to orders.csv,
  and 5000 order_items with order_id referencing orders.csv saved to order_items.csv"
```

**4. Use seeds for reproducible experiments:**
```bash
# Same seed = same data across different formats
data-generation "1000 records" --seed 123456 --format csv
data-generation "1000 records" --seed 123456 --format json  # Identical data
```

**5. Format detection is smart:**
```bash
# All of these work
data-generation "100 users as JSON"
data-generation "100 users in JSON format"
data-generation "100 users save as json"
data-generation "100 users to json"
```

## What Makes This Different?

Most synthetic data tools require you to:
1. Define complex schemas in code or config files
2. Learn domain-specific languages
3. Write custom generators for edge cases

**This tool?** Just describe what you want:

```bash
data-generation "Generate 500 e-commerce transactions with customer IDs,
  product names, quantities, prices, timestamps from last month, and
  payment methods (credit_card, debit_card, paypal, apple_pay).
  About 5% should have missing emails and 2% should be refunded"
```

The LangGraph ReAct agent:
- Understands your intent
- Infers appropriate data types
- Configures ranges and constraints
- Adds quality issues where specified
- Generates the data
- Saves in your preferred format

## Limitations

- Requires OpenAI API key (uses GPT models)
- Schema inference uses LLM (slight non-determinism in schema, but data generation is deterministic with seeds)
- Large datasets (>100k rows) may take time to generate
- Reference types require parent files to exist first

## Documentation

- **[DEVELOPER.md](DEVELOPER.md)** - Technical setup, architecture, development guide
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive technical reference (schema format, data types, quality config)
- **[examples/related_tables.md](examples/related_tables.md)** - Detailed foreign key examples

## Requirements

- Python >= 3.12
- OpenAI API key

## License

See LICENSE file for details.

---

**Need help?** Check out the examples above or run `data-generation --help`

**Want to dive deeper?** See [DEVELOPER.md](DEVELOPER.md) for technical details and [CLAUDE.md](CLAUDE.md) for complete reference documentation.
