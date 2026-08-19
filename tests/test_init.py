"""Tests for ha_whatsapp."""

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import ha_stubs

ha_stubs._build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_SELF_MESSAGES,
    CONF_URL,
    DOMAIN,
    EVENT_MESSAGE_RECEIVED,
    EVENT_MESSAGE_SENT,
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
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 0, "failed": 0, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
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
    """Ensure whatsapp_message_sent is fired on fromMe with metadata."""
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
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 0, "failed": 0, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        # This message was NOT sent by HA — loop guard must pass it through
        mock_instance.was_sent_by_ha = MagicMock(return_value=False)
        callback: Callable[[dict[str, Any]], None] | None = None

        def reg_cb(cb: Callable[[dict[str, Any]], None]) -> None:
            nonlocal callback
            callback = cb

        mock_instance.register_callback = MagicMock(side_effect=reg_cb)
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
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

        # 1. Test: Disabled (Default) - Fires whatsapp_message_sent only
        with patch.object(hass.bus, "async_fire") as mock_fire:
            assert callback is not None, "Callback was not registered!"
            callback(self_message_payload)
            assert mock_fire.call_count == 1
            call_event, call_data = mock_fire.call_args[0]
            assert call_event == EVENT_MESSAGE_SENT
            assert call_data["from"] == "me"
            assert call_data["to"] == "123456789@s.whatsapp.net"
            assert call_data["sender"] == "me"
            assert call_data["recipient"] == "123456789@s.whatsapp.net"
            assert call_data["recipient_number"] == "123456789"
            assert call_data["from_me"] is True

        # 2. Test: Enabled (self_messages: True) - Fires both sent and received
        new_options = entry.options.copy()
        new_options[CONF_SELF_MESSAGES] = True
        await hass.config_entries.async_update_entry(entry, options=new_options)
        await hass.async_block_till_done()

        with patch.object(hass.bus, "async_fire") as mock_fire:
            assert callback is not None, "Callback was not registered!"
            callback(self_message_payload)
            assert mock_fire.call_count == 2
            events_fired = [call[0][0] for call in mock_fire.call_args_list]
            assert EVENT_MESSAGE_SENT in events_fired
            assert EVENT_MESSAGE_RECEIVED in events_fired


async def test_loop_guard_blocks_ha_echo(hass: HomeAssistant) -> None:
    """Verify echoes of HA-sent messages never fire any event."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "test", CONF_API_KEY: "abc"},
        options={CONF_SELF_MESSAGES: True},  # Worst-case: guard must still hold
        entry_id="test_entry_loop",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 0, "failed": 0, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        # Simulate: HA sent this message ID — it IS a known echo
        mock_instance.was_sent_by_ha = MagicMock(return_value=True)
        callback: Callable[[dict[str, Any]], None] | None = None

        def reg_cb(cb: Callable[[dict[str, Any]], None]) -> None:
            nonlocal callback
            callback = cb

        mock_instance.register_callback = MagicMock(side_effect=reg_cb)
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
        mock_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        echo_payload = {
            "content": "Diagnostic message echoed back",
            "sender": "123456789@s.whatsapp.net",
            "is_group": False,
            "raw": {
                "key": {
                    "remoteJid": "123456789@s.whatsapp.net",
                    "fromMe": True,
                    "id": "HA_SENT_MSG_001",
                }
            },
        }

        with patch.object(hass.bus, "async_fire") as mock_fire:
            assert callback is not None
            callback(echo_payload)
            # Loop guard must drop the echo entirely — no events at all
            assert mock_fire.call_count == 0, (
                "Loop guard failed: HA echo should not fire any event, "
                f"but fired: {[c[0][0] for c in mock_fire.call_args_list]}"
            )
