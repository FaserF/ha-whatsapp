"""Notify platform for WhatsApp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WhatsAppApiClient
from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhatsApp notify entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: WhatsAppApiClient = data["client"]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]
    async_add_entities([WhatsAppNotificationEntity(client, entry, coordinator)])


class WhatsAppNotificationEntity(NotifyEntity):  # type: ignore[misc]
    """Implement the notification entity for WhatsApp."""

    _attr_name = "WhatsApp"
    _attr_has_entity_name = True
    _attr_unique_id = "whatsapp_notify"

    def __init__(
        self,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
        coordinator: WhatsAppDataUpdateCoordinator,
    ) -> None:
        """Initialize the entity."""
        self.client = client
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_notify"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(self.coordinator.data.get("connected", False))

    async def async_send_message(
        self, message: str, _title: str | None = None, **kwargs: Any
    ) -> None:
        """Send a message."""
        targets = kwargs.get("target")
        if not targets:
            raise HomeAssistantError("Target number is required provided via 'target'")

        if not isinstance(targets, list):
            targets = [targets]

        data = kwargs.get("data") or {}

        for target in targets:
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
