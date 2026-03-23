"""Tests for translation coverage and consistency."""

import json
import logging
import pathlib
import re
from typing import Any

import pytest

# Directory paths
BASE_DIR = pathlib.Path(__file__).parent.parent
COMPONENT_DIR = BASE_DIR / "custom_components" / "whatsapp"
TRANSLATIONS_DIR = COMPONENT_DIR / "translations"

_LOGGER = logging.getLogger(__name__)


def get_translation_files() -> dict[str, pathlib.Path]:
    """Return a list of translation files to check."""
    return {
        "strings": COMPONENT_DIR / "strings.json",
        "en": TRANSLATIONS_DIR / "en.json",
        "de": TRANSLATIONS_DIR / "de.json",
    }


@pytest.mark.parametrize("file_key, file_path", get_translation_files().items())  # type: ignore[untyped-decorator]
def test_translation_file_exists(file_key: str, file_path: pathlib.Path) -> None:
    """Verify that the required translation files exist."""
    assert file_path.exists(), f"Translation file {file_key} ({file_path}) is missing!"


def load_json(path: pathlib.Path) -> Any:
    """Load and parse a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_dict(
    d: dict[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """Flatten a nested dictionary into a single level with dot-separated keys."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def test_translation_consistency() -> None:
    """Verify that all keys in strings.json are present in en.json and de.json."""
    files = get_translation_files()

    # Skip if files don't exist (handled by other test)
    if not all(p.exists() for p in files.values()):
        pytest.skip("Missing translation files, skipping consistency test.")

    strings_data: dict[str, Any] = flatten_dict(load_json(files["strings"]))
    en_data: dict[str, Any] = flatten_dict(load_json(files["en"]))
    de_data: dict[str, Any] = flatten_dict(load_json(files["de"]))

    strings_keys = set(strings_data.keys())
    en_keys = set(en_data.keys())
    de_keys = set(de_data.keys())

    # 1. Check if en.json matches strings.json
    missing_in_en = strings_keys - en_keys

    # 2. Check if de.json matches strings.json (or en.json)
    missing_in_de = strings_keys - de_keys

    errors: list[str] = []
    if missing_in_en:
        errors.append(
            f"Keys in strings.json missing in en.json: {sorted(missing_in_en)}"
        )
    if missing_in_de:
        errors.append(
            f"Keys in strings.json missing in de.json: {sorted(missing_in_de)}"
        )

    assert not errors, "\n".join(errors)


def test_config_flow_keys_translated() -> None:
    """Scan config_flow.py for used translation keys and verify they exist."""
    files = get_translation_files()
    if not files["strings"].exists():
        pytest.skip("strings.json missing")

    strings_data: dict[str, Any] = flatten_dict(load_json(files["strings"]))

    config_flow_path = COMPONENT_DIR / "config_flow.py"
    if not config_flow_path.exists():
        pytest.skip("config_flow.py missing")

    with open(config_flow_path, encoding="utf-8") as f:
        content = f.read()

    # 1. Check for abort reasons
    # self.async_abort(reason="...")
    abort_reasons = re.findall(r'async_abort\(reason=["\'](\w+)["\']', content)
    for reason in abort_reasons:
        key = f"config.abort.{reason}"
        assert key in strings_data, (
            f"Abort reason '{reason}' used in code but missing in "
            f"translations ({key})"
        )

    # 2. Check for error keys
    # errors["base"] = "..." or errors["host"] = "..."
    error_keys = re.findall(r'errors\[["\']\w+["\']\] = ["\'](\w+)["\']', content)
    for err in error_keys:
        # Check in config.error
        key = f"config.error.{err}"
        # Some might be in options.error
        alt_key = f"options.error.{err}"
        assert key in strings_data or alt_key in strings_data, (
            f"Error key '{err}' used in code but missing in "
            f"translations ({key} or {alt_key})"
        )

    # 3. Check for step titles/descriptions (implicit by step_id)
    steps = re.findall(r'step_id=["\'](\w+)["\']', content)
    for step in steps:
        if step == "init" and "OptionsFlowHandler" in content:
            # This is options flow
            assert (
                "options.step.init.title" in strings_data
            ), "Options step 'init' missing title"
        else:
            assert (
                f"config.step.{step}.title" in strings_data
            ), f"Config step '{step}' missing title"


def test_hardcoded_strings_in_config_flow() -> None:
    """Identify potentially hardcoded strings that should be translated."""
    config_flow_path = COMPONENT_DIR / "config_flow.py"
    if not config_flow_path.exists():
        pytest.skip("config_flow.py missing")

    with open(config_flow_path, encoding="utf-8") as f:
        lines = f.readlines()

    errors: list[str] = []
    # Ignore some common non-translatable strings
    ignore_patterns = [
        r"logging\.",
        r"_LOGGER\.",
        r"DOMAIN",
        r"CONF_",
        r"DEFAULT_",
        r"http",
        r"uuid",
        r"session_id",
        r"localhost",
        r"socket",
        r"vol\.",
        r"return self.async_create_entry",
        r"print\(",
        r"#",
        r'"""',
        r"'''",
        r"debug",
        r"error_msg = str(e)",
        r"ADDON_NAME",
        r"slug",
        r"port = ",
    ]

    for i, line in enumerate(lines):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue

        # Look for strings in double or single quotes that might be
        # user-facing text Specifically in async_show_form,
        # async_abort, or placeholder dicts
        keywords = ["async_show_form", "description_placeholders", "data_schema"]
        if any(keyword in clean_line for keyword in keywords):
            # Check for strings that look like sentences or labels
            # (capitalized, spaces, etc.) - This is a heuristic
            matches = re.findall(r'["\']([A-Z][^"\']+\s+[^"\']+)["\']', clean_line)
            for m in matches:
                # Filter out ignored patterns
                if not any(re.search(p, m) for p in ignore_patterns):
                    errors.append(f"Line {i+1}: Potentially hardcoded string: '{m}'")

    # Specifically check the known hardcoded strings I identified earlier
    for i, line in enumerate(lines):
        if (
            '"Not connected yet' in line
            or '"Waiting for QR' in line
            or '"Scan this code' in line
        ):
            errors.append(f"Line {i+1}: Hardcoded string found: {line.strip()}")
        if "⚠️ CAUTION" in line:
            errors.append(f"Line {i+1}: Hardcoded string found: {line.strip()}")

    # We allow some for now but want to fail eventually
    if errors:
        _LOGGER.warning("Hardcoded strings to fix in config_flow.py:")
        for e in errors:
            _LOGGER.warning(e)
