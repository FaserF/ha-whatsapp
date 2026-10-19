from __future__ import annotations

import aiohttp
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from custom_components.whatsapp.api import WhatsAppApiClient
from homeassistant.exceptions import HomeAssistantError

@pytest.mark.asyncio
async def test_clear_chat_not_found(caplog: pytest.LogCaptureFixture) -> None:
    """Test clear_chat throws HomeAssistantError on 404."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="secret")
    
    mock_resp = AsyncMock()
    mock_resp.status = 404
    mock_resp.text = AsyncMock(return_value="Not found")
    
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__.return_value = mock_resp
    
    # We must patch aiohttp.ClientSession so when it is called as a context manager it yields mock_session
    mock_client_session_cls = MagicMock()
    mock_client_session_cls.return_value.__aenter__.return_value = mock_session
    
    with patch("custom_components.whatsapp.api.aiohttp.ClientSession", mock_client_session_cls):
        with pytest.raises(HomeAssistantError, match="Target chat 123456789 does not exist."):
            await client.clear_chat("123456789")

@pytest.mark.asyncio
async def test_delete_chat_not_found(caplog: pytest.LogCaptureFixture) -> None:
    """Test delete_chat throws HomeAssistantError on 404."""
    client = WhatsAppApiClient(host="http://localhost:8066", api_key="secret")
    
    mock_resp = AsyncMock()
    mock_resp.status = 404
    mock_resp.text = AsyncMock(return_value="Not found")
    
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__.return_value = mock_resp
    
    mock_client_session_cls = MagicMock()
    mock_client_session_cls.return_value.__aenter__.return_value = mock_session
    
    with patch("custom_components.whatsapp.api.aiohttp.ClientSession", mock_client_session_cls):
        with pytest.raises(HomeAssistantError, match="Target chat 123456789 does not exist."):
            await client.delete_chat("123456789")
