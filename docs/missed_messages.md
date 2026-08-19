---
title: Missed Messages
description: How the WhatsApp Integration handles messages received while the addon was offline.
---

# Missed Messages

When the WhatsApp addon restarts (e.g. after an update or Home Assistant reboot), messages that arrived during the downtime are automatically replayed if they fall within the configured lookback window.

## How It Works

1. **Disconnect time is recorded** to disk the moment the WhatsApp connection drops.
2. On reconnect, Baileys delivers queued messages via the normal `messages.upsert` event.
3. Each arriving message is evaluated:
   - If its timestamp falls **within the lookback window** → it is processed normally (commands, moderation, Telegram bridge, etc.).
   - If its timestamp is **older than the lookback window** → it is skipped. An optional one-time notification can be sent to the chat.
4. The evaluation window closes **60 seconds after reconnect** so normal real-time messages are never affected.

## Configuration

The feature is configured globally via the addon moderation store (`moderation_config.json`):

```json
{
  "missed_messages": {
    "enabled": true,
    "lookback_hours": 3,
    "notify_skipped": false
  }
}
```

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `true` | Enable/disable missed message processing |
| `lookback_hours` | number | `3` | How far back (in hours) to replay messages |
| `notify_skipped` | boolean | `false` | Send a one-time per-chat notification for skipped messages |

## Notification Behavior

When `notify_skipped: true`, the bot sends **one notification per chat per restart** if messages could not be processed (either too old or the feature is disabled).

Example (English):

> ⚠️ While the WhatsApp gateway was offline, your message could not be processed. It is too old to be retried automatically.

The message is fully localized; German translation is included out of the box.

## Limitations

- Only messages Baileys delivers during the 60-second reconnect window are evaluated. WhatsApp does not expose a server-side history API, so messages from very long outages may not arrive at all.
- Media messages that arrived while offline may lack downloadable URLs.
- `fromMe` messages and protocol messages (edits, deletions, pins) are never replayed.
