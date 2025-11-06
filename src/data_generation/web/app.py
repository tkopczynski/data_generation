"""Gradio web interface for data generation."""

import logging
import os
from pathlib import Path

import gradio as gr

from data_generation.core.agent import run_agent
from data_generation.tools.data_generation import generate_data_tool
from data_generation.tools.schema_inference import infer_schema_tool

logger = logging.getLogger(__name__)


def generate_from_natural_language(request: str, progress=gr.Progress()):
    """
    Generate data from natural language request using the ReAct agent.

    Args:
        request: Natural language description of data to generate
        progress: Gradio progress bar

    Returns:
        tuple: (status_message, file_path or None)
    """
    if not request.strip():
        return "Please enter a data generation request.", None

    try:
        progress(0.1, desc="Processing request...")

        # Run the agent
        progress(0.3, desc="Generating schema and data...")
        response = run_agent(request)

        progress(0.9, desc="Finalizing...")

        # Extract file paths from response
        # The agent returns absolute paths in its response
        files = []
        for line in response.split('\n'):
            if line.strip().endswith('.csv') and '/' in line:
                # Extract file path from response
                parts = line.split()
                for part in parts:
                    if part.endswith('.csv') and os.path.exists(part):
                        files.append(part)

        progress(1.0, desc="Complete!")

        if files:
            # Return the first file for download
            # If multiple files, show all in message
            if len(files) == 1:
                return f"✅ Data generated successfully!\n\n{response}", files[0]
            else:
                file_list = "\n".join([f"  - {f}" for f in files])
                return (
                    f"✅ Multiple files generated successfully!\n\n"
                    f"Files created:\n{file_list}\n\n"
                    f"Agent response:\n{response}",
                    files[0]  # Return first file for download
                )
        else:
            return f"⚠️ Request processed but no files were found.\n\n{response}", None

    except Exception as e:
        logger.error(f"Error in generate_from_natural_language: {e}")
        return f"❌ Error: {str(e)}", None


def generate_from_schema(schema_yaml: str, num_rows: int, output_file: str,
                         progress=gr.Progress()):
    """
    Generate data from a YAML schema (advanced mode).

    Args:
        schema_yaml: YAML schema definition
        num_rows: Number of rows to generate
        output_file: Output file name
        progress: Gradio progress bar

    Returns:
        tuple: (status_message, file_path or None)
    """
    if not schema_yaml.strip():
        return "Please provide a YAML schema.", None

    if num_rows <= 0:
        return "Number of rows must be greater than 0.", None

    if not output_file.strip():
        output_file = "generated_data.csv"

    if not output_file.endswith('.csv'):
        output_file += '.csv'

    try:
        progress(0.3, desc="Validating schema...")

        # Use the generate_data_tool directly
        progress(0.5, desc="Generating data...")
        result = generate_data_tool.invoke({
            "schema_yaml": schema_yaml,
            "num_rows": num_rows,
            "output_file": output_file
        })

        progress(1.0, desc="Complete!")

        # Extract file path from result
        if os.path.exists(result):
            return f"✅ Data generated successfully!\n\nFile: {result}", result
        else:
            return f"⚠️ Generation completed but file not found.\n\n{result}", None

    except Exception as e:
        logger.error(f"Error in generate_from_schema: {e}")
        return f"❌ Error: {str(e)}", None


def infer_schema_preview(description: str):
    """
    Preview the inferred schema from a natural language description.

    Args:
        description: Natural language description

    Returns:
        str: Inferred YAML schema
    """
    if not description.strip():
        return "Please enter a description."

    try:
        schema_yaml = infer_schema_tool.invoke({"description": description})
        return schema_yaml
    except Exception as e:
        logger.error(f"Error in infer_schema_preview: {e}")
        return f"Error: {str(e)}"


def create_gradio_interface():
    """
    Create the Gradio web interface.

    Returns:
        gr.Blocks: Gradio interface
    """

    # Custom CSS for better mobile responsiveness
    custom_css = """
    .container { max-width: 1200px; margin: auto; }
    .output-message { font-family: monospace; white-space: pre-wrap; }
    """

    with gr.Blocks(
        title="Synthetic Data Generator",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as app:

        gr.Markdown(
            """
            # 🎲 Synthetic Data Generator

            Generate realistic synthetic datasets using natural language or YAML schemas.
            Powered by LangChain and OpenAI GPT models.
            """
        )

        with gr.Tabs():
            # Tab 1: Natural Language Interface (Simple Mode)
            with gr.Tab("💬 Natural Language"):
                gr.Markdown(
                    """
                    ### Simple Mode
                    Describe the data you want in plain English and let the AI generate it for you.
                    """
                )

                with gr.Row():
                    with gr.Column():
                        nl_request = gr.Textbox(
                            label="What data would you like to generate?",
                            placeholder="Example: Generate 100 users with name, email, age between 18-80, "
                                       "and registration date",
                            lines=4,
                            elem_classes=["input-box"]
                        )

                        nl_submit = gr.Button("🚀 Generate Data", variant="primary", size="lg")

                        gr.Examples(
                            examples=[
                                "Generate 100 users with name, email, and age between 18-80",
                                "Create 500 products with product name, price between $10-$1000, "
                                "and category (electronics, clothing, food)",
                                "Generate 50 users, then 200 transactions with user_id referencing "
                                "the users",
                                "Create 1000 customers with 10% null emails and 5% duplicate names",
                            ],
                            inputs=nl_request,
                            label="Example Requests"
                        )

                    with gr.Column():
                        nl_output = gr.Textbox(
                            label="Status",
                            lines=12,
                            elem_classes=["output-message"]
                        )
                        nl_file = gr.File(label="Download Generated Data")

                nl_submit.click(
                    fn=generate_from_natural_language,
                    inputs=[nl_request],
                    outputs=[nl_output, nl_file]
                )

            # Tab 2: Schema Preview
            with gr.Tab("🔍 Schema Preview"):
                gr.Markdown(
                    """
                    ### Preview Inferred Schema
                    See what YAML schema the AI will generate from your description before creating data.
                    """
                )

                with gr.Row():
                    with gr.Column():
                        preview_request = gr.Textbox(
                            label="Describe your data",
                            placeholder="Example: Users with name, email, and age",
                            lines=4
                        )
                        preview_submit = gr.Button("🔍 Preview Schema", variant="secondary")

                    with gr.Column():
                        preview_output = gr.Code(
                            label="Inferred YAML Schema",
                            language="yaml",
                            lines=15
                        )

                preview_submit.click(
                    fn=infer_schema_preview,
                    inputs=[preview_request],
                    outputs=[preview_output]
                )

            # Tab 3: Advanced Schema Editor
            with gr.Tab("⚙️ Advanced (YAML Schema)"):
                gr.Markdown(
                    """
                    ### Advanced Mode
                    Manually define your schema using YAML for precise control over data generation.

                    [View Schema Documentation](https://github.com/yourusername/data_generation#schema-format)
                    """
                )

                with gr.Row():
                    with gr.Column():
                        schema_input = gr.Code(
                            label="YAML Schema",
                            language="yaml",
                            lines=15,
                            value="""- name: user_id
  type: uuid

- name: name
  type: name
  config:
    text_type: full_name

- name: email
  type: email

- name: age
  type: int
  config:
    min: 18
    max: 80
"""
                        )

                        with gr.Row():
                            num_rows_input = gr.Number(
                                label="Number of Rows",
                                value=100,
                                minimum=1,
                                maximum=100000
                            )
                            output_file_input = gr.Textbox(
                                label="Output Filename",
                                value="generated_data.csv"
                            )

                        schema_submit = gr.Button("🚀 Generate Data", variant="primary", size="lg")

                    with gr.Column():
                        schema_output = gr.Textbox(
                            label="Status",
                            lines=12,
                            elem_classes=["output-message"]
                        )
                        schema_file = gr.File(label="Download Generated Data")

                schema_submit.click(
                    fn=generate_from_schema,
                    inputs=[schema_input, num_rows_input, output_file_input],
                    outputs=[schema_output, schema_file]
                )

            # Tab 4: Documentation
            with gr.Tab("📚 Help"):
                gr.Markdown(
                    """
                    ## Quick Start Guide

                    ### Supported Data Types

                    - **Numeric**: `int`, `float`, `currency`, `percentage`
                    - **Date/Time**: `date`, `datetime`
                    - **Text**: `text`, `name`, `address`, `company`, `product`
                    - **Contact**: `email`, `phone`
                    - **Identifiers**: `uuid`
                    - **Logical**: `bool`, `category`
                    - **Relationships**: `reference` (for foreign keys)

                    ### Example YAML Schema

                    ```yaml
                    - name: user_id
                      type: uuid

                    - name: email
                      type: email
                      config:
                        quality_config:
                          null_rate: 0.1  # 10% nulls
                          duplicate_rate: 0.05  # 5% duplicates

                    - name: age
                      type: int
                      config:
                        min: 18
                        max: 80

                    - name: status
                      type: category
                      config:
                        categories: [active, inactive, pending]
                    ```

                    ### Related Tables (Foreign Keys)

                    To create related tables:
                    1. Generate parent table first: "Generate 50 users with user_id, name, email"
                    2. Generate child table: "Generate 200 transactions with user_id referencing users.csv"

                    ### Data Quality Options

                    Add realistic data quality issues:
                    - `null_rate`: Probability of null values
                    - `duplicate_rate`: Probability of duplicate values
                    - `similar_rate`: Probability of typos/variations
                    - `outlier_rate`: Probability of statistical outliers
                    - `invalid_format_rate`: Probability of format errors

                    All rates should be between 0.0 and 1.0 (e.g., 0.1 = 10%)

                    ### Need Help?

                    - Check out the [full documentation](https://github.com/yourusername/data_generation)
                    - Report issues on [GitHub](https://github.com/yourusername/data_generation/issues)
                    """
                )

        gr.Markdown(
            """
            ---
            **Note**: This tool uses OpenAI's GPT models. Ensure your `OPENAI_API_KEY`
            is set in the environment.
            """
        )

    return app


def main():
    """Launch the Gradio web interface."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning(
            "OPENAI_API_KEY not found in environment. "
            "Please set it before using the application."
        )

    # Create and launch the interface
    app = create_gradio_interface()

    # Launch with public sharing disabled by default
    # Set share=True to create a public link
    app.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        share=False,  # Set to True for public sharing
        show_error=True
    )


if __name__ == "__main__":
    main()
