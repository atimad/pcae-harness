"""Phase 149O.20L.7O.2W -- Generic Producer Intake Helper and Session
Provenance Integration.

Verifies the shared, producer-neutral `pcae.core.intake` helper
(`build_intake_candidate_from_files` / `derive_producer_provenance`) and
the `pcae intake from-files` CLI surface: producer provenance is derived
from the active PCAE governance agent lock (`.pcae/agent-lock.json`) when
one exists, is preserved verbatim for an explicit external/unbootstrapped
producer when none exists, and never influences any allow/deny/authority
decision regardless of which identity produced the candidate. Also
verifies the governance agent lock's `active_task`/`git_branch` snapshot
fields are never trusted as scope or base-commit authority.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import agent as agent_module
from pcae.core import intake
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init_git_root(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def _head(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()


def _setup(tmp_path, name="root", allowed_files=("src/allowed/**",)) -> tuple[HarnessPath, str, str]:
    root_dir = tmp_path / name
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root, "2W provenance integration task",
        created_at=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        allowed_files=allowed_files,
    )
    return root, contract.task_id, _head(root_dir)


def _write_content(tmp_path, name, text) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------------------------------------------------------------------
# Shared generic candidate construction: repo binding, base commit, hashing
# ---------------------------------------------------------------------------

def test_shared_helper_derives_repo_binding_and_base_commit(tmp_path):
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "c1.py", "print(1)\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-1",
        file_specs=[f"src/allowed/c1.py:create:{content_file}"],
        explicit_producer_kind="external-tool",
    )
    assert build_result["errors"] == []
    candidate = build_result["candidate"]
    assert candidate["repo_binding"]["repo_fingerprint"] == intake.compute_repo_fingerprint(root)
    assert candidate["repo_binding"]["base_commit"] == head


def test_shared_helper_content_hash_matches_manual_computation(tmp_path):
    root, task_id, head = _setup(tmp_path)
    text = "print('hashed')\n"
    content_file = _write_content(tmp_path, "c2.py", text)
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-2",
        file_specs=[f"src/allowed/c2.py:create:{content_file}"],
        explicit_producer_kind="external-tool",
    )
    change = build_result["candidate"]["proposed_changes"][0]
    assert change["content_hash_after"] == intake.compute_content_hash(text)


def test_shared_helper_rejects_no_file_changes(tmp_path):
    root, task_id, head = _setup(tmp_path)
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-empty",
        file_specs=[], explicit_producer_kind="external-tool",
    )
    assert build_result["candidate"] is None
    assert "no_file_changes_supplied" in build_result["errors"]


# ---------------------------------------------------------------------------
# Producer provenance: lock-derived, custom identity, no-lock fallback
# ---------------------------------------------------------------------------

def test_lock_derived_producer_claude_identity(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "claude-local")
    content_file = _write_content(tmp_path, "c3.py", "x = 1\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-claude",
        file_specs=[f"src/allowed/c3.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    producer = build_result["candidate"]["producer"]
    assert producer["kind"] == "claude-local"
    assert producer["source"] == "agent_lock"


def test_lock_derived_producer_codex_identity_no_dedicated_adapter(tmp_path):
    """Codex gets identical generic-helper treatment with no Codex-specific
    parser or adapter -- only its bootstrapped agent-lock identity differs."""
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-local")
    content_file = _write_content(tmp_path, "c4.py", "x = 2\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-codex",
        file_specs=[f"src/allowed/c4.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    producer = build_result["candidate"]["producer"]
    assert producer["kind"] == "codex-local"
    assert producer["source"] == "agent_lock"

    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is True


def test_lock_derived_producer_arbitrary_custom_identity_preserved(tmp_path):
    """The governance agent lock still accepts arbitrary agent IDs (Phase
    149O.20L.7O.2W does not narrow this); the helper must preserve the
    literal value as descriptive provenance, not normalize or reject it."""
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "my-custom-agent")
    content_file = _write_content(tmp_path, "c5.py", "x = 3\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-custom",
        file_specs=[f"src/allowed/c5.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    assert build_result["candidate"]["producer"]["kind"] == "my-custom-agent"


def test_no_lock_requires_explicit_producer(tmp_path):
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "c6.py", "x = 4\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-no-lock",
        file_specs=[f"src/allowed/c6.py:create:{content_file}"],
    )
    assert build_result["candidate"] is None
    assert "no_active_agent_lock_and_no_explicit_producer_supplied" in build_result["errors"]


def test_no_lock_with_explicit_producer_preserves_v0_3_compatibility(tmp_path):
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "c7.py", "x = 5\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-external",
        file_specs=[f"src/allowed/c7.py:create:{content_file}"],
        explicit_producer_kind="fully-external-producer",
    )
    assert build_result["errors"] == []
    producer = build_result["candidate"]["producer"]
    assert producer["kind"] == "fully-external-producer"
    assert producer["source"] == "candidate"
    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is True


def test_producer_conflict_with_active_lock_rejected_deterministically(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-local")
    content_file = _write_content(tmp_path, "c8.py", "x = 6\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-conflict",
        file_specs=[f"src/allowed/c8.py:create:{content_file}"],
        explicit_producer_kind="claude-local",
    )
    assert build_result["candidate"] is None
    assert any("producer_conflicts_with_active_agent_lock" in e for e in build_result["errors"])


def test_producer_matching_active_lock_is_not_a_conflict(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-local")
    content_file = _write_content(tmp_path, "c9.py", "x = 7\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-matching",
        file_specs=[f"src/allowed/c9.py:create:{content_file}"],
        explicit_producer_kind="codex-local",
    )
    assert build_result["errors"] == []
    assert build_result["candidate"]["producer"]["kind"] == "codex-local"


# ---------------------------------------------------------------------------
# Producer provenance is descriptive only: no effect on allow/deny/authority
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent_id", ["claude-local", "codex-local", "a-wholly-fictional-agent"])
def test_allow_decision_identical_across_producers(tmp_path, agent_id):
    root, task_id, head = _setup(tmp_path, name=f"repo-{agent_id}")
    agent_module.acquire_agent_lock(root, agent_id)
    content_file = _write_content(tmp_path, f"ok-{agent_id}.py", "print('ok')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id=f"cand-allow-{agent_id}",
        file_specs=[f"src/allowed/ok.py:create:{content_file}"],
    )
    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False


@pytest.mark.parametrize("agent_id", ["claude-local", "codex-local", "a-wholly-fictional-agent"])
def test_deny_decision_identical_across_producers_out_of_scope(tmp_path, agent_id):
    root, task_id, head = _setup(tmp_path, name=f"repo-deny-{agent_id}")
    agent_module.acquire_agent_lock(root, agent_id)
    content_file = _write_content(tmp_path, f"bad-{agent_id}.py", "print('bad')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id=f"cand-deny-{agent_id}",
        file_specs=[f"src/forbidden/bad.py:create:{content_file}"],
    )
    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


def test_producer_field_cannot_set_authority_fields(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "claude-local")
    content_file = _write_content(tmp_path, "auth.py", "print('x')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-authority",
        file_specs=[f"src/allowed/auth.py:create:{content_file}"],
    )
    candidate = build_result["candidate"]
    candidate["producer"]["execution_allowed"] = True
    candidate["producer"]["promotion_authorized"] = True
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["execution_allowed"] is False
    assert ecp["promotion_executed"] is False


# ---------------------------------------------------------------------------
# Task-scope and base-commit authority remain independent of the lock's
# own active_task/git_branch snapshot fields
# ---------------------------------------------------------------------------

def test_lock_active_task_snapshot_not_trusted_for_scope(tmp_path):
    root, task_id, head = _setup(tmp_path)
    # Acquire the lock while this task is active, snapshotting it into the
    # lock's own active_task field.
    agent_module.acquire_agent_lock(root, "claude-local")
    lock = agent_module.read_agent_lock(root)
    assert lock.data.get("active_task", {}).get("id") == task_id

    # Now transition to a second task -- the lock's snapshot goes stale,
    # but the helper must use current canonical task state, not the lock.
    from pcae.core.tasks import find_latest_active_task
    second_contract = create_task_contract(
        root, "second task after lock snapshot",
        created_at=datetime(2026, 8, 24, 13, 0, tzinfo=timezone.utc),
        allowed_files=("src/second/**",),
    )
    current = find_latest_active_task(root)
    assert current.task_id == second_contract.task_id != task_id

    content_file = _write_content(tmp_path, "second.py", "print('second')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=second_contract.task_id, candidate_id="cand-second-task",
        file_specs=[f"src/second/second.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is True

    # A candidate still targeting the now-superseded task (the one the
    # stale lock snapshot names) must be rejected -- scope authority comes
    # from canonical current-task state, never from the lock's snapshot.
    stale_build = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-stale-task",
        file_specs=[f"src/allowed/stale.py:create:{content_file}"],
    )
    stale_result = intake.validate_and_ingest_intake_candidate(root, stale_build["candidate"])
    assert stale_result["accepted"] is False
    assert any("task_not_active" in r for r in stale_result["rejection_reasons"])


def test_lock_git_branch_snapshot_not_used_as_base_authority(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "claude-local")
    lock = agent_module.read_agent_lock(root)
    assert lock.data.get("git_branch") is not None

    # Advance HEAD after the lock snapshot was taken.
    (root.path / "extra.txt").write_text("more\n")
    subprocess.run(["git", "add", "extra.txt"], cwd=root.path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "advance head"], cwd=root.path, check=True)
    new_head = _head(root.path)
    assert new_head != head

    content_file = _write_content(tmp_path, "post-advance.py", "print('new')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-post-advance",
        file_specs=[f"src/allowed/post-advance.py:create:{content_file}"],
    )
    # base_commit is derived from real current HEAD via git rev-parse, not
    # from anything cached in the lock -- it reflects the repo's actual
    # current state.
    assert build_result["candidate"]["repo_binding"]["base_commit"] == new_head


# ---------------------------------------------------------------------------
# Stale lock: descriptive provenance still derives; no new authority rule
# ---------------------------------------------------------------------------

def test_stale_lock_still_used_as_descriptive_provenance(tmp_path, monkeypatch):
    root, task_id, head = _setup(tmp_path)
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    agent_module.acquire_agent_lock(root, "claude-local", acquired_at=old_time)
    status = agent_module.build_agent_status(root)
    assert status["stale"] is True

    content_file = _write_content(tmp_path, "stale-lock.py", "print('x')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-stale-lock",
        file_specs=[f"src/allowed/stale-lock.py:create:{content_file}"],
    )
    # Staleness is advisory (per existing agent-lock semantics); the
    # helper does not invent a new fail-closed rule around it, and still
    # derives descriptive provenance from the (stale) lock.
    assert build_result["errors"] == []
    assert build_result["candidate"]["producer"]["kind"] == "claude-local"


# ---------------------------------------------------------------------------
# CLI surface: pcae intake from-files
# ---------------------------------------------------------------------------

def _run_cli(root_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args],
        cwd=root_dir, capture_output=True, text=True,
    )


def test_cli_from_files_end_to_end_with_bootstrapped_lock(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "claude-local")
    content_file = _write_content(tmp_path, "cli1.py", "print('cli')\n")
    proc = _run_cli(
        root.path, "intake", "from-files",
        "--task-id", task_id, "--candidate-id", "cli-cand-1",
        "--file", f"src/allowed/cli1.py:create:{content_file}",
        "--summary", "cli test", "--json",
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["accepted"] is True

    stored = intake.lookup_intake_record(root, out["intake_id"])
    assert stored["producer"]["kind"] == "claude-local"
    assert stored["producer"]["source"] == "agent_lock"


def test_cli_from_files_no_lock_no_producer_fails_clearly(tmp_path):
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "cli2.py", "print('x')\n")
    proc = _run_cli(
        root.path, "intake", "from-files",
        "--task-id", task_id, "--candidate-id", "cli-cand-2",
        "--file", f"src/allowed/cli2.py:create:{content_file}",
        "--json",
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    out = json.loads(proc.stdout)
    assert "no_active_agent_lock_and_no_explicit_producer_supplied" in out["rejection_reasons"]


def test_cli_from_files_dry_run_does_not_submit(tmp_path):
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "cli3.py", "print('x')\n")
    proc = _run_cli(
        root.path, "intake", "from-files",
        "--task-id", task_id, "--candidate-id", "cli-cand-3",
        "--file", f"src/allowed/cli3.py:create:{content_file}",
        "--producer", "dry-run-producer", "--dry-run", "--json",
    )
    assert proc.returncode == 0
    candidate = json.loads(proc.stdout)
    assert candidate["candidate_id"] == "cli-cand-3"
    listed = intake.list_intake_records(root)
    assert listed == []


def test_cli_from_files_help_does_not_imply_authorization(tmp_path):
    root, task_id, head = _setup(tmp_path)
    proc = _run_cli(root.path, "intake", "from-files", "--help")
    assert proc.returncode == 0
    text = proc.stdout.lower()
    for banned in ("this command applies", "this command executes", "this command approves",
                   "this command authorizes", "automatically promotes"):
        assert banned not in text
