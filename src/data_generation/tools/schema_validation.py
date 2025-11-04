"""Schema validation utilities."""

from typing import Any


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def validate_schema(schema: list[dict[str, Any]]) -> None:
    """
    Validate the schema configuration.

    Args:
        schema: List of column configurations to validate

    Raises:
        SchemaValidationError: If schema is invalid
    """
    if not isinstance(schema, list):
        raise SchemaValidationError("Schema must be a list")

    if not schema:
        raise SchemaValidationError("Schema cannot be empty")

    valid_types = {
        "int", "float", "date", "datetime", "category", "text", "email",
        "phone", "name", "address", "company", "product", "uuid", "bool",
        "currency", "percentage", "reference"
    }

    valid_text_types = {
        "first_name", "last_name", "full_name", "street", "city",
        "state", "zip", "country", "full"
    }

    column_names = set()

    for i, column_config in enumerate(schema):
        if not isinstance(column_config, dict):
            raise SchemaValidationError(f"Column config at index {i} must be a dictionary")

        # Validate required fields
        if "name" not in column_config:
            raise SchemaValidationError(f"Column config at index {i} missing 'name' field")

        if "type" not in column_config:
            raise SchemaValidationError(f"Column '{column_config['name']}' missing 'type' field")

        column_name = column_config["name"]
        column_type = column_config["type"]

        # Check for duplicate column names
        if column_name in column_names:
            raise SchemaValidationError(f"Duplicate column name: '{column_name}'")
        column_names.add(column_name)

        # Validate type
        if column_type not in valid_types:
            raise SchemaValidationError(
                f"Column '{column_name}' has invalid type '{column_type}'. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )

        # Get config object (optional)
        config = column_config.get("config", {})
        if not isinstance(config, dict):
            raise SchemaValidationError(f"Column '{column_name}': 'config' must be a dictionary")

        # Type-specific validations
        if column_type in ("int", "float", "currency", "percentage"):
            if "min" in config and "max" in config:
                if config["min"] > config["max"]:
                    raise SchemaValidationError(
                        f"Column '{column_name}': min value cannot be greater than max value"
                    )

        if column_type == "category":
            if "categories" not in config:
                raise SchemaValidationError(
                    f"Column '{column_name}' with type 'category' must have 'categories' in config"
                )
            if not isinstance(config["categories"], list) or not config["categories"]:
                raise SchemaValidationError(
                    f"Column '{column_name}': 'categories' must be a non-empty list"
                )

        if column_type in ("name", "address"):
            if "text_type" in config:
                text_type = config["text_type"]
                if text_type not in valid_text_types:
                    raise SchemaValidationError(
                        f"Column '{column_name}' has invalid text_type '{text_type}'. "
                        f"Valid text_types: {', '.join(sorted(valid_text_types))}"
                    )

        if column_type == "reference":
            if "reference_file" not in config:
                raise SchemaValidationError(
                    f"Column '{column_name}' with type 'reference' must have "
                    "'reference_file' in config"
                )
            if "reference_column" not in config:
                raise SchemaValidationError(
                    f"Column '{column_name}' with type 'reference' must have "
                    "'reference_column' in config"
                )

        # Validate quality_config if present
        if "quality_config" in config:
            validate_quality_config(column_name, config["quality_config"])

        # Validate target_config if present
        if "target_config" in config:
            validate_target_config(column_config)

    # Validate single-mode-per-schema constraint for target columns
    validate_single_target_mode(schema)


def validate_quality_config(column_name: str, quality_config: Any) -> None:
    """
    Validate quality configuration.

    Args:
        column_name: Name of the column (for error messages)
        quality_config: Quality configuration dictionary to validate

    Raises:
        SchemaValidationError: If quality_config is invalid
    """
    if not isinstance(quality_config, dict):
        raise SchemaValidationError(
            f"Column '{column_name}': quality_config must be a dictionary"
        )

    valid_keys = {"null_rate", "duplicate_rate", "similar_rate", "outlier_rate", "invalid_format_rate"}

    for key, value in quality_config.items():
        if key not in valid_keys:
            raise SchemaValidationError(
                f"Column '{column_name}': invalid quality_config key '{key}'. "
                f"Valid keys: {', '.join(sorted(valid_keys))}"
            )

        if not isinstance(value, (int, float)):
            raise SchemaValidationError(
                f"Column '{column_name}': quality_config '{key}' must be a number, got {type(value).__name__}"
            )

        if not 0 <= value <= 1:
            raise SchemaValidationError(
                f"Column '{column_name}': quality_config '{key}' must be between 0 and 1, got {value}"
            )


def validate_target_config(column_config: dict[str, Any]) -> None:
    """
    Validate target_config structure.

    Args:
        column_config: Column configuration with target_config

    Raises:
        SchemaValidationError: If target_config is malformed
    """
    target_config = column_config["config"]["target_config"]
    column_name = column_config["name"]

    if not isinstance(target_config, dict):
        raise SchemaValidationError(
            f"Column '{column_name}': target_config must be a dictionary"
        )

    # Require generation_mode
    if "generation_mode" not in target_config:
        raise SchemaValidationError(
            f"Column '{column_name}': target_config must have 'generation_mode'"
        )

    mode = target_config["generation_mode"]
    valid_modes = {"rule_based", "probabilistic"}

    if mode not in valid_modes:
        raise SchemaValidationError(
            f"Column '{column_name}': invalid generation_mode '{mode}'. "
            f"Must be one of: {', '.join(sorted(valid_modes))}"
        )

    # Validate mode-specific requirements
    if mode == "rule_based":
        if "rules" not in target_config:
            raise SchemaValidationError(
                f"Column '{column_name}': rule_based mode requires 'rules'"
            )

        rules = target_config["rules"]
        if not isinstance(rules, list):
            raise SchemaValidationError(
                f"Column '{column_name}': 'rules' must be a list"
            )

        # Validate each rule
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise SchemaValidationError(
                    f"Column '{column_name}': rule {i} must be a dictionary"
                )

            if "conditions" not in rule:
                raise SchemaValidationError(
                    f"Column '{column_name}': rule {i} missing 'conditions'"
                )

            if "probability" not in rule:
                raise SchemaValidationError(
                    f"Column '{column_name}': rule {i} missing 'probability'"
                )

            # Validate probability range
            prob = rule["probability"]
            if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                raise SchemaValidationError(
                    f"Column '{column_name}': rule {i} probability must be between 0 and 1, got {prob}"
                )

            # Validate conditions list
            conditions = rule["conditions"]
            if not isinstance(conditions, list):
                raise SchemaValidationError(
                    f"Column '{column_name}': rule {i} 'conditions' must be a list"
                )

            # Validate each condition
            for j, condition in enumerate(conditions):
                if not isinstance(condition, dict):
                    raise SchemaValidationError(
                        f"Column '{column_name}': rule {i} condition {j} must be a dictionary"
                    )

                if "feature" not in condition:
                    raise SchemaValidationError(
                        f"Column '{column_name}': rule {i} condition {j} missing 'feature'"
                    )

                if "operator" not in condition:
                    raise SchemaValidationError(
                        f"Column '{column_name}': rule {i} condition {j} missing 'operator'"
                    )

                if "value" not in condition:
                    raise SchemaValidationError(
                        f"Column '{column_name}': rule {i} condition {j} missing 'value'"
                    )

                # Validate operator
                valid_operators = {">", "<", ">=", "<=", "==", "!="}
                operator = condition["operator"]
                if operator not in valid_operators:
                    raise SchemaValidationError(
                        f"Column '{column_name}': rule {i} condition {j} has invalid operator '{operator}'. "
                        f"Must be one of: {', '.join(sorted(valid_operators))}"
                    )

        # Validate default_probability if present
        if "default_probability" in target_config:
            default_prob = target_config["default_probability"]
            if not isinstance(default_prob, (int, float)) or not (0 <= default_prob <= 1):
                raise SchemaValidationError(
                    f"Column '{column_name}': default_probability must be between 0 and 1, got {default_prob}"
                )

    elif mode == "probabilistic":
        if "feature_weights" not in target_config:
            raise SchemaValidationError(
                f"Column '{column_name}': probabilistic mode requires 'feature_weights'"
            )

        # Validate feature_weights is a dict
        feature_weights = target_config["feature_weights"]
        if not isinstance(feature_weights, dict):
            raise SchemaValidationError(
                f"Column '{column_name}': feature_weights must be a dictionary"
            )

        # Validate all weights are numeric
        for feature_name, weight in feature_weights.items():
            if not isinstance(weight, (int, float)):
                raise SchemaValidationError(
                    f"Column '{column_name}': weight for feature '{feature_name}' must be a number, got {type(weight).__name__}"
                )

        # Validate probability bounds if present
        if "base_probability" in target_config:
            base_prob = target_config["base_probability"]
            if not isinstance(base_prob, (int, float)) or not (0 <= base_prob <= 1):
                raise SchemaValidationError(
                    f"Column '{column_name}': base_probability must be between 0 and 1, got {base_prob}"
                )

        if "min_probability" in target_config:
            min_prob = target_config["min_probability"]
            if not isinstance(min_prob, (int, float)) or not (0 <= min_prob <= 1):
                raise SchemaValidationError(
                    f"Column '{column_name}': min_probability must be between 0 and 1, got {min_prob}"
                )

        if "max_probability" in target_config:
            max_prob = target_config["max_probability"]
            if not isinstance(max_prob, (int, float)) or not (0 <= max_prob <= 1):
                raise SchemaValidationError(
                    f"Column '{column_name}': max_probability must be between 0 and 1, got {max_prob}"
                )


def validate_single_target_mode(schema: list[dict[str, Any]]) -> None:
    """
    Validate that all target columns use the same generation_mode.

    Args:
        schema: List of column configurations

    Raises:
        SchemaValidationError: If multiple target modes are found
    """
    target_modes = []

    for column_config in schema:
        config = column_config.get("config", {})
        if "target_config" in config:
            mode = config["target_config"]["generation_mode"]
            target_modes.append((column_config["name"], mode))

    if len(target_modes) > 1:
        # Check if all modes are the same
        unique_modes = set(mode for _, mode in target_modes)
        if len(unique_modes) > 1:
            mode_details = ", ".join(f"{name}={mode}" for name, mode in target_modes)
            raise SchemaValidationError(
                f"All target columns must use the same generation_mode. Found: {mode_details}"
            )
