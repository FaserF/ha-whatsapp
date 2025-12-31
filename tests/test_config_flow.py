from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.whatsapp.const import DOMAIN


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    # Mock the API client's get_qr_code to avoid Playwright dependency in simple tests
    with patch(
        "custom_components.whatsapp.WhatsAppApiClient.get_qr_code",
        new_callable=AsyncMock,
    ) as mock_get_qr:
        mock_get_qr.return_value = "data:image/png;base64,mockqr"

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    # Test the submit step
    with patch(
        "custom_components.whatsapp.WhatsAppApiClient.connect",
        return_value=True,
    ), patch(
        "custom_components.whatsapp.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"confirmed": True},  # Simulating user clicking submit
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "WhatsApp"
    assert result2["data"] == {"session": "mock_session_string"}
    assert len(mock_setup_entry.mock_calls) == 1


from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    # Create a mock entry
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="WhatsApp",
        data={"session": "mock"},
        source="user",
        options={},
        unique_id="1234",
        entry_id="test_entry_id",
        minor_version=1,
    )
    # We must add the entry to hass to test options
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"debug_payloads": True},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"] == {"debug_payloads": True}
