"""Helper utilities for HA WhatsApp integration."""

from __future__ import annotations

from typing import TypeVar, cast

T = TypeVar("T")


def safe_text(value: T) -> T:  # noqa: UP047
    """Safely sanitize text values by replacing invalid Unicode surrogates.

    Prevents Home Assistant WebSocket serialization errors when entity state
    attributes contain invalid Unicode surrogate pairs.
    """
    if isinstance(value, str):
        return cast(
            T, value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        )
    if isinstance(value, dict):
        return cast(T, {safe_text(k): safe_text(v) for k, v in value.items()})
    if isinstance(value, list):
        return cast(T, [safe_text(v) for v in value])
    return value
