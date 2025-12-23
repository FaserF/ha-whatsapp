"""Config flow for HA WhatsApp integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError


from .const import DOMAIN
from .api import WhatsAppApiClient

_LOGGER = logging.getLogger(__name__)

# Schema for the user step (if manual input was needed, but we want QR)
# STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required("host"): str})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA WhatsApp."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.client = WhatsAppApiClient()
        self.qr_code: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # In a real scenario, we might ask for a name or just start the QR process
        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display the QR code."""
        if user_input is not None:
             # User clicked "Submit" (meaning they scanned it)
             # Verify connection
            valid = await self.client.connect()
            if valid:
                return self.async_create_entry(
                    title="WhatsApp",
                    data={"session": "mock_session_string"},
                )
            return self.async_show_progress_done(next_step_id="scan") # Loop back or error

        # Get QR Code
        if not self.qr_code:
            self.qr_code = await self.client.get_qr_code()

        # In a real integration, we'd render this QR code as an image in the description
        # using markdown or a specialized view.
        # For this scaffold, we assume a placeholder.
        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema({}), # No input needed, just "Submit" after scan
            description_placeholders={"qr_image": "https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """WhatsApp Options Flow Handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    # Example option: Enable debug logging for messages
                    vol.Optional("debug_payloads", default=self.config_entry.options.get("debug_payloads", False)): bool,
                }
            ),
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
