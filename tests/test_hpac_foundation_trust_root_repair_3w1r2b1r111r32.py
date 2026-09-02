"""Focused adversarial tests for Phase 149O...3.2.

These tests exercise the new authority-bearing APIs. Historical `.3` APIs
that explicitly return structural fixture data are not used as an oracle.
"""

from __future__ import annotations

import ast
import base64
import dataclasses
import hashlib
import inspect
import json
import shutil
from pathlib import Path

import pytest

from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationEvidence,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACSymlinkError,
    HPACStoreAuthority,
    ProtectedAdminCapability,
    canonical_digest,
    canonical_json_bytes,
    resolve_hpac_protected_root,
)
from pcae.core.hpac_lifecycle import (
    HPACLifecycleForkError,
    HPACLifecycleStateError,
    HPACLifecycleStore,
    STATE_PROOF_VERIFIED_AND_BOUND,
)
from pcae.core.human_authentication_proof import (
    PROOF_SCHEMA_VERSION,
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    HumanAuthenticationProofTrustError,
)
from pcae.core.human_authenticator import ProofMaterial
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicTestHumanAuthenticator,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryStore,
    PrincipalRecord,
)


APPROVAL_A = "ria-" + "a" * 32
APPROVAL_B = "ria-" + "b" * 32
PROOF_ID = "hap-" + "c" * 32
PRINCIPAL_ID = "hp-" + "d" * 32
CREDENTIAL_ID = "hpc-" + "e" * 32
EXPIRES_AT = "2026-08-28T01:00:00Z"


def _subject(invocation_id: str = "inv-a"):
    subject_data = {
        "repository_identity": "repo-a",
        "task_id": "task-a",
        "runtime_target_id": "target-a",
        "prompt_hash": "1" * 64,
        "invocation_id": invocation_id,
    }
    scope = {"capability": "runtime_dispatch", "network": False}
    preview = compute_deterministic_human_visible_representation_digest(
        EXPIRES_AT, subject=subject_data, approval_scope=scope
    )
    return new_canonical_runtime_approval_subject(
        subject=subject_data,
        approval_scope=scope,
        approval_preview_digest=preview,
        expires_at=EXPIRES_AT,
    )


def _installed_presentation(authority: HPACStoreAuthority):
    mechanism = DeterministicTestPresentationMechanism()
    descriptors = PresentationMechanismDescriptorStore(authority)
    descriptors.install(
        descriptors.fixture_installer(mechanism.MECHANISM_ID),
        mechanism.descriptor(),
    )
    installed = descriptors.resolve_canonical(mechanism.MECHANISM_ID)
    assert installed is not None
    return mechanism, descriptors, installed


def _canonical_presentation(
    authority: HPACStoreAuthority,
    *,
    approval_id: str = APPROVAL_A,
    invocation_id: str = "inv-a",
):
    mechanism, descriptors, installed = _installed_presentation(authority)
    subject = _subject(invocation_id)
    evidence = mechanism.present_installed(subject, approval_id, installed)
    presentations = TrustedApprovalPresentationStore(authority)
    presentations.create_canonical(
        presentations.fixture_mechanism_writer(mechanism.MECHANISM_ID),
        evidence,
        installed,
    )
    resolved = presentations.resolve_canonical(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
        descriptor_store=descriptors,
    )
    return mechanism, descriptors, installed, presentations, subject, evidence, resolved


def _proof(challenge_digest: str, subject_digest: str, evidence: TrustedApprovalPresentationEvidence):
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": PROOF_ID,
        "mechanism_id": DETERMINISTIC_MECHANISM_ID,
        "principal_id": PRINCIPAL_ID,
        "credential_id": CREDENTIAL_ID,
        "challenge_digest": challenge_digest,
        "approval_subject_digest": subject_digest,
        "trusted_presentation_ref": {
            "presentation_id": evidence.presentation_id,
            "presentation_digest": evidence.presentation_digest,
        },
        "assertion": "64657465726d696e6973746963",
        "up": True,
        "uv": True,
        "authenticated_at": "2026-08-28T00:03:02Z",
        "verifier_version": "deterministic-fixture-v1",
    }
    return HumanAuthenticationProof(proof_digest=canonical_digest(body), **body)


def _canonical_chain(authority: HPACStoreAuthority):
    (_mechanism, _descriptors, _installed, _presentations, subject, evidence, resolved) = _canonical_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID
    )
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    lifecycle = HPACLifecycleStore(authority)
    lifecycle.open_challenge_canonical(
        lifecycle.fixture_genesis_writer(PROOF_ID),
        proof_id=PROOF_ID,
        approval_id=APPROVAL_A,
        invocation_id="inv-a",
        attempt_id="attempt-a",
        principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        occurred_at="2026-08-28T00:03:00Z",
        resolved_presentation=resolved,
        challenge=challenge,
    )
    lifecycle.record_assertion_canonical(
        lifecycle.fixture_assertion_writer(PROOF_ID),
        proof_id=PROOF_ID,
        assertion_digest="2" * 64,
        occurred_at="2026-08-28T00:03:01Z",
    )
    proof = _proof(challenge.challenge_digest, subject.digest(), evidence)
    proofs = HumanAuthenticationProofStore(authority)
    proofs.create_canonical(
        proofs.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof
    )
    resolved_proof = proofs.resolve_canonical(PROOF_ID)
    assert resolved_proof is not None
    lifecycle.record_verified_canonical(
        lifecycle.fixture_verifier_writer(PROOF_ID),
        resolved_proof=resolved_proof,
        registry_state_digest="3" * 64,
        verifier_version="deterministic-fixture-v1",
        occurred_at="2026-08-28T00:03:02Z",
    )
    lifecycle.bind_gate5_canonical(
        lifecycle.fixture_gate5_writer(PROOF_ID),
        proof_id=PROOF_ID,
        approval_digest="4" * 64,
        occurred_at="2026-08-28T00:03:03Z",
    )
    return lifecycle, proof, resolved_proof


# HumanPrincipalRegistry ----------------------------------------------------------


def test_caller_created_principal_is_data_not_authoritative(tmp_path: Path):
    store = HumanPrincipalRegistryStore(tmp_path / "root")
    candidate = PrincipalRecord(
        principal_id=PRINCIPAL_ID,
        status="active",
        enrollment_provenance_ref="caller",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    assert store.resolve_canonical_principal(candidate.principal_id) is None


def test_authorized_fixture_registry_writer_and_resolver_succeed_but_are_non_real(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    store = HumanPrincipalRegistryStore(authority)
    record = store.enroll_principal(
        store.fixture_admin_writer(),
        principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture-enrollment",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    resolved = store.resolve_canonical_principal(record.principal_id)
    assert resolved is not None
    assert resolved.record == record
    assert resolved.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert resolved.is_real_runtime_eligible is False


def test_copied_registry_json_has_no_writer_provenance(tmp_path: Path):
    source = HumanPrincipalRegistryStore(tmp_path / "source")
    record = source.enroll_principal(
        ProtectedAdminCapability(),
        principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    copied = HumanPrincipalRegistryStore(tmp_path / "copied")
    copied.path.parent.mkdir(parents=True)
    copied.path.write_bytes(source.path.read_bytes())
    with pytest.raises(HPACAuthorityError):
        copied.resolve_principal(record.principal_id)


def test_repository_pcae_registry_cannot_redirect_production(tmp_path: Path):
    fake = HumanPrincipalRegistryStore(tmp_path / "repo" / ".pcae" / "hpac")
    fake.enroll_principal(
        ProtectedAdminCapability(),
        principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="repository",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    resolved = fake.resolve_canonical_principal(PRINCIPAL_ID)
    assert resolved is not None and resolved.is_real_runtime_eligible is False
    production = HumanPrincipalRegistryStore.production()
    assert production.path == resolve_hpac_protected_root() / "principals" / "principal-registry.json"
    assert not str(production.path).startswith(str(tmp_path))


def test_arbitrary_root_can_only_construct_fixture_authority(tmp_path: Path):
    store = HumanPrincipalRegistryStore(tmp_path / "caller-selected")
    assert store.authority.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    with pytest.raises(TypeError):
        HumanPrincipalRegistryStore.production(tmp_path / "redirect")  # type: ignore[call-arg]


def test_fixture_principal_field_mutation_cannot_upgrade_resolution(tmp_path: Path):
    store = HumanPrincipalRegistryStore(tmp_path / "root")
    record = store.enroll_principal(
        ProtectedAdminCapability(),
        principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    resolved = store.resolve_canonical_principal(PRINCIPAL_ID)
    forged = dataclasses.replace(record, enrollment_provenance_ref="real-enrollment")
    assert resolved is not None and resolved.record != forged
    assert resolved.is_real_runtime_eligible is False


def test_fixture_root_copy_cannot_promote_or_rebind_store(tmp_path: Path):
    source = HumanPrincipalRegistryStore(tmp_path / "source")
    source.enroll_principal(
        ProtectedAdminCapability(),
        principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    shutil.copytree(tmp_path / "source", tmp_path / "copied")
    with pytest.raises(HPACAuthorityError, match="copied or replaced"):
        HumanPrincipalRegistryStore(tmp_path / "copied").resolve_canonical_principal(PRINCIPAL_ID)


def test_registry_writer_from_another_root_is_rejected(tmp_path: Path):
    first = HumanPrincipalRegistryStore(HPACStoreAuthority.fixture(tmp_path / "first"))
    second = HumanPrincipalRegistryStore(HPACStoreAuthority.fixture(tmp_path / "second"))
    with pytest.raises(HumanPrincipalRegistryError):
        first.enroll_principal(
            second.fixture_admin_writer(),
            principal_id=PRINCIPAL_ID,
            enrollment_provenance_ref="fixture",
            enrolled_at="2026-08-28T00:00:00Z",
        )


def test_world_writable_registry_root_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(mode=0o777)
    root.chmod(0o777)
    store = HumanPrincipalRegistryStore(root)
    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(
            ProtectedAdminCapability(),
            principal_id=PRINCIPAL_ID,
            enrollment_provenance_ref="fixture",
            enrolled_at="2026-08-28T00:00:00Z",
        )


def test_symlinked_fixture_root_component_is_rejected(tmp_path: Path):
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    store = HumanPrincipalRegistryStore(linked / "hpac")
    with pytest.raises(HPACSymlinkError, match="symlink"):
        store.enroll_principal(
            ProtectedAdminCapability(),
            principal_id=PRINCIPAL_ID,
            enrollment_provenance_ref="fixture",
            enrolled_at="2026-08-28T00:00:00Z",
        )


# Protected presentation ---------------------------------------------------------


def test_caller_created_evidence_never_resolves_canonically(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, descriptors, _installed = _installed_presentation(authority)
    evidence = mechanism.present(_subject(), APPROVAL_A)
    presentations = TrustedApprovalPresentationStore(authority)
    presentations.create(evidence)
    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)):
        presentations.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptors,
        )


def test_correct_installed_deterministic_mechanism_and_writer_succeeds_non_real(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    *_items, resolved = _canonical_presentation(authority)
    assert resolved.writer_role == "protected_presentation_mechanism"
    assert resolved.is_real_runtime_eligible is False


def test_fake_installed_descriptor_without_install_writer_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    store = PresentationMechanismDescriptorStore(authority)
    descriptor = DeterministicTestPresentationMechanism().descriptor()
    body = descriptor.to_document(include_digest=False)
    sealed = {**body, "descriptor_digest": canonical_digest(body)}
    path = store._path(descriptor.mechanism_id)
    path.parent.mkdir(parents=True)
    path.write_bytes(canonical_json_bytes(sealed))
    with pytest.raises(HPACAuthorityError):
        store.resolve_canonical(descriptor.mechanism_id)


def test_fake_attestation_is_rejected_before_canonical_write(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _installed_presentation(authority)
    forged = DeterministicTestPresentationMechanism(fault="forged_attestation").present_installed(
        _subject(), APPROVAL_A, installed
    )
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError):
        store.create_canonical(
            store.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )
    assert not store._path(forged.presentation_id).exists()


def test_caller_manufactured_attestation_bytes_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _installed_presentation(authority)
    evidence = mechanism.present_installed(_subject(), APPROVAL_A, installed)
    attacker_bytes = canonical_json_bytes({"caller": "attestation"})
    body = evidence.to_document(include_presentation_digest=False)
    body["mechanism_attestation"] = base64.urlsafe_b64encode(attacker_bytes).decode().rstrip("=")
    body["mechanism_attestation_digest"] = hashlib.sha256(attacker_bytes).hexdigest()
    forged = TrustedApprovalPresentationEvidence(
        presentation_digest=canonical_digest(body), **body
    )
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError):
        store.create_canonical(
            store.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


def test_copied_presentation_json_has_no_canonical_provenance(tmp_path: Path):
    source_authority = HPACStoreAuthority.fixture(tmp_path / "source")
    (_m, _d, _i, source, _s, evidence, _resolved) = _canonical_presentation(source_authority)
    copied_authority = HPACStoreAuthority.fixture(tmp_path / "copied")
    mechanism, descriptors, _installed = _installed_presentation(copied_authority)
    copied = TrustedApprovalPresentationStore(copied_authority)
    copied_path = copied._path(evidence.presentation_id)
    copied_path.parent.mkdir(parents=True)
    copied_path.write_bytes(source._path(evidence.presentation_id).read_bytes())
    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)):
        copied.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptors,
        )
    assert mechanism.SIMULATION_ONLY is True


def test_subject_substitution_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _installed_presentation(authority)
    evidence = mechanism.present_installed(_subject(), APPROVAL_A, installed)
    body = evidence.to_document(include_presentation_digest=False)
    body["human_visible_facts"] = {**body["human_visible_facts"], "repository_identity": "repo-b"}
    forged = TrustedApprovalPresentationEvidence(
        presentation_digest=canonical_digest(body), **body
    )
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError):
        store.create_canonical(
            store.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


def test_mechanism_substitution_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _installed_presentation(authority)
    evidence = mechanism.present_installed(_subject(), APPROVAL_A, installed)
    body = evidence.to_document(include_presentation_digest=False)
    body["mechanism_ref"] = {**body["mechanism_ref"], "mechanism_id": "caller.mechanism"}
    forged = TrustedApprovalPresentationEvidence(
        presentation_digest=canonical_digest(body), **body
    )
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError):
        store.create_canonical(
            store.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


def test_presentation_challenge_substitution_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject_a, evidence_a, resolved_a) = _canonical_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID
    )
    # Challenge B is internally valid but binds neither presentation nor subject A.
    challenge_b = authenticator.prepare_challenge("b" * 64, "c" * 64)
    lifecycle = HPACLifecycleStore(authority)
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.open_challenge_canonical(
            lifecycle.fixture_genesis_writer(PROOF_ID),
            proof_id=PROOF_ID,
            approval_id=APPROVAL_A,
            invocation_id=subject_a.subject["invocation_id"],
            attempt_id="attempt-a",
            principal_id=PRINCIPAL_ID,
            credential_id=CREDENTIAL_ID,
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            occurred_at="2026-08-28T00:03:00Z",
            resolved_presentation=resolved_a,
            challenge=challenge_b,
        )
    assert evidence_a.presentation_digest != challenge_b.trusted_presentation_digest


# HumanAuthenticationProof -------------------------------------------------------


def test_caller_created_canonical_looking_proof_is_not_authoritative(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject, evidence, _r) = _canonical_presentation(authority)
    proof = _proof("5" * 64, subject.digest(), evidence)
    store = HumanAuthenticationProofStore(authority)
    store.create(proof)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.resolve_canonical(proof.proof_id)


def test_authorized_deterministic_proof_writer_creates_non_real_canonical_proof(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject, evidence, _r) = _canonical_presentation(authority)
    proof = _proof("5" * 64, subject.digest(), evidence)
    store = HumanAuthenticationProofStore(authority)
    store.create_canonical(store.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    resolved = store.resolve_canonical(proof.proof_id)
    assert resolved is not None and resolved.record == proof
    assert resolved.is_real_runtime_eligible is False


def test_proof_writer_from_another_root_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    other = HumanAuthenticationProofStore(HPACStoreAuthority.fixture(tmp_path / "other"))
    (_m, _d, _i, _p, subject, evidence, _r) = _canonical_presentation(authority)
    proof = _proof("5" * 64, subject.digest(), evidence)
    store = HumanAuthenticationProofStore(authority)
    with pytest.raises(HumanAuthenticationProofTrustError):
        store.create_canonical(other.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)


def test_copied_proof_json_is_not_authoritative(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "source")
    (_m, _d, _i, _p, subject, evidence, _r) = _canonical_presentation(authority)
    proof = _proof("5" * 64, subject.digest(), evidence)
    source = HumanAuthenticationProofStore(authority)
    source.create_canonical(source.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    copied = HumanAuthenticationProofStore(tmp_path / "copied")
    copied_path = copied._path(proof.proof_id)
    copied_path.parent.mkdir(parents=True)
    copied_path.write_bytes(source._path(proof.proof_id).read_bytes())
    with pytest.raises(HumanAuthenticationProofTrustError):
        copied.resolve_canonical(proof.proof_id)


def test_raw_parsed_canonical_and_resolved_proof_stages_remain_distinct(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject, evidence, _r) = _canonical_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID
    )
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    raw = b"raw-response"
    parsed = authenticator.verify_response(challenge, raw)
    canonical = _proof(challenge.challenge_digest, subject.digest(), evidence)
    store = HumanAuthenticationProofStore(authority)
    store.create_canonical(store.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), canonical)
    resolved = store.resolve_canonical(PROOF_ID)
    assert isinstance(raw, bytes)
    assert isinstance(parsed, ProofMaterial)
    assert isinstance(canonical, HumanAuthenticationProof)
    assert resolved is not None and resolved.record == canonical
    assert not hasattr(resolved, "verified_principal")


def test_deterministic_authenticator_up_uv_and_matches_remain_independent_but_non_real():
    outcomes = []
    for up, uv in ((False, False), (False, True), (True, False), (True, True)):
        authenticator = DeterministicTestHumanAuthenticator(
            principal_id=PRINCIPAL_ID,
            credential_id=CREDENTIAL_ID,
            up=up,
            uv=uv,
            principal_matches=not up,
            credential_matches=not uv,
        )
        challenge = authenticator.prepare_challenge("1" * 64, "2" * 64)
        proof = authenticator.verify_response(challenge, f"{up}:{uv}".encode())
        principal_id, credential_id = authenticator.resolve_principal(proof)
        outcomes.append((proof.up, proof.uv, principal_id, credential_id))
        assert proof.mechanism_id == DETERMINISTIC_MECHANISM_ID
        assert authenticator.SIMULATION_ONLY is True

    assert {(up, uv) for up, uv, _principal, _credential in outcomes} == {
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    }
    assert outcomes[0][2] == PRINCIPAL_ID and outcomes[0][3] == CREDENTIAL_ID
    assert outcomes[-1][2] != PRINCIPAL_ID and outcomes[-1][3] != CREDENTIAL_ID


# HPAC lifecycle ----------------------------------------------------------------


def test_forged_genesis_is_structural_only_and_not_authoritative(tmp_path: Path):
    mechanism = DeterministicTestPresentationMechanism()
    subject = _subject()
    evidence = mechanism.present(subject, APPROVAL_A)
    lifecycle = HPACLifecycleStore(tmp_path / "root")
    lifecycle.open_challenge(
        proof_id=PROOF_ID,
        approval_id=APPROVAL_A,
        invocation_id="inv-a",
        attempt_id="attempt-a",
        principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(),
        challenge_digest="6" * 64,
        occurred_at="2026-08-28T00:03:00Z",
        resolved_presentation=evidence,
    )
    assert len(lifecycle.resolve_chain(PROOF_ID)) == 1
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_disconnected_complete_hash_chain_is_not_authoritative(tmp_path: Path):
    lifecycle = HPACLifecycleStore(tmp_path / "root")
    mechanism = DeterministicTestPresentationMechanism()
    subject = _subject()
    evidence = mechanism.present(subject, APPROVAL_A)
    lifecycle.open_challenge(
        proof_id=PROOF_ID, approval_id=APPROVAL_A, invocation_id="inv-a",
        attempt_id="attempt-a", principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID, mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="6" * 64,
        occurred_at="2026-08-28T00:03:00Z", resolved_presentation=evidence,
    )
    lifecycle.record_assertion(proof_id=PROOF_ID, assertion_digest="2" * 64, occurred_at="2026-08-28T00:03:01Z")
    lifecycle.record_verified(proof_id=PROOF_ID, proof_digest="3" * 64, registry_state_digest="4" * 64, verifier_version="caller", occurred_at="2026-08-28T00:03:02Z")
    lifecycle.bind_gate5(proof_id=PROOF_ID, approval_digest="5" * 64, occurred_at="2026-08-28T00:03:03Z")
    assert len(lifecycle.resolve_chain(PROOF_ID)) == 4
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_canonical_valid_chain_succeeds_and_traces_to_genesis(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _proof_record, _resolved_proof = _canonical_chain(authority)
    chain = lifecycle.resolve_canonical_chain(PROOF_ID)
    assert [event.record.sequence for event in chain] == [0, 1, 2, 3]
    assert chain[0].writer_role == "hpac_challenge_coordinator"
    assert chain[-1].record.state == STATE_PROOF_VERIFIED_AND_BOUND
    assert all(event.is_real_runtime_eligible is False for event in chain)


def test_immediate_second_genesis_fork_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject, evidence, resolved) = _canonical_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID)
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    lifecycle = HPACLifecycleStore(authority)
    kwargs = dict(
        proof_id=PROOF_ID, approval_id=APPROVAL_A, invocation_id="inv-a",
        attempt_id="attempt-a", principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID, mechanism_id=DETERMINISTIC_MECHANISM_ID,
        occurred_at="2026-08-28T00:03:00Z", resolved_presentation=resolved,
        challenge=challenge,
    )
    lifecycle.open_challenge_canonical(lifecycle.fixture_genesis_writer(PROOF_ID), **kwargs)
    with pytest.raises(HPACLifecycleForkError):
        lifecycle.open_challenge_canonical(lifecycle.fixture_genesis_writer(PROOF_ID), **kwargs)


def test_deep_conflicting_successor_is_rejected_no_last_writer_wins(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _proof_record, _resolved_proof = _canonical_chain(authority)
    with pytest.raises(HPACLifecycleForkError):
        lifecycle.bind_gate5_canonical(
            lifecycle.fixture_gate5_writer(PROOF_ID),
            proof_id=PROOF_ID,
            approval_digest="9" * 64,
            occurred_at="2026-08-28T00:03:04Z",
        )
    assert lifecycle.resolve_canonical_chain(PROOF_ID)[-1].record.approval_digest == "4" * 64


def test_predecessor_absent_is_rejected(tmp_path: Path):
    lifecycle = HPACLifecycleStore(HPACStoreAuthority.fixture(tmp_path / "root"))
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.record_assertion_canonical(
            lifecycle.fixture_assertion_writer(PROOF_ID),
            proof_id=PROOF_ID,
            assertion_digest="2" * 64,
            occurred_at="2026-08-28T00:03:01Z",
        )


def test_non_authoritative_predecessor_is_rejected(tmp_path: Path):
    mechanism = DeterministicTestPresentationMechanism()
    subject = _subject()
    evidence = mechanism.present(subject, APPROVAL_A)
    lifecycle = HPACLifecycleStore(tmp_path / "root")
    lifecycle.open_challenge(
        proof_id=PROOF_ID, approval_id=APPROVAL_A, invocation_id="inv-a",
        attempt_id="attempt-a", principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID, mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="6" * 64,
        occurred_at="2026-08-28T00:03:00Z", resolved_presentation=evidence,
    )
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.record_assertion_canonical(
            lifecycle.fixture_assertion_writer(PROOF_ID),
            proof_id=PROOF_ID,
            assertion_digest="2" * 64,
            occurred_at="2026-08-28T00:03:01Z",
        )


def test_predecessor_digest_mismatch_rejected_even_if_public_digest_recomputed(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _proof_record, _resolved_proof = _canonical_chain(authority)
    path = lifecycle._path(PROOF_ID, 2)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["previous_event_digest"] = "8" * 64
    body = {key: value for key, value in document.items() if key != "event_digest"}
    document["event_digest"] = canonical_digest(body)
    path.write_bytes(canonical_json_bytes(document))
    with pytest.raises((HPACLifecycleForkError, HPACLifecycleStateError, HPACAuthorityError)):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_stale_predecessor_second_same_transition_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _p, subject, evidence, resolved) = _canonical_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID)
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    lifecycle = HPACLifecycleStore(authority)
    lifecycle.open_challenge_canonical(
        lifecycle.fixture_genesis_writer(PROOF_ID), proof_id=PROOF_ID,
        approval_id=APPROVAL_A, invocation_id="inv-a", attempt_id="attempt-a",
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        occurred_at="2026-08-28T00:03:00Z", resolved_presentation=resolved,
        challenge=challenge,
    )
    lifecycle.record_assertion_canonical(
        lifecycle.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
        assertion_digest="2" * 64, occurred_at="2026-08-28T00:03:01Z",
    )
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.record_assertion_canonical(
            lifecycle.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
            assertion_digest="7" * 64, occurred_at="2026-08-28T00:03:02Z",
        )


def test_copied_canonical_chain_cannot_rebind_to_another_root(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "source")
    _canonical_chain(authority)
    shutil.copytree(tmp_path / "source", tmp_path / "copied")
    copied = HPACLifecycleStore(tmp_path / "copied")
    with pytest.raises((HPACAuthorityError, HPACLifecycleStateError)):
        copied.resolve_canonical_chain(PROOF_ID)


# Scope/no-effect checks ---------------------------------------------------------


def test_gate9_primitive_remains_inert_and_has_no_dispatch_or_pb_imports():
    import pcae.core.runtime_invocation_authority_consumption as module

    tree = ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert imports.isdisjoint(
        {
            "pcae.core.permission_broker_foundation",
            "pcae.core.runtime_authority",
            "pcae.core.runtime_dispatch_permission",
            "pcae.core.shell_gate",
            "pcae.core.runtime_adapter",
            "subprocess",
            "socket",
            "requests",
            "urllib",
        }
    )


def test_hpac_repair_has_zero_preexisting_production_consumers():
    core = Path(inspect.getfile(HumanPrincipalRegistryStore)).parent
    modules = {
        "pcae.core.hpac_foundation",
        "pcae.core.human_principal_registry",
        "pcae.core.human_authenticator",
        "pcae.core.human_authenticator_deterministic",
        "pcae.core.approval_presentation",
        "pcae.core.approval_presentation_deterministic",
        "pcae.core.human_authentication_proof",
        "pcae.core.hpac_lifecycle",
        "pcae.core.runtime_invocation_authority_consumption",
    }
    owning = {name.rsplit(".", 1)[-1] + ".py" for name in modules}
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5's mechanism-neutral HPAC
    # verifier is the one sanctioned consumer of this foundation; see the
    # identical note in test_hpac_foundation_independent_verification_
    # 3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers.
    expected_consumers = {"hpac_verifier.py"}
    consumers = []
    for path in core.glob("*.py"):
        if path.name in owning or path.name in expected_consumers:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in modules:
                consumers.append((path.name, node.module))
            elif isinstance(node, ast.Import):
                consumers.extend((path.name, alias.name) for alias in node.names if alias.name in modules)
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 (V-15-2) re-baseline: a
    # phase-aware SUBSET invariant. Only the explicitly enumerated,
    # phase-authorized gate coordinators may consume the HPAC Layer-1/2
    # foundation; any other production file still fails
    # (`observed - AUTHORIZED == set()`), and an unbuilt gate module name
    # is not pre-authorized. See the identical rationale in
    # test_hpac_foundation_independent_verification_3w1r2b1r111r31.py.
    #   * gate5 -> hpac_lifecycle: `.1R.10` impl / `.1R.11` verified.
    #   * gate9 -> hpac_foundation / hpac_lifecycle /
    #     runtime_invocation_authority_consumption: `.1R.14` impl /
    #     `.1R.15` verified (Gate-9 atomic authority consumption).
    AUTHORIZED_CONSUMERS = {
        ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),
        # .1R.17 (Slice A): Gate-10 pre-effect eligibility re-reads the durable
        # consumption.json (RDGO-001 v3.1 §11 item 3); non-effecting, writes nothing.
        ("runtime_dispatch_gate10_eligibility.py", "pcae.core.runtime_invocation_authority_consumption"),
        # .1R.19 (Slice B) reconciled by .1R.19R (.1R.20 IV finding N-20-1):
        # the dispatch-attempt durable lifecycle mirror and the 3S.2.1 MUST-FIX
        # #2 path-containment repair reuse the canonical Layer-1 path-safety /
        # digest *utilities* only (`require_safe_relative_id_component`,
        # `canonical_digest`, `reject_symlink`, `read_canonical_json_document`,
        # `HPACMalformedError`). Neither writes an HPAC principal, presentation,
        # proof, lifecycle event, or consumption record; the non-authoritative
        # `RuntimeInvocationRecord` grants no effect authority. `.1R.16` §36.1 /
        # §38 authorizes the Slice-B file set; any other importer still trips
        # this guard.
        ("runtime_dispatch_attempt_lifecycle.py", "pcae.core.hpac_foundation"),
        ("runtime_invocation.py", "pcae.core.hpac_foundation"),
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (N-16-5 PAWA Production
        # Protected-Admin Writer Anchor, Slice 1). The non-agent-importable
        # admin-writer fence, the HPAC-PAWA-AGENT-EXCLUSION/1.0 resolver, and
        # the PAWA schema helpers consume the Layer-1/2 foundation for the
        # seal-guarded PRODUCTION writer mint primitive plus the canonical-JSON
        # / digest / atomic-create-only utilities. Their own guard test
        # (test_phase_...1r_30r_3_1...::test_39/40/41) keeps them off every
        # agent-reachable path; exact filenames, no wildcard.
        ("hpac_pawa_schemas.py", "pcae.core.hpac_foundation"),
        ("hpac_pawa_agent_exclusion.py", "pcae.core.hpac_foundation"),
        ("hpac_protected_admin_writer.py", "pcae.core.hpac_foundation"),
        ("hpac_protected_admin_writer.py", "pcae.core.human_principal_registry"),
        # Phase .1R.30R.3.4 (N-16-5 merged RHAMP `.1R.30` bundle) — the RHAMP
        # sidecar / counter-state / client-context / FIDO2-authenticator /
        # real-assertion-verify / enrollment-ceremony modules consume the
        # Layer-1/2 foundation utilities + dataclasses. Exact filenames, no
        # wildcard; the enrollment ceremony is inside the non-agent-importable
        # admin-writer fence.
        ("hpac_rhamp_client_context.py", "pcae.core.hpac_foundation"),
        ("hpac_rhamp_credential_sidecar.py", "pcae.core.hpac_foundation"),
        ("hpac_rhamp_counter_state.py", "pcae.core.hpac_foundation"),
        ("human_authenticator_fido2.py", "pcae.core.hpac_foundation"),
        ("human_authenticator_fido2.py", "pcae.core.human_authenticator"),
        ("hpac_rhamp_assertion_verify.py", "pcae.core.human_authentication_proof"),
        ("hpac_rhamp_assertion_verify.py", "pcae.core.human_authenticator"),
        ("hpac_rhamp_assertion_verify.py", "pcae.core.human_principal_registry"),
        ("hpac_rhamp_enrollment.py", "pcae.core.hpac_foundation"),
        ("hpac_rhamp_enrollment.py", "pcae.core.human_principal_registry"),
    }
    unauthorized = set(consumers) - AUTHORIZED_CONSUMERS
    assert unauthorized == set(), (
        f"unauthorized production consumer(s) of the HPAC Layer-1/2 foundation: "
        f"{sorted(unauthorized)}"
    )


def test_no_real_mechanism_ui_hardware_network_or_process_implementation_added():
    core = Path(inspect.getfile(HumanPrincipalRegistryStore)).parent
    phase_files = (
        "hpac_foundation.py", "human_principal_registry.py", "human_authenticator.py",
        "human_authenticator_deterministic.py", "approval_presentation.py",
        "approval_presentation_deterministic.py", "human_authentication_proof.py",
        "hpac_lifecycle.py", "runtime_invocation_authority_consumption.py",
    )
    imports: set[str] = set()
    definitions: set[str] = set()
    for filename in phase_files:
        tree = ast.parse((core / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.add(node.name.lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.lower())
            elif isinstance(node, ast.Import):
                imports.update(alias.name.lower() for alias in node.names)
    forbidden_imports = ("fido", "webauthn", "ctap", "pam", "biometric", "keychain", "socket", "requests")
    assert not any(fragment in imported for fragment in forbidden_imports for imported in imports)
    assert not any(name.startswith(("enroll_cli", "approval_cli", "protected_ui")) for name in definitions)
