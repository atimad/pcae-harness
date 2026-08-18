"""Phase 149O.20L.7O.2D.2 -- HATP Principal/Signer Enrollment Contract
Repair.

This phase is a documentation-only contract repair: HPSE-001 v1.0 -> v1.1,
closing Blocking findings B-149O.20L.7O.2D.1-1/2 from Phase 149O.20L.7O.2D.1's
independent verification. No hardware provider code was implemented, no
`hardware-credentials.json` writer was implemented, no Principal/Signer
enrollment writer was implemented, no credential was provisioned, no
principal or signer was enrolled, no `DeploymentBinding` was created, no
election was initiated, no CHGR was published, no certification was
performed, and no Dell mutation occurred. These tests mechanically
re-verify this phase's own load-bearing claims (numbering, closure
mapping, revision-in-place discipline) directly against the amended
contract text -- never against this phase's own report prose.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HPSE_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_REPORT_PATH = (
    _REPO_ROOT / "docs" / "PHASE_149O_20L_7O_2D_2_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_REPAIR.md"
)
_FIDO2_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"
_PIV_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_piv_provider.py"

_PHASE_ENTRY_COMMIT = "d12462c4"


def _read(path: Path) -> str:
    return path.read_text()


def _collapsed(text: str) -> str:
    return " ".join(text.split())


# ═══════════════════════════════════════════════════════════════════════════
# 1. Requirement numbering: mechanically re-verified against the amended
#    contract text, not taken from this phase's own report claim.
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementNumbering:
    def test_hpse_req_range_is_exactly_001_through_074_no_gaps_no_duplicates(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        defined = sorted(int(n) for n in re.findall(r"\*\*HPSE-REQ-(\d{3})\b", text))
        assert defined == list(range(1, 75))

    def test_each_hpse_req_id_appears_as_a_bold_definition_exactly_once(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        for n in range(1, 75):
            pattern = rf"\*\*HPSE-REQ-{n:03d}\b"
            count = len(re.findall(pattern, text))
            assert count == 1, f"HPSE-REQ-{n:03d} defined {count} times, expected exactly 1"

    def test_new_requirements_053_through_074_are_present(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        for n in range(53, 75):
            assert f"HPSE-REQ-{n:03d}" in text


# ═══════════════════════════════════════════════════════════════════════════
# 2. Version bump and status.
# ═══════════════════════════════════════════════════════════════════════════


class TestVersionAndStatus:
    def test_contract_version_is_1_1(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "**Version:** 1.1" in text

    def test_status_names_second_independent_verification(self) -> None:
        text = _collapsed(_read(_HPSE_CONTRACT_PATH))
        assert "PENDING SECOND INDEPENDENT VERIFICATION" in text

    def test_expected_verdict_says_contract_repaired(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "CONTRACT REPAIRED" in text
        assert "READY FOR SECOND INDEPENDENT VERIFICATION" in text

    def test_hbdc_contract_text_is_byte_identical_since_phase_entry(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "--", str(_HBDC_CONTRACT_PATH)],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == ""

    def test_hbdc_contract_still_declares_v1_2(self) -> None:
        text = _read(_HBDC_CONTRACT_PATH)
        assert "**Version:** 1.2" in text


# ═══════════════════════════════════════════════════════════════════════════
# 3. Revision-in-place discipline: HPSE-REQ-011/045/046 are marked
#    revised; no other v1.0 requirement's identity was renumbered.
# ═══════════════════════════════════════════════════════════════════════════


class TestRevisionInPlaceDiscipline:
    def _requirement_text(self, req_id: str) -> str:
        text = _read(_HPSE_CONTRACT_PATH)
        pattern = rf"\*\*{re.escape(req_id)}[^*]*\*\*.*?(?=\n- \*\*HPSE-REQ-|\n## )"
        match = re.search(pattern, text, re.DOTALL)
        assert match is not None, f"could not isolate {req_id}'s own text block"
        return match.group(0)

    def test_req_011_marked_revised_and_discloses_unconditional_raise(self) -> None:
        body = self._requirement_text("HPSE-REQ-011")
        assert "revised, v1.1" in body
        assert "unconditionally raise" in body
        # The v1.0 "MAY be unable to re-derive" phrasing may still appear
        # quoted, for contrast, but only inside an explicit correction --
        # never as this requirement's own current-state claim.
        assert "understates" in body or "read naturally as describing" in body

    def test_req_045_marked_revised(self) -> None:
        body = self._requirement_text("HPSE-REQ-045")
        assert "revised, v1.1" in body

    def test_req_046_marked_revised_and_sequence_has_twelve_steps(self) -> None:
        body = self._requirement_text("HPSE-REQ-046")
        assert "revised, v1.1" in body
        for n in range(1, 13):
            assert f"({n})" in body

    def test_untouched_v1_0_requirements_are_not_marked_revised(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        for req_id in ("HPSE-REQ-001", "HPSE-REQ-009", "HPSE-REQ-033", "HPSE-REQ-052"):
            body = self._requirement_text(req_id)
            assert "revised, v1.1" not in body

    def test_req_010_original_language_preserved(self) -> None:
        body = self._requirement_text("HPSE-REQ-010")
        assert "never independently invented, never human-typed" in body


# ═══════════════════════════════════════════════════════════════════════════
# 4. HHCE-001 disposition (closes B-149O.20L.7O.2D.1-1).
# ═══════════════════════════════════════════════════════════════════════════


class TestHhceDisposition:
    def test_hhce_001_named_as_required_future_companion_contract(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "HHCE-001" in text
        assert "HATP Hardware Credential Enrollment Contract" in text

    def test_disposition_c_rationale_present(self) -> None:
        text = _collapsed(_read(_HPSE_CONTRACT_PATH))
        assert "Disposition chosen" in text

    def test_hhce_001_not_claimed_as_authored_or_frozen(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "not yet authored" in text


# ═══════════════════════════════════════════════════════════════════════════
# 5. Cross-registry consistency invariant (structural closure of B-1).
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossRegistryInvariant:
    def test_req_056_states_credential_before_signer_ordering(self) -> None:
        body_match = re.search(r"\*\*HPSE-REQ-056\.\*\*(.*?)\n\n## ", _read(_HPSE_CONTRACT_PATH), re.DOTALL)
        assert body_match is not None
        body = body_match.group(1)
        assert "before" in body
        assert "signer enrollment" in body.lower()

    def test_hpi_7_names_structural_closure(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "HPI-7" in text
        assert "structurally" in text

    def test_lock_ordering_rule_is_explicit(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "HPSE-REQ-057" in text
        assert "outer" in text.lower() and "inner" in text.lower()

    def test_all_six_failure_cases_present(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        for label in ("(A)", "(B)", "(C)", "(D)", "(E)", "(F)"):
            assert label in text


# ═══════════════════════════════════════════════════════════════════════════
# 6. credential_identity() correction still matches live source (closes
#    B-149O.20L.7O.2D.1-2) -- re-verified against source, not assumed
#    carried over from Phase 149O.20L.7O.2D.1's own finding.
# ═══════════════════════════════════════════════════════════════════════════


class TestCredentialIdentityStillUnconditionalRaise:
    def test_fido2_credential_identity_still_unconditional_raise(self) -> None:
        source = _read(_FIDO2_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        body = match.group(1)
        assert "raise HATPProviderUnavailableError" in body
        assert "if " not in body

    def test_piv_credential_identity_still_unconditional_raise(self) -> None:
        source = _read(_PIV_PATH)
        match = re.search(r"def credential_identity\(self\) -> str:\n(.*?)\n\n    def ", source, re.DOTALL)
        assert match is not None
        assert "raise HATPProviderUnavailableError" in match.group(1)

    def test_req_059_names_semantic_output_not_a_function_name(self) -> None:
        text = _collapsed(_read(_HPSE_CONTRACT_PATH))
        assert "HPSE-REQ-059" in text
        assert "does not freeze an implementation function name" in text.lower() or "does not freeze" in text

    def test_req_060_names_prerequisite_distinct_from_physical_presence(self) -> None:
        text = _collapsed(_read(_HPSE_CONTRACT_PATH))
        assert "distinct" in text and "physical" in text


# ═══════════════════════════════════════════════════════════════════════════
# 7. signer_key_id equivalence disambiguation.
# ═══════════════════════════════════════════════════════════════════════════


class TestSignerKeyIdEquivalence:
    def test_req_061_states_explicit_equivalence(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "signer_key_id == hex(credential_identity_bytes)" in text


# ═══════════════════════════════════════════════════════════════════════════
# 8. Implementation-readiness gate and closure mapping.
# ═══════════════════════════════════════════════════════════════════════════


class TestImplementationReadinessGateAndClosureMapping:
    def test_req_072_names_five_preconditions(self) -> None:
        body_match = re.search(r"\*\*HPSE-REQ-072\.\*\*(.*?)\n\n## ", _read(_HPSE_CONTRACT_PATH), re.DOTALL)
        assert body_match is not None
        body = body_match.group(1)
        for label in ("(a)", "(b)", "(c)", "(d)", "(e)"):
            assert label in body

    def test_closure_mapping_names_both_blocking_findings(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        assert "B-149O.20L.7O.2D.1-1" in text
        assert "B-149O.20L.7O.2D.1-2" in text
        assert "HPSE-REQ-056" in text
        assert "HPSE-REQ-060" in text

    def test_no_addressed_in_prose_only_closure(self) -> None:
        # The closure mapping section must cite concrete requirement IDs,
        # not merely narrative prose, for each finding.
        text = _read(_HPSE_CONTRACT_PATH)
        section_match = re.search(r"## 46\. Blocking-Finding Closure Mapping(.*?)\n## 47", text, re.DOTALL)
        assert section_match is not None
        section = section_match.group(1)
        assert section.count("HPSE-REQ-") >= 8


# ═══════════════════════════════════════════════════════════════════════════
# 9. Non-Blocking findings disposition -- each of the five is classified.
# ═══════════════════════════════════════════════════════════════════════════


class TestNonBlockingDisposition:
    def test_all_five_non_blocking_findings_classified(self) -> None:
        text = _read(_HPSE_CONTRACT_PATH)
        for label in ("NB-1", "NB-2", "NB-3", "NB-4", "NB-5"):
            assert label in text

    def test_nb2_explicitly_deferred_not_silently_dropped(self) -> None:
        section_match = re.search(r"## 47\. Non-Blocking Findings Disposition(.*?)\n## 48", _read(_HPSE_CONTRACT_PATH), re.DOTALL)
        assert section_match is not None
        section = section_match.group(1)
        assert "explicitly deferred" in section


# ═══════════════════════════════════════════════════════════════════════════
# 10. Updated requirement inventory self-consistency.
# ═══════════════════════════════════════════════════════════════════════════


class TestUpdatedInventory:
    def test_inventory_states_74_requirements(self) -> None:
        text = _collapsed(_read(_HPSE_CONTRACT_PATH))
        assert "HPSE-001 v1.1 defines **74** requirements".replace("*", "") in text.replace("*", "")


# ═══════════════════════════════════════════════════════════════════════════
# 11. Report self-consistency.
# ═══════════════════════════════════════════════════════════════════════════


class TestReportSelfConsistency:
    def test_report_exists_and_states_final_verdict(self) -> None:
        text = _collapsed(_read(_REPORT_PATH))
        assert "CONTRACT REPAIRED" in text
        assert "READY FOR SECOND INDEPENDENT VERIFICATION" in text

    def test_report_recommends_second_iv_phase(self) -> None:
        text = _collapsed(_read(_REPORT_PATH))
        assert "149O.20L.7O.2D.3" in text

    def test_report_states_no_implementation_no_dell_no_enrollment(self) -> None:
        text = _collapsed(_read(_REPORT_PATH))
        assert "No implementation" in text or "no implementation" in text.lower()
        assert "No Dell mutation" in text or "no Dell mutation" in text.lower()
        assert "No enrollment" in text or "no enrollment" in text.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 12. No production source modification this phase.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionSourceModified:
    def test_no_src_or_scripts_files_changed_since_phase_entry_commit(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "--", "src/", "scripts/"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        assert changed == []
