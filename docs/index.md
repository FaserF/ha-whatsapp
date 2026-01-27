---
layout: default
title: Home
nav_order: 1
mermaid: true
description: "A professional WhatsApp bridge for Home Assistant using Baileys and Node.js."
---

<div class="hero-section">
  <img src="https://raw.githubusercontent.com/FaserF/hassio-addons/master/whatsapp/logo.png" alt="WhatsApp Logo" style="width: 100px; margin-bottom: 20px;">
  <h1>WhatsApp for HA</h1>
  <p style="font-size: 1.2rem; opacity: 0.8; max-width: 600px; margin: 0 auto 2rem;">The most robust, private, and localized WhatsApp integration for Home Assistant. Connect your automations to the world's most popular messaging platform.</p>

---

| Component | Version | Status |
| :--- | :--- | :--- |
| **Addon (Stable)** | [![Addon Version](https://img.shields.io/github/v/release/FaserF/hassio-addons?filter=whatsapp&label=Addon&style=flat-square)](https://github.com/FaserF/hassio-addons/tree/master/whatsapp) | engine |
| **Addon (Edge)** | [![Addon Edge](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FFaserF%2Fhassio-addons%2Fedge%2Fwhatsapp%2Fconfig.yaml&query=%24.version&label=Edge&style=flat-square&color=orange)](https://github.com/FaserF/hassio-addons/tree/edge/whatsapp) | engine-dev |
| **Integration (Stable)** | [![Integration Stable](https://img.shields.io/github/v/release/FaserF/ha-whatsapp?style=flat-square&label=Stable)](https://github.com/FaserF/ha-whatsapp/releases) | interface |
| **Integration (Beta)** | [![Integration Beta](https://img.shields.io/github/v/release/FaserF/ha-whatsapp?include_prereleases&style=flat-square&label=Beta&color=orange)](https://github.com/FaserF/ha-whatsapp/releases) | testing |
| **Activity** | [![Last Release](https://img.shields.io/github/release-date/FaserF/ha-whatsapp?style=flat-square&label=Last%20Update)](https://github.com/FaserF/ha-whatsapp/releases) | |

---

  <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; align-items: center; margin-bottom: 2rem;">
    <a href="installation.html" class="btn btn-green" style="padding: 12px 24px; font-weight: bold;">🚀 Get Started</a>
  </div>

  <div style="text-align: center; margin-bottom: 2rem;">
    <a href="https://my.home-assistant.io/redirect/config_flow/?domain=whatsapp" target="_blank">
      <img src="https://my.home-assistant.io/badges/config_flow.svg" alt="Open your Home Assistant instance and start setting up a new integration.">
    </a>
  </div>

  <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; opacity: 0.9;">
    <a href="https://github.com/FaserF/ha-whatsapp" class="btn btn-outline">Integration Repo</a>
    <a href="https://github.com/FaserF/hassio-addons" class="btn btn-outline">Addon Repo</a>
  </div>
</div>

> **Legal Disclaimer / Haftungsausschluss**
>
> Using automated messaging on WhatsApp may violate their **[Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)** and lead to a **permanent account ban**.
> The developers of this project assume no liability for any blocked or banned accounts. Use at your own risk.
>
> Official Policy: **[WhatsApp Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)**
{: .important }

## 🏗️ Technical Architecture

This project is built for performance and absolute privacy.

```mermaid
graph TD
    subgraph "Home Assistant Core"
        HA[Automation Engine]
        INT[Custom Integration]
    end

    subgraph "The Bridge (Addon)"
        AD[WhatsApp Server]
        BL[Baileys Engine]
    end

    HA <-->|State & Notifications| INT
    INT <-->|Secure REST API| AD
    AD <-->|Node.js Socket| BL
    BL <-->|Encrypted| WA((WhatsApp Web))
```

> **Privacy First**: Your WhatsApp connection is local. No external servers (other than WhatsApp's official ones) ever see your message content.
{: .important }

---

## 🔥 Why choose this integration?

- **Real-time**: Near-zero latency for incoming and outgoing messages.
- **Modern**: Fully supports the 2026 Home Assistant `notify` standards.
- **Rich Content**: Interactive Buttons, Polls, Reactions, and Media support.
- **Localized**: Deep German (DE) and English (EN) support.

---

*Maintained by [FaserF](https://github.com/FaserF)*.

> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with WhatsApp Inc. or any of its subsidiaries or its affiliates.
{: .note }
