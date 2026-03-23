---
layout: default
title: Services & Features
nav_order: 3
---

# 🚀 Services & Messaging Reference

This guide is the complete, 100% technical reference for all services provided by the WhatsApp integration.

---

## 🏗️ Core Communication

### `whatsapp.send_message`

Sends a plain text message.

| Field        | Type   | Description                                        |
| :----------- | :----- | :------------------------------------------------- |
| `target`     | string | **(Required)** Recipient phone or Group ID.        |
| `message`    | string | **(Required)** Text content (supports formatting). |
| `quote`      | string | Message ID to reply to.                            |
| `expiration` | number | Disappearing message timer (secs).                 |

### `whatsapp.edit_message` / `revoke_message`

- **edit_message**: Change the text of a sent message (`target`, `message_id`, `message`).
- **revoke_message**: "Delete for everyone" (`target`, `message_id`).

---

## 🖼️ Media & Files

All media services require a **target** and a **url**.

| Service           | Unique Fields          | Description                   |
| :---------------- | :--------------------- | :---------------------------- |
| **send_image**    | `caption`              | JPEG, PNG, WebP (Max 16MB).   |
| **send_video**    | `message` (caption)    | MP4, MOV (Max 16-64MB).       |
| **send_audio**    | `ptt` (boolean)        | `true` sends as a Voice Note. |
| **send_document** | `file_name`, `message` | Any file type (Max 100MB).    |

---

## 📊 Interactive & Advanced

### `whatsapp.send_poll`

- **question**: The voting topic.
- **options**: List of strings (Max 12).

### `whatsapp.send_buttons`

- **message**: Body text.
- **buttons**: List of `id` and `displayText` (Max 3).
- **footer**: Optional small text.

### `whatsapp.send_list`

- **title**, **text**, **button_text**.
- **sections**: Nested rows with `id`, `title`, and `description`.

### `whatsapp.send_location`

- **latitude**, **longitude**: **(Required)** coordinates.
- **name**, **address**: Optional labels for the map pin.

### `whatsapp.send_contact`

- **name**: Display name.
- **contact_number**: Phone number for the vCard.

---

## ⚙️ Administration

### `whatsapp.update_presence`

Updates your status. Options: `available`, `unavailable`, `composing` (typing), `recording`, `paused`.

### `whatsapp.search_groups`

Finds Group IDs. Results appear in **HA Notifications (🔔)**.

### `whatsapp.mark_as_read`

Mark specific `message_id` or whole `target` chat as read.

### `whatsapp.configure_webhook`

`url`, `enabled`, and optional security `token`.

---

## 🌍 Global Service Parameters

These are available for almost **every** sending service:

- **target**: Recipient destination.
- **account**: Instance selector (if multiple).
- **quote**: Reply-to ID (also accepts alias `reply_to`).
- **expiration**: Auto-delete timer.
