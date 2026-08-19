"""Test the WhatsApp button platform."""

from unittest.mock import AsyncMock, MagicMock, patch

from ha_stubs import _build_ha_stub_modules

_build_ha_stub_modules()

from homeassistant.core import HomeAssistant  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.whatsapp.button import (  # noqa: E402
    WhatsAppReconnectButton,
    WhatsAppTestButton,
    async_setup_entry,
)
from custom_components.whatsapp.const import (  # noqa: E402
    CONF_API_KEY,
    CONF_URL,
    DOMAIN,
)


async def test_button_setup_and_reconnect(hass: HomeAssistant) -> None:
    """Test setup of buttons and reconnect button press."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://test:8066", CONF_API_KEY: "test_key"},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.entry = entry
    client = MagicMock()
    client.get_device_info.return_value = {"identifiers": {(DOMAIN, "test")}}
    client.start_session = AsyncMock()
    coordinator.client = client
    coordinator.async_request_refresh = AsyncMock()

    added_entities = []

    def add_entities_callback(entities, _update_before_add=False):
        added_entities.extend(entities)

    hass.data = {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}}

    await async_setup_entry(hass, entry, add_entities_callback)

    assert len(added_entities) == 2
    test_btn = next(e for e in added_entities if isinstance(e, WhatsAppTestButton))
    reconnect_btn = next(
        e for e in added_entities if isinstance(e, WhatsAppReconnectButton)
    )

    assert test_btn.unique_id == f"{entry.entry_id}_diagnostic_test"
    assert reconnect_btn.unique_id == f"{entry.entry_id}_reconnect"

    # Test reconnect button press
    await reconnect_btn.async_press()
    client.start_session.assert_called_once()
    coordinator.async_request_refresh.assert_called_once()


async def test_test_button_no_jid(hass: HomeAssistant) -> None:
    """Test WhatsAppTestButton when no JID is available."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://test:8066", CONF_API_KEY: "test_key"},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.entry = entry
    client = MagicMock()
    client.get_device_info.return_value = {"identifiers": {(DOMAIN, "test")}}
    client.get_admin_jid.return_value = None
    client.get_my_jid.return_value = None
    coordinator.client = client

    btn = WhatsAppTestButton(coordinator)
    btn.hass = hass
    btn.async_write_ha_state = MagicMock()

    await btn.async_press()

    assert "Error" in btn.extra_state_attributes
    btn.async_write_ha_state.assert_called()


async def test_test_button_success_all_steps(hass: HomeAssistant) -> None:
    """Test WhatsAppTestButton successful full test execution with admin JID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://test:8066", CONF_API_KEY: "test_key"},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.entry = entry
    client = MagicMock()
    client.get_device_info.return_value = {"identifiers": {(DOMAIN, "test")}}
    client.get_admin_jid.return_value = "491761111111@s.whatsapp.net"
    client.get_my_jid.return_value = "4915902242000@s.whatsapp.net"
    client.send_message = AsyncMock(return_value="msg_123")
    client.send_reaction = AsyncMock(return_value="react_ok")
    client.edit_message = AsyncMock(return_value="edit_ok")
    client.send_buttons = AsyncMock(return_value=True)
    client.send_location = AsyncMock(return_value="loc_123")
    client.send_contact = AsyncMock(return_value="contact_123")
    client.revoke_message = AsyncMock(return_value="revoked_ok")
    coordinator.client = client

    btn = WhatsAppTestButton(coordinator)
    btn.hass = hass
    btn.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", new=AsyncMock()):
        await btn.async_press()

    attrs = btn.extra_state_attributes
    assert attrs.get("Status") == "Completed"
    assert attrs.get("Text Message") == "OK"
    assert attrs.get("Reaction") == "OK"
    assert attrs.get("Message Edit") == "OK"
    assert attrs.get("Buttons & Poll Fallback") == "OK"
    assert attrs.get("Location") == "OK"
    assert attrs.get("Contact Card") == "OK"
    assert attrs.get("Auto-Delete") == "OK"

    # Verify target was bot own JID
    client.send_message.assert_any_call(
        "4915902242000@s.whatsapp.net",
        "🤖 WhatsApp Diagnostic: Text Message Test",
    )


async def test_test_button_step_failures_handled(hass: HomeAssistant) -> None:
    """Test WhatsAppTestButton handles individual step failures gracefully."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_URL: "http://test:8066", CONF_API_KEY: "test_key"},
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.entry = entry
    client = MagicMock()
    client.get_device_info.return_value = {"identifiers": {(DOMAIN, "test")}}
    client.get_admin_jid.return_value = None
    client.get_my_jid.return_value = "4915902242000@s.whatsapp.net"

    # Send message succeeds for intro/completion/feedback, but _test_text raises
    async def mock_send_message(_jid, text):
        if "Text Message Test" in text:
            raise Exception("Text failed")
        return "msg_id"

    client.send_message = AsyncMock(side_effect=mock_send_message)
    client.send_reaction = AsyncMock()
    client.edit_message = AsyncMock(side_effect=Exception("Edit failed"))
    client.send_buttons = AsyncMock(side_effect=Exception("Button failed"))
    client.send_location = AsyncMock(side_effect=Exception("Location failed"))
    client.send_contact = AsyncMock(side_effect=Exception("Contact failed"))
    client.revoke_message = AsyncMock(side_effect=Exception("Revoke failed"))
    coordinator.client = client

    btn = WhatsAppTestButton(coordinator)
    btn.hass = hass
    btn.async_write_ha_state = MagicMock()

    with patch("asyncio.sleep", new=AsyncMock()):
        await btn.async_press()

    attrs = btn.extra_state_attributes
    assert attrs.get("Status") == "Completed"
    assert "Error" in attrs.get("Text Message", "")
    assert attrs.get("Reaction") == "Skipped (Text failed)"
    assert "Error" in attrs.get("Message Edit", "")
    assert "Error" in attrs.get("Buttons & Poll Fallback", "")
    assert "Error" in attrs.get("Location", "")
    assert "Error" in attrs.get("Contact Card", "")
    assert "Error" in attrs.get("Auto-Delete", "")
