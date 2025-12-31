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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhatsApp notify entity."""
    client: WhatsAppApiClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WhatsAppNotificationEntity(client)])


class WhatsAppNotificationEntity(NotifyEntity):  # type: ignore[misc]
    """Implement the notification entity for WhatsApp."""

    _attr_name = "WhatsApp"
    _attr_has_entity_name = True
    _attr_unique_id = "whatsapp_notify"

    def __init__(self, client: WhatsAppApiClient) -> None:
        """Initialize the entity."""
        self.client = client

    async def async_send_message(
        self, message: str, _title: str | None = None, **kwargs: Any
    ) -> None:
        """Send a message."""
        targets = kwargs.get("target")
        if not targets:
            raise HomeAssistantError("Target number is required provided via 'target'")

        if not isinstance(targets, list):
            targets = [targets]

        for target in targets:
            await self.client.send_message(target, message)
