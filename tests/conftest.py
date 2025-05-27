"""Pytest configuration and fixtures."""

import pytest
import os


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original value
    original_key = os.environ.get("INCEPTION_API_KEY")
    
    # Clear the env var
    if "INCEPTION_API_KEY" in os.environ:
        del os.environ["INCEPTION_API_KEY"]
    
    yield
    
    # Restore original value
    if original_key is not None:
        os.environ["INCEPTION_API_KEY"] = original_key