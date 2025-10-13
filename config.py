"""Configuration for dataset generation."""

# LLM Configuration
LLM_MODEL = "gpt-4o-mini"

# Tool-specific temperatures
SCHEMA_INFERENCE_TEMPERATURE = 0.2  # Low temperature for consistent schema generation

# Agent Configuration
AGENT_VERBOSE = True  # Set to True to see agent reasoning and tool calls
