"""Global fixtures for ha-whatsapp integration tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ARG001
    """Enable custom integrations defined in the test dir."""
    yield
