"""Test the WhatsApp services."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import (
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)


async def test_services(hass: HomeAssistant) -> None:
    """Test the whatsapp services."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        # Mock methods - Unified list
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.start_polling = AsyncMock()
        mock_instance.get_stats = AsyncMock(return_value={})
        mock_instance.send_message = AsyncMock()
        mock_instance.send_image = AsyncMock()
        mock_instance.send_poll = AsyncMock()
        mock_instance.send_location = AsyncMock()
        mock_instance.send_reaction = AsyncMock()
        mock_instance.send_buttons = AsyncMock()
        mock_instance.set_presence = AsyncMock()
        mock_instance.send_list = AsyncMock()
        mock_instance.send_contact = AsyncMock()
        mock_instance.edit_message = AsyncMock()
        mock_instance.revoke_message = AsyncMock()
        mock_instance.set_webhook = AsyncMock()
        mock_instance.send_document = AsyncMock()
        mock_instance.send_video = AsyncMock()
        mock_instance.send_audio = AsyncMock()

        # Setup
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # 1. Test send_message
        await hass.services.async_call(
            DOMAIN,
            "send_message",
            {"target": "12345", "message": "Hello"},
            blocking=True,
        )
        mock_instance.send_message.assert_awaited_with(
            "12345", "Hello", quoted_message_id=None
        )

        # 2. Test send_poll
        await hass.services.async_call(
            DOMAIN,
            "send_poll",
            {
                "target": "12345",
                "question": "Q?",
                "options": ["A", "B"],
            },
            blocking=True,
        )
        mock_instance.send_poll.assert_awaited_with(
            "12345", "Q?", ["A", "B"], quoted_message_id=None
        )

        # 3. Test send_image
        await hass.services.async_call(
            DOMAIN,
            "send_image",
            {
                "target": "12345",
                "url": "http://img.jpg",
                "caption": "Cap",
            },
            blocking=True,
        )
        mock_instance.send_image.assert_awaited_with(
            "12345", "http://img.jpg", "Cap", quoted_message_id=None
        )

        # 4. Test send_location
        await hass.services.async_call(
            DOMAIN,
            "send_location",
            {
                "target": "12345",
                "latitude": 1.0,
                "longitude": 2.0,
                "name": "Loc",
            },
            blocking=True,
        )
        mock_instance.send_location.assert_awaited_with(
            "12345", 1.0, 2.0, "Loc", None, quoted_message_id=None
        )

        # 5. Test send_reaction
        await hass.services.async_call(
            DOMAIN,
            "send_reaction",
            {"target": "12345", "message_id": "ID", "reaction": "Emoji"},
            blocking=True,
        )
        mock_instance.send_reaction.assert_awaited_with("12345", "Emoji", "ID")

        # 6. Test send_buttons
        await hass.services.async_call(
            DOMAIN,
            "send_buttons",
            {
                "target": "12345",
                "message": "Msg",
                "buttons": [{"id": "1", "displayText": "Btn"}],
            },
            blocking=True,
        )
        mock_instance.send_buttons.assert_awaited_with(
            "12345",
            "Msg",
            [{"id": "1", "displayText": "Btn"}],
            None,
            quoted_message_id=None,
        )

        # 7. Test update_presence
        await hass.services.async_call(
            DOMAIN,
            "update_presence",
            {"target": "12345", "presence": "composing"},
            blocking=True,
        )
        mock_instance.set_presence.assert_awaited_with("12345", "composing")

        # 8. Test send_list
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

        # 9. Test send_contact
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
        mock_instance.send_contact.assert_awaited_with("12345", "Test User", "98765")

        # 10. Test configure_webhook
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
        mock_instance.set_webhook.assert_awaited_with("http://ha/hook", True, "123")

        # 11. Test revoke_message
        await hass.services.async_call(
            DOMAIN,
            "revoke_message",
            {"target": "12345", "message_id": "MSGID"},
            blocking=True,
        )
        mock_instance.revoke_message.assert_awaited_with("12345", "MSGID")

        # 12. Test edit_message
        await hass.services.async_call(
            DOMAIN,
            "edit_message",
            {"target": "12345", "message_id": "MSGID", "message": "New Text"},
            blocking=True,
        )
        mock_instance.edit_message.assert_awaited_with("12345", "MSGID", "New Text")

        # 13. Test send_document
        await hass.services.async_call(
            DOMAIN,
            "send_document",
            {
                "target": "12345",
                "url": "http://doc.pdf",
                "file_name": "My Doc.pdf",
                "message": "Caption",
            },
            blocking=True,
        )
        mock_instance.send_document.assert_awaited_with(
            "12345", "http://doc.pdf", "My Doc.pdf", "Caption", quoted_message_id=None
        )

        # 14. Test send_video
        await hass.services.async_call(
            DOMAIN,
            "send_video",
            {
                "target": "12345",
                "url": "http://vid.mp4",
                "message": "Caption",
            },
            blocking=True,
        )
        mock_instance.send_video.assert_awaited_with(
            "12345", "http://vid.mp4", "Caption", quoted_message_id=None
        )

        # 15. Test send_audio
        await hass.services.async_call(
            DOMAIN,
            "send_audio",
            {
                "target": "12345",
                "url": "http://audio.mp3",
                "ptt": True,
            },
            blocking=True,
        )
        mock_instance.send_audio.assert_awaited_with(
            "12345", "http://audio.mp3", True, quoted_message_id=None
        )
