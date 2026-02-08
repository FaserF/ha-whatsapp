"""The HA WhatsApp integration."""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError

from .api import WhatsAppApiClient
from .const import (
    CONF_API_KEY,
    CONF_MARK_AS_READ,
    CONF_POLLING_INTERVAL,
    CONF_WHITELIST,
    DOMAIN,
    EVENT_MESSAGE_RECEIVED,
)
from .coordinator import WhatsAppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.NOTIFY, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA WhatsApp from a config entry."""

    addon_url = entry.data.get(CONF_URL, "http://localhost:8066")
    api_key = entry.data.get(CONF_API_KEY)
    mask_sensitive_data = entry.options.get("mask_sensitive_data", False)
    whitelist_str = entry.options.get(CONF_WHITELIST, "")
    whitelist = None
    if whitelist_str:
        whitelist = [x.strip() for x in whitelist_str.split(",") if x.strip()]

    session_id = entry.data.get("session_id", "default")
    client = WhatsAppApiClient(
        host=addon_url,
        api_key=api_key,
        session_id=session_id,
        mask_sensitive_data=mask_sensitive_data,
        whitelist=whitelist,
    )

    coordinator = WhatsAppDataUpdateCoordinator(hass, client, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    # Handle incoming messages
    def handle_incoming_message(data: dict[str, Any]) -> None:
        """Handle incoming message from API."""
        # Normalize sender for the event
        # The addon now sends 'sender_number' which is the best-effort phone number
        # We prefer that over splitting the raw JID which might be an LID (UUID)
        full_sender = data.get("sender", "")
        sender_number = data.get("sender_number")

        # The 'sender' field should be the full JID for direct use in replies/services
        data["sender"] = full_sender
        data["raw_sender"] = full_sender

        if sender_number:
            clean_sender = sender_number
        else:
            # Fallback for older addon versions or weird cases
            clean_sender = full_sender
            if "@s.whatsapp.net" in full_sender or "@lid" in full_sender:
                clean_sender = full_sender.split("@")[0]

        data["sender_number"] = clean_sender

        # Whitelist filtering
        if whitelist is not None:
            # For groups, the raw data contains the group JID in remoteJid
            raw_msg = data.get("raw", {})
            remote_id = raw_msg.get("key", {}).get("remoteJid", "")
            is_group = "@g.us" in remote_id
            target = remote_id if is_group else full_sender

            if not client.is_allowed(target):
                _LOGGER.info(
                    "Ignoring incoming message from non-whitelisted %s: %s",
                    "group" if is_group else "sender",
                    target,
                )
                return

        # Add session identifiers to let users distinguish between multiple bots
        data["entry_id"] = entry.entry_id
        data["session_id"] = session_id

        hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, data)

        # Automatically mark as read if enabled
        if entry.options.get(CONF_MARK_AS_READ, True):
            # Extract ID and sender JID from the nested raw data
            # The addon sends full data in 'raw'
            raw_msg = data.get("raw", {})
            # Try to get message_id from 'raw.key.id' or fallback to top-level 'id'
            message_id = raw_msg.get("key", {}).get("id") or data.get("id")
            number = data.get("sender")  # Full JID (e.g. 123456789@s.whatsapp.net)

            if message_id and number:
                hass.async_create_task(client.mark_as_read(number, message_id))
            else:
                _LOGGER.warning(
                    "Auto-mark-as-read enabled but missing data. "
                    "Message ID: %s, Number: %s",
                    message_id,
                    number,
                )

    client.register_callback(handle_incoming_message)
    polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 5)
    await client.start_polling(interval=polling_interval)

    # Automatically try to start the session on HA startup/load
    # This ensures that the addon starts working without manual intervention
    hass.async_create_task(client.start_session())

    # Register services globally
    await async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


# checking lines 141-176 replacement
def get_client_for_account(
    hass: HomeAssistant, account: str | None
) -> WhatsAppApiClient:
    """Get the correct client based on the account (entry_id or unique ID)."""
    clients: dict[str, WhatsAppApiClient] = {
        entry_id: data["client"]
        for entry_id, data in hass.data.get(DOMAIN, {}).items()
        if "client" in data
    }

    if not clients:
        raise ServiceValidationError("No WhatsApp accounts configured")

    # If only one client exists and no account specified, use it
    if account is None:
        if len(clients) == 1:
            return list(clients.values())[0]
        raise ServiceValidationError(
            "Multiple WhatsApp accounts found. "
            "Please specify the 'account' (entry ID or unique ID)."
        )

    # Try mapping by entry_id
    if account in clients:
        return clients[account]

    # Try mapping by unique_id (my_number)
    for entry_id, client in clients.items():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry and entry.unique_id == account:
            return client
        # Fallback to title
        if entry and entry.title == account:
            return client

    raise ServiceValidationError(f"WhatsApp account '{account}' not found")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up global WhatsApp services."""
    if hass.services.has_service(DOMAIN, "send_message"):
        return

    async def _handle_service(call: ServiceCall) -> None:
        """General service handler for routing."""
        account = call.data.get("account")
        client = get_client_for_account(hass, account)

        service = call.service
        data = {k: v for k, v in call.data.items() if k != "account"}

        if service == "send_message":
            await client.send_message(data["target"], data["message"])
        elif service == "send_poll":
            await client.send_poll(
                data["target"], data["question"], data.get("options", [])
            )
        elif service == "send_image":
            await client.send_image(data["target"], data["url"], data.get("caption"))
        elif service == "send_location":
            await client.send_location(
                data["target"],
                float(data["latitude"]),
                float(data["longitude"]),
                data.get("name"),
                data.get("address"),
            )
        elif service == "send_reaction":
            await client.send_reaction(
                data["target"], data["reaction"], data["message_id"]
            )
        elif service == "send_document":
            await client.send_document(
                data["target"], data["url"], data.get("file_name"), data.get("message")
            )
        elif service == "send_video":
            await client.send_video(data["target"], data["url"], data.get("message"))
        elif service == "send_audio":
            await client.send_audio(data["target"], data["url"], data.get("ptt", False))
        elif service == "revoke_message":
            await client.revoke_message(data["target"], data["message_id"])
        elif service == "edit_message":
            await client.edit_message(
                data["target"], data["message_id"], data["message"]
            )
        elif service == "send_list":
            await client.send_list(
                data["target"],
                data.get("title") or "",
                data.get("text") or "",
                data.get("button_text") or "",
                data["sections"],
            )
        elif service == "send_contact":
            await client.send_contact(
                data["target"], data["name"], data["contact_number"]
            )
        elif service == "configure_webhook":
            await client.set_webhook(
                data["url"], data.get("enabled", True), data.get("token")
            )
        elif service == "update_presence":
            await client.set_presence(data["target"], data["presence"])
        elif service == "send_buttons":
            await client.send_buttons(
                data["target"], data["message"], data["buttons"], data.get("footer")
            )
        elif service == "mark_as_read":
            await client.mark_as_read(data["target"], data.get("message_id"))
        elif service == "search_groups":
            await _handle_search_groups(hass, client, data.get("name_filter", ""))

    async def _handle_search_groups(
        hass: HomeAssistant, client: WhatsAppApiClient, name_filter: str
    ) -> None:
        """Handle search_groups separately to keep generic router cleaner."""
        name_filter = name_filter.lower()
        try:
            groups = await client.get_groups()
            if name_filter:
                groups = [g for g in groups if name_filter in g["name"].lower()]

            if not groups:
                msg_suffix = f' matching "{name_filter}"' if name_filter else ""
                message = f"No groups found{msg_suffix}."
            else:
                table = "| Name | Group ID | Participants |\n| :--- | :--- | :--- |\n"
                for g in groups:
                    table += f"| {g['name']} | `{g['id']}` | {g['participants']} |\n"

                message = (
                    f"Found {len(groups)} group(s):\n\n{table}\n\n"
                    "*Tip: Use the Group ID in the 'target' field of other services.*"
                )

            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Group Search",
                    "message": message,
                    "notification_id": "whatsapp_group_search",
                },
            )
        except Exception as e:
            _LOGGER.error("Failed to search groups: %s", e)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Group Search Error",
                    "message": f"Error: {e}",
                    "notification_id": "whatsapp_group_search_error",
                },
            )

    # Define common schema with optional account
    s_base: dict[Any, Any] = {vol.Optional("account"): cv.string}

    hass.services.async_register(
        DOMAIN,
        "send_message",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_poll",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("question"): cv.string,
                vol.Required("options"): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_image",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("caption"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_document",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("file_name"): cv.string,
                vol.Optional("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_video",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_audio",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("ptt", default=False): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "revoke_message",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("message_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "edit_message",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("message_id"): cv.string,
                vol.Required("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_list",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("sections"): cv.match_all,
                vol.Optional("title"): cv.string,
                vol.Optional("text"): cv.string,
                vol.Optional("button_text"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_contact",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("name"): cv.string,
                vol.Required("contact_number"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "configure_webhook",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("url"): cv.string,
                vol.Optional("enabled", default=True): cv.boolean,
                vol.Optional("token"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_location",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("latitude"): vol.Coerce(float),
                vol.Required("longitude"): vol.Coerce(float),
                vol.Optional("name"): cv.string,
                vol.Optional("address"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_reaction",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("reaction"): cv.string,
                vol.Required("message_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "update_presence",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("presence"): vol.In(
                    ["available", "unavailable", "composing", "recording", "paused"]
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_buttons",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Required("message"): cv.string,
                vol.Required("buttons"): vol.All(cv.ensure_list, [dict]),
                vol.Optional("footer"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "search_groups",
        _handle_service,
        schema=vol.Schema(
            {**s_base, vol.Optional("name_filter", default=""): cv.string}
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "mark_as_read",
        _handle_service,
        schema=vol.Schema(
            {
                **s_base,
                vol.Required("target"): cv.string,
                vol.Optional("message_id"): cv.string,
            }
        ),
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: WhatsAppApiClient = data["client"]
    await client.close()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return bool(unload_ok)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
