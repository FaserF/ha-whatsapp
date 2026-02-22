"""Extended tests for WhatsApp services."""

from __future__ import annotations

import sys
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()


@pytest.fixture
def service_handlers():
    """Fixture to capture service registrations."""
    handlers = {}

    def mock_register(domain, service, handler, schema=None):
        if domain == "whatsapp":
            handlers[service] = handler

    return handlers, mock_register


@pytest.fixture(autouse=True)
def cleanup_modules():
    """Clear sys.modules between tests to ensure fresh patches."""
    # Force reload of custom_components to ensure patches are applied fresh
    to_del = [m for m in sys.modules if m.startswith("custom_components.whatsapp")]
    for m in to_del:
        del sys.modules[m]
    yield


def get_patches(stack: ExitStack):
    """Apply all required patches to the stack."""
    # cv patches
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


async def test_search_groups_service(service_handlers) -> None:
    """Test that search_groups creates a persistent notification."""
    handlers, mock_register = service_handlers
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
            mock_instance.get_groups = AsyncMock(
                return_value=[
                    {"name": "Test Group", "id": "123@g.us", "participants": 5},
                ]
            )

            mock_entry = MagicMock()
            mock_entry.data = {"url": "http://localhost:8066", "api_key": "test"}
            mock_entry.options = {}
            mock_entry.entry_id = "test_entry"
            hass.data = {DOMAIN: {}}

            with patch(
                "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
            ) as mock_coord_cls:
                mock_coord = mock_coord_cls.return_value
                mock_coord.async_config_entry_first_refresh = AsyncMock()

                await async_setup_entry(hass, mock_entry)

            search_service = handlers.get("search_groups")
            assert search_service is not None

            from homeassistant.core import ServiceCall

            call = ServiceCall("whatsapp", "search_groups", {"name_filter": "Test"})

            with patch(
                "custom_components.whatsapp.get_client_for_account",
                return_value=mock_instance,
            ):
                await search_service(call)

                hass.services.async_call.assert_called_once()
                args = hass.services.async_call.call_args.args
                assert args[0] == "persistent_notification"
                assert args[1] == "create"
                assert "Found 1 group(s)" in args[2]["message"]


async def test_service_routing(service_handlers) -> None:
    """Test that specifying 'account' routes correctly."""
    handlers, mock_register = service_handlers
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
            patch(
                "custom_components.whatsapp.get_client_for_account"
            ) as mock_get_client,
            patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
            patch(
                "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
            ) as mock_coord_cls,
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

            call = ServiceCall(
                "whatsapp",
                "send_message",
                {"target": "999", "message": "Hi", "account": "MyAccount"},
            )

            await send_msg_service(call)

            mock_get_client.assert_called_with(hass, "MyAccount")
            mock_client.send_message.assert_called_once()


async def test_send_buttons_normalization(service_handlers) -> None:
    """Test send_buttons normalization."""
    handlers, mock_register = service_handlers
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
            patch(
                "custom_components.whatsapp.get_client_for_account"
            ) as mock_get_client,
            patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
            patch(
                "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
            ) as mock_coord_cls,
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
            call = ServiceCall(
                "whatsapp",
                "send_buttons",
                {"target": "123", "message": "Hello", "buttons": buttons},
            )

            await send_btn_service(call)

            mock_client.send_buttons.assert_awaited_with(
                "123", "Hello", buttons, None, quoted_message_id=None
            )
