---
layout: default
title: Supported Features
nav_order: 2
---

# ✅ Supported Features Overview

This table provides a quick overview of what is currently supported by the WhatsApp integration.

| Feature                      | Support | Notes                                                       |
| :--------------------------- | :-----: | :---------------------------------------------------------- |
| **Messaging**                |         |                                                             |
| Send Text                    |   ✅    | Full support including formatting (_bold_, _italic_, etc.)  |
| Receive Text                 |   ✅    | Instant push events via Webhook                             |
| Mark messages as read        |   ✅    | mark all / specific messages as read                        |
| Quoting                      |   ✅    | Reply to specific messages using their ID                   |
| Self-Messaging               |   ✅    | Process messages sent to yourself (Note to Self)            |
| **Media (Send)**             |         |                                                             |
| Images                       |   ✅    | Via URL                                                     |
| Audio                        |   ✅    | Send audio files or Voice Notes (PTT)                       |
| Video                        |   ✅    | Supports MP4 and other common formats                       |
| Documents                    |   ✅    | Send PDFs, CSVs, etc. with custom filenames                 |
| **Media (Receive)**          |         |                                                             |
| Images                       |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Audio                        |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Video                        |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Documents                    |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Stickers                     |   ✅    | Received as URL (webp)                                      |
| **Interactive**              |         |                                                             |
| Polls                        |   ✅    | Create polls with multiple options                          |
| Lists                        |   ⚠️    | Interactive menus (Reliability varies by device/account)    |
| Buttons                      |   ⚠️    | Interactive buttons (Reliability varies by device/account)  |
| Reactions                    |   ✅    | React to messages with emojis                               |
| **System**                   |         |                                                             |
| Location                     |   ✅    | Send location pins with address                             |
| Contacts                     |   ✅    | Send VCards (Phone Contacts)                                |
| Presence                     |   ✅    | Set status to "typing...", "recording...", etc.             |
| Whitelist                    |   ✅    | Restrict outgoing messages to specific numbers              |
| Hass.io Discovery            |   ✅    | Auto-discovery of the local WhatsApp Addon                  |
| Multiple Instances           |   ✅    | Connect multiple WhatsApp accounts simultaneously           |
| **Diagnostics & Repairs**    |         |                                                             |
| Connection Status Entity     |   ✅    | Real-time connection feedback                               |
| Uptime & Stats               |   ✅    | Monitor message throughput and system health                |
| Integration Repairs          |   ✅    | Guided troubleshooting and self-healing for common errors   |

## 🪄 Magic Status Keyword

The integration includes a built-in auto-responder for quick status checks. Simply send the following message to your bot:

`ha-app-status`

The bot will instantly reply with a comprehensive status report, including:
- **Addon Version** & **Integration Version**
- **System Uptime**
- **Message Statistics** (Sent, Received, Failed)
- Quick links to Documentation and Issue Tracker

## ⚠️ A Note on Reliability

Interactive messages (Buttons and Lists) are increasingly restricted by Meta for unofficial WhatsApp APIs. 

If you find that Buttons or Lists are not showing up on your device (especially on iOS), this is likely a server-side restriction by WhatsApp to encourage the use of the official Business API.

**Common symptoms:**
- Diagnostic tests show "OK" but no message arrives.
- Messages appear on WhatsApp Web/Desktop but not on the mobile app.
- Messages appear on Android but not on iOS.

**Recommendation:** If buttons/lists fail for you, stick to standard text messages or use the **Poll** feature, which tends to be much more reliable across all devices even in unofficial APIs.
