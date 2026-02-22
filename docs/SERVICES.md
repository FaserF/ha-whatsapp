---
layout: default
title: Services & Features
nav_order: 3
---

# 🚀 Services & Messaging

This integration provides multiple ways to interact with WhatsApp. This guide explains every service, every parameter, and provides "Pro-Tips" for the best experience.

---

## 🏗️ Which service should I use?

| Service Type | Service Name | Best for... | Recommendation |
| :--- | :--- | :--- | :--- |
| **Native Service** | `whatsapp.send_message` | YAML Automations, Scripts, Buttons, Polls | **Recommended** 🌟 |
| **Legacy Notify** | `notify.whatsapp` | Multi-target alerts, Simple text/images | **Reliable** ✅ |
| **Modern Action** | `notify.send_message` | Visual Editor (UI), Dashboard | UI Only 🛠️ |

---

## 🎨 Rich Formatting
Use these in any text field (message, caption, question):
- **Bold**: `*text*` -> **text**
- *Italic*: `_text_` -> *text*
- ~~Strikethrough~~: `~text~` -> ~~text~~
- `Monospace`: ` ```text``` ` -> `text`

---

## 💬 1. Messaging & Text

### `whatsapp.send_message`
Sends a plain text message. Supports quoting and disappearing messages.

#### Examples
```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'Hello from Home Assistant! 🚀'
  expiration: 86400 # Disappears in 24 hours
```

#### Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `target` | string | **Yes** | Phone number (`+49...`) or Group JID (`...@g.us`). |
| `message` | string | **Yes** | The text to send. Supports line breaks (`\n`) and formatting. |
| `quote` | string | No | The ID of a message to reply to. |
| `expiration` | number | No | Seconds until message disappears (`0`, `86400`, `604800`, `7776000`). |
| `account` | string | No | Phone number or Entry ID if you have multiple accounts. |

> [!TIP]
> Use `\n` in YAML for line breaks, or use the `|` symbol for multi-line strings.

---

### `whatsapp.edit_message`
Update the content of a message you already sent.

#### Examples
```yaml
service: whatsapp.edit_message
data:
  target: '491234567890'
  message_id: 'BAE5CCF5A...'
  message: 'Oops, I meant 4 PM! 🕓'
```

#### Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `target` | string | **Yes** | The chat where the message exists. |
| `message_id` | string | **Yes** | The ID of the message to edit. |
| `message` | string | **Yes** | The new text content. |

---

### `whatsapp.revoke_message`
Deletes a message for everyone (like "Delete for Everyone").

#### Examples
```yaml
service: whatsapp.revoke_message
data:
  target: '491234567890'
  message_id: 'BAE5CCF5A...'
```

---

## 🖼️ 2. Media & Files

### `whatsapp.send_image` / `video` / `audio` / `document`
Send media files via a public URL.

#### Example (Image)
```yaml
service: whatsapp.send_image
data:
  target: '+491234567890'
  url: 'https://example.com/camera.jpg'
  caption: 'Front Door! 📷'
```

#### Shared Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `url` | string | **Yes** | Publicly accessible HTTPS URL to the file. |
| `caption` | string | No | Text shown with the media (not for audio). |
| `ptt` | boolean | No | **(Audio only)** Set `true` for voice-note waveform style. |
| `file_name` | string | No | **(Document only)** Override the displayed filename. |

---

## 📊 3. Interactive Content

### `whatsapp.send_poll`
Interactive voting for groups or individuals.

```yaml
service: whatsapp.send_poll
data:
  target: '491234567890'
  question: 'What is for dinner?'
  options: ['Pizza 🍕', 'Pasta 🍝', 'Salad 🥗']
```

### `whatsapp.send_buttons`
Quick reply buttons (max 3).

```yaml
service: whatsapp.send_buttons
data:
  target: '491234567890'
  message: 'Doorbell is ringing!'
  buttons:
    - id: 'open'
      displayText: 'Open Door 🔓'
    - id: 'ignore'
      displayText: 'Ignore 🔇'
```

### `whatsapp.send_list`
A popup menu for more complex choices.

```yaml
service: whatsapp.send_list
data:
  target: '491234567890'
  title: 'Home Control'
  text: 'Select action'
  button_text: 'Open Menu'
  sections:
    - title: 'Climate'
      rows:
        - id: 'heat'
          title: 'Heating On'
        - id: 'cool'
          title: 'AC On'
```

---

## ⚙️ 4. Advanced & Utility

### `whatsapp.search_groups`
Find all your Group IDs instantly.

1. Call the service.
2. Check your HA Notifications (Bell icon).

### `whatsapp.update_presence`
Simulate "typing..." or "recording..." status.

### `whatsapp.mark_as_read`
Blue double-checks (✓✓) for messages or whole chats.

---

> [!IMPORTANT]
> Always verify your recipient's number in international format. The integration automatically converts numbers like `0171...` to the correct format if your country code is configured correctly.
