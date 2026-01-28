
import logging
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock homeassistant modules before possible imports
if "homeassistant" not in sys.modules:
    sys.modules["homeassistant"] = MagicMock()
if "homeassistant.core" not in sys.modules:
    sys.modules["homeassistant.core"] = MagicMock()

try:
    from custom_components.whatsapp.api import WhatsAppApiClient
except ImportError:
    # Fallback if running directly without package context
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from custom_components.whatsapp.api import WhatsAppApiClient

_LOGGER = logging.getLogger(__name__)

class MockAsyncContextManager:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

async def test_verify_send_document():
    """Verify the send_document logic."""
    _LOGGER.info("Verifying send_document logic...")

    client = WhatsAppApiClient(
        host="http://localhost:8066",
        api_key="test_key",
        whitelist=["49123456789"]
    )

    # 1. Test allowed target
    _LOGGER.info("Testing allowed target...")

    # Mocking response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="OK")

    # Mocking session
    mock_session = MagicMock()
    mock_session.post.return_value = MockAsyncContextManager(mock_response)

    # Mocking ClientSession() to be an async context manager returning mock_session
    mock_session_cm = MockAsyncContextManager(mock_session)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        await client.send_document(
            "49123456789",
            "http://test.com/file.pdf",
            "test.pdf",
            "Here is a file"
        )

        # Verify call data
        args, kwargs = mock_session.post.call_args
        url = args[0]
        payload = kwargs["json"]
        headers = kwargs["headers"]

        assert url == "http://localhost:8066/send_document"
        assert payload["number"] == "49123456789@s.whatsapp.net"
        assert payload["url"] == "http://test.com/file.pdf"
        assert payload["fileName"] == "test.pdf"
        assert payload["caption"] == "Here is a file"
        assert headers["X-Auth-Token"] == "test_key"
        _LOGGER.info("✅ Allowed target passed.")

        # 2. Test blocked target
        _LOGGER.info("Testing blocked target (whitelist)...")
        mock_session.post.reset_mock()
        await client.send_document("49987654321", "http://test.com/file.pdf")
        assert not mock_session.post.called
        _LOGGER.info("✅ Blocked target passed.")

    _LOGGER.info("All verification tests for send_document PASSED!")
