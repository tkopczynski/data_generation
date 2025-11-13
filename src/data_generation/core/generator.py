"""Core data generation engine."""

import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from faker import Faker

from data_generation import config
from data_generation.core.quality import QualityConfig, apply_quality_config
from data_generation.core.target_generation import generate_target_value
from data_generation.tools.schema_validation import validate_schema

logger = logging.getLogger(__name__)


def generate_reproducibility_code() -> int:
    """Generate a random 6-digit reproducibility code.

    Returns:
        Random integer between SEED_MIN and SEED_MAX (100000-999999)
    """
    return random.randint(config.SEED_MIN, config.SEED_MAX)


def _set_seed(seed: int) -> None:
    """Set seeds for Python random and Faker for reproducible generation.

    Args:
        seed: Reproducibility code to set
    """
    random.seed(seed)
    Faker.seed(seed)


def _generate_data_internal(
    schema: list[dict[str, Any]], num_rows: int, seed: int | None = None
) -> tuple[list[dict[str, Any]], int]:
    """
    Internal function to generate synthetic data with seed tracking.

    Args:
        schema: List of dictionaries defining the structure and types of data to generate.
        num_rows: Number of rows to generate
        seed: Reproducibility code (None for random generation)

    Returns:
        Tuple of (generated_data, seed_used)

    Raises:
        SchemaValidationError: If schema is invalid
    """
    validate_schema(schema)

    # Generate seed if not provided
    if seed is None:
        seed = generate_reproducibility_code()

    # Set seed for reproducible generation
    _set_seed(seed)
    logger.info(f"Using reproducibility code: {seed}")

    fake = Faker()
    data = []

    # Cache for loaded reference data
    reference_cache: dict[str, list[Any]] = {}

    # Track previous values per column for duplicate injection
    previous_values: dict[str, list[Any]] = {field["name"]: [] for field in schema}

    precomputed_quality_configs: dict[str, QualityConfig | None] = {}
    for column_config in schema:
        column_name = column_config["name"]
        config = column_config.get("config", {})
        if "quality_config" in config:
            precomputed_quality_configs[column_name] = QualityConfig(**config["quality_config"])
        else:
            precomputed_quality_configs[column_name] = None

    # Separate feature columns from target columns
    feature_columns = []
    target_columns = []

    for column_config in schema:
        if "target_config" in column_config.get("config", {}):
            target_columns.append(column_config)
        else:
            feature_columns.append(column_config)

    for _ in range(num_rows):
        row = {}

        # Step 1: Generate all feature columns first
        for column_config in feature_columns:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})

            quality_config = precomputed_quality_configs[column_name]

            # Generate base value
            value = _generate_value(fake, column_type, config, reference_cache)

            # Apply quality degradation
            value = apply_quality_config(
                value, column_type, quality_config, previous_values[column_name]
            )

            # Track for duplicates (only track non-null values)
            if value is not None:
                previous_values[column_name].append(value)

            row[column_name] = value

        # Step 2: Generate target columns (can access feature values)
        for column_config in target_columns:
            column_name = column_config["name"]
            column_type = column_config["type"]
            config = column_config.get("config", {})

            # Generate target based on row features
            value = generate_target_value(row, column_config)

            quality_config = precomputed_quality_configs[column_name]
            if quality_config is not None:
                value = apply_quality_config(
                    value, column_type, quality_config, previous_values[column_name]
                )

            # Track for duplicates (only track non-null values)
            if value is not None:
                previous_values[column_name].append(value)

            row[column_name] = value

        data.append(row)

    return data, seed


def generate_data(
    schema: list[dict[str, Any]], num_rows: int, seed: int | None = None
) -> list[dict[str, Any]]:
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
                           "reference_column": column_name (for reference),
                           "quality_config": {
                               "null_rate": 0.0-1.0,
                               "duplicate_rate": 0.0-1.0,
                               "similar_rate": 0.0-1.0,
                               "outlier_rate": 0.0-1.0,
                               "invalid_format_rate": 0.0-1.0
                           }
                       }
                   }
               ]
        num_rows: Number of rows to generate
        seed: Reproducibility code (None for random generation)

    Returns:
        List of dictionaries containing the generated data

    Raises:
        SchemaValidationError: If schema is invalid
    """
    data, _ = _generate_data_internal(schema, num_rows, seed)
    return data


def generate_data_with_seed(
    schema: list[dict[str, Any]], num_rows: int, seed: int | None = None
) -> tuple[list[dict[str, Any]], int]:
    """
    Generate synthetic data based on a schema with seed tracking.

    This function is useful when you need to know which reproducibility code
    was used for generation (e.g., for displaying to users or logging).

    Args:
        schema: List of dictionaries defining the structure and types of data to generate.
        num_rows: Number of rows to generate
        seed: Reproducibility code (None for random generation)

    Returns:
        Tuple of (generated_data, seed_used)
        - generated_data: List of dictionaries containing the generated data
        - seed_used: The actual reproducibility code used (generated if None provided)

    Raises:
        SchemaValidationError: If schema is invalid
    """
    return _generate_data_internal(schema, num_rows, seed)


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
        # Use random.getrandbits for reproducible UUID generation when seed is set
        # UUID4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        # where y is one of 8, 9, a, b
        random_bits = random.getrandbits(128)
        # Set version (4) and variant bits for UUID4
        random_bits &= ~(0xF << 76)  # Clear version bits
        random_bits |= (0x4 << 76)  # Set version to 4
        random_bits &= ~(0x3 << 62)  # Clear variant bits
        random_bits |= (0x2 << 62)  # Set variant to RFC 4122
        # Convert to UUID
        return str(uuid.UUID(int=random_bits, version=4))

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

