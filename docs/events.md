---
layout: default
title: Events & Automations
nav_order: 4
permalink: /events.html
---

# ⚡ Events & Automations

Reactive automations are the heart of this integration. This guide covers how to listen for messages, button clicks, poll votes, and emoji reactions.

## The Event: `whatsapp_message_received`

Every interaction from the linked WhatsApp account triggers a `whatsapp_message_received` event in Home Assistant.

### Event Data Structure

| Field                | Type   | Description                                                                                     |
| :------------------- | :----- | :---------------------------------------------------------------------------------------------- |
| `type`               | string | The interaction type: `chat`, `poll_update`, `reaction`, `event`, `button_reply`, `list_reply`. |
| `sender`             | string | The full JID (e.g., `49123...@s.whatsapp.net` or `123...@g.us`).                                |
| `sender_number`      | string | Clean numeric part of the sender (e.g., `49123456789`).                                         |
| `sender_name`        | string | Display name or push name of the sender (e.g., `John Doe`).                                     |
| `content`            | string | The text body or selected button/row text.                                                      |
| `selected_id`        | string | **(Special)** The ID of the clicked button or list row.                                         |
| `vote`               | list   | **(Special)** For `poll_update`, a list of selected options.                                    |
| `reaction`           | string | **(Special)** For `reaction`, the emoji. Empty when a reaction is removed.                      |
| `reacted_message_id` | string | **(Special)** For `reaction`, the ID of the message that was reacted to.                        |
| `media_url`          | string | URL to download received media.                                                                 |
| `timestamp`          | int    | Unix timestamp of the message.                                                                  |

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

### 5. Reaction as a Quick Reply

When the garage has been open for 10 minutes, send a message and close it if someone reacts with 👍. `whatsapp.send_message` returns the ID of the sent message, which is matched against `reacted_message_id`. This also works for reactions to messages sent by Home Assistant.

```yaml
alias: "WhatsApp: Close Garage on Reaction"
mode: single
trigger:
  - platform: state
    entity_id: cover.garage_door
    to: "open"
    for: "00:10:00"
action:
  - service: whatsapp.send_message
    data:
      target: "49171234567"
      message: "The garage is still open. React with 👍 to close it."
    response_variable: sent
  - wait_for_trigger:
      - platform: event
        event_type: whatsapp_message_received
        event_data:
          type: "reaction"
          reacted_message_id: "{{ sent.message_id }}"
    timeout: "00:30:00"
    continue_on_timeout: false
  - condition: template
    value_template: "{{ wait.trigger.event.data.reaction == '👍' }}"
  - service: cover.close_cover
    target:
      entity_id: cover.garage_door
```

Notes:

- `id` of a reaction event is the reaction's own ID, not the reacted message's.
- Removing a reaction fires the event again with an empty `reaction`.
- Reactions made from the linked account itself are fired as `whatsapp_message_sent`. With **Allow Self-Messages** enabled they also fire `whatsapp_message_received`, with `sender` set to `me`.
- If the reactor's phone number can't be resolved from their WhatsApp LID, `sender` stays an `@lid` JID.
- If a whitelist is configured, reactions from chats that aren't on it are dropped, like any other incoming message. This also applies to your own reactions with **Allow Self-Messages** enabled.

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
