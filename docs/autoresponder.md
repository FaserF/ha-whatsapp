---
layout: default
title: Auto Responder
nav_order: 13
---

# 🌴 WhatsApp Auto Responder (Away / Vacation Mode)

The **Auto Responder** feature allows your WhatsApp bridge to automatically send polite, informative, and configurable away replies when contacts message your bot or account.

This feature is ideal for:
- 🏖️ **Vacation / Holidays**: Let friends and family know when you are away and when you will be back.
- 📵 **Digital Detox / Phone-Free Time**: Inform incoming contacts that you are intentionally offline.
- 🏢 **Off-Hours / Out of Office**: Automatically manage incoming expectations outside business or study hours.

---

## ⚙️ Key Capabilities

| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Enabled** | Boolean | `false` | Master toggle to turn the auto-responder on or off. |
| **Start Time** | ISO 8601 DateTime | `None` (Immediate) | Optional scheduled activation time (e.g. `2026-08-20T08:00`). If omitted, starts immediately when enabled. |
| **End Time** | ISO 8601 DateTime | `None` (Indefinite) | Optional scheduled deactivation time (e.g. `2026-08-30T18:00`). If omitted, runs indefinitely until toggled off. |
| **Direct Chats Only** | Boolean | `true` | When `true`, replies **only** to 1:1 private chats. When `false`, also replies to group messages. |
| **Once Per Contact** | Boolean | `true` | When `true`, each sender receives at most **one** automated reply during the active period to prevent spam. When `false`, replies to every incoming message. |
| **Message Template** | String | Default EN Template | The template message containing variables formatted with dynamic placeholders. |

---

## 📝 Message Template Placeholders

You can customize the reply template using dynamic placeholders that are replaced in real-time upon dispatch:

- `{sender_name}`: The contact's name (resolved from phonebook name, push name, phone number, or "there").
- `{start_time}`: The configured start time/date string.
- `{end_time}`: The configured end time/date string.
- `{end_time_text}`: Formatted text ` (until <end_time>)` if an end date is set; empty otherwise.
- `{once_notice}`: Formatted reminder string `ℹ️ Note: You will only receive this automated reply once.` when `once_per_contact` is enabled.

### Default Template

```text
Hello {sender_name}!

🌴 I am currently away / on vacation{end_time_text} and have limited or no access to my messages.

This is an automated reply. I will get back to you as soon as I return.

{once_notice}
```

---

## 🛡️ Anti-Loop & Safety Protection

To prevent infinite loops and runaway spam:
- Messages sent by yourself (`fromMe: true`) are **never** auto-replied to.
- WhatsApp Status broadcasts (`status@broadcast`) and Newsletters (`@newsletter`) are automatically ignored.
- Senders are recorded in the internal responder store *before* dispatching to avoid race condition duplicates.
- When toggling the feature off and on, the seen contact cache is automatically reset.

---

## 🖥️ Configuration in Web UI

1. Open the WhatsApp Add-on Web UI.
2. In the **📊 Overview** tab, scroll to the **🌴 Auto Responder** card.
3. Configure the start/end dates, template message, and options.
4. Click **Save Configuration** (or **Reset Seen Contacts** if you want contacts to receive a new response during an ongoing period).

---

## 🏠 Home Assistant Integration

### 1. Master Switch Entity

- **Entity ID**: `switch.whatsapp_<account>_auto_responder`
- **State**: `on` / `off`
- **Attributes**:
  - `is_active`: `true` if enabled and currently within the configured `start_time` / `end_time` window.
  - `start_time`: Configured start timestamp.
  - `end_time`: Configured end timestamp.
  - `direct_only`: `true` / `false`.
  - `once_per_contact`: `true` / `false`.
  - `seen_count`: Number of unique contacts who have received an automated reply in the current period.

### 2. Services

#### `whatsapp.set_auto_responder`

Configures and enables/disables the Auto Responder dynamically from automations or scripts.

```yaml
service: whatsapp.set_auto_responder
data:
  account: "49171234567"
  enabled: true
  start_time: "2026-08-20T08:00"
  end_time: "2026-08-30T18:00"
  direct_only: true
  once_per_contact: true
  message_template: >
    Hi {sender_name}!
    I am out of the office{end_time_text}.
    This is an automatic response.
    {once_notice}
```

#### `whatsapp.reset_auto_responder_seen`

Clears the seen contacts list so that all contacts can receive a fresh automatic response.

```yaml
service: whatsapp.reset_auto_responder_seen
data:
  account: "49171234567"
```

---

## 💡 Automation Example: Vacation Calendar Sync

Activate the Auto Responder automatically when your Home Assistant calendar enters a "Vacation" state:

```yaml
alias: "WhatsApp: Auto Responder for Vacation"
trigger:
  - platform: state
    entity_id: calendar.holidays
    to: "on"
action:
  - service: whatsapp.set_auto_responder
    data:
      enabled: true
      end_time: "{{ state_attr('calendar.holidays', 'end_time') }}"
      direct_only: true
      once_per_contact: true
```
