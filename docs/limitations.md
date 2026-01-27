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
{: .important }

- **Recommendation**: Use this integration only for personal notifications or small private bots. Do **not** use it for mass marketing or unsolicited messages.

---

## 📦 Technical Limitations

### 1. One Session per Addon
Currently, one instance of the WhatsApp Addon can only be paired with **one** phone number at a time. If you need to manage multiple numbers, you would need to run multiple addon instances (if supported by your environment).

### 2. Media Uploads
The addon supports sending images, but it requires a **publicly accessible URL** or a URL that the addon container can reach (e.g., your local HA instance). It currently does not support "uploading" local files directly from your PC through the HA frontend into WhatsApp.

### 3. Buttons & Polls (Client Support)
Native WhatsApp Buttons and Polls are relatively new.
- They look great on **Android** and **iOS**.
- They might appear as "text links" or not appear at all on older versions of the **WhatsApp Desktop** app or **WhatsApp Web**.

### 4. Group IDs
Home Assistant doesn't (yet) have a way to list your WhatsApp groups. You must manually find the `@g.us` ID by listening to events. (See [Pro-Tips](tips.md)).

> **Warning**
> **Privacy Mode Warning**: If you enable "Mask Sensitive Data" in the options, Group IDs will also be masked in the logs (e.g. `123*****89@g.us`). You **must disable** masking temporarily if you are trying to find out a Group ID.
{: .warning }

---

## 🔄 Interaction with other Clients
Since this addon acts as a "Linked Device":
- You can still use WhatsApp on your phone as usual.
- Messages sent by the Addon will appear in your chat history on your phone.
- If you log out "All Devices" from your phone, the Addon will also be disconnected.

---

## 🛡️ Best Practices
1.  **Keep it Human**: Don't send hundreds of messages per minute.
2.  **Avoid Spam**: Only send messages to people who expect them (family, self-notifications).
3.  **Monitor Logs**: If you see frequent disconnects, check your internet stability or try a "Reset Session".
