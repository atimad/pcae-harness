"""Phase 149O.4 -- HATP Wave 6 RAE Integration (HATP-REQ-095/096,
HATP-REQ-101-104).

Deterministic, hardware- and environment-independent tests for
`pcae.core.rollback_approval_evidence`'s new Wave-6 addition
(`resolve_rollback_approval_evidence_with_hatp`,
`derive_rollback_approval_present_with_hatp`,
`HATPIntegratedApprovalEvidence`, `_derive_hatp_gated_approval_present`,
`_hatp_expected_operation_for`). No hardware, no real cryptography, no
network, no wall clock -- every test supplies its own explicit
`evaluation_time`.

Independently constructed fixture helpers (mirrors the 149O RAE suite's
own "no imported fixtures across phase boundaries" convention): a
combined harness produces a genuine RAE Binding (via the real,
unmodified `create_rollback_approval_decision`/`create_rollback_approval_
binding` API) plus a genuine, self-consistent HATP proof bound to that
exact Binding's identity *and* content digests, verified through the
real, unmodified `verify_hatp_proof` and a deterministic
`TestHATPProofVerifierProvider` (never selected in production, per
`hatp_providers.py`'s own module docstring).
"""
from __future__ import annotations

import inspect
import json
import uuid
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import human_approval_trusted_provenance as hatp
from pcae.core import rollback_approval_evidence as rae
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_providers import HATPProofVerifierProvider, TestHATPProofVerifierProvider
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference as HATPAg3OperationReference,
    Ag5OperationReference as HATPAg5OperationReference,
    HATPExpectedOperation,
    HATPVerificationEvidence,
    HATPVerificationStatus,
    HATP_VERIFICATION_STATUS_VALUES,
    HumanApprovalProvenanceProof,
    RollbackSite as HATPRollbackSite,
    canonicalize_hatp_proof_payload,
    inspect_hatp_verification_substrate_readiness,
)
from pcae.governance.publication.storage import PublicationRecordStore

_EVAL_TIME = datetime(2026, 8, 7, 12, 0, 1, tzinfo=timezone.utc)
_UNSET = object()


# ═══════════════════════════════════════════════════════════════════════════
# Independently authored fixture helpers -- RAE side
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state(sha: str = "a" * 40, branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _ag3_ref(job_id: str = "job-149o4", sha: str = "b" * 40) -> rae.Ag3OperationReference:
    return rae.Ag3OperationReference(job_id=job_id, original_commit_sha=sha)


def _ag3_ctx(job_id: str = "job-149o4", sha: str = "b" * 40, repo=None) -> rae.Ag3RollbackApprovalContext:
    return rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=sha, task_id=None, repository_state=repo or _repo_state()
    )


def _ag5_ref(per_id: str = "per-149o4", ecp_id: str = "ecp-149o4") -> rae.Ag5OperationReference:
    return rae.Ag5OperationReference(per_id=per_id, ecp_id=ecp_id)


def _ag5_ctx(per_id: str = "per-149o4", ecp_id: str = "ecp-149o4", repo=None) -> rae.Ag5RollbackApprovalContext:
    return rae.Ag5RollbackApprovalContext(
        per_id=per_id, ecp_id=ecp_id, task_id=None, repository_state=repo or _repo_state()
    )


def _genuine_decision(
    pub_root: Path,
    decision: rae.RollbackDecisionType = rae.RollbackDecisionType.APPROVE_ROLLBACK,
    subject: str = "job-149o4|" + "b" * 40,
) -> rae.RollbackApprovalDecisionRef:
    store = PublicationRecordStore(root=pub_root)
    return rae.create_rollback_approval_decision(
        decision=decision,
        decision_subject=subject,
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "local-operator",
            "captured_at": "2026-08-07T10:00:00Z",
        },
        operator_id="local-operator",
        publication_store=store,
    )


def _genuine_binding(
    pub_root: Path,
    evidence_root: Path,
    *,
    site: rae.RollbackSite = rae.RollbackSite.AG3,
    op_ref=None,
    decision_ref: rae.RollbackApprovalDecisionRef = None,
    subject: str = "job-149o4|" + "b" * 40,
) -> tuple:
    if decision_ref is None:
        decision_ref = _genuine_decision(pub_root, subject=subject)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    if op_ref is None:
        op_ref = _ag3_ref() if site == rae.RollbackSite.AG3 else _ag5_ref()
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=site,
        rollback_operation_reference=op_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )
    return decision_ref, binding, store


@pytest.fixture
def pub_root(tmp_path: Path) -> Path:
    return tmp_path / "publication-execution"


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    return tmp_path / "rollback-approval-evidence"


# ═══════════════════════════════════════════════════════════════════════════
# Independently authored fixture helpers -- HATP side + combined harness
# ═══════════════════════════════════════════════════════════════════════════


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(document), encoding="utf-8")


class _IntegrationHarness:
    """A complete, self-consistent, VALID-eligible Wave-6 scenario: a
    genuine RAE Binding (real API, real CHGR Decision, real publication
    receipt) plus a genuine HATP proof whose identity *and* digest
    fields exactly match that Binding, verifiable through the real,
    unmodified Wave-4 `verify_hatp_proof` and a deterministic test
    provider. Individual tests mutate exactly one dimension away from
    this baseline."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.pub_root = tmp_path / "publication-execution"
        self.evidence_root = tmp_path / "rollback-approval-evidence"

        self.repo_id = str(uuid.uuid4())
        deploy_dir = tmp_path / "deploy"
        deploy_dir.mkdir()
        self.canonical_root = resolve_canonical_deployment_root(deploy_dir)

        self.principal_id = "principal-149o4"
        self.signer_key_id = "signer-149o4"
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
        self.store_root = store_root
        self.trust_store = HATPTrustStore(_test_only_root=store_root)
        self.provider = TestHATPProofVerifierProvider()

        _decision_ref, self.binding, self.rae_store = _genuine_binding(
            self.pub_root, self.evidence_root, site=rae.RollbackSite.AG3, op_ref=_ag3_ref()
        )

        self.proof = self._proof_for(self.binding)

    def _proof_for(self, binding: rae.RollbackApprovalBinding, **overrides) -> HumanApprovalProvenanceProof:
        if binding.rollback_site is rae.RollbackSite.AG3:
            op_ref = binding.rollback_operation_reference
            hatp_op_ref = HATPAg3OperationReference(job_id=op_ref.job_id, original_commit_sha=op_ref.original_commit_sha)
            hatp_site = HATPRollbackSite.AG3
        else:
            op_ref = binding.rollback_operation_reference
            hatp_op_ref = HATPAg5OperationReference(per_id=op_ref.per_id, ecp_id=op_ref.ecp_id)
            hatp_site = HATPRollbackSite.AG5

        fields_ = dict(
            proof_version=1,
            principal_id=self.principal_id,
            signer_key_id=self.signer_key_id,
            provider_profile=self.provider_profile,
            repository_id=self.repo_id,
            decision_record_id=binding.governance_record_reference.record_id,
            decision_record_digest=binding.governance_record_reference.record_digest,
            binding_id=binding.evidence_id,
            binding_digest=binding.content_digest,
            rollback_site=hatp_site,
            operation_reference=hatp_op_ref,
            issued_at="2026-08-07T12:00:00.000Z",
        )
        fields_.update(overrides)
        return HumanApprovalProvenanceProof(**fields_)

    def sign(self, proof: HumanApprovalProvenanceProof) -> bytes:
        payload = canonicalize_hatp_proof_payload(proof)
        return self.provider.sign(payload, signer_key_id=proof.signer_key_id, provider_profile=proof.provider_profile)

    def evidence_for(self, proof: HumanApprovalProvenanceProof) -> HATPVerificationEvidence:
        return HATPVerificationEvidence(assertion=self.sign(proof))

    def resolve(
        self,
        *,
        operation_context=None,
        evidence_id=None,
        hatp_proof=_UNSET,
        hatp_evidence=None,
        hatp_provider=None,
        hatp_trust_store=None,
        current_repository_id=None,
        canonical_deployment_root=None,
        evaluation_time=None,
        evidence_store=None,
        publication_root=None,
    ) -> rae.HATPIntegratedApprovalEvidence:
        proof = self.proof if hatp_proof is _UNSET else hatp_proof
        return rae.resolve_rollback_approval_evidence_with_hatp(
            operation_context if operation_context is not None else _ag3_ctx(),
            evidence_id if evidence_id is not None else self.binding.evidence_id,
            hatp_proof=proof,
            hatp_evidence=(self.evidence_for(proof) if proof is not None else HATPVerificationEvidence(assertion=b""))
            if hatp_evidence is None
            else hatp_evidence,
            hatp_provider=self.provider if hatp_provider is None else hatp_provider,
            hatp_trust_store=self.trust_store if hatp_trust_store is None else hatp_trust_store,
            current_repository_id=self.repo_id if current_repository_id is None else current_repository_id,
            canonical_deployment_root=self.canonical_root if canonical_deployment_root is None else canonical_deployment_root,
            evaluation_time=_EVAL_TIME if evaluation_time is None else evaluation_time,
            evidence_store=self.rae_store if evidence_store is None else evidence_store,
            publication_root=self.pub_root if publication_root is None else publication_root,
        )


@pytest.fixture
def harness(tmp_path: Path) -> _IntegrationHarness:
    return _IntegrationHarness(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# 1. The single most important test (phase spec item 12): HATP VALID +
#    RAE valid + real (always NOT_READY) substrate => approval_present
#    remains False in this deployment.
# ═══════════════════════════════════════════════════════════════════════════


def test_valid_hatp_plus_valid_rae_still_false_in_current_deployment(harness: _IntegrationHarness) -> None:
    result = harness.resolve(hatp_proof=harness.proof)
    assert result.rae_result == rae.RollbackApprovalValidationResult.VALID
    assert result.hatp_status == HATPVerificationStatus.VALID
    assert result.activation_operational is False
    assert result.approval_present is False


def test_current_real_deployment_readiness_is_not_ready(harness: _IntegrationHarness) -> None:
    readiness = inspect_hatp_verification_substrate_readiness(harness.trust_store, current_repository_id=harness.repo_id)
    assert readiness.operational is False
    assert readiness.status.value == "NOT_READY"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Pure three-term conjunction (`_derive_hatp_gated_approval_present`) --
#    the only place `True` is reachable, and only synthetically.
# ═══════════════════════════════════════════════════════════════════════════


def test_pure_conjunction_full_synthetic_success() -> None:
    assert rae._derive_hatp_gated_approval_present(
        rae_approval_present=True, hatp_status=HATPVerificationStatus.VALID, activation_operational=True
    ) is True


@pytest.mark.parametrize(
    "rae_ok,hatp_status,operational",
    [
        (False, HATPVerificationStatus.VALID, True),
        (True, HATPVerificationStatus.MISSING, True),
        (True, HATPVerificationStatus.VALID, False),
    ],
)
def test_pure_conjunction_one_fact_removed(rae_ok, hatp_status, operational) -> None:
    assert (
        rae._derive_hatp_gated_approval_present(
            rae_approval_present=rae_ok, hatp_status=hatp_status, activation_operational=operational
        )
        is False
    )


@pytest.mark.parametrize(
    "rae_ok,hatp_status,operational",
    [
        (False, HATPVerificationStatus.MISSING, False),
        (False, HATPVerificationStatus.VALID, False),
        (True, HATPVerificationStatus.INVALID_SIGNATURE, False),
        (False, HATPVerificationStatus.REVOKED_SIGNER, True),
    ],
)
def test_pure_conjunction_two_failure_matrix(rae_ok, hatp_status, operational) -> None:
    assert (
        rae._derive_hatp_gated_approval_present(
            rae_approval_present=rae_ok, hatp_status=hatp_status, activation_operational=operational
        )
        is False
    )


@pytest.mark.parametrize("status", sorted(HATP_VERIFICATION_STATUS_VALUES))
def test_pure_conjunction_13_state_matrix_only_valid_can_pass(status: str) -> None:
    hatp_status = HATPVerificationStatus(status)
    outcome = rae._derive_hatp_gated_approval_present(
        rae_approval_present=True, hatp_status=hatp_status, activation_operational=True
    )
    if hatp_status is HATPVerificationStatus.VALID:
        assert outcome is True
    else:
        assert outcome is False


def test_pure_conjunction_no_default_branch_accepts_unlisted_status() -> None:
    assert HATP_VERIFICATION_STATUS_VALUES == {s.value for s in HATPVerificationStatus}
    for status in HATPVerificationStatus:
        if status is not HATPVerificationStatus.VALID:
            assert (
                rae._derive_hatp_gated_approval_present(
                    rae_approval_present=True, hatp_status=status, activation_operational=True
                )
                is False
            )


# ═══════════════════════════════════════════════════════════════════════════
# 3. RAE-side failures with HATP fully satisfied never approve
#    (Two-Independent-Gates property, phase spec items 33-40).
# ═══════════════════════════════════════════════════════════════════════════


def test_rae_missing_evidence_id_plus_valid_hatp_still_false(harness: _IntegrationHarness) -> None:
    result = harness.resolve(evidence_id="nonexistent-evidence-id", hatp_proof=harness.proof)
    assert result.rae_result == rae.RollbackApprovalValidationResult.MISSING
    assert result.approval_present is False


def test_rae_revoked_plus_valid_hatp_still_false(harness: _IntegrationHarness) -> None:
    rae.revoke_rollback_approval_binding(
        harness.binding.evidence_id,
        evidence_store=harness.rae_store,
        revoked_by="local-operator",
        reason_code="test_revocation",
    )
    result = harness.resolve(hatp_proof=harness.proof)
    assert result.rae_result == rae.RollbackApprovalValidationResult.REVOKED
    assert result.approval_present is False


def test_rae_wrong_scope_plus_valid_hatp_still_false(harness: _IntegrationHarness) -> None:
    # Live operation context does not match the Binding's own operation.
    wrong_ctx = _ag3_ctx(job_id="different-job", sha="c" * 40)
    result = harness.resolve(operation_context=wrong_ctx, hatp_proof=harness.proof)
    assert result.rae_result == rae.RollbackApprovalValidationResult.WRONG_SCOPE
    assert result.approval_present is False


def test_rae_stale_plus_valid_hatp_still_false(harness: _IntegrationHarness) -> None:
    future = _EVAL_TIME + timedelta(hours=25)
    with rae._frozen_clock(future):
        result = harness.resolve(hatp_proof=harness.proof, evaluation_time=future)
    assert result.rae_result == rae.RollbackApprovalValidationResult.STALE
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. HATP-side failures with RAE valid never approve.
# ═══════════════════════════════════════════════════════════════════════════


def test_rae_valid_hatp_missing_still_false(harness: _IntegrationHarness) -> None:
    result = harness.resolve(hatp_proof=None)
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert result.approval_present is False


def test_rae_valid_hatp_unknown_signer_still_false(harness: _IntegrationHarness) -> None:
    bad_proof = replace(harness.proof, signer_key_id="attacker-key-not-enrolled")
    result = harness.resolve(hatp_proof=bad_proof)
    assert result.hatp_status == HATPVerificationStatus.UNKNOWN_SIGNER
    assert result.approval_present is False


def test_rae_valid_hatp_revoked_signer_still_false(harness: _IntegrationHarness) -> None:
    registry = json.loads((harness.store_root / "registry.json").read_text())
    registry["signers"][0]["status"] = "revoked"
    registry["signers"][0]["revoked_at"] = "2026-08-07T11:00:00.000Z"
    (harness.store_root / "registry.json").write_text(json.dumps(registry))
    result = harness.resolve(hatp_proof=harness.proof)
    assert result.hatp_status == HATPVerificationStatus.REVOKED_SIGNER
    assert result.approval_present is False


def test_rae_valid_hatp_wrong_repository_still_false(harness: _IntegrationHarness) -> None:
    result = harness.resolve(hatp_proof=harness.proof, current_repository_id=str(uuid.uuid4()))
    assert result.hatp_status == HATPVerificationStatus.WRONG_REPOSITORY
    assert result.approval_present is False


def test_rae_valid_hatp_wrong_deployment_still_false(harness: _IntegrationHarness) -> None:
    other_deploy = harness.tmp_path / "other-deploy"
    other_deploy.mkdir()
    other_root = resolve_canonical_deployment_root(other_deploy)
    result = harness.resolve(hatp_proof=harness.proof, canonical_deployment_root=other_root)
    assert result.hatp_status == HATPVerificationStatus.WRONG_DEPLOYMENT
    assert result.approval_present is False


def test_rae_valid_hatp_expired_still_false(harness: _IntegrationHarness) -> None:
    late_eval = _EVAL_TIME - timedelta(hours=1)
    stale_proof = replace(harness.proof, issued_at="2026-08-07T13:05:00.000Z")
    result = harness.resolve(hatp_proof=stale_proof, evaluation_time=late_eval)
    assert result.hatp_status == HATPVerificationStatus.EXPIRED
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. Decision/Binding digest replay -- the 149O.1J-deferred integration
#    semantics this phase must close (phase spec items 46-53, 122-123).
# ═══════════════════════════════════════════════════════════════════════════


def test_stale_decision_digest_replay_rejected(harness: _IntegrationHarness) -> None:
    stale_proof = replace(harness.proof, decision_record_digest="f" * 64)
    result = harness.resolve(hatp_proof=stale_proof)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert "decision_record_digest_mismatch" in result.hatp_reasons
    assert result.approval_present is False


def test_stale_binding_digest_replay_rejected(harness: _IntegrationHarness) -> None:
    stale_proof = replace(harness.proof, binding_digest="e" * 64)
    result = harness.resolve(hatp_proof=stale_proof)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert "binding_digest_mismatch" in result.hatp_reasons
    assert result.approval_present is False


def test_copied_hatp_evidence_wrong_binding_context_rejected(harness: _IntegrationHarness) -> None:
    """A genuine proof/signature for one Binding, replayed against a
    different (also genuine) Binding, must fail binding (item 55)."""
    _decision_ref2, binding2, _store2 = _genuine_binding(
        harness.pub_root,
        harness.evidence_root,
        site=rae.RollbackSite.AG3,
        op_ref=_ag3_ref(job_id="another-job", sha="d" * 40),
        subject="job-149o4|" + "d" * 40,
    )
    result = harness.resolve(
        operation_context=_ag3_ctx(job_id="another-job", sha="d" * 40),
        evidence_id=binding2.evidence_id,
        hatp_proof=harness.proof,  # still bound to the *original* binding
    )
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 6. Cross-family replay (AG3 <-> AG5) -- items 48-50, 124-126.
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_proof_cannot_approve_ag5_operation(harness: _IntegrationHarness) -> None:
    _decision_ref, ag5_binding, ag5_store = _genuine_binding(
        harness.pub_root, harness.evidence_root, site=rae.RollbackSite.AG5, op_ref=_ag5_ref(), subject="job-149o4|" + "b" * 40
    )
    result = rae.resolve_rollback_approval_evidence_with_hatp(
        _ag5_ctx(),
        ag5_binding.evidence_id,
        hatp_proof=harness.proof,  # AG3 proof
        hatp_evidence=harness.evidence_for(harness.proof),
        hatp_provider=harness.provider,
        hatp_trust_store=harness.trust_store,
        current_repository_id=harness.repo_id,
        canonical_deployment_root=harness.canonical_root,
        evaluation_time=_EVAL_TIME,
        evidence_store=ag5_store,
        publication_root=harness.pub_root,
    )
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


def test_ag5_proof_cannot_approve_ag3_operation(harness: _IntegrationHarness) -> None:
    _decision_ref, ag5_binding, ag5_store = _genuine_binding(
        harness.pub_root, harness.evidence_root, site=rae.RollbackSite.AG5, op_ref=_ag5_ref(), subject="job-149o4|" + "b" * 40
    )
    ag5_proof = harness._proof_for(ag5_binding)
    result = harness.resolve(hatp_proof=ag5_proof)  # AG5 proof against AG3 binding/context
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. Consumption-time reverification -- no cached VALID survives
#    signer/authority revocation (phase spec items 90-92, 58-60).
# ═══════════════════════════════════════════════════════════════════════════


def test_consumption_time_revocation_defeats_previously_valid_proof(harness: _IntegrationHarness) -> None:
    first = harness.resolve(hatp_proof=harness.proof)
    assert first.hatp_status == HATPVerificationStatus.VALID

    registry = json.loads((harness.store_root / "registry.json").read_text())
    registry["signers"][0]["status"] = "revoked"
    registry["signers"][0]["revoked_at"] = "2026-08-07T11:00:00.000Z"
    (harness.store_root / "registry.json").write_text(json.dumps(registry))

    second = harness.resolve(hatp_proof=harness.proof)
    assert second.hatp_status == HATPVerificationStatus.REVOKED_SIGNER
    assert second.approval_present is False


def test_no_caching_of_hatp_verification_result_across_calls(harness: _IntegrationHarness) -> None:
    """`resolve_rollback_approval_evidence_with_hatp` carries no module-
    level or instance-level cache -- each call re-derives from the live
    trust-store/proof state supplied that call."""
    source = inspect.getsource(rae.resolve_rollback_approval_evidence_with_hatp)
    assert "cache" not in source.lower()
    assert "lru_cache" not in source.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 8. Threat-A full forgery -- Wave 6 must block the historical
#    B-149O-1..4 attack paths that RAE alone cannot (phase spec items
#    102, 129).
# ═══════════════════════════════════════════════════════════════════════════


def test_genuine_rae_only_chain_no_hatp_proof_no_longer_approves(harness: _IntegrationHarness) -> None:
    """The historical vulnerability, restated: a fully genuine, legitimately
    -created RAE chain (real Decision, real publication, real Binding via
    the real API -- exactly what
    `tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py::test_149o_canonical_positive_control_still_valid`
    shows currently resolves `approval_present=True` through the
    unmodified, HATP-unaware `resolve_rollback_approval_evidence`) must
    NOT be sufficient once a HATP proof is required and none is supplied.
    This is the crux of what Wave 6 changes: RAE-001 remains COMPATIBLE
    AS-IS (HATP-REQ-095) and its own `approval_present` is unaffected,
    but the new HATP-gated derivation path -- the one a future AG3/AG5
    consumer must use -- fails closed without independent HATP evidence."""

    rae_only = rae.derive_rollback_approval_present(_ag3_ctx(), harness.binding.evidence_id, evidence_store=harness.rae_store, publication_root=harness.pub_root)
    assert rae_only is True  # RAE-001 semantics untouched (HATP-REQ-095)

    gated = harness.resolve(hatp_proof=None)
    assert gated.approval_present is False


def test_legacy_approval_flag_cannot_bypass_hatp_gate() -> None:
    """No `approval_present`, `approved`, `human_authorization`,
    `hatp_valid`, `verification_status`, or `trusted` caller-controlled
    parameter exists on the Wave-6 entry points (phase spec items 7-8,
    45, 97)."""
    forbidden = {
        "approval_present",
        "approved",
        "human_authorization",
        "hatp_valid",
        "verification_status",
        "trusted",
        "hatp_operational",
        "force_operational",
        "allow_test_provider",
        "skip_hatp",
    }
    for func in (rae.resolve_rollback_approval_evidence_with_hatp, rae.derive_rollback_approval_present_with_hatp):
        params = set(inspect.signature(func).parameters)
        assert params.isdisjoint(forbidden), f"{func.__name__} exposes forbidden parameter(s): {params & forbidden}"


def test_no_default_provider_or_trust_store_production_bypass() -> None:
    """`hatp_provider` and `hatp_trust_store` are required keyword-only
    parameters with no default -- nothing here can silently resolve a
    `TestHATPProofVerifierProvider` or a non-production trust-store path
    (phase spec items 66-68)."""
    sig = inspect.signature(rae.resolve_rollback_approval_evidence_with_hatp)
    for name in ("hatp_provider", "hatp_trust_store", "hatp_proof", "hatp_evidence"):
        param = sig.parameters[name]
        assert param.default is inspect.Parameter.empty, f"{name} must have no default"
        assert param.kind is inspect.Parameter.KEYWORD_ONLY


# ═══════════════════════════════════════════════════════════════════════════
# 9. Boundary discipline -- no PB/agent/execution wiring, no reverse
#    HATP->RAE import, no attestation/canonicalization/provider-internal
#    coupling (phase spec items 79-88).
# ═══════════════════════════════════════════════════════════════════════════


def _imported_module_names(module) -> list:
    import ast

    tree = ast.parse(inspect.getsource(module))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_no_permission_broker_or_agent_import() -> None:
    imports = _imported_module_names(rae)
    for forbidden_module in ("permission_broker", "pcae.core.agent", "mutation_permission"):
        assert not any(name == forbidden_module or name.startswith(forbidden_module + ".") for name in imports)


def test_no_fido2_or_cryptography_or_hardware_provider_import() -> None:
    imports = _imported_module_names(rae)
    for forbidden in ("fido2", "cryptography", "hatp_fido2_provider", "hatp_hardware_credentials"):
        assert not any(forbidden in name for name in imports)


def test_hatp_module_does_not_import_rae() -> None:
    imports = _imported_module_names(hatp)
    assert not any("rollback_approval_evidence" in name for name in imports)


def test_integrated_evidence_type_has_no_permission_or_execution_field() -> None:
    field_names = {f.name for f in fields(rae.HATPIntegratedApprovalEvidence)}
    forbidden = {"permission", "allow", "deny", "execute", "executed", "execution_authorized"}
    assert field_names.isdisjoint(forbidden)


def test_wave4_substrate_readiness_still_mechanically_cannot_be_operational() -> None:
    """Confirms Wave 6 did not (and structurally cannot) touch Wave 4's
    hard ceiling (phase spec item 76). Phase 149O.6 (Wave 7)
    intentionally replaces the hard-coded assertion with real,
    mechanically-derived hardware-provider terms -- re-confirmed instead
    on *this* deployment (no attached hardware provider), which is the
    exact same fail-closed outcome via the real derivation path (see
    test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py)."""
    readiness = hatp.inspect_hatp_verification_substrate_readiness(
        hatp.HATPTrustStore(_test_only_root=Path("/nonexistent-hatp-trust-store-for-this-assertion")),
        current_repository_id="not-a-real-repository-id",
    )
    assert readiness.operational is False
    assert readiness.status == hatp.HATPVerificationSubstrateStatus.NOT_READY


# ═══════════════════════════════════════════════════════════════════════════
# 10. Internal-error fail-closed umbrella (mirrors RAE-REQ-042).
# ═══════════════════════════════════════════════════════════════════════════


def test_hatp_trust_store_exception_fails_closed(harness: _IntegrationHarness) -> None:
    class _ExplodingTrustStore:
        def environment_status(self):
            raise hatp.HATPTrustStoreError("boom")

        def lookup_signer(self, *_a, **_k):
            raise hatp.HATPTrustStoreError("boom")

        def lookup_principal(self, *_a, **_k):
            raise hatp.HATPTrustStoreError("boom")

        def lookup_authority(self, *_a, **_k):
            raise hatp.HATPTrustStoreError("boom")

        def resolve_deployment_authorization(self, *_a, **_k):
            raise hatp.HATPTrustStoreError("boom")

        def load_repository_enrollment(self, *_a, **_k):
            raise hatp.HATPTrustStoreError("boom")

    result = harness.resolve(hatp_proof=harness.proof, hatp_trust_store=_ExplodingTrustStore())
    assert result.approval_present is False


def test_hatp_provider_exception_fails_closed(harness: _IntegrationHarness) -> None:
    class _ExplodingProvider:
        def verify(self, **_kwargs):
            raise RuntimeError("hardware I/O error")

    result = harness.resolve(hatp_proof=harness.proof, hatp_provider=_ExplodingProvider())
    assert result.hatp_status == HATPVerificationStatus.INVALID_SIGNATURE
    assert result.approval_present is False


def test_readiness_inspection_exception_fails_closed(harness: _IntegrationHarness, monkeypatch) -> None:
    def _boom(*_a, **_k):
        raise RuntimeError("substrate inspection exploded")

    monkeypatch.setattr(rae, "inspect_hatp_verification_substrate_readiness", _boom)
    result = harness.resolve(hatp_proof=harness.proof)
    assert result.approval_present is False
