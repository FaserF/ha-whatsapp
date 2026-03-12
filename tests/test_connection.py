"""Tests for WhatsApp connection status logic."""

from __future__ import annotations

import sys
import os
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Add the root of the integration to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

# 1. Robust Module Mocking
def mock_module(name: str, **kwargs: Any) -> Any:
    parts = name.split('.')
    for i in range(1, len(parts) + 1):
        partial_name = '.'.join(parts[:i])
        if partial_name not in sys.modules:
            mod = types.ModuleType(partial_name)
            mod.__path__ = []  # Treat all as potential packages
            sys.modules[partial_name] = mod
        
        mod = sys.modules[partial_name]
        if i > 1:
            parent_name = '.'.join(parts[:i-1])
            setattr(sys.modules[parent_name], parts[i-1], mod)
            
    mod = sys.modules[name]
    for k, v in kwargs.items():
        setattr(mod, k, v)
    return mod

# Stub essential modules
mock_module("homeassistant.helpers.config_validation")
mock_module("homeassistant.helpers.entity_platform")
class MockSubscriptable:
    def __init__(self, *args, **kwargs): pass
    def __class_getitem__(cls, _): return cls

mock_module("homeassistant.helpers.entity", Entity=MockSubscriptable)
mock_module("homeassistant.helpers.entity_component", EntityComponent=MockSubscriptable)
mock_module("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=MockSubscriptable, UpdateFailed=Exception)
mock_module("homeassistant.helpers.issue_registry")
mock_module("homeassistant.helpers.device_registry", DeviceInfo=dict)
mock_module("homeassistant.helpers.entity_registry")
mock_module("homeassistant.helpers.storage")
mock_module("homeassistant.helpers.aiohttp_client")
mock_module("homeassistant.util.dt")
mock_module("homeassistant.util.uuid", random_uuid_hex=lambda: "dummy_uuid")
mock_module("homeassistant.components.sensor", SensorEntity=object)
mock_module("homeassistant.components.binary_sensor", BinarySensorEntity=object)
mock_module("homeassistant.components.hassio")
mock_module("homeassistant.components.notify")
mock_module("homeassistant.components.persistent_notification")
mock_module("homeassistant.data_entry_flow", AbortFlow=Exception, FlowResult=dict)

class MockConfigFlow:
    def __init__(self, *args, **kwargs):
        self.hass = None
        self.context = {}
    @classmethod
    def __init_subclass__(cls, **kwargs): pass
    async def async_show_form(self, *args, **kwargs): return {"type": "form"}
    async def async_abort(self, *args, **kwargs): return {"type": "abort"}
    async def async_create_entry(self, *args, **kwargs): return {"type": "create_entry"}

mock_module("homeassistant.config_entries", ConfigEntry=object, ConfigFlow=MockConfigFlow, OptionsFlow=MockSubscriptable)

class Platform:
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    NOTIFY = "notify"

mock_module("homeassistant.const", Platform=Platform, CONF_URL="url", CONF_NAME="name", CONF_HOST="host", CONF_API_KEY="api_key", CONF_SCAN_INTERVAL="scan_interval", CONF_BASE_URL="base_url", CONF_SESSION_ID="session_id")

class HomeAssistantError(Exception): """Stub."""
class ServiceValidationError(Exception): """Stub."""
class ConfigEntryNotReady(Exception): """Stub."""
mock_module("homeassistant.exceptions", HomeAssistantError=HomeAssistantError, ServiceValidationError=ServiceValidationError, ConfigEntryNotReady=ConfigEntryNotReady)

class HomeAssistant:
    def __init__(self):
        self.config_entries = MagicMock()
        self.services = MagicMock()
class ServiceCall: """Stub."""
mock_module("homeassistant.core", HomeAssistant=HomeAssistant, ServiceCall=ServiceCall, callback=lambda x: x, ServiceResponse=dict)

vol_mod = mock_module("voluptuous")
vol_mod.Schema = lambda s, **_: s
vol_mod.Required = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.Optional = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.All = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.In = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.Coerce = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.Any = MagicMock(side_effect=lambda *a, **_: a[0] if a else MagicMock())
vol_mod.Length = MagicMock(return_value=lambda x: x)
vol_mod.Email = MagicMock(return_value=lambda x: x)
vol_mod.Url = MagicMock(return_value=lambda x: x)
vol_mod.Matches = MagicMock(return_value=lambda x: x)
vol_mod.Range = MagicMock(return_value=lambda x: x)

# 2. Now we can import things that use homeassistant
try:
    from homeassistant.exceptions import HomeAssistantError
    from custom_components.whatsapp.api import WhatsAppApiClient
    from custom_components.whatsapp.config_flow import ConfigFlow
    from custom_components.whatsapp.const import DOMAIN
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)

@pytest.mark.asyncio
async def test_session_id_default_for_first_instance() -> None:
    """Verify that 'default' is used as session_id if no instances exist."""
    hass = MagicMock()
    # Mock no entries existing
    hass.config_entries.async_entries.return_value = []
    
    flow = ConfigFlow()
    flow.hass = hass
    
    # We need to mock the socket check in async_step_user or just check the session_id after it's called
    with patch("custom_components.whatsapp.config_flow.socket.create_connection") as mock_conn:
        mock_conn.side_effect = Exception("No host")
        await (await flow.async_step_user())
    
    assert flow.session_id == "default"

@pytest.mark.asyncio
async def test_session_id_uuid_for_subsequent_instances() -> None:
    """Verify that a UUID is used if an instance already exists."""
    hass = HomeAssistant()
    # Mock one entry existing
    hass.config_entries.async_entries.return_value = [MagicMock()]
    
    flow = ConfigFlow()
    flow.hass = hass
    
    # Capture initial UUID
    initial_uuid = flow.session_id
    assert initial_uuid != "default"
    
    with patch("custom_components.whatsapp.config_flow.socket.create_connection") as mock_conn:
        mock_conn.side_effect = Exception("No host")
        await (await flow.async_step_user())
    
    assert flow.session_id == initial_uuid
    assert flow.session_id != "default"

@pytest.mark.asyncio
async def test_api_client_status_handling() -> None:
    """Test how the API client handles various status responses."""
    client = WhatsAppApiClient(
        host="http://localhost:8066",
        api_key="test",
        session_id="test_session"
    )
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"connected": True})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = mock_session_class.return_value
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_response
        
        assert await client.connect() is True
        
        # Test disconnected status
        mock_response.json = AsyncMock(return_value={"connected": False})
        assert await client.connect() is False
        
        # Test error status
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Error")
        assert await client.connect() is False

        # Test 401 status raises HomeAssistantError
        mock_response.status = 401
        with pytest.raises(HomeAssistantError):
            await client.connect()

if __name__ == "__main__":
    import asyncio
    async def run():
        try:
            print("Testing session_id_default...")
            await test_session_id_default_for_first_instance()
            print("Testing session_id_uuid...")
            await test_session_id_uuid_for_subsequent_instances()
            print("Testing api_client_status...")
            await test_api_client_status_handling()
            print("Tests passed!")
        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)
    asyncio.run(run())
