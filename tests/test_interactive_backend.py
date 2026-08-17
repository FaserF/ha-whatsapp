"""Tests for interactive message payloads."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.whatsapp.api import WhatsAppApiClient


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_buttons_payload() -> None:
    """Test the JSON payload sent by send_buttons."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "success"})
        mock_post.return_value.__aenter__.return_value = mock_response

        # Mock the ClientSession to intercept calls made
        # via 'async with aiohttp.ClientSession() as session'.
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = mock_session_cls.return_value.__aenter__.return_value
            mock_session.post = mock_post

            buttons = [{"id": "b1", "displayText": "Click"}]
            await client.send_buttons("123", "Hello", buttons)

            # Check the payload
            # args, kwargs = mock_post.call_args
            # The URL is f"{self.host}/send_buttons"
            mock_post.assert_called_once()
            kwargs = mock_post.call_args.kwargs
            assert kwargs["json"]["number"] == "123@s.whatsapp.net"
            assert kwargs["json"]["message"] == "Hello"
            assert kwargs["json"]["buttons"] == [
                {
                    "id": "b1",
                    "buttonId": "b1",
                    "text": "Click",
                    "displayText": "Click",
                }
            ]


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_list_payload() -> None:
    """Test the JSON payload sent by send_list."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "success"})
        mock_post.return_value.__aenter__.return_value = mock_response

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = mock_session_cls.return_value.__aenter__.return_value
            mock_session.post = mock_post

            sections = [{"title": "S1", "rows": [{"title": "O1", "rowId": "1"}]}]
            await client.send_list("123", "Title", "Text", "Button", sections)

            # Check the payload
            mock_post.assert_called_once()
            kwargs = mock_post.call_args.kwargs
            assert kwargs["json"]["number"] == "123@s.whatsapp.net"
            assert kwargs["json"]["title"] == "Title"
            assert kwargs["json"]["text"] == "Text"
            assert kwargs["json"]["button_text"] == "Button"
            assert kwargs["json"]["sections"] == sections


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_buttons_as_polls() -> None:
    """Test send_buttons when buttons_as_polls is enabled."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")
    client.buttons_as_polls = True

    with patch.object(client, "send_poll", new_callable=AsyncMock) as mock_send_poll:
        mock_send_poll.return_value = "poll_msg_123"
        buttons = [
            {"id": "btn_yes", "displayText": "Yes, please! 💡"},
            {"id": "btn_no", "displayText": "No, leave them on."},
        ]
        msg_id = await client.send_buttons(
            "49123456789", "Turn off lights?", buttons, footer="Smart Home"
        )

        assert msg_id == "poll_msg_123"
        mock_send_poll.assert_called_once_with(
            number="49123456789@s.whatsapp.net",
            question="Turn off lights?\n\n_Smart Home_",
            options=["Yes, please! 💡", "No, leave them on."],
            quoted_message_id=None,
            expiration=None,
            allow_multiple_responses=False,
        )
        assert "poll_msg_123" in client._active_button_polls
        assert client._active_button_polls["poll_msg_123"]["button_map"] == {
            "Yes, please! 💡": "btn_yes",
            "No, leave them on.": "btn_no",
        }


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_buttons_single_button_autofix() -> None:
    """Test send_buttons auto-fixes a single button by appending placeholder."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")
    client.buttons_as_polls = True

    with patch.object(client, "send_poll", new_callable=AsyncMock) as mock_send_poll:
        mock_send_poll.return_value = "poll_msg_single"
        buttons = [{"id": "btn_ack", "displayText": "Bestätigen"}]
        msg_id = await client.send_buttons("49123456789", "Alarm ausgelöst!", buttons)

        assert msg_id == "poll_msg_single"
        call_kwargs = mock_send_poll.call_args.kwargs
        assert len(call_kwargs["options"]) == 2
        assert call_kwargs["options"][0] == "Bestätigen"
        placeholder_opt = call_kwargs["options"][1]
        assert "Placeholder" in placeholder_opt or "Platzhalter" in placeholder_opt
        btn_map = client._active_button_polls["poll_msg_single"]["button_map"]
        assert btn_map["Bestätigen"] == "btn_ack"


@pytest.mark.asyncio  # type: ignore[untyped-decorator]
async def test_send_buttons_duplicate_text_autofix() -> None:
    """Test send_buttons auto-fixes identical button texts with incremented suffix."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")
    client.buttons_as_polls = True

    with patch.object(client, "send_poll", new_callable=AsyncMock) as mock_send_poll:
        mock_send_poll.return_value = "poll_msg_dups"
        buttons = [
            {"id": "btn_opt_1", "text": "Option"},
            {"id": "btn_opt_2", "text": "Option"},
            {"id": "btn_opt_3", "text": "Option"},
        ]
        msg_id = await client.send_buttons("49123456789", "Choose option", buttons)

        assert msg_id == "poll_msg_dups"
        call_kwargs = mock_send_poll.call_args.kwargs
        assert call_kwargs["options"] == ["Option", "Option (2)", "Option (3)"]
        btn_map = client._active_button_polls["poll_msg_dups"]["button_map"]
        assert btn_map["Option"] == "btn_opt_1"
        assert btn_map["Option (2)"] == "btn_opt_2"
        assert btn_map["Option (3)"] == "btn_opt_3"
