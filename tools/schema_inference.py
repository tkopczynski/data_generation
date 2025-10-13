"""Schema inference tool using LLM."""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

import config

logger = logging.getLogger(__name__)


# Define the prompt template
_schema_inference_prompt = ChatPromptTemplate.from_template(
    """Based on the following description, generate a YAML schema for data generation.

Description: {description}

The schema should be in YAML format with the following structure:
- name: column_name
  type: one of (int, float, date, datetime, category, text, email, phone, name, address,
                company, product, uuid, bool, currency, percentage, reference)
  config:
    # Optional configuration based on type
    min: value (for int/float/currency/percentage)
    max: value (for int/float/currency/percentage)
    precision: digits (for float)
    categories: [list] (for category)
    start_date: "YYYY-MM-DD" (for date/datetime)
    end_date: "YYYY-MM-DD" (for date/datetime)
    text_type: first_name|last_name|full_name|street|city|state|zip|country
               (for name/address)
    reference_file: file.csv (for reference - REQUIRED)
    reference_column: column_name (for reference - REQUIRED)

IMPORTANT NOTES:
- Use the 'reference' type when you need to create relationships between tables
  (e.g., user_id in transactions referencing user_id in users.csv)
- For reference type, you MUST specify both reference_file and reference_column
- Return ONLY the raw YAML schema. Do not include markdown code blocks,
  backticks, or any formatting. Do not add any explanation before or after the YAML."""
)


@tool
def infer_schema_tool(description: str) -> str:
    """
    Infer a YAML schema from a natural language description of the dataset.

    Args:
        description: Natural language description of the dataset to generate
                     (e.g., "sales data with store ID, date, and weekly sales amount")

    Returns:
        YAML schema string that can be used with generate_data_tool
    """
    # Create the chain at runtime to ensure load_dotenv() has run
    llm = ChatOpenAI(model=config.LLM_MODEL, temperature=config.SCHEMA_INFERENCE_TEMPERATURE)
    schema_inference_chain = _schema_inference_prompt | llm | StrOutputParser()

    response_content = schema_inference_chain.invoke({"description": description})

    logger.info(f"Inferred schema:\n{response_content}")

    return response_content
