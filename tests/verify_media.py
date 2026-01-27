
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

async def verify_media():
    print("Verifying media logic (video/audio)...")

    client = WhatsAppApiClient(
        host="http://localhost:8066",
        api_key="test_key",
        whitelist=["49123456789"]
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
        # 1. Test Send Video
        print("Testing send_video...")
        await client.send_video("49123456789", "http://test.com/video.mp4", "Watch this")

        args, kwargs = mock_session.post.call_args
        url = args[0]
        payload = kwargs["json"]

        assert url == "http://localhost:8066/send_video"
        assert payload["number"] == "49123456789@s.whatsapp.net"
        assert payload["url"] == "http://test.com/video.mp4"
        assert payload["caption"] == "Watch this"
        print("✅ send_video passed.")

        # 2. Test Send Audio (File)
        print("Testing send_audio (file)...")
        mock_session.post.reset_mock()
        await client.send_audio("49123456789", "http://test.com/audio.mp3", ptt=False)

        args, kwargs = mock_session.post.call_args
        url = args[0]
        payload = kwargs["json"]

        assert url == "http://localhost:8066/send_audio"
        assert payload["url"] == "http://test.com/audio.mp3"
        assert payload["ptt"] is False
        print("✅ send_audio (file) passed.")

        # 3. Test Send Audio (PTT)
        print("Testing send_audio (PTT)...")
        mock_session.post.reset_mock()
        await client.send_audio("49123456789", "http://test.com/voice.ogg", ptt=True)

        args, kwargs = mock_session.post.call_args
        payload = kwargs["json"]

        assert payload["ptt"] is True
        print("✅ send_audio (PTT) passed.")

        # 4. Test Whitelist
        print("Testing whitelist...")
        mock_session.post.reset_mock()
        await client.send_video("49999999999", "http://test.com/video.mp4")
        assert not mock_session.post.called
        print("✅ Whitelist passed.")

    print("\nAll verification tests for Media PASSED!")

if __name__ == "__main__":
    asyncio.run(verify_media())
