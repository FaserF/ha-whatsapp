# 🔘 Buttons & Interactive Messages

Buttons allow you to create interactive experiences for your users. Instead of typing a response, users can simply tap a button to trigger an action in Home Assistant.

---

## 🛠️ Usage Example

You can send buttons using the `whatsapp.send_buttons` service.

```yaml
service: whatsapp.send_buttons
data:
  target: '+49123456789'
  message: 'Do you want to turn off the lights?'
  buttons:
    - id: 'lights_off_yes'
      displayText: 'Yes, please! 💡'
    - id: 'lights_off_no'
      displayText: 'No, leave them on.'
  footer: 'Smart Home Assistant'
```

### 🤖 Handling the Response

When a user taps a button, a `whatsapp_message_received` event is fired.

```yaml
alias: 'Handle Button Press'
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: 'Yes, please! 💡' # The displayText is sent as text content
action:
  - service: light.turn_off
    target:
      entity_id: all
```

> **TIP:**
> You can also check for `trigger.event.data.id` (or `trigger.event.data.raw.key.id` depending on bridge) to match the internal button ID precisely.

---

## ⚠️ Limitations & Potential Problems

While buttons are powerful, there are several technical hurdles to be aware of:

### 1. The 3-Button Limit

WhatsApp strictly limits interactive messages to a **maximum of 3 buttons**. If you need more options, consider using the [List Menu (send_list)](api.md#post-send_list), which supports up to 10 rows per section.

### 2. Standard vs. Business Accounts

WhatsApp's treatment of buttons depends on the account type:

| Feature           | Standard Account                     | Business Account (Official API) |
| :---------------- | :----------------------------------- | :------------------------------ |
| **Reliability**   | Medium (Experimental)                | Very High                       |
| **Stability**     | Buttons may disappear After 24h      | Persistent                      |
| **Display**       | May show as plain text on older apps | Full UI support                 |
| **Quick Replies** | Emulated via bridge                  | Native feature                  |

**Standard Accounts** (like the one used by this integration) use the "Linked Device" protocol. Since WhatsApp officially only supports buttons for Business APIs, the bridge has to "emulate" these. This can lead to buttons not appearing on some versions of the WhatsApp App (especially older Android versions).

### 3. Client Version Issues

If the recipient is using a very old version of WhatsApp, interactive messages might show up as:
`This message is not supported by your version of WhatsApp.`
Ensure both your bot account and the recipients have updated apps.

### 4. Group Limitations

In some regions, buttons in groups are restricted for non-business accounts to prevent spam.

---

## 🏗️ Telegram Compatibility (inline_keyboard)

For users migrating from Telegram, the `notify.whatsapp` service supports the `inline_keyboard` format and automatically normalizes it for WhatsApp:

```yaml
service: notify.whatsapp
data:
  message: 'Arm System?'
  data:
    inline_keyboard:
      - - text: 'Arm Away'
          callback_data: 'arm_away'
        - text: 'Arm Home'
          callback_data: 'arm_home'
```

_The integration will automatically pick up the first 3 buttons and map `text` to `displayText` and `callback_data` to `id`._
