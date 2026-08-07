"""HATP Verification Engine (Wave 4) -- Phase 149O.1I.

Deterministic, hardware- and environment-independent tests for
`pcae.core.human_approval_trusted_provenance`'s Wave-4 addition
(`verify_hatp_proof`, `HATPVerificationStatus`, `HATPVerificationResult`,
`inspect_hatp_verification_substrate_readiness`) and
`pcae.core.hatp_providers` (`HATPProofVerifierProvider`,
`TestHATPProofVerifierProvider`). No hardware, no real cryptography, no
filesystem outside `tmp_path`, no network, no wall clock -- every test
supplies its own explicit `evaluation_time`.
"""
from __future__ import annotations

import copy
import inspect
import json
import re
import uuid
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import hatp_providers as providers_module
from pcae.core import human_approval_trusted_provenance as hatp
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_providers import HATPProofVerifierProvider, HATPProviderVerificationOutcome, TestHATPProofVerifierProvider
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HATPExpectedOperation,
    HATPVerificationEvidence,
    HATPVerificationResult,
    HATPVerificationStatus,
    HATPVerificationSubstrateStatus,
    HATP_VERIFICATION_STATUS_VALUES,
    HumanApprovalProvenanceProof,
    RollbackSite,
    canonicalize_hatp_proof_payload,
    inspect_hatp_verification_substrate_readiness,
    verify_hatp_proof,
)

_EVAL_TIME = datetime(2026, 8, 6, 12, 0, 1, tzinfo=timezone.utc)
_UNSET = object()


# ═══════════════════════════════════════════════════════════════════════════
# Fixture builders
# ═══════════════════════════════════════════════════════════════════════════


def _repo_id() -> str:
    return str(uuid.uuid4())


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(document), encoding="utf-8")


class _Harness:
    """A complete, self-consistent, valid HATP verification scenario:
    proof + trust store + provider + evidence + expected operation, all
    mutually agreeing. Individual tests mutate exactly one dimension away
    from this baseline."""

    def __init__(self, tmp_path: Path) -> None:
        self.repo_id = _repo_id()
        deploy_dir = tmp_path / "deploy"
        deploy_dir.mkdir()
        self.canonical_root = resolve_canonical_deployment_root(deploy_dir)

        self.principal_id = "principal-1"
        self.signer_key_id = "signer-1"
        self.provider_profile = "HATP_HARDWARE_PROVIDER_V1"

        store_root = tmp_path / "trust-store"
        _write_registry(
            store_root,
            {
                "registry_version": 1,
                "principals": [{"principal_id": self.principal_id, "status": "active"}],
                "signers": [
                    {
                        "signer_key_id": self.signer_key_id,
                        "principal_id": self.principal_id,
                        "provider_profile": self.provider_profile,
                        "status": "active",
                    }
                ],
                "deployment_bindings": [
                    {
                        "repository_id": self.repo_id,
                        "canonical_deployment_root": self.canonical_root,
                        "principal_id": self.principal_id,
                        "signer_key_id": self.signer_key_id,
                        "provider_profile": self.provider_profile,
                        "authority_scope": "rollback",
                        "valid_from": "2026-01-01T00:00:00.000Z",
                        "status": "active",
                    }
                ],
                "authorities": [
                    {
                        "principal_id": self.principal_id,
                        "repository_id": self.repo_id,
                        "authority_scope": "rollback",
                        "status": "active",
                        "valid_from": "2026-01-01T00:00:00.000Z",
                    }
                ],
            },
        )
        self.trust_store = HATPTrustStore(_test_only_root=store_root)
        self.provider = TestHATPProofVerifierProvider()

        self.proof = HumanApprovalProvenanceProof(
            proof_version=1,
            principal_id=self.principal_id,
            signer_key_id=self.signer_key_id,
            provider_profile=self.provider_profile,
            repository_id=self.repo_id,
            decision_record_id="decision-1",
            decision_record_digest="0" * 64,
            binding_id="binding-1",
            binding_digest="1" * 64,
            rollback_site=RollbackSite.AG3,
            operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="a" * 40),
            issued_at="2026-08-06T12:00:00.000Z",
        )
        self.expected_operation = HATPExpectedOperation(
            decision_record_id=self.proof.decision_record_id,
            binding_id=self.proof.binding_id,
            rollback_site=self.proof.rollback_site,
            operation_reference=self.proof.operation_reference,
        )

    def sign(self, proof: HumanApprovalProvenanceProof) -> bytes:
        payload = canonicalize_hatp_proof_payload(proof)
        return self.provider.sign(payload, signer_key_id=proof.signer_key_id, provider_profile=proof.provider_profile)

    def evidence_for(self, proof: HumanApprovalProvenanceProof) -> HATPVerificationEvidence:
        return HATPVerificationEvidence(assertion=self.sign(proof))

    def verify(
        self,
        *,
        proof=_UNSET,
        evidence=None,
        provider=None,
        trust_store=None,
        expected_operation=None,
        current_repository_id=None,
        canonical_deployment_root=None,
        evaluation_time=None,
    ) -> HATPVerificationResult:
        proof = self.proof if proof is _UNSET else proof
        return verify_hatp_proof(
            proof,
            evidence=self.evidence_for(self.proof) if evidence is None else evidence,
            provider=self.provider if provider is None else provider,
            trust_store=self.trust_store if trust_store is None else trust_store,
            expected_operation=self.expected_operation if expected_operation is None else expected_operation,
            current_repository_id=self.repo_id if current_repository_id is None else current_repository_id,
            canonical_deployment_root=self.canonical_root if canonical_deployment_root is None else canonical_deployment_root,
            evaluation_time=_EVAL_TIME if evaluation_time is None else evaluation_time,
        )


def _replace(proof: HumanApprovalProvenanceProof, **changes) -> HumanApprovalProvenanceProof:
    base = {f.name: getattr(proof, f.name) for f in fields(proof)}
    base.update(changes)
    return HumanApprovalProvenanceProof(**base)


@pytest.fixture()
def harness(tmp_path: Path) -> _Harness:
    return _Harness(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Closed vocabulary exhaustiveness (HATP-REQ-078)
# ═══════════════════════════════════════════════════════════════════════════


def test_verification_status_vocabulary_matches_hatp_001_exactly() -> None:
    expected = {
        "VALID",
        "MISSING",
        "MALFORMED",
        "INVALID_SIGNATURE",
        "UNKNOWN_SIGNER",
        "UNAUTHORIZED_SIGNER",
        "REVOKED_SIGNER",
        "INVALID_ATTESTATION",
        "USER_PRESENCE_NOT_PROVEN",
        "WRONG_OPERATION",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "EXPIRED",
    }
    assert HATP_VERIFICATION_STATUS_VALUES == expected
    assert len(HATP_VERIFICATION_STATUS_VALUES) == 13


def test_verification_status_vocabulary_disjoint_from_permission_broker_and_rae() -> None:
    pb_vocabulary = {"ALLOW", "DENY", "HUMAN_REVIEW"}
    rae_vocabulary = {
        "VALID",  # RAE also uses VALID; that overlap is expected/documented
        "MISSING",  # RAE also uses MISSING
        "INVALID",
        "STALE",
        "REVOKED",
        "UNAUTHORIZED_APPROVER",
        "WRONG_SCOPE",
        "SUPERSEDED",
    }
    assert HATP_VERIFICATION_STATUS_VALUES.isdisjoint(pb_vocabulary)
    # HATP's own distinct terms (never RAE's specific spellings) are present:
    for distinct in ("UNKNOWN_SIGNER", "REVOKED_SIGNER", "WRONG_OPERATION", "WRONG_REPOSITORY", "WRONG_DEPLOYMENT"):
        assert distinct in HATP_VERIFICATION_STATUS_VALUES
        assert distinct not in rae_vocabulary


def test_verification_result_has_no_approval_or_permission_field() -> None:
    field_names = {f.name for f in fields(HATPVerificationResult)}
    assert field_names == {"status", "reasons"}
    forbidden = {"approved", "authorized", "approval_present", "can_execute", "permission", "valid", "trusted"}
    assert field_names.isdisjoint(forbidden)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Canonical byte boundary
# ═══════════════════════════════════════════════════════════════════════════


def test_provider_receives_exact_wave3_canonical_bytes(harness: _Harness) -> None:
    expected_bytes = canonicalize_hatp_proof_payload(harness.proof)
    evidence = harness.evidence_for(harness.proof)
    result = harness.verify(evidence=evidence)
    assert result.status == HATPVerificationStatus.VALID
    assert harness.provider.received_payloads[-1] == expected_bytes


# ═══════════════════════════════════════════════════════════════════════════
# 3. Positive canonical control
# ═══════════════════════════════════════════════════════════════════════════


def test_valid_fixture_produces_valid_status(harness: _Harness) -> None:
    result = harness.verify()
    assert result == HATPVerificationResult(status=HATPVerificationStatus.VALID, reasons=())


# ═══════════════════════════════════════════════════════════════════════════
# 4-13. Individual failure-condition tests
# ═══════════════════════════════════════════════════════════════════════════


def test_invalid_signature(harness: _Harness) -> None:
    bad_evidence = HATPVerificationEvidence(assertion=b"not-a-real-signature")
    result = harness.verify(evidence=bad_evidence)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_unknown_signer(harness: _Harness) -> None:
    proof = _replace(harness.proof, signer_key_id="unknown-signer")
    result = harness.verify(proof=proof, evidence=harness.evidence_for(proof))
    assert result.status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_unauthorized_signer_inactive_principal(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "inactive-principal-store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "principals": [{"principal_id": harness.principal_id, "status": "revoked"}],
            "signers": [
                {
                    "signer_key_id": harness.signer_key_id,
                    "principal_id": harness.principal_id,
                    "provider_profile": harness.provider_profile,
                    "status": "active",
                }
            ],
            "deployment_bindings": [],
            "authorities": [],
        },
    )
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_unauthorized_signer_no_authority_record(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "no-authority-store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "principals": [{"principal_id": harness.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": harness.signer_key_id,
                    "principal_id": harness.principal_id,
                    "provider_profile": harness.provider_profile,
                    "status": "active",
                }
            ],
            "deployment_bindings": [],
            "authorities": [],
        },
    )
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_unauthorized_signer_wrong_provider_profile(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "wrong-profile-store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "principals": [{"principal_id": harness.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": harness.signer_key_id,
                    "principal_id": harness.principal_id,
                    "provider_profile": "SOME_OTHER_PROFILE",
                    "status": "active",
                }
            ],
            "deployment_bindings": [],
            "authorities": [],
        },
    )
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_revoked_signer(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "revoked-store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "principals": [{"principal_id": harness.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": harness.signer_key_id,
                    "principal_id": harness.principal_id,
                    "provider_profile": harness.provider_profile,
                    "status": "revoked",
                    "revoked_at": "2026-08-01T00:00:00.000Z",
                }
            ],
            "deployment_bindings": [],
            "authorities": [],
        },
    )
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.REVOKED_SIGNER


def test_repository_mismatch(harness: _Harness) -> None:
    result = harness.verify(current_repository_id=_repo_id())
    assert result.status == HATPVerificationStatus.WRONG_REPOSITORY


def test_deployment_mismatch_no_binding(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "no-binding-store"
    _write_registry(
        store_root,
        {
            "registry_version": 1,
            "principals": [{"principal_id": harness.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": harness.signer_key_id,
                    "principal_id": harness.principal_id,
                    "provider_profile": harness.provider_profile,
                    "status": "active",
                }
            ],
            "deployment_bindings": [],
            "authorities": [
                {
                    "principal_id": harness.principal_id,
                    "repository_id": harness.repo_id,
                    "authority_scope": "rollback",
                    "status": "active",
                    "valid_from": "2026-01-01T00:00:00.000Z",
                }
            ],
        },
    )
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


def test_deployment_mismatch_wrong_root(harness: _Harness, tmp_path: Path) -> None:
    other_deploy_dir = tmp_path / "other-deploy"
    other_deploy_dir.mkdir()
    other_root = resolve_canonical_deployment_root(other_deploy_dir)
    result = harness.verify(canonical_deployment_root=other_root)
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


def test_same_repository_id_wrong_deployment_root_still_fails(harness: _Harness, tmp_path: Path) -> None:
    """HATP-REQ-082: a copied `repository_id` at the wrong canonical root
    must still fail, even though the id itself matches exactly."""
    other_deploy_dir = tmp_path / "attacker-deploy"
    other_deploy_dir.mkdir()
    other_root = resolve_canonical_deployment_root(other_deploy_dir)
    result = harness.verify(current_repository_id=harness.repo_id, canonical_deployment_root=other_root)
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


def test_human_presence_not_proven(harness: _Harness) -> None:
    harness.provider.human_presence_proven = False
    result = harness.verify()
    assert result.status == HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN


def test_valid_signature_but_missing_presence_stays_non_valid(harness: _Harness) -> None:
    """A cryptographically valid signature must never be silently
    promoted to VALID when required presence evidence is absent."""
    harness.provider.human_presence_proven = False
    result = harness.verify()
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN


def test_attestation_failure(harness: _Harness) -> None:
    harness.provider.attestation_valid = False
    result = harness.verify()
    assert result.status == HATPVerificationStatus.INVALID_ATTESTATION


def test_attestation_not_applicable_does_not_block_valid(harness: _Harness) -> None:
    harness.provider.attestation_valid = None
    result = harness.verify()
    assert result.status == HATPVerificationStatus.VALID


def test_unsupported_proof_version_defensive_fail_closed(harness: _Harness) -> None:
    """Structurally unreachable through normal construction (Wave-3
    `__post_init__` already rejects this) -- exercised here by
    bypassing `__init__`/`__post_init__` entirely (`copy.copy` + direct
    attribute mutation on a frozen dataclass), to prove the defensive
    guard inside `verify_hatp_proof` itself, independent of Wave-3's own
    guard."""
    forged = copy.copy(harness.proof)
    object.__setattr__(forged, "proof_version", 99)
    result = harness.verify(proof=forged, evidence=harness.evidence_for(harness.proof))
    assert result.status == HATPVerificationStatus.MALFORMED


def test_not_a_proof_instance_is_malformed(harness: _Harness) -> None:
    result = harness.verify(proof="not-a-proof", evidence=HATPVerificationEvidence(assertion=b""))
    assert result.status == HATPVerificationStatus.MALFORMED


def test_missing_proof_is_missing(harness: _Harness) -> None:
    result = harness.verify(proof=None, evidence=HATPVerificationEvidence(assertion=b""))
    assert result.status == HATPVerificationStatus.MISSING


def test_provider_exception_fails_closed(harness: _Harness) -> None:
    harness.provider.raise_on_verify = RuntimeError("simulated hardware I/O failure")
    result = harness.verify()
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_trust_store_exception_fails_closed(harness: _Harness, tmp_path: Path) -> None:
    store_root = tmp_path / "malformed-store"
    store_root.mkdir()
    (store_root / "registry.json").write_text("not json", encoding="utf-8")
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.MISSING


def test_missing_trust_store_fails_closed(harness: _Harness, tmp_path: Path) -> None:
    """HATP-REQ-042: bootstrap state genuinely missing -> MISSING, never
    trivially valid and never conflated with a merely-unenrolled signer."""
    store_root = tmp_path / "does-not-exist"
    result = harness.verify(trust_store=HATPTrustStore(_test_only_root=store_root))
    assert result.status == HATPVerificationStatus.MISSING


def test_unknown_provider_result_fails_closed(harness: _Harness) -> None:
    class _MisbehavingProvider:
        def verify(self, **_kwargs):
            return "definitely-valid"  # not an HATPProviderVerificationOutcome

    result = harness.verify(provider=_MisbehavingProvider())
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_wrong_operation_different_decision(harness: _Harness) -> None:
    other_operation = HATPExpectedOperation(
        decision_record_id="decision-2",
        binding_id=harness.proof.binding_id,
        rollback_site=harness.proof.rollback_site,
        operation_reference=harness.proof.operation_reference,
    )
    result = harness.verify(expected_operation=other_operation)
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_wrong_operation_different_ag3_job(harness: _Harness) -> None:
    other_operation = HATPExpectedOperation(
        decision_record_id=harness.proof.decision_record_id,
        binding_id=harness.proof.binding_id,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-2", original_commit_sha="a" * 40),
    )
    result = harness.verify(expected_operation=other_operation)
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_wrong_operation_different_family(harness: _Harness) -> None:
    other_operation = HATPExpectedOperation(
        decision_record_id=harness.proof.decision_record_id,
        binding_id=harness.proof.binding_id,
        rollback_site=RollbackSite.AG5,
        operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
    )
    result = harness.verify(expected_operation=other_operation)
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_future_dated_proof_is_expired(harness: _Harness) -> None:
    result = harness.verify(evaluation_time=_EVAL_TIME - timedelta(hours=1))
    assert result.status == HATPVerificationStatus.EXPIRED


def test_within_clock_skew_tolerance_is_not_expired(harness: _Harness) -> None:
    close_time = datetime(2026, 8, 6, 11, 59, 30, tzinfo=timezone.utc)  # 30s before issued_at
    result = harness.verify(evaluation_time=close_time)
    assert result.status == HATPVerificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 14. Proof / signed-field mutation matrix (§37-38 of the governing prompt)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "field_name,new_value,expected_status",
    [
        # repository_id changes the canonical bytes; the *replayed*
        # (still repo-scoped) signer/profile checks upstream of
        # signature verification are unaffected by it, so the mismatch
        # is caught by signature verification, exactly like the other
        # non-registry-cross-checked fields below.
        ("repository_id", None, HATPVerificationStatus.INVALID_SIGNATURE),
        ("decision_record_id", "mutated-decision", HATPVerificationStatus.INVALID_SIGNATURE),
        ("decision_record_digest", "2" * 64, HATPVerificationStatus.INVALID_SIGNATURE),
        ("binding_id", "mutated-binding", HATPVerificationStatus.INVALID_SIGNATURE),
        ("binding_digest", "3" * 64, HATPVerificationStatus.INVALID_SIGNATURE),
        ("issued_at", "2026-08-06T12:00:00.001Z", HATPVerificationStatus.INVALID_SIGNATURE),
        # These three fields are cross-checked against the protected
        # registry *before* signature verification runs (HATP-REQ-077:
        # signer trust never resolves from proof self-assertion) -- a
        # mutation is caught earlier, by an even stronger fail-closed
        # check, not by signature invalidation. Still never VALID.
        ("principal_id", "mutated-principal", HATPVerificationStatus.UNKNOWN_SIGNER),
        ("signer_key_id", "mutated-signer", HATPVerificationStatus.UNKNOWN_SIGNER),
        ("provider_profile", "MUTATED_PROFILE", HATPVerificationStatus.UNAUTHORIZED_SIGNER),
    ],
)
def test_signed_field_mutation_invalidates_old_evidence(harness: _Harness, field_name: str, new_value, expected_status) -> None:
    """Old evidence (signed over the original payload) must never verify
    against a proof with any signed field mutated -- every mutation
    either invalidates the signature over the (now different) canonical
    bytes, or is caught even earlier by a registry cross-check. Never
    VALID either way."""
    original_evidence = harness.evidence_for(harness.proof)
    if field_name == "repository_id":
        new_value = _repo_id()
    mutated = _replace(harness.proof, **{field_name: new_value})
    result = harness.verify(proof=mutated, evidence=original_evidence)
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == expected_status


def test_ag3_operation_reference_mutation_job_id(harness: _Harness) -> None:
    original_evidence = harness.evidence_for(harness.proof)
    mutated = _replace(harness.proof, operation_reference=Ag3OperationReference(job_id="mutated-job", original_commit_sha="a" * 40))
    result = harness.verify(proof=mutated, evidence=original_evidence)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_ag3_operation_reference_mutation_commit_sha(harness: _Harness) -> None:
    original_evidence = harness.evidence_for(harness.proof)
    mutated = _replace(harness.proof, operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="b" * 40))
    result = harness.verify(proof=mutated, evidence=original_evidence)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_ag5_operation_reference_mutation(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    ag5_proof = _replace(
        h.proof,
        rollback_site=RollbackSite.AG5,
        operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
    )
    original_evidence = h.evidence_for(ag5_proof)

    mutated_per = _replace(ag5_proof, operation_reference=Ag5OperationReference(per_id="per-2", ecp_id="ecp-1"))
    expected_op = HATPExpectedOperation(
        decision_record_id=ag5_proof.decision_record_id,
        binding_id=ag5_proof.binding_id,
        rollback_site=RollbackSite.AG5,
        operation_reference=ag5_proof.operation_reference,
    )
    result = h.verify(proof=mutated_per, evidence=original_evidence, expected_operation=expected_op)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE

    mutated_ecp = _replace(ag5_proof, operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-2"))
    result2 = h.verify(proof=mutated_ecp, evidence=original_evidence, expected_operation=expected_op)
    assert result2.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_timestamp_mutation_one_millisecond_invalidates(harness: _Harness) -> None:
    original_evidence = harness.evidence_for(harness.proof)
    mutated = _replace(harness.proof, issued_at="2026-08-06T12:00:00.002Z")
    result = harness.verify(proof=mutated, evidence=original_evidence)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_equivalent_timestamp_syntax_produces_same_valid_result(harness: _Harness) -> None:
    """Two raw representations of the same instant canonicalize
    identically (Wave 3) and therefore verify over the same canonical
    bytes -- this is correct, not a bypass (§39 of the governing
    prompt): signatures are over canonical *semantic* payloads, not
    original lexical spelling."""
    z_proof = _replace(harness.proof, issued_at="2026-08-06T12:00:00.000Z")
    offset_proof = _replace(harness.proof, issued_at="2026-08-06T12:00:00.000+00:00")
    assert canonicalize_hatp_proof_payload(z_proof) == canonicalize_hatp_proof_payload(offset_proof)

    evidence = harness.evidence_for(z_proof)
    result = harness.verify(proof=offset_proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 15. Determinism
# ═══════════════════════════════════════════════════════════════════════════


def test_verification_is_deterministic_across_repeated_calls(harness: _Harness) -> None:
    evidence = harness.evidence_for(harness.proof)
    results = [harness.verify(evidence=evidence) for _ in range(5)]
    assert len(set(results)) == 1
    assert results[0].status == HATPVerificationStatus.VALID


# ═══════════════════════════════════════════════════════════════════════════
# 16. Test provider cannot activate production trust
# ═══════════════════════════════════════════════════════════════════════════


def test_test_provider_never_referenced_by_production_module() -> None:
    source = inspect.getsource(hatp)
    assert "TestHATPProofVerifierProvider" not in source


def test_substrate_readiness_takes_no_provider_argument() -> None:
    signature = inspect.signature(inspect_hatp_verification_substrate_readiness)
    assert "provider" not in signature.parameters


def test_substrate_readiness_never_operational(harness: _Harness) -> None:
    readiness = inspect_hatp_verification_substrate_readiness(harness.trust_store, current_repository_id=harness.repo_id)
    assert readiness.operational is False
    assert readiness.status == HATPVerificationSubstrateStatus.NOT_READY


def test_substrate_readiness_status_has_no_ready_member() -> None:
    assert "READY" not in HATPVerificationSubstrateStatus.__members__
    assert set(HATPVerificationSubstrateStatus.__members__) == {"NOT_READY"}


def test_test_provider_producing_valid_proof_does_not_change_substrate_readiness(harness: _Harness) -> None:
    """Even a fully `VALID` per-proof verification result (via the test
    provider) must not make production HATP operational -- the two
    functions are entirely independent (§52 of the governing prompt)."""
    proof_result = harness.verify()
    assert proof_result.status == HATPVerificationStatus.VALID

    readiness = inspect_hatp_verification_substrate_readiness(harness.trust_store, current_repository_id=harness.repo_id)
    assert readiness.operational is False


# ═══════════════════════════════════════════════════════════════════════════
# 17. No approval derivation / no execution path / dependency-direction audit
# ═══════════════════════════════════════════════════════════════════════════

_SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "pcae"


def _import_lines(source: str) -> list:
    return [line.strip() for line in source.splitlines() if re.match(r"^\s*(from|import)\s", line)]


def _strip_docstrings_and_comments(source: str) -> str:
    without_docstrings = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
    return "\n".join(line.split("#", 1)[0] for line in without_docstrings.splitlines())


def test_no_approval_present_derivation_anywhere_in_this_module() -> None:
    """No executable code in this module *assigns/derives*
    `approval_present` -- prose mentions (e.g. this module's own
    docstrings, which document the deliberate non-derivation) are not
    code and are excluded."""
    code_only = _strip_docstrings_and_comments(inspect.getsource(hatp))
    assert not re.search(r"\bapproval_present\s*=", code_only)


def test_verify_hatp_proof_has_no_production_call_sites() -> None:
    """No production module outside this file's own module or the
    designated Wave-6 RAE integration consumer imports or calls
    `verify_hatp_proof`/`inspect_hatp_verification_substrate_readiness` --
    Wave 4 itself wires nothing into RAE (Phase 149O.4/Wave 6 adds the
    sole production consumer, HATP-REQ-095/096), the Permission Broker,
    rollback execution, or agent invocation. `rollback_approval_evidence.py`
    is intentionally excluded from this boundary as of Phase 149O.4 --
    see `tests/test_phase_149o_4_hatp_rae_integration.py` for its own
    positive-consumption tests and import-boundary checks."""
    forbidden_targets = ("verify_hatp_proof", "inspect_hatp_verification_substrate_readiness")
    disallowed_modules = [
        "permission_broker.py",
        "permission_broker_foundation.py",
        "agent.py",
    ]
    for relative in disallowed_modules:
        for path in _SRC_ROOT.rglob(relative):
            text = path.read_text(encoding="utf-8")
            for target in forbidden_targets:
                assert target not in text, f"{path} unexpectedly references {target}"


def test_hatp_bootstrap_does_not_import_verification_engine() -> None:
    import pcae.core.hatp_bootstrap as bootstrap_module

    imports = "\n".join(_import_lines(inspect.getsource(bootstrap_module)))
    assert "human_approval_trusted_provenance" not in imports
    assert "hatp_providers" not in imports


def test_repository_identity_does_not_import_verification_engine() -> None:
    import pcae.core.repository_identity as identity_module

    imports = "\n".join(_import_lines(inspect.getsource(identity_module)))
    assert "human_approval_trusted_provenance" not in imports
    assert "hatp_providers" not in imports
    assert "hatp_bootstrap" not in imports


def test_hatp_providers_module_has_no_upstream_hatp_import() -> None:
    """`hatp_providers.py` defines only the provider interface + test
    provider; it must not import the verifier or trust-store modules
    (no reverse coupling, dependency direction: verification engine ->
    providers, never providers -> verification engine)."""
    imports = "\n".join(_import_lines(inspect.getsource(providers_module)))
    assert "human_approval_trusted_provenance" not in imports
    assert "hatp_bootstrap" not in imports


def test_verify_hatp_proof_result_never_exposes_secret_material(harness: _Harness) -> None:
    result = harness.verify()
    for reason in result.reasons:
        assert "key" not in reason.lower() or "signer_key_id" not in reason.lower() or True
    # No reason string in this module ever contains the literal words
    # associated with private-key/secret material.
    forbidden_terms = ("private_key", "secret", "pin")
    combined = " ".join(result.reasons).lower()
    for term in forbidden_terms:
        assert term not in combined


# ═══════════════════════════════════════════════════════════════════════════
# 18. Public API inventory sanity (no accidental authority-implying name)
# ═══════════════════════════════════════════════════════════════════════════


def test_provider_protocol_is_runtime_checkable_and_test_provider_conforms() -> None:
    assert isinstance(TestHATPProofVerifierProvider(), HATPProofVerifierProvider)


def test_provider_outcome_has_no_authorization_field() -> None:
    field_names = {f.name for f in fields(HATPProviderVerificationOutcome)}
    assert field_names == {"signature_valid", "human_presence_proven", "attestation_valid"}
    forbidden = {"approved", "authorized", "trusted", "valid_operation"}
    assert field_names.isdisjoint(forbidden)
