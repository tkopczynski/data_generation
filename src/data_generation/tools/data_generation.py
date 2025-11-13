"""LangChain tool for data generation."""

import logging

import pandas as pd
import yaml
from langchain_core.tools import tool

from data_generation.core.generator import generate_data_with_seed
from data_generation.core.output_formats import SUPPORTED_FORMATS, write_dataframe
from data_generation.tools.schema_validation import SchemaValidationError

logger = logging.getLogger(__name__)


@tool
def generate_data_tool(
    schema_yaml: str,
    num_rows: int,
    output_file: str = "generated_data.csv",
    seed: int | None = None,
    output_format: str = "csv",
) -> str:
    """
    Generate synthetic data based on a YAML schema and save to file.

    Args:
        schema_yaml: YAML string defining the data structure. Format:
            - name: column_name
              type: int|float|date|datetime|category|text|email|phone|name|address|
                    company|product|uuid|bool|currency|percentage|reference
              config:
                min: value (for int/float/currency/percentage)
                max: value (for int/float/currency/percentage)
                precision: digits (for float)
                categories: [list] (for category)
                start_date: "YYYY-MM-DD" (for date/datetime)
                end_date: "YYYY-MM-DD" (for date/datetime)
                text_type: first_name|last_name|full_name|street|city|state|zip|country
                           (for name/address)
                reference_file: path/to/file.csv (for reference - REQUIRED)
                reference_column: column_name (for reference - REQUIRED)
        num_rows: Number of rows to generate
        output_file: Path to save the file (default: generated_data.csv)
        seed: Reproducibility code (optional, auto-generated if not provided)
        output_format: Output format (csv, json, parquet, xlsx; default: csv)

    Returns:
        Message with file path and reproducibility code
    """
    logger.info(
        f"generate_data_tool called: output_file='{output_file}', num_rows={num_rows}, "
        f"seed={seed}, format={output_format}"
    )

    try:
        # Validate format
        if output_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {output_format}. "
                f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )

        # Parse YAML schema
        schema = yaml.safe_load(schema_yaml)
        logger.debug(f"Parsed schema with {len(schema)} columns")

        # Generate data with reproducibility
        logger.info(f"Generating {num_rows} rows of data...")
        data, seed_used = generate_data_with_seed(schema, num_rows, seed)

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Write to file in specified format
        output_path = write_dataframe(df, output_file, output_format)

        logger.info(
            f"Successfully generated {num_rows} rows and saved to {output_path}"
        )

        return (
            f"Successfully generated {num_rows} rows and saved to {output_path}\n"
            f"Format: {output_format.upper()}\n"
            f"Reproducibility Code: {seed_used}\n"
            f"(Use --seed {seed_used} to recreate this exact dataset)"
        )

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML schema: {e}") from e
    except SchemaValidationError as e:
        raise ValueError(f"Schema validation error: {e}") from e
    except Exception as e:
        raise ValueError(f"Error generating data: {e}") from e
