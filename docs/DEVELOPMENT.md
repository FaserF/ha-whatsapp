# 👨‍💻 Development Guide

## Architecture

This integration follows the standard `custom_component` structure but employs modern "Hexagonal" principles where possible:

- **`api.py`**: Acts as the interface (Port) to the WhatsApp Protocol. Currently a mock, but designed to be swapped with a real library (e.g., `whatsapp-web.js` wrapper or python alternative).
- **`config_flow.py`**: Handles the UI-based setup using Home Assistant's Data Entry Flow.
- **`__init__.py`**: The composition root. Wired up services and event listeners.

## Tooling

We use a strict DevOps pipeline:

- **Ruff**: For linting and formatting (Fast, Rust-based).
- **Mypy**: For static type checking (Strict mode).
- **Pytest**: For unit testing.

### Commands

**Run Linter:**
```bash
ruff check .
```

**Run Tests:**
```bash
pytest tests/
```

## Contributing

1. Fork the repository.
2. Create a branch: `feat/amazing-feature`.
3. Commit your changes (we use **Conventional Commits**!).
   - `feat: add button support`
   - `fix: crash on image upload`
4. Open a Pull Request.
5. Our "Janitor" bot will automatically check your code and even fix simple linting errors for you!
