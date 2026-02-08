"""Sensor platform for WhatsApp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WhatsApp sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            WhatsAppStatSensor(coordinator, entry, "sent"),
            WhatsAppStatSensor(coordinator, entry, "received"),
            WhatsAppStatSensor(coordinator, entry, "failed"),
            WhatsAppUptimeSensor(coordinator, entry),
        ]
    )


class WhatsAppStatSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Representation of a WhatsApp statistic sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
        stat_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stat_key = stat_key
        self._attr_translation_key = stat_key
        self._attr_unique_id = f"{entry.entry_id}_{stat_key}"
        self._attr_entity_registry_enabled_default = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        stats = self.coordinator.data.get("stats", {})
        if self._stat_key == "sent":
            return {
                "last_message": stats.get("last_sent_message"),
                "last_target": stats.get("last_sent_target"),
                "last_time": self._format_time(stats.get("last_sent_time")),
            }
        if self._stat_key == "received":
            return {
                "last_message": stats.get("last_received_message"),
                "last_sender": stats.get("last_received_sender"),
                "last_time": self._format_time(stats.get("last_received_time")),
            }
        if self._stat_key == "failed":
            return {
                "last_message": stats.get("last_failed_message"),
                "last_target": stats.get("last_failed_target"),
                "error_reason": stats.get("last_error_reason"),
                "last_time": self._format_time(stats.get("last_failed_time")),
            }
        return {}

    def _format_time(self, timestamp: int | None) -> str | None:
        """Format the timestamp into a readable string."""
        if timestamp is None:
            return None
        return str(
            dt_util.as_local(dt_util.utc_from_timestamp(timestamp / 1000)).isoformat()
        )

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return int(stats.get(self._stat_key, 0))


class WhatsAppUptimeSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Representation of the WhatsApp uptime sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = "duration"
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_translation_key = "uptime"
        self._attr_unique_id = f"{entry.entry_id}_uptime"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return int(stats.get("uptime", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        stats = self.coordinator.data.get("stats", {})
        return {
            "version": stats.get("version", "Unknown"),
            "phone_number": stats.get("my_number", "Unknown"),
        }
