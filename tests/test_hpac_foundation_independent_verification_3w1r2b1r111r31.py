"""Independent adversarial verification for Phase 149O...3.1.

These tests are derived from HPAC-001 v2.0 and the verified Phase .2 plan,
not from Phase .3's test helpers.  A test whose name contains
``blocking_reproduction`` intentionally asserts that the current production
API accepts a contract-forbidden construction.  Such a passing test is
evidence that the defect remains reproducible; it is not certification of the
underlying behavior.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import json
import os
import shutil
from pathlib import Path

import pytest

from pcae.core.approval_presentation import (
    PRESENTATION_ATTESTATION_VERSION,
    PRESENTATION_EVIDENCE_SCHEMA_VERSION,
    TrustedApprovalPresentationEvidence,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DETERMINISTIC_PRESENTATION_MECHANISM_ID,
    DeterministicTestPresentationMechanism,
)
from pcae.core.hpac_foundation import (
    HPACDuplicateError,
    ProtectedAdminCapability,
    canonical_digest,
)
from pcae.core.hpac_lifecycle import (
    HPACLifecycleForkError,
    HPACLifecycleStore,
    LIFECYCLE_SCHEMA_VERSION,
    STATE_ASSERTION_RECEIVED,
    STATE_CHALLENGE_CREATED,
    STATE_PROOF_VERIFIED,
    STATE_PROOF_VERIFIED_AND_BOUND,
)
from pcae.core.human_authentication_proof import (
    PROOF_SCHEMA_VERSION,
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
)
from pcae.core.human_authenticator import AssuranceLevel, Challenge, ProofMaterial
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicAuthenticatorReplayError,
    DeterministicTestHumanAuthenticator,
)
from pcae.core.human_principal_registry import (
    CredentialRecord,
    HumanPrincipalRegistryStore,
    PrincipalRecord,
    principal_digest,
)
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionStore,
    new_inert_consumption_record,
)


REAL_AUTHENTICATOR_ID = "hpac.fido2.uv_presence.v2"
REAL_PRESENTATION_ID = "hpac.protected.presentation.v2"
APPROVAL_A = "ria-" + "a" * 32
APPROVAL_B = "ria-" + "b" * 32
PROOF_ID = "hap-" + "1" * 32


def _visible_facts(*, invocation_id: str = "inv-a", expires_at: str = "2026-08-28T01:00:00Z") -> dict:
    return {
        "repository_identity": "repo-digest",
        "repository_display": "Repository A [repo-digest]",
        "task_id": "task-a",
        "task_display": "Task A [task-a]",
        "runtime_target_id": "target-a",
        "runtime_target_display": "Target A [target-a]",
        "operation_effect_scope_display": "local simulation; no network; one attempt",
        "prompt_hash": "a" * 64,
        "prompt_instruction_display": "Instruction [aaaaaaaa]",
        "invocation_id": invocation_id,
        "invocation_display": f"Invocation [{invocation_id}]",
        "expires_at": expires_at,
        "one_shot_notice": True,
    }


def _caller_made_presentation(
    *,
    approval_id: str = APPROVAL_A,
    invocation_id: str = "inv-a",
    mechanism_id: str = REAL_PRESENTATION_ID,
    attestation: str = "caller-manufactured-attestation",
    presentation_id: str = "hpe-" + "2" * 32,
) -> TrustedApprovalPresentationEvidence:
    facts = _visible_facts(invocation_id=invocation_id)
    rendered_digest = canonical_digest(facts)
    subject = new_canonical_runtime_approval_subject(
        subject={
            "repository_identity": "repo-digest",
            "task_id": "task-a",
            "runtime_target_id": "target-a",
            "prompt_hash": "a" * 64,
            "invocation_id": invocation_id,
        },
        approval_scope={"capability": "runtime_dispatch", "network": False},
        approval_preview_digest=rendered_digest,
        expires_at=facts["expires_at"],
    )
    subject_document = subject.to_document()
    subject_digest = subject.digest()
    election = {
        "event_id": "hpevt-" + "3" * 32,
        "action": "approve",
        "occurred_at": "2026-08-28T00:02:01Z",
    }
    mechanism_ref = {
        "mechanism_id": mechanism_id,
        "descriptor_version": "caller-v1",
        "descriptor_digest": "d" * 64,
    }
    attestation_object = {
        "attestation_version": PRESENTATION_ATTESTATION_VERSION,
        "presentation_id": presentation_id,
        "approval_id": approval_id,
        "approval_subject_digest": subject_digest,
        "human_visible_representation_digest": rendered_digest,
        "descriptor_digest": mechanism_ref["descriptor_digest"],
        "election": election,
        "presented_at": "2026-08-28T00:02:00Z",
    }
    body = {
        "presentation_schema_version": PRESENTATION_EVIDENCE_SCHEMA_VERSION,
        "presentation_id": presentation_id,
        "approval_id": approval_id,
        "canonical_subject": subject_document,
        "approval_subject_digest": subject_digest,
        "mechanism_ref": mechanism_ref,
        "human_visible_facts": facts,
        "human_visible_representation_digest": rendered_digest,
        "presented_at": "2026-08-28T00:02:00Z",
        "election": election,
        "mechanism_attestation": attestation,
        "mechanism_attestation_digest": canonical_digest(attestation_object),
    }
    return TrustedApprovalPresentationEvidence(
        presentation_digest=canonical_digest(body),
        **body,
    )


def _caller_made_proof(**overrides: object) -> HumanAuthenticationProof:
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": PROOF_ID,
        "mechanism_id": REAL_AUTHENTICATOR_ID,
        "principal_id": "hp-" + "4" * 32,
        "credential_id": "hpc-" + "5" * 32,
        "challenge_digest": "6" * 64,
        "approval_subject_digest": "7" * 64,
        "trusted_presentation_ref": {
            "presentation_id": "hpe-" + "8" * 32,
            "presentation_digest": "9" * 64,
        },
        "assertion": "Y2FsbGVyLWJ5dGVz",
        "up": True,
        "uv": True,
        "authenticated_at": "2026-08-28T00:03:00Z",
        "verifier_version": "caller-claims-real-v1",
    }
    body.update(overrides)
    return HumanAuthenticationProof(proof_digest=canonical_digest(body), **body)


def _binding(*, invocation_id: str = "inv-a") -> dict:
    return {
        "approval_id": APPROVAL_A,
        "invocation_id": invocation_id,
        "attempt_id": "attempt-a",
        "principal_id": "hp-" + "4" * 32,
        "credential_id": "hpc-" + "5" * 32,
        "mechanism_id": REAL_AUTHENTICATOR_ID,
        "approval_subject_digest": "7" * 64,
        "trusted_presentation_ref": {
            "presentation_id": "hpe-" + "8" * 32,
            "presentation_digest": "9" * 64,
        },
        "challenge_digest": "6" * 64,
    }


def _event_body(
    *,
    sequence: int,
    state: str,
    previous: str | None,
    binding: dict,
    branch: str = "a",
) -> dict:
    evidence = {
        "assertion_digest": None,
        "proof_digest": None,
        "approval_digest": None,
        "registry_state_digest": None,
        "verifier_version": None,
    }
    if sequence >= 1:
        evidence["assertion_digest"] = "a" * 64
    if sequence >= 2:
        evidence["proof_digest"] = "b" * 64
        evidence["registry_state_digest"] = "c" * 64
        evidence["verifier_version"] = "caller-verifier-v1"
    if sequence >= 3:
        evidence["approval_digest"] = branch * 64
    return {
        "lifecycle_schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event_id": "hpl-" + f"{sequence + 1:x}" * 32,
        "sequence": sequence,
        "previous_event_digest": previous,
        "proof_id": PROOF_ID,
        "state": state,
        "occurred_at": f"2026-08-28T00:00:0{sequence}Z",
        "binding": binding,
        **evidence,
        "terminal_reason_code": None,
    }


def _write_self_consistent_chain(root: Path, *, branch: str = "d", pretty: bool = False) -> tuple[str, ...]:
    directory = root / "proofs" / "v2" / PROOF_ID / "lifecycle"
    directory.mkdir(parents=True)
    previous = None
    digests: list[str] = []
    states = (
        STATE_CHALLENGE_CREATED,
        STATE_ASSERTION_RECEIVED,
        STATE_PROOF_VERIFIED,
        STATE_PROOF_VERIFIED_AND_BOUND,
    )
    for sequence, state in enumerate(states):
        body = _event_body(
            sequence=sequence,
            state=state,
            previous=previous,
            binding=_binding(),
            branch=branch,
        )
        digest = canonical_digest(body)
        document = {**body, "event_digest": digest}
        kwargs = {"indent": 2} if pretty else {"sort_keys": True, "separators": (",", ":")}
        (directory / f"{sequence:04d}.json").write_text(json.dumps(document, **kwargs), encoding="utf-8")
        previous = digest
        digests.append(digest)
    return tuple(digests)


def _inert_consumption_record():
    return new_inert_consumption_record(
        request_identity={"invocation_id": "inv-a", "attempt_id": "attempt-a", "idempotency_key": "idem-a"},
        repository_task_binding={
            "repository_identity": "repo-digest",
            "head_commit": "a" * 40,
            "task_id": "task-a",
            "task_contract_digest": "b" * 64,
            "phase_id": "149O.20L.7O.3W.1R.2B.1R.1.1R.3.1",
            "session_id": None,
        },
        target_binding={
            "runtime_target_id": "target-a",
            "adapter_id": "adapter-a",
            "descriptor_version": "v1",
            "descriptor_digest": "c" * 64,
            "target_config_digest": "d" * 64,
            "executable_identity_digest": "e" * 64,
        },
        prompt_binding={"prompt_hash": "f" * 64, "prompt_hash_profile": "pcae.prompt-semantic.v1"},
        authority_binding={
            "approval_id": APPROVAL_A,
            "approval_digest": "1" * 64,
            "authority_projection_id": "projection-a",
            "authority_projection_digest": "2" * 64,
            "authority_contract_version": "RIHAC-001/2.0",
            "proof_id": PROOF_ID,
            "proof_digest": "3" * 64,
            "proof_validation_digest": "4" * 64,
            "registry_state_digest": "5" * 64,
            "approval_subject_digest": "6" * 64,
            "trusted_presentation_ref": {
                "presentation_id": "hpe-" + "7" * 32,
                "presentation_digest": "8" * 64,
            },
            "challenge_digest": "9" * 64,
        },
        pb_binding={
            "request_digest": "a" * 64,
            "decision_digest": "b" * 64,
            "decision": "ALLOW",
            "policy_version": "v1",
            "causing_policy_ids": [],
            "matched_no_go_ids": [],
        },
        runtime_enforcement_binding={
            "decision_id": "decision-a",
            "decision_digest": "c" * 64,
            "verdict": "ALLOW",
            "expires_at": "2026-08-28T01:00:00Z",
            "evaluated_input_digest": "d" * 64,
        },
        dispatch_binding={
            "containment_evidence_ref": {"id": "containment-a", "digest": "e" * 64},
            "state": "dispatch_attempted",
            "consumed_at": "2026-08-28T00:04:00Z",
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


# HumanPrincipalRegistry provenance -------------------------------------------------


def test_blocking_reproduction_caller_redirects_registry_to_repository_controlled_root(tmp_path: Path):
    repository_root = tmp_path / "attacker-repository" / ".pcae" / "hpac"
    store = HumanPrincipalRegistryStore(repository_root)
    record = store.enroll_principal(
        ProtectedAdminCapability(),
        principal_id="hp-" + "1" * 32,
        enrollment_provenance_ref="caller-provenance",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    assert store.resolve_principal(record.principal_id) == record
    assert str(store.path).startswith(str(repository_root))


def test_blocking_reproduction_copied_registry_json_resolves_in_second_store(tmp_path: Path):
    source = HumanPrincipalRegistryStore(tmp_path / "source")
    record = source.enroll_principal(
        ProtectedAdminCapability(),
        principal_id="hp-" + "2" * 32,
        enrollment_provenance_ref="source-provenance",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    copied = HumanPrincipalRegistryStore(tmp_path / "copied")
    copied.path.parent.mkdir(parents=True)
    copied.path.write_bytes(source.path.read_bytes())
    resolved = copied.resolve_principal(record.principal_id)
    assert resolved == record
    assert principal_digest(resolved) == principal_digest(record)


def test_blocking_reproduction_fixture_identity_has_no_machine_non_real_field_and_accepts_real_assurance_claim(tmp_path: Path):
    assert "simulation_only" not in {field.name for field in dataclasses.fields(PrincipalRecord)}
    assert "simulation_only" not in {field.name for field in dataclasses.fields(CredentialRecord)}
    store = HumanPrincipalRegistryStore(tmp_path)
    principal = store.enroll_principal(
        ProtectedAdminCapability(),
        principal_id="hp-" + "3" * 32,
        enrollment_provenance_ref="fixture",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    credential = store.enroll_credential(
        ProtectedAdminCapability(),
        credential_id="hpc-" + "4" * 32,
        principal_id=principal.principal_id,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        public_key="fixture-public-key",
        assurance_capabilities=(AssuranceLevel.PRINCIPAL_VERIFIED_INTENT.value,),
        enrollment_provenance_ref="fixture",
        enrolled_at="2026-08-28T00:00:01Z",
    )
    assert store.resolve_credential(credential.credential_id) == credential


def test_blocking_reproduction_registry_accepts_world_writable_root(tmp_path: Path):
    root = tmp_path / "unprotected-root"
    root.mkdir()
    root.chmod(0o777)
    store = HumanPrincipalRegistryStore(root)
    record = store.enroll_principal(
        ProtectedAdminCapability(),
        principal_id="hp-" + "5" * 32,
        enrollment_provenance_ref="unprotected",
        enrolled_at="2026-08-28T00:00:00Z",
    )
    assert store.resolve_principal(record.principal_id) == record
    assert root.stat().st_mode & 0o002


# Protected presentation -----------------------------------------------------------


def test_blocking_reproduction_caller_manufactured_attestation_and_real_mechanism_resolve_structurally(tmp_path: Path):
    evidence = _caller_made_presentation()
    store = TrustedApprovalPresentationStore(tmp_path)
    store.create(evidence)
    resolved = store.resolve_structural(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
    )
    assert resolved == evidence
    assert resolved.mechanism_ref["mechanism_id"] == REAL_PRESENTATION_ID


def test_blocking_reproduction_attestation_bytes_are_not_bound_by_attestation_digest(tmp_path: Path):
    first = _caller_made_presentation(attestation="attestation-one", presentation_id="hpe-" + "1" * 32)
    second = _caller_made_presentation(attestation="attestation-two", presentation_id="hpe-" + "1" * 32)
    assert first.mechanism_attestation_digest == second.mechanism_attestation_digest
    assert first.presentation_digest != second.presentation_digest
    store = TrustedApprovalPresentationStore(tmp_path)
    store.create(second)
    assert store.resolve_structural(
        presentation_id=second.presentation_id,
        presentation_digest=second.presentation_digest,
    ).mechanism_attestation == "attestation-two"


def test_blocking_reproduction_copied_presentation_is_independently_resolved_at_another_root(tmp_path: Path):
    evidence = _caller_made_presentation()
    source = TrustedApprovalPresentationStore(tmp_path / "source")
    source.create(evidence)
    copied = TrustedApprovalPresentationStore(tmp_path / "copied")
    copied_path = copied._path(evidence.presentation_id)
    copied_path.parent.mkdir(parents=True)
    copied_path.write_bytes(source._path(evidence.presentation_id).read_bytes())
    assert copied.resolve_structural(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
    ) == evidence


def test_blocking_reproduction_presentation_a_accepts_challenge_digest_derived_from_presentation_b(tmp_path: Path):
    evidence_a = _caller_made_presentation(approval_id=APPROVAL_A, invocation_id="inv-a")
    evidence_b = _caller_made_presentation(
        approval_id=APPROVAL_B,
        invocation_id="inv-b",
        presentation_id="hpe-" + "4" * 32,
    )
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-" + "4" * 32,
        credential_id="hpc-" + "5" * 32,
    )
    challenge_b = authenticator.prepare_challenge(
        evidence_b.approval_subject_digest,
        evidence_b.presentation_digest,
    )
    lifecycle = HPACLifecycleStore(tmp_path / "lifecycle")
    genesis = lifecycle.open_challenge(
        proof_id=PROOF_ID,
        approval_id=APPROVAL_A,
        invocation_id="inv-a",
        attempt_id="attempt-a",
        principal_id=authenticator.principal_id,
        credential_id=authenticator.credential_id,
        mechanism_id=REAL_AUTHENTICATOR_ID,
        approval_subject_digest=evidence_a.approval_subject_digest,
        challenge_digest=challenge_b.challenge_digest,
        occurred_at="2026-08-28T00:03:00Z",
        resolved_presentation=evidence_a,
    )
    assert genesis.binding["trusted_presentation_ref"]["presentation_id"] == evidence_a.presentation_id
    assert genesis.binding["challenge_digest"] == challenge_b.challenge_digest


def test_deterministic_presentation_is_non_real_but_has_no_verified_assurance_type():
    mechanism = DeterministicTestPresentationMechanism()
    descriptor = mechanism.descriptor()
    assert mechanism.SIMULATION_ONLY is True
    assert mechanism.MECHANISM_ID == DETERMINISTIC_PRESENTATION_MECHANISM_ID
    assert descriptor.mechanism_id != REAL_PRESENTATION_ID
    assert descriptor.protected_output is True
    assert descriptor.agent_substitution_resistant is True
    assert "simulation_only" not in {field.name for field in dataclasses.fields(descriptor)}


# Authentication proof stage separation -------------------------------------------


def test_raw_response_and_parsed_material_are_not_canonical_proof_records(tmp_path: Path):
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-" + "4" * 32,
        credential_id="hpc-" + "5" * 32,
    )
    challenge = authenticator.prepare_challenge("7" * 64, "9" * 64)
    raw = b"raw-authenticator-response"
    parsed = authenticator.verify_response(challenge, raw)
    assert isinstance(raw, bytes)
    assert isinstance(parsed, ProofMaterial)
    assert not isinstance(parsed, HumanAuthenticationProof)
    with pytest.raises((AttributeError, TypeError)):
        HumanAuthenticationProofStore(tmp_path).create(parsed)  # type: ignore[arg-type]


def test_blocking_reproduction_caller_created_canonical_looking_proof_is_stored_and_resolved(tmp_path: Path):
    proof = _caller_made_proof()
    store = HumanAuthenticationProofStore(tmp_path)
    store.create(proof)
    assert store.resolve(proof.proof_id) == proof


def test_canonical_proof_does_not_itself_expose_verified_principal_shortcut():
    proof = _caller_made_proof()
    assert not hasattr(proof, "verified")
    module = importlib.import_module("pcae.core.human_authentication_proof")
    assert not hasattr(module, "AuthenticatedHumanPrincipal")


def test_blocking_reproduction_noncanonical_pretty_proof_bytes_resolve(tmp_path: Path):
    proof = _caller_made_proof()
    store = HumanAuthenticationProofStore(tmp_path)
    path = store._path(proof.proof_id)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(proof.to_document(include_digest=True), indent=4), encoding="utf-8")
    assert store.resolve(proof.proof_id) == proof


# Deterministic authenticator -------------------------------------------------------


@pytest.mark.parametrize("up,uv", [(True, False), (False, True), (False, False), (True, True)])
def test_deterministic_authenticator_keeps_up_and_uv_independent(up: bool, uv: bool):
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-a",
        credential_id="hpc-a",
        up=up,
        uv=uv,
    )
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    material = authenticator.verify_response(challenge, f"{up}-{uv}".encode())
    assert (material.up, material.uv) == (up, uv)


@pytest.mark.parametrize(
    "principal_matches,credential_matches,expected_principal,expected_credential",
    [
        (False, True, "forged-hp-a", "hpc-a"),
        (True, False, "hp-a", "forged-hpc-a"),
    ],
)
def test_deterministic_authenticator_exposes_principal_and_credential_mismatch_controls(
    principal_matches: bool,
    credential_matches: bool,
    expected_principal: str,
    expected_credential: str,
):
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-a",
        credential_id="hpc-a",
        principal_matches=principal_matches,
        credential_matches=credential_matches,
    )
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    material = authenticator.verify_response(challenge, b"response")
    assert authenticator.resolve_principal(material) == (expected_principal, expected_credential)


@pytest.mark.parametrize("mode", ["stale", "foreign"])
def test_deterministic_authenticator_exposes_challenge_mismatch_controls(mode: str):
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-a",
        credential_id="hpc-a",
        challenge_response_mode=mode,
    )
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    assert authenticator.verify_response(challenge, b"response").challenge_digest != challenge.challenge_digest


def test_blocking_reproduction_same_challenge_accepts_a_second_distinct_response():
    authenticator = DeterministicTestHumanAuthenticator(principal_id="hp-a", credential_id="hpc-a")
    challenge = authenticator.prepare_challenge("a" * 64, "b" * 64)
    authenticator.verify_response(challenge, b"response-one")
    second = authenticator.verify_response(challenge, b"response-two")
    assert second.challenge_digest == challenge.challenge_digest
    with pytest.raises(DeterministicAuthenticatorReplayError):
        authenticator.verify_response(challenge, b"response-two")


def test_blocking_reproduction_expired_revoked_and_empty_response_still_produce_proof_material():
    authenticator = DeterministicTestHumanAuthenticator(
        principal_id="hp-a",
        credential_id="hpc-a",
        revoked=True,
    )
    prepared = authenticator.prepare_challenge("a" * 64, "b" * 64)
    expired = dataclasses.replace(prepared, expires_at="2000-01-01T00:00:00Z")
    material = authenticator.verify_response(expired, b"")
    assert material.assertion == ""
    assert material.challenge_digest == expired.challenge_digest
    assert authenticator.status().status.value == "revoked"


def test_deterministic_authenticator_is_non_real_but_no_real_verifier_exists_to_enforce_allowlist():
    authenticator = DeterministicTestHumanAuthenticator(principal_id="hp-a", credential_id="hpc-a")
    assert authenticator.SIMULATION_ONLY is True
    assert authenticator.MECHANISM_ID == DETERMINISTIC_MECHANISM_ID
    assert authenticator.describe().assurance_level is AssuranceLevel.ASSERTED
    core = Path(inspect.getfile(DeterministicTestHumanAuthenticator)).parent
    assert not (core / "hpac_verifier.py").exists()


# Lifecycle canonicality, genesis, predecessor, and forks --------------------------


def test_blocking_reproduction_direct_dataclass_is_sufficient_for_genesis(tmp_path: Path):
    evidence = _caller_made_presentation()
    lifecycle = HPACLifecycleStore(tmp_path)
    event = lifecycle.open_challenge(
        proof_id=PROOF_ID,
        approval_id=evidence.approval_id,
        invocation_id="inv-a",
        attempt_id="attempt-a",
        principal_id="hp-" + "4" * 32,
        credential_id="hpc-" + "5" * 32,
        mechanism_id=REAL_AUTHENTICATOR_ID,
        approval_subject_digest=evidence.approval_subject_digest,
        challenge_digest="6" * 64,
        occurred_at="2026-08-28T00:03:00Z",
        resolved_presentation=evidence,
    )
    assert event.state == STATE_CHALLENGE_CREATED


def test_blocking_reproduction_forged_complete_chain_with_public_digests_resolves(tmp_path: Path):
    expected = _write_self_consistent_chain(tmp_path)
    chain = HPACLifecycleStore(tmp_path).resolve_chain(PROOF_ID)
    assert tuple(event.event_digest for event in chain) == expected
    assert [event.state for event in chain] == [
        STATE_CHALLENGE_CREATED,
        STATE_ASSERTION_RECEIVED,
        STATE_PROOF_VERIFIED,
        STATE_PROOF_VERIFIED_AND_BOUND,
    ]


def test_blocking_reproduction_two_alternate_complete_chains_are_each_canonical_to_caller_selected_store(tmp_path: Path):
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = _write_self_consistent_chain(left_root, branch="d")
    right = _write_self_consistent_chain(right_root, branch="e")
    assert left[:3] == right[:3]
    assert left[3] != right[3]
    assert HPACLifecycleStore(left_root).resolve_chain(PROOF_ID)[-1].approval_digest == "d" * 64
    assert HPACLifecycleStore(right_root).resolve_chain(PROOF_ID)[-1].approval_digest == "e" * 64


def test_blocking_reproduction_copied_lifecycle_chain_resolves_in_second_context(tmp_path: Path):
    source_root = tmp_path / "source"
    copied_root = tmp_path / "copied"
    _write_self_consistent_chain(source_root)
    shutil.copytree(source_root, copied_root)
    source_chain = HPACLifecycleStore(source_root).resolve_chain(PROOF_ID)
    copied_chain = HPACLifecycleStore(copied_root).resolve_chain(PROOF_ID)
    assert copied_chain == source_chain


def test_blocking_reproduction_resolver_does_not_validate_state_predecessor_table(tmp_path: Path):
    directory = tmp_path / "proofs" / "v2" / PROOF_ID / "lifecycle"
    directory.mkdir(parents=True)
    genesis = _event_body(
        sequence=0,
        state=STATE_CHALLENGE_CREATED,
        previous=None,
        binding=_binding(),
    )
    genesis_digest = canonical_digest(genesis)
    (directory / "0000.json").write_text(json.dumps({**genesis, "event_digest": genesis_digest}), encoding="utf-8")
    skipped = _event_body(
        sequence=1,
        state=STATE_PROOF_VERIFIED_AND_BOUND,
        previous=genesis_digest,
        binding=_binding(),
    )
    skipped_digest = canonical_digest(skipped)
    (directory / "0001.json").write_text(json.dumps({**skipped, "event_digest": skipped_digest}), encoding="utf-8")
    chain = HPACLifecycleStore(tmp_path).resolve_chain(PROOF_ID)
    assert [event.state for event in chain] == [STATE_CHALLENGE_CREATED, STATE_PROOF_VERIFIED_AND_BOUND]


def test_blocking_reproduction_noncanonical_pretty_lifecycle_bytes_resolve(tmp_path: Path):
    _write_self_consistent_chain(tmp_path, pretty=True)
    assert len(HPACLifecycleStore(tmp_path).resolve_chain(PROOF_ID)) == 4


def test_authorized_narrow_writer_rejects_conflicting_gate5_successor(tmp_path: Path):
    evidence = _caller_made_presentation()
    lifecycle = HPACLifecycleStore(tmp_path)
    lifecycle.open_challenge(
        proof_id=PROOF_ID,
        approval_id=evidence.approval_id,
        invocation_id="inv-a",
        attempt_id="attempt-a",
        principal_id="hp-" + "4" * 32,
        credential_id="hpc-" + "5" * 32,
        mechanism_id=REAL_AUTHENTICATOR_ID,
        approval_subject_digest=evidence.approval_subject_digest,
        challenge_digest="6" * 64,
        occurred_at="2026-08-28T00:00:00Z",
        resolved_presentation=evidence,
    )
    lifecycle.record_assertion(proof_id=PROOF_ID, assertion_digest="a" * 64, occurred_at="2026-08-28T00:00:01Z")
    lifecycle.record_verified(
        proof_id=PROOF_ID,
        proof_digest="b" * 64,
        registry_state_digest="c" * 64,
        verifier_version="v1",
        occurred_at="2026-08-28T00:00:02Z",
    )
    lifecycle.bind_gate5(proof_id=PROOF_ID, approval_digest="d" * 64, occurred_at="2026-08-28T00:00:03Z")
    with pytest.raises(HPACLifecycleForkError):
        lifecycle.bind_gate5(proof_id=PROOF_ID, approval_digest="e" * 64, occurred_at="2026-08-28T00:00:04Z")


# Gate 9 and production coupling ---------------------------------------------------


def test_gate9_primitive_is_inert_and_duplicate_create_only(tmp_path: Path):
    record = _inert_consumption_record()
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    store.create(PROOF_ID, record)
    assert store.resolve(PROOF_ID) == record
    with pytest.raises(HPACDuplicateError):
        store.create(PROOF_ID, record)
    assert [path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()] == [
        f"proofs/v2/{PROOF_ID}/consumption.json"
    ]


def test_new_hpac_modules_have_zero_preexisting_production_consumers():
    core_dir = Path(inspect.getfile(HumanPrincipalRegistryStore)).parent
    new_modules = {
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
    owning_files = {module.rsplit(".", 1)[-1] + ".py" for module in new_modules}
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5 introduces the first legitimate
    # consumer of this foundation: the mechanism-neutral HPAC verifier
    # itself (that is exactly this repository's planned Layer-3-consumes-
    # Layer-1/2 architecture, `...1R.4` planning doc §6). Excluding it here
    # preserves this test's original intent -- no *unexpected* consumer --
    # without re-freezing "zero consumers ever" past the phase whose whole
    # purpose is to add the one sanctioned consumer.
    expected_consumers = {"hpac_verifier.py"}
    consumers: list[tuple[str, str]] = []
    for path in core_dir.glob("*.py"):
        if path.name in owning_files or path.name in expected_consumers:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in new_modules:
                consumers.append((path.name, node.module))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in new_modules:
                        consumers.append((path.name, alias.name))
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.2 (V-15-2) re-baseline: this is
    # a phase-aware SUBSET invariant, not a frozen point-in-time snapshot.
    # The planned Layer-1/2 foundation is consumed only by the explicitly
    # enumerated, phase-authorized gate coordinators below; any *other*
    # production file importing the foundation still fails this guard
    # (`observed - AUTHORIZED == set()`), and a not-yet-built gate module
    # name is not pre-authorized.
    #
    #   * `runtime_dispatch_gate5.py` -> `hpac_lifecycle` — `.1R.10` impl /
    #     `.1R.11` verified: read-only `resolve_gate5_binding_event` +
    #     `STATE_PROOF_VERIFIED_AND_BOUND` only; no writer capability.
    #   * `runtime_dispatch_gate9.py` -> `hpac_foundation` /
    #     `hpac_lifecycle` / `runtime_invocation_authority_consumption` —
    #     `.1R.14` impl / `.1R.15` verified (Gate-9 atomic authority
    #     consumption coordinator): the create-only atomic primitive
    #     (`write_atomic_create_only`, `HPACDuplicateError`), the read-only
    #     lifecycle sequence-3 confirm, and the closed consumption record.
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
        # digest *utilities* only -- `require_safe_relative_id_component`,
        # `canonical_digest`, `reject_symlink`, `read_canonical_json_document`,
        # `HPACMalformedError`. Neither module writes an HPAC principal,
        # presentation, proof, lifecycle event, or consumption record; the
        # non-authoritative `RuntimeInvocationRecord` grants no effect authority
        # (`GRANTS_NO_EFFECT_AUTHORITY`). `.1R.16` §36.1 / §38 authorizes the
        # Slice-B production-file set. Any *other* importer of the foundation
        # still trips this guard (`observed - AUTHORIZED == set()`).
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
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (N-16-5 merged RHAMP
        # `.1R.30` bundle — Decision A / RE-MERGE). The RHAMP credential
        # sidecar / counter-state stores, the native-CTAP2 client-context
        # builder, the FIDO2 authenticator, the real-assertion verification
        # core, and the enrollment ceremony consume the Layer-1/2 foundation
        # utilities (canonical digest / atomic-create-only / symlink-safety /
        # the registry + proof + authenticator dataclasses). The sidecar /
        # counter / ctap2 / assertion-verify modules are import-reachable
        # from `hpac_verifier` (Layer 3, already the one sanctioned
        # consumer); the enrollment ceremony is inside the non-agent-
        # importable admin-writer fence (its own guard keeps it off every
        # agent-reachable path). Exact filenames, no wildcard.
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
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 (N-16-5 protected
        # human-approval presentation + real-assurance consumption). The
        # HPAC-PPA-001 v1.0 installation store, the sole PAWA
        # configure_presentation_mechanism consumer, and the trusted launcher
        # mediator consume the Layer-1/2 foundation for the canonical-JSON /
        # digest / atomic-write / symlink-safety utilities plus the existing
        # HPAC-REQ-090 descriptor / HPAC-REQ-091 evidence stores. The launcher
        # is import-reachable from `hpac_verifier` (Layer 3, already the one
        # sanctioned consumer) only for the resolver-side attestation verifier
        # (no fence import on that path); the admin module is inside the
        # non-agent-importable fence (its own guard keeps it off every
        # agent-reachable path). Exact filenames, no wildcard.
        ("protected_presentation_installation.py", "pcae.core.approval_presentation"),
        ("protected_presentation_installation.py", "pcae.core.hpac_foundation"),
        ("protected_presentation.py", "pcae.core.approval_presentation"),
        ("protected_presentation.py", "pcae.core.hpac_foundation"),
        ("hpac_protected_presentation_admin.py", "pcae.core.hpac_foundation"),
    }
    unauthorized = set(consumers) - AUTHORIZED_CONSUMERS
    assert unauthorized == set(), (
        f"unauthorized production consumer(s) of the HPAC Layer-1/2 foundation: "
        f"{sorted(unauthorized)}"
    )


def test_gate9_module_has_no_pb_runtime_dispatch_or_external_effect_imports():
    module = importlib.import_module("pcae.core.runtime_invocation_authority_consumption")
    tree = ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    forbidden = {
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
    assert imported.isdisjoint(forbidden)


def test_no_real_mechanism_or_protected_ui_implementation_exists_in_phase_modules():
    core_dir = Path(inspect.getfile(HumanPrincipalRegistryStore)).parent
    phase_files = (
        "hpac_foundation.py",
        "human_principal_registry.py",
        "human_authenticator.py",
        "human_authenticator_deterministic.py",
        "approval_presentation.py",
        "approval_presentation_deterministic.py",
        "human_authentication_proof.py",
        "hpac_lifecycle.py",
        "runtime_invocation_authority_consumption.py",
    )
    imported_modules: set[str] = set()
    defined_names: set[str] = set()
    for filename in phase_files:
        tree = ast.parse((core_dir / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name.lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.lower())
            elif isinstance(node, ast.Import):
                imported_modules.update(alias.name.lower() for alias in node.names)
    forbidden_fragments = ("fido", "webauthn", "ctap", "pam", "biometric", "keychain")
    assert not any(fragment in name for fragment in forbidden_fragments for name in imported_modules)
    assert not any(name.startswith(("enroll_cli", "approval_cli", "protected_ui")) for name in defined_names)

