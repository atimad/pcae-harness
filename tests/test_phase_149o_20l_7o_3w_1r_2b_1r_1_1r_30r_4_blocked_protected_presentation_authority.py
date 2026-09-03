"""Phase .30R.4 BLOCKED evidence: production presentation installation authority.

These tests preserve the exact pre-implementation finding.  They do not
exercise or authorize a protected UI, a real-assurance positive path, runtime
capability, dispatch, or an external effect.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pcae.core.approval_presentation import PresentationMechanismDescriptorStore
from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACStoreAuthority,
    _PRODUCTION_TEST_FIXTURE_SEAL,
)
from pcae.core.hpac_protected_admin_writer import (
    AUTHORIZED_FACTORY_CONSUMERS,
    PawaError,
    PawaOperation,
    production_writer,
)


REPO = Path(__file__).resolve().parents[1]
PHASE_ENTRY_SHA = "0d5c3ad15a00f57525bb96b08a0e5c0d3a32de86"
FINALIZED_30R4_SHA = "db5f1dd761174d6ac1ca16e49e8871c02f747fdf"
PAWA_CONTRACT = REPO / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
RHAMP_CONTRACT = REPO / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
DECISION_A = REPO / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_3R_N_16_5_RHAMP_SLICE_2_SLICE_3_DECOMPOSITION_ADJUDICATION.md"


def test_phase_entry_sha_is_immutable_finalized_3_6_1_head() -> None:
    assert subprocess.check_output(
        ["git", "cat-file", "-t", PHASE_ENTRY_SHA], cwd=REPO, text=True
    ).strip() == "commit"


def test_decision_a_reassigned_30r_4_to_protected_presentation() -> None:
    text = DECISION_A.read_text(encoding="utf-8")
    assert ".1R.30R.4` is re-assigned from \"composite IV\" to the protected-presentation" in text
    assert "RHAMP-REQ-156 `.1R.32`" in text


def test_rhamp_requires_administrator_installed_production_descriptor() -> None:
    text = RHAMP_CONTRACT.read_text(encoding="utf-8")
    assert "Only HPAC-REQ-080's protected administrator may create or" in text
    assert "pcae-protected-local-presentation/1.0" in text
    assert "a **pinned executable digest** recorded in a protected installation" in text


def test_pawa_mutation_vocabulary_has_no_presentation_install_operation() -> None:
    # Phase .1R.30R.4R.1 reconciliation — the `.30R.4R` reconciliation
    # resolved the blocker with HPAC-PAWA-001 v1.2's exact
    # `configure_presentation_mechanism` *metadata-only* mutation family
    # (HPAC-PAWA-REQ-095). The historically proposed `install_presentation_mechanism`
    # (a generic executable-install verb) is still NOT a mutation class.
    assert {operation.value for operation in PawaOperation} == {
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    }
    assert "install_presentation_mechanism" not in {
        operation.value for operation in PawaOperation
    }


def test_pawa_production_writer_rejects_presentation_install_operation() -> None:
    with pytest.raises(PawaError) as caught:
        production_writer(
            "install_presentation_mechanism",
            _caller_module="pcae.core.approval_presentation",
        )
    assert caught.value.code == "operation_scope_invalid"
    assert "not a §42 mutation class" in caught.value.detail


def test_pawa_factory_consumer_inventory_has_no_presentation_installer() -> None:
    # Phase .1R.30R.4R.1 reconciliation — HPAC-PAWA-001 v1.2 adds exactly one
    # further consumer category, the standalone protected-presentation
    # configuration admin module (HPAC-PAWA-REQ-087). `approval_presentation`
    # itself is still NOT a factory consumer (the blocker the `.30R.4` finding
    # names).
    assert AUTHORIZED_FACTORY_CONSUMERS == frozenset(
        {
            "pcae.core.hpac_protected_admin_writer",
            "pcae.core.hpac_rhamp_enrollment",
            "pcae.core.hpac_protected_presentation_admin",
        }
    )
    assert "pcae.core.approval_presentation" not in AUTHORIZED_FACTORY_CONSUMERS


def test_descriptor_store_requires_a_distinct_unissuable_writer_role(tmp_path: Path) -> None:
    authority = HPACStoreAuthority._production_test_fixture(
        tmp_path, _seal=_PRODUCTION_TEST_FIXTURE_SEAL
    )
    store = PresentationMechanismDescriptorStore(authority)
    assert store._WRITER_ROLE == "presentation_mechanism_installer"
    with pytest.raises(HPACAuthorityError, match="no production HPAC writer"):
        store.fixture_installer("hpac.protected.local.presentation.v1")


def test_pawa_contract_requires_normative_amendment_for_new_factory_consumer() -> None:
    text = PAWA_CONTRACT.read_text(encoding="utf-8")
    assert "The closed set of mutation classes:" in text
    assert "Any **new** production consumer of the `PRODUCTION`" in text
    assert "this contract is amended to name its category" in text


def test_current_presentation_resolver_has_no_real_attestation_branch() -> None:
    # Phase .1R.30R.4R.1 reconciliation — the real
    # `pcae-protected-local-presentation/1.0` attestation branch is now
    # implemented and delegates to the launcher verifier. The deterministic
    # fail-closed discipline is preserved: any other verifier_kind still
    # fails closed.
    source = (REPO / "src/pcae/core/approval_presentation.py").read_text(encoding="utf-8")
    assert 'descriptor.verifier_kind != "deterministic-test-fixture"' in source
    assert "verify_protected_presentation_evidence" in source
    assert "no real protected-presentation attestation verifier is implemented for this verifier_kind" in source


def test_blocked_phase_changes_no_production_or_normative_contract() -> None:
    subprocess.run(
        ["git", "diff", "--quiet", PHASE_ENTRY_SHA, FINALIZED_30R4_SHA, "--", "src/pcae", "docs/contracts"],
        cwd=REPO,
        check=True,
    )
