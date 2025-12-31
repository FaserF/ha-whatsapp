"""Global fixtures for ha-whatsapp integration tests."""

from collections.abc import Generator
from typing import Any

import pytest


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def auto_enable_custom_integrations(
    _enable_custom_integrations: Any,
) -> Generator[None, None, None]:
    """Enable custom integrations defined in the test dir."""
    yield
