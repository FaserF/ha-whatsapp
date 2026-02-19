"""Binary sensor platform for HA WhatsApp.

Provides a single binary sensor entity – :class:`WhatsAppConnectionSensor` –
that represents the current WhatsApp session connectivity state.

The sensor state is ``on`` (connected) or ``off`` (disconnected) and is
updated by the :class:`~.coordinator.WhatsAppDataUpdateCoordinator` polling
loop.  Additional diagnostic attributes (version, phone number, message
counts) are exposed via :attrs:``extra_state_attributes``.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatsApp binary sensor platform from a config entry.

    Creates a single :class:`WhatsAppConnectionSensor` entity backed by
    the coordinator that was set up by the integration's main
    :func:`~.async_setup_entry` function.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry whose data is used to locate the already-
            created coordinator in ``hass.data``.
        async_add_entities: Callback to register new entities with HA.
    """
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]
    async_add_entities([WhatsAppConnectionSensor(coordinator, entry)])


class WhatsAppConnectionSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], BinarySensorEntity  # type: ignore[misc]
):
    """Binary sensor that indicates whether the WhatsApp session is connected.

    Device class: :attr:`~homeassistant.components.binary_sensor.BinarySensorDeviceClass.CONNECTIVITY`.

    State:
        ``on``:  The WhatsApp session is active and authenticated.
        ``off``: The session has been disconnected or the addon is unreachable.

    Extra state attributes:
        * ``version`` – Addon version string.
        * ``phone_number`` – Registered WhatsApp phone number.
        * ``uptime_seconds`` – Addon uptime in seconds.
        * ``total_sent`` – Total messages sent since last restart.
        * ``total_received`` – Total messages received since last restart.
        * ``total_failed`` – Total failed send attempts since last restart.
        * ``last_message_sent`` – Content of the last successfully sent message.
        * ``last_message_target`` – Recipient of the last sent message.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the binary sensor entity.

        Args:
            coordinator: The data coordinator for this config entry.
            entry: Config entry used to derive the unique entity ID and
                device-info identifiers.
        """
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
            "manufacturer": "HA WhatsApp",
            "model": "API Client",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (connected)."""
        return bool(self.coordinator.data.get("connected", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        stats = self.coordinator.data.get("stats", {})
        return {
            "version": stats.get("version", "Unknown"),
            "phone_number": stats.get("my_number", "Unknown"),
            "uptime_seconds": stats.get("uptime", 0),
            "total_sent": stats.get("sent", 0),
            "total_received": stats.get("received", 0),
            "total_failed": stats.get("failed", 0),
            "last_message_sent": stats.get("last_sent_message"),
            "last_message_target": stats.get("last_sent_target"),
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True
