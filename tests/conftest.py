"""
Pytest configuration and shared fixtures for agent tests.
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_anthropic_api_key():
    """Provide a mock Anthropic API key for testing."""
    return "sk-ant-test-mock-api-key-for-testing-only"


@pytest.fixture
def mock_database_url():
    """Provide a mock database URL for testing."""
    return "postgresql://testuser:testpass@localhost:5432/testdb"


@pytest.fixture
def mock_convex_url():
    """Provide a mock Convex URL for testing."""
    return "https://test-deployment.convex.cloud"


@pytest.fixture
def mock_vps_hostname():
    """Provide a mock VPS hostname for testing."""
    return "test.example.com"
