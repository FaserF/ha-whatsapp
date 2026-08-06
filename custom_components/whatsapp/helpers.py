"""Helper utilities for HA WhatsApp integration."""

from __future__ import annotations

from typing import Any, TypeVar, cast

from homeassistant.helpers.entity_registry import (
    RegistryEntryDisabler,
)
from homeassistant.helpers.entity_registry import (
    async_get as async_get_entity_registry,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

T = TypeVar("T")


def safe_text(value: T) -> T:  # noqa: UP047
    """Safely sanitize text values by replacing invalid Unicode surrogates.

    Prevents Home Assistant WebSocket serialization errors when entity state
    attributes contain invalid Unicode surrogate pairs.
    """
    if isinstance(value, str):
        return cast(
            T, value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        )
    if isinstance(value, dict):
        return cast(T, {safe_text(k): safe_text(v) for k, v in value.items()})
    if isinstance(value, list):
        return cast(T, [safe_text(v) for v in value])
    return value


def is_moderation_active(coordinator_data: dict[str, object] | None) -> bool:
    """Return True if moderation is globally or group-level active.

    Used by all moderation entities to decide whether they should be
    enabled in the entity registry.  Moderation is considered active when:

    * ``global_enabled`` is ``True`` in the moderation config, **or**
    * At least one group has ``enabled: true`` in its per-group config.
    """
    if not coordinator_data:
        return False
    mod: dict[str, object] = coordinator_data.get("moderation", {})  # type: ignore[assignment]
    if mod.get("global_enabled"):
        return True
    groups: dict[str, object] = mod.get("groups", {})  # type: ignore[assignment]
    return any(isinstance(cfg, dict) and cfg.get("enabled") for cfg in groups.values())


def sync_moderation_registry_enabled(entity: CoordinatorEntity[Any]) -> None:
    """Enable or disable moderation entity in registry based on moderation state."""
    if entity.hass is None or entity.registry_entry is None:
        return
    active = is_moderation_active(entity.coordinator.data)
    if entity.registry_entry.disabled != (not active):
        er = async_get_entity_registry(entity.hass)
        er.async_update_entity(
            entity.entity_id,
            disabled_by=None if active else RegistryEntryDisabler.INTEGRATION,
        )


def format_timestamp(timestamp: int | None) -> str | None:
    """Format a millisecond Unix timestamp into a readable ISO local string."""
    if timestamp is None:
        return None
    return str(
        dt_util.as_local(dt_util.utc_from_timestamp(timestamp / 1000)).isoformat()
    )


def extract_group_chats(chats_data: Any) -> list[dict[str, Any]]:
    """Extract group chats (JIDs containing @g.us) safely from chats payload."""
    if isinstance(chats_data, dict):
        groups = chats_data.get("groups", [])
        if isinstance(groups, list):
            return [g for g in groups if isinstance(g, dict)]
        return []
    if isinstance(chats_data, list):
        return [
            c for c in chats_data if isinstance(c, dict) and "@g.us" in c.get("jid", "")
        ]
    return []
