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

from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator
from .helpers import (
    extract_group_chats,
    format_timestamp,
    safe_text,
    sync_moderation_registry_enabled,
)


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
            WhatsAppChatsSensor(coordinator, entry),
            WhatsAppModerationWarningsSensor(coordinator, entry),
            WhatsAppModerationRaidStatusSensor(coordinator, entry),
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
        self._attr_device_info = coordinator.client.get_device_info()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        stats = (self.coordinator.data or {}).get("stats", {})
        if self._stat_key == "sent":
            return {
                "last_message": safe_text(stats.get("last_sent_message")),
                "last_target": safe_text(stats.get("last_sent_target")),
                "last_time": format_timestamp(stats.get("last_sent_time")),
            }
        if self._stat_key == "received":
            return {
                "last_message": safe_text(stats.get("last_received_message")),
                "last_sender": safe_text(stats.get("last_received_sender")),
                "last_time": format_timestamp(stats.get("last_received_time")),
            }
        if self._stat_key == "failed":
            return {
                "last_message": safe_text(stats.get("last_failed_message")),
                "last_target": safe_text(stats.get("last_failed_target")),
                "error_reason": safe_text(stats.get("last_error_reason")),
                "last_time": format_timestamp(stats.get("last_failed_time")),
            }
        return {}

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = (self.coordinator.data or {}).get("stats", {})
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
        self._attr_device_info = coordinator.client.get_device_info()
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = (self.coordinator.data or {}).get("stats", {})
        return int(stats.get("uptime", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        stats = (self.coordinator.data or {}).get("stats", {})
        return {
            "version": safe_text(stats.get("version", "Unknown")),
            "phone_number": safe_text(stats.get("my_number", "Unknown")),
            "connected": stats.get("connected", False),
            "disconnect_reason": safe_text(stats.get("disconnect_reason")),
        }


class WhatsAppChatsSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Sensor that reports the number of available chats and lists all groups."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:forum"
    _attr_translation_key = "chats"

    def __init__(
        self,
        coordinator: WhatsAppDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the chats sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_chats"
        self._attr_device_info = coordinator.client.get_device_info()
        self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> int:
        """Return the total number of chats."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return 0
        chats_data = self.coordinator.data.get("chats", {})
        if isinstance(chats_data, dict):
            return int(chats_data.get("total_chats", 0))
        if isinstance(chats_data, list):
            return len(chats_data)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes (lists all groups)."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return {"groups": []}
        chats_data = self.coordinator.data.get("chats", {})
        return {"groups": safe_text(extract_group_chats(chats_data))}


class WhatsAppModerationWarningsSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Sensor reporting active user warnings across all groups.

    Disabled by default and automatically activated in the entity registry
    as soon as moderation becomes active (globally or for any group).
    It is disabled again when moderation is fully turned off.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "moderation_warnings"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_moderation_warnings"
        self._attr_device_info = coordinator.client.get_device_info()

    def _sync_registry_enabled(self) -> None:
        """Enable or disable this entity in the registry based on moderation state."""
        sync_moderation_registry_enabled(self)

    def _handle_coordinator_update(self) -> None:
        """React to coordinator data updates; sync registry enabled state first."""
        self._sync_registry_enabled()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> int:
        """Return the total number of active user warnings across groups."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        total = 0
        for group in groups.values():
            user_warns = group.get("warnings", {}).get("user_warns", {})
            for warns in user_warns.values():
                if isinstance(warns, list):
                    total += len(warns)
        return total


class WhatsAppModerationRaidStatusSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Sensor reporting total groups with Anti-Raid shield active.

    Disabled by default and automatically activated in the entity registry
    as soon as moderation becomes active (globally or for any group).
    It is disabled again when moderation is fully turned off.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "moderation_raid_status"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_moderation_raid_status"
        self._attr_device_info = coordinator.client.get_device_info()

    def _sync_registry_enabled(self) -> None:
        """Enable or disable this entity in the registry based on moderation state."""
        sync_moderation_registry_enabled(self)

    def _handle_coordinator_update(self) -> None:
        """React to coordinator data updates; sync registry enabled state first."""
        self._sync_registry_enabled()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> str:
        """Return status string for anti-raid shield."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        active_raid_groups = 0
        for group in groups.values():
            antispam = group.get("antispam", {})
            if antispam.get("anti_raid", {}).get("enabled"):
                active_raid_groups += 1
        return f"{active_raid_groups} Active Shield(s)"
