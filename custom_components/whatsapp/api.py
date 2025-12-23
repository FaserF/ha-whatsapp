"""API Client for HA WhatsApp."""
from __future__ import annotations

import logging
from typing import Any, Dict

_LOGGER = logging.getLogger(__name__)

from typing import Any, Dict, Callable

_LOGGER = logging.getLogger(__name__)

class WhatsAppApiClient:
    """Sample API Client."""

    def __init__(self, session_data: str | None = None) -> None:
        """Initialize."""
        self.session_data = session_data
        self._connected = False
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

    def register_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for incoming messages."""
        self._callbacks.append(callback)

    def _mock_incoming_message(self) -> None:
        """Mock receiving a message (for testing)."""
        data = {
            "sender": "123456789",
            "content": "Hello from WhatsApp",
            "timestamp": 1234567890
        }
        for callback in self._callbacks:
            callback(data)


    async def get_qr_code(self) -> str:
        """Get the QR code for scanning.

        Returns:
            A base64 encoded string or a raw string for the QR code.
        """
        # Mocking a QR code string
        return "mock_qr_token_data"

    async def connect(self) -> bool:
        """Connect to the WhatsApp service."""
        # Mock connection logic
        self._connected = True
        return True

    async def is_connected(self) -> bool:
        """Return True if connected."""
        return self._connected

    async def send_message(self, number: str, message: str) -> None:
        """Send a message."""
        if not self._connected:
            raise ConnectionError("Not connected")
        _LOGGER.info("Sending message to %s: %s", number, message)

    async def send_image(self, number: str, image_path: str, caption: str | None = None) -> None:
        """Send an image."""
        if not self._connected:
            raise ConnectionError("Not connected")
        _LOGGER.info("Sending image to %s: %s", number, image_path)

    async def send_poll(self, number: str, question: str, options: list[str]) -> None:
        """Send a poll."""
        if not self._connected:
            raise ConnectionError("Not connected")
        _LOGGER.info("Sending poll to %s: %s %s", number, question, options)
