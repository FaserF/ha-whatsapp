"""Tests for ha_whatsapp."""

from unittest.mock import AsyncMock, MagicMock, patch
from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import (
    CONF_API_KEY,
    CONF_SELF_MESSAGES,
    CONF_URL,
    DOMAIN,
)


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "test", CONF_API_KEY: "abc"},
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    # Mock the API client
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock()
        mock_instance.close = AsyncMock()

        # Setup using the config entries flow (not direct call)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        # Check that we have a dict with client and coordinator
        assert "client" in hass.data[DOMAIN][entry.entry_id]
        assert "coordinator" in hass.data[DOMAIN][entry.entry_id]


async def test_self_message_received(hass: HomeAssistant) -> None:
    """Test that a self-message (fromMe: True) is filtered by default but processed when enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "test", CONF_API_KEY: "abc"},
        options={CONF_SELF_MESSAGES: False},  # Explicitly disabled (default)
        entry_id="test_entry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        callback = None

        def reg_cb(cb):
            nonlocal callback
            callback = cb

        mock_instance.register_callback = MagicMock(side_effect=reg_cb)
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock()
        mock_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        self_message_payload = {
            "content": "Hello to myself",
            "sender": "123456789@s.whatsapp.net",
            "sender_number": "123456789",
            "is_group": False,
            "raw": {
                "key": {
                    "remoteJid": "123456789@s.whatsapp.net",
                    "fromMe": True,
                    "id": "ABC123XYZ",
                }
            },
        }

        # 1. Test: Disabled (Default)
        with patch.object(hass.bus, "async_fire") as mock_fire:
            callback(self_message_payload)
            mock_fire.assert_not_called()

        # 2. Test: Enabled
        new_options = entry.options.copy()
        new_options[CONF_SELF_MESSAGES] = True
        await hass.config_entries.async_update_entry(entry, options=new_options)
        await hass.async_block_till_done()

        with patch("homeassistant.core.Bus.async_fire") as mock_fire:
            callback(self_message_payload)
            mock_fire.assert_called_once()
            args, _ = mock_fire.call_args
            assert args[0] == "whatsapp_message_received"
            assert args[1]["raw"]["key"]["fromMe"] is True
