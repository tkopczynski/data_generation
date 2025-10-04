"""Non-AI data generation tools."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from faker import Faker


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def validate_schema(schema: List[Dict[str, Any]]) -> None:
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
        "currency", "percentage"
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


def generate_data(schema: List[Dict[str, Any]], num_rows: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic data based on a schema.

    Args:
        schema: List of dictionaries defining the structure and types of data to generate.
               Expected format:
               [
                   {
                       "name": "column_name",
                       "type": "int|float|date|datetime|category|text|email|phone|name|address|company|product|uuid|bool|currency|percentage",
                       "config": {
                           "min": value (for int/float/currency/percentage),
                           "max": value (for int/float/currency/percentage),
                           "precision": digits (for float),
                           "categories": [list] (for category),
                           "start_date": date (for date/datetime),
                           "end_date": date (for date/datetime),
                           "text_type": "first_name|last_name|full_name|street|city|state|zip|country" (for name/address)
                       }
                   }
               ]
        num_rows: Number of rows to generate

    Returns:
        List of dictionaries containing the generated data

    Raises:
        SchemaValidationError: If schema is invalid
    """
    validate_schema(schema)

    fake = Faker()
    data = []

    for _ in range(num_rows):
        row = {}
        for column_config in schema:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})
            row[column_name] = _generate_value(fake, column_type, config)
        data.append(row)

    return data


def _generate_value(fake: Faker, field_type: str, config: Dict[str, Any]) -> Any:
    """
    Generate a single value based on the field type and configuration.

    Args:
        fake: Faker instance
        field_type: The type of field to generate
        config: Configuration dictionary for the field

    Returns:
        Generated value
    """
    # Numeric types
    if field_type == "int":
        min_val = config.get("min", 0)
        max_val = config.get("max", 100)
        return random.randint(min_val, max_val)

    elif field_type == "float":
        min_val = config.get("min", 0.0)
        max_val = config.get("max", 100.0)
        precision = config.get("precision", 2)
        value = random.uniform(min_val, max_val)
        return round(value, precision)

    elif field_type == "currency":
        min_val = config.get("min", 0.0)
        max_val = config.get("max", 10000.0)
        value = random.uniform(min_val, max_val)
        return round(value, 2)

    elif field_type == "percentage":
        min_val = config.get("min", 0.0)
        max_val = config.get("max", 100.0)
        value = random.uniform(min_val, max_val)
        return round(value, 2)

    # Date/Time types
    elif field_type == "date":
        start_date = config.get("start_date", datetime.now() - timedelta(days=365))
        end_date = config.get("end_date", datetime.now())
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        return fake.date_between(start_date=start_date, end_date=end_date)

    elif field_type == "datetime":
        start_date = config.get("start_date", datetime.now() - timedelta(days=365))
        end_date = config.get("end_date", datetime.now())
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        return fake.date_time_between(start_date=start_date, end_date=end_date)

    # Category type
    elif field_type == "category":
        categories = config.get("categories", ["A", "B", "C"])
        return random.choice(categories)

    # Boolean type
    elif field_type == "bool":
        return random.choice([True, False])

    # Text types using Faker
    elif field_type == "email":
        return fake.email()

    elif field_type == "phone":
        return fake.phone_number()

    elif field_type == "name":
        name_type = config.get("text_type", "full_name")
        if name_type == "first_name":
            return fake.first_name()
        elif name_type == "last_name":
            return fake.last_name()
        else:
            return fake.name()

    elif field_type == "address":
        addr_type = config.get("text_type", "full")
        if addr_type == "street":
            return fake.street_address()
        elif addr_type == "city":
            return fake.city()
        elif addr_type == "state":
            return fake.state()
        elif addr_type == "zip":
            return fake.zipcode()
        elif addr_type == "country":
            return fake.country()
        else:
            return fake.address()

    elif field_type == "company":
        return fake.company()

    elif field_type == "product":
        return fake.catch_phrase()

    elif field_type == "uuid":
        return str(uuid.uuid4())

    elif field_type == "text":
        return fake.text(max_nb_chars=200)

    else:
        # Default fallback
        return fake.word()
