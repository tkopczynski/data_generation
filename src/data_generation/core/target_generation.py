"""Target variable generation for ML use cases.

This module provides functionality to generate target variables that depend on
feature values, enabling the creation of datasets suitable for machine learning
model training and evaluation.

Supports two generation modes:
1. rule_based: Classification with simple threshold-based rules
2. probabilistic: Binary classification with weighted feature influence
"""

import random
from typing import Any


def generate_target_value(row: dict[str, Any], column_config: dict) -> Any:
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
    elif generation_mode == "probabilistic":
        return _generate_probabilistic_target(row, target_config, column_config["type"])
    else:
        raise ValueError(f"Unknown generation_mode: {generation_mode}")


def _generate_rule_based_target(
    row: dict[str, Any], config: dict, target_type: str
) -> Any:
    """
    Generate target using rule-based approach with simple threshold rules.

    Evaluates rules in order, returns target based on first matching condition.
    Each rule is a simple threshold comparison (e.g., "amount > 5000").

    Args:
        row: Dictionary of feature values
        config: Target configuration with rules and default_probability
        target_type: Type of target column (bool, category, etc.)

    Returns:
        Generated target value

    Raises:
        NotImplementedError: If target_type is not 'bool' (V1 limitation)

    Example:
        config = {
            "rules": [
                {
                    "conditions": [
                        {"feature": "amount", "operator": ">", "value": 5000},
                        {"feature": "hour", "operator": ">=", "value": 22}
                    ],
                    "probability": 0.8
                }
            ],
            "default_probability": 0.05
        }
    """
    rules = config.get("rules", [])
    default_prob = config.get("default_probability", 0.5)

    # Evaluate rules in order (first match wins)
    for rule in rules:
        conditions = rule.get("conditions", [])
        probability = rule["probability"]

        # All conditions must be true (AND logic)
        if all(_evaluate_condition(cond, row) for cond in conditions):
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


def _evaluate_condition(condition: dict[str, Any], row: dict[str, Any]) -> bool:
    """
    Evaluate a simple threshold condition.

    Args:
        condition: Dict with 'feature', 'operator', and 'value' keys
        row: Dictionary of feature values

    Returns:
        True if condition matches, False otherwise

    Supported operators: >, <, >=, <=, ==, !=

    Examples:
        >>> _evaluate_condition({"feature": "amount", "operator": ">", "value": 1000}, {"amount": 1500})
        True
        >>> _evaluate_condition({"feature": "hour", "operator": ">=", "value": 22}, {"hour": 23})
        True
        >>> _evaluate_condition({"feature": "missing", "operator": ">", "value": 10}, {"x": 5})
        False
    """
    feature = condition["feature"]
    operator = condition["operator"]
    threshold = condition["value"]

    # Feature must exist and not be None
    if feature not in row or row[feature] is None:
        return False

    value = row[feature]

    # Evaluate based on operator
    try:
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            # Unknown operator, condition fails
            return False
    except (TypeError, ValueError):
        # Comparison failed (e.g., comparing incompatible types)
        return False


def _generate_probabilistic_target(
    row: dict[str, Any], config: dict, target_type: str
) -> Any:
    """
    Generate target using probabilistic feature weighting.

    Calculates: probability = base + sum(weight[i] * feature[i])
    Then clamps to [min_prob, max_prob]

    Args:
        row: Dictionary of feature values
        config: Must have base_probability and feature_weights
        target_type: Type of target column (bool supported in V1)

    Returns:
        Generated target value

    Raises:
        NotImplementedError: If target_type is not 'bool' (V1 limitation)

    Example:
        config = {
            "base_probability": 0.2,
            "feature_weights": {"tenure_months": -0.01, "support_tickets": 0.05},
            "min_probability": 0.05,
            "max_probability": 0.9
        }
        row = {"tenure_months": 10, "support_tickets": 3}
        # probability = 0.2 + (-0.01 * 10) + (0.05 * 3) = 0.2 - 0.1 + 0.15 = 0.25
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
