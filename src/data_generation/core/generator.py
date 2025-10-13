"""Core data generation engine."""

import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from faker import Faker

from data_generation.tools.schema_validation import validate_schema

logger = logging.getLogger(__name__)


def generate_data(schema: list[dict[str, Any]], num_rows: int) -> list[dict[str, Any]]:
    """
    Generate synthetic data based on a schema.

    Args:
        schema: List of dictionaries defining the structure and types of data to generate.
               Expected format:
               [
                   {
                       "name": "column_name",
                       "type": "int|float|date|datetime|category|text|email|phone|name|address|
                                company|product|uuid|bool|currency|percentage|reference",
                       "config": {
                           "min": value (for int/float/currency/percentage),
                           "max": value (for int/float/currency/percentage),
                           "precision": digits (for float),
                           "categories": [list] (for category),
                           "start_date": date (for date/datetime),
                           "end_date": date (for date/datetime),
                           "text_type": "first_name|last_name|full_name|street|city|state|
                                         zip|country" (for name/address),
                           "reference_file": path (for reference),
                           "reference_column": column_name (for reference)
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

    # Cache for loaded reference data
    reference_cache: dict[str, list[Any]] = {}

    for _ in range(num_rows):
        row = {}
        for column_config in schema:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})
            row[column_name] = _generate_value(fake, column_type, config, reference_cache)
        data.append(row)

    return data


def _generate_value(
    fake: Faker,
    field_type: str,
    config: dict[str, Any],
    reference_cache: dict[str, list[Any]] | None = None,
) -> Any:
    """
    Generate a single value based on the field type and configuration.

    Args:
        fake: Faker instance
        field_type: The type of field to generate
        config: Configuration dictionary for the field
        reference_cache: Cache for loaded reference data (for reference type)

    Returns:
        Generated value
    """
    if reference_cache is None:
        reference_cache = {}
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

    elif field_type == "reference":
        # Load reference data from file
        reference_file = config.get("reference_file")
        reference_column = config.get("reference_column")

        if not reference_file:
            raise ValueError("reference type requires 'reference_file' in config")
        if not reference_column:
            raise ValueError("reference type requires 'reference_column' in config")

        # Use cache key to avoid reloading the same file
        cache_key = f"{reference_file}:{reference_column}"

        if cache_key not in reference_cache:
            # Load the reference file
            ref_path = Path(reference_file)
            if not ref_path.exists():
                raise FileNotFoundError(f"Reference file not found: {reference_file}")

            # Load CSV and extract the reference column
            logger.info(
                f"Loading reference data from '{reference_file}', column '{reference_column}'"
            )
            ref_df = pd.read_csv(ref_path)

            if reference_column not in ref_df.columns:
                raise ValueError(
                    f"Column '{reference_column}' not found in {reference_file}. "
                    f"Available columns: {', '.join(ref_df.columns)}"
                )

            # Store the values in cache
            reference_cache[cache_key] = ref_df[reference_column].tolist()
            logger.debug(
                f"Cached {len(reference_cache[cache_key])} values from {reference_file}"
            )

        # Randomly select a value from the reference data
        reference_values = reference_cache[cache_key]
        return random.choice(reference_values)

    else:
        # Default fallback
        return fake.word()

