---
layout: default
title: Beta Installation
nav_order: 3
---

# Beta & Edge Installation Guide

> **Warning**
> **This guide is for advanced users only.**
>
> Using "Beta" or "Edge" versions means you are testing software that is currently in development. These versions may contain bugs, incomplete features, or breaking changes.
>
> **For most users, the Stable version is sufficient and recommended.** Only proceed if you want to test new features early or if you have been asked to verify a fix.
> {: .warning }

This guide describes how to install the **Beta version** of the Home Assistant Integration and the **Edge version** of the WhatsApp Home Assistant App.

You can mix and match (e.g., Stable App with Beta Integration), but for testing new features, it is often necessary to update both.

## Terminology

Before we begin, let's clarify the terms:

- **Stable**: Tested and verified versions. Recommended for daily use.
- **Beta / Pre-release**: A version of the **Integration** that is ready for testing but not yet promoted to stable.
- **Edge**: A version of the **App** that is built directly from the latest source code. It is the absolute latest version but requires your Home Assistant to build the Docker image locally (which takes time).

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
6.  Look for the version selection. You might see a link or dropdown that says **"Need a different version?"** (or similar, depending on text layout).
7.  Select the latest version from the list.
    - Beta/Pre-release versions are typically marked with a **"b"** in the version number (e.g., `v0.1.2b4`).
    - HACS may explicitly label them as **"Pre-release"**.
8.  Click **Download**.
9.  After the download finishes, you **must restart Home Assistant** for the changes to take effect.

---

## 2. Installing the Edge App

The App runs the actual WhatsApp Web client (Baileys) in the background. To get updates to the underlying engine or new API features, you need the Edge version of the App.

**Note:** The Edge App is a *separate* App from the Stable one. You will likely want to stop the Stable App before starting the Edge one to avoid conflicts (they use the same port).

1.  **Add the Edge Repository**:

    The easiest way is to click the button below:

    <div class="btn-myha-wrapper">
      <a href="https://my.home-assistant.io/redirect/supervisor_add_App_repository/?repository_url=https%3A%2F%2Fgithub.com%2FFaserF%2Fhassio-addons%23edge" target="_blank" class="btn-myha"><span class="logo-box"><svg style="width:24px;height:24px" viewBox="0 0 24 24"><path d="M12,4L2,11V22h20V11M12,5.84L20,11.44V20.5H15V15.5A3,3 0 0,0 12,12.5A3,3 0 0,0 9,15.5V20.5H4V11.44L12,5.84Z" fill="white" /></svg></span><span class="label-box">Add Edge Repository</span></a>
    </div>

    **Manual Instructions:**
    1.  Open **Home Assistant** and go to **Settings** -> **Apps**.
    2.  Click the **App Store** button (bottom right).
    3.  Click the **three dots** (⋮) in the top right corner -> **Repositories**.
    4.  Add the **Edge Repository** URL:
        ```text
        https://github.com/FaserF/hassio-addons#edge
        ```
    5.  Click **Add**.
    6.  Refresh the page (or close and reopen the App Store).
    7.  Scroll down to the new **"FaserF's Home Assistant Apps (Edge)"** section.
    8.  Click on **WhatsApp (Edge)**.

2.  Click **Install**.
    - **Important:** Since this is an "Edge" build, Home Assistant will build the Docker image on your device. **This can take 5-15 minutes** depending on your hardware (Raspberry Pi takes longer than a NUC). Do not interrupt the process.

3.  Once installed, configure it exactly like the Stable App (Port 8066 etc.).

4.  **Stop** your existing Stable WhatsApp Home Assistant App.

5.  **Start** the new WhatsApp (Edge) App.

> [!TIP]
> You can switch back to the Stable App at any time by stopping the Edge version and starting the Stable version.

---

## Summary

| Component | How to get Beta/Edge |
| :--- | :--- |
| **Integration** | HACS -> Redownload -> Show beta versions |
| **App** | App Store -> Add Repository `...#edge` -> Install WhatsApp (Edge) |

Happy Testing! 🧪
