"""Tests for the message quoting functionality.

These tests verify that the notify platform correctly extracts the
`quoted_message_id` from notification data and passes it through to the
underlying API client.  All Home Assistant module dependencies are mocked
out so that the tests run in a plain Python environment without a full
Home Assistant installation.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal stubs for Home Assistant modules that are imported at module load
# time by the integration source files.
# ---------------------------------------------------------------------------


def _build_ha_stub_modules() -> None:
    """Create lightweight stub modules so `import homeassistant.*` works."""

    # Root package
    ha_pkg = types.ModuleType("homeassistant")
    sys.modules.setdefault("homeassistant", ha_pkg)

    # homeassistant.exceptions
    exceptions_mod = types.ModuleType("homeassistant.exceptions")

    class HomeAssistantError(Exception):
        """Stub for HomeAssistantError."""

    exceptions_mod.HomeAssistantError = HomeAssistantError  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.exceptions", exceptions_mod)
    ha_pkg.exceptions = exceptions_mod  # type: ignore[attr-defined]

    # homeassistant.components.notify
    notify_mod = types.ModuleType("homeassistant.components.notify")
    notify_mod.ATTR_DATA = "data"  # type: ignore[attr-defined]
    notify_mod.ATTR_MESSAGE = "message"  # type: ignore[attr-defined]
    notify_mod.ATTR_TARGET = "target"  # type: ignore[attr-defined]
    notify_mod.BaseNotificationService = object  # type: ignore[attr-defined]
    notify_mod.NotifyEntity = object  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.components.notify", notify_mod)
    components_mod = sys.modules.setdefault(
        "homeassistant.components", types.ModuleType("homeassistant.components")
    )
    components_mod.notify = notify_mod  # type: ignore[attr-defined]

    # homeassistant.helpers.update_coordinator
    coordinator_mod = types.ModuleType("homeassistant.helpers.update_coordinator")

    class _GenericBase:
        """Stub base that supports generic subscript.

        Example: DataUpdateCoordinator[int].
        """

        def __class_getitem__(cls, item: object) -> type:
            """Return the class itself so subscript doesn't fail."""
            return cls

    class CoordinatorEntity(_GenericBase):
        """Stub CoordinatorEntity that accepts and stores a coordinator."""

        def __init__(self, coordinator: object) -> None:
            """Store coordinator reference."""
            self.coordinator = coordinator

    coordinator_mod.CoordinatorEntity = CoordinatorEntity  # type: ignore[attr-defined]

    class DataUpdateCoordinator(_GenericBase):
        """Stub DataUpdateCoordinator."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialise the stub."""

    coordinator_mod.DataUpdateCoordinator = DataUpdateCoordinator  # type: ignore[attr-defined]
    coordinator_mod.UpdateFailed = Exception  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.helpers.update_coordinator", coordinator_mod)

    # homeassistant.helpers.config_validation (cv)
    cv_mod = types.ModuleType("homeassistant.helpers.config_validation")
    cv_mod.string = str  # type: ignore[attr-defined]
    cv_mod.ensure_list = list  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.helpers.config_validation", cv_mod)

    # homeassistant.helpers (namespace)
    helpers_mod = sys.modules.setdefault(
        "homeassistant.helpers", types.ModuleType("homeassistant.helpers")
    )
    helpers_mod.config_validation = cv_mod  # type: ignore[attr-defined]
    helpers_mod.update_coordinator = coordinator_mod  # type: ignore[attr-defined]

    # homeassistant.helpers.entity_platform
    ep_mod = types.ModuleType("homeassistant.helpers.entity_platform")
    ep_mod.AddEntitiesCallback = object  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.helpers.entity_platform", ep_mod)
    helpers_mod.entity_platform = ep_mod  # type: ignore[attr-defined]

    # homeassistant.helpers.typing
    ht_mod = types.ModuleType("homeassistant.helpers.typing")
    ht_mod.ConfigType = dict  # type: ignore[attr-defined]
    ht_mod.DiscoveryInfoType = dict  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.helpers.typing", ht_mod)

    # homeassistant.config_entries
    class ConfigEntry:
        """Stub for homeassistant.config_entries.ConfigEntry."""

        entry_id: str

    ce_mod = types.ModuleType("homeassistant.config_entries")
    ce_mod.ConfigEntry = ConfigEntry  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.config_entries", ce_mod)
    ha_pkg.config_entries = ce_mod  # type: ignore[attr-defined]
    helpers_mod.typing = ht_mod  # type: ignore[attr-defined]

    # homeassistant.config_entries
    ce_mod = types.ModuleType("homeassistant.config_entries")
    ce_mod.ConfigEntry = object  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.config_entries", ce_mod)
    ha_pkg.config_entries = ce_mod  # type: ignore[attr-defined]

    # homeassistant.core
    core_mod = types.ModuleType("homeassistant.core")
    core_mod.HomeAssistant = object  # type: ignore[attr-defined]
    core_mod.callback = lambda f: f  # type: ignore[attr-defined]

    class ServiceCall:  # noqa: D101
        """Stub for HomeAssistant ServiceCall."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            """Initialise the stub."""

    core_mod.ServiceCall = ServiceCall  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.core", core_mod)
    ha_pkg.core = core_mod  # type: ignore[attr-defined]

    # homeassistant.const
    const_mod = types.ModuleType("homeassistant.const")
    const_mod.CONF_URL = "url"  # type: ignore[attr-defined]

    class Platform:  # noqa: D101
        """Stub for HA Platform enum."""

        BINARY_SENSOR = "binary_sensor"
        NOTIFY = "notify"
        SENSOR = "sensor"

    const_mod.Platform = Platform  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.const", const_mod)
    ha_pkg.const = const_mod  # type: ignore[attr-defined]

    # homeassistant.exceptions – extend with ServiceValidationError
    exceptions_mod = sys.modules["homeassistant.exceptions"]

    class ServiceValidationError(Exception):
        """Stub for ServiceValidationError."""

    exceptions_mod.ServiceValidationError = ServiceValidationError  # type: ignore[attr-defined]

    # homeassistant.helpers.issue_registry
    ir_mod = types.ModuleType("homeassistant.helpers.issue_registry")
    ir_mod.async_create_issue = MagicMock()  # type: ignore[attr-defined]
    ir_mod.async_delete_issue = MagicMock()  # type: ignore[attr-defined]
    ir_mod.IssueSeverity = MagicMock()  # type: ignore[attr-defined]
    sys.modules.setdefault("homeassistant.helpers.issue_registry", ir_mod)
    helpers_mod = sys.modules["homeassistant.helpers"]
    helpers_mod.issue_registry = ir_mod  # type: ignore[attr-defined]

    # voluptuous
    vol_mod = types.ModuleType("voluptuous")
    vol_mod.Schema = lambda s, **_: s  # type: ignore[attr-defined]
    vol_mod.Optional = lambda *a, **_: a[0]  # type: ignore[attr-defined]
    vol_mod.Required = lambda *a, **_: a[0]  # type: ignore[attr-defined]
    vol_mod.All = lambda *a, **_: a[0]  # type: ignore[attr-defined]
    sys.modules.setdefault("voluptuous", vol_mod)


_build_ha_stub_modules()

# Now it is safe to import the integration modules.
from custom_components.whatsapp.notify import WhatsAppNotificationEntity  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------



@pytest.fixture
def mock_client() -> Generator[AsyncMock, None, None]:
    """Fixture to mock WhatsAppApiClient."""
    with patch(
        "custom_components.whatsapp.notify.WhatsAppApiClient", autospec=True
    ) as mock:
        mock.is_allowed.return_value = True
        mock.ensure_jid.return_value = "1234567890@s.whatsapp.net"
        yield mock


@pytest.fixture
def notify_entity(mock_client: AsyncMock) -> WhatsAppNotificationEntity:
    """Fixture to create WhatsAppNotificationEntity instance."""
    coordinator = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    return WhatsAppNotificationEntity(mock_client, entry, coordinator)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_send_message_with_quote(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that ``quote`` in data is forwarded as ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="Hello",
        target=["1234567890"],
        data={"quote": "msg_id_123"},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "Hello", quoted_message_id="msg_id_123"
    )


async def test_send_message_with_reply_to(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that ``reply_to`` in data is forwarded as ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="World",
        target=["1234567890"],
        data={"reply_to": "msg_id_456"},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "World", quoted_message_id="msg_id_456"
    )


async def test_send_message_without_quote(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that a plain message is sent without ``quoted_message_id``."""
    await notify_entity.async_send_message(
        message="Plain message",
        target=["1234567890"],
        data={},
    )

    mock_client.send_message.assert_called_once_with(
        "1234567890", "Plain message", quoted_message_id=None
    )


async def test_send_message_to_multiple_targets(
    notify_entity: WhatsAppNotificationEntity,
    mock_client: AsyncMock,
) -> None:
    """Test that quoting works correctly for multiple targets."""
    await notify_entity.async_send_message(
        message="Hi all",
        target=["111", "222"],
        data={"quote": "q_id"},
    )

    assert mock_client.send_message.call_count == 2
    calls = mock_client.send_message.call_args_list
    assert calls[0].args == ("111", "Hi all")
    assert calls[0].kwargs == {"quoted_message_id": "q_id"}
    assert calls[1].args == ("222", "Hi all")
    assert calls[1].kwargs == {"quoted_message_id": "q_id"}
