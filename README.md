# 💬 HA WhatsApp Integration

<img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="100" alt="WhatsApp Logo">

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-whatsapp.svg)](https://github.com/FaserF/ha-whatsapp/releases)

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
| **Activity**             | [![Last Release](https://img.shields.io/github/release-date/FaserF/ha-whatsapp?style=flat-square&label=Last%20Update)](https://github.com/FaserF/ha-whatsapp/releases)                                                                                                                |            |

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

- **📲 Local & Private**: Acts as a "Linked Device" (like WhatsApp Web). No cloud bridge required.
- **💬 Rich Messaging**: Send Text, Images, and Interactive Polls.
- **🤖 Automation Triggers**: Real-time events for incoming messages.
- **🌍 Localization**: Native support for English and German (DE/EN).
- **🛡️ Secure**: Built with strict typing, secret management, and extensive testing.

---

## 📚 Documentation

The most up-to-date and detailed documentation is available at our **[Official Documentation Site](https://faserf.github.io/ha-whatsapp/)**.

| Guide                                                      | Description                                               |
| :--------------------------------------------------------- | :-------------------------------------------------------- |
| **[🚀 Full Guide](https://faserf.github.io/ha-whatsapp/)** | Installation, Services, Automations, and Pro-Tips.        |
| **[📚 Whitelist Guide](docs/WHITELIST.md)**                | Restrict interaction to specific users/groups.            |
| **[📖 Local Examples](EXAMPLES.md)**                       | Quick reference for YAML snippets inside this repository. |

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

#### 4. Send Polls 📊

You can send interactive polls to groups or users.

```yaml
service: whatsapp.send_poll
data:
  target: '+491234567890' # Or Group ID
  question: 'Who wants pizza? 🍕'
  options:
    - 'Me! 🙋‍♂️'
    - 'No thanks 🙅‍♂️'
    - 'Only on Friday 📅'
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

- **Pre-release (< 1.0.0)**: Development versions. May contain breaking changes.
- **Stable (>= 1.0.0)**: Production-ready. Follows semantic versioning.

Releases are automatically created when the version in `manifest.json` is updated.

---

## 📜 License

MIT License. Open Source & Free. ❤️
