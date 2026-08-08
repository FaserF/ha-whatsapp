---
layout: default
title: Telegram Bridge
nav_order: 12
---

# ✈️ WhatsApp <-> Telegram Native Bridge

The **WhatsApp <-> Telegram Native Bridge** allows you to seamlessly mirror chats, groups, and media between WhatsApp and Telegram in real-time.

---

## ⚙️ Configuration & Option Settings

When creating or editing a Chat Mapping in the Add-on Web UI or via Home Assistant Services, you can fine-tune the following options:

### 1. 👥 Include Group Name (`include_group_name`)
- **Description**: Prefixes synced messages with the source WhatsApp or Telegram group name in the header string.
- **Header Example**: `[Family Group | Alice]: Hello everyone!`
- **Default**: `false`

---

### 2. 👤 Include Sender Name (`include_sender_name`)
- **Description**: Prefixes synced messages with the display name or phone number of the original sender.
- **Header Example**: `[Alice]: Hello everyone!`
- **Default**: `true`

---

### 3. 🔄 Sync Own Self Messages (`sync_self_messages`)
- **Description**: Enables mirroring of messages that you manually send from your primary WhatsApp account/phone (outside of the automated bridge pipeline).
- **Use Case**: Useful if you operate the bot on your personal WhatsApp account and want your manual outgoing messages in WhatsApp to appear in the Telegram channel/group as well.
- **Default**: `false`

---

### 4. 🎭 Convert Formatting (`convert_formatting`)
- **Description**: Automatically translates message text formatting between WhatsApp Markdown and Telegram HTML:
  - WhatsApp `*bold*` ↔ Telegram `<b>bold</b>`
  - WhatsApp `_italic_` ↔ Telegram `<i>italic</i>`
  - WhatsApp `~strike~` ↔ Telegram `<s>strike</s>`
  - WhatsApp ` ```code``` ` ↔ Telegram `<code>code</code>`
- **Default**: `true`

---

### 5. 🕵️ Anonymize Phones (`anonymize_phone_numbers`)
- **Description**: Masks the middle digits of phone numbers in the message header to preserve user privacy in public Telegram groups or channels.
- **Header Example**: `[+49176***567]: Hello!`
- **Default**: `false`

---

### 6. 😀 Sync Reactions (`sync_reactions`)
- **Description**: Bi-directionally mirrors emoji reactions added to or removed from synced messages.
- **Default**: `true`

---

### 7. 🔒 Ignore Command Prefixes (`ignore_command_prefixes`)
- **Description**: Ignores messages starting with specific command prefixes (e.g. `!`, `/`) to prevent accidental command triggers or infinite bot loops across connected platforms.
- **Default**: `""` (Empty string)

---

### 8. 🧵 Telegram Forum Topic ID (`tg_thread_id`)
- **Description**: Directs messages to a specific **Forum Topic** within a Telegram Supergroup using Telegram's native `message_thread_id`.
- **Default**: `null`
