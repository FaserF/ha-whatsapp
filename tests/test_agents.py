"""Tests validating AGENTS.md rules, guidelines, and referenced architecture."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = REPO_ROOT / "AGENTS.md"


def test_agents_markdown_exists_and_not_empty() -> None:
    """Ensure AGENTS.md exists at repository root and has content."""
    assert AGENTS_MD.is_file(), "AGENTS.md must exist at root"
    content = AGENTS_MD.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "AGENTS.md must not be empty"


def test_agents_referenced_files_exist() -> None:
    """Ensure all core files and platforms referenced in AGENTS.md actually exist."""
    content = AGENTS_MD.read_text(encoding="utf-8")
    # Match backticked paths like `custom_components/whatsapp/...`
    referenced_paths = set(re.findall(r"`(custom_components/[^`]+)`", content))

    assert referenced_paths, "Expected referenced file paths in AGENTS.md"
    for rel_path in referenced_paths:
        full_path = REPO_ROOT / rel_path
        msg = f"Path '{rel_path}' referenced in AGENTS.md does not exist"
        assert full_path.exists(), msg


def test_agents_no_unsupported_markdown_alerts() -> None:
    """Ensure AGENTS.md adheres to standard markdown without broken alert syntax."""
    unsupported_alerts = re.compile(
        r"\[!(TIP|NOTE|WARNING|CAUTION|IMPORTANT)\]", re.IGNORECASE
    )
    content = AGENTS_MD.read_text(encoding="utf-8")

    errors = [
        f"Line {idx + 1}: {line.strip()}"
        for idx, line in enumerate(content.splitlines())
        if unsupported_alerts.search(line)
    ]
    assert not errors, f"Unsupported markdown alerts in AGENTS.md: {errors}"
