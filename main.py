"""Dataset generation CLI with LangChain and OpenAI."""

import click
from dotenv import load_dotenv

from agent import run_agent
from logging_config import setup_logging

load_dotenv()
setup_logging()


@click.command()
@click.argument('request', nargs=-1, required=True)
@click.version_option(version="0.1.0")
def main(request):
    """
    Generate synthetic datasets using natural language requests.

    Examples:
        python main.py "Create 500 rows of customer data with names, emails, \
and phone numbers, save to customers.csv"
        python main.py "Generate 1000 rows of sales data"
    """
    user_request = " ".join(request)
    click.echo(f"Processing request: {user_request}\n")

    try:
        result = run_agent(user_request)
        click.echo(f"\n{result}")
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()
