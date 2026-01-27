"""The HA WhatsApp integration."""

from __future__ import annotations

import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall

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

    client = WhatsAppApiClient(
        host=addon_url,
        api_key=api_key,
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
        # If it's a standard user (@s.whatsapp.net or @lid), strip the suffix
        # This makes it easier for users to use numeric strings in automations
        full_sender = data.get("sender", "")
        clean_sender = full_sender
        if "@s.whatsapp.net" in full_sender or "@lid" in full_sender:
            clean_sender = full_sender.split("@")[0]

        data["sender"] = clean_sender
        data["raw_sender"] = full_sender

        # Whitelist filtering
        if whitelist is not None:
            # For groups, the raw data contains the group JID in remoteJid
            raw_msg = data.get("raw", {})
            remote_id = raw_msg.get("key", {}).get("remoteJid", "")
            is_group = "@g.us" in remote_id
            target = remote_id if is_group else full_sender

            if not client._is_allowed(target):
                _LOGGER.info(
                    "Ignoring incoming message from non-whitelisted %s: %s",
                    "group" if is_group else "sender",
                    target,
                )
                return

        hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, data)

        # Automatically mark as read if enabled
        if entry.options.get(CONF_MARK_AS_READ, True):
            # Extract ID and sender JID from the nested raw data
            # The addon sends full data in 'raw'
            raw_msg = data.get("raw", {})
            message_id = raw_msg.get("key", {}).get("id")
            number = data.get("raw_sender")  # Use full JID for API calls

            if message_id and number:
                hass.async_create_task(client.mark_as_read(number, message_id))

    client.register_callback(handle_incoming_message)
    polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 5)
    await client.start_polling(interval=polling_interval)

    # Automatically try to start the session on HA startup/load
    # This ensures that the addon starts working without manual intervention
    hass.async_create_task(client.start_session())

    # Register Services
    async def send_message_service(call: ServiceCall) -> None:
        """Handle the send_message service."""
        number = call.data.get("target")
        message = call.data.get("message")
        if number and message:
            await client.send_message(number, message)

    async def send_poll_service(call: ServiceCall) -> None:
        """Handle the send_poll service."""
        number = call.data.get("target")
        question = call.data.get("question")
        options = call.data.get("options", [])
        if number and question and options:
            await client.send_poll(number, question, options)

    async def send_image_service(call: ServiceCall) -> None:
        """Handle the send_image service."""
        number = call.data.get("target")
        image_url = call.data.get("url")
        caption = call.data.get("caption")
        if number and image_url:
            await client.send_image(number, image_url, caption)

    async def send_location_service(call: ServiceCall) -> None:
        """Handle the send_location service."""
        number = call.data.get("target")
        latitude = call.data.get("latitude")
        longitude = call.data.get("longitude")
        name = call.data.get("name")
        address = call.data.get("address")
        if number and latitude is not None and longitude is not None:
            await client.send_location(
                number, float(latitude), float(longitude), name, address
            )

    async def send_reaction_service(call: ServiceCall) -> None:
        """Handle the send_reaction service."""
        number = call.data.get("target")
        reaction = call.data.get("reaction")
        message_id = call.data.get("message_id")
        if number and reaction and message_id:
            await client.send_reaction(number, reaction, message_id)

    async def send_document_service(call: ServiceCall) -> None:
        """Handle the send_document service."""
        number = call.data.get("target")
        url = call.data.get("url")
        file_name = call.data.get("file_name")
        caption = call.data.get("message")  # Use 'message' for caption consistency
        if number and url:
            await client.send_document(number, url, file_name, caption)

    async def send_video_service(call: ServiceCall) -> None:
        """Handle the send_video service."""
        number = call.data.get("target")
        url = call.data.get("url")
        caption = call.data.get("message")
        if number and url:
            await client.send_video(number, url, caption)

    async def send_audio_service(call: ServiceCall) -> None:
        """Handle the send_audio service."""
        number = call.data.get("target")
        url = call.data.get("url")
        ptt = call.data.get("ptt", False)
        if number and url:
            await client.send_audio(number, url, ptt)

    async def revoke_message_service(call: ServiceCall) -> None:
        """Handle the revoke_message service."""
        number = call.data.get("target")
        message_id = call.data.get("message_id")
        if number and message_id:
            await client.revoke_message(number, message_id)

    async def edit_message_service(call: ServiceCall) -> None:
        """Handle the edit_message service."""
        number = call.data.get("target")
        message_id = call.data.get("message_id")
        new_content = call.data.get("message")
        if number and message_id and new_content:
            await client.edit_message(number, message_id, new_content)

    async def update_presence_service(call: ServiceCall) -> None:
        """Handle the update_presence service."""
        number = call.data.get("target")
        presence = call.data.get("presence")
        if number and presence:
            await client.set_presence(number, presence)

    async def send_buttons_service(call: ServiceCall) -> None:
        """Handle the send_buttons service."""
        number = call.data.get("target")
        text = call.data.get("message")
        buttons = call.data.get("buttons") or []
        footer = call.data.get("footer")
        if number and text and buttons:
            await client.send_buttons(number, text, buttons, footer)

    async def search_groups_service(call: ServiceCall) -> None:
        """Handle the search_groups service."""
        name_filter = call.data.get("name_filter", "").lower()

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

    hass.services.async_register(
        DOMAIN,
        "send_message",
        send_message_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_poll",
        send_poll_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("question"): cv.string,
                vol.Required("options"): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_image",
        send_image_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("caption"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_document",
        send_document_service,
        schema=vol.Schema(
            {
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
        send_video_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_audio",
        send_audio_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("url"): cv.string,
                vol.Optional("ptt", default=False): cv.boolean,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "revoke_message",
        revoke_message_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("message_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "edit_message",
        edit_message_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("message_id"): cv.string,
                vol.Required("message"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "send_location",
        send_location_service,
        schema=vol.Schema(
            {
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
        send_reaction_service,
        schema=vol.Schema(
            {
                vol.Required("target"): cv.string,
                vol.Required("reaction"): cv.string,
                vol.Required("message_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "update_presence",
        update_presence_service,
        schema=vol.Schema(
            {
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
        send_buttons_service,
        schema=vol.Schema(
            {
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
        search_groups_service,
        schema=vol.Schema(
            {
                vol.Optional("name_filter"): cv.string,
            }
        ),
    )

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


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
