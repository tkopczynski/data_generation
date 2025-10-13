"""Tests for the generate_data function."""

from datetime import datetime

import pytest

from tools.generator import generate_data
from tools.schema_validation import SchemaValidationError


class TestGenerateData:
    """Test data generation."""

    def test_generate_basic_data(self):
        """Test basic data generation."""
        schema = [
            {"name": "id", "type": "int"},
            {"name": "email", "type": "email"},
        ]
        data = generate_data(schema, 10)

        assert len(data) == 10
        assert all(isinstance(row["id"], int) for row in data)
        assert all("@" in row["email"] for row in data)

    def test_generate_zero_rows(self):
        """Test generating zero rows."""
        schema = [{"name": "id", "type": "int"}]
        data = generate_data(schema, 0)
        assert len(data) == 0

    def test_int_type_with_range(self):
        """Test int type respects min/max config."""
        schema = [{"name": "age", "type": "int", "config": {"min": 18, "max": 65}}]
        data = generate_data(schema, 100)

        assert all(18 <= row["age"] <= 65 for row in data)

    def test_float_type_with_precision(self):
        """Test float type respects precision config."""
        schema = [
            {"name": "price", "type": "float", "config": {"min": 0.0, "max": 100.0, "precision": 3}}
        ]
        data = generate_data(schema, 50)

        for row in data:
            assert 0.0 <= row["price"] <= 100.0
            # Check precision by converting to string and counting decimals
            decimal_places = (
                len(str(row["price"]).split(".")[-1]) if "." in str(row["price"]) else 0
            )
            assert decimal_places <= 3

    def test_currency_type(self):
        """Test currency type generation."""
        schema = [{"name": "amount", "type": "currency", "config": {"min": 100.0, "max": 1000.0}}]
        data = generate_data(schema, 50)

        for row in data:
            assert 100.0 <= row["amount"] <= 1000.0
            # Currency should have 2 decimal places
            assert round(row["amount"], 2) == row["amount"]

    def test_percentage_type(self):
        """Test percentage type generation."""
        schema = [{"name": "discount", "type": "percentage"}]
        data = generate_data(schema, 50)

        assert all(0.0 <= row["discount"] <= 100.0 for row in data)

    def test_category_type(self):
        """Test category type generation."""
        categories = ["A", "B", "C"]
        schema = [{"name": "status", "type": "category", "config": {"categories": categories}}]
        data = generate_data(schema, 100)

        assert all(row["status"] in categories for row in data)

    def test_bool_type(self):
        """Test bool type generation."""
        schema = [{"name": "active", "type": "bool"}]
        data = generate_data(schema, 50)

        assert all(isinstance(row["active"], bool) for row in data)

    def test_date_type(self):
        """Test date type generation."""
        schema = [{"name": "created", "type": "date"}]
        data = generate_data(schema, 10)

        for row in data:
            assert hasattr(row["created"], "year")  # Check it's a date object

    def test_date_type_with_range(self):
        """Test date type with date range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        schema = [
            {"name": "created", "type": "date", "config": {"start_date": start, "end_date": end}}
        ]
        data = generate_data(schema, 50)

        for row in data:
            assert start.date() <= row["created"] <= end.date()

    def test_datetime_type(self):
        """Test datetime type generation."""
        schema = [{"name": "timestamp", "type": "datetime"}]
        data = generate_data(schema, 10)

        for row in data:
            assert hasattr(row["timestamp"], "hour")  # Check it's a datetime object

    def test_email_type(self):
        """Test email type generation."""
        schema = [{"name": "email", "type": "email"}]
        data = generate_data(schema, 10)

        assert all("@" in row["email"] for row in data)

    def test_phone_type(self):
        """Test phone type generation."""
        schema = [{"name": "phone", "type": "phone"}]
        data = generate_data(schema, 10)

        assert all(isinstance(row["phone"], str) for row in data)

    def test_name_type_variations(self):
        """Test name type with different text_type configs."""
        schema = [
            {"name": "first", "type": "name", "config": {"text_type": "first_name"}},
            {"name": "last", "type": "name", "config": {"text_type": "last_name"}},
            {"name": "full", "type": "name", "config": {"text_type": "full_name"}},
        ]
        data = generate_data(schema, 10)

        assert all(isinstance(row["first"], str) for row in data)
        assert all(isinstance(row["last"], str) for row in data)
        assert all(isinstance(row["full"], str) for row in data)

    def test_address_type_variations(self):
        """Test address type with different text_type configs."""
        schema = [
            {"name": "street", "type": "address", "config": {"text_type": "street"}},
            {"name": "city", "type": "address", "config": {"text_type": "city"}},
            {"name": "state", "type": "address", "config": {"text_type": "state"}},
            {"name": "zip", "type": "address", "config": {"text_type": "zip"}},
            {"name": "country", "type": "address", "config": {"text_type": "country"}},
        ]
        data = generate_data(schema, 10)

        for key in ["street", "city", "state", "zip", "country"]:
            assert all(isinstance(row[key], str) for row in data)

    def test_company_type(self):
        """Test company type generation."""
        schema = [{"name": "company", "type": "company"}]
        data = generate_data(schema, 10)

        assert all(isinstance(row["company"], str) for row in data)

    def test_product_type(self):
        """Test product type generation."""
        schema = [{"name": "product", "type": "product"}]
        data = generate_data(schema, 10)

        assert all(isinstance(row["product"], str) for row in data)

    def test_uuid_type(self):
        """Test UUID type generation."""
        schema = [{"name": "id", "type": "uuid"}]
        data = generate_data(schema, 10)

        # Check format: 8-4-4-4-12 hex characters
        for row in data:
            parts = row["id"].split("-")
            assert len(parts) == 5
            assert len(parts[0]) == 8
            assert len(parts[1]) == 4
            assert len(parts[4]) == 12

    def test_text_type(self):
        """Test text type generation."""
        schema = [{"name": "description", "type": "text"}]
        data = generate_data(schema, 10)

        assert all(isinstance(row["description"], str) for row in data)
        assert all(len(row["description"]) <= 200 for row in data)

    def test_complex_schema(self):
        """Test generating data with a complex schema."""
        schema = [
            {"name": "id", "type": "uuid"},
            {"name": "customer_name", "type": "name"},
            {"name": "email", "type": "email"},
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 1000.0}},
            {
                "name": "status",
                "type": "category",
                "config": {"categories": ["pending", "completed", "cancelled"]},
            },
            {"name": "created_at", "type": "datetime"},
        ]
        data = generate_data(schema, 20)

        assert len(data) == 20
        for row in data:
            assert len(row) == 6
            assert all(
                key in row
                for key in ["id", "customer_name", "email", "amount", "status", "created_at"]
            )

    def test_invalid_schema_raises_error(self):
        """Test that invalid schema raises error during generation."""
        schema = [{"name": "id"}]  # Missing type
        with pytest.raises(SchemaValidationError):
            generate_data(schema, 10)

    def test_reference_type_basic(self, tmp_path):
        """Test reference type with a simple parent table."""
        # Create a parent CSV file
        parent_file = tmp_path / "users.csv"
        parent_file.write_text("user_id,name\n1,Alice\n2,Bob\n3,Charlie\n")

        # Create schema that references the parent file
        schema = [
            {"name": "transaction_id", "type": "uuid"},
            {
                "name": "user_id",
                "type": "reference",
                "config": {"reference_file": str(parent_file), "reference_column": "user_id"},
            },
            {"name": "amount", "type": "currency"},
        ]

        data = generate_data(schema, 20)

        assert len(data) == 20
        # All user_ids should be from the parent table
        valid_user_ids = ["1", "2", "3"]  # CSV reads as strings
        assert all(str(row["user_id"]) in valid_user_ids for row in data)

    def test_reference_type_missing_file(self):
        """Test reference type with missing file raises error."""
        schema = [
            {
                "name": "user_id",
                "type": "reference",
                "config": {
                    "reference_file": "nonexistent.csv",
                    "reference_column": "user_id",
                },
            }
        ]

        with pytest.raises(FileNotFoundError):
            generate_data(schema, 10)

    def test_reference_type_missing_column(self, tmp_path):
        """Test reference type with missing column raises error."""
        parent_file = tmp_path / "users.csv"
        parent_file.write_text("user_id,name\n1,Alice\n")

        schema = [
            {
                "name": "user_id",
                "type": "reference",
                "config": {
                    "reference_file": str(parent_file),
                    "reference_column": "nonexistent_column",
                },
            }
        ]

        with pytest.raises(ValueError, match="Column 'nonexistent_column' not found"):
            generate_data(schema, 10)

    def test_reference_type_missing_config(self):
        """Test reference type without required config raises validation error."""
        schema = [{"name": "user_id", "type": "reference", "config": {}}]

        with pytest.raises(SchemaValidationError, match="reference_file"):
            generate_data(schema, 10)

    def test_reference_type_caching(self, tmp_path):
        """Test that reference data is cached and not reloaded."""
        parent_file = tmp_path / "categories.csv"
        parent_file.write_text("category_id,name\nA,Alpha\nB,Beta\nC,Gamma\n")

        # Create schema with multiple reference columns using the same file
        schema = [
            {"name": "id", "type": "uuid"},
            {
                "name": "primary_category",
                "type": "reference",
                "config": {"reference_file": str(parent_file), "reference_column": "category_id"},
            },
            {
                "name": "secondary_category",
                "type": "reference",
                "config": {"reference_file": str(parent_file), "reference_column": "category_id"},
            },
        ]

        data = generate_data(schema, 30)

        assert len(data) == 30
        valid_categories = ["A", "B", "C"]
        assert all(str(row["primary_category"]) in valid_categories for row in data)
        assert all(str(row["secondary_category"]) in valid_categories for row in data)
