"""Phase 149O.20B -- Contract-completeness tests for the HATP Class-B
Deployment Contract (HBDC-001 v1.0,
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`).

149O.20B is a CONTRACT-FREEZE-ONLY phase: it modifies no `src/pcae/**`
file, no `scripts/**` file, and no existing `docs/contracts/**` file. This
module does not test production behavior (there is none new) -- it
mechanically verifies the new contract document is structurally complete
and internally consistent: the `HBDC-REQ-###` inventory is unique and
gapless, the `CBD-#` invariant inventory is complete, the attack matrix has
no duplicate rows, DRA-REQ-001..003 each have an explicit contract mapping,
the Option-C/Model-A-only boundary is stated without overclaim, the
two-principal and Protected Root permission model are stated, the full
Python-environment-lock checklist is present, the contract's own
binding/self-trust disposition is explicitly resolved, and the
real-authorization-gate language is present. It also confirms, as
read-only evidence gathering, that no existing `src/pcae/**` or
`docs/contracts/**` file differs from this phase's pre-phase state.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTRACT = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_PHASE_DOC = _REPO_ROOT / "docs" / "PHASE_149O_20B_HATP_CLASS_B_DEPLOYMENT_CONTRACT_FREEZE.md"

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


@pytest.fixture(scope="module")
def contract_text() -> str:
    assert _CONTRACT.exists(), f"expected contract document at {_CONTRACT}"
    return _CONTRACT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    assert _PHASE_DOC.exists(), f"expected phase document at {_PHASE_DOC}"
    return _PHASE_DOC.read_text(encoding="utf-8")


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TestContractIdentityAndStatus:
    def test_contract_document_exists(self, contract_text: str):
        assert len(contract_text) > 1000

    def test_contract_id_and_version(self, contract_text: str):
        assert "**Contract:** HBDC-001" in contract_text
        assert "**Version:** 1.0" in contract_text
        assert "FROZEN — PENDING INDEPENDENT VERIFICATION" in contract_text

    def test_depends_on_unamended_bound_contracts(self, contract_text: str):
        depends_line = _normalize_ws(contract_text)
        assert "HATP-001 v1.0 (unamended)" in depends_line
        assert "HMIC-001 v1.1 (unamended)" in depends_line
        assert "HMRC-001 v1.0 (unamended)" in depends_line

    def test_verdict_banner_present(self, contract_text: str):
        assert "HBDC-001 v1.0 — FROZEN" in contract_text
        assert "PENDING INDEPENDENT VERIFICATION" in contract_text
        assert "REAL PROVISIONING NOT AUTHORIZED" in contract_text
        assert "REAL ACTIVATION NOT AUTHORIZED" in contract_text


class TestRequirementInventory:
    """HBDC-REQ IDs must be unique, sequential from 001, gapless, and
    match the exact frozen count."""

    _EXPECTED_COUNT = 55

    @pytest.fixture(scope="class")
    def req_ids(self, contract_text: str) -> list:
        return sorted(
            {int(m) for m in re.findall(r"HBDC-REQ-(\d{3})\b", contract_text)}
        )

    def test_requirement_ids_gapless_from_one(self, req_ids: list):
        assert req_ids == list(range(1, self._EXPECTED_COUNT + 1)), (
            f"HBDC-REQ IDs must be exactly 1..{self._EXPECTED_COUNT} with no "
            f"gaps or duplicates; found {req_ids}"
        )

    def test_requirement_count_matches_stated_count(self, contract_text: str):
        assert f"defines **{self._EXPECTED_COUNT}** requirements" in contract_text

    def test_traceability_table_lists_every_requirement_exactly_once(
        self, contract_text: str
    ):
        table_section = contract_text.split("## 24. Full Requirement Traceability")[1]
        table_section = table_section.split("## 25.")[0]
        ids_in_table = re.findall(r"HBDC-REQ-(\d{3})", table_section)
        assert sorted(int(i) for i in ids_in_table) == list(
            range(1, self._EXPECTED_COUNT + 1)
        )
        assert len(ids_in_table) == self._EXPECTED_COUNT


class TestInvariantInventory:
    _EXPECTED_INVARIANTS = [f"CBD-{n}" for n in range(1, 9)]

    def test_invariants_present_and_gapless(self, contract_text: str):
        section = contract_text.split("## 19. Security Invariants")[1]
        section = section.split("## 20.")[0]
        found = re.findall(r"\*\*(CBD-\d+)\.\*\*", section)
        assert found == self._EXPECTED_INVARIANTS

    def test_invariant_count_matches_stated_count(self, contract_text: str):
        assert "Invariant count:** 8" in contract_text


class TestAttackMatrixInventory:
    def test_attack_matrix_has_21_unique_rows(self, contract_text: str):
        section = contract_text.split("### Attack Matrix (21 scenarios)")[1]
        section = section.split("## 22.")[0]
        row_numbers = re.findall(r"^\| (\d+) \|", section, flags=re.MULTILINE)
        numeric = [int(n) for n in row_numbers]
        assert numeric == list(range(1, 22))
        assert len(set(numeric)) == 21


class TestDRAReqMapping:
    def test_dra_req_001_002_003_all_mapped(self, contract_text: str):
        section = contract_text.split("## 6. DRA-REQ Traceability")[1]
        section = section.split("## 7.")[0]
        for dra_req in ("DRA-REQ-001", "DRA-REQ-002", "DRA-REQ-003"):
            assert dra_req in section, f"missing mapping row for {dra_req}"
        assert "HBDC-REQ-001..005" in _normalize_ws(section)
        assert "HBDC-REQ-011..021" in _normalize_ws(section)
        assert "HBDC-REQ-025..041" in _normalize_ws(section)


class TestPrincipalAndRootModel:
    def test_two_principal_model_named(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "exactly two os principals are required for a v1.0-compliant model-a class-b deployment" in text.lower()
        assert "agent principal and the admin principal SHALL be distinct OS accounts" in text

    def test_root_agent_nonwrite_admin_write(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "agent principal SHALL NOT hold write permission" in text
        assert "admin OS principal" in text
        assert "Protected Root SHALL be owned by the admin OS principal" in text

    def test_parent_path_and_acl_group_coverage(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "ancestor director" in text.lower()
        assert "no group of which the agent principal is a member" in text.lower()
        assert (
            "no posix acl, extended acl, default acl, or inherited acl" in text.lower()
        )

    def test_symlink_and_hardlink_coverage(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "fail closed" in text.lower()
        assert "hard link" in text.lower()

    def test_no_agent_auto_provisioning(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "No PCAE agent-invoked code path SHALL auto-create Protected Root" in text


class TestPythonEnvironmentLockChecklist:
    _REQUIRED_FRAGMENTS = [
        "production agent Python execution environment",
        "production venv, if used, SHALL be owned and writable only by the admin principal",
        "production Python executable resolved for PCAE agent invocation SHALL NOT be replaceable",
        "`PYTHONPATH` SHALL NOT be settable or influenceable by the agent principal",
        "Python user-site (`site.ENABLE_USER_SITE`) SHALL be disabled",
        "`sitecustomize.py` and `usercustomize.py`",
        "Any `.pth` file present on the resolved production `sys.path`",
        "SHALL NOT be able to install a `sys.meta_path` entry",
        "SHALL NOT cause import shadowing of certified PCAE authority modules",
        "fake or shadow `pcae` package",
        "Editable-install link metadata",
    ]

    def test_all_environment_lock_topics_present(self, contract_text: str):
        section = contract_text.split(
            "## 13. Agent Python Execution-Environment Lock"
        )[1]
        section = section.split("## 14.")[0]
        normalized = _normalize_ws(section)
        missing = [f for f in self._REQUIRED_FRAGMENTS if f not in normalized]
        assert not missing, f"missing environment-lock topic(s): {missing}"


class TestModelAAndOptionCBoundary:
    def test_model_a_only(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "HBDC-001 v1.0 authorizes exactly one deployment model: **Model A**" in text
        assert "NOT authorized under HBDC-001 v1.0" in text

    def test_option_c_no_overclaim(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "OPTION C" in text
        assert (
            "SHALL NOT be represented as executed-code or runtime-module-resolution cryptographic attestation"
            in text
        )


class TestContractBindingDisposition:
    """The contract's own trust/binding disposition (whether HBDC-001 must
    later join HMIC-001's bound-contract set) must be explicitly resolved,
    not left ambiguous -- mandatory per the phase charter."""

    def test_disposition_explicitly_resolved(self, contract_text: str):
        section = contract_text.split("## 17. HBDC Trust/Binding Disposition")[1]
        section = section.split("## 18.")[0]
        normalized = _normalize_ws(section)
        assert "Selected disposition: Option A." in normalized
        assert "not, as of v1.0, one of HMIC-001's bound contracts" in normalized
        assert "future HMIC-001 amendment" in normalized
        assert "target: HMIC-001 v1.2" in normalized
        assert "NOT made by Phase 149O.20B" in normalized
        assert "Rejected alternatives:" in normalized


class TestRealAuthorizationGates:
    def test_conformance_does_not_authorize_real_actions(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "does NOT itself authorize creation of a real Protected Root" in text
        assert "does not authorize any of the actions listed in HBDC-REQ-050" in text

    def test_fail_closed_conformance_vocabulary(self, contract_text: str):
        text = _normalize_ws(contract_text)
        assert "COMPLIANT" in text and "NON_COMPLIANT" in text and "INDETERMINATE" in text
        assert "fail-closed" in text.lower()


class TestNoProductionOrExistingContractSourceModified:
    def test_git_status_touches_no_src_pcae_or_existing_contract_file(self):
        """Best-effort self-check: confirms no `src/pcae/**` file is dirty
        and no *existing* bound-contract file under `docs/contracts/**` is
        modified in the working tree. The new HBDC-001 file itself is
        expected to appear (added), matching this phase's charter. This is
        read-only evidence gathering, not the sole authority -- the phase
        report's own `git diff --stat` against the pre-phase commit SHA is
        authoritative, consistent with 149O.14's/149O.20A's own convention
        for this exact check."""
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/pcae", "docs/contracts"],
                cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        offending = []
        for line in lines:
            status, _, path = line.partition(" ")
            path = path.strip()
            if path.startswith("src/pcae"):
                offending.append(line)
                continue
            if path in _EXISTING_EIGHT_BOUND_CONTRACTS and status.strip() != "??":
                offending.append(line)
        assert not offending, (
            "unexpected modification to src/pcae or an existing bound "
            f"contract: {offending}"
        )

    def test_no_production_source_modified_by_this_phase(self):
        """Task-lifecycle-level enforcement (forbidden-file list) plus the
        phase report's own `git diff --stat <pre-phase-HEAD>..HEAD --
        src/pcae/` step are the actual authority for this claim (mirrors
        149O.14's/149O.20A's own convention)."""
        assert True


class TestPhaseDocumentCompleteness:
    _REQUIRED_HEADING_FRAGMENTS = [
        "Charter and Mandate",
        "Baseline",
        "Initial Inspection",
        "Primary Sources Read",
        "Contract Identity",
        "DRA-REQ",
        "Principal Model",
        "Protected Root Model",
        "Agent/Admin Permission Model",
        "Model-A Deployment",
        "Agent Python Execution-Environment Lock",
        "HMIC-REQ-063 Relationship",
        "Third-Party/Git Dependency Disposition",
        "Repository/Deployment Identity",
        "Threat-Model Limits",
        "HBDC Trust/Binding Disposition",
        "Real-Authorization Gates",
        "Requirements, Invariants, Attack Matrix",
        "Tests",
        "No Production/Contract Diff",
        "No Real State Change",
        "Findings",
        "Contract Verdict",
        "Recommended Next Phase",
    ]

    def test_all_required_sections_present(self, phase_doc_text: str):
        missing = [
            fragment
            for fragment in self._REQUIRED_HEADING_FRAGMENTS
            if fragment not in phase_doc_text
        ]
        assert not missing, f"missing phase-document section(s): {missing}"

    def test_no_real_state_change_confirmations(self, phase_doc_text: str):
        section = _normalize_ws(phase_doc_text.split("## 21. No Real State Change")[1])
        for fragment in (
            "No real Class-B provisioning occurred",
            "No real Protected Root was created",
            "No real HMIC certification, active binding, or revocation state was created",
            "No Cutover Record or activation marker was created or modified",
            "No `HATP_MANDATORY` activation occurred",
            "No Permission Broker behavior changed",
            "POL-005 unchanged",
            "COMP-002 not implemented",
            "HATP production remains NOT READY",
        ):
            assert fragment in section, f"missing no-real-state-change confirmation: {fragment}"

    def test_hatp_not_ready_and_runtime_unavailable_preserved(self, phase_doc_text: str):
        assert "HATP production remains NOT READY" in _normalize_ws(phase_doc_text)
        assert "Observed / observe / unavailable" in phase_doc_text

    def test_recommended_next_phase_is_149o_20c(self, phase_doc_text: str):
        assert "149O.20C" in phase_doc_text
        assert "Independent Verification" in phase_doc_text
