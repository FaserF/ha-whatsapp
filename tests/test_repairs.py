"""Tests for the WhatsApp repairs flow."""

from __future__ import annotations

import sys
import types
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""

    def _stub(name, **kwargs):
        mod = types.ModuleType(name)
        for k, v in kwargs.items():
            setattr(mod, k, v)
        sys.modules[name] = mod
        return mod

    # homeassistant.exceptions
    class HomeAssistantError(Exception):
        """Stub."""
    class ServiceValidationError(HomeAssistantError):
        """Stub."""
    _stub("homeassistant.exceptions", HomeAssistantError=HomeAssistantError, ServiceValidationError=ServiceValidationError)

    # homeassistant.core
    class ServiceCall:
        """Stub."""
        def __init__(self, domain, service, data=None, context=None):
            self.domain = domain
            self.service = service
            self.data = data or {}
    _stub("homeassistant.core", HomeAssistant=object, callback=lambda f: f, ServiceCall=ServiceCall)

    # homeassistant.const
    class Platform:
        """Stub."""
        BINARY_SENSOR = "binary_sensor"
        NOTIFY = "notify"
        SENSOR = "sensor"
    _stub("homeassistant.const", CONF_URL="url", CONF_API_KEY="api_key", Platform=Platform)

    # homeassistant.helpers.update_coordinator
    class _GenericBase:
        def __class_getitem__(cls, item): return cls
    class CoordinatorEntity(_GenericBase):
        def __init__(self, coordinator): self.coordinator = coordinator
    class DataUpdateCoordinator(_GenericBase):
        def __init__(self, *args, **kwargs): pass
    _stub("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=DataUpdateCoordinator, CoordinatorEntity=CoordinatorEntity, UpdateFailed=Exception)

    # homeassistant.helpers.config_validation
    _stub("homeassistant.helpers.config_validation", string=str, ensure_list=list)

    # homeassistant.helpers.entity_registry
    _stub("homeassistant.helpers.entity_registry", async_get=MagicMock(), async_entries_for_config_entry=MagicMock())

    # homeassistant.helpers.issue_registry
    ir_mod = _stub("homeassistant.helpers.issue_registry", async_get=MagicMock(), IssueSeverity=MagicMock(), async_delete_issue=MagicMock())

    # homeassistant.helpers.entity_platform
    _stub("homeassistant.helpers.entity_platform", AddEntitiesCallback=object)

    # homeassistant.helpers.typing
    _stub("homeassistant.helpers.typing", ConfigType=dict, DiscoveryInfoType=dict)

    # homeassistant.components.notify
    _stub("homeassistant.components.notify", ATTR_DATA="data", ATTR_MESSAGE="message", ATTR_TARGET="target", BaseNotificationService=object, NotifyEntity=object)

    # homeassistant.data_entry_flow
    class FlowResultType:
        FORM = "form"
        ABORT = "abort"
    _stub("homeassistant.data_entry_flow", FlowResultType=FlowResultType)

    # homeassistant.config_entries
    _stub("homeassistant.config_entries", ConfigEntry=object)

    # voluptuous
    vol_mod = _stub("voluptuous")
    vol_mod.Schema = lambda s, **_: s
    vol_mod.Optional = lambda *a, **_: a[0]
    vol_mod.Required = lambda *a, **_: a[0]
    vol_mod.Marker = object
    vol_mod.In = lambda x: x
    vol_mod.All = lambda *x: x[0]
    vol_mod.Length = lambda **x: x
    vol_mod.Coerce = lambda x: x

    ha = _stub("homeassistant")
    ha.core = sys.modules["homeassistant.core"]
    ha.exceptions = sys.modules["homeassistant.exceptions"]
    ha.const = sys.modules["homeassistant.const"]
    helpers = _stub("homeassistant.helpers")
    ha.helpers = helpers
    helpers.update_coordinator = sys.modules["homeassistant.helpers.update_coordinator"]
    helpers.config_validation = sys.modules["homeassistant.helpers.config_validation"]
    helpers.entity_registry = sys.modules["homeassistant.helpers.entity_registry"]
    helpers.issue_registry = sys.modules["homeassistant.helpers.issue_registry"]
    helpers.entity_platform = sys.modules["homeassistant.helpers.entity_platform"]
    helpers.typing = sys.modules["homeassistant.helpers.typing"]
    components = _stub("homeassistant.components")
    ha.components = components
    components.notify = sys.modules["homeassistant.components.notify"]

    # homeassistant.helpers.service
    _stub("homeassistant.helpers.service", async_register_admin_service=MagicMock())
    helpers.service = sys.modules["homeassistant.helpers.service"]

    # homeassistant.components.repairs
    repairs_mod = _stub("homeassistant.components.repairs")
    class RepairsFlow:
        def __init__(self):
            self.hass = None
        def async_show_form(self, step_id, data_schema=None, description_placeholders=None):
            return {"type": "form", "step_id": step_id}
        def async_create_entry(self, title, data):
            return {"type": "abort", "reason": "reconnect_successful"}
    class ConfirmRepairFlow(RepairsFlow): pass
    repairs_mod.RepairsFlow = RepairsFlow
    repairs_mod.ConfirmRepairFlow = ConfirmRepairFlow
    components.repairs = repairs_mod


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
        patch("custom_components.whatsapp.async_setup_entry", return_value=True)
    ):
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)

        from custom_components.whatsapp.repairs import WhatsAppRepairFlow
        flow = WhatsAppRepairFlow("connection_failed")
        flow.hass = hass

        # Proceed with confirm_reconnect
        from homeassistant.data_entry_flow import FlowResultType
        result = await flow.async_step_confirm({})

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconnect_successful"

        # Verify issue is cleared
        issue_registry.async_delete_issue.assert_called_with(DOMAIN, "connection_failed")

from custom_components.whatsapp.const import DOMAIN
