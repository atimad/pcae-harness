"""Phase 149O.5 -- HATP RAE Integration Independent Verification.

Independent adversarial re-verification of Phase 149O.4's Wave-6
production integration (`resolve_rollback_approval_evidence_with_hatp`,
`derive_rollback_approval_present_with_hatp`, `HATPIntegratedApprovalEvidence`,
`_derive_hatp_gated_approval_present`, `_hatp_expected_operation_for`) in
`pcae.core.rollback_approval_evidence`.

This suite is independently authored against the production source and
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` directly --
it does not import fixtures, helpers, or assumptions from
`tests/test_phase_149o_4_hatp_rae_integration.py` (149O.4's own suite,
re-run unmodified as a separate regression). Its own harness is a fresh,
independently-constructed genuine RAE Binding + genuine HATP proof pair,
built exclusively from the real, unmodified public APIs
(`create_rollback_approval_decision`, `create_rollback_approval_binding`,
`verify_hatp_proof`, `TestHATPProofVerifierProvider`).

No hardware, no real cryptography, no network, no hidden wall clock --
every test supplies its own explicit `evaluation_time`.
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import subprocess
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import human_approval_trusted_provenance as hatp
from pcae.core import rollback_approval_evidence as rae
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_providers import HATPProofVerifierProvider, TestHATPProofVerifierProvider
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference as HAg3,
    Ag5OperationReference as HAg5,
    HATPVerificationEvidence,
    HATPVerificationStatus,
    HATP_VERIFICATION_STATUS_VALUES,
    HumanApprovalProvenanceProof,
    RollbackSite as HSite,
    canonicalize_hatp_proof_payload,
    inspect_hatp_verification_substrate_readiness,
)
from pcae.governance.publication.storage import PublicationRecordStore

REPO_ROOT = Path(__file__).resolve().parent.parent
_T0 = datetime(2026, 8, 7, 9, 0, 0, tzinfo=timezone.utc)
_UNSET = object()


# ═══════════════════════════════════════════════════════════════════════════
# 0. Independent fixture harness -- fresh construction from real APIs only
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state() -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha="c" * 40, branch="main")


def _write_registry(root: Path, doc: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(doc), encoding="utf-8")


class _Harness:
    """A single, genuinely-VALID-eligible AG3 scenario built exclusively
    from real, unmodified production APIs. Individual tests deviate from
    this baseline in exactly one dimension per attack."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.pub_root = tmp_path / "pub"
        self.evidence_root = tmp_path / "evidence"
        self.repo_id = str(uuid.uuid4())
        deploy_dir = tmp_path / "deploy"
        deploy_dir.mkdir()
        self.canonical_root = resolve_canonical_deployment_root(deploy_dir)

        self.principal_id = "principal-149o5"
        self.signer_key_id = "signer-149o5"
        self.provider_profile = "HATP_HARDWARE_PROVIDER_V1"

        self.store_root = tmp_path / "trust-store"
        self._write_baseline_registry()
        self.trust_store = HATPTrustStore(_test_only_root=self.store_root)
        self.provider = TestHATPProofVerifierProvider()

        self.job_id = "job-149o5"
        self.commit_sha = "d" * 40
        op_ref = rae.Ag3OperationReference(job_id=self.job_id, original_commit_sha=self.commit_sha)

        pub_store = PublicationRecordStore(root=self.pub_root)
        self.decision_ref = rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject=f"{self.job_id}|{self.commit_sha}",
            decision_maker_identity_evidence={
                "evidence_kind": "typed_confirmation_only",
                "identifier": "local-operator",
                "captured_at": "2026-08-07T08:00:00Z",
            },
            operator_id="local-operator",
            publication_store=pub_store,
        )
        self.rae_store = rae.RollbackApprovalEvidenceStore(root=self.evidence_root)
        self.binding = rae.create_rollback_approval_binding(
            decision_ref=self.decision_ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=op_ref,
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=self.pub_root,
            evidence_store=self.rae_store,
        )
        self.proof = self._genuine_proof(self.binding)

    def _write_baseline_registry(self) -> None:
        _write_registry(
            self.store_root,
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

    def _genuine_proof(self, binding: rae.RollbackApprovalBinding, **overrides) -> HumanApprovalProvenanceProof:
        op = binding.rollback_operation_reference
        if binding.rollback_site is rae.RollbackSite.AG3:
            hop = HAg3(job_id=op.job_id, original_commit_sha=op.original_commit_sha)
            site = HSite.AG3
        else:
            hop = HAg5(per_id=op.per_id, ecp_id=op.ecp_id)
            site = HSite.AG5
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
            rollback_site=site,
            operation_reference=hop,
            issued_at="2026-08-07T09:00:00.000Z",
        )
        fields_.update(overrides)
        return HumanApprovalProvenanceProof(**fields_)

    def evidence_for(self, proof: HumanApprovalProvenanceProof, provider=None) -> HATPVerificationEvidence:
        p = provider or self.provider
        payload = canonicalize_hatp_proof_payload(proof)
        return HATPVerificationEvidence(assertion=p.sign(payload, signer_key_id=proof.signer_key_id, provider_profile=proof.provider_profile))

    def resolve(
        self,
        *,
        evidence_id=None,
        hatp_proof=_UNSET,
        hatp_evidence=_UNSET,
        hatp_provider=None,
        hatp_trust_store=None,
        current_repository_id=None,
        canonical_deployment_root=None,
        evaluation_time=None,
        op_ref=None,
    ) -> rae.HATPIntegratedApprovalEvidence:
        proof = self.proof if hatp_proof is _UNSET else hatp_proof
        if hatp_evidence is _UNSET:
            hatp_evidence = self.evidence_for(proof, hatp_provider or self.provider) if proof is not None else HATPVerificationEvidence(assertion=b"")
        ctx = rae.Ag3RollbackApprovalContext(
            job_id=self.job_id, original_commit_sha=self.commit_sha, task_id=None, repository_state=_repo_state()
        ) if op_ref is None else op_ref
        return rae.resolve_rollback_approval_evidence_with_hatp(
            ctx,
            evidence_id if evidence_id is not None else self.binding.evidence_id,
            hatp_proof=proof,
            hatp_evidence=hatp_evidence,
            hatp_provider=hatp_provider or self.provider,
            hatp_trust_store=hatp_trust_store or self.trust_store,
            current_repository_id=current_repository_id or self.repo_id,
            canonical_deployment_root=canonical_deployment_root or self.canonical_root,
            evaluation_time=evaluation_time or (_T0 + timedelta(hours=1)),
            evidence_store=self.rae_store,
            publication_root=self.pub_root,
        )


@pytest.fixture
def h(tmp_path: Path) -> _Harness:
    return _Harness(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Current real deployment: genuine RAE + genuine HATP VALID still False
# ═══════════════════════════════════════════════════════════════════════════


def test_current_real_deployment_cannot_approve(h: _Harness) -> None:
    result = h.resolve()
    assert result.rae_result == rae.RollbackApprovalValidationResult.VALID
    assert result.hatp_status == HATPVerificationStatus.VALID
    assert result.activation_operational is False
    assert result.approval_present is False, "BLOCKING: current same-principal deployment approved"


def test_readiness_inspection_independently_not_ready(h: _Harness) -> None:
    readiness = inspect_hatp_verification_substrate_readiness(h.trust_store, current_repository_id=h.repo_id)
    assert readiness.operational is False
    # independent check: the mechanism is the hardcoded provider terms,
    # not solely the `assert` statement (which is stripped under `python -O`)
    term_map = dict(readiness.terms)
    assert term_map["provider_profile_available"] is False
    assert term_map["provider_attestation_trusted"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 2. Independent 8-row truth table over the pure conjunction
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("rae_ok", [True, False])
@pytest.mark.parametrize("hatp_ok", [True, False])
@pytest.mark.parametrize("activation_ok", [True, False])
def test_pure_conjunction_exhaustive_8_rows(rae_ok, hatp_ok, activation_ok) -> None:
    status = HATPVerificationStatus.VALID if hatp_ok else HATPVerificationStatus.MISSING
    result = rae._derive_hatp_gated_approval_present(
        rae_approval_present=rae_ok, hatp_status=status, activation_operational=activation_ok
    )
    expected = rae_ok and hatp_ok and activation_ok
    assert result is expected, f"row rae={rae_ok} hatp={hatp_ok} activation={activation_ok} expected {expected} got {result}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Independent 13-state HATP status matrix
# ═══════════════════════════════════════════════════════════════════════════


def test_13_state_matrix_only_valid_passes() -> None:
    assert len(HATP_VERIFICATION_STATUS_VALUES) == 13
    for value in HATP_VERIFICATION_STATUS_VALUES:
        status = HATPVerificationStatus(value)
        result = rae._derive_hatp_gated_approval_present(
            rae_approval_present=True, hatp_status=status, activation_operational=True
        )
        if status is HATPVerificationStatus.VALID:
            assert result is True
        else:
            assert result is False, f"BLOCKING: status {status} produced approval_present=True"


def test_unknown_future_status_cannot_default_to_success() -> None:
    """A status object that is not the VALID enum member must fail --
    verifies no default/fallback branch by construction, not by name."""

    class _ForeignStatus:
        """Deliberately not `HATPVerificationStatus.VALID`, not even
        equal by value, to prove the guard uses identity/enum equality,
        not a loose string comparison that a spoofed value could pass."""

        value = "VALID"

        def __eq__(self, other):
            return False

    result = rae._derive_hatp_gated_approval_present(
        rae_approval_present=True, hatp_status=_ForeignStatus(), activation_operational=True
    )
    assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Decision / Binding identity + digest replay
# ═══════════════════════════════════════════════════════════════════════════


def test_decision_id_mismatch_rejected(h: _Harness) -> None:
    forged = replace(h.proof, decision_record_id="wrong-decision-id")
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


def test_binding_id_mismatch_rejected(h: _Harness) -> None:
    forged = replace(h.proof, binding_id="wrong-binding-id")
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


def test_stale_decision_digest_replay_rejected(h: _Harness) -> None:
    """Proof correctly identifies the Decision by id, but carries a
    digest that no longer matches -- the Wave-4-deferred check Wave 6
    claims to close."""
    forged = replace(h.proof, decision_record_digest="0" * 64)
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert "decision_record_digest_mismatch" in result.hatp_reasons
    assert result.approval_present is False


def test_stale_binding_digest_replay_rejected(h: _Harness) -> None:
    forged = replace(h.proof, binding_digest="0" * 64)
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert "binding_digest_mismatch" in result.hatp_reasons
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. AG3/AG5 operation binding + cross-family replay
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_operation_wrong_job_id_rejected(h: _Harness) -> None:
    forged = replace(h.proof, operation_reference=HAg3(job_id="other-job", original_commit_sha=h.commit_sha))
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


def test_ag5_proof_cannot_approve_ag3_operation(h: _Harness) -> None:
    forged = replace(h.proof, rollback_site=HSite.AG5, operation_reference=HAg5(per_id="p", ecp_id="e"))
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.WRONG_OPERATION
    assert result.approval_present is False


def test_ag3_proof_cannot_approve_ag5_operation(tmp_path: Path) -> None:
    h5 = _Harness(tmp_path)
    ag5_ref = rae.Ag5OperationReference(per_id="per-x", ecp_id="ecp-x")
    decision_ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="per-x|ecp-x",
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "local-operator",
            "captured_at": "2026-08-07T08:00:00Z",
        },
        operator_id="local-operator",
        publication_store=PublicationRecordStore(root=h5.pub_root),
    )
    ag5_binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=ag5_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=h5.pub_root,
        evidence_store=h5.rae_store,
    )
    # AG3-shaped proof (from the harness's own AG3 baseline), consumed
    # against the AG5 Binding/operation context.
    ag5_ctx = rae.Ag5RollbackApprovalContext(per_id="per-x", ecp_id="ecp-x", task_id=None, repository_state=_repo_state())
    result = rae.resolve_rollback_approval_evidence_with_hatp(
        ag5_ctx,
        ag5_binding.evidence_id,
        hatp_proof=h5.proof,  # AG3 proof
        hatp_evidence=h5.evidence_for(h5.proof),
        hatp_provider=h5.provider,
        hatp_trust_store=h5.trust_store,
        current_repository_id=h5.repo_id,
        canonical_deployment_root=h5.canonical_root,
        evaluation_time=_T0 + timedelta(hours=1),
        evidence_store=h5.rae_store,
        publication_root=h5.pub_root,
    )
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 6. Repository / deployment binding
# ═══════════════════════════════════════════════════════════════════════════


def test_wrong_repository_rejected(h: _Harness) -> None:
    """A proof bound to a repository_id with no authority record for
    this signer fails closed. Per `verify_hatp_proof`'s own documented
    ordering note (HATP-REQ-079 is an unordered AND-list; failure
    *precedence* when multiple terms fail simultaneously is a
    non-normative implementation choice): the authority-lookup check
    (`UNAUTHORIZED_SIGNER`) executes before the repository-id equality
    check (`WRONG_REPOSITORY`) in the current implementation, so an
    unenrolled foreign repository_id is independently and correctly
    rejected -- via `UNAUTHORIZED_SIGNER`, not `WRONG_REPOSITORY` --
    confirmed directly against source (`_derive_hatp_gated_approval_present`
    is never reached with a VALID status here)."""
    forged = replace(h.proof, repository_id=str(uuid.uuid4()))
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status != HATPVerificationStatus.VALID
    assert result.hatp_status in (HATPVerificationStatus.WRONG_REPOSITORY, HATPVerificationStatus.UNAUTHORIZED_SIGNER)
    assert result.approval_present is False


def test_wrong_deployment_root_rejected(h: _Harness) -> None:
    result = h.resolve(canonical_deployment_root="/nonexistent/other-root")
    assert result.hatp_status == HATPVerificationStatus.WRONG_DEPLOYMENT
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 7. Consumption-time revocation (signer / authority / deployment)
# ═══════════════════════════════════════════════════════════════════════════


def test_signer_revocation_at_consumption_time_defeats_prior_valid(h: _Harness) -> None:
    baseline = h.resolve()
    assert baseline.hatp_status == HATPVerificationStatus.VALID

    doc = json.loads((h.store_root / "registry.json").read_text(encoding="utf-8"))
    doc["signers"][0]["status"] = "revoked"
    doc["signers"][0]["revoked_at"] = "2026-08-07T09:30:00.000Z"
    _write_registry(h.store_root, doc)

    result = h.resolve(hatp_trust_store=HATPTrustStore(_test_only_root=h.store_root))
    assert result.hatp_status == HATPVerificationStatus.REVOKED_SIGNER
    assert result.approval_present is False


def test_authority_revocation_at_consumption_time_defeats_prior_valid(h: _Harness) -> None:
    baseline = h.resolve()
    assert baseline.hatp_status == HATPVerificationStatus.VALID

    doc = json.loads((h.store_root / "registry.json").read_text(encoding="utf-8"))
    doc["authorities"][0]["status"] = "revoked"
    doc["authorities"][0]["revoked_at"] = "2026-08-07T09:30:00.000Z"
    _write_registry(h.store_root, doc)

    result = h.resolve(hatp_trust_store=HATPTrustStore(_test_only_root=h.store_root))
    assert result.hatp_status == HATPVerificationStatus.UNAUTHORIZED_SIGNER
    assert result.approval_present is False


def test_deployment_binding_revocation_at_consumption_time_defeats_prior_valid(h: _Harness) -> None:
    baseline = h.resolve()
    assert baseline.hatp_status == HATPVerificationStatus.VALID

    doc = json.loads((h.store_root / "registry.json").read_text(encoding="utf-8"))
    doc["deployment_bindings"][0]["status"] = "revoked"
    doc["deployment_bindings"][0]["revoked_at"] = "2026-08-07T09:30:00.000Z"
    _write_registry(h.store_root, doc)

    result = h.resolve(hatp_trust_store=HATPTrustStore(_test_only_root=h.store_root))
    assert result.hatp_status == HATPVerificationStatus.WRONG_DEPLOYMENT
    assert result.approval_present is False


def test_no_cached_valid_survives_trust_store_mutation_same_process(h: _Harness) -> None:
    """Two calls, same process, same proof object -- second call after
    revocation must not reuse the first call's VALID."""
    first = h.resolve()
    assert first.approval_present is False and first.hatp_status == HATPVerificationStatus.VALID

    doc = json.loads((h.store_root / "registry.json").read_text(encoding="utf-8"))
    doc["signers"][0]["status"] = "revoked"
    doc["signers"][0]["revoked_at"] = "2026-08-07T09:30:00.000Z"
    _write_registry(h.store_root, doc)
    fresh_store = HATPTrustStore(_test_only_root=h.store_root)

    second = h.resolve(hatp_trust_store=fresh_store)
    assert second.hatp_status == HATPVerificationStatus.REVOKED_SIGNER


# ═══════════════════════════════════════════════════════════════════════════
# 8. Expiry
# ═══════════════════════════════════════════════════════════════════════════


def test_future_dated_proof_beyond_skew_tolerance_expired(h: _Harness) -> None:
    forged = replace(h.proof, issued_at="2099-01-01T00:00:00.000Z")
    result = h.resolve(hatp_proof=forged)
    assert result.hatp_status == HATPVerificationStatus.EXPIRED
    assert result.approval_present is False


def test_hatp_proof_has_no_independent_staleness_ceiling_by_contract_design(h: _Harness) -> None:
    """HATP-REQ-084: HATP proof validity is binary, not a second decaying
    TTL -- freshness is RAE's own 24h `expires_at` (RAE-REQ-043). A HATP
    proof issued long before consumption, but not future-dated, must
    still verify (identity/consumption-time-authority permitting) --
    this is contract-conformant, not a defect; overall approval is still
    gated by whether the RAE Binding itself remains fresh."""
    old_proof = replace(h.proof, issued_at="2026-01-01T00:00:00.000Z")
    result = h.resolve(hatp_proof=old_proof, evaluation_time=_T0 + timedelta(hours=1))
    assert result.hatp_status == HATPVerificationStatus.VALID
    # still False overall in this deployment -- activation gate, not staleness
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 9. Exception / fail-closed matrix
# ═══════════════════════════════════════════════════════════════════════════


class _RaisingTrustStore:
    def environment_status(self):
        raise hatp.HATPTrustStoreError("boom")

    def lookup_signer(self, *a, **k):
        raise hatp.HATPTrustStoreError("boom")

    def lookup_principal(self, *a, **k):
        raise hatp.HATPTrustStoreError("boom")

    def lookup_authority(self, *a, **k):
        raise hatp.HATPTrustStoreError("boom")

    def resolve_deployment_authorization(self, *a, **k):
        raise hatp.HATPTrustStoreError("boom")

    def load_repository_enrollment(self, *a, **k):
        raise hatp.HATPTrustStoreError("boom")


def test_trust_store_exception_fails_closed(h: _Harness) -> None:
    result = h.resolve(hatp_trust_store=_RaisingTrustStore())
    assert result.approval_present is False


class _RaisingProvider:
    def verify(self, **kwargs):
        raise RuntimeError("simulated hardware I/O failure")

    def sign(self, *a, **k):
        return b"irrelevant"


def test_provider_exception_fails_closed(h: _Harness) -> None:
    result = h.resolve(hatp_provider=_RaisingProvider())
    assert result.approval_present is False


def test_readiness_inspection_exception_fails_closed(h: _Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a, **k):
        raise RuntimeError("simulated readiness failure")

    monkeypatch.setattr(rae, "inspect_hatp_verification_substrate_readiness", _raise)
    result = h.resolve()
    assert result.approval_present is False
    assert result.diagnostic is not None


# ═══════════════════════════════════════════════════════════════════════════
# 10. Legacy-flag / hidden bypass search
# ═══════════════════════════════════════════════════════════════════════════


def test_no_legacy_or_caller_supplied_authority_parameter_exists() -> None:
    forbidden = {
        "approval_present",
        "approved",
        "human_authorization",
        "is_authorized",
        "hatp_valid",
        "verification_status",
        "trusted",
        "operational",
        "force_operational",
        "allow_test_provider",
        "skip_hatp",
        "legacy_approval",
        "existing_flag",
    }
    for fn in (rae.resolve_rollback_approval_evidence_with_hatp, rae.derive_rollback_approval_present_with_hatp):
        params = set(inspect.signature(fn).parameters)
        overlap = params & forbidden
        assert not overlap, f"BLOCKING: {fn.__name__} exposes bypass parameter(s): {overlap}"


def test_no_hidden_fourth_disjunctive_success_path_in_source() -> None:
    source = inspect.getsource(rae.resolve_rollback_approval_evidence_with_hatp)
    source += inspect.getsource(rae._derive_hatp_gated_approval_present)
    for pattern in (r"\bor\s+approval", r"\bor\s+legacy_approval", r"\bor\s+human_authorization", r"\bor\s+existing"):
        assert not re.search(pattern, source), f"BLOCKING: possible disjunctive bypass matching {pattern!r}"


def test_activation_gate_not_a_caller_parameter() -> None:
    for fn in (rae.resolve_rollback_approval_evidence_with_hatp, rae.derive_rollback_approval_present_with_hatp):
        params = inspect.signature(fn).parameters
        assert "activation_operational" not in params
        assert "operational" not in params


def test_required_hatp_dependencies_have_no_default() -> None:
    """`hatp_provider`/`hatp_trust_store` are trusted-dependency-injection
    seams with no production default -- no caller can silently resolve a
    test provider/store by omission. This does NOT by itself prevent a
    caller from deliberately passing a test provider/store (see the
    verification doc's dependency-injection-trust discussion) -- Python
    structural typing cannot enforce that; it is a code-review/call-site
    boundary, tracked by the call-site-inventory tests below."""
    sig = inspect.signature(rae.resolve_rollback_approval_evidence_with_hatp)
    for name in ("hatp_provider", "hatp_trust_store"):
        assert sig.parameters[name].default is inspect.Parameter.empty


def test_test_provider_structurally_satisfies_production_protocol() -> None:
    """Architecture finding, not a defect: `HATPProofVerifierProvider` is
    a structural `Protocol` -- `TestHATPProofVerifierProvider` type-
    checks as a valid provider with nothing in the type system
    distinguishing it from a real hardware provider. Isolation currently
    depends entirely on there being zero production call sites (verified
    below), not on any code-enforced provenance check. Recorded as a
    NON-BLOCKING/DEFERRED observation for Wave 7's PB/AG3/AG5 adapter
    design, since no such adapter exists yet to misuse it."""
    assert isinstance(TestHATPProofVerifierProvider(), HATPProofVerifierProvider)


# ═══════════════════════════════════════════════════════════════════════════
# 11. Production call-site inventory (legacy vs gated API, PB/AG3/AG5)
# ═══════════════════════════════════════════════════════════════════════════


def _grep_src(pattern: str) -> list[str]:
    result = subprocess.run(
        ["grep", "-rl", pattern, "--include=*.py", str(REPO_ROOT / "src")],
        capture_output=True, text=True, check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_zero_production_callers_of_gated_api_outside_own_module() -> None:
    hits = _grep_src(r"resolve_rollback_approval_evidence_with_hatp\|derive_rollback_approval_present_with_hatp")
    outside = [h_ for h_ in hits if not h_.endswith("rollback_approval_evidence.py")]
    assert outside == [], f"Wave-6 gated API has production consumer(s) not yet independently reviewed: {outside}"


def test_zero_production_callers_of_legacy_api_feed_permission_broker() -> None:
    """The critical B-149O-1..4 systemic-closure question: does any
    production module import `resolve_rollback_approval_evidence`/
    `derive_rollback_approval_present` (legacy, RAE-alone, still
    separately forgeable per HATP-REQ-095) and feed its result into
    Permission Broker or rollback execution authority?"""
    hits = _grep_src(r"resolve_rollback_approval_evidence\b\|derive_rollback_approval_present\b")
    outside = [h_ for h_ in hits if not h_.endswith("rollback_approval_evidence.py")]
    assert outside == [], f"legacy RAE API has production consumer(s): {outside}"


def test_permission_broker_approval_present_is_caller_supplied_not_rae_derived() -> None:
    """Confirms `approval_present`/`human_approval_present` reaching
    Permission Broker today are plain caller-supplied booleans (CLI
    args), with no import of `rollback_approval_evidence` or
    `human_approval_trusted_provenance` anywhere in the PB module chain
    -- i.e. Wave 6 is API-level integration only, not yet system-wired.
    This is expected per HATP-REQ-105/106 (AG3/AG5 PB wiring is a
    separately-governed future step) and is NOT itself a Wave-6 defect."""
    for module in ("permission_broker.py", "permission_broker_foundation.py", "mutation_permission.py"):
        text = (REPO_ROOT / "src" / "pcae" / "core" / module).read_text(encoding="utf-8")
        tree = ast.parse(text)
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)
        assert not any("rollback_approval_evidence" in n or "human_approval_trusted_provenance" in n for n in imported_names), (
            f"{module} unexpectedly imports RAE/HATP -- re-adjudicate B-149O-1..4 legacy-path closure"
        )


def test_no_permission_broker_or_agent_import_in_gated_module() -> None:
    text = (REPO_ROOT / "src" / "pcae" / "core" / "rollback_approval_evidence.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    forbidden_substrings = ("permission_broker", "mutation_permission", "agent", "fido2", "cryptography", "hatp_hardware_credentials")
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    for name in imported:
        for forbidden in forbidden_substrings:
            assert forbidden not in name, f"BLOCKING: forbidden import {name!r} in gated integration module"


def test_hatp_module_has_no_reverse_import_of_rae() -> None:
    """AST-based, not substring -- the module's own docstrings *discuss*
    `rollback_approval_evidence.py` in prose (describing the one-way
    dependency boundary itself), which a naive substring search
    incorrectly flags. Only actual `import`/`from ... import` statements
    count."""
    text = (REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    assert not any("rollback_approval_evidence" in name for name in imported)


# ═══════════════════════════════════════════════════════════════════════════
# 12. Threat-A full forgery through the gated API
# ═══════════════════════════════════════════════════════════════════════════


def test_threat_a_hand_forged_hatp_proof_unenrolled_signer_rejected(h: _Harness) -> None:
    """Attacker (agent OS principal, per HATP-001 threat model) hand-
    constructs a `HumanApprovalProvenanceProof` with correct-looking
    identity/digest fields but a signer key never enrolled in the
    protected trust store, and signs it with their own (agent-
    controlled) fake provider key."""
    attacker_provider = TestHATPProofVerifierProvider()
    forged = replace(h.proof, signer_key_id="attacker-controlled-key")
    evidence = h.evidence_for(forged, attacker_provider)
    result = h.resolve(hatp_proof=forged, hatp_evidence=evidence, hatp_provider=attacker_provider)
    assert result.hatp_status == HATPVerificationStatus.UNKNOWN_SIGNER
    assert result.approval_present is False


def test_threat_a_hand_forged_rae_chain_no_hatp_proof_rejected(tmp_path: Path) -> None:
    """Full B-149O-1/B-149O-3-class attack: attacker fabricates the
    entire RAE artifact chain (fake CHGR record + fake publication
    receipt, via the real API but self-serve/no genuine external human
    review) and supplies no HATP proof at all through the *gated* API.
    Distinct from the historical suite (which tests RAE alone) -- this
    drives the identical forged-artifact-chain scenario through the new
    Wave-6 entry point specifically."""
    h2 = _Harness(tmp_path)
    result = h2.resolve(hatp_proof=None)
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert result.approval_present is False


def test_threat_a_genuine_rae_chain_no_hatp_proof_cannot_approve_through_gated_api(h: _Harness) -> None:
    """Even a fully *genuine* RAE chain (real CHGR Decision, real
    publication, real Binding -- the exact scenario that resolves
    `approval_present=True` through the legacy, RAE-alone function per
    HATP-REQ-095) cannot approve through the gated API without a HATP
    proof. This is the precise boundary the historical B-149O-1..4
    attacks exploit against the legacy path and the exact gap Wave 6
    exists to close for callers that use the new path."""
    legacy_only = rae.resolve_rollback_approval_evidence(
        rae.Ag3RollbackApprovalContext(job_id=h.job_id, original_commit_sha=h.commit_sha, task_id=None, repository_state=_repo_state()),
        h.binding.evidence_id,
        evidence_store=h.rae_store,
        publication_root=h.pub_root,
    )
    assert legacy_only.approval_present is True  # HATP-REQ-095: RAE-001 alone, compatible as-is

    gated = h.resolve(hatp_proof=None)
    assert gated.hatp_status == HATPVerificationStatus.MISSING
    assert gated.approval_present is False


def test_threat_a_copied_genuine_proof_wrong_binding_context_rejected(h: _Harness, tmp_path: Path) -> None:
    """Attacker copies a genuine, validly-signed HATP proof/signature
    wholesale and attempts to present it for a *different* genuine
    Binding (repository state changed / different rollback attempt)."""
    other_store_root = tmp_path / "other-evidence"
    other_store = rae.RollbackApprovalEvidenceStore(root=other_store_root)
    other_op_ref = rae.Ag3OperationReference(job_id="job-other", original_commit_sha="e" * 40)
    other_pub_root = tmp_path / "other-pub"
    other_decision_ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="job-other|" + "e" * 40,
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "local-operator",
            "captured_at": "2026-08-07T08:00:00Z",
        },
        operator_id="local-operator",
        publication_store=PublicationRecordStore(root=other_pub_root),
    )
    other_binding = rae.create_rollback_approval_binding(
        decision_ref=other_decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=other_op_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=other_pub_root,
        evidence_store=other_store,
    )
    ctx = rae.Ag3RollbackApprovalContext(job_id="job-other", original_commit_sha="e" * 40, task_id=None, repository_state=_repo_state())
    # h.proof (genuine, VALID-eligible, but for h.binding) copied wholesale.
    result = rae.resolve_rollback_approval_evidence_with_hatp(
        ctx,
        other_binding.evidence_id,
        hatp_proof=h.proof,
        hatp_evidence=h.evidence_for(h.proof),
        hatp_provider=h.provider,
        hatp_trust_store=h.trust_store,
        current_repository_id=h.repo_id,
        canonical_deployment_root=h.canonical_root,
        evaluation_time=_T0 + timedelta(hours=1),
        evidence_store=other_store,
        publication_root=other_pub_root,
    )
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 13. Boundary-scope: no execution/runtime/PB semantic change introduced
# ═══════════════════════════════════════════════════════════════════════════


def test_integrated_evidence_carries_no_permission_or_execution_field() -> None:
    field_names = {f.name for f in rae.HATPIntegratedApprovalEvidence.__dataclass_fields__.values()}
    forbidden = {"permission", "allow", "deny", "execute", "authorized_to_execute"}
    assert not (field_names & forbidden)


def test_wave4_operational_ceiling_source_still_load_bearing() -> None:
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    assert "provider_profile_available = False" in source
    assert "provider_attestation_trusted = False" in source
    assert "assert operational is False" in source


def test_no_production_source_changed_by_this_phase() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pcae/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    changed = [line for line in result.stdout.splitlines() if line]
    assert changed == [], f"149O.5 must not modify production source, found: {changed}"
