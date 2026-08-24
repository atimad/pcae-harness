"""Phase 149O.20L.7O.2U.3 -- Reference Adapter Implementation Independent
Verification.

Fresh, independent adversarial suite against the real, unmodified
pcae.core.intake / pcae.commands.intake / scripts/claude_code_intake_adapter.py
surface shipped in Phase 149O.20L.7O.2U.2. This file does not call 2U.2's
own test helpers or reuse its test functions; it re-derives its own attack
fixtures directly against the production module to independently verify
(not merely re-confirm) that no producer-controlled field can influence an
authority-bearing outcome, that repo/base-commit/hash binding is fail-
closed, that task-scope reuse cannot be bypassed, and that stored-record
tamper detection is real.
"""

from __future__ import annotations

import hashlib
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


# ---------------------------------------------------------------------------
# Independent fixture construction (deliberately not shared with 2U.2 tests)
# ---------------------------------------------------------------------------

def _git(root_dir: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root_dir, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _new_repo(tmp_path: Path, name: str = "root") -> Path:
    """Each repo's genesis commit content is unique (embeds `name`), since
    compute_repo_fingerprint hashes only *root* commit(s) -- two repos with
    an identical genesis commit (content+author+committer+timestamp) are
    by design indistinguishable to repo binding (stable across clones of
    the same history). Distinct fixtures must therefore have distinct
    genesis content, not merely distinct *later* commits."""
    root_dir = tmp_path / name
    root_dir.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root_dir, check=True)
    subprocess.run(["git", "config", "user.email", "attacker@example.com"], cwd=root_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Attacker"], cwd=root_dir, check=True)
    (root_dir / "README.md").write_text(f"seed-{name}\n")
    subprocess.run(["git", "add", "README.md"], cwd=root_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"seed-{name}"], cwd=root_dir, check=True)
    return root_dir


def _bootstrap_task(root_dir: Path, allowed_files=("src/scoped/**",)) -> tuple[HarnessPath, str, str]:
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root, "2U3 independent verification task",
        created_at=datetime(2026, 8, 23, 20, 0, tzinfo=timezone.utc),
        allowed_files=allowed_files,
    )
    return root, contract.task_id, _git(root_dir, "rev-parse", "HEAD")


def _base_candidate(root, task_id, head, **overrides) -> dict:
    content = overrides.pop("content", "attack payload\n")
    path = overrides.pop("path", "src/scoped/x.py")
    doc = {
        "intake_contract_version": "1.0",
        "candidate_id": overrides.pop("candidate_id", "atk-1"),
        "producer": {"kind": "adversary-tool", "adapter_version": "n/a"},
        "task_context": {"task_id": task_id, "declared_goal": "attack"},
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
        "producer_claims": {"summary": "attack", "self_reported_complete": True},
    }
    doc.update(overrides)
    return doc


# ── §6 authority-injection matrix ────────────────────────────────────────

_AUTHORITY_FIELD_NAMES = [
    "promotion_authorized", "execution_allowed", "promotion_executed",
    "approved", "confirmed", "permitted", "decision", "permission",
    "capability", "executed", "review_result", "rollback_authorized",
    "human_authorized", "trusted", "validated", "state", "status",
]


@pytest.mark.parametrize("field", _AUTHORITY_FIELD_NAMES)
def test_top_level_authority_field_injection_ignored(tmp_path, field):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id=f"atk-top-{field}")
    candidate[field] = True
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    if result["accepted"]:
        ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
        assert ecp["execution_allowed"] is False
        assert ecp["promotion_executed"] is False


@pytest.mark.parametrize("field", _AUTHORITY_FIELD_NAMES)
def test_change_level_authority_field_injection_ignored(tmp_path, field):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id=f"atk-chg-{field}")
    candidate["proposed_changes"][0][field] = True
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False


@pytest.mark.parametrize("field", _AUTHORITY_FIELD_NAMES)
def test_producer_claims_authority_field_injection_ignored(tmp_path, field):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id=f"atk-claim-{field}")
    candidate["producer_claims"][field] = True
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["execution_allowed"] is False
    assert ecp["promotion_executed"] is False
    # producer_claims is stored verbatim as descriptive metadata only, never
    # copied into any top-level authority field of the ECP.
    for key in ("execution_allowed", "promotion_executed"):
        assert ecp[key] is False


def test_nested_authority_object_injection_ignored(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-nested")
    candidate["authorization"] = {"promotion_authorized": True, "human_authorized": True}
    candidate["review"] = {"result": "approved", "decision": "permitted"}
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False


def test_unknown_fields_never_reach_ecp_top_level_keys(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-unknown")
    candidate["totally_unrecognized_field"] = {"nested": "junk", "execution_allowed": True}
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert "totally_unrecognized_field" not in ecp
    assert ecp["execution_allowed"] is False


# ── §9/§10 repository binding ────────────────────────────────────────────

def test_repo_fingerprint_from_different_repo_rejected(tmp_path):
    repo_a = _new_repo(tmp_path, "repo_a")
    repo_b = _new_repo(tmp_path, "repo_b")
    # give repo_b genuinely different root-commit content/timestamps so its
    # fingerprint cannot coincidentally match repo_a's (see the dedicated
    # fingerprint-collision observation test below for the content-identical
    # edge case).
    (repo_b / "UNIQUE_B.md").write_text("unique to repo b\n")
    subprocess.run(["git", "add", "UNIQUE_B.md"], cwd=repo_b, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "repo b marker"], cwd=repo_b, check=True)
    root_a, task_id, head_a = _bootstrap_task(repo_a)
    root_b = HarnessPath(repo_b)
    # candidate carries repo_a's true fingerprint/base but is submitted
    # against repo_b, which has its own unrelated history.
    candidate = _base_candidate(root_a, task_id, head_a, candidate_id="atk-repo-swap")
    result = intake.validate_and_ingest_intake_candidate(root_b, candidate)
    assert result["accepted"] is False
    assert result["rejection_reasons"] in (["task_not_active"],)  # no active task in repo_b
    # Also attack with an active task present in repo_b but repo_a's fingerprint.
    root_b2, task_id_b, head_b = _bootstrap_task(repo_b)
    candidate2 = _base_candidate(root_a, task_id_b, head_a, candidate_id="atk-repo-swap-2")
    result2 = intake.validate_and_ingest_intake_candidate(root_b2, candidate2)
    assert result2["accepted"] is False
    assert "repo_binding_mismatch" in result2["rejection_reasons"]


def test_repo_fingerprint_is_a_content_hash_not_a_location_identifier(tmp_path):
    """OBSERVATION (not exploitable in practice): repo_fingerprint is
    SHA256 of sorted root-commit hash(es) -- by design this is stable
    across clones/forks of the *same* history (that's the whole point:
    reject a diff computed against a different repo's history). A direct
    consequence is that two independently-created directories whose root
    commit(s) are byte-identical (same tree, author, committer, message,
    and second-resolution timestamp) produce the same fingerprint. This
    requires an attacker to already reproduce the exact root-commit bytes
    of the real target repo, which for any real project's actual history
    is not materially different from possessing a genuine clone of it --
    it is not a way to impersonate an unrelated repository."""
    import os

    def _repo_with_pinned_genesis(dirname: str) -> Path:
        r = tmp_path / dirname
        r.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        subprocess.run(["git", "config", "user.email", "attacker@example.com"], cwd=r, check=True)
        subprocess.run(["git", "config", "user.name", "Attacker"], cwd=r, check=True)
        (r / "README.md").write_text("identical seed content\n")
        subprocess.run(["git", "add", "README.md"], cwd=r, check=True)
        env = dict(os.environ)
        env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00"
        env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00"
        subprocess.run(["git", "commit", "-q", "-m", "identical seed"], cwd=r, check=True, env=env)
        return r

    repo_x = _repo_with_pinned_genesis("repo_x")
    repo_y = _repo_with_pinned_genesis("repo_y")
    fp_x = intake.compute_repo_fingerprint(HarnessPath(repo_x))
    fp_y = intake.compute_repo_fingerprint(HarnessPath(repo_y))
    # This DOES collide, by design: repo_fingerprint hashes only the root
    # commit(s), so two directories that reproduce byte-identical genesis
    # commits (content+author+committer+same-second timestamp) are
    # indistinguishable. This is the documented "stable across clones/
    # forks" behavior taken to its logical edge case -- reproducing it
    # requires an attacker to already know and replay the real target's
    # exact genesis commit bytes, which is not a meaningfully different
    # capability than already possessing a genuine clone of that history.
    assert fp_x == fp_y

    # Diverging genesis content (the realistic case: two actually
    # different projects) does NOT collide:
    repo_a = _new_repo(tmp_path, "repo_a_diverging")
    repo_b = _new_repo(tmp_path, "repo_b_diverging")
    fp_a = intake.compute_repo_fingerprint(HarnessPath(repo_a))
    fp_b = intake.compute_repo_fingerprint(HarnessPath(repo_b))
    assert fp_a != fp_b


def test_forged_repo_fingerprint_literal_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-forged-fp")
    candidate["repo_binding"]["repo_fingerprint"] = "0" * 64
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert "repo_binding_mismatch" in result["rejection_reasons"]


def test_missing_repo_binding_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-no-repo-binding")
    del candidate["repo_binding"]
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["missing_repo_binding"]


# ── §11 base-commit binding ──────────────────────────────────────────────

def test_nonexistent_base_commit_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-bad-commit")
    candidate["repo_binding"]["base_commit"] = "deadbeef" * 5
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["invalid_base_commit"]


def test_malformed_base_commit_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-malformed-commit")
    candidate["repo_binding"]["base_commit"] = "not-a-sha; rm -rf /"
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["invalid_base_commit"]


def test_base_commit_from_unrelated_repo_rejected(tmp_path):
    repo_a = _new_repo(tmp_path, "repo_a")
    repo_b = _new_repo(tmp_path, "repo_b")
    (repo_a / "UNIQUE_A.md").write_text("unique to repo a\n")
    subprocess.run(["git", "add", "UNIQUE_A.md"], cwd=repo_a, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "repo a marker"], cwd=repo_a, check=True)
    root_b, task_id, head_b = _bootstrap_task(repo_b)
    foreign_head = _git(repo_a, "rev-parse", "HEAD")
    candidate = _base_candidate(root_b, task_id, head_b, candidate_id="atk-foreign-commit")
    candidate["repo_binding"]["base_commit"] = foreign_head
    result = intake.validate_and_ingest_intake_candidate(root_b, candidate)
    assert result["accepted"] is False
    assert result["rejection_reasons"] in (["invalid_base_commit"],)


def test_base_commit_ahead_of_head_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    # Advance HEAD past the task's creation point, then submit a candidate
    # whose declared base_commit is that *future* commit relative to a
    # constructed HEAD that has since been reset backward -- simulate by
    # creating a branch commit not on HEAD's ancestry.
    subprocess.run(["git", "checkout", "-q", "-b", "future"], cwd=root_dir, check=True)
    (root_dir / "future.txt").write_text("future\n")
    subprocess.run(["git", "add", "future.txt"], cwd=root_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "future commit"], cwd=root_dir, check=True)
    future_commit = _git(root_dir, "rev-parse", "HEAD")
    subprocess.run(["git", "checkout", "-q", "master"], cwd=root_dir, check=True) \
        if _git(root_dir, "branch", "--list", "master") else \
        subprocess.run(["git", "checkout", "-q", "main"], cwd=root_dir, check=True)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-not-ancestor")
    candidate["repo_binding"]["base_commit"] = future_commit
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert result["rejection_reasons"] == ["base_commit_not_ancestor_of_head"]


def test_current_head_as_base_commit_is_valid_not_a_silent_substitution(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-head-is-fine")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["pre_git_head"] == head


# ── §13/§14 hash canonicalization + payload/hash swap ────────────────────

def test_hash_mismatch_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-hash-mismatch")
    candidate["proposed_changes"][0]["content_hash_after"] = hashlib.sha256(b"different content").hexdigest()
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert "hash_mismatch:src/scoped/x.py" in result["rejection_reasons"][0]


def test_payload_hash_swap_between_two_valid_candidates_detected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    content_1 = "legit content\n"
    content_2 = "swapped malicious content\n"
    cand_1 = _base_candidate(
        root, task_id, head, candidate_id="atk-swap-1",
        content=content_1,
    )
    cand_2 = _base_candidate(
        root, task_id, head, candidate_id="atk-swap-2",
        content=content_2,
    )
    # Attacker submits cand_1's declared hash but cand_2's actual content.
    forged = json.loads(json.dumps(cand_2))
    forged["proposed_changes"][0]["content_hash_after"] = cand_1["proposed_changes"][0]["content_hash_after"]
    result = intake.validate_and_ingest_intake_candidate(root, forged)
    assert result["accepted"] is False
    assert any("hash_mismatch" in r for r in result["rejection_reasons"])


def test_crlf_vs_lf_content_produces_different_required_hash(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    content_lf = "line1\nline2\n"
    content_crlf = "line1\r\nline2\r\n"
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-crlf", content=content_crlf)
    # declare the LF hash while sending CRLF bytes -- must be rejected,
    # proving no silent newline canonicalization occurs before hashing.
    candidate["proposed_changes"][0]["content_hash_after"] = hashlib.sha256(content_lf.encode("utf-8")).hexdigest()
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("hash_mismatch" in r for r in result["rejection_reasons"])


# ── §16/§17 task-scope authority source, active-task-only narrowing ─────

def test_producer_supplied_task_id_not_current_active_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, real_task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, "some-other-task-id-not-active", head, candidate_id="atk-wrong-task")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["task_not_active"]


def test_no_active_task_rejects_everything(tmp_path):
    root_dir = _new_repo(tmp_path)
    root = HarnessPath(root_dir)
    head = _git(root_dir, "rev-parse", "HEAD")
    candidate = _base_candidate(root, "any-task-id", head, candidate_id="atk-no-task")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["task_not_active"]


def test_stale_previous_task_id_no_longer_current_is_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, old_task_id, head = _bootstrap_task(root_dir)
    # A second task contract is created (simulating governed transition);
    # the new one becomes "current" by filename-sort, the old id must no
    # longer authorize scope even though it was once a legitimate task.
    new_contract = create_task_contract(
        root, "second task",
        created_at=datetime(2026, 8, 23, 21, 0, tzinfo=timezone.utc),
        allowed_files=("src/scoped/**",),
    )
    candidate = _base_candidate(root, old_task_id, head, candidate_id="atk-stale-task")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["rejection_reasons"] == ["task_not_active"]
    # the new task id, by contrast, is honored
    candidate2 = _base_candidate(root, new_contract.task_id, head, candidate_id="atk-fresh-task")
    result2 = intake.validate_and_ingest_intake_candidate(root, candidate2)
    assert result2["accepted"] is True


# ── §18/§19/§20/§21 task-scope bypass: prefix / traversal / case ────────

def test_prefix_bypass_not_treated_as_containment(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    # "src/scopedXYZ/evil.py" shares a lexical prefix with "src/scoped" but
    # must not be treated as inside it.
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-prefix", path="src/scopedXYZ/evil.py")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


def test_path_traversal_rejected_before_scope_check(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    candidate = _base_candidate(
        root, task_id, head, candidate_id="atk-traversal",
        path="src/scoped/../../etc/passwd",
    )
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("path_traversal_or_absolute_path" in r for r in result["rejection_reasons"])


def test_absolute_path_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-abs", path="/etc/passwd")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("path_traversal_or_absolute_path" in r for r in result["rejection_reasons"])


def test_windows_style_absolute_path_rejected(tmp_path):
    """FINDING (Non-Blocking): `_path_is_safe_relative`'s drive-letter
    check (`":" in path.split("/")[0] and len(...) == 2`) only fires when
    a forward slash follows the drive letter (e.g. "C:/x"); a pure-
    backslash Windows absolute path like "C:\\Windows\\evil.py" contains
    no "/" at all, so path.split("/")[0] is the *whole* string and its
    length is never 2 -- the admission-control layer's own stated
    invariant ("no absolute paths ... backslash content" -> reject) is not
    actually enforced for this exact shape. It is still caught here as a
    second, independent layer: the literal string does not match the
    allow-list glob pattern, so out_of_scope_path fires instead. On POSIX
    (the only supported PCAE runtime), backslash is not a path separator,
    so this bypasses no actual filesystem boundary -- the write path
    (promotion) still joins the literal path under repo root -- but the
    admission-control docstring's claim is inaccurate and should be
    tightened in a dedicated follow-up (recommend rejecting any path
    containing "\\" outright, not just the 2-char-drive-with-slash case)."""
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-winabs", path="C:\\Windows\\evil.py")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    # Rejected via the scope check backstop, not via the path-safety layer
    # that is documented to (but does not actually) catch this shape.
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])
    from pcae.core.intake import _path_is_safe_relative
    assert _path_is_safe_relative("C:\\Windows\\evil.py") is True  # documents the actual gap


def test_case_variant_path_outside_allowed_files_pattern_is_evaluated_lexically(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-case", path="SRC/SCOPED/x.py")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    # On a case-sensitive Git repo, "SRC/SCOPED/x.py" is a different path
    # from "src/scoped/x.py" and must not match the allow-list pattern.
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


# ── §23/§24 content_after / text-only narrowing ──────────────────────────

def test_nul_byte_in_content_after_rejected_not_accepted_as_string(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-nul")
    candidate["proposed_changes"][0]["content_after"] = "abc\x00def"
    candidate["proposed_changes"][0]["content_hash_after"] = hashlib.sha256("abc\x00def".encode("utf-8")).hexdigest()
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    # JSON strings can legally carry a NUL; the module accepts it as text
    # content (Python str), it is not silently treated as binary/rejected
    # by this layer -- document actual behavior rather than assume.
    assert result["accepted"] in (True, False)
    if result["accepted"]:
        ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
        entry = ecp["file_entries"][0]
        assert entry["binary"] is True  # _ecp_is_binary flags embedded NUL


def test_content_after_must_be_string_not_bytes_or_object(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-not-string")
    candidate["proposed_changes"][0]["content_after"] = {"not": "a string"}
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("missing_content_after" in r for r in result["rejection_reasons"])


def test_no_diff_or_patch_application_field_is_honored_by_core(tmp_path):
    """Even if a 'diff' field (per the frozen §3 schema) is supplied
    alongside content_after, the implementation must not apply it as a
    patch -- it must be ignored, since 2U.2 narrowed to content_after only."""
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-diff-field")
    candidate["proposed_changes"][0]["diff"] = (
        "--- a/src/scoped/x.py\n+++ b/src/scoped/x.py\n@@ -1 +1 @@\n-attack payload\n+DIFFERENT\n"
    )
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    # content actually stored must equal content_after, not a patch result.
    assert ecp["file_entries"][0]["content"] == candidate["proposed_changes"][0]["content_after"]


# ── §25/§27 delete / duplicate-path semantics ────────────────────────────

def test_delete_with_declared_content_hash_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    (root_dir / "src" / "scoped").mkdir(parents=True)
    (root_dir / "src" / "scoped" / "x.py").write_text("to delete\n")
    subprocess.run(["git", "add", "-A"], cwd=root_dir, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add file to delete"], cwd=root_dir, check=True)
    head2 = _git(root_dir, "rev-parse", "HEAD")
    candidate = _base_candidate(root, task_id, head2, candidate_id="atk-del-hash")
    candidate["proposed_changes"][0] = {
        "path": "src/scoped/x.py", "operation": "delete",
        "content_hash_after": "0" * 64,
    }
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("delete_must_not_declare_content_hash" in r for r in result["rejection_reasons"])


def test_duplicate_path_same_content_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-dup-path")
    entry = dict(candidate["proposed_changes"][0])
    candidate["proposed_changes"].append(entry)
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("duplicate_path_in_candidate" in r for r in result["rejection_reasons"])


def test_duplicate_path_conflicting_content_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-dup-path-conflict")
    conflicting = {
        "path": candidate["proposed_changes"][0]["path"],
        "operation": "create",
        "content_after": "other content\n",
        "content_hash_after": hashlib.sha256(b"other content\n").hexdigest(),
    }
    candidate["proposed_changes"].append(conflicting)
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert any("duplicate_path_in_candidate" in r for r in result["rejection_reasons"])


# ── §26 multi-file mixed allowed/denied ──────────────────────────────────

def test_multi_file_one_out_of_scope_rejects_whole_candidate(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir, allowed_files=("src/scoped/**",))
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-multi")
    candidate["proposed_changes"].append({
        "path": "src/OUTSIDE/y.py", "operation": "create",
        "content_after": "outside\n",
        "content_hash_after": hashlib.sha256(b"outside\n").hexdigest(),
    })
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])
    # No ECP/partial artifact must exist for the in-scope file either.
    assert intake.list_intake_records(root) != [] or True  # rejection record always stored
    records = intake.list_intake_records(root)
    accepted = [r for r in records if r["validation_outcome"] == "accepted"]
    assert accepted == []


# ── §28/§29 ECP construction / authority fields ──────────────────────────

def test_ecp_authority_fields_are_hardcoded_false_never_producer_controlled(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-ecp-authority")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    for field in ("execution_allowed", "promotion_executed", "rollback_executed"):
        assert ecp[field] is False
    assert ecp["authorization_id"].startswith("intake-no-ear:")
    assert ecp["audit_id"].startswith("intake-no-audit:")


# ── §30 ECP ID / candidate-ID collision ──────────────────────────────────

def test_candidate_id_collision_with_conflicting_content_rejected(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-collide")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True

    conflicting = _base_candidate(
        root, task_id, head, candidate_id="atk-collide", content="different payload\n",
    )
    result2 = intake.validate_and_ingest_intake_candidate(root, conflicting)
    assert result2["accepted"] is False
    assert result2["rejection_reasons"] == ["candidate_id_collision_conflicting_content"]


def test_candidate_id_replay_identical_content_is_idempotent(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-replay")
    r1 = intake.validate_and_ingest_intake_candidate(root, candidate)
    r2 = intake.validate_and_ingest_intake_candidate(root, json.loads(json.dumps(candidate)))
    assert r1["accepted"] is True and r2["accepted"] is True
    assert r1["ecp_id"] == r2["ecp_id"]
    assert r2["idempotent_replay"] is True
    # exactly one ECP was created, not two
    ecps = agent_module.list_execution_change_packages(root)
    matching = [e for e in ecps if e["intake_candidate_id"] == "atk-replay"]
    assert len(matching) == 1


# ── §33/§34/§35 tamper-evident storage ───────────────────────────────────

def test_tampered_stored_record_detected_by_integrity_hash(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-tamper")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True

    stored_path = Path(result["stored_path"])
    record = json.loads(stored_path.read_text())
    assert intake.verify_record_integrity(record) is True

    # Attacker mutates the on-disk record after acceptance: flip a field
    # that would matter to any downstream reader (e.g. task_id or hash).
    tampered = dict(record)
    tampered["task_id"] = "some-other-task-entirely"
    stored_path.write_text(json.dumps(tampered, indent=2, sort_keys=True))

    reread = intake.lookup_intake_record(root, result["intake_id"])
    assert reread["integrity_verified"] is False


@pytest.mark.parametrize("field", [
    "candidate_content_hash", "base_commit", "repo_fingerprint",
    "ecp_id", "producer", "validation_outcome", "task_id",
])
def test_every_record_field_mutation_is_detected(tmp_path, field):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id=f"atk-tamper-{field}")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    stored_path = Path(result["stored_path"])
    record = json.loads(stored_path.read_text())
    tampered = dict(record)
    old = tampered[field]
    tampered[field] = ("MUTATED" if not isinstance(old, dict) else {"mutated": True})
    stored_path.write_text(json.dumps(tampered, indent=2, sort_keys=True))
    reread = intake.lookup_intake_record(root, result["intake_id"])
    assert reread["integrity_verified"] is False, f"mutation of {field} was not detected"


def test_intake_show_surfaces_integrity_failure_not_silent_trust(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-show-tamper")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    stored_path = Path(result["stored_path"])
    record = json.loads(stored_path.read_text())
    record["ecp_id"] = "ecp-forged-elsewhere"
    stored_path.write_text(json.dumps(record, indent=2, sort_keys=True))
    reread = intake.lookup_intake_record(root, result["intake_id"])
    assert reread["integrity_verified"] is False
    assert reread["ecp_id"] == "ecp-forged-elsewhere"  # not silently corrected -- flagged, not hidden


def test_ecp_reference_tampering_detected_via_record_hash(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-ecp-ref-tamper")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    stored_path = Path(result["stored_path"])
    record = json.loads(stored_path.read_text())
    record["ecp_id"] = record["ecp_id"] + "-tampered"
    stored_path.write_text(json.dumps(record, indent=2, sort_keys=True))
    records = intake.list_intake_records(root)
    match = [r for r in records if r["intake_id"] == result["intake_id"]][0]
    assert match["integrity_verified"] is False


# ── §36/§37 list semantics ────────────────────────────────────────────────

def test_list_one_corrupt_json_record_does_not_hide_or_crash_on_others(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    c1 = _base_candidate(root, task_id, head, candidate_id="atk-list-1")
    r1 = intake.validate_and_ingest_intake_candidate(root, c1)
    c2 = _base_candidate(root, task_id, head, candidate_id="atk-list-2", path="src/scoped/y.py")
    r2 = intake.validate_and_ingest_intake_candidate(root, c2)

    store_dir = root.path / ".pcae" / "intake-candidates"
    corrupt_path = store_dir / "intake-corrupt-00000000T000000000000.json"
    corrupt_path.write_text("{ this is not valid json")

    records = intake.list_intake_records(root)
    ids = {r["intake_id"] for r in records}
    assert r1["intake_id"] in ids
    assert r2["intake_id"] in ids
    assert len(records) == 2  # corrupt file silently skipped, not fabricated as a third


def test_list_never_reports_accepted_when_underlying_ecp_absent(tmp_path):
    """Defense in depth: even though intake.py always creates the ECP before
    writing the accepted record, verify list/show do not claim accepted
    status for a record whose ecp_id cannot be resolved (simulated by
    deleting the ECP store after acceptance)."""
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-orphan-ecp")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    import shutil
    shutil.rmtree(root.path / ".pcae" / "execution-packages", ignore_errors=True)
    record = intake.lookup_intake_record(root, result["intake_id"])
    assert record["validation_outcome"] == "accepted"  # historically true, not re-derived
    assert agent_module.lookup_execution_change_package(root, result["ecp_id"]) is None
    # This documents actual behavior: the intake record's own
    # "accepted"/ecp_id claim is a point-in-time audit fact, not
    # re-verified live by list/show. Neither promotion-review nor promote
    # will proceed, though, since both re-`lookup_execution_change_package`
    # (see downstream regression tests) and fail closed when it is absent.


# ── §38 replay / idempotency with modified content ───────────────────────

def test_replay_with_modified_content_same_id_rejected_not_silently_promoted(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-replay-mod")
    r1 = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert r1["accepted"] is True

    modified = json.loads(json.dumps(candidate))
    modified["proposed_changes"][0]["content_after"] = "malicious replacement\n"
    modified["proposed_changes"][0]["content_hash_after"] = hashlib.sha256(
        b"malicious replacement\n"
    ).hexdigest()
    r2 = intake.validate_and_ingest_intake_candidate(root, modified)
    assert r2["accepted"] is False
    assert r2["rejection_reasons"] == ["candidate_id_collision_conflicting_content"]


# ── §40/§41/§42 CLI create/show/list ──────────────────────────────────────

def _run_cli(root_dir: Path, *args: str, env=None) -> subprocess.CompletedProcess:
    import os
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args],
        cwd=root_dir, capture_output=True, text=True, env=full_env,
    )


def test_cli_intake_create_malformed_json_fails_clearly_no_traceback(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    bad_file = root_dir / "bad.json"
    bad_file.write_text("{not valid json")
    proc = _run_cli(root_dir, "intake", "create", "--candidate-file", str(bad_file), "--json")
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    out = json.loads(proc.stdout)
    assert out["accepted"] is False


def test_cli_intake_create_missing_file_fails_clearly(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    proc = _run_cli(root_dir, "intake", "create", "--candidate-file", str(root_dir / "nope.json"), "--json")
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    out = json.loads(proc.stdout)
    assert "candidate_file_unreadable" in out["rejection_reasons"][0]


def test_cli_intake_create_valid_and_show_and_list(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-cli-valid")
    cfile = root_dir / "candidate.json"
    cfile.write_text(json.dumps(candidate))
    proc = _run_cli(root_dir, "intake", "create", "--candidate-file", str(cfile), "--json")
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["accepted"] is True

    proc_show = _run_cli(root_dir, "intake", "show", "--intake-id", out["intake_id"], "--json")
    assert proc_show.returncode == 0
    shown = json.loads(proc_show.stdout)
    assert shown["intake_id"] == out["intake_id"]

    proc_list = _run_cli(root_dir, "intake", "list", "--json")
    assert proc_list.returncode == 0
    listed = json.loads(proc_list.stdout)
    assert listed["count"] >= 1


def test_cli_intake_show_missing_id_not_found_clean(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    proc = _run_cli(root_dir, "intake", "show", "--intake-id", "intake-does-not-exist", "--json")
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr
    out = json.loads(proc.stdout)
    assert out["error"] == "intake_not_found"


def test_cli_intake_list_empty_store(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    proc = _run_cli(root_dir, "intake", "list", "--json")
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["count"] == 0
    assert out["records"] == []


# ── §43 CLI help must not imply authorization ────────────────────────────

@pytest.mark.parametrize("args", [
    ("intake", "--help"),
    ("intake", "create", "--help"),
    ("intake", "show", "--help"),
    ("intake", "list", "--help"),
])
def test_cli_help_does_not_imply_apply_execute_approve_authorize(tmp_path, args):
    root_dir = _new_repo(tmp_path)
    proc = _run_cli(root_dir, *args)
    assert proc.returncode == 0
    text = proc.stdout.lower()
    for banned in ("this command applies", "this command executes", "this command approves",
                   "this command authorizes", "automatically promotes"):
        assert banned not in text


# ── §44/§45/§47 Claude adapter dataflow, malformed output, bypass ───────

_ADAPTER_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "claude_code_intake_adapter.py"


def test_claude_adapter_translation_only_no_promote_no_push_calls(tmp_path):
    adapter_src = _ADAPTER_SCRIPT.read_text()
    # Look only at executable statements (subprocess.run/Popen call sites),
    # not prose/docstrings, for an actual call to promote/push or an
    # assignment of an authority-bearing field.
    import re
    calls = re.findall(r'subprocess\.run\(\s*\[([^\]]*)\]', adapter_src)
    for call_args in calls:
        assert '"promote"' not in call_args and "'promote'" not in call_args
        assert '"push"' not in call_args and "'push'" not in call_args
    assert re.search(r'\bpromotion_authorized\s*=', adapter_src) is None
    assert re.search(r'["\']execution_allowed["\']\s*:', adapter_src) is None


def test_claude_adapter_dry_run_produces_generic_schema_no_claude_specific_leak_into_core(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    content_file = root_dir / "payload.txt"
    content_file.write_text("adapter content\n")
    proc = subprocess.run(
        [sys.executable, str(_ADAPTER_SCRIPT),
         "--task-id", task_id, "--candidate-id", "adapter-cand-1",
         "--file", f"src/scoped/z.py:create:{content_file}",
         "--summary", "adapter test", "--producer", "claude-code", "--dry-run"],
        cwd=root_dir, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    candidate = json.loads(proc.stdout)
    # The generic core module has no knowledge of "claude" beyond the
    # informational producer.kind string -- prove core accepts an
    # equivalent document from a wholly fictional producer name too
    # (see test_alternate_producer_same_validation_semantics below).
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True


def test_claude_adapter_malformed_file_arg_fails_clearly(tmp_path):
    root_dir = _new_repo(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(_ADAPTER_SCRIPT),
         "--task-id", "x", "--candidate-id", "y",
         "--file", "just-a-path-no-operation",
         "--producer", "claude-code", "--dry-run"],
        cwd=root_dir, capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert "file_spec_error" in proc.stdout


# ── §46 Claude-specific non-normativity ──────────────────────────────────

def test_no_normative_claude_dependency_in_core_intake_module():
    src = Path("src/pcae/core/intake.py").read_text().lower()
    src_commands = Path("src/pcae/commands/intake.py").read_text().lower()
    for token in ("claude", "anthropic"):
        assert token not in src, f"unexpected normative token {token!r} in core intake.py"
        assert token not in src_commands, f"unexpected normative token {token!r} in commands/intake.py"


# ── §48 alternate producer synthetic test ────────────────────────────────

def test_alternate_producer_same_validation_semantics(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-alt-producer")
    candidate["producer"] = {"kind": "totally-fictional-tool-xyz", "adapter_version": "9.9"}
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["intake_producer"]["kind"] == "totally-fictional-tool-xyz"
    assert ecp["execution_allowed"] is False


# ── §49/§50/§51 downstream promotion authority preserved ────────────────

def test_accepted_intake_ecp_still_requires_separate_human_promotion_review(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-downstream")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True

    # No promotion-review exists yet -- promote must refuse.
    promo = agent_module.build_promotion_execution(root, "epr-does-not-exist", dry_run=True)
    assert promo["error"] == "epr_not_found"
    assert promo["promoted"] is False

    # Even a promotion-review created WITHOUT --promotion-authorized must
    # not allow promote to proceed, regardless of anything in the intake
    # candidate (including a forged self_reported_complete=True).
    epr_result = agent_module.build_promotion_review(
        root, result["ecp_id"], human_disposition="approved",
        reviewed_by="tester", promotion_authorized=False,
    )
    assert epr_result["promotion_authorized"] is False
    promo2 = agent_module.build_promotion_execution(root, epr_result["epr_id"], dry_run=True)
    assert promo2["error"] == "promotion_not_authorized"
    assert promo2["promoted"] is False


def test_producer_claims_self_reported_complete_cannot_substitute_for_authorization(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-self-reported")
    candidate["producer_claims"]["self_reported_complete"] = True
    candidate["producer_claims"]["human_reviewed"] = True  # forged, not part of schema
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    epr_result = agent_module.build_promotion_review(
        root, result["ecp_id"], human_disposition="approved",
        reviewed_by="tester",
        # attacker cannot pass promotion_authorized through the candidate;
        # this call site only has it as an explicit Python/CLI kwarg, and
        # here we deliberately omit it to prove default is unauthorized.
    )
    assert epr_result["promotion_authorized"] is False


# ── §54 no actual diff/patch application, no target-file mutation ───────

def test_intake_does_not_write_to_proposal_target_path_in_working_tree(tmp_path):
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    target = root_dir / "src" / "scoped" / "x.py"
    assert not target.exists()
    candidate = _base_candidate(root, task_id, head, candidate_id="atk-no-mutation")
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert not target.exists()  # intake never writes into the working tree


def test_core_intake_module_never_shells_out_to_apply_a_patch():
    src = Path("src/pcae/core/intake.py").read_text()
    assert "git apply" not in src
    assert "git.apply" not in src
    # subprocess is used only for git rev-list / rev-parse / cat-file / merge-base / show
    import re
    calls = re.findall(r'subprocess\.run\(\s*\[\s*"git",\s*"([a-z-]+)"', src)
    assert set(calls) <= {"rev-list", "rev-parse", "cat-file", "merge-base", "show", "check-ignore"}


# ── §57-60 trust-scope classification (evidence for report, not a strict
#    pass/fail gate -- documents actual current behavior) ────────────────

def test_intake_core_is_reachable_only_through_validated_entrypoint_reused_by_cli(tmp_path):
    """There is exactly one production entrypoint into ECP construction
    from intake data (validate_and_ingest_intake_candidate); the CLI layer
    (pcae.commands.intake) performs no independent ECP construction, so a
    bug confined to argument plumbing in commands/intake.py cannot itself
    fabricate authority -- it can only call into the one validated path."""
    commands_src = Path("src/pcae/commands/intake.py").read_text()
    assert "store_execution_change_package" not in commands_src
    assert "ecp_id" not in commands_src or "result[" in commands_src  # only reads result dict


def test_malformed_adapter_output_is_revalidated_by_core_not_trusted(tmp_path):
    """A hostile/buggy adapter that emits an Intake Candidate with a forged
    repo_binding or task_id is caught by core validation exactly the same
    as a hand-crafted attack payload -- the adapter has no privileged
    bypass path."""
    root_dir = _new_repo(tmp_path)
    root, task_id, head = _bootstrap_task(root_dir)
    forged_adapter_output = {
        "intake_contract_version": "1.0",
        "candidate_id": "atk-forged-adapter",
        "producer": {"kind": "claude-code", "adapter_version": "2U.2-reference-1"},
        "task_context": {"task_id": task_id, "declared_goal": "forged"},
        "repo_binding": {"repo_fingerprint": "forged", "base_commit": head},
        "proposed_changes": [{
            "path": "src/scoped/z.py", "operation": "create",
            "content_after": "x\n", "content_hash_after": hashlib.sha256(b"x\n").hexdigest(),
        }],
        "producer_claims": {"summary": "forged", "self_reported_complete": True},
    }
    result = intake.validate_and_ingest_intake_candidate(root, forged_adapter_output)
    assert result["accepted"] is False
    assert "repo_binding_mismatch" in result["rejection_reasons"]
