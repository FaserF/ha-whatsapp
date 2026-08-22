# ⚡ Events & Automations

Reactive automations are the heart of this integration. This guide covers how to listen for messages, button clicks, and poll votes.

## The Event: `whatsapp_message_received`

Every interaction from the linked WhatsApp account triggers a `whatsapp_message_received` event in Home Assistant.

### Event Data Structure

| Field           | Type   | Description                                                                         |
| :-------------- | :----- | :---------------------------------------------------------------------------------- |
| `type`          | string | The interaction type: `chat`, `poll_update`, `event`, `button_reply`, `list_reply`. |
| `sender`        | string | The full JID (e.g., `49123...@s.whatsapp.net` or `123...@g.us`).                    |
| `sender_number` | string | Clean numeric part of the sender (e.g., `49123456789`).                             |
| `sender_name`   | string | Display name or push name of the sender (e.g., `John Doe`).                         |
| `content`       | string | The text body or selected button/row text.                                          |
| `selected_id`   | string | **(Special)** The ID of the clicked button or list row.                             |
| `vote`          | list   | **(Special)** For `poll_update`, a list of selected options.                        |
| `media_url`     | string | URL to download received media.                                                     |
| `timestamp`     | int    | Unix timestamp of the message.                                                      |

---

## The Event: `whatsapp_message_sent`

This event is explicitly fired whenever a message is sent from your linked WhatsApp account (from your phone, WhatsApp Web, or Home Assistant).

### Event Data Structure

| Field              | Type    | Description                                                                         |
| :----------------- | :------ | :---------------------------------------------------------------------------------- |
| `from`             | string  | Always `"me"` for sent messages.                                                   |
| `to`               | string  | Destination JID (e.g. `49123...@s.whatsapp.net` or `123...@g.us`).                  |
| `sender`           | string  | Always `"me"`.                                                                      |
| `recipient`        | string  | Destination JID.                                                                    |
| `recipient_number` | string  | Clean numeric part of recipient (e.g. `49123456789`).                               |
| `content`          | string  | The text body or caption sent.                                                      |
| `type`             | string  | The interaction type (`chat`, `image`, `video`, `audio`, `document`, `poll`, etc.). |
| `is_group`         | boolean | `true` if sent to a group chat, `false` otherwise.                                  |
| `group_id`         | string  | **(Optional)** Group JID if `is_group` is true.                                     |
| `id`               | string  | Unique WhatsApp message ID.                                                         |
| `media_url`        | string  | **(Optional)** URL of sent media attachment.                                        |
| `entry_id`         | string  | Home Assistant config entry ID.                                                     |
| `session_id`       | string  | WhatsApp session ID.                                                                |

---

## The Event: `whatsapp_button_pressed`

This event is explicitly fired when a user clicks an interactive button sent by the integration, allowing for targeted button automations.

### Event Data Structure

| Field           | Type   | Description                                                                         |
| :-------------- | :----- | :---------------------------------------------------------------------------------- |
| `sender`        | string | The full JID of the user who pressed the button.                                    |
| `sender_number` | string | Clean numeric part of the sender (e.g., `49123456789`).                             |
| `sender_name`   | string | Display name or push name of the sender.                                            |
| `button_id`     | string | The unique ID of the clicked button (defined when sending).                         |
| `button_text`   | string | The display text of the clicked button.                                             |
| `message_id`    | string | The ID of the original message containing the buttons.                              |
| `timestamp`     | int    | Unix timestamp of the event.                                                        |

---

## 🤖 Automation Examples

### 1. Simple Command Trigger (Direct Reply)

Best for basic "bots".

```yaml
alias: "WhatsApp Bot: Ping"
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

### 2. Handling Button Clicks (Security)

React to specific button IDs you sent earlier.

```yaml
alias: "WhatsApp Bot: Alarm Control"
trigger:
  - platform: event
    event_type: whatsapp_button_pressed
condition:
  - condition: template
    # 'button_id' is the ID you defined in 'whatsapp.send_buttons'
    value_template: "{{ trigger.event.data.button_id == 'arm_away' }}"
action:
  - service: alarm_control_panel.alarm_arm_away
    target:
      entity_id: alarm_control_panel.home
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "🔒 Alarm armed successfully!"
```

### 3. Poll Vote Handler

Gather data from family votes.

```yaml
alias: "WhatsApp Bot: Dinner Vote"
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      type: "poll_update"
condition:
  - condition: template
    value_template: "{{ 'Pizza 🍕' in trigger.event.data.vote }}"
action:
  - service: input_select.select_option
    data:
      option: "Pizza"
    target:
      entity_id: input_select.dinner_choice
```

### 4. Outgoing Message Tracking (`whatsapp_message_sent`)

React whenever you send a message (e.g. from your phone or HA) to a specific person or group.

```yaml
alias: "WhatsApp: Outgoing Message Tracker"
trigger:
  - platform: event
    event_type: whatsapp_message_sent
condition:
  - condition: template
    value_template: "{{ trigger.event.data.recipient_number == '49123456789' }}"
action:
  - service: logbook.log
    data:
      name: "WhatsApp Sent"
      message: "Sent message to {{ trigger.event.data.recipient_number }}: {{ trigger.event.data.content }}"
```

---

## 🙋 Self-Messages (`fromMe`)

If you want Home Assistant to react to messages you send to yourself (Note to Self), enable **Allow Self-Messages** in the integration configuration.

- **Pro-Tip**: Use this as a private remote control for your home. You send "/lights off" to your own number, and HA reacts!

## 🛡️ Whitelisting

To prevent strangers from triggering your automations, always use a condition to check the `sender_number`.

```yaml
condition:
  - condition: template
    value_template: "{{ trigger.event.data.sender_number in ['49171234567', '49171987654'] }}"
```
