"""Dataset generation CLI with LangChain and OpenAI."""

import click
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import pandas as pd
from io import StringIO
import config

load_dotenv()


def create_llm():
    """Create and configure the LLM."""
    return ChatOpenAI(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)


def build_prompt():
    """Build the prompt for sales data generation."""
    return """Generate 5 rows of sales data in pipe-separated format with the following columns:
- store_id: A unique store identifier (e.g., S001, S002, etc.)
- date: A date in YYYY-MM-DD format
- weekly_sales: Weekly sales amount in dollars (realistic values between 10000 and 100000)

Return ONLY the pipe-separated data (|) with headers, no additional text or explanation."""


def generate_data(llm, prompt):
    """Generate data using the LLM."""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def parse_pipe_separated(data):
    """Parse pipe-separated data into a DataFrame."""
    df = pd.read_csv(StringIO(data), sep='|', skipinitialspace=True)
    df = df.dropna(axis=1, how='all')  # Remove empty columns
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    return df


def save_to_csv(df, output_file):
    """Save DataFrame to CSV file."""
    df.to_csv(output_file, index=False)


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Dataset generation CLI with LangChain and OpenAI."""
    pass


@main.command()
def generate():
    """Generate dataset."""
    click.echo("Generating sales data...")

    llm = create_llm()
    prompt = build_prompt()
    data = generate_data(llm, prompt)

    click.echo("\n" + data)

    df = parse_pipe_separated(data)

    save_to_csv(df, config.OUTPUT_FILE)
    click.echo(f"\nSaved to {config.OUTPUT_FILE}")


if __name__ == "__main__":
    main()
