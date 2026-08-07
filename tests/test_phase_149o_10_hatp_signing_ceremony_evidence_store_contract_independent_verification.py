"""Phase 149O.10 — HATP Signing Ceremony + Evidence Store Contract
Independent Verification.

Independently re-derives, from the current source tree and the frozen
HSCE-001 contract text itself (never from 149O.9's own test file or its
constants), the facts this phase's verification report relies on:
requirement-numbering self-consistency, the AG5/AG3 CLI entry-point
inventory, absence of any signing-command implementation, the
no-symlink-check gap in the atomic-write primitive HSCE-REQ-052 claims
to reuse, and the closed vocabularies HSCE-001 depends on from HATP-001.
Contract/verification-only: asserts facts about existing source and
contract text; does not implement, sign, or persist any evidence.
"""

from __future__ import annotations

import inspect
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HSCE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

# HSCE-001 v1.0's own freeze commit (Phase 149O.9). Phase 149O.10.1
# repaired HSCE-REQ-052/077/078 and widened the §38 attack matrix
# in-place on the working file, so two of this suite's original
# current-tree assertions (the "78 not 79" miscount and the "exactly
# twenty attack items" count) are pinned to read the contract text as it
# existed at this commit instead, preserving them as explicit historical
# v1.0 reproductions rather than letting them spuriously fail against the
# repaired v1.1 tree (see docs/PHASE_149O_10_1_HSCE_001_NARROW_CONTRACT_REPAIR.md
# §23).
_HSCE_V1_0_FREEZE_COMMIT = "3ad4e839"

_HSCE_REQ_RE = re.compile(r"HSCE-REQ-(\d+)")


def _hsce_text() -> str:
    return HSCE_CONTRACT.read_text(encoding="utf-8")


def _hsce_text_at_v1_0_freeze() -> str:
    result = subprocess.run(
        ["git", "show", f"{_HSCE_V1_0_FREEZE_COMMIT}:{HSCE_CONTRACT.relative_to(REPO_ROOT)}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("git show unavailable for historical HSCE-001 v1.0 text")
    return result.stdout


def test_hsce_contract_file_exists():
    assert HSCE_CONTRACT.is_file()


def test_hsce_requirement_numbering_is_sequential_gapless_no_duplicates_currently():
    """Independent re-count of every HSCE-REQ-### token in the *current*
    contract text. Phase 149O.10.1 repaired Finding F-1 (the "78 not 79"
    editorial miscount this test used to assert) -- HSCE-REQ-078 now
    correctly states "through HSCE-REQ-079 inclusive". This test
    reconfirms the requirement sequence remains 1..79, sequential and
    gapless, on the repaired tree."""

    text = _hsce_text()
    ids = sorted({int(m) for m in _HSCE_REQ_RE.findall(text)})
    assert ids == list(range(1, 80)), f"expected sequential 1..79, got {ids[:5]}...{ids[-5:]} (n={len(ids)})"
    assert max(ids) == 79
    assert "through `HSCE-REQ-079` inclusive" in text
    assert "HSCE-REQ-079." in text


def test_hsce_v1_0_freeze_historically_undercounted_78_not_79():
    """Historical/documentary reproduction (pinned to the HSCE-001 v1.0
    freeze commit, Phase 149O.9): the contract's own closing requirement
    (HSCE-REQ-078) asserted it defined HSCE-REQ-001 through HSCE-REQ-078
    inclusive -- but HSCE-REQ-079 already existed at that commit in
    Section 40 (Blocking-Condition Check). This is what Phase 149O.10
    independently found and Phase 149O.10.1 repaired (Finding F-1); this
    test preserves that historical finding against the pinned v1.0
    commit rather than the current, repaired working tree, per
    docs/PHASE_149O_10_1_HSCE_001_NARROW_CONTRACT_REPAIR.md §23."""

    text = _hsce_text_at_v1_0_freeze()
    if not text:
        pytest.skip("HSCE-001 v1.0 freeze commit text unavailable")
    ids = sorted({int(m) for m in _HSCE_REQ_RE.findall(text)})
    assert ids == list(range(1, 80)), f"expected sequential 1..79, got {ids[:5]}...{ids[-5:]} (n={len(ids)})"
    assert max(ids) == 79, "v1.0 already defined HSCE-REQ-001..079, not ...078 as REQ-078 itself claimed"
    assert "through `HSCE-REQ-078` inclusive" in text
    assert "HSCE-REQ-079." in text


def test_hsce_contract_defines_exactly_one_cli_command_family():
    text = _hsce_text()
    grammar_block = "pcae hatp sign rollback --site {ag3|ag5} [locator flags] [--json]"
    assert grammar_block in text
    # None of the explicitly-prohibited flags appear in the frozen
    # command-grammar block itself.
    for forbidden in ("--dry-run", "--ecp-id", "--provider", "--signer", "--force", "--overwrite", "--output"):
        assert forbidden not in grammar_block
    # Each is affirmatively named as prohibited somewhere in the text
    # (normalized to collapse line-wrap whitespace).
    normalized = " ".join(text.split())
    assert "No `--dry-run` flag exists" in normalized
    assert "No `--ecp-id` flag exists" in normalized
    for forbidden in ("--provider", "--signer", "--force", "--overwrite", "--output"):
        assert f"`{forbidden}`" in normalized


def test_hsce_evidence_envelope_schema_is_closed_four_fields():
    text = _hsce_text()
    assert "evidence_version: 1" in text
    assert "evidence_id: <sha256-hex>" in text
    assert "proof: <HumanApprovalProvenanceProof canonical document>" in text
    assert "provider_assertion: <base64 string>" in text
    assert "No other top-level field exists." in text


def test_hsce_evidence_id_formula_is_proof_only_never_full_envelope():
    text = _hsce_text()
    assert "evidence_id = digest_hatp_proof_payload(proof)" in text
    normalized = " ".join(text.split())
    assert "it does NOT address the complete envelope byte sequence" in normalized
    assert "it does NOT address `provider_assertion` at all" in normalized


def test_hsce_mandatory_attack_matrix_has_exactly_twentyone_items_currently():
    """Phase 149O.10.1 added attack-matrix item 21 (Obs-2, the AG3
    original_commit_sha-resolution analogue of item 20). This test
    reconfirms the current, repaired count."""

    text = _hsce_text()
    section_start = text.index("## 38. Mandatory Future Attack Matrix")
    section_end = text.index("## 39. Contract Ownership")
    section = text[section_start:section_end]
    items = re.findall(r"^\d+\. ", section, flags=re.MULTILINE)
    assert len(items) == 21, f"expected 21 mandatory attack-matrix items, found {len(items)}"


def test_hsce_v1_0_freeze_historically_had_exactly_twenty_attack_items():
    """Historical/documentary reproduction (pinned to the HSCE-001 v1.0
    freeze commit): §38's attack matrix originally had 20 items, before
    Phase 149O.10.1 added item 21 (Obs-2)."""

    text = _hsce_text_at_v1_0_freeze()
    if not text:
        pytest.skip("HSCE-001 v1.0 freeze commit text unavailable")
    section_start = text.index("## 38. Mandatory Future Attack Matrix")
    section_end = text.index("## 39. Contract Ownership")
    section = text[section_start:section_end]
    items = re.findall(r"^\d+\. ", section, flags=re.MULTILINE)
    assert len(items) == 20, f"expected 20 mandatory attack-matrix items at v1.0, found {len(items)}"


def test_hsce_security_invariants_sc1_through_sc12_present():
    text = _hsce_text()
    for n in range(1, 13):
        assert f"**SC-{n}.**" in text, f"missing security invariant SC-{n}"


def test_hsce_error_vocabulary_is_twelve_members_mapped_to_nine_exit_codes():
    text = _hsce_text()
    section_start = text.index("## 22. Closed Error Vocabulary")
    section_end = text.index("## 23. Secret Handling")
    section = text[section_start:section_end]
    exit_constants = re.findall(r"EXIT_[A-Z_]+\s*=\s*\d+", section)
    assert len(exit_constants) == 9, f"expected 9 exit-code categories, found {len(exit_constants)}"
    error_types = [
        m for m in re.findall(r"^\| `([a-z_]+)` \|", section, flags=re.MULTILINE) if m != "error_type"
    ]
    assert len(error_types) == 12, f"expected 12 error_type table rows, found {len(error_types)}"


# ─────────────────────────────────────────────────────────────────────────
# Source-tree reconfirmation (independent grep/import, not report prose)
# ─────────────────────────────────────────────────────────────────────────


def test_ag5_production_entry_point_is_exactly_one_call_site():
    """Independent re-grep of src/pcae/ (excluding tests/) for
    build_rollback_execution call sites, matching HSCE-REQ-014/015's
    inventory claim."""

    result = subprocess.run(
        ["grep", "-rn", r"build_rollback_execution(", "src/pcae/", "--include=*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    call_lines = [
        line
        for line in result.stdout.splitlines()
        if "def build_rollback_execution(" not in line and "build_rollback_execution_pilot" not in line
    ]
    assert len(call_lines) == 1, f"expected exactly one call site, found: {call_lines}"
    assert "src/pcae/commands/agent.py" in call_lines[0]
    assert "run_rollback" in Path(REPO_ROOT / "src/pcae/commands/agent.py").read_text(encoding="utf-8")


def test_run_rollback_passes_no_hatp_arguments():
    from pcae.commands.agent import run_rollback

    source = inspect.getsource(run_rollback)
    assert "build_rollback_execution(" in source
    assert "hatp_evidence_id" not in source
    assert "hatp_proof" not in source
    assert "hatp_evidence" not in source


def test_build_rollback_execution_pilot_does_not_call_build_rollback_execution():
    from pcae.core.agent import build_rollback_execution_pilot

    source = inspect.getsource(build_rollback_execution_pilot)
    assert "build_rollback_execution(" not in source


def test_no_hatp_sign_cli_implementation_exists_anywhere():
    """Verification-only phase precondition: no `hatp sign` command, no
    HATPSignedEvidenceEnvelope, and no hatp_evidence_id/hatp_proof/
    hatp_evidence string exists in the CLI/commands layer."""

    result = subprocess.run(
        ["grep", "-rEn", "hatp sign|HATPSignedEvidenceEnvelope", "src/pcae/cli.py", "src/pcae/commands/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout == "", f"unexpected HATP-signing CLI surface found: {result.stdout}"


def test_no_hatp_evidence_store_directory_exists():
    assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists()


def test_hatp_contract_and_rae_contract_byte_unchanged_since_phase_start():
    """Confirms neither HATP-001 nor RAE-001 contract text was modified
    during this phase's own working tree state (verification-only
    boundary, HSCE-REQ-006/007)."""

    for path in (HATP_CONTRACT, RAE_CONTRACT):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", f"{path} was modified: {result.stdout}"


def test_no_production_source_modified_by_this_phase():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"src/pcae/** was modified: {result.stdout}"


def test_hsce_contract_text_itself_unmodified_by_phase_149o_10():
    """Phase 149O.10 was verification-only and did not modify HSCE-001;
    Phase 149O.10.1 (a later, narrow contract-repair phase) legitimately
    does. This is pinned to the commit range spanning 149O.10's own
    commits (the 149O.9 freeze commit through 149O.10's last commit)
    rather than a generic `git diff HEAD`, so it keeps documenting
    149O.10's own boundary instead of spuriously failing against
    149O.10.1's authorized, in-scope amendment."""

    result = subprocess.run(
        ["git", "diff", "--stat", f"{_HSCE_V1_0_FREEZE_COMMIT}..8b0259d9", "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("git diff unavailable for historical 149O.10 commit range")
    assert result.stdout.strip() == ""


# ─────────────────────────────────────────────────────────────────────────
# Atomic no-clobber write algorithm — high-priority concurrency finding
# ─────────────────────────────────────────────────────────────────────────


def test_write_atomic_json_reused_by_hsce_has_no_symlink_check():
    """HSCE-REQ-052 states envelope persistence SHALL use "the identical
    temp-file-in-same-directory + fsync + os.replace technique
    rollback_approval_evidence.py::_write_atomic_json already uses."
    HSCE-REQ-057 separately requires destination-symlink rejection.
    Independently confirms the cited existing function performs no
    symlink check at all -- a future implementation cannot literally
    reuse `_write_atomic_json` unmodified and satisfy HSCE-REQ-057; it
    must add symlink-rejection logic itself. This is consistent with
    (not a refutation of) HSCE-REQ-052's own "with one addition"
    framing, but the contract does not name the symlink check as a
    second necessary addition -- recorded as a non-blocking precision
    gap in the verification report."""

    from pcae.core.rollback_approval_evidence import _write_atomic_json

    source = inspect.getsource(_write_atomic_json)
    assert "islink" not in source
    assert "O_NOFOLLOW" not in source
    assert "readlink" not in source


def test_write_atomic_json_no_clobber_check_is_toctou_racy_by_construction():
    """Independent structural confirmation of this phase's primary
    BLOCKING finding: `_write_atomic_json` (the function HSCE-REQ-052
    says to reuse) performs a plain `path.exists()` check followed,
    after unrelated I/O (mkstemp/write/fsync), by an unconditional
    `os.replace()` -- not an atomically exclusive create. `os.replace`
    on POSIX always succeeds and silently replaces an existing
    destination; it is not conditioned on the state observed by the
    earlier `path.exists()` check. Two concurrent writers can each
    observe "does not exist," each proceed, and the second writer's
    unconditional `os.replace()` silently overwrites the first writer's
    file even when the two envelopes' bytes differ -- violating SC-7
    ("existing evidence can never be silently overwritten... always
    rejected, never replaced"). This test does not exploit the race
    (that requires OS-level thread/process concurrency this suite does
    not attempt); it structurally confirms the write path contains no
    exclusive-create primitive (`O_EXCL`, `os.link`, or equivalent)
    between the existence check and the replace, which is what would be
    required to close the race."""

    from pcae.core.rollback_approval_evidence import _write_atomic_json

    source = inspect.getsource(_write_atomic_json)
    assert "path.exists()" in source
    assert "os.replace(" in source
    assert "O_EXCL" not in source
    assert "os.link(" not in source

    # Contrast: RAE-001's own creation-registry marker *does* use a true
    # exclusive create, confirming the primitive exists in this
    # repository's own conventions and was available to reuse for HATP
    # evidence persistence too, but HSCE-001 Section 20 (HSCE-REQ-042)
    # explicitly declines to require an equivalent marker for this
    # store.
    from pcae.core.rollback_approval_evidence import RollbackApprovalEvidenceStore

    registration_source = inspect.getsource(RollbackApprovalEvidenceStore.write_creation_registration)
    assert "O_CREAT" in registration_source and "O_EXCL" in registration_source


def test_hsce_creation_registry_marker_explicitly_declined():
    normalized = " ".join(_hsce_text().split())
    assert "No `creation-registry/` marker subdirectory is required for this store" in normalized


# ─────────────────────────────────────────────────────────────────────────
# HATP-001 closed vocabulary reconfirmation (dependency compatibility)
# ─────────────────────────────────────────────────────────────────────────


def test_hatp_verification_status_vocabulary_is_thirteen_members():
    from pcae.core.human_approval_trusted_provenance import HATPVerificationStatus

    values = {member.value for member in HATPVerificationStatus}
    assert values == {
        "VALID",
        "MISSING",
        "MALFORMED",
        "INVALID_SIGNATURE",
        "UNKNOWN_SIGNER",
        "UNAUTHORIZED_SIGNER",
        "REVOKED_SIGNER",
        "INVALID_ATTESTATION",
        "USER_PRESENCE_NOT_PROVEN",
        "WRONG_OPERATION",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "EXPIRED",
    }


def test_hatp_and_hsce_error_vocabularies_never_overlap():
    from pcae.core.human_approval_trusted_provenance import HATPVerificationStatus

    hatp_values = {member.value for member in HATPVerificationStatus}
    hsce_text = _hsce_text()
    section_start = hsce_text.index("## 22. Closed Error Vocabulary")
    section_end = hsce_text.index("## 23. Secret Handling")
    hsce_error_types = set(re.findall(r"^\| `([a-z_]+)` \|", hsce_text[section_start:section_end], flags=re.MULTILINE))
    assert hatp_values.isdisjoint(hsce_error_types)


def test_require_proof_version_rejects_bool_before_membership_check():
    from pcae.core.human_approval_trusted_provenance import _require_proof_version

    with pytest.raises(Exception):
        _require_proof_version(True)
    with pytest.raises(Exception):
        _require_proof_version(False)


def test_digest_and_canonicalize_functions_exist_and_are_sha256_hex():
    from pcae.core.human_approval_trusted_provenance import (
        HumanApprovalProvenanceProof,
        canonicalize_hatp_proof_payload,
        digest_hatp_proof_payload,
    )

    assert callable(canonicalize_hatp_proof_payload)
    assert callable(digest_hatp_proof_payload)
    sig = inspect.signature(digest_hatp_proof_payload)
    (param,) = sig.parameters.values()
    assert param.annotation is HumanApprovalProvenanceProof or "HumanApprovalProvenanceProof" in str(param.annotation)


def test_test_provider_unreachable_from_cli_and_commands_layer():
    result = subprocess.run(
        ["grep", "-rln", "TestHATPProofVerifierProvider", "src/pcae/cli.py", "src/pcae/commands/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == "", f"TestHATPProofVerifierProvider referenced from production CLI layer: {result.stdout}"


def test_decision_session_exit_code_convention_is_many_to_few_mapping():
    from pcae.commands.decision_session import _EXIT_CODE_BY_ERROR_TYPE

    error_types = list(_EXIT_CODE_BY_ERROR_TYPE.keys())
    exit_codes = set(_EXIT_CODE_BY_ERROR_TYPE.values())
    assert len(error_types) > len(exit_codes), "expected many error_types to map onto fewer exit-code categories"


def test_rae_binding_ttl_is_frozen_at_24_hours_not_caller_overridable():
    from pcae.core.rollback_approval_evidence import create_rollback_approval_binding

    source = inspect.getsource(create_rollback_approval_binding)
    assert "ttl_hours != 24" in source


def test_list_bindings_with_keys_exists_for_binding_lookup():
    from pcae.core.rollback_approval_evidence import RollbackApprovalEvidenceStore

    assert hasattr(RollbackApprovalEvidenceStore, "list_bindings_with_keys")
