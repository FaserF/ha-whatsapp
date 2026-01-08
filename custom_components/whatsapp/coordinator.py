"""DataUpdateCoordinator for HA WhatsApp."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhatsAppApiClient
from .const import CONF_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WhatsAppDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):  # type: ignore[misc]
    """Class to manage fetching data from the WhatsApp API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.client = client
        self.entry = entry

        polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 2)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        notification_id = f"{DOMAIN}_connection_lost"
        try:
            connected = await self.client.connect()

            # If we were disconnected and now we are connected, dismiss notification
            if connected:
                persistent_notification.async_dismiss(self.hass, notification_id)

            return {
                "connected": connected,
                "stats": self.client.stats.copy(),
            }
        except Exception as err:
            # Create persistent notification on connection loss
            persistent_notification.async_create(
                self.hass,
                f"Integration lost connection to the WhatsApp Addon: {err}",
                title="WhatsApp Connection Lost",
                notification_id=notification_id,
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
