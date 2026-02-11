---
layout: default
title: Home
nav_order: 1
mermaid: true
description: 'A professional WhatsApp bridge for Home Assistant using Baileys and Node.js.'
---

<div class="hero-section">
  <img src="https://raw.githubusercontent.com/FaserF/hassio-addons/master/whatsapp/logo.png" alt="WhatsApp Logo" style="width: 100px; margin-bottom: 20px;">
  <h1>WhatsApp for HA</h1>
  <p style="font-size: 1.2rem; opacity: 0.8; max-width: 600px; margin: 0 auto 2rem;">The most robust, private, and localized WhatsApp integration for Home Assistant. Connect your automations to the world's most popular messaging platform.</p>

  <div style="overflow-x: auto; margin: 2rem 0;">
    <table style="width: 100%; border-collapse: collapse; background: rgba(255, 255, 255, 0.02); border-radius: 12px; overflow: hidden; border: 1px solid var(--wa-border);">
      <thead>
        <tr style="background: rgba(37, 211, 102, 0.1);">
          <th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--wa-border);">Component</th>
          <th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--wa-border);">Version</th>
          <th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--wa-border);">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);"><strong>App (Stable)</strong></td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">
            <a href="https://github.com/FaserF/hassio-addons/tree/master/whatsapp">
              <img src="https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FFaserF%2Fhassio-addons%2Fmaster%2Fwhatsapp%2Fconfig.yaml&query=%24.version&label=App&style=flat-square&color=blue" alt="App Stable">
            </a>
          </td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">engine</td>
        </tr>
        <tr>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);"><strong>App (Edge)</strong></td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">
            <a href="https://github.com/FaserF/hassio-addons/tree/edge/whatsapp">
              <img src="https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FFaserF%2Fhassio-addons%2Fedge%2Fwhatsapp%2Fconfig.yaml&query=%24.version&label=Edge&style=flat-square&color=orange" alt="App Edge">
            </a>
          </td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">engine-dev</td>
        </tr>
        <tr>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);"><strong>Integration (Stable)</strong></td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">
            <a href="https://github.com/FaserF/ha-whatsapp/releases">
              <img src="https://img.shields.io/github/v/release/FaserF/ha-whatsapp?style=flat-square&label=Stable" alt="Integration Stable">
            </a>
          </td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">interface</td>
        </tr>
        <tr>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);"><strong>Integration (Beta)</strong></td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">
            <a href="https://github.com/FaserF/ha-whatsapp/releases">
              <img src="https://img.shields.io/github/v/release/FaserF/ha-whatsapp?include_prereleases&style=flat-square&label=Beta&color=orange" alt="Integration Beta">
            </a>
          </td>
          <td style="padding: 12px; border-bottom: 1px solid var(--wa-border);">testing</td>
        </tr>
        <tr>
          <td style="padding: 12px;"><strong>Activity</strong></td>
          <td style="padding: 12px;">
            <a href="https://github.com/FaserF/ha-whatsapp/releases">
              <img src="https://img.shields.io/github/release-date/FaserF/ha-whatsapp?style=flat-square&label=Last%20Update" alt="Last Update">
            </a>
          </td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; align-items: center; margin-bottom: 2rem;">
    <a href="installation.html" class="btn btn-green" style="padding: 12px 24px; font-weight: bold;">🚀 Get Started</a>
  </div>

  <div class="btn-myha-wrapper">
    <a href="https://my.home-assistant.io/redirect/config_flow/?domain=whatsapp" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Add Integration</span></a>
  </div>

  <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; opacity: 0.9;">
    <a href="https://github.com/FaserF/ha-whatsapp" class="btn btn-outline">Integration Repo</a>
    <a href="https://github.com/FaserF/hassio-addons" class="btn btn-outline">App Repo</a>
  </div>
</div>

## 🔗 Webhook Integration

Forward your WhatsApp messages to any HTTP endpoint in real-time. This project isn't just for Home Assistant; you can use the built-in Webhook to bridge WhatsApp to:

- **Node-RED** for complex automation flows.
- **Generic HTTP Servers** (Python, Node.js, PHP, etc.) for logging or custom bots.
- **Unified Chat Platforms** like Rocket.Chat or Slack.

[View the Webhook Guide](webhooks.html)
{: .btn .btn-outline }

> **Legal Disclaimer / Haftungsausschluss**
>
> Using automated messaging on WhatsApp may violate their **[Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)** and lead to a **permanent account ban**.
> The developers of this project assume no liability for any blocked or banned accounts. Use at your own risk.
>
> Official Policy: **[WhatsApp Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)**
> {: .important }

## 🏗️ Technical Architecture

This project is built for performance and absolute privacy.

```mermaid
graph TD
    %% Define Styles
    classDef wa fill:#25D366,stroke:#075E54,stroke-width:2px,color:#fff,font-weight:bold;
    classDef ha fill:#111b21,stroke:#25D366,stroke-width:1px,color:#e9edef;
    classDef logic fill:#128C7E,stroke:#075E54,stroke-width:1px,color:#fff;
    classDef network fill:#000,stroke:#25D366,stroke-width:1px,dasharray: 5 5;

    subgraph UserInterface ["User Layer"]
        User((User))
        HA_UI[HA Dashboard]
    end

    subgraph HACore ["Home Assistant Core"]
        direction TB
        WH[WhatsApp Integration]
        Core[Automation Engine]
        Notify[Notify Service]
    end

    subgraph AppBridge ["App Architecture (Local)"]
        direction TB
        API[Express API Server]
        BL[Baileys Node.js Engine]
        Auth[Local Auth Session]
    end

    subgraph External ["WhatsApp Cloud"]
        WA[WhatsApp Servers]
    end

    %% Flows
    User <-->|Control & Status| HA_UI
    HA_UI <-->|Web Interface| Core
    Core <-->|Triggers| WH
    Notify -->|Send Message| WH
    WH <-->|REST API :8066| API
    API <-->|Local Events| BL
    BL <-->|Persistent Session| Auth
    BL <-->|Websocket / MD| WA
    WA <-->|End-to-End Encrypted| Recipient((Phone))

    %% Assign Styles
    class WA,User,Recipient wa;
    class WH,Core,Notify,API,Auth ha;
    class BL logic;
    class External network;
```

> **Privacy First**: Your WhatsApp connection is local. No external servers (other than WhatsApp's official ones) ever see your message content.
> {: .important }
>
> > **Tip:**
> **Want to use Rocket.Chat?** Check out our [Rocket.Chat Bridge Guide](rocketchat.md) to connect WhatsApp to your team workspace!

## 🏷️ Versions

- **Stable**: Production-ready. Follows semantic versioning (e.g., `v1.0.1`).
- **Beta**: Feature-complete testing versions (e.g., `v1.0.1b0`). [See Installation Guide](beta.html).
- **Nightly/Dev**: Experimental builds from the latest code (e.g., `v1.0.2-dev`).

---

## 🔥 Why choose this integration?

- **💡 [Tips & Tricks](tips.md)**: Optimize your experience.
- **💬 [Rocket.Chat Bridge](rocketchat.md)**: Connect WhatsApp to your team chat.
- **🔗 [Webhook Support](webhooks.md)**: Forward messages to any external service.
- **📜 [API Documentation](api.html)**: For developers and advanced users.
- **Real-time**: Near-zero latency for incoming and outgoing messages.
- **Modern**: Fully supports the 2026 Home Assistant `notify` standards.
- **Rich Content**: Interactive Buttons, Polls, Reactions, and Media support.
- **Easy Setup**: Automatic Add-on installation and configuration for Home Assistant OS users.
- **Localized**: Deep German (DE) and English (EN) support.

---

_Maintained by [FaserF](https://github.com/FaserF)_.

> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with WhatsApp Inc. or any of its subsidiaries or its affiliates.
> {: .note }
