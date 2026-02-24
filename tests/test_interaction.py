"""Tests for WhatsApp interaction payloads (Quoting & Buttons)."""

from __future__ import annotations

import sys
import types
from contextlib import ExitStack
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Global handlers to capture service registrations
handlers: dict[str, Any] = {}


def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""

    def _stub(name: str, **kwargs: Any) -> types.ModuleType:
        if name in sys.modules:
            mod = sys.modules[name]
        else:
            mod = types.ModuleType(name)
            sys.modules[name] = mod
        for k, v in kwargs.items():
            if not hasattr(mod, k):
                setattr(mod, k, v)
        return mod

    # Create basic structure
    ha: Any = _stub("homeassistant")
    ha_helpers: Any = _stub("homeassistant.helpers")
    ha.helpers = ha_helpers

    if "homeassistant.exceptions" in sys.modules:
        ha_exceptions = sys.modules["homeassistant.exceptions"]
    else:

        class HomeAssistantError(Exception):
            """Stub."""

        class ServiceValidationError(HomeAssistantError):
            """Stub."""

        ha_exceptions = _stub(
            "homeassistant.exceptions",
            HomeAssistantError=HomeAssistantError,
            ServiceValidationError=ServiceValidationError,
        )
    ha.exceptions = ha_exceptions

    # Core
    class ServiceCall:
        """Stub."""

        def __init__(
            self,
            domain: str,
            service: str,
            service_data: dict[str, Any] | None = None,
        ) -> None:
            self.domain = domain
            self.service = service
            self.data = service_data or {}

    _stub("homeassistant.core", ServiceCall=ServiceCall)

    # Config Validation & Entity Registry
    _stub(
        "homeassistant.helpers.entity_registry",
        async_get=lambda _: MagicMock(),
    )

    # Const
    _stub(
        "homeassistant.const",
        CONF_URL="url",
        Platform=types.SimpleNamespace(
            BINARY_SENSOR="binary_sensor",
            NOTIFY="notify",
            SENSOR="sensor",
            SWITCH="switch",
        ),
        ATTR_ENTITY_ID="entity_id",
        ATTR_DATA="data",
        ATTR_MESSAGE="message",
        ATTR_TARGET="target",
        BaseNotificationService=object,
        NotifyEntity=object,
    )

    # Others
    class FlowResultType:
        FORM = "form"
        ABORT = "abort"
        CREATE_ENTRY = "create_entry"

    _stub("homeassistant.data_entry_flow", FlowResultType=FlowResultType)
    _stub("homeassistant.config_entries", ConfigEntry=object)

    # voluptuous
    vol_mod: Any = _stub("voluptuous")
    vol_mod.Schema = lambda s, **_: s
    vol_mod.Optional = MagicMock(side_effect=lambda x, **_: x)
    vol_mod.Required = MagicMock(side_effect=lambda x, **_: x)
    vol_mod.All = MagicMock(side_effect=lambda *a, **_: a[0])
    vol_mod.In = MagicMock(side_effect=lambda *a, **_: a[0])
    vol_mod.Coerce = MagicMock(side_effect=lambda *a, **_: a[0])
    vol_mod.Range = MagicMock(side_effect=lambda *a, **_: a[0])
    vol_mod.Any = MagicMock(side_effect=lambda *a, **_: a[1] if a[0] is None else a[0])
    vol_mod.Invalid = Exception
    vol_mod.SchemaError = Exception
    vol_mod.Marker = object


_build_ha_stub_modules()


@pytest.fixture(autouse=True)
def cleanup_handlers() -> Any:
    """Clear handlers and sys.modules between tests."""
    handlers.clear()
    to_del = [m for m in sys.modules if m.startswith("custom_components.whatsapp")]
    for m in to_del:
        del sys.modules[m]
    yield


def mock_register(
    domain: str,
    service: str,
    handler: Any,
    schema: Any = None,  # noqa: ARG001
) -> None:
    if domain == "whatsapp":
        handlers[service] = handler


def get_patches(stack: ExitStack) -> None:
    """Apply all required HA/voluptuous patches."""
    stack.enter_context(
        patch("homeassistant.helpers.config_validation.string", str, create=True)
    )
    stack.enter_context(
        patch("homeassistant.helpers.config_validation.ensure_list", list, create=True)
    )
    stack.enter_context(
        patch("homeassistant.helpers.config_validation.boolean", bool, create=True)
    )
    stack.enter_context(
        patch(
            "homeassistant.helpers.config_validation.match_all",
            lambda x: x,
            create=True,
        )
    )
    stack.enter_context(
        patch("voluptuous.All", side_effect=lambda *a, **_: a[0], create=True)
    )
    stack.enter_context(
        patch("voluptuous.Required", side_effect=lambda x, **_: x, create=True)
    )
    stack.enter_context(
        patch("voluptuous.Optional", side_effect=lambda x, **_: x, create=True)
    )
    stack.enter_context(patch("voluptuous.Schema", lambda s, **_: s, create=True))
    stack.enter_context(
        patch("voluptuous.Coerce", side_effect=lambda *a, **_: a[0], create=True)
    )
    stack.enter_context(
        patch("voluptuous.In", side_effect=lambda *a, **_: a[0], create=True)
    )
    stack.enter_context(
        patch("voluptuous.Range", side_effect=lambda *a, **_: a[0], create=True)
    )
    stack.enter_context(
        patch(
            "voluptuous.Any",
            side_effect=lambda *a, **_: a[1] if a[0] is None else a[0],
            create=True,
        )
    )
    stack.enter_context(patch("voluptuous.Marker", object, create=True))
    stack.enter_context(patch("voluptuous.Invalid", Exception, create=True))
    stack.enter_context(patch("voluptuous.SchemaError", Exception, create=True))


def setup_mock_session(stack: ExitStack) -> MagicMock:
    """Set up mocked aiohttp session."""
    import aiohttp

    mock_session = MagicMock(spec=aiohttp.ClientSession)

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.get = MagicMock(return_value=mock_response)

    # Async context manager for session
    stack.enter_context(
        patch("aiohttp.ClientSession", return_value=mock_instance_cm(mock_session))
    )
    return mock_session


def mock_instance_cm(instance: Any) -> MagicMock:
    """Mock for async context managers."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=instance)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


async def test_quoted_message_payload() -> None:
    """Verify that quotedMessageId is correctly sent in the payload."""
    hass = MagicMock()
    hass.services.async_register.side_effect = mock_register
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with ExitStack() as stack:
        get_patches(stack)
        from custom_components.whatsapp import async_setup_entry
        from custom_components.whatsapp.const import DOMAIN

        hass.data = {DOMAIN: {}}

        mock_session = setup_mock_session(stack)

        mock_entry = MagicMock()
        mock_entry.data = {"url": "http://localhost:8066", "api_key": "test_key"}
        mock_entry.options = {}
        mock_entry.entry_id = "test_entry"

        with patch(
            "custom_components.whatsapp.api.WhatsAppApiClient.start_session",
            return_value=None,
        ), patch(
            "custom_components.whatsapp.api.WhatsAppApiClient.mark_as_read",
            side_effect=lambda *a: None,
        ), patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord:
            mock_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            await async_setup_entry(hass, mock_entry)

        # Call service
        send_msg_service = handlers.get("send_message")
        assert send_msg_service is not None

        from homeassistant.core import ServiceCall

        call = ServiceCall(
            "whatsapp",
            "send_message",
            {"target": "123456789", "message": "Reply text", "quote": "MSG_ID_123"},
        )

        await send_msg_service(call)

        # Verify payload
        if mock_session.post.called:
            args = mock_session.post.call_args.args
            assert args[0] == "http://localhost:8066/send_message"
            payload = mock_session.post.call_args.kwargs["json"]
            assert payload["number"] == "123456789@s.whatsapp.net"
            assert payload["message"] == "Reply text"
            assert payload["quotedMessageId"] == "MSG_ID_123"


async def test_buttons_payload() -> None:
    """Verify that buttons are correctly sent in the payload."""
    hass = MagicMock()
    hass.services.async_register.side_effect = mock_register
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with ExitStack() as stack:
        get_patches(stack)
        from custom_components.whatsapp import async_setup_entry
        from custom_components.whatsapp.const import DOMAIN

        hass.data = {DOMAIN: {}}

        mock_session = setup_mock_session(stack)

        mock_entry = MagicMock()
        mock_entry.data = {"url": "http://localhost:8066", "api_key": "test_key"}
        mock_entry.options = {}
        mock_entry.entry_id = "test_entry"

        with patch(
            "custom_components.whatsapp.api.WhatsAppApiClient.start_session",
            return_value=None,
        ), patch(
            "custom_components.whatsapp.api.WhatsAppApiClient.mark_as_read",
            side_effect=lambda *a: None,
        ), patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord:
            mock_coord.return_value.async_config_entry_first_refresh = AsyncMock()
            await async_setup_entry(hass, mock_entry)

        # Call send_buttons service
        send_btn_service = handlers.get("send_buttons")
        assert send_btn_service is not None

        buttons = [
            {"id": "btn_1", "displayText": "Option 1"},
            {"id": "btn_2", "displayText": "Option 2"},
        ]
        from homeassistant.core import ServiceCall

        call = ServiceCall(
            "whatsapp",
            "send_buttons",
            {
                "target": "123456789",
                "message": "Choose one:",
                "buttons": buttons,
                "footer": "My Footer",
            },
        )

        await send_btn_service(call)

        # Verify payload
        if mock_session.post.called:
            args = mock_session.post.call_args.args
            assert args[0] == "http://localhost:8066/send_buttons"
            payload = mock_session.post.call_args.kwargs["json"]
            assert payload["number"] == "123456789@s.whatsapp.net"
            assert payload["message"] == "Choose one:"
            assert payload["buttons"] == buttons
            assert payload["footer"] == "My Footer"


async def test_telegram_buttons_normalization() -> None:
    """Verify Telegram inline_keyboard buttons are normalized correctly."""

    with ExitStack() as stack:
        get_patches(stack)

        from custom_components.whatsapp.api import WhatsAppApiClient
        from custom_components.whatsapp.notify import WhatsAppNotificationService

        mock_client = MagicMock(spec=WhatsAppApiClient)
        mock_client.send_buttons = AsyncMock()
        mock_client.ensure_jid = MagicMock(
            side_effect=lambda x: x if "@" in x else f"{x}@s.whatsapp.net"
        )

        service_instance = WhatsAppNotificationService(mock_client)

        # Telegram format
        inline_keyboard = [
            [
                {"text": "Yes", "callback_data": "click_yes"},
                {"text": "No", "callback_data": "click_no"},
            ]
        ]

        await service_instance.async_send_message(
            message="Alarm?",
            target=["123456789"],
            data={"inline_keyboard": inline_keyboard},
        )

        # Check if send_buttons was called on the client with normalized buttons
        expected_normalized = [
            {"id": "click_yes", "displayText": "Yes"},
            {"id": "click_no", "displayText": "No"},
        ]
        mock_client.send_buttons.assert_awaited_once()
        args = mock_client.send_buttons.call_args.args
        assert args[0] == "123456789"
        assert args[1] == "Alarm?"
        assert args[2] == expected_normalized
