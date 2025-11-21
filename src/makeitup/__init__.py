"""makeitup - LLM-powered synthetic dataset generation."""

__version__ = "0.1.0"

from makeitup.api import generate_dataset
from makeitup.core.output_formats import SUPPORTED_FORMATS, write_dataframe

__all__ = [
    "__version__",
    "generate_dataset",
    "write_dataframe",
    "SUPPORTED_FORMATS",
]
