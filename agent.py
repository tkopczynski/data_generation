"""Agent for autonomous data generation."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import config
from tools.generator import generate_data_tool
from tools.schema_inference import infer_schema_tool

logger = logging.getLogger(__name__)


class DataGenerationRequest(BaseModel):
    """Structured representation of a data generation request."""

    description: str = Field(
        description="Description of what kind of data to generate, including field names"
    )
    num_rows: int = Field(
        default=100, description="Number of rows to generate", ge=1, le=100000
    )
    output_file: str = Field(
        default="generated_data.csv", description="Path to the output CSV file"
    )


def extract_request_params(user_request: str) -> DataGenerationRequest:
    """
    Extract parameters from user request using structured output.

    Args:
        user_request: Natural language request

    Returns:
        DataGenerationRequest with extracted parameters
    """
    llm = ChatOpenAI(model=config.LLM_MODEL, temperature=0)

    # Use structured output with Pydantic model
    structured_llm = llm.with_structured_output(DataGenerationRequest)

    extraction_prompt = ChatPromptTemplate.from_template(
        """Extract the data generation parameters from the user's request.

User request: {request}

Instructions:
- description: Extract what kind of data to generate, including specific field names mentioned
- num_rows: Extract how many rows (if not specified, use 100)
- output_file: Extract the output filename (if not specified, use "generated_data.csv")
"""
    )

    chain = extraction_prompt | structured_llm
    result = chain.invoke({"request": user_request})

    logger.info(f"Extracted params: {result}")
    return result


def run_agent(user_request: str) -> str:
    """
    Run the data generation process with a user request.

    This uses a simple chain approach with structured outputs instead of
    a full agent to avoid parsing issues.

    Args:
        user_request: Natural language request for data generation

    Returns:
        Success message with file path
    """
    try:
        # Step 1: Extract parameters using structured output
        logger.info(f"Processing request: {user_request}")
        params = extract_request_params(user_request)

        # Step 2: Infer schema
        logger.info(f"Inferring schema for: {params.description}")
        schema_yaml = infer_schema_tool.invoke({"description": params.description})
        logger.info(f"Inferred schema:\n{schema_yaml}")

        # Step 3: Generate data
        logger.info(f"Generating {params.num_rows} rows to {params.output_file}")
        file_path = generate_data_tool.invoke(
            {
                "schema_yaml": schema_yaml,
                "num_rows": params.num_rows,
                "output_file": params.output_file,
            }
        )

        return f"Data generated successfully! Saved to: {file_path}"

    except Exception as e:
        logger.error(f"Data generation failed: {e}")
        raise
