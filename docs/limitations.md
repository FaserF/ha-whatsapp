---
layout: default
title: Limitations & Warnings
nav_order: 7
---

# ⚠️ Limitations & Warnings

Every tool has its limits. To ensure you have the best experience, please be aware of the following technical and policy-based limitations.

---

## 🚫 Not an Official API & Legal Terms

This project uses **Baileys**, which simulates a **WhatsApp Web** client. It does **not** use the official WhatsApp Business API.

> **Legal Disclaimer / Haftungsausschluss**
>
> Using automated messaging on WhatsApp may violate their **[Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)** and lead to a **permanent account ban**.
>
> **The developers assume no liability for any such damage.** By using this software, you acknowledge that you are responsible for any consequences.
>
> For official information, see: **[WhatsApp Terms of Service](https://www.whatsapp.com/legal/terms-of-service/)**
> {: .important }

- **Recommendation**: Use this integration only for personal notifications or small private bots. Do **not** use it for mass marketing or unsolicited messages.

---

## 📦 Technical Limitations

### 1. One Session per App & Multi-Account Support

Currently, one instance of the WhatsApp Home Assistant App can only be paired with **one** phone number at a time. If you need to manage multiple numbers, you must run multiple App instances (if supported by your environment).

#### 📱 How to run a second/dedicated WhatsApp number for Home Assistant
Most users do not want to use their primary WhatsApp number for Home Assistant notifications. If you want to use a separate/dedicated number (e.g., using a second SIM card, eSIM, or landline number) without uninstalling your main WhatsApp, you can use the following methods:

1. **WhatsApp Business (Recommended & Easiest)**:
   You can download the official **WhatsApp Business** app from the Google Play Store or Apple App Store. It can run side-by-side with your standard WhatsApp app on the same phone. Register your second number on WhatsApp Business, pair it with the Home Assistant Add-on via QR code, and you are done.
2. **Work Profiles & App Cloners (Android)**:
   If you want to run a second copy of standard WhatsApp, you can use a Work Profile app like **[Island](https://play.google.com/store/apps/details?id=com.oasisfeng.island)** or **Shelter**. These apps create an isolated sandbox/work profile on your phone, letting you install and run a second, completely separate instance of WhatsApp.
3. **Manufacturer Dual Apps**:
   Many Android phone manufacturers include a built-in feature to clone apps (e.g., Samsung's *Dual Messenger*, OnePlus's *Parallel Apps*, or Xiaomi's *Dual Apps*). Search your phone settings for these options to easily clone WhatsApp.

> **💡 Sim Card / Activation Note**
> You only need the physical SIM card (or eSIM) inside a phone during the initial SMS activation of WhatsApp. Once the second WhatsApp account is activated on your phone and paired with Home Assistant, the SIM card does not need to stay inside the phone. However, the WhatsApp app on the phone must remain active.
> {: .tip }

---

### 2. Media Uploads

The App supports sending images, but it requires a **publicly accessible URL** or a URL that the App container can reach (e.g., your local HA instance). It currently does not support "uploading" local files directly from your PC through the HA frontend into WhatsApp.

### 3. Buttons & Polls (Client Support)

Native WhatsApp Buttons and Polls are relatively new.

- They look great on **Android** and **iOS**.
- They might appear as "text links" or not appear at all on older versions of the **WhatsApp Desktop** app or **WhatsApp Web**.

#### 🗳️ Poll Reaction Limitation
Due to WhatsApp's End-to-End Encryption (E2EE), poll votes (updates) can only be decrypted if the bot has the original "Poll Creation" message in its local memory.

- **Requirement**: The bot must have been **online** when the poll was sent (or sent the poll itself).
- **Restart**: If the App (addon) is restarted, it attempts to restore the message store from disk. However, if the store was cleared or the poll is very old (evicted from cache), votes for that poll can no longer be resolved.
- **Result**: If resolution fails, the automation will receive a generic `[Poll Vote] (Resolution failed...)` message instead of the actual choice.
- {: .important }

### 4. Group IDs

The integration provides a `Chats` sensor which lists all your participating groups and their corresponding `@g.us` IDs in its attributes. You can also use the `whatsapp.search_groups` service to find IDs for your automations.

> **Warning**
> **Privacy Mode Warning**: If you enable "Mask Sensitive Data" in the options, Group IDs will also be masked in the logs. You **must disable** masking temporarily if you are trying to find out a Group ID through logs, although using the sensor/service is recommended.
### 5. Passkey Verification Requirement

WhatsApp sometimes requires **passkey verification** (biometrics, PIN, or pattern check on your registered phone) during linked-device setup. Since this is an unofficial client, the native passkey handshake is not fully stable.

- **Effect**: Pairing or reconnection may halt with a "Passkey Required" warning.
- **Fix**: Remove all passkeys from WhatsApp on your phone (**Settings → Account → Passkeys → Remove all passkeys**) to skip the prompt, or use the experimental passkey flow to approve the prompt within 2 minutes.
{: .important }

---

## 🔄 Interaction with other Clients & Disconnection Rules

Since this App acts as a "Linked Device" (similar to WhatsApp Web or Desktop):

- You can still use WhatsApp on your phone as usual.
- Messages sent by the App will appear in your chat history on your phone.
- **The 14-Day Inactivity Rule**: WhatsApp requires your main device (the phone where WhatsApp is registered) to connect to the internet **at least once every 14 days**. If your phone is offline or has no internet connection for more than 14 days, WhatsApp will automatically log out all linked devices (including this Home Assistant App).
- **Device Switches & Re-registration**: If you switch your phone, reinstall WhatsApp on your phone, or re-register WhatsApp (e.g. using a different number or resetting the device), WhatsApp immediately revokes all current linked device sessions. You will need to re-scan the QR code to pair the Home Assistant App again.
- If you manually select "Log out" from the linked devices list on your phone, the App will be disconnected immediately.


---

## 🛡️ Best Practices

1. **Keep it Human**: Don't send hundreds of messages per minute.
2. **Avoid Spam**: Only send messages to people who expect them (family, self-notifications).
3. **Monitor Logs**: If you see frequent disconnects, check your internet stability or try a "Reset Session".
