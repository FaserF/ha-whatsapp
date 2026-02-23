# 💬 Quoting & Replying

The WhatsApp integration supports quoting (replying to) specific messages. This is particularly useful in group chats to maintain context or for providing direct answers to user queries.

---

## 🔍 Obtaining Message IDs

To quote a message, you need its unique `message_id`. You can find this ID in:
- The **Attributes** of the `whatsapp_message_received` event.
- The **Return Value** of a successfully sent message (if calling the service via script).

---

## 🛠️ Usage Examples

### A. Using the `whatsapp.send_message` Service (Recommended)

In custom services, the `quote` parameter is used at the **top level** of the data block.

```yaml
alias: "Auto-Reply with Quote"
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "ping"
action:
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.sender }}"
      message: "pong 🏓"
      quote: "{{ trigger.event.data.id | default(trigger.event.data.raw.key.id) }}"
```

### B. Using the `notify.whatsapp` Service (Legacy)

In the classic notify service, quoting must be placed inside the `data` dictionary.

```yaml
alias: "Legacy Notify Reply"
sequence:
  - service: notify.whatsapp
    data:
      message: "This is a reply via legacy notify!"
      target: '49123456789'
      data:
        quote: "3EB0B8A7C2E4F6789ABCDE"
```

---

## 📋 Parameters

Both parameters are supported for compatibility. If both are provided, `quote` takes precedence.

| Parameter  | Description                                                         |
| :--------- | :------------------------------------------------------------------ |
| `quote`    | The unique ID of the message to reply to.                           |
| `reply_to` | Alias for `quote`. Used by many existing integrations and chatbots. |

---

> [!TIP]
> You can quote messages in almost all sending services, including `send_image`, `send_poll`, `send_buttons`, and `send_list`!
