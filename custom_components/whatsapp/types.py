"""Type definitions for the HA WhatsApp integration.

This module provides lightweight :mod:`dataclasses` that are used as
typed containers for configuration and message data throughout the
integration.

Classes:
    WhatsAppConfig: Holds raw session configuration data as returned by
        the addon.
    WhatsAppMessage: Represents an outgoing WhatsApp message with its
        target, content, and optional attachments / buttons.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WhatsAppConfig:
    """Configuration data for a WhatsApp addon session.

    Attributes:
        session_data (str): Opaque session string returned by the addon
            that encodes the active WhatsApp session.
    """

    session_data: str


@dataclass
class WhatsAppMessage:
    """Data for an outgoing WhatsApp message.

    Attributes:
        target_number (str): Destination phone number or JID.
        content (str): Text body of the message.
        attachments (list[str] | None): Optional list of media URLs to
            attach to the message.
        buttons (list[dict[str, Any]] | None): Optional list of button
            definitions.  Each button is a dict with at least the keys
            ``id`` and ``displayText``.
    """

    target_number: str
    content: str
    attachments: list[str] | None = None
    buttons: list[dict[str, Any]] | None = None
