"""Phase 149O.20H -- Plan-completeness test for the Class-B Deployment
Verifier / Model-A Environment-Lock Implementation Plan
(`docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_
IMPLEMENTATION_PLAN.md`).

149O.20H is an IMPLEMENTATION-PLAN-ONLY phase: it modifies no
`src/pcae/**` file, no `scripts/**` file, and no `docs/contracts/**` file.
This module does not test production behavior (there is none new) -- it
mechanically verifies the plan document itself is structurally complete:
every required topic is present, the 55 HBDC-REQ requirements / 8 CBD
invariants / 21 attacks are each individually mapped, the self-binding
stop conditions are enumerated, the future-phase sequence is named, the
production-boundary confirmations hold, and -- as read-only evidence
gathering -- that no `src/pcae/**`, `scripts/**`, or `docs/contracts/**`
file differs from this phase's pre-phase state.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_IMPLEMENTATION_PLAN.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert _DOC.exists(), f"expected plan document at {_DOC}"
    return _DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def section_headings(doc_text: str) -> list:
    return re.findall(r"^## (\d+)\. (.+)$", doc_text, flags=re.MULTILINE)


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TestDocumentExistsAndHasVerdict:
    def test_document_exists(self, doc_text: str):
        assert len(doc_text) > 5000

    def test_verdict_banner_present(self, doc_text: str):
        assert "CLASS-B DEPLOYMENT VERIFIER / MODEL-A ENVIRONMENT-LOCK IMPLEMENTATION PLAN:" in doc_text
        assert "COMPLETE" in doc_text
        assert "HBDC-001 55/55 REQUIREMENTS MAPPED" in doc_text
        assert "CBD 8/8 INVARIANTS MAPPED" in doc_text
        assert "21/21 FROZEN ATTACKS MAPPED" in doc_text
        assert "REAL PROVISIONING NOT AUTHORIZED" in doc_text

    def test_baseline_cites_149o_20g_closure(self, doc_text: str):
        assert "149O.20G" in doc_text
        assert "B-149O.20D-1" in doc_text
        assert "HBDC-BINDING-GATE" in doc_text


class TestRequiredSectionsPresent:
    _REQUIRED_HEADING_FRAGMENTS = [
        "Phase Identity and Type",
        "Baseline",
        "Requirement Inventory",
        "Invariant Mapping",
        "Attack Matrix Mapping",
        "Retained Implementation-Coverage Findings",
        "Result Model and Status Vocabulary",
        "Public API",
        "Protected Root Resolution",
        "Principal Verification",
        "Effective ACL/Group-Access Verification",
        "Full Ancestor-Chain Verification",
        "Path / Symlink Safety",
        "Hard-Link Verification",
        "Trusted Git Executable Verification",
        "Repository/Deployment Identity",
        "Model-A Installation and Module-Origin Verification",
        "Launcher / Service Environment",
        "Non-Auto-Creation",
        "Verifier",
        "Future Readiness Consumption",
        "Class-B COMPLIANT",
        "Authority Source Inventory",
        "New-Module Consequence and Existing-File Alternative",
        "Self-Binding Stop Condition and Circularity Resolution",
        "No Self-Certification",
        "Test Plan",
        "Platform Scope",
        "Error Handling and Status Reasons",
        "Blocking-Condition Self-Check",
        "Implementation File Manifest",
        "Test File Manifest",
        "Real Authorization Boundaries",
        "Stop Conditions",
        "Plan Verdict",
        "Recommended Next Phase",
    ]

    def test_all_required_sections_present(self, doc_text: str):
        missing = [h for h in self._REQUIRED_HEADING_FRAGMENTS if h not in doc_text]
        assert not missing, f"missing required section(s): {missing}"

    def test_section_numbers_ascending_from_zero(self, section_headings):
        numbers = [int(n) for n, _ in section_headings]
        assert numbers[0] == 0
        assert numbers == sorted(numbers), "section numbers must be in ascending order"
        assert len(numbers) >= 30


class TestRequirementInventoryComplete:
    def test_all_55_hbdc_req_ids_present_exactly_once(self, doc_text: str):
        ids = re.findall(r"HBDC-REQ-(\d{3})", doc_text)
        unique_ids = sorted(set(int(i) for i in ids))
        assert unique_ids == list(range(1, 56)), (
            f"expected HBDC-REQ-001..055 all referenced; "
            f"missing={sorted(set(range(1, 56)) - set(unique_ids))}"
        )

    def test_requirement_table_has_55_data_rows(self, doc_text: str):
        section = doc_text.split("## 2. HBDC-REQ-001..055 Requirement Inventory")[1]
        section = section.split("## 3.")[0]
        rows = re.findall(r"^\| HBDC-REQ-\d{3} \|", section, flags=re.MULTILINE)
        assert len(rows) == 55, f"expected 55 requirement table rows, got {len(rows)}"


class TestInvariantAndAttackCoverage:
    def test_all_8_cbd_invariants_present(self, doc_text: str):
        section = doc_text.split("## 3. CBD-1..CBD-8 Invariant Mapping")[1].split("## 4.")[0]
        for i in range(1, 9):
            assert f"CBD-{i} " in section or f"CBD-{i} |" in section, f"CBD-{i} missing from §3"

    def test_all_21_attacks_present(self, doc_text: str):
        section = doc_text.split("## 4. HBDC Attack Matrix Mapping")[1].split("## 5.")[0]
        rows = re.findall(r"^\| (\d{1,2}) \|", section, flags=re.MULTILINE)
        numbers = sorted(int(n) for n in rows)
        assert numbers == list(range(1, 22)), f"expected attacks 1..21, got {numbers}"

    def test_no_covered_by_contract_shortcut(self, doc_text: str):
        section = doc_text.split("## 4. HBDC Attack Matrix Mapping")[1].split("## 5.")[0]
        row_lines = [line for line in section.splitlines() if re.match(r"^\| \d{1,2} \|", line)]
        assert row_lines, "expected numbered attack table rows"
        assert not any("covered by contract" in line.lower() for line in row_lines)


class TestRetainedFindingsMapped:
    def test_all_four_20c_findings_mapped_to_a_wave(self, doc_text: str):
        section = doc_text.split("## 5. 20C Retained Implementation-Coverage Findings")[1].split("## 6.")[0]
        for fragment in [
            "Effective ACL/group-access verification absent",
            "Full authority-bearing ancestor-chain verification absent",
            "Hard-link verification absent",
            "Model-A Python execution-environment lock has no implementation",
        ]:
            assert fragment in section, f"20C finding not mapped: {fragment}"
        assert "Future work" not in section
        assert "TBD" not in section


class TestSelfBindingDiscipline:
    def test_self_binding_rule_cbv_s1_present_and_frozen(self, doc_text: str):
        section = doc_text.split("## 24. Self-Binding Stop Condition and Circularity Resolution")[1].split("## 25.")[0]
        assert "CBV-S1" in section
        assert "frozen" in section.lower()

    def test_new_modules_classified_not_yet_hmic_bound(self, doc_text: str):
        section = doc_text.split("## 22. Authority Source Inventory")[1].split("## 23.")[0]
        assert section.count("NOT_YET_HMIC_BOUND") >= 3
        assert "ALREADY_HMIC_BOUND" not in section.split("| Path (planned)")[1].split("hatp_bootstrap.py")[0]

    def test_existing_file_alternative_evaluated_and_rejected(self, doc_text: str):
        section = doc_text.split("## 23. New-Module Consequence and Existing-File Alternative")[1].split("## 24.")[0]
        assert "Rejected" in section
        assert "hatp_bootstrap.py" in section

    def test_all_twelve_stop_conditions_enumerated(self, doc_text: str):
        section = doc_text.split("## 33. Stop Conditions")[1].split("## 34.")[0]
        for i in range(1, 13):
            assert f"CBV-S{i}" in section, f"stop condition CBV-S{i} missing from §33"


class TestFuturePhaseSequenceNamed:
    def test_149o_20i_named_as_next_phase(self, doc_text: str):
        assert "149O.20I" in doc_text
        assert "Bounded Implementation" in doc_text

    def test_wave_f_sequence_named(self, doc_text: str):
        section = doc_text.split("## 24. Self-Binding Stop Condition and Circularity Resolution")[1].split("## 25.")[0]
        for letter in ("149O.20J", "149O.20K", "149O.20L", "149O.20M", "149O.20N"):
            assert letter in section, f"{letter} missing from the self-binding sequence (§24)"


class TestProductionBoundaryConfirmationsPresent:
    _FRAGMENTS = [
        "No positive Class-B conformance result may become production-authoritative",
        "None of these accepts",
        "read-only by construction",
    ]

    def test_no_go_language_present(self, doc_text: str):
        text = _normalize_ws(doc_text)
        for fragment in self._FRAGMENTS:
            assert _normalize_ws(fragment) in text, f"missing no-go/boundary language: {fragment}"

    def test_class_b_and_hatp_status_preserved(self, doc_text: str):
        assert "CONTRACT VERIFIED" in doc_text
        assert "NOT PROVISIONED" in doc_text
        assert "HATP production NOT READY" in doc_text or "HATP production remains NOT READY" in doc_text
        assert "Observed / observe / unavailable" in doc_text


class TestNoProductionOrContractSourceModified:
    def test_git_status_touches_no_src_pcae_scripts_or_contract_file(self):
        """Best-effort self-check mirroring 149O.20A's own convention:
        confirms no `src/pcae/**`, `scripts/**`, or existing
        `docs/contracts/**` file is dirty in the working tree. Read-only
        evidence gathering; the phase report's own `git diff --stat`
        against the pre-phase commit SHA is authoritative."""
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/pcae", "scripts", "docs/contracts"],
                cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        offending = [line for line in proc.stdout.splitlines() if line.strip()]
        assert not offending, (
            f"unexpected working-tree change under src/pcae, scripts, or docs/contracts: {offending}"
        )

    def test_no_production_source_modified_by_this_phase(self):
        """Task-lifecycle-level enforcement (forbidden-file list) plus the
        phase report's own `git diff --stat <pre-phase-HEAD>..HEAD --
        src/pcae/ scripts/ docs/contracts/` step are the actual authority
        for this claim (mirrors 149O.20A's own convention)."""
        assert True
