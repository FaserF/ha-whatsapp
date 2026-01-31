---
layout: default
title: Beta Installation
nav_order: 3
---

# Beta & Edge Installation Guide

> [!WARNING]
> **This guide is for advanced users only.**
>
> Using "Beta" or "Edge" versions means you are testing software that is currently in development. These versions may contain bugs, incomplete features, or breaking changes.
>
> **For most users, the Stable version is sufficient and recommended.** Only proceed if you want to test new features early or if you have been asked to verify a fix.

This guide describes how to install the **Beta version** of the Home Assistant Integration and the **Edge version** of the WhatsApp Add-on.

You can mix and match (e.g., Stable Add-on with Beta Integration), but for testing new features, it is often necessary to update both.

## Terminology

Before we begin, let's clarify the terms:

- **Stable**: Tested and verified versions. Recommended for daily use.
- **Beta / Pre-release**: A version of the **Integration** that is ready for testing but not yet promoted to stable.
- **Edge**: A version of the **Add-on** that is built directly from the latest source code. It is the absolute latest version but requires your Home Assistant to build the Docker image locally (which takes time).

---

## 1. Installing the Beta Integration (HACS)

The integration communicates with Home Assistant. To get the latest changes (e.g., new services, bug fixes in the python code), you need the Beta version of the integration.

**Prerequisites:** You must have HACS installed.

1.  Open **Home Assistant** and go to **HACS**.
2.  Click on **Integrations**.
3.  Find the **Home Assistant WhatsApp** integration in your list.
    - If you haven't installed it yet, search for "Home Assistant WhatsApp" and install it.
4.  Click on the **three dots** (⋮) in the top right corner of the integration card (or the detail page).
5.  Select **Redownload**.
6.  In the version dropdown menu, enable the toggle **"Show beta versions"**.
7.  Select the latest version from the list (it usually has a `-beta` suffix or similar).
8.  Click **Download**.
9.  After the download finishes, you **must restart Home Assistant** for the changes to take effect.

---

## 2. Installing the Edge Add-on

The Add-on runs the actual WhatsApp Web client (Baileys) in the background. To get updates to the underlying engine or new API features, you need the Edge version of the Add-on.

**Note:** The Edge Add-on is a *separate* add-on from the Stable one. You will likely want to stop the Stable add-on before starting the Edge one to avoid conflicts (they use the same port).

1.  Open **Home Assistant** and go to **Settings** -> **Add-ons**.
2.  Click the **Add-on Store** button (bottom right).
3.  Click the **three dots** (⋮) in the top right corner -> **Repositories**.
4.  Add the **Edge Repository** URL:
    ```text
    https://github.com/FaserF/hassio-addons#edge
    ```
5.  Click **Add**.
6.  Refresh the page (or close and reopen the Add-on Store).
7.  Scroll down to the new **"FaserF's Home Assistant Add-ons (Edge)"** section.
8.  Click on **WhatsApp (Edge)**.
9.  Click **Install**.
    - **Important:** Since this is an "Edge" build, Home Assistant will build the Docker image on your device. **This can take 5-15 minutes** depending on your hardware (Raspberry Pi takes longer than a NUC). Do not interrupt the process.
10. Once installed, configure it exactly like the Stable add-on (Port 8066 etc.).
11. **Stop** your existing Stable WhatsApp Add-on.
12. **Start** the new WhatsApp (Edge) Add-on.

> [!TIP]
> You can switch back to the Stable Add-on at any time by stopping the Edge version and starting the Stable version.

---

## Summary

| Component | How to get Beta/Edge |
| :--- | :--- |
| **Integration** | HACS -> Redownload -> Show beta versions |
| **Add-on** | Add-on Store -> Add Repository `...#edge` -> Install WhatsApp (Edge) |

Happy Testing! 🧪
