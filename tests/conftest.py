"""Global fixtures for ha-whatsapp integration tests."""

from typing import Any

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: Any,  # noqa: ARG001
) -> Any:
    """Enable custom integrations defined in the test dir."""
    yield
