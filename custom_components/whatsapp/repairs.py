"""Repairs platform for HA WhatsApp."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant


class WhatsAppRepairFlow(RepairsFlow):  # type: ignore[misc]
    """Handler for an issue fixing flow."""

    def __init__(self, issue_id: str) -> None:
        """Initialize."""
        self.issue_id = issue_id

    async def async_step_init(
        self, _user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step."""
        if user_input is not None:
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


async def async_setup_repair_flow(
    _hass: HomeAssistant,
    issue_id: str,
    _data: dict[str, str] | None,
) -> RepairsFlow:
    """Handle the setup of a repair flow."""
    if issue_id == "session_expired":
        return ConfirmRepairFlow()
    return ConfirmRepairFlow()
