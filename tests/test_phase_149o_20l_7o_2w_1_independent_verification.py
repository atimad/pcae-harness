"""Phase 149O.20L.7O.2W.1 -- Independent Verification of the Generic
Producer Intake Helper and Session Provenance Integration (149O.20L.7O.2W).

Freshly constructed fixtures and assertions, re-deriving the governing
properties directly from `pcae.core.intake` / `pcae.core.agent` rather than
trusting the 2W report or 2W test suite as an oracle. Where this suite
disagrees with 2W's own framing (malformed governance-lock handling), the
disagreement is the point -- see test_malformed_agent_lock_json_*.
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


def _git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "w1@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "W1"], cwd=path, check=True)
    (path / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "add", "seed.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=path, check=True)


def _head(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()


def _task(root: HarnessPath, allowed=("app/allowed/**",)) -> str:
    contract = create_task_contract(
        root, "W.1 verification task",
        created_at=datetime(2026, 8, 24, 20, 0, tzinfo=timezone.utc),
        allowed_files=allowed,
    )
    return contract.task_id


def _root(tmp_path, name="repo") -> HarnessPath:
    d = tmp_path / name
    d.mkdir()
    _git_repo(d)
    return HarnessPath(d)


def _write(tmp_path, name, text) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------------------------------------------------------------------
# 4. Lock-derived producer behavior -- identities beyond the registry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "agent_id",
    [
        "claude-local",
        "codex-local",
        "totally-unregistered-identity",
        "custom.id-with_punct+chars",
        "not-in-capability-registry-or-backend-vocab",
    ],
)
def test_lock_derived_producer_arbitrary_identity_not_registry_gated(tmp_path, agent_id):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, agent_id)

    content = _write(tmp_path, "c1.txt", "hello\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-1",
        file_specs=[f"app/allowed/f.txt:create:{content}"],
    )
    assert result["errors"] == []
    assert result["candidate"]["producer"]["kind"] == agent_id
    assert result["candidate"]["producer"]["source"] == "agent_lock"


# ---------------------------------------------------------------------------
# 5. Vocabulary-mismatch containment: literal preservation, no normalization
# ---------------------------------------------------------------------------

def test_codex_local_lock_identity_not_normalized_to_codex(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, "codex-local")

    content = _write(tmp_path, "c2.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-2",
        file_specs=[f"app/allowed/f2.txt:create:{content}"],
    )
    assert result["candidate"]["producer"]["kind"] == "codex-local"
    assert result["candidate"]["producer"]["kind"] != "codex"


def test_backend_session_lock_vocabulary_is_a_separate_store(tmp_path):
    # The narrower backend/session vocabulary lives at a different path
    # (.pcae/agent-locks/latest.json) and is untouched by the governance
    # agent lock this helper reads (.pcae/agent-lock.json).
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, "codex-local")
    backend_dir = root.path / ".pcae" / "agent-locks"
    backend_dir.mkdir(parents=True, exist_ok=True)
    (backend_dir / "latest.json").write_text(json.dumps({"session_agent": "codex"}))

    content = _write(tmp_path, "c3.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-3",
        file_specs=[f"app/allowed/f3.txt:create:{content}"],
    )
    # The governance-lock literal value wins; the backend vocabulary is not
    # consulted at all by this helper.
    assert result["candidate"]["producer"]["kind"] == "codex-local"


# ---------------------------------------------------------------------------
# 6. Lock / explicit-candidate mismatch
# ---------------------------------------------------------------------------

def test_explicit_producer_conflicting_with_lock_rejected(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, "claude-local")

    content = _write(tmp_path, "c4.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-4",
        file_specs=[f"app/allowed/f4.txt:create:{content}"],
        explicit_producer_kind="codex-local",
    )
    assert result["candidate"] is None
    assert any("producer_conflicts_with_active_agent_lock" in e for e in result["errors"])


def test_explicit_producer_matching_lock_is_accepted_not_treated_as_conflict(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, "claude-local")

    content = _write(tmp_path, "c5.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-5",
        file_specs=[f"app/allowed/f5.txt:create:{content}"],
        explicit_producer_kind="claude-local",
    )
    assert result["errors"] == []
    assert result["candidate"]["producer"]["kind"] == "claude-local"
    assert result["candidate"]["producer"]["source"] == "agent_lock"


# ---------------------------------------------------------------------------
# 7. No-lock compatibility -- must not invent identity, must not require bootstrap
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent_id", ["some-external-tool", "fictional-producer-9000"])
def test_no_lock_explicit_producer_still_works_unbootstrapped(tmp_path, agent_id):
    root = _root(tmp_path)
    task_id = _task(root)
    assert agent_module.read_agent_lock(root) is None

    content = _write(tmp_path, "c6.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-6",
        file_specs=[f"app/allowed/f6.txt:create:{content}"],
        explicit_producer_kind=agent_id,
    )
    assert result["errors"] == []
    assert result["candidate"]["producer"]["kind"] == agent_id
    assert result["candidate"]["producer"]["source"] == "candidate"


def test_no_lock_no_explicit_producer_does_not_invent_identity(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    content = _write(tmp_path, "c7.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-7",
        file_specs=[f"app/allowed/f7.txt:create:{content}"],
    )
    assert result["candidate"] is None
    assert result["errors"] == ["no_active_agent_lock_and_no_explicit_producer_supplied"]


# ---------------------------------------------------------------------------
# 8. Malformed / stale lock handling -- FRESH FINDING, disagrees with the
#    "never raises for ordinary input problems" docstring claim.
# ---------------------------------------------------------------------------

def test_malformed_agent_lock_json_raises_uncaught_exception(tmp_path):
    """CONFIRMED defect (non-blocking, see phase report): a malformed
    `.pcae/agent-lock.json` is not an exotic adversarial input -- it is
    exactly the kind of "ordinary input problem" build_intake_candidate_
    from_files's own docstring promises never to raise for. `read_agent_lock`
    does an uncaught `json.loads`, so this helper raises `JSONDecodeError`
    instead of returning a rejection tuple, and `run_intake_from_files` in
    pcae.commands.intake has no try/except around the call, so the CLI
    would crash with a traceback rather than a clean rejection."""
    root = _root(tmp_path)
    task_id = _task(root)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")

    content = _write(tmp_path, "c8.txt", "x\n")
    with pytest.raises(json.JSONDecodeError):
        intake.build_intake_candidate_from_files(
            root, task_id=task_id, candidate_id="cand-8",
            file_specs=[f"app/allowed/f8.txt:create:{content}"],
        )


def test_malformed_agent_lock_missing_agent_id_field_falls_back_to_empty_string(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    lock_path = root.path / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"acquired_at": "2026-08-24T00:00:00+00:00"}))

    content = _write(tmp_path, "c9.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-9",
        file_specs=[f"app/allowed/f9.txt:create:{content}"],
    )
    # AgentLock.agent_id property degrades missing/non-str values to "",
    # which this helper then happily uses as the producer kind -- an empty
    # producer.kind is accepted (schema does not forbid it), stored purely
    # descriptively, and does not affect the accept/reject decision below.
    assert result["errors"] == []
    assert result["candidate"]["producer"]["kind"] == ""


def test_stale_lock_by_age_still_used_descriptively_no_freshness_gate(tmp_path):
    """derive_producer_provenance does not consult staleness at all --
    freshness is a session/agent-status concept (build_agent_status),
    never checked by this helper. A lock acquired long ago is still read
    verbatim. This is intentional per the phase's own semantics (producer
    is descriptive only) but is worth pinning explicitly."""
    root = _root(tmp_path)
    task_id = _task(root)
    old_ts = datetime(2020, 1, 1, tzinfo=timezone.utc)
    agent_module.acquire_agent_lock(root, "claude-local", acquired_at=old_ts)

    content = _write(tmp_path, "c10.txt", "x\n")
    result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-10",
        file_specs=[f"app/allowed/f10.txt:create:{content}"],
    )
    assert result["candidate"]["producer"]["kind"] == "claude-local"


# ---------------------------------------------------------------------------
# 9. Task-scope isolation: lock.active_task must never gate acceptance
# ---------------------------------------------------------------------------

def test_lock_active_task_stale_snapshot_does_not_gate_or_widen_scope(tmp_path):
    root = _root(tmp_path)
    real_task_id = _task(root)

    # Acquire the lock, then transition to a second task so the lock's
    # frozen active_task snapshot now names a task that is no longer
    # canonically active -- while build_intake_candidate_from_files is
    # called with the CURRENT canonical task id.
    agent_module.acquire_agent_lock(root, "claude-local")
    stale_lock = agent_module.read_agent_lock(root)
    assert stale_lock.data["active_task"]["id"] == real_task_id

    # Corrupt the on-disk lock snapshot to point at a task that never
    # existed, simulating an arbitrarily stale/adversarial snapshot.
    lock_path = root.path / ".pcae" / "agent-lock.json"
    data = json.loads(lock_path.read_text())
    data["active_task"] = {"id": "task-that-does-not-exist", "title": "phantom"}
    lock_path.write_text(json.dumps(data))

    content = _write(tmp_path, "c11.txt", "x\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=real_task_id, candidate_id="cand-11",
        file_specs=[f"app/allowed/f11.txt:create:{content}"],
    )
    assert build_result["errors"] == []
    # producer.kind still comes from the lock (agent_id, unaffected by
    # the active_task corruption); scope acceptance below must come from
    # canonical current task state, not the lock's stale active_task.
    ingest = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert ingest["accepted"] is True

    # Conversely: candidate declares the PHANTOM task id (matching the
    # stale lock snapshot) instead of the real canonical task -- must be
    # rejected as task_not_active, proving the lock snapshot alone cannot
    # manufacture scope for a task that isn't canonically active.
    build_result_2 = intake.build_intake_candidate_from_files(
        root, task_id="task-that-does-not-exist", candidate_id="cand-11b",
        file_specs=[f"app/allowed/f11b.txt:create:{content}"],
    )
    ingest_2 = intake.validate_and_ingest_intake_candidate(root, build_result_2["candidate"])
    assert ingest_2["accepted"] is False
    assert ingest_2["rejection_reasons"] == ["task_not_active"]


# ---------------------------------------------------------------------------
# 10. Base/repository authority isolation: lock.git_branch must never be
#     used for base-commit / repo-fingerprint authority.
# ---------------------------------------------------------------------------

def test_lock_git_branch_snapshot_never_consulted_for_base_authority(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, "claude-local")

    # Corrupt the lock's git_branch snapshot to a nonsense value.
    lock_path = root.path / ".pcae" / "agent-lock.json"
    data = json.loads(lock_path.read_text())
    data["git_branch"] = "branch-that-does-not-exist-anywhere"
    lock_path.write_text(json.dumps(data))

    real_head = _head(root.path)
    content = _write(tmp_path, "c12.txt", "x\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-12",
        file_specs=[f"app/allowed/f12.txt:create:{content}"],
    )
    assert build_result["errors"] == []
    # base_commit must be the real current HEAD (via `git rev-parse HEAD`),
    # not anything derived from the corrupted git_branch snapshot.
    assert build_result["candidate"]["repo_binding"]["base_commit"] == real_head


# ---------------------------------------------------------------------------
# 11. Producer-to-authority non-flow: differential ALLOW/DENY across
#     identically-scoped candidates that differ only in producer identity.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent_id", ["claude-local", "codex-local", "wholly-arbitrary-id"])
def test_producer_identity_does_not_change_in_scope_acceptance(tmp_path, agent_id):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, agent_id)
    content = _write(tmp_path, f"c13-{agent_id}.txt", "x\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id=f"cand-13-{agent_id}",
        file_specs=[f"app/allowed/f13-{agent_id}.txt:create:{content}"],
    )
    ingest = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert ingest["accepted"] is True
    assert ingest["execution_allowed"] is False
    assert ingest["promotion_executed"] is False


@pytest.mark.parametrize("agent_id", ["claude-local", "codex-local", "wholly-arbitrary-id"])
def test_producer_identity_does_not_change_out_of_scope_denial(tmp_path, agent_id):
    root = _root(tmp_path)
    task_id = _task(root)
    agent_module.acquire_agent_lock(root, agent_id)
    content = _write(tmp_path, f"c14-{agent_id}.txt", "x\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id=f"cand-14-{agent_id}",
        file_specs=[f"OUT_OF_SCOPE/f14-{agent_id}.txt:create:{content}"],
    )
    ingest = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert ingest["accepted"] is False
    assert ingest["rejection_reasons"] == [f"out_of_scope_path:OUT_OF_SCOPE/f14-{agent_id}.txt"]


def test_producer_field_never_read_for_authority_by_ingest(tmp_path, monkeypatch):
    """Directly prove non-consumption: forge a candidate whose producer
    object contains authority-shaped keys the ingest path could plausibly
    (but must not) special-case."""
    root = _root(tmp_path)
    task_id = _task(root)
    content = _write(tmp_path, "c15.txt", "x\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-15",
        file_specs=[f"app/allowed/f15.txt:create:{content}"],
        explicit_producer_kind="claude-local",
    )
    candidate = build_result["candidate"]
    candidate["producer"]["execution_allowed"] = True
    candidate["producer"]["promotion_authorized"] = True
    candidate["producer"]["kind"] = "pcae-native"  # try to impersonate a trusted-sounding id

    ingest = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert ingest["accepted"] is True
    assert ingest["execution_allowed"] is False
    assert ingest["promotion_executed"] is False


# ---------------------------------------------------------------------------
# 12. Additive producer.source: old candidates without it remain valid.
# ---------------------------------------------------------------------------

def test_pre_2w_style_candidate_without_producer_source_still_accepted(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    head = _head(root.path)
    fp = intake.compute_repo_fingerprint(root)
    content_text = "old-style\n"
    old_style_candidate = {
        "intake_contract_version": "1.0",
        "candidate_id": "cand-old-style",
        "producer": {"kind": "claude-code", "adapter_version": "2U.2-reference-1"},  # no "source" key
        "task_context": {"task_id": task_id, "declared_goal": "pre-2W shape"},
        "repo_binding": {"repo_fingerprint": fp, "base_commit": head},
        "proposed_changes": [{
            "path": "app/allowed/old.txt",
            "operation": "create",
            "content_after": content_text,
            "content_hash_after": intake.compute_content_hash(content_text),
        }],
        "producer_claims": {"summary": "pre-2W shape", "self_reported_complete": False},
    }
    result = intake.validate_and_ingest_intake_candidate(root, old_style_candidate)
    assert result["accepted"] is True


def test_no_producer_object_at_all_still_accepted_and_stored_empty(tmp_path):
    root = _root(tmp_path)
    task_id = _task(root)
    head = _head(root.path)
    fp = intake.compute_repo_fingerprint(root)
    content_text = "no-producer\n"
    candidate = {
        "intake_contract_version": "1.0",
        "candidate_id": "cand-no-producer",
        "task_context": {"task_id": task_id, "declared_goal": "no producer field"},
        "repo_binding": {"repo_fingerprint": fp, "base_commit": head},
        "proposed_changes": [{
            "path": "app/allowed/np.txt",
            "operation": "create",
            "content_after": content_text,
            "content_hash_after": intake.compute_content_hash(content_text),
        }],
    }
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True


# ---------------------------------------------------------------------------
# 13/14. Wrapper equivalence + no dedicated adapters
# ---------------------------------------------------------------------------

def test_claude_wrapper_script_contains_no_hashing_or_fingerprint_logic():
    script = Path(__file__).resolve().parents[1] / "scripts" / "claude_code_intake_adapter.py"
    text = script.read_text()
    for forbidden in ("hashlib", "rev-list", "rev-parse", "sha256"):
        assert forbidden not in text, f"wrapper reimplements {forbidden!r}; drift risk from shared helper"
    assert "subprocess.run" in text
    assert "pcae intake from-files" in text or '"from-files"' in text


def test_no_dedicated_codex_cursor_deepseek_adapter_files_exist():
    repo_root = Path(__file__).resolve().parents[1]
    hits = []
    for pattern in ("*codex*adapter*", "*cursor*adapter*", "*deepseek*adapter*"):
        hits.extend(p for p in repo_root.rglob(pattern) if ".git" not in p.parts)
    assert hits == []


# ---------------------------------------------------------------------------
# CLI-level: no-lock explicit producer works without session bootstrap
# ---------------------------------------------------------------------------

def test_cli_from_files_dry_run_no_lock_explicit_producer(tmp_path, monkeypatch):
    root_dir = tmp_path / "cliroot"
    root_dir.mkdir()
    _git_repo(root_dir)
    root = HarnessPath(root_dir)
    task_id = _task(root)
    content = (tmp_path / "clicontent.txt")
    content.write_text("cli content\n")

    proc = subprocess.run(
        [
            sys.executable, "-c", "import sys; from pcae.cli import main; sys.exit(main())",
            "intake", "from-files",
            "--task-id", task_id,
            "--candidate-id", "cli-cand-1",
            "--file", f"app/allowed/cli.txt:create:{content}",
            "--producer", "external-unbootstrapped-tool",
            "--dry-run", "--json",
        ],
        cwd=root_dir, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    printed = json.loads(proc.stdout)
    assert printed["producer"]["kind"] == "external-unbootstrapped-tool"
    assert printed["producer"]["source"] == "candidate"
