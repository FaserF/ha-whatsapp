"""Extended tests for WhatsApp services."""

from __future__ import annotations

from typing import Any
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


async def test_search_groups_service(hass: HomeAssistant) -> None:
    """Test that search_groups creates a persistent notification."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "test"},
    )
    mock_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.start_polling = AsyncMock()
    mock_client.set_webhook = AsyncMock()
    mock_client.get_groups = AsyncMock(
        return_value=[
            {"name": "Test Group", "id": "123@g.us", "participants": 5},
        ]
    )

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_client),
        patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord_cls,
        patch(
            "custom_components.whatsapp.get_client_for_account",
            return_value=mock_client,
        ),
    ):
        mock_coord = mock_coord_cls.return_value
        mock_coord.async_config_entry_first_refresh = AsyncMock()

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][mock_entry.entry_id]["client"] = mock_client

        real_async_call = hass.services.async_call

        async def spy_async_call(
            domain: str, service: str, service_data: Any = None, **kwargs: Any
        ) -> Any:
            if domain == "persistent_notification":
                mock_async_call(domain, service, service_data)
                return None
            return await real_async_call(
                domain, service, service_data=service_data, **kwargs
            )

        mock_async_call = MagicMock()
        with patch.object(hass.services, "async_call", side_effect=spy_async_call):
            await hass.services.async_call(
                DOMAIN,
                "search_groups",
                {"name_filter": "Test"},
                blocking=True,
            )
            mock_async_call.assert_called_once()
            args = mock_async_call.call_args.args
            assert args[0] == "persistent_notification"
            assert args[1] == "create"
            assert args[2]["title"] == "WhatsApp Group Search"
            assert "Found 1 group(s):" in args[2]["message"]
            assert "Test Group" in args[2]["message"]
            assert args[2]["notification_id"] == "whatsapp_group_search"


async def test_service_routing(hass: HomeAssistant) -> None:
    """Test that specifying 'account' routes correctly."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "test"},
    )
    mock_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.start_polling = AsyncMock()
    mock_client.set_webhook = AsyncMock()
    mock_client.send_message = AsyncMock()

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_client),
        patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord_cls,
        patch(
            "custom_components.whatsapp.get_client_for_account",
            return_value=mock_client,
        ) as mock_get_client,
    ):
        mock_coord = mock_coord_cls.return_value
        mock_coord.async_config_entry_first_refresh = AsyncMock()

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][mock_entry.entry_id]["client"] = mock_client

        await hass.services.async_call(
            DOMAIN,
            "send_message",
            {"target": "999", "message": "Hi", "account": "MyAccount"},
            blocking=True,
        )
        mock_get_client.assert_called_with(hass, "MyAccount")
        mock_client.send_message.assert_called_once_with(
            "999", "Hi", quoted_message_id=None, expiration=None
        )


async def test_send_buttons_normalization(hass: HomeAssistant) -> None:
    """Test send_buttons normalization."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "test"},
    )
    mock_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.start_polling = AsyncMock()
    mock_client.set_webhook = AsyncMock()
    mock_client.send_buttons = AsyncMock()

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_client),
        patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord_cls,
        patch(
            "custom_components.whatsapp.get_client_for_account",
            return_value=mock_client,
        ),
    ):
        mock_coord = mock_coord_cls.return_value
        mock_coord.async_config_entry_first_refresh = AsyncMock()

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][mock_entry.entry_id]["client"] = mock_client

        buttons = [{"id": "b1", "displayText": "Click"}]
        await hass.services.async_call(
            DOMAIN,
            "send_buttons",
            {"target": "123", "message": "Hello", "buttons": buttons},
            blocking=True,
        )

        mock_client.send_buttons.assert_awaited_with(
            "123", "Hello", buttons, None, quoted_message_id=None, expiration=None
        )


async def test_new_services_routing(hass: HomeAssistant) -> None:
    """Test routing for new group, chat, and contact services."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "test"},
    )
    mock_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.start_polling = AsyncMock()
    mock_client.set_webhook = AsyncMock()
    mock_client.create_group = AsyncMock(return_value={"id": "g1"})
    mock_client.add_group_participants = AsyncMock(return_value={})
    mock_client.star_message = AsyncMock(return_value={})
    mock_client.pin_message = AsyncMock(return_value={})
    mock_client.forward_message = AsyncMock(return_value={})
    mock_client.send_status = AsyncMock(return_value={})
    mock_client.block_contact = AsyncMock(return_value={})
    mock_client.mute_chat = AsyncMock(return_value={})

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient", return_value=mock_client),
        patch(
            "custom_components.whatsapp.WhatsAppDataUpdateCoordinator"
        ) as mock_coord_cls,
        patch(
            "custom_components.whatsapp.get_client_for_account",
            return_value=mock_client,
        ),
    ):
        mock_coord = mock_coord_cls.return_value
        mock_coord.async_config_entry_first_refresh = AsyncMock()

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        hass.data[DOMAIN][mock_entry.entry_id]["client"] = mock_client

        # Test create_group
        await hass.services.async_call(
            DOMAIN,
            "create_group",
            {"subject": "Test", "participants": ["123"]},
            blocking=True,
        )
        mock_client.create_group.assert_awaited_with("Test", ["123"])

        # Test star_message
        await hass.services.async_call(
            DOMAIN,
            "star_message",
            {"target": "123", "message_id": "m1"},
            blocking=True,
        )
        mock_client.star_message.assert_awaited_with("123", "m1", star=True)

        # Test pin_message
        await hass.services.async_call(
            DOMAIN,
            "pin_message",
            {"target": "123", "message_id": "m1", "duration": 3600},
            blocking=True,
        )
        mock_client.pin_message.assert_awaited_with("123", "m1", duration=3600)

        # Test send_status
        await hass.services.async_call(
            DOMAIN,
            "send_status",
            {"message": "Status update"},
            blocking=True,
        )
        mock_client.send_status.assert_awaited_with(
            message="Status update", url=None, caption=None
        )
