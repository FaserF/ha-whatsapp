"""DataUpdateCoordinator for HA WhatsApp."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhatsAppApiClient
from .const import DOMAIN, CONF_POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WhatsAppDataUpdateCoordinator(DataUpdateCoordinator):
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
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self) -> dict:
        """Update data via library."""
        try:
            connected = await self.client.connect()

            # If we were disconnected and now we are connected, dismiss notification
            if connected:
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": f"{DOMAIN}_connection_lost"},
                )

            return {
                "connected": connected,
                "stats": self.client.stats.copy(),
            }
        except Exception as err:
            # Create persistent notification on connection loss
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Connection Lost",
                    "message": f"Integration lost connection to the WhatsApp Addon: {err}",
                    "notification_id": f"{DOMAIN}_connection_lost",
                },
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
