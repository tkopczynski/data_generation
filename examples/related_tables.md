# Related Tables Example

This example demonstrates how to generate related tables using the `reference` type.

## Example: Users and Transactions

Generate both parent and child tables in a **single request**:

```bash
data-generation "Generate 50 users with user_id (uuid), name, and email saved to users.csv,
  and 200 transactions with transaction_id (uuid), user_id referencing users.csv,
  amount (currency between 10 and 1000), and date saved to transactions.csv"
```

The agent will:
1. Generate the parent table (users.csv) first
2. Then generate the child table (transactions.csv) with user_id values referencing users.csv

**Important:** The agent cannot reference files from previous separate commands - you must request all related tables in one command.

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

## Important Notes

- **Single Request Required**: You must request all related tables in one command. The agent cannot reference files created in previous separate commands.
- **Order Handling**: When you describe related tables in natural language, the agent automatically generates the parent table first, then child tables.
- **Multiple Relationships**: You can have child tables reference multiple parent tables in the same request (e.g., comments referencing both posts and users).
