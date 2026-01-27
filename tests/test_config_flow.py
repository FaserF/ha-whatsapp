from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import (
    CONF_API_KEY,
    CONF_MARK_AS_READ,
    CONF_POLLING_INTERVAL,
    CONF_RETRY_ATTEMPTS,
    CONF_URL,
    DOMAIN,
)


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

    # Test the submit step - need to mock all API calls
    with (
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.connect",
            new_callable=AsyncMock,
            side_effect=[True, False, True],
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.start_session",
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_qr_code",
            new_callable=AsyncMock,
            return_value="data:image/png;base64,mockqr",
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.close",
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.whatsapp.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        # Submit user step
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://localhost:8066", "api_key": "123"},
        )
        # After user step, we go to scan step
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] == "scan"

        # Submit scan step (simulate user clicked submit after scanning)
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "WhatsApp"
    # The config flow now generates a session_id
    assert result3["data"]["session_id"]
    assert result3["data"][CONF_URL] == "http://localhost:8066"
    assert result3["data"]["api_key"] == "123"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    # Create a mock entry
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="WhatsApp",
        data={"session": "mock", CONF_API_KEY: "mock_key"},
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
    assert result2["data"] == {
        "debug_payloads": True,
        CONF_POLLING_INTERVAL: 5,
        "mask_sensitive_data": False,
        CONF_MARK_AS_READ: True,
        CONF_RETRY_ATTEMPTS: 2,
    }
