"""Data generation package for creating synthetic datasets."""

__version__ = "0.1.0"

from data_generation.api import generate, generate_with_metadata
from data_generation.core.output_formats import SUPPORTED_FORMATS, write_dataframe

__all__ = [
    "__version__",
    "generate",
    "generate_with_metadata",
    "write_dataframe",
    "SUPPORTED_FORMATS",
]
