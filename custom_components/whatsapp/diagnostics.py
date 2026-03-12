"""Diagnostics support for HA WhatsApp.

Provides the :func:`async_get_config_entry_diagnostics` hook consumed by
Home Assistant's diagnostics framework, which renders a JSON report visible
under *Settings → Devices & services → WhatsApp → Download diagnostics*.

Sensitive values are redacted before being included in the report so that
the report can be shared safely for debugging.

Attributes redacted:
    * ``api_key`` – The API key used to authenticate with the addon.
    * ``session_data`` – Raw session data that could identify the user.
    * ``session`` – Alternative session-data key.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {"api_key", "session_data", "session"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a WhatsApp config entry.

    Collects and returns a dictionary that includes:

    * ``entry`` – The full config-entry data with sensitive values redacted
      (see :attr:`TO_REDACT`).
    * ``client_connected`` – Boolean indicating whether the WhatsApp addon
      is currently reachable and authenticated.
    * ``stats`` – The latest statistics snapshot from the coordinator
      (message counts, uptime, version …).

    Args:
        hass: The Home Assistant instance.
        entry: The config entry to gather diagnostics for.

    Returns:
        A JSON-serialisable dictionary suitable for the HA diagnostics
        download endpoint.
    """
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "client_connected": coordinator.data.get("connected", False),
        "stats": coordinator.data.get("stats", {}),
    }
