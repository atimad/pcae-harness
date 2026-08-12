"""Phase 149O.20D.1 -- HMIC v1.2 HBDC Content-Identity Binding Contract
Repair (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§52; phase document
`docs/PHASE_149O_20D_1_HMIC_V1_2_HBDC_CONTENT_IDENTITY_BINDING_REPAIR.md`).

This is a CONTRACT-REPAIR-ONLY phase: it modifies no `src/pcae/**` file,
no `scripts/**` file, and no existing bound contract other than
`HMIC-001` itself (HBDC-001 and the other seven pre-existing frozen
corpus members remain byte-unchanged).

Finding **B-149O.20D-1**: Phase 149O.20D bound `HBDC-001` into
`contract_versions` (HMIC-REQ-067, v1.2) but left its document bytes
outside `implementation_scope_digest` (HMIC-REQ-050's twenty-four-file
enumeration), disclosing at HMIC-REQ-145 that a same-version,
content-only edit to `HBDC-001` would leave certification identity
unchanged. This repair closes that gap by adding HBDC-001's document as
the twenty-fifth entry to HMIC-REQ-050, giving `HBDC-001` the identical
dual binding (`contract_versions` + `implementation_scope_digest`) the
other four bound contracts already had -- the same mechanism HMIC-REQ-
145's own pre-repair text already named as the available closing
option, not a novel one.

This module independently verifies, by direct document inspection
(never trusting this phase's own prose or a prior phase's summary):

  * the pre-repair defect, reproduced from the frozen 149O.20D git
    snapshot (commit `5671448a`), not merely asserted -- HMIC-REQ-050
    named 24 files, excluded HBDC-001, and HMIC-REQ-145 explicitly
    disclosed the same-version-drift gap;
  * the repaired, live contract text: HMIC-REQ-050 now names 25 files
    including HBDC-001's document; HMIC-REQ-145 now states the gap is
    CLOSED; the attack matrix carries a new row (#37) with an
    IMPLEMENTATION_MISMATCH expected result for same-version drift;
  * version-drift and Contract-ID-drift detection remain intact,
    unaffected by this repair;
  * the other four bound contracts' own dual-binding protections are
    unweakened -- their positions and content in HMIC-REQ-050 are
    byte-identical before and after this repair;
  * HMIC-001 remains v1.2 (in-place repair, not a version bump),
    consistent with the 149O.19.3R precedent for repairing a
    not-yet-independently-verified contract;
  * no artifact schema, canonical-serialization, or `CertificationStatus`
    vocabulary change was introduced;
  * HMIC-REQ-063/Option-C text is byte-unchanged, not solved by this
    repair;
  * HBDC-001 itself, and every other pre-existing bound contract, are
    byte-unchanged in the working tree;
  * no `src/pcae/**` or `scripts/**` file is modified;
  * production remains intentionally stale (`_FROZEN_AUTHORITY_BEARING_
    FILES` still 24, `_CONTRACT_IDENTITY_FILES` still 4 members) --
    disclosed, fail-closed, not a repair-phase oversight;
  * no real certification/binding/revocation artifact exists anywhere
    in the repository.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

#: This phase's (149O.20D.1's) own final commit -- used to pin
#: "production still disclosed-stale" claims to a fixed historical
#: window, since Phase 149O.20F later, legitimately aligns production
#: past this phase's own 24-file/four-member checkpoint.
_PHASE_149O_20D_1_EXIT_COMMIT = "7c632bdff07bef7b027839f17c8ba948631eb6fe"

#: The pre-repair 149O.20D commit -- the exact contract text finding
#: B-149O.20D-1 was found against, before this phase's own edits.
_PRE_REPAIR_COMMIT = "5671448a"

_EXISTING_EIGHT_BOUND_CONTRACTS = (
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

_HBDC_CONTRACT_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"

_ORIGINAL_FOUR_CONTRACT_VERSIONS_MEMBERS = ("HMRC-001", "HATP-001", "HSCE-001", "RAE-001")


def _extract_req_050_paths(text: str) -> "list[str]":
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = text.index(marker)
    fence_start = text.index("```", start)
    fence_end = text.index("```", fence_start + 3)
    block = text[fence_start + 3 : fence_end]
    return [ln.strip() for ln in block.splitlines() if ln.strip()]


def _extracted_bare_paths(text: str) -> "list[str]":
    return [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", ln).strip() for ln in _extract_req_050_paths(text)]


def _git_show(commit: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=15,
    )
    if proc.returncode != 0:
        pytest.skip(f"git unavailable or commit {commit} not reachable: {proc.stderr.strip()}")
    return proc.stdout


# ---------------------------------------------------------------------------
# Section 3: defect independently reproduced from the frozen pre-repair
# git snapshot (not erased, not merely asserted from this phase's own
# prose)
# ---------------------------------------------------------------------------


def _pre_repair_contract_text() -> str:
    return _git_show(_PRE_REPAIR_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")


def test_premise_a_hbdc_was_a_contract_versions_member_pre_repair():
    text = _pre_repair_contract_text()
    section_start = text.index("**HMIC-REQ-067")
    section_end = text.index("**HMIC-REQ-068")
    body = " ".join(text[section_start:section_end].split())
    assert "`HBDC-001`" in body
    assert "Five entries, no more, no fewer, under v1.2" in body


def test_premise_b_pre_repair_binding_was_version_header_only():
    text = _pre_repair_contract_text()
    section_start = text.index("**HMIC-REQ-145")
    body = " ".join(text[section_start : section_start + 2000].split())
    assert "version-header comparison only" in body
    assert "do **not** additionally participate in" in body or "do not additionally participate in" in body


def test_premise_c_hbdc_absent_from_pre_repair_24_file_digest_set():
    text = _pre_repair_contract_text()
    bare = set(_extracted_bare_paths(text))
    assert len(bare) == 24
    assert "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" not in bare


def test_premise_c_cross_checked_against_live_production_pre_repair_state():
    """The 24-file production constant was never touched by this repair
    (it remains disclosed-stale) -- confirms premise C independently
    against production source, not merely contract prose.

    Pinned to this phase's own exit commit, not live source: Phase
    149O.20F later, legitimately aligns production (149O.20D.1's own
    repair, production-aligned by that later phase); this claim is about
    THIS phase's own (149O.20D.1's) conclusion, preserved unweakened."""
    source = subprocess.run(
        ["git", "show", f"{_PHASE_149O_20D_1_EXIT_COMMIT}:src/pcae/core/hatp_mandatory_certification.py"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24" in source
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT" not in source


def test_premise_d_modeled_same_version_mutation_was_invisible_pre_repair():
    """Models the exact attack the governing phase instruction requires
    reproduced: given pre-repair HMIC-REQ-067/069/050 semantics, a
    hypothetical HBDC-001 byte mutation A->B with Contract ID and
    Version string both held constant changes neither `contract_
    versions`' stored value (version string unchanged) nor
    `implementation_scope_digest` (HBDC-001 not in the 24-file set) --
    so a certification bound to bytes A would continue to validate
    against bytes B under the pre-repair contract."""
    text = _pre_repair_contract_text()
    bare = set(_extracted_bare_paths(text))
    hbdc_in_digest_set = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in bare
    # contract_versions binding is declared-version-string-only (HMIC-REQ-069);
    # byte content is not one of its comparison inputs, so a content-only
    # mutation leaving the version string unchanged is invisible to it.
    version_string_unchanged_by_content_edit = True
    assert not hbdc_in_digest_set and version_string_unchanged_by_content_edit, (
        "pre-repair: a same-version HBDC-001 content mutation was invisible "
        "to both binding mechanisms -- defect independently reproduced"
    )


def test_defect_status_pre_repair_was_not_yet_closed():
    text = _pre_repair_contract_text()
    section_start = text.index("**HMIC-REQ-145")
    body = " ".join(text[section_start : section_start + 2500].split())
    assert "named, explicit, disclosed residual limitation" in body
    assert "SHALL NOT be represented" in body


# ---------------------------------------------------------------------------
# Section 53: repaired semantics -- live contract now closes the gap
# ---------------------------------------------------------------------------


def test_hmic_req_050_now_names_exactly_25_files_including_hbdc():
    bare = set(_extracted_bare_paths(_CONTRACT_TEXT))
    assert len(bare) == 25
    assert "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in bare


def test_hmic_req_145_now_states_closed_not_disclosed_limitation():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-145")
    body = " ".join(_CONTRACT_TEXT[section_start : section_start + 3500].split())
    assert "Status: CLOSED" in body
    assert "B-149O.20D-1 is repaired at the contract level" in body
    assert "does not depend on repository actors honestly bumping" in body


def test_attack_37_present_expects_implementation_mismatch_for_same_version_drift():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_37 = next(line for line in table.splitlines() if line.startswith("| 37 "))
    assert "same-version content drift" in row_37.lower()
    assert "IMPLEMENTATION_MISMATCH" in row_37
    assert "B-149O.20D-1" in row_37


def test_attack_35_no_longer_claims_same_version_exception():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_35 = next(line for line in table.splitlines() if line.startswith("| 35 "))
    assert "no longer" in row_35.lower()
    assert "see attack #37" in row_35


def test_hmic_req_053_now_covers_five_contracts_uniformly():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-053")
    section_end = _CONTRACT_TEXT.index("## 18. Implementation Identity")
    body = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "five contract files" in body
    assert "every `contract_versions` member" in body
    assert "no `contract_versions` member is exempted" in body


def test_civc_5_states_uniform_dual_binding_post_repair():
    section_start = _CONTRACT_TEXT.index("**CIVC-5.**")
    section_end = _CONTRACT_TEXT.index("**CIVC-6.**")
    body = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "all five" in body
    assert "uniformly" in body


# ---------------------------------------------------------------------------
# Version-drift and Contract-ID-drift detection remain intact
# ---------------------------------------------------------------------------


def test_version_drift_still_caught_by_contract_versions():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-069")
    section_end = _CONTRACT_TEXT.index("**HMIC-REQ-070")
    body = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "CONTRACT_MISMATCH" in body
    assert "five entries as of v1.2" in body


def test_contract_id_drift_still_caught_via_malformed_missing_key():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_36 = next(line for line in table.splitlines() if line.startswith("| 36 "))
    assert "MALFORMED" in row_36


def test_both_mechanisms_still_required_not_either_sufficient():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-053")
    section_end = _CONTRACT_TEXT.index("## 18. Implementation Identity")
    body = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "No future implementation SHALL treat either mechanism as" in body
    assert "sufficient without the other" in body


# ---------------------------------------------------------------------------
# Other four bound contracts -- protections unweakened, byte-identical
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("member_doc", (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
))
def test_other_four_bound_contract_docs_still_in_frozen_set(member_doc):
    bare = set(_extracted_bare_paths(_CONTRACT_TEXT))
    assert member_doc in bare


def test_other_four_bound_contracts_frozen_set_membership_unchanged_by_repair():
    pre = set(_extracted_bare_paths(_pre_repair_contract_text()))
    post = set(_extracted_bare_paths(_CONTRACT_TEXT))
    for member_doc in (
        "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
        "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
        "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    ):
        assert member_doc in pre and member_doc in post
    only_new = post - pre
    assert only_new == {"docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"}, (
        f"repair changed more than the single expected new entry: {only_new}"
    )


# ---------------------------------------------------------------------------
# Contract version stays v1.2 (in-place repair, precedent-consistent)
# ---------------------------------------------------------------------------


def test_contract_version_remains_1_2_not_bumped():
    assert "**Version:** 1.2" in _CONTRACT_TEXT


def test_status_line_now_names_the_repair():
    idx = _CONTRACT_TEXT.index("**Status:**")
    line = _CONTRACT_TEXT[idx : _CONTRACT_TEXT.index("\n", idx)]
    assert "CONTENT-IDENTITY BINDING REPAIRED" in line
    assert "PENDING INDEPENDENT VERIFICATION" in line
    assert "not VERIFIED at v1.2" in line


def test_repaired_by_line_names_this_phase():
    assert "**Repaired by:** Phase 149O.20D.1" in _CONTRACT_TEXT
    idx = _CONTRACT_TEXT.index("**Repaired by:** Phase 149O.20D.1")
    line = _CONTRACT_TEXT[idx : _CONTRACT_TEXT.index("\n", idx)]
    assert "B-149O.20D-1" in line


def test_version_decision_rationale_present_mirrors_149o_19_3r_precedent():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "HMIC-001 remains v1.2" in body
    assert "149O.19.3" in body
    assert "has never been independently verified" in body


# ---------------------------------------------------------------------------
# No artifact schema / canonical-serialization / status-vocabulary change
# ---------------------------------------------------------------------------


def test_no_schema_bump_claimed():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "remain **1**, untouched by this repair" in body
    assert "No new field was added" in body


def test_no_new_certification_status_value_claimed():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "no new status value was introduced" in body


def test_canonical_serialization_rules_not_reopened():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "no map-order ambiguity exists" in body


# ---------------------------------------------------------------------------
# HMIC-REQ-063 / Option C byte-unchanged; not solved by this repair
# ---------------------------------------------------------------------------


def test_hmic_req_063_text_byte_unchanged_by_repair():
    marker = "**HMIC-REQ-063 (Import-Shadowing"
    assert marker in _CONTRACT_TEXT
    idx = _CONTRACT_TEXT.index(marker)
    end = _CONTRACT_TEXT.index("**HMIC-REQ-064", idx)
    live = _CONTRACT_TEXT[idx:end]
    pre = _pre_repair_contract_text()
    pre_idx = pre.index(marker)
    pre_end = pre.index("**HMIC-REQ-064", pre_idx)
    assert live == pre[pre_idx:pre_end], "HMIC-REQ-063's own text must be byte-unchanged by this repair"


def test_hmic_req_063_not_falsely_solved():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "HMIC-REQ-063 remains unaffected, not solved" in body


def test_option_c_still_conditional_not_unconditional():
    text = " ".join(_CONTRACT_TEXT.split())
    assert "does not convert it into an unconditional acceptance" in text
    assert "Model A remains the" in text


# ---------------------------------------------------------------------------
# HBDC-001 itself, and every other pre-existing bound contract, unchanged
# in the working tree
# ---------------------------------------------------------------------------


def test_hbdc_contract_still_declares_v1_0_byte_unchanged():
    hbdc_text = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.0" in hbdc_text
    assert "**Contract:** HBDC-001" in hbdc_text


@pytest.mark.parametrize("existing_contract", _EXISTING_EIGHT_BOUND_CONTRACTS)
def test_only_hmic_contract_dirty_others_clean_in_working_tree(existing_contract):
    if existing_contract.endswith("HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"):
        pytest.skip("this is the one contract this phase intentionally repairs")
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", existing_contract],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"unexpected modification to {existing_contract}: {proc.stdout}"


def test_hbdc_contract_itself_clean_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", _HBDC_CONTRACT_RELATIVE],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"unexpected modification to HBDC-001: {proc.stdout}"


# ---------------------------------------------------------------------------
# No production source touched; no scripts touched
# ---------------------------------------------------------------------------


def test_no_src_pcae_files_dirty_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "src/pcae"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"production source dirty during a contract-repair-only phase: {proc.stdout}"


def test_no_scripts_files_dirty_in_working_tree():
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", "scripts"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    assert proc.stdout.strip() == "", f"scripts/ dirty during a contract-repair-only phase: {proc.stdout}"


# ---------------------------------------------------------------------------
# Production remains intentionally stale (24 files, 4-member set) --
# disclosed, fail-closed, not this phase's own oversight
# ---------------------------------------------------------------------------


def test_production_frozen_file_count_still_24_not_updated_by_this_phase():
    # Pinned to this phase's own exit commit, not live source: Phase
    # 149O.20F later, legitimately widens this same assert to 25
    # (production-aligning this phase's own repair); this claim is about
    # THIS phase's own conclusion, preserved unweakened.
    source = subprocess.run(
        ["git", "show", f"{_PHASE_149O_20D_1_EXIT_COMMIT}:src/pcae/core/hatp_mandatory_certification.py"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 24" in source
    assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT" not in source


def test_production_contract_versions_required_keys_still_four():
    # Pinned to this phase's own exit commit, not live source, for the
    # same reason as the test above.
    source = subprocess.run(
        ["git", "show", f"{_PHASE_149O_20D_1_EXIT_COMMIT}:src/pcae/core/hatp_mandatory_certification.py"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    match = re.search(r"_CONTRACT_IDENTITY_FILES:.*?=\s*\(\s*(.*?)\n\)", source, re.DOTALL)
    assert match, "could not locate _CONTRACT_IDENTITY_FILES in hatp_mandatory_certification.py"
    body = match.group(1)
    ids = re.findall(r'\("([A-Z0-9-]+)",', body)
    assert ids == list(_ORIGINAL_FOUR_CONTRACT_VERSIONS_MEMBERS), (
        f"production contract_versions membership changed during a contract-repair-only phase: {ids}"
    )
    assert "HBDC-001" not in body


def test_no_certification_storage_files_exist_so_validator_fails_closed():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == [], f"unexpected real certification storage file present: {hits}"


def test_wave_f_validator_call_present_and_unmodified_by_this_phase():
    source = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    assert "validate_active_hatp_mandatory_independent_verification_certification(" in source
    assert "certification_status_satisfies_readiness(" in source


# ---------------------------------------------------------------------------
# HBDC-BINDING-GATE status, W-1 / B-149O.19.3-1 not reopened, recommended
# next phase
# ---------------------------------------------------------------------------


def test_hbdc_binding_gate_status_updated_to_repair_complete():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "HBDC-BINDING-GATE: CONTRACT CONTENT-BINDING REPAIR COMPLETE" in body
    assert "INDEPENDENT VERIFICATION PENDING" in body
    assert "PRODUCTION ALIGNMENT PENDING" in body


def test_b_149o_20d_1_finding_status_repaired_not_closed():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "B-149O.20D-1: REPAIRED AT CONTRACT LEVEL" in body
    assert "INDEPENDENT VERIFICATION PENDING" in body
    assert "NOT CLOSED" in body


def test_w1_and_b149o1931_not_reopened_by_this_phase():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    body = " ".join(section.split())
    assert "`W-1` and `B-149O.19.3-1` remain" in body
    assert "independently closed/repaired" in body
    assert "unchanged by this phase" in body


def test_recommended_next_phase_still_149o_20e_not_provisioning():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 52. Contract Repair History") :]
    assert "149O.20E" in section
    assert "not** Class-B provisioning" in section or "provisioning planning" in section


def test_history_section_52_present_and_after_section_51():
    idx_51 = _CONTRACT_TEXT.index("## 51. Contract Amendment History")
    idx_52 = _CONTRACT_TEXT.index("## 52. Contract Repair History")
    assert idx_52 > idx_51


# ---------------------------------------------------------------------------
# No real certification state anywhere in the repository
# ---------------------------------------------------------------------------


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == []


def test_requirement_ids_still_exactly_001_to_145_no_gaps_no_duplicates():
    ids = sorted(int(m) for m in re.findall(r"\*\*HMIC-REQ-(\d{3})", _CONTRACT_TEXT))
    assert ids == list(range(1, 146)), "no new requirement ID should have been minted by this repair"


def test_civc_invariants_still_exactly_1_to_12():
    ids = sorted(int(m) for m in re.findall(r"- \*\*CIVC-(\d+)\.\*\*", _CONTRACT_TEXT))
    assert ids == list(range(1, 13))
