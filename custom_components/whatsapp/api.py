import asyncio
import contextlib
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WhatsAppApiClient:
    def __init__(self, host: str, api_key: str | None = None) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.api_key = api_key
        self._connected = False
        self.stats: dict[str, Any] = {
            "sent": 0,
            "received": 0,
            "failed": 0,
            "last_sent_message": None,
            "last_sent_target": None,
            "uptime": 0,
        }
        self._callback: Any = None
        self._polling_task: asyncio.Task[Any] | None = None
        self._session: aiohttp.ClientSession | None = None

    async def start_polling(self, interval: int = 2) -> None:
        """Start the polling loop."""
        if self._polling_task:
            return

        self._session = aiohttp.ClientSession()
        self._polling_task = asyncio.create_task(self._poll_loop(interval))
        _LOGGER.debug("Started polling loop with interval %ss", interval)

    async def stop_polling(self) -> None:
        """Stop the polling loop."""
        if self._polling_task:
            self._polling_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._polling_task
            self._polling_task = None

        if self._session:
            await self._session.close()
            self._session = None
        _LOGGER.debug("Stopped polling loop")

    async def _poll_loop(self, interval: int) -> None:
        """Poll for new events."""
        url = f"{self.host}/events"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        while True:
            try:
                if not self._session or self._session.closed:
                    self._session = aiohttp.ClientSession()

                async with self._session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        events = await resp.json()
                        if isinstance(events, list) and self._callback:
                            for event in events:
                                self._callback(event)
                    elif resp.status == 401:
                        _LOGGER.error("Polling failed: Invalid API Key")
                        await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.debug("Polling error: %s", e)
                await asyncio.sleep(5)

            await asyncio.sleep(interval)

    async def start_session(self) -> None:
        """Start (or restart) the session negotiation."""
        url = f"{self.host}/session/start"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                # We just fire and forget, or wait for 200 OK
                async with session.post(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
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
                async with session.delete(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
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
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 401:
                        raise Exception("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get("status", "")
                        qr = data.get("qr", "")
                        _LOGGER.debug(
                            "QR endpoint returned status=%s, qr_present=%s",
                            status,
                            bool(qr),
                        )

                        if status == "connected":
                            # Already connected, no QR needed
                            _LOGGER.info(
                                "Addon reports already connected, no QR code needed"
                            )
                            return ""
                        if status == "waiting":
                            # QR not yet generated
                            _LOGGER.debug("Addon is still generating QR code")
                            return ""
                        # status == "scanning" means QR is available
                        return str(qr) if qr else ""
                    _LOGGER.warning("QR endpoint returned status %s", resp.status)
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
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 401:
                        raise Exception("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        connected = bool(data.get("connected", False))
                        self._connected = connected
                        return connected

                    # Any other status is an error (e.g. 404, 500)
                    raise Exception(f"Unexpected API response: {resp.status}")
            except Exception as e:
                self._connected = False
                if "Invalid API Key" in str(e):
                    raise
                # Connectivity error (ClientConnectorError, etc)
                raise Exception(f"Cannot connect to Addon: {e}") from e
        return False

    async def is_connected(self) -> bool:
        """Return if connected."""
        return self._connected

    async def get_stats(self) -> dict[str, Any]:
        """Fetch stats from the Addon."""
        url = f"{self.host}/stats"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.stats.update(data)
                        return self.stats
            except Exception as e:
                _LOGGER.debug(f"Failed to fetch stats: {e}")
        return self.stats

    def register_callback(self, callback: Any) -> None:
        """Register a callback."""
        self._callback = callback

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

            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to send: {text}")

            # Local fallback increment (stats will update on next poll)
            self.stats["sent"] += 1
            self.stats["last_sent_message"] = message
            self.stats["last_sent_target"] = number

    async def close(self) -> None:
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()
        await self.stop_polling()

    async def send_poll(self, number: str, question: str, options: list[str]) -> None:
        """Send a poll."""
        url = f"{self.host}/send_poll"
        payload = {"number": number, "question": question, "options": options}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                # Track failure in stats?
                self.stats["failed"] += 1
                raise Exception(f"Failed to send poll: {text}")

            if resp.status != 200:
                text = await resp.text()
                # Track failure in stats?
                self.stats["failed"] += 1
                raise Exception(f"Failed to send poll: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Poll: {question}"
            self.stats["last_sent_target"] = number

    async def send_image(
        self, number: str, image_url: str, caption: str | None = None
    ) -> None:
        """Send an image."""
        url = f"{self.host}/send_image"
        payload = {"number": number, "url": image_url, "caption": caption}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send image: {text}")

            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send image: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = "Image Sent"
            self.stats["last_sent_target"] = number

    async def send_location(
        self,
        number: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
    ) -> None:
        """Send a location."""
        url = f"{self.host}/send_location"
        payload = {
            "number": number,
            "latitude": latitude,
            "longitude": longitude,
            "title": name,
            "description": address,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send location: {text}")

            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send location: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Location: {name or 'Pinned'}"
            self.stats["last_sent_target"] = number

    async def send_reaction(self, number: str, text: str, message_id: str) -> None:
        """Send a reaction to a specific message."""
        url = f"{self.host}/send_reaction"
        payload = {"number": number, "reaction": text, "messageId": message_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status != 200:
                text_content = await resp.text()
                raise Exception(f"Failed to send reaction: {text_content}")

    async def set_presence(self, number: str, presence: str) -> None:
        """Set presence (available, composing, recording, paused)."""
        url = f"{self.host}/set_presence"
        payload = {"number": number, "presence": presence}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status != 200:
                text_content = await resp.text()
                raise Exception(f"Failed to set presence: {text_content}")

    async def send_buttons(
        self,
        number: str,
        text: str,
        buttons: list[dict[str, str]],
        footer: str | None = None,
    ) -> None:
        """Send a message with buttons."""
        url = f"{self.host}/send_buttons"
        payload = {
            "number": number,
            "message": text,
            "buttons": buttons,
            "footer": footer,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, json=payload, headers=headers) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send buttons: {text_content}")

            if resp.status != 200:
                text_content = await resp.text()
                self.stats["failed"] += 1
                raise Exception(f"Failed to send buttons: {text_content}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Buttons: {text}"
            self.stats["last_sent_target"] = number
