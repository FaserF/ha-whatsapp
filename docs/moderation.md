---
layout: default
title: Group Moderation & Bot Commands
nav_order: 8
---

# 🛡️ Group Moderation & Bot Commands Handbook

Welcome to the comprehensive guide for the **WhatsApp Group Moderation, Defender, and Interactive Bot Command Engine**. Modeled after popular community management bots (like Rose Bot and AegisBot), this system provides total control over WhatsApp group security, automated moderation, member verification, and interactive commands.

---

## 📖 Table of Contents

1. [Architecture & How It Works](#-architecture--how-it-works)
2. [Role-Based Access Control (RBAC)](#-role-based-access-control-rbac)
3. [Complete Command Reference](#-complete-command-reference)
   - [Public User Commands](#-public-user-commands)
   - [Admin Moderation Commands](#-admin-moderation-commands)
   - [Admin Management & Configuration Commands](#-admin-management--configuration-commands)
4. [Content Locks & Security Controls](#-content-locks--security-controls)
5. [Warnings & Automated Penalty Decay](#-warnings--automated-penalty-decay)
6. [Welcome Greetings & Captcha Verification](#-welcome-greetings--captcha-verification)
7. [Notes & Auto-Responder Filters](#-notes--auto-responder-filters)
8. [Gemini AI Capabilities](#-gemini-ai-capabilities)
9. [Anti-Raid & Flood Protection](#-anti-raid--flood-protection)
10. [Global Ban Federations](#-global-ban-federations)

---

## 🏗️ Architecture & How It Works

The Moderation Engine operates as a high-performance interceptor inside the WhatsApp gateway. Every incoming message and group event follows a strict execution pipeline:

```
Incoming Message ➔ Approved Whitelist Check ➔ Command Parser ➔ Global Ban Check ➔ Captcha Check ➔ Content Locks ➔ Word Blacklist ➔ Flood Rate Check ➔ Filters & Notes ➔ AI Assistant
```

### Key Highlights

- **Disabled by Default**: Privacy-first design. Moderation features remain completely dormant until enabled globally or for a specific group.
- **Prefix Engine**: Configure custom command prefixes per group (e.g. `!`, `/`, `#`). Defaults to `!`.
- **Stateless & Resilient**: Group settings are stored locally in `/data/moderation_config.json` and persist across container restarts.

---

## 🔐 Role-Based Access Control (RBAC)

Commands are categorized into **Public Commands** and **Admin Commands**.

- **Admin Detection**: A user is recognized as an Admin if:
  1. They are a WhatsApp Group Admin or Superadmin.
  2. Their phone number is listed in `admin_numbers` in the Addon Configuration.
  3. The message is sent by the bot account itself (`fromMe`).
- **Help Menu Filtering**: Non-admin users who type `!help` will only see public commands. Admin commands are hidden to prevent clutter and security discovery.
- **Unauthorized Interception**: If a regular member attempts to run an admin command (e.g. `!kick @user`), the bot responds with an explicit permission error message: `⚠️ Permission Denied: You must be a group admin to use !kick.`

---

## 🤖 Complete Command Reference

---

### 👥 Public User Commands

These commands can be run by **any member** in the group.

---

#### 1. `!help`
- **Description**: Displays the interactive command menu. Automatically hides admin commands when used by non-admins.
- **Syntax**: `!help`
- **Example**:
  ```
  User: !help
  Bot: 📖 Group Commands Help (Prefix: !)
       User Commands:
       • !help: Shows this help message
       • !ping: Check if the bot is responsive
       ...
  ```

---

#### 2. `!ping`
- **Description**: Verifies that the bot is online and active.
- **Syntax**: `!ping`
- **Response**: `🏓 Pong!`

---

#### 3. `!id`
- **Description**: Returns the unique JID (Jabber Identifier) of the current group chat and your own WhatsApp user JID. Useful for setting up Home Assistant automations.
- **Syntax**: `!id`
- **Response**:
  ```
  Group ID: 120363000000000000@g.us
  Your ID: 491701234567@s.whatsapp.net
  ```

---

#### 4. `!rules`
- **Description**: Displays the group rules. If an optional question is appended and Gemini AI is enabled, the bot uses AI natural language interpretation to answer questions based on the group's rules.
- **Syntax**: `!rules [question]`
- **Examples**:
  - `!rules` ➔ Displays stored group rules text.
  - `!rules Are external links allowed?` ➔ *Bot (via Gemini AI):* "Based on rule #2, links are only allowed if approved by an admin."

---

#### 5. `!info`
- **Description**: Displays a comprehensive status card for a target user (or yourself if no user is specified). Shows warning count, max limit, whitelist approval status, mute status, and recent warning log timestamps.
- **Syntax**: `!info [@user]`
- **Example**:
  ```
  User: !info @491701234567
  Bot: 📋 User Info: @491701234567
       🆔 ID: 491701234567
       ⚠️ Warnings: 2/3
       ✅ Approved: No
       🔇 Muted: Yes
       
       Warning History:
       1. Excessive caps lock (05/08/2026, 10:15)
       2. Shared link without permission (05/08/2026, 11:30)
  ```

---

#### 6. `!adminlist` (Alias: `!admins`)
- **Description**: Fetches and lists all current administrators of the WhatsApp group, visually distinguishing the Group Owner/Creator (👑) from Group Admins (👮).
- **Syntax**: `!adminlist` or `!admins`
- **Response**:
  ```
  👮 Group Admins (2):
  👑 @491701111111
  👮 @491702222222
  ```

---

#### 7. `!locktypes`
- **Description**: Displays all 12 available content lock types that admins can lock or unlock.
- **Syntax**: `!locktypes`
- **Response**: Lists `image`, `video`, `audio`, `document`, `sticker`, `url`, `invite`, `poll`, `contact`, `location`, `forwarded`, `rtl`.

---

#### 8. `!report`
- **Description**: Allows group members to flag problematic messages. When called (or sent as a reply to an offending message), it tags all group admins instantly with an optional reason.
- **Syntax**: `!report [reason]` (or reply to a message with `!report`)
- **Example**:
  ```
  User (replying to spam): !report Scam link
  Bot: 🚨 Report from @491703333333
       Admins requested.
       Reason: Scam link
       @491701111111 @491702222222
  ```

---

#### 9. `!get`
- **Description**: Fetches and posts a pre-saved text note by name.
- **Syntax**: `!get <notename>`
- **Example**: `!get wifi` ➔ *Bot:* "Guest Wi-Fi SSID: Home-Guest, Pass: 12345678"

---

#### 10. `!notes`
- **Description**: Lists all saved text notes available in the group.
- **Syntax**: `!notes`
- **Response**: Shows `#wifi`, `#faq`, `#rules`, etc.

---

#### 11. `!filters`
- **Description**: Lists all active auto-responder keyword triggers configured in the group.
- **Syntax**: `!filters`

---

#### 12. `!translate`
- **Description**: Translates a replied-to message or provided text into the group's target language using Gemini AI.
- **Syntax**: `!translate [text]` (or reply to a message with `!translate`)
- **Example**:
  ```
  User (replying to Spanish message): !translate
  Bot: 🌐 Translation (en):
       Hello everyone, welcome to the group!
  ```

---

### 👮 Admin Moderation Commands

These commands require **Group Admin** privileges.

---

#### 13. `!warn`
- **Description**: Issues a formal warning to a user. Can mention the user or be sent in reply to their message. When the user reaches `max_warnings` (default 3), the bot automatically executes the configured punishment (Mute, Kick, or Ban) and resets their warning count.
- **Syntax**: `!warn [@user] [reason]`
- **Example**: `!warn @491709999999 Stop spamming` ➔ *Bot:* "⚠️ Warning Issued to @491709999999 (1/3). Reason: Stop spamming"

---

#### 14. `!unwarn`
- **Description**: Clears all active warnings for the specified user.
- **Syntax**: `!unwarn [@user]`
- **Example**: `!unwarn @491709999999` ➔ *Bot:* "✅ Cleared warnings for @491709999999"

---

#### 15. `!warns`
- **Description**: Displays detailed warning logs for a user, including timestamps and reasons.
- **Syntax**: `!warns [@user]`

---

#### 16. `!kick` (Alias: `!ban`)
- **Description**: Immediately removes the targeted user from the WhatsApp group via Baileys `groupParticipantsUpdate`.
- **Syntax**: `!kick [@user] [reason]`
- **Example**: `!kick @491709999999 Unacceptable behavior` ➔ User is removed from group.

---

#### 17. `!tban`
- **Description**: Temporarily bans a user by kicking them and scheduling an automated notification timer when the ban duration expires.
- **Syntax**: `!tban <duration> [@user] [reason]`
- **Supported Durations**: `10s` (seconds), `30m` (minutes), `12h` (hours), `1d` (days).
- **Example**: `!tban 1d @491709999999 Off-topic spam` ➔ Kicks user for 1 day.

---

#### 18. `!mute`
- **Description**: Stummschaltung (Mute). Because WhatsApp does not natively allow muting individual users in a group, **the bot enforces mutes by automatically deleting any new messages sent by the muted user** as soon as they arrive!
- **Syntax**: `!mute [@user] [reason]`
- **Example**: `!mute @491709999999 Flooding` ➔ Any future message from `@491709999999` is deleted instantly.

---

#### 19. `!tmute`
- **Description**: Temporarily mutes a user for a specific duration. The bot auto-deletes their messages until the duration expires, after which the mute is lifted automatically.
- **Syntax**: `!tmute <duration> [@user] [reason]`
- **Example**: `!tmute 2h @491709999999 Cool down period`

---

#### 20. `!unmute`
- **Description**: Removes the mute restriction from a user, allowing them to send messages again.
- **Syntax**: `!unmute [@user]`

---

#### 21. `!del` (Alias: `!delete`)
- **Description**: Deletes the replied-to message immediately using WhatsApp's message deletion API.
- **Syntax**: `!del` (must reply to a message)

---

#### 22. `!approve`
- **Description**: Whitelists a user. Approved users **completely bypass** all content locks, word blacklists, anti-spam rate limits, and captchas.
- **Syntax**: `!approve [@user]`
- **Example**: `!approve @491708888888` ➔ User can now post links, images, etc., even if locked.

---

#### 23. `!unapprove`
- **Description**: Removes a user from the approved whitelist.
- **Syntax**: `!unapprove [@user]`

---

### 👮 Admin Management & Configuration Commands

---

#### 24. `!setrules`
- **Description**: Updates the group's rules text directly from WhatsApp.
- **Syntax**: `!setrules <text>`
- **Example**: `!setrules 1. Be polite. 2. No advertising. 3. No NSFW content.`

---

#### 25. `!promote`
- **Description**: Promotes a member to WhatsApp Group Admin.
- **Syntax**: `!promote [@user]`

---

#### 26. `!demote`
- **Description**: Demotes a Group Admin back to regular member status.
- **Syntax**: `!demote [@user]`

---

#### 27. `!setwelcome`
- **Description**: Sets the greeting message sent when a new member joins. Enables welcome greetings automatically.
- **Placeholders**:
  - `{mention}` ➔ `@491701234567` (clickable mention)
  - `{name}` ➔ `491701234567` (phone number/name)
  - `{group}` ➔ `My Group Name`
  - `{rules}` ➔ Group rules text
- **Syntax**: `!setwelcome <text>`
- **Example**: `!setwelcome Welcome {mention} to {group}! Please read our rules: {rules}`

---

#### 28. `!welcome`
- **Description**: Displays the current welcome message template.
- **Syntax**: `!welcome`

---

#### 29. `!setgoodbye`
- **Description**: Sets the message sent when a member leaves or is removed from the group.
- **Placeholders**: `{mention}`, `{name}`, `{group}`.
- **Syntax**: `!setgoodbye <text>`

---

#### 30. `!goodbye`
- **Description**: Displays the current goodbye message template.
- **Syntax**: `!goodbye`

---

#### 31. `!lock`
- **Description**: Locks a specific content type in the group. Any non-approved member attempting to post this content type will have their message deleted automatically.
- **Syntax**: `!lock <type>`
- **Example**: `!lock image`, `!lock url`, `!lock invite`, `!lock forwarded`

---

#### 32. `!unlock`
- **Description**: Unlocks a previously locked content type.
- **Syntax**: `!unlock <type>`

---

#### 33. `!locks`
- **Description**: Lists all currently active content locks in the group.
- **Syntax**: `!locks`

---

#### 34. `!save`
- **Description**: Saves a reusable text note. Once saved, any user can retrieve it with `!get <name>` or simply by typing `#<name>` in the chat.
- **Syntax**: `!save <name> <content>`
- **Example**: `!save faq For support visit https://example.com`

---

#### 35. `!filter`
- **Description**: Sets up an automated keyword responder. When a user message matches the trigger, the bot sends the reply.
- **Syntax**: `!filter <trigger> <reply>`
- **Example**: `!filter website Check out https://mywebsite.com`

---

#### 36. `!stop`
- **Description**: Deletes an auto-responder filter.
- **Syntax**: `!stop <trigger>`

---

#### 37. `!setlang`
- **Description**: Configures the target language for AI translations (`de`, `en`, `es`, `fr`, `it`, `ar`, `zh`, `ja`, etc.).
- **Syntax**: `!setlang <code>`
- **Example**: `!setlang de`

---

## 🔒 Content Locks & Security Controls

Content locks allow administrators to restrict specific media or text types. When a restricted message type is posted:
1. The message is **deleted instantly**.
2. A notice is posted: `🔒 Message deleted: Images are locked in this group.`
3. If configured, a secondary penalty (Warn, Kick, Ban) is applied to the sender.

### Supported Locks Table

| Lock Key | What it Blocks | Detection Mechanism |
| :--- | :--- | :--- |
| `image` | Photo attachments | Baileys `imageMessage` |
| `video` | Video attachments | Baileys `videoMessage` |
| `audio` | Voice notes and audio files | Baileys `audioMessage` |
| `document` | Files (PDFs, ZIPs, docs) | Baileys `documentMessage` |
| `sticker` | WebP stickers | Baileys `stickerMessage` |
| `url` | Web links | Text containing `http://`, `https://`, `www.` |
| `invite` | WhatsApp group links | Text containing `chat.whatsapp.com/` |
| `poll` | Poll creations & updates | Event type `poll_update` or poll creation |
| `contact` | Shared contact cards (vCards) | Baileys `contactMessage` / `contactsArrayMessage` |
| `location` | Location pins | Baileys `locationMessage` / `liveLocationMessage` |
| `forwarded` | Forwarded messages | Context info `isForwarded: true` |
| `rtl` | Right-to-Left character text | Regex `/[\u0591-\u07FF\uFB1D-\uFDFD\uFE70-\uFEFC]/` |

---

## ⚠️ Warnings & Automated Penalty Decay

The Warning Engine tracks user infractions (manual warnings via `!warn`, or automatic warnings from blacklisted words, toxicity detection, or flood protection).

### Features
- **Max Warnings**: Threshold (1 to 20, default 3).
- **Max Action**: Penalty executed upon reaching threshold (`mute`, `kick`, `ban`). Warnings reset to 0 after penalty.
- **Warning Decay (`decay_hours`)**: Configurable expiration window (e.g. 24 hours). Warnings older than `decay_hours` automatically expire and vanish from the user's warning count, giving reformed users a fresh start!

---

## 👋 Welcome Greetings & Captcha Verification

### Welcome & Goodbye Greetings
When a new participant joins (`action === 'add'`) or leaves (`action === 'remove'`), the bot generates a dynamic message substituting template tags:
- `{mention}` ➔ `@491701234567`
- `{name}` ➔ `491701234567`
- `{group}` ➔ Group Title
- `{rules}` ➔ Group Rules text

### Captcha Verification Modes
Protect your group against automated spam accounts joining via invite links.
- **Button Challenge**: New user must reply with the keyword `"pass"`.
- **Math Problem**: Generates a random addition challenge (e.g. `Solve math problem: 7 + 4 = ?`).
- **Timeout**: Configurable timeout (default 120s). If the user fails to answer before the timeout expires, the bot automatically kicks them from the group.

---

## 📝 Notes & Auto-Responder Filters

### Notes System
Save frequently requested information (Wi-Fi passwords, server IPs, links) using `!save <name> <content>`.
- Members can query notes via `!get <name>`.
- **Auto-Trigger**: Simply typing `#<name>` (e.g. `#wifi` or `#rules`) in any message automatically triggers the bot to post the note content!

### Auto-Responder Filters
Set up keyword triggers using `!filter <trigger> <reply>`. Supports exact matches and regular expressions.

---

## 🧠 Gemini AI Capabilities

Configure a **Gemini API Key** in the Addon UI to unlock advanced AI capabilities:

1. **AI Group Assistant & FAQ**: Auto-replies to user questions in the group using a custom system persona prompt.
2. **AI Natural Language Rules Interpreter**: Typing `!rules <question>` lets Gemini analyze your group rules and answer the member's question intelligently.
3. **AI Sentiment & Toxicity Moderation**: Automatically scans incoming messages for hate speech, extreme insults, or harassment. Toxic messages are deleted instantly and a warning is logged.
4. **AI Translation Engine**: On-demand translation via `!translate` into any supported language.

---

## ⚡ Anti-Raid & Flood Protection

### Flood Protection (Anti-Spam Rate Limit)
Uses a sliding-window tracker per user (`groupId:userId`). If a user sends more than `max_messages` within `window_seconds` (e.g. 5 messages in 5 seconds), their extra messages are stopped and a penalty (Mute/Kick) is issued.

### Anti-Raid Shield
Tracks join velocity across the whole group (`max_joins` within `window_seconds`). If a botnet or raid attempt is detected (e.g. 10 joins in 10 seconds), the bot automatically puts the group in **Lockdown Mode**:
1. Sets group send permissions to **Announcement Mode** (only admins can send messages) via `session.sock.groupSettingUpdate(groupId, 'announcement')`.
2. Posts an urgent alert in the group.

---

## 🌐 Global Ban Federations

Cluster multiple WhatsApp groups into a shared **Ban Federation**:
- When a user is banned in one group of the federation, their ID is registered in the central federation ban list.
- If that user joins or posts in any other group linked to the same federation, they are **automatically banned immediately**!

---

## 💡 Acknowledgments & Inspiration

The Group Moderation Engine, Content Locks, Security Federations, and Group Commands features in this project were inspired by the conceptual architecture of **Miss Rose** and **[AegisBot](https://github.com/FaserF/AegisBot)**.

- **AegisBot Project**: [https://github.com/FaserF/AegisBot](https://github.com/FaserF/AegisBot)
