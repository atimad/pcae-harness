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


_NOTIFICATION_RECEIPTS_DIR_ENV = "PCAE_NOTIFICATION_RECEIPTS_DIR"


@pytest.fixture(autouse=True)
def _isolate_notification_receipts_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Phase ...1.1R.1R — a unit test that constructs `TelegramSink` with
    explicit `bot_token`/`chat_id`/`enabled=True` (bypassing the env-based
    disable above by design, so the sink's own logic can be exercised
    deterministically against a fake `_opener`) now also durably persists
    a notification-receipt JSON file per Telegram operation. Without this
    isolation, every such ordinary unit test run would write real files
    into this repository's own `.pcae/notification-receipts/` (relative
    to cwd) purely as a side effect of running the test suite -- exactly
    the kind of ordinary-test-mutates-real-repo-state leak `_isolate_
    external_notifications` above already exists to prevent for live
    delivery. Individual tests that want to assert on receipt content
    still override this by setting the same env var themselves (which
    simply takes precedence for that test)."""
    monkeypatch.setenv(_NOTIFICATION_RECEIPTS_DIR_ENV, str(tmp_path / "notification-receipts"))


# Phase 135K — the shadow CLTR observer (pcae.cltr.shadow) writes to
# ``.pcae/cltr-shadow/`` (relative to cwd) whenever ``PCAE_CLTR_SHADOW_
# ENABLED`` is set, from inside ``run_finalization_transaction()``. Tests
# that exercise finalization without an isolated cwd would otherwise leak
# real shadow-generation artifacts into this repository's own working tree
# if a developer's shell happens to export the flag. Tests that
# specifically exercise the shadow feature set it explicitly via
# ``monkeypatch.setenv`` within their own scope, which still applies after
# this autouse deletion (fixture order: this one runs first per normal
# autouse-then-explicit-fixture ordering within the same test).
@pytest.fixture(autouse=True)
def _isolate_cltr_shadow_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PCAE_CLTR_SHADOW_ENABLED", raising=False)


# Phase 135O — the Stage 1 dual-derivation coordinator (pcae.cltr.migration)
# writes to ``.pcae/cltr-migration/`` (relative to cwd) whenever
# ``PCAE_CLTR_DUAL_DERIVATION_ENABLED`` is set, from the same
# ``run_finalization_transaction()`` call sites as the shadow observer.
# Same rationale as ``_isolate_cltr_shadow_flag`` above: delete by default,
# tests that specifically exercise Stage 1 set it explicitly.
@pytest.fixture(autouse=True)
def _isolate_cltr_migration_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PCAE_CLTR_DUAL_DERIVATION_ENABLED", raising=False)
    monkeypatch.delenv("PCAE_CLTR_MIGRATION_STAGE", raising=False)
    monkeypatch.delenv("PCAE_CLTR_MIGRATION_EPOCH", raising=False)

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
    # 149O.1E HATP Wave 1/2 foundation -- deterministic, hardware- and
    # environment-independent (149O.1D plan §58 Fast Green policy)
    "test_repository_identity",
    "test_hatp_bootstrap_foundation",
    # 149O.1G HATP Wave 3 (proof models + canonical serialization) --
    # deterministic, hardware- and environment-independent (149O.1D
    # plan §58 Fast Green policy)
    "test_hatp_proof_models",
    "test_hatp_canonical_serialization",
    "test_phase_149o_1g_hatp_proof_models_canonical_serialization",
    # 149O.1I HATP Wave 4 (verification engine) -- deterministic,
    # hardware- and environment-independent (149O.1D plan §58 Fast Green
    # policy); no real cryptography, no wall clock, no network.
    "test_hatp_verification_engine",
    # 149O.2 HATP Wave 5 (real hardware provider) -- the deterministic
    # majority of this module (evidence-format, real-cryptography
    # round-trip, factory/discovery, boundary tests) is hardware- and
    # environment-independent; its few genuinely hardware-dependent
    # cases are separately marked `hatp_hardware_required` and always
    # skip (never fail) when no device is attached (149O.1D plan §58).
    "test_phase_149o_2_hatp_hardware_provider_implementation",
    # 149O.12A HATP Wave A/B (signed evidence model + evidence store) --
    # deterministic, real-filesystem-only I/O (temp dirs, real os.link),
    # no hardware, no network, no wall-clock dependency (149O.1D plan §58
    # Fast Green policy; governing-prompt §85 candidate confirmation).
    "test_hatp_signed_evidence",
    "test_hatp_evidence_store",
    # 149O.12B HATP Waves C/D (signing-ceremony proof-context resolver +
    # orchestrator) -- deterministic, real-filesystem-only I/O (temp job/
    # PER/Binding records), no hardware, no network, no wall-clock
    # dependency (an injectable deterministic clock is used throughout);
    # the hardware provider/trust store are in-memory fakes, never the
    # real production factories (149O.1D plan §58 Fast Green policy).
    "test_hatp_signing_ceremony",
    # 149O.12C Wave E/F (signing CLI + integrated HSCE attack matrix) --
    # deterministic, real-filesystem-only I/O identical in profile to
    # 149O.12A/B above; the CLI handler is exercised via `build_parser()`/
    # direct function calls (no subprocess except the dedicated,
    # already-fast `--help` isolation tests), and the hardware provider/
    # trust store are the identical in-memory fakes 149O.12B's own suite
    # uses -- never the real production factories (149O.1D plan §58 Fast
    # Green policy).
    "test_hatp_cli",
    "test_phase_149o_12c_hsce_attack_matrix",
    # 149O.18A HATP Mandatory Cutover State Foundation (Wave A of HMRC-001)
    # -- deterministic, real-filesystem-only I/O (temp dirs, real symlinks,
    # real flock), no hardware, no network, no wall-clock dependency
    # (149O.1D plan §58 Fast Green policy).
    "test_hatp_mandatory_cutover",
    "test_phase_149o_18a_hatp_mandatory_cutover_state_foundation",
    # 149O.19.5A HMIC Certification Data Models + Canonical Parsing (Wave A
    # of HMIC-001) -- pure, deterministic, no filesystem/Git/network/
    # hardware I/O at all (149O.1D plan §58 Fast Green policy).
    "test_hatp_mandatory_certification_models",
    "test_phase_149o_19_5a_hmic_certification_models_canonical_parsing",
    # 149O.19.5B HMIC Implementation + Contract Identity Derivation (Wave B
    # of HMIC-001) -- deterministic; all Git/filesystem fixtures live
    # entirely under pytest's `tmp_path`, no shared/network state.
    "test_phase_149o_19_5b_hmic_identity_derivation",
    # 149O.19.5C HMIC Protected Certification State Store (Wave C of
    # HMIC-001) -- deterministic; all protected-root fixtures live entirely
    # under pytest's `tmp_path`, no shared/network state, no real
    # HATPTrustStore.production() write.
    "test_phase_149o_19_5c_hmic_protected_certification_state_store",
})


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    fast_green = pytest.mark.fast_green
    for item in items:
        module_name = item.module.__name__.split(".")[-1]
        if module_name in FAST_GREEN_MODULES:
            item.add_marker(fast_green)
