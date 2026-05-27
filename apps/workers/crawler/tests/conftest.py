"""Shared fixtures for crawler tests using respx."""

import pytest
import respx


@pytest.fixture
def httpx_mock():
    """Provide a respx mock router for httpx requests."""
    with respx.mock(assert_all_called=False) as router:
        yield router
