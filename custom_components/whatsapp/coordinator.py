"""DataUpdateCoordinator for HA WhatsApp."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.helpers import issue_registry as ir

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

        polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 5)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""

        try:
            connected = await self.client.connect()

            # Fix for issue #1: WhatsApp Disconnected
            # (Addon is running, but session is gone)
            if not connected:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "session_expired",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="session_expired",
                    learn_more_url="https://github.com/FaserF/ha-whatsapp/blob/master/docs/installation.md#pairing-with-whatsapp",
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, "session_expired")

            # Always delete connection issue if we successfully reached this point
            ir.async_delete_issue(self.hass, DOMAIN, "connection_failed")

            # Fetch full stats from addon
            stats = await self.client.get_stats()

            return {
                "connected": connected,
                "stats": stats,
            }
        except Exception as err:
            # Create issue for connection failure (Addon unreachable)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "connection_failed",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="connection_failed",
                translation_placeholders={"error": str(err)},
            )
            raise UpdateFailed(f"Error communicating with API: {err}") from err
