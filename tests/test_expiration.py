"""Test the expiration parameter for WhatsApp services."""

from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.const import (  # noqa: E402
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
    mock_instance.get_stats = AsyncMock(return_value={"connected": True})
    mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
    mock_instance.get_status = AsyncMock(return_value={"connected": True})
    mock_instance.get_dashboard = AsyncMock(return_value={})
    mock_instance.get_chats = AsyncMock(return_value={"total_chats": 0, "groups": []})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_message = AsyncMock()

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_client_cls.return_value = mock_instance
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][entry.entry_id]["client"] = mock_instance

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
    mock_instance.get_stats = AsyncMock(return_value={"connected": True})
    mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
    mock_instance.get_status = AsyncMock(return_value={"connected": True})
    mock_instance.get_dashboard = AsyncMock(return_value={})
    mock_instance.get_chats = AsyncMock(return_value={"total_chats": 0, "groups": []})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_image = AsyncMock()

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_client_cls.return_value = mock_instance
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][entry.entry_id]["client"] = mock_instance

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


async def test_client_send_message_payload_with_expiration() -> None:
    """Verify that WhatsAppApiClient includes expiration in its outgoing JSON payload."""
    from custom_components.whatsapp.api import WhatsAppApiClient

    client = WhatsAppApiClient("http://localhost:8066", "mock_key")
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"status": "sent", "id": "TEST_123"})

    mock_post_cm = MagicMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        await client._send_message_internal(
            "12345@s.whatsapp.net",
            "This will disappear",
            expiration=604800,
        )

        mock_session.post.assert_called_once()
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["expiration"] == 604800
        assert kwargs["json"]["number"] == "12345@s.whatsapp.net"
        assert kwargs["json"]["message"] == "This will disappear"


async def test_send_location_with_expiration(hass: HomeAssistant) -> None:
    """Test send_location with expiration parameter."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={"connected": True})
    mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
    mock_instance.get_status = AsyncMock(return_value={"connected": True})
    mock_instance.get_dashboard = AsyncMock(return_value={})
    mock_instance.get_chats = AsyncMock(return_value={"total_chats": 0, "groups": []})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_location = AsyncMock()

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_client_cls.return_value = mock_instance
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][entry.entry_id]["client"] = mock_instance

        await hass.services.async_call(
            DOMAIN,
            "send_location",
            {
                "target": "12345",
                "latitude": 52.52,
                "longitude": 13.405,
                "expiration": 604800,
            },
            blocking=True,
        )

        mock_instance.send_location.assert_awaited_with(
            "12345",
            52.52,
            13.405,
            None,
            None,
            quoted_message_id=None,
            expiration=604800,
        )


async def test_send_document_with_expiration(hass: HomeAssistant) -> None:
    """Test send_document with expiration parameter."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    from custom_components.whatsapp.api import WhatsAppApiClient

    mock_instance = MagicMock(spec=WhatsAppApiClient)
    mock_instance.connect = AsyncMock(return_value=True)
    mock_instance.get_stats = AsyncMock(return_value={"connected": True})
    mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
    mock_instance.get_status = AsyncMock(return_value={"connected": True})
    mock_instance.get_dashboard = AsyncMock(return_value={})
    mock_instance.get_chats = AsyncMock(return_value={"total_chats": 0, "groups": []})
    mock_instance.start_polling = AsyncMock()
    mock_instance.start_session = MagicMock(return_value=None)
    mock_instance.send_document = AsyncMock()

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_client_cls.return_value = mock_instance
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][entry.entry_id]["client"] = mock_instance

        await hass.services.async_call(
            DOMAIN,
            "send_document",
            {
                "target": "12345",
                "url": "http://example.com/doc.pdf",
                "filename": "doc.pdf",
                "expiration": 86400,
            },
            blocking=True,
        )

        mock_instance.send_document.assert_awaited_with(
            "12345",
            "http://example.com/doc.pdf",
            None,
            None,
            quoted_message_id=None,
            expiration=86400,
            mimetype=None,
        )
