"""Tests for ha_whatsapp."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp import async_setup_entry
from custom_components.whatsapp.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"session": "test"}, entry_id="test_entry"
    )
    entry.add_to_hass(hass)

    # Mock the API client entirely so we don't need Playwright installed
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        # Mock register_callback as it's called during setup
        mock_instance.register_callback = MagicMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
    ) as mock_forward:
        assert await async_setup_entry(hass, entry)
        assert DOMAIN in hass.data
        assert mock_forward.call_count == 1
