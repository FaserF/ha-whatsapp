"""Lightweight REST Client for connecting to the WhatsApp Addon."""

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WhatsAppApiClient:
    """REST Client for the WhatsApp Addon."""

    # In Home Assistant Addons, the hostname is the slug usually.
    # Or configurable via user input.
    # For local addon communication, we might default to 'http://local-whatsapp-addon:8000'
    # but practically we let the user configure the URL or try to discover it.

    def __init__(self, host: str = "http://localhost:8000") -> None:
        """Initialize."""
        self.host = host.rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        self._connected: bool = False

    async def get_qr_code(self) -> str:
        """Get the QR code from the Addon."""
        url = f"{self.host}/qr"
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return str(data.get("qr", ""))
                    return ""
            except Exception as e:
                _LOGGER.error("Error fetching QR from addon: %s", e)
                return ""

    async def connect(self) -> bool:
        """Check if connected (by checking status)."""
        url = f"{self.host}/status"
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        connected = bool(data.get("connected", False))
                        self._connected = connected
                        return connected
            except Exception:
                self._connected = False
                return False
        self._connected = False
        return False

    async def is_connected(self) -> bool:
        """Return if connected."""
        return self._connected

    def register_callback(self, callback: Any) -> None:
        """Register a callback."""
        # Check logic later, for now stubs to satisfy MyPy and usage
        pass

    async def send_message(self, number: str, message: str) -> None:
        """Send message via Addon."""
        url = f"{self.host}/send_message"
        payload = {"number": number, "message": message}

        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload) as resp,
        ):
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to send: {text}")

    async def send_poll(self, number: str, question: str, options: list[str]) -> None:
        """Send a poll."""
        # Stub implementation
        pass

    async def close(self) -> None:
        """Close session."""
        pass
