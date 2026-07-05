"""Tests for Phase 112B.1 -- Planning & Bootstrap Consistency Hardening.

Proves the source-of-truth precedence PROJECT_STATUS.md > tasks/TODO.md
holds mechanically, not just by convention: a stale tasks/TODO.md "next
phase" marker cannot outrank PROJECT_STATUS.md's own current-phase record,
pcae session bootstrap surfaces the comparison explicitly (which source is
authoritative, which was stale, why it was ignored), the recommended next
phase is derived from PROJECT_STATUS.md rather than tasks/TODO.md text, the
real repo's tasks/TODO.md has been repaired to the current roadmap, and
bootstrap still succeeds in the idle/no-active-task state.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.context import (
    CONTEXT_PACK_OPERATIONAL_RULES,
    build_bootstrap_prompt,
    build_context_pack,
    resolve_profile,
)
from pcae.core.paths import HarnessPath

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Local test fixtures (mirrors tests/test_session.py's own local helpers)
# ---------------------------------------------------------------------------


def run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def init_git_repo(root: Path) -> None:
    run_git(root, "init")
    run_git(root, "config", "user.email", "test@example.com")
    run_git(root, "config", "user.name", "Test User")


def commit_baseline(root: Path) -> None:
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "baseline")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_project_status(root: Path, *, current_phase_line: str, recommended_line: str) -> None:
    write_file(
        root / "PROJECT_STATUS.md",
        "# Project Status\n\n## Current Phase\n\n"
        f"{current_phase_line}\n\n"
        f"{recommended_line}\n",
    )


def write_todo(root: Path, *, next_phase_row: str | None) -> None:
    body = "# TODO\n\n## Current Roadmap\n\n| Phase | Name | Status |\n|---|---|---|\n"
    if next_phase_row:
        body += f"| {next_phase_row} | Some Phase | \U0001F51C Next |\n"
    write_file(root / "tasks" / "TODO.md", body)


def minimal_repo(tmp_path: Path) -> HarnessPath:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    (tmp_path / ".pcae").mkdir(exist_ok=True)
    (tmp_path / ".pcae" / "session.json").write_text(
        json.dumps({"active_task": None}), encoding="utf-8"
    )
    (tmp_path / ".pcae" / "provenance-history.json").write_text("[]", encoding="utf-8")
    return HarnessPath(tmp_path)


# ---------------------------------------------------------------------------
# recommended_next_phase extraction
# ---------------------------------------------------------------------------


def test_recommended_next_phase_extracted_from_project_status(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line=(
            "No automatic next repo phase implementation started. Recommended next "
            "repo phase: 112C — Runtime Context Prototype (Observation-Only) (not started)."
        ),
    )
    pack = build_context_pack(root)
    assert pack.roadmap_summary["recommended_next_phase"] == (
        "112C — Runtime Context Prototype (Observation-Only)"
    )


def test_recommended_next_phase_none_when_absent(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase Test.",
        recommended_line="",
    )
    pack = build_context_pack(root)
    assert pack.roadmap_summary["recommended_next_phase"] is None


def test_recommended_next_phase_matches_real_project_status() -> None:
    """The real repo's own PROJECT_STATUS.md must parse cleanly -- this is
    the exact sentence format every 108D+ phase has used."""
    root = HarnessPath(REPO_ROOT)
    pack = build_context_pack(root)
    recommended = pack.roadmap_summary["recommended_next_phase"]
    assert recommended is not None
    assert "113X" in recommended


# ---------------------------------------------------------------------------
# tasks/TODO.md staleness comparison
# ---------------------------------------------------------------------------


def test_todo_marked_as_stale_when_next_phase_number_is_lower(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="90C")
    pack = build_context_pack(root)
    status = pack.roadmap_summary["todo_status"]
    assert status["todo_next_phase"] == "90C"
    assert status["stale"] is True


def test_todo_not_stale_when_consistent_with_current_phase(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="112C")
    pack = build_context_pack(root)
    status = pack.roadmap_summary["todo_status"]
    assert status["todo_next_phase"] == "112C"
    assert status["stale"] is False


def test_todo_status_none_when_no_next_marker_row(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="",
    )
    write_todo(tmp_path, next_phase_row=None)
    pack = build_context_pack(root)
    status = pack.roadmap_summary["todo_status"]
    assert status["todo_next_phase"] is None
    assert status["stale"] is False


def test_todo_status_safe_when_file_absent(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="",
    )
    pack = build_context_pack(root)
    status = pack.roadmap_summary["todo_status"]
    assert status["todo_next_phase"] is None
    assert status["stale"] is False


# ---------------------------------------------------------------------------
# Bootstrap prompt surfaces the comparison explicitly
# ---------------------------------------------------------------------------


def test_bootstrap_prompt_states_stale_source_and_authoritative_source(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="90C")
    pack = build_context_pack(root)
    profile, _ = resolve_profile("implementation")
    prompt = build_bootstrap_prompt(pack, profile)

    assert "Recommended next phase: 112C" in prompt
    assert "Planning note:" in prompt
    assert "tasks/TODO.md marks 90C as next" in prompt
    assert "stale" in prompt
    assert "PROJECT_STATUS.md is authoritative" in prompt
    assert "ignored" in prompt


def test_bootstrap_prompt_confirms_consistency_when_todo_matches(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="112C")
    pack = build_context_pack(root)
    profile, _ = resolve_profile("implementation")
    prompt = build_bootstrap_prompt(pack, profile)

    assert "is consistent with PROJECT_STATUS.md" in prompt
    assert "stale" not in prompt.lower().split("planning note:")[-1].split("\n")[0]


def test_bootstrap_prompt_silent_when_todo_has_no_next_marker(tmp_path: Path) -> None:
    root = minimal_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="",
    )
    write_todo(tmp_path, next_phase_row=None)
    pack = build_context_pack(root)
    profile, _ = resolve_profile("implementation")
    prompt = build_bootstrap_prompt(pack, profile)

    assert "Planning note:" not in prompt


def test_new_operational_rule_states_todo_precedence() -> None:
    assert any(
        "tasks/TODO.md is informational planning notes only" in rule
        for rule in CONTEXT_PACK_OPERATIONAL_RULES
    )
    assert any("never outranks PROJECT_STATUS.md" in rule for rule in CONTEXT_PACK_OPERATIONAL_RULES)


# ---------------------------------------------------------------------------
# Real repo: tasks/TODO.md repaired to the current roadmap
# ---------------------------------------------------------------------------


def test_real_todo_no_longer_marks_90_series_as_next() -> None:
    text = (REPO_ROOT / "tasks" / "TODO.md").read_text(encoding="utf-8")
    lines_with_next_marker = [
        line for line in text.splitlines() if "\U0001F51C Next" in line and line.strip().startswith("|")
    ]
    assert len(lines_with_next_marker) == 1
    assert "113X" in lines_with_next_marker[0]
    assert "90C" not in lines_with_next_marker[0]


def test_real_todo_marks_90_series_table_historical() -> None:
    text = (REPO_ROOT / "tasks" / "TODO.md").read_text(encoding="utf-8")
    assert "Historical: Production v1 Path (90-series, superseded)" in text
    assert "Historical reference only" in text


def test_real_todo_current_roadmap_lists_113x_as_next() -> None:
    text = (REPO_ROOT / "tasks" / "TODO.md").read_text(encoding="utf-8")
    current_section = text.split("## Current Roadmap")[1].split("## Historical")[0]
    assert "113X" in current_section
    assert "Next" in current_section


def test_real_todo_not_flagged_stale_against_real_project_status() -> None:
    root = HarnessPath(REPO_ROOT)
    pack = build_context_pack(root)
    status = pack.roadmap_summary["todo_status"]
    assert status["todo_next_phase"] is not None
    assert status["stale"] is False


def test_source_of_truth_precedence_documented() -> None:
    doc = REPO_ROOT / "docs" / "PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "## 2. Source-of-Truth Precedence" in text
    assert "Active task contract" in text
    assert "tasks/DONE.md" in text
    assert "historical record" in text


# ---------------------------------------------------------------------------
# Bootstrap still succeeds in idle/no-active-task state (regression)
# ---------------------------------------------------------------------------


def test_bootstrap_compact_succeeds_idle_no_active_task(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B.1 — Planning & Bootstrap Consistency Hardening (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="112C")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--profile", "implementation"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Active task: none" in output
    assert "Recommended next phase: 112C" in output


def test_bootstrap_compact_json_includes_todo_status(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    init_harness(HarnessPath(tmp_path))
    init_git_repo(tmp_path)
    write_project_status(
        tmp_path,
        current_phase_line="Phase 112B — Runtime Context Contract Freeze (completed).",
        recommended_line="Recommended next repo phase: 112C — Runtime Context Prototype (not started).",
    )
    write_todo(tmp_path, next_phase_row="90C")
    commit_baseline(tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["session", "bootstrap", "--compact", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert "90C" in data["bootstrap_prompt"]
    assert "stale" in data["bootstrap_prompt"]
