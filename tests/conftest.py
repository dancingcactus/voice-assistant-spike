"""
Pytest configuration for E2E tests

Provides fixtures and configuration for the test suite.
"""

import pytest
import httpx
import time
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "character: mark test as character validation"
    )


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def check_server_running(base_url):
    """Check that the server is running before tests"""
    try:
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        response.raise_for_status()
        print(f"\n✓ Server is running at {base_url}")
    except Exception as e:
        pytest.exit(
            f"Server is not running at {base_url}. "
            f"Please start the server before running E2E tests.\n"
            f"Error: {e}"
        )


@pytest.fixture(scope="function", autouse=True)
def rate_limit():
    """Add small delay between tests to avoid rate limiting"""
    yield
    time.sleep(0.1)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark all tests in test_e2e.py as e2e tests
        if "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Mark character tests
        if "character" in item.name.lower() or "mode" in item.name.lower():
            item.add_marker(pytest.mark.character)
