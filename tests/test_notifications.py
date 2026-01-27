"""Test the connection loss notifications."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import CONF_API_KEY, CONF_URL, DOMAIN


async def test_connection_lost_notification(hass: HomeAssistant) -> None:
    """Test that a notification is created on connection loss."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://localhost:8066", CONF_API_KEY: "mock"},
    )
    entry.add_to_hass(hass)

    from homeassistant.helpers import issue_registry as ir

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        # Fail initially to trigger notification
        mock_instance.connect = AsyncMock(side_effect=Exception("Connection Failed"))
        mock_instance.get_stats = AsyncMock(return_value={"sent": 0, "failed": 0})
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock()
        mock_instance.close = AsyncMock()

        # Setup
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Check for issue in registry
        issue_registry = ir.async_get(hass)
        assert issue_registry.async_get_issue(DOMAIN, "connection_failed")

        # Simulate reconnect
        mock_instance.connect = AsyncMock(return_value=True)
        data = hass.data[DOMAIN][entry.entry_id]
        await data["coordinator"].async_refresh()
        await hass.async_block_till_done()

        # Notification (issue) should be removed
        assert not issue_registry.async_get_issue(DOMAIN, "connection_failed")
