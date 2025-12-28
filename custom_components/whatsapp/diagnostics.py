"""Diagnostics support for HA WhatsApp."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import WhatsAppApiClient
from .const import DOMAIN

TO_REDACT = {"session_data", "session"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    client: WhatsAppApiClient = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "client_connected": await client.is_connected(),
    }
