"""Extended tests for WhatsApp services."""

from __future__ import annotations

import sys
import types
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Global handlers to capture service registrations
handlers = {}

def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""

    def _stub(name, **kwargs):
        if name in sys.modules:
            mod = sys.modules[name]
        else:
            mod = types.ModuleType(name)
            sys.modules[name] = mod
        for k, v in kwargs.items():
            setattr(mod, k, v)
        return mod

    # Create basic structure
    ha = _stub("homeassistant")
    ha_helpers = _stub("homeassistant.helpers")
    ha.helpers = ha_helpers

    # Exceptions
    class HomeAssistantError(Exception):
        """Stub."""
    class ServiceValidationError(HomeAssistantError):
        """Stub."""
    ha_exceptions = _stub("homeassistant.exceptions", HomeAssistantError=HomeAssistantError, ServiceValidationError=ServiceValidationError)
    ha.exceptions = ha_exceptions

    # Core
    class ServiceCall:
        """Stub."""
        def __init__(self, domain, service, data=None, context=None):
            self.domain = domain
            self.service = service
            self.data = data or {}
    ha_core = _stub("homeassistant.core", HomeAssistant=object, callback=lambda f: f, ServiceCall=ServiceCall)
    ha.core = ha_core

    # Const
    class Platform:
        """Stub."""
        BINARY_SENSOR = "binary_sensor"
        NOTIFY = "notify"
        SENSOR = "sensor"
    ha_const = _stub("homeassistant.const", CONF_URL="url", CONF_API_KEY="api_key", Platform=Platform)
    ha.const = ha_const

    # Config Validation - Minimal stub, will patch properly in tests
    cv = _stub("homeassistant.helpers.config_validation")
    ha_helpers.config_validation = cv

    # Update Coordinator
    class _GenericBase:
        def __class_getitem__(cls, item): return cls
    class CoordinatorEntity(_GenericBase):
        def __init__(self, coordinator): self.coordinator = coordinator
    class DataUpdateCoordinator(_GenericBase):
        def __init__(self, *args, **kwargs): pass
    uc = _stub("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=DataUpdateCoordinator, CoordinatorEntity=CoordinatorEntity, UpdateFailed=Exception)
    ha_helpers.update_coordinator = uc

    # Registries
    ha_helpers.entity_registry = _stub("homeassistant.helpers.entity_registry", async_get=MagicMock(), async_entries_for_config_entry=MagicMock())
    ha_helpers.issue_registry = _stub("homeassistant.helpers.issue_registry", async_get=MagicMock(), IssueSeverity=MagicMock())
    ha_helpers.entity_platform = _stub("homeassistant.helpers.entity_platform", AddEntitiesCallback=object)
    ha_helpers.typing = _stub("homeassistant.helpers.typing", ConfigType=dict, DiscoveryInfoType=dict)
    ha_helpers.service = _stub("homeassistant.helpers.service", async_register_admin_service=MagicMock())

    # Components
    ha_comp = _stub("homeassistant.components")
    ha.components = ha_comp
    ha_comp.notify = _stub("homeassistant.components.notify", ATTR_DATA="data", ATTR_MESSAGE="message", ATTR_TARGET="target", BaseNotificationService=object, NotifyEntity=object)

    # Others
    class FlowResultType:
        FORM = "form"
        ABORT = "abort"
    _stub("homeassistant.data_entry_flow", FlowResultType=FlowResultType)
    _stub("homeassistant.config_entries", ConfigEntry=object)

    # voluptuous - robust stub
    vol_mod = _stub("voluptuous")
    vol_mod.Schema = lambda s, **_: s
    vol_mod.Optional = MagicMock()
    vol_mod.Required = MagicMock()
    vol_mod.All = lambda *a, **_: a[0]
    vol_mod.In = lambda *a, **_: a[0]
    vol_mod.Coerce = lambda *a, **_: a[0]
    vol_mod.Range = lambda *a, **_: a[0]
    vol_mod.Any = lambda *a, **_: a[0]
    vol_mod.Invalid = Exception
    vol_mod.SchemaError = Exception
    vol_mod.Marker = object


_build_ha_stub_modules()


@pytest.fixture(autouse=True)
def cleanup_handlers():
    """Clear handlers and sys.modules between tests."""
    handlers.clear()

    # Force reload of custom_components    # Force reload of custom_components to ensure patches are applied fresh
    to_del = [m for m in sys.modules if m.startswith("custom_components.whatsapp")]
    for m in to_del:
        del sys.modules[m]

    yield

def mock_register(domain, service, handler, schema=None):
    if domain == "whatsapp":
        handlers[service] = handler

def get_patches(stack: ExitStack):
    """Apply all required patches to the stack."""
    # cv patches
    stack.enter_context(patch("homeassistant.helpers.config_validation.string", str, create=True))
    stack.enter_context(patch("homeassistant.helpers.config_validation.ensure_list", list, create=True))
    stack.enter_context(patch("homeassistant.helpers.config_validation.boolean", bool, create=True))
    stack.enter_context(patch("homeassistant.helpers.config_validation.match_all", lambda x: x, create=True))

    # voluptuous patches
    stack.enter_context(patch("voluptuous.All", lambda *a, **_: a[0], create=True))
    stack.enter_context(patch("voluptuous.Required", MagicMock(), create=True))
    stack.enter_context(patch("voluptuous.Optional", MagicMock(), create=True))
    stack.enter_context(patch("voluptuous.Schema", lambda s, **_: s, create=True))
    stack.enter_context(patch("voluptuous.Coerce", lambda *a, **_: a[0], create=True))
    stack.enter_context(patch("voluptuous.In", lambda *a, **_: a[0], create=True))
    stack.enter_context(patch("voluptuous.Range", lambda *a, **_: a[0], create=True))
    stack.enter_context(patch("voluptuous.Any", lambda *a, **_: a[0], create=True))
    stack.enter_context(patch("voluptuous.Marker", object, create=True))
    stack.enter_context(patch("voluptuous.Invalid", Exception, create=True))
    stack.enter_context(patch("voluptuous.SchemaError", Exception, create=True))

async def test_search_groups_service() -> None:
    """Test that search_groups creates a persistent notification."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.services.async_register.side_effect = mock_register
    hass.services.has_service.return_value = False
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with ExitStack() as stack:
        get_patches(stack)

        from custom_components.whatsapp import async_setup_entry
        from custom_components.whatsapp.const import DOMAIN

        with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
            mock_instance = mock_client_cls.return_value
            mock_instance.connect = AsyncMock(return_value=True)
            mock_instance.start_polling = AsyncMock()
            mock_instance.set_webhook = AsyncMock()
            mock_instance.get_groups = AsyncMock(return_value=[
                {"name": "Test Group", "id": "123@g.us", "participants": 5},
            ])

            mock_entry = MagicMock()
            mock_entry.data = {"url": "http://localhost:8066", "api_key": "test"}
            mock_entry.options = {}
            mock_entry.entry_id = "test_entry"
            hass.data = {DOMAIN: {}}

            with patch("custom_components.whatsapp.WhatsAppDataUpdateCoordinator") as mock_coord_cls:
                mock_coord = mock_coord_cls.return_value
                mock_coord.async_config_entry_first_refresh = AsyncMock()

                await async_setup_entry(hass, mock_entry)

            search_service = handlers.get("search_groups")
            assert search_service is not None

            from homeassistant.core import ServiceCall
            call = ServiceCall("whatsapp", "search_groups", {"name_filter": "Test"})

            with patch("custom_components.whatsapp.get_client_for_account", return_value=mock_instance):
                await search_service(call)

                hass.services.async_call.assert_called_once()
                args = hass.services.async_call.call_args.args
                assert args[0] == "persistent_notification"
                assert args[1] == "create"
                assert "Found 1 group(s)" in args[2]["message"]

async def test_service_routing() -> None:
    """Test that specifying 'account' routes correctly."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.services.async_register.side_effect = mock_register
    hass.services.has_service.return_value = False
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with ExitStack() as stack:
        get_patches(stack)
        from custom_components.whatsapp import async_setup_entry
        from custom_components.whatsapp.const import DOMAIN
        hass.data = {DOMAIN: {}}

        with (
            patch("custom_components.whatsapp.get_client_for_account") as mock_get_client,
            patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
            patch("custom_components.whatsapp.WhatsAppDataUpdateCoordinator") as mock_coord_cls
        ):
            mock_instance = mock_client_cls.return_value
            mock_instance.connect = AsyncMock(return_value=True)
            mock_instance.start_polling = AsyncMock()
            mock_instance.set_webhook = AsyncMock()

            mock_coord = mock_coord_cls.return_value
            mock_coord.async_config_entry_first_refresh = AsyncMock()

            mock_entry = MagicMock()
            mock_entry.data = {"url": "http://localhost:8066", "api_key": "test"}
            mock_entry.options = {}
            mock_entry.entry_id = "test_entry"

            await async_setup_entry(hass, mock_entry)

            send_msg_service = handlers.get("send_message")
            assert send_msg_service is not None

            mock_client = MagicMock()
            mock_client.send_message = AsyncMock()
            mock_get_client.return_value = mock_client

            from homeassistant.core import ServiceCall
            call = ServiceCall("whatsapp", "send_message", {"target": "999", "message": "Hi", "account": "MyAccount"})

            await send_msg_service(call)

            mock_get_client.assert_called_with(hass, "MyAccount")
            mock_client.send_message.assert_called_once()

async def test_send_buttons_normalization() -> None:
    """Test send_buttons normalization."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.services.async_register.side_effect = mock_register
    hass.services.has_service.return_value = False
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with ExitStack() as stack:
        get_patches(stack)
        from custom_components.whatsapp import async_setup_entry
        from custom_components.whatsapp.const import DOMAIN
        hass.data = {DOMAIN: {}}

        with (
            patch("custom_components.whatsapp.get_client_for_account") as mock_get_client,
            patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
            patch("custom_components.whatsapp.WhatsAppDataUpdateCoordinator") as mock_coord_cls
        ):
            mock_instance = mock_client_cls.return_value
            mock_instance.connect = AsyncMock(return_value=True)
            mock_instance.start_polling = AsyncMock()
            mock_instance.set_webhook = AsyncMock()

            mock_coord = mock_coord_cls.return_value
            mock_coord.async_config_entry_first_refresh = AsyncMock()

            mock_entry = MagicMock()
            mock_entry.data = {"url": "http://localhost:8066", "api_key": "test"}
            mock_entry.options = {}
            mock_entry.entry_id = "test_entry"

            await async_setup_entry(hass, mock_entry)

            send_btn_service = handlers.get("send_buttons")
            assert send_btn_service is not None

            mock_client = MagicMock()
            mock_client.send_buttons = AsyncMock()
            mock_get_client.return_value = mock_client

            from homeassistant.core import ServiceCall
            buttons = [{"id": "b1", "displayText": "Click"}]
            call = ServiceCall("whatsapp", "send_buttons", {"target": "123", "message": "Hello", "buttons": buttons})

            await send_btn_service(call)

            mock_client.send_buttons.assert_awaited_with(
                "123", "Hello", buttons, None, quoted_message_id=None
            )
