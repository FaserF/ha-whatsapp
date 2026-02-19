"""Repairs platform for HA WhatsApp.

This module wires up the Home Assistant *Repairs* UI for the WhatsApp
integration.  When the coordinator detects a broken connection or an
expired session it creates a *repair issue*; this module provides the
interactive fix-flow that is displayed when the user clicks "Fix" on
that issue.

Currently implemented issues:
    * ``session_expired`` – The addon is running but the WhatsApp QR
      session has been revoked / logged out.  The repair flow instructs
      the user to re-scan the QR code via the integration's config flow.

All other unknown issues fall back to a generic :class:`ConfirmRepairFlow`.
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant


class WhatsAppRepairFlow(RepairsFlow):  # type: ignore[misc]
    """Guided fix-flow for WhatsApp integration issues.

    Presents a simple confirmation step to the user.  Subclass this class
    to add more sophisticated multi-step flows for specific issue types.
    """

    def __init__(self, issue_id: str) -> None:
        """Initialise the repair flow.

        Args:
            issue_id: The identifier of the issue being fixed, e.g.
                ``"session_expired"``.
        """
        self.issue_id = issue_id

    async def async_step_init(
        self, _user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Entry point for the repair flow, forwards to the confirmation step.

        Args:
            _user_input: Unused.  Provided for compatibility with the flow
                framework.

        Returns:
            The result of :meth:`async_step_confirm`.
        """
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Show a confirmation form and complete the flow when the user confirms.

        Args:
            user_input: ``None`` the first time the form is shown.  When the
                user submits, an empty dict is passed.

        Returns:
            A :class:`~homeassistant.data_entry_flow.FlowResult` that either
            shows the form or creates a completed-entry to close the issue.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


async def async_setup_repair_flow(
    _hass: HomeAssistant,
    issue_id: str,
    _data: dict[str, str] | None,
) -> RepairsFlow:
    """Create and return the repair flow for a given issue.

    Called by Home Assistant when the user initiates a repair for the
    WhatsApp integration.  The returned :class:`RepairsFlow` drives the
    multi-step fix wizard shown in the UI.

    Args:
        _hass: The Home Assistant instance (unused, but required by the
            platform API).
        issue_id: Identifier of the issue to repair (e.g.
            ``"session_expired"``).
        _data: Optional extra data attached to the issue (unused).

    Returns:
        A :class:`RepairsFlow` appropriate for the given issue.  Falls
        back to a simple :class:`~homeassistant.components.repairs.ConfirmRepairFlow`
        for unknown issues.
    """
    if issue_id == "session_expired":
        return ConfirmRepairFlow()
    return ConfirmRepairFlow()
