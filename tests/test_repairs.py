from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

from custom_components.whatsapp.const import DOMAIN

_build_ha_stub_modules()


async def test_repair_flow_connection_failure() -> None:
    """Test the repair flow when a connection failure occurs."""
    hass = MagicMock()

    from homeassistant.helpers import issue_registry as ir

    issue_registry = MagicMock()
    ir.async_get.return_value = issue_registry

    # Initialize the repair flow
    # We test the class directly
    from custom_components.whatsapp.repairs import WhatsAppRepairFlow

    flow = WhatsAppRepairFlow("connection_failed")
    flow.hass = hass
    assert flow.issue_id == "connection_failed"

    # Test the start step
    from homeassistant.data_entry_flow import FlowResultType

    result = await flow.async_step_init()
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "confirm"


async def test_repair_flow_reconnect_success() -> None:
    """Test that the repair flow successfully reconnects and clears the issue."""
    hass = MagicMock()

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
        patch("custom_components.whatsapp.async_setup_entry", return_value=True),
        patch(
            "custom_components.whatsapp.repairs.ir.async_delete_issue"
        ) as mock_delete_issue,
    ):
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)

        from custom_components.whatsapp.repairs import WhatsAppRepairFlow

        flow = WhatsAppRepairFlow("connection_failed")
        flow.hass = hass

        # Proceed with confirm_reconnect
        from homeassistant.data_entry_flow import FlowResultType

        result = await flow.async_step_confirm({})

        assert result["type"] == FlowResultType.CREATE_ENTRY

        # Verify issue is cleared
        mock_delete_issue.assert_called_with(hass, DOMAIN, "connection_failed")


async def test_repair_flow_session_expired_triggers_reauth() -> None:
    """Test that repairing session_expired triggers a reauth flow for the entry."""
    hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.unique_id = "49176123456"
    mock_entry.data = {
        "session_id": "default",
        "host": "http://localhost:8066",
        "api_key": "123",
    }
    hass.config_entries.async_entries.return_value = [mock_entry]

    with patch(
        "custom_components.whatsapp.repairs.ir.async_delete_issue"
    ) as mock_delete_issue:
        from custom_components.whatsapp.repairs import WhatsAppRepairFlow

        flow = WhatsAppRepairFlow("session_expired")
        flow.hass = hass

        from homeassistant.data_entry_flow import FlowResultType

        result = await flow.async_step_confirm({})

        assert result["type"] == FlowResultType.CREATE_ENTRY
        mock_delete_issue.assert_called_with(hass, DOMAIN, "session_expired")
        assert hass.async_create_task.called


async def test_coordinator_repair_suppressed_when_is_connecting() -> None:
    """Test that connection_error_baileys repair is suppressed while isConnecting is True."""
    hass = MagicMock()
    mock_client = MagicMock()
    mock_client.ensure_polling = MagicMock()
    mock_client.get_health = AsyncMock(return_value={"status": "connected"})
    mock_client.get_stats = AsyncMock(
        return_value={
            "connected": False,
            "isConnecting": True,
            "sent": 0,
            "failed": 0,
        }
    )
    mock_client.get_status = AsyncMock(
        return_value={"connected": False, "isConnecting": True}
    )
    mock_client.get_dashboard = AsyncMock(return_value={})
    mock_client.get_moderation_config = AsyncMock(return_value={"data": {}})
    mock_client.get_telegram_config = AsyncMock(return_value={"data": {}})
    mock_client.get_auto_responder_config = AsyncMock(return_value={"data": {}})

    mock_entry = MagicMock()
    mock_entry.options = {}

    from custom_components.whatsapp.coordinator import (
        WhatsAppDataUpdateCoordinator,
    )

    coord = WhatsAppDataUpdateCoordinator(hass, mock_client, mock_entry)

    with (
        patch("homeassistant.helpers.issue_registry.async_create_issue") as mock_create,
        patch(
            "homeassistant.helpers.issue_registry.async_delete_issue"
        ) as _mock_delete,
    ):
        await coord._async_update_data()
        for call in mock_create.call_args_list:
            assert call[0][2] != "connection_error_baileys"


async def test_coordinator_repair_debounced_on_first_disconnected_cycle() -> None:
    """Test that connection_error_baileys repair is debounced on the first disconnected cycle."""
    hass = MagicMock()
    mock_client = MagicMock()
    mock_client.ensure_polling = MagicMock()
    mock_client.get_health = AsyncMock(return_value={"status": "connected"})
    mock_client.get_stats = AsyncMock(
        return_value={
            "connected": False,
            "isConnecting": False,
            "sent": 0,
            "failed": 0,
        }
    )
    mock_client.get_status = AsyncMock(
        return_value={"connected": False, "isConnecting": False}
    )
    mock_client.get_dashboard = AsyncMock(return_value={})
    mock_client.get_moderation_config = AsyncMock(return_value={"data": {}})
    mock_client.get_telegram_config = AsyncMock(return_value={"data": {}})
    mock_client.get_auto_responder_config = AsyncMock(return_value={"data": {}})

    mock_entry = MagicMock()
    mock_entry.options = {}

    from custom_components.whatsapp.coordinator import (
        WhatsAppDataUpdateCoordinator,
    )

    coord = WhatsAppDataUpdateCoordinator(hass, mock_client, mock_entry)

    with (
        patch("homeassistant.helpers.issue_registry.async_create_issue") as mock_create,
        patch(
            "homeassistant.helpers.issue_registry.async_delete_issue"
        ) as _mock_delete,
    ):
        # Cycle 1: Disconnected once — debounced (cycle count = 1 < 2)
        await coord._async_update_data()
        assert not any(
            call[0][2] == "connection_error_baileys"
            for call in mock_create.call_args_list
        )

        # Cycle 2: Disconnected twice — issue created (cycle count = 2 >= 2)
        await coord._async_update_data()
        assert any(
            call[0][2] == "connection_error_baileys"
            for call in mock_create.call_args_list
        )
