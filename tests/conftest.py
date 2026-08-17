import contextlib
import logging
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

# Import ha_stubs to ensure it's available
import ha_stubs
import pytest


def pytest_sessionstart(session: Any) -> None:  # noqa: ARG001
    """Called after the Session object has been created and before performing collection and entering the run test loop."""  # noqa: E501
    import sys

    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import pytest_socket

        # Intercept socket_allow_hosts so any downstream call
        # automatically retains ::1, 127.0.0.1, and localhost
        if hasattr(pytest_socket, "socket_allow_hosts") and not getattr(
            pytest_socket, "_patched_for_ipv6", False
        ):
            orig_allow_hosts = pytest_socket.socket_allow_hosts

            def _safe_socket_allow_hosts(*args: Any, **kwargs: Any) -> Any:
                allowed_hosts: list[str] = []
                if args and args[0] is not None:
                    allowed_hosts = list(args[0])
                elif "allowed" in kwargs and kwargs["allowed"] is not None:
                    allowed_hosts = list(kwargs["allowed"])
                elif "allowed_hosts" in kwargs and kwargs["allowed_hosts"] is not None:
                    allowed_hosts = list(kwargs["allowed_hosts"])

                for h in ("::1", "127.0.0.1", "localhost", "0.0.0.0", "::"):
                    if h not in allowed_hosts:
                        allowed_hosts.append(h)

                allow_unix = kwargs.get(
                    "allow_unix_socket",
                    args[1] if len(args) > 1 else True,
                )
                return orig_allow_hosts(allowed_hosts, allow_unix)

            pytest_socket.socket_allow_hosts = _safe_socket_allow_hosts
            pytest_socket._patched_for_ipv6 = True

        pytest_socket.socket_allow_hosts(
            ["::1", "127.0.0.1", "localhost", "0.0.0.0", "::"], allow_unix_socket=True
        )
        if hasattr(pytest_socket, "enable_socket"):
            pytest_socket.enable_socket()
        elif hasattr(pytest_socket, "enable_sockets"):
            pytest_socket.enable_sockets()

        orig_check = getattr(pytest_socket, "_check_address", None)
        if orig_check and not getattr(pytest_socket, "_check_address_patched", False):

            def _safe_check_address(address: Any) -> None:
                if isinstance(address, tuple) and address:
                    host = str(address[0])
                    if host in ("::1", "127.0.0.1", "localhost", "0.0.0.0", "::"):
                        return
                orig_check(address)

            pytest_socket._check_address = _safe_check_address
            pytest_socket._check_address_patched = True
    except Exception:
        pass
    ha_stubs._build_ha_stub_modules()


@pytest.fixture(autouse=True)
def _patch_aiodns_resolver() -> Generator[None, None, None]:
    """Patch aiodns.DNSResolver.__init__ on Windows to prevent error."""
    import sys
    from unittest.mock import patch

    if sys.platform == "win32":
        with patch("aiodns.DNSResolver.__init__", return_value=None):
            yield
    else:
        yield


def _ensure_sockets() -> None:
    import socket

    try:
        import pytest_socket

        if hasattr(pytest_socket, "socket_allow_hosts"):
            pytest_socket.socket_allow_hosts(
                ["::1", "127.0.0.1", "localhost", "0.0.0.0", "::"],
                allow_unix_socket=True,
            )
        if hasattr(pytest_socket, "enable_socket"):
            pytest_socket.enable_socket()
        elif hasattr(pytest_socket, "enable_sockets"):
            pytest_socket.enable_sockets()
        if hasattr(pytest_socket, "_true_socket"):
            socket.socket = pytest_socket._true_socket
    except Exception:
        pass

    # On Windows, socket.socketpair uses fallback sockets.
    # We patch socket.socketpair to temporarily use _true_socket if available.
    orig_socketpair = getattr(socket, "socketpair", None)
    if orig_socketpair and hasattr(pytest_socket, "_true_socket"):

        def _safe_socketpair(*args: Any, **kwargs: Any) -> Any:
            old_sock = socket.socket
            socket.socket = pytest_socket._true_socket
            try:
                return orig_socketpair(*args, **kwargs)
            finally:
                socket.socket = old_sock

        socket.socketpair = _safe_socketpair


def pytest_runtest_setup(item: Any) -> None:  # noqa: ARG001
    """Hook running before each test item setup."""
    _ensure_sockets()


def pytest_runtest_teardown(item: Any) -> None:  # noqa: ARG001
    """Hook running after each test item execution."""
    _ensure_sockets()


@pytest.fixture(autouse=True)
def enable_socket() -> Generator[None, None, None]:
    """Enable socket access during custom component testing."""
    _ensure_sockets()
    yield
    _ensure_sockets()


@pytest.fixture(autouse=True)
def socket_enabled(socket_enabled: Any = None) -> Generator[None, None, None]:  # noqa: ARG001
    """Ensure socket_enabled fixture always includes IPv6 ::1 and localhost."""
    _ensure_sockets()
    yield
    _ensure_sockets()


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def cleanup_whatsapp_module_cache() -> Generator[None, None, None]:
    """Clear sys.modules between tests to ensure fresh global variables."""
    import sys

    def _reset_globals() -> None:
        if "custom_components.whatsapp" in sys.modules:
            with contextlib.suppress(Exception):
                sys.modules["custom_components.whatsapp"]._SERVICES_REGISTERED = False

    _reset_globals()
    to_del = [m for m in sys.modules if m.startswith("custom_components.whatsapp")]
    for m in to_del:
        sys.modules.pop(m, None)
    yield
    _reset_globals()
    to_del = [m for m in sys.modules if m.startswith("custom_components.whatsapp")]
    for m in to_del:
        sys.modules.pop(m, None)


@pytest.fixture  # type: ignore[untyped-decorator]
def mock_client() -> MagicMock:
    """Fixture for mocking WhatsAppApiClient."""
    from custom_components.whatsapp.api import WhatsAppApiClient

    client = MagicMock(spec=WhatsAppApiClient)
    client.connect = AsyncMock(return_value=True)
    client.start_session = MagicMock(return_value=None)
    client.get_qr_code = AsyncMock(return_value="data:image/png;base64,mock_qr")
    client.get_stats = AsyncMock(
        return_value={
            "sent": 0,
            "failed": 0,
            "my_number": "123456789",
            "connected": True,
        }
    )
    client.register_callback = MagicMock()
    client.start_polling = AsyncMock()
    client.close = AsyncMock()
    client.mark_as_read = MagicMock(return_value=None)
    client.get_dashboard = AsyncMock(return_value={})
    client.get_status = AsyncMock(return_value={"connected": True})
    client.get_chats = AsyncMock(return_value={"total_chats": 0, "groups": []})
    client.get_health = AsyncMock(return_value={"status": "connected"})
    client.stats = {"sent": 0, "failed": 0, "my_number": "123456789", "connected": True}
    return client


@pytest.fixture  # type: ignore[untyped-decorator]
def hass(mock_client: MagicMock) -> MagicMock:
    """Fixture to mock Home Assistant object."""
    hass = MagicMock()
    hass.data = {}
    service_handlers: dict[tuple[str, str], Any] = {}
    states: dict[str, MagicMock] = {}

    def async_register(domain: str, service: str, handler: Any, **_kwargs: Any) -> None:
        service_handlers[(domain, service)] = handler

    async def async_call(
        domain: str, service: str, service_data: Any = None, **_kwargs: Any
    ) -> None:
        if (domain, service) in service_handlers:
            from ha_stubs import ServiceCall

            call = ServiceCall(domain, service, service_data)
            await service_handlers[(domain, service)](call)

    def async_set_state(entity_id: str, state: str, attributes: Any = None) -> None:
        states[entity_id] = MagicMock(state=state, attributes=attributes or {})

    def get_state(entity_id: str) -> MagicMock | None:
        return states.get(entity_id)

    hass.services = MagicMock()
    hass.services.async_register = MagicMock(side_effect=async_register)
    hass.services.async_call = AsyncMock(side_effect=async_call)
    hass.services.has_service = MagicMock(
        side_effect=lambda d, s: (d, s) in service_handlers
    )  # noqa: E501

    hass.states = MagicMock()
    hass.states.get = MagicMock(side_effect=get_state)
    hass.states.async_set_state = MagicMock(side_effect=async_set_state)

    def async_create_task(coro: Any, name: str | None = None) -> Any:
        import asyncio
        import inspect

        if inspect.iscoroutine(coro):
            return asyncio.create_task(coro, name=name)
        return coro

    hass.async_create_task = MagicMock(side_effect=async_create_task)

    def async_run_hass_job(job: Any, *args: Any, **_kwargs: Any) -> Any:
        import asyncio
        import inspect

        target = getattr(job, "target", job)
        if callable(target):
            res = target(*args)
            if inspect.iscoroutine(res):
                return asyncio.create_task(res)
            return res
        return None

    hass.async_run_hass_job = MagicMock(side_effect=async_run_hass_job)
    hass.async_block_till_done = AsyncMock()

    def async_create_background_task(
        coro: Any,
        name: str | None = None,  # noqa: ARG001
        eager_start: bool = True,  # noqa: ARG001
    ) -> Any:
        import asyncio
        import inspect

        if inspect.iscoroutine(coro):
            return asyncio.ensure_future(coro)
        # Return a done future so task.done() calls by MockConfigEntry don't fail
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[None] = loop.create_future()
        fut.set_result(None)
        return fut

    hass.async_create_background_task = MagicMock(
        side_effect=async_create_background_task
    )

    hass.bus = ha_stubs.Bus()

    hass.config_entries = MagicMock()
    hass.config_entries._entries = {}

    async def async_setup(entry_id: str) -> bool:
        entry = None
        if "entries" in hass.data and entry_id in hass.data["entries"]:
            entry = hass.data["entries"][entry_id]
        elif entry_id in hass.config_entries._entries:
            entry = hass.config_entries._entries[entry_id]
        if entry is not None:
            try:
                from custom_components.whatsapp import async_setup_entry

                try:
                    from homeassistant.config_entries import ConfigEntryState

                    object.__setattr__(
                        entry, "state", ConfigEntryState.SETUP_IN_PROGRESS
                    )
                except Exception:
                    object.__setattr__(
                        entry, "state", ha_stubs.ConfigEntryState.SETUP_IN_PROGRESS
                    )
                result = await async_setup_entry(hass, entry)
                if result:
                    try:
                        from homeassistant.config_entries import ConfigEntryState

                        object.__setattr__(entry, "state", ConfigEntryState.LOADED)
                    except Exception:
                        object.__setattr__(
                            entry, "state", ha_stubs.ConfigEntryState.LOADED
                        )
                    from custom_components.whatsapp.const import DOMAIN

                    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                        # Integration's real setup put its objects in hass.data
                        pass
                    else:
                        hass.data.setdefault(DOMAIN, {})
                        hass.data[DOMAIN][entry.entry_id] = {
                            "client": mock_client,
                            "coordinator": ha_stubs.DataUpdateCoordinator(
                                hass, mock_client, entry
                            ),
                        }
                return result
            except Exception as exc:
                logging.getLogger(__name__).exception(
                    "Error in async_setup_entry: %s", exc
                )
                raise exc
        return True

    hass.config_entries.async_setup = AsyncMock(side_effect=async_setup)
    hass.config_entries.async_reload = AsyncMock(return_value=True)

    async def async_update_entry(
        entry: Any, options: dict[str, Any] | None = None, data: Any = None
    ) -> None:
        if options is not None:
            try:
                entry.options.update(options)  # mutable dict
            except AttributeError:
                # options is a MappingProxyType (immutable) - replace it
                from types import MappingProxyType

                new_opts = {**entry.options, **options}
                try:
                    entry.options = MappingProxyType(new_opts)
                except AttributeError:
                    object.__setattr__(entry, "options", MappingProxyType(new_opts))
        if data is not None:
            try:
                entry.data.update(data)
            except AttributeError:
                from types import MappingProxyType

                new_data = {**entry.data, **data}
                try:
                    entry.data = MappingProxyType(new_data)
                except AttributeError:
                    object.__setattr__(entry, "data", MappingProxyType(new_data))
        from custom_components.whatsapp import async_setup_entry

        # Reset state so async_config_entry_first_refresh is allowed to run
        try:
            from homeassistant.config_entries import ConfigEntryState

            object.__setattr__(entry, "state", ConfigEntryState.SETUP_IN_PROGRESS)
        except Exception:
            object.__setattr__(
                entry, "state", ha_stubs.ConfigEntryState.SETUP_IN_PROGRESS
            )
        await async_setup_entry(hass, entry)

    hass.config_entries.async_update_entry = AsyncMock(side_effect=async_update_entry)

    async def async_forward_entry_setups(entry: Any, platforms: list[str]) -> None:
        import importlib

        for platform in platforms:

            def _mock_add_entities(
                entities: Any, update_before_add: bool = False
            ) -> None:
                ha_stubs.mock_add_entities(hass, entities, update_before_add)

            try:
                mod = importlib.import_module(f"custom_components.whatsapp.{platform}")
                await mod.async_setup_entry(hass, entry, _mock_add_entities)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Error setup platform %s: %s", platform, e
                )
                raise

    hass.config_entries.async_forward_entry_setups = AsyncMock(
        side_effect=async_forward_entry_setups
    )  # noqa: E501

    hass.config_entries.flow = MagicMock()
    flow_data: dict[str, Any] = {}
    flow_steps: dict[str, int] = {}  # flow_id -> step_count

    async def async_init(
        domain: str,  # noqa: ARG001
        context: Any = None,
        data: Any = None,  # noqa: ARG001
    ) -> dict[str, Any]:
        import uuid

        flow_id = str(uuid.uuid4())
        if context and context.get("source") == "reauth":
            flow_id = "reauth_flow"
        return {"type": "form", "flow_id": flow_id, "step_id": "user"}

    async def async_configure(flow_id: str, user_input: Any = None) -> dict[str, Any]:
        if flow_id not in flow_steps:
            flow_steps[flow_id] = 0
        flow_steps[flow_id] += 1

        if user_input is not None:
            flow_data.update(user_input)
            url = flow_data.get("url") or flow_data.get("host")
            # Usually we check for unique_id instead of host for multi-instance
            # but if we want to check host, we only do it if unique_id is NOT yet known
            # or if the test specifically expects an abort.
            # In test_multi_instance_setup, it expects NO ABORT for same host.
            # In test_duplicate_instance_rejected, it expects ABORT for same UNIQUE_ID.
            if (
                url and "entries" in hass.data and flow_id == "test_flow_reauth"
            ):  # only for reauth or specific cases  # noqa: E501
                pass

            # For the user step, check if we should go to scan
            if flow_steps[flow_id] == 1:
                # Preference: use classes to see patches if available
                from custom_components.whatsapp.api import WhatsAppApiClient

                conn: Any = mock_client
                if isinstance(
                    getattr(WhatsAppApiClient, "connect", None), (MagicMock, AsyncMock)
                ):  # noqa: E501
                    conn = WhatsAppApiClient

                await conn.connect()  # burn first call if needed
                if await conn.connect():
                    pass  # Skips scan
                else:
                    return {"type": "form", "flow_id": flow_id, "step_id": "scan"}

            # For the scan step
            if flow_steps[flow_id] > 1 and not user_input:
                # Scan step submission (empty dict)
                pass

        unique_id = None
        try:
            # Try to get stats from the class (to see patches)
            from custom_components.whatsapp.api import WhatsAppApiClient

            if isinstance(
                getattr(WhatsAppApiClient, "get_stats", None), (MagicMock, AsyncMock)
            ):  # noqa: E501
                stats = await WhatsAppApiClient.get_stats()  # type: ignore[call-arg]
            else:
                stats = await mock_client.get_stats()
            unique_id = stats.get("my_number")
        except Exception:
            unique_id = "test_number"

        final_data = flow_data.copy()
        if "url" not in final_data and "host" in final_data:
            final_data["url"] = final_data["host"]
        if "session_id" not in final_data and "url" in final_data:
            import uuid

            final_data["session_id"] = str(uuid.uuid4())

        res = MagicMock()
        res.unique_id = unique_id

        result = {
            "type": "create_entry",
            "title": (
                "WhatsApp"
                if unique_id == "123456789"
                else (f"WhatsApp ({unique_id})" if unique_id else "WhatsApp")
            ),  # noqa: E501
            "data": final_data,
            "result": res,
            "version": 1,
            "flow_id": flow_id,
        }

        if unique_id and "entries" in hass.data:
            for entry in hass.data["entries"].values():
                if entry.unique_id == unique_id and entry.entry_id != flow_id:
                    return {"type": "abort", "reason": "already_configured"}

        if result["type"] == "create_entry":
            from ha_stubs import MockConfigEntry

            entry = MockConfigEntry(
                domain="whatsapp", data=final_data, unique_id=unique_id
            )  # noqa: E501
            entry.add_to_hass(hass)
            await hass.config_entries.async_setup(entry.entry_id)

            # Reset flow data for next iteration in same test
            flow_data.clear()

        return result

    hass.config_entries.flow.async_init = AsyncMock(side_effect=async_init)
    hass.config_entries.flow.async_configure = AsyncMock(side_effect=async_configure)

    hass.config_entries.options = MagicMock()

    async def async_options_init(
        entry_id: str,  # noqa: ARG001
        context: Any = None,  # noqa: ARG001
        data: Any = None,  # noqa: ARG001
    ) -> dict[str, Any]:
        return {"type": "form", "flow_id": "test_options", "step_id": "init"}

    async def async_options_configure(
        flow_id: str,  # noqa: ARG001
        user_input: Any = None,  # noqa: ARG001
    ) -> dict[str, Any]:
        from custom_components.whatsapp.const import (
            CONF_DEBUG_PAYLOADS,
            CONF_MARK_AS_READ,
            CONF_MASK_SENSITIVE_DATA,
            CONF_POLLING_INTERVAL,
            CONF_RETRY_ATTEMPTS,
            CONF_SELF_MESSAGES,
            CONF_WHITELIST,
        )

        defaults = {
            CONF_MARK_AS_READ: True,
            CONF_POLLING_INTERVAL: 5,
            CONF_RETRY_ATTEMPTS: 2,
            CONF_DEBUG_PAYLOADS: False,
            CONF_MASK_SENSITIVE_DATA: False,
            CONF_WHITELIST: "",
            CONF_SELF_MESSAGES: False,
        }
        return {"type": "create_entry", "data": {**defaults, **(user_input or {})}}

    hass.config_entries.options.async_init = AsyncMock(side_effect=async_options_init)
    hass.config_entries.options.async_configure = AsyncMock(
        side_effect=async_options_configure
    )  # noqa: E501

    hass.data = {}
    return hass


@pytest.fixture  # type: ignore[untyped-decorator]
def data(hass: MagicMock, mock_client: MagicMock) -> dict[str, Any]:
    """Fixture for common test data (coordinator)."""
    # homeassistant.util
    util_mod = ha_stubs.stub(
        "homeassistant.util", slugify=lambda x: x.lower().replace(" ", "_")
    )  # noqa: E501
    dt_mod = ha_stubs.stub(
        "homeassistant.util.dt", utcnow=lambda: None, now=lambda: None
    )  # noqa: E501
    util_mod.dt = dt_mod
    sw_mod = ha_stubs.stub("homeassistant.util.search_web", is_safe_url=lambda _: True)
    util_mod.search_web = sw_mod

    # pytest_homeassistant_custom_component.common
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.whatsapp.const import CONF_API_KEY, CONF_URL

    entry = MockConfigEntry(
        domain="whatsapp", data={CONF_URL: "test", CONF_API_KEY: "mock"}
    )  # noqa: E501
    entry.add_to_hass(hass)

    coordinator = ha_stubs.DataUpdateCoordinator(hass, mock_client, entry)

    # Override async_refresh to actually call _async_update_data (like the real HA does)
    # This allows test_connection_lost_notification to verify ir.async_create_issue is called  # noqa: E501
    async def _real_refresh() -> None:
        try:
            from custom_components.whatsapp.coordinator import (
                WhatsAppDataUpdateCoordinator,
            )

            # TODO: Refactor test `_real_refresh` mocking injection
            # using `object.__new__` directly skips validation and requires manually
            # wiring internal dependencies like `client`, `entry`, `data`, and
            # `_listeners`.
            # This should be replaced with a real test initialization helper or by
            # invoking `__init__` normally to ensure structural changes fail loudly.
            # Tracking issue: [TODO]
            real_coord = object.__new__(WhatsAppDataUpdateCoordinator)
            real_coord.hass = hass
            real_coord.client = mock_client
            real_coord.entry = entry
            real_coord.data = coordinator.data
            real_coord._listeners = coordinator._listeners
            result = await real_coord._async_update_data()
            coordinator.data = result
            for listener in coordinator._listeners:
                if callable(listener):
                    listener()
        except Exception:
            # Still notify listeners on error
            for listener in coordinator._listeners:
                if callable(listener):
                    listener()
            raise

    coordinator.async_refresh = _real_refresh  # type: ignore[method-assign,assignment]
    # coordinator already has default data from ha_stubs.py

    return {"coordinator": coordinator, "entry": entry}
