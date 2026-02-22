# Quoting Messages

The WhatsApp integration supports quoting (replying to) specific messages. This is particularly useful in group chats to maintain context.

## Usage

To quote a message, you need the `message_id` of the message you want to reply to. You can obtain this ID from the `whatsapp_message_received` event.

### Example Automation

```yaml
alias: "Auto-Reply with Quote"
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "ping"
action:
  - action: notify.whatsapp_contact_name
    data:
      message: "pong"
      quote: "{{ trigger.event.data.raw.key.id }}"
```

### Script Example

```yaml
alias: "Reply to specific message"
sequence:
  - action: notify.whatsapp_contact_name
    data:
      message: "This is a reply!"
      data:
        reply_to: "MESSAGE_ID_HERE"
```

## Parameters

You can use either `quote` or `reply_to` in the `data` dictionary. Both accept the `message_id` string.

- `quote`: The ID of the message to quote.
- `reply_to`: The ID of the message to quote (alias for `quote`).
