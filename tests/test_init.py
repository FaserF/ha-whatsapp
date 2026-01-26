"""Tests for ha_whatsapp."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"url": "test", "api_key": "abc"}, entry_id="test_entry"
    )
    entry.add_to_hass(hass)

    # Mock the API client
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.stats = {"sent": 0, "failed": 0}
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.close = AsyncMock()

        # Setup using the config entries flow (not direct call)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        # Check that we have a dict with client and coordinator
        assert "client" in hass.data[DOMAIN][entry.entry_id]
        assert "coordinator" in hass.data[DOMAIN][entry.entry_id]
