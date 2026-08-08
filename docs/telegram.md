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

---

## ❓ Troubleshooting & Important Telegram Bot API Notes

### 🛡️ 1. Telegram Bot Group Privacy Mode (Messages from Telegram -> WhatsApp not arriving)
By default, Telegram Bot API enables **Group Privacy Mode** on all newly created bots via `@BotFather`.
- **Symptom**: Messages sent in a Telegram Group are ignored by the bot and do not sync to WhatsApp (unless the message starts with `/` or tags `@botname`).
- **Solution**:
  1. Open Telegram and send a message to `@BotFather`.
  2. Send `/mybots` and select your bot.
  3. Go to **Bot Settings** -> **Group Privacy**.
  4. Click **Turn off** (until it confirms `Group Privacy is DISABLED`).
  5. Remove the bot once from your Telegram Group and re-add it.

---

### 🆔 2. Telegram Group ID Changes (Supergroups & Topics)
When a standard Telegram group is upgraded to a **Supergroup** (or when Topics/Forums are enabled), Telegram changes the Chat ID from a short negative number (e.g. `-3625914253`) to a Supergroup ID starting with `-100` (e.g. `-1003625914253`).
- **Solution**: Open the Add-on Web UI, click **Edit** on the mapping, and select the group again from the Telegram dropdown menu to automatically fetch the updated Supergroup ID.

