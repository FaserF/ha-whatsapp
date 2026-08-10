"""Config flow for HA WhatsApp integration."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import HomeAssistantError

try:
    from homeassistant.helpers import selector
except ImportError:
    from unittest.mock import MagicMock

    selector = MagicMock()  # type: ignore[assignment]
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

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
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Check if we are starting fresh (no accounts)
        # If so, we use 'default' as the session_id for better UX
        # with the Addon dashboard
        if not self.hass.config_entries.async_entries(DOMAIN):
            self.session_id = "default"
        # Check if we are running in Hass.io
        is_hassio_env = False
        try:
            from homeassistant.components.hassio import (  # type: ignore[attr-defined]
                is_hassio,
            )

            is_hassio_env = is_hassio(self.hass)
        except (ImportError, AttributeError):
            _LOGGER.debug("Hass.io component not found or is_hassio missing")

        if (
            user_input is None
            and is_hassio_env
            and not self.context.get("hassio_checked")
            and not self.discovery_info.get(CONF_URL)
        ):
            self.context["hassio_checked"] = True  # type: ignore[typeddict-unknown-key]
            return await self.async_step_hassio()

        # Support multiple instances

        errors: dict[str, str] = {}

        # Store host and api_key for scan step
        self.discovery_info = self.discovery_info or {}

        # Auto-discovery attempt: Scan candidates
        suggested_url = f"http://localhost:{DEFAULT_PORT}"

        if self.discovery_info and (
            self.discovery_info.get("host") or self.discovery_info.get(CONF_URL)
        ):
            suggested_url = str(
                self.discovery_info.get("host") or self.discovery_info.get(CONF_URL)
            )
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
                        _, writer = await asyncio.wait_for(
                            asyncio.open_connection(candidate, DEFAULT_PORT),
                            timeout=0.3,
                        )
                        writer.close()
                        await writer.wait_closed()
                        found_host = candidate
                        _LOGGER.debug("Found reachable host: %s", candidate)
                        break
                    except Exception:
                        continue

                if found_host:
                    suggested_url = f"http://{found_host}:{DEFAULT_PORT}"

        if user_input is None:
            # If CONF_API_KEY is missing from discovery_info,
            # attempt to read token from local disk
            if not self.discovery_info.get(CONF_API_KEY):
                try:
                    import os

                    data_dir = "/data" if os.name != "nt" else os.path.abspath("data")
                    token_file = os.path.join(data_dir, ".api_token")
                    if os.path.exists(token_file):
                        with open(token_file, encoding="utf-8") as f:
                            tok = f.read().strip()
                            if tok:
                                self.discovery_info[CONF_API_KEY] = tok
                except Exception:
                    pass

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("host", default=suggested_url): vol.All(
                            str, vol.Length(min=1)
                        ),
                        vol.Required(
                            CONF_API_KEY,
                            default=self.discovery_info.get(CONF_API_KEY) or "",
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.PASSWORD
                            )
                        ),
                    }
                ),
                description_placeholders={
                    "setup_url": "https://faserf.github.io/ha-whatsapp/"
                },
                errors=errors,
            )

        # If we reach here, user_input must be set
        assert user_input is not None
        clean_api_key = str(user_input[CONF_API_KEY]).strip()
        if not re.match(r"^[a-zA-Z0-9_\-]{8,128}$", clean_api_key):
            errors["base"] = "invalid_api_key_format"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("host", default=user_input.get("host")): vol.All(
                            str, vol.Length(min=1)
                        ),
                        vol.Required(
                            CONF_API_KEY, default=user_input.get(CONF_API_KEY)
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                type=selector.TextSelectorType.PASSWORD
                            )
                        ),
                    }
                ),
                description_placeholders={
                    "setup_url": "https://faserf.github.io/ha-whatsapp/"
                },
                errors=errors,
            )

        self.discovery_info[CONF_URL] = user_input["host"]
        self.discovery_info[CONF_API_KEY] = clean_api_key

        self.client = WhatsAppApiClient(
            host=str(user_input["host"]),
            api_key=clean_api_key,
            session_id=self.session_id,
        )

        # Validate connection and Key BEFORE proceeding
        try:
            await self.client.connect()
            # connect() now raises Exception if not 200 OK or invalid auth
        except HomeAssistantError as e:
            from .api import WhatsAppAuthError, WhatsAppRateLimitError

            error_msg = str(e)
            _LOGGER.error("Config Flow Validation Error: %s", error_msg)

            if isinstance(e, WhatsAppAuthError) or "Invalid API Key" in error_msg:
                errors["base"] = "invalid_auth"
            elif isinstance(e, WhatsAppRateLimitError):
                errors["base"] = "rate_limit"
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
                description_placeholders={
                    "setup_url": "https://faserf.github.io/ha-whatsapp/"
                },
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
                description_placeholders={
                    "setup_url": "https://faserf.github.io/ha-whatsapp/"
                },
                errors=errors,
            )

        return await self.async_step_scan()

    async def async_step_already_connected(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Present choice when an existing active WhatsApp session is detected."""
        if not self.client:
            return self.async_abort(reason="unknown")

        try:
            stats = await self.client.get_stats()
            my_number = stats.get("my_number") or "Unknown"
        except Exception:
            my_number = "Unknown"

        if user_input is not None:
            action = user_input.get("action")
            if action == "reconnect_new":
                _LOGGER.info(
                    "User requested logout of existing session to pair a new phone"
                )
                try:
                    await self.client.delete_session()
                except Exception as e:
                    _LOGGER.warning("Logout failed during reconnect choice: %s", e)
                self.qr_code = None
                return await self.async_step_scan()
            _LOGGER.info(
                "User confirmed using existing WhatsApp session (%s)", my_number
            )
            if my_number and my_number != "Unknown":
                await self.async_set_unique_id(my_number)
            return await self.async_create_flow_entry(my_number)

        return self.async_show_form(
            step_id="already_connected",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "action", default="use_existing"
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value="use_existing",
                                    label=f"Use active session ({my_number})",
                                ),
                                selector.SelectOptionDict(
                                    value="reconnect_new",
                                    label="Log out & pair a new phone (Scan QR)",
                                ),
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            description_placeholders={"phone_number": my_number},
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Display the QR code."""
        if not self.client:
            return self.async_abort(reason="unknown")

        # First check if already connected (e.g. from previous session)
        try:
            is_connected = await self.client.connect()
            _LOGGER.debug("Connect check result: %s", is_connected)
            if is_connected:
                _LOGGER.info("Already connected to WhatsApp, presenting choice step")
                return await self.async_step_already_connected()
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
                for _ in range(10):
                    self.qr_code = await self.client.get_qr_code()
                    if self.qr_code:
                        break
                    await asyncio.sleep(1)
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
            if user_input.get("use_phone_pairing"):
                return await self.async_step_phone_pairing()

            if user_input.get("request_new_qr"):
                # Force restart the session on the addon side to get a fresh QR code
                try:
                    await self.client.delete_session()
                    await self.client.start_session()
                except Exception as e:
                    _LOGGER.error("Failed to regenerate session for new QR: %s", e)
                self.qr_code = None
                await asyncio.sleep(5)
                return await self.async_step_scan()

            # User clicked "Submit" (meaning they scanned it)
            # Poll connection status for up to 30 seconds.
            # WhatsApp performs a rapid stream restart (515) right after QR scan,
            # and initial key/message sync may take up to 20-30 seconds.
            for _attempt in range(30):
                try:
                    if await self.client.connect():
                        _LOGGER.info("Connected to WhatsApp after QR scan submission")
                        stats = await self.client.get_stats()
                        my_number = stats.get("my_number")
                        if my_number:
                            await self.async_set_unique_id(my_number)
                        else:
                            await self.async_set_unique_id(self.session_id)
                        return await self.async_create_flow_entry(my_number)
                except AbortFlow:
                    raise
                except Exception as poll_err:
                    _LOGGER.debug(
                        "Polling connection status after scan submission: %s", poll_err
                    )
                await asyncio.sleep(1)

            # Final safety check: query stats directly if connect() was transient
            try:
                stats = await self.client.get_stats()
                if stats.get("connected") or stats.get("my_number"):
                    _LOGGER.info("Stats confirm connection after QR scan submission")
                    my_number = stats.get("my_number")
                    if my_number:
                        await self.async_set_unique_id(my_number)
                    else:
                        await self.async_set_unique_id(self.session_id)
                    return await self.async_create_flow_entry(my_number)
            except AbortFlow:
                raise
            except Exception as stats_err:
                _LOGGER.debug("Final stats safety check failed: %s", stats_err)

            # Check if the addon detected a passkey ceremony before concluding error
            try:
                dashboard = await self.client.get_dashboard()
                if dashboard.get("passkeyDetected"):
                    return await self.async_step_passkey_warning()
            except Exception:
                pass

            # If verification failed (not connected), show error and let user retry
            self.qr_code = None
            for _i in range(5):
                try:
                    self.qr_code = await self.client.get_qr_code()
                    if self.qr_code:
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)

            transparent_placeholder = (
                "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAAL"
                "AAAAAABAAEAAAIBRAA7"
            )

            errors = {}
            if not self.qr_code:
                errors["base"] = "qr_timeout"
            else:
                errors["base"] = "connection_error"

            return self.async_show_form(
                step_id="scan",
                data_schema=vol.Schema(
                    {
                        vol.Optional("request_new_qr", default=False): bool,
                        vol.Optional("use_phone_pairing", default=False): bool,
                    }
                ),
                description_placeholders={
                    "qr_image": self.qr_code or transparent_placeholder,
                },
                errors=errors,
            )

        # Get QR Code (Base64 data URI)
        if not self.qr_code:
            # Retry fetching multiple times
            for _i in range(15):  # Try for ~15 seconds
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
                        return await self.async_create_flow_entry(my_number)
                except Exception:
                    pass
                await asyncio.sleep(1)

        transparent_placeholder = (
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAAL"
            "AAAAAABAAEAAAIBRAA7"
        )

        errors = {}
        if user_input is not None and not self.qr_code:
            errors["base"] = "qr_timeout"

        return self.async_show_form(
            step_id="scan",
            data_schema=vol.Schema(
                {
                    vol.Optional("request_new_qr", default=False): bool,
                    vol.Optional("use_phone_pairing", default=False): bool,
                }
            ),  # No input needed, just "Submit" after scan
            description_placeholders={
                "qr_image": self.qr_code or transparent_placeholder,
            },
            errors=errors,
        )

    async def async_step_passkey_warning(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show passkey warning and let the user choose how to proceed.

        Option 1 (default): Instruct user to disable passkey on phone, then retry.
        Option 2 (checkbox): Attempt the experimental passkey ceremony
        — go to waiting step.
        """
        if user_input is not None:
            if user_input.get("continue_with_passkey"):
                # User chose Option 2: go to the waiting/approval screen
                return await self.async_step_passkey_waiting()
            # User acknowledged Option 1 — abort with instructions
            return self.async_abort(reason="passkey_remove_required")

        return self.async_show_form(
            step_id="passkey_warning",
            data_schema=vol.Schema(
                {
                    vol.Optional("continue_with_passkey", default=False): bool,
                }
            ),
            description_placeholders={
                "baileys_issue_url": "https://github.com/WhiskeySockets/Baileys/issues/2672",
                "qiua_fork_url": "https://github.com/Qiua/Baileys/commit/210740666c5e24a88e53dab7f19329bb336e1525",
                "baileys_pr_url": "https://github.com/WhiskeySockets/Baileys/pull/2676",
            },
        )

    async def async_step_passkey_waiting(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Waiting screen while the passkey ceremony completes on the phone.

        Polls /passkey/status every 3 seconds for up to 120 seconds.
        If connected → finishes setup.
        If still waiting → shows the form again with a status message.
        If timed out or still not connected after form submit → lets the user
        go back to passkey_warning or abort.
        """
        if not self.client:
            return self.async_abort(reason="unknown")

        errors: dict[str, str] = {}

        # Poll the addon a few times before deciding the answer
        for _i in range(40):  # up to ~120 seconds (40 × 3s)
            try:
                status = await self.client.get_passkey_status()
                if status.get("isConnected"):
                    # Passkey ceremony succeeded — complete the setup
                    _LOGGER.info("Passkey ceremony completed — WhatsApp connected")
                    stats = await self.client.get_stats()
                    my_number = stats.get("my_number")
                    if my_number:
                        await self.async_set_unique_id(my_number)
                    return await self.async_create_flow_entry(my_number)
                if not status.get("passkeyWaiting") and not status.get(
                    "passkeyDetected"
                ):
                    # Ceremony no longer active (e.g. timed out on addon side)
                    errors["base"] = "passkey_timeout"
                    break
            except Exception as e:
                _LOGGER.debug("Passkey status poll error: %s", e)

            await asyncio.sleep(3)

        if not errors:
            # Ran through all retries without connecting
            errors["base"] = "passkey_timeout"

        # Show the waiting form again (with error) so user can retry or abort
        return self.async_show_form(
            step_id="passkey_waiting",
            data_schema=vol.Schema({}),
            errors=errors,
        )

    async def async_step_phone_pairing(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle phone pairing."""
        errors: dict[str, str] = {}
        if user_input is not None:
            raw_phone = user_input.get("phone_number", "").strip()
            # Clean all non-digit characters
            digits = "".join(filter(str.isdigit, raw_phone))
            # Handle European national trunk zero e.g. 490151... -> 49151...
            import re

            clean_phone = re.sub(
                r"^(49|43|41|33|44|31|32|34|39|48)0(\d{8,})$", r"\1\2", digits
            )
            # Handle local German/EU zero prefix e.g. 0151... -> 49151...
            if clean_phone.startswith("0") and not clean_phone.startswith("00"):
                clean_phone = f"49{clean_phone[1:]}"
            elif clean_phone.startswith("00"):
                clean_phone = clean_phone[2:]

            try:
                assert self.client is not None
                code = await self.client.request_pairing_code(clean_phone)
                self.pairing_code = code
                return await self.async_step_show_pairing_code()
            except Exception as e:
                _LOGGER.error("Failed to request pairing code: %s", e)
                errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="phone_pairing",
            data_schema=vol.Schema(
                {
                    vol.Required("phone_number"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_show_pairing_code(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Display the pairing code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                assert self.client is not None
                connected = await self.client.connect()
                if connected:
                    stats = await self.client.get_stats()
                    my_number = stats.get("my_number")
                    if my_number:
                        await self.async_set_unique_id(my_number)
                    return await self.async_create_flow_entry(my_number)
            except Exception:
                pass
            errors["base"] = "connection_error"

        return self.async_show_form(
            step_id="show_pairing_code",
            data_schema=vol.Schema({}),
            description_placeholders={
                "pairing_code": getattr(self, "pairing_code", "N/A")
            },
            errors=errors if errors else None,
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
            from homeassistant.components.hassio import AddonManager  # type: ignore[attr-defined] # noqa: I001

            return AddonManager(self.hass, _LOGGER, slug, ADDON_NAME)
        except (ImportError, AttributeError):
            return None

    async def async_step_hassio(  # type: ignore[override]
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle Hass.io discovery."""
        try:
            from homeassistant.components.hassio import AddonState  # type: ignore[attr-defined] # noqa: I001
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
            self.discovery_info[CONF_URL] = f"http://{host}:{port}"

            # Also check for api_key in options or read from /data/.api_token
            if addon_info.options and (api_key := addon_info.options.get(CONF_API_KEY)):
                self.discovery_info[CONF_API_KEY] = api_key
            else:
                try:
                    import os

                    data_dir = "/data" if os.name != "nt" else os.path.abspath("data")
                    token_file = os.path.join(data_dir, ".api_token")
                    if os.path.exists(token_file):
                        with open(token_file, encoding="utf-8") as f:
                            tok = f.read().strip()
                            if tok:
                                self.discovery_info[CONF_API_KEY] = tok
                except Exception:
                    pass

            _LOGGER.debug("Pre-filled addon info: %s", self.discovery_info)
        except Exception as e:
            _LOGGER.warning("Could not pre-fill addon info: %s", e)

    async def async_step_hassio_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:  # type: ignore[override]
        """Handle zeroconf discovery."""
        host = discovery_info.host
        port = discovery_info.port
        properties = discovery_info.properties

        def decode_property(key: str) -> str | None:
            value = properties.get(key)
            if isinstance(value, bytes):
                return value.decode("utf-8")
            return str(value) if value is not None else None

        system_id = decode_property("system_id")
        api_key = decode_property("api_key")

        # Pre-fill discovery info
        suggested_url = f"http://{host}:{port}"
        self.discovery_info[CONF_URL] = suggested_url
        self.discovery_info["system_id"] = system_id
        self.discovery_info[CONF_API_KEY] = api_key

        if system_id:
            # First check if any entry already has this system_id
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.data.get("system_id") == system_id:
                    return self.async_abort(reason="already_configured")

            await self.async_set_unique_id(system_id)
            self._abort_if_unique_id_configured(updates={CONF_URL: suggested_url})
        else:
            # Fallback for older addon versions or if system_id is missing
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

        self.context.update(
            {
                "title_placeholders": {"host": suggested_url},
                "hassio_checked": True,  # Avoid jumping to Hassio install step
            }  # type: ignore[typeddict-item]
        )

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        url = self.discovery_info.get(CONF_URL) or self.discovery_info.get("host") or ""

        # Always attempt to resolve API key from discovery_info or local token file
        api_key = self.discovery_info.get(CONF_API_KEY) or ""
        if not api_key:
            try:
                import os

                data_dir = "/data" if os.name != "nt" else os.path.abspath("data")
                token_file = os.path.join(data_dir, ".api_token")
                if os.path.exists(token_file):
                    with open(token_file, encoding="utf-8") as f:
                        tok = f.read().strip()
                        if tok:
                            api_key = tok
                            self.discovery_info[CONF_API_KEY] = tok
            except Exception:
                pass

        if user_input is not None:
            return await self.async_step_user(
                {
                    "host": url,
                    CONF_API_KEY: api_key,
                }
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"host": url},
            data_schema=vol.Schema({}),
        )

    async def async_create_flow_entry(self, my_number: str | None) -> ConfigFlowResult:
        """Create the config entry, performing safety check first."""
        self._abort_if_unique_id_configured()

        show_warning = False
        show_fallback = False

        if not self.client:
            return self.async_abort(reason="unknown")

        # Poll get_chats up to 15 times (~15s) to detect if history sync populates chats
        for _i in range(15):
            try:
                chats = await self.client.get_chats()
                total_chats = int(chats.get("total_chats") or 0)
                initial_chats_received = bool(
                    chats.get("initial_chats_received") or False
                )
                _LOGGER.debug(
                    "Safety warning check: total_chats = %s, initial_received = %s",
                    total_chats,
                    initial_chats_received,
                )
                if total_chats > 0:
                    show_warning = False
                    show_fallback = False
                    break

                if initial_chats_received and total_chats == 0:
                    show_warning = True
                    break
            except Exception as e:
                _LOGGER.debug("Failed to retrieve chat history count: %s", e)
                show_fallback = True
                break
            await asyncio.sleep(1)
        else:
            # Timeout reached. Fall back to current chat count check.
            try:
                chats = await self.client.get_chats()
                total_chats = int(chats.get("total_chats") or 0)
                if total_chats == 0:
                    show_warning = True
                else:
                    show_fallback = False
            except Exception:
                show_fallback = True

        if self.client:
            await self.client.close()

        if show_warning or show_fallback:
            self.context["my_number"] = my_number  # type: ignore[typeddict-unknown-key]
            wtype = "fallback" if show_fallback else "new_account"
            self.context["warning_type"] = wtype  # type: ignore[typeddict-unknown-key]
            if show_fallback:
                return await self.async_step_account_warning_fallback()
            return await self.async_step_account_warning()

        url = (
            self.discovery_info.get(CONF_URL)
            or self.discovery_info.get("host")
            or (self.client.host if self.client else "http://localhost:8066")
        )
        api_key = self.discovery_info.get(CONF_API_KEY) or (
            self.client.api_key if self.client else ""
        )
        return self.async_create_entry(
            title=f"WhatsApp ({my_number})" if my_number else "WhatsApp",
            data={
                "session_id": self.session_id,
                CONF_URL: url,
                CONF_API_KEY: api_key,
                "system_id": self.discovery_info.get("system_id"),
            },
        )

    async def async_step_account_warning(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show warning for new account."""
        return await self._show_safety_warning("new_account", user_input)

    async def async_step_account_warning_fallback(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show warning fallback."""
        return await self._show_safety_warning("fallback", user_input)

    async def _show_safety_warning(
        self, warning_type: str, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Display safety warnings before completing setup."""
        if user_input is not None:
            my_number = self.context.get("my_number")
            url = (
                self.discovery_info.get(CONF_URL)
                or self.discovery_info.get("host")
                or ""
            )
            return self.async_create_entry(
                title=f"WhatsApp ({my_number})" if my_number else "WhatsApp",
                data={
                    "session_id": self.session_id,
                    CONF_URL: url,
                    CONF_API_KEY: self.discovery_info[CONF_API_KEY],
                    "system_id": self.discovery_info.get("system_id"),
                },
            )

        self.context["warning_type"] = warning_type  # type: ignore[typeddict-unknown-key]
        step_id = (
            "account_warning_fallback"
            if warning_type == "fallback"
            else "account_warning"
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema({}),
            description_placeholders={
                "issue_url": "https://github.com/FaserF/ha-whatsapp/issues/59",
                "docs_url": (
                    "https://faserf.github.io/ha-whatsapp/troubleshooting.html"
                    "#6-whatsapp-account-suspended--banned"
                ),
            },
        )


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
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
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
                    default=self._config_entry.options.get(CONF_MARK_AS_READ, False),
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Handle API Key Update
            raw_key = user_input.get(CONF_API_KEY)
            new_key = raw_key.strip() if isinstance(raw_key, str) else raw_key
            current_key = self._config_entry.data.get(CONF_API_KEY)

            if new_key and new_key != current_key:
                if not re.match(r"^[a-zA-Z0-9_\-]{8,128}$", new_key):
                    errors["base"] = "invalid_api_key_format"
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._get_schema(),
                        errors=errors,
                    )

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
                        errors=errors,
                    )
                except Exception:
                    _LOGGER.exception("Unexpected error validation API Key")
                    errors["base"] = "invalid_auth"
                    return self.async_show_form(
                        step_id="init",
                        data_schema=self._get_schema(),
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
        )


class CannotConnectError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate we cannot connect."""


class InvalidAuthError(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
