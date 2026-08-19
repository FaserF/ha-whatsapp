"""Test the HA WhatsApp stats sensors."""

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


async def test_stats_sensors(hass: HomeAssistant) -> None:
    """Test the statistics sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 5, "failed": 1, "connected": True}
        )
        mock_instance.get_health = AsyncMock(return_value={"status": "ok"})
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
        mock_instance.close = AsyncMock()

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Check sensors directly via instance creation
        from custom_components.whatsapp.sensor import WhatsAppStatSensor

        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        sensor_sent = WhatsAppStatSensor(coordinator, entry, "sent")
        sensor_failed = WhatsAppStatSensor(coordinator, entry, "failed")

        assert sensor_sent.native_value == 5
        assert sensor_failed.native_value == 1

        # Update stats
        mock_instance.get_stats.return_value = {"sent": 12, "failed": 3}

        # Trigger coordinator refresh
        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert sensor_sent.native_value == 12
        assert sensor_failed.native_value == 3

        # Update stats with lifetime persistence
        mock_instance.get_stats.return_value = {
            "sent": 2,
            "failed": 0,
            "lifetime_sent": 50,
            "lifetime_failed": 5,
        }

        await coordinator.async_refresh()
        await hass.async_block_till_done()

        assert sensor_sent.native_value == 50
        assert sensor_sent.extra_state_attributes["session_count"] == 2
        assert sensor_sent.extra_state_attributes["lifetime_count"] == 50
        assert sensor_failed.native_value == 5
        assert sensor_failed.extra_state_attributes["session_count"] == 0
        assert sensor_failed.extra_state_attributes["lifetime_count"] == 5


def test_chats_sensor_list_fallback() -> None:
    """Test WhatsAppChatsSensor handles list input safely without crashing."""
    from custom_components.whatsapp.sensor import WhatsAppChatsSensor

    mock_coordinator = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"

    sensor = WhatsAppChatsSensor(mock_coordinator, mock_entry)

    # Test with dict
    mock_coordinator.data = {
        "chats": {"total_chats": 10, "groups": [{"jid": "123@g.us"}]}
    }
    assert sensor.extra_state_attributes == {
        "groups": [{"jid": "123@g.us"}],
        "group_count": 1,
        "status_description": "10 chat(s) total (1 group(s))",
    }

    # Test with list (the bug condition in Issue #83)
    mock_coordinator.data = {
        "chats": [{"jid": "123@g.us"}, {"jid": "456@s.whatsapp.net"}]
    }
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "groups": [{"jid": "123@g.us"}],
        "group_count": 1,
        "status_description": "2 chat(s) total (1 group(s))",
    }

    # Test with None/empty data
    mock_coordinator.data = None
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {
        "groups": [],
        "group_count": 0,
        "status_description": "No data available",
    }


def test_invalid_unicode_sanitization() -> None:
    """Test that invalid Unicode surrogates in attributes are sanitized."""
    import json  # noqa: E402

    from custom_components.whatsapp.helpers import safe_text  # noqa: E402
    from custom_components.whatsapp.sensor import WhatsAppStatSensor  # noqa: E402

    invalid_str = "Invalid \ud800 Unicode"
    sanitized = safe_text(invalid_str)
    assert "\ud800" not in sanitized
    dumped = json.dumps({"last_message": sanitized})
    assert "Invalid" in dumped

    mock_coordinator = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"

    mock_coordinator.data = {
        "stats": {
            "last_received_message": "Hello \ud800 World",
            "last_received_sender": "Sender \ud800",
            "last_sent_message": "Sent \ud800",
            "last_sent_target": "Target \ud800",
            "last_failed_message": "Failed \ud800",
            "last_failed_target": "Target \ud800",
            "last_error_reason": "Error \ud800",
        }
    }

    sensor_rec = WhatsAppStatSensor(mock_coordinator, mock_entry, "received")
    sensor_sent = WhatsAppStatSensor(mock_coordinator, mock_entry, "sent")
    sensor_failed = WhatsAppStatSensor(mock_coordinator, mock_entry, "failed")

    attrs_rec = sensor_rec.extra_state_attributes
    attrs_sent = sensor_sent.extra_state_attributes
    attrs_failed = sensor_failed.extra_state_attributes

    json.dumps(attrs_rec)
    json.dumps(attrs_sent)
    json.dumps(attrs_failed)

    assert attrs_rec["last_message"] in ("Hello \ufffd World", "Hello ? World")
    assert attrs_sent["last_message"] in ("Sent \ufffd", "Sent ?")
    assert attrs_failed["error_reason"] in ("Error \ufffd", "Error ?")
