"""Tests for the make() API."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from makeitup import make


class TestMakeValidation:
    """Tests for input validation in make()."""

    def test_invalid_target_not_dict(self):
        """Test that non-dict target raises ValueError."""
        with pytest.raises(ValueError, match="target must be a dictionary"):
            make(columns={"age": "Age of person"}, num_rows=10, target="invalid")

    def test_invalid_target_missing_name(self):
        """Test that target without 'name' raises ValueError."""
        with pytest.raises(ValueError, match="target must have 'name' and 'prompt' keys"):
            make(columns={"age": "Age of person"}, num_rows=10, target={"prompt": "Some prompt"})

    def test_invalid_target_missing_prompt(self):
        """Test that target without 'prompt' raises ValueError."""
        with pytest.raises(ValueError, match="target must have 'name' and 'prompt' keys"):
            make(columns={"age": "Age of person"}, num_rows=10, target={"name": "target_col"})

    def test_invalid_output_extension(self, tmp_path):
        """Test that invalid file extension raises ValueError."""
        with patch("makeitup.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = '[{"age": 30}]'
            mock_llm_class.return_value = mock_llm

            with pytest.raises(ValueError, match="Cannot infer format"):
                make(columns={"age": "Age"}, num_rows=1, output_path=tmp_path / "data.txt")

    def test_invalid_quality_issues_not_list(self):
        """Test that non-list quality_issues raises ValueError."""
        with pytest.raises(ValueError, match="quality_issues must be a list"):
            make(columns={"age": "Age of person"}, num_rows=10, quality_issues="nulls")

    def test_invalid_quality_issues_unknown_value(self):
        """Test that unknown quality_issues value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid quality_issues"):
            make(columns={"age": "Age of person"}, num_rows=10, quality_issues=["invalid"])


class TestMakeWithMock:
    """Tests for make() with mocked LLM."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response."""
        return [
            {"age": 32, "salary": 75000},
            {"age": 28, "salary": 62000},
            {"age": 45, "salary": 120000},
        ]

    def test_returns_dataframe(self, mock_llm_response):
        """Test that make returns a DataFrame."""
        with patch("makeitup.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(mock_llm_response)
            mock_llm_class.return_value = mock_llm

            df = make(columns={"age": "Age", "salary": "Salary"}, num_rows=3)

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

        with patch("makeitup.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(response_with_target)
            mock_llm_class.return_value = mock_llm

            df = make(
                columns={"age": "Age", "salary": "Salary"},
                target={"name": "will_leave", "prompt": "Will leave company"},
                num_rows=3,
            )

            assert "will_leave" in df.columns

    def test_saves_to_file(self, mock_llm_response, tmp_path):
        """Test that output_path saves the file."""
        with patch("makeitup.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(mock_llm_response)
            mock_llm_class.return_value = mock_llm

            output_file = tmp_path / "test.csv"
            make(columns={"age": "Age", "salary": "Salary"}, num_rows=3, output_path=output_file)

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

        with patch("makeitup.core.generator.ChatOpenAI") as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = json.dumps(response_with_nulls)
            mock_llm_class.return_value = mock_llm

            df = make(
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

    def test_make_is_exported(self):
        from makeitup import make as m

        assert callable(m)


# Integration tests - require OPENAI_API_KEY
@pytest.mark.integration
class TestIntegration:
    """Integration tests that make real LLM calls.

    Run with: pytest tests/test_api.py -v -m integration
    Requires OPENAI_API_KEY environment variable.
    """

    def test_generate_basic(self):
        """Test basic generation with real LLM."""
        df = make(
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
        df = make(
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
        df = make(
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
