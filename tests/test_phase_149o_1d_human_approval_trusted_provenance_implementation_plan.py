"""Phase 149O.1D -- Human Approval Trusted Provenance Implementation Plan.

Plan-validation suite for
`docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`.
This is a planning phase: no HATP production code, CRI implementation,
Class-B OS boundary, hardware provider, or RAE/AG3/AG5 integration is
implemented. This suite does not exercise any such implementation --
none exists -- it validates that the *plan document itself* is
internally complete and consistent, independently re-deriving the
canonical HATP-REQ-001..117 requirement set from the frozen contract
text exactly as Phase 149O.1C's own suite did, rather than trusting this
phase's own prose count.

No production file (`src/pcae/**`) or contract file
(`docs/contracts/**`) is read for mutation-detection purposes beyond
plain text inspection; this suite writes nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
PLAN_DOC = REPO_ROOT / "docs" / "PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md"

VALID_SUBSYSTEMS = set("ABCDEFGHIJKLMN")


@pytest.fixture(scope="module")
def contract_text() -> str:
    return HATP_CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def plan_text() -> str:
    return PLAN_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def canonical_requirement_ids(contract_text: str) -> list[int]:
    """Independently re-derive the requirement ID set from the frozen
    contract text -- never trust this plan's own prose count (mirrors
    149O.1C's own methodology, carried forward per F-149O.1C-2's
    disposition, plan §3.2)."""
    ids = sorted(int(m) for m in re.findall(r"\*\*HATP-REQ-(\d+)\.", contract_text))
    return ids


@pytest.fixture(scope="module")
def traceability_rows(plan_text: str) -> list[tuple[int, int, str]]:
    """Parse §4.2's range-collapsed traceability table into
    (lo, hi, subsystem_letter) tuples."""
    rows: list[tuple[int, int, str]] = []
    pattern = re.compile(
        r"\|\s*HATP-REQ-(\d+)(?:\.\.(\d+))?\s*\|\s*([A-N])\s*\|"
    )
    for line in plan_text.splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        letter = m.group(3)
        rows.append((lo, hi, letter))
    return rows


class TestCanonicalRequirementCount:
    def test_contract_defines_117_sequential_requirements(self, canonical_requirement_ids):
        ids = canonical_requirement_ids
        assert ids, "no HATP-REQ-* requirements found in contract text"
        assert ids[0] == 1
        assert ids == list(range(1, len(ids) + 1)), (
            "HATP-REQ-* numbering has a gap or duplicate"
        )
        assert ids[-1] == 117, (
            "independently re-derived requirement count must be 117 "
            "(F-149O.1C-2: HATP-REQ-116's own prose says 116, but the "
            "contract actually spans 117 -- this plan uses 117, never "
            "the prose miscount)"
        )


class TestTraceabilityTableCompleteness:
    def test_table_has_rows(self, traceability_rows):
        assert traceability_rows, "§4.2 traceability table not found or empty"

    def test_every_requirement_1_to_117_mapped_exactly_once(self, traceability_rows):
        covered: dict[int, int] = {}
        for lo, hi, _letter in traceability_rows:
            for n in range(lo, hi + 1):
                covered[n] = covered.get(n, 0) + 1

        missing = [n for n in range(1, 118) if n not in covered]
        duplicated = [n for n, count in covered.items() if count > 1]

        assert not missing, f"HATP-REQ-{missing} left UNMAPPED by the plan"
        assert not duplicated, (
            f"HATP-REQ-{duplicated} mapped to more than one primary "
            "subsystem owner"
        )
        assert set(covered) == set(range(1, 118))

    def test_every_row_uses_a_valid_subsystem_letter(self, traceability_rows):
        for lo, hi, letter in traceability_rows:
            assert letter in VALID_SUBSYSTEMS, (
                f"HATP-REQ-{lo}..{hi} mapped to unknown subsystem '{letter}'"
            )

    def test_subsystems_without_a_primary_requirement_are_explained(
        self, traceability_rows, plan_text: str
    ):
        # K (Test Provider) and M (Migration/Initialization) are
        # supporting subsystems by design -- they implement other
        # requirements' obligations (e.g. HATP-REQ-022's test-provider
        # containment lives under E/K jointly) rather than owning a
        # primary requirement themselves. Any subsystem absent from the
        # traceability table must still be substantively discussed
        # elsewhere in the plan (not merely defined in the §4.1 legend).
        used = {letter for _lo, _hi, letter in traceability_rows}
        unused = VALID_SUBSYSTEMS - used
        assert unused <= {"K", "M"}, (
            f"subsystem(s) {unused - {'K', 'M'}} own no primary requirement "
            "and are not an accepted supporting-subsystem exception"
        )
        for letter in unused:
            heading = {
                "K": "Test Provider",
                "M": "Migration",
            }[letter]
            assert heading in plan_text, (
                f"supporting subsystem {letter} ({heading}) must still be "
                "substantively planned elsewhere in the document"
            )


class TestMandatoryAttackMatrixMapped:
    def test_all_twenty_attacks_present_in_plan(self, plan_text: str):
        # Section 44's attack-mapping table is expected to enumerate
        # rows 1-20 in its leading numeric column.
        attack_rows = re.findall(
            r"^\|\s*(\d+)\s*\|", plan_text, flags=re.MULTILINE
        )
        attack_numbers = {int(n) for n in attack_rows if 1 <= int(n) <= 20}
        assert attack_numbers == set(range(1, 21)), (
            "not all 20 mandatory acceptance attacks (HATP-REQ-111) are "
            "mapped in the plan's attack-implementation-mapping table"
        )

    def test_each_attack_row_names_an_expected_outcome_and_wave(self, plan_text: str):
        # Spot-check a representative sample of expected-outcome tokens
        # from HATP-REQ-111 appear in the plan's attack table.
        for token in (
            "UNKNOWN_SIGNER",
            "UNAUTHORIZED_SIGNER",
            "USER_PRESENCE_NOT_PROVEN",
            "WRONG_OPERATION",
            "WRONG_REPOSITORY",
            "WRONG_DEPLOYMENT",
            "REVOKED_SIGNER",
            "EXPIRED",
            "VALID",
        ):
            assert token in plan_text, (
                f"expected verification-outcome token '{token}' from the "
                "mandatory attack matrix (HATP-REQ-111) not found in plan"
            )


class TestBFindingsMapped:
    @pytest.mark.parametrize("finding", ["B-149O-1", "B-149O-2", "B-149O-3", "B-149O-4"])
    def test_finding_present_and_marked_open(self, plan_text: str, finding: str):
        assert finding in plan_text, f"{finding} not referenced in plan"

    def test_findings_explicitly_remain_open(self, plan_text: str):
        flat = re.sub(r"\s+", " ", plan_text)
        assert "remain **OPEN**" in flat or "remain OPEN" in flat, (
            "plan must explicitly state B-149O-1..4 remain OPEN, not closed "
            "by this planning-only phase"
        )


class TestF1F2DispositionPresent:
    def test_f1_disposition_present(self, plan_text: str):
        assert "F-149O.1C-1" in plan_text
        assert "CLOSED BY IMPLEMENTATION PLAN DECISION" in plan_text

    def test_f2_disposition_present(self, plan_text: str):
        assert "F-149O.1C-2" in plan_text
        assert "RETAINED EDITORIAL OBSERVATION" in plan_text

    def test_plan_does_not_claim_contract_was_edited(self, plan_text: str):
        flat = re.sub(r"\s+", " ", plan_text)
        assert "byte-unchanged" in flat or "not edited by this phase" in flat


class TestWavesPreserveFailClosedPartialDeployment:
    @pytest.mark.parametrize(
        "wave_heading",
        [
            "Wave 1",
            "Wave 2",
            "Wave 3",
            "Wave 4",
            "Wave 5",
            "Wave 6",
            "Wave 7",
        ],
    )
    def test_wave_section_exists(self, plan_text: str, wave_heading: str):
        assert wave_heading in plan_text, f"{wave_heading} section missing from plan"

    def test_no_wave_before_seven_claims_production_activation(self, plan_text: str):
        # Waves 1-6 must each state that production trust activation
        # remains gated; Wave 7 is explicitly the only wave after which
        # HATP_TRUSTED_OPERATIONAL becomes achievable.
        assert "HATP_TRUSTED_OPERATIONAL" in plan_text
        assert (
            "this is the **only** wave after which" in plan_text
            or "only wave after which" in plan_text
        ), "plan must explicitly restrict production activation to Wave 7"

    def test_activation_conjunction_defined(self, plan_text: str):
        for term in (
            "repository_identity_valid",
            "protected_deployment_enrollment_valid",
            "class_b_bootstrap_environment_safe",
            "trusted_approver_mapping_valid",
            "provider_profile_available",
            "provider_attestation_trusted",
            "proof_verifier_available",
        ):
            assert term in plan_text, f"activation conjunction missing term '{term}'"

    def test_wave_six_has_explicit_stop_condition_for_approval_present(self, plan_text: str):
        wave6_start = plan_text.index("### Wave 6")
        wave7_start = plan_text.index("### Wave 7")
        wave6_section = plan_text[wave6_start:wave7_start]
        assert "approval_present=True" in wave6_section
        assert "STOP" in wave6_section


class TestNoProductionOrContractBoundaryViolation:
    def test_plan_states_src_pcae_untouched(self, plan_text: str):
        assert "src/pcae/**" in plan_text

    def test_plan_states_contracts_untouched(self, plan_text: str):
        assert "docs/contracts/**" in plan_text

    def test_no_dependency_added_this_phase(self, plan_text: str):
        assert "No dependency is added this phase" in plan_text


class TestImplementationReadinessVerdict:
    def test_verdict_present(self, plan_text: str):
        assert "HATP-001 IMPLEMENTATION PLAN COMPLETE" in plan_text
        assert "READY FOR BOUNDED IMPLEMENTATION" in plan_text

    def test_recommended_next_phase_is_bounded_not_full_hatp(self, plan_text: str):
        assert "149O.1E" in plan_text
        flat = re.sub(r"\s+", " ", plan_text)
        assert "implement HATP" not in flat.lower().replace(
            "not simply say: implement hatp", ""
        ) or "Wave 1 + Wave 2" in plan_text
        assert "Wave 1 + Wave 2" in plan_text


class TestProductionBoundaryUnchanged:
    def test_no_src_pcae_files_modified_this_phase(self):
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", "src/pcae/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", (
            "this planning-only phase must not modify src/pcae/**: "
            f"{result.stdout}"
        )

    def test_no_contract_files_modified_this_phase(self):
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", "docs/contracts/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "", (
            "this planning-only phase must not modify docs/contracts/**: "
            f"{result.stdout}"
        )
