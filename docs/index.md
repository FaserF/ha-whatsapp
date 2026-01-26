---
layout: default
title: Home
nav_order: 1
mermaid: true
description: "A professional WhatsApp bridge for Home Assistant using Baileys and Node.js."
---

<div class="hero-section">
  <h1>WhatsApp for HA</h1>
  <p style="font-size: 1.2rem; opacity: 0.8;">The most robust, private, and localized WhatsApp integration for Home Assistant.</p>
  <div style="margin-top: 2rem;">
    <a href="installation.html" class="btn">Get Started Now</a>
  </div>
</div>

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
