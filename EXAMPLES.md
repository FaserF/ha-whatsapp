# 📖 WhatsApp Integration Examples & Automations

This documentation provides detailed examples for using the WhatsApp integration in Home Assistant, following the **modern Notify Standard (ADR-0010)**.

---

## 🚀 Modern Notify Service (Recipient Handling)

In the new `notify.send_message` standard, the recipient phone number is passed via the `target` parameter within the `data` block.

### 🏠 Simple Text Message
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Hello from Home Assistant! 🚀"
  target: "+49123456789" # Phone number or Group JID
```

### 🔘 Message with Interactive Buttons
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "The garage door is still open. Close it?"
  target: "+49123456789"
  data:
    footer: "Security Alert"
    buttons:
      - buttonId: "garage_close"
        buttonText: { displayText: "Close now 🏠" }
        type: 1
      - buttonId: "garage_ignore"
        buttonText: { displayText: "Ignore ❌" }
        type: 1
```

### 📊 Polls
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Poll"
  target: "+49123456789"
  data:
    poll:
      question: "What's for dinner?"
      options:
        - "Pizza"
        - "Sushi"
```

### 📍 Location
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Check this out!"
  target: "+49123456789"
  data:
    location:
      latitude: 52.5200
      longitude: 13.4050
      name: "Berlin"
      address: "Alexanderplatz"
```

---

## 🤖 Automations (Using the 'target' from Event)

When building automations, the "target" is dynamic.

### 📨 Reacting to Bot Commands
```yaml
alias: "WhatsApp Bot: Status Request"
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.text == '/status' }}"
action:
  - service: notify.send_message
    target:
      entity_id: notify.whatsapp
    data:
      message: "Home Status: {{ states('alarm_control_panel.home') }}"
      target: "{{ trigger.event.data.raw.key.remoteJid }}" # Sends reply back to origin (User or Group)
```

---

### 📸 Camera Snapshot on Alarm
```yaml
alias: "WhatsApp: Camera Alarm"
trigger:
  - platform: state
    entity_id: binary_sensor.doorbell_motion
    to: "on"
action:
  - service: camera.snapshot
    data:
      filename: "/config/www/tmp/snapshot.jpg"
    target:
      entity_id: camera.doorbell
  - delay: "00:00:01"
  - service: notify.send_message
    target:
      entity_id: notify.whatsapp
    data:
      message: "Motion at the door!"
      target: "+49123456789"
      data:
        image: "https://your-domain.com/local/tmp/snapshot.jpg"
```

---

## 💡 Important Note
1.  **Recipient**: The `target` field is **mandatory**. Use a phone number with country code (e.g., `+49...`) or a WhatsApp Group ID (e.g., `123456@g.us`).
2.  **Multiple Targets**: You can also pass a list: `target: ["+49123", "+49456"]`.
3.  **Standard Alignment**: These examples follow the modern Home Assistant Notify standard.
