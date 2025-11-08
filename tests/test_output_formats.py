"""Tests for output format functionality."""

import json
from pathlib import Path

import pandas as pd
import pytest

from data_generation.core.output_formats import (
    SUPPORTED_FORMATS,
    adjust_file_extension,
    detect_format_from_filename,
    write_dataframe,
)


class TestFormatExtensionAdjustment:
    """Test file extension adjustment logic."""

    def test_adjust_extension_csv_to_json(self):
        result = adjust_file_extension("data.csv", "json")
        assert result == "data.json"

    def test_adjust_extension_no_extension_to_parquet(self):
        result = adjust_file_extension("data", "parquet")
        assert result == "data.parquet"

    def test_adjust_extension_correct_already(self):
        result = adjust_file_extension("data.xlsx", "xlsx")
        assert result == "data.xlsx"

    def test_adjust_extension_multiple_dots(self):
        result = adjust_file_extension("my.data.file.csv", "json")
        assert result == "my.data.file.json"

    def test_adjust_extension_path_with_directory(self):
        result = adjust_file_extension("/path/to/data.csv", "parquet")
        assert result == "/path/to/data.parquet"


class TestFormatDetection:
    """Test format detection from filename."""

    def test_detect_csv(self):
        assert detect_format_from_filename("data.csv") == "csv"

    def test_detect_json(self):
        assert detect_format_from_filename("data.json") == "json"

    def test_detect_parquet(self):
        assert detect_format_from_filename("data.parquet") == "parquet"

    def test_detect_xlsx(self):
        assert detect_format_from_filename("data.xlsx") == "xlsx"

    def test_detect_unknown(self):
        assert detect_format_from_filename("data.txt") is None

    def test_detect_no_extension(self):
        assert detect_format_from_filename("data") is None

    def test_detect_case_insensitive(self):
        assert detect_format_from_filename("data.CSV") == "csv"
        assert detect_format_from_filename("data.JSON") == "json"


class TestWriteDataFrame:
    """Test DataFrame writing in different formats."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
                "age": [25, 30, 35, 28, 42],
                "email": [
                    "alice@example.com",
                    "bob@example.com",
                    "charlie@example.com",
                    "diana@example.com",
                    "eve@example.com",
                ],
            }
        )

    def test_write_csv(self, sample_dataframe, tmp_path):
        output_file = tmp_path / "test.csv"
        result_path = write_dataframe(sample_dataframe, str(output_file), "csv")

        assert result_path.exists()
        assert result_path.suffix == ".csv"

        # Verify contents
        df_read = pd.read_csv(result_path)
        pd.testing.assert_frame_equal(df_read, sample_dataframe)

    def test_write_json(self, sample_dataframe, tmp_path):
        output_file = tmp_path / "test.json"
        result_path = write_dataframe(sample_dataframe, str(output_file), "json")

        assert result_path.exists()
        assert result_path.suffix == ".json"

        # Verify contents
        with open(result_path) as f:
            data = json.load(f)

        assert len(data) == 5
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == 25

    def test_write_parquet(self, sample_dataframe, tmp_path):
        output_file = tmp_path / "test.parquet"
        result_path = write_dataframe(sample_dataframe, str(output_file), "parquet")

        assert result_path.exists()
        assert result_path.suffix == ".parquet"

        # Verify contents
        df_read = pd.read_parquet(result_path)
        pd.testing.assert_frame_equal(df_read, sample_dataframe)

    def test_write_excel(self, sample_dataframe, tmp_path):
        output_file = tmp_path / "test.xlsx"
        result_path = write_dataframe(sample_dataframe, str(output_file), "xlsx")

        assert result_path.exists()
        assert result_path.suffix == ".xlsx"

        # Verify contents
        df_read = pd.read_excel(result_path)
        pd.testing.assert_frame_equal(df_read, sample_dataframe)

    def test_auto_extension_adjustment(self, sample_dataframe, tmp_path):
        # Request JSON but provide CSV filename
        output_file = tmp_path / "test.csv"
        result_path = write_dataframe(sample_dataframe, str(output_file), "json")

        # Should have .json extension, not .csv
        assert result_path.suffix == ".json"
        assert result_path.name == "test.json"

    def test_unsupported_format(self, sample_dataframe, tmp_path):
        output_file = tmp_path / "test.txt"
        with pytest.raises(ValueError, match="Unsupported format"):
            write_dataframe(sample_dataframe, str(output_file), "txt")

    def test_all_supported_formats(self, sample_dataframe, tmp_path):
        """Verify all formats in SUPPORTED_FORMATS work."""
        for fmt in SUPPORTED_FORMATS:
            output_file = tmp_path / f"test_{fmt}.{fmt}"
            result_path = write_dataframe(sample_dataframe, str(output_file), fmt)
            assert result_path.exists()


class TestIntegrationWithDataGeneration:
    """Integration tests with the data generation tool."""

    def test_generate_with_json_format(self, tmp_path):
        """Test end-to-end generation with JSON format."""
        from data_generation.core.generator import generate_data_with_seed
        from data_generation.core.output_formats import write_dataframe

        schema = [
            {"name": "id", "type": "int", "config": {"min": 1, "max": 100}},
            {"name": "name", "type": "name"},
            {"name": "email", "type": "email"},
        ]

        data, seed = generate_data_with_seed(schema, 50)
        df = pd.DataFrame(data)

        output_file = tmp_path / "users.json"
        result_path = write_dataframe(df, str(output_file), "json")

        assert result_path.exists()

        # Verify JSON structure
        with open(result_path) as f:
            json_data = json.load(f)

        assert len(json_data) == 50
        assert "id" in json_data[0]
        assert "name" in json_data[0]
        assert "email" in json_data[0]

    def test_generate_with_parquet_format(self, tmp_path):
        """Test end-to-end generation with Parquet format."""
        from data_generation.core.generator import generate_data_with_seed
        from data_generation.core.output_formats import write_dataframe

        schema = [
            {"name": "transaction_id", "type": "uuid"},
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 1000.0}},
            {"name": "date", "type": "date"},
        ]

        data, seed = generate_data_with_seed(schema, 100)
        df = pd.DataFrame(data)

        output_file = tmp_path / "transactions.parquet"
        result_path = write_dataframe(df, str(output_file), "parquet")

        assert result_path.exists()

        # Verify Parquet can be read
        df_read = pd.read_parquet(result_path)
        assert len(df_read) == 100
        assert list(df_read.columns) == ["transaction_id", "amount", "date"]

    def test_quality_degradation_with_excel(self, tmp_path):
        """Test that quality degradation works with Excel format."""
        from data_generation.core.generator import generate_data_with_seed
        from data_generation.core.output_formats import write_dataframe

        schema = [
            {"name": "id", "type": "int", "config": {"min": 1, "max": 1000}},
            {
                "name": "email",
                "type": "email",
                "config": {
                    "quality_config": {
                        "null_rate": 0.1,
                        "invalid_format_rate": 0.05,
                    }
                },
            },
        ]

        data, seed = generate_data_with_seed(schema, 200, seed=123456)
        df = pd.DataFrame(data)

        output_file = tmp_path / "users.xlsx"
        result_path = write_dataframe(df, str(output_file), "xlsx")

        assert result_path.exists()

        # Verify Excel can be read and has quality issues
        df_read = pd.read_excel(result_path)
        assert len(df_read) == 200

        # Check for null values (should be around 10%)
        null_count = df_read["email"].isna().sum()
        assert 10 <= null_count <= 30  # ±10% tolerance


class TestFormatConstants:
    """Test format-related constants."""

    def test_supported_formats(self):
        assert "csv" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS
        assert "parquet" in SUPPORTED_FORMATS
        assert "xlsx" in SUPPORTED_FORMATS

    def test_format_count(self):
        """Ensure we have exactly 4 supported formats."""
        assert len(SUPPORTED_FORMATS) == 4
