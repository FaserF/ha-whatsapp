# 🚀 Setup & Installation

## Installation

### 1. HACS (Recommended)
*Coming soon to HACS Default Repository.*

1. Open HACS > Integrations > **Custom Repositories**.
2. Add `https://github.com/FaserF/ha-whatsapp` as an Integration.
3. Click **Install**.
4. Restart Home Assistant.

### 2. Manual Installation
1. Download the latest release `ha-whatsapp.zip`.
2. Extract the `custom_components/whatsapp` folder to your HA `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for **WhatsApp**.
3. A **QR Code** will appear in the setup window.
4. Open WhatsApp on your phone:
   - **iOS**: Settings > Linked Devices > Link a Device.
   - **Android**: Three dots > Linked Devices > Link a Device.
5. Scan the QR Code.
6. Does it say **Success**? Great! You are connected.

## Troubleshooting

- **QR Code fails to scan:** Ensure your phone camera lens is clean and the screen brightness is high.
- **Connection lost:** If the container restarts, the session is restored automatically. If it fails, check the logs for "Auth Invalid" and re-authenticate by deleting and re-adding the integration.
