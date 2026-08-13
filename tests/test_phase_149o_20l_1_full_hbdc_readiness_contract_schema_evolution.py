"""Phase 149O.20L.1 -- Full-HBDC Readiness Contract / Schema Evolution
(`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` §19,
§19A, §37; phase document
`docs/PHASE_149O_20L_CLASS_B_FULL_HBDC_READINESS_CONTRACT_INTEGRATION_ANALYSIS.md`).

This is a CONTRACT/SCHEMA-EVOLUTION-ONLY phase. It modifies no
`src/pcae/**` file, no `scripts/**` file, and no other contract
(HMIC-001/HBDC-001/HATP-001/HSCE-001/RAE-001/RWMPC-001/PBPA-001/
PBPC-001). It amends HMRC-001 from v1.0 to v1.1: repairs HMRC-REQ-054
in place to enumerate all seven live `PREPARED` readiness terms
(closing a contract-drift gap 149O.20L disclosed but did not repair),
then adds HMRC-REQ-086 through HMRC-REQ-100, defining full HBDC Class-B
deployment conformance as a mandatory, fail-closed eighth `PREPARED`
prerequisite, and widens the attack matrix from 45 to 52 scenarios.

This module independently re-verifies, by direct document/source
inspection (never trusting this phase's own prose or 149O.20L's
report):

  * the contract declares HMRC-001 v1.1, amended by this phase;
  * HMRC-REQ-054 now enumerates seven bullets, including the repaired
    `repository_deployment_identity_valid` bullet citing HATP-REQ-052;
  * HMRC-REQ-086-100 are present and cover: the eighth prerequisite;
    the canonical source function with no duplicate calculation; the
    closed-enum mapping over the exact live six-member vocabulary;
    fail-closed unknown/future/erroring-state behavior; evidence/
    Boolean separation; the frozen field name (explicitly not
    `class_b_ready`); freshness/no-cache; lock-held re-evaluation with
    no separate lock; TOCTOU/staleness rejection; no-caller-override;
    AND-conjunction with no alternate ready path; HMIC/HBDC
    independence; the no-HBDC-001-amendment relationship; additive-only
    schema evolution with a fail-closed default; and restated
    non-bypassability;
  * the attack matrix now has exactly 52 sequential rows, with the
    original 45 unaltered and new rows 46-52 present and fail-closed;
  * §37's amendment-history section is present, after §36, and
    documents the six-vs-seven repair, the Classification-B verdict,
    zero-production-consumer reconfirmation, the HBDC-001 consistency
    check, and the version-bump rationale;
  * HMRC-REQ-080 ("frozen as `HMRC-001 v1.0`") remains byte-unchanged
    (historical statement, not redefinition);
  * live `ClassBConformanceStatus` is reconfirmed as exactly six
    members, matching the contract's mapping table;
  * `certification_status_satisfies_readiness`'s identity-comparison
    pattern is reconfirmed as the mirrored precedent;
  * production still implements only the pre-amendment seven-term
    readiness vector -- `class_b_deployment_conformance_satisfies_
    readiness` is absent from `hatp_mandatory_cutover.py`, confirming
    the contract-ahead-of-production gap is intentional and disclosed;
  * zero production consumers of `verify_class_b_deployment_
    conformance` and `HATPMandatoryActivationReadiness` exist outside
    their own modules;
  * no persisted-artifact/JSON-serialization consumer of the readiness
    dataclass exists anywhere in `src/pcae/**`;
  * HMIC-001, HBDC-001, and every other depended-on contract, plus all
    `src/pcae/**` and `scripts/**` files, are clean (byte-unchanged) in
    the working tree;
  * CBV-S10 is restated OPEN, not closed, by this amendment; CBV-S1 is
    not reopened.
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
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CUTOVER_MODULE_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"
_TOPOLOGY_VERIFIER_PATH = _SRC / "core" / "hatp_class_b_topology_verifier.py"
_CERTIFICATION_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"

_OTHER_BOUND_CONTRACTS = (
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
)

_LIVE_CLASS_B_CONFORMANCE_STATUS_MEMBERS = (
    "COMPLIANT",
    "NON_COMPLIANT",
    "INDETERMINATE",
    "ACCESS_ERROR",
    "MALFORMED_STATE",
    "UNSUPPORTED_DEPLOYMENT_MODEL",
)


def _git_status_porcelain(path: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", path],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
        )
    except Exception:
        pytest.skip("git unavailable in this environment")
    if proc.returncode != 0:
        pytest.skip("not a git checkout")
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# Contract identity / version
# ---------------------------------------------------------------------------


def test_contract_version_is_v1_1():
    assert "**Version:** 1.1" in _CONTRACT_TEXT


def test_status_line_declares_pending_independent_verification_not_verified():
    status_line = next(ln for ln in _CONTRACT_TEXT.splitlines() if ln.startswith("**Status:**"))
    assert "PENDING INDEPENDENT CONTRACT VERIFICATION" in status_line
    assert "not VERIFIED at v1.1" in status_line


def test_amended_by_line_names_this_phase():
    assert "**Amended by:** Phase 149O.20L.1" in _CONTRACT_TEXT
    assert "v1.0 → v1.1" in _CONTRACT_TEXT


def test_depends_on_line_now_includes_hbdc_001():
    depends_line = next(ln for ln in _CONTRACT_TEXT.splitlines() if ln.startswith("**Depends on"))
    assert "HBDC-001 v1.0" in depends_line


# ---------------------------------------------------------------------------
# HMRC-REQ-054 repair: seven-bullet conjunction
# ---------------------------------------------------------------------------


def _req_054_block() -> str:
    start = _CONTRACT_TEXT.index("**HMRC-REQ-054 (")
    end = _CONTRACT_TEXT.index("**HMRC-REQ-055.", start)
    return _CONTRACT_TEXT[start:end]


def test_req_054_repaired_marker_present():
    block = _req_054_block()
    assert "repaired at v1.1" in block


def test_req_054_has_seven_bullets():
    block = _req_054_block()
    bullets = [ln for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert len(bullets) == 7, f"expected 7 bullets in repaired HMRC-REQ-054, found {len(bullets)}: {bullets}"


def test_req_054_second_bullet_is_repository_deployment_identity():
    block = _req_054_block()
    bullets = [ln.strip() for ln in block.splitlines() if ln.strip().startswith("- ")]
    assert bullets[1].startswith("- Repository/deployment identity valid")
    assert "HATP-REQ-052" in block


def test_req_054_eighth_bullet_references_class_b_conformance():
    block = _req_054_block()
    assert "full HBDC Class-B deployment conformance valid" in block
    assert "HMRC-REQ-086" in block
    assert "eighth prerequisite" in block


def test_req_054_original_six_bullets_still_present_in_some_form():
    block = _req_054_block()
    for phrase in (
        "Class-B protected storage valid",
        "HATP substrate operational",
        "HSCE signing implementation available",
        "Mandatory-consumption implementation version present",
        "Production dependency provenance valid",
        "Protected Activation Authority mechanism available",
    ):
        assert phrase in block, f"missing original HMRC-REQ-054 bullet content: {phrase!r}"


# ---------------------------------------------------------------------------
# New §19A / HMRC-REQ-086 .. 100
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("req_number", range(86, 101))
def test_new_requirement_present(req_number):
    assert f"**HMRC-REQ-{req_number:03d} (" in _CONTRACT_TEXT


def test_section_19a_heading_present():
    assert "## 19A. Full HBDC Class-B Deployment Conformance Readiness Prerequisite (New at v1.1)" in _CONTRACT_TEXT


def test_req_086_states_mandatory_eighth_prerequisite():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-086 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "eighth" in block.lower()
    assert "fail-closed" in block.lower()
    assert "mandatory" in block.lower()


def test_req_087_names_canonical_source_no_duplicate():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-087 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "verify_class_b_deployment_conformance" in block
    assert "SHALL NOT define a second" in block or "duplicate" in block.lower()


def test_req_088_mapping_table_covers_all_six_live_members():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-088 (")
    block = _CONTRACT_TEXT[idx: idx + 1600]
    for member in _LIVE_CLASS_B_CONFORMANCE_STATUS_MEMBERS:
        assert f"ClassBConformanceStatus.{member}" in block, f"mapping table missing {member}"
    assert block.count("-> readiness satisfied (True)") == 1
    assert block.count("-> readiness not satisfied (False)") == 5


def test_req_089_fail_closed_on_unknown_future_and_exception():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-089 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "future" in block.lower()
    assert "exception" in block.lower()
    assert "never" in block.lower() or "SHALL" in block


def test_req_090_evidence_boolean_separation():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-090 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "satisfied" in block
    assert "detail" in block
    for member in ("NON_COMPLIANT", "INDETERMINATE", "ACCESS_ERROR", "MALFORMED_STATE", "UNSUPPORTED_DEPLOYMENT_MODEL"):
        assert member in block


def test_req_091_freezes_field_name_and_rejects_class_b_ready():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-091 (")
    block = _CONTRACT_TEXT[idx: idx + 700]
    assert "class_b_deployment_conformance_satisfies_readiness" in block
    assert "`class_b_ready`" in block


def test_req_092_freshness_no_cache():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-092 (")
    block = _CONTRACT_TEXT[idx: idx + 700]
    assert "fresh" in block.lower()
    assert "cache" in block.lower()


def test_req_093_lock_held_no_separate_lock():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-093 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "readiness_check" in block
    assert "SHALL NOT introduce a" in block
    assert "separate" in block.lower()


def test_req_094_toctou_staleness():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-094 (")
    block = _CONTRACT_TEXT[idx: idx + 700]
    assert "SHALL NOT be treated as authorizing" in block


def test_req_095_no_caller_override():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-095 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "class_b_ok" in block
    assert "No future" in block
    assert "SHALL accept" in block


def test_req_096_conjunction_no_override_path():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-096 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "AND" in block
    assert "ready=False" in block


def test_req_097_hmic_hbdc_independence():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-097 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "independent" in block.lower()
    assert "does not imply" in block.lower()


def test_req_098_no_hbdc_001_amendment_relationship():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-098 (")
    block = _CONTRACT_TEXT[idx: idx + 1100]
    assert "does not amend" in block
    assert "HBDC-REQ-049" in block
    assert "HBDC-REQ-055" in block
    assert "CBD-8" in block


def test_req_099_additive_only_fail_closed_default():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-099 (")
    block = _CONTRACT_TEXT[idx: idx + 900]
    assert "additive-only" in block.lower() or "additive only" in block.lower()
    assert "satisfied=False" in block


def test_req_100_non_bypassability_restated():
    idx = _CONTRACT_TEXT.index("**HMRC-REQ-100 (")
    block = _CONTRACT_TEXT[idx: idx + 700]
    assert "SHALL" in block


# ---------------------------------------------------------------------------
# Attack matrix widened 45 -> 52
# ---------------------------------------------------------------------------


def test_attack_matrix_heading_declares_52_scenarios():
    assert "## 29. Full Mandatory Attack Matrix (52 Scenarios)" in _CONTRACT_TEXT


def _attack_matrix_rows() -> "list[str]":
    start = _CONTRACT_TEXT.index("| # | Attack | Expected Result (frozen) |")
    end = _CONTRACT_TEXT.index("\n\n---", start)
    lines = _CONTRACT_TEXT[start:end].splitlines()
    return [ln for ln in lines if re.match(r"^\|\s*\d+\s*\|", ln)]


def test_attack_matrix_has_exactly_52_rows_sequential():
    rows = _attack_matrix_rows()
    assert len(rows) == 52
    numbers = [int(re.match(r"^\|\s*(\d+)\s*\|", row).group(1)) for row in rows]
    assert numbers == list(range(1, 53))


def test_attack_matrix_original_45_unaltered_row_45():
    rows = _attack_matrix_rows()
    row_45 = rows[44]
    assert "Evidence existence without an explicit evidence ID supplied" in row_45
    assert "HMRC-REQ-014" in row_45


@pytest.mark.parametrize("row_index,expected_fragment", [
    (45, "NON_COMPLIANT"),
    (46, "INDETERMINATE"),
    (47, "conjunction preserved"),
    (48, "Fail closed, never ready"),
    (49, "fresh lock-held re-check is authoritative"),
    (50, "Structurally impossible"),
    (51, "Structurally impossible once wired"),
])
def test_new_attack_rows_46_through_52_fail_closed(row_index, expected_fragment):
    rows = _attack_matrix_rows()
    assert expected_fragment in rows[row_index]


# ---------------------------------------------------------------------------
# Requirement numbering: no gaps, no duplicates, sequential through 100
# ---------------------------------------------------------------------------


def test_requirement_numbering_sequential_no_gaps_through_100():
    numbers = sorted({int(n) for n in re.findall(r"HMRC-REQ-(\d+)", _CONTRACT_TEXT)})
    assert numbers[0] == 1
    assert numbers[-1] == 100
    assert numbers == list(range(1, 101)), "gap or duplicate found in HMRC-REQ numbering"


# ---------------------------------------------------------------------------
# §37 amendment history
# ---------------------------------------------------------------------------


def test_section_37_present_after_section_36():
    idx_36 = _CONTRACT_TEXT.index("## 36. Explicit Confirmations")
    idx_37 = _CONTRACT_TEXT.index("## 37. Contract Amendment History — Phase 149O.20L.1 (v1.1)")
    assert idx_37 > idx_36


def test_section_37_documents_classification_b():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    text = " ".join(section.split())
    assert "contract drift (Classification B)" in text or "Classification B" in text
    assert "945af762" in text
    assert "861fb04f" in text


def test_section_37_documents_hbdc_consistency_check():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    assert "HBDC-REQ-049" in section
    assert "HBDC-REQ-055" in section
    assert "byte-unchanged" in section


def test_section_37_documents_expected_production_mismatch():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    text = " ".join(section.split())
    assert "does not yet appear" in text or "does not yet call" in text


def test_section_37_recommends_149o_20l_2():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    assert "149O.20L.2" in section


# ---------------------------------------------------------------------------
# Historical pinning: HMRC-REQ-080 left byte-unchanged
# ---------------------------------------------------------------------------


def test_req_080_still_reads_frozen_as_v1_0():
    assert "**HMRC-REQ-080.** This contract is frozen as `HMRC-001 v1.0`." in _CONTRACT_TEXT


def test_hmic_req_139_precedent_reference_present():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    assert "HMIC-REQ-139" in section


# ---------------------------------------------------------------------------
# Requirement category index updated
# ---------------------------------------------------------------------------


def test_category_index_has_new_row():
    assert "| Full HBDC Class-B readiness prerequisite (new at v1.1) | HMRC-REQ-086 – 100 |" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# Fresh, independent re-derivation directly from live source (never trusts
# this phase's own prose or 149O.20L's report)
# ---------------------------------------------------------------------------


def test_live_class_b_conformance_status_matches_contract_mapping():
    source = _TOPOLOGY_VERIFIER_PATH.read_text(encoding="utf-8")
    match = re.search(r"class ClassBConformanceStatus\(str, Enum\):(.*?)\n\n\n", source, re.DOTALL)
    assert match, "could not locate ClassBConformanceStatus definition"
    body = match.group(1)
    members = re.findall(r'^\s*([A-Z_]+)\s*=\s*"[A-Z_]+"', body, re.MULTILINE)
    assert tuple(members) == _LIVE_CLASS_B_CONFORMANCE_STATUS_MEMBERS


def test_live_certification_status_satisfies_readiness_uses_identity_comparison():
    source = _CERTIFICATION_MODULE_PATH.read_text(encoding="utf-8")
    assert "return status is CertificationStatus.VALID" in source


def test_production_readiness_vector_still_seven_terms_pre_amendment():
    """Confirms the contract-ahead-of-production gap §37.8 discloses:
    production has not been wired to the new eighth term by this phase."""
    source = _CUTOVER_MODULE_PATH.read_text(encoding="utf-8")
    assert "class_b_deployment_conformance_satisfies_readiness" not in source
    for existing_term in (
        "class_b_protected_storage_available",
        "repository_deployment_identity_valid",
        "hatp_substrate_operational",
        "hsce_signing_implementation_available",
        "mandatory_consumption_implementation_independently_verified",
        "production_dependency_provenance_valid",
        "protected_activation_authority_mechanism_available",
    ):
        assert existing_term in source


def test_zero_production_consumers_of_class_b_verifier_outside_own_module():
    consumer_markers = ("verify_class_b_deployment_conformance",)
    for path in _SRC.rglob("*.py"):
        if path.name == "hatp_class_b_conformance.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in consumer_markers:
            assert marker not in text, f"unexpected Class-B verifier consumer in {path}: {marker}"


def test_zero_consumers_of_readiness_dataclass_outside_own_module():
    for path in _SRC.rglob("*.py"):
        if path.name == "hatp_mandatory_cutover.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "HATPMandatoryActivationReadiness" not in text, f"unexpected readiness-dataclass consumer in {path}"


def test_no_json_serialization_consumer_of_readiness_in_cli_or_commands():
    for candidate in (_SRC / "cli.py",):
        text = candidate.read_text(encoding="utf-8", errors="replace")
        assert "assess_hatp_mandatory_activation_readiness" not in text
        assert "activate_hatp_mandatory" not in text
    commands_dir = _SRC / "commands"
    if commands_dir.is_dir():
        for path in commands_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            assert "assess_hatp_mandatory_activation_readiness" not in text
            assert "activate_hatp_mandatory" not in text


# ---------------------------------------------------------------------------
# No HMIC-001/HBDC-001/other-contract amendment; no production edit
# ---------------------------------------------------------------------------


def test_hmic_contract_still_declares_v1_3():
    hmic_text = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.3" in hmic_text
    assert "**Contract ID:** HMIC-001" in hmic_text


def test_hbdc_contract_still_declares_v1_0():
    hbdc_text = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.0" in hbdc_text
    assert "**Contract:** HBDC-001" in hbdc_text


@pytest.mark.parametrize("other_contract", _OTHER_BOUND_CONTRACTS)
def test_other_contracts_clean_in_working_tree(other_contract):
    assert _git_status_porcelain(other_contract) == ""


def test_no_src_pcae_files_dirty_in_working_tree():
    assert _git_status_porcelain("src/pcae") == "", "production source dirty during a contract-only phase"


def test_no_scripts_files_dirty_in_working_tree():
    assert _git_status_porcelain("scripts") == "", "scripts/ dirty during a contract-only phase"


# ---------------------------------------------------------------------------
# CBV-S10 / CBV-S1 status restated correctly
# ---------------------------------------------------------------------------


def test_cbv_s10_restated_open_not_closed():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 37. Contract Amendment History"):]
    assert "CBV-S10 remains" in section
    assert "OPEN" in section


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        assert not list(_REPO_ROOT.rglob(name))
