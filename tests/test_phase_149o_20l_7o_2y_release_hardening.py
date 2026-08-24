"""Phase 149O.20L.7O.2Y -- Post-v0.3 Release Hardening and Release Scope
Reassessment.

Fresh tests for the bounded hardening this phase implements (the W.1
malformed-agent-lock finding's uncaught-exception defect), plus fresh
evidence for the release-scope questions this phase answers: package
boundary, supported-agent-matrix facts, and producer-identity
non-authority under the repaired code path. Does not reuse 2W.1/2X.1's
own test functions.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import agent as agent_module
from pcae.core import intake
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "2y@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "2Y"], cwd=path, check=True)
    (path / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "add", "seed.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


def _root(tmp_path, name="repo") -> HarnessPath:
    d = tmp_path / name
    d.mkdir()
    _git_repo(d)
    return HarnessPath(d)


def _task(root: HarnessPath, allowed=("app/allowed/**",)) -> str:
    contract = create_task_contract(
        root, "2Y hardening verification task",
        created_at=datetime(2026, 8, 24, 22, 0, tzinfo=timezone.utc),
        allowed_files=allowed,
    )
    return contract.task_id


def _write(tmp_path, name, text) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------------------------------------------------------------------
# Bounded repair: malformed agent-lock now rejected cleanly, not raised
# ---------------------------------------------------------------------------

def test_derive_producer_provenance_rejects_malformed_lock_cleanly(tmp_path):
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")

    producer, errors = intake.derive_producer_provenance(root, None)
    assert producer is None
    assert len(errors) == 1
    assert errors[0].startswith("malformed_agent_lock:")


def test_derive_producer_provenance_rejects_truncated_lock_cleanly(tmp_path):
    """A different malformed-JSON shape (truncated file) hits the same path."""
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text('{"agent_id": "codex-o')

    producer, errors = intake.derive_producer_provenance(root, None)
    assert producer is None
    assert errors[0].startswith("malformed_agent_lock:")


def test_build_intake_candidate_from_files_does_not_raise_on_malformed_lock(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("not json at all")

    content = _write(tmp_path, "c.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-1",
        file_specs=[f"app/allowed/f.txt:create:{content}"],
    )
    assert result["candidate"] is None
    assert any(e.startswith("malformed_agent_lock:") for e in result["errors"])


def test_cli_intake_from_files_no_traceback_on_malformed_lock(tmp_path, monkeypatch, capsys):
    """End-to-end CLI-level regression for the repair: this used to crash
    with a raw Python traceback (uncaught JSONDecodeError propagating all
    the way through pcae.cli.main); it must now print a clean rejection."""
    from pcae.cli import main
    from pcae.commands.init import init_harness

    root_dir = tmp_path / "cliroot"
    root_dir.mkdir()
    _git_repo(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    task_id = _task(root)
    lock_path = root_dir / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")
    content_file = root_dir / "content.txt"
    content_file.write_text("hi\n")
    monkeypatch.chdir(root_dir)

    exit_code = main([
        "intake", "from-files",
        "--task-id", task_id,
        "--candidate-id", "cli-cand-1",
        "--file", f"app/allowed/x.txt:create:{content_file}",
        "--summary", "s",
        "--json",
    ])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Traceback" not in out
    result = json.loads(out)
    assert result["accepted"] is False
    assert any(e.startswith("malformed_agent_lock:") for e in result["rejection_reasons"])


def test_malformed_lock_repair_does_not_weaken_no_lock_fallback(tmp_path):
    """The repair must reject a malformed lock outright, not silently
    treat it as equivalent to "no lock" (which would accept an explicit
    --producer even though a real lock was intended but corrupted)."""
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")

    # Even with an explicit producer supplied, a malformed lock must still
    # be rejected -- it must NOT silently fall through to the "no lock"
    # candidate-sourced path and accept the explicit producer.
    producer, errors = intake.derive_producer_provenance(root, "explicit-producer")
    assert producer is None
    assert errors[0].startswith("malformed_agent_lock:")


def test_read_agent_lock_low_level_function_unchanged_still_raises(tmp_path):
    """The repair is scoped to derive_producer_provenance's call site, not
    to agent.read_agent_lock itself -- its contract is unspecified for
    malformed input and other callers may rely on it raising."""
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")

    with pytest.raises(json.JSONDecodeError):
        agent_module.read_agent_lock(root)


def test_repair_does_not_affect_well_formed_lock_behavior(tmp_path):
    """Regression guard: the try/except must not change behavior for the
    ordinary well-formed-lock path."""
    root = _root(tmp_path)
    agent_module.acquire_agent_lock(
        root, "claude-local", acquired_at=datetime(2026, 8, 24, 22, 0, tzinfo=timezone.utc),
    )
    producer, errors = intake.derive_producer_provenance(root, None)
    assert errors == []
    assert producer == {"kind": "claude-local", "source": "agent_lock"}


# ---------------------------------------------------------------------------
# Empty agent_id finding: independently reconfirmed SAFE-TO-DEFER
# ---------------------------------------------------------------------------

def test_empty_agent_id_cannot_impersonate_a_registered_identity(tmp_path):
    """Confirm the empty-agent_id finding's harm ceiling: an empty
    producer.kind is not, and cannot become, a real registered identity
    someone could confuse with a legitimate agent."""
    root = _root(tmp_path)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"agent_id": ""}))

    producer, errors = intake.derive_producer_provenance(root, None)
    assert errors == []
    assert producer["kind"] == ""
    assert agent_module.get_agent_by_id("") is None


# ---------------------------------------------------------------------------
# Producer-to-authority non-flow re-confirmed under the repaired code path
# ---------------------------------------------------------------------------

def test_authority_fields_unaffected_by_malformed_lock_rejection(tmp_path):
    """A malformed-lock rejection must fail closed -- no partial ECP/intake
    record should be created, and no authority field should be set."""
    root = _root(tmp_path)
    task_id = _task(root)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("garbage")

    content = _write(tmp_path, "c2.txt", "y\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-2",
        file_specs=[f"app/allowed/f2.txt:create:{content}"],
    )
    assert result["candidate"] is None
    records_dir = root.path / ".pcae" / "intake-candidates"
    assert not records_dir.exists() or not any(records_dir.iterdir())
