# 💬 HA WhatsApp Integration

<img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="100" alt="WhatsApp Logo">

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-whatsapp.svg)](https://github.com/FaserF/ha-whatsapp/releases)

> **Enterprise-grade WhatsApp integration for Home Assistant.**
>
> Connect your Home Assistant instance directly to WhatsApp using the "Linked Devices" (Web) protocol. No Business API required. 🚀
>
> **Requires the [Home Assistant Addon](https://github.com/FaserF/hassio-addons) to function.** This integration communicates with the addon to send and receive messages.

---

## 📥 Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-whatsapp&category=integration)

1. Click the button above or add this repository as a **custom repository** in HACS:
   - Go to HACS → Integrations → ⋮ (menu) → Custom repositories
   - Add: `https://github.com/FaserF/ha-whatsapp` (Category: Integration)
2. Install "Home Assistant WhatsApp" from HACS.
3. Restart Home Assistant.
4. Add the integration via Settings → Devices & Services → Add Integration → WhatsApp.

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/FaserF/ha-whatsapp/releases).
2. Extract and copy the `whatsapp` folder to `config/custom_components/`.
3. Restart Home Assistant.

---

## 🌟 Features

- **📲 Local & Private**: Acts as a "Linked Device" (like WhatsApp Web). No cloud bridge required.
- **💬 Rich Messaging**: Send Text, Images, and Interactive Polls.
- **🤖 Automation Triggers**: Real-time events for incoming messages.
- **🌍 Localization**: Native support for English and German (DE/EN).
- **🛡️ Secure**: Built with strict typing, secret management, and extensive testing.

---

## 📚 Documentation

We believe in comprehensive documentation. Check out our detailed guides below:

| Guide | Description |
| :--- | :--- |
| **[🚀 Setup & Installation](docs/SETUP.md)** | How to install, configure URL (`8066`), and link your device via QR Code. |
| **[✉️ Services & Actions](docs/SERVICES.md)** | Detailed examples for sending messages, images, and polls. |
| **[⚡ Events & Automations](docs/EVENTS.md)** | How to react to incoming messages and build chat bots. |
| **[👨‍💻 Development](docs/DEVELOPMENT.md)** | Architecture, contributing guidelines, and CI/CD details. |

---

## 💡 How to use

### The WhatsApp Sensor
The integration provides a binary sensor (e.g., `binary_sensor.whatsapp`).
- **State**: Indicates if the integration is successfully connected to the Addon.
- **Attributes**:
  - `messages_sent`: Total number of messages sent since restart.
  - `last_message_content`: Content of the last sent message.
  - `last_message_target`: Phone number of the last recipient.

If the sensor is `disabled`, check your Home Assistant "Entities" settings and enable it. It tracks the connection health to the WhatsApp addon.

### Services

#### 1. Send simple text (Standard Notify)
You can use the standard `notify.whatsapp` service.
```yaml
service: notify.whatsapp
data:
  message: "Washing machine is done! 🧺"
  target: "+491234567890"
```

#### 2. Send Message (Native Service)
For more control, use the native service.
```yaml
service: whatsapp.send_message
data:
  target: "+491234567890"
  message: "Hello from HA!"
```

#### 3. Send Polls 📊
You can send interactive polls to groups or users.
```yaml
service: whatsapp.send_poll
data:
  target: "+491234567890"  # Or Group ID
  question: "Who wants pizza? 🍕"
  options:
    - "Me! 🙋‍♂️"
    - "No thanks 🙅‍♂️"
    - "Only on Friday 📅"
```

#### 4. Supported Features
- **Text Messages**: Fully supported.
- **Polls**: Create interactive polls.
- **Images**: Send images via URL.
- **Locations**: Send pinned locations onto the map.
- **Incoming Messages**: The integration fires `whatsapp_message_received` events.

#### 5. Send Image 🖼️
```yaml
service: whatsapp.send_image
data:
  target: "+491234567890"
  url: "https://www.home-assistant.io/images/favicon.jpg"
  caption: "Look at this!"
```

#### 6. Send Location 📍
```yaml
service: whatsapp.send_location
data:
  target: "+491234567890"
  latitude: 52.5200
  longitude: 13.4050
  name: "My Home"
  address: "Berlin, Germany"
```

### Automation Example: Reply to "Status"
```yaml
alias: WhatsApp Auto-Reply
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Status"
condition: []
action:
  - service: whatsapp.send_message
    data:
      target: "{{ trigger.event.data.from }}"
      message: "System is Online! 🟢\nBattery: {{ states('sensor.phone_battery_level') }}%"
```

---

## 🆔 Finding Chat IDs & Group IDs

To send messages, you need the correct Chat ID (`target`).

### For Private Chats
The ID is usually the phone number in international format without `+` or `00`, followed by `@c.us`.
Example: `491234567890@c.us` (often just the number work too: `+491234567890`).

### For Groups
Group IDs are harder to guess (e.g., `123456789-123456@g.us`). The easiest way to find them is to **Listen for events**.

1. Go to **Developer Tools** → **Events**.
2. In "Listen to events", type: `whatsapp_message_received`.
3. Click "Start Listening".
4. Send a message to the group you want to find.
5. The event will appear! Look for the `from` or `chatId` field.

```json
event_type: whatsapp_message_received
data:
  from: "491234567890-16123456@g.us"
  content: "Hello Test"
  ...
```
Copy that ID and use it as your `target`.

---

## 🛠️ Requirements & Addon

> [!IMPORTANT]
> **This integration DOES NOT work alone.**
> It is strictly a bridge to the **[HA WhatsApp Addon](https://github.com/FaserF/hassio-addons/tree/master/whatsapp)**.

### Why?
WhatsApp Web protocols are complex and require a headless browser to maintain encryption and session state.
- **The Addon**: Runs the browser (Puppeteer/Playwright), handles QR scanning, and encryption.
- **The Integration**: Connects to the addon API to expose services and sensors to Home Assistant.

You **Must** install the Addon from the repo above for this to work.


---

## 🏷️ Versioning & Releases

- **Pre-release** (`< 1.0.0`): Development versions. May contain breaking changes.
- **Stable** (`>= 1.0.0`): Production-ready. Follows semantic versioning.

Releases are automatically created when the version in `manifest.json` is updated.

---

## 📜 License

MIT License. Open Source & Free. ❤️
