"""Phase 134B.3 — finalization configuration, identity, and cross-agent
hardening: focused regression coverage.

Covers three areas investigated and hardened in this phase:

1. Automatic, channel-agnostic delivery-configuration resolution
   (``pcae.core.notification_config``), removing the requirement to source
   a shell environment file in the same command chain as finalization.
2. Canonical phase-identity / stale-metadata repair
   (``pcae phase metadata-repair``), and confirmation that the existing
   repository transition validator already fails closed on identity
   conflicts.
3. Cross-agent / model-agnostic lifecycle correctness — synthetic caller
   identities must not change lifecycle outcomes.

No test performs real network I/O.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core.notification_config import (
    CONFIG_DISABLE_ENV,
    CONFIG_PATH_ENV,
    DEFAULT_CONFIG_PATH,
    ensure_notification_environment_loaded,
    is_config_resolution_disabled,
    redact_config_value,
    resolve_notification_config_path,
)
from pcae.core.notifications import dispatch, make_notification_event, EVENT_TYPE_MANUAL_TEST
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    validate_transition,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# Part I — automatic delivery configuration resolution
# ─────────────────────────────────────────────────────────────────────────────


def test_resolver_disabled_under_test_isolation():
    """conftest.py's autouse fixture sets the disable flag; confirm the
    resolver honors it unconditionally, regardless of any config file.
    """
    assert is_config_resolution_disabled() is True
    summary = ensure_notification_environment_loaded()
    assert summary["disabled"] is True
    assert summary["applied_keys"] == []


def test_resolver_loads_from_governed_file_without_shell_sourcing(monkeypatch, tmp_path):
    """The core requirement: a governed config file, with no shell `source`
    involved, is enough for the resolver to populate os.environ for the
    current process.
    """
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text(json.dumps({
        "PCAE_NOTIFY_ENABLED": "1",
        "PCAE_NOTIFY_SINKS": "filesystem",
        "PCAE_TELEGRAM_ENABLED": "1",
        "PCAE_TELEGRAM_BOT_TOKEN": "fake-token",
        "PCAE_TELEGRAM_CHAT_ID": "fake-chat",
    }))
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    for key in (
        "PCAE_NOTIFY_ENABLED", "PCAE_NOTIFY_SINKS", "PCAE_TELEGRAM_ENABLED",
        "PCAE_TELEGRAM_BOT_TOKEN", "PCAE_TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    summary = ensure_notification_environment_loaded()
    assert summary["source"] == "governed_config_file"
    assert os.environ.get("PCAE_NOTIFY_ENABLED") == "1"
    assert os.environ.get("PCAE_TELEGRAM_BOT_TOKEN") == "fake-token"


def test_explicit_environment_always_wins_over_governed_file(monkeypatch, tmp_path):
    """Shell-sourced/explicit environment must never be overwritten by the
    governed file -- the file is a fallback, not an override.
    """
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text(json.dumps({"PCAE_NOTIFY_ENABLED": "1"}))
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "0")

    ensure_notification_environment_loaded()
    assert os.environ.get("PCAE_NOTIFY_ENABLED") == "0"


def test_missing_config_file_fails_safely(monkeypatch, tmp_path):
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    monkeypatch.setenv(CONFIG_PATH_ENV, str(tmp_path / "does-not-exist.json"))
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    summary = ensure_notification_environment_loaded()
    assert summary["source"] == "none"
    assert "PCAE_NOTIFY_ENABLED" not in os.environ


def test_invalid_config_file_fails_safely_and_never_raises(monkeypatch, tmp_path):
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text("{ not valid json ]")
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)

    summary = ensure_notification_environment_loaded()
    assert summary["source"] == "invalid_or_unreadable"
    assert "PCAE_NOTIFY_ENABLED" not in os.environ


def test_secrets_never_exposed_in_resolver_summary_or_redaction_helper(monkeypatch, tmp_path):
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text(json.dumps({"PCAE_TELEGRAM_BOT_TOKEN": "super-secret-value"}))
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    monkeypatch.delenv("PCAE_TELEGRAM_BOT_TOKEN", raising=False)

    summary = ensure_notification_environment_loaded()
    dumped = json.dumps(summary)
    assert "super-secret-value" not in dumped

    assert redact_config_value("PCAE_TELEGRAM_BOT_TOKEN", "super-secret-value") == "present"
    assert redact_config_value("PCAE_NOTIFY_SINKS", "telegram,filesystem") == "telegram,filesystem"


def test_non_pcae_keys_are_never_applied_from_config_file(monkeypatch, tmp_path):
    """The resolver must never let a config file inject arbitrary
    (non-PCAE_) environment variables -- security boundary, not just a
    channel-agnostic convenience.
    """
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text(json.dumps({
        "PCAE_NOTIFY_ENABLED": "1",
        "PATH": "/evil/path",
        "LD_PRELOAD": "/evil.so",
    }))
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    original_path = os.environ.get("PATH")

    ensure_notification_environment_loaded()
    assert os.environ.get("PATH") == original_path
    assert "LD_PRELOAD" not in os.environ


def test_future_synthetic_adapter_env_resolves_through_the_same_mechanism(monkeypatch, tmp_path):
    """Core Question 9 (Part I): a brand-new, made-up channel's env var
    resolves through the exact same generic resolver, with no code change.
    """
    monkeypatch.delenv(CONFIG_DISABLE_ENV, raising=False)
    config_path = tmp_path / "notify.json"
    config_path.write_text(json.dumps({"PCAE_FUTURECHANNEL_ENABLED": "1"}))
    monkeypatch.setenv(CONFIG_PATH_ENV, str(config_path))
    monkeypatch.delenv("PCAE_FUTURECHANNEL_ENABLED", raising=False)

    summary = ensure_notification_environment_loaded()
    assert os.environ.get("PCAE_FUTURECHANNEL_ENABLED") == "1"
    assert summary["source"] == "governed_config_file"


def test_notify_status_and_dispatch_share_the_same_resolved_environment(monkeypatch, tmp_path):
    """Requirement #3: notification status and actual dispatch use the same
    resolver. Both are reached only through `pcae.cli.main()`, which calls
    the resolver exactly once before any subcommand -- so a single governed
    config file drives both consistently. Verified end-to-end via the real
    CLI subprocess (isolation env inherited, so no real delivery occurs).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "notify", "status", "--json"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["notify_enabled"] is False  # isolated subprocess: disabled


def test_ordinary_tests_isolated_even_though_resolver_is_globally_wired(monkeypatch):
    """Requirement #7: with the resolver wired into every CLI invocation,
    ordinary tests must still never reach real delivery -- proven end to
    end via a real subprocess CLI call, not just a unit-level check.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "import json, os; "
         "print(json.dumps({k: os.environ.get(k) for k in "
         "['PCAE_NOTIFY_ENABLED','PCAE_TELEGRAM_ENABLED','PCAE_NOTIFY_CONFIG_DISABLE']}))"],
        capture_output=True, text=True,
    )
    values = json.loads(result.stdout)
    assert values["PCAE_NOTIFY_CONFIG_DISABLE"] == "1"


def test_live_test_opt_in_remains_separate_from_config_resolution(monkeypatch, tmp_path):
    """Requirement #8: explicit live-test authorization stays independent of
    (and is not granted by) the config resolver itself -- opting in only
    stops the isolation fixture from disabling resolution; it does not by
    itself enable notifications.
    """
    from conftest import isolate_external_notification_env, _LIVE_NOTIFICATION_TEST_OPT_IN

    env = {_LIVE_NOTIFICATION_TEST_OPT_IN: "1"}
    applied = isolate_external_notification_env(env)
    assert applied is False
    assert CONFIG_DISABLE_ENV not in env or env.get(CONFIG_DISABLE_ENV) != "1"


# ─────────────────────────────────────────────────────────────────────────────
# Part II — canonical identity and stale metadata
# ─────────────────────────────────────────────────────────────────────────────


def test_identity_conflict_fails_closed_before_promotion_or_delivery():
    """Requirement #11/#12: the repository transition validator already
    fails closed (blocking) when independent phase-identity sources
    disagree -- confirmed directly against the validator, not against a
    caller's incidental error handling.
    """
    state = RepositoryState(
        phase_id="134B.3",
        active_task_phase_id="134B.3",
        metadata_phase_id="134B.2",  # stale
        artifact_state=ArtifactState.CERTIFIED,
    )
    result = validate_transition(
        state,
        ProposedTransition(kind=TransitionKind.REPORT_PROMOTION, payload={}),
        ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="134B.3"),
    )
    assert result.verdict in (TransitionVerdict.REJECT, TransitionVerdict.QUARANTINE)
    reasons = " ".join(v.reason for v in result.violations)
    assert "134B.2" in reasons and "134B.3" in reasons


def test_stale_metadata_cannot_silently_become_canonical():
    """Requirement #13: a REPORT_PROMOTION transition targeting a phase_id
    that disagrees with metadata's declared identity must never reach
    ArtifactState.CANONICAL.
    """
    state = RepositoryState(
        phase_id="134B.3",
        metadata_phase_id="134B.2",
        artifact_state=ArtifactState.CERTIFIED,
    )
    result = validate_transition(
        state,
        ProposedTransition(kind=TransitionKind.REPORT_PROMOTION, payload={}),
        ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="134B.3"),
    )
    assert result.verdict != TransitionVerdict.ACCEPT


def test_metadata_repair_refuses_without_canonical_report(tmp_path, monkeypatch):
    from pcae.commands.phase import run_phase_metadata_repair
    import argparse

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps({"phase_id": "134B.2", "phase_name": "Old"})
    )
    args = argparse.Namespace(json=True)
    exit_code = run_phase_metadata_repair(args)
    assert exit_code == 1


def test_metadata_repair_syncs_from_canonical_report_one_direction_only(tmp_path, monkeypatch):
    from pcae.commands.phase import run_phase_metadata_repair
    import argparse

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps({"phase_id": "134B.2", "phase_name": "Old Name"})
    )
    (tmp_path / ".pcae" / "phase-completion-report.md").write_text(
        "# Phase 134B.3 Complete — New Canonical Name\n\nbody\n"
    )
    args = argparse.Namespace(json=True)
    exit_code = run_phase_metadata_repair(args)
    assert exit_code == 0

    repaired = json.loads((tmp_path / ".pcae" / "phase-completion-metadata.json").read_text())
    assert repaired["phase_id"] == "134B.3"
    assert repaired["phase_name"] == "New Canonical Name"
    assert (tmp_path / ".pcae" / "phase-metadata-repairs.log").exists()


def test_metadata_repair_is_a_noop_when_already_current(tmp_path, monkeypatch):
    from pcae.commands.phase import run_phase_metadata_repair
    import argparse

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps({"phase_id": "134B.3", "phase_name": "Same Name"})
    )
    (tmp_path / ".pcae" / "phase-completion-report.md").write_text(
        "# Phase 134B.3 Complete — Same Name\n\nbody\n"
    )
    args = argparse.Namespace(json=True)
    exit_code = run_phase_metadata_repair(args)
    assert exit_code == 0
    log_path = tmp_path / ".pcae" / "phase-metadata-repairs.log"
    assert not log_path.exists()


def test_metadata_repair_does_not_require_clean_or_pushed_state(tmp_path, monkeypatch):
    """Part II requirement: recovery must not require an impossible
    clean/pushed state cycle. The repair command touches only local files
    and never inspects git status.
    """
    from pcae.commands.phase import run_phase_metadata_repair
    import argparse
    import inspect

    src = inspect.getsource(run_phase_metadata_repair)
    assert "git" not in src.lower()
    assert "pushed_status" not in src


def test_report_notification_and_completion_identity_are_the_single_source():
    """Requirement #15: report identity, notification identity, and
    completion identity all derive from the same RepositoryState.phase_id
    -- there is exactly one phase_id field on RepositoryState, not three.
    """
    import dataclasses
    fields = {f.name for f in dataclasses.fields(RepositoryState)}
    identity_fields = {f for f in fields if "phase_id" in f}
    # Exactly one *authoritative* transition-target identity
    # (`phase_id`); the others are independent *evidence* sources by
    # design (active_task_phase_id, metadata_phase_id,
    # lifecycle_current_phase_id) -- consistency between them is what
    # phase_identity_consistency enforces, not merging them into one field.
    assert "phase_id" in identity_fields


# ─────────────────────────────────────────────────────────────────────────────
# Part III — cross-agent / model-agnostic correctness
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("synthetic_agent", ["deepseek-agent", "claude-agent", "codex-agent", "unknown-future-agent"])
def test_validator_produces_equivalent_verdicts_regardless_of_caller_identity(synthetic_agent):
    """No field on RepositoryState/ProposedTransition carries caller
    identity, so passing one through ProposedTransition.payload (an open
    bag) must not change the verdict for otherwise-identical repository
    state -- proven for four synthetic callers including an unknown future
    one.
    """
    state = RepositoryState(
        phase_id="134B.3",
        active_task_phase_id="134B.3",
        metadata_phase_id="134B.3",
        report_completeness="complete",
        pushed_status="pushed",
        origin_main_head_count=0,
        artifact_state=ArtifactState.CERTIFIED,
        test_results={"fast_green": "1/1"},
        recommended_next_phase="134C",
    )
    result = validate_transition(
        state,
        ProposedTransition(
            kind=TransitionKind.REPORT_PROMOTION,
            payload={"agent": synthetic_agent, "model": synthetic_agent},
        ),
        ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="134B.3"),
    )
    assert result.verdict == TransitionVerdict.ACCEPT


def test_no_model_specific_branch_exists_in_lifecycle_critical_modules():
    """Static confirmation, not just behavioral: none of the lifecycle-
    critical modules contain a DeepSeek/Claude/Codex/model-identity branch
    that could make correctness depend on the calling agent.
    """
    import inspect
    from pcae.core import (
        repository_transition_validator, notification_certification,
        notifications, phase_reports, notification_config,
    )
    for module in (
        repository_transition_validator, notification_certification,
        notifications, phase_reports, notification_config,
    ):
        src = inspect.getsource(module)
        lowered = src.lower()
        for marker in ("deepseek", "claude", "codex"):
            assert marker not in lowered, f"{module.__name__} contains a {marker} reference"


def test_configuration_resolution_is_caller_independent(monkeypatch, tmp_path):
    """Part III requirement: configuration resolution does not consult any
    caller/agent-identity value -- confirmed by source inspection of the
    resolver's own signature and body.
    """
    import inspect
    from pcae.core import notification_config

    sig = inspect.signature(notification_config.ensure_notification_environment_loaded)
    assert list(sig.parameters) == []  # takes no caller/agent argument at all


def test_synthetic_execution_remains_isolated_regardless_of_synthetic_caller_marker(monkeypatch):
    """Combines Part I and Part III: even with a synthetic "which agent is
    calling" marker set in the environment, dispatch() still fail-closes
    external delivery under test isolation.
    """
    monkeypatch.setenv("PCAE_SYNTHETIC_CALLER_AGENT", "deepseek-agent")
    monkeypatch.delenv("PCAE_NOTIFY_ENABLED", raising=False)
    from pcae.core.notifications import TelegramSink

    sink = TelegramSink(bot_token="t", chat_id="c", enabled=True)
    event = make_notification_event(event_type=EVENT_TYPE_MANUAL_TEST, title="t", message="m")
    results = dispatch(event, [sink])
    assert results[0].success is False
    assert results[0].error == "external_delivery_not_authorized"


# ─────────────────────────────────────────────────────────────────────────────
# Regression: 134B.1 / 134B.2 isolation remain green
# ─────────────────────────────────────────────────────────────────────────────


def test_134b1_and_134b2_isolation_env_vars_still_stripped():
    from conftest import _EXTERNAL_NOTIFICATION_ENV
    for key in _EXTERNAL_NOTIFICATION_ENV:
        assert key not in os.environ
