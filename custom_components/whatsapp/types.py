"""Type definitions for the HA WhatsApp integration."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WhatsAppConfig:
    """Config data."""
    session_data: str

@dataclass
class WhatsAppMessage:
    """Message data."""
    target_number: str
    content: str
    attachments: Optional[List[str]] = None
    buttons: Optional[List[Dict[str, Any]]] = None
