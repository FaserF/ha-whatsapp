"""Test the HA WhatsApp binary sensor."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN


async def test_binary_sensor(hass: HomeAssistant) -> None:
    """Test the binary sensor."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "mock"})
    entry.add_to_hass(hass)

    # Patch the Client Class
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.is_connected = AsyncMock(return_value=True)
        # Initialize internal state for the synchronous property check if needed,
        # or we rely on the sensor reading a property.
        # The sensor implementation reads `self.client._connected`.
        mock_instance._connected = True

        # We also need to patch async_setup_entry to use our mocked client if it
        # instantiates it internally, OR we rely on the fact that we patched the
        # class before setup called it?
        # Actually, async_setup_entry instantiates WhatsAppApiClient().
        # The patch above should catch that.

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.whatsapp")
        assert state
        assert state.state == "on"
        # Depending on device class "connectivity", on=Connected

        # Simulate disconnect
        mock_instance._connected = False
        # Trigger update (normally done by coordinator or callback)
        entity = entry.async_get_component(hass, "binary_sensor").get_entity(
            "binary_sensor.whatsapp"
        )
        entity.async_write_ha_state()
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.whatsapp")
        assert state.state == "off"
