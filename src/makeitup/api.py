"""Programmatic API for LLM-based data generation."""

import logging
from pathlib import Path

import pandas as pd

from makeitup.core.generator import generate_dataset_with_llm
from makeitup.core.output_formats import detect_format_from_filename, write_dataframe

logger = logging.getLogger(__name__)


def make(
    columns: dict[str, str],
    num_rows: int,
    *,
    target: dict[str, str] | None = None,
    output_path: str | Path | None = None,
    quality_issues: list[str] | None = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float | None = None,
) -> pd.DataFrame:
    """
    Generate synthetic data using LLM based on column descriptions.

    Args:
        columns: Dictionary mapping column names to their descriptions.
                 Example: {"age": "Age of employees, 25-55",
                          "salary": "Annual salary in USD"}
        num_rows: Number of rows to generate
        target: Optional target column with 'name' and 'prompt' keys.
                Example: {"name": "will_churn",
                         "prompt": "Boolean indicating customer churn"}
        output_path: Optional path to save the generated data.
                     Format is inferred from extension (.csv, .json, .parquet, .xlsx).
                     If not provided, data is only returned as DataFrame.
        quality_issues: Optional list of data quality issues to introduce.
                        Supported values: "nulls", "outliers", "typos", "duplicates".
                        Example: ["nulls", "outliers"]
        model: LLM model name. Defaults to LLM_MODEL env var or "gpt-4o-mini".
        base_url: Base URL for OpenAI-compatible API. Defaults to LLM_BASE_URL env var.
                  Examples: "http://localhost:11434/v1" (Ollama),
                           "http://localhost:8000/v1" (vLLM)
        api_key: API key for the LLM service. Defaults to LLM_API_KEY or OPENAI_API_KEY env var.
        temperature: Sampling temperature (0.0-1.0). Defaults to DATA_GENERATION_TEMPERATURE
                     env var or 0.7.

    Returns:
        pandas DataFrame containing the generated data

    Examples:
        >>> df = make(
        ...     columns={
        ...         "age": "Age of working professionals, 25-55",
        ...         "salary": "Annual salary in USD, tech industry",
        ...     },
        ...     num_rows=100
        ... )

        >>> df = make(
        ...     columns={
        ...         "tenure": "Months as customer, 1-60",
        ...         "monthly_spend": "Monthly spending in USD",
        ...     },
        ...     target={
        ...         "name": "churned",
        ...         "prompt": "Boolean: true if customer left"
        ...     },
        ...     num_rows=500,
        ...     output_path="customers.parquet"
        ... )

        >>> # Using local Ollama
        >>> df = make(
        ...     columns={"name": "Full name", "city": "US city"},
        ...     num_rows=1000,
        ...     base_url="http://localhost:11434/v1",
        ...     model="llama3",
        ... )
    """
    logger.info(f"Generating dataset: {num_rows} rows, columns={list(columns.keys())}")

    # Validate target format if provided
    if target is not None:
        if not isinstance(target, dict):
            raise ValueError("target must be a dictionary with 'name' and 'prompt' keys")
        if "name" not in target or "prompt" not in target:
            raise ValueError("target must have 'name' and 'prompt' keys")

    # Validate quality_issues if provided
    valid_quality_issues = {"nulls", "outliers", "typos", "duplicates"}
    if quality_issues is not None:
        if not isinstance(quality_issues, list):
            raise ValueError("quality_issues must be a list")
        invalid = set(quality_issues) - valid_quality_issues
        if invalid:
            raise ValueError(
                f"Invalid quality_issues: {invalid}. Valid options: {sorted(valid_quality_issues)}"
            )

    # Generate data using LLM
    data = generate_dataset_with_llm(
        columns,
        num_rows,
        target,
        quality_issues,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
    )

    # Convert to DataFrame
    df = pd.DataFrame(data)

    logger.info(f"Generated {len(df)} rows with columns: {list(df.columns)}")

    # Save to file if path provided
    if output_path is not None:
        output_path = Path(output_path)
        output_format = detect_format_from_filename(str(output_path))
        if output_format is None:
            raise ValueError(
                f"Cannot infer format from '{output_path}'. "
                "Use extension: .csv, .json, .parquet, or .xlsx"
            )
        write_dataframe(df, str(output_path), output_format)
        logger.info(f"Saved to {output_path}")

    return df
