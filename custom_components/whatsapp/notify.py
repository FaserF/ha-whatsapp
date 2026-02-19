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
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], NotifyEntity  # type: ignore[misc]
):  # type: ignore[misc]
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

        if not isinstance(target_list, list):
            target_list = [target_list]

        for target in target_list:
            if "poll" in data:
                # Send poll: data: { poll: { question: "...", options: [...] } }
                poll_data = data["poll"]
                question = poll_data.get("question", message)
                options = poll_data.get("options", [])
                await self.client.send_poll(target, question, options)

            elif "location" in data:
                # Send location: data: { location: { lat, lon, name, address } }
                loc = data["location"]
                await self.client.send_location(
                    target,
                    loc.get("latitude"),
                    loc.get("longitude"),
                    loc.get("name"),
                    loc.get("address"),
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
                    await self.client.send_reaction(target, reaction, msg_id)
            elif "image" in data:
                # Send image: data: { image: "..." }
                image_url = data["image"]
                await self.client.send_image(target, image_url, message)
            elif "buttons" in data or "inline_keyboard" in data:
                # Send buttons: data: { buttons: [...], footer: "..." }
                # OR Telegram-style:
                # data: { inline_keyboard: [[{text: "...", callback_data: "..."}]] }
                buttons = data.get("buttons")
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
                    await self.client.send_buttons(target, message, buttons, footer)
            elif "document" in data:
                # Send document: data: { document: "http://..." }
                url = data["document"]
                file_name = data.get("file_name")
                await self.client.send_document(target, url, file_name, message)
            elif "video" in data:
                # Send video: data: { video: "http://..." }
                url = data["video"]
                await self.client.send_video(target, url, message)
            elif "audio" in data:
                # Send audio: data: { audio: "http://..." }
                url = data["audio"]
                ptt = data.get("ptt", False)
                await self.client.send_audio(target, url, ptt)
            else:
                # Default text message
                quoted = data.get("quote") or data.get("reply_to")
                await self.client.send_message(
                    target, message, quoted_message_id=quoted
                )


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

        for target in targets:
            try:
                if "poll" in data:
                    poll_data = data["poll"]
                    question = poll_data.get("question", message)
                    options = poll_data.get("options", [])
                    await self.client.send_poll(target, question, options)
                elif "location" in data:
                    loc = data["location"]
                    await self.client.send_location(
                        target,
                        loc.get("latitude"),
                        loc.get("longitude"),
                        loc.get("name"),
                        loc.get("address"),
                    )
                elif "reaction" in data:
                    react = data["reaction"]
                    if isinstance(react, str):
                        reaction = react
                    else:
                        reaction = react.get("reaction")
                    msg_id = (
                        react.get("message_id")
                        if isinstance(react, dict)
                        else data.get("message_id")
                    )
                    if reaction and msg_id:
                        await self.client.send_reaction(target, reaction, msg_id)
                elif "image" in data:
                    await self.client.send_image(target, data["image"], message)
                elif "buttons" in data or "inline_keyboard" in data:
                    buttons = data.get("buttons")
                    if not buttons and "inline_keyboard" in data:
                        buttons = []
                        for row in data["inline_keyboard"]:
                            for btn in row:
                                buttons.append(
                                    {
                                        "id": btn.get(
                                            "callback_data", btn.get("url", "")
                                        ),
                                        "displayText": btn.get("text", ""),
                                    }
                                )
                    footer = data.get("footer")
                    if buttons:
                        await self.client.send_buttons(target, message, buttons, footer)
                elif "document" in data:
                    url = data["document"]
                    file_name = data.get("file_name")
                    await self.client.send_document(target, url, file_name, message)
                elif "video" in data:
                    # Send video: data: { video: "http://..." }
                    url = data["video"]
                    await self.client.send_video(target, url, message)
                elif "audio" in data:
                    # Send audio: data: { audio: "http://..." }
                    url = data["audio"]
                    ptt = data.get("ptt", False)
                    await self.client.send_audio(target, url, ptt)
                else:
                    quoted = data.get("quote") or data.get("reply_to")
                    await self.client.send_message(
                        target, message, quoted_message_id=quoted
                    )
            except HomeAssistantError as err:
                raise err
            except Exception as err:
                _LOGGER.error("Error sending WhatsApp message to %s: %s", target, err)


async def async_get_service(
    _hass: HomeAssistant,
    _config: ConfigType,
    _discovery_info: DiscoveryInfoType | None = None,
) -> WhatsAppNotificationService | None:
    """Get the WhatsApp notification service (Legacy YAML support)."""
    # This is mainly for legacy/manual setup, but we focus on setup_entry
    return None
