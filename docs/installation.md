---
layout: default
title: Installation
nav_order: 2
---

# ⚙️ Installation Guide

Setting up the WhatsApp integration is a two-step process: installing the Addon (the engine) and then the Integration (the interface).

---

## 1️⃣ Addon Installation

The Addon handles the heavy lifting of connecting to WhatsApp.

1.  Open your Home Assistant instance.
2.  Navigate to **Settings** -> **Add-ons**.
3.  Click the **Add-on Store** button in the bottom right.
4.  Add the repository: `https://github.com/FaserF/hassio-addons`.
5.  Find the **WhatsApp** addon and click **Install**.
6.  Go to the **Configuration** tab and ensure the `log_level` is set to `info`.
7.  Start the addon.

### 📱 Pairing with WhatsApp
1.  Open the **Web UI** of the addon.
2.  A QR code will appear.
3.  On your phone, open WhatsApp -> **Linked Devices** -> **Link a Device**.
4.  Scan the QR code shown in the Addon UI.
5.  Wait until the status changes to `Connected`.

---

## 2️⃣ Integration Installation

The Integration connects Home Assistant's core to the Addon.

1.  Ensure you have **HACS** installed.
2.  Go to **HACS** -> **Integrations**.
3.  Click the three dots in the top right and select **Custom repositories**.
4.  Add `https://github.com/FaserF/ha-whatsapp` as an **Integration**.
5.  Install the **WhatsApp** integration via HACS.
6.  Restart Home Assistant.

---

## 3️⃣ Configuration

1.  Navigate to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** and search for **WhatsApp**.
3.  **Auto-Discovery**: If your network supports mDNS, Home Assistant might already show a notification that the "WhatsApp Addon" was found. Click **Configure**.
4.  Enter the URL of your Addon. If running locally on the same machine, this is usually `http://localhost:8066`.
5.  The integration will automatically detect your connection status and create the necessary entities.

---

### ⚠️ Common Prerequisites
- **Supervisor**: This addon requires a Home Assistant Supervised or Home Assistant OS installation.
- **Network**: Ensure the Addon port (`8066`) is not blocked by a firewall if HA and the Addon are on different machines.
