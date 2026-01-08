"""Test the connection loss notifications."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN


async def test_connection_lost_notification(hass: HomeAssistant) -> None:
    """Test that a notification is created on connection loss."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "mock"})
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        # Fail initially to trigger notification
        mock_instance.connect = AsyncMock(side_effect=Exception("Connection Failed"))
        mock_instance.stats = {"sent": 0, "failed": 0}

        # Mock the service calls
        with patch.object(hass.services, "async_call", AsyncMock()) as mock_service_call:
            # Setup - this will call first refresh
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

            # Verify notification created
            mock_service_call.assert_any_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Connection Lost",
                    "message": "Integration lost connection to the WhatsApp Addon: Connection Failed",
                    "notification_id": f"{DOMAIN}_connection_lost",
                },
            )

            # Restored connection
            mock_instance.connect = AsyncMock(return_value=True)

            data = hass.data[DOMAIN][entry.entry_id]
            await data["coordinator"].async_refresh()
            await hass.async_block_till_done()

            # Verify notification dismissed
            mock_service_call.assert_any_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": f"{DOMAIN}_connection_lost"},
            )
