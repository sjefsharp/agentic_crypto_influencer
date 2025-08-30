"""
Pytest configuration and shared fixtures for the agentic crypto influencer project.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for the entire test session."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_crypto_data():
    """Sample cryptocurrency data for testing."""
    return {
        "bitcoin": {
            "symbol": "BTC",
            "price": 45000.0,
            "change_24h": 2.5,
            "market_cap": 850000000000,
        },
        "ethereum": {
            "symbol": "ETH",
            "price": 3000.0,
            "change_24h": -1.2,
            "market_cap": 360000000000,
        },
    }


@pytest.fixture
def mock_api_response():
    """Mock API response for testing."""
    return {
        "status": "success",
        "data": {
            "price": 45000.0,
            "volume": 2500000000,
            "timestamp": "2025-01-30T12:00:00Z",
        },
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """Setup test environment with temporary paths and mocked external dependencies."""
    # Mock environment variables for testing
    monkeypatch.setenv("TESTING", "true")

    # Create temporary config directory
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Mock any external API keys if needed
    monkeypatch.setenv("MOCK_API_KEY", "test_key_123")


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "smoke: marks tests as smoke tests")


# Test selection helpers
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark slow tests
        if "slow" in item.nodeid or "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in item.nodeid or "api" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default)
        if not any(
            marker.name in ["slow", "integration"] for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)
