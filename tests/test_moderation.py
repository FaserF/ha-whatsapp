"""Test the group moderation engine in HA WhatsApp."""

from unittest.mock import AsyncMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

import pytest  # noqa: E402
from homeassistant.exceptions import HomeAssistantError  # noqa: E402

from custom_components.whatsapp.api import WhatsAppApiClient  # noqa: E402


@pytest.mark.asyncio
async def test_api_moderation_methods() -> None:
    """Test API client moderation methods."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="secret_token")

    with (
        patch("aiohttp.ClientSession.get") as mock_get,
        patch("aiohttp.ClientSession.post") as mock_post,
        patch("aiohttp.ClientSession.delete") as mock_delete,
    ):
        # Mock GET config response
        mock_resp_get = AsyncMock()
        mock_resp_get.status = 200
        mock_resp_get.json = AsyncMock(
            return_value={
                "success": True,
                "data": {
                    "global_enabled": True,
                    "groups": {"1203630123456789@g.us": {"enabled": True}},
                },
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_resp_get

        config = await client.get_moderation_config()
        assert config["success"] is True
        assert config["data"]["global_enabled"] is True

        # Mock POST enable response
        mock_resp_post = AsyncMock()
        mock_resp_post.status = 200
        mock_resp_post.json = AsyncMock(
            return_value={"success": True, "data": {"enabled": True}}
        )
        mock_post.return_value.__aenter__.return_value = mock_resp_post

        enabled_res = await client.enable_group_moderation("1203630123456789@g.us")
        assert enabled_res["success"] is True

        # Mock POST warn response
        warn_res = await client.warn_user(
            "1203630123456789@g.us", "491761234567", "Spamming links"
        )
        assert warn_res["success"] is True

        # Mock DELETE clear warnings response
        mock_resp_del = AsyncMock()
        mock_resp_del.status = 200
        mock_resp_del.json = AsyncMock(return_value={"success": True, "cleared": True})
        mock_delete.return_value.__aenter__.return_value = mock_resp_del

        clear_res = await client.clear_warnings("1203630123456789@g.us", "491761234567")
        assert clear_res["success"] is True

        # Mock error handling
        mock_resp_err = AsyncMock()
        mock_resp_err.status = 400
        mock_resp_err.text = AsyncMock(return_value="Invalid parameter")
        mock_post.return_value.__aenter__.return_value = mock_resp_err

        with pytest.raises(HomeAssistantError):
            await client.import_moderation_config(
                "1203630123456789@g.us", {"invalid": True}
            )
