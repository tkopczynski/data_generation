#!/bin/bash
# Validate code quality and run tests
#
# Usage:
#   ./scripts/validate.sh        # Run without integration tests
#   ./scripts/validate.sh --all  # Run all tests including integration

set -e  # Exit on first error

RUN_ALL=false
if [[ "$1" == "--all" ]]; then
    RUN_ALL=true
fi

echo "=== Running Ruff Check ==="
ruff check src/ tests/

echo ""
echo "=== Running Ruff Format Check ==="
ruff format --check src/ tests/

echo ""
if [[ "$RUN_ALL" == true ]]; then
    echo "=== Running All Tests (including integration) ==="
    python -m pytest tests/ -v --tb=short
else
    echo "=== Running Tests (excluding integration) ==="
    python -m pytest tests/ -v --tb=short -m "not integration"
fi

echo ""
echo "=== All validations passed! ==="
