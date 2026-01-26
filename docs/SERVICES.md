---
layout: default
title: Services & Features
nav_order: 3
---

# 🚀 Services & Messaging

This integration provides three ways to send messages. Choosing the right one depends on your use case (YAML vs. UI) and whether you need WhatsApp-specific features like polls or buttons.

---

## 🏗️ Which service should I use?

| Service Type | Service Name | Best for... | Recommendation |
| :--- | :--- | :--- | :--- |
| **Domain Service** | `whatsapp.send_message` | YAML Automations, Scripts | **Highly Recommended** 🌟 |
| **Legacy Notify** | `notify.whatsapp` | Multi-target, Simple Alerts | **Very Reliable** ✅ |
| **Entity Action** | `notify.send_message` | Visual Editor (UI), Dashboard | Use only in the UI 🛠️ |

---

## 1. `whatsapp.*` Services (Recommended)

These services are custom-built for this integration. They are the most reliable way to use all features (Polls, Buttons, etc.) without running into Home Assistant's strict schema errors.

### Text Message
```yaml
service: whatsapp.send_message
data:
  target: "+49123456789"
  message: "Hello from Home Assistant! 🚀"
```

### Polls 📊
```yaml
service: whatsapp.send_poll
data:
  target: "+49123456789"
  question: "Pizza tonight? 🍕"
  options: ["Yes!", "No", "Maybe"]
```

### Reactions ❤️
React to a message using its ID (from receiver events).
```yaml
service: whatsapp.send_reaction
data:
  target: "+49123456789"
  message_id: "ABC-123"
  reaction: "👍"
```

---

## 2. `notify.whatsapp` (Legacy Service)

This is a classic Home Assistant notification service. It is very flexible and works great for simple text or media alerts.

> [!TIP]
> Use this service if you want to send the same message to **multiple recipients** at once.

```yaml
service: notify.whatsapp
data:
  message: "Intruder detected! 🚨"
  target:
    - "+49111222333"
    - "12345678@g.us" # Group
```

**Sending Images via Legacy Notify:**
```yaml
service: notify.whatsapp
data:
  message: "Snapshot from Garden"
  target: "+49111222333"
  data:
    image: "https://example.com/snapshot.jpg"
```

---

## 3. `notify.send_message` (Entity Action)

This follows the modern **ADR-0010** standard. It is primarily designed for the **Visual Automation Editor** in the Home Assistant UI.

> [!WARNING]
> **Strict Schema**: If you use this service in **YAML**, Home Assistant may reject the `target` parameter inside the `data` block. If you see "extra keys not allowed", switch to `whatsapp.send_message` or `notify.whatsapp`.

```yaml
action: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: "Modern notification"
  # Note: 'target' inside 'data' is NOT recommended here in YAML!
```

---

## 📊 Available Entities

| Entity | Type | Description |
| :--- | :--- | :--- |
| `notify.whatsapp` | Notify | Main notification channel. |
| `binary_sensor.whatsapp_connected` | Binary Sensor | Status of the connection. |
| `sensor.whatsapp_uptime` | Sensor | **Diagnostic**: Uptime, Version, and Phone Number. |
| `sensor.whatsapp_messages_sent` | Sensor | Stats for sent messages. |

> [!TIP]
> Check the **Attributes** of the `uptime` sensor to see the version and paired phone number!
