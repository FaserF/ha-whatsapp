"""Test the HA WhatsApp diagnostics."""
from unittest.mock import MagicMock, patch
from homeassistant.core import HomeAssistant
from custom_components.whatsapp.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.whatsapp import diagnostics

async def test_diagnostics(hass: HomeAssistant) -> None:
    """Test diagnostics redaction."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "SENSITIVE_DATA", "other": "ok"})
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient.connect", return_value=True):
         assert await hass.config_entries.async_setup(entry.entry_id)

    result = await diagnostics.async_get_config_entry_diagnostics(hass, entry)

    assert result["entry"]["data"]["session"] == "**REDACTED**"
    assert result["entry"]["data"]["other"] == "ok"
