"""The HA WhatsApp integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import discovery

from .api import WhatsAppApiClient
from .const import DOMAIN, EVENT_MESSAGE_RECEIVED

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA WhatsApp from a config entry."""

    addon_url = entry.data.get(CONF_URL, "http://localhost:8066")
    client = WhatsAppApiClient(host=addon_url)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    # Handle incoming messages
    def handle_incoming_message(data: dict) -> None:
        """Handle incoming message from API."""
        hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, data)

    client.register_callback(handle_incoming_message)

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

    hass.services.async_register(DOMAIN, "send_message", send_message_service)
    hass.services.async_register(DOMAIN, "send_poll", send_poll_service)
    # Add other services here (image, buttons, etc)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up Notify Platform (Legacy)
    hass.async_create_task(
        discovery.async_load_platform(
            hass, Platform.NOTIFY, DOMAIN, {"entry_id": entry.entry_id}, entry.config
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
