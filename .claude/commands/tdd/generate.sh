#!/bin/bash
# /tdd generate <spec-file>
# Generates pytest test files from a test specification

SPEC_FILE="$1"

if [ -z "$SPEC_FILE" ]; then
    echo "❌ Usage: /tdd generate <spec-file>"
    echo "Example: /tdd generate tests/specs/contractor-approval.spec.md"
    exit 1
fi

if [ ! -f "$SPEC_FILE" ]; then
    echo "❌ Spec file not found: $SPEC_FILE"
    exit 1
fi

# Extract feature name from spec file
FEATURE_NAME=$(basename "$SPEC_FILE" .spec.md)

echo "🤖 Generating tests from spec: $SPEC_FILE"
echo "Feature: $FEATURE_NAME"
echo ""

# Create test directories
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e

# Generate unit tests
UNIT_TEST="tests/unit/test_${FEATURE_NAME}.py"

# Convert feature name to valid Python class name (handle hyphens, underscores)
# Example: "test-feature" -> "TestFeature", "contractor_approval" -> "ContractorApproval"
FEATURE_CLASS=$(echo "$FEATURE_NAME" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1' OFS="")

if [ ! -f "$UNIT_TEST" ]; then
    cat > "$UNIT_TEST" << EOF
"""Unit tests for ${FEATURE_NAME}

Generated from: $SPEC_FILE
Author: Auto-generated
Date: $(date +%Y-%m-%d)
"""

import pytest
from unittest.mock import Mock, patch


class Test${FEATURE_CLASS}:
    """Unit tests for ${FEATURE_NAME} feature."""

    def test_example_unit_test(self):
        """Example unit test - replace with actual tests from spec."""
        # Arrange
        # TODO: Set up test data from spec

        # Act
        # TODO: Call the function/method being tested

        # Assert
        # TODO: Verify expected output from spec
        assert True, "Replace with actual test"

    def test_edge_case_example(self):
        """Test edge case - replace with actual edge cases from spec."""
        # TODO: Implement edge case tests from spec
        pass


# TODO: Review spec file and implement all test cases marked as "Unit Tests"
# Spec file: $SPEC_FILE
EOF
    echo "✅ Created: $UNIT_TEST"
else
    echo "⚠️  Already exists: $UNIT_TEST"
fi

# Generate integration tests
INTEGRATION_TEST="tests/integration/test_${FEATURE_NAME}_integration.py"
if [ ! -f "$INTEGRATION_TEST" ]; then
    cat > "$INTEGRATION_TEST" << EOF
"""Integration tests for ${FEATURE_NAME}

Generated from: $SPEC_FILE
Author: Auto-generated
Date: $(date +%Y-%m-%d)
"""

import pytest
import os
from dotenv import load_dotenv

load_dotenv()


class Test${FEATURE_CLASS}Integration:
    """Integration tests for ${FEATURE_NAME} feature."""

    @pytest.fixture
    def setup_test_db(self):
        """Set up test database for integration tests."""
        # TODO: Set up test database
        # Use test Neon database or local PostgreSQL
        yield
        # TODO: Tear down test database

    def test_example_integration_test(self, setup_test_db):
        """Example integration test - replace with actual tests from spec."""
        # Arrange
        # TODO: Set up test data in database

        # Act
        # TODO: Call API endpoint or service method

        # Assert
        # TODO: Verify database state or API response
        assert True, "Replace with actual test"


# TODO: Review spec file and implement all test cases marked as "Integration Tests"
# Spec file: $SPEC_FILE
EOF
    echo "✅ Created: $INTEGRATION_TEST"
else
    echo "⚠️  Already exists: $INTEGRATION_TEST"
fi

# Generate E2E tests (optional, for tightly coupled modules)
E2E_TEST="tests/e2e/test_${FEATURE_NAME}_e2e.py"
echo ""
read -p "Generate E2E tests? (tightly coupled modules only) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -f "$E2E_TEST" ]; then
        cat > "$E2E_TEST" << EOF
"""E2E tests for ${FEATURE_NAME}

Generated from: $SPEC_FILE
Author: Auto-generated
Date: $(date +%Y-%m-%d)

NOTE: E2E tests required for tightly coupled modules (workflow, installations, projects)
"""

import pytest
from playwright.sync_api import Page, expect


class Test${FEATURE_CLASS}E2E:
    """End-to-end tests for ${FEATURE_NAME} feature."""

    def test_example_user_flow(self, page: Page):
        """Example E2E test - replace with actual user flows from spec."""
        # TODO: Implement user flow from spec
        # Example:
        # page.goto("http://localhost:3000/feature")
        # page.fill("#input", "test data")
        # page.click("button[type=submit]")
        # expect(page.locator(".success-message")).to_be_visible()
        pass


# TODO: Review spec file and implement all test cases marked as "E2E Tests"
# Spec file: $SPEC_FILE

# To run E2E tests:
# pytest tests/e2e/test_${FEATURE_NAME}_e2e.py --headed
EOF
        echo "✅ Created: $E2E_TEST"
    else
        echo "⚠️  Already exists: $E2E_TEST"
    fi
fi

echo ""
echo "📝 Test Generation Complete!"
echo ""
echo "Generated files:"
echo "  - $UNIT_TEST"
echo "  - $INTEGRATION_TEST"
[ -f "$E2E_TEST" ] && echo "  - $E2E_TEST"
echo ""
echo "Next steps:"
echo "1. Review spec: $SPEC_FILE"
echo "2. Implement test cases in generated files"
echo "3. Run tests: pytest tests/ -v"
echo "4. Verify coverage: pytest --cov=. tests/"
echo "5. Validate TDD compliance: /tdd validate"
echo ""
