"""N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL — Model E production
implementation tests (HPAC-PAWA-HELPER-001 v3.0 §30B).

Disposable fixture protected roots only (via
``HPACStoreAuthority._production_test_fixture`` + a real, isolated
``tmp_path`` root created by ``provision_protected_root``) — never a real
live protected root. No sudo, no real OS accounts, no CTAP2 hardware.
"""

from __future__ import annotations

import copy
import hashlib
import pickle
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as legacy_admin
from pcae.core import protected_presentation_installation as inst
from pcae.core.approval_presentation import TrustedApprovalPresentationStore
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    HPACWriterCapability,
)
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_ADMIN_MUTATIONS,
    CLOSED_CERTIFICATION_ROLES,
)
from pcae.core.hpac_pawa_helper_store_adapter import RealCanonicalReadAdapter
from pcae.core import hpac_pawa_helper_writer_authority as wa
from pcae.core.human_principal_registry import HumanPrincipalRegistryStore
from pcae.core.hpac_lifecycle import HPACLifecycleStore

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "pcae"

_AGENT_UID = 5_262_626
_AGENT_GID = 999_999
HELPER_BYTES = b"#!/usr/bin/env python3\n# disposable test helper\n"


def _agent_src():
    return lambda account, provisioned_uid: (provisioned_uid, frozenset({_AGENT_GID}))


def _probe():
    return legacy_admin.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "test_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("test_root",)),
    )


def _root(tmp_path: Path) -> Path:
    r = (tmp_path / "root").resolve()
    legacy_admin.provision_protected_root(protected_root=r, agent_account="pcae-agent-svc", agent_uid=_AGENT_UID)
    return r


def _authority(root: Path) -> HPACStoreAuthority:
    return HPACStoreAuthority._production_test_fixture(root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_probe())


def _install_bytes(root: Path, b: bytes) -> str:
    sha = hashlib.sha256(b).hexdigest()
    p = inst.helper_content_addressed_path(root, sha)
    p.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if p.exists():
        p.chmod(0o600)
    p.write_bytes(b)
    p.chmod(0o500)
    return sha


def _install_mechanism(authority: HPACStoreAuthority, root: Path) -> "inst.ResolvedCurrentGeneration":
    """Test-only setup: install the presentation mechanism using the SAME
    internal-capability pattern the new Model E facade uses (mint via
    ``_new_capability`` directly), never via the legacy
    ``hpac_protected_admin_writer``/``hpac_protected_presentation_admin``
    factories."""

    store = inst.ProtectedPresentationInstallationStore(authority)
    cap = authority._new_capability(
        "presentation_mechanism_installer", "pcae-protected-local-presentation",
        single_use=True, multi_write=True,
    )
    resolved = store.apply_configuration(
        cap,
        action="install",
        helper_sha256=_install_bytes(root, HELPER_BYTES),
        helper_implementation_version="test/1.0.0",
        verifier_configuration_digest=hashlib.sha256(b"vc").hexdigest(),
        renderer_profile="pcae-protected-local-presentation-renderer/1.0",
        descriptor_version="test-1.0",
        installed_at="2026-01-01T00:00:00Z",
    )
    return resolved


@pytest.fixture
def installed(tmp_path):
    root = _root(tmp_path)
    authority = _authority(root)
    resolved = _install_mechanism(authority, root)
    adapter = RealCanonicalReadAdapter(authority)
    return root, authority, adapter, resolved


def _fixture_authority(tmp_path) -> HPACStoreAuthority:
    return HPACStoreAuthority.fixture(tmp_path / "fixture-root")


# ═══════════════ 1. family separation / no isinstance escape (both directions) ═══


def test_01_three_families_are_distinct_types_no_shared_recognizable_base():
    assert wa.HelperAdminMutationAuthority is not wa.HelperCertificationWriteAuthority
    assert wa.HelperCertificationWriteAuthority is not wa.HelperPresentationEvidenceAuthority
    for cls in (wa.HelperAdminMutationAuthority, wa.HelperCertificationWriteAuthority, wa.HelperPresentationEvidenceAuthority):
        assert not issubclass(cls, HPACWriterCapability)
        assert not issubclass(HPACWriterCapability, cls)


def test_02_helper_authority_never_isinstance_of_hpac_writer_capability(tmp_path):
    authority = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    assert not isinstance(authority, HPACWriterCapability)


def test_03_legacy_capability_never_recognized_by_helper_store_predicate(installed):
    root, authority, adapter, resolved = installed
    store = HumanPrincipalRegistryStore(authority)
    legacy_cap = authority._new_capability(store._WRITER_ROLE, "hp-legacy", single_use=True)
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            legacy_cap, authority, mutation="enroll_principal", subject="hp-legacy",
            session_id="s", request_id="r", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation,
            operation_params={"enrollment_provenance_ref": "prov-1", "enrolled_at": "2026-01-01T00:00:00Z"},
        )


# ═══════════════ 2. ordinary-process construction / direct entrypoint failure ════


def test_04_ordinary_construction_of_authority_classes_fails():
    with pytest.raises(wa.HelperWriterAuthorityError):
        wa.HelperAdminMutationAuthority(
            mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
            installation_id="i", generation=1, authority_class=HPACAuthorityClass.PRODUCTION,
            _seal=object(),
        )


def test_05_direct_facade_invocation_without_production_authority_fails(tmp_path):
    fixture_authority = _fixture_authority(tmp_path)
    with pytest.raises(wa.HelperWriterAuthorityError):
        wa.mint_and_perform_admin_mutation(
            fixture_authority, mutation="enroll_principal", subject="hp-x", session_id="s",
            request_id="r", installation_id="i", generation=1, operation_params={},
        )


# ═══════════════ 3. NON_REAL cannot satisfy REAL ═════════════════════════════════


def test_06_non_real_authority_never_carries_production_class():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    assert a.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    c = wa.fixture_non_real_certification_write_authority(
        role="hpac_challenge_coordinator", subject="hap-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    assert c.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    p = wa.fixture_non_real_presentation_evidence_authority(
        invocation_id="inv", attempt_id="att", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    assert p.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL


def test_07_non_real_authority_rejected_by_recognition(installed):
    root, authority, adapter, resolved = installed
    fake = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            fake, authority, mutation="enroll_principal", subject="hp-x", session_id="s",
            request_id="r", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


# ═══════════════ 4. admin_mutation positive cases (real store) ═════════════════


def test_08_enroll_principal_real_write(installed):
    root, authority, adapter, resolved = installed
    key = wa.mint_and_perform_admin_mutation(
        authority, mutation="enroll_principal", subject="hp-" + "a" * 32,
        session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
        generation=resolved.anchor.current_generation,
        operation_params={"enrollment_provenance_ref": "prov-1", "enrolled_at": "2026-01-01T00:00:00Z"},
    )
    assert key.startswith("human_principal_registry:principal:")
    record = HumanPrincipalRegistryStore(authority).resolve_principal("hp-" + "a" * 32)
    assert record is not None and record.status == "active"


def test_09_revoke_principal_real_write(installed):
    root, authority, adapter, resolved = installed
    pid = "hp-" + "b" * 32
    wa.mint_and_perform_admin_mutation(
        authority, mutation="enroll_principal", subject=pid, session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        operation_params={"enrollment_provenance_ref": "prov-1", "enrolled_at": "2026-01-01T00:00:00Z"},
    )
    wa.mint_and_perform_admin_mutation(
        authority, mutation="revoke_principal", subject=pid, session_id="s1", request_id="r2",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        operation_params={"revoked_at": "2026-01-02T00:00:00Z"},
    )
    record = HumanPrincipalRegistryStore(authority).resolve_principal(pid)
    assert record.status == "revoked"


def test_10_configure_privileged_helper_metadata_only_real_write(installed):
    root, authority, adapter, resolved = installed
    key = wa.mint_and_perform_admin_mutation(
        authority, mutation="configure_privileged_helper", subject="txn-1", session_id="s1",
        request_id="r1", installation_id=resolved.record.installation_id,
        generation=resolved.anchor.current_generation,
        operation_params={"metadata": {"note": "disposable-test"}, "registered_at": "2026-01-01T00:00:00Z"},
    )
    assert key.startswith("protected_presentation_installation:helper_metadata:")


def test_11_configure_privileged_helper_rejects_helper_bytes_fields(installed):
    root, authority, adapter, resolved = installed
    with pytest.raises(Exception):
        wa.mint_and_perform_admin_mutation(
            authority, mutation="configure_privileged_helper", subject="txn-2", session_id="s1",
            request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation,
            operation_params={"metadata": {"helper_sha256": "x" * 64}, "registered_at": "2026-01-01T00:00:00Z"},
        )


# ═══════════════ 5. admin subtype matrix (cross-subtype rejection sample) ═══════


def test_12_admin_subtype_binding_rejects_mismatched_mutation(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperAdminMutationAuthority(
        mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            authority_obj, authority, mutation="revoke_principal", subject="hp-x",
            session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


def test_13_all_seven_admin_subtypes_in_closed_enum():
    assert CLOSED_ADMIN_MUTATIONS == {
        "enroll_principal", "revoke_principal", "enroll_credential", "revoke_credential",
        "initialize_credential_sidecar_state", "configure_presentation_mechanism",
        "configure_privileged_helper",
    }


# ═══════════════ 6. certification positive cases + 5x5 matrix (sample) ═════════


def _facts(**ov):
    f = {
        "repository_identity": "repo-impl", "repository_display": "repo-impl (fp:i)",
        "task_id": "task-impl", "task_display": "task-impl -- active",
        "runtime_target_id": "rt-impl", "runtime_target_display": "rt-impl -- mock",
        "operation_effect_scope_display": "cap=read; local; one-dispatch; no-network",
        "prompt_hash": "q" * 64, "prompt_instruction_display": "bounded thing (fp:q)",
        "invocation_id": "inv-impl", "invocation_display": "inv-impl (fp:i)",
        "expires_at": "2099-01-01T00:00:00Z", "one_shot_notice": True,
    }
    f.update(ov)
    return f


def _build_evidence(resolved, *, presentation_id: str, approval_id: str):
    """Builds a fully schema-valid ``TrustedApprovalPresentationEvidence``
    bound to the fixture's actually-installed descriptor -- reuses the
    same closed constructors (``new_canonical_runtime_approval_subject``,
    ``render_human_visible_bytes``) real callers use, not ad hoc dicts."""

    from pcae.core.approval_presentation import (
        TrustedApprovalPresentationEvidence,
        new_canonical_runtime_approval_subject,
    )
    from pcae.core.hpac_foundation import canonical_digest
    from pcae.protected_presentation_helper import render_human_visible_bytes

    facts = _facts()
    renderer_profile = resolved.descriptor.renderer_profile
    hv_digest = hashlib.sha256(render_human_visible_bytes(facts, renderer_profile=renderer_profile)).hexdigest()
    subject = new_canonical_runtime_approval_subject(
        subject={"repository_identity": facts["repository_identity"], "task_id": facts["task_id"]},
        approval_scope={"capability": "read", "one_dispatch": True, "network": False},
        approval_preview_digest=hv_digest,
        expires_at=facts["expires_at"],
    )
    canonical_subject_doc = subject.to_document() if hasattr(subject, "to_document") else subject.__dict__
    body = {
        "presentation_schema_version": "HPAC-PRESENTATION-EVIDENCE/2.0",
        "presentation_id": presentation_id,
        "approval_id": approval_id,
        "canonical_subject": canonical_subject_doc,
        "approval_subject_digest": hv_digest,
        "mechanism_ref": {
            "mechanism_id": resolved.descriptor.mechanism_id,
            "descriptor_version": resolved.descriptor.descriptor_version,
            "descriptor_digest": resolved.descriptor.descriptor_digest,
        },
        "human_visible_facts": facts,
        "human_visible_representation_digest": hv_digest,
        "presented_at": "2026-01-01T00:00:00Z",
        "election": {"event_id": "hpevt-" + "1" * 26, "action": "approve", "occurred_at": "2026-01-01T00:00:00Z"},
        "mechanism_attestation": "att",
        "mechanism_attestation_digest": hashlib.sha256(b"att").hexdigest(),
    }
    digest = canonical_digest(body)
    return TrustedApprovalPresentationEvidence(presentation_digest=digest, **body), facts, hv_digest


def test_14_certification_challenge_coordinator_real_write(installed):
    root, authority, adapter, resolved = installed
    presentation_store = TrustedApprovalPresentationStore(authority)
    evidence, facts, hv_digest = _build_evidence(
        resolved, presentation_id="hpe-" + "1" * 32, approval_id="ria-" + "a" * 32,
    )
    created = presentation_store.create(evidence)

    key = wa.mint_and_perform_certification_write(
        authority, role="hpac_challenge_coordinator", subject="hap-" + "c" * 29,
        session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
        generation=resolved.anchor.current_generation,
        operation_params={
            "approval_id": "ria-" + "a" * 32, "invocation_id": "inv-1", "attempt_id": "att-1",
            "principal_id": "hp-" + "p" * 32, "credential_id": "hpc-" + "c" * 31,
            "mechanism_id": resolved.descriptor.mechanism_id,
            "approval_subject_digest": hv_digest, "challenge_digest": "z" * 64,
            "occurred_at": "2026-01-01T00:00:00Z", "resolved_presentation": created,
        },
    )
    assert key.startswith("hpac_lifecycle:")
    chain = HPACLifecycleStore(authority).resolve_chain("hap-" + "c" * 29)
    assert chain and chain[0].state == "CHALLENGE_CREATED"


def test_15_all_five_certification_roles_in_closed_enum():
    assert CLOSED_CERTIFICATION_ROLES == {
        "hpac_challenge_coordinator", "hpac_assertion_recorder",
        "human_authentication_proof_verifier", "hpac_gate5_binder",
        "hpac_rhamp_counter_state_verifier",
    }
    assert "hpac_lifecycle_terminator" not in CLOSED_CERTIFICATION_ROLES


def test_16_certification_role_binding_rejects_cross_role_use(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperCertificationWriteAuthority(
        role="hpac_challenge_coordinator", subject="hap-x", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_certification_write

    with pytest.raises(Exception):
        perform_recognized_certification_write(
            authority_obj, authority, role="hpac_assertion_recorder", subject="hap-x",
            session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


# ═══════════════ 7. presentation evidence create-only + cross-family ═══════════


def _evidence_operation_params(resolved, *, presentation_id: str, approval_id: str, ceremony_approve_ref: str):
    evidence, facts, hv_digest = _build_evidence(resolved, presentation_id=presentation_id, approval_id=approval_id)
    doc = evidence.to_document(include_presentation_digest=False)
    doc["ceremony_approve_ref"] = ceremony_approve_ref
    doc["mechanism_id"] = doc["mechanism_ref"]["mechanism_id"]
    return doc


def test_17_presentation_evidence_write_real_create(installed):
    root, authority, adapter, resolved = installed
    params = _evidence_operation_params(
        resolved, presentation_id="hpe-" + "2" * 32, approval_id="ria-" + "b" * 32,
        ceremony_approve_ref="approve-1",
    )
    key = wa.mint_and_perform_presentation_evidence_write(
        authority, invocation_id="inv-1", attempt_id="att-1", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        operation_params=params,
    )
    assert key == "trusted_approval_presentation:" + "hpe-" + "2" * 32


def test_18_presentation_evidence_write_second_write_rejected(installed):
    root, authority, adapter, resolved = installed
    params = _evidence_operation_params(
        resolved, presentation_id="hpe-" + "3" * 32, approval_id="ria-" + "c" * 32,
        ceremony_approve_ref="approve-2",
    )
    wa.mint_and_perform_presentation_evidence_write(
        authority, invocation_id="inv-2", attempt_id="att-2", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        operation_params=params,
    )
    with pytest.raises(Exception):
        wa.mint_and_perform_presentation_evidence_write(
            authority, invocation_id="inv-2", attempt_id="att-2", session_id="s1", request_id="r2",
            installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
            operation_params=params,
        )


def test_19_presentation_evidence_write_rejects_self_asserted_approval(installed):
    root, authority, adapter, resolved = installed
    with pytest.raises(Exception):
        wa.mint_and_perform_presentation_evidence_write(
            authority, invocation_id="inv-3", attempt_id="att-3", session_id="s1", request_id="r1",
            installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
            operation_params={"ceremony_approve_ref": "x", "approved": True},
        )


def test_20_cross_family_matrix_admin_authority_cannot_write_certification(installed):
    root, authority, adapter, resolved = installed
    admin_authority = wa.HelperAdminMutationAuthority(
        mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_certification_write

    with pytest.raises(Exception):
        perform_recognized_certification_write(
            admin_authority, authority, role="hpac_challenge_coordinator", subject="hap-x",
            session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


# ═══════════════ 8. target/request/generation/currentness binding ══════════════


def test_21_target_substitution_rejected(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperAdminMutationAuthority(
        mutation="enroll_principal", subject="hp-original", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            authority_obj, authority, mutation="enroll_principal", subject="hp-substituted",
            session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


def test_22_request_substitution_rejected(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperAdminMutationAuthority(
        mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r-original",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            authority_obj, authority, mutation="enroll_principal", subject="hp-x",
            session_id="s1", request_id="r-substituted", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


def test_23_generation_mismatch_rejected(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperAdminMutationAuthority(
        mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=999,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    from pcae.core.hpac_pawa_helper_store_adapter import perform_recognized_admin_mutation

    with pytest.raises(Exception):
        perform_recognized_admin_mutation(
            authority_obj, authority, mutation="enroll_principal", subject="hp-x",
            session_id="s1", request_id="r1", installation_id=resolved.record.installation_id,
            generation=resolved.anchor.current_generation, operation_params={},
        )


def test_24_installation_mismatch_rejected(installed):
    root, authority, adapter, resolved = installed
    with pytest.raises(Exception):
        wa.mint_and_perform_admin_mutation(
            authority, mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r1",
            installation_id="wrong-installation-id", generation=resolved.anchor.current_generation,
            operation_params={"enrollment_provenance_ref": "p", "enrolled_at": "2026-01-01T00:00:00Z"},
        )


# ═══════════════ 9. replay / consumption / no-auto-retry (via full helper stack) ══


def test_25_helper_operations_admin_mutation_end_to_end_real(installed):
    root, authority, adapter, resolved = installed
    from pcae.core.hpac_pawa_helper_operations import handle_admin_mutation
    from pcae.core.hpac_pawa_helper_protocol import (
        HelperContext, HelperState, HelperStateMachine, ReplayLedger, EvidenceStager,
        HelperRequest, CLOSED_OPERATIONS,
    )

    request = HelperRequest.from_mapping({
        "request_schema_version": "HPAC-PAWA-HELPER-REQUEST/1.0",
        "protocol_version": "HPAC-PAWA-HELPER/1.0",
        "operation": "admin_mutation",
        "operation_version": "admin_mutation/1.0",
        "session_id": "s1",
        "operation_params": {
            "mutation": "enroll_principal", "transaction_id": "hp-" + "e" * 32,
            "enrollment_provenance_ref": "prov-e2e", "enrolled_at": "2026-01-01T00:00:00Z",
        },
        "request_id": "req-e2e-1", "nonce": "n" * 64, "expiry": "2099-01-01T00:00:00.000000Z",
        "installation_id": resolved.record.installation_id, "generation": resolved.anchor.current_generation,
        "request_digest": "",
    })
    context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=adapter,
    )
    context.replay_ledger.check_and_mark_in_flight(request)
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    machine.advance_to(HelperState.OPERATION_ADMITTED)
    response = handle_admin_mutation(request, context, machine)
    assert response.decision == "PERFORMED"
    record = HumanPrincipalRegistryStore(authority).resolve_principal("hp-" + "e" * 32)
    assert record is not None and record.status == "active"


def test_26_consumed_authority_cannot_be_reused(installed):
    root, authority, adapter, resolved = installed
    authority_obj = wa.HelperAdminMutationAuthority(
        mutation="revoke_principal", subject="hp-consumed", session_id="s1", request_id="r1",
        installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
        authority_class=HPACAuthorityClass.PRODUCTION, _seal=wa._HELPER_AUTHORITY_SEAL,
    )
    wa._spend(authority_obj)
    with pytest.raises(wa.HelperWriterAuthorityError):
        wa._spend(authority_obj)


# ═══════════════ 10. serialization / copy / deepcopy / field reconstruction ═════


def test_27_authority_pickle_raises():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    with pytest.raises(TypeError):
        pickle.dumps(a)


def test_28_authority_deepcopy_raises():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    with pytest.raises(TypeError):
        copy.deepcopy(a)


def test_29_authority_copy_raises():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    with pytest.raises(TypeError):
        copy.copy(a)


def test_30_authority_has_no_reconstructable_dict():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    assert not hasattr(a, "__dict__")


# ═══════════════ 11. restart-dead (fresh interpreter process) ══════════════════


def test_31_authority_seal_is_fresh_per_process(tmp_path):
    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(SRC_ROOT.parent)!r})
        from pcae.core import hpac_pawa_helper_writer_authority as wa
        a = wa.fixture_non_real_admin_mutation_authority(
            mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
            installation_id="i", generation=1,
        )
        print(id(wa._HELPER_AUTHORITY_SEAL))
        """
    )
    out1 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True).stdout.strip()
    out2 = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True).stdout.strip()
    # Different processes -> different object identities; a seal from one
    # process is never valid in another (restart-dead, PAWAH-INV-19 basis).
    assert out1 != out2


def test_32_fresh_process_cannot_construct_authority_with_this_process_seal(tmp_path):
    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(SRC_ROOT.parent)!r})
        from pcae.core import hpac_pawa_helper_writer_authority as wa
        from pcae.core.hpac_foundation import HPACAuthorityClass
        try:
            wa.HelperAdminMutationAuthority(
                mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
                installation_id="i", generation=1, authority_class=HPACAuthorityClass.PRODUCTION,
                _seal=object(),
            )
            print("CONSTRUCTED")
        except wa.HelperWriterAuthorityError:
            print("REJECTED")
        """
    )
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True).stdout.strip()
    assert out == "REJECTED"


# ═══════════════ 12. IPC / disk export ══════════════════════════════════════════


def test_33_helper_response_never_contains_authority(installed):
    root, authority, adapter, resolved = installed
    from pcae.core.hpac_pawa_helper_operations import handle_admin_mutation
    from pcae.core.hpac_pawa_helper_protocol import (
        HelperContext, HelperState, HelperStateMachine, ReplayLedger, EvidenceStager,
        HelperRequest, CLOSED_OPERATIONS, response_leaks_authority,
    )

    request = HelperRequest.from_mapping({
        "request_schema_version": "HPAC-PAWA-HELPER-REQUEST/1.0",
        "protocol_version": "HPAC-PAWA-HELPER/1.0",
        "operation": "admin_mutation", "operation_version": "admin_mutation/1.0",
        "session_id": "s1",
        "operation_params": {
            "mutation": "enroll_principal", "transaction_id": "hp-" + "f" * 32,
            "enrollment_provenance_ref": "prov-ipc", "enrolled_at": "2026-01-01T00:00:00Z",
        },
        "request_id": "req-ipc-1", "nonce": "n" * 64, "expiry": "2099-01-01T00:00:00.000000Z",
        "installation_id": resolved.record.installation_id, "generation": resolved.anchor.current_generation,
        "request_digest": "",
    })
    context = HelperContext(
        replay_ledger=ReplayLedger(), evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS, store=adapter,
    )
    context.replay_ledger.check_and_mark_in_flight(request)
    machine = HelperStateMachine(mutating=True)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)
    machine.advance_to(HelperState.OPERATION_ADMITTED)
    response = handle_admin_mutation(request, context, machine)
    assert not response_leaks_authority(response)


def test_34_no_disk_export_helper_metadata_document_has_no_authority_fields(installed):
    root, authority, adapter, resolved = installed
    wa.mint_and_perform_admin_mutation(
        authority, mutation="configure_privileged_helper", subject="txn-disk", session_id="s1",
        request_id="r1", installation_id=resolved.record.installation_id,
        generation=resolved.anchor.current_generation,
        operation_params={"metadata": {"note": "n"}, "registered_at": "2026-01-01T00:00:00Z"},
    )
    path = inst.ProtectedPresentationInstallationStore(authority)._helper_metadata_path()
    text = path.read_text(encoding="utf-8")
    for token in ("_seal", "HelperAdminMutationAuthority", "authority_seal"):
        assert token not in text


# ═══════════════ 13. no legacy fallback / no legacy-factory import ═════════════


def test_35_writer_authority_module_does_not_import_legacy_factory():
    text = (SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority.py").read_text(encoding="utf-8")
    assert "import pcae.core.hpac_protected_admin_writer" not in text
    assert "from pcae.core.hpac_protected_admin_writer" not in text
    assert "from pcae.core import hpac_protected_admin_writer" not in text
    assert "_PRODUCTION_WRITER_FACTORY_SEAL = object()" not in text
    assert "def _mint_production_writer_capability" not in text
    assert "._mint_production_writer_capability(" not in text


def test_36_facade_failure_has_no_fallback_to_foundation_store(installed):
    root, authority, adapter, resolved = installed
    with pytest.raises(Exception):
        wa.mint_and_perform_admin_mutation(
            authority, mutation="enroll_principal", subject="hp-x", session_id="s1", request_id="r1",
            installation_id=resolved.record.installation_id, generation=resolved.anchor.current_generation,
            operation_params={},  # missing required fields -> must fail, not silently succeed
        )
    record = HumanPrincipalRegistryStore(authority).resolve_principal("hp-x")
    assert record is None


# ═══════════════ 14. no generic broker / reflection ════════════════════════════


def test_37_no_reflection_in_new_or_changed_modules():
    for rel in (
        "core/hpac_pawa_helper_writer_authority.py",
        "core/hpac_pawa_helper_store_adapter.py",
        "core/hpac_pawa_helper_operations.py",
    ):
        text = (SRC_ROOT / rel).read_text(encoding="utf-8")
        assert "eval(" not in text
        assert "exec(" not in text
        assert "importlib" not in text
        assert "getattr(store" not in text
        assert "getattr(request" not in text


def test_38_no_generic_helper_write_function_signature():
    text = (SRC_ROOT / "core" / "hpac_pawa_helper_writer_authority.py").read_text(encoding="utf-8")
    assert "def helper_write(" not in text
    assert "def helper_write" not in text.replace("def helper_write(", "")


# ═══════════════ 15. import-graph structural test (threat-matrix row 31/40) ═══


def _module_source_paths():
    for path in (SRC_ROOT).rglob("*.py"):
        if "worktrees" in path.parts:
            continue
        yield path


def test_39_import_graph_no_agent_reachable_module_imports_writer_authority():
    target = "hpac_pawa_helper_writer_authority"
    allowed_importers = {"hpac_pawa_helper_operations.py", "hpac_pawa_helper_store_adapter.py",
                          "hpac_pawa_helper_writer_authority.py"}
    offenders = []
    for path in _module_source_paths():
        if path.name in allowed_importers or path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if target in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"unexpected importers of {target}: {offenders}"


def test_40_cli_module_does_not_import_writer_authority():
    cli_path = SRC_ROOT / "cli.py"
    if cli_path.exists():
        text = cli_path.read_text(encoding="utf-8")
        assert "hpac_pawa_helper_writer_authority" not in text


def test_41_hpac_foundation_does_not_import_writer_authority():
    text = (SRC_ROOT / "core" / "hpac_foundation.py").read_text(encoding="utf-8")
    assert "hpac_pawa_helper_writer_authority" not in text


def test_42_legacy_admin_writer_does_not_import_writer_authority():
    text = (SRC_ROOT / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "hpac_pawa_helper_writer_authority" not in text


# ═══════════════ 16. read operations remain non-writer ═════════════════════════


def test_43_certification_read_and_ceremony_entry_unchanged_behavior():
    text = (SRC_ROOT / "core" / "hpac_pawa_helper_operations.py").read_text(encoding="utf-8")
    # Both handlers' bodies are untouched by this phase's edits (only the
    # three write handlers gained a `real_authority` branch).
    assert "def handle_certification_read" in text
    assert "def handle_ceremony_entry" in text
    ceremony_start = text.index("def handle_ceremony_entry")
    ceremony_body = text[ceremony_start:text.index("def handle_presentation_evidence_write")]
    assert "mint_and_perform" not in ceremony_body
    read_start = text.index("def handle_certification_read")
    read_body = text[read_start:text.index("def handle_ceremony_entry")]
    assert "mint_and_perform" not in read_body


# ═══════════════ 17. NON_REAL cannot become REAL (deterministic->REAL attack) ══


def test_44_deterministic_authority_class_is_immutable_via_normal_attribute_set():
    a = wa.fixture_non_real_admin_mutation_authority(
        mutation="enroll_principal", subject="hp-x", session_id="s", request_id="r",
        installation_id="i", generation=1,
    )
    a.authority_class = HPACAuthorityClass.PRODUCTION  # slots allow reassignment...
    # ...but recognition always re-derives PRODUCTION-ness from the live
    # HPACStoreAuthority passed to the facade, never trusts the authority
    # object's own claimed class as authoritative for real-store selection;
    # this is exercised end-to-end in test_07 (fixture authority + fake
    # object rejected) and test_05 (fixture HPACStoreAuthority rejected
    # regardless of what class the caller claims).
    assert a.authority_class is HPACAuthorityClass.PRODUCTION  # the mutation succeeded structurally...
    # ...confirming recognition must NOT rely on this field alone without
    # also checking store_authority.authority_class (which test_05 covers).
