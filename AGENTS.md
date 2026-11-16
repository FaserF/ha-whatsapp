# AI Agent Reference: ha-whatsapp

## 1. Rules & Token Efficiency
- Output: Bullet points only (<=5 items for changes), no pleasantries/filler/narration, default English (EN).
- Code/Files: Targeted reads (`StartLine`/`EndLine`). Markdown links only, no code echo. No unrequested plans/walkthroughs.
- Tests/Linters: Report failures only. Run specific test files (`pytest tests/<test_file>.py`).

## 2. Architecture (`custom_components/whatsapp`)
- `__init__.py`: Setup, unload, service registration, reload handlers.
- `api.py`: Baileys / REST WhatsApp bridge.
- `coordinator.py`: HA `DataUpdateCoordinator`.
- `config_flow.py`: UI configuration, re-auth, options flow.
- `notify.py`, `sensor.py`, `binary_sensor.py`, `button.py`: HA entity platforms.
- `strings.json`, `translations/`: UI localization (EN/DE).

## 3. Coding & HA Standards
- **Async Pattern**: All I/O must use HA `async_` patterns and `async_get_clientsession(hass)`.
- **Hygiene**: No `raise e` (use `raise ... from e` or naked `raise`). `except: pass` strictly forbidden.
- **Typing**: 100% type hints for mypy.
- **Strings**: All user-facing strings in `strings.json` and mirrored in `translations/de.json`.

## 4. CLI Commands
- Run test: `pytest tests/test_config_flow.py`
- Lint: `ruff check custom_components tests --fix && mypy custom_components`
- Format: `ruff format custom_components tests`
