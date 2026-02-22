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
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import WhatsAppApiClient
from .const import (
    CONF_API_KEY,
    CONF_MARK_AS_READ,
    CONF_POLLING_INTERVAL,
    CONF_RETRY_ATTEMPTS,
    CONF_SELF_MESSAGES,
    CONF_URL,
    CONF_WHITELIST,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

ADDON_STABLE_SLUG = "7da084a7_whatsapp"
ADDON_EDGE_SLUG = "7da084a7_whatsapp_edge"
ADDON_NAME = "WhatsApp"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg, misc]
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
        # Check if we are running in Hass.io
        is_hassio_env = False
        try:
            from homeassistant.components.hassio import is_hassio

            is_hassio_env = is_hassio(self.hass)
        except (ImportError, AttributeError):
            _LOGGER.debug("Hass.io component not found or is_hassio missing")

        if (
            user_input is None
            and is_hassio_env
            and not self.context.get("hassio_checked")
        ):
            self.context["hassio_checked"] = True
            return await self.async_step_hassio()

        # Support multiple instances

        errors: dict[str, str] = {}

        # Store host and api_key for scan step
        self.discovery_info = self.discovery_info or {}

        # Auto-discovery attempt: Scan candidates
        suggested_url = f"http://localhost:{DEFAULT_PORT}"

        if self.discovery_info and self.discovery_info.get("host"):
            suggested_url = str(self.discovery_info["host"])
        else:
            candidates = [
                "localhost",
                "7da084a7-whatsapp",  # Standard Slug
                "7da084a7-whatsapp-edge",  # Edge Slug
                "local-whatsapp",  # Local Slug
                "whatsapp",  # Docker
                "addon-whatsapp",  # Supervisor
            ]

            found_host = None

            # Only scan if we are NOT submitting (first load)
            if user_input is None:
                for candidate in candidates:
                    try:
                        sock = socket.create_connection(
                            (candidate, DEFAULT_PORT), timeout=0.3
                        )
                        sock.close()
                        found_host = candidate
                        _LOGGER.debug("Found reachable host: %s", candidate)
                        break
                    except Exception:
                        continue

                if found_host:
                    suggested_url = f"http://{found_host}:{DEFAULT_PORT}"

            if user_input is None:
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Required("host", default=suggested_url): vol.All(
                                str, vol.Length(min=1)
                            ),
                            vol.Required(
                                CONF_API_KEY,
                                default=self.discovery_info.get(CONF_API_KEY, ""),
                            ): vol.All(str, vol.Length(min=1)),
                        }
                    ),
                    description_placeholders={
                        "setup_url": "https://github.com/FaserF/ha-whatsapp/blob/master/docs/SETUP.md"
                    },
                    errors=errors,
                )

        # If we reach here, user_input must be set
        assert user_input is not None
        self.discovery_info[CONF_URL] = user_input["host"]
        self.discovery_info[CONF_API_KEY] = user_input[CONF_API_KEY]

        self.client = WhatsAppApiClient(
            host=str(user_input["host"]),
            api_key=str(user_input[CONF_API_KEY]),
            session_id=self.session_id,
        )

        # Validate connection and Key BEFORE proceeding
        try:
            await self.client.connect()
            # connect() now raises Exception if not 200 OK or invalid auth
        except HomeAssistantError as e:
            error_msg = str(e)
            _LOGGER.error("Config Flow Validation Error: %s", error_msg)

            if "Invalid API Key" in error_msg:
                errors["base"] = "invalid_auth"
            else:
                errors["base"] = "cannot_connect"

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("host", default=user_input.get("host")): vol.All(
                            str, vol.Length(min=1)
                        ),
                        vol.Required(
                            CONF_API_KEY, default=user_input.get(CONF_API_KEY)
                        ): vol.All(str, vol.Length(min=1)),
                    }
                ),
                errors=errors,
            )
        except Exception:
            _LOGGER.exception("Unexpected error in config flow")
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("host", default=user_input.get("host")): vol.All(
                            str, vol.Length(min=1)
                        ),
                        vol.Required(
                            CONF_API_KEY, default=user_input.get(CONF_API_KEY)
                        ): vol.All(str, vol.Length(min=1)),
                    }
                ),
                errors=errors,
            )

        return await self.async_step_scan()

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display the QR code."""
        if not self.client:
            return self.async_abort(reason="unknown")

        # First check if already connected (e.g. from previous session)
        try:
            is_connected = await self.client.connect()
            _LOGGER.debug("Connect check result: %s", is_connected)
            if is_connected:
                _LOGGER.info("Already connected to WhatsApp, skipping QR scan")
                stats = await self.client.get_stats()
                my_number = stats.get("my_number")
                if my_number:
                    await self.async_set_unique_id(my_number)
                    self._abort_if_unique_id_configured()

                await self.client.close()
                return self.async_create_entry(
                    title=f"WhatsApp ({my_number})" if my_number else "WhatsApp",
                    data={
                        "session_id": self.session_id,
                        CONF_URL: self.discovery_info[CONF_URL],
                        CONF_API_KEY: self.discovery_info[CONF_API_KEY],
                    },
                )
        except AbortFlow:
            raise
        except Exception as e:
            _LOGGER.debug("Connect check failed with exception: %s", e)
            pass  # Not connected, proceed with QR flow

        try:
            # Trigger browser initialization to get QR
            if not self.qr_code:
                # Trigger session start on addon side (Lazy Init)
                await self.client.start_session()
                await asyncio.sleep(2)
                self.qr_code = await self.client.get_qr_code()
        except ImportError:
            return self.async_abort(reason="missing_dependency")
        except HomeAssistantError as e:
            _LOGGER.warning("Error initializing WhatsApp client: %s", e)
            if "Invalid API Key" in str(e):
                return self.async_abort(reason="invalid_auth")
            return self.async_abort(reason="connection_error")
        except Exception:
            _LOGGER.exception("Unexpected error initializing WhatsApp client")
            return self.async_abort(reason="connection_error")

        if user_input is not None:
            # User clicked "Submit" (meaning they scanned it)
            # Verify connection AGAIN - check if WhatsApp is actually connected
            try:
                connected = await self.client.connect()
                if connected:
                    stats = await self.client.get_stats()
                    my_number = stats.get("my_number")
                    if my_number:
                        await self.async_set_unique_id(my_number)
                        self._abort_if_unique_id_configured()

                    await self.client.close()
                    return self.async_create_entry(
                        title=f"WhatsApp ({my_number})" if my_number else "WhatsApp",
                        data={
                            "session_id": self.session_id,
                            CONF_URL: self.discovery_info[CONF_URL],
                            CONF_API_KEY: self.discovery_info[CONF_API_KEY],
                        },
                    )

            except Exception:
                pass

            # If verification failed (not connected), show error and let user retry
            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "qr_image": self.qr_code
                    or "https://via.placeholder.com/300x300.png?text=Waiting+for+QR+Code...",
                    "status_text": (
                        "Not connected yet. Please scan the QR code and try again."
                    ),
                },
                errors={"base": "connection_error"},
            )

        # Get QR Code (Base64 data URI)
        if not self.qr_code:
            # Retry fetching multiple times
            for _i in range(5):  # Try for ~5 seconds
                try:
                    self.qr_code = await self.client.get_qr_code()
                    if self.qr_code:
                        break

                    # If no QR code, check if we actually connected in the background
                    if await self.client.connect():
                        _LOGGER.debug("Connected in background during QR scan")
                        stats = await self.client.get_stats()
                        my_number = stats.get("my_number")
                        if my_number:
                            await self.async_set_unique_id(my_number)
                            self._abort_if_unique_id_configured()

                        await self.client.close()
                        return self.async_create_entry(
                            title=(
                                f"WhatsApp ({my_number})" if my_number else "WhatsApp"
                            ),
                            data={
                                "session_id": self.session_id,
                                CONF_URL: self.discovery_info[CONF_URL],
                                CONF_API_KEY: self.discovery_info[CONF_API_KEY],
                            },
                        )
                except Exception:
                    pass
                await asyncio.sleep(1)

        if not self.qr_code:
            # If still no QR code, show a "Waiting" placeholder or instructions
            # to retry.
            pass

        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema({}),  # No input needed, just "Submit" after scan
            description_placeholders={
                "qr_image": self.qr_code
                or "https://via.placeholder.com/300x300.png?text=Waiting+for+QR+Code...",
                "status_text": (
                    "Waiting for QR Code... (Click Submit to refresh)"
                    if not self.qr_code
                    else "Scan this code with WhatsApp"
                ),
            },
        )

    @staticmethod
    @callback  # type: ignore[untyped-decorator]
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def _async_get_addon_manager(self, slug: str) -> Any:
        """Return the addon manager."""
        try:
            from homeassistant.components.hassio import AddonManager

            return AddonManager(self.hass, slug, ADDON_NAME)
        except (ImportError, AttributeError):
            return None

    async def async_step_hassio(
        self, _user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Hass.io discovery."""
        try:
            from homeassistant.components.hassio import AddonState
        except (ImportError, AttributeError):
            return await self.async_step_user()

        # Check if either stable or edge is installed
        for slug in [ADDON_STABLE_SLUG, ADDON_EDGE_SLUG]:
            addon_manager = await self._async_get_addon_manager(slug)
            if addon_manager is None:
                continue
            addon_info = await addon_manager.async_get_addon_info()
            if addon_info.state != AddonState.NOT_INSTALLED:
                # Already installed, pre-fill info and go to user step
                await self._async_prefill_addon_info(slug)
                return await self.async_step_user()

        # Neither installed, ask user
        return await self.async_step_hassio_confirm()

    async def _async_prefill_addon_info(self, slug: str) -> None:
        """Pre-fill addon info from Supervisor."""
        addon_manager = await self._async_get_addon_manager(slug)
        try:
            addon_info = await addon_manager.async_get_addon_info()
            # Supervisor hostnames use hyphens, slugs might use underscores
            host = slug.replace("_", "-")
            port = DEFAULT_PORT

            if addon_info.network:
                # Find port for 8066 (internal)
                for internal, external in addon_info.network.items():
                    if internal.startswith(f"{DEFAULT_PORT}/"):
                        port = external
                        break

            self.discovery_info["host"] = f"http://{host}:{port}"

            # Also check for api_key in options
            if addon_info.options and (api_key := addon_info.options.get(CONF_API_KEY)):
                self.discovery_info[CONF_API_KEY] = api_key

            _LOGGER.debug("Pre-filled addon info: %s", self.discovery_info)
        except Exception as e:
            _LOGGER.warning("Could not pre-fill addon info: %s", e)

    async def async_step_hassio_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm installation of the official addon."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Install selected addon
            slug = (
                ADDON_EDGE_SLUG
                if user_input.get("version") == "edge"
                else ADDON_STABLE_SLUG
            )
            addon_manager = await self._async_get_addon_manager(slug)
            try:
                await addon_manager.async_install_addon()
                await addon_manager.async_start_addon()
            except Exception as e:
                _LOGGER.error("Failed to install WhatsApp addon (%s): %s", slug, e)
                errors["base"] = "addon_install_error"
                return self.async_show_form(
                    step_id="hassio_confirm",
                    data_schema=vol.Schema(
                        {
                            vol.Required("version", default="stable"): vol.In(
                                {"stable": "Stable", "edge": "Edge (Development)"}
                            )
                        }
                    ),
                    errors=errors,
                )
            # After installation, pre-fill info
            await self._async_prefill_addon_info(slug)
            return await self.async_step_user()

        return self.async_show_form(
            step_id="hassio_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("version", default="stable"): vol.In(
                        {"stable": "Stable", "edge": "Edge (Development)"}
                    )
                }
            ),
            description_placeholders={"addon_name": ADDON_NAME},
        )

    async def async_step_zeroconf(self, discovery_info: Any) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port

        # Check if already configured
        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured()

        # Pre-fill host
        suggested_url = f"http://{host}:{port}"
        self.discovery_info["host"] = suggested_url

        self.context["title_placeholders"] = {"name": "WhatsApp Addon"}

        # Pass to user step with suggested host
        return await self.async_step_user()


class OptionsFlowHandler(config_entries.OptionsFlow):  # type: ignore[misc]
    """WhatsApp Options Flow Handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    def _get_schema(self) -> vol.Schema:
        """Return the options schema."""
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=self._config_entry.data.get(CONF_API_KEY),
                ): str,
                vol.Optional(
                    "debug_payloads",
                    default=self._config_entry.options.get("debug_payloads", False),
                ): bool,
                vol.Optional(
                    CONF_POLLING_INTERVAL,
                    default=self._config_entry.options.get(CONF_POLLING_INTERVAL, 5),
                ): vol.All(int, vol.Range(min=5)),
                vol.Optional(
                    "mask_sensitive_data",
                    default=self._config_entry.options.get(
                        "mask_sensitive_data", False
                    ),
                ): bool,
                vol.Optional(
                    CONF_MARK_AS_READ,
                    default=self._config_entry.options.get(CONF_MARK_AS_READ, True),
                ): bool,
                vol.Optional(
                    CONF_RETRY_ATTEMPTS,
                    default=self._config_entry.options.get(CONF_RETRY_ATTEMPTS, 2),
                ): vol.All(int, vol.Range(min=0, max=10)),
                vol.Optional(
                    CONF_WHITELIST,
                    default=self._config_entry.options.get(CONF_WHITELIST, ""),
                ): str,
                vol.Optional(
                    CONF_SELF_MESSAGES,
                    default=self._config_entry.options.get(CONF_SELF_MESSAGES, False),
                ): bool,
                vol.Optional("reset_session", default=False): bool,
            }
        )

    def _get_placeholders(self) -> dict[str, str]:
        """Return description placeholders."""
        return {
            "warning": (
                "⚠️ CAUTION: 'Reset Session' will log you out and "
                "delete session data on the Addon."
            )
        }

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Handle API Key Update
            new_key = user_input.get(CONF_API_KEY)
            current_key = self._config_entry.data.get(CONF_API_KEY)

            if new_key and new_key != current_key:
                # Validate new key
                host = self._config_entry.data.get(CONF_URL, "")
                test_client = WhatsAppApiClient(host=host, api_key=new_key)
                try:
                    await test_client.connect()
                except HomeAssistantError:
                    errors["base"] = "invalid_auth"
                    # Redisplay form with error
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._get_schema(),
                        description_placeholders=self._get_placeholders(),
                        errors=errors,
                    )
                except Exception:
                    _LOGGER.exception("Unexpected error validation API Key")
                    errors["base"] = "invalid_auth"
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._get_schema(),
                        description_placeholders=self._get_placeholders(),
                        errors=errors,
                    )

                # Update the main config entry data (not options)
                new_data = self._config_entry.data.copy()
                new_data[CONF_API_KEY] = new_key
                self.hass.config_entries.async_update_entry(
                    self._config_entry, data=new_data
                )
                _LOGGER.info("WhatsApp API Key updated successfully via Options Flow")

            if user_input.get("reset_session"):
                try:
                    # Call DELETE /session
                    data = self.hass.data[DOMAIN][self._config_entry.entry_id]
                    client: WhatsAppApiClient = data["client"]
                    # data['client'] may be stale if key changed.
                    # Reload happens on update. returning create_entry triggers it.
                    # Reset session happens before reload.
                    # If key changed, we assume user just wants to fix auth.
                    # If reset_session checked, try it (might fail if old client).
                    # Validated new key, so use fresh client or rely on reload.

                    _LOGGER.info(
                        "Triggering session reset for WhatsApp instance: %s",
                        self._config_entry.entry_id,
                    )
                    await client.delete_session()
                    _LOGGER.info("Session reset request sent successfully")
                except Exception as e:
                    _LOGGER.error("Failed to reset session: %s", e)
                    # Only show error if we didn't just fix the API key
                    # If API key was fixed, maybe the old client failed (expected).
                    if not (new_key and new_key != current_key):
                        errors["base"] = "reset_failed"
                        return self.async_show_form(
                            step_id="init",
                            data_schema=self._get_schema(),
                            description_placeholders=self._get_placeholders(),
                            errors=errors,
                        )

            # Always remove API Key from options (it belongs in data)
            user_input.pop(CONF_API_KEY, None)

            # Always remove ephemeral reset_session option
            user_input.pop("reset_session", None)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_schema(),
            description_placeholders=self._get_placeholders(),
        )


class CannotConnectError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
