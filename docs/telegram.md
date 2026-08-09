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

### 9. 🪞 1:1 Direct Chat Mirror (`is_direct_chat_mirror`)
- **Description**: Enables clean 1:1 message relay between any WhatsApp chat (Direct 1:1 DM or dedicated WA Group) and any Telegram chat (Direct Bot DM or Telegram Group/Topic). Strips all group and sender header clutter (`[Group | Sender]`), so conversations feel like native 1:1 direct messages.
- **Default**: `false`

---

### 10. 📊 Poll Sync Modes & Options (`poll_sync_mode`)
- **Description**: Configures how polls and poll votes are synchronized between WhatsApp and Telegram:
  - **Text Diagram & Updates** (`text_diagram` - Default): Sends poll status as a text diagram into the target chat, sends vote updates as text messages in the chat (enabled by default), and cleans up / deletes old poll update messages where possible (enabled by default).
  - **Native Poll Sync & Auto-Vote** (`native_sync`): Creates a native Telegram/WhatsApp poll in the target chat and automatically casts a vote for the current winning option from the source poll.
  - **Native Poll Sync without Vote** (`native_no_vote`): Creates a native Telegram/WhatsApp poll in the target chat without automatically voting for options.
  - **Single Notification Only** (`once_no_update`): Sends the initial poll information once as a single text message and suppresses all subsequent vote update messages.
- **Individual Toggles**:
  - `poll_send_text_diagram` (Default: `true` / Enabled): Send status update as a text diagram into the target.
  - `poll_send_update_message` (Default: `true` / Enabled): Send repeated vote updates into the chat.
  - `poll_delete_old_message` (Default: `true` / Enabled): Delete the old update message when a new vote update arrives.

---

### 11. 📍 Native Location & Live Location Sharing
- **Description**: Bi-directional native location pin sharing between WhatsApp and Telegram:
  - **Telegram -> WhatsApp**: Receiving a location pin in Telegram translates directly into a native WhatsApp location pin (`degreesLatitude` & `degreesLongitude`) rather than plain text.
  - **WhatsApp -> Telegram**: Sending a location pin in WhatsApp triggers Telegram's native `sendLocation` API to display an interactive map pin directly in Telegram.
  - **Live Locations**: Supports real-time GPS live location tracking node translation across platforms.

---

### 12. 📇 Native Contact Cards (`sendContact`)
- **Description**: Bi-directional native contact sharing:
  - **WhatsApp -> Telegram**: Extracted contact vcards (`contactMessage` / `contactsArrayMessage`) are sent to Telegram as native contact objects using `sendContact`.
  - **Telegram -> WhatsApp**: Shared contact cards in Telegram (`msg.contact`) are constructed into native WhatsApp vcard contact nodes.

> **TIP:** After every native location pin (both directions), a follow-up text message with the sender's name and location label is automatically appended — so recipients always know who sent the location.

---

### 13. 📹 Video Notes & Media Group Support
- **Description**:
  - **Video Notes**: Telegram Video Notes (`msg.video_note`) are mapped directly to native WhatsApp round video messages (`ptvMessage` / `ptv: true`).
  - **Media Groups**: Photos & Videos sent in multi-media albums/bundles (`media_group_id`) preserve group association flags during relay.

---

### 14. 👥 System & Group Event Syncing (`group-participants.update` & Telegram System Events)
- **Description**: Bi-directionally mirrors group membership changes, promotions, and pins:
  - **WhatsApp -> Telegram**: When a user joins, leaves, is removed, or is promoted/demoted to admin in WhatsApp, a clean system notification card is posted to the mapped Telegram group.
  - **Telegram -> WhatsApp**: When members join/leave a Telegram group (`msg.new_chat_members` / `msg.left_chat_member`) or a message is pinned (`msg.pinned_message`), a system notification card is relayed to WhatsApp.

---

### 15. 📅 WhatsApp Event Messages (`eventMessage`)
- **Description**: WhatsApp event/appointment cards are forwarded to Telegram as rich formatted messages. Telegram has no native event type, so the full event details are extracted and formatted as an HTML card:
  - **WhatsApp → Telegram**: Sends a structured event card with name (bold), date/time, description, location and join link (clickable).
  - **Telegram → WhatsApp**: Plain text is relayed as-is (no native WA event can be created from unstructured Telegram messages).

**Example output in Telegram:**
```
WA Gateway Test Group | Fabian Seitz:
📅 [Event]: Sommerfest
🕐 Samstag, 10. August 2025, 18:00
📝 Komm vorbei!
📍 Münchner Rathaus
🔗 Join Link
```

> **Note:** If the event is canceled (`isCanceled: true`), the title shows **📅 [Event ❌ ABGESAGT]**.

---

## 🛠️ Step-by-Step Guide: 1:1 Direct Chat Mirror Setup

1:1 Direct Chat Mirroring is **100% flexible** on both platforms:
- **WhatsApp side**: You can map either a direct WhatsApp 1:1 chat (`<phone>@s.whatsapp.net`) OR a dedicated WhatsApp group (`<group_id>@g.us`).
- **Telegram side**: You can map either a direct Telegram Bot DM (`<user_id>`) OR a Telegram Group/Supergroup/Topic (`<chat_id>`).

### Recommended Setup Flow:

#### Step 1: Set Up Telegram (Bot or Group)
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts to get your **Bot Token**.
3. Disable Group Privacy: `/mybots` -> Select Bot -> **Bot Settings** -> **Group Privacy** -> **Turn off**.
4. Have the user open a chat with your Telegram Bot and send a `/start` message (or add the bot to a Telegram group).

#### Step 2: Choose Your WhatsApp Chat Variant
- **Variant 1: Solo WhatsApp Group (Recommended for single phone number setup)**
  Create a WhatsApp group where **ONLY YOUR OWN PHONE NUMBER is present (no other phone numbers or real contacts are added)**. Name the group after your target contact (e.g. `Max Mustermann`) and set their profile picture. Everything you type into this solo group is picked up by the bridge and sent seamlessly to Telegram.
- **Variant 2: Direct WhatsApp 1:1 Chat (Multi-Number / Separate WA Account setup)**
  If you run the WhatsApp Bot on a separate secondary WhatsApp phone number or dedicated bot account, you can directly select the 1:1 phone number JID (`<phone>@s.whatsapp.net`).

#### Step 3: Choose Your Telegram Variant
- **Variant A: Standalone Telegram Bot per Contact**
  Create a dedicated bot via `@BotFather` for each contact (e.g., `Max_Bot`). The Telegram user chats 1:1 with this bot.
- **Variant B: Single Shared Telegram Bot with Separate DMs**
  Use one single Telegram bot for all your contacts. Each Telegram user sends `/start` to the same bot, and you map their individual Telegram User Chat IDs to separate WhatsApp chats/groups.
- **Variant C: Telegram Group / Supergroup / Topic**
  Map the WhatsApp chat to a Telegram Group or a specific Forum Topic (`message_thread_id`).

#### Step 4: Create the 1:1 Mirror Mapping
1. Open the Add-on Web UI -> **Telegram Bridge** tab (or use HA Service `whatsapp.add_telegram_mapping`).
2. Select your WhatsApp JID (Direct or Group) and the Telegram Chat ID.
3. Check / enable **1:1 Direct Chat Mirror** (`is_direct_chat_mirror: true`).
4. Save the mapping.

> 💡 **Why Use a Solo WhatsApp Group? (Single Phone Number Efficiency)**:
> Since you only have your own single WhatsApp phone number, you don't need a second phone number or a second WhatsApp account!
> You create a WhatsApp group with **just yourself in it (NO other phone numbers/contacts)**.
> - Because your WhatsApp session (Baileys) runs in the background on your account, everything you send into this solo group is captured by the bridge and forwarded cleanly to the Telegram user via the Telegram Bot.
> - When the Telegram user replies to the bot, the message appears cleanly in your solo WhatsApp group.
> - **Result**: On WhatsApp, you are in a solo group named "Max Mustermann" with Max's picture—it feels 100% like a direct 1:1 chat with Max! Neither person needs an extra phone number, second WA account, or extra Telegram account.

Once saved, messages pass back and forth cleanly without header prefixes!

---

### 📊 1:1 Bridge Setup Variants Comparison Table

| Setup Variant | WhatsApp Side | Telegram Side | Primary Benefit / Ideal Use Case | Extra Phone Number / WA Account Needed? | Extra Telegram Account Needed? | Header Prefix Noise? |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Solo WA Group ↔ Standalone TG Bot** *(Recommended)* | Solo Group (Only yourself) named after contact | Standalone TG Bot DM | **1-Number Setup**: Feels 100% like 1:1 DM for both users without extra numbers or accounts | ❌ No | ❌ No | ❌ No (`is_direct_chat_mirror: true`) |
| **Solo WA Group ↔ Shared TG Bot** | Solo Group (Only yourself) named after contact | Single TG Bot (Separate User DMs) | **Bot Token Efficiency**: 1 TG Bot handles multiple contacts | ❌ No | ❌ No | ❌ No (`is_direct_chat_mirror: true`) |
| **Solo WA Group ↔ TG Group / Topic** | Solo Group (Only yourself) named after contact | Telegram Group or Forum Topic | **Group Collaboration**: Relay solo WA chat into a TG group/topic | ❌ No | ❌ No | ❌ No (clean) or optional headers |
| **Direct WA 1:1 DM ↔ TG Bot** | Direct WA Chat (`<phone>@s.whatsapp.net`) | Standalone or Shared TG Bot DM | **Dedicated Bot Account**: Uses secondary WA phone number as dedicated bot |  Yes | ❌ No | ❌ No (`is_direct_chat_mirror: true`) |
| **WA Group ↔ TG Group** *(Classic)* | Standard WA Group with multiple contacts | Standard TG Group | **Community Bridge**: Full group-to-group mirroring with sender headers | ❌ No | ❌ No | Yes (Headers `[Group \| Sender]` enabled) |

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

