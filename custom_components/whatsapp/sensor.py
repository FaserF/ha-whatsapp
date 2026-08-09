"""Sensor platform for HA WhatsApp.

Provides the following sensor entities, all backed by the shared
:class:`~.coordinator.WhatsAppDataUpdateCoordinator`:

* :class:`WhatsAppStatSensor` – One entity per statistic key (``sent``,
  ``received``, ``failed``).  Each reports a running integer count and
  exposes detailed attributes such as the last message, target and
  timestamp.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
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

    Creates sensor entities:

    * ``sent`` – Number of messages successfully sent.
    * ``received`` – Number of messages received.
    * ``failed`` – Number of failed send attempts.

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
        val = self.native_value
        if self._stat_key == "sent":
            msg = safe_text(stats.get("last_sent_message"))
            target = safe_text(stats.get("last_sent_target"))
            t_str = format_timestamp(stats.get("last_sent_time"))
            return {
                "last_message": msg,
                "last_target": target,
                "last_time": t_str,
                "status_description": (
                    f"{val} sent (Last to {target} at {t_str})"
                    if val > 0 and target
                    else f"{val} sent"
                ),
            }
        if self._stat_key == "received":
            msg = safe_text(stats.get("last_received_message"))
            sender = safe_text(stats.get("last_received_sender"))
            t_str = format_timestamp(stats.get("last_received_time"))
            return {
                "last_message": msg,
                "last_sender": sender,
                "last_time": t_str,
                "status_description": (
                    f"{val} received (Last from {sender} at {t_str})"
                    if val > 0 and sender
                    else f"{val} received"
                ),
            }
        if self._stat_key == "failed":
            msg = safe_text(stats.get("last_failed_message"))
            target = safe_text(stats.get("last_failed_target"))
            reason = safe_text(stats.get("last_error_reason"))
            t_str = format_timestamp(stats.get("last_failed_time"))
            return {
                "last_message": msg,
                "last_target": target,
                "error_reason": reason,
                "last_time": t_str,
                "status_description": (
                    f"{val} failed (Error: {reason})"
                    if val > 0 and reason
                    else "No transmission errors"
                ),
            }
        return {}

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = (self.coordinator.data or {}).get("stats", {})
        return int(stats.get(self._stat_key, 0))


class WhatsAppChatsSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SensorEntity,  # type: ignore[misc]
):
    """Sensor that reports the number of available chats and lists all groups."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:forum"
    _attr_translation_key = "chats"
    _attr_state_class = SensorStateClass.MEASUREMENT

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
        """Return the state attributes (lists all groups and clear description)."""
        if not self.coordinator.data or not isinstance(self.coordinator.data, dict):
            return {
                "groups": [],
                "group_count": 0,
                "status_description": "No data available",
            }
        chats_data = self.coordinator.data.get("chats", {})
        groups = safe_text(extract_group_chats(chats_data))
        total_chats = self.native_value
        group_count = len(groups) if isinstance(groups, list) else 0
        return {
            "groups": groups,
            "group_count": group_count,
            "status_description": (
                f"{total_chats} chat(s) total ({group_count} group(s))"
                if total_chats > 0
                else "No active chats"
            ),
        }


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

    async def async_added_to_hass(self) -> None:
        """React to entity added to hass; sync registry enabled state first."""
        await super().async_added_to_hass()
        self._sync_registry_enabled()

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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed attributes about active group warnings."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        warned_users_count = 0
        warned_groups: list[str] = []

        for gid, group in groups.items():
            user_warns = group.get("warnings", {}).get("user_warns", {})
            group_has_warns = False
            for _uid, warns in user_warns.items():
                if isinstance(warns, list) and len(warns) > 0:
                    warned_users_count += 1
                    group_has_warns = True
            if group_has_warns:
                name = group.get("name") or group.get("subject") or gid
                warned_groups.append(str(name))

        return {
            "total_active_warnings": self.native_value,
            "warned_users_count": warned_users_count,
            "groups_with_warnings": warned_groups,
            "status_description": (
                (
                    f"{self.native_value} warning(s)"
                    f" for {warned_users_count} user(s)"
                    f" in {len(warned_groups)} group(s)"
                )
                if self.native_value > 0
                else "No active warnings"
            ),
        }


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
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_moderation_raid_status"
        self._attr_device_info = coordinator.client.get_device_info()

    async def async_added_to_hass(self) -> None:
        """React to entity added to hass; sync registry enabled state first."""
        await super().async_added_to_hass()
        self._sync_registry_enabled()

    def _sync_registry_enabled(self) -> None:
        """Enable or disable this entity in the registry based on moderation state."""
        sync_moderation_registry_enabled(self)

    def _handle_coordinator_update(self) -> None:
        """React to coordinator data updates; sync registry enabled state first."""
        self._sync_registry_enabled()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> int:
        """Return the number of groups with active Anti-Raid shield."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        active_raid_groups = 0
        for group in groups.values():
            antispam = group.get("antispam", {})
            if antispam.get("anti_raid", {}).get("enabled"):
                active_raid_groups += 1
        return active_raid_groups

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed Anti-Raid shield status attributes."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        active_groups: list[str] = []
        for gid, group in groups.items():
            antispam = group.get("antispam", {})
            if antispam.get("anti_raid", {}).get("enabled"):
                name = group.get("name") or group.get("subject") or gid
                active_groups.append(str(name))
        return {
            "active_shield_count": len(active_groups),
            "protected_groups": active_groups,
            "status_description": (
                f"Active in {len(active_groups)} group(s)"
                if active_groups
                else "Not active in any group"
            ),
        }
