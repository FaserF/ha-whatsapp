---
layout: default
title: Buttons & Interactive Messages
nav_order: 11
---

# 🔘 Buttons & Interactive Messages

Buttons allow you to create interactive experiences for your users. Instead of typing a response, users can simply tap a button to trigger an action in Home Assistant.

---

## 🛠️ Usage Example

You can send buttons using the `whatsapp.send_buttons` service.

```yaml
service: whatsapp.send_buttons
data:
  target: "+49123456789"
  message: "Do you want to turn off the lights?"
  buttons:
    - id: "lights_off_yes"
      displayText: "Yes, please! 💡"
    - id: "lights_off_no"
      displayText: "No, leave them on."
  footer: "Smart Home Assistant"
```

### 🤖 Handling the Response

When a user taps a button, a `whatsapp_message_received` event is fired.

```yaml
alias: "Handle Button Press"
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Yes, please! 💡" # The displayText is sent as text content
action:
  - service: light.turn_off
    target:
      entity_id: all
```

> **TIP:**
> You can also check for `trigger.event.data.id` (or `trigger.event.data.raw.key.id` depending on bridge) to match the internal button ID precisely.

---

## ✨ Automatic Fallback: "Emulate Buttons via Polls" Option

If you already have existing automations using `whatsapp.send_buttons` or `notify.whatsapp` with `data.buttons` / `data.inline_keyboard`, you can enable the **"Emulate Buttons via Polls"** option in the integration settings:

1. Go to **Settings → Devices & Services → WhatsApp → Configure (Options)**
2. Enable **"Emulate Buttons via Polls"**
3. Save

### How it works:
* Every `whatsapp.send_buttons` or `notify` button call is automatically converted into a native WhatsApp **Poll** under the hood.
* The message text and footer are mapped to the poll question.
* The buttons (`displayText` / `text`) become the selectable poll options.
* When a user taps an option in WhatsApp, the integration intercepts the vote, resolves the corresponding button ID, and fires both:
  1. `whatsapp_button_pressed` (with `button_id: "your_id"`, matching native button press events)
  2. `whatsapp_message_received` (with the chosen option as `content`)

This gives you **100% backwards compatibility** with existing button automations without having to rewrite YAML!

---

## ⚠️ Known Technical Limitations & Deprecation in WhatsApp

> **IMPORTANT:**
> **Why do buttons fail to render on official WhatsApp mobile / desktop clients?**
>
> WhatsApp (Meta) deprecated and disabled legacy MD / multi-device protobuf buttons (`buttonsMessage`, `templateMessage`, `interactiveMessage`) for standard web/linked-device multi-device clients. 
> 
> When sending legacy buttons via the Web multi-device protocol (Baileys), WhatsApp's servers strip or reject the interactive button layout on modern WhatsApp clients (iOS, Android, WhatsApp Web/Desktop), causing the recipient to receive only the message body / header with no clickable buttons rendered.
>
> **Recommended Alternative: Interactive Polls (`whatsapp.send_poll`)** 📊
>
> For reliable single-tap interactive choices in Home Assistant with WhatsApp, use **Polls** directly or turn on the **"Emulate Buttons via Polls"** option!

```yaml
service: whatsapp.send_poll
data:
  target: "+49123456789"
  question: "¿Hay alguien en casa?"
  options:
    - "🔒 Hay gente"
    - "📷 No hay nadie"
```

---

## ⚠️ Limitations & Account Behavior

### 1. WhatsApp Button Support
Buttons are officially restricted by Meta exclusively to **WhatsApp Cloud API (Official Business API)**. On linked-device Web sessions (used by this addon and Baileys), button protobuf rendering is not supported by WhatsApp mobile clients.

### 2. The 3-Button Limit
Even where supported, WhatsApp restricts button messages to a maximum of 3 buttons.

### 3. Client Rendering
On modern mobile clients, button messages render only as plain text header/message.

### 4. Interactive Polls as Universal Replacement
Polls (`whatsapp.send_poll`) trigger `whatsapp_message_received` or poll update events when selected and work seamlessly without account restrictions.


---

## 🏗️ Telegram Compatibility (inline_keyboard)

For users migrating from Telegram, the `notify.whatsapp` service supports the `inline_keyboard` format and automatically normalizes it for WhatsApp:

```yaml
service: notify.whatsapp
data:
  message: "Arm System?"
  data:
    inline_keyboard:
      - - text: "Arm Away"
          callback_data: "arm_away"
        - text: "Arm Home"
          callback_data: "arm_home"
```

_The integration will automatically pick up the first 3 buttons and map `text` to `displayText` and `callback_data` to `id`._

---

## 🎛️ Home Assistant Button Entities

*Note: This page describes sending Interactive Message Buttons in WhatsApp.* 
If you are looking for the integration's native Home Assistant **Action Button Entities** (such as the **WhatsApp Reconnect** button or the **Diagnostic Test** button), you can find them in your Home Assistant device settings. See the [Troubleshooting Guide](troubleshooting.md) for more details.
