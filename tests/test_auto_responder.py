"""Test Auto Responder functionality in HA WhatsApp."""

from unittest.mock import AsyncMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

import pytest  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.api import WhatsAppApiClient  # noqa: E402
from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_api_auto_responder_methods() -> None:
    """Test API client Auto Responder methods."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="secret_token")

    with (
        patch("aiohttp.ClientSession.get") as mock_get,
        patch("aiohttp.ClientSession.post") as mock_post,
    ):
        # Mock GET config response
        mock_resp_get = AsyncMock()
        mock_resp_get.status = 200
        mock_resp_get.json = AsyncMock(
            return_value={
                "success": True,
                "data": {
                    "enabled": True,
                    "start_time": "2026-08-20T08:00",
                    "end_time": "2026-08-30T18:00",
                    "direct_only": True,
                    "once_per_contact": True,
                    "message_template": "Hello {sender_name}!",
                    "is_active": True,
                    "seen_count": 5,
                },
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_resp_get

        config = await client.get_auto_responder_config()
        assert config["success"] is True
        assert config["data"]["enabled"] is True
        assert config["data"]["is_active"] is True

        # Mock POST update response
        mock_resp_post = AsyncMock()
        mock_resp_post.status = 200
        mock_resp_post.json = AsyncMock(
            return_value={
                "success": True,
                "data": {"enabled": False, "is_active": False},
            }
        )
        mock_post.return_value.__aenter__.return_value = mock_resp_post

        set_res = await client.set_auto_responder_config(enabled=False)
        assert set_res["success"] is True

        reset_seen_res = await client.reset_auto_responder_seen()
        assert reset_seen_res["success"] is True


@pytest.mark.asyncio
async def test_auto_responder_switch_and_services(hass: HomeAssistant) -> None:
    """Test Auto Responder switch entity and service calls."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.start_polling = AsyncMock()
        mock_instance.get_stats = AsyncMock(return_value={"connected": True})
        mock_instance.get_status = AsyncMock(return_value={"connected": True})
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.get_moderation_config = AsyncMock(return_value={"data": {}})
        mock_instance.get_telegram_store = AsyncMock(return_value={"data": {}})
        mock_instance.get_telegram_config = AsyncMock(return_value={"data": {}})
        mock_instance.get_auto_responder_config = AsyncMock(
            return_value={
                "data": {
                    "enabled": True,
                    "is_active": True,
                    "start_time": "2026-08-20T08:00",
                    "end_time": "2026-08-30T18:00",
                    "direct_only": True,
                    "once_per_contact": True,
                    "seen_count": 3,
                }
            }
        )
        mock_instance.set_auto_responder_config = AsyncMock(
            return_value={"success": True}
        )
        mock_instance.set_auto_responder_enabled = AsyncMock(
            return_value={"success": True}
        )
        mock_instance.reset_auto_responder_seen = AsyncMock(
            return_value={"success": True}
        )
        mock_instance.session_id = "default"
        mock_instance.stats = {
            "sent": 1,
            "failed": 0,
            "my_number": "12345",
            "version": "1.0",
        }

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        from custom_components.whatsapp.switch import WhatsAppAutoResponderSwitch

        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        switch = WhatsAppAutoResponderSwitch(coordinator, entry)

        assert switch.is_on is True
        attrs = switch.extra_state_attributes
        assert attrs["is_active"] is True
        assert attrs["start_time"] == "2026-08-20T08:00"
        assert attrs["end_time"] == "2026-08-30T18:00"
        assert attrs["direct_only"] is True
        assert attrs["once_per_contact"] is True
        assert attrs["seen_count"] == 3

        # Test turn on / turn off
        await switch.async_turn_off()
        mock_instance.set_auto_responder_enabled.assert_called_with(False)

        await switch.async_turn_on()
        mock_instance.set_auto_responder_config.assert_called()
        call_kwargs = mock_instance.set_auto_responder_config.call_args.kwargs
        assert call_kwargs["enabled"] is True
        assert "T" in call_kwargs["start_time"]
        assert call_kwargs["end_time"] == ""

        # Test set_auto_responder service
        await hass.services.async_call(
            DOMAIN,
            "set_auto_responder",
            {
                "enabled": True,
                "start_time": "2026-08-20T10:00",
                "direct_only": True,
                "once_per_contact": True,
                "message_template": "Away currently",
            },
            blocking=True,
        )
        mock_instance.set_auto_responder_config.assert_called_with(
            enabled=True,
            start_time="2026-08-20T10:00",
            end_time=None,
            direct_only=True,
            once_per_contact=True,
            message_template="Away currently",
        )

        # Test reset_auto_responder_seen service
        await hass.services.async_call(
            DOMAIN,
            "reset_auto_responder_seen",
            {},
            blocking=True,
        )
        mock_instance.reset_auto_responder_seen.assert_called_once()
