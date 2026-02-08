---
layout: default
title: Installation
nav_order: 2
---

# ⚙️ Installation Guide

Setting up the WhatsApp integration is a two-step process: installing the **App** (the engine) and then the **Integration** (the interface).

---

## 1️⃣ App Installation

The App handles the heavy lifting of connecting to WhatsApp.

1.  **Add the Repository**: Click the button below to add the App repository to your Home Assistant.

<div class="btn-myha-wrapper">
  <a href="https://my.home-assistant.io/redirect/supervisor_add_App_repository/?repository_url=https%3A%2F%2Fgithub.com%2FFaserF%2Fhassio-addons" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Add Repository</span></a>
</div>

2.  **Install the App**: Navigate to the store, search for **WhatsApp**, and click **Install**.

> [!TIP]
> **Using Home Assistant OS / Supervisor?** You can skip manual addon installation! The integration will offer to install the official Addon (Stable or Edge) automatically during the config flow setup.

<div class="btn-myha-wrapper">
  <a href="https://my.home-assistant.io/redirect/supervisor_Apps/" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">App Dashboard</span></a>
</div>

3.  **Start & Get Token**:
    - Ensure `log_level` is set to `info` in the **Configuration** tab.
    - **Start** the App.
    - Open the **Web UI** and look for the **API Token** (hidden behind "Show API Key"). **Copy this token** for the next step.

> **Tip**
> **Host Network Mode:** If you want the integration to be automatically discovered ("New devices found"), enable the **"Use Host Network"** toggle in the App configuration.
>
> **Note**
> The QR Code might not appear immediately in the App Web UI if you are not observing it. **Do not scan anything yet.** The scanning happens in the Integration setup.
> {: .tip }

---

## 2️⃣ Integration Installation

The Integration connects Home Assistant's core to the App and provides the entities.

### Option A: HACS (Recommended)

1.  **Install Repository**: Add the custom repository in HACS.

<div class="btn-myha-wrapper">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=FaserF&repository=ha-whatsapp&category=integration" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Open HACS</span></a>
</div>

2.  **Restart**: Once installed via HACS, **Restart Home Assistant**.

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

1.  Click the button below to start the setup:

<div class="btn-myha-wrapper">
  <a href="https://my.home-assistant.io/redirect/config_flow/?domain=whatsapp" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Add Integration</span></a>
</div>

2.  **Auto-Discovery**: If your network supports mDNS (and Host Network is enabled in the App), you will see a notification in Home Assistant. Click **Configure**.
3.  **Connection Details**:
    - **Host**: Enter the URL of your App. (Default: `http://localhost:8066`).
    - **API Key**: Paste the **API Token** you copied from the App Web UI.
4.  Click **Submit**.

### 📱 Pairing with WhatsApp

1.  After submitting the API Key, the Integration will verify the connection.
2.  The **Integration Setup Dialog** will now display a **QR Code**.
3.  On your phone, open WhatsApp -> **Linked Devices** -> **Link a Device**.
4.  **Scan the QR code shown in the Integration Dialog**.
5.  The integration will confirm the connection. Click **Finish**.

---

### ⚠️ Common Prerequisites

- **Supervisor**: This App requires a Home Assistant Supervised or Home Assistant OS installation.
- **Network**: Ensure the App port (`8066`) is not blocked by a firewall if HA and the App are on different machines.
