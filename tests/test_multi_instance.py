"""Tests for multi-instance support of the WhatsApp integration."""

from unittest.mock import patch

from custom_components.whatsapp.const import CONF_API_KEY, CONF_URL, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_multi_instance_setup(hass: HomeAssistant) -> None:
    """Test that multiple instances can be set up independently."""

    # 1. Setup first instance
    with (
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.connect",
            return_value=True,
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_stats",
            return_value={"my_number": "49123456789"},
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.close",
            return_value=None,
        ),
        patch("custom_components.whatsapp.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://localhost:8066", "api_key": "key1"},
        )
        # Scan step (already connected mock)
        # result2 is already the result of the flow because connect()=True
        # skipped the scan form
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == "WhatsApp (49123456789)"
        assert result2["result"].unique_id == "49123456789"
        session_id_1 = result2["data"]["session_id"]

    # 2. Setup second instance with different number
    with (
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.connect",
            return_value=True,
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_stats",
            return_value={"my_number": "49987654321"},
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.close",
            return_value=None,
        ),
        patch("custom_components.whatsapp.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://localhost:8066", "api_key": "key2"},
        )
        # Scan step
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == "WhatsApp (49987654321)"
        assert result2["result"].unique_id == "49987654321"
        session_id_2 = result2["data"]["session_id"]

        # Ensure session IDs are different
        assert session_id_1 != session_id_2


async def test_duplicate_instance_rejected(hass: HomeAssistant) -> None:
    """Test that adding the same phone number twice is rejected."""

    # Pre-existing entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="49123456789",
        data={
            CONF_URL: "http://localhost:8066",
            CONF_API_KEY: "key1",
            "session_id": "session1",
        },
    )
    entry.add_to_hass(hass)

    # Try to add again
    with (
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.connect",
            return_value=True,
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.get_stats",
            return_value={"my_number": "49123456789"},
        ),
        patch(
            "custom_components.whatsapp.config_flow.WhatsAppApiClient.close",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://localhost:8066", "api_key": "key1"},
        )
        # Scan step
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"
