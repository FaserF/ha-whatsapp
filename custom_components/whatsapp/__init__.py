"""The HA WhatsApp integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .api import WhatsAppApiClient
from .const import (
    CONF_API_KEY,
    CONF_POLLING_INTERVAL,
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
    client = WhatsAppApiClient(
        host=addon_url, api_key=api_key, mask_sensitive_data=mask_sensitive_data
    )

    coordinator = WhatsAppDataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Handle incoming messages
    def handle_incoming_message(data: dict[str, Any]) -> None:
        """Handle incoming message from API."""
        hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, data)

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
