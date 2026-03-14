"""Comprehensive tests for WhatsApp Integration."""

from __future__ import annotations

import os
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the root of the integration to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


# Use centralized stubs
from ha_stubs import _build_ha_stub_modules  # noqa: E402

_build_ha_stub_modules()


# 2. Import under test
from custom_components.whatsapp.api import WhatsAppApiClient  # noqa: E402


@pytest.fixture  # type: ignore[untyped-decorator]
def api_client() -> WhatsAppApiClient:
    """Fixture."""
    return WhatsAppApiClient(
        host="http://localhost:8066", api_key="test_key", session_id="default"
    )


def mock_aiohttp_post(
    status: int = 200, json_data: Any | None = None, text_data: str = ""
) -> MagicMock:
    """Mock aiohttp post."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=json_data or {"status": "sent"})
    mock_response.text = AsyncMock(return_value=text_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    mock_session.get.return_value = mock_response
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    return mock_session


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_message(api_client: WhatsAppApiClient) -> None:
    """Test sending a text message."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_message("12345", "Hello", expiration=604800)
        mock_session.post.assert_called_once()
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["message"] == "Hello"
        assert kwargs["json"]["expiration"] == 604800
        assert kwargs["params"]["session_id"] == "default"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_poll(api_client: WhatsAppApiClient) -> None:
    """Test sending a poll message."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_poll(
            "12345", "Question?", ["Yes", "No"], expiration=86400
        )
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["question"] == "Question?"
        assert kwargs["json"]["options"] == ["Yes", "No"]
        assert kwargs["json"]["expiration"] == 86400


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_media(api_client: WhatsAppApiClient) -> None:
    """Test sending various media types (image, video, document, audio)."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Image
        await api_client.send_image(
            "12345", "http://img.jpg", "caption", expiration=3600
        )
        assert "/send_image" in mock_session.post.call_args[0][0]
        assert mock_session.post.call_args[1]["json"]["expiration"] == 3600

        # Video
        mock_session.post.reset_mock()
        await api_client.send_video(
            "12345", "http://vid.mp4", "caption", expiration=3600
        )
        assert "/send_video" in mock_session.post.call_args[0][0]
        assert mock_session.post.call_args[1]["json"]["expiration"] == 3600

        # Document
        mock_session.post.reset_mock()
        await api_client.send_document(
            "12345", "http://doc.pdf", "file.pdf", "caption", expiration=3600
        )
        assert "/send_document" in mock_session.post.call_args[0][0]
        assert mock_session.post.call_args[1]["json"]["expiration"] == 3600

        # Audio
        mock_session.post.reset_mock()
        await api_client.send_audio(
            "12345", "http://aud.mp3", ptt=True, expiration=3600
        )
        assert "/send_audio" in mock_session.post.call_args[0][0]
        assert mock_session.post.call_args[1]["json"]["expiration"] == 3600


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_revoke_message(api_client: WhatsAppApiClient) -> None:
    """Test revoking a message."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        # Default (fromMe=True)
        await api_client.revoke_message("12345", "msg123")
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["message_id"] == "msg123"
        assert kwargs["json"]["fromMe"] is True

        # Admin delete (fromMe=False)
        mock_session.post.reset_mock()
        await api_client.revoke_message("12345", "msg456", from_me=False)
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["fromMe"] is False


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_edit_message(api_client: WhatsAppApiClient) -> None:
    """Test editing a message."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.edit_message("12345", "msg123", "New text")
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["new_content"] == "New text"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_reaction(api_client: WhatsAppApiClient) -> None:
    """Test sending a reaction."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_reaction("12345", "👍", "msg123")
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["reaction"] == "👍"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_fetch_groups(api_client: WhatsAppApiClient) -> None:
    """Test fetching groups."""
    groups_data = [{"id": "g1", "name": "Group 1", "participants": 5}]
    mock_session = mock_aiohttp_post(json_data=groups_data)
    with patch("aiohttp.ClientSession", return_value=mock_session):
        res = await api_client.get_groups()
        assert res == groups_data
        assert "/groups" in mock_session.get.call_args[0][0]


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_mark_as_read(api_client: WhatsAppApiClient) -> None:
    """Test marking a message as read."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.mark_as_read("12345", "msg123")
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["messageId"] == "msg123"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_list(api_client: WhatsAppApiClient) -> None:
    """Test sending a list message."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_list(
            "12345", "Title", "Text", "Button", [], expiration=604800
        )
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["title"] == "Title"
        assert kwargs["json"]["expiration"] == 604800


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_buttons(api_client: WhatsAppApiClient) -> None:
    """Test sending buttons."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_buttons(
            "12345",
            "Text",
            [{"id": "btn1", "displayText": "Yes"}],
            "Footer",
            expiration=3600,
        )
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["message"] == "Text"
        assert kwargs["json"]["footer"] == "Footer"
        assert kwargs["json"]["expiration"] == 3600


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_contact(api_client: WhatsAppApiClient) -> None:
    """Test sending a contact."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_contact("12345", "Name", "123456789", expiration=3600)
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["contact_name"] == "Name"
        assert kwargs["json"]["expiration"] == 3600


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_location(api_client: WhatsAppApiClient) -> None:
    """Test sending a location."""
    mock_session = mock_aiohttp_post()
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await api_client.send_location(
            "12345", 52.52, 13.40, "Berlin", "Germany", expiration=3600
        )
        _, kwargs = mock_session.post.call_args
        assert kwargs["json"]["latitude"] == 52.52
        assert kwargs["json"]["expiration"] == 3600


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_self_chat_bypass(api_client: WhatsAppApiClient) -> None:
    """Test that the bot can always message itself even if not in whitelist."""
    api_client.whitelist = ["11111"]  # Current whitelist doesn't include 12345
    api_client.stats["my_number"] = "12345"

    # Should be allowed (bypass)
    assert api_client.is_allowed("12345") is True
    # Should NOT be allowed (not in whitelist, not self)
    assert api_client.is_allowed("22222") is False


if __name__ == "__main__":
    import asyncio

    async def run() -> None:
        """Sanity check helper."""
        # print("Running comprehensive tests...")
        client = WhatsAppApiClient("http://localhost:8066", "key", "session")
        # Just a sanity check that imports work and methods exist
        methods = [
            "send_message",
            "send_image",
            "send_video",
            "send_poll",
            "revoke_message",
            "edit_message",
            "send_reaction",
            "get_groups",
            "mark_as_read",
            "send_list",
            "send_buttons",
            "send_contact",
            "send_location",
        ]
        for method in methods:
            assert hasattr(client, method), f"Missing method {method}"
        # print("All methods present. Run with pytest for full verification.")

    asyncio.run(run())
