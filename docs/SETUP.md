# 🚀 Setup & Installation

Follow these steps to get your WhatsApp integration up and running in minutes! ⏱️

---

## 📦 1. Installation

### A. HACS (Recommended) ⭐

_Coming soon to HACS Default Repository._

1.  Open **HACS** > **Integrations**.
2.  Click the **3 dots** (top right) > **Custom Repositories**.
3.  Add `https://github.com/FaserF/ha-whatsapp` as an Integration.
4.  Click **Install**.
5.  **Restart Home Assistant**. 🔄

### B. Manual Installation

1.  Download the latest release `ha-whatsapp.zip`.
2.  Extract the `custom_components/whatsapp` folder to your HA `config/custom_components/` directory.
3.  **Restart Home Assistant**.

---

## ⚙️ 2. Configuration (The Ingress Way 🛡️)

The integration is secured with a token. The easiest way to get it is via the specific Ingress Web UI.

### 1. Get Token & Check Status

1.  Start the **WhatsApp Addon**.
2.  Click **"Open Web UI"** (Ingress).
    - _Tip: If you see "Checking Status...", just give it a second!_
3.  You will see a Status Badge and (eventually) a QR Code.
4.  Click **"Show API Key"** to reveal your token.
5.  **Copy this token**. 🔑

### 2. Add Integration in Home Assistant

1.  Go to **Settings** > **Devices & Services** > **Add Integration**.
2.  Search for **WhatsApp** (Custom).
3.  **Host**:
    - Usually `http://localhost:8066` works.
    - If not, use the addon hostname e.g. `http://7da084a7-whatsapp:8066`.
4.  **API Key**: Paste the token you copied from the Web UI.
5.  Click **Submit**.

> **🛑 Error Handling**:
>
> - If you get "Invalid API Key", double-check what you copied.
> - If you get "Cannot Connect", check the Host URL.

### 3. Link Device 📱

1.  If the API Key is valid, the integration will ask the Addon to start a session.
2.  Go back to the **Ingress Web UI**. You should see a **QR Code**.
3.  Open WhatsApp on your phone -> **Linked Devices** -> **Link a Device**.
4.  **Scan the QR Code**.
5.  The Web UI should update to **"Device Linked ✅"**.
6.  Go back to the Integration setup and click **Submit**.

---

## 🔧 Options & Reset

### Reset Authentication / Logout

If you need to change phones or fix a stuck session:

1.  Go to **Settings** -> **Devices & Services** -> **WhatsApp**.
2.  Click **Configure**.
3.  **Options Available:**
    - **Debug Payloads**: Log every incoming event to Home Assistant logs (useful for developers).
    - **Polling Interval**: How often to fetch new messages (default 2s).
    - **Mask Sensitive Data**: Hides phone numbers in logs (e.g. `491*****67`).
    - **Reset Session**: Check this box to log out and clear data.
4.  Click **Next**.
    - This will:
      - Log out the session on WhatsApp.
      - Delete the session files in the Addon.
      - Reset the Addon state to "Disconnected".
5.  You can now re-configure a new session.
