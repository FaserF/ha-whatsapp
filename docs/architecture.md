---
layout: default
title: Architecture & Why
nav_order: 6
---

# 🏗️ Architecture & Why

Users often ask: _"Why do I need both an App and an Integration? Can't it be one thing?"_

The answer is stability, compatibility, and isolation. Here is the breakdown of why this architecture was chosen.

---

## 🧩 The "Sidecar" Pattern

In the world of Home Assistant, complex integrations that rely on large external libraries (like `Baileys` for WhatsApp) are best served by a dedicated backend.

### 1. Dependency Management (Node.js vs Python)

Home Assistant is built on **Python**. The most robust and up-to-date WhatsApp library, **Baileys**, is written in **Node.js**.
By running Baileys in a separate Docker container (the App), we avoid:

- Mixing Python and Node.js environments.
- Conflicts between system dependencies.
- Large images for the core Home Assistant installation.

### 2. Isolation & Stability

If the WhatsApp connection process consumes a lot of memory or crashes during a heavy pairing session, it **only** affects the App. Home Assistant remains stable and responsive. The Supervisor automatically restarts the App if it fails, without requiring a full Home Assistant reboot.

### 3. Persistent Sessions

WhatsApp Web sessions are sensitive. The App provides a dedicated `/data` partition where the Baileys session data is stored safely. This environment is specifically optimized for maintaining a low-footprint background connection.

---

## 🛠️ How they communicate

The Integration and App communicate over a **REST API**.

- **Integration -> App**: Sends HTTP POST requests (e.g., `send_message`) with an API key for security.
- **App -> Integration**: The App doesn't "push" directly. Instead, the Integration **polls** the App for new events (like received messages). This ensures a stable connection even if network conditions are suboptimal.

---

## 🚀 Performance

Since the App is built on **Node.js (Baileys)**, it handles the encrypted WhatsApp socket in a highly efficient, non-blocking way. This means negligible CPU usage once connected, even on smaller devices like a Raspberry Pi 3 or 4.
