---
layout: default
title: Supported Features
nav_order: 2
---

# ✅ Supported Features Overview

This table provides a quick overview of what is currently supported by the WhatsApp integration.

| Feature                   | Support | Notes                                                      |
| :------------------------ | :-----: | :--------------------------------------------------------- |
| **Messaging**             |         |                                                            |
| Send Text                 |   ✅    | Full support including formatting (_bold_, _italic_, etc.) |
| Receive Text              |   ✅    | Instant push events via Webhook                            |
| Mark messages as read     |   ✅    | mark all / specific messages as read via Integration       |
| Quoting                   |   ✅    | Reply to specific messages using their ID                  |
| Self-Messaging            |   ✅    | Process messages sent to yourself (Note to Self)           |
| **Media (Send)**          |         |                                                            |
| Images                    |   ✅    | Via URL                                                    |
| Audio                     |   ✅    | Send audio files or Voice Notes (PTT)                      |
| Video                     |   ✅    | Supports MP4 and other common formats                      |
| Documents                 |   ✅    | Send PDFs, CSVs, etc. with custom filenames                |
| **Media (Receive)**       |         |                                                            |
| Images                    |   ✅    | Received as URL (stored locally or in `media_folder`)      |
| Audio                     |   ✅    | Received as URL (stored locally or in `media_folder`)      |
| Video                     |   ✅    | Received as URL (stored locally or in `media_folder`)      |
| Documents                 |   ✅    | Received as URL (stored locally or in `media_folder`)      |
| Stickers                  |   ✅    | Received as URL (webp)                                     |
| **Interactive**           |         |                                                            |
| Polls                     |   ✅    | Create polls with multiple options                         |
| Lists                     |   ⚠️    | Interactive menus (Reliability varies by device/account)   |
| Buttons                   |   ⚠️    | Interactive buttons (Reliability varies by device/account) |
| Reactions                 |   ✅    | React to messages with emojis                              |
| **System**                |         |                                                            |
| Location                  |   ✅    | Send location pins with address                            |
| Contacts                  |   ✅    | Send VCards (Phone Contacts)                               |
| Presence                  |   ✅    | Set status to "typing...", "recording...", etc.            |
| Whitelist                 |   ✅    | Restrict outgoing messages to specific numbers             |
| Hass.io Discovery         |   ✅    | Auto-discovery of the local WhatsApp Addon                 |
| Multiple Instances        |   ✅    | Connect multiple WhatsApp accounts simultaneously          |
| **Diagnostics & Repairs** |         |                                                            |
| Connection Status Entity  |   ✅    | Real-time connection feedback                              |
| Uptime & Stats            |   ✅    | Monitor message throughput and system health               |
| Integration Repairs       |   ✅    | Guided troubleshooting and self-healing for common errors  |

## 🪄 HA-App Control Commands

The integration includes a built-in command system for authorized administrators. To use these commands, you must first configure your phone number(s) in the **Addon Configuration** under the `admin_numbers` field.

### Admin Setup

1. Go to the **WhatsApp Addon** -> **Configuration**.
2. Add your phone number to `admin_numbers` (multiple numbers can be comma-separated).
3. **Note**: Formats like `+49...`, `49...`, `0...`, or with spaces are automatically normalized.

### Available Commands

Simply send one of these commands to your bot:

| Command          | Description                                                          |
| :--------------- | :------------------------------------------------------------------- |
| `ha-app-status`  | **Public** status report (Anonymized & Rate-limited for non-admins). |
| `ha-app-help`    | Lists all available commands and examples (Admin only).              |
| `ha-app-logs`    | Retrieves the 10 most recent connection events (Admin only).         |
| `ha-app-restart` | Restarts the WhatsApp connection gracefully (Admin only).            |
| `ha-app-stats`   | View message statistics (Admin only).                                |

> **NOTE:**
> **Permissions & Rate Limits**:
>
> - `ha-app-status` can be used by anyone, but non-admins see masked Session IDs and are limited to **1 request per minute**.
> - If a non-admin user tries to send any other command, they will receive a one-time "Permission Denied" message. Subsequent attempts (except for status) will be silently ignored.

## ⚠️ A Note on Reliability

Interactive messages (Buttons and Lists) are increasingly restricted by Meta for unofficial WhatsApp APIs.

If you find that Buttons or Lists are not showing up on your device (especially on iOS), this is likely a server-side restriction by WhatsApp to encourage the use of the official Business API.

**Common symptoms:**

- Diagnostic tests show "OK" but no message arrives.
- Messages appear on WhatsApp Web/Desktop but not on the mobile app.
- Messages appear on Android but not on iOS.

**Recommendation:** If buttons/lists fail for you, stick to standard text messages or use the **Poll** feature, which tends to be much more reliable across all devices even in unofficial APIs.
