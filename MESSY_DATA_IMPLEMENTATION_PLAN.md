# Messy Data Generation - Implementation Plan

## Overview

This document outlines the design and implementation plan for adding messy/realistic data quality issues to the data generation system, including null values, duplicates, typos, outliers, and other common data quality problems.

---

## Current Architecture Understanding

The system currently generates clean, consistent data through:
- **Schema-based generation**: YAML schemas define 16+ field types
- **LangGraph agent**: Plans and executes data generation autonomously
- **Faker-powered values**: Generates realistic data per type
- **Reference support**: Maintains foreign key relationships

Key files:
- `src/data_generation/core/generator.py` - Core generation logic
- `src/data_generation/core/agent.py` - LangGraph agent
- `src/data_generation/tools/schema_inference.py` - LLM schema inference
- `src/data_generation/tools/schema_validation.py` - Validation logic

---

## Proposed Architecture

A **multi-level quality degradation system** with these extension points:

### 1. Schema-Level Configuration (Highest Priority)

Add optional `quality_config` to each column in the schema:

```yaml
- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1              # 10% null values
      duplicate_rate: 0.05        # 5% exact duplicates
      similar_rate: 0.03          # 3% typos/variations
      outlier_rate: 0.02          # 2% type-specific anomalies
      invalid_format_rate: 0.02   # 2% format violations
```

**Benefits:**
- Fine-grained control per column
- Works with existing schema structure
- LLM can infer from natural language ("10% missing emails")

---

### 2. Type-Specific Messiness Patterns

Different data types have different realistic quality issues:

| Type | Messiness Patterns |
|------|-------------------|
| **Numeric (int/float)** | Outliers (>3σ), negative values where shouldn't be, out-of-range, wrong precision |
| **Text** | Truncation, extra/leading/trailing whitespace, special chars, encoding issues (é→e) |
| **Email** | Invalid format, missing @, extra dots, typos in domain |
| **Phone** | Wrong length, invalid area codes, mixed formats, missing digits |
| **Date/Datetime** | Impossible dates (Feb 30), format inconsistencies, timezone issues, future dates |
| **Category** | Invalid values not in list, case mismatches, typos |
| **Bool** | String representations ("true" vs True), 1/0 vs True/False |
| **Reference** | Orphaned foreign keys, null references, references to non-existent IDs |
| **UUID** | Invalid format, duplicate UUIDs, truncated UUIDs |
| **Currency** | Negative amounts, excessive precision, missing decimal |
| **Percentage** | Values >100 or <0, wrong scale (5 vs 0.05) |

---

### 3. Row-Level Anomalies (Cross-Column)

Beyond individual field issues, implement logical inconsistencies:

- **Date inconsistencies**: `end_date` before `start_date`
- **Age/birthdate mismatch**: Age doesn't match calculated age from birth_date
- **Conditional nulls**: Null address but valid phone, or vice versa
- **Duplicate records**: Full rows duplicated with slight variations
- **Reference orphans**: Child records without valid parent references
- **Logical violations**: Negative inventory, order_total ≠ sum(line_items)

---

### 4. Implementation Strategy

#### New Module: `src/data_generation/core/quality.py`

```python
from dataclasses import dataclass
from typing import Any, Optional
import random
import re

@dataclass
class QualityConfig:
    """Configuration for data quality degradation"""
    null_rate: float = 0.0                  # 0.0-1.0: Probability of null value
    duplicate_rate: float = 0.0             # 0.0-1.0: Exact duplicates
    similar_rate: float = 0.0               # 0.0-1.0: Near-duplicates with typos
    outlier_rate: float = 0.0               # 0.0-1.0: Statistical outliers
    invalid_format_rate: float = 0.0        # 0.0-1.0: Format violations

    def __post_init__(self):
        """Validate rates are between 0 and 1"""
        for field in [self.null_rate, self.duplicate_rate, self.similar_rate,
                      self.outlier_rate, self.invalid_format_rate]:
            if not 0 <= field <= 1:
                raise ValueError(f"Quality config rates must be between 0 and 1")

# Core quality degradation functions
def apply_null(value: Any, rate: float) -> Any | None:
    """Apply null values at specified rate"""
    if random.random() < rate:
        return None
    return value

def apply_duplicate(current_value: Any, previous_values: list, rate: float) -> Any:
    """Replace with a previous value to create duplicates"""
    if previous_values and random.random() < rate:
        return random.choice(previous_values)
    return current_value

def apply_typo(value: str, rate: float) -> str:
    """Introduce typos: character swap, deletion, insertion"""
    if not isinstance(value, str) or random.random() >= rate or len(value) < 2:
        return value

    typo_type = random.choice(['swap', 'delete', 'insert', 'replace'])
    chars = list(value)
    pos = random.randint(0, len(chars) - 1)

    if typo_type == 'swap' and pos < len(chars) - 1:
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    elif typo_type == 'delete':
        chars.pop(pos)
    elif typo_type == 'insert':
        chars.insert(pos, random.choice('abcdefghijklmnopqrstuvwxyz'))
    elif typo_type == 'replace':
        chars[pos] = random.choice('abcdefghijklmnopqrstuvwxyz')

    return ''.join(chars)

def apply_outlier(value: Any, field_type: str, rate: float) -> Any:
    """Apply type-specific outliers"""
    if random.random() >= rate:
        return value

    if field_type in ['int', 'float', 'currency']:
        # Multiply by large factor or make negative
        multiplier = random.choice([10, 100, 1000, -1])
        return value * multiplier if value else value

    elif field_type == 'percentage':
        # Percentage > 100 or < 0
        return random.choice([150, 200, -10, -50])

    elif field_type in ['date', 'datetime']:
        # Far future or far past dates - would need to handle datetime objects
        pass

    return value

def apply_format_issue(value: Any, field_type: str, rate: float) -> str:
    """Apply format violations specific to field type"""
    if random.random() >= rate or value is None:
        return value

    if field_type == 'email' and isinstance(value, str):
        # Remove @ or add extra dots
        issues = [
            value.replace('@', ''),           # Missing @
            value.replace('@', '@@'),         # Double @
            value.replace('.', '..'),         # Double dots
            value.split('@')[0] if '@' in value else value,  # Missing domain
        ]
        return random.choice(issues)

    elif field_type == 'phone' and isinstance(value, str):
        # Remove digits or add extras
        if len(value) > 3:
            return value[:-2]  # Truncate
        return value + '123'   # Add extras

    elif field_type == 'uuid' and isinstance(value, str):
        # Truncate or remove hyphens
        return value[:20] if len(value) > 20 else value.replace('-', '')

    return value

def apply_whitespace_issues(value: str, rate: float) -> str:
    """Add leading/trailing/extra whitespace"""
    if not isinstance(value, str) or random.random() >= rate:
        return value

    issue = random.choice(['leading', 'trailing', 'double', 'mixed'])

    if issue == 'leading':
        return '  ' + value
    elif issue == 'trailing':
        return value + '  '
    elif issue == 'double':
        return value.replace(' ', '  ')
    else:  # mixed
        return '  ' + value + '  '

def apply_quality_config(
    value: Any,
    field_type: str,
    quality_config: Optional[QualityConfig],
    previous_values: list
) -> Any:
    """
    Apply quality degradation to a generated value.

    Args:
        value: The cleanly generated value
        field_type: The type of the field
        quality_config: Quality configuration (or None for clean data)
        previous_values: List of previous values for duplicate injection

    Returns:
        Value with quality issues applied
    """
    if quality_config is None:
        return value

    # Apply null first (if null, skip other transformations)
    value = apply_null(value, quality_config.null_rate)
    if value is None:
        return None

    # Apply duplicates
    value = apply_duplicate(value, previous_values, quality_config.duplicate_rate)

    # Apply similar duplicates (typos)
    if isinstance(value, str):
        value = apply_typo(value, quality_config.similar_rate)
        value = apply_whitespace_issues(value, quality_config.similar_rate)

    # Apply outliers
    value = apply_outlier(value, field_type, quality_config.outlier_rate)

    # Apply format issues
    value = apply_format_issue(value, field_type, quality_config.invalid_format_rate)

    return value
```

---

#### Integration Points

**1. Update `src/data_generation/tools/schema_validation.py`**

Add validation for quality_config in schema:

```python
def validate_quality_config(quality_config: dict) -> None:
    """Validate quality_config structure"""
    if quality_config is None:
        return

    valid_keys = ['null_rate', 'duplicate_rate', 'similar_rate',
                  'outlier_rate', 'invalid_format_rate']

    for key in quality_config:
        if key not in valid_keys:
            raise ValueError(f"Invalid quality_config key: {key}")

        value = quality_config[key]
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise ValueError(f"Quality config '{key}' must be between 0 and 1")

# Add to validate_field function:
if 'quality_config' in field.get('config', {}):
    validate_quality_config(field['config']['quality_config'])
```

**2. Update `src/data_generation/core/generator.py`**

Modify `generate_data()` and `_generate_value()`:

```python
from data_generation.core.quality import QualityConfig, apply_quality_config

def generate_data(schema: list[dict], num_rows: int) -> list[dict]:
    """Generate data based on schema"""
    fake = Faker()
    data = []
    reference_cache = {}

    # Track previous values per column for duplicate injection
    previous_values = {field['name']: [] for field in schema}

    for _ in range(num_rows):
        row = {}
        for field in schema:
            field_name = field['name']
            field_type = field['type']
            config = field.get('config', {})

            # Parse quality config if present
            quality_config = None
            if 'quality_config' in config:
                quality_config = QualityConfig(**config['quality_config'])

            # Generate base value
            value = _generate_value(fake, field_type, config, reference_cache)

            # Apply quality degradation
            value = apply_quality_config(
                value,
                field_type,
                quality_config,
                previous_values[field_name]
            )

            # Track for duplicates (only track non-null values)
            if value is not None:
                previous_values[field_name].append(value)

            row[field_name] = value

        data.append(row)

    return data
```

**3. Update `src/data_generation/tools/schema_inference.py`**

Enhance LLM prompt to extract quality requirements:

```python
SCHEMA_INFERENCE_PROMPT = """
You are a data schema expert. Convert the user's description into a YAML schema.

... (existing instructions) ...

If the user mentions data quality issues, include quality_config:
- "10% nulls" → null_rate: 0.1
- "5% duplicates" → duplicate_rate: 0.05
- "some typos" → similar_rate: 0.05
- "messy data" → null_rate: 0.1, similar_rate: 0.05

Example with quality issues:
```yaml
- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1
      duplicate_rate: 0.05
```

... (rest of prompt) ...
"""
```

**4. Update `src/data_generation/core/agent.py`**

Enhance system prompt to recognize quality parameters:

```python
AGENT_SYSTEM_PROMPT = """
... (existing prompt) ...

If the user mentions data quality, messiness, or realism:
- "messy data" → include quality_config with ~10% null_rate, ~5% similar_rate
- "X% nulls/missing" → set null_rate accordingly
- "duplicates" → set duplicate_rate (default 5% if not specified)
- "realistic errors" → include mix of quality issues

Quality requirements should be passed to infer_schema_tool descriptions.

... (rest of prompt) ...
"""
```

---

### 5. Usage Examples

#### CLI Usage

```bash
# Clean data (default)
data-generation "Generate 1000 customer records with name, email, phone"

# With quality issues
data-generation "Generate 1000 customer records with name, email, phone. Make it messy with 15% null emails and 5% duplicate names"

# Multiple quality specs
data-generation "Generate 500 product records with messy data: 10% missing prices, 5% duplicate SKUs, some typos in names"
```

#### Generated Schema Example

**Input**: "Generate 1000 customers with messy emails (10% null, 5% duplicates)"

**Generated Schema**:
```yaml
- name: id
  type: int
  config:
    min: 1
    max: 100000

- name: name
  type: name
  config:
    text_type: full_name

- name: email
  type: email
  config:
    quality_config:
      null_rate: 0.1
      duplicate_rate: 0.05

- name: phone
  type: phone
```

#### Output Data Sample

```csv
id,name,email,phone
1,John Smith,john.smith@example.com,555-123-4567
2,Jane Doe,,555-234-5678                    # Null email (10% rate)
3,Bob Wilson,john.smith@example.com,555-345-6789   # Duplicate email (5% rate)
4,Alice Brown,alice.browm@example.com,555-456-7890 # Typo in email
5,Charlie Davis,charlie@example.com,555-567-8901
```

---

### 6. Statistical Validation

Add reporting to verify quality rates match configuration:

```python
def validate_quality_statistics(data: list[dict], schema: list[dict]) -> dict:
    """
    Validate that actual quality issues match configured rates.
    Returns a report dictionary.
    """
    report = {}

    for field in schema:
        field_name = field['name']
        quality_config = field.get('config', {}).get('quality_config')

        if quality_config:
            values = [row[field_name] for row in data]
            total = len(values)

            # Count nulls
            null_count = sum(1 for v in values if v is None)
            null_rate = null_count / total if total > 0 else 0

            # Count duplicates
            non_null_values = [v for v in values if v is not None]
            unique_count = len(set(str(v) for v in non_null_values))
            duplicate_count = len(non_null_values) - unique_count
            duplicate_rate = duplicate_count / total if total > 0 else 0

            report[field_name] = {
                'configured_null_rate': quality_config.get('null_rate', 0),
                'actual_null_rate': null_rate,
                'null_count': null_count,
                'configured_duplicate_rate': quality_config.get('duplicate_rate', 0),
                'actual_duplicate_rate': duplicate_rate,
                'duplicate_count': duplicate_count,
            }

    return report
```

Add to data generation tool output:
```
Generated 1000 rows with quality issues:
  - email: 103 nulls (10.3%, target 10%), 48 duplicates (4.8%, target 5%)
  - name: 52 duplicates (5.2%, target 5%)
```

---

### 7. Implementation Phases

#### Phase 1 - Foundation (2-3 hours)
- [ ] Create `src/data_generation/core/quality.py` module
- [ ] Implement `QualityConfig` dataclass
- [ ] Implement `apply_null()` function
- [ ] Update `schema_validation.py` to validate quality_config
- [ ] Update `generator.py` to accept and apply quality_config
- [ ] Basic unit tests for null injection

**Deliverable**: Can generate data with configurable null rates

#### Phase 2 - Value-Level Issues (3-4 hours)
- [ ] Implement `apply_duplicate()` - exact duplicates
- [ ] Implement `apply_typo()` - character-level errors
- [ ] Implement `apply_whitespace_issues()` - spacing problems
- [ ] Implement type-specific outliers per field type
- [ ] Implement format violations per field type
- [ ] Unit tests for each function

**Deliverable**: Full value-level quality degradation working

#### Phase 3 - Statistical Validation (2 hours)
- [ ] Implement `validate_quality_statistics()` function
- [ ] Add quality report to data generation tool output
- [ ] Add tolerance checks (actual within ±2% of target)
- [ ] Integration tests verifying statistical accuracy

**Deliverable**: Quality rates are verified and reported

#### Phase 4 - LLM Integration (2-3 hours)
- [ ] Update schema inference prompt to recognize quality keywords
- [ ] Update agent system prompt with quality guidance
- [ ] Add examples to prompts
- [ ] Test natural language parsing:
  - "messy data"
  - "X% nulls"
  - "some duplicates"
  - "realistic errors"

**Deliverable**: Natural language quality specifications work end-to-end

#### Phase 5 - Row-Level Anomalies (3-4 hours) [Optional/Future]
- [ ] Implement cross-column consistency checks
- [ ] Implement logical relationship violations
- [ ] Add row-level quality config to schema
- [ ] Tests for row-level issues

**Deliverable**: Advanced cross-column quality issues

#### Phase 6 - Documentation & Examples (1-2 hours)
- [ ] Update README.md with quality features
- [ ] Add examples to `examples/` directory
- [ ] Update CLAUDE.md with quality config guidance
- [ ] Add docstrings and type hints

**Deliverable**: Complete documentation

---

### 8. Testing Strategy

#### Unit Tests (`tests/test_quality.py`)

```python
def test_apply_null_rate():
    """Test null injection at specified rate"""
    # Run 10000 times, verify ~10% nulls (within tolerance)
    results = [apply_null("value", 0.1) for _ in range(10000)]
    null_count = sum(1 for r in results if r is None)
    assert 900 <= null_count <= 1100  # 10% ± 1%

def test_apply_typo():
    """Test typo injection changes string"""
    # Some runs should produce typos
    results = [apply_typo("example", 0.5) for _ in range(100)]
    assert any(r != "example" for r in results)

def test_quality_config_validation():
    """Test quality config validates rates"""
    with pytest.raises(ValueError):
        QualityConfig(null_rate=1.5)  # > 1
```

#### Integration Tests (`tests/test_integration_quality.py`)

```python
def test_end_to_end_quality():
    """Test quality issues through full pipeline"""
    schema = [
        {
            'name': 'email',
            'type': 'email',
            'config': {
                'quality_config': {
                    'null_rate': 0.1,
                    'duplicate_rate': 0.05
                }
            }
        }
    ]

    data = generate_data(schema, 1000)

    # Verify nulls
    null_count = sum(1 for row in data if row['email'] is None)
    assert 70 <= null_count <= 130  # 10% ± 3%

    # Verify duplicates
    emails = [row['email'] for row in data if row['email']]
    unique_count = len(set(emails))
    duplicate_count = len(emails) - unique_count
    assert 20 <= duplicate_count <= 80  # ~5% ± 3%
```

---

### 9. File Structure Summary

#### New Files
- `src/data_generation/core/quality.py` - Quality degradation logic
- `tests/test_quality.py` - Unit tests for quality functions
- `tests/test_integration_quality.py` - Integration tests
- `examples/messy_data_example.py` - Usage examples

#### Modified Files
- `src/data_generation/core/generator.py` - Integrate quality application
- `src/data_generation/tools/schema_validation.py` - Validate quality_config
- `src/data_generation/tools/schema_inference.py` - Extract quality from NL
- `src/data_generation/core/agent.py` - Guide agent on quality parameters
- `README.md` - Document quality features
- `CLAUDE.md` - Add quality guidance for Claude Code

---

### 10. Key Design Decisions

✅ **Non-intrusive**: Existing clean data generation unchanged (backward compatible)
✅ **Modular**: Quality logic separated in dedicated module
✅ **Controllable**: Fine-grained per-column configuration
✅ **LLM-friendly**: Natural language → quality_config parsing
✅ **Extensible**: Easy to add new messiness patterns
✅ **Testable**: Statistical verification of quality rates
✅ **Realistic**: Type-specific quality issues mirror real-world data problems

---

### 11. Future Enhancements

#### Row-Level Anomalies (Phase 5)
- Cross-field validation violations
- Logical inconsistencies (age vs birthdate)
- Conditional null patterns

#### Advanced Patterns
- Time-based quality degradation (older records messier)
- Geographic patterns (certain regions have more issues)
- Categorical biases (quality varies by category)

#### Quality Presets
```python
QUALITY_PRESETS = {
    'clean': {},  # No quality issues
    'slightly_messy': {'null_rate': 0.05, 'similar_rate': 0.02},
    'messy': {'null_rate': 0.15, 'duplicate_rate': 0.05, 'similar_rate': 0.05},
    'very_messy': {'null_rate': 0.25, 'duplicate_rate': 0.1, 'similar_rate': 0.1},
}
```

Usage: `data-generation "1000 customers, messy preset"`

#### Quality Profiles by Industry
- **Financial**: Low nulls, high precision requirements
- **Social Media**: High duplicates, typos common
- **IoT/Sensors**: Missing values common, outliers frequent

---

## Conclusion

This implementation plan provides a comprehensive, modular approach to generating realistic messy data while maintaining backward compatibility and leveraging the existing LLM-powered agent system. The phased approach allows incremental development and testing, with early phases delivering immediate value.

**Estimated Total Effort**: 13-18 hours for Phases 1-4, 16-24 hours including optional Phase 5.

**Immediate Next Steps**:
1. Create `quality.py` module with `QualityConfig` class
2. Implement null injection
3. Update schema validation
4. Test with simple null rate configuration
