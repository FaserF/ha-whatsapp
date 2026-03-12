"""Shared Home Assistant stub modules for testing."""

import logging
import sys
import types
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

_LOGGER = logging.getLogger(__name__)

# --- Singleton Classes to ensure identity across reloads ---


def _get_or_create_class(name: str, base: type = object) -> type:
    attr = f"_ha_stub_{name}"
    if not hasattr(sys, attr):
        # Create the class
        if base == Exception:

            class StubException(Exception):
                pass

            cls = StubException
        else:

            class StubClass(base):
                pass

            cls = StubClass

        cls.__name__ = name
        # Determine module name
        mod_prefix = "homeassistant"
        if name in ["HomeAssistantError", "ServiceValidationError"]:
            mod_prefix = "homeassistant.exceptions"
        elif name in ["DataUpdateCoordinator", "CoordinatorEntity"]:
            mod_prefix = "homeassistant.helpers.update_coordinator"
        elif name in ["ConfigFlow", "OptionsFlow"]:
            mod_prefix = "homeassistant.config_entries"

        cls.__module__ = mod_prefix
        setattr(sys, attr, cls)

    return getattr(sys, attr)


# Exceptions
HomeAssistantError = _get_or_create_class("HomeAssistantError", Exception)
ServiceValidationError = _get_or_create_class(
    "ServiceValidationError", HomeAssistantError
)


# Core
class ServiceCall:
    def __init__(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> None:
        self.domain = domain
        self.service = service
        self.data = data or {}


class Bus:
    def __init__(self) -> None:
        self.async_fire = MagicMock()


# Const
class Platform:
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    NOTIFY = "notify"
    SENSOR = "sensor"


class EntityCategory:
    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


# Helpers
# Use _get_or_create_class for Coordinator to ensure identity
_DataUpdateCoordinatorBase = _get_or_create_class("DataUpdateCoordinator")


class DataUpdateCoordinator(_DataUpdateCoordinatorBase):
    def __init__(self, hass: Any, *_args: Any, **kwargs: Any) -> None:
        self.hass = hass
        self.data: Any = {"connected": True, "stats": {"sent": 0, "failed": 0}}
        self._listeners: list[Callable[[], None]] = []
        if "config_entry" in kwargs:
            self.config_entry = kwargs["config_entry"]

    def __class_getitem__(cls, _: Any) -> Any:
        return cls

    async def async_config_entry_first_refresh(self) -> None:
        if hasattr(self, "_async_update_data"):
            res = self._async_update_data()
            if hasattr(res, "__await__"):
                self.data = await res
            else:
                self.data = res

    async def async_refresh(self) -> None:
        await self.async_config_entry_first_refresh()
        for listener in list(self._listeners):
            listener()

    def async_add_listener(
        self, update_callback: Callable[[], None]
    ) -> Callable[[], None]:
        self._listeners.append(update_callback)
        return lambda: self._listeners.remove(update_callback)


_CoordinatorEntityBase = _get_or_create_class("CoordinatorEntity")


class CoordinatorEntity(_CoordinatorEntityBase):
    def __init__(self, coordinator: Any) -> None:
        self.coordinator = coordinator
        self.hass: Any = None
        self.entity_id: str | None = None
        coordinator.async_add_listener(self.async_write_ha_state)

    def __class_getitem__(cls, _: Any) -> Any:
        return cls

    def async_write_ha_state(self) -> None:
        if self.hass and self.entity_id:
            state = getattr(self, "state", None)
            if state is None:
                native = getattr(self, "native_value", None)
                if native is not None:
                    state = str(native)
            if hasattr(self, "is_on"):
                state = "on" if self.is_on else "off"

            self.hass.states.async_set_state(
                self.entity_id, state, getattr(self, "extra_state_attributes", {})
            )


# Flow
class FlowResultType:
    FORM = "form"
    ABORT = "abort"
    CREATE_ENTRY = "create_entry"


class ConfigFlow:
    def __init_subclass__(cls, **_kwargs: Any) -> None:
        pass

    def __init__(self) -> None:
        self.hass: Any = None

    def async_show_form(self, step_id: str, **_kwargs: Any) -> dict[str, Any]:
        return {"type": "form", "step_id": step_id}

    def async_create_entry(self, title: str, data: Any) -> dict[str, Any]:
        return {"type": "create_entry", "title": title, "data": data, "version": 1}


class OptionsFlow:
    def __init_subclass__(cls, **_kwargs: Any) -> None:
        pass

    def __init__(self, config_entry: Any) -> None:
        self.config_entry = config_entry
        self.hass: Any = None


class RepairsFlow(ConfigFlow):
    pass


class ConfirmRepairFlow(RepairsFlow):
    pass


# --- Utilities ---


def redact(data: Any, keys: list[str]) -> Any:
    if isinstance(data, dict):
        return {
            k: "**REDACTED**" if k in keys else redact(v, keys) for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact(item, keys) for item in data]
    return data


def _stub(name: str, **kwargs: Any) -> Any:
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


def mock_add_entities(
    hass: Any, entities: list[Any], update_before_add: bool = False
) -> None:
    for entity in entities:
        entity.hass = hass
        if not getattr(entity, "entity_id", None):
            domain = "sensor"
            if hasattr(entity, "is_on"):
                domain = "binary_sensor"

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


class MockConfigEntry:
    def __init__(
        self,
        domain: str,
        data: dict[str, Any],
        title: str = "WhatsApp",
        entry_id: str | None = None,
        options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.domain = domain
        self.data = data or {}
        if entry_id is None:
            import uuid

            entry_id = uuid.uuid4().hex
        self.entry_id = entry_id
        self.options = options or {}
        self.title = title
        self.unique_id = kwargs.get("unique_id")
        self.version = kwargs.get("version", 1)

    def async_on_unload(self, func: Callable[..., Any]) -> None:
        pass

    def add_update_listener(self, func: Callable[..., Any]) -> Callable[[], None]:
        return lambda: None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "domain": self.domain,
            "title": self.title,
            "data": self.data,
            "options": self.options,
            "unique_id": self.unique_id,
            "version": self.version,
        }

    def add_to_hass(self, hass: Any) -> None:
        if "entries" not in hass.data:
            hass.data["entries"] = {}
        hass.data["entries"][self.entry_id] = self
        if "whatsapp" not in hass.data:
            hass.data["whatsapp"] = {}


def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""
    if sys.modules.get("homeassistant") and getattr(
        sys.modules["homeassistant"], "_is_stub", False
    ):
        return

    _LOGGER.debug("Building HA stubs...")

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
        EntityCategory=EntityCategory,
    )

    # homeassistant.helpers
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
    vol_mod.Any = lambda *a, **_: a[0]
    vol_mod.Marker = object
    vol_mod.In = lambda x: x
    vol_mod.All = lambda *x: x[0]
    vol_mod.Length = lambda **x: x
    vol_mod.Coerce = lambda x: x

    # Finalize parents
    ha = _stub("homeassistant")
    ha.core = sys.modules["homeassistant.core"]
    ha.exceptions = sys.modules["homeassistant.exceptions"]
    ha.const = sys.modules["homeassistant.const"]
    ha.helpers = sys.modules["homeassistant.helpers"]
    ha.helpers.update_coordinator = sys.modules[
        "homeassistant.helpers.update_coordinator"
    ]
    ha.helpers.config_validation = cv_mod
    ha.helpers.entity_registry = sys.modules["homeassistant.helpers.entity_registry"]
    ha.helpers.issue_registry = ir_mod
    ha.helpers.entity_platform = platform_mod
    ha.helpers.typing = sys.modules["homeassistant.helpers.typing"]

    components = _stub("homeassistant.components")
    ha.components = components
    components.notify = sys.modules["homeassistant.components.notify"]

    # components.binary_sensor / sensor
    _stub(
        "homeassistant.components.binary_sensor",
        BinarySensorDeviceClass=MagicMock(),
        BinarySensorEntity=object,
    )
    _stub(
        "homeassistant.components.sensor",
        SensorDeviceClass=MagicMock(),
        SensorEntity=object,
        SensorStateClass=MagicMock(),
    )

    # components.diagnostics
    components.diagnostics = _stub(
        "homeassistant.components.diagnostics", async_redact_data=redact
    )

    # helpers.service
    ha.helpers.service = _stub(
        "homeassistant.helpers.service", async_register_admin_service=MagicMock()
    )

    # components.repairs
    repairs_mod = _stub(
        "homeassistant.components.repairs",
        RepairsFlow=RepairsFlow,
        ConfirmRepairFlow=ConfirmRepairFlow,
    )
    components.repairs = repairs_mod

    # homeassistant.util
    util_mod = _stub(
        "homeassistant.util", slugify=lambda x: x.lower().replace(" ", "_")
    )
    import datetime

    dt_mod = _stub(
        "homeassistant.util.dt",
        utcnow=lambda: datetime.datetime.now(datetime.UTC),
        now=lambda: datetime.datetime.now(),
        as_local=lambda dt: dt,
    )
    util_mod.dt = dt_mod
    util_mod.search_web = _stub(
        "homeassistant.util.search_web", is_safe_url=lambda _: True
    )

    # pytest_homeassistant_custom_component.common
    pytest_ha_mod = _stub("pytest_homeassistant_custom_component")
    pytest_ha_common_mod = _stub(
        "pytest_homeassistant_custom_component.common", MockConfigEntry=MockConfigEntry
    )
    pytest_ha_mod.common = pytest_ha_common_mod

    ha._is_stub = True
