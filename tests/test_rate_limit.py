"""Tests for rate limiting handling in the WhatsApp integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.whatsapp.api import WhatsAppApiClient


async def test_get_chats_rate_limit() -> None:
    """Test that get_chats handles 429 (Too Many Requests) gracefully."""
    client = WhatsAppApiClient("http://localhost:8066", "test_key")

    mock_response = MagicMock()
    mock_response.status = 429
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Use a real ClientSession mock pattern as used in other tests
    with patch("aiohttp.ClientSession.get", return_value=mock_response):
        # get_chats should return empty data on 429 instead of raising an error
        # so that the coordinator can continue with cached or empty data.
        result = await client.get_chats()
        assert result == {"total_chats": 0, "groups": []}


async def test_get_groups_rate_limit() -> None:
    """Test that get_groups raises HomeAssistantError with details on 429."""
    client = WhatsAppApiClient("http://localhost:8066", "test_key")

    mock_response = MagicMock()
    mock_response.status = 429
    mock_response.json = AsyncMock(
        return_value={
            "detail": "Rate limit: Group fetch is currently in cooldown",
            "cooldown_remaining": 600,
        }
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession.get", return_value=mock_response):
        with pytest.raises(HomeAssistantError) as excinfo:
            await client.get_groups()
        assert (
            "Rate limit: Group fetch is currently in cooldown (Remaining: 600s)"
            in str(excinfo.value)
        )


async def test_get_chats_generic_error() -> None:
    """Test that get_chats handles generic HTTP errors gracefully."""
    client = WhatsAppApiClient("http://localhost:8066", "test_key")

    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession.get", return_value=mock_response):
        result = await client.get_chats()
        assert result == {"total_chats": 0, "groups": []}


async def test_get_groups_generic_error() -> None:
    """Test that get_groups raises HomeAssistantError on generic addon errors."""
    client = WhatsAppApiClient("http://localhost:8066", "test_key")

    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession.get", return_value=mock_response):
        with pytest.raises(HomeAssistantError) as excinfo:
            await client.get_groups()
        assert "Addon error 500" in str(excinfo.value)
