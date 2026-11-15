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
from .helpers import (
    sync_moderation_registry_enabled,
    sync_telegram_bridge_registry_enabled,
)


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
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SwitchEntity,  # type: ignore[misc]
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
        if self.enabled:
            super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        """Return true if the moderation engine is globally enabled."""
        data = self.coordinator.data or {}
        return bool(data.get("moderation", {}).get("global_enabled", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed moderation and anti-raid status attributes."""
        data = self.coordinator.data or {}
        mod = data.get("moderation", {})
        groups = mod.get("groups", {})
        federations = mod.get("federations", [])
        chats_data = data.get("chats", {})

        # Build map of JID -> chat name from chats data
        chat_names: dict[str, str] = {}
        if isinstance(chats_data, dict):
            for c in chats_data.get("groups", []):
                if isinstance(c, dict) and c.get("jid"):
                    chat_names[str(c.get("jid"))] = str(
                        c.get("name") or c.get("subject") or c.get("jid")
                    )
        elif isinstance(chats_data, list):
            for c in chats_data:
                if isinstance(c, dict) and c.get("jid"):
                    chat_names[str(c.get("jid"))] = str(
                        c.get("name") or c.get("subject") or c.get("jid")
                    )

        managed_group_list: list[str] = []
        protected_groups: list[str] = []
        for gid, gdata in groups.items():
            name = (
                gdata.get("name")
                or gdata.get("subject")
                or chat_names.get(str(gid))
                or str(gid)
            )
            managed_group_list.append(str(name))
            antispam = gdata.get("antispam", {})
            if antispam.get("anti_raid", {}).get("enabled"):
                protected_groups.append(str(name))

        active_shields = len(protected_groups)
        return {
            "global_enabled": mod.get("global_enabled", False),
            "managed_groups_count": len(groups),
            "managed_groups": managed_group_list,
            "federations_count": len(federations),
            "active_shield_count": active_shields,
            "protected_groups": protected_groups,
            "status_description": (
                f"Active — {len(groups)} managed group(s), {active_shields} protected with Anti-Raid"
                if self.is_on
                else "Moderation engine disabled"
            ),
        }

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the moderation engine globally."""
        await self.coordinator.client.set_global_moderation_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the moderation engine globally."""
        await self.coordinator.client.set_global_moderation_enabled(False)
        await self.coordinator.async_request_refresh()


class WhatsAppTelegramBridgeMasterSwitch(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SwitchEntity,  # type: ignore[misc]
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
        if self.enabled:
            super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        """Return true if the Telegram bridge is globally enabled."""
        data = self.coordinator.data or {}
        return bool(data.get("telegram", {}).get("enabled", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed Telegram bridge attributes."""
        data = self.coordinator.data or {}
        tg = data.get("telegram", {})
        mappings = tg.get("mappings", [])
        active_mappings = [m for m in mappings if m.get("enabled")]
        active_count = len(active_mappings)
        bot_username = tg.get("bot_username", "")
        has_token = bool(tg.get("bot_token"))

        active_mapping_names: list[str] = []
        for m in active_mappings:
            name = (
                m.get("name")
                or m.get("chat_name")
                or m.get("tg_chat_id")
                or "Unnamed forwarder"
            )
            active_mapping_names.append(str(name))

        return {
            "enabled": tg.get("enabled", False),
            "bot_configured": has_token,
            "bot_username": f"@{bot_username}" if bot_username else "None",
            "mappings_count": len(mappings),
            "active_mappings_count": active_count,
            "active_forwarders": active_mapping_names,
            "status_description": (
                (
                    f"Active with bot @{bot_username} — "
                    f"{active_count} active forwarder(s)"
                )
                if self.is_on and bot_username
                else (
                    "Active (bot configured)"
                    if self.is_on and has_token
                    else "Inactive or no bot configured"
                )
            ),
        }

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on the Telegram bridge globally."""
        await self.coordinator.client.set_telegram_bridge_enabled(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the Telegram bridge globally."""
        await self.coordinator.client.set_telegram_bridge_enabled(False)
        await self.coordinator.async_request_refresh()


class WhatsAppAutoResponderSwitch(
    CoordinatorEntity[WhatsAppDataUpdateCoordinator],  # type: ignore[misc]
    SwitchEntity,  # type: ignore[misc]
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
        """Turn on Auto Responder with start_time set to now and unlimited end_time."""
        from homeassistant.util import dt as dt_util

        now_local = dt_util.now()
        start_time_iso = now_local.strftime("%Y-%m-%dT%H:%M")
        await self.coordinator.client.set_auto_responder_config(
            enabled=True,
            start_time=start_time_iso,
            end_time="",
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off the Auto Responder."""
        await self.coordinator.client.set_auto_responder_enabled(False)
        await self.coordinator.async_request_refresh()
