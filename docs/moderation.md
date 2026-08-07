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
- **Description**: Displays a comprehensive status card for a target user (or yourself if no user is specified). Shows warning count, max limit, Captcha verification status, Whitelist approval status, mute status, and recent warning log timestamps.
- **Syntax**: `!info [@user]`
- **Example**:
  ```
  User: !info @491701234567
  Bot: 📋 User Info: John Doe
       🆔 ID: 491701234567
       ⚠️ Warnings: 2/3
       🤖 Captcha Verified: Yes
       ✅ Approved (Whitelist): No
       🔇 Muted: Yes
       
       Warning History:
       1. Excessive caps lock (05/08/2026, 10:15)
       2. Shared link without permission (05/08/2026, 11:30)
  ```

---

#### 6. `!adminlist` (Alias: `!admins`)
- **Description**: Fetches and lists all current administrators of the WhatsApp group, visually distinguishing the Group Owner/Creator (👑) from Group Admins (👮).
- **Syntax**: `!adminlist` or `!admins`

---

#### 7. `!approved`
- **Description**: Lists all whitelisted/approved users in the group *(MissRose Parity)*.
- **Syntax**: `!approved`

---

#### 8. `#notename`
- **Description**: Hashtag shortcut trigger to retrieve and display a saved note *(MissRose Parity)*.
- **Example**: `#wifi`, `#rules`

---

### 👮 Admin Commands Overview

The following admin commands are available to group administrators:

| Command | Arguments | Description |
|---|---|---|
| `!newfed` | `<name>` | Create a new ban federation *(MissRose parity)* |
| `!joinfed` | `<fed_id>` | Join group to a ban federation *(MissRose parity)* |
| `!leavefed` | - | Leave current ban federation *(MissRose parity)* |
| `!fban` | `[@user]` | Federation-ban user across all linked groups *(MissRose parity)* |
| `!unfban` | `<user_id>` | Remove federation ban from user *(MissRose parity)* |
| `!fedinfo` | `[fed_id]` | Show federation details *(MissRose parity)* |
| `!fbanlist` | - | List active federation bans *(MissRose parity)* |
| `!fedadmins` | - | List federation owner and admins *(MissRose parity)* |
| `!removespamlinks` | `<on\|off>` | Toggle automatic removal of `t.me` and `wa.me` invite links *(RemoveSpamLinkBot parity)* |
| `!pin` | `[loud]` | Pin message in group |
| `!unpin` | - | Unpin message in group |
| `!unpinall` | - | Unpin all messages in group |
| `!pinned` | - | Display current pinned message |
| `!blacklist` | `[word]` | List blacklisted words or add `<word>` to blacklist *(MissRose parity)* |
| `!rmblacklist` / `!unblacklist` | `<word>` | Remove word from group blacklist *(MissRose parity)* |
| `!setblacklistaction` | `<action>` | Set action on blacklist hit (`delete`, `warn`, `mute`, `kick`, `ban`) |
| `!setlog` | `<jid>` | Set moderation log channel *(MissRose parity)* |
| `!unsetlog` | - | Remove log channel |
| `!slowmode` | `<time\|off>` | Configure chat rate limit delay (e.g. `10s`, `1m`, `off`) |
| `!settitle` | `<title>` | Update group subject/title |
| `!setdescription` | `<text>` | Update group description |
| `!setphoto` | - | Update group photo/avatar |
| `!mode` | `<quiet\|normal>` | Set scanner notification mode: `quiet` vs `normal` *(DrWebBot parity)* |
| `!unapproveall` | - | Bulk clear all user approvals *(MissRose parity)* |
| `!reports` | `<on\|off>` | Toggle `/report` system for group members *(MissRose parity)* |


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
  - `{mention}` / `{user}` ➔ `@491701234567` (clickable mention)
  - `{name}` ➔ `491701234567` (phone number/name)
  - `{pushname}` ➔ WhatsApp profile name (if available)
  - `{group}` / `{subject}` / `{title}` ➔ Group Title
  - `{count}` / `{members}` ➔ Total group member count
  - `{rules}` ➔ Group rules text
  - `{date}` ➔ Current date (e.g. `06.08.2026`)
  - `{time}` ➔ Current time (e.g. `10:15`)
- **Syntax**: `!setwelcome <text>`
- **Example**: `!setwelcome Welcome {pushname} ({mention}) to {group}! You are member #{count}. Please read our rules: {rules}`

---

#### 28. `!welcome`
- **Description**: Displays the current welcome message template.
- **Syntax**: `!welcome`

---

#### 29. `!setgoodbye`
- **Description**: Sets the message sent when a member leaves or is removed from the group.
- **Placeholders**: `{mention}`, `{name}`, `{pushname}`, `{group}`, `{subject}`, `{title}`, `{count}`, `{members}`, `{rules}`, `{date}`, `{time}`.
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

#### 38. `!resetwarn` (Alias: `!rmwarn`)
- **Description**: Resets/clears all warnings for a specific user.
- **Syntax**: `!resetwarn [@user]` or `!rmwarn [@user]`

---

#### 39. `!setwarnlimit`
- **Description**: Sets the maximum warning threshold (1 to 20) before a penalty is executed.
- **Syntax**: `!setwarnlimit <count>`

---

#### 40. `!setwarnaction`
- **Description**: Sets the penalty action when warning limit is reached (`mute`, `kick`, `ban`).
- **Syntax**: `!setwarnaction <mute|kick|ban>`

---

#### 41. `!whitelist` / `!approve`
- **Description**: Adds a user to the group approved whitelist, bypassing moderation checks.
- **Syntax**: `!whitelist [@user]`

---

#### 42. `!unwhitelist` / `!unapprove`
- **Description**: Removes a user from the group approved whitelist.
- **Syntax**: `!unwhitelist [@user]`

---

#### 43. `!whitelisted`
- **Description**: Lists all whitelisted users in the group.
- **Syntax**: `!whitelisted`

---

#### 44. `!scan`
- **Description**: Triggers an AI security scan on the group or replied message.
- **Syntax**: `!scan`

---

#### 45. `!autotranslate`
- **Description**: Configures auto-translation settings for group messages.
- **Syntax**: `!autotranslate <on|off>`

---

#### 46. `!flood`
- **Description**: Configures rate-limit flood protection settings.
- **Syntax**: `!flood <max_messages> <window_seconds>`

---

#### 47. `!newfed`
- **Description**: Creates a new cross-group Ban Federation.
- **Syntax**: `!newfed <name>`

---

#### 48. `!joinfed`
- **Description**: Connects the current group to a Ban Federation.
- **Syntax**: `!joinfed <fed_id>`

---

#### 49. `!leavefed`
- **Description**: Disconnects the current group from its Ban Federation.
- **Syntax**: `!leavefed`

---

#### 50. `!fban`
- **Description**: Bans a user across all groups linked to the active Ban Federation.
- **Syntax**: `!fban [@user] [reason]`

---

#### 51. `!unfban`
- **Description**: Lifts a federation ban for a user.
- **Syntax**: `!unfban <user_id>`

---

#### 52. `!fedinfo`
- **Description**: Displays details, statistics, and owner of a Ban Federation.
- **Syntax**: `!fedinfo [fed_id]`

---

#### 53. `!fbanlist`
- **Description**: Lists all users currently banned in the federation.
- **Syntax**: `!fbanlist`

---

#### 54. `!fedadmins`
- **Description**: Lists administrators of the Ban Federation.
- **Syntax**: `!fedadmins`

---

#### 55. `!removespamlinks`
- **Description**: Toggles automatic deletion of invite links (`t.me`, `wa.me`, `signal`, etc.).
- **Syntax**: `!removespamlinks <on|off>`

---

#### 56. `!pin`
- **Description**: Pins a message in the WhatsApp group.
- **Syntax**: `!pin [loud]` (replying to a message)

---

#### 57. `!unpin`
- **Description**: Unpins the currently pinned message in the group.
- **Syntax**: `!unpin`

---

#### 58. `!unpinall`
- **Description**: Unpins all pinned messages in the group.
- **Syntax**: `!unpinall`

---

#### 59. `!pinned`
- **Description**: Shows the current pinned message in the group.
- **Syntax**: `!pinned`

---

#### 60. `!blacklist`
- **Description**: Views or adds a word/pattern to the group word blacklist.
- **Syntax**: `!blacklist [word]`

---

#### 61. `!rmblacklist` / `!unblacklist`
- **Description**: Removes a word from the group blacklist.
- **Syntax**: `!rmblacklist <word>`

---

#### 62. `!setblacklistaction`
- **Description**: Sets penalty action when a blacklisted word is posted (`delete`, `warn`, `mute`, `kick`, `ban`).
- **Syntax**: `!setblacklistaction <action>`

---

#### 63. `!setlog`
- **Description**: Sets a log channel for moderation events.
- **Syntax**: `!setlog <jid>`

---

#### 64. `!unsetlog`
- **Description**: Removes the configured log channel.
- **Syntax**: `!unsetlog`

---

#### 65. `!slowmode`
- **Description**: Sets chat rate limit delay between member messages.
- **Syntax**: `!slowmode <10s|1m|off>`

---

#### 66. `!settitle`
- **Description**: Updates the WhatsApp group title/subject.
- **Syntax**: `!settitle <new_title>`

---

#### 67. `!setdescription`
- **Description**: Updates the WhatsApp group description text.
- **Syntax**: `!setdescription <text>`

---

#### 68. `!setphoto`
- **Description**: Updates the group icon/avatar.
- **Syntax**: `!setphoto` (replying to an image)

---

#### 69. `!mode`
- **Description**: Configures bot notification mode (`quiet` vs `normal`).
- **Syntax**: `!mode <quiet|normal>`

---

#### 70. `!unapproveall`
- **Description**: Clears all whitelisted user approvals in the group.
- **Syntax**: `!unapproveall`

---

#### 71. `!reports`
- **Description**: Enables or disables member message reporting (`!report`).
- **Syntax**: `!reports <on|off>`

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
- `{mention}` / `{user}` ➔ Clickable mention using configured Name Priority
- `{name}` ➔ `491701234567` (User ID / Phone digits)
- `{pushname}` ➔ WhatsApp Profile Pushname
- `{group}` / `{subject}` / `{title}` ➔ Group Title
- `{count}` / `{members}` ➔ Member Count
- `{rules}` ➔ Group Rules text
- `{date}` ➔ Current Date (e.g. `06.08.2026`)
- `{time}` ➔ Current Time (e.g. `10:15`)

Farewell (Goodbye) messages automatically include the exact departure reason:
- 🚶 **Left voluntarily**
- ⏱️ **Captcha verification timed out**
- 🚫 **Banned** (with ban reason)
- 🌐 **Banned via Global Security Federation**
- ⚠️ **Removed after N warnings**
- 🔇 **Removed by an admin**

### User Addressing & Name Format Priority
Configure how members are mentioned in bot responses and greeting messages:
- **Name Priority Order**:
  1. `Contact Name > Pushname > Phone Number` (Default)
  2. `Pushname > Contact Name > Phone Number`
  3. `Phone Number Only` (+49...)
- **Fallback**: Select between `Phone Number` (+49...) or Generic (`@User`) when name information is missing.

### Captcha Verification & DM Resolution
Protect your group against automated spam accounts joining via invite links:
- **Challenge Modes**: Security Code (e.g. `M5UAY`), Math Problem (`7 + 4 = ?`), or Button Challenge (`pass`).
- **Delivery Target**: Group Chat or **Private Chat (DM)**.
- **Private DM Resolution**: When configured for Private Chat, challenges are sent via DM. Users can reply with the security code directly in their private chat with the bot. The bot verifies them instantly, cancels the kick timer, sends a confirmation DM, and posts a welcome notice in the group.
- **Captcha Dashboard**: Manage pending and verified users directly in the Web UI Dashboard with 1-click manual verification toggling.
- **Timeout**: Configurable timeout (30s–600s, default 120s). Users who fail to verify in time are automatically removed with a timeout notification.

### Custom Command Handler Modes
Create custom group commands (`!wifi`, `!faq`, `!socials`) with three execution types:
1. 🤖 **Auto Reply**: Bot sends an automated text response.
2. 🏠 **HA / Webhook**: No automated bot reply is sent; the event is forwarded to Home Assistant / Webhooks for custom automation handling. Still appears in `!help`.
3. 🔗 **Alias**: Redirects execution to execute another built-in or custom command target.


---

## 📝 Notes & Auto-Responder Filters

### Notes System
Save frequently requested information (Wi-Fi passwords, server IPs, links) using `!save <name> <content>`.
- Members can query notes via `!get <name>`.
- **Auto-Trigger**: Simply typing `#<name>` (e.g. `#wifi` or `#rules`) in any message automatically triggers the bot to post the note content!

### Auto-Responder Filters
Set up keyword triggers using `!filter <trigger> <reply>`. Supports exact matches and regular expressions.

---

## 🧠 Multi-AI Provider Capabilities (OpenAI & Gemini)

Configure an **OpenAI API Key** or **Gemini API Key** in the Addon UI to unlock advanced multi-model AI capabilities:

1. **Multi-Model Provider Support**: Select between OpenAI (e.g. `gpt-4o-mini`) and Gemini (e.g. `gemini-1.5-flash`) for auto-responses, intent scanning, and rules interpretation.
2. **AI Intent & Scam Detection**: Automatically scans long or suspicious messages for phishing, crypto-scams, or fraud intent. Malicious messages are deleted instantly.
3. **AI Group Assistant & FAQ**: Auto-replies to user questions in the group using a custom system persona prompt.
4. **AI Natural Language Rules Interpreter**: Typing `!rules <question>` lets AI analyze your group rules and answer the member's question intelligently.
5. **AI Sentiment & Toxicity Moderation**: Automatically scans incoming messages for hate speech, extreme insults, or harassment. Toxic messages are deleted instantly and a warning is logged.
6. **AI Translation Engine**: On-demand translation via `!translate` into any supported language.

---

## 📦 External Blocklists & Filter Subscriptions (GitHub Sync)

Import external YAML filter blocklists (compatible with **AegisBot** standard filter definitions):
- **GitHub Auto-Sync**: Automatically syncs raw YAML rule sets (e.g. `filters/default.yaml`) from GitHub repositories.
- **1-Click Import & Export**: Import and export complete group configurations as JSON.


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
- **⚡ Spam Link Guard Synergy**: When `!removespamlinks on` is active in a federated group, any member posting `t.me` or `wa.me` spam invite links is deleted AND automatically **Federation-Banned (`!fban`)** across all linked groups in the network!

---

## 💡 Acknowledgments & Inspiration

The Group Moderation Engine, Content Locks, Security Federations, and Group Commands features in this project were inspired by the conceptual architecture of **Miss Rose** and **[AegisBot](https://github.com/FaserF/AegisBot)**.

- **AegisBot Project**: [https://github.com/FaserF/AegisBot](https://github.com/FaserF/AegisBot)
