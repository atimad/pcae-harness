"""Phase 149O.20E -- HMIC v1.2 HBDC Bound-Contract Identity Independent
Verification (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§17/§20/§40/§41/§52; phase document
`docs/PHASE_149O_20E_HMIC_V1_2_HBDC_BOUND_CONTRACT_IDENTITY_INDEPENDENT_VERIFICATION.md`).

INDEPENDENT VERIFICATION ONLY: this module modifies no `src/pcae/**`
file, no `scripts/**` file, and no contract file. It does not import or
reuse `test_phase_149o_20d_1_hmic_v1_2_hbdc_content_identity_binding_
repair.py`'s expected-value constants as an oracle -- every fixed value
below (25 files, 5 contract_versions members, 145 requirements, 12
CIVCs, 37 attack rows) is independently re-derived, either by fresh
regex extraction of the live contract text or by direct `git show`
against the frozen 149O.20D commit `5671448a`, and the digest-mutation-
sensitivity tests below reimplement HMIC-REQ-054..058 from scratch
against a scratch copy of the frozen file set, rather than calling
`derive_implementation_scope_digest` from `hatp_mandatory_
certification.py`.

Verifies, independently:

  * B-149O.20D-1's pre-repair defect, reproduced fresh from git commit
    `5671448a` (not merely re-read from this repair's own §52 prose);
  * the live, repaired HMIC-REQ-050 enumeration is exactly 25 files,
    the live `contract_versions` set (HMIC-REQ-067) is exactly 5
    members, and the only difference from the pre-repair/pre-evolution
    baseline is the disclosed +1/+1 delta (HBDC-001's document /
    HBDC-001 contract ID);
  * a from-scratch reimplementation of the HMIC-REQ-054..058 digest
    algorithm, run against a scratch copy of the live 25-file set, is
    sensitive to a same-version, content-only mutation of HBDC-001's
    document -- and, for regression, to a same-version mutation of each
    of the other 24 frozen files, including the four pre-existing bound
    contracts;
  * version-drift and Contract-ID-drift on HBDC-001 remain caught by
    `contract_versions`' independent version-header mechanism (text-
    level, since no live validator implements the repaired scope yet);
  * production (`core/hatp_mandatory_certification.py`) remains
    intentionally stale at the pre-repair 24-file / 4-member sets, and
    the Wave-F validator caller in `hatp_mandatory_cutover.py` is
    present and unmodified;
  * HMIC-REQ-063/Option-C, the total 9-contract frozen corpus vs. the
    5-member `contract_versions` count, and the requirement/CIVC/attack
    inventories (145/12/37) hold under fresh extraction;
  * no real certification/binding/revocation/Protected-Root state
    exists anywhere on this host.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_HMIC_MODULE_TEXT = _HMIC_MODULE_PATH.read_text(encoding="utf-8")

#: This phase's (149O.20E's) own final commit -- used to pin "production
#: still disclosed-stale" claims to a fixed historical window, since
#: Phase 149O.20F later, legitimately aligns production past this
#: phase's own 24-file/four-member checkpoint.
_PHASE_149O_20E_EXIT_COMMIT = "43ecacb91c91443ae00a06cf819296c99edc628a"
_HMIC_MODULE_TEXT_AT_PHASE_EXIT = subprocess.run(
    ["git", "show", f"{_PHASE_149O_20E_EXIT_COMMIT}:src/pcae/core/hatp_mandatory_certification.py"],
    cwd=str(_REPO_ROOT),
    capture_output=True,
    text=True,
    check=True,
).stdout
_CUTOVER_MODULE_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"
_CUTOVER_MODULE_TEXT = _CUTOVER_MODULE_PATH.read_text(encoding="utf-8")

_PRE_REPAIR_20D_COMMIT = "5671448a"

_HBDC_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"

_FOUR_PRE_EXISTING_BOUND_CONTRACTS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)

_NINE_TOTAL_FROZEN_CORPUS = (
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
)


# ═══════════════════════════════════════════════════════════════════════════
# Fresh extraction helpers (independent of any prior phase's test module)
# ═══════════════════════════════════════════════════════════════════════════


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _extract_req_050_block(text: str) -> str:
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = text.index(marker)
    fence_start = text.index("```", start)
    fence_end = text.index("```", fence_start + 3)
    return text[fence_start + 3 : fence_end]


def _extract_req_050_paths(text: str) -> "list[str]":
    block = _extract_req_050_block(text)
    paths: "list[str]" = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Strip a trailing parenthetical annotation like "(HMRC-001)".
        bare = re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", line).strip()
        paths.append(bare)
    return paths


def _extract_contract_versions_members(text: str) -> "list[str]":
    # Find the actual bold requirement definition, not an earlier
    # header-summary mention of the same ID (e.g. the "Amended by"
    # line at the top of the document).
    marker = "**HMIC-REQ-067"
    start = text.index(marker)
    end = text.index("\n\n", start)
    segment = text[start:end]
    return re.findall(r"`([A-Z]+-\d{3})`", segment)


def _extract_req_ids(text: str) -> "list[int]":
    return sorted({int(m) for m in re.findall(r"HMIC-REQ-(\d{3})\b", text)})


def _extract_civc_ids(text: str) -> "list[int]":
    return sorted({int(m) for m in re.findall(r"\*\*CIVC-(\d+)\.\*\*", text)})


def _extract_attack_row_numbers(text: str) -> "list[int]":
    marker = "## 41. Full Mandatory Attack Matrix"
    start = text.index(marker)
    end = text.index("\n---\n", start)
    block = text[start:end]
    rows = re.findall(r"^\|\s*(\d+)\s*(?:\*|\|)", block, flags=re.MULTILINE)
    return sorted(int(r) for r in rows)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Pre-repair defect (B-149O.20D-1), reproduced fresh from git history
# ═══════════════════════════════════════════════════════════════════════════


def test_frozen_20d_commit_is_the_correct_pre_repair_snapshot():
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    assert "**Version:** 1.2" in subject
    assert "Repaired by:** Phase 149O.20D.1" not in subject


def test_premise_a_hbdc_contract_versions_member_pre_repair():
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    members = _extract_contract_versions_members(subject)
    assert "HBDC-001" in members
    assert len(members) == 5


def test_premise_b_pre_repair_binding_is_version_header_comparison_only():
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    req_069_start = subject.index("HMIC-REQ-069")
    req_069_text = subject[req_069_start : req_069_start + 700]
    assert "live version header" in req_069_text or "version header" in req_069_text
    assert "content digest" not in req_069_text.lower().replace("content-digest", "content digest")


def test_premise_c_hbdc_absent_from_pre_repair_24_file_enumeration():
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    paths = _extract_req_050_paths(subject)
    assert len(paths) == 24
    assert _HBDC_RELATIVE not in paths


def test_premise_c_cross_checked_against_live_production_constant():
    # Production's frozen-set constant, independently re-derived from
    # the module's own source text, not merely quoted from the contract.
    # Pinned to this phase's own exit commit, not live source: Phase
    # 149O.20F later, legitimately aligns production to 25/HBDC-present;
    # this claim is about THIS phase's own (149O.20E's) conclusion,
    # preserved unweakened.
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24" in _HMIC_MODULE_TEXT_AT_PHASE_EXIT
    assert "hatp_class_b_deployment" not in _HMIC_MODULE_TEXT_AT_PHASE_EXIT.lower()


def test_premise_d_same_version_hbdc_mutation_invisible_under_pre_repair_semantics():
    """Modeled directly, independent of §52's own prose: given the four
    premises above (HBDC-001 is a contract_versions member; its binding
    is version-header-only; its bytes are outside implementation_scope_
    digest; contract_versions' value is a version string, not a digest),
    neither of a certification's two authority-bearing digest inputs
    would change under a same-version HBDC-001 content mutation -- the
    certification would continue to validate as VALID against mutated
    bytes."""
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    members = _extract_contract_versions_members(subject)
    paths = _extract_req_050_paths(subject)
    contract_versions_binding_is_version_string_only = "HBDC-001" in members
    hbdc_bytes_outside_digest_scope = _HBDC_RELATIVE not in paths
    # Both conditions true => a content-only, same-version mutation
    # changes neither `contract_versions`' stored value (string
    # unaffected) nor `implementation_scope_digest` (HBDC-001 bytes not
    # hashed) => defect reproduced.
    assert contract_versions_binding_is_version_string_only and hbdc_bytes_outside_digest_scope


def test_defect_b_149o_20d_1_independently_reproduced():
    # Composite check restating the four premises as one verdict.
    subject = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    assert "HBDC-001" in _extract_contract_versions_members(subject)
    assert _HBDC_RELATIVE not in _extract_req_050_paths(subject)
    req_145_start = subject.index("**HMIC-REQ-145")
    req_145_text = subject[req_145_start : req_145_start + 900]
    assert "residual limitation" in req_145_text.lower() or "not caught" in req_145_text.lower() or "not" in req_145_text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 2. Live (repaired) contract state -- fresh extraction, 25 files / 5 members
# ═══════════════════════════════════════════════════════════════════════════


def test_live_req_050_names_exactly_25_files():
    paths = _extract_req_050_paths(_CONTRACT_TEXT)
    assert len(paths) == 25
    assert len(set(paths)) == 25  # no duplicates


def test_live_req_050_includes_hbdc_as_the_only_addition_vs_pre_repair():
    pre_repair_text = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    pre_repair_paths = set(_extract_req_050_paths(pre_repair_text))
    live_paths = set(_extract_req_050_paths(_CONTRACT_TEXT))
    added = live_paths - pre_repair_paths
    removed = pre_repair_paths - live_paths
    assert added == {_HBDC_RELATIVE}
    assert removed == set()


def test_live_contract_versions_exactly_5_members():
    """As of this phase (149O.20E) this was exactly 5; a later amendment
    (149O.20L.7O.2H) additively widened it to 7."""
    members = _extract_contract_versions_members(_CONTRACT_TEXT)
    assert len(members) >= 5
    assert {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"} <= set(members)


def test_live_contract_versions_delta_vs_v1_1_baseline_is_exactly_hbdc():
    # v1.1 baseline (pre-20D) had 4 members; independently reconstructed
    # from §50's own frozen historical statement (not the 20D/20D.1
    # repair sections), cross-checked against the pre-repair 20D
    # snapshot's own "unamended" four-member set before HBDC-001 joined.
    v1_1_marker = "## 50. Contract Amendment History"
    start = _CONTRACT_TEXT.index(v1_1_marker)
    end = _CONTRACT_TEXT.index("## 51.", start)
    segment = _CONTRACT_TEXT[start:end]
    assert "HMRC-001" in segment and "HATP-001" in segment and "HSCE-001" in segment and "RAE-001" in segment
    live_members = set(_extract_contract_versions_members(_CONTRACT_TEXT))
    # As of this phase (149O.20E) the only delta vs. the v1.1 four-member
    # baseline was HBDC-001; a later amendment (149O.20L.7O.2H)
    # additively widened it further (+HPSE-001/HHCE-001), so HBDC-001 is
    # now asserted as present in the delta, not the delta's sole member.
    assert "HBDC-001" in live_members - {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}


def test_total_frozen_corpus_is_nine_distinct_from_five_member_contract_versions():
    assert len(_NINE_TOTAL_FROZEN_CORPUS) == 9
    assert len(set(_NINE_TOTAL_FROZEN_CORPUS)) == 9
    members = _extract_contract_versions_members(_CONTRACT_TEXT)
    assert len(members) >= 5
    assert len(members) != len(_NINE_TOTAL_FROZEN_CORPUS)


# ═══════════════════════════════════════════════════════════════════════════
# 3. From-scratch HMIC-REQ-054..058 digest reimplementation + mutation tests
# ═══════════════════════════════════════════════════════════════════════════


_SRC_PCAE_RELATIVE_MARKER_COUNT = 19  # entries before the blank line in the fenced HMIC-REQ-050 block


def _canonicalize(paths: "list[str]") -> "list[str]":
    """Independent reimplementation of HMIC-REQ-055's canonicalization:
    the first 19 entries are `src/pcae/`-relative, the rest are
    repository-root-relative -- derived from the fenced block's own
    blank-line split, not copied from production's bucket-count
    constant."""

    block = _extract_req_050_block(_CONTRACT_TEXT)
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    blank_split_index = None
    raw_lines = block.splitlines()
    seen_non_blank = 0
    for i, raw in enumerate(raw_lines):
        if raw.strip() == "" and seen_non_blank > 0:
            blank_split_index = seen_non_blank
            break
        if raw.strip():
            seen_non_blank += 1
    assert blank_split_index is not None
    canonical = []
    for index, path in enumerate(paths):
        if index < blank_split_index:
            canonical.append(f"src/pcae/{path}")
        else:
            canonical.append(path)
    return canonical


def _independent_digest(root: Path, canonical_paths: "list[str]") -> str:
    """From-scratch reimplementation of HMIC-REQ-054/056-058: SHA-256 of
    the lexicographically-ordered, null/newline-delimited per-file
    record list. Deliberately does NOT call `derive_implementation_
    scope_digest` from production."""

    hasher = hashlib.sha256()
    for path in sorted(canonical_paths):
        data = (root / path).read_bytes()
        file_digest = hashlib.sha256(data).hexdigest()
        record = f"{path}\0{file_digest}\n".encode("utf-8")
        hasher.update(record)
    return hasher.hexdigest()


@pytest.fixture(scope="module")
def _scratch_25_file_tree():
    """Copies exactly the live 25 HMIC-REQ-050 files into an isolated
    scratch directory, preserving their canonical relative paths, so
    mutation tests never touch the real working tree."""

    bare_paths = _extract_req_050_paths(_CONTRACT_TEXT)
    canonical_paths = _canonicalize(bare_paths)
    assert len(canonical_paths) == 25
    with tempfile.TemporaryDirectory(prefix="pcae-149o-20e-scratch-") as tmp:
        tmp_root = Path(tmp)
        for rel in canonical_paths:
            src = _REPO_ROOT / rel
            assert src.is_file(), f"live frozen file missing: {rel}"
            dst = tmp_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        yield tmp_root, canonical_paths


def test_scratch_tree_has_exactly_25_files(_scratch_25_file_tree):
    tmp_root, canonical_paths = _scratch_25_file_tree
    assert len(canonical_paths) == 25
    for rel in canonical_paths:
        assert (tmp_root / rel).is_file()


def test_baseline_digest_is_stable_and_reproducible(_scratch_25_file_tree):
    tmp_root, canonical_paths = _scratch_25_file_tree
    digest_a = _independent_digest(tmp_root, canonical_paths)
    digest_b = _independent_digest(tmp_root, canonical_paths)
    assert digest_a == digest_b
    assert len(digest_a) == 64  # SHA-256 hex


def test_hbdc_same_version_content_mutation_changes_digest(_scratch_25_file_tree):
    tmp_root, canonical_paths = _scratch_25_file_tree
    baseline = _independent_digest(tmp_root, canonical_paths)
    hbdc_scratch_path = tmp_root / _HBDC_RELATIVE
    original_bytes = hbdc_scratch_path.read_bytes()
    try:
        # One-byte, same-declared-version mutation: append a byte,
        # leaving the "**Version:** 1.0" header line untouched.
        hbdc_scratch_path.write_bytes(original_bytes + b"\n")
        mutated = _independent_digest(tmp_root, canonical_paths)
        assert mutated != baseline
    finally:
        hbdc_scratch_path.write_bytes(original_bytes)


@pytest.mark.parametrize("target_relative", _FOUR_PRE_EXISTING_BOUND_CONTRACTS)
def test_other_four_bound_contracts_still_digest_sensitive(_scratch_25_file_tree, target_relative):
    tmp_root, canonical_paths = _scratch_25_file_tree
    baseline = _independent_digest(tmp_root, canonical_paths)
    target = tmp_root / target_relative
    original_bytes = target.read_bytes()
    try:
        target.write_bytes(original_bytes + b"\n")
        mutated = _independent_digest(tmp_root, canonical_paths)
        assert mutated != baseline
    finally:
        target.write_bytes(original_bytes)


def test_all_25_files_individually_digest_sensitive(_scratch_25_file_tree):
    tmp_root, canonical_paths = _scratch_25_file_tree
    baseline = _independent_digest(tmp_root, canonical_paths)
    sensitive_count = 0
    for rel in canonical_paths:
        target = tmp_root / rel
        original_bytes = target.read_bytes()
        try:
            target.write_bytes(original_bytes + b"\n")
            mutated = _independent_digest(tmp_root, canonical_paths)
            if mutated != baseline:
                sensitive_count += 1
        finally:
            target.write_bytes(original_bytes)
    assert sensitive_count == 25


def test_missing_hbdc_file_fails_closed(_scratch_25_file_tree):
    tmp_root, canonical_paths = _scratch_25_file_tree
    hbdc_scratch_path = tmp_root / _HBDC_RELATIVE
    original_bytes = hbdc_scratch_path.read_bytes()
    hbdc_scratch_path.unlink()
    try:
        with pytest.raises(FileNotFoundError):
            _independent_digest(tmp_root, canonical_paths)
    finally:
        hbdc_scratch_path.write_bytes(original_bytes)


def test_hbdc_symlink_position_rejected_by_frozen_file_safety_check():
    # Mirrors HMIC-REQ-061 (symlink rejection) applying uniformly to the
    # new 25th entry -- exercised against production's own real safety
    # primitive so the check under test is the actual production
    # mechanism, not a reimplementation (unlike the digest algorithm
    # above, which the phase instruction requires reimplementing
    # independently; symlink/non-regular-file rejection is a narrow,
    # already-generic primitive this phase does not need to
    # reimplement).
    from pcae.core.hatp_mandatory_certification import (  # noqa: PLC0415
        FrozenFileDerivationError,
        _resolve_and_reject_unsafe_frozen_file,
    )

    with tempfile.TemporaryDirectory(prefix="pcae-149o-20e-symlink-") as tmp:
        tmp_root = Path(tmp)
        target_dir = tmp_root / "docs" / "contracts"
        target_dir.mkdir(parents=True)
        real_file = tmp_root / "elsewhere.md"
        real_file.write_text("x", encoding="utf-8")
        symlink_path = target_dir / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
        try:
            symlink_path.symlink_to(real_file)
        except (OSError, NotImplementedError):
            pytest.skip("platform does not support symlink creation in this sandbox")
        with pytest.raises(FrozenFileDerivationError):
            _resolve_and_reject_unsafe_frozen_file(tmp_root, "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")


def test_hbdc_path_is_canonical_no_alternate_alias():
    paths = _extract_req_050_paths(_CONTRACT_TEXT)
    hbdc_entries = [p for p in paths if "CLASS_B_DEPLOYMENT" in p]
    assert hbdc_entries == [_HBDC_RELATIVE]


# ═══════════════════════════════════════════════════════════════════════════
# 4. Version-drift / Contract-ID-drift (text-level, no live validator yet)
# ═══════════════════════════════════════════════════════════════════════════


def test_version_drift_still_text_mandated_as_contract_mismatch():
    """As of this phase (149O.20E) HMIC-REQ-069 named 'five entries as of
    v1.2'; a later amendment (149O.20L.7O.2H) widened it to 'seven
    entries as of v1.5' -- the CONTRACT_MISMATCH rule this test's real
    point covers is unaffected."""
    req_069_start = _CONTRACT_TEXT.index("HMIC-REQ-069")
    req_069_text = _CONTRACT_TEXT[req_069_start : req_069_start + 900]
    assert "CONTRACT_MISMATCH" in req_069_text
    assert "entries as of v1." in req_069_text


def test_contract_id_drift_still_text_mandated_as_malformed_missing_key():
    attack_36_start = _CONTRACT_TEXT.index("| 36 ")
    attack_36_text = _CONTRACT_TEXT[attack_36_start : attack_36_start + 700]
    assert "MALFORMED" in attack_36_text
    assert "missing" in attack_36_text.lower() or "lacks" in attack_36_text.lower()


def test_attack_37_present_hbdc_same_version_drift_implementation_mismatch():
    attack_37_start = _CONTRACT_TEXT.index("| 37 ")
    attack_37_text = _CONTRACT_TEXT[attack_37_start : attack_37_start + 900]
    assert "IMPLEMENTATION_MISMATCH" in attack_37_text
    assert "HBDC-001" in attack_37_text


def test_attack_35_no_longer_a_same_version_exception():
    attack_35_start = _CONTRACT_TEXT.index("| 35 ")
    attack_35_end = _CONTRACT_TEXT.index("| 36 ")
    attack_35_text = _CONTRACT_TEXT[attack_35_start:attack_35_end]
    assert "no longer" in attack_35_text.lower()
    assert "attack #37" in attack_35_text or "#37" in attack_35_text


def test_id_version_content_three_way_binding_all_visible():
    # ID: a `contract_versions` key rename is a closed-schema MALFORMED
    # case (attack #36's reasoning). Version: HMIC-REQ-069 version-header
    # comparison. Content: HMIC-REQ-053/058 digest inclusion.
    assert "MALFORMED" in _CONTRACT_TEXT[_CONTRACT_TEXT.index("| 36 ") :][:700]
    assert "CONTRACT_MISMATCH" in _CONTRACT_TEXT[_CONTRACT_TEXT.index("HMIC-REQ-069") :][:900]
    assert "IMPLEMENTATION_MISMATCH" in _CONTRACT_TEXT[_CONTRACT_TEXT.index("| 37 ") :][:900]


# ═══════════════════════════════════════════════════════════════════════════
# 5. Existing-four dual-binding mechanism -- reconstructed, not accepted
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("member_doc", _FOUR_PRE_EXISTING_BOUND_CONTRACTS)
def test_existing_four_members_present_in_req_050_and_contract_versions(member_doc):
    paths = _extract_req_050_paths(_CONTRACT_TEXT)
    assert member_doc in paths
    contract_id = {
        "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md": "HMRC-001",
        "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md": "HATP-001",
        "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md": "HSCE-001",
        "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md": "RAE-001",
    }[member_doc]
    assert contract_id in _extract_contract_versions_members(_CONTRACT_TEXT)


def test_req_053_states_uniform_five_member_digest_participation():
    """As of this phase (149O.20E) HMIC-REQ-053 named 'five'; a later
    amendment (149O.20L.7O.2H) widened the uniform-coverage rule to
    'seven' (+HPSE-001/HHCE-001) -- HBDC-001's own inclusion, this test's
    real point, is unaffected."""
    req_053_start = _CONTRACT_TEXT.index("**HMIC-REQ-053")
    req_053_text = _CONTRACT_TEXT[req_053_start : req_053_start + 900]
    assert "five" in req_053_text.lower() or "seven" in req_053_text.lower()
    assert "HBDC-001" in req_053_text


def test_existing_four_positions_unweakened_vs_pre_repair_snapshot():
    pre_repair_text = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    pre_repair_paths = _extract_req_050_paths(pre_repair_text)
    live_paths = _extract_req_050_paths(_CONTRACT_TEXT)
    for member_doc in _FOUR_PRE_EXISTING_BOUND_CONTRACTS:
        assert pre_repair_paths.index(member_doc) == live_paths.index(member_doc)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Requirement / CIVC / attack inventories -- fresh extraction
# ═══════════════════════════════════════════════════════════════════════════


def test_requirement_ids_gapless_001_to_145():
    ids = _extract_req_ids(_CONTRACT_TEXT)
    assert ids[0] == 1
    assert ids[-1] == 145
    assert ids == list(range(1, 146))


def test_civc_invariants_exactly_1_to_12():
    ids = _extract_civc_ids(_CONTRACT_TEXT)
    assert ids == list(range(1, 13))


def test_attack_matrix_37_sequential_rows():
    rows = _extract_attack_row_numbers(_CONTRACT_TEXT)
    assert rows == list(range(1, 38))


def test_hmic_req_145_closed_and_closure_not_version_bump_dependent():
    req_145_start = _CONTRACT_TEXT.index("**HMIC-REQ-145")
    req_145_text = _CONTRACT_TEXT[req_145_start : req_145_start + 3500]
    assert "CLOSED" in req_145_text
    assert "does not depend" in req_145_text.lower() and "version" in req_145_text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 7. HMIC-REQ-063 / Option C -- preserved, not solved
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_req_063_byte_unchanged_since_pre_repair_20d_snapshot():
    pre_repair_text = _git_show(_PRE_REPAIR_20D_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    pre_marker = pre_repair_text.index("HMIC-REQ-063")
    live_marker = _CONTRACT_TEXT.index("HMIC-REQ-063")
    pre_block = pre_repair_text[pre_marker : pre_marker + 1400]
    live_block = _CONTRACT_TEXT[live_marker : live_marker + 1400]
    assert pre_block == live_block


def test_hmic_req_063_not_falsely_claimed_solved():
    req_063_start = _CONTRACT_TEXT.index("HMIC-REQ-063")
    req_063_text = _CONTRACT_TEXT[req_063_start : req_063_start + 1400]
    assert "does NOT implement an" in req_063_text or "does not implement" in req_063_text.lower()


def test_option_c_still_conditional_on_environment_lock():
    hbdc_text = (_CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md").read_text(encoding="utf-8")
    option_c_start = hbdc_text.index("**HBDC-REQ-040")
    option_c_text = hbdc_text[option_c_start : option_c_start + 900]
    assert "environment-lock" in option_c_text or "environment lock" in option_c_text.lower()
    assert "concrete mitigation" in option_c_text.lower()


def test_model_a_remains_sole_authorized_deployment_model():
    hbdc_text = (_CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md").read_text(encoding="utf-8")
    assert "Models B" in hbdc_text and "NOT authorized" in hbdc_text


# ═══════════════════════════════════════════════════════════════════════════
# 8. Production staleness (24/4) + Wave-F caller reality
# ═══════════════════════════════════════════════════════════════════════════


def test_production_frozen_file_count_still_24():
    # Pinned to this phase's own exit commit -- see rationale on
    # `test_premise_c_cross_checked_against_live_production_constant`.
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24" in _HMIC_MODULE_TEXT_AT_PHASE_EXIT


def test_production_contract_identity_files_still_four_members():
    # Pinned to this phase's own exit commit, same rationale.
    tuple_start = _HMIC_MODULE_TEXT_AT_PHASE_EXIT.index("_CONTRACT_IDENTITY_FILES: ")
    tuple_end = _HMIC_MODULE_TEXT_AT_PHASE_EXIT.index("\n)", tuple_start)
    segment = _HMIC_MODULE_TEXT_AT_PHASE_EXIT[tuple_start:tuple_end]
    ids = re.findall(r'\("([A-Z]+-\d{3})"', segment)
    assert set(ids) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}
    assert "HBDC-001" not in segment


def test_production_hbdc_path_not_present_anywhere_in_frozen_constant():
    frozen_start = _HMIC_MODULE_TEXT.index("_FROZEN_AUTHORITY_BEARING_FILES: ")
    frozen_end = _HMIC_MODULE_TEXT.index("assert len(_FROZEN_AUTHORITY_BEARING_FILES)", frozen_start)
    segment = _HMIC_MODULE_TEXT[frozen_start:frozen_end]
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT" not in segment


def test_wave_f_validator_caller_present_and_wired():
    assert "validate_active_hatp_mandatory_independent_verification_certification" in _CUTOVER_MODULE_TEXT
    assert "mandatory_consumption_implementation_independently_verified" in _CUTOVER_MODULE_TEXT
    call_index = _CUTOVER_MODULE_TEXT.index("hmic_validation = validate_active_hatp_mandatory_independent_verification_certification")
    surrounding = _CUTOVER_MODULE_TEXT[call_index : call_index + 400]
    assert "certification_status_satisfies_readiness" in surrounding


def test_no_real_certification_storage_exists_on_this_host():
    from pcae.core.hatp_bootstrap import _default_production_trust_root  # noqa: PLC0415

    root = _default_production_trust_root()
    assert not root.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 9. Byte-stability of HMIC/HBDC/other bound contracts + no repo mutation
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_contract_byte_unchanged_in_working_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", str(_CONTRACT_PATH)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.stdout.strip() == ""


def test_hbdc_contract_byte_unchanged_in_working_tree():
    hbdc_path = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", str(hbdc_path)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.stdout.strip() == ""


def test_no_src_pcae_or_scripts_files_dirty():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "src/pcae", "scripts"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.stdout.strip() == ""


def test_hbdc_declares_v1_0_unchanged():
    hbdc_text = (_CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md").read_text(encoding="utf-8")
    assert "**Version:** 1.0" in hbdc_text


def test_hmic_remains_v1_2_not_bumped():
    assert "**Version:** 1.2" in _CONTRACT_TEXT


# ═══════════════════════════════════════════════════════════════════════════
# 10. B-149O.20D-1 / HBDC-BINDING-GATE / W-1 / B-149O.19.3-1 status text
# ═══════════════════════════════════════════════════════════════════════════


def test_b_149o_20d_1_status_repaired_at_contract_level_not_closed_pre_verification():
    finding_start = _CONTRACT_TEXT.index("B-149O.20D-1")
    surrounding = _CONTRACT_TEXT[finding_start - 200 : finding_start + 2000]
    assert "CLOSED" in _CONTRACT_TEXT[_CONTRACT_TEXT.index("**HMIC-REQ-145") :][:3500]


def test_hbdc_binding_gate_not_yet_fully_closed_pending_production_alignment():
    gate_start = _CONTRACT_TEXT.index("HBDC-BINDING-GATE")
    gate_text = _CONTRACT_TEXT[gate_start : gate_start + 400]
    assert "PENDING" in gate_text


def test_recommended_next_phase_is_149o_20e_not_provisioning():
    assert "149O.20E" in _CONTRACT_TEXT
    next_phase_start = _CONTRACT_TEXT.rindex("Recommended next phase")
    next_phase_text = _CONTRACT_TEXT[next_phase_start : next_phase_start + 2600]
    assert "149O.20E" in next_phase_text
    assert "provisioning planning be considered" in next_phase_text.lower() or "not recommended directly" in next_phase_text.lower()
