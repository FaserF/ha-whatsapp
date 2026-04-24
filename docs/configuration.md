---
layout: default
title: Configuration
nav_order: 3
---

# ⚙️ Configuration Guide

This guide explains every configuration option available in the WhatsApp Home Assistant App and the Home Assistant Integration.

---

## 🛠️ Integration Settings

_Location: Settings > Devices & Services > WhatsApp > Configure_

These settings control how the integration behaves within Home Assistant.

| Setting                 | Recommendation | Why use this?                                                                             |
| :---------------------- | :------------- | :---------------------------------------------------------------------------------------- |
| **Mark as Read**        | `Enabled`      | Automatically shows blue double-checks (✓✓) on your phone when HA receives a message.     |
| **Allow Self-Messages** | `Optional`     | Enables "Note to Self" mode. Also allows triggering HA events from your own messages in **Group Chats**. |
| **Polling Interval**    | `5 seconds`    | How fast HA checks for new messages. `5` is a good balance between speed and battery/CPU. |
| **Whitelist**           | `Empty`        | List specific numbers (comma separated) to only allow them to interact with your system.  |
| **Retry Attempts**      | `2`            | If a message fails (e.g. bad internet), HA tries again automatically.                     |
| **Mask Sensitive Data** | `Enabled`      | Partially hides phone numbers in HA logs (important if you share logs online).            |
| **Reset Session**       | `Disabled`     | **Danger!** Only use this if you want to completely log out and delete all local data.    |

---

## ⚙️ App Options

_Location: Add-ons > WhatsApp > Configuration_

These settings control the engine (the WhatsApp browser bridge).

- **Log Level**: Set to `info` for normal use. Use `debug` only if you encounter problems.
- **Media Folder**: Set to `/media/whatsapp` to permanently save incoming photos/videos. If left blank, files are deleted after 24h.
- **Mark Online**: If enabled, your WhatsApp status will show "Online" as long as the App is running.
- **UI Auth**: Optional password protection for the Web UI.
  - **Security Layer**: If `UI_Auth` is enabled, the App automatically bypasses the password check when accessed via **Home Assistant Ingress** (trusted).
  - **External Protection**: If `UI_Auth` is disabled, the App restricts access to private network ranges and Ingress only, blocking external (public) access by default for safety.

---

## 🔒 Security: Whitelist Feature

The Whitelist allows you to restrict interaction to specific users and groups.

- **How it works**: If set, only messages from whitelisted sources fire events. Outgoing messages to non-whitelisted targets are blocked.
- **Format**: Comma-separated phone numbers (`49123...`) or Group IDs (`123...@g.us`).
- **Empty**: No filtering (allows everyone).

---

## 📊 Monitoring Entities

Once configured, the integration provides several entities:

### Sensors

- **WhatsApp Connected**: A binary sensor showing if the bridge is "Online".
- **Messages Sent**: Tracks your automation volume.
- **Last Message**: Attributes show the content and target of the very last message sent.
- **Chats**: Displays the total number of available chats (direct and group chats). Its attributes include a `groups` list containing all available group names and their corresponding IDs, which is extremely useful for setting up automations.

### Repairs

If your session expires (e.g. you logged out on your phone), a **Repair Issue** will appear in the Home Assistant sidebar. Click **Fix** and follow the instructions to re-scan the QR code.

---

## 🌐 Network & Ports

- **Port 8066**: The App uses this port for its Web Interface and API.
- **Host Network**: Required for the App to be discovered automatically by the Integration.
