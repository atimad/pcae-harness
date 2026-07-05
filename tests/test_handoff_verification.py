"""Phase 114D: Cross-Agent Verification Command.

`pcae agent verify-handoff` is read-only containment infrastructure: it
answers "safe to continue?" for any model, agent, automation, or human
picking up work in this repository, without ever modifying it. These
tests exercise `verify_handoff()` directly (pure-function-style, with a
real local "origin" remote so push state is genuinely determinable) and
through the CLI command.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.handoff_verification import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARNING,
    verify_handoff,
)
from pcae.core.paths import HarnessPath
from pcae.core.phase_reports import write_notification_dispatch_marker


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
    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "baseline")
    _run_git(work, "remote", "add", "origin", str(origin_bare))
    _run_git(work, "push", "-u", "origin", "main")
    return work


def _commit_hash(work: Path) -> str:
    result = _run_git(work, "rev-parse", "--short", "HEAD")
    return result.stdout.strip()


def _write_report(work: Path, **overrides) -> None:
    reports_dir = work / ".pcae" / "phase-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "phase_id": "205Z",
        "phase_name": "Handoff Fixture",
        "status": "completed",
        "summary": "Handoff verification fixture report.",
        "commits": [_commit_hash(work)],
        "files_changed": 1,
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205AA — Next",
        "report_completeness": "complete",
        "created_at": "2026-07-05T00:00:00+00:00",
        "architecture_status": {
            "completed_phase_ids": ["205X", "205Y"],
            "planned": ["205AA — Next"],
        },
    }
    data.update(overrides)
    (reports_dir / "latest.json").write_text(json.dumps(data), encoding="utf-8")
    md_phase_id = overrides.get("_md_phase_id", data["phase_id"])
    (reports_dir / "latest.md").write_text(f"# Phase Report\n\nphase_id: {md_phase_id}\n", encoding="utf-8")


def _write_metadata(work: Path, **overrides) -> None:
    data = {
        "phase_id": "205Z",
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "execution_availability": "unavailable",
    }
    data.update(overrides)
    (work / ".pcae" / "phase-completion-metadata.json").write_text(json.dumps(data), encoding="utf-8")


def _write_project_status(work: Path, current_phase_line: str, recommended: str) -> None:
    text = (
        "# Project Status\n\n"
        "## Current Phase\n\n"
        f"{current_phase_line}\n\n"
        f"Recommended next repo phase: {recommended} (not started).\n"
    )
    (work / "PROJECT_STATUS.md").write_text(text, encoding="utf-8")


def _make_fully_healthy_repo(tmp_path: Path, monkeypatch) -> Path:
    work = _init_repo_with_real_origin(tmp_path)

    # Mirrors this actual repository's own `.pcae/.gitignore` convention
    # (`phase-reports/` is untracked/ignored there too) -- so mutating or
    # deleting a report/marker file in a test never shows up as working
    # tree dirtiness, matching real usage.
    pcae_gitignore = work / ".pcae" / ".gitignore"
    existing = pcae_gitignore.read_text(encoding="utf-8") if pcae_gitignore.exists() else ""
    pcae_gitignore.write_text(existing + "\nphase-reports/\n", encoding="utf-8")
    _run_git(work, "add", ".pcae/.gitignore")
    _run_git(work, "commit", "-m", "ignore phase-reports")
    _run_git(work, "push", "origin", "main")

    commit = _commit_hash(work)
    _write_report(work, commits=[commit])
    _write_metadata(work, phase_commits=[{"hash": commit}])
    _write_project_status(work, "Phase 205Z — Handoff Fixture (completed).", "205AA — Next")
    write_notification_dispatch_marker("205Z", commit, marker_path=work / ".pcae" / "phase-reports" / ".last-notified.json")

    # `verify_handoff` checks git cleanliness against whatever this fixture
    # repo actually tracks -- commit the fixture's own setup files so the
    # "happy path" baseline is genuinely clean and pushed, not incidentally
    # dirty because of untracked fixture output.
    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", "fixture: report, metadata, status, marker")
    _run_git(work, "push", "origin", "main")

    monkeypatch.setenv("PCAE_TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("PCAE_TELEGRAM_CHAT_ID", "test-chat")
    monkeypatch.setenv("PCAE_TELEGRAM_ENABLED", "1")

    # `compute_live_push_state()` (114C) derives push state from the
    # process's current working directory, not from any `root` argument
    # passed to it -- exactly how `pcae phase complete`/`pcae task finish`
    # already consume it. Real CLI usage always matches (the command uses
    # `HarnessPath.cwd()`); direct-call tests need the same chdir their
    # CLI counterparts get for free.
    monkeypatch.chdir(work)
    return work


# ═══════════════════════════════════════════════════════════════════════════
# Happy path
# ═══════════════════════════════════════════════════════════════════════════


def test_clean_pushed_fully_reported_repo_passes(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_PASS, f"failures={result.failures} warnings={result.warnings}"
    assert result.failures == ()
    assert result.recommended_next_action == "proceed"
    assert result.pushed_status == "pushed"
    assert result.execution_availability == "unavailable"


# ═══════════════════════════════════════════════════════════════════════════
# Individual failure/warning scenarios
# ═══════════════════════════════════════════════════════════════════════════


def test_dirty_working_tree_fails(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    (work / "untracked_change.txt").write_text("dirty")

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("dirty" in f for f in result.failures)


def test_unpushed_commits_fail(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    (work / "extra.txt").write_text("x")
    _run_git(work, "add", "extra.txt")
    _run_git(work, "commit", "-m", "unpushed change")

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("origin/main..HEAD" in f for f in result.failures)


def test_missing_latest_report_fails(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    (work / ".pcae" / "phase-reports" / "latest.json").unlink()

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("no canonical phase report found" in f for f in result.failures)


def test_latest_md_json_mismatch_fails(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    (work / ".pcae" / "phase-reports" / "latest.md").write_text("# unrelated content\n", encoding="utf-8")

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("latest.md does not reference" in f for f in result.failures)


def test_metadata_report_phase_mismatch_fails(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    _write_metadata(work, phase_id="999X")

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("does not match canonical report phase_id" in f for f in result.failures)


def test_stale_push_metadata_vs_live_is_detected(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    _write_metadata(work, pushed_status="not_pushed", origin_main_head_count=9)

    result = verify_handoff(HarnessPath(work))

    stale_warning = next((w for w in result.warnings if "stale" in w), None)
    assert stale_warning is not None
    assert "metadata_origin_main_head_count=9" in stale_warning
    assert "live_origin_main_head_count=0" in stale_warning
    # Live push state still correctly reported as pushed at the top level.
    assert result.pushed_status == "pushed"


def test_runtime_execution_available_fails(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    monkeypatch.setattr("pcae.core.handoff_verification.EXECUTION_AVAILABILITY", "available")

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_FAIL
    assert any("execution_availability" in f for f in result.failures)


def test_missing_notification_marker_is_a_warning_not_a_failure(tmp_path, monkeypatch):
    work = _make_fully_healthy_repo(tmp_path, monkeypatch)
    (work / ".pcae" / "phase-reports" / ".last-notified.json").unlink()

    result = verify_handoff(HarnessPath(work))

    assert result.status == STATUS_WARNING
    assert any("no notification dispatch marker" in w for w in result.warnings)
    assert not any("notification" in f for f in result.failures)


# ═══════════════════════════════════════════════════════════════════════════
# CLI: JSON schema, default output, no mutation
# ═══════════════════════════════════════════════════════════════════════════


class TestCliOutput:
    def test_json_output_schema(self, tmp_path, monkeypatch, capsys):
        work = _make_fully_healthy_repo(tmp_path, monkeypatch)
        monkeypatch.chdir(work)

        exit_code = main(["agent", "verify-handoff", "--json"])
        out = capsys.readouterr().out
        payload = json.loads(out)

        assert exit_code == 0
        for key in (
            "status", "checks", "warnings", "failures", "recommended_next_action",
            "latest_completed_phase", "recommended_next_phase", "pushed_status",
            "execution_availability",
        ):
            assert key in payload
        assert isinstance(payload["checks"], list)
        assert all({"name", "status", "detail"} <= set(c) for c in payload["checks"])

    def test_default_output_is_concise_and_human_readable(self, tmp_path, monkeypatch, capsys):
        work = _make_fully_healthy_repo(tmp_path, monkeypatch)
        monkeypatch.chdir(work)

        exit_code = main(["agent", "verify-handoff"])
        out = capsys.readouterr().out

        assert exit_code == 0
        assert "Cross-agent handoff verification: PASS" in out
        assert "Latest completed phase: 205Z" in out
        assert "Recommended next phase: 205AA" in out
        assert "Git: clean, pushed" in out
        assert "Safe to continue: yes" in out

    def test_fail_exit_code_is_one(self, tmp_path, monkeypatch, capsys):
        work = _make_fully_healthy_repo(tmp_path, monkeypatch)
        (work / "dirty.txt").write_text("x")
        monkeypatch.chdir(work)

        exit_code = main(["agent", "verify-handoff"])
        out = capsys.readouterr().out

        assert exit_code == 1
        assert "Cross-agent handoff verification: FAIL" in out
        assert "Safe to continue: no" in out

    def test_command_never_mutates_repository(self, tmp_path, monkeypatch):
        work = _make_fully_healthy_repo(tmp_path, monkeypatch)
        monkeypatch.chdir(work)

        before_status = _run_git(work, "status", "--porcelain=v1").stdout
        before_head = _run_git(work, "rev-parse", "HEAD").stdout

        main(["agent", "verify-handoff"])
        main(["agent", "verify-handoff", "--json"])

        after_status = _run_git(work, "status", "--porcelain=v1").stdout
        after_head = _run_git(work, "rev-parse", "HEAD").stdout

        assert before_status == after_status
        assert before_head == after_head

    def test_model_agnostic_no_identity_fields(self, tmp_path, monkeypatch, capsys):
        """No model/agent/backend identity anywhere in the result -- mirrors
        the Repository Transition Validator's own frozen constraint."""
        work = _make_fully_healthy_repo(tmp_path, monkeypatch)
        monkeypatch.chdir(work)

        main(["agent", "verify-handoff", "--json"])
        out = capsys.readouterr().out
        lowered = out.lower()

        for forbidden in ("claude", "gpt", "anthropic", "openai", "model_id", "agent_id", "backend_id"):
            assert forbidden not in lowered


def test_verify_handoff_function_is_not_cli_specific():
    """`verify_handoff()` takes only a repository root -- no agent/model
    parameter of any kind -- so any caller (CLI, another tool, a future
    consumer) gets the identical, agent-blind verification."""
    import inspect

    from pcae.core.handoff_verification import verify_handoff as fn

    params = list(inspect.signature(fn).parameters)
    assert params == ["root"]
