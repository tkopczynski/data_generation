"""Dataset generation CLI with LangChain and OpenAI."""

import click
from dotenv import load_dotenv

from data_generation.core.agent import run_agent
from data_generation.core.output_formats import SUPPORTED_FORMATS
from data_generation.utils.logging import setup_logging

load_dotenv()
setup_logging()


@click.command()
@click.argument("request", nargs=-1, required=True)
@click.option(
    "--seed",
    "--reproducibility-code",
    type=int,
    default=None,
    help="Reproducibility code (6-digit number) to generate the same data. "
    "Leave blank for random generation.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    default=None,
    help="Output format (csv, json, parquet, xlsx). "
    "Overrides format specified in the request. Default: csv",
)
@click.version_option(version="0.1.0")
def main(request, seed, format):
    """
    Generate synthetic datasets using natural language requests.

    Examples:
        # Random generation (different every time)
        data-generation "100 users with emails"

        # Reproducible generation (same data every time)
        data-generation "100 users with emails" --seed 123456

        # Specify output format
        data-generation "100 users" --format json
        data-generation "100 users as JSON"  # Format in natural language

        # Multiple options
        data-generation "100 users" --seed 123456 --format parquet

    Reproducibility:
        Every generation produces a 6-digit reproducibility code.
        Use this code with --seed to recreate the exact same dataset later.

    Output Formats:
        Supported formats: csv (default), json, parquet, xlsx
        Format can be specified in the request or via --format flag.
        The --format flag overrides format mentioned in the request.
    """
    user_request = " ".join(request)

    # Build status message
    status_parts = []
    if seed:
        status_parts.append(f"Reproducibility Code: {seed}")
    if format:
        status_parts.append(f"Format: {format.upper()}")

    if status_parts:
        status = f"Processing request ({', '.join(status_parts)}): {user_request}\n"
    else:
        status = f"Processing request: {user_request}\n"

    click.echo(status)

    try:
        result = run_agent(user_request, seed, format)
        click.echo(f"\n{result}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()
