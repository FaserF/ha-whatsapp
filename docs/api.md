---
layout: default
title: REST API Reference
nav_order: 10
---

# 📜 REST API Technical Reference

The WhatsApp Addon bridge exposes a REST API for programmatic interaction. This document is the **authoritative source** for all available endpoints.

---

## 🔒 Security & Headers

All requests (except `/health`) **MUST** include:

- `X-Auth-Token`: Your security token (found in the Web UI).
- `Content-Type: application/json`

---

## 🚀 Messaging Endpoints

Every sending endpoint supports these **Global JSON Keys**:

- `number`: (String) Target JID (e.g., `49123...@s.whatsapp.net` or `12345...@g.us`).
- `quotedMessageId`: (String, Optional) Reply to a specific message ID.
- `expiration`: (Number, Optional) Auto-delete timer in seconds.

### `POST /send_message`

Basic text messaging.

- `message`: (String) The text content.

### `POST /send_image` / `send_video` / `send_document`

Media transmission.

- `url`: (String) Publicly accessible HTTPS URL.
- `caption` / `message`: (String, Optional) The accompanying text.
- `fileName`: (String, **Document Only**) Override the recipient's view.

### `POST /send_audio`

- `url`: (String) Link to audio.
- `ptt`: (Boolean) Set `true` for voice-note style.

### `POST /send_poll`

- `question`: (String)
- `options`: (Array of Strings) Max 12.
- `selectableCount`: (Integer, Optional) Use `1` for single-select polls or `0` for multi-choice polls.

### `POST /send_location`

- `latitude`: (Float)
- `longitude`: (Float)
- `title`: (String, Optional)
- `description`: (String, Optional)

### `POST /send_buttons`

- `message`: (String) Body text.
- `buttons`: (Array) Objects with `id` and `displayText`.
- `footer`: (String, Optional)

### `POST /send_list`

- `title`, `text`, `button_text`: (Strings)
- `sections`: (Array) Nested rows with `id`, `title`, `description`.

---

## 📝 Message Management

### `POST /edit_message`

- `message_id`: (String)
- `new_content`: (String)

### `POST /revoke_message`

- `message_id`: (String)

### `POST /send_reaction`

- `messageId`: (String) **Note case sensitivity.**
- `reaction`: (String) Emoji.

### `POST /mark_as_read`

- `messageId`: (String, Optional) If omitted, marks whole chat.

---

## ⚙️ Administration

### `POST /set_presence`

- `presence`: `composing`, `recording`, `paused`, `available`, `unavailable`.

### `POST /settings/webhook`

- `url`: Destination URL.
- `enabled`: (Boolean)
- `token`: (String, Optional) Secure validation header.

---

## 📊 Connection & Info

### `GET /status`

Returns: `{ "connected": bool, "version": string }`

### `GET /stats`

Returns internal traffic and error counters.

### `GET /qr`

Returns: `{ "status": "scanning", "qr": "data:image/png..." }`

### `GET /groups`

Returns an array of all participating Group objects.

### `GET /health`

Standard healthcheck. **No Token required.**
