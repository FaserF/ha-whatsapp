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

    # Reset mock since it is shared across tests and might have been triggered before
    ir.async_create_issue.reset_mock()

    issue_registry = MagicMock()
    ir.async_get.return_value = issue_registry

    from homeassistant.exceptions import HomeAssistantError

    mock_client.get_stats = AsyncMock(
        side_effect=HomeAssistantError("Connection Failed")
    )
    mock_client.connect = AsyncMock(return_value=False)

    import pytest
    from homeassistant.helpers.update_coordinator import UpdateFailed

    # In a real setup, async_setup_entry would create the issue
    # We test the logic by calling a coordinator update that fails
    with pytest.raises(UpdateFailed):
        await data["coordinator"].async_refresh()

    # Verify issue creation was called
    # In this integration, the coordinator handles the error and async_setup_entry creates the issue  # noqa: E501
    # We need to make sure ir.async_create_issue was called.
    # Since we use the shared stub, ir.async_create_issue is a MagicMock.
    ir.async_create_issue.assert_called()


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

        # Call the send_message
        await entity.async_send_message(message="Hello", target=["555"])

        # Verify client was called
        mock_instance.send_message.assert_awaited_once_with(
            "555", "Hello", quoted_message_id=None, expiration=None
        )
