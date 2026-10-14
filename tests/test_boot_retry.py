"""Tests for boot-time DNS/connection race retry and entity availability transitions (Issue #118)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.exceptions import (  # noqa: E402
    ConfigEntryAuthFailed,
)
from homeassistant.helpers.update_coordinator import UpdateFailed  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.binary_sensor import (  # noqa: E402
    WhatsAppConnectionSensor,
)
from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)
from custom_components.whatsapp.coordinator import (  # noqa: E402
    WhatsAppDataUpdateCoordinator,
)
from custom_components.whatsapp.helpers import is_connection_or_dns_error  # noqa: E402
from custom_components.whatsapp.notify import (  # noqa: E402
    WhatsAppNotificationEntity,
)


def test_is_connection_or_dns_error() -> None:
    """Verify detection of various DNS, timeout, and connection errors."""
    assert is_connection_or_dns_error(
        "Cannot connect to host core-whatsapp:8066 ssl:default [Timeout while contacting DNS servers]"
    )
    assert is_connection_or_dns_error(
        "Cannot connect to host <slug>-whatsapp:8066 ssl:default [DNS server returned answer with no data]"
    )
    assert is_connection_or_dns_error("Temporary failure in name resolution")
    assert is_connection_or_dns_error("Name or service not known")
    assert is_connection_or_dns_error("Connection refused")
    assert is_connection_or_dns_error("Connection reset by peer")
    assert is_connection_or_dns_error(TimeoutError())
    assert is_connection_or_dns_error(TimeoutError())
    assert is_connection_or_dns_error(
        aiohttp.ClientConnectorError(
            connection_key=MagicMock(),
            os_error=OSError("getaddrinfo failed"),
        )
    )

    # Negative cases
    assert not is_connection_or_dns_error("Invalid API Key")
    assert not is_connection_or_dns_error("HTTP 401 Unauthorized")
    assert not is_connection_or_dns_error("Payload missing required field")


@pytest.mark.asyncio
async def test_coordinator_health_retry_on_dns_race(hass: HomeAssistant) -> None:
    """Test that the coordinator retries health checks during boot-time DNS races."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "secret"},
        entry_id="test_dns_retry",
    )
    entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.ensure_polling = MagicMock()
    mock_client.stats = {"sent": 0, "failed": 0, "connected": True}
    mock_client.get_stats = AsyncMock(
        return_value={"sent": 5, "failed": 0, "connected": True}
    )
    mock_client.get_status = AsyncMock(return_value={"connected": True})
    mock_client.get_chats = AsyncMock(return_value={"total_chats": 1, "groups": []})
    mock_client.get_dashboard = AsyncMock(return_value={})
    mock_client.get_moderation_config = AsyncMock(return_value={"data": {}})
    mock_client.get_telegram_config = AsyncMock(return_value={"data": {}})
    mock_client.get_auto_responder_config = AsyncMock(return_value={"data": {}})

    # First attempt fails with DNS timeout; second succeeds
    mock_client.get_health = AsyncMock(
        side_effect=[
            {
                "status": "unreachable",
                "details": "Cannot connect to host core-whatsapp:8066 ssl:default [Timeout while contacting DNS servers]",
            },
            {"status": "connected", "details": ""},
        ]
    )

    coordinator = WhatsAppDataUpdateCoordinator(hass, mock_client, entry)

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        data = await coordinator._async_update_data()
        assert data["connected"] is True
        assert data["stats"]["sent"] == 5
        assert mock_client.get_health.call_count == 2
        mock_sleep.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_setup_entry_retry_and_success(hass: HomeAssistant) -> None:
    """Test async_setup_entry retrying when initial coordinator refresh hits DNS race."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "secret"},
        entry_id="test_setup_retry",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.connect = AsyncMock(return_value=True)
        mock_instance.get_stats = AsyncMock(
            return_value={"sent": 0, "failed": 0, "connected": True}
        )
        mock_instance.get_dashboard = AsyncMock(return_value={})
        mock_instance.get_chats = AsyncMock(
            return_value={"total_chats": 0, "groups": []}
        )
        mock_instance.get_status = AsyncMock(return_value={"connected": True})
        mock_instance.get_moderation_config = AsyncMock(return_value={"data": {}})
        mock_instance.get_telegram_config = AsyncMock(return_value={"data": {}})
        mock_instance.get_auto_responder_config = AsyncMock(return_value={"data": {}})
        mock_instance.register_callback = MagicMock()
        mock_instance.start_polling = AsyncMock()
        mock_instance.start_session = AsyncMock(return_value=None)
        mock_instance.close = AsyncMock()

        # get_health: fails once with DNS timeout, then succeeds
        mock_instance.get_health = AsyncMock(
            side_effect=[
                {
                    "status": "unreachable",
                    "details": "Cannot connect to host core-whatsapp:8066 [Timeout while contacting DNS servers]",
                },
                {"status": "connected", "details": ""},
            ]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
            assert mock_instance.get_health.call_count == 2
            mock_sleep.assert_called_once_with(1)
            assert entry.entry_id in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_setup_entry_auth_failure_not_retried(hass: HomeAssistant) -> None:
    """Test that auth failures are raised immediately without retrying."""
    from custom_components.whatsapp.api import WhatsAppAuthError

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "bad_key"},
        entry_id="test_auth_fail",
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_instance = mock_client_cls.return_value
        mock_instance.get_health = AsyncMock(return_value={"status": "connected"})
        mock_instance.get_stats = AsyncMock(
            side_effect=WhatsAppAuthError("Invalid API Key")
        )
        with pytest.raises(ConfigEntryAuthFailed):
            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()
        mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_entity_availability_transition(hass: HomeAssistant) -> None:
    """Test that entities cleanly transition from unavailable to available once gateway recovers."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "secret"},
        entry_id="test_availability_transition",
    )
    entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.session_id = "default"
    mock_client.get_device_info = MagicMock(
        return_value={"identifiers": {(DOMAIN, "default")}}
    )
    mock_client.stats = {"sent": 0, "failed": 0, "connected": True}

    coordinator = WhatsAppDataUpdateCoordinator(hass, mock_client, entry)
    coordinator.data = {"connected": True, "stats": {"sent": 10, "failed": 0}}
    coordinator.last_update_success = True

    binary_sensor = WhatsAppConnectionSensor(coordinator, entry)
    notify_entity = WhatsAppNotificationEntity(mock_client, entry, coordinator)

    # 1. Initially both entities are available
    assert binary_sensor.available is True
    assert binary_sensor.is_on is True
    assert notify_entity.available is True

    # 2. Addon goes down and grace period expires -> UpdateFailed
    coordinator._unreachable_count = 5
    with (
        patch("homeassistant.helpers.issue_registry.async_create_issue"),
        pytest.raises(UpdateFailed),
    ):
        coordinator._handle_unreachable(
            "Cannot connect to host core-whatsapp:8066 [Timeout while contacting DNS servers]"
        )

    coordinator.last_update_success = False
    coordinator.data = None

    # Entities must report unavailable cleanly without throwing AttributeError
    assert binary_sensor.available is False
    assert notify_entity.available is False

    # 3. Addon recovers -> update succeeds
    coordinator.data = {"connected": True, "stats": {"sent": 15, "failed": 0}}
    coordinator.last_update_success = True
    coordinator._unreachable_count = 0

    # Entities must cleanly transition back to available
    assert binary_sensor.available is True
    assert binary_sensor.is_on is True
    assert notify_entity.available is True


@pytest.mark.asyncio
async def test_start_session_exponential_backoff_retry(hass: HomeAssistant) -> None:
    """Test client.start_session retries on boot-time connection errors."""
    from custom_components.whatsapp.api import WhatsAppApiClient

    client = WhatsAppApiClient("http://core-whatsapp:8066", "secret", "default")

    mock_resp_fail = MagicMock()
    mock_resp_fail.__aenter__ = AsyncMock(
        side_effect=aiohttp.ClientConnectorError(
            connection_key=MagicMock(),
            os_error=OSError("Timeout while contacting DNS servers"),
        )
    )
    mock_resp_fail.__aexit__ = AsyncMock(return_value=None)

    mock_resp_ok = MagicMock()
    mock_resp_ok.status = 200
    mock_resp_ok.__aenter__ = AsyncMock(return_value=mock_resp_ok)
    mock_resp_ok.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(side_effect=[mock_resp_fail, mock_resp_ok])

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await client.start_session()
        assert mock_session.post.call_count == 2
        mock_sleep.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_coordinator_health_retry_exhausted_raises(hass: HomeAssistant) -> None:
    """Test that exhausting health check retries raises UpdateFailed."""
    if hasattr(hass, "loop") and hasattr(hass.loop, "time"):
        hass.loop.time.return_value = 0.0

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "secret"},
        entry_id="test_dns_exhausted",
    )
    entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.ensure_polling = MagicMock()
    mock_client.get_health = AsyncMock(
        return_value={
            "status": "unreachable",
            "details": "Cannot connect to host core-whatsapp:8066 ssl:default [Timeout while contacting DNS servers]",
        }
    )

    coordinator = WhatsAppDataUpdateCoordinator(hass, mock_client, entry)
    coordinator.data = None

    with (
        patch("homeassistant.helpers.issue_registry.async_create_issue") as mock_create_issue,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()

    # 1 initial + 4 retries = 5 calls
    assert mock_client.get_health.call_count == 5
    assert mock_sleep.call_count == 4
    mock_create_issue.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_retry_exhausted_raises(hass: HomeAssistant) -> None:
    """Test that async_setup_entry raises when all setup retries are exhausted."""
    if hasattr(hass, "loop") and hasattr(hass.loop, "time"):
        hass.loop.time.return_value = 0.0

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://core-whatsapp:8066", CONF_API_KEY: "secret"},
        entry_id="test_setup_exhausted",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.whatsapp.WhatsAppApiClient") as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.get_health = AsyncMock(
            return_value={
                "status": "unreachable",
                "details": "Cannot connect to host core-whatsapp:8066 [Timeout while contacting DNS servers]",
            }
        )

        with (
            patch("homeassistant.helpers.issue_registry.async_create_issue"),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            pytest.raises(Exception),
        ):
            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        assert mock_sleep.call_count > 0
