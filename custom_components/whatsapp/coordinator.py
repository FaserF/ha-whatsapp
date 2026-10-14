"""DataUpdateCoordinator for HA WhatsApp.

This module defines :class:`WhatsAppDataUpdateCoordinator`, the central
poll-based coordinator that drives the periodic refresh of integration data
(connection status, statistics) from the WhatsApp addon.

The coordinator is responsible for:

* Checking whether the WhatsApp session is still connected.
* Creating / deleting Home Assistant issues (repairs) based on the session
  and connectivity state.
* Fetching aggregated statistics (messages sent/received/failed, uptime …)
  that are exposed through sensor and binary-sensor entities.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

try:
    from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
except ImportError:
    from homeassistant.exceptions import (
        HomeAssistantError,  # type: ignore[attr-defined]
    )

    class ConfigEntryAuthFailed(Exception):  # type: ignore[no-redef] # noqa: N818
        pass


from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WhatsAppApiClient, WhatsAppAuthError
from .const import CONF_POLLING_INTERVAL, DOMAIN
from .helpers import (
    async_sync_moderation_entities,
    async_sync_telegram_bridge_entities,
    is_connection_or_dns_error,
)
from .helpers import (
    safe_text as _safe_text,
)

_LOGGER = logging.getLogger(__name__)


class WhatsAppDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):  # type: ignore[misc]
    """Coordinator that periodically polls the WhatsApp addon for status and stats.

    Inherits from
    :class:`homeassistant.helpers.update_coordinator.DataUpdateCoordinator`
    and wraps a :class:`~.api.WhatsAppApiClient`.  All platform entities
    (binary sensor, sensors) subscribe to this coordinator and are updated
    automatically whenever new data is fetched.
    """

    client: WhatsAppApiClient
    _unreachable_count: int = 0

    def __init__(
        self,
        hass: HomeAssistant,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the coordinator.

        Args:
            hass: The Home Assistant instance.
            client: A fully initialised :class:`~.api.WhatsAppApiClient`
                that will be used for API communication.
            entry: The config entry this coordinator belongs to.  The
                :attr:`~homeassistant.config_entries.ConfigEntry.options`
                dictionary is queried for ``polling_interval``.
        """
        self.client = client
        self.entry = entry
        self._connected: bool = False
        self._unreachable_count: int = 0

        polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 30)
        self._normal_interval: timedelta = timedelta(seconds=polling_interval)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=self._normal_interval,
        )

    def _handle_unreachable(self, err_or_details: Any) -> dict[str, Any]:
        """Handle unreachable addon state gracefully during updates or restarts."""
        previous_data = self.data or {}
        prev_stats = (
            previous_data.get("stats", {}) if isinstance(previous_data, dict) else {}
        )
        prev_health = (
            previous_data.get("health", {}) if isinstance(previous_data, dict) else {}
        )
        last_reason = str(prev_stats.get("last_disconnect_reason", "")).lower()
        health_status = str(prev_health.get("status", "")).lower()

        self._unreachable_count = getattr(self, "_unreachable_count", 0) + 1
        self._connected = False

        # Exponential backoff for coordinator polling interval when unreachable:
        # 5s, 10s, 20s, 40s, 80s, 160s, capped at max 300s
        backoff_sec = min(5 * (2 ** min(self._unreachable_count - 1, 6)), 300)
        self.update_interval = timedelta(seconds=backoff_sec)
        _LOGGER.debug(
            "Addon unreachable (count=%d). Backing off polling interval to %ss: %s",
            self._unreachable_count,
            backoff_sec,
            err_or_details,
        )

        is_shutting_down = (
            bool(prev_stats.get("shutting_down", False))
            or health_status in ("shutting_down", "updating")
            or last_reason in ("shutting_down", "updating")
        )

        # Allow a grace period of up to 4 polling intervals (~2 mins)
        # if the coordinator was previously connected.
        if previous_data and (is_shutting_down or self._unreachable_count <= 4):
            status_str = (
                "updating"
                if (
                    health_status == "updating"
                    or last_reason == "updating"
                    or self._unreachable_count <= 4
                )
                else "shutting_down"
            )
            status_desc = (
                f"Addon is updating/restarting ({self._unreachable_count}/4)..."
                if self._unreachable_count <= 4
                else "Addon is restarting..."
            )
            _LOGGER.info(
                "WhatsApp Addon is %s (%d/4) — maintaining availability (%s)",
                status_str,
                self._unreachable_count,
                err_or_details,
            )
            return _safe_text(
                {
                    "connected": False,
                    "status": status_str,
                    "status_details": status_desc,
                    "health": {"status": status_str},
                    "stats": {
                        "last_disconnect_reason": status_str,
                        "shutting_down": True,
                        "my_number": prev_stats.get("my_number", "Unknown"),
                        "version": prev_stats.get("version", "Unknown"),
                        "sent": prev_stats.get("sent", 0),
                        "received": prev_stats.get("received", 0),
                        "failed": prev_stats.get("failed", 0),
                    },
                    "chats": previous_data.get("chats", {}),
                    "dashboard": previous_data.get("dashboard", {}),
                    "moderation": previous_data.get("moderation", {}),
                    "telegram": previous_data.get("telegram", {}),
                }
            )

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            "connection_failed",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="connection_failed",
            translation_placeholders={"error": str(err_or_details)},
        )
        _LOGGER.debug("Error communicating with WhatsApp API: %s", err_or_details)
        raise UpdateFailed(f"Addon unreachable: {err_or_details}")

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh data from the WhatsApp addon.

        Calls :meth:`~.api.WhatsAppApiClient.connect` to verify the session
        state and :meth:`~.api.WhatsAppApiClient.get_stats` to retrieve
        message statistics.  Home Assistant *repair issues* are created or
        deleted depending on the outcome:

        * ``session_expired`` – Created when the addon responds but the
          WhatsApp session is no longer authenticated.  Deleted once the
          session comes back.
        * ``connection_failed`` – Created when the addon cannot be reached
          or returns an auth error.  Deleted on a successful round-trip.

        Returns:
            A dict with two keys:
            ``connected`` (bool) – Whether the WhatsApp session is active.
            ``stats`` (dict) – Statistics as returned by
            :meth:`~.api.WhatsAppApiClient.get_stats`.

        Raises:
            UpdateFailed: When a :class:`~homeassistant.exceptions.HomeAssistantError`
                or unexpected exception is raised by the API client.
        """

        try:
            # 0. Watchdog: ensure event polling loop is alive
            polling_interval = (
                self.entry.options.get(CONF_POLLING_INTERVAL, 5) if self.entry else 5
            )
            self.client.ensure_polling(interval=polling_interval)

            # 1. Check Addon Health first (Lightweight)
            health = await self.client.get_health()
            status = health.get("status", "unknown")
            details = health.get("details", "")

            # If health check reports unreachable due to transient DNS/connection errors
            # (e.g. boot race or container startup), retry with exponential backoff.
            if status == "unreachable" and is_connection_or_dns_error(details):
                max_health_retries = 4
                retry_delay = 1
                for attempt in range(max_health_retries):
                    wait_time = min(retry_delay * (2**attempt), 16)
                    _LOGGER.info(
                        "WhatsApp gateway not reachable during health check (%s). "
                        "Retrying in %ss (attempt %d/%d)...",
                        details,
                        wait_time,
                        attempt + 1,
                        max_health_retries,
                    )
                    await asyncio.sleep(wait_time)
                    health = await self.client.get_health()
                    status = health.get("status", "unknown")
                    details = health.get("details", "")
                    if status != "unreachable" or not is_connection_or_dns_error(
                        details
                    ):
                        break

            # If addon is unreachable, handle gracefully (e.g. during addon updates)
            if status == "unreachable":
                return self._handle_unreachable(details)

            # If addon is still starting, we report that and skip full stats
            if status == "starting":
                self._connected = False
                return {
                    "connected": False,
                    "status": "starting",
                    "status_details": details,
                    "stats": self.client.stats,
                }

            # 2. Fetch full stats (Requires Auth and fully started service)
            stats = await self.client.get_stats()
            connected = bool(stats.get("connected", False))
            if not connected:
                # Double-check via client's status if get_stats returned connected=False
                try:
                    status_info = await self.client.get_status()
                    if (
                        isinstance(status_info, dict)
                        and status_info.get("connected") is True
                    ):
                        connected = True
                        stats["connected"] = True
                except Exception as status_err:
                    _LOGGER.debug("Status fallback check failed: %s", status_err)

            self._connected = connected

            # 2b. Fetch dashboard for passkey detection (lightweight, best-effort)
            dashboard: dict[str, Any] = {}
            try:
                raw_dash = await self.client.get_dashboard()
                if isinstance(raw_dash, dict):
                    dashboard = raw_dash
            except Exception as dash_err:
                _LOGGER.debug("Dashboard fetch skipped: %s", dash_err)

            moderation: dict[str, Any] = {}
            try:
                mod_res = await self.client.get_moderation_config()
                if isinstance(mod_res, dict) and "data" in mod_res:
                    moderation = mod_res["data"]
            except Exception as mod_err:
                _LOGGER.debug("Moderation fetch skipped: %s", mod_err)

            telegram: dict[str, Any] = {}
            try:
                tg_res = await self.client.get_telegram_config()
                if isinstance(tg_res, dict) and "data" in tg_res:
                    telegram = tg_res["data"]
            except Exception as tg_err:
                _LOGGER.debug("Telegram fetch skipped: %s", tg_err)

            autoresponder: dict[str, Any] = {}
            try:
                ar_res = await self.client.get_auto_responder_config()
                if isinstance(ar_res, dict) and "data" in ar_res:
                    autoresponder = ar_res["data"]
            except Exception as ar_err:
                _LOGGER.debug("Autoresponder fetch skipped: %s", ar_err)

            chats = {"total_chats": 0, "groups": []}
            if connected:
                try:
                    chats = await self.client.get_chats()
                except Exception as chat_err:
                    _LOGGER.debug("Failed to fetch chats: %s", chat_err)

            # Differentiated disconnect handling:
            passkey_detected = dashboard.get("passkeyDetected", False)
            if passkey_detected:
                # Passkey ceremony active — surface a specific, actionable repair issue.
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    "passkey_required",
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="passkey_required",
                    translation_placeholders={
                        "baileys_issue_url": "https://github.com/WhiskeySockets/Baileys/issues/2672"
                    },
                    learn_more_url="https://github.com/WhiskeySockets/Baileys/issues/2672",
                )
                ir.async_delete_issue(self.hass, DOMAIN, "session_expired")
                ir.async_delete_issue(self.hass, DOMAIN, "connection_error_baileys")
            elif not connected:
                ir.async_delete_issue(self.hass, DOMAIN, "passkey_required")
                reason = stats.get("disconnect_reason")
                if reason == "logged_out":
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        "session_expired",
                        is_fixable=False,
                        severity=ir.IssueSeverity.WARNING,
                        translation_key="session_expired",
                        learn_more_url="https://faserf.github.io/ha-whatsapp/setup/",
                    )
                    ir.async_delete_issue(self.hass, DOMAIN, "connection_error_baileys")
                else:
                    ir.async_create_issue(
                        self.hass,
                        DOMAIN,
                        "connection_error_baileys",
                        is_fixable=False,
                        severity=ir.IssueSeverity.WARNING,
                        translation_key="connection_error_baileys",
                    )
                    ir.async_delete_issue(self.hass, DOMAIN, "session_expired")
            else:
                ir.async_delete_issue(self.hass, DOMAIN, "session_expired")
                ir.async_delete_issue(self.hass, DOMAIN, "connection_error_baileys")
                ir.async_delete_issue(self.hass, DOMAIN, "passkey_required")

            # Reset unreachable counter and delete issue on success
            self._unreachable_count = 0
            if hasattr(self, "_normal_interval"):
                self.update_interval = self._normal_interval
            ir.async_delete_issue(self.hass, DOMAIN, "connection_failed")

            # Dynamically update device registry sw_version with live version
            version = stats.get("version")
            if version and version != "Unknown" and self.config_entry:
                try:
                    from homeassistant.helpers import device_registry as dr

                    dev_reg = dr.async_get(self.hass)
                    devices = dr.async_entries_for_config_entry(
                        dev_reg, self.config_entry.entry_id
                    )
                    for device in devices:
                        if (DOMAIN, self.client.session_id) in device.identifiers:
                            if device.sw_version != version:
                                dev_reg.async_update_device(
                                    device.id, sw_version=version
                                )
                            break
                except Exception as dr_err:
                    _LOGGER.debug(
                        "Failed to update device registry version: %s", dr_err
                    )

            data = {
                "connected": connected,
                "status": status,
                "status_details": details,
                "stats": stats,
                "chats": chats,
                "dashboard": dashboard,
                "moderation": moderation,
                "telegram": telegram,
                "autoresponder": autoresponder,
            }
            if self.config_entry:
                async_sync_moderation_entities(
                    self.hass, self.config_entry.entry_id, data
                )
                async_sync_telegram_bridge_entities(
                    self.hass, self.config_entry.entry_id, data
                )
            return _safe_text(data)
        except WhatsAppAuthError as err:
            _LOGGER.error("Authentication failed during polling: %s", err)
            raise ConfigEntryAuthFailed("Invalid API Key for WhatsApp Addon") from err
        except (HomeAssistantError, aiohttp.ClientError, TimeoutError) as err:
            return self._handle_unreachable(err)
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error communicating with WhatsApp API: %s", err)
            raise UpdateFailed(
                f"Unexpected error communicating with API: {err}"
            ) from err
