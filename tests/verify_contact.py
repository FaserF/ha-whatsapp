
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

async def verify_contact():
    print("Verifying contact message logic...")

    client = WhatsAppApiClient(
        host="http://localhost:8066",
        api_key="test_key",
        whitelist=["1234567890"]
    )

    # Mocking response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="OK")

    # Mocking session
    mock_session = MagicMock()
    mock_session.post.return_value = MockAsyncContextManager(mock_response)

    # Mocking ClientSession()
    mock_session_cm = MockAsyncContextManager(mock_session)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        # 1. Test Send Contact
        print("Testing send_contact...")
        await client.send_contact("1234567890", "Home Assistant", "1234567890")

        args, kwargs = mock_session.post.call_args
        url = args[0]
        payload = kwargs["json"]

        assert url == "http://localhost:8066/send_contact"
        assert payload["number"] == "1234567890@s.whatsapp.net"
        assert payload["contact_name"] == "Home Assistant"
        assert payload["contact_number"] == "1234567890"
        print("✅ send_contact passed.")


    print("\nAll verification tests for Contact Message PASSED!")

if __name__ == "__main__":
    asyncio.run(verify_contact())
