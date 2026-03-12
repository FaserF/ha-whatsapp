"""Test the mark as read feature."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_MARK_AS_READ,
    CONF_URL,
    DOMAIN,
)


async def test_mark_as_read_enabled(hass: HomeAssistant) -> None:
    """Test that messages are marked as read when enabled."""
    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.close = AsyncMock()
    mock_instance.mark_as_read = MagicMock(return_value=None)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
        options={CONF_MARK_AS_READ: True},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_instance):
        # Capture the callback
        callback_capture: Any = None

        def register_side_effect(callback: Any) -> None:
            nonlocal callback_capture
            callback_capture = callback

        mock_instance.register_callback.side_effect = register_side_effect

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Simulate incoming message
        assert callback_capture is not None

        msg_data = {
            "sender": "123456789@s.whatsapp.net",
            "raw": {"key": {"id": "MSGID123"}},
            "content": "Hello",
        }

        callback_capture(msg_data)
        await hass.async_block_till_done()

        # Verify mark_as_read was called
        mock_instance.mark_as_read.assert_called_with(
            "123456789@s.whatsapp.net",
            "MSGID123",
        )


async def test_mark_as_read_disabled(hass: HomeAssistant) -> None:
    """Test that messages are NOT marked as read when disabled."""
    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.close = AsyncMock()
    mock_instance.mark_as_read = MagicMock(return_value=None)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
        options={CONF_MARK_AS_READ: False},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_instance):
        callback_capture: Any = None

        def register_side_effect(callback: Any) -> None:
            nonlocal callback_capture
            callback_capture = callback

        mock_instance.register_callback = MagicMock(side_effect=register_side_effect)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert callback_capture is not None

        msg_data = {
            "sender": "123456789@s.whatsapp.net",
            "raw": {"key": {"id": "MSGID123"}},
            "content": "Hello",
        }

        callback_capture(msg_data)
        await hass.async_block_till_done()

        # Verify mark_as_read was NOT called
        mock_instance.mark_as_read.assert_not_called()
