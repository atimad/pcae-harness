"""Phase 145G.2V independent verification tests.

Fresh, adversarial, re-derived-from-contract tests for Phase 145G.2's
``decision-session select`` command and its ``preview`` transition
repair, covering ground the 145G.2 test suite itself does not:

- Persistence tamper tests: directly mutate a persisted session JSON on
  disk (bypassing every application/domain code path) and confirm the
  filesystem repository fails deterministically (or, where it does not,
  documents the exact silent-acceptance gap) on reload.
- A genuine, real-subprocess, restart-separated, CLI-only
  create -> evidence -> select -> preview -> confirm -> readiness ->
  governance-record publish chain (the 145G.2 suite's own "end-to-end"
  test invokes handler functions in-process; this one shells out to a
  fresh ``python -m pcae`` process per step against an isolated tmp
  directory, so there is no shared Python object graph across steps at
  all).
- Adversarial/security probes: path-traversal-shaped identifiers,
  confirm without preview, readiness/publish without confirmation,
  malformed package ids.
- Preview-transition idempotency re-verified independently.

Constraints observed: read-only with respect to ``src/``; no bypass
flags used or invented; no direct Session/OrchestrationRecord/repository
construction used to fabricate state for any test that is supposed to
prove CLI-only reachability (the CLI-only test literally shells out to
subprocesses). Tamper tests intentionally *do* write raw bytes to disk,
because that is the only way to probe the persistence layer's own
corruption handling -- this does not go through, and is not claimed to
go through, the CLI/application boundary.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.interactive_workflow.persistence.filesystem_repository import (
    FilesystemSessionRepository,
)
from pcae.interactive_workflow.errors import SessionStoreCorruptError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Invoke ``python -m pcae <args>`` as a genuine, separate OS process
    with ``cwd`` as its working directory. Each call is a fresh process
    with no shared Python object graph with any other call."""

    env = dict(os.environ)
    repo_src = str(Path(__file__).resolve().parents[1] / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = repo_src + (os.pathsep + existing if existing else "")
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _json_out(proc: subprocess.CompletedProcess) -> dict:
    assert proc.stdout.strip(), f"empty stdout; stderr={proc.stderr!r}"
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# 1. Persistence tamper tests
# ---------------------------------------------------------------------------


@pytest.fixture
def _repo_and_session(tmp_path):
    repo = FilesystemSessionRepository(root=tmp_path / "sessions")
    proc = _run_cli(tmp_path, "decision-session", "create",
                     "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    # create against the *default* repo root (.pcae/decision-sessions under
    # tmp_path), not the standalone `repo` above -- the standalone repo is
    # only used for direct file-path resolution/tamper convenience.
    return tmp_path


def test_tamper_unsupported_schema_version_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    path = tmp_path / ".pcae" / "decision-sessions" / f"{session_id}.json"
    assert path.exists()

    payload = json.loads(path.read_text())
    payload["schema_version"] = "bogus/9.9"
    path.write_text(json.dumps(payload))

    status = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    body = _json_out(status)
    assert status.returncode == 1
    assert body["status"] == "error"
    assert body["error_type"] == "persistence_corrupt"


def test_tamper_mismatched_wrapper_session_id_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    path = tmp_path / ".pcae" / "decision-sessions" / f"{session_id}.json"

    payload = json.loads(path.read_text())
    payload["session_id"] = "CDS-00000000-0000-4000-8000-000000000099"
    path.write_text(json.dumps(payload))

    status = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    body = _json_out(status)
    assert status.returncode == 1
    assert body["error_type"] == "persistence_corrupt"


def test_tamper_truncated_json_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    path = tmp_path / ".pcae" / "decision-sessions" / f"{session_id}.json"

    raw = path.read_bytes()
    path.write_bytes(raw[:20])

    status = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    body = _json_out(status)
    assert status.returncode == 1
    assert body["error_type"] == "persistence_corrupt"


def test_tamper_missing_nested_session_payload_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    path = tmp_path / ".pcae" / "decision-sessions" / f"{session_id}.json"

    payload = json.loads(path.read_text())
    del payload["session"]
    path.write_text(json.dumps(payload))

    status = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    body = _json_out(status)
    assert status.returncode == 1
    assert body["error_type"] == "persistence_corrupt"


def test_tamper_decision_selected_state_with_null_selection_id_is_NOT_rejected(tmp_path):
    """FINDING (non-blocking, disclosed by this verification): the
    ``Session`` dataclass's own ``__post_init__`` (models/session.py)
    validates session_id/owner_identity/template_ref/subject_ref/
    session_state/created_at/updated_at/decision_maker_evidence_kind, but
    performs no cross-field invariant check that a session_state of
    ``DecisionSelected`` (or later) implies a non-null
    ``human_selection_id``. A session file hand-edited on disk to declare
    ``session_state: DecisionSelected`` with ``human_selection_id: null``
    is accepted silently by ``status``/``load`` -- deserialization
    succeeds and the (semantically invalid) session is returned as-is.

    This test asserts the OBSERVED (silently-accepting) behavior, not the
    contractually-desirable one, so a future repair that adds the missing
    invariant check will fail this test and must update it deliberately."""

    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    path = tmp_path / ".pcae" / "decision-sessions" / f"{session_id}.json"

    payload = json.loads(path.read_text())
    payload["session"]["session_state"] = "DecisionSelected"
    payload["session"]["human_selection_id"] = None
    path.write_text(json.dumps(payload))

    status = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    body = _json_out(status)
    assert status.returncode == 0
    assert body["status"] == "success"
    assert body["session"]["session_state"] == "DecisionSelected"
    assert body["session"]["human_selection_id"] is None


def test_direct_repository_load_raises_dedicated_corruption_exception(tmp_path):
    """Direct-repository-level (below the application/CLI boundary) check
    that corruption raises ``SessionStoreCorruptError`` specifically, not
    a bare exception or silent None/best-effort recovery."""

    root = tmp_path / "sessions"
    root.mkdir()
    repo = FilesystemSessionRepository(root=root)

    # Fabricate a syntactically-invalid file directly (no session ever
    # created through the repository -- this targets `load`'s own
    # decode-and-validate path in isolation).
    bogus_path = root / "CDS-11111111-1111-4111-8111-111111111111.json"
    bogus_path.write_text("{not json")

    with pytest.raises(SessionStoreCorruptError):
        repo.load("CDS-11111111-1111-4111-8111-111111111111")


# ---------------------------------------------------------------------------
# 2. Restart-safety (fresh object graph within the same process)
# ---------------------------------------------------------------------------


def test_restart_safety_fresh_repository_instance_sees_persisted_selection(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    _run_cli(tmp_path, "decision-session", "evidence", session_id, "--declare", "e1",
             "--as-identity", "o", "--json")
    select = _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "a", "--options-presented", "a", "--options-presented", "b",
        "--template-version", "v1", "--as-identity", "o", "--json",
    )
    assert select.returncode == 0

    # Fresh repository object, never touched by the calls above.
    fresh_repo = FilesystemSessionRepository(root=tmp_path / ".pcae" / "decision-sessions")
    reloaded = fresh_repo.load(session_id)
    assert reloaded.session_state.value == "DecisionSelected"
    assert reloaded.human_selection_id == "a"
    assert reloaded.options_presented == ("a", "b")
    assert reloaded.template_version == "v1"


# ---------------------------------------------------------------------------
# 3. Genuine CLI-only, subprocess-restart-separated, end-to-end chain
# ---------------------------------------------------------------------------


def test_genuine_subprocess_e2e_create_through_publish(tmp_path):
    """Every step below is a brand-new OS process (``python -m pcae ...``)
    against an isolated tmp working directory -- no shared Python object
    graph, no direct Session/repository construction, no fixture-only
    state injection anywhere in this chain."""

    # Phase 149O.20L.7O.3C.2: CHGR publication now requires an active-task
    # contract (POL-001), mirroring commit/push/promotion's existing
    # Permission Broker invariant -- see the identical fixture change in
    # test_phase_145g_decision_session_cli.py.
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260101-0000-phase-145g2v-cli-fixture-task.md").write_text(
        "# Phase 145G.2v CLI fixture task\n", encoding="utf-8"
    )

    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "tmpl", "--subject-ref", "subj", "--owner-id", "owner",
                       "--json")
    assert create.returncode == 0
    session_id = _json_out(create)["session"]["session_id"]

    evidence = _run_cli(tmp_path, "decision-session", "evidence", session_id,
                         "--declare", "ev-1", "--declare", "ev-2", "--as-identity", "owner", "--json")
    assert evidence.returncode == 0
    assert _json_out(evidence)["session"]["session_state"] == "EvidenceReady"

    # Preview before select must fail (invalid_state_transition, exit 2).
    early_preview = _run_cli(tmp_path, "decision-session", "preview", session_id,
                              "--as-identity", "owner", "--json")
    assert early_preview.returncode == 2
    assert _json_out(early_preview)["error_type"] == "invalid_state_transition"

    select = _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "opt-a", "--options-presented", "opt-a", "--options-presented", "opt-b",
        "--template-version", "1.0", "--rationale", "because", "--as-identity", "owner", "--json",
    )
    assert select.returncode == 0
    assert _json_out(select)["session"]["session_state"] == "DecisionSelected"

    preview1 = _run_cli(tmp_path, "decision-session", "preview", session_id,
                         "--as-identity", "owner", "--json")
    assert preview1.returncode == 0
    digest1 = _json_out(preview1)["preview_digest"]

    status_after_preview = _run_cli(tmp_path, "decision-session", "status", session_id, "--json")
    assert _json_out(status_after_preview)["session"]["session_state"] == "AwaitingConfirmation"

    preview2 = _run_cli(tmp_path, "decision-session", "preview", session_id,
                         "--as-identity", "owner", "--json")
    assert preview2.returncode == 0
    digest2 = _json_out(preview2)["preview_digest"]
    assert digest1 == digest2, "preview digest must be stable across idempotent re-renders"

    confirm = _run_cli(tmp_path, "decision-session", "confirm", session_id,
                        "--preview-digest", digest1, "--statement", "I confirm",
                        "--as-identity", "owner", "--json")
    assert confirm.returncode == 0
    assert _json_out(confirm)["session"]["session_state"] == "Confirmed"

    readiness = _run_cli(tmp_path, "decision-session", "readiness", session_id,
                          "--as-identity", "owner", "--json")
    assert readiness.returncode == 0
    readiness_body = _json_out(readiness)
    package_id = readiness_body["package_id"]
    assert readiness_body["disposition"] == "pending"

    publish = _run_cli(tmp_path, "governance-record", "publish", package_id,
                        "--operator-id", "operator-1", "--json")
    assert publish.returncode == 0
    publish_body = _json_out(publish)
    assert publish_body["success"] is True
    assert publish_body["record_id"].startswith("chgr-")


def test_genuine_subprocess_e2e_confirm_without_ever_previewing_fails(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    _run_cli(tmp_path, "decision-session", "evidence", session_id, "--declare", "e1",
             "--as-identity", "o", "--json")
    _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "a", "--options-presented", "a", "--template-version", "v1",
        "--as-identity", "o", "--json",
    )
    # Session is now DecisionSelected but preview was never called, so it
    # cannot have reached AwaitingConfirmation.
    confirm = _run_cli(tmp_path, "decision-session", "confirm", session_id,
                        "--preview-digest", "deadbeef", "--statement", "x",
                        "--as-identity", "o", "--json")
    assert confirm.returncode == 2
    body = _json_out(confirm)
    assert body["error_type"] == "invalid_state_transition"


def test_genuine_subprocess_readiness_without_confirmation_fails(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    _run_cli(tmp_path, "decision-session", "evidence", session_id, "--declare", "e1",
             "--as-identity", "o", "--json")
    _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "a", "--options-presented", "a", "--template-version", "v1",
        "--as-identity", "o", "--json",
    )
    readiness = _run_cli(tmp_path, "decision-session", "readiness", session_id,
                          "--as-identity", "o", "--json")
    assert readiness.returncode == 1
    assert _json_out(readiness)["error_type"] == "readiness_incomplete"


# ---------------------------------------------------------------------------
# 4. Security / adversarial probes
# ---------------------------------------------------------------------------


def test_path_traversal_shaped_session_id_rejected_no_traceback(tmp_path):
    result = _run_cli(tmp_path, "decision-session", "status", "../../../etc/passwd", "--json")
    assert result.returncode == 1
    body = _json_out(result)
    assert body["error_type"] == "invalid_request"
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_path_traversal_shaped_session_id_with_cds_prefix_rejected(tmp_path):
    result = _run_cli(tmp_path, "decision-session", "status", "CDS-../../etc/passwd", "--json")
    assert result.returncode == 1
    assert _json_out(result)["error_type"] == "invalid_request"


def test_nonexistent_session_id_well_formed_returns_session_not_found(tmp_path):
    result = _run_cli(
        tmp_path, "decision-session", "select",
        "CDS-00000000-0000-4000-8000-000000000000",
        "--option-id", "a", "--options-presented", "a", "--template-version", "v1",
        "--as-identity", "o", "--json",
    )
    assert result.returncode == 1
    assert _json_out(result)["error_type"] == "session_not_found"
    assert "Traceback" not in result.stdout


def test_publish_path_traversal_shaped_package_id_rejected(tmp_path):
    result = _run_cli(tmp_path, "governance-record", "publish", "../../../etc/passwd",
                       "--operator-id", "op", "--json")
    assert result.returncode == 1
    body = _json_out(result)
    assert body["error_type"] == "invalid_request"
    assert "Traceback" not in result.stdout


def test_publish_nonexistent_well_formed_package_id_rejected(tmp_path):
    result = _run_cli(tmp_path, "governance-record", "publish", "prp-doesnotexist",
                       "--operator-id", "op", "--json")
    assert result.returncode == 1
    assert _json_out(result)["error_type"] == "artifact_not_found"


def test_select_duplicate_options_presented_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    _run_cli(tmp_path, "decision-session", "evidence", session_id, "--declare", "e1",
             "--as-identity", "o", "--json")
    result = _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "a", "--options-presented", "a", "--options-presented", "a",
        "--template-version", "v1", "--as-identity", "o", "--json",
    )
    assert result.returncode == 1
    assert _json_out(result)["error_type"] == "invalid_request"


def test_select_option_not_member_of_presented_set_rejected(tmp_path):
    create = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s", "--owner-id", "o", "--json")
    session_id = _json_out(create)["session"]["session_id"]
    _run_cli(tmp_path, "decision-session", "evidence", session_id, "--declare", "e1",
              "--as-identity", "o", "--json")
    result = _run_cli(
        tmp_path, "decision-session", "select", session_id,
        "--option-id", "c", "--options-presented", "a", "--options-presented", "b",
        "--template-version", "v1", "--as-identity", "o", "--json",
    )
    assert result.returncode == 1
    assert _json_out(result)["error_type"] == "invalid_request"


def test_no_force_or_bypass_flag_in_decision_session_or_governance_record_help(tmp_path):
    for subcommand in ("create", "evidence", "select", "clarify", "preview", "confirm",
                       "status", "readiness", "cancel"):
        result = _run_cli(tmp_path, "decision-session", subcommand, "--help")
        combined = (result.stdout + result.stderr).lower()
        assert "--force" not in combined
        assert "--bypass" not in combined
        assert "--skip-validation" not in combined
        assert "--assume-authorized" not in combined

    result = _run_cli(tmp_path, "governance-record", "publish", "--help")
    combined = (result.stdout + result.stderr).lower()
    assert "--force" not in combined
    assert "--bypass" not in combined


def test_malformed_missing_arguments_produce_argparse_usage_not_traceback(tmp_path):
    # Missing required --owner-id: argparse itself should reject this with
    # a usage message and nonzero exit, never a Python traceback.
    result = _run_cli(tmp_path, "decision-session", "create",
                       "--template-ref", "t", "--subject-ref", "s")
    assert result.returncode != 0
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr
