---
layout: default
title: Advanced Automations
nav_order: 4
---

# 🤖 Advanced Automations

The real power of the WhatsApp integration lies in the events. Every message received by the Addon is fired into Home Assistant as a `whatsapp_message_received` event.

---

## 📨 Building a WhatsApp Bot

To react to commands, listen for the event and check the `text` field.

### Simple Command: `/status`
{% raw %}
```yaml
alias: "WhatsApp Bot: Status"
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.text == '/status' }}"
action:
  - service: notify.send_message
    target:
      entity_id: notify.whatsapp
    data:
      message: "The server is online! 🚀\nUptime: {{ states('sensor.uptime') }}"
      target: "{{ trigger.event.data.raw.key.remoteJid }}"
```
{% endraw %}

### Complex Command: `/light [on|off]`
Using regex or simple "in" checks to handle parameters.
{% raw %}
```yaml
alias: "WhatsApp Bot: Light Switch"
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: "{{ trigger.event.data.text.startswith('/light') }}"
action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ 'on' in trigger.event.data.text }}"
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.living_room
      - conditions:
          - condition: template
            value_template: "{{ 'off' in trigger.event.data.text }}"
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
alias: "WhatsApp Bot: Beer Keyword"
trigger:
  - platform: event
    event_type: whatsapp_message_received
condition:
  - condition: template
    value_template: >
      {{ trigger.event.data.is_group and
         ('Beer' in trigger.event.data.text or 'Cheers' in trigger.event.data.text) }}
action:
  - service: notify.send_message
    target:
      entity_id: notify.whatsapp
    data:
      message: "Reaction"
      target: "{{ trigger.event.data.raw.key.remoteJid }}"
      data:
        reaction:
          reaction: "🍺"
          message_id: "{{ trigger.event.data.raw.key.id }}"
```
{% endraw %}

---

## 📸 Security: Camera Snapshots

Send an image when motion is detected.

{% raw %}
```yaml
alias: "WhatsApp: Motion Security"
trigger:
  - platform: state
    entity_id: binary_sensor.front_door_motion
    to: "on"
action:
  - service: camera.snapshot
    data:
      filename: "/config/www/tmp/snapshot.jpg"
    target:
      entity_id: camera.front_door
  - delay: "00:00:02"
  - service: notify.send_message
    target:
      entity_id: notify.whatsapp
    data:
      message: "Movement at the door! 📷"
      target: "+49123456789"
      data:
        image: "https://your-domain.com/local/tmp/snapshot.jpg"
```
{% endraw %}

> **Image Access**: The Addon needs to be able to download the image from the URL you provided. If using `localhost` URLs, ensure the Addon has network access to the Home Assistant instance.
{: .important }
