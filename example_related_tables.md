# Related Tables Example

This example demonstrates how to generate related tables using the `reference` type.

## Example: Users and Transactions

### Step 1: Generate the parent table (users)

```bash
python main.py "Generate 50 users with user_id (uuid), name, and email, save to users.csv"
```

### Step 2: Generate the child table (transactions)

```bash
python main.py "Generate 200 transactions with transaction_id (uuid), user_id referencing users.csv, amount (currency between 10 and 1000), and date, save to transactions.csv"
```

## Manual Schema Example

You can also create schemas manually:

### users.csv schema:
```yaml
- name: user_id
  type: uuid
- name: name
  type: name
- name: email
  type: email
- name: created_at
  type: datetime
```

### transactions.csv schema:
```yaml
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
- name: transaction_date
  type: datetime
- name: status
  type: category
  config:
    categories: [pending, completed, cancelled, refunded]
```

## Features

- **Foreign Key Relationships**: Child tables reference parent tables using the `reference` type
- **Caching**: Reference data is cached to improve performance when multiple columns reference the same file
- **Validation**: Proper error messages if reference file or column doesn't exist
- **Natural Distribution**: References are randomly selected, creating realistic many-to-one relationships

## Order Matters

Always generate the parent table FIRST, then the child tables that reference it. The agent will handle this automatically when you describe related tables in natural language.
