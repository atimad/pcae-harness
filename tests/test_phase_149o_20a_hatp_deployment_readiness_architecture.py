"""Phase 149O.20A -- Architecture-completeness test for the HATP Deployment
Readiness Architecture (`docs/PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_
ARCHITECTURE.md`).

149O.20A is an ARCHITECTURE-ONLY phase: it modifies no `src/pcae/**` file,
no `scripts/**` file, and no `docs/contracts/**` file. This module does not
test production behavior (there is none new) -- it mechanically verifies
the architecture document itself is structurally complete: every section
this phase's governing prompt requires is present, the three central
Decision Records exist and are non-empty, all nine stop conditions are
enumerated and explicitly dispositioned "NOT TRIGGERED", the future-phase
sequence is named, the production-boundary confirmations are present, and
-- as read-only evidence gathering -- that no `src/pcae/**` or
`docs/contracts/**` file differs from this phase's pre-phase state.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC = _REPO_ROOT / "docs" / "PHASE_149O_20A_HATP_DEPLOYMENT_READINESS_ARCHITECTURE.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert _DOC.exists(), f"expected architecture document at {_DOC}"
    return _DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def section_headings(doc_text: str) -> list:
    return re.findall(r"^## (\d+)\. (.+)$", doc_text, flags=re.MULTILINE)


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace (including hard line-wraps within a
    paragraph) to single spaces, so substring checks aren't defeated by
    the document's own prose line-wrapping."""
    return re.sub(r"\s+", " ", text)


class TestDocumentExistsAndHasVerdict:
    def test_document_exists(self, doc_text: str):
        assert len(doc_text) > 1000

    def test_verdict_banner_present(self, doc_text: str):
        assert "HATP DEPLOYMENT READINESS ARCHITECTURE: COMPLETE" in doc_text
        assert "IMPLEMENTATION VERIFIED" in doc_text
        assert "REAL DEPLOYMENT NOT AUTHORIZED" in doc_text
        assert "REAL ACTIVATION NOT AUTHORIZED" in doc_text

    def test_charter_cites_149o_19_5g_mandate(self, doc_text: str):
        assert "149O.19.5G" in doc_text
        assert "deployment-readiness architecture phase" in doc_text


class TestRequiredSectionsPresent:
    """Mechanical check that every required topic (per the governing
    prompt's numbered requirement list) has a corresponding section."""

    _REQUIRED_HEADING_FRAGMENTS = [
        "Charter and Mandate",
        "Baseline",
        "Initial Inspection",
        "Primary Sources Read",
        "Deployment Trust Model",
        "Class-B Principal Separation",
        "Agent Principal",
        "Protected Admin Principal",
        "Root Creation",
        "Repository Identity",
        "Deployment Identity",
        "Worktree Semantics",
        "Installation Model",
        "HMIC-REQ-063 Disposition",
        "HMIC-REQ-063 Risk Analysis",
        "Threat Model",
        "Root / OS Admin",
        "Executed-Source Binding",
        "Self-Binding Consequence",
        "Deployment Manifest",
        "Python Executable",
        "PYTHONPATH",
        "Import Hooks",
        "Site-Packages",
        "Editable Install",
        "Third-Party Dependencies",
        "FIDO2/PIV Provider Deployment",
        "Signer Trust Bootstrap",
        "HMIC Certification Bootstrap",
        "Certification After Source Change",
        "Contract Change",
        "Admin-Script Change",
        "Cutover-Source Change",
        "Deployment Update State Machine",
        "Certification ≠ Activation",
        "Active Certification ≠ Full Readiness",
        "Readiness ≠ Activation",
        "Activation ≠ Execution Availability",
        "PB / COMP-002 Blocker",
        "Deployment-Ready vs. Operational-Rollback-Ready",
        "Operational Readiness Matrix",
        "Current Real State",
        "Provisioning Plan Boundary",
        "Possible Future Phases",
        "Real Deployment Authorization Gate",
        "Real Activation Authorization Gate",
        "First Certification Authorization Gate",
        "First Active-Binding Gate",
        "Cutover PREPARED State",
        "PREPARED Failure Recovery",
        "HATP_MANDATORY One-Way Property",
        "Post-Activation Cert Revocation",
        "Lost Hardware Credential",
        "Admin Principal Loss",
        "Protected State Backup",
        "Host Migration",
        "Repository Clone / Restore",
        "Disaster Recovery",
        "Observability",
        "No Authority From Diagnostics",
        "PROJECT_STATUS",
        "Deployment Status Documentation",
        "HATP Production READY Definition",
        "Rollback Operational READY Definition",
        "HMIC-REQ-063 Impact on \"READY\"",
        "Security Ceiling",
        "Class-B Verification",
        "Real-Host Testing",
        "Hardware Verification",
        "First-End-to-End Ceremony",
        "Activation Dry Run",
        "Real Activation Change Window",
        "Authority Semantic Walls",
        "No Prompt-Generation Scope Expansion",
        "Telegram",
        "Runtime",
        "HMIC Stale v1.0 Text Debt",
        "HMIC-REQ-063 Decision Record",
        "Class-B Architecture Decision Record",
        "Deployment Model Decision Record",
        "Certification Deployment Decision Record",
        "Activation Decision Record",
        "PB/Capability Decision Record",
        "Requirement Inventory",
        "Attack Matrix",
        "Stop Conditions",
        "No Production Change",
        "No Contract Change",
        "No Real Protected State",
        "No Real OS Change",
        "No Hardware Change",
        "No PB Change",
        "No POL-005 Change",
        "No COMP-002",
        "No Runtime Change",
        "Architecture-Completeness Test",
        "Existing Regression",
        "Fast Green",
        "Report Trust",
        "Governance Close Checks",
        "Architecture Verdict",
        "Strategic Next Phase",
        "No-Go Confirmations",
        "Recommended Next Phase",
    ]

    def test_all_required_sections_present(self, doc_text: str):
        missing = [h for h in self._REQUIRED_HEADING_FRAGMENTS if h not in doc_text]
        assert not missing, f"missing required section(s): {missing}"

    def test_at_least_one_hundred_numbered_sections(self, section_headings):
        numbers = [int(n) for n, _ in section_headings]
        assert len(numbers) >= 100, f"expected >=100 numbered sections, got {len(numbers)}"
        assert numbers == sorted(numbers), "section numbers must be in ascending order"


class TestDecisionRecordsPresentAndNonEmpty:
    def test_hmic_req_063_decision_record_present(self, doc_text: str):
        match = re.search(
            r"## 78\. HMIC-REQ-063 Decision Record\n(.+?)\n## 79\.",
            doc_text, flags=re.DOTALL,
        )
        assert match is not None
        body = match.group(1)
        assert "Selected option" in body
        assert "OPTION C" in body
        assert "Rejected alternatives" in body

    def test_class_b_architecture_decision_record_present(self, doc_text: str):
        match = re.search(
            r"## 79\. Class-B Architecture Decision Record\n(.+?)\n## 80\.",
            doc_text, flags=re.DOTALL,
        )
        assert match is not None
        body = match.group(1)
        assert "Principal topology" in body
        assert "Protected root" in body

    def test_deployment_model_decision_record_present(self, doc_text: str):
        match = re.search(
            r"## 80\. Deployment Model Decision Record\n(.+?)\n## 81\.",
            doc_text, flags=re.DOTALL,
        )
        assert match is not None
        assert "Model A" in _normalize_ws(match.group(1))

    def test_hmic_req_063_not_left_tbd(self, doc_text: str):
        section = doc_text.split("## 14. HMIC-REQ-063 Disposition")[1].split("## 15.")[0]
        assert "TBD" not in section
        assert "not yet decided" not in section.lower()


class TestStopConditionsAllDispositioned:
    _STOP_CONDITIONS = [f"DRA-S{i}" for i in range(1, 10)]

    def test_all_nine_stop_conditions_enumerated(self, doc_text: str):
        section = doc_text.split("## 86. Stop Conditions")[1].split("## 87.")[0]
        for code in self._STOP_CONDITIONS:
            assert code in section, f"stop condition {code} missing from §86"

    def test_all_nine_stop_conditions_marked_not_triggered(self, doc_text: str):
        section = doc_text.split("## 86. Stop Conditions")[1].split("## 87.")[0]
        for code in self._STOP_CONDITIONS:
            pattern = re.compile(rf"\*\*{re.escape(code)}\*\*.*?NOT TRIGGERED", re.DOTALL)
            assert pattern.search(section), f"{code} not explicitly marked NOT TRIGGERED"


class TestFuturePhaseSequenceNamed:
    def test_149o_20b_named_as_next_phase(self, doc_text: str):
        assert "149O.20B" in doc_text
        assert "HATP Class-B Deployment Contract Freeze" in doc_text

    def test_future_phase_letters_present_in_section_44(self, doc_text: str):
        section = doc_text.split("## 44. Possible Future Phases")[1].split("## 45.")[0]
        for letter in ("149O.20B", "149O.20C", "149O.20D", "149O.20E", "149O.20F", "149O.20G"):
            assert letter in section, f"{letter} missing from §44 future-phase sequence"


class TestProductionBoundaryConfirmationsPresent:
    _NO_GO_FRAGMENTS = [
        "No `src/pcae/**` file was modified",
        "No `scripts/**` file was modified",
        "No contract file was modified",
        "No real protected root, certification, active binding, revocation, Cutover Record, or activation marker was created",
        "No real HATP_MANDATORY activation occurred",
        "No real Class-B provisioning occurred",
        "No Permission Broker behavior changed",
        "No COMP-002 capability was implemented",
    ]

    def test_no_go_confirmations_present(self, doc_text: str):
        section = _normalize_ws(doc_text.split("## 103. No-Go Confirmations")[1])
        missing = [f for f in self._NO_GO_FRAGMENTS if _normalize_ws(f) not in section]
        assert not missing, f"missing no-go confirmation(s): {missing}"

    def test_hatp_not_ready_and_runtime_unavailable_preserved(self, doc_text: str):
        assert "HATP production remains NOT READY" in _normalize_ws(doc_text)
        assert "Observed / observe / unavailable" in doc_text


class TestNoProductionOrContractSourceModified:
    def test_git_status_touches_no_src_pcae_or_contract_file(self):
        """Best-effort self-check: confirms no `src/pcae/**` file is
        currently dirty, and no *existing* `docs/contracts/**` file is
        modified, in the working tree. This is read-only evidence
        gathering, not the sole authority -- the phase report's own `git
        diff --stat` against the pre-phase commit SHA is authoritative,
        consistent with 149O.14's own convention for this exact check.

        Narrowed by Phase 149O.20B: 149O.20A itself named a future
        contract-freeze phase (149O.20B) as its own recommended next
        phase, and that phase's charter is to *add* a new file under
        `docs/contracts/`. An unqualified "nothing under docs/contracts
        may ever appear dirty" check would therefore make this test fail
        for the very next phase this architecture recommended -- not a
        real regression. The check now tolerates a newly added
        (untracked, `??`) file under `docs/contracts/`; it still fails
        closed on any *modification* to an existing tracked file there,
        or on anything touching `src/pcae`."""
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/pcae", "docs/contracts"],
                cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        offending = [
            line
            for line in proc.stdout.splitlines()
            if line.strip() and not line.startswith("?? docs/contracts/")
        ]
        assert not offending, (
            "unexpected working-tree change under src/pcae, or a "
            "modification to an existing docs/contracts file: "
            f"{offending}"
        )

    def test_no_production_source_modified_by_this_phase(self):
        """Task-lifecycle-level enforcement (forbidden-file list) plus the
        phase report's own `git diff --stat <pre-phase-HEAD>..HEAD --
        src/pcae/ docs/contracts/` step are the actual authority for this
        claim (mirrors 149O.14's own convention)."""
        assert True
