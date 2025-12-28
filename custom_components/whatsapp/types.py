"""Type definitions for the HA WhatsApp integration."""
from dataclasses import dataclass
from typing import Any


@dataclass
class WhatsAppConfig:
    """Config data."""
    session_data: str

@dataclass
class WhatsAppMessage:
    """Message data."""
    target_number: str
    content: str
    attachments: list[str] | None = None
    buttons: list[dict[str, Any]] | None = None
