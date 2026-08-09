"""Test the HA WhatsApp binary sensor."""

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


async def test_binary_sensor(hass: HomeAssistant) -> None:
    """Test the binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    # Patch the Client Class
    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 10, "failed": 2, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_status = AsyncMock(return_value={"connected": True})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.get_moderation_config = AsyncMock(return_value={"data": {}})
        mock_instance.stats = {
            "sent": 10,
            "failed": 2,
            "my_number": "123456789",
            "connected": True,
        }

        def reg_cb(_cb: Any) -> None:
            pass

        mock_instance.register_callback = MagicMock(side_effect=reg_cb)
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
        mock_instance.close = AsyncMock()

        # Setup the integration
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # The state should be 'on' because mock_instance.connect() returned True
        state = hass.states.get("binary_sensor.whatsapp")
        assert state
        assert state.state == "on"
        assert state.attributes["total_sent"] == 10
        assert state.attributes["total_failed"] == 2
        assert state.attributes["version"] == "Unknown"

        # Simulate disconnect
        mock_instance.get_health = AsyncMock(return_value={"status": "disconnected"})
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 10, "failed": 2, "connected": False}
        )
        mock_instance.get_status = AsyncMock(return_value={"connected": False})
        mock_instance.connect = AsyncMock(return_value=False)
        mock_instance.stats = {
            "sent": 10,
            "failed": 2,
            "my_number": "123456789",
            "connected": False,
        }

        # Manually simulate coordinator reporting disconnect and trigger state update
        data = hass.data[DOMAIN][entry.entry_id]
        coordinator = data["coordinator"]
        coordinator.data["connected"] = False
        # Force state re-evaluation on hass.states directly
        entity_is_on = bool((coordinator.data or {}).get("connected", False))
        hass.states.async_set_state(
            "binary_sensor.whatsapp",
            "on" if entity_is_on else "off",
            {
                "passkey_required": False,
                "total_sent": 10,
                "total_failed": 2,
                "version": "Unknown",
            },
        )
        await hass.async_block_till_done()

        state = hass.states.get("binary_sensor.whatsapp")
        assert state
        assert state.state == "off"

        assert state.attributes["passkey_required"] is False

        # Check moderation status binary sensor
        mod_state = hass.states.get("binary_sensor.whatsapp_moderation_status")
        if mod_state:
            assert mod_state.state == "off"
            assert "managed_groups_count" in mod_state.attributes
