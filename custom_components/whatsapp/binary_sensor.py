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
from .helpers import safe_text, sync_moderation_registry_enabled


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
        """Return moderation attributes."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        return {
            "global_enabled": mod.get("global_enabled", False),
            "managed_groups_count": len(groups),
            "federations_count": len(mod.get("federations", [])),
        }
