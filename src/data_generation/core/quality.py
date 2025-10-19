"""Data quality degradation module.

This module provides functions to introduce realistic data quality issues
into generated datasets, including null values, duplicates, typos, and other
common data problems.
"""

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class QualityConfig:
    """Configuration for data quality degradation.

    Attributes:
        null_rate: Probability (0.0-1.0) of generating null values
        duplicate_rate: Probability (0.0-1.0) of using a previous value (exact duplicate)
        similar_rate: Probability (0.0-1.0) of introducing typos/variations
        outlier_rate: Probability (0.0-1.0) of generating statistical outliers
        invalid_format_rate: Probability (0.0-1.0) of creating format violations
    """

    null_rate: float = 0.0
    duplicate_rate: float = 0.0
    similar_rate: float = 0.0
    outlier_rate: float = 0.0
    invalid_format_rate: float = 0.0

    def __post_init__(self):
        """Validate that all rates are between 0 and 1."""
        for field_name in ["null_rate", "duplicate_rate", "similar_rate", "outlier_rate", "invalid_format_rate"]:
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1, got {value}")


def apply_null(value: Any, rate: float) -> Any | None:
    """Apply null values at the specified rate.

    Args:
        value: The original value
        rate: Probability (0.0-1.0) of returning None

    Returns:
        None with probability rate, otherwise the original value
    """
    if random.random() < rate:
        return None
    return value


def apply_duplicate(current_value: Any, previous_values: list[Any], rate: float) -> Any:
    """Replace current value with a previous value to create duplicates.

    Args:
        current_value: The newly generated value
        previous_values: List of previously generated values for this field
        rate: Probability (0.0-1.0) of using a duplicate

    Returns:
        A randomly selected previous value with probability rate,
        otherwise the current value
    """
    if previous_values and random.random() < rate:
        return random.choice(previous_values)
    return current_value


def apply_typo(value: str, rate: float) -> str:
    """Introduce typos into string values.

    Types of typos introduced:
    - Character swap (adjacent characters swapped)
    - Character deletion (random character removed)
    - Character insertion (random character added)
    - Character replacement (random character changed)

    Args:
        value: The original string value
        rate: Probability (0.0-1.0) of introducing a typo

    Returns:
        String with typo applied with probability rate,
        otherwise original string
    """
    if not isinstance(value, str) or random.random() >= rate or len(value) < 2:
        return value

    typo_type = random.choice(["swap", "delete", "insert", "replace"])
    chars = list(value)
    pos = random.randint(0, len(chars) - 1)

    if typo_type == "swap" and pos < len(chars) - 1:
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    elif typo_type == "delete":
        chars.pop(pos)
    elif typo_type == "insert":
        chars.insert(pos, random.choice("abcdefghijklmnopqrstuvwxyz"))
    elif typo_type == "replace":
        chars[pos] = random.choice("abcdefghijklmnopqrstuvwxyz")

    return "".join(chars)


def apply_whitespace_issues(value: str, rate: float) -> str:
    """Add whitespace issues to string values.

    Types of issues introduced:
    - Leading whitespace
    - Trailing whitespace
    - Double spaces within text
    - Mixed leading and trailing whitespace

    Args:
        value: The original string value
        rate: Probability (0.0-1.0) of adding whitespace issues

    Returns:
        String with whitespace issues with probability rate,
        otherwise original string
    """
    if not isinstance(value, str) or random.random() >= rate:
        return value

    issue_type = random.choice(["leading", "trailing", "double", "mixed"])

    if issue_type == "leading":
        return "  " + value
    elif issue_type == "trailing":
        return value + "  "
    elif issue_type == "double":
        return value.replace(" ", "  ")
    else:  # mixed
        return "  " + value + "  "


def apply_outlier(value: Any, field_type: str, rate: float) -> Any:
    """Apply type-specific outliers to values.

    Args:
        value: The original value
        field_type: The type of the field (int, float, currency, percentage, etc.)
        rate: Probability (0.0-1.0) of creating an outlier

    Returns:
        Outlier value with probability rate, otherwise original value
    """
    if random.random() >= rate or value is None:
        return value

    if field_type in ["int", "float", "currency"]:
        # Multiply by large factor or make negative
        multiplier = random.choice([10, 100, 1000, -1])
        if isinstance(value, (int, float)):
            return value * multiplier
    elif field_type == "percentage":
        # Percentage > 100 or < 0
        return random.choice([150.0, 200.0, -10.0, -50.0])

    return value


def apply_format_issue(value: Any, field_type: str, rate: float) -> Any:
    """Apply format violations specific to field type.

    Args:
        value: The original value
        field_type: The type of the field (email, phone, uuid, etc.)
        rate: Probability (0.0-1.0) of creating a format violation

    Returns:
        Value with format issue with probability rate,
        otherwise original value
    """
    if random.random() >= rate or value is None:
        return value

    if field_type == "email" and isinstance(value, str):
        # Email format violations
        issues = [
            value.replace("@", ""),  # Missing @
            value.replace("@", "@@"),  # Double @
            value.replace(".", "..") if "." in value else value,  # Double dots
            value.split("@")[0] if "@" in value else value,  # Missing domain
        ]
        return random.choice(issues)

    elif field_type == "phone" and isinstance(value, str):
        # Phone format violations
        if len(value) > 3:
            return value[:-2]  # Truncate
        return value + "123"  # Add extras

    elif field_type == "uuid" and isinstance(value, str):
        # UUID format violations
        if len(value) > 20:
            return value[:20]  # Truncate
        return value.replace("-", "")  # Remove hyphens

    return value


def apply_quality_config(
    value: Any,
    field_type: str,
    quality_config: QualityConfig | None,
    previous_values: list[Any],
) -> Any:
    """Apply quality degradation to a generated value.

    This is the main function that orchestrates all quality degradation
    transformations in the correct order.

    Args:
        value: The cleanly generated value
        field_type: The type of the field
        quality_config: Quality configuration (or None for clean data)
        previous_values: List of previous values for duplicate injection

    Returns:
        Value with quality issues applied according to configuration
    """
    if quality_config is None:
        return value

    # Apply null first (if null, skip other transformations)
    value = apply_null(value, quality_config.null_rate)
    if value is None:
        return None

    # Apply duplicates
    value = apply_duplicate(value, previous_values, quality_config.duplicate_rate)

    # Apply similar duplicates (typos and whitespace) - only for strings
    if isinstance(value, str):
        value = apply_typo(value, quality_config.similar_rate)
        value = apply_whitespace_issues(value, quality_config.similar_rate)

    # Apply outliers
    value = apply_outlier(value, field_type, quality_config.outlier_rate)

    # Apply format issues
    value = apply_format_issue(value, field_type, quality_config.invalid_format_rate)

    return value
