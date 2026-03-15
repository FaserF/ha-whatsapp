# 📖 WhatsApp Integration Examples & Automations

This guide provides comprehensive, beginner-friendly examples for all services available in the WhatsApp integration. Whether you are using the modern Home Assistant Notify standard or the native WhatsApp services, you'll find everything here.

---

## ⚡ Native WhatsApp Services (Recommended)

Native services offer the most control and are the most robust way to use the integration in YAML automations.

### 📝 1. Messaging & Text

#### Simple Message
```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'Hello! This is a simple text message. 🚀'
```

#### Message with Expiration (Disappearing Messages)
*Note: The expiration must match your chat settings (e.g., 86400 for 24h).*
```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'This message will self-destruct. 🕵️'
  expiration: 86400
```

#### Edit a Sent Message
*You need a `message_id` (from events or service response).*
```yaml
service: whatsapp.edit_message
data:
  target: '+491234567890'
  message_id: 'BAE5F...'
  message: 'Actually, the meeting is at 3 PM! 🕒'
```

#### Revoke (Delete) a Message
```yaml
service: whatsapp.revoke_message
data:
  target: '+491234567890'
  message_id: 'BAE5F...'
```

---

### 🖼️ 2. Media & Files

#### Send Image
```yaml
service: whatsapp.send_image
data:
  target: '+491234567890'
  url: 'https://www.home-assistant.io/images/favicon.jpg'
  caption: 'Check out the HA logo! 🏠'
```

#### Send Video
```yaml
service: whatsapp.send_video
data:
  target: '+491234567890'
  url: 'https://example.com/security_clip.mp4'
  message: '🎥 Motion detected at the front door!'
```

#### Send Audio / Voice Note (PTT)
*Setting `ptt: true` makes it look like a recorded voice message.*
```yaml
service: whatsapp.send_audio
data:
  target: '+491234567890'
  url: 'https://example.com/alarm_chime.mp3'
  ptt: true
```

#### Send Document
```yaml
service: whatsapp.send_document
data:
  target: '+491234567890'
  url: 'https://example.com/energy_report.pdf'
  file_name: 'Monthly_Report.pdf'
  message: 'Here is your report. 📊'
```

---

### 📊 3. Interactive Content

#### Send Poll
```yaml
service: whatsapp.send_poll
data:
  target: '+491234567890'
  question: 'What do you want for dinner?'
  options:
    - 'Pizza 🍕'
    - 'Sushi 🍣'
    - 'Burgers 🍔'
```

#### Send Buttons (Quick Response)
*Max 3 buttons. Tapping a button sends an event back to HA.*
```yaml
service: whatsapp.send_buttons
data:
  target: '+491234567890'
  message: 'Is someone at home?'
  buttons:
    - id: 'yes'
      displayText: 'Yes, I am! 🙋‍♀️'
    - id: 'no'
      displayText: 'No, empty house 🏠'
  footer: 'Smart Home Security'
```

#### Send List Menu
*Ideal for many choices. Opens a popup menu on the phone.*
```yaml
service: whatsapp.send_list
data:
  target: '+491234567890'
  title: '🏠 Home Control'
  text: 'Select an action:'
  button_text: 'Open Menu'
  sections:
    - title: 'Lights'
      rows:
        - id: 'lights_on'
          title: 'Turn On All'
        - id: 'lights_off'
          title: 'Turn Off All'
```

---

### ⚙️ 4. Administration & Utilities

#### Search for Group IDs
*Results appear in your Home Assistant Notifications area!*
```yaml
service: whatsapp.search_groups
data:
  name_filter: 'Family' # Optional
```

#### Set Presence Status
```yaml
service: whatsapp.update_presence
data:
  target: '+491234567890'
  presence: 'composing' # Shows "typing..."
```

#### Mark Messages as Read
```yaml
service: whatsapp.mark_as_read
data:
  target: '+491234567890'
  # Omit message_id to mark ALL unread messages in this chat as read.
```

---

## 🚀 Modern Notify Service (`notify.send_message`)

If you prefer the standard Home Assistant notification action, use this format.

```yaml
action: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: 'System Online 🟢'
  target: '+491234567890'
  data:
    # Most native parameters can be passed under this 'data' block
    expiration: 3600 # disappears in 1 hour
```

---

## 🤖 Advanced Automation Examples

### 🚗 Automatic Reply with Location
*Reply with the current car location when someone asks "Where is the car?"*

```yaml
alias: "Reply with Car Location"
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Where is the car?"
action:
  - service: whatsapp.send_location
    data:
      target: "{{ trigger.event.data.sender }}"
      latitude: "{{ state_attr('device_tracker.car', 'latitude') }}"
      longitude: "{{ state_attr('device_tracker.car', 'longitude') }}"
      name: "Tesla Model 3"
```

### 🚨 Handle Button Clicks
*Turn on the light when the "Yes" button is clicked.*

```yaml
alias: "Handle 'Light On' Button"
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  # Check if it was a button click and if the ID matches
  - condition: template
    value_template: "{{ trigger.event.data.content == 'Yes' }}"
action:
  - service: light.turn_on
    target:
      entity_id: light.hallway
```

### 📊 🚨 Handle Poll Votes
*React when someone votes for a specific option in a poll.*

```yaml
alias: Pizza Poll Handler
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      type: 'poll_update'
condition:
  # 'vote' is a list of selected option names (as strings)
  - condition: template
    value_template: "{{ 'Pizza' in trigger.event.data.vote }}"
action:
  - service: whatsapp.send_message
    data:
      target: '{{ trigger.event.data.from }}'
      message: 'Great choice! 🍕'
```


---

## 💡 Best Practices for Beginners

1.  **Format your numbers**: Always use the international format like `+49123...` or `49123...`. The integration handles the REST.
2.  **Groups**: Use `whatsapp.search_groups` to find your Group IDs. They look like `123456789@g.us`.
3.  **Security**: Use the `sender_number` field in automation conditions to ensure only authorized people can trigger your home actions.
4.  **Logging**: Enable `mask_sensitive_data` in the integration configuration if you share logs and want to hide phone numbers.
