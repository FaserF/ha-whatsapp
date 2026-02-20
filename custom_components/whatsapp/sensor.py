"""Sensor platform for HA WhatsApp.

Provides the following sensor entities, all backed by the shared
:class:`~.coordinator.WhatsAppDataUpdateCoordinator`:

* :class:`WhatsAppStatSensor` – One entity per statistic key (``sent``,
  ``received``, ``failed``).  Each reports a running integer count and
  exposes detailed attributes such as the last message, target and
  timestamp.
* :class:`WhatsAppUptimeSensor` – Reports the addon's uptime in seconds.
  Exposed as a diagnostic entity in the ``duration`` device class so that
  Home Assistant can convert the value to a human-readable duration.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    """Set up WhatsApp sensor entities from a config entry.

    Creates four sensor entities:

    * ``sent`` – Number of messages successfully sent.
    * ``received`` – Number of messages received.
    * ``failed`` – Number of failed send attempts.
    * ``uptime`` – Addon uptime in seconds.

    Args:
        hass: The Home Assistant instance.
        entry: Config entry used to retrieve the coordinator from
            ``hass.data``.
        async_add_entities: Callback to register the new entities.
    """
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
    """Integer counter sensor for a single WhatsApp message statistic.

    One instance is created for each of the three statistic keys:
    ``sent``, ``received``, and ``failed``.

    The :attr:`native_value` is the raw integer count.  Additional context
    (last message content, target / sender, and timestamp) is exposed
    through :attr:`extra_state_attributes`.
    """

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
        stat_key: str,
    ) -> None:
        """Initialise the sensor.

        Args:
            coordinator: Shared data coordinator for this config entry.
            entry: Config entry providing device-info identifiers.
            stat_key: One of ``"sent"``, ``"received"``, or ``"failed"``.
                Determines which statistic this sensor will report.
        """
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
    """Sensor that reports the WhatsApp addon's uptime in seconds.

    Uses ``SensorDeviceClass.DURATION`` (``_attr_device_class = "duration"``)
    with ``seconds`` as the unit of measurement, enabling Home Assistant to
    display the value in a human-readable format (e.g. ``3 h 22 min``).

    This entity is classified as a :attr:`EntityCategory.DIAGNOSTIC` sensor
    so it is hidden from the default Lovelace entities card but still
    accessible through the device page.
    """

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the uptime sensor.

        Args:
            coordinator: Shared data coordinator for this config entry.
            entry: Config entry providing device-info identifiers.
        """
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
