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
