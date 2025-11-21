"""Tests for the generate_dataset API."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_generation import generate_dataset, write_dataframe


class TestGenerateDatasetValidation:
    """Tests for input validation in generate_dataset()."""

    def test_invalid_target_not_dict(self):
        """Test that non-dict target raises ValueError."""
        with pytest.raises(ValueError, match="target must be a dictionary"):
            generate_dataset(columns={"age": "Age of person"}, num_rows=10, target="invalid")

    def test_invalid_target_missing_name(self):
        """Test that target without 'name' raises ValueError."""
        with pytest.raises(ValueError, match="target must have 'name' and 'prompt' keys"):
            generate_dataset(
                columns={"age": "Age of person"}, num_rows=10, target={"prompt": "Some prompt"}
            )

    def test_invalid_target_missing_prompt(self):
        """Test that target without 'prompt' raises ValueError."""
        with pytest.raises(ValueError, match="target must have 'name' and 'prompt' keys"):
            generate_dataset(
                columns={"age": "Age of person"}, num_rows=10, target={"name": "target_col"}
            )

    def test_invalid_output_extension(self, tmp_path):
        """Test that invalid file extension raises ValueError."""
        with patch("data_generation.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = '[{"age": 30}]'
            mock_llm_class.return_value = mock_llm

            with pytest.raises(ValueError, match="Cannot infer format"):
                generate_dataset(
                    columns={"age": "Age"}, num_rows=1, output_path=tmp_path / "data.txt"
                )

    def test_invalid_quality_issues_not_list(self):
        """Test that non-list quality_issues raises ValueError."""
        with pytest.raises(ValueError, match="quality_issues must be a list"):
            generate_dataset(columns={"age": "Age of person"}, num_rows=10, quality_issues="nulls")

    def test_invalid_quality_issues_unknown_value(self):
        """Test that unknown quality_issues value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid quality_issues"):
            generate_dataset(
                columns={"age": "Age of person"}, num_rows=10, quality_issues=["invalid"]
            )


class TestGenerateDatasetWithMock:
    """Tests for generate_dataset() with mocked LLM."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response."""
        return [
            {"age": 32, "salary": 75000},
            {"age": 28, "salary": 62000},
            {"age": 45, "salary": 120000},
        ]

    def test_returns_dataframe(self, mock_llm_response):
        """Test that generate_dataset returns a DataFrame."""
        with patch("data_generation.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(mock_llm_response)
            mock_llm_class.return_value = mock_llm

            df = generate_dataset(columns={"age": "Age", "salary": "Salary"}, num_rows=3)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert "age" in df.columns
            assert "salary" in df.columns

    def test_with_target(self):
        """Test generation with target column."""
        response_with_target = [
            {"age": 32, "salary": 75000, "will_leave": False},
            {"age": 28, "salary": 62000, "will_leave": True},
            {"age": 45, "salary": 120000, "will_leave": False},
        ]

        with patch("data_generation.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(response_with_target)
            mock_llm_class.return_value = mock_llm

            df = generate_dataset(
                columns={"age": "Age", "salary": "Salary"},
                target={"name": "will_leave", "prompt": "Will leave company"},
                num_rows=3,
            )

            assert "will_leave" in df.columns

    def test_saves_to_file(self, mock_llm_response, tmp_path):
        """Test that output_path saves the file."""
        with patch("data_generation.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(mock_llm_response)
            mock_llm_class.return_value = mock_llm

            output_file = tmp_path / "test.csv"
            generate_dataset(
                columns={"age": "Age", "salary": "Salary"}, num_rows=3, output_path=output_file
            )

            assert output_file.exists()
            loaded = pd.read_csv(output_file)
            assert len(loaded) == 3

    def test_with_quality_issues(self):
        """Test generation with quality_issues parameter."""
        response_with_nulls = [
            {"name": "John Smith", "age": 32, "salary": 75000},
            {"name": None, "age": 28, "salary": 62000},
            {"name": "Jane Doe", "age": None, "salary": 120000},
        ]

        with patch("data_generation.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(response_with_nulls)
            mock_llm_class.return_value = mock_llm

            df = generate_dataset(
                columns={"name": "Person name", "age": "Age", "salary": "Salary"},
                num_rows=3,
                quality_issues=["nulls"],
            )

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            # Verify prompt included quality issues instruction
            call_args = mock_llm.invoke.call_args[0][0]
            assert "null" in call_args.lower()


class TestExports:
    """Tests for package exports."""

    def test_generate_dataset_is_exported(self):
        from data_generation import generate_dataset as gen

        assert callable(gen)

    def test_write_dataframe_is_exported(self):
        from data_generation import write_dataframe as wdf

        assert callable(wdf)

    def test_supported_formats_is_exported(self):
        from data_generation import SUPPORTED_FORMATS

        assert isinstance(SUPPORTED_FORMATS, list)
        assert "csv" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS
        assert "parquet" in SUPPORTED_FORMATS
        assert "xlsx" in SUPPORTED_FORMATS


class TestWriteDataframe:
    """Tests for write_dataframe integration."""

    def test_write_csv(self, tmp_path):
        """Test writing DataFrame to CSV."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        output_path = tmp_path / "test.csv"

        result = write_dataframe(df, str(output_path), "csv")

        assert result.exists()
        loaded = pd.read_csv(result)
        pd.testing.assert_frame_equal(df, loaded)

    def test_write_json(self, tmp_path):
        """Test writing DataFrame to JSON."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        output_path = tmp_path / "test.json"

        result = write_dataframe(df, str(output_path), "json")

        assert result.exists()
        loaded = pd.read_json(result)
        pd.testing.assert_frame_equal(df, loaded)


# Integration tests - require OPENAI_API_KEY
@pytest.mark.integration
class TestIntegration:
    """Integration tests that make real LLM calls.

    Run with: pytest tests/test_api.py -v -m integration
    Requires OPENAI_API_KEY environment variable.
    """

    def test_generate_basic(self):
        """Test basic generation with real LLM."""
        df = generate_dataset(
            columns={
                "name": "Person's full name",
                "age": "Age between 20 and 60",
            },
            num_rows=5,
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "name" in df.columns
        assert "age" in df.columns

    def test_generate_with_target(self):
        """Test generation with target column."""
        df = generate_dataset(
            columns={
                "tenure_months": "Months as customer, 1-60",
                "monthly_spend": "Monthly spending in USD, 10-500",
            },
            target={"name": "churned", "prompt": "Boolean indicating if customer churned"},
            num_rows=5,
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "churned" in df.columns

    def test_generate_with_quality_issues(self):
        """Test generation with data quality degradation (nulls, outliers)."""
        df = generate_dataset(
            columns={
                "name": "Person's full name",
                "age": "Age between 20 and 60",
                "salary": "Annual salary in USD, 30000-150000",
            },
            num_rows=20,
            quality_issues=["nulls", "outliers"],
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 15  # Allow some flexibility due to LLM
        assert "name" in df.columns
        assert "age" in df.columns
        assert "salary" in df.columns
        # Note: LLM may or may not introduce nulls, so we just verify it runs
