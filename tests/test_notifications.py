from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()


async def test_connection_lost_notification(data: dict[str, Any]) -> None:
    """Test the connection lost notification logic."""

    from homeassistant.helpers import issue_registry as ir

    issue_registry = MagicMock()
    ir.async_get.return_value = issue_registry

    from homeassistant.exceptions import HomeAssistantError

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(
            side_effect=HomeAssistantError("Connection Failed")
        )
        mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})

        # In a real setup, async_setup_entry would create the issue
        # We test the logic by calling a coordinator update that fails
        await data["coordinator"].async_refresh()

        # Verify issue creation was called
        # In this integration, the coordinator handles the error and async_setup_entry creates the issue
        # We need to make sure ir.async_create_issue was called.
        # Since we use the shared stub, ir.async_create_issue is a MagicMock.
        ir.async_create_issue.assert_called()


async def test_whatsapp_notification_entity() -> None:
    """Test the WhatsApp notification entity."""
    hass = MagicMock()

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

        # Call the send_message
        await entity.async_send_message(message="Hello", target=["555"])

        # Verify client was called
        mock_instance.send_message.assert_awaited_with(
            "555", "Hello", quoted_message_id=None
        )
