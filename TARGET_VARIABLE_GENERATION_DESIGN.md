# Target Variable Generation - Design Document

## Overview

This document outlines the design for adding target variable generation to the data generation tool. This feature enables ML practitioners to generate datasets where target variables have controlled relationships with features, making the data suitable for training machine learning models.

## Problem Statement

### Current Limitation
Currently, all columns are generated **independently**. Each column's value is random and has no relationship to other columns.

```python
# Current flow (generator.py:71-97)
for _ in range(num_rows):
    row = {}
    for column_config in schema:
        # Each column generated independently
        value = _generate_value(fake, column_type, config)
        row[column_name] = value
    data.append(row)
```

### Why This Matters for ML

For machine learning, you often want the **target variable to depend on features**:

**Example: Fraud Detection**
```
Features → Target
-----------------
amount=5000, hour=23, num_transactions=15 → is_fraud=True (80% probability)
amount=50, hour=14, num_transactions=1 → is_fraud=False (95% probability)
```

**Example: Customer Churn**
```
Features → Target
-----------------
tenure_months=2, support_tickets=5 → will_churn=True (70% probability)
tenure_months=60, support_tickets=0 → will_churn=False (90% probability)
```

**Current limitation:** You can generate `is_fraud` as a random boolean, but it won't correlate with features, so models can't learn meaningful patterns.

---

## Design Requirements

### Functional Requirements
1. ✅ **Rule-based targets** - "If X and Y, then target=True with probability P"
2. ✅ **Probabilistic targets** - "Add controlled noise, not perfect prediction"
3. ✅ **Multi-class support** - "Predict category A, B, or C based on features" (future)
4. ✅ **Continuous targets** - "Regression: target = f(features) + noise"
5. ✅ **Controlled class balance** - "Ensure minority class has enough samples"

### Technical Requirements
1. ✅ **Two-phase generation** - Features first, then targets
2. ✅ **Safe evaluation** - No arbitrary code execution
3. ✅ **Schema validation** - Validate target_config structure
4. ✅ **Quality degradation** - Targets can also have quality issues
5. ✅ **Backward compatibility** - Existing schemas still work

---

## Proposed Architecture

### Generation Flow

**Option Selected: Deferred Target Generation (Pragmatic)**

```python
for _ in range(num_rows):
    row = {}

    # Step 1: Generate all feature columns (non-target)
    for column_config in feature_columns:
        value = _generate_value(...)
        row[column_name] = value

    # Step 2: Generate target columns (can access feature values)
    for column_config in target_columns:
        value = _generate_target_value(row, column_config)
        row[column_name] = value

    data.append(row)
```

**Why this approach:**
- ✅ Simple implementation
- ✅ Covers 90% of ML use cases (single-level dependencies)
- ✅ Clear separation of concerns
- ✅ Easy to test

**Limitations:**
- ❌ Only single-level dependencies (targets can't depend on other targets)
- ❌ Requires features to be defined before targets in schema

---

## API Design

### Schema Format: `target_config`

Targets are identified by having a `target_config` key in their `config`:

```yaml
# Feature columns (generated first, independently)
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

# Target column (generated second, based on features)
- name: is_fraud
  type: bool
  config:
    target_config:
      generation_mode: "rule_based"
      rules:
        - condition: "transaction_amount > 5000 and hour_of_day >= 22"
          probability: 0.8
      default_probability: 0.05
```

### Three Generation Modes

#### 1. Rule-Based (Classification)

**Use case:** Binary/multi-class classification with explicit decision rules

```yaml
- name: is_fraud
  type: bool
  config:
    target_config:
      generation_mode: "rule_based"
      rules:
        - condition: "amount > 5000 and hour >= 22"
          probability: 0.8  # 80% fraud when condition true
        - condition: "num_transactions > 15"
          probability: 0.7  # 70% fraud when condition true
        - condition: "amount > 5000 and num_transactions > 10"
          probability: 0.9  # 90% fraud when both conditions true
      default_probability: 0.05  # 5% fraud otherwise (base rate)
```

**Behavior:**
- Rules evaluated in order (first match wins)
- Each rule has a condition (boolean expression) and probability
- If condition matches, generate target with that probability
- If no rules match, use `default_probability`

**Generated data:**
- High-value late-night transactions → mostly fraud
- Low-value daytime transactions → mostly legitimate
- Model can learn the pattern!

#### 2. Formula-Based (Regression)

**Use case:** Continuous targets with mathematical relationships

```yaml
- name: house_price
  type: float
  config:
    target_config:
      generation_mode: "formula"
      formula: "50000 + (bedrooms * 20000) + (sqft * 100) + noise"
      noise_std: 10000  # Add Gaussian noise with std=10000
```

**Behavior:**
- Evaluate formula using feature values
- `noise` keyword replaced with random Gaussian noise
- Returns float value

**Generated data:**
- 2 bed, 1000 sqft → ~$190k ± $10k noise
- 4 bed, 3000 sqft → ~$430k ± $10k noise
- Linear relationship with controlled noise

#### 3. Probabilistic (Weighted Features)

**Use case:** Binary classification with weighted feature influence

```yaml
- name: will_churn
  type: bool
  config:
    target_config:
      generation_mode: "probabilistic"
      base_probability: 0.2  # 20% base churn rate
      feature_weights:
        tenure_months: -0.01    # Each month reduces churn by 1%
        support_tickets: 0.05   # Each ticket increases churn by 5%
        account_balance: -0.0001  # Each dollar reduces churn slightly
      min_probability: 0.01  # Clamp to minimum 1%
      max_probability: 0.95  # Clamp to maximum 95%
```

**Behavior:**
- Start with `base_probability`
- Add weighted contribution from each feature
- Clamp to `[min_probability, max_probability]`
- Generate boolean based on final probability

**Generated data:**
- New customer (1 month, 5 tickets, $100) → ~44% churn
- Long-term customer (60 months, 0 tickets, $5000) → ~10% churn
- Weighted feature influence with bounds

---

## Implementation Plan

### File Structure

```
src/data_generation/
├── core/
│   ├── generator.py           # MODIFY: Add two-phase generation
│   └── target_generation.py   # NEW: Target generation logic
└── tools/
    └── schema_validation.py   # MODIFY: Add target_config validation

tests/
└── test_target_generation.py  # NEW: Target generation tests
```

### 1. New File: `src/data_generation/core/target_generation.py`

```python
"""Target variable generation for ML use cases."""

from typing import Any, Dict
import random


def generate_target_value(row: Dict[str, Any], column_config: Dict) -> Any:
    """
    Generate a target value based on feature values in the row.

    Args:
        row: Current row with all feature values
        column_config: Column configuration with target_config

    Returns:
        Generated target value

    Raises:
        ValueError: If generation_mode is invalid or config is malformed
    """
    target_config = column_config["config"]["target_config"]
    generation_mode = target_config["generation_mode"]

    if generation_mode == "rule_based":
        return _generate_rule_based_target(row, target_config, column_config["type"])
    elif generation_mode == "formula":
        return _generate_formula_based_target(row, target_config)
    elif generation_mode == "probabilistic":
        return _generate_probabilistic_target(row, target_config, column_config["type"])
    else:
        raise ValueError(f"Unknown generation_mode: {generation_mode}")


def _generate_rule_based_target(row: Dict[str, Any], config: Dict, target_type: str) -> Any:
    """
    Generate target using rule-based approach.

    Evaluates rules in order, returns target based on first matching condition.
    """
    rules = config.get("rules", [])
    default_prob = config.get("default_probability", 0.5)

    # Evaluate rules in order
    for rule in rules:
        condition = rule["condition"]
        probability = rule["probability"]

        if _evaluate_condition(condition, row):
            # Condition matched, use this probability
            if target_type == "bool":
                return random.random() < probability
            else:
                # Future: multi-class support
                raise NotImplementedError("Only bool targets supported in V1")

    # No rule matched, use default probability
    if target_type == "bool":
        return random.random() < default_prob
    else:
        raise NotImplementedError("Only bool targets supported in V1")


def _evaluate_condition(condition: str, row: Dict[str, Any]) -> bool:
    """
    Safely evaluate a condition string against row values.

    Args:
        condition: Boolean expression like "amount > 5000 and hour >= 22"
        row: Dictionary of feature values

    Returns:
        True if condition evaluates to True, False otherwise

    Examples:
        >>> _evaluate_condition("amount > 1000", {"amount": 1500})
        True
        >>> _evaluate_condition("x > 10 and y < 5", {"x": 15, "y": 3})
        True
    """
    # Create a safe namespace with only row values (filter out None)
    namespace = {key: value for key, value in row.items() if value is not None}

    try:
        # Safe eval (only with row values, no builtins to prevent code injection)
        return eval(condition, {"__builtins__": {}}, namespace)
    except Exception:
        # If evaluation fails (e.g., missing column), condition is False
        return False


def _generate_formula_based_target(row: Dict[str, Any], config: Dict) -> float:
    """
    Generate target using formula.

    Args:
        config: Must have "formula" key, optional "noise_std"

    Returns:
        Computed float value

    Example:
        formula: "50000 + (bedrooms * 30000) + (sqft * 100) + noise"
        noise_std: 15000
    """
    formula = config["formula"]
    noise_std = config.get("noise_std", 0.0)

    # Create namespace with row values
    namespace = {key: value for key, value in row.items() if value is not None}

    # Handle 'noise' keyword
    noise_value = random.gauss(0, noise_std) if noise_std > 0 else 0
    namespace["noise"] = noise_value

    try:
        result = eval(formula, {"__builtins__": {}}, namespace)
        return float(result)
    except Exception as e:
        raise ValueError(f"Failed to evaluate formula '{formula}': {e}")


def _generate_probabilistic_target(row: Dict[str, Any], config: Dict, target_type: str) -> Any:
    """
    Generate target using probabilistic feature weighting.

    Calculates: probability = base + sum(weight[i] * feature[i])
    Then clamps to [min_prob, max_prob]
    """
    base_prob = config.get("base_probability", 0.5)
    feature_weights = config.get("feature_weights", {})
    min_prob = config.get("min_probability", 0.0)
    max_prob = config.get("max_probability", 1.0)

    # Calculate probability based on weighted features
    probability = base_prob
    for feature_name, weight in feature_weights.items():
        if feature_name in row and row[feature_name] is not None:
            probability += weight * row[feature_name]

    # Clamp to [min_prob, max_prob]
    probability = max(min_prob, min(max_prob, probability))

    if target_type == "bool":
        return random.random() < probability
    else:
        # Future: extend to other types
        raise NotImplementedError("Only bool targets supported in V1")
```

### 2. Modify: `src/data_generation/core/generator.py`

**Changes needed:**

```python
from data_generation.core.target_generation import generate_target_value

def generate_data(schema: list[dict[str, Any]], num_rows: int) -> list[dict[str, Any]]:
    """Generate synthetic data based on a schema."""
    validate_schema(schema)

    fake = Faker()
    data = []
    reference_cache = {}
    previous_values = {field["name"]: [] for field in schema}

    # NEW: Separate target columns from feature columns
    feature_columns = []
    target_columns = []

    for column_config in schema:
        if "target_config" in column_config.get("config", {}):
            target_columns.append(column_config)
        else:
            feature_columns.append(column_config)

    for _ in range(num_rows):
        row = {}

        # NEW: Step 1 - Generate all feature columns first
        for column_config in feature_columns:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})

            # Parse quality config if present
            quality_config = None
            if "quality_config" in config:
                quality_config = QualityConfig(**config["quality_config"])

            # Generate base value
            value = _generate_value(fake, column_type, config, reference_cache)

            # Apply quality degradation
            value = apply_quality_config(
                value, column_type, quality_config, previous_values[column_name]
            )

            # Track for duplicates
            if value is not None:
                previous_values[column_name].append(value)

            row[column_name] = value

        # NEW: Step 2 - Generate target columns (can access feature values)
        for column_config in target_columns:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})

            # Generate target based on row features
            value = generate_target_value(row, column_config)

            # Targets can also have quality degradation
            if "quality_config" in config:
                quality_config = QualityConfig(**config["quality_config"])
                value = apply_quality_config(
                    value, column_type, quality_config, previous_values[column_name]
                )

            # Track for duplicates
            if value is not None:
                previous_values[column_name].append(value)

            row[column_name] = value

        data.append(row)

    return data

# _generate_value() remains unchanged
```

### 3. Modify: `src/data_generation/tools/schema_validation.py`

**Add target_config validation:**

```python
def validate_schema(schema: list) -> None:
    """Validate schema structure and configuration."""
    # ... existing validation ...

    # NEW: Validate target_config if present
    for column in schema:
        config = column.get("config", {})
        if "target_config" in config:
            validate_target_config(column)


def validate_target_config(column_config: dict) -> None:
    """
    Validate target_config structure.

    Raises:
        SchemaValidationError: If target_config is malformed
    """
    target_config = column_config["config"]["target_config"]
    column_name = column_config["name"]

    # Require generation_mode
    if "generation_mode" not in target_config:
        raise SchemaValidationError(
            f"Column {column_name}: target_config must have 'generation_mode'"
        )

    mode = target_config["generation_mode"]

    # Validate mode-specific requirements
    if mode == "rule_based":
        if "rules" not in target_config:
            raise SchemaValidationError(
                f"Column {column_name}: rule_based mode requires 'rules'"
            )

        # Validate each rule
        for i, rule in enumerate(target_config["rules"]):
            if "condition" not in rule:
                raise SchemaValidationError(
                    f"Column {column_name}: rule {i} missing 'condition'"
                )
            if "probability" not in rule:
                raise SchemaValidationError(
                    f"Column {column_name}: rule {i} missing 'probability'"
                )

            # Validate probability range
            prob = rule["probability"]
            if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                raise SchemaValidationError(
                    f"Column {column_name}: rule {i} probability must be between 0 and 1"
                )

    elif mode == "formula":
        if "formula" not in target_config:
            raise SchemaValidationError(
                f"Column {column_name}: formula mode requires 'formula'"
            )

    elif mode == "probabilistic":
        if "feature_weights" not in target_config:
            raise SchemaValidationError(
                f"Column {column_name}: probabilistic mode requires 'feature_weights'"
            )

        # Validate feature_weights is a dict
        if not isinstance(target_config["feature_weights"], dict):
            raise SchemaValidationError(
                f"Column {column_name}: feature_weights must be a dictionary"
            )

    else:
        raise SchemaValidationError(
            f"Column {column_name}: invalid generation_mode '{mode}'. "
            f"Must be 'rule_based', 'formula', or 'probabilistic'"
        )
```

### 4. New File: `tests/test_target_generation.py`

```python
"""Tests for target variable generation."""

import pytest
from data_generation.core.generator import generate_data


class TestRuleBasedTargets:
    """Test rule-based target generation."""

    def test_rule_based_single_condition(self):
        """Test single rule with high probability."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 10000.0}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {"condition": "amount > 5000", "probability": 0.9}
                        ],
                        "default_probability": 0.05,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Count fraud for high-value transactions
        high_value_fraud = sum(
            1 for row in data if row["amount"] > 5000 and row["is_fraud"]
        )
        high_value_total = sum(1 for row in data if row["amount"] > 5000)

        if high_value_total > 0:
            fraud_rate = high_value_fraud / high_value_total
            # Should be around 90% ±10%
            assert 0.8 <= fraud_rate <= 1.0

    def test_rule_based_default_probability(self):
        """Test default probability when no rules match."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 1000.0}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {"condition": "amount > 5000", "probability": 0.9}
                        ],
                        "default_probability": 0.1,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # All amounts are < 5000, so should use default probability
        fraud_count = sum(1 for row in data if row["is_fraud"])
        fraud_rate = fraud_count / len(data)

        # Should be around 10% ±5%
        assert 0.05 <= fraud_rate <= 0.15


class TestFormulaBasedTargets:
    """Test formula-based target generation."""

    def test_formula_basic_calculation(self):
        """Test basic formula without noise."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {"name": "y", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "z",
                "type": "float",
                "config": {
                    "target_config": {
                        "generation_mode": "formula",
                        "formula": "x * 10 + y * 5",
                    }
                },
            },
        ]

        data = generate_data(schema, 100)

        # Verify formula is correct for each row
        for row in data:
            expected = row["x"] * 10 + row["y"] * 5
            assert row["z"] == expected

    def test_formula_with_noise(self):
        """Test formula with Gaussian noise."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 5, "max": 5}},  # Fixed value
            {
                "name": "y",
                "type": "float",
                "config": {
                    "target_config": {
                        "generation_mode": "formula",
                        "formula": "x * 100 + noise",
                        "noise_std": 10.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # All x=5, so base value is 500
        values = [row["y"] for row in data]
        import statistics
        mean = statistics.mean(values)
        std = statistics.stdev(values)

        # Mean should be around 500 ±5
        assert 495 <= mean <= 505

        # Std should be around 10 ±3
        assert 7 <= std <= 13


class TestProbabilisticTargets:
    """Test probabilistic target generation."""

    def test_probabilistic_positive_weight(self):
        """Test positive feature weight increases probability."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 0, "max": 100}},
            {
                "name": "pass",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.0,
                        "feature_weights": {"score": 0.01},  # +1% per point
                        "min_probability": 0.0,
                        "max_probability": 1.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # High scores should have higher pass rate
        high_score_pass = sum(1 for row in data if row["score"] >= 80 and row["pass"])
        high_score_total = sum(1 for row in data if row["score"] >= 80)

        low_score_pass = sum(1 for row in data if row["score"] <= 20 and row["pass"])
        low_score_total = sum(1 for row in data if row["score"] <= 20)

        if high_score_total > 0 and low_score_total > 0:
            high_rate = high_score_pass / high_score_total
            low_rate = low_score_pass / low_score_total

            # High scores should have significantly higher pass rate
            assert high_rate > low_rate + 0.3

    def test_probabilistic_clamping(self):
        """Test min/max probability clamping."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 0, "max": 100}},
            {
                "name": "result",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.5,
                        "feature_weights": {"score": 0.02},  # Would go > 1.0
                        "min_probability": 0.1,
                        "max_probability": 0.9,  # Clamped
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Even with score=100 (prob=0.5+2.0=2.5), should clamp to 0.9
        # So we should never see 100% True for high scores
        very_high_score = [row for row in data if row["score"] >= 95]
        if len(very_high_score) >= 20:
            true_count = sum(1 for row in very_high_score if row["result"])
            # Should be around 90%, not 100%
            assert true_count < len(very_high_score)


class TestTargetWithQualityDegradation:
    """Test targets with quality degradation applied."""

    def test_target_with_nulls(self):
        """Test target can have null values via quality_config."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "y",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [{"condition": "x > 5", "probability": 1.0}],
                        "default_probability": 0.0,
                    },
                    "quality_config": {"null_rate": 0.2},
                },
            },
        ]

        data = generate_data(schema, 1000)

        null_count = sum(1 for row in data if row["y"] is None)
        null_rate = null_count / len(data)

        # Should have ~20% nulls ±3%
        assert 0.17 <= null_rate <= 0.23


class TestTargetValidation:
    """Test target_config validation."""

    def test_missing_generation_mode(self):
        """Test error when generation_mode is missing."""
        from data_generation.tools.schema_validation import SchemaValidationError

        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {"target_config": {"rules": []}},
            }
        ]

        with pytest.raises(SchemaValidationError, match="generation_mode"):
            generate_data(schema, 10)

    def test_invalid_generation_mode(self):
        """Test error for invalid generation_mode."""
        from data_generation.tools.schema_validation import SchemaValidationError

        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {"generation_mode": "invalid_mode"}
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="invalid generation_mode"):
            generate_data(schema, 10)
```

---

## Usage Examples

### Example 1: Fraud Detection

```yaml
- name: transaction_id
  type: uuid

- name: amount
  type: currency
  config:
    min: 10.0
    max: 10000.0

- name: hour
  type: int
  config:
    min: 0
    max: 23

- name: num_transactions_today
  type: int
  config:
    min: 0
    max: 50

- name: is_fraud
  type: bool
  config:
    target_config:
      generation_mode: "rule_based"
      rules:
        - condition: "amount > 5000 and hour >= 22"
          probability: 0.8
        - condition: "num_transactions_today > 15"
          probability: 0.7
      default_probability: 0.05
```

**Generated patterns:**
- High-value late-night transactions → 80% fraud
- Many transactions per day → 70% fraud
- Normal transactions → 5% fraud
- **ML models can learn these patterns!**

### Example 2: House Price Prediction

```yaml
- name: bedrooms
  type: int
  config:
    min: 1
    max: 5

- name: sqft
  type: int
  config:
    min: 500
    max: 5000

- name: age_years
  type: int
  config:
    min: 0
    max: 100

- name: price
  type: currency
  config:
    target_config:
      generation_mode: "formula"
      formula: "100000 + (bedrooms * 50000) + (sqft * 150) - (age_years * 500) + noise"
      noise_std: 20000
```

**Generated patterns:**
- More bedrooms → higher price
- Larger sqft → higher price
- Older homes → lower price
- Realistic noise prevents perfect prediction

### Example 3: Customer Churn

```yaml
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

- name: will_churn
  type: bool
  config:
    target_config:
      generation_mode: "probabilistic"
      base_probability: 0.25
      feature_weights:
        tenure_months: -0.002      # -0.2% per month
        support_tickets: 0.03       # +3% per ticket
        monthly_charges: 0.001      # +0.1% per dollar
      min_probability: 0.05
      max_probability: 0.90
```

**Generated patterns:**
- New customers with issues → high churn
- Long-term customers with low support needs → low churn
- Weighted combination of multiple features

---

## Testing Strategy

### Unit Tests (test_target_generation.py)
- ✅ Rule-based: single/multiple conditions, priority, defaults
- ✅ Formula-based: basic calculation, noise, multiple features
- ✅ Probabilistic: positive/negative weights, clamping
- ✅ Integration: targets with quality degradation
- ✅ Validation: error cases, missing configs

### Integration Tests (test_ml_validation.py - extend existing)
- ✅ Train model on generated data with targets
- ✅ Verify model achieves better-than-random performance
- ✅ Verify model learns the configured patterns

### Example Test:
```python
def test_model_learns_rule_based_pattern():
    """Verify RandomForest can learn rule-based fraud pattern."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    schema = [
        {"name": "amount", "type": "currency", "config": {"min": 10, "max": 10000}},
        {"name": "hour", "type": "int", "config": {"min": 0, "max": 23}},
        {
            "name": "is_fraud",
            "type": "bool",
            "config": {
                "target_config": {
                    "generation_mode": "rule_based",
                    "rules": [
                        {"condition": "amount > 5000 and hour >= 22", "probability": 0.9}
                    ],
                    "default_probability": 0.05,
                }
            },
        },
    ]

    data = generate_data(schema, 2000)
    df = pd.DataFrame(data)

    X = df[["amount", "hour"]].values
    y = df["is_fraud"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)

    # Should achieve good AUC (pattern is learnable)
    assert auc >= 0.75, f"Model AUC {auc} too low - pattern not learnable"
```

---

## Documentation Updates

### CLAUDE.md additions:

```markdown
## Target Variable Generation (ML Use Cases)

For machine learning use cases, you can configure target variables to depend on feature values.

### Three Generation Modes

#### 1. Rule-Based (Classification)
Generate boolean targets based on conditional rules:

```yaml
- name: is_fraud
  type: bool
  config:
    target_config:
      generation_mode: "rule_based"
      rules:
        - condition: "amount > 5000 and hour >= 22"
          probability: 0.8
      default_probability: 0.05
```

#### 2. Formula-Based (Regression)
Generate continuous targets using mathematical formulas:

```yaml
- name: price
  type: float
  config:
    target_config:
      generation_mode: "formula"
      formula: "base_value + (feature1 * 100) + noise"
      noise_std: 1000
```

#### 3. Probabilistic (Weighted Features)
Generate targets using weighted feature combinations:

```yaml
- name: will_churn
  type: bool
  config:
    target_config:
      generation_mode: "probabilistic"
      base_probability: 0.2
      feature_weights:
        tenure_months: -0.01
        support_tickets: 0.05
      min_probability: 0.01
      max_probability: 0.95
```

### Important Notes
- Feature columns must be defined **before** target columns in schema
- Targets are generated after all features, so they can access feature values
- Targets can also have `quality_config` for null/duplicate/outlier injection
- Use `eval()` safely - only row values accessible, no arbitrary code execution
```

---

## Benefits

### For ML Practitioners
- ✅ **Realistic training data** - Targets correlate with features
- ✅ **Controlled patterns** - Specify exact decision boundaries
- ✅ **Reproducible experiments** - Same schema → same pattern
- ✅ **Testable models** - Verify models learn what you expect

### For Data Scientists
- ✅ **Prototype quickly** - Generate training data before collecting real data
- ✅ **Test edge cases** - Generate rare scenarios (fraud, failures, outliers)
- ✅ **Benchmark models** - Compare model performance on known patterns
- ✅ **Educational** - Teach ML concepts with controllable data

---

## Limitations (V1)

### Supported
- ✅ Boolean targets (classification)
- ✅ Float targets (regression via formula)
- ✅ Single-level dependencies (targets depend on features)
- ✅ Safe condition evaluation

### Not Yet Supported
- ❌ Multi-class categorical targets (future: use probabilities per class)
- ❌ Multi-level dependencies (target A depends on target B)
- ❌ Complex expressions (only simple arithmetic and boolean logic)
- ❌ Feature engineering within rules (must reference raw columns)

### Future Enhancements
- Multi-class support: `{"category": "A", "probability": 0.3}`
- Advanced expressions: Import `math`, `numpy` functions
- Feature transformations: `condition: "log(amount) > 5"`
- Dependency DAG: Allow targets to depend on other targets

---

## Implementation Checklist

- [ ] Create `src/data_generation/core/target_generation.py`
- [ ] Modify `src/data_generation/core/generator.py` (two-phase generation)
- [ ] Modify `src/data_generation/tools/schema_validation.py` (add validation)
- [ ] Create `tests/test_target_generation.py` (20-30 tests)
- [ ] Update `CLAUDE.md` with target generation documentation
- [ ] Add examples to README or examples/ directory
- [ ] Test with existing ML validation tests
- [ ] Verify backward compatibility (existing schemas still work)

**Estimated effort:** 1-2 days

---

## Summary

Target variable generation enables ML practitioners to create datasets where targets have meaningful relationships with features. This makes the generated data suitable for training and evaluating machine learning models.

The design uses a two-phase generation approach: features first, then targets. Three generation modes cover most ML use cases: rule-based (classification with explicit rules), formula-based (regression with mathematical relationships), and probabilistic (weighted feature influence).

Implementation is straightforward, backward compatible, and fully testable. Models trained on this data can learn the configured patterns, making it suitable for prototyping, testing, and education.
