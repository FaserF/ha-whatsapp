"""CI tests for documentation formatting and structure."""

import glob
import re

import pytest

# The documentation engine does not support GitHub-style alerts.
# Example: > [!TIP] will literally render as "[!TIP]"
UNSUPPORTED_ALERTS = re.compile(
    r"\[!(TIP|NOTE|WARNING|CAUTION|IMPORTANT)\]", re.IGNORECASE
)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "filepath",
    list(glob.glob("docs/**/*.md", recursive=True)),
)
def test_documentation_alert_formatting(filepath: str) -> None:
    """Verify that unsupported GitHub alerts are not used in markdown files.

    The documentation site does not render `> [!TIP]` correctly.
    Instead, use standard markdown blockquotes like `> **TIP:**`.
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    errors = []
    for i, line in enumerate(content.splitlines()):
        if UNSUPPORTED_ALERTS.search(line):
            errors.append(f"{filepath}:{i + 1}: Unsupported alert: {line.strip()}")

    if errors:
        error_msg = "\n".join(errors)
        fail_msg = (
            "Unsupported Markdown alerts found.\n"
            "Please use standard Markdown like `> **TIP:**` instead of `> [!TIP]`.\n\n"
            f"{error_msg}"
        )
        pytest.fail(fail_msg)
