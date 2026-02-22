"""DataUpdateCoordinator for HA WhatsApp.

This module defines :class:`WhatsAppDataUpdateCoordinator`, the central
poll-based coordinator that drives the periodic refresh of integration data
(connection status, statistics) from the WhatsApp addon.

The coordinator is responsible for:

* Checking whether the WhatsApp session is still connected.
* Creating / deleting Home Assistant issues (repairs) based on the session
  and connectivity state.
* Fetching aggregated statistics (messages sent/received/failed, uptime …)
  that are exposed through sensor and binary-sensor entities.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhatsAppApiClient
from .const import CONF_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WhatsAppDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):  # type: ignore[misc]
    """Coordinator that periodically polls the WhatsApp addon for status and stats.

    Inherits from
    :class:`homeassistant.helpers.update_coordinator.DataUpdateCoordinator`
    and wraps a :class:`~.api.WhatsAppApiClient`.  All platform entities
    (binary sensor, sensors) subscribe to this coordinator and are updated
    automatically whenever new data is fetched.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the coordinator.

        Args:
            hass: The Home Assistant instance.
            client: A fully initialised :class:`~.api.WhatsAppApiClient`
                that will be used for API communication.
            entry: The config entry this coordinator belongs to.  The
                :attr:`~homeassistant.config_entries.ConfigEntry.options`
                dictionary is queried for ``polling_interval``.
        """
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
        """Fetch fresh data from the WhatsApp addon.

        Calls :meth:`~.api.WhatsAppApiClient.connect` to verify the session
        state and :meth:`~.api.WhatsAppApiClient.get_stats` to retrieve
        message statistics.  Home Assistant *repair issues* are created or
        deleted depending on the outcome:

        * ``session_expired`` – Created when the addon responds but the
          WhatsApp session is no longer authenticated.  Deleted once the
          session comes back.
        * ``connection_failed`` – Created when the addon cannot be reached
          or returns an auth error.  Deleted on a successful round-trip.

        Returns:
            A dict with two keys:
            ``connected`` (bool) – Whether the WhatsApp session is active.
            ``stats`` (dict) – Statistics as returned by
            :meth:`~.api.WhatsAppApiClient.get_stats`.

        Raises:
            UpdateFailed: When a :class:`~homeassistant.exceptions.HomeAssistantError`
                or unexpected exception is raised by the API client.
        """

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
        except HomeAssistantError as err:
            # Create issue for connection failure (Addon unreachable or Auth)
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
        except Exception as err:
            raise UpdateFailed(
                f"Unexpected error communicating with API: {err}"
            ) from err
