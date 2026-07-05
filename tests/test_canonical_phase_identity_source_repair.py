"""Tests for Phase 113X.4 — Canonical Phase Identity Repair.

Repairs 113X (Cross-Agent Governance Verification) Finding 3 in full.
The forensic review proved that deriving phase identity by regex over
free-text `--summary` is fundamentally unsound: a summary mentioning a
previous phase for context (e.g. "extends Phase 113B") could become
the report's own identity. 113X.2 only detected a *disagreement*
between that regex-derived value and metadata's declared one; this
phase removes the regex derivation entirely. Canonical phase_id/
phase_name/recommended_next_phase now originate from exactly one
authoritative source, resolved by `resolve_canonical_phase_identity()`
in a fixed precedence order -- active task contract, phase-completion
metadata, active lifecycle context, explicit --phase-id/--phase-name --
never free text. Fails closed (refuses finalization, writes nothing)
if none resolve.

This file supersedes `tests/test_canonical_phase_identity_repair.py`
(113X.2), which tested the now-retired `resolve_finalization_phase_
identity()` comparison mechanism. That mechanism compared a regex-
derived summary phase_id against metadata's; there is no more
regex-derived value to compare, so those tests no longer apply.

Non-executing, non-authorizing. No real network calls. No Advisory
Runtime, Runtime Snapshot, Runtime Context, Runtime Registry, Runtime
Inspect, Permission Broker, execution, authorization, plugin,
Telegram-inbound, REST, Web UI, Dashboard, or Architecture Status
changes (out of scope -- see PROJECT_STATUS.md Phase 113X.4).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import (
    CanonicalPhaseIdentity,
    resolve_canonical_phase_identity,
)
from pcae.core.tasks import create_task_contract


def _init_repo(tmp_path: Path) -> HarnessPath:
    root = HarnessPath(tmp_path)
    init_harness(root)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    return root


def _complete_metadata(**overrides) -> dict:
    meta = {
        "phase_id": "205D",
        "phase_name": "Some Governed Phase",
        "files_changed_count": 2,
        "tests_added_or_updated": "5 tests added",
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
        ],
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "no_go_confirmation": (
            "No runtime enforcement. No execution. No subprocess. No shell. "
            "No network. No Telegram inbound. No apply. No commit authorization. "
            "No push authorization. No rollback. No adapter execution."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205E — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
    }
    meta.update(overrides)
    return meta


def _write_metadata(tmp_path: Path, **overrides) -> dict:
    meta = _complete_metadata(**overrides)
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
    return meta


# ── Unit-level: resolve_canonical_phase_identity() precedence ──────────────


class TestResolveCanonicalPhaseIdentityPrecedence:
    def test_active_task_contract_wins_over_everything(self):
        identity = resolve_canonical_phase_identity(
            active_task_title="Phase 113X.4: Canonical Phase Identity Repair",
            metadata={"phase_id": "999Z", "phase_name": "Wrong"},
            lifecycle_current_phase_line="Phase 888Y — Also Wrong.",
            cli_phase_id="777W",
        )
        assert identity == CanonicalPhaseIdentity("113X.4", "Canonical Phase Identity Repair", "active_task_contract")

    def test_metadata_wins_when_no_active_task(self):
        identity = resolve_canonical_phase_identity(
            active_task_title=None,
            metadata={"phase_id": "205D", "phase_name": "Some Phase"},
            lifecycle_current_phase_line="Phase 888Y — Also Wrong.",
        )
        assert identity == CanonicalPhaseIdentity("205D", "Some Phase", "phase_completion_metadata")

    def test_lifecycle_context_wins_when_in_progress(self):
        identity = resolve_canonical_phase_identity(
            active_task_title=None, metadata={},
            lifecycle_current_phase_line="Phase 205E — In Progress Phase.",
        )
        assert identity == CanonicalPhaseIdentity("205E", "In Progress Phase", "active_lifecycle_context")

    def test_lifecycle_context_skipped_when_marked_completed(self):
        identity = resolve_canonical_phase_identity(
            active_task_title=None, metadata={},
            lifecycle_current_phase_line="Phase 205E — Already Done (completed).",
            cli_phase_id="900A",
        )
        # Falls through past the completed lifecycle line to the CLI arg.
        assert identity.source == "cli_argument"
        assert identity.phase_id == "900A"

    def test_cli_argument_is_last_resort(self):
        identity = resolve_canonical_phase_identity(
            active_task_title=None, metadata={}, lifecycle_current_phase_line=None,
            cli_phase_id="999Z", cli_phase_name="Bootstrap Phase",
        )
        assert identity == CanonicalPhaseIdentity("999Z", "Bootstrap Phase", "cli_argument")

    def test_no_source_resolves_returns_none(self):
        assert resolve_canonical_phase_identity(
            active_task_title=None, metadata={}, lifecycle_current_phase_line=None,
        ) is None


# ── Regression: the exact forensic scenario ─────────────────────────────────


class TestForensicScenarioReproduction:
    """Reproduces the exact 113X-audit-documented failure: a summary
    mentioning a previous phase for context must never become the
    report's own identity."""

    def test_summary_mentioning_previous_phase_does_not_affect_id(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="113C", phase_name="Advisory Runtime Prototype")
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary",
            "Implements the Advisory Runtime, extending Phase 113B's frozen "
            "contract into a concrete prototype.",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "113C"
        assert latest["phase_id"] != "113B"

    def test_summary_mentioning_future_phase_does_not_affect_id(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary",
            "Lays groundwork so that a future Phase 999Z can add execution capability.",
        ])

        assert exit_code == 0
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "205D"

    def test_summary_with_multiple_phase_numbers_does_not_affect_id(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="113X.4")
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary",
            "Repairs Phase 113X Finding 3 following Phase 113B, Phase 113C, "
            "and Phase 113X.2's own partial attempt, recommending Phase 113D next.",
        ])

        assert exit_code == 0
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "113X.4"

    def test_canonical_identity_always_wins_over_contradicting_summary(self, tmp_path, monkeypatch, capsys):
        """Even when metadata's phase_id doesn't textually appear
        anywhere in the summary at all, it is still used."""
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="500A", phase_name="Unrelated Governed Phase")
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary",
            "This summary never mentions its own phase number at all.",
        ])

        assert exit_code == 0
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "500A"
        assert latest["phase_name"] == "Unrelated Governed Phase"


# ── Invalid identity fails closed ───────────────────────────────────────────


class TestInvalidIdentityFailsClosed:
    def test_no_metadata_no_task_no_lifecycle_fails_closed(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "PROJECT_STATUS.md").unlink(missing_ok=True)
        # No .pcae/phase-completion-metadata.json written at all.

        exit_code = main(["phase", "complete", "--summary", "Phase 999Z: done."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "could not be determined" in output.lower()
        assert "refusing to finalize" in output.lower()
        # Fail closed means nothing is written at all -- not even a
        # quarantined artifact, since there is no identity to build a
        # report around.
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()
        assert not (tmp_path / ".pcae" / "phase-reports").exists() or not list(
            (tmp_path / ".pcae" / "phase-reports").glob("**/*")
        )

    def test_explicit_cli_phase_id_resolves_when_nothing_else_does(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        (tmp_path / "PROJECT_STATUS.md").unlink(missing_ok=True)
        _write_metadata(tmp_path, phase_id="")  # metadata present but no phase_id declared
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps({
            "files_changed_count": 2,
            "tests_added_or_updated": "5 tests added",
            "governance_results": [
                {"name": "pcae_health", "status": "healthy"},
                {"name": "pcae_check", "status": "passed"},
                {"name": "pcae_doctor_task_memory", "status": "clean"},
                {"name": "pcae_push_check", "status": "clean"},
                {"name": "telegram_runtime", "status": "loaded, configured, enabled"},
            ],
            "validation_results": [
                {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
                {"name": "bootstrap_session_reporting_tests", "result": "present", "status": ""},
                {"name": "fast_green", "result": "1/1", "status": "passed"},
            ],
            "no_go_confirmation": (
                "No runtime enforcement. No execution. No subprocess. No shell. "
                "No network. No Telegram inbound. No apply. No commit authorization. "
                "No push authorization. No rollback. No adapter execution."
            ),
            "pushed_status": "pushed",
            "origin_main_head_count": 0,
            "recommended_next_phase": "999B — Next",
            "phase_commits": [{"hash": "abc1234500000000"}],
            "commit_attribution": "phase_owned",
        }))

        exit_code = main([
            "phase", "complete", "--summary", "Bootstrap completion.",
            "--phase-id", "999A", "--phase-name", "Bootstrap Phase",
        ])

        assert exit_code == 0
        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "999A"


# ── Report phase_id matches active task / phase_name matches canonical ─────


class TestReportMatchesCanonicalSources:
    def test_report_phase_id_matches_active_task(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        create_task_contract(
            root, title="Phase 205F: Active Task Wins",
            goal="test", mode="implementation",
        )
        # recommended_next_phase must be forward of the *resolved* identity
        # (205F, from the active task) to avoid tripping the unrelated
        # branch-aware backward-pointing check (113X.3) in this fixture.
        _write_metadata(
            tmp_path, phase_id="205Z", phase_name="Should Not Win",
            recommended_next_phase="205G — Next Phase",
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary",
            "Mentions a completely different Phase 999Q in passing.",
        ])

        output = capsys.readouterr().out
        assert exit_code == 1
        assert "Repository transition validator: Transition rejected" in output
        assert "phase_identity_consistency" in output
        assert "metadata_consistency" in output
        assert not (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()

    def test_report_phase_name_matches_canonical_phase(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D", phase_name="Canonical Governed Name")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Phase 999Z: irrelevant summary phase."])

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_name"] == "Canonical Governed Name"


# ── Recommendation chain remains correct ────────────────────────────────────


class TestRecommendationChainCorrect:
    def test_recommended_next_phase_comes_from_metadata_not_summary(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D", recommended_next_phase="205E — Real Next Phase")
        monkeypatch.chdir(tmp_path)

        main(["phase", "complete", "--summary", "Recommended next phase: 999Z — Fake Phase From Summary."])

        latest = json.loads((tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["recommended_next_phase"] == "205E — Real Next Phase"

    def test_missing_recommended_next_phase_fails_closed_via_existing_gate(self, tmp_path, monkeypatch, capsys):
        """With no summary-text fallback, an absent structured
        recommended_next_phase now hits the pre-existing gate blocker
        instead of silently parsing the summary."""
        root = _init_repo(tmp_path)
        meta = _complete_metadata(phase_id="205D")
        meta.pop("recommended_next_phase")
        (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(meta))
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Recommended next phase: 999Z — Should Be Ignored."])
        output = capsys.readouterr().out

        assert exit_code == 1
        assert "recommended_next_phase missing as structured metadata" in output
        assert "999Z" not in output.split("BLOCKED")[-1] if "BLOCKED" in output else True


# ── Backward compatibility: prior phases' behavior remains intact ──────────


class TestBackwardCompatibility:
    def test_matching_identity_completes_normally(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output
        assert "BLOCKED" not in output

    def test_113x1_quarantine_still_blocks_and_never_overwrites_latest(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D")
        monkeypatch.chdir(tmp_path)

        assert main(["phase", "complete", "--summary", "Phase 205D: done."]) == 0
        capsys.readouterr()
        valid_latest = (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text()

        _write_metadata(tmp_path, phase_id="205D", files_changed_count=0)  # now a blocker
        exit_code2 = main(["phase", "complete", "--summary", "Phase 205D: done."])
        output = capsys.readouterr().out

        assert exit_code2 == 1
        assert "BLOCKED by finalization gate" in output
        assert "Report quarantined" in output
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").read_text() == valid_latest

    def test_allow_partial_report_still_works(self, tmp_path, monkeypatch, capsys):
        root = _init_repo(tmp_path)
        _write_metadata(tmp_path, phase_id="205D", files_changed_count=0)
        monkeypatch.chdir(tmp_path)

        exit_code = main([
            "phase", "complete", "--summary", "Phase 205D: done.", "--allow-partial-report",
        ])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "--allow-partial-report" in output
        assert (tmp_path / ".pcae" / "phase-reports" / "latest.json").exists()

    def test_branch_aware_backward_check_still_works(self, tmp_path, monkeypatch, capsys):
        """113X.3's branch-aware fix (113D from 113X.2 not backward)
        remains intact under the new identity resolution."""
        root = _init_repo(tmp_path)
        _write_metadata(
            tmp_path, phase_id="113X.2",
            recommended_next_phase="113D — Advisory Runtime Verification",
        )
        monkeypatch.chdir(tmp_path)

        exit_code = main(["phase", "complete", "--summary", "Phase 113X.2: done."])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Trust gate (105D): complete" in output
        assert "points backward" not in output
