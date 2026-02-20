"""Global fixtures for ha-whatsapp integration tests."""

from collections.abc import Generator

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations() -> Generator[None, None, None]:
    """Stub for auto_enable_custom_integrations."""
    yield
