"""Binary sensor platform for HA WhatsApp.

Provides a single binary sensor entity – :class:`WhatsAppConnectionSensor` –
that represents the current WhatsApp session connectivity state.

The sensor state is ``on`` (connected) or ``off`` (disconnected) and is
updated by the :class:`~.coordinator.WhatsAppDataUpdateCoordinator` polling
loop.  Additional diagnostic attributes (version, phone number, message
counts) are exposed via :attr:``extra_state_attributes``.
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
from .helpers import (
    safe_text,
    sync_moderation_registry_enabled,
    sync_telegram_bridge_registry_enabled,
)


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
    async_add_entities(
        [
            WhatsAppConnectionSensor(coordinator, entry),
            WhatsAppModerationStatusBinarySensor(coordinator, entry),
            WhatsAppTelegramBridgeStatusBinarySensor(coordinator, entry),
        ]
    )


class WhatsAppConnectionSensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    BinarySensorEntity,  # type: ignore[misc]
):
    """Binary sensor that indicates whether the WhatsApp session is connected."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "connection"

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the binary sensor entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection"
        self._attr_device_info = coordinator.client.get_device_info()

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (connected)."""
        return bool((self.coordinator.data or {}).get("connected", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        data = self.coordinator.data or {}
        stats = data.get("stats", {})
        dashboard = data.get("dashboard", {})
        return {
            "version": safe_text(stats.get("version", "Unknown")),
            "phone_number": safe_text(stats.get("my_number", "Unknown")),
            "addon_status": safe_text(data.get("status")),
            "addon_status_details": safe_text(data.get("status_details")),
            "passkey_required": (
                bool(dashboard.get("passkeyDetected", False))
                if isinstance(dashboard, dict)
                else False
            ),
            "last_update": stats.get("start_time"),
            "uptime_seconds": stats.get("uptime", 0),
            "total_sent": stats.get("sent", 0),
            "total_received": stats.get("received", 0),
            "total_failed": stats.get("failed", 0),
            "last_message_sent": safe_text(stats.get("last_sent_message")),
            "last_message_target": safe_text(stats.get("last_sent_target")),
            "status_description": (
                f"Connected ({safe_text(stats.get('my_number', 'Unknown'))})"
                if self.is_on
                else (
                    f"Disconnected ({safe_text(data.get('status_details', 'Offline'))})"
                )
            ),
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True


class WhatsAppModerationStatusBinarySensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    BinarySensorEntity,  # type: ignore[misc]
):
    """Binary sensor indicating global WhatsApp moderation engine status.

    Disabled by default and automatically activated in the entity registry
    as soon as moderation becomes active (globally or for any group).
    It is disabled again when moderation is fully turned off.
    """

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_has_entity_name = True
    _attr_translation_key = "moderation_status"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the moderation status binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_moderation_status"
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
    def is_on(self) -> bool:
        """Return true if global moderation is enabled."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        return bool(mod.get("global_enabled", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed, user-friendly moderation attributes."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        federations = mod.get("federations", [])

        # Build list of managed group names / IDs for clarity
        managed_group_list: list[str] = []
        for gid, gdata in groups.items():
            name = gdata.get("name") or gdata.get("subject") or gid
            managed_group_list.append(str(name))

        return {
            "global_enabled": mod.get("global_enabled", False),
            "managed_groups_count": len(groups),
            "managed_groups": managed_group_list,
            "federations_count": len(federations),
            "status_description": (
                (
                    f"Globally active with {len(groups)} managed group(s)"
                    f" and {len(federations)} federation(s)"
                )
                if mod.get("global_enabled")
                else "Globally disabled"
            ),
        }


class WhatsAppTelegramBridgeStatusBinarySensor(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    BinarySensorEntity,  # type: ignore[misc]
):
    """Binary sensor indicating global Telegram Bridge engine status.

    Disabled by default in entity registry. Automatically enabled as soon as
    a Telegram bot token is configured and at least one mapping is active.
    Disabled again automatically when no active mappings remain.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_translation_key = "telegram_bridge_status"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the Telegram bridge status binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_telegram_bridge_status"
        self._attr_device_info = coordinator.client.get_device_info()

    async def async_added_to_hass(self) -> None:
        """React to entity added to hass; sync registry enabled state first."""
        await super().async_added_to_hass()
        self._sync_registry_enabled()

    def _sync_registry_enabled(self) -> None:
        """Enable or disable this entity in the registry based on bridge state."""
        sync_telegram_bridge_registry_enabled(self)

    def _handle_coordinator_update(self) -> None:
        """React to coordinator data updates; sync registry enabled state first."""
        self._sync_registry_enabled()
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        """Return true if Telegram bridge is enabled and bot is connected."""
        data = self.coordinator.data or {}
        tg = data.get("telegram", {})
        return bool(tg.get("enabled", False) and tg.get("bot_token"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return Telegram bridge attributes."""
        data = self.coordinator.data or {}
        tg = data.get("telegram", {})
        mappings = tg.get("mappings", [])
        active_mappings = [m for m in mappings if m.get("enabled")]
        active_count = len(active_mappings)
        bot_username = tg.get("bot_username", "")
        return {
            "enabled": tg.get("enabled", False),
            "bot_username": bot_username,
            "mappings_count": len(mappings),
            "active_mappings_count": active_count,
            "status_description": (
                f"Active with bot @{bot_username} ({active_count} active forwarder(s))"
                if self.is_on and bot_username
                else "Inactive or no bot configured"
            ),
        }
