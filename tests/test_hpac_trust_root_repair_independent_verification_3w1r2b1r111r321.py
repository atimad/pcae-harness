"""Independent adversarial verification for Phase 149O...3.2.1.

This suite is derived from the contracts and the four Blocking findings in
Phase .3.1.  It intentionally does not import any helper from the .3 or .3.2
test suites.  Tests whose names contain ``blocking_reproduction`` document
unsafe current behaviour with positive assertions; a passing reproduction is
evidence of a defect, not evidence that the foundation is verified.
"""

from __future__ import annotations

import ast
import base64
import dataclasses
import hashlib
import inspect
import json
import pickle
import shutil
from concurrent.futures import ThreadPoolExecutor
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
    DETERMINISTIC_PRESENTATION_MECHANISM_ID,
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACDuplicateError,
    HPACMalformedError,
    HPACResolvedRecord,
    HPACStoreAuthority,
    HPACSymlinkError,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
    resolve_hpac_protected_root,
)
from pcae.core.hpac_lifecycle import (
    HPACLifecycleForkError,
    HPACLifecycleStateError,
    HPACLifecycleStore,
)
from pcae.core.human_authentication_proof import (
    PROOF_SCHEMA_VERSION,
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    HumanAuthenticationProofTrustError,
)
from pcae.core.human_authenticator import AssuranceLevel, ProofMaterial
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicAuthenticatorReplayError,
    DeterministicTestHumanAuthenticator,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryStore,
    PrincipalRecord,
)
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionStore,
    new_inert_consumption_record,
)


APPROVAL_ID = "ria-" + "1" * 32
PROOF_ID = "hap-" + "2" * 32
PRINCIPAL_ID = "hp-" + "3" * 32
CREDENTIAL_ID = "hpc-" + "4" * 32
EXPIRY = "2026-08-28T12:00:00Z"


def _approval_subject(*, invocation_id: str = "iv-independent"):
    subject = {
        "repository_identity": "repo-independent",
        "task_id": "task-independent",
        "runtime_target_id": "target-independent",
        "prompt_hash": "5" * 64,
        "invocation_id": invocation_id,
    }
    scope = {"capability": "runtime_dispatch", "network": False}
    preview = compute_deterministic_human_visible_representation_digest(
        EXPIRY, subject=subject, approval_scope=scope
    )
    return new_canonical_runtime_approval_subject(
        subject=subject,
        approval_scope=scope,
        approval_preview_digest=preview,
        expires_at=EXPIRY,
    )


def _install_fixture_mechanism(authority: HPACStoreAuthority):
    mechanism = DeterministicTestPresentationMechanism()
    store = PresentationMechanismDescriptorStore(authority)
    store.install(store.fixture_installer(mechanism.MECHANISM_ID), mechanism.descriptor())
    installed = store.resolve_canonical(mechanism.MECHANISM_ID)
    assert installed is not None
    return mechanism, store, installed


def _write_fixture_presentation(authority: HPACStoreAuthority):
    mechanism, descriptor_store, installed = _install_fixture_mechanism(authority)
    subject = _approval_subject()
    evidence = mechanism.present_installed(subject, APPROVAL_ID, installed)
    store = TrustedApprovalPresentationStore(authority)
    store.create_canonical(
        store.fixture_mechanism_writer(mechanism.MECHANISM_ID), evidence, installed
    )
    resolved = store.resolve_canonical(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
        descriptor_store=descriptor_store,
    )
    return mechanism, descriptor_store, installed, subject, evidence, store, resolved


def _proof_for(evidence: TrustedApprovalPresentationEvidence, subject_digest: str, challenge_digest: str):
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
        "assertion": "696e646570656e64656e74",
        "up": True,
        "uv": True,
        "authenticated_at": "2026-08-28T10:02:00Z",
        "verifier_version": "independent-fixture-v1",
    }
    return HumanAuthenticationProof(proof_digest=canonical_digest(body), **body)


def _genesis_fixture(authority: HPACStoreAuthority, *, proof_id: str = PROOF_ID):
    (_mechanism, _descriptors, _installed, subject, evidence, _store, resolved) = (
        _write_fixture_presentation(authority)
    )
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID
    )
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    lifecycle = HPACLifecycleStore(authority)
    lifecycle.open_challenge_canonical(
        lifecycle.fixture_genesis_writer(proof_id),
        proof_id=proof_id,
        approval_id=APPROVAL_ID,
        invocation_id="iv-independent",
        attempt_id="attempt-independent",
        principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        occurred_at="2026-08-28T10:00:00Z",
        resolved_presentation=resolved,
        challenge=challenge,
    )
    return lifecycle, subject, evidence, challenge, resolved


def _complete_fixture_chain(authority: HPACStoreAuthority):
    lifecycle, subject, evidence, challenge, _resolved = _genesis_fixture(authority)
    lifecycle.record_assertion_canonical(
        lifecycle.fixture_assertion_writer(PROOF_ID),
        proof_id=PROOF_ID,
        assertion_digest="6" * 64,
        occurred_at="2026-08-28T10:01:00Z",
    )
    proof = _proof_for(evidence, subject.digest(), challenge.challenge_digest)
    proofs = HumanAuthenticationProofStore(authority)
    proofs.create_canonical(
        proofs.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof
    )
    resolved_proof = proofs.resolve_canonical(PROOF_ID)
    assert resolved_proof is not None
    lifecycle.record_verified_canonical(
        lifecycle.fixture_verifier_writer(PROOF_ID),
        resolved_proof=resolved_proof,
        registry_state_digest="7" * 64,
        verifier_version="independent-fixture-v1",
        occurred_at="2026-08-28T10:02:00Z",
    )
    lifecycle.bind_gate5_canonical(
        lifecycle.fixture_gate5_writer(PROOF_ID),
        proof_id=PROOF_ID,
        approval_digest="8" * 64,
        occurred_at="2026-08-28T10:03:00Z",
    )
    return lifecycle


def _inert_gate9_record():
    return new_inert_consumption_record(
        request_identity={"invocation_id": "i", "attempt_id": "a", "idempotency_key": "k"},
        repository_task_binding={
            "repository_identity": "r", "head_commit": "a" * 40,
            "task_id": "t", "task_contract_digest": "b" * 64,
            "phase_id": "p", "session_id": None,
        },
        target_binding={
            "runtime_target_id": "rt", "adapter_id": "ad", "descriptor_version": "v",
            "descriptor_digest": "c" * 64, "target_config_digest": "d" * 64,
            "executable_identity_digest": "e" * 64,
        },
        prompt_binding={"prompt_hash": "f" * 64, "prompt_hash_profile": "semantic-v1"},
        authority_binding={
            "approval_id": APPROVAL_ID, "approval_digest": "1" * 64,
            "authority_projection_id": "projection", "authority_projection_digest": "2" * 64,
            "authority_contract_version": "RIHAC-001/2.0", "proof_id": PROOF_ID,
            "proof_digest": "3" * 64, "proof_validation_digest": "4" * 64,
            "registry_state_digest": "5" * 64, "approval_subject_digest": "6" * 64,
            "trusted_presentation_ref": {"presentation_id": "hpe-" + "7" * 32, "presentation_digest": "8" * 64},
            "challenge_digest": "9" * 64,
        },
        pb_binding={
            "request_digest": "a" * 64, "decision_digest": "b" * 64,
            "decision": "ALLOW", "policy_version": "v", "causing_policy_ids": [],
            "matched_no_go_ids": [],
        },
        runtime_enforcement_binding={
            "decision_id": "d", "decision_digest": "c" * 64, "verdict": "ALLOW",
            "expires_at": EXPIRY, "evaluated_input_digest": "d" * 64,
        },
        dispatch_binding={
            "containment_evidence_ref": {"id": "e", "digest": "e" * 64},
            "state": "dispatch_attempted", "consumed_at": "2026-08-28T10:04:00Z",
        },
        authority_generation_binding={
            "snapshot_schema_version": "HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0",
            "principal_generation": "ag0" + "0" * 61,
            "credential_generation": "ag1" + "1" * 61,
            "approval_generation": "ag2" + "2" * 61,
            "lifecycle_generation": "ag3" + "3" * 61,
            "consumption_generation": "absent",
        },
    )


# Principal authority -----------------------------------------------------------


def test_public_principal_constructor_is_only_candidate_data(tmp_path: Path):
    candidate = PrincipalRecord(
        principal_id=PRINCIPAL_ID, status="active",
        enrollment_provenance_ref="caller says real",
        enrolled_at="2026-08-28T10:00:00Z",
    )
    store = HumanPrincipalRegistryStore(tmp_path / "principal-root")
    assert store.resolve_canonical_principal(candidate.principal_id) is None


def test_fixture_writer_positive_case_resolves_permanently_non_real(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "principal-root")
    store = HumanPrincipalRegistryStore(authority)
    store.enroll_principal(
        store.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="independent fixture",
        enrolled_at="2026-08-28T10:00:00Z",
    )
    resolved = store.resolve_canonical_principal(PRINCIPAL_ID)
    assert resolved is not None
    assert resolved.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert resolved.is_real_runtime_eligible is False


def test_copied_principal_bytes_and_digest_do_not_recreate_provenance(tmp_path: Path):
    source = HumanPrincipalRegistryStore(tmp_path / "source")
    source.enroll_principal(
        source.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture", enrolled_at="2026-08-28T10:00:00Z",
    )
    target = HumanPrincipalRegistryStore(tmp_path / "target")
    target.path.parent.mkdir(parents=True)
    target.path.write_bytes(source.path.read_bytes())
    with pytest.raises(HPACAuthorityError, match="provenance|manifest"):
        target.resolve_canonical_principal(PRINCIPAL_ID)


def test_repository_fake_registry_does_not_redirect_platform_authority(tmp_path: Path, monkeypatch):
    repository = tmp_path / "repo"
    repository.mkdir()
    monkeypatch.chdir(repository)
    fake = HumanPrincipalRegistryStore(repository / ".pcae" / "hpac")
    fake.enroll_principal(
        fake.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="repository fake", enrolled_at="2026-08-28T10:00:00Z",
    )
    assert fake.resolve_canonical_principal(PRINCIPAL_ID).is_real_runtime_eligible is False
    assert HumanPrincipalRegistryStore.production().path == (
        resolve_hpac_protected_root() / "principals" / "principal-registry.json"
    )


def test_production_root_has_no_public_redirection_argument(tmp_path: Path):
    with pytest.raises(TypeError):
        HPACStoreAuthority.production(tmp_path / "caller-root")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        HumanPrincipalRegistryStore.production(tmp_path / "caller-root")  # type: ignore[call-arg]


def test_writer_and_resolved_authority_tokens_are_not_constructible_or_serializable(tmp_path: Path):
    with pytest.raises(HPACAuthorityError, match="cannot be caller-constructed"):
        HPACWriterCapability(object(), "principal_registry_admin", None, HPACAuthorityClass.PRODUCTION, _seal=object())
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    store = HumanPrincipalRegistryStore(authority)
    writer = store.fixture_admin_writer()
    with pytest.raises(TypeError):
        pickle.dumps(writer)
    with pytest.raises(HPACAuthorityError, match="cannot be caller-constructed"):
        HPACResolvedRecord(
            record=object(), authority_class=HPACAuthorityClass.PRODUCTION,
            store_id="hpacs-caller", record_digest="0" * 64,
            record_path=tmp_path / "x", writer_role="caller", writer_subject=None,
            authority_seal=object(), _seal=object(),
        )


def test_foreign_root_writer_cannot_enroll_principal(tmp_path: Path):
    first = HumanPrincipalRegistryStore(HPACStoreAuthority.fixture(tmp_path / "one"))
    second = HumanPrincipalRegistryStore(HPACStoreAuthority.fixture(tmp_path / "two"))
    with pytest.raises(HumanPrincipalRegistryError):
        first.enroll_principal(
            second.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
            enrollment_provenance_ref="foreign", enrolled_at="2026-08-28T10:00:00Z",
        )


def test_fixture_to_real_field_and_location_upgrade_fails(tmp_path: Path):
    source = HumanPrincipalRegistryStore(tmp_path / "fixture")
    original = source.enroll_principal(
        source.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
        enrollment_provenance_ref="fixture-only", enrolled_at="2026-08-28T10:00:00Z",
    )
    claimed_real = dataclasses.replace(original, enrollment_provenance_ref="real-enrollment")
    assert claimed_real.enrollment_provenance_ref == "real-enrollment"
    assert source.resolve_canonical_principal(PRINCIPAL_ID).is_real_runtime_eligible is False
    shutil.copytree(tmp_path / "fixture", tmp_path / "authoritative-looking")
    copied = HumanPrincipalRegistryStore(tmp_path / "authoritative-looking")
    with pytest.raises(HPACAuthorityError, match="copied or replaced"):
        copied.resolve_canonical_principal(PRINCIPAL_ID)


def test_symlinked_authority_root_is_rejected_before_fixture_write(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    store = HumanPrincipalRegistryStore(linked)
    with pytest.raises((HPACSymlinkError, HumanPrincipalRegistryError), match="symlink"):
        store.enroll_principal(
            store.fixture_admin_writer(), principal_id=PRINCIPAL_ID,
            enrollment_provenance_ref="fixture", enrolled_at="2026-08-28T10:00:00Z",
        )


def test_contract_nonempty_principal_id_cannot_redirect_fixed_registry_path(tmp_path: Path):
    principal_store = HumanPrincipalRegistryStore(tmp_path / "principal")
    record = principal_store.enroll_principal(
        principal_store.fixture_admin_writer(), principal_id="../principal-escape",
        enrollment_provenance_ref="fixture", enrolled_at="2026-08-28T10:00:00Z",
    )
    resolved = principal_store.resolve_canonical_principal(record.principal_id)
    assert resolved is not None and resolved.record.principal_id == "../principal-escape"
    assert resolved.is_real_runtime_eligible is False
    assert principal_store.path.is_relative_to(tmp_path / "principal")


def test_presentation_and_proof_identifiers_reject_traversal(tmp_path: Path):

    authority = HPACStoreAuthority.fixture(tmp_path / "shared")
    mechanism, _descriptors, installed = _install_fixture_mechanism(authority)
    evidence = mechanism.present_installed(_approval_subject(), APPROVAL_ID, installed)
    evidence_body = evidence.to_document(include_presentation_digest=False)
    evidence_body["presentation_id"] = "../presentation-escape"
    forged_evidence = TrustedApprovalPresentationEvidence(
        presentation_digest=canonical_digest(evidence_body), **evidence_body
    )
    with pytest.raises(HPACMalformedError, match="presentation_id"):
        TrustedApprovalPresentationStore(authority).create(forged_evidence)

    (_m, _d, _i, subject, valid_evidence, _store, _resolved) = _write_fixture_presentation(
        HPACStoreAuthority.fixture(tmp_path / "proof-context")
    )
    proof = _proof_for(valid_evidence, subject.digest(), "a" * 64)
    proof_body = proof.to_document(include_digest=False)
    proof_body["proof_id"] = str(tmp_path / "proof-escape")
    forged_proof = HumanAuthenticationProof(
        proof_digest=canonical_digest(proof_body), **proof_body
    )
    with pytest.raises(HPACMalformedError, match="proof_id"):
        HumanAuthenticationProofStore(tmp_path / "proof-store").create(forged_proof)


# Presentation authority --------------------------------------------------------


def test_fake_descriptor_with_valid_digest_is_not_installed(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    authority.writer("unrelated-fixture-role")
    descriptors = PresentationMechanismDescriptorStore(authority)
    descriptor = DeterministicTestPresentationMechanism().descriptor()
    body = descriptor.to_document(include_digest=False)
    path = descriptors._path(descriptor.mechanism_id)
    path.parent.mkdir(parents=True)
    path.write_bytes(canonical_json_bytes({**body, "descriptor_digest": canonical_digest(body)}))
    with pytest.raises(HPACAuthorityError, match="provenance"):
        descriptors.resolve_canonical(descriptor.mechanism_id)


def test_copied_installed_descriptor_does_not_rebind_to_another_store(tmp_path: Path):
    source_authority = HPACStoreAuthority.fixture(tmp_path / "source")
    mechanism, source_store, _installed = _install_fixture_mechanism(source_authority)
    target_authority = HPACStoreAuthority.fixture(tmp_path / "target")
    target_authority.writer("unrelated-fixture-role")
    target_store = PresentationMechanismDescriptorStore(target_authority)
    target_path = target_store._path(mechanism.MECHANISM_ID)
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(source_store._path(mechanism.MECHANISM_ID).read_bytes())
    with pytest.raises(HPACAuthorityError, match="provenance"):
        target_store.resolve_canonical(mechanism.MECHANISM_ID)


def test_caller_created_presentation_can_be_structural_but_not_canonical(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, descriptors, installed = _install_fixture_mechanism(authority)
    evidence = mechanism.present_installed(_approval_subject(), APPROVAL_ID, installed)
    presentations = TrustedApprovalPresentationStore(authority)
    presentations.create(evidence)
    assert presentations.resolve_structural(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
    ) == evidence
    with pytest.raises(ApprovalPresentationTrustError, match="provenance"):
        presentations.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptors,
        )


def test_copied_canonical_evidence_reaches_and_fails_writer_provenance(tmp_path: Path):
    source_authority = HPACStoreAuthority.fixture(tmp_path / "source")
    (_m, _d, _i, _s, evidence, source, _r) = _write_fixture_presentation(source_authority)
    target_authority = HPACStoreAuthority.fixture(tmp_path / "target")
    _target_mechanism, target_descriptors, _target_installed = _install_fixture_mechanism(target_authority)
    target = TrustedApprovalPresentationStore(target_authority)
    target_path = target._path(evidence.presentation_id)
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(source._path(evidence.presentation_id).read_bytes())
    with pytest.raises(ApprovalPresentationTrustError, match="attestation|provenance|store"):
        target.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=target_descriptors,
        )


def test_forged_attestation_with_recomputed_outer_digests_is_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _install_fixture_mechanism(authority)
    evidence = mechanism.present_installed(_approval_subject(), APPROVAL_ID, installed)
    attacker_bytes = canonical_json_bytes({"caller": "attestation", "trusted": True})
    body = evidence.to_document(include_presentation_digest=False)
    body["mechanism_attestation"] = base64.urlsafe_b64encode(attacker_bytes).decode().rstrip("=")
    body["mechanism_attestation_digest"] = hashlib.sha256(attacker_bytes).hexdigest()
    forged = TrustedApprovalPresentationEvidence(presentation_digest=canonical_digest(body), **body)
    presentations = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError, match="attestation"):
        presentations.create_canonical(
            presentations.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


@pytest.mark.parametrize("field", ["repository_identity", "invocation_id"])
def test_visible_subject_substitution_rejected(field: str, tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _install_fixture_mechanism(authority)
    evidence = mechanism.present_installed(_approval_subject(), APPROVAL_ID, installed)
    body = evidence.to_document(include_presentation_digest=False)
    body["human_visible_facts"] = {**body["human_visible_facts"], field: "substituted"}
    forged = TrustedApprovalPresentationEvidence(presentation_digest=canonical_digest(body), **body)
    presentations = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError, match="human-visible"):
        presentations.create_canonical(
            presentations.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


def test_mechanism_substitution_rejected_at_installed_descriptor_boundary(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, _descriptors, installed = _install_fixture_mechanism(authority)
    evidence = mechanism.present_installed(_approval_subject(), APPROVAL_ID, installed)
    body = evidence.to_document(include_presentation_digest=False)
    body["mechanism_ref"] = {**body["mechanism_ref"], "mechanism_id": "hpac.fake.real.v1"}
    forged = TrustedApprovalPresentationEvidence(presentation_digest=canonical_digest(body), **body)
    presentations = TrustedApprovalPresentationStore(authority)
    with pytest.raises(ApprovalPresentationTrustError, match="installed mechanism"):
        presentations.create_canonical(
            presentations.fixture_mechanism_writer(mechanism.MECHANISM_ID), forged, installed
        )


def test_challenge_for_other_subject_or_presentation_cannot_open_genesis(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _subject, _evidence, _store, resolved) = _write_fixture_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(PRINCIPAL_ID, CREDENTIAL_ID)
    foreign = authenticator.prepare_challenge("a" * 64, "b" * 64)
    lifecycle = HPACLifecycleStore(authority)
    with pytest.raises(HPACLifecycleStateError, match="substitution"):
        lifecycle.open_challenge_canonical(
            lifecycle.fixture_genesis_writer(PROOF_ID), proof_id=PROOF_ID,
            approval_id=APPROVAL_ID, invocation_id="iv-independent", attempt_id="a",
            principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            occurred_at="2026-08-28T10:00:00Z", resolved_presentation=resolved,
            challenge=foreign,
        )


def test_deterministic_presentation_cannot_be_relabelled_real(tmp_path: Path):
    mechanism = DeterministicTestPresentationMechanism()
    mechanism.SIMULATION_ONLY = False
    mechanism.MECHANISM_ID = "hpac.protected.real.v1"
    assert mechanism.descriptor().mechanism_id == DETERMINISTIC_PRESENTATION_MECHANISM_ID
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _s, _e, _store, resolved) = _write_fixture_presentation(authority)
    assert resolved.is_real_runtime_eligible is False
    assert resolved.record.mechanism_ref["mechanism_id"] == DETERMINISTIC_PRESENTATION_MECHANISM_ID


def test_deterministic_attestation_encoding_has_contract_extra_fields(tmp_path: Path):
    """Non-authority-widening fidelity observation against HPAC-REQ-092."""
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, _s, evidence, _store, _resolved) = _write_fixture_presentation(authority)
    padded = evidence.mechanism_attestation + "=" * (-len(evidence.mechanism_attestation) % 4)
    attestation = json.loads(base64.urlsafe_b64decode(padded))
    assert {"installation_store_id", "simulation_only"} <= set(attestation)


# Proof authority and deterministic authenticator --------------------------------


def test_caller_written_proof_with_matching_digest_is_not_canonical(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(authority)
    proof = _proof_for(evidence, subject.digest(), "a" * 64)
    store = HumanAuthenticationProofStore(authority)
    store.create(proof)
    with pytest.raises(HumanAuthenticationProofTrustError, match="provenance"):
        store.resolve_canonical(proof.proof_id)


def test_copied_proof_bytes_do_not_copy_writer_authority(tmp_path: Path):
    source_authority = HPACStoreAuthority.fixture(tmp_path / "source")
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(source_authority)
    proof = _proof_for(evidence, subject.digest(), "a" * 64)
    source = HumanAuthenticationProofStore(source_authority)
    source.create_canonical(source.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    target = HumanAuthenticationProofStore(tmp_path / "target")
    path = target._path(PROOF_ID)
    path.parent.mkdir(parents=True)
    path.write_bytes(source._path(PROOF_ID).read_bytes())
    with pytest.raises(HumanAuthenticationProofTrustError, match="provenance|manifest"):
        target.resolve_canonical(PROOF_ID)


def test_proof_writer_is_root_and_mechanism_bound(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    other = HumanAuthenticationProofStore(HPACStoreAuthority.fixture(tmp_path / "other"))
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(authority)
    proof = _proof_for(evidence, subject.digest(), "a" * 64)
    store = HumanAuthenticationProofStore(authority)
    with pytest.raises(HumanAuthenticationProofTrustError, match="another HPAC root"):
        store.create_canonical(other.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    with pytest.raises(HumanAuthenticationProofTrustError, match="role/subject"):
        store.create_canonical(store.fixture_proof_writer("hpac.fake.real.v1"), proof)


def test_authorized_fixture_proof_is_canonical_but_never_real(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(authority)
    proof = _proof_for(evidence, subject.digest(), "a" * 64)
    store = HumanAuthenticationProofStore(authority)
    store.create_canonical(store.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    resolved = store.resolve_canonical(PROOF_ID)
    assert resolved is not None
    assert resolved.is_real_runtime_eligible is False
    assert resolved.record.mechanism_id == DETERMINISTIC_MECHANISM_ID


def test_raw_parsed_record_and_resolution_stages_do_not_collapse(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(authority)
    authenticator = DeterministicTestHumanAuthenticator(PRINCIPAL_ID, CREDENTIAL_ID)
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    raw = b"independent response"
    parsed = authenticator.verify_response(challenge, raw)
    record = _proof_for(evidence, subject.digest(), challenge.challenge_digest)
    store = HumanAuthenticationProofStore(authority)
    store.create_canonical(store.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), record)
    resolution = store.resolve_canonical(PROOF_ID)
    assert isinstance(raw, bytes)
    assert isinstance(parsed, ProofMaterial)
    assert isinstance(record, HumanAuthenticationProof)
    assert isinstance(resolution, HPACResolvedRecord)
    assert not hasattr(record, "verified")
    assert not hasattr(resolution, "verified_principal")


def test_unknown_verified_shortcut_field_fails_closed(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (_m, _d, _i, subject, evidence, _p, _r) = _write_fixture_presentation(authority)
    proof = _proof_for(evidence, subject.digest(), "a" * 64)
    store = HumanAuthenticationProofStore(authority)
    store.create_canonical(store.fixture_proof_writer(DETERMINISTIC_MECHANISM_ID), proof)
    path = store._path(PROOF_ID)
    document = json.loads(path.read_text())
    document["verified"] = True
    path.write_bytes(canonical_json_bytes(document))
    with pytest.raises(HPACMalformedError, match="unrecognized"):
        store.resolve_canonical(PROOF_ID)


@pytest.mark.parametrize("up,uv", [(False, False), (False, True), (True, False), (True, True)])
def test_up_and_uv_are_independent_and_never_raise_assurance(up: bool, uv: bool):
    authenticator = DeterministicTestHumanAuthenticator(PRINCIPAL_ID, CREDENTIAL_ID, up=up, uv=uv)
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    parsed = authenticator.verify_response(challenge, f"{up}:{uv}".encode())
    assert (parsed.up, parsed.uv) == (up, uv)
    assert parsed.mechanism_id == DETERMINISTIC_MECHANISM_ID
    assert authenticator.describe().assurance_level is AssuranceLevel.ASSERTED


@pytest.mark.parametrize(
    "principal_matches,credential_matches,expected_principal,expected_credential",
    [
        (False, True, "forged-" + PRINCIPAL_ID, CREDENTIAL_ID),
        (True, False, PRINCIPAL_ID, "forged-" + CREDENTIAL_ID),
    ],
)
def test_principal_and_credential_mismatches_are_separate_controls(
    principal_matches: bool, credential_matches: bool,
    expected_principal: str, expected_credential: str,
):
    authenticator = DeterministicTestHumanAuthenticator(
        PRINCIPAL_ID, CREDENTIAL_ID,
        principal_matches=principal_matches, credential_matches=credential_matches,
    )
    parsed = authenticator.verify_response(
        authenticator.prepare_challenge("a" * 64, "b" * 64), b"response"
    )
    assert authenticator.resolve_principal(parsed) == (expected_principal, expected_credential)


@pytest.mark.parametrize("mode", ["match", "stale", "foreign"])
def test_challenge_match_modes_are_distinct_but_non_real(mode: str):
    authenticator = DeterministicTestHumanAuthenticator(
        PRINCIPAL_ID, CREDENTIAL_ID, challenge_response_mode=mode
    )
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    parsed = authenticator.verify_response(challenge, mode.encode())
    assert (parsed.challenge_digest == challenge.challenge_digest) is (mode == "match")
    assert parsed.mechanism_id == DETERMINISTIC_MECHANISM_ID


def test_replay_revocation_expiry_and_malformed_response_do_not_create_real_authority():
    authenticator = DeterministicTestHumanAuthenticator(PRINCIPAL_ID, CREDENTIAL_ID, revoked=True)
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    parsed = authenticator.verify_response(challenge, b"")
    assert parsed.assertion == ""
    assert authenticator.status().status.value == "revoked"
    assert challenge.expires_at == "2026-08-28T00:05:00Z"
    assert parsed.mechanism_id == DETERMINISTIC_MECHANISM_ID
    with pytest.raises(DeterministicAuthenticatorReplayError):
        authenticator.verify_response(challenge, b"")


# Lifecycle authority -----------------------------------------------------------


def test_forged_digest_correct_genesis_is_structural_only(tmp_path: Path):
    subject = _approval_subject()
    evidence = DeterministicTestPresentationMechanism().present(subject, APPROVAL_ID)
    lifecycle = HPACLifecycleStore(tmp_path / "root")
    lifecycle.open_challenge(
        proof_id=PROOF_ID, approval_id=APPROVAL_ID,
        invocation_id="iv-independent", attempt_id="a",
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="a" * 64,
        occurred_at="2026-08-28T10:00:00Z", resolved_presentation=evidence,
    )
    assert len(lifecycle.resolve_chain(PROOF_ID)) == 1
    with pytest.raises(HPACLifecycleStateError, match="provenance"):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_complete_alternate_chain_from_forged_root_never_becomes_authoritative(tmp_path: Path):
    subject = _approval_subject()
    evidence = DeterministicTestPresentationMechanism().present(subject, APPROVAL_ID)
    lifecycle = HPACLifecycleStore(tmp_path / "alternate")
    lifecycle.open_challenge(
        proof_id=PROOF_ID, approval_id=APPROVAL_ID,
        invocation_id="iv-independent", attempt_id="a",
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="a" * 64,
        occurred_at="2026-08-28T10:00:00Z", resolved_presentation=evidence,
    )
    lifecycle.record_assertion(proof_id=PROOF_ID, assertion_digest="b" * 64, occurred_at="2026-08-28T10:01:00Z")
    lifecycle.record_verified(
        proof_id=PROOF_ID, proof_digest="c" * 64, registry_state_digest="d" * 64,
        verifier_version="caller", occurred_at="2026-08-28T10:02:00Z",
    )
    lifecycle.bind_gate5(proof_id=PROOF_ID, approval_digest="e" * 64, occurred_at="2026-08-28T10:03:00Z")
    assert len(lifecycle.resolve_chain(PROOF_ID)) == 4
    with pytest.raises(HPACLifecycleStateError, match="provenance"):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_copied_authoritative_genesis_and_chain_do_not_rebind(tmp_path: Path):
    source_authority = HPACStoreAuthority.fixture(tmp_path / "source")
    _complete_fixture_chain(source_authority)
    shutil.copytree(tmp_path / "source", tmp_path / "copy")
    copied = HPACLifecycleStore(tmp_path / "copy")
    with pytest.raises((HPACAuthorityError, HPACLifecycleStateError), match="copied|provenance|identity"):
        copied.resolve_canonical_chain(PROOF_ID)


def test_missing_and_non_authoritative_predecessors_are_rejected(tmp_path: Path):
    canonical = HPACLifecycleStore(HPACStoreAuthority.fixture(tmp_path / "missing"))
    with pytest.raises(HPACLifecycleStateError):
        canonical.record_assertion_canonical(
            canonical.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
            assertion_digest="a" * 64, occurred_at="2026-08-28T10:01:00Z",
        )
    subject = _approval_subject()
    evidence = DeterministicTestPresentationMechanism().present(subject, APPROVAL_ID)
    structural = HPACLifecycleStore(tmp_path / "structural")
    structural.open_challenge(
        proof_id=PROOF_ID, approval_id=APPROVAL_ID, invocation_id="iv-independent",
        attempt_id="a", principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="a" * 64,
        occurred_at="2026-08-28T10:00:00Z", resolved_presentation=evidence,
    )
    with pytest.raises(HPACLifecycleStateError, match="provenance"):
        structural.record_assertion_canonical(
            structural.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
            assertion_digest="b" * 64, occurred_at="2026-08-28T10:01:00Z",
        )


def test_immediate_fork_and_stale_successor_are_rejected(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _subject, _evidence, challenge, resolved = _genesis_fixture(authority)
    with pytest.raises(HPACLifecycleForkError):
        lifecycle.open_challenge_canonical(
            lifecycle.fixture_genesis_writer(PROOF_ID), proof_id=PROOF_ID,
            approval_id=APPROVAL_ID, invocation_id="iv-independent", attempt_id="a-2",
            principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            occurred_at="2026-08-28T10:00:01Z", resolved_presentation=resolved,
            challenge=challenge,
        )
    lifecycle.record_assertion_canonical(
        lifecycle.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
        assertion_digest="a" * 64, occurred_at="2026-08-28T10:01:00Z",
    )
    with pytest.raises(HPACLifecycleStateError):
        lifecycle.record_assertion_canonical(
            lifecycle.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
            assertion_digest="b" * 64, occurred_at="2026-08-28T10:01:01Z",
        )


def test_deep_conflicting_successor_is_not_last_writer_wins(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle = _complete_fixture_chain(authority)
    with pytest.raises(HPACLifecycleForkError):
        lifecycle.bind_gate5_canonical(
            lifecycle.fixture_gate5_writer(PROOF_ID), proof_id=PROOF_ID,
            approval_digest="f" * 64, occurred_at="2026-08-28T10:04:00Z",
        )
    assert lifecycle.resolve_canonical_chain(PROOF_ID)[-1].record.approval_digest == "8" * 64


def test_tampered_predecessor_digest_and_recomputed_event_digest_fail_authority(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle = _complete_fixture_chain(authority)
    path = lifecycle._path(PROOF_ID, 2)
    document = json.loads(path.read_text())
    document["previous_event_digest"] = "0" * 64
    document["event_digest"] = canonical_digest({k: v for k, v in document.items() if k != "event_digest"})
    path.write_bytes(canonical_json_bytes(document))
    with pytest.raises((HPACLifecycleForkError, HPACLifecycleStateError, HPACAuthorityError)):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_concurrent_conflicting_successors_have_one_canonical_winner(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _subject, _evidence, _challenge, _resolved = _genesis_fixture(authority)

    def append(digest: str):
        try:
            lifecycle.record_assertion_canonical(
                lifecycle.fixture_assertion_writer(PROOF_ID), proof_id=PROOF_ID,
                assertion_digest=digest, occurred_at="2026-08-28T10:01:00Z",
            )
            return "created"
        except (HPACDuplicateError, HPACLifecycleStateError, HPACLifecycleForkError, HPACAuthorityError):
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(append, ("a" * 64, "b" * 64)))
    assert sorted(results) == ["created", "rejected"]
    chain = lifecycle.resolve_canonical_chain(PROOF_ID)
    assert len(chain) == 2
    assert chain[-1].record.assertion_digest in {"a" * 64, "b" * 64}


def test_unknown_lifecycle_field_is_closed_schema_failure(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    lifecycle, _subject, _evidence, _challenge, _resolved = _genesis_fixture(authority)
    path = lifecycle._path(PROOF_ID, 0)
    document = json.loads(path.read_text())
    document["trusted"] = True
    path.write_bytes(canonical_json_bytes(document))
    with pytest.raises(HPACMalformedError, match="unrecognized"):
        lifecycle.resolve_canonical_chain(PROOF_ID)


def test_blocking_reproduction_structural_lifecycle_absolute_proof_id_escapes_root(tmp_path: Path):
    root = tmp_path / "configured"
    escaped_proof = tmp_path / "escaped-structural"
    subject = _approval_subject()
    evidence = DeterministicTestPresentationMechanism().present(subject, APPROVAL_ID)
    lifecycle = HPACLifecycleStore(root)
    lifecycle.open_challenge(
        proof_id=str(escaped_proof), approval_id=APPROVAL_ID,
        invocation_id="iv-independent", attempt_id="a",
        principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=subject.digest(), challenge_digest="a" * 64,
        occurred_at="2026-08-28T10:00:00Z", resolved_presentation=evidence,
    )
    assert (escaped_proof / "lifecycle" / "0000.json").is_file()
    assert not str((escaped_proof / "lifecycle" / "0000.json")).startswith(str(root))


def test_blocking_reproduction_canonical_lifecycle_detects_escape_after_file_creation(tmp_path: Path):
    authority = HPACStoreAuthority.fixture(tmp_path / "configured")
    escaped_proof = tmp_path / "escaped-canonical"
    with pytest.raises(HPACAuthorityError, match="escapes"):
        _genesis_fixture(authority, proof_id=str(escaped_proof))
    assert (escaped_proof / "lifecycle" / "0000.json").is_file()


# Isolation and Gate-9 ----------------------------------------------------------


def test_blocking_reproduction_inert_gate9_absolute_proof_id_escapes_root(tmp_path: Path):
    root = tmp_path / "gate9-configured"
    escaped = tmp_path / "gate9-escaped"
    store = RuntimeInvocationAuthorityConsumptionStore(root)
    store.create(str(escaped), _inert_gate9_record())
    assert (escaped / "consumption.json").is_file()
    assert not str(escaped / "consumption.json").startswith(str(root))


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    found.update(
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    )
    return found


def test_gate9_remains_inert_without_pb_runtime_or_external_effect_imports():
    import pcae.core.runtime_invocation_authority_consumption as gate9

    imports = _module_imports(Path(inspect.getfile(gate9)))
    forbidden = {
        "pcae.core.permission_broker_foundation", "pcae.core.runtime_authority",
        "pcae.core.runtime_dispatch_permission", "pcae.core.shell_gate",
        "subprocess", "socket", "requests", "urllib", "fido2",
    }
    assert imports.isdisjoint(forbidden)


def test_foundation_has_no_production_consumers_or_gate_wiring():
    import pcae.core.hpac_foundation as foundation

    core = Path(inspect.getfile(foundation)).parent
    owned = {
        "hpac_foundation.py", "human_principal_registry.py", "human_authenticator.py",
        "human_authenticator_deterministic.py", "approval_presentation.py",
        "approval_presentation_deterministic.py", "human_authentication_proof.py",
        "hpac_lifecycle.py", "runtime_invocation_authority_consumption.py",
    }
    module_names = {"pcae.core." + name.removesuffix(".py") for name in owned}
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5's mechanism-neutral HPAC
    # verifier is the one sanctioned consumer of this foundation; see the
    # identical note in test_hpac_foundation_independent_verification_
    # 3w1r2b1r111r31.py::test_new_hpac_modules_have_zero_preexisting_production_consumers.
    expected_consumers = {"hpac_verifier.py"}
    consumers: list[tuple[str, str]] = []
    for path in core.glob("*.py"):
        if path.name in owned or path.name in expected_consumers:
            continue
        for imported in _module_imports(path):
            if imported in module_names:
                consumers.append((path.name, imported))
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 (V-15-2) re-baseline: a
    # phase-aware SUBSET invariant. Only the explicitly enumerated,
    # phase-authorized gate coordinators consume the HPAC Layer-1/2
    # foundation; any other production file still fails
    # (`observed - AUTHORIZED == set()`), and an unbuilt gate module is not
    # pre-authorized.
    #   * gate5 -> hpac_lifecycle: `.1R.10` impl / `.1R.11` verified
    #     (read-only `resolve_gate5_binding_event` +
    #     `STATE_PROOF_VERIFIED_AND_BOUND`; no writer, no consumption).
    #   * gate9 -> hpac_foundation / hpac_lifecycle /
    #     runtime_invocation_authority_consumption: `.1R.14` impl /
    #     `.1R.15` verified (Gate-9 atomic authority consumption
    #     coordinator: create-only atomic primitive, read-only sequence-3
    #     confirm, closed consumption record).
    AUTHORIZED_CONSUMERS = {
        ("runtime_dispatch_gate5.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_foundation"),
        ("runtime_dispatch_gate9.py", "pcae.core.hpac_lifecycle"),
        ("runtime_dispatch_gate9.py", "pcae.core.runtime_invocation_authority_consumption"),
    }
    unauthorized = set(consumers) - AUTHORIZED_CONSUMERS
    assert unauthorized == set(), (
        f"unauthorized production consumer(s) of the HPAC Layer-1/2 foundation: "
        f"{sorted(unauthorized)}"
    )


def test_foundation_implements_no_real_auth_ui_network_hardware_or_process_path():
    import pcae.core.hpac_foundation as foundation

    core = Path(inspect.getfile(foundation)).parent
    names = (
        "hpac_foundation.py", "human_principal_registry.py", "human_authenticator.py",
        "human_authenticator_deterministic.py", "approval_presentation.py",
        "approval_presentation_deterministic.py", "human_authentication_proof.py",
        "hpac_lifecycle.py", "runtime_invocation_authority_consumption.py",
    )
    imports = set().union(*(_module_imports(core / name) for name in names))
    forbidden_fragments = (
        "fido", "webauthn", "ctap", "pam", "biometric", "keychain",
        "subprocess", "socket", "requests",
        "runtime_dispatch_permission", "permission_broker", "shell_gate",
    )
    assert not any(fragment in imported.lower() for fragment in forbidden_fragments for imported in imports)
