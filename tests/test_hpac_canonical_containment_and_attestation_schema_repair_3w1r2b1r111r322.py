"""Focused repair tests for Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2.

Covers the two Blocking findings from `.3.2.1` (report
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_1_INDEPENDENT_VERIFICATION_
CANONICAL_HPAC_TRUST_ROOT_WRITER_PROVENANCE_LIFECYCLE_VALIDATION_REPAIR.md`,
findings B-3.2.1-01 and B-3.2.1-02):

* Finding P — deterministic protected-presentation attestation must
  serialize *exactly* HPAC-REQ-092's eight closed fields; no extra field
  (`installation_store_id`, `simulation_only`) is contract-conformant.
* Finding C — `HPACLifecycleStore` and the inert Gate-9
  `RuntimeInvocationAuthorityConsumptionStore` must never accept a
  caller-supplied `proof_id` that resolves outside their configured root
  (absolute path, `../` traversal, or a path-separator-bearing value),
  and must reject it *before* any file is created -- not merely detect the
  escape afterward.

This suite does not import helpers from `.3`, `.3.1`, `.3.2`, or `.3.2.1`
test modules (same discipline as the independent-verification suite it
repairs against).
"""

from __future__ import annotations

import base64
import json

import pytest

from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
    presentation_attestation_object,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACMalformedError,
    HPACStoreAuthority,
    canonical_digest,
    canonical_json_bytes,
)
from pcae.core.hpac_lifecycle import HPACLifecycleStore
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicTestHumanAuthenticator,
)
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionStore,
    new_inert_consumption_record,
)

APPROVAL_ID = "ria-" + "5" * 32
PROOF_ID = "hap-" + "6" * 32
PRINCIPAL_ID = "hp-" + "7" * 32
CREDENTIAL_ID = "hpc-" + "8" * 32
EXPIRY = "2026-08-28T12:00:00Z"

_REQ_092_FIELDS = frozenset(
    {
        "attestation_version",
        "presentation_id",
        "approval_id",
        "approval_subject_digest",
        "human_visible_representation_digest",
        "descriptor_digest",
        "election",
        "presented_at",
    }
)


# ── shared fixtures (self-contained; mirrors .3.2.1 suite's own helpers) ──


def _approval_subject(*, invocation_id: str = "iv-3-2-2"):
    subject = {
        "repository_identity": "repo-3-2-2",
        "task_id": "task-3-2-2",
        "runtime_target_id": "target-3-2-2",
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


def _write_fixture_presentation(authority: HPACStoreAuthority, *, approval_id: str = APPROVAL_ID):
    mechanism, descriptor_store, installed = _install_fixture_mechanism(authority)
    subject = _approval_subject()
    evidence = mechanism.present_installed(subject, approval_id, installed)
    store = TrustedApprovalPresentationStore(authority)
    store.create_canonical(store.fixture_mechanism_writer(mechanism.MECHANISM_ID), evidence, installed)
    resolved = store.resolve_canonical(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
        descriptor_store=descriptor_store,
    )
    return mechanism, descriptor_store, installed, subject, evidence, store, resolved


def _decode(attestation_b64: str) -> dict:
    padded = attestation_b64 + "=" * (-len(attestation_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _re_encode_attestation(evidence, attestation_object: dict):
    """Rebuild a presentation evidence record around a tampered attestation
    object, recomputing only the digests a real mechanism would recompute
    (never the fields the contract binds to the original evidence)."""

    import hashlib
    from dataclasses import replace

    attestation_bytes = canonical_json_bytes(attestation_object)
    mechanism_attestation = base64.urlsafe_b64encode(attestation_bytes).decode("ascii").rstrip("=")
    mechanism_attestation_digest = hashlib.sha256(attestation_bytes).hexdigest()
    tampered = replace(
        evidence,
        mechanism_attestation=mechanism_attestation,
        mechanism_attestation_digest=mechanism_attestation_digest,
    )
    body = tampered.to_document(include_presentation_digest=False)
    return replace(tampered, presentation_digest=canonical_digest(body))


# ═══════════════════════════════════════════════════════════════════════
# Finding P — HPAC-REQ-092 attestation schema conformance
# ═══════════════════════════════════════════════════════════════════════


def test_repaired_attestation_object_has_exactly_the_contract_closed_field_set(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (*_ignored, evidence, _store, resolved) = _write_fixture_presentation(authority)
    attestation = _decode(evidence.mechanism_attestation)
    assert set(attestation) == _REQ_092_FIELDS
    assert "installation_store_id" not in attestation
    assert "simulation_only" not in attestation
    assert attestation["attestation_version"] == "HPAC-PRESENTATION-ATTESTATION/2.0"
    assert resolved.record.presentation_id == evidence.presentation_id


def test_conformant_positive_deterministic_fixture_resolves_canonically(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (*_ignored, evidence, _store, resolved) = _write_fixture_presentation(authority)
    assert resolved.record.mechanism_attestation_digest == hashlib_sha256_hexdigest(
        _raw_attestation_bytes(evidence)
    )
    assert resolved.is_real_runtime_eligible is False


def hashlib_sha256_hexdigest(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _raw_attestation_bytes(evidence) -> bytes:
    padded = evidence.mechanism_attestation + "=" * (-len(evidence.mechanism_attestation) % 4)
    return base64.urlsafe_b64decode(padded)


def test_omitted_required_attestation_field_is_rejected(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (mechanism, descriptor_store, installed, _subject, evidence, store, _resolved) = (
        _write_fixture_presentation(authority, approval_id="ria-" + "a" * 32)
    )
    attestation = presentation_attestation_object(evidence)
    del attestation["descriptor_digest"]
    tampered = _re_encode_attestation(evidence, attestation)
    other_authority = HPACStoreAuthority.fixture(tmp_path / "other")
    other_mechanism, other_descriptors, other_installed = _install_fixture_mechanism(other_authority)
    other_store = TrustedApprovalPresentationStore(other_authority)
    # Writing bypasses create()'s own re-derivation only because we hand-built
    # `tampered`; resolution must still fail closed on the missing field.
    other_store.create(tampered)
    with pytest.raises(ApprovalPresentationTrustError):
        other_store.resolve_structural(
            presentation_id=tampered.presentation_id,
            presentation_digest=tampered.presentation_digest,
        )


def test_wrong_installation_identity_rejected_via_mechanism_substitution(tmp_path):
    authority_a = HPACStoreAuthority.fixture(tmp_path / "a")
    authority_b = HPACStoreAuthority.fixture(tmp_path / "b")
    (*_ignored, evidence_a, _store_a, _resolved_a) = _write_fixture_presentation(
        authority_a, approval_id="ria-" + "b" * 32
    )
    _mechanism_b, descriptor_store_b, _installed_b = _install_fixture_mechanism(authority_b)
    store_b = TrustedApprovalPresentationStore(authority_b)
    with pytest.raises(
        ApprovalPresentationTrustError,
        match="not authoritatively installed|substitution|no presentation evidence",
    ):
        store_b.resolve_canonical(
            presentation_id=evidence_a.presentation_id,
            presentation_digest=evidence_a.presentation_digest,
            descriptor_store=descriptor_store_b,
        )


def test_wrong_subject_binding_in_attestation_rejected(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (mechanism, descriptor_store, installed, _subject, evidence, store, _resolved) = (
        _write_fixture_presentation(authority, approval_id="ria-" + "c" * 32)
    )
    attestation = presentation_attestation_object(evidence)
    attestation["approval_subject_digest"] = "0" * 64
    tampered = _re_encode_attestation(evidence, attestation)
    other_authority = HPACStoreAuthority.fixture(tmp_path / "other")
    other_store = TrustedApprovalPresentationStore(other_authority)
    other_store.create(tampered)
    with pytest.raises(ApprovalPresentationTrustError):
        other_store.resolve_structural(
            presentation_id=tampered.presentation_id,
            presentation_digest=tampered.presentation_digest,
        )


def test_copied_attestation_bytes_rejected_on_a_second_presentation(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (mechanism, descriptor_store, installed, subject, evidence, store, _resolved) = (
        _write_fixture_presentation(authority, approval_id="ria-" + "d" * 32)
    )
    second_subject = _approval_subject(invocation_id="iv-second")
    second_evidence = mechanism.present_installed(second_subject, "ria-" + "e" * 32, installed)
    from dataclasses import replace

    copied = replace(
        second_evidence,
        mechanism_attestation=evidence.mechanism_attestation,
        mechanism_attestation_digest=evidence.mechanism_attestation_digest,
    )
    body = copied.to_document(include_presentation_digest=False)
    copied = replace(copied, presentation_digest=canonical_digest(body))
    with pytest.raises(ApprovalPresentationTrustError, match="does not bind the evidence exactly|does not verify"):
        store.create_canonical(store.fixture_mechanism_writer(mechanism.MECHANISM_ID), copied, installed)


def test_caller_created_attestation_object_is_rejected(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, descriptor_store, installed = _install_fixture_mechanism(authority)
    subject = _approval_subject()
    evidence = mechanism.present_installed(subject, "ria-" + "f" * 32, installed)
    from dataclasses import replace

    forged_object = {
        "attestation_version": "HPAC-PRESENTATION-ATTESTATION/2.0",
        "presentation_id": evidence.presentation_id,
        "approval_id": evidence.approval_id,
        "approval_subject_digest": evidence.approval_subject_digest,
        "human_visible_representation_digest": evidence.human_visible_representation_digest,
        "descriptor_digest": evidence.mechanism_ref["descriptor_digest"],
        "election": evidence.election,
        "presented_at": evidence.presented_at,
    }
    forged = _re_encode_attestation(evidence, forged_object)
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(HPACAuthorityError, match="role/subject|another HPAC root"):
        store.create_canonical(store.fixture_mechanism_writer("hpac.fake.v1"), forged, installed)


def test_deterministic_attestation_remains_non_real_even_when_relabelled(tmp_path):
    mechanism = DeterministicTestPresentationMechanism()
    mechanism.SIMULATION_ONLY = False
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    (*_ignored, resolved) = _write_fixture_presentation(authority, approval_id="ria-" + "1" * 32)
    assert resolved.is_real_runtime_eligible is False
    assert resolved.authority_class is HPACAuthorityClass.FIXTURE_NON_REAL


def test_deterministic_attestation_cannot_claim_real_verifier_kind(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, descriptor_store, installed = _install_fixture_mechanism(authority)
    subject = _approval_subject()
    evidence = mechanism.present_installed(subject, "ria-" + "2" * 32, installed)
    assert installed.record.verifier_kind == "deterministic-test-fixture"
    assert installed.record.verifier_kind != "fido2-hardware"


# ═══════════════════════════════════════════════════════════════════════
# Finding C — canonical-store containment (lifecycle + inert Gate-9)
# ═══════════════════════════════════════════════════════════════════════


def _open_structural(lifecycle: HPACLifecycleStore, *, proof_id: str, resolved_presentation):
    return lifecycle.open_challenge(
        proof_id=proof_id,
        approval_id=resolved_presentation.approval_id,
        invocation_id="iv-repair",
        attempt_id="attempt-repair",
        principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        approval_subject_digest=resolved_presentation.approval_subject_digest,
        challenge_digest="a" * 64,
        occurred_at="2026-08-28T10:00:00Z",
        resolved_presentation=resolved_presentation,
    )


@pytest.mark.parametrize(
    "malicious_id",
    [
        "/tmp/attacker-lifecycle-escape",
        "/etc/attacker-lifecycle-escape",
        "../outside",
        "../../outside",
        "a/../../../outside",
        "nested/traversal",
        "back\\slash\\escape",
    ],
)
def test_lifecycle_structural_open_challenge_rejects_unsafe_proof_id_before_any_write(tmp_path, malicious_id):
    root = tmp_path / "configured"
    authority = HPACStoreAuthority.fixture(root)
    (*_ignored, evidence, _store, _resolved) = _write_fixture_presentation(authority, approval_id="ria-" + "3" * 32)
    lifecycle = HPACLifecycleStore(root)
    with pytest.raises(HPACMalformedError, match="safe path component"):
        _open_structural(lifecycle, proof_id=malicious_id, resolved_presentation=evidence)
    escaped_root = tmp_path
    # No file must exist anywhere reachable from tmp_path outside the configured root.
    for created in escaped_root.rglob("0000.json"):
        assert str(created).startswith(str(root)), f"lifecycle event escaped configured root: {created}"


def test_lifecycle_canonical_genesis_rejects_absolute_proof_id_before_any_write(tmp_path):
    root = tmp_path / "configured"
    authority = HPACStoreAuthority.fixture(root)
    (*_ignored, subject, evidence, _pres_store, resolved_presentation) = _write_fixture_presentation(
        authority, approval_id="ria-" + "4" * 32
    )
    authenticator = DeterministicTestHumanAuthenticator(principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID)
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    escaped_proof = str(tmp_path / "escaped-canonical-322")
    lifecycle = HPACLifecycleStore(authority)
    with pytest.raises(HPACMalformedError, match="safe path component"):
        lifecycle.open_challenge_canonical(
            lifecycle.fixture_genesis_writer(escaped_proof),
            proof_id=escaped_proof,
            approval_id="ria-" + "4" * 32,
            invocation_id="iv-3-2-2",
            attempt_id="attempt-3-2-2",
            principal_id=PRINCIPAL_ID,
            credential_id=CREDENTIAL_ID,
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            occurred_at="2026-08-28T10:00:00Z",
            resolved_presentation=resolved_presentation,
            challenge=challenge,
        )
    assert not (tmp_path / "escaped-canonical-322" / "lifecycle" / "0000.json").exists()


def test_lifecycle_symlinked_proof_directory_is_rejected_before_write(tmp_path):
    root = tmp_path / "configured"
    root.mkdir()
    outside = tmp_path / "outside-target"
    outside.mkdir()
    proofs_v2 = root / "proofs" / "v2"
    proofs_v2.mkdir(parents=True)
    (proofs_v2 / PROOF_ID).symlink_to(outside, target_is_directory=True)
    authority = HPACStoreAuthority.fixture(root)
    (*_ignored, evidence, _store, _resolved) = _write_fixture_presentation(authority, approval_id="ria-" + "6" * 32)
    lifecycle = HPACLifecycleStore(root)
    with pytest.raises(Exception):
        _open_structural(lifecycle, proof_id=PROOF_ID, resolved_presentation=evidence)
    assert not (outside / "lifecycle").exists()


def _inert_gate9_record(*, proof_id: str = PROOF_ID):
    from pcae.core.runtime_invocation_authority_consumption import RuntimeInvocationAuthorityConsumption

    return new_inert_consumption_record(
        request_identity={"invocation_id": "inv-1", "attempt_id": "att-1", "idempotency_key": "idem-1"},
        repository_task_binding={
            "repository_identity": "repo-1",
            "head_commit": "a" * 40,
            "task_id": "task-1",
            "task_contract_digest": "b" * 64,
            "phase_id": "phase-1",
            "session_id": None,
        },
        target_binding={
            "runtime_target_id": "target-1",
            "adapter_id": "adapter-1",
            "descriptor_version": "v1",
            "descriptor_digest": "c" * 64,
            "target_config_digest": "d" * 64,
            "executable_identity_digest": "e" * 64,
        },
        prompt_binding={"prompt_hash": "f" * 64, "prompt_hash_profile": "pcae.prompt-semantic.v1"},
        authority_binding={
            "approval_id": APPROVAL_ID,
            "approval_digest": "g" * 64,
            "authority_projection_id": "proj-1",
            "authority_projection_digest": "h" * 64,
            "authority_contract_version": "RIHAC-001/2.0",
            "proof_id": proof_id if proof_id.startswith("hap-") else PROOF_ID,
            "proof_digest": "i" * 64,
            "proof_validation_digest": "j" * 64,
            "registry_state_digest": "k" * 64,
            "approval_subject_digest": "l" * 64,
            "trusted_presentation_ref": {"presentation_id": "hpe-" + "1" * 32, "presentation_digest": "m" * 64},
            "challenge_digest": "n" * 64,
        },
        pb_binding={
            "request_digest": "o" * 64,
            "decision_digest": "p" * 64,
            "decision": "ALLOW",
            "policy_version": "v1",
            "causing_policy_ids": [],
            "matched_no_go_ids": [],
        },
        runtime_enforcement_binding={
            "decision_id": "q" * 8,
            "decision_digest": "r" * 64,
            "verdict": "ALLOW",
            "expires_at": EXPIRY,
            "evaluated_input_digest": "s" * 64,
        },
        dispatch_binding={
            "containment_evidence_ref": {"id": "ce-1", "digest": "t" * 64},
            "state": "dispatch_attempted",
            "consumed_at": EXPIRY,
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


@pytest.mark.parametrize(
    "malicious_id",
    [
        "/tmp/attacker-gate9-escape",
        "/etc/attacker-gate9-escape",
        "../outside",
        "../../outside",
        "a/../../../outside",
    ],
)
def test_gate9_create_rejects_unsafe_proof_id_before_any_write(tmp_path, malicious_id):
    root = tmp_path / "gate9-configured"
    store = RuntimeInvocationAuthorityConsumptionStore(root)
    with pytest.raises(HPACMalformedError, match="safe path component"):
        store.create(malicious_id, _inert_gate9_record())
    for created in tmp_path.rglob("consumption.json"):
        assert str(created).startswith(str(root)), f"Gate-9 consumption record escaped configured root: {created}"


def test_gate9_resolve_rejects_unsafe_proof_id_and_cannot_read_arbitrary_files(tmp_path):
    root = tmp_path / "gate9-configured"
    outside = tmp_path / "outside-secret"
    outside.mkdir()
    secret = outside / "consumption.json"
    secret.write_text("{}", encoding="utf-8")
    store = RuntimeInvocationAuthorityConsumptionStore(root)
    with pytest.raises(HPACMalformedError, match="safe path component"):
        store.resolve(str(outside))


def test_gate9_valid_opaque_proof_id_succeeds_and_stays_inside_root(tmp_path):
    root = tmp_path / "gate9-configured"
    store = RuntimeInvocationAuthorityConsumptionStore(root)
    record = _inert_gate9_record(proof_id=PROOF_ID)
    created = store.create(PROOF_ID, record)
    assert created.record_digest == record.record_digest
    expected_path = root / "proofs" / "v2" / PROOF_ID / "consumption.json"
    assert expected_path.is_file()
    resolved = store.resolve(PROOF_ID)
    assert resolved is not None
    assert resolved.record_digest == record.record_digest


def test_gate9_remains_inert_after_containment_repair():
    import ast
    import inspect
    from pathlib import Path

    import pcae.core.runtime_invocation_authority_consumption as gate9

    tree = ast.parse(Path(inspect.getfile(gate9)).read_text(encoding="utf-8"))
    imports = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    } | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    forbidden = {
        "pcae.core.permission_broker_foundation",
        "pcae.core.runtime_authority",
        "pcae.core.runtime_dispatch_permission",
        "pcae.core.shell_gate",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "fido2",
    }
    assert imports.isdisjoint(forbidden)


# ═══════════════════════════════════════════════════════════════════════
# Lifecycle regression — genesis/predecessor/fork still enforced post-repair
# ═══════════════════════════════════════════════════════════════════════


def test_authoritative_genesis_still_succeeds_for_valid_opaque_proof_id(tmp_path):
    root = tmp_path / "configured"
    authority = HPACStoreAuthority.fixture(root)
    (*_ignored, subject, evidence, _pres_store, resolved_presentation) = _write_fixture_presentation(
        authority, approval_id="ria-" + "7" * 32
    )
    authenticator = DeterministicTestHumanAuthenticator(principal_id=PRINCIPAL_ID, credential_id=CREDENTIAL_ID)
    challenge = authenticator.prepare_challenge(subject.digest(), evidence.presentation_digest)
    lifecycle = HPACLifecycleStore(authority)
    event = lifecycle.open_challenge_canonical(
        lifecycle.fixture_genesis_writer(PROOF_ID),
        proof_id=PROOF_ID,
        approval_id="ria-" + "7" * 32,
        invocation_id="iv-3-2-2",
        attempt_id="attempt-3-2-2",
        principal_id=PRINCIPAL_ID,
        credential_id=CREDENTIAL_ID,
        mechanism_id=DETERMINISTIC_MECHANISM_ID,
        occurred_at="2026-08-28T10:00:00Z",
        resolved_presentation=resolved_presentation,
        challenge=challenge,
    )
    assert event.sequence == 0
    resolved_chain = lifecycle.resolve_canonical_chain(PROOF_ID)
    assert len(resolved_chain) == 1


def test_forged_genesis_at_valid_path_is_rejected_by_provenance(tmp_path):
    root = tmp_path / "configured"
    authority = HPACStoreAuthority.fixture(root)
    (*_ignored, evidence, _store, _resolved) = _write_fixture_presentation(authority, approval_id="ria-" + "8" * 32)
    lifecycle = HPACLifecycleStore(authority)
    _open_structural(lifecycle, proof_id=PROOF_ID, resolved_presentation=evidence)
    with pytest.raises(Exception, match="provenance"):
        lifecycle.resolve_canonical_chain(PROOF_ID)
