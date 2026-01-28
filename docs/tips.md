---
layout: default
title: Tips, Tricks & Troubleshooting
nav_order: 5
---

# 💡 Pro-Tips, Tricks & Troubleshooting

Manage your integration like a pro and resolve common issues.

> **Tip:**
> **[🛡️ Whitelist Guide](WHITELIST.md)**: Secure your integration by restricting interaction to specific numbers and groups.

---

## 🆔 How to find Group Chat IDs?

Home Assistant doesn't list WhatsApp Group IDs in the UI. To find them:

1.  Open **Developer Tools** -> **Events**.
2.  In "Listen to events", type: `whatsapp_message_received`.
3.  Click **Start Listening**.
4.  Send a message into the WhatsApp group you want to identify.
5.  Check the event output. The `target` (or `raw.key.remoteJid`) will look like `123456789@g.us`.
6.  Use this ID (the suffix `@g.us` is optional in service calls) as your `target`.

---

## 🧪 Testing your Services

Use the **Developer Tools** -> **Services** tab to verify your configuration before building automations.

1.  Select `whatsapp.send_message` (or `notify.whatsapp`).
2.  Switch to **YAML Mode**.
3.  Paste one of the examples from the **[Service Docs](services.md)** (Ensure you use the correct recipient number).
4.  Click **Call Service**.

## 🛠️ Troubleshooting

### Message not sending?
- **Check Logs**: Go to the WhatsApp Addon logs. Search for "Connection closed" or "Unauthorized".
- **External URL**: If sending images, ensure the URL is correct and the addon can download the file.
- **Pairing**: Does the Addon Web UI show `Connected`? If not, re-scan the QR code.

### "Reset Session" - When to use it?
If you have persistent connection issues or want to pair with a different phone number:
1.  Go to the Addon **Configuration**.
2.  Set `reset_session` to `true`.
3.  **Save** and **Restart** the addon.
4.  The addon will delete all old session data and present a fresh QR code.
5.  The `reset_session` flag will automatically be set back to `false` once used.

### Unauthorized API Access
If you see 401 errors in the addon logs:
1.  Check the `api_token.txt` in your HA `/data` folder (internal to addon).
2.  Integration and Addon must use the same token. Usually, the integration handles this automatically via the Config Flow, but a re-installation of the integration might be needed if things are out of sync.

---

---

## 🔒 Privacy & Security

- **Local Processing**: All message processing happens on your own hardware.
- **No Cloud Storage**: This integration does not store your messages on any cloud server except for the official WhatsApp servers.
- **Tokens**: The API token is stored locally in your Home Assistant configuration. Never share your `/data` folder or the token with anyone.

---

## ❓ FAQ

**Q: Can I use multiple WhatsApp accounts?**
A: Currently, one addon instance supports one WhatsApp session. To use multiple, you would need to install the addon multiple times with different names (supported in future versions).

**Q: Do buttons work on all devices?**
A: Native buttons are part of the latest WhatsApp MD (Multi-Device) protocol. While most modern mobile apps support them, some older versions or the WhatsApp Desktop app might show them as text links.
