# Whitelist Feature

The WhatsApp integration supports a **Whitelist** feature, allowing you to restrict interaction to specific users and groups. This is similar to the Telegram bot whitelist.

## How it works

When a whitelist is configured:

1. **Incoming Messages**: Only messages from whitelisted senders or groups will fire the `whatsapp_message_received` event. All other messages are ignored and logged as `INFO` in the Home Assistant logs.
2. **Outgoing Messages**: All outgoing services (message, poll, image, etc.) will check the recipient. If the recipient is not whitelisted, the message will not be sent, and an `INFO` log entry will be created.

## Configuration

You can configure the whitelist in the **Integration Options**:

1. Go to **Settings** -> **Devices & Services**.
2. Find the **WhatsApp** integration and click **Configure**.
3. In the **Whitelist** field, enter a comma-separated list of:
   - **Phone Numbers**: Numeric strings (e.g., `49123456789`). The `+` prefix is optional.
   - **Group IDs**: Unique WhatsApp group identifiers (e.g., `1234567890-111222333`).

### Examples

- `49123456789` - Only allow communication with this specific number.
- `49123456789, 49987654321` - Allow multiple numbers.
- `1234567890-111222333` - Allow a specific group chat.
- `49123456789, 1234567-890` - Allow a user and a group.

## Important Notes

- **Groups**: If a Group ID is whitelisted, **any** user in that group can interact with the bot within that specific chat. You do not need to whitelist every member of the group individually.
- **Empty Whitelist**: If the field is left empty (default), **no filtering** is applied, and all users/groups can interact with the integration.
- **Logging**: Filtered messages are logged with `INFO` level. If you expect a message but don't see it, check your Home Assistant logs.
