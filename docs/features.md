---
layout: default
title: Supported Features
nav_order: 2
---

# ✅ Supported Features Overview

This table provides a quick overview of what is currently supported by the WhatsApp integration.

| Feature               | Support | Notes                                                       |
| :-------------------- | :-----: | :---------------------------------------------------------- |
| **Messaging**         |         |                                                             |
| Send Text             |   ✅    | Full support including formatting (_bold_, _italic_, etc.)  |
| Receive Text          |   ✅    | Instant push events via Webhook                             |
| Mark messages as read |   ✅    | mark all / specific messages as read                        |
| **Media (Send)**      |         |                                                             |
| Images                |   ✅    | Via URL                                                     |
| Audio                 |   ✅    | Send audio files or Voice Notes (PTT)                       |
| Video                 |   ✅    | Supports MP4 and other common formats                       |
| Documents             |   ✅    | Send PDFs, CSVs, etc. with custom filenames                 |
| **Media (Receive)**   |         |                                                             |
| Images                |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Audio                 |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Video                 |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Documents             |   ✅    | Received as URL (stored locally or in `media_folder`)       |
| Stickers              |   ✅    | Received as URL (webp)                                      |
| **Interactive**       |         |                                                             |
| Polls                 |   ✅    | Create polls with multiple options                          |
| Lists                 |   ✅    | Interactive menus with sections and rows                    |
| Buttons               |   ✅    | Interactive buttons (iOS limitations apply, List preferred) |
| Reactions             |   ✅    | React to messages with emojis                               |
| **System**            |         |                                                             |
| Location              |   ✅    | Send location pins with address                             |
| Contacts              |   ✅    | Send VCards (Phone Contacts)                                |
| Presence              |   ✅    | Set status to "typing...", "recording...", etc.             |
| Whitelist             |   ✅    | Restrict outgoing messages to specific numbers              |
