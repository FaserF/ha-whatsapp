"""Global fixtures for ha-whatsapp integration tests."""

from collections.abc import Generator
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: Any,  # noqa: ARG001
) -> Generator[None, None, None]:
    """Enable custom integrations defined in the test dir."""
    yield
