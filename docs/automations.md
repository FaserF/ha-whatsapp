---
layout: default
title: Advanced Automations
nav_order: 4
---

# 🤖 Advanced Automations

The real power of the WhatsApp integration lies in the events. Every message received by the App is fired into Home Assistant as a `whatsapp_message_received` event.

---

## 📨 Building a WhatsApp Bot

To react to commands, listen for the event and check the `content` field. You can create these automations directly in the Home Assistant UI.

<div class="btn-myha-wrapper">
  <a href="https://my.home-assistant.io/redirect/automations/" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Open Automations</span></a>
</div>

### Simple Command: `/status`

{% raw %}

```yaml
alias: 'WhatsApp Bot: Status'
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.content | lower == '/status' }}"
action:
  - service: whatsapp.send_message
    data:
      target: '{{ trigger.event.data.sender }}'
      message: |
        The server is online! 🚀
        Uptime: {{ states('sensor.whatsapp_uptime') }}
```

{% endraw %}

### Complex Command: `/light [on|off]`

Using regex or simple "in" checks to handle parameters.

{% raw %}

```yaml
alias: 'WhatsApp Bot: Light Switch'
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.content | lower | startswith('/light') }}"
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ 'on' in trigger.event.data.content | lower }}"
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.living_room
      - conditions:
          - condition: template
            value_template: "{{ 'off' in trigger.event.data.content | lower }}"
        sequence:
          - service: light.turn_off
            target:
              entity_id: light.living_room
```

{% endraw %}

---

## 🎭 Group Interactions

Automating group chats requires checking if the message came from a group.

### Auto-Emoji Reaction

React with a specific emoji if a keyword is mentioned in a group.

{% raw %}

```yaml
alias: 'WhatsApp Bot: Beer Keyword'
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: >
      {{ 'beer' in trigger.event.data.content | lower or
         'cheers' in trigger.event.data.content | lower or
         'bier' in trigger.event.data.content | lower }}
action:
  - service: whatsapp.send_reaction
    data:
      target: '{{ trigger.event.data.sender }}'
      message_id: '{{ trigger.event.data.raw.key.id }}'
      reaction: '🍺'
```

{% endraw %}

---

## 📸 Security: Camera Snapshots

Send an image when motion is detected.

{% raw %}

```yaml
alias: 'WhatsApp: Motion Security'
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_motion
    to: 'on'
action:
  - service: camera.snapshot
    data:
      filename: '/config/www/tmp/snapshot.jpg'
    target:
      entity_id: camera.front_door
  - delay: '00:00:02'
  - service: whatsapp.send_image
    data:
      target: '49123456789' # Suffix added automatically
      message: 'Movement at the door! 📷'
      url: 'https://your-domain.com/local/tmp/snapshot.jpg'
```

{% endraw %}

---

## 📧 Useful Real-Life Examples

### Forward Emails (IMAP) to WhatsApp

Useful for urgent training inquiries or important work emails.

{% raw %}

```yaml
id: 'volleyball_new_training_inquiry_mail'
alias: 'Volleyball Training: Forward New Email to WhatsApp'
description: 'Sends a WhatsApp message on new training inquiry via IMAP.'
mode: single
trigger:
  - platform: event
    event_type: imap_content
condition:
  # Filter for a specific mailbox user if needed
  - condition: template
    value_template: "{{ trigger.event.data['username'] | lower | trim == 'your-mail@gmail.com' }}"
action:
  - service: whatsapp.send_message
    continue_on_error: true
    data:
      target: '49171234567'
      message: |
        🏐 *Neue Trainingsanfrage*

        📅 *Datum:* {{ as_timestamp(trigger.event.data['date']) | timestamp_custom('%d.%m.%Y %H:%M') }}
        👤 *Von:* {{ trigger.event.data['sender'] }}
        📝 *Betreff:* {{ trigger.event.data['subject'] }}

        --------------------------------

        {{ trigger.event.data['text'] | default(trigger.event.data['body']) | default('No content') | truncate(800) }}
```

{% endraw %}

### Appliances: Washer/Dryer Notifications

Get a WhatsApp when your laundry is done.

{% raw %}

```yaml
alias: 'WhatsApp: Laundry Notification'
trigger:
  - platform: state
    entity_id: binary_sensor.washer_running
    from: 'on'
    to: 'off'
action:
  - service: whatsapp.send_message
    data:
      target: '1203630234567@g.us' # Send to a family group
      message: |
        🧺 *Wäsche ist fertig!*
        Bitte die Waschmaschine leeren und in den Trockner räumen.
```

{% endraw %}

### System: Low Battery Alert

Get a list of all devices with low battery.

{% raw %}

```yaml
alias: 'WhatsApp: Low Battery Alert'
trigger:
  - platform: numeric_state
    entity_id:
      - sensor.living_room_temp_battery
      - sensor.kitchen_motion_battery
    below: 20
action:
  - service: whatsapp.send_message
    data:
      target: '49171234567'
      message: |
        🪫 *Batterie schwach!*
        Das Gerät *{{ friendly_name(trigger.entity_id) }}* hat nur noch {{ state(trigger.entity_id) }}%.
```

{% endraw %}

> **Image Access**: The App needs to be able to download the image from the URL you provided. If using `localhost` URLs, ensure the App has network access to the Home Assistant instance.
> {: .important }
