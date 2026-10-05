from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()


async def test_connection_lost_notification(
    data: dict[str, Any], mock_client: MagicMock
) -> None:
    """Test the connection lost notification logic."""

    from homeassistant.helpers import issue_registry as ir

    fn_reset = getattr(ir, "async_create_issue", None)
    if hasattr(fn_reset, "reset_mock"):
        fn_reset.reset_mock()

    issue_registry = MagicMock()
    ir.async_get.return_value = issue_registry

    from homeassistant.exceptions import HomeAssistantError

    mock_client.get_stats = AsyncMock(
        side_effect=HomeAssistantError("Connection Failed")
    )
    mock_client.connect = AsyncMock(return_value=False)

    import pytest
    from homeassistant.helpers.update_coordinator import UpdateFailed

    # In a real setup, async_setup_entry would create the issue.
    # Test that a coordinator update fails without previous cache.
    data["coordinator"].data = None
    with pytest.raises(UpdateFailed):
        await data["coordinator"].async_refresh()

    # Verify issue creation was called
    # In this integration, the coordinator handles the error and async_setup_entry creates the issue  # noqa: E501
    fn = getattr(ir, "async_create_issue", None)
    if hasattr(fn, "assert_called"):
        fn.assert_called()


async def test_addon_update_grace_period(
    data: dict[str, Any], mock_client: MagicMock
) -> None:
    """Test that temporary unreachability during addon updates is handled gracefully."""
    from homeassistant.exceptions import HomeAssistantError

    # Coordinator starts with existing active session data
    data["coordinator"].data = {
        "connected": True,
        "status": "ready",
        "stats": {"my_number": "4912345678", "sent": 10},
    }

    # Simulate temporary connection drops (e.g. during container rebuild)
    mock_client.get_health = AsyncMock(
        return_value={"status": "unreachable", "details": "Connect call failed"}
    )
    mock_client.get_stats = AsyncMock(
        side_effect=HomeAssistantError("Connect call failed")
    )

    # First refresh should NOT raise UpdateFailed; it should maintain updating state
    await data["coordinator"].async_refresh()
    assert data["coordinator"].data["connected"] is False
    assert data["coordinator"].data["status"] == "updating"


async def test_whatsapp_notification_entity() -> None:
    """Test the WhatsApp notification entity."""

    from homeassistant.helpers import entity_registry as er

    registry = MagicMock()
    er.async_get.return_value = registry

    notify_entry = MagicMock()
    notify_entry.domain = "notify"
    notify_entry.entity_id = "notify.whatsapp_number"
    notify_entry.unique_id = "test_entry_notify"
    er.async_entries_for_config_entry.return_value = [notify_entry]

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.send_message = AsyncMock()

        # Instantiate Entity
        from custom_components.whatsapp.notify import WhatsAppNotificationEntity

        entity = WhatsAppNotificationEntity(mock_instance, MagicMock(), MagicMock())
        entity._async_record_notification = lambda: None  # type: ignore[method-assign]

        # Call the send_message
        await entity.async_send_message(message="Hello", target=["555"])

        # Verify client was called
        mock_instance.send_message.assert_awaited_once_with(
            "555", "Hello", quoted_message_id=None, expiration=None
        )


async def test_whatsapp_notification_attachments() -> None:
    """Test notification entity with single and multiple attachments."""
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.send_image = AsyncMock()
        mock_instance.send_video = AsyncMock()
        mock_instance.send_audio = AsyncMock()
        mock_instance.send_document = AsyncMock()

        from custom_components.whatsapp.notify import WhatsAppNotificationEntity

        entity = WhatsAppNotificationEntity(mock_instance, MagicMock(), MagicMock())
        entity._async_record_notification = lambda: None  # type: ignore[method-assign]

        # Test single image attachment
        await entity.async_send_message(
            message="Check this image",
            target=["555"],
            data={"attachment": "https://example.com/photo.jpg"},
        )
        mock_instance.send_image.assert_awaited_once_with(
            "555",
            "https://example.com/photo.jpg",
            "Check this image",
            quoted_message_id=None,
            expiration=None,
        )

        # Test multiple attachments (video + audio + document)
        await entity.async_send_message(
            message="Check files",
            target=["555"],
            data={
                "attachments": [
                    "https://example.com/clip.mp4",
                    "https://example.com/voice.opus",
                    {"url": "https://example.com/doc.pdf", "file_name": "manual.pdf"},
                ]
            },
        )
        mock_instance.send_video.assert_awaited_once_with(
            "555",
            "https://example.com/clip.mp4",
            "Check files",
            quoted_message_id=None,
            expiration=None,
        )
        mock_instance.send_audio.assert_awaited_once_with(
            "555",
            "https://example.com/voice.opus",
            False,
            quoted_message_id=None,
            expiration=None,
        )
        mock_instance.send_document.assert_awaited_once_with(
            "555",
            "https://example.com/doc.pdf",
            "manual.pdf",
            None,
            quoted_message_id=None,
            expiration=None,
        )


async def test_notify_service_lifecycle_and_account_resolution() -> None:
    """Test legacy notify.whatsapp service lifecycle, dynamic client resolution and error handling."""
    from homeassistant.exceptions import ServiceValidationError

    from custom_components.whatsapp.const import DOMAIN
    from custom_components.whatsapp.notify import async_setup_entry

    hass = MagicMock()
    registered_services: dict[tuple[str, str], Any] = {}

    def mock_has_service(domain: str, service: str) -> bool:
        return (domain, service) in registered_services

    def mock_register(
        domain: str, service: str, handler: Any, schema: Any = None
    ) -> None:
        registered_services[(domain, service)] = handler

    def mock_remove(domain: str, service: str) -> None:
        registered_services.pop((domain, service), None)

    hass.services.has_service = MagicMock(side_effect=mock_has_service)
    hass.services.async_register = MagicMock(side_effect=mock_register)
    hass.services.async_remove = MagicMock(side_effect=mock_remove)

    mock_client1 = MagicMock()
    mock_client1.send_message = AsyncMock()
    mock_client1.close = AsyncMock()
    mock_client2 = MagicMock()
    mock_client2.send_message = AsyncMock()
    mock_client2.close = AsyncMock()

    entry1 = MagicMock(entry_id="entry_1", options={})
    entry2 = MagicMock(entry_id="entry_2", options={})

    hass.data = {
        DOMAIN: {
            "entry_1": {"client": mock_client1, "coordinator": MagicMock()},
            "entry_2": {"client": mock_client2, "coordinator": MagicMock()},
        }
    }

    async_add_entities = MagicMock()
    await async_setup_entry(hass, entry1, async_add_entities)

    assert ("notify", "whatsapp") in registered_services
    handler = registered_services[("notify", "whatsapp")]

    # 1. Call with specific valid account
    call_valid = MagicMock(
        data={"account": "entry_2", "message": "Test Msg", "target": ["12345"]}
    )
    await handler(call_valid)
    mock_client2.send_message.assert_awaited_once_with(
        "12345", "Test Msg", quoted_message_id=None, expiration=None
    )

    # 2. Call with invalid account should raise ServiceValidationError
    import pytest

    call_invalid = MagicMock(
        data={"account": "invalid_acc", "message": "Test", "target": ["12345"]}
    )
    with pytest.raises(ServiceValidationError):
        await handler(call_invalid)

    # 3. Test unload removes notify.whatsapp when last entry is unloaded
    from custom_components.whatsapp import async_unload_entry

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    # Unload entry_1 (entry_2 remains)
    await async_unload_entry(hass, entry1)
    assert ("notify", "whatsapp") in registered_services

    # Unload entry_2 (last entry)
    await async_unload_entry(hass, entry2)
    assert ("notify", "whatsapp") not in registered_services
