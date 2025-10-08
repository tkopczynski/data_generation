"""Tests for schema validation."""

import pytest

from tools.schema_validation import SchemaValidationError, validate_schema


class TestValidateSchema:
    """Test schema validation."""

    def test_valid_schema(self):
        """Test that a valid schema passes validation."""
        schema = [
            {"name": "id", "type": "int", "config": {"min": 1, "max": 100}},
            {"name": "email", "type": "email"},
        ]
        validate_schema(schema)  # Should not raise

    def test_empty_schema(self):
        """Test that empty schema raises error."""
        with pytest.raises(SchemaValidationError, match="Schema cannot be empty"):
            validate_schema([])

    def test_non_list_schema(self):
        """Test that non-list schema raises error."""
        with pytest.raises(SchemaValidationError, match="Schema must be a list"):
            validate_schema({"name": "id", "type": "int"})

    def test_missing_name_field(self):
        """Test that missing name field raises error."""
        schema = [{"type": "int"}]
        with pytest.raises(SchemaValidationError, match="missing 'name' field"):
            validate_schema(schema)

    def test_missing_type_field(self):
        """Test that missing type field raises error."""
        schema = [{"name": "id"}]
        with pytest.raises(SchemaValidationError, match="missing 'type' field"):
            validate_schema(schema)

    def test_invalid_type(self):
        """Test that invalid type raises error."""
        schema = [{"name": "id", "type": "invalid_type"}]
        with pytest.raises(SchemaValidationError, match="invalid type"):
            validate_schema(schema)

    def test_duplicate_column_names(self):
        """Test that duplicate column names raise error."""
        schema = [
            {"name": "id", "type": "int"},
            {"name": "id", "type": "text"},
        ]
        with pytest.raises(SchemaValidationError, match="Duplicate column name"):
            validate_schema(schema)

    def test_min_greater_than_max(self):
        """Test that min > max raises error."""
        schema = [{"name": "id", "type": "int", "config": {"min": 100, "max": 10}}]
        with pytest.raises(SchemaValidationError, match="min value cannot be greater than max"):
            validate_schema(schema)

    def test_category_without_categories(self):
        """Test that category type without categories raises error."""
        schema = [{"name": "status", "type": "category"}]
        with pytest.raises(SchemaValidationError, match="must have 'categories' in config"):
            validate_schema(schema)

    def test_category_with_empty_categories(self):
        """Test that category type with empty categories raises error."""
        schema = [{"name": "status", "type": "category", "config": {"categories": []}}]
        with pytest.raises(SchemaValidationError, match="must be a non-empty list"):
            validate_schema(schema)

    def test_invalid_text_type(self):
        """Test that invalid text_type raises error."""
        schema = [{"name": "user", "type": "name", "config": {"text_type": "invalid"}}]
        with pytest.raises(SchemaValidationError, match="invalid text_type"):
            validate_schema(schema)
