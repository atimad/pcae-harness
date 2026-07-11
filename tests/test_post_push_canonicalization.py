"""Phase 114D.1: Post-Push Canonicalization & Notification Reconciliation.

Covers the live defect Phase 114D's own `pcae agent verify-handoff` run
found immediately after 114D's governed push: declared phase-completion
metadata named `114D`, but the canonical report (`latest.json`) was still
`114A` -- nothing ever re-ran finalization after the push that made the
repository push-clean. These tests use a real local "origin" remote (a
bare repo under `tmp_path`, no network) so live push state is genuinely
determinable through `pcae push` itself, exactly like Phase 114C's and
114D's own test suites.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import read_notification_dispatch_marker
from pcae.core.post_push_canonicalization import (
    live_push_is_clean,
    reconciliation_pending,
)


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo_with_real_origin(tmp_path: Path) -> Path:
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

    # Mirrors this actual repository's own `.pcae/.gitignore` convention:
    # `phase-reports/` is untracked/ignored there too, so canonical report
    # writes (including this phase's post-push reconciliation) never dirty
    # the tracked working tree. Phase 134E.10 activates the finalization
    # transaction, which writes its own ephemeral bookkeeping
    # (`finalization-transactions/`, `delivery-receipts/`) alongside the
    # report -- same convention, same reason.
    pcae_gitignore = work / ".pcae" / ".gitignore"
    existing = pcae_gitignore.read_text(encoding="utf-8") if pcae_gitignore.exists() else ""
    pcae_gitignore.write_text(
        existing + "\nphase-reports/\nfinalization-transactions/\ndelivery-receipts/\n",
        encoding="utf-8",
    )

    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "baseline")
    _run_git(work, "remote", "add", "origin", str(origin_bare))
    _run_git(work, "push", "-u", "origin", "main")
    return work


def _write_metadata(work: Path, **overrides) -> None:
    data = {
        "phase_id": "205Z",
        "phase_name": "Reconciliation Fixture",
        "status": "completed",
        "summary": "Post-push canonicalization fixture.",
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
            "No lifecycle command beyond post-push reconciliation."
        ),
        "commit_attribution": "phase_owned",
        "phase_commits": [],
        "recommended_next_phase": "206A — Next",
        "execution_availability": "unavailable",
        "pushed_status": "not_pushed",
        "origin_main_head_count": 5,
    }
    data.update(overrides)
    (work / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(data), encoding="utf-8")


def _write_project_status(work: Path, phase_id: str) -> None:
    text = (
        "# Project Status\n\n"
        "## Current Phase\n\n"
        f"Phase {phase_id} — Reconciliation Fixture (completed).\n\n"
        "Recommended next repo phase: 206A — Next (not started).\n"
    )
    (work / "PROJECT_STATUS.md").write_text(text, encoding="utf-8")


def _commit_and_push_metadata(work: Path) -> None:
    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "declare phase completion metadata")
    _run_git(work, "push", "origin", "main")


def _commit_hash(work: Path) -> str:
    return _run_git(work, "rev-parse", "--short", "HEAD").stdout.strip()


# ═══════════════════════════════════════════════════════════════════════════
# Unit tests: reconciliation_pending() / live_push_is_clean()
# ═══════════════════════════════════════════════════════════════════════════


def test_no_metadata_is_not_pending(tmp_path):
    work = _init_repo_with_real_origin(tmp_path)
    pending, reason, _ = reconciliation_pending(HarnessPath(work))
    assert pending is False
    assert "no phase-completion metadata" in reason


def test_metadata_matching_canonical_report_is_not_pending(tmp_path):
    work = _init_repo_with_real_origin(tmp_path)
    reports_dir = work / ".pcae" / "phase-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest.json").write_text(json.dumps({"phase_id": "205Z"}), encoding="utf-8")
    _write_metadata(work, phase_id="205Z")

    pending, reason, _ = reconciliation_pending(HarnessPath(work))
    assert pending is False
    assert "already matches" in reason


def test_metadata_phase_id_mismatch_is_pending(tmp_path):
    work = _init_repo_with_real_origin(tmp_path)
    reports_dir = work / ".pcae" / "phase-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest.json").write_text(json.dumps({"phase_id": "114A"}), encoding="utf-8")
    _write_metadata(work, phase_id="205Z")

    pending, reason, metadata = reconciliation_pending(HarnessPath(work))
    assert pending is True
    assert "does not match" in reason
    assert metadata["phase_id"] == "205Z"


def test_missing_canonical_report_is_pending(tmp_path):
    work = _init_repo_with_real_origin(tmp_path)
    _write_metadata(work, phase_id="205Z")

    pending, reason, _ = reconciliation_pending(HarnessPath(work))
    assert pending is True
    assert "no canonical report exists yet" in reason


def test_live_push_is_clean_true_when_pushed(tmp_path, monkeypatch):
    work = _init_repo_with_real_origin(tmp_path)
    monkeypatch.chdir(work)
    assert live_push_is_clean(HarnessPath(work)) is True


def test_live_push_is_clean_false_when_dirty(tmp_path, monkeypatch):
    work = _init_repo_with_real_origin(tmp_path)
    monkeypatch.chdir(work)
    (work / "dirty.txt").write_text("x")
    assert live_push_is_clean(HarnessPath(work)) is False


def test_live_push_is_clean_false_when_unpushed(tmp_path, monkeypatch):
    work = _init_repo_with_real_origin(tmp_path)
    monkeypatch.chdir(work)
    (work / "extra.txt").write_text("x")
    _run_git(work, "add", "extra.txt")
    _run_git(work, "commit", "-m", "unpushed")
    assert live_push_is_clean(HarnessPath(work)) is False


# ═══════════════════════════════════════════════════════════════════════════
# CLI integration: pcae push triggers reconciliation
# ═══════════════════════════════════════════════════════════════════════════


class TestPushReconciliation:
    def test_push_clean_pending_metadata_triggers_reconciliation(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        exit_code = main(["push"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Post-push reconciliation:" in out
        assert "Canonical promotion + notification: completed" in out

    def test_latest_json_updates_after_push(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])

        latest = json.loads((work / ".pcae" / "phase-reports" / "latest.json").read_text())
        assert latest["phase_id"] == "205Z"

    def test_stale_latest_report_is_repaired(self, tmp_path, monkeypatch):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        reports_dir = work / ".pcae" / "phase-reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "latest.json").write_text(json.dumps({"phase_id": "OLD"}), encoding="utf-8")
        (reports_dir / "latest.md").write_text("# Old\nphase_id: OLD\n", encoding="utf-8")
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])

        latest = json.loads((reports_dir / "latest.json").read_text())
        assert latest["phase_id"] == "205Z"
        assert "205Z" in (reports_dir / "latest.md").read_text()

    def test_notification_dispatched_once(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])
        out = capsys.readouterr().out

        assert "Notification dispatch: sent" in out
        marker = read_notification_dispatch_marker(
            work / ".pcae" / "phase-reports" / ".last-notified.json"
        )
        assert marker.get("phase_id") == "205Z"

    def test_duplicate_reconciliation_is_no_op(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])
        capsys.readouterr()
        marker_path = work / ".pcae" / "phase-reports" / ".last-notified.json"
        marker_after_first = marker_path.read_text()

        exit_code = main(["push"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Notification dispatch: sent" not in out
        assert "Post-push reconciliation:" not in out  # not_pending -> silent
        assert marker_path.read_text() == marker_after_first

    def test_dirty_state_does_not_promote(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}])
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        (work / "dirty.txt").write_text("uncommitted")
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")

        main(["push"])
        out = capsys.readouterr().out

        assert "skipped (live push state is not clean" in out
        reports_dir = work / ".pcae" / "phase-reports"
        assert not (reports_dir / "latest.json").exists()

    def test_verify_handoff_passes_after_reconciliation(self, tmp_path, monkeypatch, capsys):
        work = _init_repo_with_real_origin(tmp_path)
        commit = _commit_hash(work)
        _write_metadata(work, phase_id="205Z", phase_commits=[{"hash": commit}], commit_attribution="phase_owned")
        _write_project_status(work, "205Z")
        _commit_and_push_metadata(work)
        monkeypatch.chdir(work)
        monkeypatch.setenv("PCAE_NOTIFY_ENABLED", "1")
        monkeypatch.setenv("PCAE_NOTIFY_SINKS", "noop")
        monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "test-token")
        monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "test-chat")
        monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")

        main(["push"])
        capsys.readouterr()

        exit_code = main(["agent", "verify-handoff", "--json"])
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert payload["status"] != "fail"
        assert not any("phase_id" in f and "does not match" in f for f in payload["failures"])
