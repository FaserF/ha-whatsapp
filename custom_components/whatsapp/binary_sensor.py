"""Binary sensor for HA WhatsApp."""

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
    """Set up the WhatsApp binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]
    async_add_entities([WhatsAppConnectionSensor(coordinator, entry)])


class WhatsAppConnectionSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], BinarySensorEntity  # type: ignore[misc]
):
    """Representation of a WhatsApp connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize."""
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
            "messages_sent": stats.get("sent", 0),
            "messages_failed": stats.get("failed", 0),
            "last_message_content": stats.get("last_sent_message"),
            "last_message_target": stats.get("last_sent_target"),
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True
