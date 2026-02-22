"""HTTP client for the HA WhatsApp addon REST API.

This module provides :class:`WhatsAppApiClient`, an ``aiohttp``-based client
that communicates with the WhatsApp addon over its HTTP REST API.  Every
public method maps to one (or more) addon endpoints and follows the same
pattern:

1. Validate whether the target is on the whitelist.
2. Normalise the target to a valid WhatsApp JID via :meth:`ensure_jid`.
3. Delegate to a private ``*_internal`` helper that performs the actual
   HTTP request.
4. Retry on transient failures via :meth:`_send_with_retry`.

The client also manages an event-polling loop that calls a registered
callback whenever new messages arrive from the addon.

Example usage::

    client = WhatsAppApiClient(host="http://localhost:8066", api_key="secret")
    await client.start_polling(interval=5)
    await client.send_message("491234567890", "Hello from HA!")
    await client.close()
"""

import asyncio
import contextlib
import json
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class WhatsAppAuthError(HomeAssistantError):  # type: ignore[misc]
    """Raised when the API key is invalid."""


class WhatsAppApiClient:  # noqa: PLR0904 – many public API methods are intentional
    """Async HTTP client for the HA WhatsApp addon.

    This client wraps every HTTP endpoint exposed by the WhatsApp addon
    and provides a Pythonic interface for Home Assistant integrations.

    Attributes:
        host (str): Base URL of the addon, e.g. ``http://localhost:8066``.
        api_key (str | None): Optional API key sent in the
            ``X-Auth-Token`` header.
        session_id (str): Identifier of the WhatsApp session managed by the
            addon.  Defaults to ``"default"``.
        mask_sensitive_data (bool): When ``True``, phone numbers and message
            contents are partially masked in log output.
        whitelist (list[str]): Phone numbers / JIDs that are allowed to
            receive messages.  An empty list disables filtering.
        retry_attempts (int): Number of *extra* attempts after the first
            failure (0 = no retry).
        stats (dict[str, Any]): Running statistics updated after every
            send/receive operation.  Keys: ``sent``, ``received``,
            ``failed``, ``last_sent_message``, ``last_sent_target``,
            ``last_failed_message``, ``last_failed_target``,
            ``last_error_reason``, ``uptime``, ``version``, ``my_number``.
    """

    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        session_id: str = "default",
        mask_sensitive_data: bool = False,
        whitelist: list[str] | None = None,
    ) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.session_id = session_id
        self.mask_sensitive_data = mask_sensitive_data
        self.whitelist = whitelist or []
        self.retry_attempts = 2
        self._connected = False
        self.stats: dict[str, Any] = {
            "sent": 0,
            "received": 0,
            "failed": 0,
            "last_sent_message": None,
            "last_sent_target": None,
            "last_failed_message": None,
            "last_failed_target": None,
            "last_error_reason": None,
            "uptime": 0,
            "version": None,
            "my_number": None,
        }
        self._callback: Any = None
        self._polling_task: asyncio.Task[Any] | None = None
        self._session: aiohttp.ClientSession | None = None

    def _extract_error(self, text: str) -> str:
        """Extract a clean error message from a JSON response."""
        try:
            data = json.loads(text)
            return data.get("detail") or data.get("error") or text
        except (json.JSONDecodeError, AttributeError):
            return text

    def is_allowed(self, target: str) -> bool:
        """Check if a target JID is allowed by the whitelist."""
        if not self.whitelist:
            return True

        # Normalize target for comparison
        target_jid = self.ensure_jid(target)
        if not target_jid:
            _LOGGER.warning("Could not normalize target '%s' to a valid JID", target)
            return False

        for allowed_entry in self.whitelist:
            allowed = allowed_entry.strip()
            if not allowed:
                continue

            # 1. Full JID comparison (contains @)
            if "@" in allowed:
                entry_jid = self.ensure_jid(allowed)
                if entry_jid and target_jid == entry_jid:
                    return True

            # 2. Group ID comparison (hyphenated, no @)
            elif "-" in allowed:
                # Remove spaces, but keep digits and hyphen
                clean_group = "".join(c for c in allowed if c.isdigit() or c == "-")
                if target_jid == f"{clean_group}@g.us":
                    return True

            # 3. Numeric / Phone comparison
            else:
                # Clean entry: remove +, spaces, and other non-digits
                clean_allowed = "".join(filter(str.isdigit, allowed))
                if clean_allowed and target_jid.split("@")[0] == clean_allowed:
                    return True

        _LOGGER.info(
            "Blocking outgoing message to non-whitelisted target: %s",
            self.mask(target),
        )
        return False

    def ensure_jid(self, target: str | None) -> str | None:
        """Ensure the target is a valid JID.

        Handles:
        - Full JIDs with @domain
        - Old-style group IDs with hyphen (creator-timestamp)
        - Modern numeric group IDs (16+ digits)
        - Phone numbers
        """
        if not target:
            return target

        target = target.strip()

        # If it already has an @, assume it's a full JID (e.g. standard, group, or lid)
        if "@" in target:
            return target.replace("+", "") if target.startswith("+") else target

        # If it contains exactly one hyphen and both parts are numeric,
        # it's likely an old-style group ID (creator-timestamp)
        if "-" in target:
            parts = target.split("-")
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                return f"{target}@g.us"

        # Clean all non-digit characters for further analysis
        clean_number = "".join(filter(str.isdigit, target))

        # Modern group IDs are typically 16-20 digits (much longer than phone numbers)
        # E.164 phone numbers are max 15 digits (including country code)
        if len(clean_number) >= 16:
            return f"{clean_number}@g.us"

        # Default: treat as phone number
        return f"{clean_number}@s.whatsapp.net"

    def mask(self, text: str) -> str:
        """Mask sensitive data if enabled."""
        if not self.mask_sensitive_data or not text:
            return text
        if len(text) <= 4:
            return "****"
        return f"{text[:3]}****{text[-2:]}"

    def _mask(self, text: str) -> str:
        """Deprecated: use mask()."""
        return self.mask(text)

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
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        while True:
            try:
                if not self._session or self._session.closed:
                    self._session = aiohttp.ClientSession()

                async with self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        events = await resp.json()
                        if isinstance(events, list) and self._callback:
                            for event in events:
                                # Mask sensitive data if needed (debug logging)
                                if _LOGGER.isEnabledFor(logging.DEBUG):
                                    # Optionally mask deep structure here if strictly
                                    # required
                                    _LOGGER.debug("Received event: %s", events)
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
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                # We just fire and forget, or wait for 200 OK
                async with session.post(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 401:
                        raise HomeAssistantError("Invalid API Key")
                    if resp.status != 200:
                        _LOGGER.error("Start session failed: %s", resp.status)
                        # We don't raise here strictly to allow "already started" flows?
                        # But 401 must raise.
            except HomeAssistantError:
                raise
            except Exception as e:
                _LOGGER.error("Failed to start session: %s", e)
                raise HomeAssistantError(f"Failed to start session: {e}") from e

    async def delete_session(self) -> None:
        """Delete the session (Logout/Reset)."""
        url = f"{self.host}/session"
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.delete(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 401:
                        raise HomeAssistantError("Invalid API Key")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HomeAssistantError(f"Addon error {resp.status}: {text}")
            except Exception as e:
                _LOGGER.error("Failed to delete session: %s", e)
                raise HomeAssistantError(f"Failed to delete session: {e}") from e

    async def get_qr_code(self) -> str:
        """Get the QR code from the Addon."""
        url = f"{self.host}/qr"
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise HomeAssistantError("Invalid API Key")
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
            except HomeAssistantError:
                raise
            except Exception as e:
                _LOGGER.error("Error fetching QR from addon: %s", e)
                return ""

    async def connect(self) -> bool:
        """Check connection and validate Auth."""
        url = f"{self.host}/status"
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 401:
                        raise HomeAssistantError("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        connected = bool(data.get("connected", False))
                        self._connected = connected
                        return connected

                    # Any other status is an error
                    _LOGGER.debug("Unexpected API response in connect: %s", resp.status)
                    self._connected = False
                    return False
            except HomeAssistantError:
                self._connected = False
                raise
            except Exception as e:
                self._connected = False
                # Connectivity error (ClientConnectorError, etc)
                _LOGGER.debug("Cannot connect to Addon: %s", e)
                return False

    async def is_connected(self) -> bool:
        """Return if connected."""
        return self._connected

    async def get_stats(self) -> dict[str, Any]:
        """Fetch stats from the Addon."""
        url = f"{self.host}/stats"
        params = {"session_id": self.session_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.stats.update(data)
                        return self.stats
            except Exception as e:
                _LOGGER.debug("Failed to fetch stats: %s", e)
        return self.stats

    def register_callback(self, callback: Any) -> None:
        """Register a callback."""
        self._callback = callback

    async def send_message(
        self, number: str, message: str, quoted_message_id: str | None = None
    ) -> None:
        """Send message via Addon (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_message_internal, target_jid, message, quoted_message_id
        )

    async def _send_message_internal(
        self, number: str, message: str, quoted_message_id: str | None = None
    ) -> None:
        """Internal send message logic."""
        url = f"{self.host}/send_message"
        params = {"session_id": self.session_id}
        payload: dict[str, Any] = {
            "number": number,
            "message": message,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = message
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send: {error_msg}")

            # Local fallback increment (stats will update on next poll)
            self.stats["sent"] += 1
            self.stats["last_sent_message"] = message
            self.stats["last_sent_target"] = number

    async def _send_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Helper to retry API calls."""
        last_error: Exception | None = None
        for attempt in range(self.retry_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except WhatsAppAuthError:
                raise
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts:
                    _LOGGER.warning(
                        "Attempt %s failed to send WhatsApp message: %s. Retrying...",
                        attempt + 1,
                        e,
                    )
                    await asyncio.sleep(1)
                else:
                    _LOGGER.error(
                        "All %s attempts failed to send WhatsApp message: %s",
                        self.retry_attempts + 1,
                        e,
                    )

        if last_error:
            raise last_error

        # Should never reach here if retry_attempts >= 0 and no error occurs
        # as func returns directly in the loop.
        return None

    async def close(self) -> None:
        """Close session."""
        if self._session and not self._session.closed:
            await self._session.close()
        await self.stop_polling()

    async def send_poll(
        self,
        number: str,
        question: str,
        options: list[str],
        quoted_message_id: str | None = None,
    ) -> None:
        """Send a poll (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_poll_internal, target_jid, question, options, quoted_message_id
        )

    async def _send_poll_internal(
        self,
        number: str,
        question: str,
        options: list[str],
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send poll logic."""
        url = f"{self.host}/send_poll"
        payload: dict[str, Any] = {
            "number": number,
            "question": question,
            "options": options,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Poll: {question}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send poll: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Poll: {question}"
            self.stats["last_sent_target"] = number

    async def send_image(
        self,
        number: str,
        image_url: str,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send an image (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_image_internal, target_jid, image_url, caption, quoted_message_id
        )

    async def _send_image_internal(
        self,
        number: str,
        image_url: str,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send image logic."""
        url = f"{self.host}/send_image"
        payload: dict[str, Any] = {
            "number": number,
            "url": image_url,
            "caption": caption,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = (
                    "Image" if not caption else f"Image: {caption}"
                )
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send image: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = "Image Sent"
            self.stats["last_sent_target"] = number

    async def send_document(
        self,
        number: str,
        url: str,
        file_name: str | None = None,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send a document (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_document_internal,
            target_jid,
            url,
            file_name,
            caption,
            quoted_message_id,
        )

    async def _send_document_internal(
        self,
        number: str,
        url: str,
        file_name: str | None = None,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send document logic."""
        api_url = f"{self.host}/send_document"
        payload: dict[str, Any] = {
            "number": number,
            "url": url,
            "fileName": file_name,
            "caption": caption,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                label = file_name or "unnamed"
                self.stats["last_failed_message"] = f"Document: {label}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send document: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Document: {file_name or 'unnamed'}"
            self.stats["last_sent_target"] = number

    async def send_video(
        self,
        number: str,
        url: str,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send a video (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_video_internal, target_jid, url, caption, quoted_message_id
        )

    async def _send_video_internal(
        self,
        number: str,
        url: str,
        caption: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send video logic."""
        api_url = f"{self.host}/send_video"
        payload: dict[str, Any] = {
            "number": number,
            "url": url,
            "caption": caption,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=60),  # Longer timeout for video
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Video: {caption or 'unnamed'}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send video: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Video: {caption or 'unnamed'}"
            self.stats["last_sent_target"] = number

    async def send_audio(
        self,
        number: str,
        url: str,
        ptt: bool = False,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send audio (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_audio_internal, target_jid, url, ptt, quoted_message_id
        )

    async def _send_audio_internal(
        self,
        number: str,
        url: str,
        ptt: bool = False,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send audio logic."""
        api_url = f"{self.host}/send_audio"
        payload: dict[str, Any] = {
            "number": number,
            "url": url,
            "ptt": ptt,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=60),  # Longer timeout for audio
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = "Voice Note" if ptt else "Audio"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send audio: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = "Voice Note" if ptt else "Audio"
            self.stats["last_sent_target"] = number

    async def revoke_message(
        self,
        number: str,
        message_id: str,
    ) -> None:
        """Revoke (delete) a message."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._revoke_message_internal, target_jid, message_id
        )

    async def _revoke_message_internal(
        self,
        number: str,
        message_id: str,
    ) -> None:
        """Internal revoke message logic."""
        api_url = f"{self.host}/revoke_message"
        payload = {"number": number, "message_id": message_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                raise HomeAssistantError(f"Failed to revoke message: {error_msg}")

    async def edit_message(
        self,
        number: str,
        message_id: str,
        new_content: str,
    ) -> None:
        """Edit a message."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._edit_message_internal, target_jid, message_id, new_content
        )

    async def _edit_message_internal(
        self,
        number: str,
        message_id: str,
        new_content: str,
    ) -> None:
        """Internal edit message logic."""
        api_url = f"{self.host}/edit_message"
        payload = {
            "number": number,
            "message_id": message_id,
            "new_content": new_content,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                raise HomeAssistantError(f"Failed to edit message: {error_msg}")

    async def send_location(
        self,
        number: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send a location (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_location_internal,
            target_jid,
            latitude,
            longitude,
            name,
            address,
            quoted_message_id,
        )

    async def _send_location_internal(
        self,
        number: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send location logic."""
        url = f"{self.host}/send_location"
        payload = {
            "number": number,
            "latitude": latitude,
            "longitude": longitude,
            "title": name,
            "description": address,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Location: {name or 'Pinned'}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send location: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Location: {name or 'Pinned'}"
            self.stats["last_sent_target"] = number

    async def send_reaction(
        self,
        number: str,
        text: str,
        message_id: str,
    ) -> None:
        """Send a reaction to a specific message (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_reaction_internal, target_jid, text, message_id
        )

    async def _send_reaction_internal(
        self, number: str, text: str, message_id: str
    ) -> None:
        """Internal send reaction logic."""
        url = f"{self.host}/send_reaction"
        payload = {"number": number, "reaction": text, "messageId": message_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                error_msg = self._extract_error(text_content)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Reaction: {text}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send reaction: {error_msg}")

    async def set_webhook(
        self,
        url: str,
        enabled: bool = True,
        token: str | None = None,
    ) -> None:
        """Configure the webhook settings on the Addon."""
        api_url = f"{self.host}/settings/webhook"
        payload = {"url": url, "enabled": enabled}
        if token:
            payload["token"] = token
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp,
        ):
            if resp.status == 401:
                raise HomeAssistantError("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                error_msg = self._extract_error(text)
                raise HomeAssistantError(f"Failed to set webhook: {error_msg}")

    async def send_list(
        self,
        number: str,
        title: str,
        text: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> None:
        """Send a list message (interactive menu)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_list_internal, target_jid, title, text, button_text, sections
        )

    async def _send_list_internal(
        self,
        number: str,
        title: str,
        text: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> None:
        """Internal send list logic."""
        api_url = f"{self.host}/send_list"
        payload = {
            "number": number,
            "title": title,
            "text": text,
            "button_text": button_text,
            "sections": sections,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                resp_text = await resp.text()
                error_msg = self._extract_error(resp_text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"List: {title}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send list: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"List: {title}"
            self.stats["last_sent_target"] = number

    async def send_contact(
        self,
        number: str,
        contact_name: str,
        contact_number: str,
    ) -> None:
        """Send a contact card (VCard)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_contact_internal, target_jid, contact_name, contact_number
        )

    async def _send_contact_internal(
        self,
        number: str,
        contact_name: str,
        contact_number: str,
    ) -> None:
        """Internal send contact logic."""
        api_url = f"{self.host}/send_contact"
        payload = {
            "number": number,
            "contact_name": contact_name,
            "contact_number": contact_number,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                resp_text = await resp.text()
                error_msg = self._extract_error(resp_text)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Contact: {contact_name}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send contact: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Contact: {contact_name}"
            self.stats["last_sent_target"] = number

    async def set_presence(self, number: str, presence: str) -> None:
        """Set presence (available, composing, recording, paused)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        url = f"{self.host}/set_presence"
        payload = {"number": target_jid, "presence": presence}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise HomeAssistantError("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                error_msg = self._extract_error(text_content)
                raise HomeAssistantError(f"Failed to set presence: {error_msg}")

    async def send_buttons(
        self,
        number: str,
        text: str,
        buttons: list[dict[str, str]],
        footer: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Send a message with buttons (with retry)."""
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        await self._send_with_retry(
            self._send_buttons_internal,
            target_jid,
            text,
            buttons,
            footer,
            quoted_message_id,
        )

    async def _send_buttons_internal(
        self,
        number: str,
        text: str,
        buttons: list[dict[str, str]],
        footer: str | None = None,
        quoted_message_id: str | None = None,
    ) -> None:
        """Internal send buttons logic."""
        url = f"{self.host}/send_buttons"
        payload = {
            "number": number,
            "message": text,
            "buttons": buttons,
            "footer": footer,
        }
        if quoted_message_id is not None:
            payload["quotedMessageId"] = quoted_message_id
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise WhatsAppAuthError("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                error_msg = self._extract_error(text_content)
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Buttons: {text}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = error_msg
                raise HomeAssistantError(f"Failed to send buttons: {error_msg}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Buttons: {text}"
            self.stats["last_sent_target"] = number

    async def get_groups(self) -> list[dict[str, Any]]:
        """Fetch all participating groups."""
        url = f"{self.host}/groups"
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    params={"session_id": self.session_id},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise HomeAssistantError("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        return list(data)
                    _LOGGER.warning("Groups endpoint returned status %s", resp.status)
                    return []
            except HomeAssistantError:
                raise
            except Exception as e:
                _LOGGER.error("Error fetching groups from addon: %s", e)
                return []

    async def mark_as_read(self, number: str, message_id: str | None = None) -> None:
        """Mark a message (or all messages) as read.

        Args:
            number: Target phone number or group ID
            message_id: Optional specific message ID.
                If None, marks all unread messages.
        """
        if not self.is_allowed(number):
            raise HomeAssistantError(f"Target {number} is not in the whitelist.")
        target_jid = self.ensure_jid(number)
        if not target_jid:
            raise HomeAssistantError(f"Could not parse valid JID from target: {number}")
        url = f"{self.host}/mark_as_read"
        payload: dict[str, Any] = {"number": target_jid}
        if message_id:
            payload["messageId"] = message_id
        # If no messageId, addon will mark all unread messages
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                params={"session_id": self.session_id},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise HomeAssistantError("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                error_msg = self._extract_error(text_content)
                raise HomeAssistantError(f"Failed to mark message as read: {error_msg}")
