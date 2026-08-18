"""Button platform for WhatsApp Integration."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator as WACoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatsApp button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WACoordinator = data["coordinator"]
    async_add_entities(
        [
            WhatsAppTestButton(coordinator),
            WhatsAppReconnectButton(coordinator),
        ]
    )


class WhatsAppReconnectButton(CoordinatorEntity[WACoordinator], ButtonEntity):  # type: ignore[misc]
    """Button entity to trigger a gentle WhatsApp session reconnect."""

    coordinator: WACoordinator

    _attr_has_entity_name = True
    _attr_translation_key = "reconnect"
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: WACoordinator) -> None:
        """Initialize the reconnect button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_reconnect"
        self._attr_device_info = coordinator.client.get_device_info()

    async def async_press(self) -> None:
        """Handle the button press to restart session negotiation."""
        client = self.coordinator.client
        await client.start_session()
        await self.coordinator.async_request_refresh()


class WhatsAppTestButton(CoordinatorEntity[WACoordinator], ButtonEntity):  # type: ignore[misc]
    """Diagnostic button for WhatsApp integration."""

    coordinator: WACoordinator

    _attr_has_entity_name = True
    _attr_translation_key = "diagnostic_test"
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: WACoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_diagnostic_test"
        self._attr_device_info = coordinator.client.get_device_info()
        self._results: dict[str, str] = {}

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._results

    async def async_press(self) -> None:
        """Handle the button press."""
        client = self.coordinator.client
        target_jid = client.get_admin_jid() or client.get_my_jid()

        if not target_jid:
            self._results = {
                "Error": (
                    "Could not determine target JID (neither admin number nor "
                    "bot JID found). Is the bot connected?"
                )
            }
            self.async_write_ha_state()
            return

        self._results = {"Status": "Running diagnostic tests..."}
        self.async_write_ha_state()

        # 0. Intro Message
        intro_text = (
            "🤖 *WhatsApp Integration: Diagnostic Test Started*\n\n"
            "This test was triggered from Home Assistant to verify "
            "the communication between the integration and the addon.\n\n"
            "*Upcoming Tests:*\n"
            "• 📝 Text Message\n"
            "• ✅ Reaction\n"
            "• ✏️ Message Edit\n"
            "• 🔘 Interactive Buttons & Poll Fallback\n"
            "• 📍 Location Sharing\n"
            "• 👤 Contact Card\n"
            "• 🗑️ Auto-Deletion\n"
        )
        await client.send_message(target_jid, intro_text)

        final_results = {}

        # 1. Text Message
        try:
            msg_id = await self._test_text(target_jid)
            final_results["Text Message"] = "OK"

            # 2. Reaction (needs ID from 1)
            try:
                await self._test_reaction(target_jid, msg_id)
                final_results["Reaction"] = "OK"
            except Exception as err:
                final_results["Reaction"] = f"Error: {err}"
        except Exception as err:
            final_results["Text Message"] = f"Error: {err}"
            final_results["Reaction"] = "Skipped (Text failed)"

        self._results = {**final_results, "Status": "In Progress..."}
        self.async_write_ha_state()

        # 3. Message Edit
        try:
            await self._test_edit(target_jid)
            final_results["Message Edit"] = "OK"
        except Exception as err:
            final_results["Message Edit"] = f"Error: {err}"

        # 4. Buttons (with poll fallback & interaction response)
        try:
            await self._test_buttons(target_jid)
            final_results["Buttons & Poll Fallback"] = "OK"
        except Exception as err:
            final_results["Buttons & Poll Fallback"] = f"Error: {err}"

        # 5. Location
        try:
            await self._test_location(target_jid)
            final_results["Location"] = "OK"
        except Exception as err:
            final_results["Location"] = f"Error: {err}"

        # 6. Contact Card
        try:
            await self._test_contact(target_jid)
            final_results["Contact Card"] = "OK"
        except Exception as err:
            final_results["Contact Card"] = f"Error: {err}"

        # 7. Auto-Delete
        try:
            await self._test_delete(target_jid)
            final_results["Auto-Delete"] = "OK"
        except Exception as err:
            final_results["Auto-Delete"] = f"Error: {err}"

        # 8. Final Completion Message
        completion_text = (
            "🏁 *Diagnostic Test Completed*\n\n"
            "All functional tests have been performed. Check the Home Assistant "
            "button entity attributes for detailed status of each step.\n\n"
            "📖 *Documentation:* https://faserf.github.io/ha-whatsapp/\n"
            "🐞 *Report Issues:* https://github.com/FaserF/ha-whatsapp/issues"
        )
        await client.send_message(target_jid, completion_text)

        self._results = {**final_results, "Status": "Completed"}
        self.async_write_ha_state()

    async def _test_text(self, jid: str) -> str:
        """Test sending a text message."""
        return await self.coordinator.client.send_message(
            jid, "🤖 WhatsApp Diagnostic: Text Message Test"
        )

    async def _test_reaction(self, jid: str, message_id: str) -> str:
        """Test sending a reaction."""
        return await self.coordinator.client.send_reaction(jid, "✅", message_id)

    async def _test_edit(self, jid: str) -> str:
        """Test sending and editing a message."""
        msg_id = await self.coordinator.client.send_message(
            jid, "🤖 WhatsApp Diagnostic: Message before edit..."
        )
        if not msg_id:
            raise ValueError("Failed to get message ID for edit test")
        await asyncio.sleep(1)
        return await self.coordinator.client.edit_message(
            jid, msg_id, "🤖 WhatsApp Diagnostic: Message successfully edited! ✏️✅"
        )

    async def _test_buttons(self, jid: str) -> None:
        """Test sending buttons with poll fallback and interactive response."""
        buttons = [
            {"id": "btn_diag_1", "text": "Option 1"},
            {"id": "btn_diag_2", "text": "Option 2"},
        ]
        msg_id = await self.coordinator.client.send_buttons(
            jid,
            "This is a button test. Choose one below:",
            buttons,
            "Diagnostic Footer",
        )
        await asyncio.sleep(1)
        button_data = {
            "from": jid,
            "sender": jid,
            "button_id": "btn_diag_1",
            "selected_text": "Option 1",
            "poll_id": msg_id,
        }
        self.hass.bus.async_fire("whatsapp_button_pressed", button_data)
        await self.coordinator.client.send_message(
            jid,
            "🔘 *Button / Poll Test Dispatched & Verified*\n"
            "Options: 1️⃣ Option 1 | 2️⃣ Option 2\n"
            "• Simulated Action: Option 1 (btn_diag_1)\n"
            "• HA Event `whatsapp_button_pressed` fired successfully! ✅",
        )

    async def _test_location(self, jid: str) -> str:
        """Test sending location."""
        return await self.coordinator.client.send_location(
            jid, 48.1351, 11.5820, "Marienplatz", "Munich"
        )

    async def _test_contact(self, jid: str) -> str:
        """Test sending a contact card."""
        vcard = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            "FN:Home Assistant Bot\n"
            "ORG:Home Assistant;\n"
            "TEL;type=CELL;type=VOICE;waid=123456789:+123456789\n"
            "END:VCARD"
        )
        return await self.coordinator.client.send_contact(
            jid, "Home Assistant Bot", vcard
        )

    async def _test_delete(self, jid: str) -> str:
        """Test auto-delete."""
        msg_id = await self.coordinator.client.send_message(
            jid, "🗑️ This message will be deleted automatically in 2 seconds."
        )
        if not msg_id:
            raise ValueError("Failed to get message ID for deletion test")
        await asyncio.sleep(2)
        return await self.coordinator.client.revoke_message(jid, msg_id)
