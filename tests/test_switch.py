"""Tests for the WhatsApp switch platform."""

from unittest.mock import AsyncMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)


async def test_switch_entities_setup(hass: HomeAssistant) -> None:
    """Test setup of master switch entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 10, "failed": 2, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_status = AsyncMock(return_value={"connected": True})
        mock_instance.start_polling = AsyncMock()
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.get_moderation_config = AsyncMock(return_value={"data": {}})
        mock_instance.get_telegram_store = AsyncMock(return_value={"data": {}})
        mock_instance.stats = {
            "sent": 10,
            "failed": 2,
            "my_number": "123456789",
            "version": "1.0.0",
        }
        mock_instance.session_id = "default"

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
