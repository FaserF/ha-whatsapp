import asyncio
import contextlib
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WhatsAppApiClient:
    def __init__(
        self,
        host: str,
        api_key: str | None = None,
        mask_sensitive_data: bool = False,
        whitelist: list[str] | None = None,
    ) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.api_key = api_key
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

        _LOGGER.info("Blocking outgoing message to non-whitelisted target: %s", target)
        return False

    def ensure_jid(self, target: str | None) -> str | None:
        """Ensure the target is a valid JID."""
        if not target:
            return target

        target = target.strip()

        # If it already has an @, assume it's a full JID (e.g. standard, group, or lid)
        if "@" in target:
            return target.replace("+", "") if target.startswith("+") else target

        # If it contains exactly one hyphen and both parts are numeric, it's likely a group ID
        if "-" in target:
            parts = target.split("-")
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                return f"{target}@g.us"

        # Otherwise treat as phone number
        # Remove any leading + and non-digit characters
        clean_number = "".join(filter(str.isdigit, target))
        return f"{clean_number}@s.whatsapp.net"

    def _mask(self, text: str) -> str:
        """Mask sensitive data if enabled."""
        if not self.mask_sensitive_data or not text:
            return text
        if len(text) <= 4:
            return "****"
        return f"{text[:3]}****{text[-2:]}"

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
                    if resp.status != 200:
                        text = await resp.text()
                        raise Exception(f"Addon error {resp.status}: {text}")
            except Exception as e:
                _LOGGER.error("Failed to delete session: %s", e)
                raise

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

                    # Any other status is an error
                    _LOGGER.debug("Unexpected API response in connect: %s", resp.status)
                    self._connected = False
                    return False
            except Exception as e:
                self._connected = False
                if "Invalid API Key" in str(e):
                    raise
                # Connectivity error (ClientConnectorError, etc)
                _LOGGER.debug("Cannot connect to Addon: %s", e)
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
        """Send message via Addon (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(self._send_message_internal, number, message)

    async def _send_message_internal(self, number: str, message: str) -> None:
        """Internal send message logic."""
        url = f"{self.host}/send_message"
        payload = {"number": number, "message": message}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = message
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send: {text}")

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

    async def send_poll(self, number: str, question: str, options: list[str]) -> None:
        """Send a poll (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(self._send_poll_internal, number, question, options)

    async def _send_poll_internal(
        self, number: str, question: str, options: list[str]
    ) -> None:
        """Internal send poll logic."""
        url = f"{self.host}/send_poll"
        payload = {"number": number, "question": question, "options": options}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Poll: {question}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send poll: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Poll: {question}"
            self.stats["last_sent_target"] = number

    async def send_image(
        self, number: str, image_url: str, caption: str | None = None
    ) -> None:
        """Send an image (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_image_internal, number, image_url, caption
        )

    async def _send_image_internal(
        self, number: str, image_url: str, caption: str | None = None
    ) -> None:
        """Internal send image logic."""
        url = f"{self.host}/send_image"
        payload = {"number": number, "url": image_url, "caption": caption}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = (
                    "Image" if not caption else f"Image: {caption}"
                )
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send image: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = "Image Sent"
            self.stats["last_sent_target"] = number

    async def send_document(
        self,
        number: str,
        url: str,
        file_name: str | None = None,
        caption: str | None = None,
    ) -> None:
        """Send a document (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_document_internal, number, url, file_name, caption
        )

    async def _send_document_internal(
        self,
        number: str,
        url: str,
        file_name: str | None = None,
        caption: str | None = None,
    ) -> None:
        """Internal send document logic."""
        api_url = f"{self.host}/send_document"
        payload = {
            "number": number,
            "url": url,
            "fileName": file_name,
            "caption": caption,
        }
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                label = file_name or "unnamed"
                self.stats["last_failed_message"] = f"Document: {label}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send document: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Document: {file_name or 'unnamed'}"
            self.stats["last_sent_target"] = number

    async def send_video(
        self,
        number: str,
        url: str,
        caption: str | None = None,
    ) -> None:
        """Send a video (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(self._send_video_internal, number, url, caption)

    async def _send_video_internal(
        self,
        number: str,
        url: str,
        caption: str | None = None,
    ) -> None:
        """Internal send video logic."""
        api_url = f"{self.host}/send_video"
        payload = {"number": number, "url": url, "caption": caption}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),  # Longer timeout for video
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Video: {caption or 'unnamed'}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send video: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Video: {caption or 'unnamed'}"
            self.stats["last_sent_target"] = number

    async def send_audio(
        self,
        number: str,
        url: str,
        ptt: bool = False,
    ) -> None:
        """Send audio (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(self._send_audio_internal, number, url, ptt)

    async def _send_audio_internal(
        self,
        number: str,
        url: str,
        ptt: bool = False,
    ) -> None:
        """Internal send audio logic."""
        api_url = f"{self.host}/send_audio"
        payload = {"number": number, "url": url, "ptt": ptt}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),  # Longer timeout for audio
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = "Voice Note" if ptt else "Audio"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send audio: {text}")

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
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(self._revoke_message_internal, number, message_id)

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
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to revoke message: {text}")

    async def edit_message(
        self,
        number: str,
        message_id: str,
        new_content: str,
    ) -> None:
        """Edit a message."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._edit_message_internal, number, message_id, new_content
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
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to edit message: {text}")

    async def send_location(
        self,
        number: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
    ) -> None:
        """Send a location (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_location_internal, number, latitude, longitude, name, address
        )

    async def _send_location_internal(
        self,
        number: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
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
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Location: {name or 'Pinned'}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text
                raise Exception(f"Failed to send location: {text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Location: {name or 'Pinned'}"
            self.stats["last_sent_target"] = number

    async def send_reaction(self, number: str, text: str, message_id: str) -> None:
        """Send a reaction to a specific message (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_reaction_internal, number, text, message_id
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
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Reaction: {text}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text_content

                raise Exception(f"Failed to send reaction: {text_content}")

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
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to set webhook: {text}")

    async def send_list(
        self,
        number: str,
        title: str,
        text: str,
        button_text: str,
        sections: list[dict],
    ) -> None:
        """Send a list message (interactive menu)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_list_internal, number, title, text, button_text, sections
        )

    async def _send_list_internal(
        self,
        number: str,
        title: str,
        text: str,
        button_text: str,
        sections: list[dict],
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
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                resp_text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"List: {title}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = resp_text
                raise Exception(f"Failed to send list: {resp_text}")

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
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_contact_internal, number, contact_name, contact_number
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
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                resp_text = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Contact: {contact_name}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = resp_text
                raise Exception(f"Failed to send contact: {resp_text}")

            self.stats["sent"] += 1
            self.stats["last_sent_message"] = f"Contact: {contact_name}"
            self.stats["last_sent_target"] = number

    async def set_presence(self, number: str, presence: str) -> None:
        """Set presence (available, composing, recording, paused)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        url = f"{self.host}/set_presence"
        payload = {"number": number, "presence": presence}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
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
        """Send a message with buttons (with retry)."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        await self._send_with_retry(
            self._send_buttons_internal, number, text, buttons, footer
        )

    async def _send_buttons_internal(
        self,
        number: str,
        text: str,
        buttons: list[dict[str, str]],
        footer: str | None = None,
    ) -> None:
        """Internal send buttons logic."""
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
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                self.stats["failed"] += 1
                self.stats["last_failed_message"] = f"Buttons: {text}"
                self.stats["last_failed_target"] = number
                self.stats["last_error_reason"] = text_content
                raise Exception(f"Failed to send buttons: {text_content}")

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
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 401:
                        raise Exception("Invalid API Key")
                    if resp.status == 200:
                        data = await resp.json()
                        return list(data)
                    _LOGGER.warning("Groups endpoint returned status %s", resp.status)
                    return []
            except Exception as e:
                if "Invalid API Key" in str(e):
                    raise
                _LOGGER.error("Error fetching groups from addon: %s", e)
                return []

    async def mark_as_read(self, number: str, message_id: str) -> None:
        """Mark a message as read."""
        if not self.is_allowed(number):
            return
        number = self.ensure_jid(number)
        url = f"{self.host}/mark_as_read"
        payload = {"number": number, "messageId": message_id}
        headers = {"X-Auth-Token": self.api_key} if self.api_key else {}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            if resp.status == 401:
                raise Exception("Invalid API Key")
            if resp.status != 200:
                text_content = await resp.text()
                raise Exception(f"Failed to mark message as read: {text_content}")
