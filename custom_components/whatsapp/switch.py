"""Switch platform for HA WhatsApp integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up WhatsApp switch entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]

    async_add_entities(
        [
            WhatsAppModerationMasterSwitch(coordinator, entry),
            WhatsAppTelegramBridgeMasterSwitch(coordinator, entry),
            WhatsAppAutoResponderSwitch(coordinator, entry),
        ]
    )


class WhatsAppModerationMasterSwitch(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch entity to control global WhatsApp Moderation Engine state."""

    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True
    _attr_icon = "mdi:shield-check"
    _attr_translation_key = "moderation_master"

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the moderation master switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_switch_moderation_master"
        self._attr_device_info = coordinator.client.get_device_info()

    @property
    def is_on(self) -> bool:
        """Return true if the moderation engine is globally enabled."""
        data = self.coordinator.data or {}
        return bool(data.get("moderation", {}).get("global_enabled", False))

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the moderation engine globally."""
        await self.coordinator.client.set_global_moderation_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the moderation engine globally."""
        await self.coordinator.client.set_global_moderation_enabled(False)
        await self.coordinator.async_request_refresh()


class WhatsAppTelegramBridgeMasterSwitch(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch entity to control global WhatsApp-Telegram Bridge state."""

    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True
    _attr_icon = "mdi:bridge"
    _attr_translation_key = "telegram_bridge_master"

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the Telegram bridge master switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_switch_telegram_bridge_master"
        self._attr_device_info = coordinator.client.get_device_info()

    @property
    def is_on(self) -> bool:
        """Return true if the Telegram bridge is globally enabled."""
        data = self.coordinator.data or {}
        return bool(data.get("telegram", {}).get("enabled", False))

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the Telegram bridge globally."""
        await self.coordinator.client.set_telegram_bridge_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the Telegram bridge globally."""
        await self.coordinator.client.set_telegram_bridge_enabled(False)
        await self.coordinator.async_request_refresh()


class WhatsAppAutoResponderSwitch(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch entity to control WhatsApp Auto Responder (Away / Vacation) state."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:message-reply-text"
    _attr_translation_key = "auto_responder"

    def __init__(
        self, coordinator: WhatsAppDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the Auto Responder switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_switch_auto_responder"
        self._attr_device_info = coordinator.client.get_device_info()

    @property
    def is_on(self) -> bool:
        """Return true if the auto responder is enabled."""
        data = self.coordinator.data or {}
        return bool(data.get("autoresponder", {}).get("enabled", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return dynamic metadata attributes about the active responder."""
        data = self.coordinator.data or {}
        ar = data.get("autoresponder", {})
        return {
            "is_active": bool(ar.get("is_active", False)),
            "start_time": ar.get("start_time"),
            "end_time": ar.get("end_time"),
            "direct_only": bool(ar.get("direct_only", True)),
            "once_per_contact": bool(ar.get("once_per_contact", True)),
            "seen_count": int(ar.get("seen_count", 0)),
        }

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the Auto Responder."""
        await self.coordinator.client.set_auto_responder_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the Auto Responder."""
        await self.coordinator.client.set_auto_responder_enabled(False)
        await self.coordinator.async_request_refresh()
