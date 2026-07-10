"""
Fast-green marker auto-application (Phase 88N.5).

Tests in FAST_GREEN_MODULES are automatically marked ``fast_green``.  The
set was chosen to cover high-signal PCAE governance invariants while staying
well under 60 seconds with ``-n auto``.  It excludes:

- subprocess-heavy tests without the slow marker (governance-info commands:
  test_governance_timeline, test_decision_log, test_risk_register,
  test_project_state) — those run one subprocess per xdist worker but still
  total ~2:25 for the group.
- test_agent (4 236 tests, ~2:06, includes capsys-bound capability-discovery
  tests that cannot be effectively parallelised).
- test_phase (886 tests, ~25 s, exhaustive command-catalog not required for
  the normal development gate).
- All ``slow`` / ``integration`` / ``phase_closure`` marked files — those
  spawn a pcae subprocess per test and are never suitable for a fast gate.

Invocation:

    python -m pytest -m "fast_green" -n auto -ra --durations=50
"""

from __future__ import annotations

import os

import pytest


# Phase 134B.1 — ordinary automated tests must never inherit the operator's
# live outbound-notification configuration.  In-process production functions
# and subprocess CLIs both resolve notification configuration from os.environ,
# so isolating only individual sink tests is insufficient: any unrelated test
# that calls finalize_phase_report() can otherwise reach the live adapter when
# pytest itself was started from a shell that sourced telegram.env.
_EXTERNAL_NOTIFICATION_ENV = (
    "PCAE_NOTIFY_ENABLED",
    "PCAE_NOTIFY_SINKS",
    "PCAE_TELEGRAM_ENABLED",
    "PCAE_TELEGRAM_BOT_TOKEN",
    "PCAE_TELEGRAM_CHAT_ID",
)
_LIVE_NOTIFICATION_TEST_OPT_IN = "PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS"

# Phase 134B.3 — the governed configuration resolver (pcae.core.
# notification_config) auto-loads real delivery configuration from
# ~/.config/pcae/notify.json for every `pcae` CLI invocation, including
# ones a test spawns as a subprocess. Deleting only the five known
# environment-variable names (below) is no longer sufficient on its own:
# a subprocess's own CLI entrypoint would simply reload them from the
# governed file. This explicit disable flag is the resolver's own,
# unconditional escape hatch -- set for the whole isolated test session and
# inherited by every subprocess, exactly like the five env vars already are.
_NOTIFICATION_CONFIG_DISABLE_ENV = "PCAE_NOTIFY_CONFIG_DISABLE"


def isolate_external_notification_env(env: dict[str, str]) -> bool:
    """Remove live-delivery configuration unless explicitly test-authorized.

    Returns True when isolation was applied.  The explicit opt-in is intended
    only for separately governed live integration runs; normal unit/regression
    suites never set it.  Production code is untouched.
    """
    if str(env.get(_LIVE_NOTIFICATION_TEST_OPT_IN, "")).lower() in (
        "1", "true", "yes",
    ):
        return False
    for key in _EXTERNAL_NOTIFICATION_ENV:
        env.pop(key, None)
    env[_NOTIFICATION_CONFIG_DISABLE_ENV] = "1"
    return True


@pytest.fixture(autouse=True)
def _isolate_external_notifications(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail-safe test boundary for in-process and inherited subprocess env."""
    if str(os.environ.get(_LIVE_NOTIFICATION_TEST_OPT_IN, "")).lower() in (
        "1", "true", "yes",
    ):
        return
    for key in _EXTERNAL_NOTIFICATION_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(_NOTIFICATION_CONFIG_DISABLE_ENV, "1")

FAST_GREEN_MODULES: frozenset[str] = frozenset({
    # Core governance safety
    "test_check",
    "test_health",
    "test_hook_bypass_policy",
    "test_hooks",
    "test_policy",
    "test_ci",
    # 88N.2 feature: test-run preflight
    "test_doctor_test_run",
    # Task / session lifecycle
    "test_task",
    "test_session",
    "test_task_memory_reconciliation",
    # Lifecycle state machine and gates
    "test_lifecycle_state_machine",
    "test_lifecycle_gate_approval",
    "test_lifecycle_gate_runner_dry_run",
    "test_lifecycle_next_command",
    "test_lifecycle_status_command",
    "test_lifecycle_summary_command",
    # Project structure and commands
    "test_init",
    "test_inspect",
    "test_docs",
    "test_repo",
    # Architecture zone enforcement
    "test_architecture",
    # Strategic and provenance
    "test_strategic_lineage",
    "test_provenance",
    # Governance artefacts (in-process read)
    "test_artifact_index",
    "test_artifact_metadata_consistency",
    "test_memory_snapshot",
    # Status, context, orchestration
    "test_status",
    "test_context",
    "test_orchestration",
    # Utility / command smoke
    "test_analytics",
    "test_import",
    "test_daemon",
    "test_fleet",
    "test_pipeline",
    "test_export",
    "test_review",
    # 88N.5 self-verification
    "test_88n5_fast_green_validation",
    # 88P shell gate prototype
    "test_shell_gate",
    # 88Q shell gate test matrix
    "test_shell_gate_matrix",
})


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    fast_green = pytest.mark.fast_green
    for item in items:
        module_name = item.module.__name__.split(".")[-1]
        if module_name in FAST_GREEN_MODULES:
            item.add_marker(fast_green)
