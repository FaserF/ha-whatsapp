---
layout: default
title: Installation
nav_order: 2
---

# ⚙️ Installation Guide

Setting up the WhatsApp integration is a two-step process: installing the **Addon** (the engine) and then the **Integration** (the interface).

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
8.  **Important**: Open the **Web UI** of the addon and look for the **API Token** (often hidden behind a "Show API Key" button). **Copy this token**, you will need it for the next step.

> [!NOTE]
> The QR Code might not appear immediately in the Addon Web UI if you are not observing it. **Do not scan anything yet.** The scanning happens in the Integration setup.

---

## 2️⃣ Integration Installation

The Integration connects Home Assistant's core to the Addon and provides the entities.

### Option A: HACS (Recommended)

1.  Ensure you have **HACS** installed.
2.  Go to **HACS** -> **Integrations**.
3.  Click the three dots in the top right and select **Custom repositories**.
4.  Add `https://github.com/FaserF/ha-whatsapp` as an **Integration**.
5.  Install the **WhatsApp** integration via HACS.
6.  Restart Home Assistant.

### Option B: Manual Installation (Fallback)

1.  Go to the **[GitHub Release Page](https://github.com/FaserF/ha-whatsapp/releases)**.
2.  Download the latest `ha-whatsapp.zip` file.
3.  Open your Home Assistant configuration directory (where `configuration.yaml` is located).
4.  Create a folder `custom_components` if it doesn't exist.
5.  Extract the `whatsapp` folder from the zip file into `custom_components`.
    - Final path should be: `/config/custom_components/whatsapp/__init__.py` etc.
6.  Restart Home Assistant.

---

## 3️⃣ Configuration & Linking

Now we connect the components and link your device.

1.  Navigate to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** and search for **WhatsApp**.
3.  **Auto-Discovery**: If your network supports mDNS, Home Assistant might already show a notification. Click **Configure**.
4.  **Connection Details**:
    - **Host**: Enter the URL of your Addon. (Default: `http://localhost:8066` if on the same machine).
    - **API Key**: Paste the **API Token** you copied from the Addon Web UI in Step 1.
5.  Click **Submit**.

### 📱 Pairing with WhatsApp

1.  After submitting the API Key, the Integration will verify the connection.
2.  The **Integration Setup Dialog** will now display a **QR Code**.
3.  On your phone, open WhatsApp -> **Linked Devices** -> **Link a Device**.
4.  **Scan the QR code shown in the Integration Dialog**.
5.  The integration will confirm the connection. Click **Finish**.

---

### ⚠️ Common Prerequisites
- **Supervisor**: This addon requires a Home Assistant Supervised or Home Assistant OS installation.
- **Network**: Ensure the Addon port (`8066`) is not blocked by a firewall if HA and the Addon are on different machines.
