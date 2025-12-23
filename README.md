# HA WhatsApp

![WhatsApp Logo](https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg)
<!-- Use a smaller width if possible via HTML, but markdown standard above -->

Home Assistant integration for WhatsApp with Linked Device support (QR Code).

## Features
- 📲 **Linked Device Login**: Scan QR Code to connect.
- 💬 **Send Messages**: Text, Images, Buttons.
- 📊 **Polls**: Create polls directly from HA.
- 📅 **Events**: Create calendar events (Experimental).
- 🌍 **Localization**: English & German support.

## Setup
1. Go to Home Assistant -> Integrations.
2. Add "WhatsApp".
3. Scan the QR Code with your phone (Settings -> Linked Devices).

## Development
This project deals with:
- **Strict Typing**: Python 3.11+
- **Security**: Secret scanning enabled.

### Quick Start
```bash
# Install dependencies
pip install -e .

# Run Tests
pytest
```

## Documentation
See `/docs` for:
- [Architecture](docs/COMPONENT.md)
- [API Reference](docs/API.md)
- [Contributing](docs/CONTRIBUTING.md)
