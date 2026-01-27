
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Add the integration directory to sys.path so we can import api directly
sys.path.append(os.path.abspath("custom_components/whatsapp"))

# Mock a few things that might be needed if they were added
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()

try:
    from api import WhatsAppApiClient
except ImportError:
    # If that fails, try the full path
    import importlib.util
    spec = importlib.util.spec_from_file_location("api", "custom_components/whatsapp/api.py")
    api_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_mod)
    WhatsAppApiClient = api_mod.WhatsAppApiClient

class MockAsyncContextManager:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

async def verify_send_document():
    print("Verifying send_document logic...")

    client = WhatsAppApiClient(
        host="http://localhost:8066",
        api_key="test_key",
        whitelist=["49123456789"]
    )

    # 1. Test allowed target
    print("Testing allowed target...")

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
        await client.send_document("49123456789", "http://test.com/file.pdf", "test.pdf", "Here is a file")

        # Verify call data
        # Note: session is the return value of ClientSession().__aenter__()
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
        print("✅ Allowed target passed.")

        # 2. Test blocked target
        print("Testing blocked target (whitelist)...")
        mock_session.post.reset_mock()
        await client.send_document("49987654321", "http://test.com/file.pdf")
        assert not mock_session.post.called
        print("✅ Blocked target passed.")

    print("\nAll verification tests for send_document PASSED!")

if __name__ == "__main__":
    asyncio.run(verify_send_document())
