"""Schema inference tool using LLM."""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from data_generation import config

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

    # Target variable configuration (for ML use cases - OPTIONAL)
    target_config:
      generation_mode: rule_based|probabilistic
      # See mode-specific examples below

TARGET VARIABLE GENERATION (for ML/predictive modeling):

IMPORTANT: Only use target_config when the description EXPLICITLY mentions that a column
should DEPEND on other columns (e.g., "flag fraud if amount > 5000", "churn probability
increases with support tickets"). For independent columns like house prices, bedrooms,
ages, etc., DO NOT use target_config - just generate them as regular independent columns.

If the description explicitly mentions a target/outcome variable that should depend on
other features, use target_config with the appropriate generation_mode:

MODE 1: rule_based - For classification with explicit conditional rules
Use when: Description mentions "if/when/rule", explicit conditions, or thresholds
IMPORTANT: Use structured conditions (NOT string expressions)
Example:
  - name: is_fraud
    type: bool
    config:
      target_config:
        generation_mode: "rule_based"
        rules:
          - conditions:
              - feature: amount
                operator: ">"
                value: 5000
              - feature: hour
                operator: ">="
                value: 22
            probability: 0.8
          - conditions:
              - feature: num_transactions
                operator: ">"
                value: 15
            probability: 0.7
        default_probability: 0.05

Supported operators: ">", "<", ">=", "<=", "==", "!="
All conditions in a rule are evaluated with AND logic (all must be true)

MODE 2: probabilistic - For binary outcomes with weighted feature influence
Use when: Description mentions "probability", "likelihood", "weighted influence"
Example:
  - name: will_churn
    type: bool
    config:
      target_config:
        generation_mode: "probabilistic"
        base_probability: 0.2
        feature_weights:
          tenure_months: -0.01
          support_tickets: 0.05
        min_probability: 0.05
        max_probability: 0.9

MODE SELECTION HEURISTICS:
- Explicit conditions/rules (e.g., "fraud if amount > 5000") → rule_based
- Binary target with weighted features (e.g., "churn increases with tickets") → probabilistic
- Boolean target without conditions → rule_based with simple rules
- ALL target columns in a schema MUST use the SAME generation_mode
- For regular independent columns (prices, ages, dates, etc.) → DO NOT use target_config

IMPORTANT NOTES:
- Feature columns (non-targets) MUST be defined BEFORE target columns in the schema
- Target columns can reference feature values using column names
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
