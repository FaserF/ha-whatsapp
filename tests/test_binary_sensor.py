"""Test the HA WhatsApp binary sensor."""
from unittest.mock import MagicMock, patch
import pytest

from homeassistant.core import HomeAssistant
from custom_components.whatsapp.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_binary_sensor(hass: HomeAssistant) -> None:
    """Test the binary sensor."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "mock"})
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient.connect", return_value=True):
         assert await hass.config_entries.async_setup(entry.entry_id)
         await hass.async_block_till_done()

    # Get the client that was created
    client = hass.data[DOMAIN][entry.entry_id]

    # Verify initial state (API init sets _connected = False until connected?)
    # Actually our mock 'connect' call in setup logic (if we had one) implies connection.
    # In __init__.py we commented out the actual connect call.
    # Let's manually simulate connection.
    client._connected = True

    # We need to force an update if we were relying on polling, but for the property
    # read we just read the state.
    state = hass.states.get("binary_sensor.whats_app")

    # Note: Name resolution might vary based on how HA names entities in test env.
    # Usually device_name + entity_name.
    # Our entity name is None, so it takes Device Name "WhatsApp".

    # Let's check all states to find it
    # ensure platform is loaded
    assert state
    assert state.state == "on"

    client._connected = False
    # In a real entity we'd call async_write_ha_state() or coordinator.async_refresh()
    # But since we just mocked the property access:
    entry.async_get_component(hass, "binary_sensor").get_entity("binary_sensor.whats_app").async_write_ha_state()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.whats_app")
    assert state.state == "off"
