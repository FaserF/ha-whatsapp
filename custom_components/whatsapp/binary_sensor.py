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

from homeassistant.components.binary_sensor import (  # type: ignore[attr-defined]
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
    format_timestamp,
    safe_text,
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
    async_add_entities([WhatsAppConnectionSensor(coordinator, entry)])


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
        # Build map of JID -> chat name from chats data
        chats_data = data.get("chats", {})
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

        last_target_raw = safe_text(stats.get("last_sent_target"))
        last_target_resolved = (
            chat_names.get(str(last_target_raw), last_target_raw)
            if last_target_raw
            else None
        )

        health = data.get("health", {})
        health_status = str(health.get("status", "")).lower()
        last_reason = str(stats.get("last_disconnect_reason", "")).lower()
        is_shutting_down = bool(stats.get("shutting_down", False))

        connection_state = "connected" if self.is_on else "disconnected"
        if health_status == "updating" or last_reason == "updating":
            connection_state = "updating"
        elif (
            health_status == "shutting_down"
            or last_reason == "shutting_down"
            or is_shutting_down
        ):
            connection_state = "restarting"

        num_str = safe_text(stats.get("my_number", "Unknown"))
        det_str = safe_text(data.get("status_details", "Offline"))
        state_title = connection_state.capitalize()

        return {
            "version": safe_text(stats.get("version", "Unknown")),
            "phone_number": safe_text(stats.get("my_number", "Unknown")),
            "addon_status": safe_text(data.get("status")),
            "addon_status_details": safe_text(data.get("status_details")),
            "connection_state": connection_state,
            "passkey_required": (
                bool(dashboard.get("passkeyDetected", False))
                if isinstance(dashboard, dict)
                else False
            ),
            "last_update": format_timestamp(stats.get("start_time")),
            "uptime_seconds": stats.get("uptime", 0),
            "total_sent": stats.get("sent", 0),
            "total_received": stats.get("received", 0),
            "total_failed": stats.get("failed", 0),
            "last_message_sent": safe_text(stats.get("last_sent_message")),
            "last_message_target": last_target_resolved,
            "status_description": (
                f"{state_title} ({num_str})"
                if self.is_on
                else f"{state_title} ({det_str})"
            ),
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added."""
        return True
