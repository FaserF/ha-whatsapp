"""Tests for the message quoting functionality.

These tests verify that the notify platform correctly extracts the
`quoted_message_id` from notification data and passes it through to the
underlying API client.  All Home Assistant module dependencies are mocked
out so that the tests run in a plain Python environment without a full
Home Assistant installation.
"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

# Now it is safe to import the integration modules.
from custom_components.whatsapp.notify import WhatsAppNotificationEntity  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> Generator[AsyncMock, None, None]:
    """Fixture to mock WhatsAppApiClient."""
    with patch(
        "custom_components.whatsapp.notify.WhatsAppApiClient", autospec=True
    ) as mock:
        mock.is_allowed.return_value = True
        mock.ensure_jid.return_value = "1234567890@s.whatsapp.net"
        yield mock


@pytest.fixture
def notify_entity(mock_client: AsyncMock) -> WhatsAppNotificationEntity:
    """Fixture to create WhatsAppNotificationEntity instance."""
    coordinator = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    return WhatsAppNotificationEntity(mock_client, entry, coordinator)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_send_message_with_quote(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that ``quote`` in data is forwarded as ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="Hello",
        target=["1234567890"],
        data={"quote": "msg_id_123"},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "Hello", quoted_message_id="msg_id_123"
    )


async def test_send_message_with_reply_to(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that ``reply_to`` in data is forwarded as ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="World",
        target=["1234567890"],
        data={"reply_to": "msg_id_456"},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "World", quoted_message_id="msg_id_456"
    )


async def test_send_message_without_quote(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that a plain message is sent without ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="Plain message",
        target=["1234567890"],
        data={},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "Plain message", quoted_message_id=None
    )


async def test_send_message_to_multiple_targets(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that quoting works correctly for multiple targets."""
    await notify_entity.async_send_message(
        message="Hi all",
        target=["111", "222"],
        data={"quote": "q_id"},
    )

    assert mock_client.send_message.call_count == 2
    calls = mock_client.send_message.call_args_list
    assert calls[0].args == ("111", "Hi all")
    assert calls[0].kwargs == {"quoted_message_id": "q_id"}
    assert calls[1].args == ("222", "Hi all")
    assert calls[1].kwargs == {"quoted_message_id": "q_id"}
