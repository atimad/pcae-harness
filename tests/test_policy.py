from __future__ import annotations

from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.policy import (
    DEFAULT_PROTECTED_PATTERNS,
    POLICY_SOURCE_DEFAULTS,
    POLICY_SOURCE_REPO,
    load_policy,
    parse_protected_patterns,
)


def test_parse_protected_patterns_from_policy_text() -> None:
    content = """[protected]
patterns = [
  ".env",
  "*.pem",
]
"""

    assert parse_protected_patterns(content) == (".env", "*.pem")


def test_load_policy_reads_repo_policy_file(tmp_path: Path) -> None:
    policy_file = tmp_path / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        """[protected]
patterns = [
  "custom.lock",
]
""",
        encoding="utf-8",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert policy.protected_patterns == ("custom.lock",)
    assert policy.source == POLICY_SOURCE_REPO
    assert policy.file_exists
    assert policy.valid


def test_load_policy_falls_back_to_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.protected_patterns == DEFAULT_PROTECTED_PATTERNS
    assert policy.source == POLICY_SOURCE_DEFAULTS
    assert not policy.file_exists
    assert policy.valid


def test_load_policy_reports_invalid_toml(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected\npatterns = []\n")

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == "Invalid TOML: malformed table header."


def test_load_policy_requires_protected_section(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[other]
patterns = [
  ".env",
]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == "Invalid policy: [protected] section is missing."


def test_load_policy_requires_patterns(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\n")

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == "Invalid policy: protected.patterns is missing."


def test_load_policy_requires_patterns_list(tmp_path: Path) -> None:
    write_policy(tmp_path, '[protected]\npatterns = ".env"\n')

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == "Invalid policy: protected.patterns must be a list."


def test_load_policy_rejects_empty_pattern(tmp_path: Path) -> None:
    write_policy(tmp_path, '[protected]\npatterns = [""]\n')

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: every protected pattern must be a non-empty string."
    )


def test_load_policy_rejects_non_string_pattern(tmp_path: Path) -> None:
    write_policy(tmp_path, "[protected]\npatterns = [42]\n")

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: every protected pattern must be a non-empty string."
    )


def write_policy(root: Path, content: str) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(content, encoding="utf-8")
