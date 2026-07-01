"""Tests for the passkey steps in config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402

from custom_components.whatsapp.config_flow import ConfigFlow  # noqa: E402
from custom_components.whatsapp.const import CONF_API_KEY, CONF_URL  # noqa: E402


async def test_passkey_warning_step_aborts_by_default(hass: HomeAssistant) -> None:
    """Test that passkey warning step aborts by default if no continue."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.discovery_info = {"host": "http://localhost:8066"}

    # Form view
    res = await flow.async_step_passkey_warning(user_input=None)
    assert res["type"] == "form"
    assert res["step_id"] == "passkey_warning"

    # Abort submit
    res = await flow.async_step_passkey_warning(
        user_input={"continue_with_passkey": False}
    )
    assert res["type"] == "abort"
    assert res["reason"] == "passkey_remove_required"


async def test_passkey_warning_step_goes_to_waiting_with_continue(
    hass: HomeAssistant,
) -> None:
    """Test that passkey warning step redirects to waiting step with continue."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.discovery_info = {
        CONF_URL: "http://localhost:8066",
        CONF_API_KEY: "mock",
    }
    flow.client = MagicMock()
    flow.client.get_passkey_status = AsyncMock(return_value={"isConnected": True})
    flow.client.get_stats = AsyncMock(return_value={"my_number": "12345"})
    flow.client.get_chats = AsyncMock(return_value={"total_chats": 10})
    flow.client.close = AsyncMock()

    with patch("asyncio.sleep"):
        res = await flow.async_step_passkey_warning(
            user_input={"continue_with_passkey": True}
        )
        assert res["type"] == "create_entry"


async def test_passkey_waiting_step_success(hass: HomeAssistant) -> None:
    """Test that passkey waiting step succeeds when isConnected is True."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.discovery_info = {
        CONF_URL: "http://localhost:8066",
        CONF_API_KEY: "mock",
    }
    flow.client = MagicMock()
    flow.client.get_passkey_status = AsyncMock(return_value={"isConnected": True})
    flow.client.get_stats = AsyncMock(return_value={"my_number": "12345"})
    flow.client.get_chats = AsyncMock(return_value={"total_chats": 10})
    flow.client.close = AsyncMock()

    with patch("asyncio.sleep"):
        res = await flow.async_step_passkey_waiting()
        assert res["type"] == "create_entry"
        assert res["title"] == "WhatsApp (12345)"


async def test_passkey_waiting_step_timeout(hass: HomeAssistant) -> None:
    """Test that passkey waiting step times out when passkey is no longer active."""
    flow = ConfigFlow()
    flow.hass = hass
    flow.client = MagicMock()
    flow.client.get_passkey_status = AsyncMock(
        return_value={
            "isConnected": False,
            "passkeyWaiting": False,
            "passkeyDetected": False,
        }
    )

    with patch("asyncio.sleep"):
        res = await flow.async_step_passkey_waiting()
        assert res["type"] == "form"
        assert res["step_id"] == "passkey_waiting"
        assert res["errors"] == {"base": "passkey_timeout"}
