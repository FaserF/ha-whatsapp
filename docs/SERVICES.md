# ✉️ Services & Actions

The `whatsapp` integration provides several powerful services to interact with WhatsApp.

## 1. Send Message (`whatsapp.send_message`)
Sends a standard text message to a specific number.

**Parameters:**
- `target` (Required): The phone number in international format `+49...`.
- `message` (Required): The content of the message.

**YAML Example:**
```yaml
service: whatsapp.send_message
data:
  target: "+4915112345678"
  message: "🚨 The Alarm has been triggered!"
```

---

## 2. Send Image (`whatsapp.send_image`)
Sends an image file from your Home Assistant instance.

**Parameters:**
- `target` (Required): The phone number.
- `image_path` (Required): Absolute path or generic path allowed by HA (e.g., `/config/www/snapshot.jpg`).
- `caption` (Optional): A text caption for the image.

**YAML Example:**
```yaml
service: whatsapp.send_image
data:
  target: "+4915112345678"
  image_path: "/config/www/cam_snapshot.jpg"
  caption: "Front Door Camera 📷"
```

---

## 3. Send Poll (`whatsapp.send_poll`)
Creates a voting poll in a chat. This is excellent for family decisions (e.g., "What's for dinner?").

**Parameters:**
- `target` (Required): The phone number or group ID.
- `question` (Required): The main question text.
- `options` (Required): A list of options (max 12).

**YAML Example:**
```yaml
service: whatsapp.send_poll
data:
  target: "+4915112345678"
  question: "What should the thermostat be set to?"
  options:
    - "19°C ❄️"
    - "21°C 🌡️"
    - "23°C 🔥"
```

---

## 4. Send Buttons (coming soon)
*Note: This feature depends on the underlying library support for "Interactive Messages".*
