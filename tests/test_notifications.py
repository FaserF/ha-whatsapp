"""Test the connection loss notifications."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.whatsapp.const import DOMAIN


async def test_connection_lost_notification(hass: HomeAssistant) -> None:
    """Test that a notification is created on connection loss."""
    entry = MockConfigEntry(domain=DOMAIN, data={"session": "mock"})
    entry.add_to_hass(hass)

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
        patch(
            "custom_components.whatsapp.coordinator.persistent_notification"
        ) as mock_pn,
    ):
        mock_instance = mock_client_cls.return_value
        # Fail initially to trigger notification
        mock_instance.connect = AsyncMock(side_effect=Exception("Connection Failed"))
        mock_instance.stats = {"sent": 0, "failed": 0}
        mock_instance.register_callback = MagicMock()

        # Setup - this will fail the first refresh, but entry should still load
        # with UpdateFailed being raised. We expect setup to return False.
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # The setup might fail due to UpdateFailed, but notification should still
        # have been created.
        mock_pn.async_create.assert_called_once()
        call_args = mock_pn.async_create.call_args
        assert "WhatsApp Connection Lost" in str(call_args)

        # If setup succeeded, verify notification dismiss on reconnect
        if result:
            mock_instance.connect = AsyncMock(return_value=True)
            data = hass.data[DOMAIN][entry.entry_id]
            await data["coordinator"].async_refresh()
            await hass.async_block_till_done()

            mock_pn.async_dismiss.assert_called()
