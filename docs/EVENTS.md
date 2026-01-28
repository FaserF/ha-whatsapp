# ⚡ Events & Automations

Reactive automations are the core of this integration. Instead of just sending notifications, `whatsapp` allows you to build two-way logic.

## The Event: `whatsapp_message_received`

When a text message arrives on the linked WhatsApp account, an event is fired on the Home Assistant Event Bus.

### Event Data Structure

The event payload contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | The cleaned phone number (e.g., `49123456789`). Best for simple automation triggers. |
| `raw_sender` | string | The full WhatsApp JID (e.g., `49123...@s.whatsapp.net` or `12345678-999...@g.us`). |
| `content` | string | The text body of the message. |
| `timestamp` | int | Unix timestamp of when the message was received. |
| `raw` | object | The complete raw JSON payload from the WhatsApp engine (for advanced users). |

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
    value_template: "{{ trigger.event.data.sender == '4915112345678' }}"
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
