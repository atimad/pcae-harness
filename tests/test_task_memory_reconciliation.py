"""Tests for task memory auto-reconciliation (Phase 79F).

Tests that pcae doctor task-memory detects drift and --fix repairs
unambiguous issues without deleting files or modifying source code.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.tasks import (
    diagnose_task_memory,
    repair_task_memory,
    TaskMemoryDiagnostics,
)


def _init(tmp_path: Path, monkeypatch) -> Path:
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _write(root: Path, rel: str, content: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


TASK_TEMPLATE = """# Task Contract

## Task ID

{task_id}

## Title

{title}

## Status

{status}

## Mode

implementation

## Goal

TBD

## Allowed Files

- TBD

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-23T00:00:00+00:00
"""


def test_clean_task_memory_reports_clean(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    d = diagnose_task_memory(HarnessPath(root))
    assert not d.has_errors
    assert not d.has_warnings


def test_completed_task_in_active_detected_as_drift(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/active/test-task.md",
           TASK_TEMPLATE.format(task_id="test-task", title="Test", status="done"))
    d = diagnose_task_memory(HarnessPath(root))
    checks = [f.check for f in d.findings]
    assert "done_status_in_active_folder" in checks


def test_fix_moves_completed_active_task_to_done(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/active/test-task.md",
           TASK_TEMPLATE.format(task_id="test-task", title="Test", status="done"))
    result = repair_task_memory(HarnessPath(root))
    repaired_checks = [r.check for r in result.repairs]
    assert "done_status_in_active_folder" in repaired_checks
    assert (root / "tasks" / "done" / "test-task.md").is_file()


def test_active_status_in_done_folder_fixed(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/done/77r-task.md",
           TASK_TEMPLATE.format(task_id="77r-task", title="Phase 77R", status="active"))
    result = repair_task_memory(HarnessPath(root))
    repaired_checks = [r.check for r in result.repairs]
    assert "active_status_in_done_folder" in repaired_checks
    content = (root / "tasks" / "done" / "77r-task.md").read_text()
    assert "completed" in content or "done" in content


def test_fix_never_deletes_task_files(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/done/safe-task.md",
           TASK_TEMPLATE.format(task_id="safe-task", title="Safe", status="active"))
    files_before = set(p.name for p in (root / "tasks" / "done").glob("*.md"))
    repair_task_memory(HarnessPath(root))
    files_after = set(p.name for p in (root / "tasks" / "done").glob("*.md"))
    assert files_before <= files_after


def test_fix_does_not_modify_source_files(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "src/pcae/test.py", "# source\n")
    _write(root, "tasks/done/drift-task.md",
           TASK_TEMPLATE.format(task_id="drift-task", title="Drift", status="active"))
    src_before = (root / "src" / "pcae" / "test.py").read_text()
    repair_task_memory(HarnessPath(root))
    src_after = (root / "src" / "pcae" / "test.py").read_text()
    assert src_before == src_after


def test_json_output_lists_drift(tmp_path, monkeypatch, capsys):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/done/json-task.md",
           TASK_TEMPLATE.format(task_id="json-task", title="JSON Test", status="active"))
    main(["doctor", "task-memory", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert d.get("has_errors") or d.get("has_warnings") or d.get("findings")


def test_dry_run_reports_without_changing(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/done/dryrun-task.md",
           TASK_TEMPLATE.format(task_id="dryrun-task", title="Dry Run", status="active"))
    content_before = (root / "tasks" / "done" / "dryrun-task.md").read_text()
    result = repair_task_memory(HarnessPath(root), dry_run=True)
    content_after = (root / "tasks" / "done" / "dryrun-task.md").read_text()
    assert content_before == content_after
    assert len(result.repairs) > 0


def test_repaired_state_is_clean(tmp_path, monkeypatch):
    root = _init(tmp_path, monkeypatch)
    _write(root, "tasks/done/fixme-task.md",
           TASK_TEMPLATE.format(task_id="fixme-task", title="Fix Me", status="active"))
    result = repair_task_memory(HarnessPath(root))
    assert not result.post_findings
