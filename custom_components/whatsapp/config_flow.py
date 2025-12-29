"""Config flow for HA WhatsApp integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import WhatsAppApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg, misc]
    """Handle a config flow for HA WhatsApp."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_info: dict[str, Any] = {}

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Zeroconf discovered: %s", discovery_info)

        # Check if already configured
        await self.async_set_unique_id(discovery_info.hostname)
        self._abort_if_unique_id_configured()

        self.discovery_info = {
            CONF_HOST: discovery_info.host,
            CONF_PORT: discovery_info.port,
            CONF_URL: f"http://{discovery_info.host}:{discovery_info.port}",
        }

        # Update title for discovery card
        self.context["title_placeholders"] = {"name": "WhatsApp Addon"}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title="WhatsApp",
                data=self.discovery_info,
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": "WhatsApp Addon"},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Construct URL
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            url = f"http://{host}:{port}"

            # Validate Connection
            client = WhatsAppApiClient(host=url)
            if await client.connect():
                # Connection checks out, but we might be unconnected to WhatsApp
                # That is fine, we just need to verify we can talk to the addon
                await self.async_set_unique_id(f"whatsapp-{host}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="WhatsApp",
                    data={CONF_HOST: host, CONF_PORT: port, CONF_URL: url},
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="localhost"): str,
                    vol.Required(CONF_PORT, default=8066): int,
                }
            ),
            errors=errors,
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
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    # Example option: Enable debug logging for messages
                    vol.Optional(
                        "debug_payloads",
                        default=self._config_entry.options.get("debug_payloads", False),
                    ): bool,
                }
            ),
        )


class CannotConnectError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
