from __future__ import annotations

from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.policy import DEFAULT_PROTECTED_PATTERNS, load_policy, parse_protected_patterns


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


def test_load_policy_falls_back_to_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.protected_patterns == DEFAULT_PROTECTED_PATTERNS
