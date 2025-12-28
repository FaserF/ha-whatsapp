"""Notify platform for WhatsApp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.notify import BaseNotificationService
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import DiscoveryInfoType

from .api import WhatsAppApiClient
from .const import DOMAIN


async def async_get_service(
    hass: HomeAssistant,
    discovery_info: DiscoveryInfoType | None = None,
) -> WhatsAppNotificationService | None:
    """Get the WhatsApp notification service."""
    if discovery_info is None:
        return None

    entry_id = discovery_info.get("entry_id")
    if not entry_id:
        return None

    client = hass.data[DOMAIN][entry_id]
    return WhatsAppNotificationService(client)


class WhatsAppNotificationService(BaseNotificationService):
    """Implement the notification service for WhatsApp."""

    def __init__(self, client: WhatsAppApiClient) -> None:
        """Initialize the service."""
        self.client = client

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        targets = kwargs.get("target")
        if not targets:
            raise HomeAssistantError("Target number is required")

        if not isinstance(targets, list):
            targets = [targets]

        for target in targets:
            await self.client.send_message(target, message)
