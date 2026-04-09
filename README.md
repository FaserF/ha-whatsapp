# 💬 HA WhatsApp Integration

<img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="100" alt="WhatsApp Logo">

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/FaserF/ha-whatsapp.svg)](https://github.com/FaserF/ha-whatsapp/releases)

> Connect your Home Assistant instance directly to WhatsApp using the "Linked Devices" (Web) protocol. No Business API required. 🚀
>
> **Requires the [Home Assistant App](https://github.com/FaserF/hassio-addons) to function.** This integration communicates with the App to send and receive messages.

---

| Component                | Version                                                                                                                                                                                                                                                                               | Status     |
| :----------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------- |
| **App (Stable)**         | [![App Version](https://img.shields.io/github/v/release/FaserF/hassio-addons?filter=whatsapp&label=App&style=flat-square)](https://github.com/FaserF/hassio-addons/tree/master/whatsapp)                                                                                              | engine     |
| **App (Edge)**           | [![App Edge](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FFaserF%2Fhassio-addons%2Fedge%2Fwhatsapp%2Fconfig.yaml&query=%24.version&label=Edge&style=flat-square&color=orange)](https://github.com/FaserF/hassio-addons/tree/edge/whatsapp) | engine-dev |
| **Integration (Stable)** | [![Integration Stable](https://img.shields.io/github/v/release/FaserF/ha-whatsapp?style=flat-square&label=Stable)](https://github.com/FaserF/ha-whatsapp/releases)                                                                                                                    | interface  |
| **Integration (Beta)**   | [![Integration Beta](https://img.shields.io/github/v/release/FaserF/ha-whatsapp?include_prereleases&style=flat-square&label=Beta&color=orange)](https://github.com/FaserF/ha-whatsapp/releases)                                                                                       | testing    |
| **Activity**             | [![Last Commit](https://img.shields.io/github/last-commit/FaserF/ha-whatsapp?style=flat-square&label=Last%20Update)](https://github.com/FaserF/ha-whatsapp/commits/master)                                                                                                            |            |

---

## ❤️ Support This Project

> I maintain this integration in my **free time alongside my regular job** — bug hunting, new features, testing on real devices. Test hardware costs money, and every donation helps me stay independent and dedicate more time to open-source work.
>
> **This project is and will always remain 100% free.** There are no "Premium Upgrades", paid features, or subscriptions. Every feature is available to everyone.
>
> Donations are completely voluntary — but the more support I receive, the less I depend on other income sources and the more time I can realistically invest into these projects. 💪

<div align="center">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor%20on-GitHub-%23EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/FaserF)&nbsp;&nbsp;
[![PayPal](https://img.shields.io/badge/Donate%20via-PayPal-%2300457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/FaserF)

</div>

---

> [!CAUTION]
> **Legal Disclaimer / Haftungsausschluss**
>
> Using this integration may violate WhatsApp's **[Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)**. WhatsApp explicitly prohibits unauthorized automated or bulk messaging.
>
> **The developers of this project assume no liability for any banned or blocked accounts.** Use at your own risk. For more information, please read the official **[Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)**.

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

- **📲 Local & Private**: Acts as a "Linked Device" (like WhatsApp Web). No cloud bridge, no external servers.
- **💬 Rich Messaging**: Send Text, Images, Videos, Audio (PTT), Documents, and Locations.
- **📊 Interactive Content**: Send Polls, Buttons, and List Menus to interact with users.
- **🔄 Two-Way Communication**: React to incoming messages, button clicks, and poll votes.
- **🛡️ Modern Standards**: Fully compatible with the Home Assistant `notify` standard (ADR-0010).
- **📝 Message Management**: Edit or Revoke (delete) messages after sending.
- **🕵️ Discovery Tools**: Built-in service to find Group IDs without checking logs.
- **🤖 Automation Triggers**: Real-time events for everything happening on WhatsApp.
- **🛡️ Native Control**: Built-in commands (`ha-app-*`) to check status, restart, or run diagnostics directly via WhatsApp.
- **🔔 Admin Alerts**: Proactive system notifications for WhatsApp loss/restore and HA Core/Integration updates.
- **🌍 Localization**: Full native support for English and German (DE/EN).

---

## 📚 Documentation

The most up-to-date and detailed documentation is available at our **[Official Documentation Site](https://faserf.github.io/ha-whatsapp/)**.

| Guide                                                                      | Description                                               |
| :------------------------------------------------------------------------- | :-------------------------------------------------------- |
| **[🚀 Full Guide](https://faserf.github.io/ha-whatsapp/)**                 | Installation, Services, Automations, and Pro-Tips.        |
| **[📚 Whitelist Guide](docs/configuration.md#security-whitelist-feature)** | Restrict interaction to specific users/groups.            |
| **[🔘 Buttons Guide](docs/buttons.md)**                                    | Deep dive into interactive buttons and limitations.       |
| **[📖 Local Examples](EXAMPLES.md)**                                       | Quick reference for YAML snippets inside this repository. |
| **[🛠️ Troubleshooting](docs/troubleshooting.md)**                          | Diagnostic tools and fixing common connection issues.     |

---

## 💡 How to use

### The WhatsApp Sensor

The integration provides a binary sensor (e.g., `binary_sensor.whatsapp`).

- **State**: Indicates if the integration is successfully connected to the App.
- **Attributes**:
  - `messages_sent`: Total number of messages sent since restart.
  - `last_message_content`: Content of the last sent message.
  - `last_message_target`: Phone number of the last recipient.

If the sensor is `disabled`, check your Home Assistant "Entities" settings and enable it. It tracks the connection health to the WhatsApp Home Assistant App.

### Services

#### 1. Native WhatsApp Services (Recommended)

Use these for the most robust experience in YAML.

```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'Hello from HA!'
```

#### 2. Legacy Notify (`notify.whatsapp`)

Great for sending to multiple numbers at once or for simple alerts.

```yaml
service: notify.whatsapp
data:
  message: 'Washing machine is done! 🧺'
  target:
    - '+491234567890'
    - '123456789@g.us'
```

#### 3. Modern Notify Action (`notify.send_message`)

> [!WARNING]
> Only use this in the **Visual Editor (UI)**. In YAML, it often fails with `extra keys not allowed`.

```yaml
action: notify.send_message
target:
  entity_id: notify.whatsapp
data:
  message: 'Hello World!'
```

#### 4. Interactive Polls 📊

Gather feedback or make decisions with family/groups.

```yaml
service: whatsapp.send_poll
data:
  target: '+491234567890'
  question: 'What should we have for dinner? 🍕'
  options:
    - 'Pizza'
    - 'Sushi'
    - 'Cooking myself'
```

#### 5. Disappearing Messages ⏳

Ensure privacy by setting an expiration time (matching chat settings).

```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'This message will disappear according to chat rules.'
  expiration: 86400 # 24 hours
```

### Service Examples

We've provided examples for **Personal (Direct)** chats and **Group** chats.

- **Direct ID**: `+491234567890` (Phone number with country code)
- **Group ID**: `123456789-123456@g.us` (Find this via Events, see below)

#### 1. Send Text Message 📝

<details>
<summary>Click to show YAML examples</summary>

**Direct Chat:**

```yaml
service: whatsapp.send_message
data:
  target: '+491234567890'
  message: 'Hello!'
```

**Group Chat:**

```yaml
service: whatsapp.send_message
data:
  target: '123456789-123456@g.us'
  message: 'Hello Everyone! 👋'
```

</details>

#### 2. Send Polls 📊

<details>
<summary>Click to show YAML examples</summary>

**Direct Chat:**

```yaml
service: whatsapp.send_poll
data:
  target: '+491234567890'
  question: 'Lunch?'
  options: ['Pizza', 'Sushi']
```

**Group Chat:**

```yaml
service: whatsapp.send_poll
data:
  target: '123456789-123456@g.us'
  question: 'Team Building Activity?'
  options:
    - 'Bowling 🎳'
    - 'Cinema 🍿'
    - 'Hiking 🥾'
```

</details>

#### 3. Send Image 🖼️

<details>
<summary>Click to show YAML examples</summary>

**Direct Chat:**

```yaml
service: whatsapp.send_image
data:
  target: '+491234567890'
  url: 'https://www.home-assistant.io/images/favicon.jpg'
  caption: 'Check this out!'
```

**Group Chat:**

```yaml
service: whatsapp.send_image
data:
  target: '123456789-123456@g.us'
  url: 'https://www.home-assistant.io/images/favicon.jpg'
  caption: 'New Logo Proposal'
```

</details>

#### 4. Send Location 📍

<details>
<summary>Click to show YAML examples</summary>

**Direct Chat:**

```yaml
service: whatsapp.send_location
data:
  target: '+491234567890'
  latitude: 52.5200
  longitude: 13.4050
  name: 'Meeting Point'
```

**Group Chat:**

```yaml
service: whatsapp.send_location
data:
  target: '123456789-123456@g.us'
  latitude: 48.8566
  longitude: 2.3522
  name: 'Holiday Home'
  address: 'Paris, France'
```

</details>

#### 5. Send Buttons 🔘

_Note: Button support varies by WhatsApp version._

<details>
<summary>Click to show YAML examples</summary>

**Direct Chat:**

```yaml
service: whatsapp.send_buttons
data:
  target: '+491234567890'
  message: 'Arm Alarm System?'
  footer: 'Security Automation'
  buttons:
    - id: 'arm_home'
      displayText: 'Arm Home 🏠'
    - id: 'arm_away'
      displayText: 'Arm Away 🛡️'
```

**Group Chat:**

```yaml
service: whatsapp.send_buttons
data:
  target: '123456789-123456@g.us'
  message: 'Who is coming?'
  buttons:
    - id: 'yes'
      displayText: "I'm in!"
    - id: 'no'
      displayText: "Can't make it"
```

</details>

#### 6. Reactions & Presence

<details>
<summary>Click to show YAML examples</summary>

**React to a message** (Direct or Group):

```yaml
service: whatsapp.send_reaction
data:
  target: '123456789-123456@g.us'
  message_id: 'BAE5F...' # ID from event
  reaction: '❤️'
```

**Set Presence** (Direct or Group):

```yaml
service: whatsapp.update_presence
data:
  target: '+491234567890'
  presence: 'composing' # status: typing...
```

</details>

### 🤖 Automating Replies

You can use Home Assistant automations to react to **incoming messages**, **button clicks**, and **poll votes**.

#### 1. React to a Button Click

When a user clicks a button, a `whatsapp_message_received` event is fired with `type: button_reply` (depending on App version).
The most important field is `buttonId` or `selectedId`.

```yaml
alias: Handle Alarm Button
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      type: 'button_reply' # Check your event listener for exact type
      buttonId: 'arm_away' # Matches the ID you sent
action:
  - service: alarm_control_panel.alarm_arm_away
    target:
      entity_id: alarm_control_panel.home_alarm
  - service: whatsapp.send_message
    data:
      target: '{{ trigger.event.data.from }}'
      message: 'Alarm Armed! 🛡️'
```

#### 2. React to a Poll Vote

Polls fire updates when votes change.

```yaml
alias: Pizza Poll Handler
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      type: 'poll_update'
condition:
  - condition: template
    value_template: "{{ 'Pizza' in trigger.event.data.vote }}"
action:
  - service: whatsapp.send_message
    data:
      target: '{{ trigger.event.data.from }}'
      message: 'Great choice! 🍕'
```

#### 3. General Message Handler

```yaml
alias: WhatsApp Auto-Reply
trigger:
  - platform: event
    event_type: whatsapp_message_received
    event_data:
      content: 'Status'
condition: []
action:
  - service: whatsapp.send_message
    data:
      target: '{{ trigger.event.data.from }}'
      message: "System is Online! 🟢\nBattery: {{ states('sensor.phone_battery_level') }}%"
```

---

---

## 🗝️ Native Control & Notifications

This integration works in tandem with the [WhatsApp App](https://github.com/FaserF/hassio-addons/tree/master/whatsapp), which provides several built-in features that don't require any YAML configuration:

### 🎮 Control Commands

If you are configured as an **Admin**, you can control the addon directly via WhatsApp by sending:

- `ha-app-status`: Full health check (Versions, Uptime, Memory).
- `ha-app-help`: List all available control commands.
- `ha-app-logs`: View the latest connection events.
- `ha-app-diagnose`: Run a full diagnostic of all message types.
- `ha-app-restart`: Trigger a reconnect of the WhatsApp session.

### 🔔 System Status Notifications

The app can automatically notify administrators about critical events:

- **✅ Update Success**: Reports when HA Core, the Addon, or this Integration has been successfully updated.
- **🔄 HA Restart**: Notifies you when HA Core is back online after a restart/reboot.
- **🌐 Connectivity**: Alerts if the connection to WhatsApp or HA Core is lost/restored, including downtime duration.

### 👋 Welcome Message

The bot automatically sends a role-aware greeting to new users on their first direct contact, ensuring they know how to interact with the system.

---

## 🆔 Finding Chat IDs & Group IDs

To send messages, you need a `target` ID. The integration makes finding these very easy.

### 1. Private Chats (Phone Numbers)

Use the phone number in international format. The integration automatically adds the required suffix.

- **Example**: `+491234567890` or `491234567890`

### 2. Group IDs (The Easy Way) 🏆

Group IDs look like `120363012345678901@g.us`. Instead of searching through logs or listening to events, use the built-in **Search Service**:

1. Go to **Developer Tools** → **Services**.
2. Select `whatsapp.search_groups`.
3. (Optional) Enter a `name_filter`.
4. Click **Call Service**.
5. **Check your Notifications (Bell icon 🔔 in the sidebar)!** A table with all your groups and their IDs will appear instantly.

### 3. Listening to Events (Advanced)

If you need the ID of a specific incoming message or a dynamic sender:

1. Go to **Developer Tools** → **Events**.
2. Listen to `whatsapp_message_received`.
3. Send a message to the bot. The ID is in the `from` field.

---

## 🛠️ Requirements & App

> [!IMPORTANT]
> **This integration DOES NOT work alone.**
> It is strictly a bridge to the **[HA WhatsApp Home Assistant App](https://github.com/FaserF/hassio-addons/tree/master/whatsapp)**.

### Why?

WhatsApp Web protocols are complex and require a headless browser to maintain encryption and session state.

- **The App**: Runs the browser (Puppeteer/Playwright), handles QR scanning, and encryption.
- **The Integration**: Connects to the App API to expose services and sensors to Home Assistant.

You **Must** install the App from the repo above for this to work.

---

## 🏷️ Versioning & Releases

We use a structured release cycle to ensure stability while providing new features:

- **Stable (v1.x.x)**: Recommended for all users. Tested and verified for production use.
- **Beta (v1.x.xbX)**: Public testing of new features. Recommended if you want the latest tech and can provide feedback. Available via HACS "Redownload" -> "Show beta versions".
- **Edge/Dev (v1.x.x-dev)**: Bleeding edge from the master branch. May be unstable. Only for developers.

Releases are automatically created when the version in `manifest.json` is updated.

---

## 📜 License

MIT License. Open Source & Free. ❤️
