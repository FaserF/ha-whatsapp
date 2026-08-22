---
layout: default
title: Services & Features
nav_order: 3
---

# 📡 Services & Messaging Reference

This guide is the complete, 100% technical reference for all services provided by the WhatsApp integration.

All services can be called via `whatsapp.<service_name>`.

## Messaging

### `whatsapp.send_message`

Sends a plain text message to a WhatsApp user or group. This is the most basic messaging action. Use it for notifications, alerts, or any text-based communication from your automations. Supports emoji, line breaks (\n), and basic formatting (*bold*, _italic_).

```yaml
service: whatsapp.send_message
data:
  account: "49171234567"
  target: "49171234567"
  message: |
      🏠 *Home Assistant Alert*
      
      The front door was opened at {{ now().strftime('%H:%M') }}.
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.edit_message`

Edits the text content of a previously sent message. The message will show "(edited)" indicator. Useful for correcting typos or updating information in a sent message. Only works for text messages, not media.

```yaml
service: whatsapp.edit_message
data:
  account: "49171234567"
  target: "49171234567"
  message_id: "3EB0B8A7C2E4F6789ABCDE"
  message: "Updated: The meeting is now at 3 PM instead of 2 PM."
```

### `whatsapp.revoke_message`

Deletes a previously sent message for everyone in the chat. Works like "Delete for Everyone" in WhatsApp. The message is replaced with "This message was deleted". Must be called within the WhatsApp time limit (usually ~1 hour for groups, longer for individual chats).

```yaml
service: whatsapp.revoke_message
data:
  account: "49171234567"
  target: "49171234567"
  message_id: "3EB0B8A7C2E4F6789ABCDE"
```

### `whatsapp.send_reaction`

Adds an emoji reaction to a specific message. Just like tapping and holding a message in WhatsApp to react. Requires the message_id which you receive from webhook events or from the response of a send action.

```yaml
service: whatsapp.send_reaction
data:
  account: "49171234567"
  target: "49171234567"
  message_id: "3EB0B8A7C2E4F6789ABCDE"
  reaction: "👍"
```

### `whatsapp.forward_message`

Forwards an existing message to another chat target.

```yaml
service: whatsapp.forward_message
data:
  account: "..."
  target: "..."
  message_id: "..."
  destination: "..."
```

### `whatsapp.star_message`

Stars a specific message in a chat.

```yaml
service: whatsapp.star_message
data:
  account: "..."
  target: "..."
  message_id: "..."
```

### `whatsapp.unstar_message`

Unstars a specific message in a chat.

```yaml
service: whatsapp.unstar_message
data:
  account: "..."
  target: "..."
  message_id: "..."
```

### `whatsapp.pin_message`

Pins a message in a chat.

```yaml
service: whatsapp.pin_message
data:
  account: "..."
  target: "..."
  message_id: "..."
  duration: "..."
```

### `whatsapp.unpin_message`

Unpins a message in a chat.

```yaml
service: whatsapp.unpin_message
data:
  account: "..."
  target: "..."
  message_id: "..."
```


## Polls/Buttons

### `whatsapp.send_poll`

Sends an interactive poll/survey to a WhatsApp user or group. Recipients can vote on the options. Perfect for household decisions, dinner choices, or gathering feedback from family members. Note: Poll results are received via webhook events.

```yaml
service: whatsapp.send_poll
data:
  account: "49171234567"
  target: "49171234567"
  question: "What should we have for dinner tonight?"
  options: ['Pizza 🍕', 'Sushi 🍣', 'Pasta 🍝', 'Order something else']
  allow_multiple_responses: true
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.send_buttons`

Sends a message with interactive buttons that the recipient can tap. Note: WhatsApp/Meta has deprecated legacy interactive buttons on standard Multi-Device (Web) accounts, which may cause modern WhatsApp clients to display only text without clickable buttons. For reliable 1-click interactions, use 'whatsapp.send_poll' instead. See [Buttons Guide](https://faserf.github.io/ha-whatsapp/buttons) for details.

```yaml
service: whatsapp.send_buttons
data:
  account: "49171234567"
  target: "49171234567"
  message: |
      🚨 *Security Alert*
      
      Motion detected at the front door. What would you like to do?
  buttons: [{'id': 'arm_alarm', 'displayText': '🔒 Arm Alarm'}, {'id': 'view_camera', 'displayText': '📷 View Camera'}, {'id': 'ignore', 'displayText': '✓ Dismiss'}]
  footer: "Tap a button to respond"
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.send_list`

Sends an interactive list/menu that expands when the user taps a button. Contains sections with selectable rows. When a row is selected, its ID is sent back via webhook. Ideal for complex menus, settings selection, or multi-option responses.

```yaml
service: whatsapp.send_list
data:
  account: "49171234567"
  target: "49171234567"
  title: "🏠 Smart Home Control"
  text: "Select an action from the menu below to control your home."
  button_text: "Open Menu"
  sections: [{'title': 'Lighting', 'rows': [{'id': 'lights_on', 'title': '💡 All Lights On', 'description': 'Turn on all lights in the house'}, {'id': 'lights_off', 'title': '🌙 All Lights Off', 'description': 'Turn off all lights'}]}, {'title': 'Climate', 'rows': [{'id': 'heating_boost', 'title': '🔥 Heating Boost', 'description': 'Boost heating for 1 hour'}, {'id': 'ac_on', 'title': '❄️ AC On', 'description': 'Turn on air conditioning'}]}]
```


## Media & Location

### `whatsapp.send_image`

Sends an image with an optional caption to a WhatsApp user or group. The image must be accessible via a public URL (HTTPS recommended). Ideal for sending camera snapshots, graphs, or notifications with visuals. Supported formats: JPEG, PNG, WebP. Max size: 16MB.

```yaml
service: whatsapp.send_image
data:
  account: "49171234567"
  target: "49171234567"
  url: "https://my-home.duckdns.org/local/camera_snapshots/front_door.jpg"
  caption: "📷 Front door camera snapshot at {{ now().strftime('%H:%M:%S') }}"
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.send_document`

Sends a document/file to a WhatsApp user or group. Supports PDF, Word, Excel, ZIP, and many other file types. Perfect for sending reports, invoices, backups, or log files. The file must be accessible via a public URL. Max size: 100MB.

```yaml
service: whatsapp.send_document
data:
  account: "49171234567"
  target: "49171234567"
  url: "https://my-home.duckdns.org/local/reports/energy_report.pdf"
  file_name: "Energy_Report_January_2024.pdf"
  mimetype: "audio/mpeg"
  message: "📊 Here's your monthly energy consumption report."
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.send_video`

Sends a video file to a WhatsApp user or group. Useful for sending security camera clips, doorbell recordings, or any video content. Supported formats: MP4, 3GP, MOV. Max size: 16MB for standard, 64MB for WhatsApp Web.

```yaml
service: whatsapp.send_video
data:
  account: "49171234567"
  target: "49171234567"
  url: "https://my-home.duckdns.org/local/clips/doorbell_motion.mp4"
  message: "🚪 Motion detected at front door - {{ now().strftime('%H:%M') }}"
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
  seconds: 33
```

### `whatsapp.send_audio`

Sends an audio file or voice note to a WhatsApp user or group. Can send as a regular audio file (shows as playable file) or as a voice note/PTT (shows with waveform, like a recorded message). Supported formats: MP3, OGG, WAV, AAC. Max size: 16MB.

```yaml
service: whatsapp.send_audio
data:
  account: "49171234567"
  target: "49171234567"
  url: "https://my-home.duckdns.org/local/audio/doorbell_chime.mp3"
  ptt: true
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
  seconds: 33
```

### `whatsapp.send_location`

Sends a location pin to a WhatsApp user or group. The recipient sees an interactive map preview they can tap to open in their maps app. Perfect for sharing addresses, meeting points, or your home location for deliveries.

```yaml
service: whatsapp.send_location
data:
  account: "49171234567"
  target: "49171234567"
  latitude: 48.137154
  longitude: 11.576124
  name: "Home"
  address: "Marienplatz 1, 80331 München, Germany"
  quote: "3EB0B8A7C2E4F6789ABCDE"
  reply_to: "3EB0B8A7C2E4F6789ABCDE"
  expiration: 86400
```

### `whatsapp.send_contact`

Sends a contact card (vCard) to a WhatsApp user or group. The recipient can save the contact directly to their phone. Useful for sharing business contacts, emergency numbers, or service provider details.

```yaml
service: whatsapp.send_contact
data:
  account: "49171234567"
  target: "49171234567"
  name: "Dr. Max Mustermann"
  contact_number: "+49 89 12345678"
```

### `whatsapp.send_event`

Sends an interactive WhatsApp Group Event message to a chat or group. Group members can RSVP directly inside WhatsApp.

```yaml
service: whatsapp.send_event
data:
  account: "49171234567"
  target: "123456789@g.us"
  name: "Squash - Tuesday evening"
  description: "Court 1 booked from 20:00 to 21:00"
  date: "2026-07-22T20:00:00"
  location: "SquashCity Amsterdam"
  join_link: "https://call.whatsapp.com/video/example"
  is_canceled: false
  expiration: 86400
```


## Status/Stories

### `whatsapp.send_status`

Posts a text or image/media status (story) to status@broadcast.

```yaml
service: whatsapp.send_status
data:
  account: "..."
  message: "..."
  url: "..."
  caption: "..."
```


## Group Management

### `whatsapp.create_group`

Creates a new WhatsApp group with subject and initial participants.

```yaml
service: whatsapp.create_group
data:
  account: "..."
  subject: "..."
  participants: "..."
```

### `whatsapp.add_group_participant`

Adds participants to an existing WhatsApp group.

```yaml
service: whatsapp.add_group_participant
data:
  account: "..."
  target: "..."
  participants: "..."
```

### `whatsapp.remove_group_participant`

Removes participants from a WhatsApp group.

```yaml
service: whatsapp.remove_group_participant
data:
  account: "..."
  target: "..."
  participants: "..."
```

### `whatsapp.promote_group_participant`

Promotes participants to group admin.

```yaml
service: whatsapp.promote_group_participant
data:
  account: "..."
  target: "..."
  participants: "..."
```

### `whatsapp.demote_group_participant`

Demotes group admins to regular participants.

```yaml
service: whatsapp.demote_group_participant
data:
  account: "..."
  target: "..."
  participants: "..."
```

### `whatsapp.leave_group`

Leaves a WhatsApp group.

```yaml
service: whatsapp.leave_group
data:
  account: "..."
  target: "..."
```

### `whatsapp.update_group_subject`

Changes the title / subject of a WhatsApp group.

```yaml
service: whatsapp.update_group_subject
data:
  account: "..."
  target: "..."
  subject: "..."
```

### `whatsapp.update_group_description`

Changes the description of a WhatsApp group.

```yaml
service: whatsapp.update_group_description
data:
  account: "..."
  target: "..."
  description: "..."
```

### `whatsapp.update_group_settings`

Configures group announcement mode and info restriction mode.

```yaml
service: whatsapp.update_group_settings
data:
  account: "..."
  target: "..."
  announce: "..."
  locked: "..."
```

### `whatsapp.join_group`

Joins a group using an invite link or code.

```yaml
service: whatsapp.join_group
data:
  account: "..."
  code: "..."
```

### `whatsapp.search_groups`

Finds WhatsApp Group IDs by searching for group names.
⚠️ IMPORTANT: Results appear as a PERSISTENT NOTIFICATION in Home Assistant! After running this service, click the bell icon (🔔) in the sidebar to see results.
The notification shows a table with Group Name, Group ID, and participant count. Copy the Group ID (format: 120363012345678901@g.us) to use in other services.

```yaml
service: whatsapp.search_groups
data:
  account: "49171234567"
  name_filter: "Family"
```


## Chat Management

### `whatsapp.mark_as_read`

Marks messages as read in a chat (blue double-check ✓✓). Works for both individual chats AND group chats.
• With message_id: Marks that specific message as read • Without message_id: Marks ALL unread messages in the chat as read

```yaml
service: whatsapp.mark_as_read
data:
  account: "49171234567"
  target: "49171234567"
  message_id: "3EB0B8A7C2E4F6789ABCDE"
```

### `whatsapp.mark_as_unread`

Marks a specific chat as unread. Works for both individual chats AND group chats.

```yaml
service: whatsapp.mark_as_unread
data:
  account: "49171234567"
  target: "49171234567"
```

### `whatsapp.archive_chat`

Archives a chat.

```yaml
service: whatsapp.archive_chat
data:
  account: "..."
  target: "..."
```

### `whatsapp.unarchive_chat`

Unarchives a chat.

```yaml
service: whatsapp.unarchive_chat
data:
  account: "..."
  target: "..."
```

### `whatsapp.mute_chat`

Mutes notifications for a chat.

```yaml
service: whatsapp.mute_chat
data:
  account: "..."
  target: "..."
  duration_ms: "..."
```

### `whatsapp.unmute_chat`

Unmutes notifications for a chat.

```yaml
service: whatsapp.unmute_chat
data:
  account: "..."
  target: "..."
```

### `whatsapp.clear_chat`

Clears all messages in a chat history.

```yaml
service: whatsapp.clear_chat
data:
  account: "..."
  target: "..."
```

### `whatsapp.delete_chat`

Deletes a chat from WhatsApp.

```yaml
service: whatsapp.delete_chat
data:
  account: "..."
  target: "..."
```

### `whatsapp.get_chat_messages`

Fetches recent stored messages for a chat.

```yaml
service: whatsapp.get_chat_messages
data:
  account: "..."
  target: "..."
  limit: "..."
```


## Contacts & Profile

### `whatsapp.get_contacts`

Retrieves the list of contacts cached from your paired phone. Returns response data with contact details (id/JID, name from phonebook, notify/pushName, verified_name). Note: 'notify' is populated when contacts send a message, 'verified_name' is for Business accounts only.

```yaml
service: whatsapp.get_contacts
data:
  account: "49171234567"
```

### `whatsapp.check_number`

Checks if a phone number exists on WhatsApp and whether it is saved in your paired phone's contacts. Returns response data with 'exists', 'in_contacts', 'name', 'notify', and 'jid'.

```yaml
service: whatsapp.check_number
data:
  account: "49171234567"
  number: "49171234567"
```

### `whatsapp.get_profile_picture`

Fetches profile picture / avatar URL of contact or group.

```yaml
service: whatsapp.get_profile_picture
data:
  account: "..."
  target: "..."
```

### `whatsapp.get_contact_info`

Fetches contact status/about message.

```yaml
service: whatsapp.get_contact_info
data:
  account: "..."
  target: "..."
```

### `whatsapp.block_contact`

Blocks a contact number.

```yaml
service: whatsapp.block_contact
data:
  account: "..."
  target: "..."
```

### `whatsapp.unblock_contact`

Unblocks a contact number.

```yaml
service: whatsapp.unblock_contact
data:
  account: "..."
  target: "..."
```

### `whatsapp.update_presence`

Updates your online presence status in a specific chat. Shows typing indicator, recording indicator, or online/offline status. Use "composing" before sending a message to show "typing...", or "recording" to show "recording audio...".

```yaml
service: whatsapp.update_presence
data:
  account: "49171234567"
  target: "49171234567"
  presence: "composing"
```


## Channel/Newsletter

### `whatsapp.get_channel_info`

Fetches metadata for a WhatsApp Channel (Newsletter) via JID or invite code.

```yaml
service: whatsapp.get_channel_info
data:
  account: "..."
  target: "..."
  code: "..."
```

### `whatsapp.follow_channel`

Follows a WhatsApp Channel (Newsletter).

```yaml
service: whatsapp.follow_channel
data:
  account: "..."
  target: "..."
```

### `whatsapp.unfollow_channel`

Unfollows a WhatsApp Channel (Newsletter).

```yaml
service: whatsapp.unfollow_channel
data:
  account: "..."
  target: "..."
```

### `whatsapp.mute_channel`

Mutes notifications for a WhatsApp Channel.

```yaml
service: whatsapp.mute_channel
data:
  account: "..."
  target: "..."
```

### `whatsapp.unmute_channel`

Unmutes notifications for a WhatsApp Channel.

```yaml
service: whatsapp.unmute_channel
data:
  account: "..."
  target: "..."
```


## Business Labels

### `whatsapp.add_chat_label`

Adds a WhatsApp Business label to a chat.

```yaml
service: whatsapp.add_chat_label
data:
  account: "..."
  target: "..."
  label_id: "..."
```

### `whatsapp.remove_chat_label`

Removes a WhatsApp Business label from a chat.

```yaml
service: whatsapp.remove_chat_label
data:
  account: "..."
  target: "..."
  label_id: "..."
```


## Moderation

### `whatsapp.enable_moderation`

Enables group moderation engine for a target WhatsApp group.

```yaml
service: whatsapp.enable_moderation
data:
  account: "..."
  target: "..."
```

### `whatsapp.disable_moderation`

Disables group moderation engine for a target WhatsApp group.

```yaml
service: whatsapp.disable_moderation
data:
  account: "..."
  target: "..."
```

### `whatsapp.warn_user`

Issues a warning to a group user and enforces penalty upon reaching maximum warnings.

```yaml
service: whatsapp.warn_user
data:
  account: "..."
  target: "..."
  user_id: "..."
  reason: "..."
```

### `whatsapp.clear_warnings`

Clears all active warnings for a group member.

```yaml
service: whatsapp.clear_warnings
data:
  account: "..."
  target: "..."
  user_id: "..."
```

### `whatsapp.import_moderation_config`

Imports JSON moderation configuration for a group.

```yaml
service: whatsapp.import_moderation_config
data:
  account: "..."
  target: "..."
  config: "..."
```


## Telegram Bridge

### `whatsapp.configure_telegram_bot`

Configures or updates Telegram Bot token and active state for the native bridge.

```yaml
service: whatsapp.configure_telegram_bot
data:
  account: "..."
  bot_token: "..."
  enabled: "..."
```

### `whatsapp.add_telegram_mapping`

Creates or updates a chat bridging mapping between WhatsApp and Telegram.

```yaml
service: whatsapp.add_telegram_mapping
data:
  account: "..."
  bot_id: "..."
  mapping_name: "..."
  wa_jid: "..."
  tg_chat_id: "..."
  sync_mode: "..."
  sync_self_messages: "..."
  tg_thread_id: "..."
  convert_formatting: "..."
  anonymize_phone_numbers: "..."
  ignore_command_prefixes: "..."
  is_direct_chat_mirror: "..."
```

### `whatsapp.remove_telegram_mapping`

Deletes an existing Telegram chat mapping by ID.

```yaml
service: whatsapp.remove_telegram_mapping
data:
  account: "..."
  mapping_id: "..."
```


## Auto Responder

### `whatsapp.set_auto_responder`

Configures and activates/deactivates the automated away / vacation auto-responder.

```yaml
service: whatsapp.set_auto_responder
data:
  account: "49171234567"
  enabled: true
  start_time: "2026-08-20T08:00"
  end_time: "2026-08-30T18:00"
  direct_only: true
  once_per_contact: true
  message_template: "Hello {sender_name}!\n\nI am on vacation{end_time_text}.\n{once_notice}"
```

### `whatsapp.reset_auto_responder_seen`

Clears the cache of contacts who have already received an automated response during the active period.

```yaml
service: whatsapp.reset_auto_responder_seen
data:
  account: "49171234567"
```


## Other

### `whatsapp.configure_webhook`

Configures the webhook URL where the WhatsApp Home Assistant App sends incoming message events. This is how Home Assistant receives incoming messages, button clicks, poll votes, and read receipts. Usually set during initial configuration, but can be updated dynamically.

```yaml
service: whatsapp.configure_webhook
data:
  account: "49171234567"
  url: "https://my-home.duckdns.org/api/webhook/whatsapp_incoming"
  enabled: true
  token: "my_secret_token_12345"
```
