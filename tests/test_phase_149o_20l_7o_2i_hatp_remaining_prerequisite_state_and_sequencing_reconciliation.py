"""Phase 149O.20L.7O.2I — HATP Remaining-Prerequisite State and Sequencing
Reconciliation.

Analysis/reconciliation-only evidence checks. These tests do not build a
new production prerequisite engine; they mechanically confirm the primary-
source facts this phase's report relies on, so the reconciliation is not
merely narrative.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CUTOVER_SRC = REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
HMIC_CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
HMRC_CONTRACT = (
    REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
)


pytestmark = pytest.mark.fast_green


def test_hmic_contract_is_version_1_6_and_frozen():
    """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
    governing prompt): true at this phase's own exit commit
    (ddccb992). Superseded for LIVE contract state by Phase
    149O.20L.7O.2M's own HMIC v1.7 widening."""

    text = subprocess.check_output(
        ["git", "show", "ddccb992:docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"],
        cwd=REPO_ROOT,
        text=True,
    )
    assert "**Version:** 1.6" in text
    assert "FROZEN" in text.splitlines()[2] or "FROZEN" in text[:400]


def test_class_b_readiness_term_present_and_joined_into_conjunction():
    text = CUTOVER_SRC.read_text(encoding="utf-8")
    assert "class_b_deployment_conformance_satisfies_readiness" in text
    assert "verify_class_b_deployment_conformance(" in text
    assert "ready=(len(unmet_reasons) == 0)" in text
    # the eighth term must be appended to the same `checks` list consumed
    # by unmet_reasons, not a separate/parallel gate.
    idx_check = text.index('"class_b_deployment_conformance_satisfies_readiness"')
    idx_unmet = text.index("unmet_reasons = tuple(check.detail for check in checks")
    assert idx_check < idx_unmet


def test_readiness_calculation_has_exactly_eight_named_checks():
    text = CUTOVER_SRC.read_text(encoding="utf-8")
    names = re.findall(
        r'HATPMandatoryActivationReadinessCheck\(\s*\n?\s*"([a-z_]+)"', text
    )
    assert len(names) == 8, names
    assert len(set(names)) == 8, "duplicate readiness term name found"
    assert "class_b_deployment_conformance_satisfies_readiness" in names


def test_no_production_source_changed_since_phase_entry_commit():
    """Pinned to this phase's own entry/exit commits (§26 of the
    149O.20L.7O.2M governing prompt: historical snapshot, preserved) --
    not to the live working tree: a later, separately-governed phase
    (149O.20L.7O.2M) legitimately amending src/docs/contracts does not
    retroactively make THIS phase guilty of a production change it
    never performed."""

    entry_commit = "f0471cc5245bdcf96e7a881f2bab203221da68e2"
    exit_commit = "ddccb992"
    diff = subprocess.run(
        ["git", "diff", "--name-only", entry_commit, exit_commit, "--", "src", "docs/contracts"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    assert changed == [], f"unexpected production/contract changes: {changed}"


def test_no_real_trust_enrollment_or_certification_state_files_exist():
    forbidden_names = {
        "certifications.json",
        "certification-bindings.json",
        "hardware-credentials.json",
    }
    found = []
    for path in REPO_ROOT.rglob("*.json"):
        if ".claude/worktrees" in str(path):
            continue
        if path.name in forbidden_names:
            found.append(str(path.relative_to(REPO_ROOT)))
    assert found == [], f"real certification/enrollment state files found: {found}"


def test_hmrc_contract_explicitly_disclaims_comp_002_and_defers_permission_broker():
    text = HMRC_CONTRACT.read_text(encoding="utf-8")
    assert "COMP-002" in text
    assert "POL-005" in text
    assert "not_implemented" in text


def test_cbv_s10_closure_language_present_in_project_status_20l_4_record():
    status = (REPO_ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert (
        "`CBV-S10`: INDEPENDENTLY CONFIRMED CLOSED\n"
        "AT READINESS CONTRACT + PRODUCTION INTEGRATION BOUNDARY."
        in status
        or "INDEPENDENTLY CONFIRMED CLOSED" in status
    )


def test_reconciliation_doc_exists_and_is_nonempty():
    doc = (
        REPO_ROOT
        / "docs"
        / "PHASE_149O_20L_7O_2I_HATP_REMAINING_PREREQUISITE_STATE_AND_SEQUENCING_RECONCILIATION.md"
    )
    assert doc.exists()
    assert len(doc.read_text(encoding="utf-8")) > 2000
