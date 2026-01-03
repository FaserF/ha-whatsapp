import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WhatsAppApiClient:
    def __init__(self, host: str, api_key: str = None) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.api_key = api_key
        self._connected = False

    async def start_session(self) -> None:
        """Start (or restart) the session negotiation."""
        url = f"{self.host}/session/start"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                # We just fire and forget, or wait for 200 OK
                async with session.post(url, headers=headers, timeout=5) as resp:
                    if resp.status == 401:
                        raise Exception("Invalid API Key")
                    if resp.status != 200:
                        _LOGGER.error("Start session failed: %s", resp.status)
                        # We don't raise here strictly to allow "already started" flows?
                        # But 401 must raise.
            except Exception as e:
                if "Invalid API Key" in str(e):
                    raise
                _LOGGER.error("Failed to start session: %s", e)
                raise

    async def delete_session(self) -> None:
        """Delete the session (Logout/Reset)."""
        url = f"{self.host}/session"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.delete(url, headers=headers, timeout=5) as resp:
                     if resp.status == 401:
                         raise Exception("Invalid API Key")
            except Exception as e:
                _LOGGER.error("Failed to delete session: %s", e)

    async def get_qr_code(self) -> str:
        """Get the QR code from the Addon."""
        url = f"{self.host}/qr"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as resp:
                     if resp.status == 401:
                         raise Exception("Invalid API Key")
                     if resp.status == 200:
                         data = await resp.json()
                         return data.get("qr", "")
                     return ""
            except Exception as e:
                 if "Invalid API Key" in str(e):
                     raise
                 _LOGGER.error("Error fetching QR from addon: %s", e)
                 return ""

    async def connect(self) -> bool:
        """Check connection and validate Auth."""
        url = f"{self.host}/status"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=5) as resp:
                    if resp.status == 401:
                        raise Exception("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        connected = data.get("connected", False)
                        self._connected = connected
                        return connected

                    # Any other status is an error (e.g. 404, 500)
                    raise Exception(f"Unexpected API response: {resp.status}")
            except Exception as e:
                if "Invalid API Key" in str(e):
                    raise
                # Connectivity error (ClientConnectorError, etc)
                raise Exception(f"Cannot connect to Addon: {e}") from e
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
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
                if resp.status == 401:
                     raise Exception("Invalid API Key")
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Failed to send: {text}")

    async def close(self) -> None:
        """Close session."""
        pass
