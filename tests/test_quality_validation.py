"""Quality validation tests for messy data generation.

These tests verify that quality degradation (nulls, duplicates, typos, etc.)
works correctly and matches configured rates.
"""

import pytest

from data_generation.core.generator import generate_data
from data_generation.tools.schema_validation import SchemaValidationError


class TestQualityConfigValidation:
    """Test quality_config schema validation."""

    def test_valid_quality_config(self):
        """Test schema with valid quality_config."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {
                    "quality_config": {
                        "null_rate": 0.1,
                        "duplicate_rate": 0.05,
                        "similar_rate": 0.03,
                    }
                },
            }
        ]
        # Should not raise
        data = generate_data(schema, 10)
        assert len(data) == 10

    def test_quality_config_rate_out_of_range(self):
        """Test quality_config with rate > 1."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"null_rate": 1.5}}}
        ]
        with pytest.raises(SchemaValidationError, match="must be between 0 and 1"):
            generate_data(schema, 10)

    def test_quality_config_negative_rate(self):
        """Test quality_config with negative rate."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {"quality_config": {"null_rate": -0.1}},
            }
        ]
        with pytest.raises(SchemaValidationError, match="must be between 0 and 1"):
            generate_data(schema, 10)

    def test_quality_config_invalid_key(self):
        """Test quality_config with invalid key."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {"quality_config": {"invalid_key": 0.1}},
            }
        ]
        with pytest.raises(SchemaValidationError, match="invalid quality_config key"):
            generate_data(schema, 10)

    def test_quality_config_non_numeric(self):
        """Test quality_config with non-numeric value."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"null_rate": "0.1"}}}
        ]
        with pytest.raises(SchemaValidationError, match="must be a number"):
            generate_data(schema, 10)


class TestNullRateValidation:
    """Test null rate quality degradation."""

    def test_null_rate_10_percent(self):
        """Test 10% null rate is achieved within tolerance."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"null_rate": 0.1}}}
        ]
        data = generate_data(schema, 1000)

        null_count = sum(1 for row in data if row["email"] is None)
        null_rate = null_count / len(data)

        # Allow ±3% tolerance
        assert 0.07 <= null_rate <= 0.13, f"Null rate {null_rate} outside expected range 0.1 ± 0.03"

    def test_null_rate_25_percent(self):
        """Test 25% null rate is achieved within tolerance."""
        schema = [
            {"name": "value", "type": "int", "config": {"quality_config": {"null_rate": 0.25}}}
        ]
        # Use larger sample size (5000) to reduce statistical variance
        data = generate_data(schema, 5000)

        null_count = sum(1 for row in data if row["value"] is None)
        null_rate = null_count / len(data)

        # Allow ±3% tolerance
        assert 0.22 <= null_rate <= 0.28, f"Null rate {null_rate} outside expected range 0.25 ± 0.03"

    def test_null_rate_zero(self):
        """Test zero null rate produces no nulls."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"null_rate": 0.0}}}
        ]
        data = generate_data(schema, 500)

        null_count = sum(1 for row in data if row["email"] is None)
        assert null_count == 0, f"Expected no nulls, got {null_count}"

    def test_null_rate_one(self):
        """Test null rate of 1.0 produces all nulls."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"null_rate": 1.0}}}
        ]
        data = generate_data(schema, 100)

        null_count = sum(1 for row in data if row["email"] is None)
        assert null_count == 100, f"Expected all nulls, got {null_count}/100"

    def test_null_rate_multiple_fields(self):
        """Test different null rates on different fields."""
        schema = [
            {"name": "field1", "type": "text", "config": {"quality_config": {"null_rate": 0.1}}},
            {"name": "field2", "type": "text", "config": {"quality_config": {"null_rate": 0.2}}},
            {"name": "field3", "type": "text"},  # No quality config
        ]
        data = generate_data(schema, 1000)

        null_count_1 = sum(1 for row in data if row["field1"] is None)
        null_count_2 = sum(1 for row in data if row["field2"] is None)
        null_count_3 = sum(1 for row in data if row["field3"] is None)

        null_rate_1 = null_count_1 / len(data)
        null_rate_2 = null_count_2 / len(data)

        assert 0.07 <= null_rate_1 <= 0.13, f"Field1 null rate {null_rate_1} outside range"
        assert 0.16 <= null_rate_2 <= 0.24, f"Field2 null rate {null_rate_2} outside range"
        assert null_count_3 == 0, f"Field3 should have no nulls, got {null_count_3}"


class TestDuplicateRateValidation:
    """Test duplicate rate quality degradation."""

    def test_duplicate_rate_10_percent(self):
        """Test 10% duplicate rate is achieved within tolerance."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {"quality_config": {"duplicate_rate": 0.1}},
            }
        ]
        data = generate_data(schema, 1000)

        emails = [row["email"] for row in data if row["email"] is not None]
        unique_emails = len(set(emails))
        duplicate_count = len(emails) - unique_emails
        duplicate_rate = duplicate_count / len(data)

        # Allow ±5% tolerance (duplicates are probabilistic)
        assert (
            0.05 <= duplicate_rate <= 0.15
        ), f"Duplicate rate {duplicate_rate} outside expected range 0.1 ± 0.05"

    def test_duplicate_rate_with_nulls(self):
        """Test duplicates work correctly with nulls present."""
        schema = [
            {
                "name": "value",
                "type": "int",
                "config": {
                    "quality_config": {
                        "null_rate": 0.2,
                        "duplicate_rate": 0.1,
                    }
                },
            }
        ]
        data = generate_data(schema, 1000)

        # Nulls should not be counted as duplicates
        values = [row["value"] for row in data if row["value"] is not None]
        null_count = sum(1 for row in data if row["value"] is None)

        # Check null rate
        null_rate = null_count / len(data)
        assert 0.17 <= null_rate <= 0.23, f"Null rate {null_rate} outside range"

        # Check duplicates among non-null values
        unique_values = len(set(values))
        assert unique_values < len(values), "Expected some duplicates among non-null values"

    def test_duplicate_rate_zero(self):
        """Test zero duplicate rate with small value space."""
        schema = [
            {
                "name": "value",
                "type": "int",
                "config": {"min": 1, "max": 1000, "quality_config": {"duplicate_rate": 0.0}},
            }
        ]
        data = generate_data(schema, 100)

        values = [row["value"] for row in data]
        # With duplicate_rate=0, we should see natural randomness
        # Not all unique (small chance of random duplicates), but many unique
        unique_count = len(set(values))
        assert unique_count >= 90, f"Expected mostly unique values, got {unique_count}/100"


class TestSimilarRateValidation:
    """Test similar rate (typos/whitespace) quality degradation."""

    def test_similar_rate_introduces_typos(self):
        """Test similar_rate introduces variations in string fields."""
        schema = [
            {"name": "name", "type": "name", "config": {"quality_config": {"similar_rate": 0.2}}}
        ]
        data = generate_data(schema, 1000)

        # Count how many names might have whitespace or character variations
        # This is hard to test precisely, but we can check that not all values are identical
        names = [row["name"] for row in data if row["name"] is not None]

        # Should have good variety (names are already varied, but similar_rate adds more)
        unique_names = len(set(names))
        assert unique_names >= 900, f"Expected high variety in names, got {unique_names}/1000"

    def test_similar_rate_with_email(self):
        """Test similar_rate affects email strings."""
        schema = [
            {"name": "email", "type": "email", "config": {"quality_config": {"similar_rate": 0.3}}}
        ]
        data = generate_data(schema, 500)

        emails = [row["email"] for row in data if row["email"] is not None]

        # With 30% similar rate, some emails should have variations
        # Check that we have variety (emails are already varied)
        unique_emails = len(set(emails))
        assert unique_emails >= 450, f"Expected variety in emails, got {unique_emails}/500"


class TestOutlierRateValidation:
    """Test outlier rate quality degradation."""

    def test_outlier_rate_numeric(self):
        """Test outlier_rate creates extreme values in numeric fields."""
        schema = [
            {
                "name": "value",
                "type": "int",
                "config": {"min": 1, "max": 100, "quality_config": {"outlier_rate": 0.1}},
            }
        ]
        data = generate_data(schema, 1000)

        values = [row["value"] for row in data if row["value"] is not None]

        # Some values should be outliers (outside 1-100 range due to multiplication)
        outliers = [v for v in values if v < 1 or v > 100]
        outlier_rate = len(outliers) / len(values)

        # Allow ±5% tolerance
        assert (
            0.05 <= outlier_rate <= 0.15
        ), f"Outlier rate {outlier_rate} outside expected range 0.1 ± 0.05"

    def test_outlier_rate_currency(self):
        """Test outlier_rate affects currency fields."""
        schema = [
            {
                "name": "price",
                "type": "currency",
                "config": {"min": 10.0, "max": 100.0, "quality_config": {"outlier_rate": 0.15}},
            }
        ]
        data = generate_data(schema, 1000)

        prices = [row["price"] for row in data if row["price"] is not None]

        # Some prices should be outliers
        outliers = [p for p in prices if p < 10.0 or p > 100.0]
        assert len(outliers) > 100, f"Expected ~150 outliers, got {len(outliers)}"


class TestFormatIssueValidation:
    """Test invalid_format_rate quality degradation."""

    def test_format_issue_email(self):
        """Test invalid_format_rate creates malformed emails."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {"quality_config": {"invalid_format_rate": 0.2}},
            }
        ]
        data = generate_data(schema, 1000)

        emails = [row["email"] for row in data if row["email"] is not None]

        # Some emails should be malformed (missing @, etc.)
        malformed = [e for e in emails if "@" not in e or ".." in e or e.count("@") > 1]
        malformed_rate = len(malformed) / len(emails)

        # Allow ±10% tolerance (format issues are specific transformations)
        assert (
            0.10 <= malformed_rate <= 0.30
        ), f"Malformed rate {malformed_rate} outside expected range 0.2 ± 0.1"


class TestCombinedQualityIssues:
    """Test multiple quality issues combined."""

    def test_multiple_quality_issues(self):
        """Test combining null, duplicate, and similar rates."""
        schema = [
            {
                "name": "email",
                "type": "email",
                "config": {
                    "quality_config": {
                        "null_rate": 0.1,
                        "duplicate_rate": 0.05,
                        "similar_rate": 0.03,
                    }
                },
            }
        ]
        data = generate_data(schema, 1000)

        # Check nulls
        null_count = sum(1 for row in data if row["email"] is None)
        null_rate = null_count / len(data)
        assert 0.07 <= null_rate <= 0.13, f"Null rate {null_rate} outside range"

        # Check duplicates among non-null
        emails = [row["email"] for row in data if row["email"] is not None]
        unique_emails = len(set(emails))
        duplicate_count = len(emails) - unique_emails
        # Some duplicates should exist
        assert duplicate_count > 20, f"Expected some duplicates, got {duplicate_count}"

    def test_complex_schema_with_quality(self):
        """Test complex schema with mixed quality settings."""
        schema = [
            {"name": "id", "type": "uuid"},  # No quality issues
            {
                "name": "name",
                "type": "name",
                "config": {"quality_config": {"null_rate": 0.05, "duplicate_rate": 0.1}},
            },
            {
                "name": "email",
                "type": "email",
                "config": {
                    "quality_config": {
                        "null_rate": 0.15,
                        "similar_rate": 0.05,
                        "invalid_format_rate": 0.05,
                    }
                },
            },
            {
                "name": "age",
                "type": "int",
                "config": {"min": 18, "max": 80, "quality_config": {"outlier_rate": 0.05}},
            },
        ]
        data = generate_data(schema, 1000)

        assert len(data) == 1000

        # All rows should have id (no quality issues)
        ids = [row["id"] for row in data]
        assert all(id is not None for id in ids), "IDs should never be null"

        # Names should have some nulls
        null_names = sum(1 for row in data if row["name"] is None)
        assert null_names > 30, f"Expected ~50 null names, got {null_names}"

        # Emails should have more nulls
        null_emails = sum(1 for row in data if row["email"] is None)
        assert null_emails > 120, f"Expected ~150 null emails, got {null_emails}"

        # Ages should have some outliers
        ages = [row["age"] for row in data if row["age"] is not None]
        outlier_ages = [a for a in ages if a < 18 or a > 80]
        assert len(outlier_ages) > 30, f"Expected ~50 outlier ages, got {len(outlier_ages)}"
