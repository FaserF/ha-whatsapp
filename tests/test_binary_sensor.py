"""Test the HA WhatsApp binary sensor."""

from unittest.mock import AsyncMock, MagicMock, patch

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
        mock_instance.stats = {"sent": 10, "failed": 2}
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.close = AsyncMock()

        # Setup the integration
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # The state should be 'on' because mock_instance.connect() returned True
        state = hass.states.get("binary_sensor.whatsapp")
        assert state
        assert state.state == "on"
        assert state.attributes["messages_sent"] == 10

        # Simulate disconnect
        mock_instance.connect = AsyncMock(return_value=False)

        # Manually trigger coordinator refresh
        data = hass.data[DOMAIN][entry.entry_id]
        await data["coordinator"].async_refresh()
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.whatsapp")
        assert state.state == "off"
