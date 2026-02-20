"""Notification platform for HA WhatsApp.

This module implements the HA *notify* platform for the WhatsApp
integration.  It registers two complementary notification services:

* :class:`WhatsAppNotificationEntity` – Entity-based notification service
  (the modern HA approach).  Each integration instance registers one
  ``notify`` entity that shows up in the *Notifications* helper.
* :class:`WhatsAppNotificationService` – Legacy
  :class:`~homeassistant.components.notify.BaseNotificationService` kept
  for backwards compatibility with automations that still use
  ``service: notify.whatsapp_<entry_id>``.

Both services support the same message features:

* Sending a plain text message to one or more targets.
* Sending a media file (image, document, video, audio) via the
  ``attachment`` or ``attachments`` keys in ``data``.
* Quoting / replying to an existing message via the ``quote`` or
  ``reply_to`` keys in ``data``.
"""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    BaseNotificationService,
    NotifyEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WhatsAppApiClient
from .const import CONF_RETRY_ATTEMPTS, DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhatsApp notify entity and legacy service."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: WhatsAppApiClient = data["client"]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]

    # 0. Configure client options
    client.retry_attempts = entry.options.get(CONF_RETRY_ATTEMPTS, 2)

    # 1. Add modern NotifyEntity
    async_add_entities([WhatsAppNotificationEntity(client, entry, coordinator)])

    # 2. Register legacy notify service (notify.whatsapp)
    # This provides a service 'notify.whatsapp' for YAML users.
    service = WhatsAppNotificationService(client)

    async def async_notify_service(call: Any) -> None:
        """Handle the legacy notify service call."""
        await service.async_send_message(
            message=call.data.get(ATTR_MESSAGE, ""),
            target=call.data.get(ATTR_TARGET),
            data=call.data.get(ATTR_DATA),
        )

    hass.services.async_register(
        "notify",
        "whatsapp",
        async_notify_service,
        schema=vol.Schema(
            {
                vol.Required(ATTR_MESSAGE): cv.string,
                vol.Optional(ATTR_TARGET): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(ATTR_DATA): dict,
            }
        ),
    )


class WhatsAppNotificationEntity(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    NotifyEntity,  # type: ignore[misc]
):
    """Entity-based notification service for Home Assistant WhatsApp integration.

    This entity is registered by the integration's main
    :func:`~.async_setup_entry` function and allows automations to send
    WhatsApp messages using the modern ``notify`` entity platform.

    Supported ``data`` keys:
        ``attachment`` (str): URL of a single file to attach.
        ``attachments`` (list[str]): URLs of multiple files to attach.
        ``quote`` (str): ID of a message to quote / reply to.
        ``reply_to`` (str): Alias for ``quote``.
    """

    _attr_name = None
    _attr_has_entity_name = True
    _attr_unique_id = "whatsapp_notify"

    def __init__(
        self,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
        coordinator: WhatsAppDataUpdateCoordinator,
    ) -> None:
        """Initialise the notification entity.

        Args:
            client: An initialised :class:`~.api.WhatsAppApiClient`
                for sending messages.
            entry: The config entry this entity belongs to.
            coordinator: Used to check connection state before sending.
        """
        super().__init__(coordinator)
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_notify"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        connected = bool(self.coordinator.data.get("connected", False))
        return "online" if connected else "offline"

    async def async_send_message(  # type: ignore[override]
        self,
        message: str = "",
        target: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a WhatsApp message to one or more targets.

        Accepts an optional ``data`` dict via ``kwargs`` which may contain:

        * ``attachment`` / ``attachments`` – Media URL(s) to attach.
        * ``quote`` / ``reply_to`` – Message ID to quote / reply to.

        Args:
            message: The text body of the message.
            target: List of destination phone numbers or JIDs.  If ``None``,
                the method returns without sending.
            **kwargs: Any additional keyword arguments.  The ``data`` key
                is inspected for attachment and quoting information.
        """
        data = kwargs.get(ATTR_DATA) or {}
        # Support target as kwarg OR inside data
        # (if schema allows, though HA core might reject it in data)
        target_list = target or kwargs.get(ATTR_TARGET) or data.get(ATTR_TARGET)

        if not target_list:
            raise HomeAssistantError(
                "Recipient number is required. Provide it as 'target'."
            )

        if isinstance(target_list, str):
            target_list = [target_list]

        # Ensure we have a list of strings
        recipients: list[str] = list(target_list) if target_list else []

        errors: list[tuple[str, Exception]] = []
        for recipient in recipients:
            try:
                await self._async_send_message_static(
                    self.client, recipient, message, data
                )
            except Exception as err:  # pylint: disable=broad-except
                if len(recipients) == 1:
                    raise
                errors.append((recipient, err))

        if errors:
            raise Exception(
                f"Failed to send WhatsApp message to {len(errors)} recipient(s): "
                f"{', '.join(r for r, _ in errors)}"
            )

    @staticmethod
    async def _async_send_message_static(
        client: WhatsAppApiClient,
        recipient: str,
        message: str,
        data: dict[str, Any],
    ) -> None:
        """Internal static helper to dispatch different message types.

        This is used by both the NotifyEntity and the legacy NotificationService.
        """
        # Common quoted_message_id for text and media
        quoted = data.get("quote") or data.get("reply_to")

        try:
            if "poll" in data:
                # Send poll: data: { poll: { question: "...", options: [...] } }
                poll_data: dict[str, Any] = data["poll"]
                question = poll_data.get("question", message)
                options = poll_data.get("options", [])
                await client.send_poll(
                    recipient, question, options, quoted_message_id=quoted
                )

            elif "location" in data:
                # Send location: data: { location: { lat, lon, name, address } }
                loc: dict[str, Any] = data["location"]
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                if lat is None or lon is None:
                    _LOGGER.error(
                        "Skipping location message to %s: latitude/longitude missing",
                        recipient,
                    )
                    return
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                except (ValueError, TypeError) as err:
                    _LOGGER.error(
                        "Skipping location message to %s: "
                        "invalid coordinates (%s, %s): %s",
                        recipient,
                        lat,
                        lon,
                        err,
                    )
                    return

                await client.send_location(
                    recipient,
                    lat_f,
                    lon_f,
                    loc.get("name"),
                    loc.get("address"),
                    quoted_message_id=quoted,
                )
            elif "reaction" in data:
                # Send reaction: data: { reaction: "...", message_id: "..." }
                react = data["reaction"]
                # If reaction is provided as a simple string, use it
                reaction = react if isinstance(react, str) else react.get("reaction")
                msg_id = (
                    react.get("message_id")
                    if isinstance(react, dict)
                    else data.get("message_id")
                )
                if reaction and msg_id:
                    await client.send_reaction(recipient, reaction, msg_id)
            elif "image" in data:
                # Send image: data: { image: "..." }
                image_url = data["image"]
                await client.send_image(
                    recipient, image_url, message, quoted_message_id=quoted
                )
            elif "buttons" in data or "inline_keyboard" in data:
                # Send buttons: data: { buttons: [...], footer: "..." }
                # OR Telegram-style:
                # data: { inline_keyboard: [[{text: "...", callback_data: "..."}]] }
                buttons: list[dict[str, str]] | None = data.get("buttons")
                if not buttons and "inline_keyboard" in data:
                    # Map Telegram-style to WhatsApp style
                    buttons = []
                    for row in data["inline_keyboard"]:
                        for btn in row:
                            buttons.append(
                                {
                                    "id": btn.get("callback_data", btn.get("url", "")),
                                    "displayText": btn.get("text", ""),
                                }
                            )
                footer = data.get("footer")
                if buttons:
                    await client.send_buttons(
                        recipient, message, buttons, footer, quoted_message_id=quoted
                    )
            elif "document" in data:
                # Send document: data: { document: "http://..." }
                url = data["document"]
                file_name = data.get("file_name")
                await client.send_document(
                    recipient, url, file_name, message, quoted_message_id=quoted
                )
            elif "video" in data:
                # Send video: data: { video: "http://..." }
                url = data["video"]
                await client.send_video(
                    recipient, url, message, quoted_message_id=quoted
                )
            elif "audio" in data:
                # Send audio: data: { audio: "http://..." }
                url = data["audio"]
                ptt = data.get("ptt", False)
                await client.send_audio(recipient, url, ptt, quoted_message_id=quoted)
            else:
                # Default text message
                await client.send_message(recipient, message, quoted_message_id=quoted)
        except Exception as err:
            _LOGGER.error("Error sending WhatsApp message to %s: %s", recipient, err)


class WhatsAppNotificationService(BaseNotificationService):  # type: ignore[misc]
    """Legacy notification service for Home Assistant WhatsApp integration.

    This service is registered by the integration's main
    :func:`~.async_setup_entry` function and allows automations to send
    WhatsApp messages using the legacy ``notify.whatsapp`` service.

    Supported ``data`` keys:
        ``attachment`` (str): URL of a single file to attach.
        ``attachments`` (list[str]): URLs of multiple files to attach.
        ``quote`` (str): ID of a message to quote / reply to.
        ``reply_to`` (str): Alias for ``quote``.
    """

    def __init__(self, client: WhatsAppApiClient) -> None:
        """Initialize the service."""
        self.client = client

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a WhatsApp message via the legacy notify platform.

        Target phone numbers / JIDs are taken from the ``target`` key inside
        ``kwargs``.

        Supports the same ``data`` keys as
        :meth:`WhatsAppNotificationEntity.async_send_message`:
        attachments, ``quote`` / ``reply_to``.

        Args:
            message: The text body of the message.
            **kwargs: Must include a ``target`` list.  The optional ``data``
                dict is inspected for attachment and quoting information.
        """
        targets = kwargs.get(ATTR_TARGET)
        data = kwargs.get(ATTR_DATA) or {}

        if not targets:
            # Check data for target if top-level target is missing
            targets = data.get(ATTR_TARGET)

        if not targets:
            _LOGGER.error("No target provided for WhatsApp notification")
            return

        if not isinstance(targets, list):
            targets = [targets]

        errors: list[tuple[str, Exception]] = []
        for target in targets:
            try:
                await WhatsAppNotificationEntity._async_send_message_static(
                    self.client, target, message, data
                )
            except Exception as err:  # pylint: disable=broad-except
                if len(targets) == 1:
                    raise
                errors.append((target, err))

        if errors:
            raise Exception(
                f"Failed to send WhatsApp message to {len(errors)} recipient(s): "
                f"{', '.join(r for r, _ in errors)}"
            )


async def async_get_service(
    _hass: HomeAssistant,
    _config: ConfigType,
    _discovery_info: DiscoveryInfoType | None = None,
) -> WhatsAppNotificationService | None:
    """Get the WhatsApp notification service (Legacy YAML support)."""
    # This is mainly for legacy/manual setup, but we focus on setup_entry
    return None
