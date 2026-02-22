"""Shared Home Assistant stub modules for testing."""

import sys
import types
from unittest.mock import MagicMock, AsyncMock

# homeassistant.exceptions
class HomeAssistantError(Exception):
    """Stub."""


class ServiceValidationError(HomeAssistantError):
    """Stub."""


# homeassistant.core
class ServiceCall:
    """Stub."""

    def __init__(self, domain, service, data=None, context=None):
        self.domain = domain
        self.service = service
        self.data = data or {}


class Bus:
    """Stub."""
    # Must be on class for patch() to work
    async_fire = MagicMock()


# homeassistant.const
class Platform:
    """Stub."""

    BINARY_SENSOR = "binary_sensor"
    NOTIFY = "notify"
    SENSOR = "sensor"


class EntityCategory:
    """Stub."""

    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


# homeassistant.helpers.update_coordinator
class _GenericBase:
    def __class_getitem__(cls, item):
        return cls


class CoordinatorEntity(_GenericBase):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.hass = None
        self.entity_id = None
        coordinator.async_add_listener(self.async_write_ha_state)

    def async_write_ha_state(self):
        if self.hass and self.entity_id:
            state = getattr(self, "state", None)
            if state is None:
                native = getattr(self, "native_value", None)
                if native is not None:
                    state = str(native)
            if hasattr(self, "is_on"):
                state = "on" if self.is_on else "off"

            self.hass.states.async_set_state(
                self.entity_id,
                state,
                getattr(self, "extra_state_attributes", {})
            )


class DataUpdateCoordinator(_GenericBase):
    def __init__(self, hass, *args, **kwargs):
        self.data = {"connected": True, "stats": {"sent": 0, "failed": 0}}
        self.hass = hass
        self._listeners = []
        if "config_entry" in kwargs:
            self.config_entry = kwargs["config_entry"]

    async def async_config_entry_first_refresh(self):
        if hasattr(self, "_async_update_data"):
             try:
                 res = self._async_update_data()
                 if hasattr(res, "__await__"):
                     self.data = await res
                 else:
                     self.data = res
             except Exception as e:
                 print(f"Refresh failed: {e}")

    async def async_refresh(self):
        if hasattr(self, "_async_update_data"):
             try:
                 res = self._async_update_data()
                 if hasattr(res, "__await__"):
                     self.data = await res
                 else:
                     self.data = res
             except Exception as e:
                 print(f"Refresh failed: {e}")
        for listener in self._listeners:
            if callable(listener):
                listener()

    def async_add_listener(self, update_callback):
        self._listeners.append(update_callback)
        return lambda: self._listeners.remove(update_callback)


# homeassistant.data_entry_flow
class FlowResultType:
    FORM = "form"
    ABORT = "abort"
    CREATE_ENTRY = "create_entry"


# homeassistant.components.repairs
class ConfigFlow:
    def __init_subclass__(cls, **kwargs):
        pass


class OptionsFlow:
    def __init_subclass__(cls, **kwargs):
        pass


class RepairsFlow:
    def __init__(self):
        self.hass = None

    def async_show_form(self, step_id, data_schema=None, description_placeholders=None):
        return {"type": "form", "step_id": step_id}

    def async_create_entry(self, title, data):
        return {"type": "create_entry", "version": 1}


class ConfirmRepairFlow(RepairsFlow):
    def __init__(self):
        super().__init__()


def redact(data, keys):
    if isinstance(data, dict):
        return {
            k: "**REDACTED**" if k in keys else redact(v, keys)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact(item, keys) for item in data]
    return data


def _stub(name, **kwargs):
    """Stub a module."""
    if name in sys.modules:
        mod = sys.modules[name]
    else:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    mod.__path__ = []
    for k, v in kwargs.items():
        setattr(mod, k, v)
    mod._is_stub = True
    return mod

stub = _stub


def mock_add_entities(entities, update_before_add=False):
    hass = sys.modules.get("conftest_hass")
    for entity in entities:
        entity.hass = hass
        if not entity.entity_id:
            domain = "sensor"
            if hasattr(entity, "is_on"):
                domain = "binary_sensor"

            # Use _stat_key if present (WhatsAppStatSensor), else translation_key, else name
            if domain == "sensor" and hasattr(entity, "_stat_key") and entity._stat_key:
                stat = entity._stat_key
                if stat == "uptime":
                    entity.entity_id = "sensor.whatsapp_uptime"
                else:
                    entity.entity_id = f"sensor.whatsapp_messages_{stat}"
            elif domain == "binary_sensor":
                entity.entity_id = "binary_sensor.whatsapp"
            elif hasattr(entity, "translation_key") and entity.translation_key:
                entity.entity_id = f"{domain}.whatsapp_{entity.translation_key}"
            elif hasattr(entity, "name") and entity.name:
                name = entity.name.lower().replace(" ", "_")
                entity.entity_id = f"{domain}.{name}"
            else:
                entity.entity_id = f"{domain}.whatsapp"

        entity.async_write_ha_state()

def _dt_utcnow():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc)

def _dt_now():
    import datetime
    return datetime.datetime.now()

class _MockDT:
    @staticmethod
    def utcnow(): return _dt_utcnow()
    @staticmethod
    def now(): return _dt_now()
    @staticmethod
    def as_local(dt): return dt
    @staticmethod
    def utc_from_timestamp(ts):
        import datetime
        return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


class MockConfigEntry:
    def __init__(self, domain="whatsapp", data=None, entry_id=None, options=None, title="WhatsApp", **kwargs):
        self.domain = domain
        self.data = data or {}
        self.entry_id = entry_id or "test_entry"
        self.options = options or {}
        self.title = title
        self.unique_id = kwargs.get("unique_id")
        self.version = kwargs.get("version", 1)

    def async_on_unload(self, func):
        pass

    def add_update_listener(self, func):
        return lambda: None

    def as_dict(self):
        return {
            "entry_id": self.entry_id,
            "domain": self.domain,
            "title": self.title,
            "data": self.data,
            "options": self.options,
            "unique_id": self.unique_id,
            "version": self.version,
        }

    def add_to_hass(self, hass):
        if "entries" not in hass.data:
            hass.data["entries"] = {}
        hass.data["entries"][self.entry_id] = self
        if "whatsapp" not in hass.data:
            hass.data["whatsapp"] = {}


def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""
    if "homeassistant" in sys.modules and getattr(sys.modules["homeassistant"], "_is_stub", False):
        return

    # homeassistant.exceptions
    _stub(
        "homeassistant.exceptions",
        HomeAssistantError=HomeAssistantError,
        ServiceValidationError=ServiceValidationError,
    )

    # homeassistant.core
    _stub(
        "homeassistant.core",
        HomeAssistant=object,
        callback=lambda f: f,
        ServiceCall=ServiceCall,
        Bus=Bus,
    )

    # homeassistant.const
    _stub(
        "homeassistant.const",
        CONF_URL="url",
        CONF_API_KEY="api_key",
        Platform=Platform,
        EntityCategory=EntityCategory
    )

    helpers = _stub("homeassistant.helpers")

    # homeassistant.helpers.update_coordinator
    _stub(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=DataUpdateCoordinator,
        CoordinatorEntity=CoordinatorEntity,
        UpdateFailed=Exception,
    )

    # homeassistant.helpers.config_validation
    cv_mod = _stub(
        "homeassistant.helpers.config_validation",
        string=str,
        ensure_list=list,
        boolean=bool,
        match_all=lambda x: x,
    )

    # homeassistant.helpers.entity_registry
    _stub(
        "homeassistant.helpers.entity_registry",
        async_get=MagicMock(),
        async_entries_for_config_entry=MagicMock(),
    )

    # homeassistant.helpers.issue_registry
    ir_mod = _stub(
        "homeassistant.helpers.issue_registry",
        async_get=MagicMock(),
        IssueSeverity=MagicMock(),
        async_delete_issue=MagicMock(),
        async_create_issue=MagicMock(),
    )
    helpers.issue_registry = ir_mod

    # homeassistant.helpers.entity_platform
    platform_mod = _stub("homeassistant.helpers.entity_platform")
    platform_mod.AddEntitiesCallback = mock_add_entities

    # homeassistant.helpers.typing
    _stub("homeassistant.helpers.typing", ConfigType=dict, DiscoveryInfoType=dict)

    # homeassistant.components.notify
    _stub(
        "homeassistant.components.notify",
        ATTR_DATA="data",
        ATTR_MESSAGE="message",
        ATTR_TARGET="target",
        BaseNotificationService=object,
        NotifyEntity=object,
    )

    # homeassistant.data_entry_flow
    _stub(
        "homeassistant.data_entry_flow",
        FlowResultType=FlowResultType,
        AbortFlow=Exception,
        FlowResult=dict,
    )

    # homeassistant.config_entries
    _stub(
        "homeassistant.config_entries",
        ConfigEntry=object,
        ConfigFlow=ConfigFlow,
        OptionsFlow=OptionsFlow,
        SOURCE_USER="user",
        SOURCE_REAUTH="reauth",
    )

    # voluptuous
    vol_mod = _stub("voluptuous")
    vol_mod.Schema = lambda s, **_: s
    vol_mod.Optional = lambda *a, **_: a[0]
    vol_mod.Required = lambda *a, **_: a[0]
    vol_mod.Marker = object
    vol_mod.In = lambda x: x
    vol_mod.All = lambda *x: x[0]
    vol_mod.Length = lambda **x: x
    vol_mod.Coerce = lambda x: x

    # Ensure parents exist and have children attributes
    ha = _stub("homeassistant")
    ha.core = sys.modules["homeassistant.core"]
    ha.exceptions = sys.modules["homeassistant.exceptions"]
    ha.const = sys.modules["homeassistant.const"]
    helpers = sys.modules["homeassistant.helpers"]
    ha.helpers = helpers
    helpers.update_coordinator = sys.modules["homeassistant.helpers.update_coordinator"]
    helpers.config_validation = cv_mod
    helpers.entity_registry = sys.modules["homeassistant.helpers.entity_registry"]
    helpers.issue_registry = ir_mod
    ha.helpers.issue_registry = ir_mod
    helpers.entity_platform = platform_mod
    helpers.typing = sys.modules["homeassistant.helpers.typing"]

    components = _stub("homeassistant.components")
    ha.components = components
    components.notify = sys.modules["homeassistant.components.notify"]

    # homeassistant.components.binary_sensor
    _stub("homeassistant.components.binary_sensor", BinarySensorDeviceClass=MagicMock(), BinarySensorEntity=object)
    # homeassistant.components.sensor
    _stub("homeassistant.components.sensor", SensorDeviceClass=MagicMock(), SensorEntity=object, SensorStateClass=MagicMock())

    # homeassistant.components.diagnostics
    diag_mod = _stub("homeassistant.components.diagnostics", async_redact_data=redact)
    components.diagnostics = diag_mod

    # homeassistant.helpers.service
    _stub("homeassistant.helpers.service", async_register_admin_service=MagicMock())
    helpers.service = sys.modules["homeassistant.helpers.service"]

    # homeassistant.components.repairs
    repairs_mod = _stub("homeassistant.components.repairs")
    repairs_mod.RepairsFlow = RepairsFlow
    repairs_mod.ConfirmRepairFlow = ConfirmRepairFlow
    components.repairs = repairs_mod

    # homeassistant.util
    util_mod = _stub("homeassistant.util", slugify=lambda x: x.lower().replace(" ", "_"))
    dt_mod = _stub("homeassistant.util.dt", utcnow=lambda: None, now=lambda: None)
    util_mod.dt = dt_mod
    sw_mod = _stub("homeassistant.util.search_web", is_safe_url=lambda x: True)
    util_mod.search_web = sw_mod

    # pytest_homeassistant_custom_component.common
    pytest_ha_mod = _stub("pytest_homeassistant_custom_component")
    pytest_ha_common_mod = _stub("pytest_homeassistant_custom_component.common")
    pytest_ha_common_mod.MockConfigEntry = MockConfigEntry
    pytest_ha_mod.common = pytest_ha_common_mod

    # Mark as stub
    ha._is_stub = True
