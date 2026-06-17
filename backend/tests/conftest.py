"""
Pytest configuration and environment overrides.
"""
import os
import asyncio
import pytest

# Set ENVIRONMENT to testing before any app modules are imported
os.environ["ENVIRONMENT"] = "testing"

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop to prevent event loop mismatch errors in tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
