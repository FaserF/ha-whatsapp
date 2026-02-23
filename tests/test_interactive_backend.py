"""Tests for interactive message payloads."""

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.whatsapp.api import WhatsAppApiClient


@pytest.mark.asyncio
async def test_send_buttons_payload() -> None:
    """Test the JSON payload sent by send_buttons."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="test")

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "success"})
        mock_post.return_value.__aenter__.return_value = mock_response

        # We need to mock the ClientSession instance or just the post method if it's called on a new instance
        # Actually, since it's used as 'async with aiohttp.ClientSession() as session, session.post(...)',
        # we can patch ClientSession.
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
            assert kwargs["json"]["buttons"] == buttons


@pytest.mark.asyncio
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
