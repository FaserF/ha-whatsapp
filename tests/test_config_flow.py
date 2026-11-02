from unittest.mock import AsyncMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant import config_entries  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.data_entry_flow import FlowResultType  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_DEBUG_PAYLOADS,
    CONF_MARK_AS_READ,
    CONF_MASK_SENSITIVE_DATA,
    CONF_POLLING_INTERVAL,
    CONF_RETRY_ATTEMPTS,
    CONF_SELF_MESSAGES,
    CONF_SESSION_ID,
    CONF_URL,
    CONF_WHITELIST,
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
            {CONF_URL: "http://localhost:8066", CONF_API_KEY: "123"},
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
    assert result3["data"][CONF_SESSION_ID]
    assert result3["data"][CONF_URL] == "http://localhost:8066"
    assert result3["data"][CONF_API_KEY] == "123"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test the re-authentication flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="49176123456",
        data={
            CONF_SESSION_ID: "default",
            CONF_URL: "http://localhost:8066",
            CONF_API_KEY: "old_key",
        },
        entry_id="test_reauth_entry",
    )
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_entries.return_value = [mock_entry]

    from custom_components.whatsapp.config_flow import ConfigFlow

    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {
        "source": config_entries.SOURCE_REAUTH,
        "entry_id": mock_entry.entry_id,
        "unique_id": mock_entry.unique_id,
    }
    from unittest.mock import MagicMock

    flow.async_update_reload_and_abort = MagicMock(
        return_value={"type": FlowResultType.ABORT, "reason": "reauth_successful"}
    )

    with (
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.connect",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_stats",
            new_callable=AsyncMock,
            return_value={"my_number": "49176123456", "connected": True},
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_chats",
            new_callable=AsyncMock,
            return_value={"total_chats": 10, "initial_chats_received": True},
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
    ):
        result = await flow.async_step_reauth(dict(mock_entry.data))
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        # Submit reauth_confirm
        result2 = await flow.async_step_reauth_confirm({})
        assert result2["type"] == FlowResultType.FORM
        assert result2["step_id"] in ("scan", "already_connected")

        if result2["step_id"] == "already_connected":
            result3 = await flow.async_step_already_connected(
                {"action": "use_existing"}
            )
        else:
            result3 = await flow.async_step_scan({})

        assert result3["type"] == FlowResultType.ABORT
        assert result3["reason"] == "reauth_successful"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    # Create a mock entry
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="WhatsApp",
        data={CONF_SESSION_ID: "mock", CONF_API_KEY: "mock_key"},
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
        user_input={CONF_DEBUG_PAYLOADS: True},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_DEBUG_PAYLOADS: True,
        CONF_POLLING_INTERVAL: 5,
        CONF_MASK_SENSITIVE_DATA: False,
        CONF_MARK_AS_READ: True,
        CONF_RETRY_ATTEMPTS: 2,
        CONF_WHITELIST: "",
        CONF_SELF_MESSAGES: False,
    }


async def test_zeroconf_abort_already_configured_by_url(hass: HomeAssistant) -> None:
    """Test that zeroconf discovery aborts if host/port is already configured."""
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="WhatsApp (49176123456)",
        data={
            CONF_SESSION_ID: "default",
            CONF_URL: "http://192.168.1.100:8066",
            CONF_API_KEY: "mock_key",
        },
        unique_id="49176123456",
        entry_id="test_existing_hub",
    )
    entry.add_to_hass(hass)
    hass.config_entries.async_entries.return_value = [entry]

    from unittest.mock import MagicMock

    def mock_update_entry(e, **kwargs):
        if "data" in kwargs:
            object.__setattr__(e, "data", kwargs["data"])
        return True

    hass.config_entries.async_update_entry = MagicMock(side_effect=mock_update_entry)

    discovery_info = ZeroconfServiceInfo(
        ip_address="192.168.1.100",
        ip_addresses=["192.168.1.100"],
        hostname="whatsapp-gw.local.",
        name="WhatsApp Gateway._ha-whatsapp._tcp.local.",
        port=8066,
        properties={"system_id": "test-addon-sys-id-123", "api_key": "mock_key"},
        type="_ha-whatsapp._tcp.local.",
    )

    from custom_components.whatsapp.config_flow import ConfigFlow

    flow = ConfigFlow()
    flow.hass = hass
    flow.context = {"source": config_entries.SOURCE_ZEROCONF}

    result = await flow.async_step_zeroconf(discovery_info)

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Verify that system_id was backfilled into the existing entry
    assert entry.data.get("system_id") == "test-addon-sys-id-123"
