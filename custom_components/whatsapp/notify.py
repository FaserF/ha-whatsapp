"""Notify platform for WhatsApp."""

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
from .const import DOMAIN
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
    """Implement the notification entity for WhatsApp."""

    _attr_name = None
    _attr_has_entity_name = True
    _attr_unique_id = "whatsapp_notify"

    def __init__(
        self,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
        coordinator: WhatsAppDataUpdateCoordinator,
    ) -> None:
        """Initialize the entity."""
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

    async def async_send_message(
        self, message: str, _title: str | None = None, **kwargs: Any
    ) -> None:
        """Send a message."""
        data = kwargs.get(ATTR_DATA) or {}
        # Support target as kwarg OR inside data
        # (if schema allows, though HA core might reject it in data)
        target_list = kwargs.get(ATTR_TARGET) or data.get(ATTR_TARGET)

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
            elif "buttons" in data:
                # Send buttons: data: { buttons: [...], footer: "..." }
                buttons = data.get("buttons", [])
                footer = data.get("footer")
                await self.client.send_buttons(target, message, buttons, footer)
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
            else:
                # Default text message
                await self.client.send_message(target, message)


class WhatsAppNotificationService(BaseNotificationService):  # type: ignore[misc]
    """Implement the legacy notification service for WhatsApp."""

    def __init__(self, client: WhatsAppApiClient) -> None:
        """Initialize the service."""
        self.client = client

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message."""
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
                elif "image" in data:
                    await self.client.send_image(target, data["image"], message)
                else:
                    await self.client.send_message(target, message)
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
