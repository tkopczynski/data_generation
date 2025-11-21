"""Tests for output format functionality."""

import json

import pandas as pd
import pytest

from makeitup.core.output_formats import (
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

    def test_adjust_extension_excel_alias(self):
        result = adjust_file_extension("data.csv", "excel")
        assert result == "data.xlsx"

    def test_adjust_extension_excel_no_extension(self):
        result = adjust_file_extension("data", "excel")
        assert result == "data.xlsx"


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

    def test_write_excel_alias(self, sample_dataframe, tmp_path):
        """Test that 'excel' format works as an alias for 'xlsx'."""
        output_file = tmp_path / "test.xlsx"
        result_path = write_dataframe(sample_dataframe, str(output_file), "excel")

        assert result_path.exists()
        assert result_path.suffix == ".xlsx"

        # Verify contents
        df_read = pd.read_excel(result_path)
        pd.testing.assert_frame_equal(df_read, sample_dataframe)

    def test_write_excel_alias_auto_extension(self, sample_dataframe, tmp_path):
        """Test that 'excel' format adjusts extension to .xlsx."""
        output_file = tmp_path / "test.csv"
        result_path = write_dataframe(sample_dataframe, str(output_file), "excel")

        # Should have .xlsx extension, not .csv
        assert result_path.suffix == ".xlsx"
        assert result_path.name == "test.xlsx"

        # Verify it's a valid Excel file
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


class TestFormatConstants:
    """Test format-related constants."""

    def test_supported_formats(self):
        assert "csv" in SUPPORTED_FORMATS
        assert "json" in SUPPORTED_FORMATS
        assert "parquet" in SUPPORTED_FORMATS
        assert "xlsx" in SUPPORTED_FORMATS
        assert "excel" in SUPPORTED_FORMATS

    def test_format_count(self):
        """Ensure we have exactly 5 supported formats (including 'excel' alias)."""
        assert len(SUPPORTED_FORMATS) == 5
