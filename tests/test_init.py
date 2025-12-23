"""Tests for ha_whatsapp."""
from unittest.mock import MagicMock, patch
import pytest
from custom_components.ha_whatsapp import async_setup_entry
from custom_components.ha_whatsapp.const import DOMAIN

async def test_setup_entry(hass):
    """Test setting up the entry."""
    entry = MagicMock()
    entry.data = {"session": "test"}
    entry.entry_id = "test_entry"

    with patch("custom_components.ha_whatsapp.WhatsAppApiClient.connect", return_value=True):
        assert await async_setup_entry(hass, entry)
        assert DOMAIN in hass.data
