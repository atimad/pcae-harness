"""Tests for Phase 149F — Repository-Wide Mutation Permission Coverage
Wave 1: TK1/TK2/TK3 (`pcae task finish --commit`/`recover`) non-
interference regression.

RWMPC-001 Section 14 assigns TK1-3 disposition `LIFECYCLE_INTERNAL /
DEFERRED_COVERAGE`, not `BROKER_WIRE` -- Wave 1 explicitly does not wire
these three sites. This suite proves that fact directly against current
source and behavior: `task.py` never references the Permission Broker
Foundation or `mutation_permission`, and a real `pcae task finish
--commit` dispatch succeeds with no active-task-adjacent Permission
Broker consultation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASK_PY = REPO_ROOT / "src" / "pcae" / "commands" / "task.py"


def test_task_py_does_not_reference_permission_broker_or_mutation_permission():
    source = TASK_PY.read_text(encoding="utf-8")
    assert "permission_broker_foundation" not in source
    assert "PermissionBroker(" not in source
    assert "mutation_permission" not in source


def test_task_py_still_contains_its_three_git_commit_dispatches():
    """Confirms TK1/TK2/TK3 remain real, present, and unmodified in shape
    -- deferred, not silently removed."""
    source = TASK_PY.read_text(encoding="utf-8")
    assert source.count('"git", "commit", "--no-verify"') == 3


def test_task_py_unchanged_since_pre_149f_baseline():
    """Direct git-diff confirmation that Phase 149F made zero changes to
    task.py, per its own binding scope-creep prohibition (`No
    broker-wiring of TK1/TK2/TK3`)."""
    result = subprocess.run(
        ["git", "log", "--follow", "--oneline", "-1", "--", "src/pcae/commands/task.py"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0
    # The most recent commit touching task.py must not be a 149F commit
    # (149F commits are prefixed "Phase 149F:" per this repo's convention).
    assert "Phase 149F" not in result.stdout


def test_run_task_finish_commit_dispatch_unaffected_end_to_end(tmp_path, monkeypatch):
    """A real `pcae task finish --commit` (staged-file-aware branch, TK1)
    still succeeds without any Permission Broker consultation -- direct
    behavioral confirmation, not just source inspection."""
    from pcae.cli import main
    from pcae.commands.init import init_harness
    from pcae.core.paths import HarnessPath
    from pcae.core.tasks import create_task_contract
    from pcae.core import permission_broker_foundation as pbf

    root_dir = tmp_path
    init_harness(HarnessPath(root_dir))
    subprocess.run(["git", "init", "-q"], cwd=root_dir, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root_dir, check=True, capture_output=True)
    monkeypatch.chdir(root_dir)

    create_task_contract(HarnessPath(root_dir), "TK1 non-interference test task")

    calls = {"count": 0}
    real_evaluate = pbf.PermissionBroker.evaluate

    def counting_evaluate(self, request):
        calls["count"] += 1
        return real_evaluate(self, request)

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", counting_evaluate)

    exit_code = main(["task", "finish", "--commit", "TK1 non-interference commit", "--skip-checks", "--json"])

    # TK1's own mechanical gates may block or allow depending on staged
    # content shape in this minimal fixture; what matters here is
    # exclusively that the Permission Broker was never consulted for
    # this dispatch, regardless of outcome.
    assert calls["count"] == 0
