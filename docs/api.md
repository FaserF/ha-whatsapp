---
layout: default
title: REST API
nav_order: 10
---

# 📜 REST API Documentation

The WhatsApp Addon exposes a REST API that acts as a bridge between Home Assistant and the WhatsApp network. While the integration handles most things automatically, advanced users can interact with the API directly.

---

## 🔒 Authentication

All API requests (except `/health`) **MUST** include the `X-Auth-Token` header.

- The token is automatically generated on first run.
- You can view and copy the token from the **Addon Dashboard** (Web UI).

---

## 🚀 Endpoints

### 1️⃣ Connection Management

#### `POST /session/start`
Initiates a new session. If not connected, it starts the QR code generation process.

**Response:**
```json
{ "status": "starting", "message": "Session init started" }
```

#### `GET /status`
Returns the current connection status and library version.

**Response:**
```json
{
  "connected": true,
  "version": "1.0.4"
}
```

#### `GET /qr`
Returns the current QR code as a Data URL image string if scanning is required.

**Response:**
```json
{
  "status": "scanning",
  "qr": "data:image/png;base64,..."
}
```

#### `DELETE /session`
Logs out and deletes the current session data. Useful for resetting connection errors.

**Response:**
```json
{ "status": "success", "message": "Session deleted and logged out" }
```

---

### 2️⃣ Messaging

#### `POST /send_message`
Sends a basic text message.

**Payload:**
```json
{
  "number": "491234567890",
  "message": "Hello World"
}
```

#### `POST /send_image`
Sends an image from a public URL.

**Payload:**
```json
{
  "number": "491234567890",
  "url": "https://example.com/image.png",
  "caption": "Check this out!"
}
```

#### `POST /send_poll`
Sends an interactive poll.

**Payload:**
```json
{
  "number": "491234567890",
  "question": "Pizza or Burger?",
  "options": ["Pizza", "Burger", "Both"]
}
```

#### `POST /send_location`
Sends a location pin.

**Payload:**
```json
{
  "number": "491234567890",
  "latitude": 52.5200,
  "longitude": 13.4050,
  "name": "Berlin",
  "address": "Alexanderplatz"
}
```

#### `POST /send_reaction`
Reacts to a specific message using an emoji.

**Payload:**
```json
{
  "number": "491234567890",
  "reaction": "❤️",
  "messageId": "BAE5F..."
}
```

---

### 3️⃣ Interaction

#### `POST /set_presence`
Sets the chat presence/status for a specific contact.

**Payload:**
```json
{
  "number": "491234567890",
  "presence": "composing"
}
```
**Allowed Values:** `composing` (typing...), `recording` (recording audio...), `paused`, `available`.

---

### 4️⃣ System & Health

#### `GET /health`
Healthcheck endpoint for Docker/Supervisor. **No authentication required.**

**Response:**
```json
{ "status": "ok", "service": "whatsapp-addon" }
```

#### `GET /logs`
Returns the recent internal connection logs (same as shown in the Dashboard).

---

> [!TIP]
> **Base URL**: Most users will access the API at `http://YOUR_HA_IP:8066`.
> If using SSL/Ingress, use the appropriate internal proxy URL provided by Home Assistant.
