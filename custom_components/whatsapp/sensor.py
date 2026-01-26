"""Sensor platform for WhatsApp."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
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
    """Set up WhatsApp sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            WhatsAppStatSensor(coordinator, entry, "sent"),
            WhatsAppStatSensor(coordinator, entry, "received"),
            WhatsAppStatSensor(coordinator, entry, "failed"),
            WhatsAppUptimeSensor(coordinator, entry),
            WhatsAppVersionSensor(coordinator, entry),
            WhatsAppPhoneNumberSensor(coordinator, entry),
        ]
    )


class WhatsAppStatSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], SensorEntity  # type: ignore[misc]
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
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return int(stats.get(self._stat_key, 0))


class WhatsAppUptimeSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], SensorEntity  # type: ignore[misc]
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

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return int(stats.get("uptime", 0))


class WhatsAppVersionSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], SensorEntity  # type: ignore[misc]
):
    """Representation of the WhatsApp version sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_translation_key = "version"
        self._attr_unique_id = f"{entry.entry_id}_version"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return str(stats.get("version", "Unknown"))


class WhatsAppPhoneNumberSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator], SensorEntity  # type: ignore[misc]
):
    """Representation of the WhatsApp phone number sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_translation_key = "phone_number"
        self._attr_unique_id = f"{entry.entry_id}_phone_number"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        stats = self.coordinator.data.get("stats", {})
        return str(stats.get("my_number", "Unknown"))
