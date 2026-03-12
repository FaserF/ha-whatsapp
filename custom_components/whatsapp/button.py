"""Button platform for WhatsApp Integration."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WhatsAppDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatsApp button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WhatsAppDataUpdateCoordinator = data["coordinator"]
    async_add_entities([WhatsAppTestButton(coordinator)])


class WhatsAppTestButton(CoordinatorEntity, ButtonEntity):  # type: ignore[misc]
    """Diagnostic button for WhatsApp integration."""

    _attr_has_entity_name = True
    _attr_translation_key = "diagnostic_test"
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator: WhatsAppDataUpdateCoordinator) -> None:
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
        my_jid = client.get_my_jid()

        if not my_jid:
            self._results = {"Error": "Could not determine own JID. Is the bot connected?"}
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
            "• 🔘 Interactive Buttons\n"
            "• 📋 Interactive List\n"
            "• 📍 Location Sharing\n"
            "• 🗑️ Auto-Deletion\n"
        )
        await client.send_message(my_jid, intro_text)

        final_results = {}

        # 1. Text Message
        try:
            msg_id = await self._test_text(my_jid)
            final_results["Text Message"] = "OK"

            # 2. Reaction (needs ID from 1)
            try:
                await self._test_reaction(my_jid, msg_id)
                final_results["Reaction"] = "OK"
            except Exception as err:
                final_results["Reaction"] = f"Error: {err}"
        except Exception as err:
            final_results["Text Message"] = f"Error: {err}"
            final_results["Reaction"] = "Skipped (Text failed)"

        self._results = {**final_results, "Status": "In Progress..."}
        self.async_write_ha_state()

        # 3. Buttons
        try:
            await self._test_buttons(my_jid)
            final_results["Buttons"] = "OK"
        except Exception as err:
            final_results["Buttons"] = f"Error: {err}"

        # 4. List
        try:
            await self._test_list(my_jid)
            final_results["List"] = "OK"
        except Exception as err:
            final_results["List"] = f"Error: {err}"

        # 5. Location
        try:
            await self._test_location(my_jid)
            final_results["Location"] = "OK"
        except Exception as err:
            final_results["Location"] = f"Error: {err}"

        # 6. Auto-Delete
        try:
            await self._test_delete(my_jid)
            final_results["Auto-Delete"] = "OK"
        except Exception as err:
            final_results["Auto-Delete"] = f"Error: {err}"

        # 7. Final Completion Message
        completion_text = (
            "🏁 *Diagnostic Test Completed*\n\n"
            "All functional tests have been performed. Check the Home Assistant "
            "button entity attributes for detailed status of each step.\n\n"
            "📖 *Documentation:* https://faserf.github.io/ha-whatsapp/\n"
            "🐞 *Report Issues:* https://github.com/FaserF/ha-whatsapp/issues"
        )
        await client.send_message(my_jid, completion_text)

        self._results = {**final_results, "Status": "Completed"}
        self.async_write_ha_state()

    async def _test_text(self, jid: str) -> str:
        """Test sending a text message."""
        return await self.coordinator.client.send_message(jid, "🤖 WhatsApp Diagnostic: Text Message Test")

    async def _test_reaction(self, jid: str, message_id: str) -> str:
        """Test sending a reaction."""
        return await self.coordinator.client.send_reaction(jid, "✅", message_id)

    async def _test_buttons(self, jid: str) -> None:
        """Test sending buttons."""
        buttons = [
            {"buttonId": "btn_1", "displayText": "Option 1"},
            {"buttonId": "btn_2", "displayText": "Option 2"},
        ]
        await self.coordinator.client.send_buttons(
            jid,
            "This is a button test. Choose one below:",
            buttons,
            "Diagnostic Footer",
        )

    async def _test_list(self, jid: str) -> None:
        """Test sending a list."""
        sections = [
            {
                "title": "Category 1",
                "rows": [
                    {"title": "Row 1", "description": "Description 1", "id": "row_1"},
                    {"title": "Row 2", "description": "Description 2", "id": "row_2"},
                ],
            }
        ]
        await self.coordinator.client.send_list(
            jid,
            "Diagnostic List Test",
            "Please select an option from the list below.",
            "Select Option",
            sections,
            "Diagnostic Footer",
        )

    async def _test_location(self, jid: str) -> str:
        """Test sending location."""
        return await self.coordinator.client.send_location(jid, 48.1351, 11.5820, "Marienplatz", "Munich")

    async def _test_delete(self, jid: str) -> str:
        """Test auto-delete."""
        msg_id = await self.coordinator.client.send_message(
            jid, "🗑️ This message will be deleted automatically in 2 seconds."
        )
        if not msg_id:
            raise ValueError("Failed to get message ID for deletion test")
        # For diagnostic, let's just wait 2s to simulate.
        await asyncio.sleep(2)
        return await self.coordinator.client.revoke_message(jid, msg_id)
