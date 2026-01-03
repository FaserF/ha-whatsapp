# 💬 HA WhatsApp Integration

<img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="100" alt="WhatsApp Logo">

> **Enterprise-grade WhatsApp integration for Home Assistant.**
>
> Connect your Home Assistant instance directly to WhatsApp using the "Linked Devices" (Web) protocol. No Business API required. 🚀
>
> **Requires the [Home Assistant Addon](https://github.com/FaserF/hassio-addons) to function.** This integration communicates with the addon to send and receive messages.

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

## 🚀 Quick Example

### Send a message via YAML
```yaml
service: whatsapp.send_message
data:
  target: "+491234567890"
  message: "Home Assistant says Hello! 👋"
```

### React to an incoming message
```yaml
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: "Status"
```

---

## 📦 Requirements

- **Home Assistant**: 2024.1.0 or newer
- **WhatsApp Addon**: You need the companion addon running (Port `8066`).

---

## 📜 License

MIT License. Open Source & Free. ❤️
