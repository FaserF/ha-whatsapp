"""Tests for ha_whatsapp."""
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.whatsapp import async_setup_entry
from custom_components.whatsapp.const import DOMAIN


async def test_setup_entry(hass):
    """Test setting up the entry."""
    entry = MagicMock()
    entry.data = {"session": "test"}
    entry.entry_id = "test_entry"

    # Mock the API client entirely so we don't need Playwright installed
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        # Mock register_callback as it's called during setup
        mock_instance.register_callback = MagicMock()

        assert await async_setup_entry(hass, entry)
        assert DOMAIN in hass.data
