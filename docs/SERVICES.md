---
layout: default
title: Services & Features
nav_order: 3
---

# 🚀 Services & Messaging

This integration provides three ways to send messages. Choosing the right one depends on your use case (YAML vs. UI) and whether you need WhatsApp-specific features like polls or buttons.

---

## 🏗️ Which service should I use?

| Service Type       | Service Name            | Best for...                   | Recommendation            |
| :----------------- | :---------------------- | :---------------------------- | :------------------------ |
| **Domain Service** | `whatsapp.send_message` | YAML Automations, Scripts     | **Highly Recommended** 🌟 |
| **Legacy Notify**  | `notify.whatsapp`       | Multi-target, Simple Alerts   | **Very Reliable** ✅      |
| **Entity Action**  | `notify.send_message`   | Visual Editor (UI), Dashboard | Use only in the UI 🛠️     |

## 🎨 Rich Formatting

You can use standard WhatsApp Markdown in any text field (message, caption, etc.):

| Style           | Syntax         | Example        | Result    |
| :-------------- | :------------- | :------------- | :-------- |
| **Bold**        | `*text*`       | `*Alert*`      | **Alert** |
| _Italic_        | `_text_`       | `_Warning_`    | _Warning_ |
| ~Strikethrough~ | `~text~`       | `~Old~`        | ~~Old~~   |
| `Monospace`     | ` ```text``` ` | ` ```Code``` ` | `Code`    |

---

## 1. `whatsapp.*` Services (Recommended)

These services are custom-built for this integration. They are the most reliable way to use all features without running into Home Assistant's strict schema errors.

### 💬 Text Message (`send_message`)

The most common way to send alerts.

```yaml
service: whatsapp.send_message
data:
  account: '49123456789' # Optional: Specify phone number or Entry ID for multi-instance
  target: '+49123456789' # '+' is optional, @s.whatsapp.net is added automatically
  message: 'Hello from Home Assistant! 🚀'
```

### 📊 Polls (`send_poll`)

Interactive polls with multiple options.

```yaml
service: whatsapp.send_poll
data:
  target: '49123456789'
  question: 'Pizza tonight? 🍕'
  options: ['Yes!', 'No', 'Maybe']
```

### 📸 Images (`send_image`)

Send images via a URL.

```yaml
service: whatsapp.send_image
data:
  target: '49123456789'
  url: 'https://your-domain.com/local/snapshot.jpg'
  caption: 'Front door movement! 📷'
```

### 📄 Documents (`send_document`)

Send files like PDFs, Zip archives, or spreadsheets.

```yaml
service: whatsapp.send_document
data:
  target: '49123456789'
  url: 'https://example.com/invoice.pdf'
  file_name: 'Invoice_January.pdf' # Optional: Rename the file
  message: 'Here is your monthly invoice.' # Optional: Add a caption
```

### 🎥 Videos (`send_video`)

Send video files (MP4, etc).

```yaml
service: whatsapp.send_video
data:
  target: '49123456789'
  url: 'https://example.com/video.mp4'
  message: 'Check this out! 🎥' # Optional: Add a caption
```

### 🎤 Audio (`send_audio`)

Send audio files or voice notes.

```yaml
service: whatsapp.send_audio
data:
  target: '49123456789'
  url: 'https://example.com/audio.mp3'
  ptt: true # Set to true to send as a voice note (waveform), false for audio file
```

### 🗑️ Delete/Revoke (`revoke_message`)

Delete a message for everyone in the chat.

```yaml
service: whatsapp.revoke_message
data:
  target: '49123456789'
  message_id: 'BAE5CCF5A...' # ID from event or reaction
```

### ✏️ Edit (`edit_message`)

Edit the text of a sent message.

```yaml
service: whatsapp.edit_message
data:
  target: '49123456789'
  message_id: 'BAE5CCF5A...'
  message: 'Corrected text'
```

### 🔗 Webhook (`configure_webhook`)

Configure the App to push events (messages) to a specific URL.

```yaml
service: whatsapp.configure_webhook
data:
  account: '49123456789'
  url: 'http://homeassistant:8123/api/webhook/YOUR_ID'
  enabled: true
```

### 🤖 Multi-Instance Routing

If you have multiple WhatsApp accounts configured, you can use the `account` parameter to specify which bot should handle the service call.

**You can provide:**

- The **Phone Number** (e.g., `49123456789`)
- The **Entry ID** (found in integration details)
- The **Title** of the integration instance

If `account` is omitted, the integration will attempt to use the only available account. If multiple accounts are found, the service call will fail with a validation error.

### 📋 List Message (`send_list`)

Send an interactive menu with sections and rows. Preferred over buttons on iOS.

```yaml
service: whatsapp.send_list
data:
  target: '1234567890'
  title: 'Main Title'
  text: 'Body text description'
  button_text: 'View Menu'
  sections:
    - title: 'Section 1'
      rows:
        - title: 'Option A'
          rowId: 'opt_a'
          description: 'Description for A'
    - title: 'Section 2'
      rows:
        - title: 'Option B'
          rowId: 'opt_b'
```

### 👤 Contact (`send_contact`)

Send a VCard contact that users can easily save.

```yaml
service: whatsapp.send_contact
data:
  target: '1234567890'
  name: 'Home Assistant'
  contact_number: '1234567890'
```

### 📍 Location (`send_location`)

Send a map pin with an optional name and address.

```yaml
service: whatsapp.send_location
data:
  target: '49123456789'
  latitude: 52.5200
  longitude: 13.4050
  name: 'Brandenburg Gate'
  address: 'Pariser Platz, Berlin'
```

### ❤️ Reactions (`send_reaction`)

React to an existing message using its context ID.

```yaml
service: whatsapp.send_reaction
data:
  target: '49123456789'
  message_id: 'ABC-123' # Get this from 'whatsapp_message_received' event
  reaction: '👍'
```

### 🔘 Buttons (`send_buttons`)

Send interactive buttons. You can provide a custom ID for each button to react to it in automations.

```yaml
service: whatsapp.send_buttons
data:
  target: '49123456789'
  message: 'Do you want to turn off the lights?'
  buttons:
    - id: 'light_on'
      displayText: 'Yes, please'
    - id: 'light_off'
      displayText: 'No, thanks'
  footer: 'Smart Home Assistant'
```

### ⌨️ Update Presence (`update_presence`)

Simulate typing or recording status.

```yaml
service: whatsapp.update_presence
data:
  target: '49123456789'
  presence: 'composing' # Available: composing, recording, available, unavailable, paused
```

---

## 2. `notify.whatsapp` (Legacy Service)

This is a classic Home Assistant notification service. It is very flexible and works great for simple text or media alerts.

> **Tip:**
> Use this service if you want to send the same message to **multiple recipients** at once.

```yaml
service: notify.whatsapp
data:
  message: '🚨 Intruder detected!'
  target:
    - '+49111222333'
    - '12345678-999999@g.us' # Group
```

**Advanced Notify Data:**
You can also use the `data` block to access advanced features via the legacy notify service.

```yaml
service: notify.whatsapp
data:
  message: 'Would you like some coffee?'
  target: '+49111222333'
  data:
    buttons:
      - id: 'coffee_yes'
        displayText: 'Yes ☕'
      - id: 'coffee_no'
        displayText: 'No'
```

---

## 3. `notify.send_message` (Entity Action)

This follows the modern **ADR-0010** standard. It is primarily designed for the **Visual Automation Editor** in the Home Assistant UI.

```yaml
action: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: 'Modern notification'
```

---

## 📊 Available Entities

| Entity                             | Type          | Description                                        |
| :--------------------------------- | :------------ | :------------------------------------------------- |
| `notify.whatsapp`                  | Notify        | Main notification channel.                         |
| `binary_sensor.whatsapp_connected` | Binary Sensor | Status of the connection.                          |
| `sensor.whatsapp_uptime`           | Sensor        | **Diagnostic**: Uptime, Version, and Phone Number. |
| `sensor.whatsapp_messages_sent`    | Sensor        | Stats for sent messages.                           |

---

## 🔍 Finding Group IDs

If you want to send messages to a group, you need its **Group ID** (JID). Use the helper service below.

### 🔍 `whatsapp.search_groups` (Helper)

Finding the "JID" (Group ID) for a group can be tricky. This service helps you find it easily.

**Parameters:**

- `name_filter` (Optional): Filter groups by name (case-insensitive). Leave empty to list ALL groups.

**How it works:**

1. Call the service: `action: whatsapp.search_groups` with optional `name_filter`
2. **Click the 🔔 bell icon** in the Home Assistant sidebar
3. A notification titled "WhatsApp Group Search" will show a table with:
   - Group Name
   - Group ID (the JID you need)
   - Participant count

> **💡 Example:**
>
> ```yaml
> action: whatsapp.search_groups
> data:
>   name_filter: 'Family'
> ```

---

> **Tip:**
> Group IDs look like `1234567890-111111111@g.us`. However, you can also just use the ID part `1234567890-111111111` and the integration will automatically add `@g.us`.

---

> **Tip:**
> Check the **Attributes** of the `uptime` sensor to see the version and paired phone number!
