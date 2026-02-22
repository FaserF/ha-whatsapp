from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.whatsapp.const import DOMAIN

from ha_stubs import _build_ha_stub_modules

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

    from homeassistant.helpers import issue_registry as ir

    issue_registry = MagicMock()
    ir.async_get.return_value = issue_registry

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
        patch("custom_components.whatsapp.async_setup_entry", return_value=True),
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
        issue_registry.async_delete_issue.assert_called_with(
            DOMAIN, "connection_failed"
        )
