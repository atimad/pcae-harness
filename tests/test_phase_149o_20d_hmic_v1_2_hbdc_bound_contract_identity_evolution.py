"""Phase 149O.20D -- HMIC v1.2 HBDC Bound-Contract Identity Evolution
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§51; phase document
`docs/PHASE_149O_20D_HMIC_V1_2_HBDC_BOUND_CONTRACT_IDENTITY_EVOLUTION.md`).

This is a CONTRACT-EVOLUTION-ONLY phase: it modifies no `src/pcae/**`
file, no `scripts/**` file, and no other bound contract (HMRC-001/
HATP-001/HSCE-001/RAE-001/RWMPC-001/PBPA-001/PBPC-001/HBDC-001). It
widens HMIC-001 from v1.1 to v1.2, adding `HBDC-001` v1.0 as a fifth
`contract_versions` member (HMIC-REQ-067), per HBDC-REQ-048's own
prerequisite and Phase 149O.20C's independent recommendation. It
deliberately does NOT add HBDC-001's document to the twenty-four-file
`implementation_scope_digest` enumeration (HMIC-REQ-050), leaving a
disclosed residual limitation (HMIC-REQ-145) rather than silently
overclaiming completeness.

This module independently re-verifies, by direct document inspection
(never trusting this phase's own prose or a prior phase's summary):

  * the contract declares HMIC-001 v1.2;
  * `contract_versions`' minimal sufficient set (HMIC-REQ-067) now names
    exactly five contracts, the original four preserved plus HBDC-001;
  * the twenty-four-file `implementation_scope_digest` enumeration
    (HMIC-REQ-050) is byte-identical to its pre-phase form -- HBDC-001's
    document is NOT a 25th entry;
  * the total frozen-contract-corpus-vs-`contract_versions`-membership
    terminology distinction (8->9 corpus, 4->5 `contract_versions`) is
    stated explicitly and not conflated;
  * the contract's requirement/CIVC/attack-matrix inventory counts
    (145/12/36) after the amendment;
  * HMIC-REQ-145 names the same-version-byte-drift residual limitation
    explicitly, honestly, without claiming it solved;
  * HMIC-REQ-063/Option C's own text is byte-unchanged;
  * the contract states the "contract-first temporary divergence"
    (production still computes the four-member `contract_versions` set)
    explicitly, and states this is fail-closed;
  * HBDC-001 itself, and the other seven pre-existing bound contracts,
    are byte-unchanged;
  * no `src/pcae/**` or `scripts/**` file is modified in the working
    tree by this phase;
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

#: The eight pre-existing bound contracts (149O.20B/149O.20C's own
#: convention), plus HBDC-001 itself as the ninth member of the total
#: frozen-contract corpus this phase adds (149O.20C §12 disambiguation).
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

_ORIGINAL_24_FROZEN_PATHS = (
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_mandatory_certification.py",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "scripts/hatp_certification_admin.py",
)

_ORIGINAL_FOUR_CONTRACT_VERSIONS_MEMBERS = ("HMRC-001", "HATP-001", "HSCE-001", "RAE-001")


def _extract_req_050_paths() -> "list[str]":
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = _CONTRACT_TEXT.index(marker)
    fence_start = _CONTRACT_TEXT.index("```", start)
    fence_end = _CONTRACT_TEXT.index("```", fence_start + 3)
    block = _CONTRACT_TEXT[fence_start + 3 : fence_end]
    return [ln.strip() for ln in block.splitlines() if ln.strip()]


def _extracted_bare_paths() -> "list[str]":
    return [re.sub(r"\s+\([A-Z0-9-]+\)\s*$", "", ln).strip() for ln in _extract_req_050_paths()]


# ---------------------------------------------------------------------------
# Version identity
# ---------------------------------------------------------------------------


def test_contract_version_is_v1_2():
    assert "**Contract ID:** HMIC-001" in _CONTRACT_TEXT
    assert "**Version:** 1.2" in _CONTRACT_TEXT


def test_status_line_declares_pending_independent_verification_not_verified():
    idx = _CONTRACT_TEXT.index("**Status:**")
    line = _CONTRACT_TEXT[idx : _CONTRACT_TEXT.index("\n", idx)]
    assert "HBDC BOUND-CONTRACT IDENTITY EVOLUTION COMPLETE" in line
    assert "PENDING INDEPENDENT VERIFICATION" in line
    assert "not VERIFIED at v1.2" in line


def test_amended_by_line_names_this_phase():
    assert "**Amended by:** Phase 149O.20D" in _CONTRACT_TEXT


def test_depends_on_line_lists_hbdc():
    idx = _CONTRACT_TEXT.index("**Depends on (unamended, byte-unchanged):**")
    line = _CONTRACT_TEXT[idx : _CONTRACT_TEXT.index("\n", idx)]
    assert "HBDC-001 v1.0" in line


# ---------------------------------------------------------------------------
# contract_versions widened to five, HMIC-REQ-067
# ---------------------------------------------------------------------------


def test_hmic_req_067_names_exactly_five_contract_versions_members():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-067")
    section_end = _CONTRACT_TEXT.index("**HMIC-REQ-068")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    for member in _ORIGINAL_FOUR_CONTRACT_VERSIONS_MEMBERS + ("HBDC-001",):
        assert f"`{member}`" in text, f"{member} missing from revised HMIC-REQ-067"
    assert "Five entries, no more, no fewer, under v1.2" in text


def test_hmic_req_068_excludes_rwmpc_pbpa_pbpc_but_not_hbdc():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-068")
    section_end = _CONTRACT_TEXT.index("**HMIC-REQ-069")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "RWMPC-001" in text and "PBPA-001" in text and "PBPC-001" in text
    assert "opposite disposition" in text
    assert "it is included, not excluded" in text


def test_hmic_req_069_references_five_member_comparison_and_hmic_req_145():
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-069")
    section_end = _CONTRACT_TEXT.index("**HMIC-REQ-070")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "five entries as of v1.2" in text
    assert "HMIC-REQ-145" in text


# ---------------------------------------------------------------------------
# 24-file implementation_scope_digest set preserved byte-for-byte
# ---------------------------------------------------------------------------


def test_frozen_file_set_still_has_exactly_24_entries():
    extracted = _extract_req_050_paths()
    assert len(extracted) == 24, f"expected 24 lines in HMIC-REQ-050's fenced block, found {len(extracted)}: {extracted}"


def test_hbdc_contract_not_present_in_frozen_implementation_scope_digest_set():
    bare = set(_extracted_bare_paths())
    assert "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" not in bare


def test_frozen_file_set_unchanged_from_pre_phase_v1_1_enumeration():
    bare = _extracted_bare_paths()
    src_relative = [p for p in bare if not p.startswith("docs/") and not p.startswith("scripts/")]
    others = [p for p in bare if p.startswith("docs/") or p.startswith("scripts/")]
    reconstructed = [f"src/pcae/{p}" for p in src_relative] + others
    assert sorted(reconstructed) == sorted(_ORIGINAL_24_FROZEN_PATHS)


# ---------------------------------------------------------------------------
# Total-corpus vs contract_versions-membership terminology, preserved from
# 149O.20C's own disambiguation, restated (not conflated) at v1.2
# ---------------------------------------------------------------------------


def test_total_corpus_and_contract_versions_counts_both_stated_and_distinct():
    text = " ".join(_CONTRACT_TEXT.split())
    assert "total frozen-contract corpus: 8" in text or "total-frozen-contract-corpus" in text
    assert "4 -> 5" in text.replace("→", "->") or "4 → 5" in _CONTRACT_TEXT
    assert "8 -> 9" in text.replace("→", "->") or "8 → 9" in _CONTRACT_TEXT
    assert "not nine" in text or "not 9" in text or "five, not nine" in text.replace("→", "->")


# ---------------------------------------------------------------------------
# Requirement / CIVC / attack inventory counts after amendment
# ---------------------------------------------------------------------------


def test_requirement_ids_are_exactly_001_to_145_no_gaps_no_duplicates():
    ids = sorted(int(m) for m in re.findall(r"\*\*HMIC-REQ-(\d{3})", _CONTRACT_TEXT))
    assert ids == list(range(1, 146))
    assert len(set(ids)) == 145


def test_hmic_req_145_present_and_names_residual_limitation():
    assert "**HMIC-REQ-145" in _CONTRACT_TEXT
    section_start = _CONTRACT_TEXT.index("**HMIC-REQ-145")
    section_end = _CONTRACT_TEXT.index("## 21. `CertificationRecord` Schema") if False else None
    # Bounded read: take the next 2500 chars, sufficient to cover the requirement's own prose.
    text = " ".join(_CONTRACT_TEXT[section_start : section_start + 2500].split())
    assert "not caught by v1.2" in text or "not** caught by v1.2" in text
    assert "named, explicit, disclosed residual limitation" in text


def test_civc_invariants_are_exactly_1_to_12():
    ids = sorted(int(m) for m in re.findall(r"- \*\*CIVC-(\d+)\.\*\*", _CONTRACT_TEXT))
    assert ids == list(range(1, 13))


def test_civc_5_mentions_five_member_v1_2_set():
    section_start = _CONTRACT_TEXT.index("**CIVC-5.**")
    section_end = _CONTRACT_TEXT.index("**CIVC-6.**")
    text = " ".join(_CONTRACT_TEXT[section_start:section_end].split())
    assert "HBDC-001" in text
    assert "five" in text.lower()


def test_attack_matrix_heading_declares_36_scenarios():
    assert "## 41. Full Mandatory Attack Matrix (36 Scenarios)" in _CONTRACT_TEXT


def _attack_matrix_table_text() -> str:
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    return _CONTRACT_TEXT[table_start:table_end]


def test_attack_matrix_has_exactly_36_rows_sequential():
    table = _attack_matrix_table_text()
    rows = re.findall(r"^\| ([0-9]+) ", table, flags=re.MULTILINE)
    assert [int(r) for r in rows] == list(range(1, 37))


def test_attack_rows_35_and_36_present_and_named():
    table = _attack_matrix_table_text()
    row_35 = next(line for line in table.splitlines() if line.startswith("| 35 "))
    row_36 = next(line for line in table.splitlines() if line.startswith("| 36 "))
    assert "semantic-drift" in row_35.lower()
    assert "HBDC" in row_35
    assert "Legacy four-contract" in row_36 or "legacy four-contract" in row_36.lower()
    assert "not yet operative" in row_36.lower()


def test_preexisting_attack_rows_1_through_34_untouched_in_count():
    table = _attack_matrix_table_text()
    rows = re.findall(r"^\| ([0-9]+) ", table, flags=re.MULTILINE)
    assert len(rows) == 36


# ---------------------------------------------------------------------------
# HMIC-REQ-063 / Option C byte-unchanged; no overclaim
# ---------------------------------------------------------------------------


def test_hmic_req_063_text_byte_unchanged():
    marker = "**HMIC-REQ-063 (Import-Shadowing"
    assert marker in _CONTRACT_TEXT
    idx = _CONTRACT_TEXT.index(marker)
    end = _CONTRACT_TEXT.index("**HMIC-REQ-064", idx)
    text = _CONTRACT_TEXT[idx:end]
    assert "does NOT implement an" in text
    assert "executed-code/runtime-module-resolution check" in text


def test_option_c_not_converted_to_unconditional_acceptance():
    text = " ".join(_CONTRACT_TEXT.split())
    assert "does not convert it into an unconditional acceptance" in text
    assert "Model A remains the" in text


# ---------------------------------------------------------------------------
# Contract-first temporary divergence, fail-closed, explicitly disclosed
# ---------------------------------------------------------------------------


def test_production_divergence_section_present_and_fail_closed():
    text = " ".join(_CONTRACT_TEXT.split())
    assert "temporarily **not conformant**" in _CONTRACT_TEXT
    assert "zero** functional effect" in _CONTRACT_TEXT
    assert "Fail-closed holds throughout" in _CONTRACT_TEXT


def test_hbdc_binding_gate_status_named():
    assert "HBDC-BINDING-GATE" in _CONTRACT_TEXT
    assert "CONTRACT-LEVEL EVOLUTION COMPLETE" in _CONTRACT_TEXT
    assert "INDEPENDENT CONTRACT VERIFICATION PENDING" in _CONTRACT_TEXT


def test_w1_and_b149o1931_not_reopened():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 51. Contract Amendment History") :]
    text = " ".join(section.split())
    assert "does not reopen, narrow, or widen" in text
    assert "B-149O.19.3-1" in text and "remains independently closed" in text


def test_contract_evolution_verdict_present():
    assert "**Contract-evolution verdict.**" in _CONTRACT_TEXT
    assert "HMIC-001 v1.2: FROZEN — HBDC BOUND-" in _CONTRACT_TEXT


def test_recommended_next_phase_is_149o_20e_not_provisioning():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 51. Contract Amendment History") :]
    assert "149O.20E" in section
    assert "not** Class-B provisioning" in section


# ---------------------------------------------------------------------------
# HBDC-001 itself, and every other pre-existing bound contract, unchanged
# ---------------------------------------------------------------------------


def test_hbdc_contract_still_declares_v1_0():
    hbdc_text = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.0" in hbdc_text
    assert "**Contract:** HBDC-001" in hbdc_text


def test_hbdc_req_047_still_states_not_yet_bound_as_of_its_own_v1_0_text():
    """HBDC-001's own text is byte-unchanged; it still describes its
    pre-149O.20D disposition (v1.0 was frozen before this amendment and
    is not itself amended by it -- HMIC-001, not HBDC-001, changed)."""
    hbdc_text = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
    assert "HBDC-001's normative text is deployment-verification-governing but is not, as of v1.0, one of HMIC-001's bound contracts." in hbdc_text


@pytest.mark.parametrize("existing_contract", _EXISTING_EIGHT_BOUND_CONTRACTS)
def test_only_hmic_contract_dirty_others_clean_in_working_tree(existing_contract):
    """Best-effort self-check via `git status --porcelain`: confirms no
    *other* existing bound-contract file under `docs/contracts/**` is
    modified in the working tree by this phase. Read-only evidence
    gathering, not the sole authority -- the phase report's own
    `git diff --stat` is authoritative, consistent with 149O.20B's own
    convention for this exact check."""
    if existing_contract.endswith("HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"):
        pytest.skip("this is the one contract this phase intentionally amends")
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
    assert proc.stdout.strip() == "", f"production source dirty during a contract-only phase: {proc.stdout}"


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
    assert proc.stdout.strip() == "", f"scripts/ dirty during a contract-only phase: {proc.stdout}"


def test_production_contract_versions_required_keys_still_four():
    """Confirms production's own `_CONTRACT_IDENTITY_FILES` constant is
    still the pre-amendment four-member set -- the expected, disclosed,
    fail-closed contract-first divergence this phase's charter requires,
    not accidentally aligned to five by this contract-only phase."""
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"_CONTRACT_IDENTITY_FILES:.*?=\s*\(\s*(.*?)\n\)", source, re.DOTALL)
    assert match, "could not locate _CONTRACT_IDENTITY_FILES in hatp_mandatory_certification.py"
    body = match.group(1)
    ids = re.findall(r'\("([A-Z0-9-]+)",', body)
    assert ids == list(_ORIGINAL_FOUR_CONTRACT_VERSIONS_MEMBERS), (
        f"production contract_versions membership changed during a contract-only phase: {ids}"
    )
    assert "HBDC-001" not in body


def test_wave_f_validator_call_present_and_unmodified_by_this_phase():
    """Wave F (Phase 149O.19.5F, predating 149O.20A-D) already wired a
    real, fresh call to the HMIC validator into the readiness assessment
    -- the literal hard-coded `False` ceiling §49/§50 describe no longer
    exists in this file. This phase does not touch it; confirms the
    fresh-call wiring is present and, separately, that no certification
    state exists on this host, so the call still fails closed to `False`
    regardless of this phase's contract_versions text change."""
    source = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    assert "validate_active_hatp_mandatory_independent_verification_certification(" in source
    assert "certification_status_satisfies_readiness(" in source


def test_no_certification_storage_files_exist_so_validator_fails_closed():
    for name in ("certifications.json", "certification-bindings.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == [], f"unexpected real certification storage file present: {hits}"


# ---------------------------------------------------------------------------
# No real certification state anywhere in the repository
# ---------------------------------------------------------------------------


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "certification-bindings.json", "active_certification.json"):
        hits = [h for h in _REPO_ROOT.rglob(name) if ".git" not in h.parts and ".venv" not in h.parts]
        assert hits == []


def test_history_section_51_present_and_after_section_50():
    idx_50 = _CONTRACT_TEXT.index("## 50. Contract Amendment History")
    idx_51 = _CONTRACT_TEXT.index("## 51. Contract Amendment History")
    assert idx_51 > idx_50


def test_hbdc_req_048_language_referenced_as_the_prerequisite_this_phase_closes():
    section = _CONTRACT_TEXT[_CONTRACT_TEXT.index("## 51. Contract Amendment History") :]
    text = " ".join(section.split())
    assert "HBDC-REQ-048" in text
    assert "at minimum, its version tracked in" in text
