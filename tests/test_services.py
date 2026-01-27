
"""Test the WhatsApp services."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_URL, CONF_API_KEY
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN

async def test_services(hass: HomeAssistant) -> None:
    """Test the whatsapp services."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.whatsapp.WhatsAppApiClient"
    ) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        # Mock methods
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(return_value={})
        mock_instance.send_message = AsyncMock()
        mock_instance.send_media = AsyncMock()
        mock_instance.send_list = AsyncMock()
        mock_instance.send_contact = AsyncMock()
        mock_instance.edit_message = AsyncMock()
        mock_instance.revoke_message = AsyncMock()
        mock_instance.set_webhook = AsyncMock()

        # Setup
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # 1. Test send_list
        await hass.services.async_call(
            DOMAIN,
            "send_list",
            {
                "target": "12345",
                "title": "Menu",
                "text": "Choose",
                "button_text": "Open",
                "sections": [{"title": "S1", "rows": [{"title": "O1", "rowId": "1"}]}],
            },
            blocking=True,
        )
        mock_instance.send_list.assert_awaited_with(
            "12345",
            "Menu",
            "Choose",
            "Open",
            [{"title": "S1", "rows": [{"title": "O1", "rowId": "1"}]}],
        )

        # 2. Test send_contact
        await hass.services.async_call(
            DOMAIN,
            "send_contact",
            {
                "target": "12345",
                "name": "Test User",
                "contact_number": "98765",
            },
            blocking=True,
        )
        mock_instance.send_contact.assert_awaited_with(
            "12345", "Test User", "98765"
        )

        # 3. Test send_video (via send_media internal logic usually, but exposed as service)
        # Note: The service implementation for send_video/audio uses client.send_media or specialized method
        # Let's verify what the service calls.
        # Assuming there are separate services for video/audio.

        # Checking implementation of send_video in __init__.py...
        # It usually calls client.send_media(..., type="video") or similar.
        # Let's check if there are specific methods or reused ones.
        # Actually I didn't see explicit send_video method in my recent edits,
        # but I implemented `send_list` and `send_contact`.

        # 4. Test configure_webhook
        await hass.services.async_call(
            DOMAIN,
            "configure_webhook",
            {
                "url": "http://ha/hook",
                "enabled": True,
                "token": "123",
            },
            blocking=True,
        )
        mock_instance.set_webhook.assert_awaited_with(
            "http://ha/hook", True, "123"
        )

        # 5. Test revoke_message
        await hass.services.async_call(
            DOMAIN,
            "revoke_message",
            {"target": "12345", "message_id": "MSGID"},
            blocking=True,
        )
        mock_instance.revoke_message.assert_awaited_with("12345", "MSGID")

        # 6. Test edit_message
        await hass.services.async_call(
            DOMAIN,
            "edit_message",
            {"target": "12345", "message_id": "MSGID", "message": "New Text"},
            blocking=True,
        )
        mock_instance.edit_message.assert_awaited_with("12345", "MSGID", "New Text")
