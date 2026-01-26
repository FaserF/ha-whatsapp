---
layout: default
title: Services & Features
nav_order: 3
---

# 🚀 Services & Features

This integration follows the modern **Home Assistant Notify Standard (ADR-0010)**. You can use the unified `notify.send_message` service to interact with WhatsApp.

---

## 💬 The `notify.send_message` Service

This is the primary way to send content. You must specify the WhatsApp entity and the target.

### Standard Text
> [!TIP]
> Use standard text messages for simple alerts. They are compatible with 100% of WhatsApp clients.

```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Hello World! 🚀"
  target: "+49123456789" # International format
```

---

## 🔘 Advanced Features (via `data`)

WhatsApp-specific features are passed within the `data` block of the service call.

### Interactive Buttons
Buttons allow users to reply with a single tap. Great for "Yes/No" confirmations.
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Do you want to turn off the lights?"
  target: "+49123456789"
  data:
    footer: "Home Butler"
    buttons:
      - buttonId: "light_off_yes"
        buttonText: { displayText: "Yes, please! ✅" }
        type: 1
      - buttonId: "light_off_no"
        buttonText: { displayText: "No, leave them on 🌑" }
        type: 1
```

### Polls
Create native WhatsApp polls for group decisions.
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Vote now!"
  target: "+49123456789"
  data:
    poll:
      question: "What should we eat today?"
      options:
        - "Pizza 🍕"
        - "Burger 🍔"
        - "Sushi 🍣"
```

### Reactions
React to an existing message with an emoji. You need the `message_id` from the incoming message event.
```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Reaction"
  target: "+49123456789"
  data:
    reaction:
      reaction: "👍"
      message_id: "ABC-123-XYZ" # From event data
```

### Images & Snapshots
> [!IMPORTANT]
> To send local Home Assistant images, you must first save them to the `/config/www/` (local) folder so they are accessible via an HTTP URL.

```yaml
service: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Someone is at the door!"
  target: "+49123456789"
  data:
    image: "https://your-domain.com/local/camera_snapshot.jpg"
```

---

## 📊 Available Entities

| Entity | Type | Description |
| :--- | :--- | :--- |
| `notify.whatsapp` | Notify | Main notification channel. |
| `binary_sensor.whatsapp_connected` | Binary Sensor | Status of the connection to WhatsApp servers. |
| `sensor.whatsapp_messages_sent` | Sensor | Count of messages sent in the current session. |
| `sensor.whatsapp_messages_received` | Sensor | Count of messages received. |

> [!TIP]
> Check the **Attributes** of the `sent` and `received` sensors to see the content and recipient of the last message!
