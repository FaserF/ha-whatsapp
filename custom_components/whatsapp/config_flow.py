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
        import uuid
        self.session_id = str(uuid.uuid4())
        self.client: WhatsAppApiClient | None = None
        self.qr_code: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Define storage path for this session
        storage_dir = self.hass.config.path(".storage", "whatsapp", self.session_id)
        self.client = WhatsAppApiClient(user_data_dir=storage_dir)

        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display the QR code."""
        if not self.client:
             return self.async_abort(reason="unknown")

        try:
            # Trigger browser initialization to get QR
            # If Playwright is missing, this should raise ImportError/Error from API
            if not self.qr_code:
                 self.qr_code = await self.client.get_qr_code()
        except ImportError:
            return self.async_abort(reason="missing_dependency")
        except Exception as e:
            _LOGGER.exception("Unexpected error initializing WhatsApp client")
            return self.async_abort(reason="connection_error")

        if user_input is not None:
             # User clicked "Submit" (meaning they scanned it)
             # Verify connection
            valid = await self.client.connect()
            if valid:
                # IMPORTANT: Close the client so it releases the directory lock
                # The __init__ setup will re-open it.
                await self.client.close()

                return self.async_create_entry(
                    title="WhatsApp",
                    data={"session_id": self.session_id},
                )
            return self.async_show_progress_done(next_step_id="scan") # Loop back or error

        # Get QR Code (Base64 data URI)
        if not self.qr_code:
            self.qr_code = await self.client.get_qr_code()

        # We pass the base64 string directly to the markdown
        # Markdown in HA supports ![Alt](data:image/png;base64,...)
        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema({}), # No input needed, just "Submit" after scan
            description_placeholders={"qr_image": self.qr_code},
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
        self._config_entry = config_entry

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
                    vol.Optional("debug_payloads", default=self._config_entry.options.get("debug_payloads", False)): bool,
                }
            ),
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
