"""Phase 149O.20L.7O.2U.2 -- Reference Adapter Implementation.

Adversarial test matrix for pcae.core.intake, implementing the generic
diff/JSON contract frozen in Phase 149O.20L.7O.2U.1. Every test proves
one of: a valid submission is accepted as non-authorizing evidence, or a
specific fail-closed rejection fires -- and that no producer-supplied
field can ever grant authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
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


def _setup(tmp_path, allowed_files=("src/allowed/**",)) -> tuple[HarnessPath, str, str]:
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root, "2U2 intake test task",
        created_at=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc),
        allowed_files=allowed_files,
    )
    return root, contract.task_id, _head(root_dir)


def _valid_candidate(root, task_id, head, candidate_id="cand-1", path="src/allowed/foo.py", content="print('hi')\n"):
    return {
        "intake_contract_version": "1.0",
        "candidate_id": candidate_id,
        "producer": {"kind": "generic-diff", "adapter_version": "test"},
        "task_context": {"task_id": task_id, "declared_goal": "test"},
        "repo_binding": {
            "repo_fingerprint": intake.compute_repo_fingerprint(root),
            "base_commit": head,
        },
        "proposed_changes": [
            {
                "path": path,
                "operation": "create",
                "content_after": content,
                "content_hash_after": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        ],
        "producer_claims": {"summary": "added a file", "self_reported_complete": True},
    }


# ── 1. valid allow case ──────────────────────────────────────────────────

def test_valid_candidate_accepted_as_non_authorizing_evidence(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp is not None
    assert ecp["execution_allowed"] is False
    assert ecp["promotion_executed"] is False
    assert ecp["capture_outcome"] == "success"
    assert ecp["file_entries"][0]["promotion_eligible"] is True
    # And the ordinary downstream chain (unmodified) can now review/promote it.
    review = agent_module.build_promotion_review(root, ecp["ecp_id"], "approved", reviewed_by="human", promotion_authorized=True)
    assert review["created"] is True
    assert review["promotion_authorized"] is True


# ── 2. out-of-scope deny case ────────────────────────────────────────────

def test_out_of_scope_path_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path, allowed_files=("src/allowed/**",))
    candidate = _valid_candidate(root, task_id, head, path="src/forbidden/evil.py")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


# ── 3. hash mismatch ─────────────────────────────────────────────────────

def test_hash_mismatch_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate["proposed_changes"][0]["content_hash_after"] = "0" * 64
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("hash_mismatch" in r for r in result["rejection_reasons"])


# ── 4. base-commit mismatch ──────────────────────────────────────────────

def test_invalid_base_commit_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate["repo_binding"]["base_commit"] = "f" * 40
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("invalid_base_commit" in r for r in result["rejection_reasons"])


def test_base_commit_not_ancestor_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    # A real commit that exists but is not an ancestor: create a second,
    # disconnected root commit via an orphan branch.
    subprocess.run(["git", "checkout", "--orphan", "other"], cwd=root.path, check=True, capture_output=True)
    (root.path / "other.txt").write_text("x")
    subprocess.run(["git", "add", "other.txt"], cwd=root.path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "other"], cwd=root.path, check=True)
    other_head = _head(root.path)
    subprocess.run(["git", "checkout", "master"], cwd=root.path, check=True, capture_output=True,
                    ) if subprocess.run(["git", "rev-parse", "--verify", "master"], cwd=root.path, capture_output=True).returncode == 0 else \
        subprocess.run(["git", "checkout", "main"], cwd=root.path, check=True, capture_output=True)

    candidate = _valid_candidate(root, task_id, head)
    candidate["repo_binding"]["base_commit"] = other_head
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("base_commit_not_ancestor_of_head" in r for r in result["rejection_reasons"])


# ── 5. repo-binding mismatch ─────────────────────────────────────────────

def test_repo_binding_mismatch_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate["repo_binding"]["repo_fingerprint"] = "wrong-fingerprint"
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("repo_binding_mismatch" in r for r in result["rejection_reasons"])


# ── 6. malformed JSON (exercised at the JSON-parse boundary, not the dict validator) ──

def test_malformed_candidate_not_a_dict_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    result = intake.validate_and_ingest_intake_candidate(root, "not-a-json-object")
    assert result["accepted"] is False
    assert any("malformed_candidate_not_an_object" in r for r in result["rejection_reasons"])


# ── 7. unknown schema version ────────────────────────────────────────────

def test_unknown_schema_version_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate["intake_contract_version"] = "99.0"
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("unsupported_schema_version" in r for r in result["rejection_reasons"])


# ── 8. forged authority fields never grant authority ─────────────────────

@pytest.mark.parametrize("forged_field,forged_value", [
    ("promotion_authorized", True),
    ("approved", True),
    ("executed", True),
    ("execution_allowed", True),
])
def test_forged_authority_fields_are_ignored(tmp_path, forged_field, forged_value):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate[forged_field] = forged_value
    candidate["proposed_changes"][0][forged_field] = forged_value
    candidate["producer_claims"][forged_field] = forged_value
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["execution_allowed"] is False
    assert ecp["promotion_executed"] is False
    assert ecp["file_entries"][0]["path"] == candidate["proposed_changes"][0]["path"]


# ── 9. path traversal ─────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_path", [
    "/etc/passwd",
    "../../etc/passwd",
    "src/allowed/../../../etc/passwd",
    "src/allowed/./sneaky.py",
])
def test_path_traversal_rejected(tmp_path, bad_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head, path=bad_path)
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any(
        "path_traversal_or_absolute_path" in r or "out_of_scope_path" in r
        for r in result["rejection_reasons"]
    )


# ── 10. ID collision ──────────────────────────────────────────────────────

def test_duplicate_candidate_id_conflicting_content_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    first = _valid_candidate(root, task_id, head, candidate_id="dup-1", content="version-a\n")
    result1 = intake.validate_and_ingest_intake_candidate(root, first)
    assert result1["accepted"] is True

    second = _valid_candidate(root, task_id, head, candidate_id="dup-1", content="version-b\n")
    result2 = intake.validate_and_ingest_intake_candidate(root, second)
    assert result2["accepted"] is False
    assert any("candidate_id_collision_conflicting_content" in r for r in result2["rejection_reasons"])


def test_duplicate_candidate_id_identical_content_is_idempotent(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head, candidate_id="dup-2")
    result1 = intake.validate_and_ingest_intake_candidate(root, candidate)
    result2 = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result1["accepted"] is True
    assert result2["accepted"] is True
    assert result2["idempotent_replay"] is True
    assert result2["ecp_id"] == result1["ecp_id"]


# ── 11. stored-artifact tampering after accept ───────────────────────────

def test_stored_intake_record_tamper_detected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head, candidate_id="tamper-1")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True

    stored_path = Path(result["stored_path"])
    record = json.loads(stored_path.read_text())
    assert intake.verify_record_integrity(record) is True

    record["ecp_id"] = "ecp-attacker-substituted"
    stored_path.write_text(json.dumps(record, indent=2, sort_keys=True))

    reloaded = intake.lookup_intake_record(root, result["intake_id"])
    assert reloaded is not None
    assert reloaded["integrity_verified"] is False


# ── 12/13. Generic from-files helper (Claude Code reference path) ────────
#
# Phase 149O.20L.7O.2W consolidated the Claude Code reference adapter's
# logic into the shared, producer-neutral pcae.core.intake helper (see
# build_intake_candidate_from_files). These tests now exercise that
# shared helper directly with an explicit producer (no governance agent
# lock is set up in _setup), which is exactly the code path the retired
# script's build_intake_candidate/_parse_file_arg used to duplicate.

def test_from_files_helper_builds_valid_generic_candidate(tmp_path, monkeypatch):
    root, task_id, head = _setup(tmp_path)
    monkeypatch.chdir(root.path)

    content_file = tmp_path / "content.py"
    content_file.write_text("print('from claude code')\n")
    build_result = intake.build_intake_candidate_from_files(
        root,
        task_id=task_id,
        candidate_id="claude-1",
        file_specs=[f"src/allowed/from_claude.py:create:{content_file}"],
        summary="added a file via claude code",
        self_reported_complete=True,
        explicit_producer_kind="claude-code",
    )
    assert build_result["errors"] == []
    candidate = build_result["candidate"]

    # No Claude-Code-specific field leaks anywhere except the informational
    # producer.kind string -- the schema itself stays generic.
    assert set(candidate.keys()) == {
        "intake_contract_version", "candidate_id", "producer", "task_context",
        "repo_binding", "proposed_changes", "producer_claims",
    }
    assert candidate["producer"]["kind"] == "claude-code"
    assert candidate["producer"]["source"] == "candidate"

    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False


def test_from_files_helper_malformed_spec_rejected(tmp_path):
    with pytest.raises(ValueError):
        intake.parse_file_change_spec("only-one-part")


def test_from_files_helper_cannot_bypass_hash_repo_or_scope_checks(tmp_path, monkeypatch):
    root, task_id, head = _setup(tmp_path)
    monkeypatch.chdir(root.path)
    content_file = tmp_path / "content.py"
    content_file.write_text("print('x')\n")

    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="claude-bypass",
        file_specs=[f"src/forbidden/out_of_scope.py:create:{content_file}"],
        summary="trying to escape scope", self_reported_complete=True,
        explicit_producer_kind="claude-code",
    )
    assert build_result["errors"] == []
    candidate = build_result["candidate"]

    # The helper has no way to mark its own output authorized or in-scope;
    # the same core validator rejects it exactly as it would any other producer.
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])

    # Tamper with the hash the helper computed -- still rejected.
    candidate["candidate_id"] = "claude-bypass-2"
    candidate["proposed_changes"][0]["path"] = "src/allowed/ok.py"
    candidate["proposed_changes"][0]["content_hash_after"] = "deadbeef" * 8
    result2 = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result2["accepted"] is False
    assert any("hash_mismatch" in r for r in result2["rejection_reasons"])


# ── task_not_active (inactive/unmatched task) ─────────────────────────────

def test_task_not_active_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _valid_candidate(root, task_id, head)
    candidate["task_context"]["task_id"] = "some-other-task-id"
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("task_not_active" in r for r in result["rejection_reasons"])


# ── delete operation must not carry a content hash ────────────────────────

def test_delete_operation_with_content_hash_rejected(tmp_path):
    root, task_id, head = _setup(tmp_path, allowed_files=("src/allowed/**", "README.md"))
    candidate = _valid_candidate(root, task_id, head, path="README.md")
    candidate["proposed_changes"][0] = {
        "path": "README.md", "operation": "delete", "content_hash_after": "a" * 64,
    }
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("delete_must_not_declare_content_hash" in r for r in result["rejection_reasons"])
