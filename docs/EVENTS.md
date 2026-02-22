# ⚡ Events & Automations

Reactive automations are the core of this integration. Instead of just sending notifications, `whatsapp` allows you to build two-way logic.

## The Event: `whatsapp_message_received`

When a text message arrives on the linked WhatsApp account, an event is fired on the Home Assistant Event Bus.

### Event Data Structure

The event payload contains the following fields:

| Field            | Type   | Description                                                                                  |
| ---------------- | ------ | -------------------------------------------------------------------------------------------- |
| `sender`         | string | The full WhatsApp JID (e.g., `49123...@s.whatsapp.net` or `123...@g.us`), ideal for replies. |
| `sender_number`  | string | The cleaned numeric part of the sender (e.g., `49123456789`).                                |
| `entry_id`       | string | Unique identifier of the Home Assistant config entry that received the message.              |
| `session_id`     | string | The unique session ID used by the WhatsApp Home Assistant App for this instance.             |
| `raw_sender`     | string | The full WhatsApp JID (same as `sender`).                                                    |
| `content`        | string | The text body of the message.                                                                |
| `media_url`      | string | URL to download the received media (if any).                                                 |
| `media_path`     | string | Internal local path to the media file.                                                       |
| `media_type`     | string | Type of media: `image`, `video`, `audio`, `document`, `sticker`.                             |
| `media_mimetype` | string | MIME type of the media (e.g., `image/jpeg`).                                                 |
| `timestamp`      | int    | Unix timestamp of when the message was received.                                             |
| `raw`            | object | The complete raw JSON payload from the WhatsApp engine (for advanced users).                 |

---

## Integration Options

These options are configured within Home Assistant (Settings > Devices & Services > WhatsApp > Configure).

| Option                | Type    | Default | Description                                                                                                                                                           |
| :-------------------- | :------ | :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `marking_as_read`     | boolean | `true`  | Automatically marks incoming messages as read.                                                                                                                        |
| `self_messages`       | boolean | `false` | **(New)** If enabled, messages sent from your own account to yourself will trigger events in Home Assistant. Useful for "Note to Self" automations.                   |
| `polling_interval`    | int     | `5`     | How often (in seconds) the integration checks for new events from the addon.                                                                                           |
| `whitelist`           | string  | -       | Comma-separated list of phone numbers or group IDs. If set, only messages from these sources will be processed.                                                       |
| `mask_sensitive_data` | boolean | `false` | If enabled, phone numbers in Home Assistant logs will be partially hidden.                                                                                            |
| `retry_attempts`      | int     | `2`     | Number of times to retry sending a message if the first attempt fails.                                                                                                |
| `ui_auth_enabled`     | boolean | `false` | Enables Basic Authentication for the Web UI (Port 8066). Recommended if exposed to the internet.                                                                      |
| `ui_auth_password`    | string  | -       | The password for the Web UI (Username is always `admin`).                                                                                                             |

---

## 🤖 Automation Examples

### 1. Simple Command Trigger

React to a specific word from any user.

{% raw %}

```yaml
alias: WhatsApp Bot: Ping
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Ping"
action:
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "Pong! 🏓"
```

{% endraw %}

### 2. Secure Admin Commands

Only allow specific users (based on numeric ID) to control your home.

{% raw %}

```yaml
alias: WhatsApp Bot: Security Disarm
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    # Use the clean numeric sender ID for easy comparison
    value_template: "{{ trigger.event.data.sender_number == '4915112345678' }}"
  - condition: template
    value_template: "{{ trigger.event.data.content == 'Disarm Home' }}"
action:
  - service: alarm_control_panel.alarm_disarm
    target:
      entity_id: alarm_control_panel.home_alarm
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "🔓 Alarm has been disarmed by Admin."
```

{% endraw %}

### 3. Handling Button Responses

If you sent a message with buttons, you can catch the response by checking the `content` or the `raw` payload.

{% raw %}

```yaml
alias: WhatsApp Bot: Button Response
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.content == 'Yes, please' }}"
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
```

{% endraw %}

> **Tip:**
> For advanced logic, you can inspect `trigger.event.data.raw.message.buttonsResponseMessage` to get the specific `id` of the button that was clicked.

---

## 🙋 Self-Messages (`fromMe`)

By default, Home Assistant ignores messages that you send to yourself (i.e., messages where the sender is your own WhatsApp account). This is to prevent infinite loops where a bot might reply to its own message.

If you want to use Home Assistant to react to commands you send to yourself (from your phone to your own "My account" chat), you can enable this in the **Integration Options**:

1.  Go to **Settings** > **Devices & Services**.
2.  Find the **WhatsApp** integration.
3.  Click **Configure**.
4.  Check **Allow Self-Messages**.

When enabled, these messages will fire the same `whatsapp_message_received` event, but the `raw.key.fromMe` field will be `true`.
