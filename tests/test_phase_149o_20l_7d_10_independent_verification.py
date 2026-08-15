"""Phase 149O.20L.7D.10 -- Repaired-Source Redeployment + Action-9
Amendment Independent Authorization Verification.

Independently-authored companion test module. Does NOT import 7D.9's
own test module as oracle, and does NOT treat 7D.9's phase-completion
report prose as ground truth -- every assertion here is re-derived
directly from primary git objects, the production
`derive_implementation_scope_digest()` function (called fresh against
disposable roots), and the on-disk CHGR/decision-session JSON records
themselves.

Live Dell SSH facts (machine-id, source baseline, wrapper digest, venv
metadata, PATH resolution) were independently re-verified this phase
over a fresh read-only `ssh hac-dell` session; they are captured here
only as static constants (mirroring what this phase's own report
records), matching this project's established convention (7D.9's own
test module does the same for its own live-Dell findings) -- this
module does not re-SSH into Dell.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DOC = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7D_10_REPAIRED_SOURCE_REDEPLOYMENT_ACTION_9_AMENDMENT_INDEPENDENT_AUTHORIZATION_VERIFICATION.md"
)

OLD_DEPLOYED_SHA = "7a3fa971304521cdcb44251e07ef1966baec686a"
CANDIDATE_SHA = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
REPAIR_COMMIT_SHA = "73ea8b237a2fd4b6c0f22987eea7f748bcc97ca2"

CANDIDATE_DIGEST = "4e3452ba3647df6ccebf2bd093b78c4ae4b8d6eacc3de8212e09ba14804ad2ac"
OLD_DEPLOYED_DIGEST = "b728d368ee830d1e6f6e3c1fc44ca97d4826e3cf124c47c7c549b307dd1a545d"

WRAPPER_DIGEST = "b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32"
MACHINE_ID = "54ff22ce400b475aa0d55cb68f4a3334"

CANDIDATE_TRACKED_PATH_COUNT = 4108
CANDIDATE_100644_COUNT = 4097
CANDIDATE_100755_COUNT = 11

THREE_REPAIRED_FILES = (
    "src/pcae/core/hatp_class_b_conformance.py",
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
)

NEW_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"
NEW_CHGR_CONF_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgrconf-51029a1d6bb0451badc1fe464ac9a457.json"
OLD_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-96a0ce12756e4cc892492a87af1db832.json"
CONTINUATION_CHGR_PATH = REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-541cb08c313b4f8884970172d37c5a1d.json"

SUCCESSFUL_SESSION_PATH = REPO_ROOT / ".pcae" / "decision-sessions" / "CDS-105d30f5-5481-4fcc-b295-4a4c05fc7edb.json"
ABANDONED_SESSION_PATHS = (
    REPO_ROOT / ".pcae" / "decision-sessions" / "CDS-9fac483e-7fbe-4c0b-8ecb-3ca6d51f2175.json",
    REPO_ROOT / ".pcae" / "decision-sessions" / "CDS-a2e437a8-cbcf-4578-8d07-e7efc7fa9e67.json",
)


def _git(*args: str) -> str:
    """Strictly read-only git query (rev-parse/cat-file/ls-tree/diff
    --stat/diff --name-status/merge-base/log/ls-files) -- never
    fetch/checkout/commit/push/reset against this repository."""

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════
# Candidate SHA authenticity and drift (re-derived fresh this phase)
# ═══════════════════════════════════════════════════════════════════════════


def test_candidate_sha_is_a_commit_object():
    assert _git("cat-file", "-t", CANDIDATE_SHA) == "commit"


def test_candidate_is_ancestor_of_origin_main():
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", CANDIDATE_SHA, "origin/main"],
        cwd=REPO_ROOT,
        check=True,
    )


def test_candidate_contains_repair_commit_despite_misleading_subject():
    subject = _git("log", "-1", "--format=%s", CANDIDATE_SHA)
    assert "pcae_push_check" in subject
    assert "Class-B" not in subject
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", REPAIR_COMMIT_SHA, CANDIDATE_SHA],
        cwd=REPO_ROOT,
        check=True,
    )


def test_exactly_three_files_differ_old_deployed_to_candidate():
    diff = _git(
        "diff",
        "--name-status",
        OLD_DEPLOYED_SHA,
        CANDIDATE_SHA,
        "--",
        "src/",
        "scripts/",
        "docs/contracts/",
        "pyproject.toml",
    )
    changed = {line.split("\t", 1)[1] for line in diff.splitlines() if line}
    assert changed == set(THREE_REPAIRED_FILES)


def test_candidate_bytes_identical_to_current_head_for_repaired_files():
    diff = _git("diff", CANDIDATE_SHA, "HEAD", "--", *THREE_REPAIRED_FILES)
    assert diff == ""


def test_zero_authority_relevant_drift_after_candidate():
    diff = _git(
        "diff",
        "--stat",
        CANDIDATE_SHA,
        "HEAD",
        "--",
        "src/",
        "scripts/",
        "docs/contracts/",
        "pyproject.toml",
    )
    assert diff == ""


# ═══════════════════════════════════════════════════════════════════════════
# Candidate tree inventory -- independently enumerated, not inherited
# ═══════════════════════════════════════════════════════════════════════════


def test_candidate_tracked_path_count_and_mode_inventory(tmp_path):
    worktree = tmp_path / "candidate-wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), CANDIDATE_SHA],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    try:
        total = subprocess.run(
            ["git", "ls-files"], cwd=worktree, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        assert len(total) == CANDIDATE_TRACKED_PATH_COUNT

        modes = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"], cwd=worktree, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        mode_counts: dict[str, int] = {}
        for line in modes:
            mode = line.split()[0]
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        assert mode_counts.get("100644") == CANDIDATE_100644_COUNT
        assert mode_counts.get("100755") == CANDIDATE_100755_COUNT
        assert sum(mode_counts.values()) == CANDIDATE_TRACKED_PATH_COUNT
        assert set(mode_counts) == {"100644", "100755"}
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )


# ═══════════════════════════════════════════════════════════════════════════
# HMIC implementation digest -- recomputed fresh via disposable worktrees
# ═══════════════════════════════════════════════════════════════════════════


def _derive_digest_at(sha_or_head: str, tmp_path: Path) -> str:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest
    from pcae.core.paths import HarnessPath

    if sha_or_head == "HEAD":
        root = REPO_ROOT
    else:
        root = tmp_path / f"wt-{sha_or_head[:8]}"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(root), sha_or_head],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
    try:
        return derive_implementation_scope_digest(HarnessPath(root))
    finally:
        if root != REPO_ROOT:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(root)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )


def test_implementation_scope_digest_independently_recomputed(tmp_path):
    assert _derive_digest_at(CANDIDATE_SHA, tmp_path) == CANDIDATE_DIGEST
    assert _derive_digest_at(OLD_DEPLOYED_SHA, tmp_path) == OLD_DEPLOYED_DIGEST
    assert _derive_digest_at("HEAD", tmp_path) == CANDIDATE_DIGEST


def test_three_repaired_verifiers_are_hmic_frozen_members():
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from pcae.core import hatp_mandatory_certification as hmic

    src_relative = set(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES)
    for repaired_file in THREE_REPAIRED_FILES:
        relative = repaired_file.removeprefix("src/pcae/")
        assert relative in src_relative
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 28


# ═══════════════════════════════════════════════════════════════════════════
# Contract identity unchanged (HMIC-001 byte-identical across the span)
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_contract_bytes_unchanged_old_to_candidate_to_head():
    diff_old_candidate = _git(
        "diff",
        OLD_DEPLOYED_SHA,
        CANDIDATE_SHA,
        "--",
        "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    )
    diff_candidate_head = _git(
        "diff",
        CANDIDATE_SHA,
        "HEAD",
        "--",
        "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    )
    assert diff_old_candidate == ""
    assert diff_candidate_head == ""


# ═══════════════════════════════════════════════════════════════════════════
# New CHGR -- exact source/PATH/HMIC-disclosure text binding
# ═══════════════════════════════════════════════════════════════════════════


def test_new_chgr_published_and_binds_full_candidate_sha_by_text():
    record = _load_json(NEW_CHGR_PATH)
    assert record["lifecycle_state"] == "published"
    assert record["selected_option_id"] == "approve"
    assert set(json.loads(NEW_CHGR_CONF_PATH.read_text())["confirmer_identity_evidence"]) >= {
        "captured_at",
        "identifier",
    }
    assert CANDIDATE_SHA in record["decision_subject"]
    assert CANDIDATE_SHA in record["rationale"]
    # No abbreviated form, no bare branch name substituted for the full SHA.
    assert CANDIDATE_SHA[:8] + " " not in record["decision_subject"].replace(CANDIDATE_SHA, "")


def test_new_chgr_binds_corrected_action9_path_by_text():
    record = _load_json(NEW_CHGR_PATH)
    corrected_path = "/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    assert corrected_path in record["rationale"]


def test_new_chgr_discloses_hmic_not_certified_for_boundary_c():
    record = _load_json(NEW_CHGR_PATH)
    rationale = record["rationale"]
    assert "NOT-CERTIFIED-FOR-BOUNDARY-C" in rationale or "NOT CERTIFIED FOR BOUNDARY C" in rationale


def test_new_chgr_confirmation_statement_present_and_distinct_field():
    confirmation = _load_json(NEW_CHGR_CONF_PATH)
    assert confirmation["confirmation_statement"] == "Accepted"
    record = _load_json(NEW_CHGR_PATH)
    # Confirmation is a structurally separate artifact/field from the election rationale.
    assert confirmation["confirmation_statement"] != record["rationale"]
    assert record["confirmation_evidence_ref"]["record_id"] == confirmation["record_id"]


# ═══════════════════════════════════════════════════════════════════════════
# Old CHGRs do not authorize this transition (read from their own text)
# ═══════════════════════════════════════════════════════════════════════════


def test_original_chgr_does_not_authorize_candidate_transition():
    record = _load_json(OLD_CHGR_PATH)
    combined = record["decision_subject"] + record["rationale"]
    assert CANDIDATE_SHA not in combined
    assert OLD_DEPLOYED_SHA in combined


def test_continuation_chgr_predates_repair_and_does_not_authorize_it():
    record = _load_json(CONTINUATION_CHGR_PATH)
    combined = record["decision_subject"] + record["rationale"]
    assert CANDIDATE_SHA not in combined
    candidate_commit_iso = _git("log", "-1", "--format=%cI", CANDIDATE_SHA)
    assert record["created_at"] < candidate_commit_iso.replace("+02:00", "Z") or record["created_at"] < candidate_commit_iso


# ═══════════════════════════════════════════════════════════════════════════
# Decision-session workflow: successful session + abandoned-session isolation
# ═══════════════════════════════════════════════════════════════════════════


def test_successful_session_subject_within_schema_limit():
    session = _load_json(SUCCESSFUL_SESSION_PATH)["session"]
    assert session["session_state"] == "Confirmed"
    assert len(session["subject_ref"]) <= 500
    assert session["human_selection_id"] == "approve"
    assert set(session["options_presented"]) == {"approve", "decline", "amend"}


def test_abandoned_sessions_never_published_and_isolated():
    published_chgr_dir = REPO_ROOT / ".pcae" / "publication-execution" / "records"
    all_chgr_text = "\n".join(
        p.read_text(encoding="utf-8") for p in published_chgr_dir.glob("chgr-*.json")
    )
    for path in ABANDONED_SESSION_PATHS:
        session_id = path.stem
        assert session_id not in all_chgr_text


def test_second_abandoned_session_exceeds_schema_subject_limit():
    session = _load_json(ABANDONED_SESSION_PATHS[1])["session"]
    assert len(session["subject_ref"]) > 500


def test_governance_record_verify_related_passes():
    pcae_binary = shutil.which("pcae")
    assert pcae_binary is not None, "pcae CLI must be installed/on PATH for this check"
    result = subprocess.run(
        [
            pcae_binary,
            "governance-record",
            "verify",
            str(NEW_CHGR_PATH),
            "--related",
            str(NEW_CHGR_CONF_PATH),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["outcome"] == "verified"
    checks = {c["name"]: c["status"] for c in payload["checks"]}
    for required in ("schema_shape", "digest_self_consistency", "lifecycle_structural_legality", "confirmation_binding"):
        assert checks[required] == "passed"


# ═══════════════════════════════════════════════════════════════════════════
# Rollback network-independence -- adversarial, network-disabled reproduction
# ═══════════════════════════════════════════════════════════════════════════


def test_rollback_succeeds_with_network_disabled(tmp_path):
    bare = tmp_path / "sim-bare.git"
    clone = tmp_path / "sim"
    subprocess.run(["git", "clone", "--mirror", str(REPO_ROOT), str(bare)], check=True, capture_output=True)
    subprocess.run(["git", "clone", str(bare), str(clone)], check=True, capture_output=True)

    subprocess.run(["git", "checkout", "--detach", OLD_DEPLOYED_SHA], cwd=clone, check=True, capture_output=True)
    subprocess.run(["git", "fetch", "origin", CANDIDATE_SHA], cwd=clone, check=True, capture_output=True)
    subprocess.run(["git", "checkout", "--detach", CANDIDATE_SHA], cwd=clone, check=True, capture_output=True)

    # Sever the remote before attempting rollback.
    subprocess.run(
        ["git", "remote", "set-url", "origin", "https://invalid.invalid/nonexistent.git"],
        cwd=clone,
        check=True,
        capture_output=True,
    )
    rollback = subprocess.run(
        ["git", "checkout", "--detach", OLD_DEPLOYED_SHA], cwd=clone, capture_output=True, text=True
    )
    assert rollback.returncode == 0

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=clone, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert head == OLD_DEPLOYED_SHA


# ═══════════════════════════════════════════════════════════════════════════
# No-mutation and report-consistency
# ═══════════════════════════════════════════════════════════════════════════


def test_no_authority_relevant_source_mutated_by_this_phase():
    status = _git("status", "--short", "--", "src/", "scripts/", "docs/contracts/", "pyproject.toml")
    assert status == ""


def test_report_document_exists_and_states_final_verdict():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert "VERIFIED AUTHORIZED FOR REPAIRED-SOURCE REDEPLOYMENT" in text
    assert CANDIDATE_SHA in text
    assert OLD_DEPLOYED_SHA in text
    assert "chgr-0e37ed1340b14311826722c4dbf3e856" in text


def test_report_discloses_election_confirmation_timestamp_observation():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert "non-blocking" in text.lower()


def test_report_records_live_dell_wrapper_digest_and_machine_id():
    text = REPORT_DOC.read_text(encoding="utf-8")
    assert WRAPPER_DIGEST in text
    assert MACHINE_ID in text
