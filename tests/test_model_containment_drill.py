"""Phase 114E: Model Containment Drill.

Verification-only phase. Drills 12 known DeepSeek-style model/agent drift
patterns against the existing containment stack --
113Y/113Z (Repository Transition Validator integration),
114A (Canonical Artifact Promotion & Quarantine),
114B (Notification Certification & Idempotency),
114B.1 (Repository Events & Notification Policy),
114C (Push-State Reconciliation),
114D (`pcae agent verify-handoff`),
114D.1 (Post-Push Canonicalization & Notification Reconciliation)
-- and asserts each drift pattern is still contained.

No new runtime mechanism is added by this phase. Every scenario below
drives an already-existing enforcement point through an isolated scratch
repository (a real local "origin" remote, no network, never the actual
pcae-harness repository) and asserts it holds. Where a scenario is more
clearly proven at the pure-function level (the Repository Transition
Validator, notification eligibility) than through the full CLI, both are
used: CLI reproduction is preferred whenever the scenario is about a
lifecycle command's end-to-end behavior.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.handoff_verification import STATUS_FAIL, STATUS_WARNING, verify_handoff
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import read_latest_report, read_notification_dispatch_marker
from pcae.core.push_state_reconciliation import reconcile_push_state
from pcae.core.repository_transition_validator import (
    ArtifactState,
    ExpectedTargetState,
    ProposedTransition,
    RepositoryState,
    TransitionKind,
    TransitionVerdict,
    validate_transition,
)
from pcae.core.tasks import create_task_contract

# ═══════════════════════════════════════════════════════════════════════════
# Shared scratch-repo fixture helpers
# ═══════════════════════════════════════════════════════════════════════════


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_real_origin(tmp_path: Path) -> Path:
    """An isolated scratch repository with a real local (no-network)
    origin remote -- never the actual pcae-harness repository."""
    work = tmp_path / "work"
    origin_bare = tmp_path / "origin.git"
    work.mkdir()
    subprocess.run(["git", "init", "--bare", str(origin_bare)], check=True, capture_output=True)
    _run_git(work, "init")
    _run_git(work, "config", "user.email", "test@example.com")
    _run_git(work, "config", "user.name", "Test User")
    _run_git(work, "checkout", "-b", "main")

    root = HarnessPath(work)
    init_harness(root)

    pcae_gitignore = work / ".pcae" / ".gitignore"
    existing = pcae_gitignore.read_text(encoding="utf-8") if pcae_gitignore.exists() else ""
    pcae_gitignore.write_text(existing + "\nphase-reports/\n", encoding="utf-8")

    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "baseline")
    _run_git(work, "remote", "add", "origin", str(origin_bare))
    _run_git(work, "push", "-u", "origin", "main")
    return work


def _commit_hash(work: Path) -> str:
    return _run_git(work, "rev-parse", "--short", "HEAD").stdout.strip()


def _valid_metadata(**overrides) -> dict:
    data = {
        "phase_id": "205Z",
        "phase_name": "Drill Fixture",
        "status": "completed",
        "summary": "Model containment drill fixture.",
        "files_changed_count": 2,
        "files_changed": ["a.py", "b.py"],
        "tests_added_or_updated": "4 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No notification integration. No push-check integration. No execution. "
            "No authorization. No Permission Broker enforcement. No Telegram inbound. "
            "No REST. No Web UI. No Dashboard. No package publication. "
            "No lifecycle command beyond the drill fixture."
        ),
        "commit_attribution": "phase_owned",
        "phase_commits": [],
        "recommended_next_phase": "206A — Next",
        "execution_availability": "unavailable",
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
    }
    data.update(overrides)
    return data


def _write_metadata(work: Path, **overrides) -> dict:
    data = _valid_metadata(**overrides)
    (work / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(data), encoding="utf-8")
    return data


def _write_project_status(work: Path, phase_id: str, recommended: str = "206A — Next") -> None:
    text = (
        "# Project Status\n\n"
        "## Current Phase\n\n"
        f"Phase {phase_id} — Drill Fixture (completed).\n\n"
        f"Recommended next repo phase: {recommended} (not started).\n"
    )
    (work / "PROJECT_STATUS.md").write_text(text, encoding="utf-8")


def _new_task(root: HarnessPath, title: str) -> None:
    create_task_contract(
        root,
        title=title,
        goal="model containment drill fixture",
        mode="implementation",
        allowed_files=[".pcae/**", "tasks/active/**", "tasks/done/**", "PROJECT_STATUS.md"],
        allowed_zones=["config", "tasks", "docs"],
    )


def _snapshot_canonical_report(work: Path) -> str | None:
    latest = work / ".pcae" / "phase-reports" / "latest.json"
    return latest.read_text(encoding="utf-8") if latest.exists() else None


def _certified_state(**overrides) -> RepositoryState:
    base = dict(
        phase_id="205Z",
        active_task_phase_id="205Z",
        metadata_phase_id="205Z",
        lifecycle_current_phase_id="205Y",
        lifecycle_current_phase_completed=True,
        commits=("abc12345",),
        files_changed=2,
        test_results={"fast_green": "1/1 (passed)"},
        recommended_next_phase="206A — Next",
        report_completeness="complete",
        pushed_status="pushed",
        origin_main_head_count=0,
        notification_already_dispatched=False,
        notification_transport_enabled=True,
        artifact_state=ArtifactState.CERTIFIED,
        execution_availability="unavailable",
    )
    base.update(overrides)
    return RepositoryState(**base)


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 1 — Wrong phase identity
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario1WrongPhaseIdentity:
    def test_disagreeing_identity_sources_reject_at_validator_level(self):
        state = _certified_state(active_task_phase_id="205Z", metadata_phase_id="999X")
        target = ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="205Z")
        result = validate_transition(state, ProposedTransition(kind=TransitionKind.COMPLETE_PHASE), target)

        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "phase_identity_consistency" for v in result.violations)

    def test_active_task_metadata_mismatch_rejects_via_cli_and_report_unchanged(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 999X: Unrelated Drift Task")  # active task claims 999X
        _write_metadata(work, phase_id="205Z")  # metadata claims a different phase
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        main(["task", "finish", "--staged-file-aware", "--commit", "drift attempt"])
        out = capsys.readouterr().out
        after = _snapshot_canonical_report(work)

        assert "Repository transition validator" in out
        assert "Transition rejected" in out or "rejected" in out.lower()
        assert after == before  # canonical report untouched


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 2 — Stale phase-completion metadata
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario2StaleMetadata:
    def test_metadata_naming_a_phase_inconsistent_with_active_task_is_rejected(self, tmp_path, monkeypatch, capsys):
        """Simulates an old phase's metadata file being reused during a
        newer phase's task -- the active task (the freshest signal) and
        the stale metadata disagree, and the validator refuses to
        reconcile them silently."""
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        reports_dir = work / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "latest.json").write_text(json.dumps({"phase_id": "205Y"}), encoding="utf-8")
        (reports_dir / "latest.md").write_text("phase_id: 205Y\n", encoding="utf-8")

        _new_task(root, "Phase 205Z: Fresh Task")
        _write_metadata(work, phase_id="OLD1")  # stale metadata from a prior phase
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        main(["task", "finish", "--staged-file-aware", "--commit", "stale metadata attempt"])
        after = _snapshot_canonical_report(work)

        assert after == before
        latest = json.loads(after)
        assert latest["phase_id"] == "205Y"  # never overwritten with stale OLD1


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 3 — Stale commit hashes
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario3StaleCommitHashes:
    def test_files_changed_without_real_commits_blocks_promotion(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 205Z: Drill Fixture")
        _write_metadata(work, phase_commits=[])  # files_changed>0 but no commits declared
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        exit_code = main(["task", "finish", "--staged-file-aware", "--commit", "stale commit attempt"])
        out = capsys.readouterr().out
        after = _snapshot_canonical_report(work)

        assert "quarantined" in out.lower() or "rejected" in out.lower()
        assert after == before


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 4 — Missing recommended_next_phase
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario4MissingRecommendedNextPhase:
    def test_absent_recommended_next_phase_rejects_at_validator_level(self):
        state = _certified_state(recommended_next_phase="")
        target = ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="205Z")
        result = validate_transition(state, ProposedTransition(kind=TransitionKind.COMPLETE_PHASE), target)

        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "recommended_next_phase_presence" for v in result.violations)

    def test_missing_recommended_next_phase_via_cli_blocks_and_report_unchanged(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 205Z: Drill Fixture")
        commit = _commit_hash(work)
        _write_metadata(work, phase_commits=[{"hash": commit}], recommended_next_phase="")
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        main(["task", "finish", "--staged-file-aware", "--commit", "no next phase"])
        after = _snapshot_canonical_report(work)

        assert after == before


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 5 — Bad test result structure
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario5BadTestResultStructure:
    def test_missing_fast_green_entry_blocks_promotion(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 205Z: Drill Fixture")
        commit = _commit_hash(work)
        _write_metadata(
            work, phase_commits=[{"hash": commit}],
            validation_results=[
                {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
                # fast_green deliberately omitted -- prose could still claim "all green"
            ],
        )
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        exit_code = main(["task", "finish", "--staged-file-aware", "--commit", "bad test structure"])
        after = _snapshot_canonical_report(work)

        assert after == before


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 6 — Duplicate notification attempt
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario6DuplicateNotification:
    def test_repeated_push_does_not_duplicate_dispatch(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _run_git(work, "add", ".")
        _run_git(work, "commit", "-m", "declare completion")
        _run_git(work, "push", "origin", "main")
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])
        first_out = capsys.readouterr().out
        marker_path = work / ".pcae" / "phase-reports" / ".last-notified.json"
        marker_after_first = marker_path.read_text()

        main(["push"])
        second_out = capsys.readouterr().out

        assert "Notification dispatch: sent" in first_out
        assert "Notification dispatch: sent" not in second_out
        assert marker_path.read_text() == marker_after_first


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 7 — Silent notification prevention
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario7SilentNotificationPrevention:
    def test_quarantined_transition_never_claims_dispatch_success(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 205Z: Drill Fixture")
        _write_metadata(work, phase_commits=[])  # will quarantine (Scenario 3's condition)
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["task", "finish", "--staged-file-aware", "--commit", "silent notification check"])
        out = capsys.readouterr().out

        assert "Notification dispatch: sent" not in out
        assert "Report notification: sent" not in out
        # The refusal itself must be visible, not silent.
        assert ("quarantined" in out.lower()) or ("rejected" in out.lower())


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 8 — Push-state mismatch (both directions)
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario8PushStateMismatch:
    def test_metadata_claims_pushed_but_live_is_unpushed_reconciliation_wins(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        (work / "extra.txt").write_text("x")
        _run_git(work, "add", "extra.txt")
        _run_git(work, "commit", "-m", "unpushed")  # genuinely unpushed, live state disagrees
        monkeypatch.chdir(work)

        metadata = _valid_metadata(pushed_status="pushed", origin_main_head_count=0)
        reconciled = reconcile_push_state(metadata)

        assert reconciled.source == "live"
        assert reconciled.pushed_status == "not_pushed"
        assert reconciled.metadata_push_state_stale is True

    def test_metadata_claims_unpushed_but_live_is_clean_reconciliation_wins(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        monkeypatch.chdir(work)

        metadata = _valid_metadata(pushed_status="not_pushed", origin_main_head_count=9)
        reconciled = reconcile_push_state(metadata)

        assert reconciled.source == "live"
        assert reconciled.pushed_status == "pushed"
        assert reconciled.origin_main_head_count == 0
        assert reconciled.metadata_push_state_stale is True
        # Discrepancy is always visible, never silent.
        assert reconciled.metadata_origin_main_head_count == 9
        assert reconciled.live_origin_main_head_count == 0


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 9 — Architecture Status overclaim
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario9ArchitectureOverclaim:
    def test_planned_phase_already_completed_is_flagged(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        reports_dir = work / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "phase_id": "205Z",
            "phase_name": "Drill Fixture",
            "status": "completed",
            "commits": [commit],
            "pushed_status": "pushed",
            "origin_main_head_count": 0,
            "report_completeness": "complete",
            "recommended_next_phase": "206A — Next",
            "architecture_status": {
                "completed_phase_ids": ["205X", "205Y", "205Z"],
                "planned": ["205Z"],  # overclaim: "planned" already appears completed
            },
        }
        (reports_dir / "latest.json").write_text(json.dumps(report), encoding="utf-8")
        (reports_dir / "latest.md").write_text("phase_id: 205Z\n", encoding="utf-8")
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        result = verify_handoff(HarnessPath(work))

        overlap_check = next(c for c in result.checks if c.name == "architecture_no_duplicate_claim")
        assert overlap_check.status == STATUS_WARNING
        assert "205Z" in overlap_check.detail


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 10 — Dirty working tree / untracked drift
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario10DirtyWorkingTree:
    def test_dirty_tree_fails_verify_handoff(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        (work / "untracked_drift.txt").write_text("model wrote this without committing")
        monkeypatch.chdir(work)

        result = verify_handoff(HarnessPath(work))

        assert result.status == STATUS_FAIL
        assert any("dirty" in f for f in result.failures)


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 11 — Latest report mismatch (latest.md vs latest.json)
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario11LatestReportMismatch:
    def test_md_json_disagreement_fails_verify_handoff(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        reports_dir = work / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "latest.json").write_text(json.dumps({
            "phase_id": "205Z", "status": "completed", "report_completeness": "complete",
            "pushed_status": "pushed", "origin_main_head_count": 0,
        }), encoding="utf-8")
        (reports_dir / "latest.md").write_text("# Unrelated content, different phase entirely\n", encoding="utf-8")
        monkeypatch.chdir(work)

        result = verify_handoff(HarnessPath(work))

        assert result.status == STATUS_FAIL
        assert any("latest.md does not reference" in f for f in result.failures)


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 12 — Execution availability violation
# ═══════════════════════════════════════════════════════════════════════════


class TestScenario12ExecutionAvailabilityViolation:
    def test_execution_available_metadata_rejects_at_validator_level(self):
        state = _certified_state(execution_availability="available")
        target = ExpectedTargetState(artifact_state=ArtifactState.CANONICAL, phase_id="205Z")
        result = validate_transition(state, ProposedTransition(kind=TransitionKind.COMPLETE_PHASE), target)

        assert result.verdict == TransitionVerdict.REJECT
        assert any(v.invariant == "no_execution_availability_unless_contracted" for v in result.violations)

    def test_execution_available_metadata_blocks_via_cli(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        root = HarnessPath(work)
        _new_task(root, "Phase 205Z: Drill Fixture")
        commit = _commit_hash(work)
        _write_metadata(work, phase_commits=[{"hash": commit}], execution_availability="available")
        _write_project_status(work, "205Z")
        monkeypatch.chdir(work)

        before = _snapshot_canonical_report(work)
        main(["task", "finish", "--staged-file-aware", "--commit", "execution overclaim attempt"])
        out = capsys.readouterr().out
        after = _snapshot_canonical_report(work)

        assert "execution_availability" in out
        assert after == before

    def test_execution_unavailable_constant_unchanged(self):
        from pcae.core.runtime_context import (
            CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            CURRENT_RUNTIME_STATE,
            EXECUTION_AVAILABILITY,
        )

        assert EXECUTION_AVAILABILITY == "unavailable"
        assert CURRENT_RUNTIME_STATE == "Observed"
        assert CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
