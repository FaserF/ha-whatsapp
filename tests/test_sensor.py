"""Test the HA WhatsApp stats sensors."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN


async def test_stats_sensors(hass: HomeAssistant) -> None:
    """Test the statistics sensors."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "mock"})
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        # Initial stats
        mock_instance.stats = {"sent": 5, "failed": 1}
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Enable entities
        registry = er.async_get(hass)
        registry.async_update_entity("sensor.whatsapp_messages_sent", disabled_by=None)
        registry.async_update_entity(
            "sensor.whatsapp_messages_failed", disabled_by=None
        )
        await hass.async_block_till_done()
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        # Check sensors
        state_sent = hass.states.get("sensor.whatsapp_messages_sent")
        state_failed = hass.states.get("sensor.whatsapp_messages_failed")

        assert state_sent
        assert state_sent.state == "5"
        assert state_failed
        assert state_failed.state == "1"

        # Update stats
        mock_instance.stats = {"sent": 12, "failed": 3}

        # Trigger coordinator refresh
        data = hass.data[DOMAIN][entry.entry_id]
        await data["coordinator"].async_refresh()
        await hass.async_block_till_done()

        state_sent = hass.states.get("sensor.whatsapp_messages_sent")
        state_failed = hass.states.get("sensor.whatsapp_messages_failed")

        assert state_sent.state == "12"
        assert state_failed.state == "3"
