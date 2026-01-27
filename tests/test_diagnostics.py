"""Test the HA WhatsApp diagnostics."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp import diagnostics
from custom_components.whatsapp.const import DOMAIN


async def test_diagnostics(hass: HomeAssistant) -> None:
    """Test diagnostics redaction."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "test", CONF_API_KEY: "SENSITIVE_DATA", "other": "ok"},
    )
    entry.add_to_hass(hass)

    with (patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,):
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock()
        mock_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(entry.entry_id)

        result = await diagnostics.async_get_config_entry_diagnostics(hass, entry)

        assert result["entry"]["data"]["session"] == "**REDACTED**"
        assert result["entry"]["data"]["other"] == "ok"
        assert result["client_connected"] is True
