# AI Agent Reference for ha-whatsapp

---

## Token Efficiency Rules (CRITICAL — Read First)

These rules apply to **every response** without exception:

1. **Output minimal prose.** Bullet points only. No introductory sentences, no filler, no "Great question!", no "As requested".
2. **No walkthrough unless explicitly asked.** Never create or update `walkthrough.md` unless the user writes "walkthrough" or "summary" in their request.
3. **No implementation plan unless complex.** Skip planning artifacts for simple tweaks, single-file edits, bug fixes, or minor features. Plan only for major architectural changes.
4. **Short change summaries only.** After making changes, output ≤5 bullet points describing *what* changed and *why* — never a line-by-line description.
5. **No repeating file content.** Never echo back code you just wrote or edited. Reference filenames with links instead.
6. **No tool-call narration.** Do not describe what tool you are about to call. Just call it.
7. **Targeted file reads only.** Use `grep_search` or `view_file` with `StartLine`/`EndLine` to read only the relevant section. Never view an entire large file unless strictly necessary.
8. **Parallel tool calls.** Fire all independent tool calls in a single block. Never sequence calls that can run simultaneously.
9. **No re-summarizing artifacts.** After creating or updating an artifact, do NOT restate its contents — just link to it and note any open questions.
10. **Skip trivial confirmations.** Do not ask "Would you like me to proceed?" for obvious next steps. Just do them.
11. **No closing pleasantries.** End your response after the change summary. No "Let me know if you have questions!" etc.
12. **Suppress test output noise.** When running pytest, only report failures. Do not paste successful test output unless requested.
13. **Delegate with subagents.** For any research-heavy, multi-file, or parallelizable task, spin up a subagent instead of doing it inline. This keeps your own context lean and reduces token usage for the main conversation.
14. **Reuse idle subagents.** Send follow-up instructions to an already-running subagent via `send_message` — never spawn a new one for the same task thread.
15. **Don't poll subagents.** After launching a subagent, stop calling tools. The system wakes you automatically when the subagent replies.
16. **Subagent scope = minimal.** Give each subagent one focused goal. Never dump the entire task into a single subagent prompt.
17. **Prefer `research` subagent for read-only work.** Codebase exploration, grep searches, file reads, and web lookups should go to the `research` subagent so the main agent stays focused on writing code.
18. **Prefer `self` subagent for isolated execution.** Use the `self` subagent for tasks that need write access in a separate context (e.g. branch workspace edits, test runs, parallel fixes on different modules).

---

## Subagent Strategy (Antigravity 2.0)

Use subagents proactively whenever a task has independent subtasks, requires heavy research, or would bloat the main context:

| Scenario | Action |
|---|---|
| Reading/searching codebase before coding | Delegate to `research` subagent |
| Parallel bug fixes across multiple modules | Spawn one `self` subagent per module with `branch` workspace |
| Exploring docs / web while coding continues | Delegate to `research` subagent, continue main task |
| Running tests after a fix | Delegate to `self` subagent, await result |

**Workspace modes:**

- `inherit` — shares parent workspace (default, for read or simple edits)
- `branch` — isolated copy (for concurrent writes to same files)
- `share` — shared repo, independent branch (for parallel feature work)

---

## Codebase Architecture (Home Assistant Integration)

### Core Component (`custom_components/whatsapp`)

| Area | File | Description |
|---|---|---|
| Integration Entry | `custom_components/whatsapp/__init__.py` | Setup, unload, service registration, reload handlers |
| API Client | `custom_components/whatsapp/api.py` | Communication bridge with WhatsApp (Baileys / REST endpoint) |
| Coordinator | `custom_components/whatsapp/coordinator.py` | Home Assistant `DataUpdateCoordinator` for polling/push status |
| Config Flow | `custom_components/whatsapp/config_flow.py` | UI config, re-auth, options flow |
| Constants | `custom_components/whatsapp/const.py` | Domain, default config, event names |
| Helpers | `custom_components/whatsapp/helpers.py` | Common utility functions & helpers |
| Repairs | `custom_components/whatsapp/repairs.py` | HA Repair flow handlers |
| Types | `custom_components/whatsapp/types.py` | TypedDicts and type definitions |

### Entity Platforms

| Platform | File | Description |
|---|---|---|
| Sensors | `custom_components/whatsapp/sensor.py` | Connection status, message counters, state sensors |
| Binary Sensors | `custom_components/whatsapp/binary_sensor.py` | Online/offline states, connectivity checks |
| Buttons | `custom_components/whatsapp/button.py` | Action buttons (e.g. reconnect, QR code request) |
| Notifications | `custom_components/whatsapp/notify.py` | HA `notify` service implementation for WhatsApp |

### UI & Service Definitions

| Area | File | Description |
|---|---|---|
| Service Schemas | `custom_components/whatsapp/services.yaml` | HA custom service parameters & descriptions |
| Translations | `custom_components/whatsapp/strings.json`, `custom_components/whatsapp/translations/` | English/German translation strings |
| Manifest | `custom_components/whatsapp/manifest.json` | HA Integration manifest metadata & dependencies |

---

## CLI Commands

| Task | Command | Directory |
|---|---|---|
| Run all tests | `.venv\Scripts\pytest.exe` | Root |
| Run specific test | `.venv\Scripts\pytest.exe tests/test_config_flow.py` | Root |
| Ruff linter | `.venv\Scripts\ruff.exe check custom_components tests --fix` | Root |
| Ruff formatter | `.venv\Scripts\ruff.exe format custom_components tests` | Root |
| MyPy type check | `.venv\Scripts\mypy.exe custom_components` | Root |

---

## Coding & Quality Standards

### Python & Home Assistant Standards

- **Traceback Preservation**: NEVER use `raise e`. ALWAYS use `raise ... from e` or a naked `raise` to prevent stack trace destruction.
- **Silent Failure Prohibition**: `except: pass` is FORBIDDEN. All exceptions must be wrapped and propagated, or logged with context (`_LOGGER.warning("Failed to parse X: %s", e)`).
- **Async Pattern**: All network requests and async calls MUST be properly awaited using HA `async_` patterns and aiohttp session.
- **Type Annotations**: Provide 100% type hints compatible with `mypy`.
- **String Localization**: All user-facing strings must be in `strings.json` and mirrored in `translations/de.json`.

### Testing

- **Always run only specific test file(s)** relevant to the change when iterating.
- Only report failures in output; suppress verbose successful test output.

---

## Language Rules

- **Codebase & Documentation**: All program code, configuration files, documentation, READMEs, and inline comments must always be written in English (EN), unless explicitly requested otherwise.
- **AI Chat Interactions**: The AI must respond in English (EN) by default, unless the user explicitly requests another language.
