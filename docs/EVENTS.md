# ⚡ Events & Automations

Reactive automations are the core of this integration. Instead of just sending notifications, `whatsapp` allows you to build two-way logic.

## The Event: `whatsapp_message_received`

When a text message arrives on the linked WhatsApp account, an event is fired on the Home Assistant Event Bus.

### Event Data Structure

The event payload contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | The phone number of the sender (e.g., `+49123...`). |
| `content` | string | The text body of the message. |
| `timestamp` | int | Unix timestamp of when the message was received. |

---

## 🤖 Automation Examples

### 1. Simple "Ping-Pong" Bot
If someone writes "Status", reply with "Online".

{% raw %}
```yaml
alias: WhatsApp Status Bot
description: "Replies to 'Status' with system health."
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Status"  # Exact match
action:
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "✅ Home Assistant is Online!\nTime: {{ now().strftime('%H:%M') }}"
```
{% endraw %}

### 2. Security Disarm via Code
Allows disarming the alarm by sending a specific code from a specific number.

{% raw %}
```yaml
alias: Disarm Alarm via WhatsApp
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.sender == '+4915112345678' }}"
  - condition: template
    value_template: "{{ trigger.event.data.content == 'MySecretCode' }}"
action:
  - service: alarm_control_panel.alarm_disarm
    target:
      entity_id: alarm_control_panel.home_alarm
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "🔓 Alarm Disarmed."
```
{% endraw %}
