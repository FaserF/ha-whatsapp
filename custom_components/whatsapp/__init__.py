"""HA WhatsApp integration entry point.

This module is the heart of the Home Assistant WhatsApp integration. It
is responsible for:

1. **Setup** (:func:`async_setup_entry`) – Reads the config entry, creates
   a :class:`~.api.WhatsAppApiClient`, starts the WebSocket/polling loop,
   registers HA services (``send_message``, ``send_image``, …), and spins
   up the :class:`~.coordinator.WhatsAppDataUpdateCoordinator`.
2. **Tear-down** (:func:`async_unload_entry`) – Cancels all background
   tasks, closes the HTTP session, and unloads all platform entities.
3. **Incoming-message handling** – Fires
   :attr:`~.const.EVENT_MESSAGE_RECEIVED` Home Assistant events for every
   message received from the addon, optionally marks them as read, and
   applies whitelist filtering.
4. **Service registration** – Binds ``whatsapp.send_message``,
   ``whatsapp.send_image``, ``whatsapp.send_document``, … services to
   the :class:`~.api.WhatsAppApiClient` methods so that automations can
   call them directly.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError

from .api import WhatsAppApiClient
from .const import (
    CONF_API_KEY,
    CONF_MARK_AS_READ,
    CONF_POLLING_INTERVAL,
    CONF_SELF_MESSAGES,
    CONF_WHITELIST,
    DOMAIN,
    EVENT_MESSAGE_RECEIVED,
)
from .coordinator import WhatsAppDataUpdateCoordinator

_LOGGER = getLogger(__name__)

_SERVICES_REGISTERED = False

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NOTIFY,
    Platform.SENSOR,
]

_SERVICES = [
    "send_message",
    "send_poll",
    "send_image",
    "send_document",
    "send_video",
    "send_audio",
    "revoke_message",
    "edit_message",
    "send_list",
    "send_contact",
    "configure_webhook",
    "send_location",
    "send_event",
    "send_reaction",
    "update_presence",
    "send_buttons",
    "search_groups",
    "mark_as_read",
    "get_contacts",
    "check_number",
    "create_group",
    "add_group_participant",
    "remove_group_participant",
    "promote_group_participant",
    "demote_group_participant",
    "leave_group",
    "update_group_subject",
    "update_group_description",
    "update_group_settings",
    "join_group",
    "star_message",
    "unstar_message",
    "pin_message",
    "unpin_message",
    "forward_message",
    "send_status",
    "get_profile_picture",
    "get_contact_info",
    "block_contact",
    "unblock_contact",
    "archive_chat",
    "unarchive_chat",
    "mute_chat",
    "unmute_chat",
    "get_channel_info",
    "follow_channel",
    "unfollow_channel",
    "mute_channel",
    "unmute_channel",
    "add_chat_label",
    "remove_chat_label",
    "mark_as_unread",
    "clear_chat",
    "delete_chat",
    "get_chat_messages",
    "enable_moderation",
    "disable_moderation",
    "warn_user",
    "clear_warnings",
    "import_moderation_config",
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the WhatsApp integration from a config entry.

    Called by Home Assistant when the integration is first loaded or when
    the user completes the config flow. This function:

    * Creates the :class:`~.api.WhatsAppApiClient` and starts the addon
      polling loop.
    * Creates and refreshes the
      :class:`~.coordinator.WhatsAppDataUpdateCoordinator`.
    * Forwards platform setup to ``binary_sensor``, ``sensor``, and
      ``notify`` platforms.
    * Registers all ``whatsapp.*`` services in the HA service registry.
    * Sets up the incoming-message callback that fires HA events.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being loaded. Contains all configuration
            values entered by the user (URL, API key, options …).

    Returns:
        ``True`` on success. Raises
        :class:`~homeassistant.exceptions.ConfigEntryNotReady` if the
        initial coordinator refresh fails.
    """

    addon_url = (
        entry.data.get(CONF_URL) or entry.data.get("host") or "http://localhost:8066"
    )
    api_key = entry.data.get(CONF_API_KEY)
    mask_sensitive_data = entry.options.get("mask_sensitive_data", False)
    whitelist_str = entry.options.get(CONF_WHITELIST, "")
    whitelist = None
    if whitelist_str:
        whitelist = [x.strip() for x in whitelist_str.split(",") if x.strip()]

    session_id = entry.data.get("session_id", "default")

    # Resolve internal container IPs/hostnames for the 'Visit' button
    ha_base_url = None
    try:
        import homeassistant.helpers.network as network_helper

        ha_base_url = network_helper.get_url(hass)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.debug("Could not resolve HA URL", exc_info=True)

    config_url = addon_url

    is_internal_host = any(
        pattern in addon_url.lower()
        for pattern in ("localhost", "127.0.0.1", "172.", "7da084a7", "supervisor")
    )

    is_hassio_env = False
    try:
        import homeassistant.components.hassio as hassio_mod

        if hasattr(hassio_mod, "is_hassio"):
            is_hassio_env = bool(hassio_mod.is_hassio(hass))  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        pass

    if is_hassio_env and is_internal_host:
        slug = (
            "7da084a7_whatsapp_edge"
            if "edge" in addon_url.lower()
            else "7da084a7_whatsapp"
        )
        config_url = f"/hassio/ingress/{slug}"
    elif is_internal_host and ha_base_url:
        try:
            from yarl import URL

            ha_host = URL(ha_base_url).host
            if ha_host:
                config_url = str(URL(addon_url).with_host(ha_host))
                _LOGGER.debug(
                    "Resolved addon URL for Visit button: %s -> %s",
                    addon_url,
                    config_url,
                )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.debug("Could not resolve HA URL for Visit button", exc_info=True)

    session = None
    try:
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(hass)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.debug("Could not resolve HA aiohttp clientsession")

    client = WhatsAppApiClient(
        host=addon_url,
        api_key=api_key,
        session_id=session_id,
        mask_sensitive_data=mask_sensitive_data,
        whitelist=whitelist,
        config_url=config_url,
        ha_base_url=ha_base_url,
        session=session,
    )

    coordinator = WhatsAppDataUpdateCoordinator(hass, client, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    # Handle incoming messages
    def handle_incoming_message(data: dict[str, Any]) -> None:
        """Handle incoming message from API."""
        # Normalize sender for the event
        # The addon now sends 'sender_number' which is the best-effort phone number
        # We prefer that over splitting the raw JID which might be an LID (UUID)
        full_sender = data.get("sender", "")
        sender_number = data.get("sender_number")

        # The 'sender' field should be the full JID for direct use in replies/services
        data["sender"] = full_sender
        data["raw_sender"] = full_sender

        if sender_number:
            clean_sender = sender_number
        else:
            # Fallback for older addon versions or weird cases
            clean_sender = full_sender
            if "@s.whatsapp.net" in full_sender or "@lid" in full_sender:
                clean_sender = full_sender.split("@")[0]

        data["sender_number"] = clean_sender

        # Self-message filtering (fromMe)
        # Default: Don't monitor 'fromMe' messages unless explicitly enabled in options
        raw_msg = data.get("raw", {})
        from_me = raw_msg.get("key", {}).get("fromMe", False)
        if from_me and not entry.options.get(CONF_SELF_MESSAGES, False):
            _LOGGER.debug(
                "Ignoring self-message (fromMe) as it's disabled in configuration"
            )
            return

        # Whitelist filtering
        if whitelist is not None:
            # For groups, the raw data contains the group JID in remoteJid
            remote_id = raw_msg.get("key", {}).get("remoteJid", "")
            is_group = "@g.us" in remote_id
            target = remote_id if is_group else full_sender

            if not client.is_allowed(target):
                _LOGGER.debug(
                    "Ignoring incoming message from non-whitelisted %s: %s",
                    "group" if is_group else "sender",
                    client.mask(target),
                )
                return

        # Add session identifiers to let users distinguish between multiple bots
        data["entry_id"] = entry.entry_id
        data["session_id"] = session_id

        _LOGGER.debug("Firing WhatsApp event: %s", data)
        hass.bus.async_fire(EVENT_MESSAGE_RECEIVED, data)

        # Check for interactive button / template response
        raw_msg_msg = raw_msg.get("message", {})
        button_id = None
        if "buttonsResponseMessage" in raw_msg_msg:
            button_id = raw_msg_msg["buttonsResponseMessage"].get("selectedButtonId")
        elif "listResponseMessage" in raw_msg_msg:
            reply = raw_msg_msg["listResponseMessage"].get("singleSelectReply", {})
            button_id = reply.get("selectedRowId")
        elif "templateButtonReplyMessage" in raw_msg_msg:
            button_id = raw_msg_msg["templateButtonReplyMessage"].get("selectedId")

        if button_id:
            button_data = {**data, "button_id": button_id}
            _LOGGER.debug("Firing WhatsApp button event: %s", button_data)
            hass.bus.async_fire("whatsapp_button_pressed", button_data)

        # Automatically mark as read if enabled
        if entry.options.get(CONF_MARK_AS_READ, False):
            # Extract ID and sender JID from the nested raw data
            # Try to get message_id from 'raw.key.id' or fallback to top-level 'id'
            message_id = raw_msg.get("key", {}).get("id") or data.get("id")
            number = data.get("sender")  # Full JID (e.g. 123456789@s.whatsapp.net)

            if message_id and number:

                async def _safe_mark_as_read(_number: str, _message_id: str) -> None:
                    """Call mark_as_read and swallow any exception to avoid

                    'Task exception was never retrieved' log spam when the addon
                    is under load or a request times out.
                    """
                    try:
                        await client.mark_as_read(_number, _message_id)
                    except Exception as _exc:  # noqa: BLE001
                        _LOGGER.warning(
                            "Auto-mark-as-read failed for %s (msg %s): %s",
                            client.mask(_number),
                            _message_id,
                            _exc,
                        )

                entry.async_create_background_task(
                    hass,
                    _safe_mark_as_read(number, message_id),
                    name="whatsapp_mark_as_read",
                )
            else:
                _LOGGER.warning(
                    "Auto-mark-as-read enabled but missing data. "
                    "Message ID: %s, Number: %s",
                    message_id,
                    number,
                )

    client.register_callback(handle_incoming_message)
    polling_interval = entry.options.get(CONF_POLLING_INTERVAL, 5)
    await client.start_polling(interval=polling_interval)

    if hasattr(entry, "async_create_background_task"):
        entry.async_create_background_task(
            hass, client.start_session(), name="whatsapp_start_session"
        )
    elif hasattr(hass, "async_create_task"):
        hass.async_create_task(client.start_session(), name="whatsapp_start_session")

    # Register services globally
    await async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


def get_client_for_account(
    hass: HomeAssistant, account: str | None
) -> WhatsAppApiClient:
    """Get the correct client based on the account (entry_id or unique ID)."""
    clients: dict[str, WhatsAppApiClient] = {
        entry_id: data["client"]
        for entry_id, data in hass.data.get(DOMAIN, {}).items()
        if "client" in data
    }

    if not clients:
        raise ServiceValidationError("No WhatsApp accounts configured")

    # If only one client exists and no account specified, use it
    if account is None:
        if len(clients) == 1:
            return list(clients.values())[0]
        raise ServiceValidationError(
            "Multiple WhatsApp accounts found. "
            "Please specify the 'account' (entry ID or unique ID)."
        )

    # Try mapping by entry_id
    if account in clients:
        return clients[account]

    # Try mapping by unique_id (my_number)
    for entry_id, client in clients.items():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry and entry.unique_id == account:
            return client

    # Fallback to title with ambiguity check
    title_matches: list[tuple[str, WhatsAppApiClient]] = []
    for entry_id, client in clients.items():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry and entry.title == account:
            title_matches.append((entry_id, client))

    if len(title_matches) > 1:
        raise ServiceValidationError(
            f"Multiple WhatsApp accounts found with title '{account}'. "
            "Please disambiguate by using the entry ID or unique ID instead."
        )

    if len(title_matches) == 1:
        _LOGGER.warning(
            "Using title-based fallback for WhatsApp account '%s'. "
            "Please update your automation to use the entry ID or unique ID "
            "to avoid future collisions.",
            account,
        )
        return title_matches[0][1]

    raise ServiceValidationError(f"WhatsApp account '{account}' not found")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up global WhatsApp services."""
    global _SERVICES_REGISTERED
    if _SERVICES_REGISTERED:
        return

    async def _handle_service(call: ServiceCall) -> Any:
        """General service handler for routing."""
        account = call.data.get("account")
        client = get_client_for_account(hass, account)

        service = call.service
        data: dict[str, Any] = {k: v for k, v in call.data.items() if k != "account"}

        def _get_quoted() -> str | None:
            return data["quote"] if "quote" in data else data.get("reply_to")

        if service == "send_message":
            await client.send_message(
                data["target"],
                data["message"],
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "send_poll":
            await client.send_poll(
                data["target"],
                data["question"],
                data.get("options", []),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
                allow_multiple_responses=data.get("allow_multiple_responses", False),
            )
        elif service == "send_image":
            await client.send_image(
                data["target"],
                data["url"],
                data.get("caption"),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "send_location":
            await client.send_location(
                data["target"],
                float(data["latitude"]),
                float(data["longitude"]),
                data.get("name"),
                data.get("address"),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "send_event":
            await client.send_event(
                data["target"],
                data["name"],
                description=data.get("description"),
                date=data.get("date"),
                location=data.get("location"),
                join_link=data.get("join_link"),
                is_canceled=data.get("is_canceled", False),
                expiration=data.get("expiration"),
            )
        elif service == "send_reaction":
            await client.send_reaction(
                data["target"], data["reaction"], data["message_id"]
            )
        elif service == "send_document":
            await client.send_document(
                data["target"],
                data["url"],
                data.get("file_name"),
                data.get("message"),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "send_video":
            await client.send_video(
                data["target"],
                data["url"],
                data.get("message"),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
                seconds=data.get("seconds"),
            )
        elif service == "send_audio":
            await client.send_audio(
                data["target"],
                data["url"],
                data.get("ptt", False),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
                seconds=data.get("seconds"),
            )
        elif service == "revoke_message":
            await client.revoke_message(data["target"], data["message_id"])
        elif service == "edit_message":
            await client.edit_message(
                data["target"], data["message_id"], data["message"]
            )
        elif service == "send_list":
            await client.send_list(
                data["target"],
                data.get("title") or "",
                data.get("text") or "",
                data.get("button_text") or "",
                data["sections"],
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "send_contact":
            await client.send_contact(
                data["target"], data["name"], data["contact_number"]
            )
        elif service == "configure_webhook":
            await client.set_webhook(
                data["url"], data.get("enabled", True), data.get("token")
            )
        elif service == "update_presence":
            await client.set_presence(data["target"], data["presence"])
        elif service == "send_buttons":
            await client.send_buttons(
                data["target"],
                data["message"],
                data["buttons"],
                data.get("footer"),
                quoted_message_id=_get_quoted(),
                expiration=data.get("expiration"),
            )
        elif service == "mark_as_read":
            await client.mark_as_read(data["target"], data.get("message_id"))
        elif service == "search_groups":
            await _handle_search_groups(hass, client, data.get("name_filter", ""))
        elif service == "get_contacts":
            contacts = await client.get_contacts()
            return {"contacts": contacts}
        elif service == "check_number":
            return await client.check_number(data["number"])
        elif service == "create_group":
            return await client.create_group(data["subject"], data["participants"])
        elif service == "add_group_participant":
            return await client.add_group_participants(
                data["target"], data["participants"]
            )
        elif service == "remove_group_participant":
            return await client.remove_group_participants(
                data["target"], data["participants"]
            )
        elif service == "promote_group_participant":
            return await client.promote_group_participants(
                data["target"], data["participants"]
            )
        elif service == "demote_group_participant":
            return await client.demote_group_participants(
                data["target"], data["participants"]
            )
        elif service == "leave_group":
            return await client.leave_group(data["target"])
        elif service == "update_group_subject":
            return await client.update_group_subject(data["target"], data["subject"])
        elif service == "update_group_description":
            return await client.update_group_description(
                data["target"], data["description"]
            )
        elif service == "update_group_settings":
            return await client.update_group_settings(
                data["target"],
                announce=data.get("announce"),
                locked=data.get("locked"),
            )
        elif service == "join_group":
            return await client.join_group_via_invite(data["code"])
        elif service == "star_message":
            return await client.star_message(
                data["target"], data["message_id"], star=True
            )
        elif service == "unstar_message":
            return await client.unstar_message(data["target"], data["message_id"])
        elif service == "pin_message":
            return await client.pin_message(
                data["target"], data["message_id"], duration=data.get("duration", 86400)
            )
        elif service == "unpin_message":
            return await client.unpin_message(data["target"], data["message_id"])
        elif service == "forward_message":
            return await client.forward_message(
                data["target"], data["message_id"], data["destination"]
            )
        elif service == "send_status":
            return await client.send_status(
                message=data.get("message"),
                url=data.get("url"),
                caption=data.get("caption"),
            )
        elif service == "get_profile_picture":
            return {
                "profile_picture_url": await client.get_profile_picture(data["target"])
            }
        elif service == "get_contact_info":
            return await client.get_contact_about(data["target"])
        elif service == "block_contact":
            return await client.block_contact(data["target"])
        elif service == "unblock_contact":
            return await client.unblock_contact(data["target"])
        elif service == "archive_chat":
            return await client.archive_chat(data["target"])
        elif service == "unarchive_chat":
            return await client.unarchive_chat(data["target"])
        elif service == "mute_chat":
            return await client.mute_chat(
                data["target"], duration_ms=data.get("duration_ms", 8 * 3600 * 1000)
            )
        elif service == "unmute_chat":
            return await client.unmute_chat(data["target"])
        elif service == "get_channel_info":
            return await client.get_channel_info(
                data.get("target") or data.get("code") or ""
            )
        elif service == "follow_channel":
            return await client.follow_channel(data["target"])
        elif service == "unfollow_channel":
            return await client.unfollow_channel(data["target"])
        elif service == "mute_channel":
            return await client.mute_channel(data["target"])
        elif service == "unmute_channel":
            return await client.unmute_channel(data["target"])
        elif service == "add_chat_label":
            return await client.add_chat_label(data["target"], data["label_id"])
        elif service == "remove_chat_label":
            return await client.remove_chat_label(data["target"], data["label_id"])
        elif service == "mark_as_unread":
            return await client.mark_as_unread(data["target"])
        elif service == "clear_chat":
            return await client.clear_chat(data["target"])
        elif service == "delete_chat":
            return await client.delete_chat(data["target"])
        elif service == "get_chat_messages":
            return await client.get_chat_messages(
                data["target"], limit=data.get("limit", 50)
            )
        elif service == "enable_moderation":
            return await client.enable_group_moderation(data["target"])
        elif service == "disable_moderation":
            return await client.disable_group_moderation(data["target"])
        elif service == "warn_user":
            return await client.warn_user(
                data["target"], data["user_id"], data.get("reason")
            )
        elif service == "clear_warnings":
            return await client.clear_warnings(data["target"], data["user_id"])
        elif service == "import_moderation_config":
            return await client.import_moderation_config(
                data["target"], data.get("config", {})
            )
        return None

    async def _handle_search_groups(
        hass: HomeAssistant, client: WhatsAppApiClient, name_filter: str
    ) -> None:
        """Handle search_groups separately to keep generic router cleaner."""
        name_filter = name_filter.lower()
        try:
            groups = await client.get_groups()
            if name_filter:
                groups = [g for g in groups if name_filter in g["name"].lower()]

            if not groups:
                msg_suffix = f' matching "{name_filter}"' if name_filter else ""
                message = f"No groups found{msg_suffix}."
            else:
                table = "| Name | Group ID | Participants |\n| :--- | :--- | :--- |\n"
                for g in groups:
                    table += f"| {g['name']} | `{g['id']}` | {g['participants']} |\n"

                message = (
                    f"Found {len(groups)} group(s):\n\n{table}\n\n"
                    "*Tip: Use the Group ID in the 'target' field of other services.*"
                )

            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Group Search",
                    "message": message,
                    "notification_id": "whatsapp_group_search",
                },
            )
        except Exception as e:  # Changed from bare except
            _LOGGER.error("Failed to search groups", exc_info=e)
            error_str = str(e)
            error_details = error_str[:200]
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WhatsApp Group Search Error",
                    "message": (
                        f"An error occurred while searching groups: {error_details}"
                    ),
                    "notification_id": "whatsapp_group_search_error",
                },
            )

    # Define common schemas
    s_account: dict[vol.Marker, Any] = {vol.Optional("account"): cv.string}  # type: ignore[misc]
    # Note: Both 'quote' and 'reply_to' are accepted for backwards compatibility.
    # If both are provided, 'quote' takes precedence over 'reply_to'.
    s_quotable: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_account,
        vol.Optional("quote"): cv.string,
        vol.Optional("reply_to"): cv.string,
        vol.Optional("expiration"): vol.Any(None, vol.Coerce(int)),
    }

    msg_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("message"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_message",
        _handle_service,
        schema=vol.Schema(msg_schema),
    )

    poll_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("question"): cv.string,
        vol.Required("options"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("allow_multiple_responses", default=False): cv.boolean,
    }
    hass.services.async_register(
        DOMAIN,
        "send_poll",
        _handle_service,
        schema=vol.Schema(poll_schema),
    )
    image_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("url"): cv.string,
        vol.Optional("caption"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_image",
        _handle_service,
        schema=vol.Schema(image_schema),
    )
    doc_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("url"): cv.string,
        vol.Optional("file_name"): cv.string,
        vol.Optional("message"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_document",
        _handle_service,
        schema=vol.Schema(doc_schema),
    )
    video_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("url"): cv.string,
        vol.Optional("message"): cv.string,
        vol.Optional("seconds"): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "send_video",
        _handle_service,
        schema=vol.Schema(video_schema),
    )
    audio_schema: dict[vol.Marker, Any] = {  # type: ignore[misc]
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("url"): cv.string,
        vol.Optional("ptt", default=False): cv.boolean,
        vol.Optional("seconds"): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "send_audio",
        _handle_service,
        schema=vol.Schema(audio_schema),
    )
    revoke_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("message_id"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "revoke_message",
        _handle_service,
        schema=vol.Schema(revoke_schema),
    )
    edit_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("message_id"): cv.string,
        vol.Required("message"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "edit_message",
        _handle_service,
        schema=vol.Schema(edit_schema),
    )
    list_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("sections"): cv.match_all,
        vol.Optional("expiration"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("title"): cv.string,
        vol.Optional("text"): cv.string,
        vol.Optional("button_text"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_list",
        _handle_service,
        schema=vol.Schema(list_schema),
    )
    contact_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("name"): cv.string,
        vol.Required("contact_number"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_contact",
        _handle_service,
        schema=vol.Schema(contact_schema),
    )
    webhook_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("url"): cv.string,
        vol.Optional("enabled", default=True): cv.boolean,
        vol.Optional("token"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "configure_webhook",
        _handle_service,
        schema=vol.Schema(webhook_schema),
    )
    loc_schema: dict[vol.Marker, Any] = {
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("latitude"): vol.Coerce(float),
        vol.Required("longitude"): vol.Coerce(float),
        vol.Optional("name"): cv.string,
        vol.Optional("address"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_location",
        _handle_service,
        schema=vol.Schema(loc_schema),
    )
    event_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("name"): cv.string,
        vol.Optional("description"): cv.string,
        vol.Optional("date"): cv.string,
        vol.Optional("location"): vol.Any(cv.string, dict),
        vol.Optional("join_link"): cv.string,
        vol.Optional("is_canceled"): cv.boolean,
        vol.Optional("expiration"): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "send_event",
        _handle_service,
        schema=vol.Schema(event_schema),
    )
    react_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("reaction"): cv.string,
        vol.Required("message_id"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_reaction",
        _handle_service,
        schema=vol.Schema(react_schema),
    )
    presence_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("presence"): vol.In(
            ["available", "unavailable", "composing", "recording", "paused"]
        ),
    }
    hass.services.async_register(
        DOMAIN,
        "update_presence",
        _handle_service,
        schema=vol.Schema(presence_schema),
    )
    buttons_schema: dict[vol.Marker, Any] = {
        **s_quotable,
        vol.Required("target"): cv.string,
        vol.Required("message"): cv.string,
        vol.Required("buttons"): vol.All(cv.ensure_list, [dict]),
        vol.Optional("footer"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_buttons",
        _handle_service,
        schema=vol.Schema(buttons_schema),
    )
    search_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Optional("name_filter", default=""): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "search_groups",
        _handle_service,
        schema=vol.Schema(search_schema),
    )
    mark_as_read_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Optional("message_id"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "mark_as_read",
        _handle_service,
        schema=vol.Schema(mark_as_read_schema),
    )
    get_contacts_schema: dict[vol.Marker, Any] = {
        **s_account,
    }
    hass.services.async_register(
        DOMAIN,
        "get_contacts",
        _handle_service,
        schema=vol.Schema(get_contacts_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )
    check_number_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("number"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "check_number",
        _handle_service,
        schema=vol.Schema(check_number_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )

    create_group_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("subject"): cv.string,
        vol.Required("participants"): vol.All(cv.ensure_list, [cv.string]),
    }
    hass.services.async_register(
        DOMAIN,
        "create_group",
        _handle_service,
        schema=vol.Schema(create_group_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )

    group_participants_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("participants"): vol.All(cv.ensure_list, [cv.string]),
    }
    hass.services.async_register(
        DOMAIN,
        "add_group_participant",
        _handle_service,
        schema=vol.Schema(group_participants_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "remove_group_participant",
        _handle_service,
        schema=vol.Schema(group_participants_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "promote_group_participant",
        _handle_service,
        schema=vol.Schema(group_participants_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "demote_group_participant",
        _handle_service,
        schema=vol.Schema(group_participants_schema),
    )

    target_only_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "leave_group",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )

    group_subject_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("subject"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "update_group_subject",
        _handle_service,
        schema=vol.Schema(group_subject_schema),
    )

    group_desc_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("description"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "update_group_description",
        _handle_service,
        schema=vol.Schema(group_desc_schema),
    )

    group_settings_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Optional("announce"): cv.boolean,
        vol.Optional("locked"): cv.boolean,
    }
    hass.services.async_register(
        DOMAIN,
        "update_group_settings",
        _handle_service,
        schema=vol.Schema(group_settings_schema),
    )

    join_group_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("code"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "join_group",
        _handle_service,
        schema=vol.Schema(join_group_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )

    msg_id_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("message_id"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "star_message",
        _handle_service,
        schema=vol.Schema(msg_id_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unstar_message",
        _handle_service,
        schema=vol.Schema(msg_id_schema),
    )

    pin_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("message_id"): cv.string,
        vol.Optional("duration", default=86400): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "pin_message",
        _handle_service,
        schema=vol.Schema(pin_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unpin_message",
        _handle_service,
        schema=vol.Schema(msg_id_schema),
    )

    forward_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("message_id"): cv.string,
        vol.Required("destination"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "forward_message",
        _handle_service,
        schema=vol.Schema(forward_schema),
    )

    status_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Optional("message"): cv.string,
        vol.Optional("url"): cv.string,
        vol.Optional("caption"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "send_status",
        _handle_service,
        schema=vol.Schema(status_schema),
    )

    hass.services.async_register(
        DOMAIN,
        "get_profile_picture",
        _handle_service,
        schema=vol.Schema(target_only_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "get_contact_info",
        _handle_service,
        schema=vol.Schema(target_only_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "block_contact",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unblock_contact",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "archive_chat",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unarchive_chat",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )

    mute_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Optional("duration_ms", default=8 * 3600 * 1000): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "mute_chat",
        _handle_service,
        schema=vol.Schema(mute_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unmute_chat",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )

    channel_info_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Optional("target"): cv.string,
        vol.Optional("code"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "get_channel_info",
        _handle_service,
        schema=vol.Schema(channel_info_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        "follow_channel",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unfollow_channel",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "mute_channel",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "unmute_channel",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )

    chat_label_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Required("label_id"): cv.string,
    }
    hass.services.async_register(
        DOMAIN,
        "add_chat_label",
        _handle_service,
        schema=vol.Schema(chat_label_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "remove_chat_label",
        _handle_service,
        schema=vol.Schema(chat_label_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "mark_as_unread",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "clear_chat",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )
    hass.services.async_register(
        DOMAIN,
        "delete_chat",
        _handle_service,
        schema=vol.Schema(target_only_schema),
    )

    get_messages_schema: dict[vol.Marker, Any] = {
        **s_account,
        vol.Required("target"): cv.string,
        vol.Optional("limit", default=50): cv.positive_int,
    }
    hass.services.async_register(
        DOMAIN,
        "get_chat_messages",
        _handle_service,
        schema=vol.Schema(get_messages_schema),
        supports_response=SupportsResponse.OPTIONAL,
    )

    _SERVICES_REGISTERED = True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the WhatsApp integration config entry.

    Called by Home Assistant when the user removes the integration or
    when HA shuts down.  This function:

    * Cancels the polling task and closes the HTTP session.
    * Unloads all platform entities (binary sensor, sensor, notify).
    * Removes all ``whatsapp.*`` services from the service registry.
    * Cleans up ``hass.data`` entries for the removed config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry being unloaded.

    Returns:
        ``True`` if unloading succeeded, ``False`` otherwise.
    """
    data = hass.data[DOMAIN][entry.entry_id]
    client: WhatsAppApiClient = data["client"]
    await client.close()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # If this was the last entry, remove global services
    if not hass.data[DOMAIN]:
        for service in _SERVICES:
            if hass.services.has_service(DOMAIN, service):
                hass.services.async_remove(DOMAIN, service)
        hass.data.pop(DOMAIN)

        global _SERVICES_REGISTERED
        _SERVICES_REGISTERED = False

    return bool(unload_ok)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
