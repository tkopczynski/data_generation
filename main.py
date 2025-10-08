"""Dataset generation CLI with LangChain and OpenAI."""

import click
from dotenv import load_dotenv

from logging_config import setup_logging
from tools.generator import generate_data_tool
from tools.schema_inference import infer_schema_tool

load_dotenv()
setup_logging()


def create_generation_chain():
    """Create LCEL chain that infers schema and generates data."""

    def infer_schema(input_dict):
        """Wrapper to call infer_schema_tool."""
        description = input_dict["description"]
        schema_yaml = infer_schema_tool.invoke({"description": description})
        return {
            "schema_yaml": schema_yaml,
            "num_rows": input_dict["num_rows"],
            "output_file": input_dict["output_file"]
        }

    # Create LCEL chain using | operator
    chain = infer_schema | generate_data_tool

    return chain


@click.command()
@click.option(
    '--description',
    '-d',
    prompt='Dataset description',
    help='Natural language description of the dataset to generate'
)
@click.option(
    '--rows',
    '-n',
    default=100,
    help='Number of rows to generate (default: 100)'
)
@click.option(
    '--output',
    '-o',
    default="output.csv",
    help='Output CSV file path (default: output.csv)'
)
@click.version_option(version="0.1.0")
def main(description, rows, output):
    """Generate synthetic datasets using LangChain and OpenAI."""

    output_file = output

    click.echo(f"Generating {rows} rows of data...")
    click.echo(f"Description: {description}\n")

    # Create and run the LCEL chain
    chain = create_generation_chain()

    file_path = chain.invoke({
        "description": description,
        "num_rows": rows,
        "output_file": output_file
    })

    click.echo("\n✓ Data generated successfully!")
    click.echo(f"Saved to: {file_path}")


if __name__ == "__main__":
    main()
