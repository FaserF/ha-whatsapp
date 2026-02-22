---
layout: default
title: Configuration
nav_order: 3
---

# ⚙️ App Configuration

The WhatsApp Home Assistant App can be configured via the **Configuration** tab in the Home Assistant App store.

## Options

| Option                 | Type    | Default           | Description                                                                                                                                                                                                                                                   |
| :--------------------- | :------ | :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `log_level`            | string  | `info`            | Controls the verbosity of the logs (`trace`, `debug`, `info`, `warning`, `error`, `fatal`).                                                                                                                                                                   |
| `media_folder`         | string  | `/media/whatsapp` | **(New)** Path to a public folder to save received media (Images, Videos, Voice, Documents). <br>If set, files will **NOT** be automatically deleted (App cleanup disabled). <br>If cleared (set to null), files are stored internally and deleted after 24h. |
| `send_message_timeout` | int     | `25000`           | Time in milliseconds to wait for a WhatsApp acknowledgement before timing out.                                                                                                                                                                                |
| `keep_alive_interval`  | int     | `30000`           | How often (in ms) to check the connection to detect stale connections.                                                                                                                                                                                        |
| `mask_sensitive_data`  | boolean | `false`           | If enabled, phone numbers in logs will be partially hidden (e.g. `4917*****123`).                                                                                                                                                                             |
| `mark_online`          | boolean | `false`           | If true, marks your account as "Online" while the App is running.                                                                                                                                                                                             |
| `ui_auth_enabled`      | boolean | `false`           | Enables Basic Authentication for the Web UI (Port 8066). Recommended if exposed to the internet.                                                                                                                                                              |
| `ui_auth_password`     | string  | -                 | The password for the Web UI (Username is always `admin`).                                                                                                                                                                                                     |

---

## 🛠️ Integration Options

These options are configured within Home Assistant via the **Configure** button on the WhatsApp integration card (**Settings > Devices & Services**).

| Option                 | Type    | Default | Description                                                                                                                                         |
| :--------------------- | :------ | :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Mark as Read`         | boolean | `true`  | Automatically mark incoming messages as read on WhatsApp.                                                                                           |
| `Allow Self-Messages`  | boolean | `false` | **(New)** If enabled, messages you send to yourself will trigger events. This allows you to trigger automations via "Note to Self".              |
| `Polling Interval`     | int     | `5`     | Seconds between event checks.                                                                                                                       |
| `Whitelist`            | string  | -       | Comma-separated list of allowed Numbers/Group IDs. If empty, all incoming messages are processed.                                                   |
| `Mask Sensitive Data`  | boolean | `false` | Masks phone numbers in Home Assistant logs.                                                                                                         |
| `Retry Attempts`       | int     | `2`     | How many times to retry sending a message on failure.                                                                                              |
| `Debug Payload`        | boolean | `false` | Logs the full outgoing JSON payload for troubleshooting.                                                                                            |
| `Reset Session`        | boolean | `false` | **(Caution)** Logging this instance out and deleting all Local Data from the Addon. Requires re-pairing.                                            |

### Detailed: Allow Self-Messages

By default, WhatsApp considers messages sent to yourself as "outgoing" (`fromMe: true`). Most bots ignore these to prevent loops. However, if you don't have a second phone number, you can use your own "Note to Self" chat to send commands to Home Assistant.

> [!IMPORTANT]
> When enabled, ensure your automations don't cause an infinite loop (e.g., an automation that reacts to any message by sending a message to yourself).

## Webhook Configuration

Forward incoming messages to an external URL.

| Option            | Type    | Description                                                        |
| :---------------- | :------ | :----------------------------------------------------------------- |
| `webhook_enabled` | boolean | Enable/Disable webhook forwarding.                                 |
| `webhook_url`     | string  | The destination URL (e.g., `https://my-backend.com/api/whatsapp`). |
| `webhook_token`   | string  | A secret token sent in the `X-Webhook-Token` header.               |

## Network

- **Host Network**: Enabled by default to allow auto-discovery.
- **Port 8066**: Used for the API and Web UI.
