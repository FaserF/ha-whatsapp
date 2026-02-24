"""Test the expiration parameter for WhatsApp services."""

from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import (
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)


async def test_send_message_with_expiration(hass: HomeAssistant) -> None:
    """Test send_message with expiration parameter."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_message = AsyncMock()

    with patch(
        "custom_components.whatsapp.WhatsAppApiClient", return_value=mock_instance
    ):

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Call send_message with expiration
        await hass.services.async_call(
            DOMAIN,
            "send_message",
            {"target": "12345", "message": "Expires", "expiration": 86400},
            blocking=True,
        )

        mock_instance.send_message.assert_awaited_with(
            "12345", "Expires", quoted_message_id=None, expiration=86400
        )


async def test_send_image_with_expiration(hass: HomeAssistant) -> None:
    """Test send_image with expiration parameter."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_image = AsyncMock()

    with patch(
        "custom_components.whatsapp.WhatsAppApiClient", return_value=mock_instance
    ):

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Call send_image with expiration
        await hass.services.async_call(
            DOMAIN,
            "send_image",
            {"target": "12345", "url": "http://img.jpg", "expiration": 3600},
            blocking=True,
        )

        mock_instance.send_image.assert_awaited_with(
            "12345", "http://img.jpg", None, quoted_message_id=None, expiration=3600
        )
