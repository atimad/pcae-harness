from __future__ import annotations

from pathlib import Path

from pcae.core.paths import HarnessPath
from pcae.core.policy import (
    ARCHITECTURE_ENFORCEMENT_ADVISORY,
    ARCHITECTURE_ENFORCEMENT_STRICT,
    DEFAULT_AGENT_STALE_AFTER_SECONDS,
    DEFAULT_ARCHITECTURE_RULES,
    DEFAULT_ARCHITECTURE_ZONES,
    DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS,
    DEFAULT_PROTECTED_PATTERNS,
    POLICY_SOURCE_DEFAULTS,
    POLICY_SOURCE_REPO,
    load_policy,
    parse_lifecycle_review_require_approved,
    parse_policy,
    parse_protected_patterns,
    render_default_policy,
)


def test_parse_protected_patterns_from_policy_text() -> None:
    content = """[protected]
patterns = [
  ".env",
  "*.pem",
]
"""

    assert parse_protected_patterns(content) == (".env", "*.pem")


def test_parse_policy_reads_architecture_zones() -> None:
    content = """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]
docs = ["docs/**", "*.md"]
"""

    policy = parse_policy(content)

    assert policy.protected_patterns == (".env",)
    assert policy.architecture_zones == {
        "core": ("src/pcae/core/**",),
        "docs": ("docs/**", "*.md"),
    }
    assert policy.architecture_rules == {}
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY


def test_parse_policy_reads_architecture_rules() -> None:
    content = """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]
commands = ["src/pcae/commands/**"]
tests = ["tests/**"]

[architecture.rules]
core = ["core"]
commands = ["core", "commands"]
tests = ["*"]
"""

    policy = parse_policy(content)

    assert policy.architecture_rules == {
        "core": ("core",),
        "commands": ("core", "commands"),
        "tests": ("*",),
    }
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY


def test_parse_policy_reads_architecture_enforcement_mode() -> None:
    content = """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = ["core"]

[architecture.enforcement]
mode = "strict"
"""

    policy = parse_policy(content)

    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_STRICT


def test_parse_policy_reads_agent_stale_after_seconds() -> None:
    content = """[protected]
patterns = [
  ".env",
]

[agent]
stale_after_seconds = 7200
"""

    policy = parse_policy(content)

    assert policy.agent_stale_after_seconds == 7200


def test_parse_policy_reads_daemon_watch_interval_seconds() -> None:
    content = """[protected]
patterns = [
  ".env",
]

[daemon]
watch_interval_seconds = 120
"""

    policy = parse_policy(content)

    assert policy.daemon_watch_interval_seconds == 120


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
    assert policy.architecture_zones == {}
    assert policy.architecture_rules == {}
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY
    assert policy.agent_stale_after_seconds == DEFAULT_AGENT_STALE_AFTER_SECONDS
    assert policy.daemon_watch_interval_seconds == DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS
    assert policy.source == POLICY_SOURCE_REPO
    assert policy.file_exists
    assert policy.valid


def test_load_policy_reads_architecture_zones_from_repo_policy_file(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]
commands = ["src/pcae/commands/**"]
"""
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.architecture_zones == {
        "core": ("src/pcae/core/**",),
        "commands": ("src/pcae/commands/**",),
    }
    assert policy.architecture_rules == {}
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY
    assert policy.agent_stale_after_seconds == DEFAULT_AGENT_STALE_AFTER_SECONDS
    assert policy.daemon_watch_interval_seconds == DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS


def test_load_policy_reads_architecture_rules_from_repo_policy_file(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]
commands = ["src/pcae/commands/**"]

[architecture.rules]
core = ["core"]
commands = ["core", "commands"]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.architecture_rules == {
        "core": ("core",),
        "commands": ("core", "commands"),
    }
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY


def test_load_policy_reads_architecture_enforcement_mode(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [
  ".env",
]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = ["core"]

[architecture.enforcement]
mode = "strict"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_STRICT


def test_load_policy_falls_back_to_defaults_when_missing(tmp_path: Path) -> None:
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.protected_patterns == DEFAULT_PROTECTED_PATTERNS
    assert policy.architecture_zones == {}
    assert policy.architecture_rules == {}
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY
    assert policy.source == POLICY_SOURCE_DEFAULTS
    assert not policy.file_exists
    assert policy.valid
    assert policy.agent_stale_after_seconds == DEFAULT_AGENT_STALE_AFTER_SECONDS
    assert policy.daemon_watch_interval_seconds == DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS


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


def test_load_policy_rejects_non_list_architecture_zone(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = "src/pcae/core/**"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture zone 'core' patterns must be a list."
    )


def test_load_policy_rejects_empty_architecture_zone_name(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
"" = ["src/pcae/core/**"]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture zone names must be non-empty strings."
    )


def test_load_policy_rejects_empty_architecture_zone_pattern(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = [""]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture zone patterns must be non-empty strings."
    )


def test_load_policy_rejects_empty_architecture_zone(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = []
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture zone 'core' patterns must contain patterns."
    )


def test_load_policy_rejects_non_list_architecture_rule(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = "core"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture rule 'core' targets must be a list."
    )


def test_load_policy_rejects_empty_architecture_rule_source(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
"" = ["core"]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture zone names must be non-empty strings."
    )


def test_load_policy_rejects_empty_architecture_rule_target(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = [""]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture rule targets must be non-empty strings."
    )


def test_load_policy_rejects_empty_architecture_rule_targets(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = []
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture rule 'core' targets must contain zones."
    )


def test_load_policy_rejects_rule_for_unknown_source_zone(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
commands = ["core"]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture rule source 'commands' "
        "must exist in architecture.zones."
    )


def test_load_policy_rejects_rule_for_unknown_target_zone(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.zones]
core = ["src/pcae/core/**"]

[architecture.rules]
core = ["commands"]
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture rule 'core' references "
        "unknown target zone 'commands'."
    )


def test_load_policy_rejects_invalid_architecture_enforcement_mode(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.enforcement]
mode = "blocking"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture.enforcement.mode must be "
        "'advisory' or 'strict'."
    )


def test_load_policy_rejects_non_string_architecture_enforcement_mode(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[architecture.enforcement]
mode = 42
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: architecture.enforcement.mode must be a string."
    )


def test_load_policy_rejects_non_integer_agent_stale_threshold(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[agent]
stale_after_seconds = "soon"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: agent.stale_after_seconds must be a positive integer."
    )


def test_load_policy_rejects_zero_agent_stale_threshold(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[agent]
stale_after_seconds = 0
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: agent.stale_after_seconds must be a positive integer."
    )


def test_load_policy_rejects_non_integer_daemon_watch_interval(
    tmp_path: Path,
) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[daemon]
watch_interval_seconds = "soon"
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: daemon.watch_interval_seconds must be a positive integer."
    )


def test_load_policy_rejects_zero_daemon_watch_interval(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        """[protected]
patterns = [".env"]

[daemon]
watch_interval_seconds = 0
""",
    )

    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error == (
        "Invalid policy: daemon.watch_interval_seconds must be a positive integer."
    )


def test_rendered_default_policy_includes_architecture_zones(tmp_path: Path) -> None:
    write_policy(tmp_path, render_default_policy())

    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.architecture_zones == DEFAULT_ARCHITECTURE_ZONES
    assert policy.architecture_rules == DEFAULT_ARCHITECTURE_RULES
    assert policy.architecture_enforcement_mode == ARCHITECTURE_ENFORCEMENT_ADVISORY
    assert policy.agent_stale_after_seconds == DEFAULT_AGENT_STALE_AFTER_SECONDS
    assert policy.daemon_watch_interval_seconds == DEFAULT_DAEMON_WATCH_INTERVAL_SECONDS


# ---------------------------------------------------------------------------
# orchestration policy parsing
# ---------------------------------------------------------------------------


def test_policy_orchestration_defaults_when_section_missing(tmp_path: Path) -> None:
    from pcae.core.policy import (
        DEFAULT_ORCHESTRATION_DEFAULT_AGENT,
        DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT,
        DEFAULT_ORCHESTRATION_RUNTIME_AGENT,
        DEFAULT_ORCHESTRATION_VALIDATION_AGENT,
    )

    write_policy(tmp_path, '[protected]\npatterns = [".env"]\n')
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.orchestration.default_agent == DEFAULT_ORCHESTRATION_DEFAULT_AGENT
    assert policy.orchestration.documentation_agent == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
    assert policy.orchestration.runtime_agent == DEFAULT_ORCHESTRATION_RUNTIME_AGENT
    assert policy.orchestration.validation_agent == DEFAULT_ORCHESTRATION_VALIDATION_AGENT


def test_policy_orchestration_reads_overrides(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[orchestration]\ndefault_agent = "opus"\nruntime_agent = "codex-turbo"\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.orchestration.default_agent == "opus"
    assert policy.orchestration.runtime_agent == "codex-turbo"


def test_policy_orchestration_rejects_empty_agent_string(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[orchestration]\ndefault_agent = ""\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error is not None
    assert "orchestration.default_agent" in policy.error


def test_policy_orchestration_rejects_non_string_agent(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[orchestration]\ndefault_agent = 42\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid


def test_rendered_default_policy_includes_orchestration_section(tmp_path: Path) -> None:
    from pcae.core.policy import (
        DEFAULT_ORCHESTRATION_DEFAULT_AGENT,
        DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT,
        DEFAULT_ORCHESTRATION_RUNTIME_AGENT,
        DEFAULT_ORCHESTRATION_VALIDATION_AGENT,
    )

    write_policy(tmp_path, render_default_policy())
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.orchestration.default_agent == DEFAULT_ORCHESTRATION_DEFAULT_AGENT
    assert policy.orchestration.documentation_agent == DEFAULT_ORCHESTRATION_DOCUMENTATION_AGENT
    assert policy.orchestration.runtime_agent == DEFAULT_ORCHESTRATION_RUNTIME_AGENT
    assert policy.orchestration.validation_agent == DEFAULT_ORCHESTRATION_VALIDATION_AGENT


# ---------------------------------------------------------------------------
# agent registry parsing
# ---------------------------------------------------------------------------


def test_policy_agent_registry_defaults_when_section_missing(tmp_path: Path) -> None:
    from pcae.core.policy import DEFAULT_AGENT_REGISTRY

    write_policy(tmp_path, '[protected]\npatterns = [".env"]\n')
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert policy.agent_registry == DEFAULT_AGENT_REGISTRY


def test_policy_agent_registry_reads_single_agent(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[agents.my-agent]\nkind = "claude"\nroles = ["analysis"]\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert len(policy.agent_registry) == 1
    entry = policy.agent_registry[0]
    assert entry.agent_id == "my-agent"
    assert entry.kind == "claude"
    assert entry.roles == ("analysis",)


def test_policy_agent_registry_reads_multiple_agents(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n'
        '[agents.a]\nkind = "ka"\nroles = ["r1"]\n\n'
        '[agents.b]\nkind = "kb"\nroles = ["r2", "r3"]\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    assert len(policy.agent_registry) == 2
    assert policy.agent_registry[0].agent_id == "a"
    assert policy.agent_registry[1].agent_id == "b"
    assert policy.agent_registry[1].roles == ("r2", "r3")


def test_policy_agent_registry_rejects_empty_kind(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[agents.x]\nkind = ""\nroles = ["r"]\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error is not None
    assert "kind" in policy.error


def test_policy_agent_registry_rejects_empty_roles_list(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[agents.x]\nkind = "k"\nroles = []\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid


def test_policy_agent_registry_rejects_missing_kind(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[agents.x]\nroles = ["r"]\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error is not None
    assert "kind" in policy.error


def test_policy_agent_registry_rejects_missing_roles(tmp_path: Path) -> None:
    write_policy(
        tmp_path,
        '[protected]\npatterns = [".env"]\n\n[agents.x]\nkind = "k"\n',
    )
    policy = load_policy(HarnessPath(tmp_path))

    assert not policy.valid
    assert policy.error is not None
    assert "roles" in policy.error


def test_rendered_default_policy_includes_agent_registry(tmp_path: Path) -> None:
    from pcae.core.policy import DEFAULT_AGENT_REGISTRY

    write_policy(tmp_path, render_default_policy())
    policy = load_policy(HarnessPath(tmp_path))

    assert policy.valid
    ids = {e.agent_id for e in policy.agent_registry}
    assert "claude-local" in ids
    assert "codex-local" in ids
    assert "pcae-native" in ids
    assert len(policy.agent_registry) == len(DEFAULT_AGENT_REGISTRY)


# --- Phase 70T: lifecycle review policy ---


def test_parse_lifecycle_review_require_approved_true() -> None:
    content = """[protected]
patterns = [".env"]

[lifecycle_review]
require_approved = true
"""
    assert parse_lifecycle_review_require_approved(content) is True


def test_parse_lifecycle_review_require_approved_false() -> None:
    content = """[protected]
patterns = [".env"]

[lifecycle_review]
require_approved = false
"""
    assert parse_lifecycle_review_require_approved(content) is False


def test_parse_lifecycle_review_absent_defaults_false() -> None:
    content = """[protected]
patterns = [".env"]
"""
    assert parse_lifecycle_review_require_approved(content) is False


def test_parse_lifecycle_review_invalid_value() -> None:
    content = """[protected]
patterns = [".env"]

[lifecycle_review]
require_approved = "yes"
"""
    import pytest
    with pytest.raises(ValueError, match="must be true or false"):
        parse_lifecycle_review_require_approved(content)


def test_load_policy_with_lifecycle_review_required(tmp_path: Path) -> None:
    write_policy(tmp_path, render_default_policy() + "\n[lifecycle_review]\nrequire_approved = true\n")
    policy = load_policy(HarnessPath(tmp_path))
    assert policy.lifecycle_review_require_approved is True


def test_load_policy_default_lifecycle_review_false(tmp_path: Path) -> None:
    policy = load_policy(HarnessPath(tmp_path))
    assert policy.lifecycle_review_require_approved is False


def test_parse_policy_includes_lifecycle_review_field() -> None:
    content = render_default_policy() + "\n[lifecycle_review]\nrequire_approved = true\n"
    parsed = parse_policy(content)
    assert parsed.lifecycle_review_require_approved is True


def write_policy(root: Path, content: str) -> None:
    policy_file = root / ".pcae" / "policy.toml"
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(content, encoding="utf-8")
