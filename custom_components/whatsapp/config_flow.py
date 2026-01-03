"""Config flow for HA WhatsApp integration."""

from __future__ import annotations

import asyncio
import logging
import socket
import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import WhatsAppApiClient
from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA WhatsApp."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_info: dict[str, Any] = {}
        self.session_id = str(uuid.uuid4())
        self.client: WhatsAppApiClient | None = None
        self.qr_code: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Auto-discovery attempt: Scan candidates
        suggested_url = "http://localhost:8066"

        candidates = [
            "localhost",
            "7da084a7-whatsapp", # Standard Slug
            "whatsapp", # Docker
            "addon-whatsapp" # Supervisor
        ]

        found_host = None

        # Only scan if we are NOT submitting (first load)
        if user_input is None:
            for candidate in candidates:
                try:
                    sock = socket.create_connection((candidate, 8066), timeout=0.3)
                    sock.close()
                    found_host = candidate
                    _LOGGER.debug("Found reachable host: %s", candidate)
                    break
                except Exception:
                    continue

            if found_host:
                suggested_url = f"http://{found_host}:8066"

            if user_input is None:
                 return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({
                        vol.Required("host", default=suggested_url): str,
                        vol.Required(CONF_API_KEY): str,
                    }),
                    description_placeholders={
                        "setup_url": "https://github.com/FaserF/ha-whatsapp/blob/master/docs/SETUP.md"
                    },
                    errors=errors
                )

        self.client = WhatsAppApiClient(
            host=user_input["host"], api_key=user_input[CONF_API_KEY]
        )

        # Validate connection and Key BEFORE proceeding
        try:
            await self.client.connect()
            # connect() now raises Exception if not 200 OK
        except Exception as e:
            error_msg = str(e)
            _LOGGER.error("Config Flow Validation Error: %s", error_msg)

            if "Invalid API Key" in error_msg:
                errors["base"] = "invalid_auth"
            else:
                errors["base"] = "cannot_connect"

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("host", default=user_input["host"]): str,
                    vol.Required(CONF_API_KEY, default=user_input[CONF_API_KEY]): str,
                }),
                errors=errors
            )

        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display the QR code."""
        if not self.client:
             return self.async_abort(reason="unknown")

        try:
            # Trigger browser initialization to get QR
            if not self.qr_code:
                 # Trigger session start on addon side (Lazy Init)
                 await self.client.start_session()
                 await asyncio.sleep(2)
                 self.qr_code = await self.client.get_qr_code()
        except ImportError:
            return self.async_abort(reason="missing_dependency")
        except Exception as e:
            _LOGGER.exception("Unexpected error initializing WhatsApp client")
            if "Invalid API Key" in str(e):
                return self.async_abort(reason="invalid_auth")
            return self.async_abort(reason="connection_error")

        if user_input is not None:
             # User clicked "Submit" (meaning they scanned it)
             # Verify connection AGAIN
             try:
                valid = await self.client.connect()
                if valid:
                    await self.client.close()

                return self.async_create_entry(
                    title="WhatsApp",
                    data={"session_id": self.session_id},
                )
             except Exception:
                 pass

             return self.async_show_progress_done(next_step_id="scan") # Loop back

        # Get QR Code (Base64 data URI)
        if not self.qr_code:
            # Retry fetching multiple times
            for _i in range(5): # Try for ~5 seconds
                try:
                    self.qr_code = await self.client.get_qr_code()
                    if self.qr_code:
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)

        if not self.qr_code:
             # If still no QR code, show a "Waiting" placeholder or instructions
             # to retry.
             pass

        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema({}), # No input needed, just "Submit" after scan
            description_placeholders={
                "qr_image": self.qr_code or "https://via.placeholder.com/300x300.png?text=Waiting+for+QR+Code...",
                "status_text": "Waiting for QR Code... (Click Submit to refresh)"
                if not self.qr_code
                else "Scan this code with WhatsApp",
            },
        )

    @staticmethod
    @callback  # type: ignore[untyped-decorator]
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):  # type: ignore[misc]
    """WhatsApp Options Flow Handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get("reset_session"):
                try:
                    # Call DELETE /session
                    host = (
                        self.hass.data[DOMAIN][self._config_entry.entry_id].client.host
                    )
                    api_key = (
                        self.hass.data[DOMAIN][self._config_entry.entry_id].client.api_key
                    )
                    client = WhatsAppApiClient(host=host, api_key=api_key)
                    await client.delete_session()
                except Exception as e:
                    _LOGGER.error("Failed to reset session: %s", e)
                    errors["base"] = "reset_failed"
                    return self.async_show_form(step_id="init", errors=errors)

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "debug_payloads",
                        default=self._config_entry.options.get("debug_payloads", False),
                    ): bool,
                    vol.Optional("reset_session", default=False): bool,
                }
            ),
             description_placeholders={
                "warning": "⚠️ CAUTION: 'Reset Session' will log you out and "
                           "delete session data on the Addon."
            }
        )

    async def async_step_zeroconf(
        self, discovery_info: Any
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port

        # Check if already configured
        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured()

        # Pre-fill host
        suggested_url = f"http://{host}:{port}"

        self.context["title_placeholders"] = {"name": "WhatsApp Addon"}

        # Pass to user step with suggested host
        return await self.async_step_user(
            user_input={"host": suggested_url, "api_key": ""}
        )

class CannotConnectError(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
