"""Phase 149O.20L.6 — Class-B Provisioning Authorization Record Capture.

Governance-record-capture/contract-only test coverage. No production host
mutation is performed or tested here. This phase's substantive output is
a published CHGR (Canonical Human Governance Record) recording the human
governance authority's explicit APPROVE election on the Boundary-P
provisioning-authorization proposition; these tests verify the shape and
content of that record and its own inspect/verify results, and that no
`src/pcae/**`/`docs/contracts/**`/`scripts/**` file was touched.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PCAE_EXECUTABLE = shutil.which("pcae")
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_6_CLASS_B_PROVISIONING_AUTHORIZATION_RECORD_CAPTURE.md"
)
CHGR_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / "chgr-d4343fa51b9743f3abaeb87a881a78b1.json"
)
CHGR_CONF_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / "chgrconf-71ceda34408e4c469b5a799c01774364.json"
)
CHGR_PROV_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / "chgrprov-9cd1ad63128c4c3ea7624a437c0b73a7.json"
)
CHGR_INTG_PATH = (
    REPO_ROOT
    / ".pcae"
    / "publication-execution"
    / "records"
    / "chgrintg-ee5908d1ded84b1ea8531806f445349e.json"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def chgr_record() -> dict:
    return json.loads(CHGR_PATH.read_text(encoding="utf-8"))


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    assert match, f"section {heading!r} not found in {DOC_PATH.name}"
    return match.group(1)


def test_doc_exists_and_is_nonempty(doc_text: str) -> None:
    assert len(doc_text) > 5000


def test_chgr_file_exists_and_is_valid_json() -> None:
    assert CHGR_PATH.exists(), f"published CHGR not found at {CHGR_PATH}"
    payload = json.loads(CHGR_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)


def test_chgr_is_published_human_governance_record(chgr_record: dict) -> None:
    assert chgr_record["record_type"] == "human_governance_record"
    assert chgr_record["lifecycle_state"] == "published"
    assert chgr_record["record_id"] == "chgr-d4343fa51b9743f3abaeb87a881a78b1"


def test_chgr_selected_option_is_approve(chgr_record: dict) -> None:
    assert chgr_record["selected_option_id"] == "approve"


def test_chgr_decision_maker_is_named_human(chgr_record: dict) -> None:
    evidence = chgr_record["decision_maker_identity_evidence"]
    assert evidence["identifier"] == "Atila Madai"
    assert evidence["evidence_kind"] == "typed_confirmation_only"
    assert chgr_record["assurance_level"] == "L0"


def test_chgr_decision_subject_cites_both_planning_documents(chgr_record: dict) -> None:
    subject = chgr_record["decision_subject"]
    assert "PHASE_149O_20L_5_" in subject
    assert "PHASE_149O_20L_5A_" in subject


def test_chgr_rationale_and_conditions_are_nonempty_and_scoped(chgr_record: dict) -> None:
    rationale = chgr_record.get("rationale", "")
    conditions = chgr_record.get("conditions", "")
    assert rationale, "expected non-empty human rationale"
    assert conditions, "expected non-empty human conditions"
    combined = f"{rationale}\n{conditions}"
    required_phrases = [
        "APPROVE",
        "Boundary C",
        "Boundary A",
        "HATP_MANDATORY",
        "Permission Broker",
        "POL-005",
        "COMP-002",
    ]
    for phrase in required_phrases:
        assert phrase in combined, f"expected exclusion/scope phrase {phrase!r} in rationale/conditions"


def test_chgr_template_ref_matches_authored_template(chgr_record: dict) -> None:
    template_ref = chgr_record["template_ref"]
    assert template_ref["template_id"] == "class-b-boundary-p-provisioning-authorization"
    assert template_ref["version"] == "1.0"


def test_chgr_carries_confirmation_provenance_integrity_refs(chgr_record: dict) -> None:
    for field in ("confirmation_evidence_ref", "provenance_ref", "integrity_ref"):
        ref = chgr_record[field]
        assert ref.get("record_id"), f"expected non-empty {field}.record_id"


def test_authored_aesic_template_exists_and_names_human_authority() -> None:
    template_path = (
        REPO_ROOT
        / ".pcae"
        / "authority-evaluation"
        / "templates"
        / "class-b-boundary-p-provisioning-authorization"
        / "1.0.json"
    )
    assert template_path.exists()
    payload = json.loads(template_path.read_text(encoding="utf-8"))
    assert payload["template_ref"] == "class-b-boundary-p-provisioning-authorization"
    assert payload["template_version"] == "1.0"
    assert "Atila Madai" in payload["eligible_authority"]


def test_governance_record_inspect_succeeds() -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [PCAE_EXECUTABLE, "governance-record", "inspect", str(CHGR_PATH), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["outcome"] == "inspected"
    assert payload["record_identity"] == "chgr-d4343fa51b9743f3abaeb87a881a78b1"


def test_governance_record_verify_with_related_artifacts_passes_all_non_skipped_checks() -> None:
    assert PCAE_EXECUTABLE, "pcae executable not found on PATH"
    proc = subprocess.run(
        [
            PCAE_EXECUTABLE,
            "governance-record",
            "verify",
            str(CHGR_PATH),
            "--related",
            str(CHGR_CONF_PATH),
            "--related",
            str(CHGR_PROV_PATH),
            "--related",
            str(CHGR_INTG_PATH),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["outcome"] == "verified"
    checks = payload["checks"]
    for check in checks:
        assert check["status"] in ("passed", "skipped"), f"unexpected check status: {check}"
    non_skipped = [c for c in checks if c["status"] != "skipped"]
    assert non_skipped, "expected at least one non-skipped check"
    for check in non_skipped:
        assert check["status"] == "passed", f"expected check to pass: {check}"


def test_doc_boundary_separation_section_is_explicit(doc_text: str) -> None:
    section = _section(doc_text, "13. Boundary Separation After Approval (Explicit, Not Blurred)")
    assert "Boundary P: AUTHORIZED" in section
    assert "Boundary C: NOT AUTHORIZED" in section
    assert "Boundary A: NOT AUTHORIZED" in section


def test_doc_phase_exit_state_shows_not_provisioned_not_ready(doc_text: str) -> None:
    section = _section(doc_text, "14. Class-B / HATP / Runtime State (Phase Exit)")
    assert "NOT PROVISIONED" in section
    assert "NOT READY" in section


def test_doc_contains_no_real_provisioning_or_activation_call(doc_text: str) -> None:
    forbidden = ["activate_hatp_mandatory(", "certify(", "revoke(", "sysadminctl -addUser", "useradd "]
    for heading in (
        "7. Exact Boundary-P Proposition Presented to the Human Authority",
        "9. CHGR Publication",
        "14. Class-B / HATP / Runtime State (Phase Exit)",
    ):
        section = _section(doc_text, heading)
        for token in forbidden:
            assert token not in section, f"forbidden token found in {heading!r}: {token!r}"


def test_doc_does_not_claim_more_than_election_was_captured(doc_text: str) -> None:
    section = _section(doc_text, "15. No Real Certification, No Real Activation")
    normalized = section.lower()
    assert "never invoked" in normalized or "never called" in normalized


def test_repo_clean_and_no_production_source_touched() -> None:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    for path in changed:
        assert not path.startswith("src/pcae/"), f"unexpected src/pcae/ modification: {path}"
        assert not path.startswith("docs/contracts/"), f"unexpected contract modification: {path}"
        assert not path.startswith("scripts/"), f"unexpected scripts/ modification: {path}"


def test_no_real_host_provisioning_artifacts_created() -> None:
    protected_root = Path("/Library/Application Support/PCAE")
    assert not protected_root.exists(), "Protected Root must not exist after this phase"

    id_proc = subprocess.run(["id"], capture_output=True, text=True, check=True)
    assert "pcae" not in id_proc.stdout.lower()
