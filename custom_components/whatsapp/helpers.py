"""Helper utilities for HA WhatsApp integration."""

from __future__ import annotations

import logging
from typing import Any, TypeVar, cast

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.helpers.entity_registry import RegistryEntryDisabler
except ImportError:

    class RegistryEntryDisabler:  # type: ignore[no-redef]
        INTEGRATION = "integration"
        USER = "user"
        DEVICE = "device"


from homeassistant.helpers.entity_registry import (  # noqa: E402
    async_get as async_get_entity_registry,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # noqa: E402
from homeassistant.util import dt as dt_util  # noqa: E402

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


def _sync_entity_registry_enabled(
    entity: CoordinatorEntity[Any], is_active: bool
) -> None:
    """Enable or disable an entity in the registry based on its active condition."""
    if entity.hass is None or entity.registry_entry is None:
        return
    if entity.registry_entry.disabled != (not is_active):
        er = async_get_entity_registry(entity.hass)
        er.async_update_entity(
            entity.entity_id,
            disabled_by=None if is_active else RegistryEntryDisabler.INTEGRATION,
        )


def sync_moderation_registry_enabled(entity: CoordinatorEntity[Any]) -> None:
    """Enable or disable moderation entity in registry based on moderation state."""
    _sync_entity_registry_enabled(entity, is_moderation_active(entity.coordinator.data))


def is_telegram_bridge_active(coordinator_data: dict[str, object] | None) -> bool:
    """Return True if Telegram bridge is configured with at least one enabled mapping.

    The entity is considered active when:
    * A ``bot_token`` is set, **and**
    * At least one mapping has ``enabled: true``.
    """
    if not coordinator_data:
        return False
    tg: dict[str, object] = coordinator_data.get("telegram", {})  # type: ignore[assignment]
    if not tg.get("bot_token") and not tg.get("enabled"):
        return False
    mappings: list[object] = tg.get("mappings", [])  # type: ignore[assignment]
    return any(isinstance(m, dict) and m.get("enabled") for m in mappings)


def sync_telegram_bridge_registry_enabled(entity: CoordinatorEntity[Any]) -> None:
    """Enable or disable Telegram bridge entity in registry based on bridge state."""
    _sync_entity_registry_enabled(
        entity, is_telegram_bridge_active(entity.coordinator.data)
    )


def async_sync_entities_by_unique_ids(
    hass: Any,
    unique_ids: list[str],
    is_active: bool,
    domains: tuple[str, ...] = ("sensor", "binary_sensor"),
) -> None:
    """Sync multiple entity enabled states in entity registry for given unique IDs."""
    if hass is None:
        return
    from .const import DOMAIN

    try:
        er = async_get_entity_registry(hass)
        for unique_id in unique_ids:
            entity_id = None
            for domain in domains:
                entity_id = er.async_get_entity_id(domain, DOMAIN, unique_id)
                if entity_id:
                    break
            if entity_id:
                entry = er.async_get(entity_id)
                if entry:
                    if (
                        is_active
                        and entry.disabled_by == RegistryEntryDisabler.INTEGRATION
                    ):
                        er.async_update_entity(entity_id, disabled_by=None)
                    elif not is_active and entry.disabled_by is None:
                        er.async_update_entity(
                            entity_id, disabled_by=RegistryEntryDisabler.INTEGRATION
                        )
    except Exception as exc:
        _LOGGER.debug("Entity registry sync skipped: %s", exc)


def async_sync_moderation_entities(
    hass: Any, entry_id: str, coordinator_data: dict[str, Any] | None
) -> None:
    """Sync moderation entity enabled states in entity registry."""
    async_sync_entities_by_unique_ids(
        hass,
        [
            f"{entry_id}_moderation_warnings",
            f"{entry_id}_moderation_raid_status",
            f"{entry_id}_moderation_status",
        ],
        is_moderation_active(coordinator_data),
    )


def async_sync_telegram_bridge_entities(
    hass: Any, entry_id: str, coordinator_data: dict[str, Any] | None
) -> None:
    """Sync Telegram bridge entity enabled state in entity registry."""
    async_sync_entities_by_unique_ids(
        hass,
        [f"{entry_id}_telegram_bridge_status"],
        is_telegram_bridge_active(coordinator_data),
        domains=("binary_sensor",),
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


def normalize_media_url(url: str, ha_base_url: str | None = None) -> str:
    """Prepend HA base URL to relative URLs starting with '/'."""
    if not url or url.startswith("//"):
        return url
    # /config/www/ is the filesystem path; HA serves it at /local/
    if url.startswith("/config/www/"):
        url = "/local/" + url[len("/config/www/") :]
    if url.startswith("/") and ha_base_url:
        return f"{ha_base_url.rstrip('/')}{url}"
    return url
