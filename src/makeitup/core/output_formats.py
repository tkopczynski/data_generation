"""Output format handlers for data generation."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Supported output formats
SUPPORTED_FORMATS = ["csv", "json", "parquet", "xlsx", "excel"]

# Format to file extension mapping
FORMAT_EXTENSIONS = {
    "csv": ".csv",
    "json": ".json",
    "parquet": ".parquet",
    "xlsx": ".xlsx",
    "excel": ".xlsx",  # Alias for xlsx
}


def adjust_file_extension(output_file: str, format: str) -> str:
    """
    Adjust file extension to match the specified format.

    Args:
        output_file: Original output file path
        format: Output format (csv, json, parquet, xlsx, excel)

    Returns:
        File path with correct extension for the format

    Examples:
        >>> adjust_file_extension("data.csv", "json")
        "data.json"
        >>> adjust_file_extension("output", "parquet")
        "output.parquet"
        >>> adjust_file_extension("data.csv", "excel")
        "data.xlsx"
    """
    path = Path(output_file)
    expected_extension = FORMAT_EXTENSIONS[format]

    # If the file already has the correct extension, return as-is
    if path.suffix == expected_extension:
        return output_file

    # Replace extension or add it if missing
    return str(path.with_suffix(expected_extension))


def write_dataframe(df: pd.DataFrame, output_file: str, format: str = "csv") -> Path:
    """
    Write DataFrame to file in the specified format.

    Args:
        df: pandas DataFrame to write
        output_file: Path to save the file
        format: Output format (csv, json, parquet, xlsx, excel)
               'excel' is an alias for 'xlsx'

    Returns:
        Absolute Path to the written file

    Raises:
        ValueError: If format is not supported or writing fails
    """
    if format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Adjust file extension to match format
    output_file = adjust_file_extension(output_file, format)
    output_path = Path(output_file)

    try:
        if format == "csv":
            df.to_csv(output_path, index=False)
            logger.info(f"Wrote {len(df)} rows to CSV: {output_path.absolute()}")

        elif format == "json":
            # Use records orientation for better readability and compatibility
            df.to_json(output_path, orient="records", indent=2)
            logger.info(f"Wrote {len(df)} rows to JSON: {output_path.absolute()}")

        elif format == "parquet":
            df.to_parquet(output_path, index=False, engine="pyarrow")
            logger.info(f"Wrote {len(df)} rows to Parquet: {output_path.absolute()}")

        elif format in ("xlsx", "excel"):
            df.to_excel(output_path, index=False, engine="openpyxl")
            logger.info(f"Wrote {len(df)} rows to Excel: {output_path.absolute()}")

        return output_path.absolute()

    except Exception as e:
        raise ValueError(f"Error writing {format} file: {e}") from e


def detect_format_from_filename(filename: str) -> str | None:
    """
    Detect format from file extension.

    Args:
        filename: File path or name

    Returns:
        Detected format or None if extension not recognized

    Examples:
        >>> detect_format_from_filename("data.json")
        "json"
        >>> detect_format_from_filename("output.parquet")
        "parquet"
        >>> detect_format_from_filename("data.unknown")
        None
    """
    path = Path(filename)
    extension = path.suffix.lower()

    # Reverse lookup in FORMAT_EXTENSIONS
    for fmt, ext in FORMAT_EXTENSIONS.items():
        if extension == ext:
            return fmt

    return None
