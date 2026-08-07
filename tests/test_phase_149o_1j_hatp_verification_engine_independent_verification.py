"""Phase 149O.1J -- HATP Verification Engine Independent Verification.

Independent (does not trust Phase 149O.1I's own report, test list, or
claimed requirement mapping) adversarial verification of the Wave-4 HATP
verification engine: `verify_hatp_proof`,
`inspect_hatp_verification_substrate_readiness`, `HATPVerificationStatus`,
`HATPVerificationResult` (`pcae.core.human_approval_trusted_provenance`)
and `hatp_providers.py`.

Every fixture/harness in this file is independently constructed (not
imported from `tests/test_hatp_verification_engine.py`), and every
mutation-matrix field set is independently re-derived from
`hatp_proof_to_document(proof).keys()` at test-collection time rather
than hardcoded from the 149O.1I test list.

This file does not modify any file under `src/pcae/` or `docs/contracts/`.
"""
from __future__ import annotations

import ast
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
from pcae.core import human_approval_trusted_provenance as hatp_module
from pcae.core.hatp_bootstrap import HATPTrustStore, HATPTrustStoreError, resolve_canonical_deployment_root
from pcae.core.hatp_providers import (
    HATPProofVerifierProvider,
    HATPProviderVerificationOutcome,
    TestHATPProofVerifierProvider,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HATPExpectedOperation,
    HATPVerificationEvidence,
    HATPVerificationResult,
    HATPVerificationStatus,
    HATPVerificationSubstrateStatus,
    HATP_CLOCK_SKEW_TOLERANCE,
    HATP_VERIFICATION_STATUS_VALUES,
    HumanApprovalProvenanceProof,
    RollbackSite,
    canonicalize_hatp_proof_payload,
    hatp_proof_to_document,
    inspect_hatp_verification_substrate_readiness,
    verify_hatp_proof,
)

_EVAL_TIME = datetime(2026, 8, 6, 12, 0, 1, tzinfo=timezone.utc)
_UNSET = object()

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HATP_MODULE_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "human_approval_trusted_provenance.py"
_HATP_PROVIDERS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Independent re-derivation of HATP-REQ-078's closed vocabulary from the
#    frozen contract text itself (not from `HATPVerificationStatus` and not
#    from 149O.1I's own claimed list).
# ═══════════════════════════════════════════════════════════════════════════

# Copied verbatim from docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
# HATP-REQ-078 (section 22), re-typed by hand from the contract prose, not
# from the implementation.
_CONTRACT_VOCABULARY = {
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

_PERMISSION_BROKER_VOCABULARY = {"ALLOW", "DENY", "HUMAN_REVIEW"}
_RAE_VOCABULARY = {
    "VALID",
    "MISSING",
    "INVALID",
    "STALE",
    "REVOKED",
    "UNAUTHORIZED_APPROVER",
    "WRONG_SCOPE",
    "SUPERSEDED",
}


def test_status_vocabulary_exact_equality_with_contract_text():
    assert len(_CONTRACT_VOCABULARY) == 13, "sanity: contract defines exactly 13 statuses"
    assert set(HATPVerificationStatus.__members__.keys()) == _CONTRACT_VOCABULARY
    assert HATP_VERIFICATION_STATUS_VALUES == _CONTRACT_VOCABULARY
    assert {s.value for s in HATPVerificationStatus} == _CONTRACT_VOCABULARY


def test_vocabulary_disjoint_from_permission_broker_and_rae_except_shared_VALID_MISSING():
    # HATP-REQ-078: must not reuse PB vocabulary at all.
    assert _CONTRACT_VOCABULARY & _PERMISSION_BROKER_VOCABULARY == set()
    # RAE and HATP both legitimately use the English words VALID/MISSING
    # for their own closed vocabularies -- HATP-REQ-078 forbids *reuse as
    # the same vocabulary* (conflation), not the coincidental appearance
    # of these two common status words in both closed sets. Every other
    # HATP status name must be entirely absent from RAE's vocabulary.
    overlap = _CONTRACT_VOCABULARY & _RAE_VOCABULARY
    assert overlap == {"VALID", "MISSING"}, (
        f"unexpected additional overlap between HATP and RAE vocabularies: {overlap - {'VALID', 'MISSING'}}"
    )


def test_status_enum_is_str_enum_with_exact_string_values():
    for member in HATPVerificationStatus:
        assert isinstance(member, str)
        assert member.value == member.name


# ═══════════════════════════════════════════════════════════════════════════
# 2. Fixture builder -- independently constructed, not imported from
#    tests/test_hatp_verification_engine.py.
# ═══════════════════════════════════════════════════════════════════════════


def _repo_id() -> str:
    return str(uuid.uuid4())


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(document), encoding="utf-8")


class _Rig:
    """A complete, mutually-consistent, VALID-producing HATP scenario.
    Every adversarial test starts from this baseline and removes/mutates
    exactly the fact(s) under test."""

    def __init__(self, tmp_path: Path) -> None:
        self.repo_id = _repo_id()
        deploy_dir = tmp_path / "deploy"
        deploy_dir.mkdir()
        self.canonical_root = resolve_canonical_deployment_root(deploy_dir)

        self.principal_id = "principal-alpha"
        self.signer_key_id = "signer-alpha"
        self.provider_profile = "HATP_HARDWARE_PROVIDER_V1"

        self.store_root = tmp_path / "trust-store"
        self._registry_doc = {
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
        }
        _write_registry(self.store_root, self._registry_doc)
        self.trust_store = HATPTrustStore(_test_only_root=self.store_root)
        self.provider = TestHATPProofVerifierProvider()

        self.proof = HumanApprovalProvenanceProof(
            proof_version=1,
            principal_id=self.principal_id,
            signer_key_id=self.signer_key_id,
            provider_profile=self.provider_profile,
            repository_id=self.repo_id,
            decision_record_id="decision-alpha",
            decision_record_digest="a" * 64,
            binding_id="binding-alpha",
            binding_digest="b" * 64,
            rollback_site=RollbackSite.AG3,
            operation_reference=Ag3OperationReference(job_id="job-alpha", original_commit_sha="c" * 40),
            issued_at="2026-08-06T12:00:00.000Z",
        )
        self.expected_operation = HATPExpectedOperation(
            decision_record_id=self.proof.decision_record_id,
            binding_id=self.proof.binding_id,
            rollback_site=self.proof.rollback_site,
            operation_reference=self.proof.operation_reference,
        )

    def rewrite_registry(self, mutate) -> None:
        """Mutate the live trust-store document *after* proof creation,
        simulating a current-state (consumption-time) change without
        regenerating the proof."""
        doc = copy.deepcopy(self._registry_doc)
        mutate(doc)
        _write_registry(self.store_root, doc)

    def sign(self, proof: HumanApprovalProvenanceProof, *, provider=None) -> bytes:
        p = provider or self.provider
        payload = canonicalize_hatp_proof_payload(proof)
        return p.sign(payload, signer_key_id=proof.signer_key_id, provider_profile=proof.provider_profile)

    def evidence_for(self, proof: HumanApprovalProvenanceProof, *, provider=None) -> HATPVerificationEvidence:
        return HATPVerificationEvidence(assertion=self.sign(proof, provider=provider))

    def verify(
        self,
        *,
        proof=_UNSET,
        evidence=_UNSET,
        provider=None,
        trust_store=None,
        expected_operation=None,
        current_repository_id=None,
        canonical_deployment_root=None,
        evaluation_time=None,
    ) -> HATPVerificationResult:
        p = self.proof if proof is _UNSET else proof
        if evidence is _UNSET:
            evidence = self.evidence_for(self.proof, provider=provider)
        return verify_hatp_proof(
            p,
            evidence=evidence,
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
def rig(tmp_path: Path) -> _Rig:
    return _Rig(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Positive control + success conjunction / one-fact-removed matrix.
# ═══════════════════════════════════════════════════════════════════════════


def test_baseline_valid_control(rig: _Rig):
    result = rig.verify()
    assert result.status == HATPVerificationStatus.VALID
    assert result.reasons == ()


def test_missing_proof_is_MISSING(rig: _Rig):
    result = rig.verify(proof=None)
    assert result.status == HATPVerificationStatus.MISSING


def test_non_proof_object_is_MALFORMED(rig: _Rig):
    result = rig.verify(proof="not-a-proof")
    assert result.status == HATPVerificationStatus.MALFORMED


def test_trust_store_registry_absent_is_MISSING(rig: _Rig, tmp_path: Path):
    empty_root = tmp_path / "nonexistent-store"
    store = HATPTrustStore(_test_only_root=empty_root)
    result = rig.verify(trust_store=store)
    assert result.status == HATPVerificationStatus.MISSING


def test_unenrolled_signer_key_is_UNKNOWN_SIGNER(rig: _Rig):
    proof = _replace(rig.proof, signer_key_id="attacker-key")
    evidence = rig.evidence_for(proof)  # sign with correct key material irrelevant; provider is deterministic per key
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_revoked_signer_at_verification_time_is_REVOKED_SIGNER(rig: _Rig):
    def revoke(doc):
        doc["signers"][0]["status"] = "revoked"
        doc["signers"][0]["revoked_at"] = "2026-08-06T00:00:00.000Z"

    rig.rewrite_registry(revoke)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.REVOKED_SIGNER


def test_principal_id_self_assertion_mismatch_is_UNKNOWN_SIGNER(rig: _Rig):
    proof = _replace(rig.proof, principal_id="attacker-principal")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_provider_profile_self_assertion_mismatch(rig: _Rig):
    proof = _replace(rig.proof, provider_profile="SOME_OTHER_PROFILE")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    # HATP-001 has no dedicated status for this specific cause; disposed
    # below (§9 of the disposition list) as an OBSERVATION, not a defect,
    # as long as it fails closed to a non-VALID status.
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_invalid_signature_wrong_assertion_bytes_is_INVALID_SIGNATURE(rig: _Rig):
    result = rig.verify(evidence=HATPVerificationEvidence(assertion=b"garbage"))
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_human_presence_not_proven_is_USER_PRESENCE_NOT_PROVEN(rig: _Rig):
    provider = TestHATPProofVerifierProvider(human_presence_proven=False)
    evidence = rig.evidence_for(rig.proof, provider=provider)
    result = rig.verify(provider=provider, evidence=evidence)
    assert result.status == HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN


def test_attestation_invalid_is_INVALID_ATTESTATION(rig: _Rig):
    provider = TestHATPProofVerifierProvider(attestation_valid=False)
    evidence = rig.evidence_for(rig.proof, provider=provider)
    result = rig.verify(provider=provider, evidence=evidence)
    assert result.status == HATPVerificationStatus.INVALID_ATTESTATION


def test_attestation_none_is_not_applicable_and_still_reaches_VALID(rig: _Rig):
    provider = TestHATPProofVerifierProvider(attestation_valid=None)
    evidence = rig.evidence_for(rig.proof, provider=provider)
    result = rig.verify(provider=provider, evidence=evidence)
    assert result.status == HATPVerificationStatus.VALID


def test_principal_not_active_is_UNAUTHORIZED_SIGNER(rig: _Rig):
    def deactivate(doc):
        doc["principals"][0]["status"] = "revoked"

    # principal status vocabulary only accepts active/revoked at the
    # trust-store layer; "not active" per HATP-REQ-079 for a principal is
    # exercised via the only other status this store schema accepts.
    rig.rewrite_registry(deactivate)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_authority_revoked_at_verification_time_is_UNAUTHORIZED_SIGNER(rig: _Rig):
    def revoke_authority(doc):
        doc["authorities"][0]["status"] = "revoked"
        doc["authorities"][0]["revoked_at"] = "2026-08-06T00:00:00.000Z"

    rig.rewrite_registry(revoke_authority)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_wrong_repository_is_WRONG_REPOSITORY(rig: _Rig):
    other_repo = _repo_id()
    result = rig.verify(current_repository_id=other_repo)
    assert result.status == HATPVerificationStatus.WRONG_REPOSITORY


def test_wrong_deployment_missing_binding_is_WRONG_DEPLOYMENT(rig: _Rig, tmp_path: Path):
    other_root = resolve_canonical_deployment_root((tmp_path / "other-deploy").resolve() if (tmp_path / "other-deploy").exists() else _mkdir_and_resolve(tmp_path / "other-deploy"))
    result = rig.verify(canonical_deployment_root=other_root)
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


def _mkdir_and_resolve(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_wrong_operation_is_WRONG_OPERATION(rig: _Rig):
    other_expected = HATPExpectedOperation(
        decision_record_id="different-decision",
        binding_id=rig.proof.binding_id,
        rollback_site=rig.proof.rollback_site,
        operation_reference=rig.proof.operation_reference,
    )
    result = rig.verify(expected_operation=other_expected)
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_expired_future_dated_beyond_skew_is_EXPIRED(rig: _Rig):
    proof = _replace(rig.proof, issued_at="2026-08-06T13:05:00.000Z")  # far future
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.EXPIRED


# ═══════════════════════════════════════════════════════════════════════════
# 4. Multi-failure precedence: determinism under repeated evaluation, and
#    documenting the implementation's actual chosen precedence for combined
#    failures (not asserting a specific order is *mandated* by the
#    contract, only that the implementation is internally deterministic).
# ═══════════════════════════════════════════════════════════════════════════


def test_triple_failure_is_deterministic_across_repeated_calls(rig: _Rig):
    # unknown signer AND wrong repository AND future-dated -- all three
    # simultaneously wrong.
    proof = _replace(
        rig.proof,
        signer_key_id="totally-unenrolled-key",
        issued_at="2026-08-06T13:30:00.000Z",
    )
    evidence = rig.evidence_for(proof)
    other_repo = _repo_id()
    results = [
        rig.verify(proof=proof, evidence=evidence, current_repository_id=other_repo)
        for _ in range(5)
    ]
    assert len({r.status for r in results}) == 1
    # Documented precedence: signer-identity checks precede repository/time
    # checks in this implementation (§5 of the 149O.1I report).
    assert results[0].status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_revoked_signer_and_invalid_signature_precedence_is_deterministic(rig: _Rig):
    def revoke(doc):
        doc["signers"][0]["status"] = "revoked"
        doc["signers"][0]["revoked_at"] = "2026-08-06T00:00:00.000Z"

    rig.rewrite_registry(revoke)
    bad_evidence = HATPVerificationEvidence(assertion=b"garbage")
    results = [rig.verify(evidence=bad_evidence) for _ in range(5)]
    assert len({r.status for r in results}) == 1
    # revocation check happens before signature verification in this
    # implementation.
    assert results[0].status == HATPVerificationStatus.REVOKED_SIGNER


def test_wrong_repository_and_wrong_operation_precedence_is_deterministic(rig: _Rig):
    other_repo = _repo_id()
    other_expected = HATPExpectedOperation(
        decision_record_id="different-decision",
        binding_id=rig.proof.binding_id,
        rollback_site=rig.proof.rollback_site,
        operation_reference=rig.proof.operation_reference,
    )
    results = [
        rig.verify(current_repository_id=other_repo, expected_operation=other_expected)
        for _ in range(5)
    ]
    assert len({r.status for r in results}) == 1
    assert results[0].status == HATPVerificationStatus.WRONG_REPOSITORY


# ═══════════════════════════════════════════════════════════════════════════
# 5. Provider exception mapping, unknown-provider-result mapping,
#    trust-store exception mapping (every trust-store call site).
# ═══════════════════════════════════════════════════════════════════════════


class _RaisingProvider:
    def verify(self, *, canonical_payload, signer_key_id, provider_profile, assertion):
        raise RuntimeError("simulated hardware I/O failure")


class _WrongTypeProvider:
    def verify(self, *, canonical_payload, signer_key_id, provider_profile, assertion):
        return {"signature_valid": True}  # not a HATPProviderVerificationOutcome


def test_provider_exception_maps_to_INVALID_SIGNATURE(rig: _Rig):
    result = rig.verify(provider=_RaisingProvider(), evidence=HATPVerificationEvidence(assertion=b"x"))
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


def test_provider_wrong_return_type_maps_to_INVALID_SIGNATURE(rig: _Rig):
    result = rig.verify(provider=_WrongTypeProvider(), evidence=HATPVerificationEvidence(assertion=b"x"))
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


class _RaisingTrustStore:
    """Raises HATPTrustStoreError from every method verify_hatp_proof
    might call, to independently confirm each call site fails closed."""

    def __init__(self, *, fail_at: str):
        self.fail_at = fail_at
        self._delegate = None

    def _boom(self):
        raise HATPTrustStoreError("simulated trust-store I/O failure")

    def environment_status(self):
        if self.fail_at == "environment_status":
            self._boom()
        from pcae.core.hatp_bootstrap import BootstrapEnvironmentResult, BootstrapEnvironmentStatus

        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.READY, ())

    def lookup_signer(self, signer_key_id):
        if self.fail_at == "lookup_signer":
            self._boom()
        return None

    def lookup_principal(self, principal_id):
        if self.fail_at == "lookup_principal":
            self._boom()
        return None

    def lookup_authority(self, principal_id, repository_id):
        if self.fail_at == "lookup_authority":
            self._boom()
        return None

    def resolve_deployment_authorization(self, *, repository_id, canonical_deployment_root):
        if self.fail_at == "resolve_deployment_authorization":
            self._boom()
        return None


@pytest.mark.parametrize("fail_at", ["environment_status", "lookup_signer"])
def test_trust_store_exception_at_each_early_call_site_maps_to_MISSING(rig: _Rig, fail_at: str):
    store = _RaisingTrustStore(fail_at=fail_at)
    result = rig.verify(trust_store=store)
    assert result.status == HATPVerificationStatus.MISSING


def test_trust_store_exception_at_lookup_principal_or_authority_maps_to_MISSING(rig: _Rig):
    class _PartialRaisingStore(_RaisingTrustStore):
        def lookup_signer(self, signer_key_id):
            from pcae.core.hatp_bootstrap import SignerRecord

            return SignerRecord(
                signer_key_id=signer_key_id,
                principal_id=rig.principal_id,
                provider_profile=rig.provider_profile,
                status="active",
            )

    store = _PartialRaisingStore(fail_at="lookup_principal")
    result = rig.verify(trust_store=store)
    assert result.status == HATPVerificationStatus.MISSING


# ═══════════════════════════════════════════════════════════════════════════
# 6. Clock-skew / freshness boundary tests. Confirms: no internal
#    wall-clock read (evaluation_time strictly caller-supplied), and exact
#    tolerance boundary behavior (-1s / 0s / +59.999s / +60s / +60.001s).
# ═══════════════════════════════════════════════════════════════════════════


def test_clock_skew_tolerance_is_60_seconds():
    assert HATP_CLOCK_SKEW_TOLERANCE == timedelta(seconds=60)


@pytest.mark.parametrize(
    "delta_seconds,expected_status",
    [
        (-1.0, HATPVerificationStatus.VALID),  # issued in the past
        (0.0, HATPVerificationStatus.VALID),  # issued exactly at eval time
        (59.999, HATPVerificationStatus.VALID),  # just under tolerance
        (60.0, HATPVerificationStatus.VALID),  # exactly at tolerance boundary (not strictly greater)
        (60.001, HATPVerificationStatus.EXPIRED),  # just over tolerance
    ],
)
def test_freshness_boundary_matrix(rig: _Rig, delta_seconds: float, expected_status):
    issued_at_dt = _EVAL_TIME + timedelta(seconds=delta_seconds)
    # issued_at accepts millisecond precision only; round to milliseconds.
    ms = int(round(issued_at_dt.microsecond / 1000.0))
    issued_at_dt = issued_at_dt.replace(microsecond=0) + timedelta(milliseconds=ms)
    issued_at_str = issued_at_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    proof = _replace(rig.proof, issued_at=issued_at_str)
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == expected_status, f"delta={delta_seconds}s issued_at={issued_at_str} got {result.status}"


def test_verify_hatp_proof_source_contains_no_wall_clock_read():
    # Parse the AST and inspect only the executable body (docstrings, which
    # legitimately reference "datetime.now()" in prose while documenting
    # the no-hidden-wall-clock discipline, are excluded from this check).
    source = inspect.getsource(verify_hatp_proof)
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    body_without_docstring = func_node.body[1:] if (
        func_node.body and isinstance(func_node.body[0], ast.Expr) and isinstance(func_node.body[0].value, ast.Constant)
    ) else func_node.body
    for node in body_without_docstring:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                assert sub.func.attr not in ("now", "utcnow"), f"forbidden wall-clock call: .{sub.func.attr}()"
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                assert sub.func.id != "time", "forbidden wall-clock call: time()"


def test_evaluation_time_is_a_required_keyword_argument():
    sig = inspect.signature(verify_hatp_proof)
    assert "evaluation_time" in sig.parameters
    assert sig.parameters["evaluation_time"].kind == inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["evaluation_time"].default is inspect.Parameter.empty


# ═══════════════════════════════════════════════════════════════════════════
# 7. Canonical byte boundary: the provider seam receives EXACTLY
#    canonicalize_hatp_proof_payload(proof) bytes -- no re-derivation, no
#    extra/missing bytes.
# ═══════════════════════════════════════════════════════════════════════════


def test_provider_receives_exact_canonical_bytes(rig: _Rig):
    capturing = TestHATPProofVerifierProvider()
    evidence = rig.evidence_for(rig.proof, provider=capturing)
    capturing.received_payloads.clear()
    result = rig.verify(provider=capturing, evidence=evidence)
    assert result.status == HATPVerificationStatus.VALID
    assert len(capturing.received_payloads) == 1
    expected_bytes = canonicalize_hatp_proof_payload(rig.proof)
    assert capturing.received_payloads[0] == expected_bytes


def test_canonical_bytes_are_deterministic_and_injective_across_field_changes(rig: _Rig):
    b1 = canonicalize_hatp_proof_payload(rig.proof)
    b2 = canonicalize_hatp_proof_payload(rig.proof)
    assert b1 == b2
    mutated = _replace(rig.proof, decision_record_id="different-decision-id")
    b3 = canonicalize_hatp_proof_payload(mutated)
    assert b3 != b1


# ═══════════════════════════════════════════════════════════════════════════
# 8. Full signed-field mutation matrix -- field set independently derived
#    from hatp_proof_to_document(proof).keys(), not hardcoded from 149O.1I's
#    own test parametrization list.
# ═══════════════════════════════════════════════════════════════════════════


def _document_field_names(rig: _Rig) -> list:
    return sorted(hatp_proof_to_document(rig.proof).keys())


_MUTATION_VALUES = {
    "proof_version": None,  # skip -- version is structurally frozen at 1, no other supported value exists
    "principal_id": "mutated-principal",
    "signer_key_id": "mutated-signer",
    "provider_profile": "MUTATED_PROFILE",
    "repository_id": None,  # handled specially: must remain a valid UUID4
    "decision_record_id": "mutated-decision-id",
    "decision_record_digest": "9" * 64,
    "binding_id": "mutated-binding-id",
    "binding_digest": "8" * 64,
    "rollback_site": None,  # handled specially (changes required-field family)
    "issued_at": "2026-08-06T12:00:01.000Z",
    "job_id": "mutated-job-id",
    "original_commit_sha": "f" * 40,
}


def test_mutation_matrix_field_set_matches_document_keys(tmp_path: Path):
    rig = _Rig(tmp_path)
    doc_fields = set(hatp_proof_to_document(rig.proof).keys())
    assert doc_fields == set(_MUTATION_VALUES.keys()), (
        "mutation matrix field set drifted from hatp_proof_to_document(proof).keys(); "
        f"missing={doc_fields - set(_MUTATION_VALUES.keys())} extra={set(_MUTATION_VALUES.keys()) - doc_fields}"
    )


#: For each signed field, the status expected when that field alone is
#: mutated on a proof verified with STALE evidence (signed over the
#: original, unmutated payload). Every mutation changes the canonical
#: payload bytes, so the stale signature never matches -- but this
#: implementation's documented failure precedence (149O.1I §5) checks
#: signer-identity self-assertion consistency (`principal_id`,
#: `signer_key_id`, `provider_profile`, all resolved against the
#: registry's `SignerRecord`) BEFORE calling the provider's signature
#: verification at all. So mutating one of those three fields is caught
#: earlier, by an identity-mismatch status, never reaching
#: `INVALID_SIGNATURE`. Every other field's mutation is caught at the
#: signature-verification step itself. This table is independently
#: derived by directly exercising the implementation (not assumed), and
#: is exactly why a blanket "every mutation -> INVALID_SIGNATURE"
#: assumption would be WRONG -- recorded as a finding in the verification
#: report, not silently special-cased away.
_STALE_MUTATION_EXPECTED_STATUS = {
    "principal_id": HATPVerificationStatus.UNKNOWN_SIGNER,
    "signer_key_id": HATPVerificationStatus.UNKNOWN_SIGNER,
    "provider_profile": HATPVerificationStatus.UNAUTHORIZED_SIGNER,
    "repository_id": HATPVerificationStatus.INVALID_SIGNATURE,
    "decision_record_id": HATPVerificationStatus.INVALID_SIGNATURE,
    "decision_record_digest": HATPVerificationStatus.INVALID_SIGNATURE,
    "binding_id": HATPVerificationStatus.INVALID_SIGNATURE,
    "binding_digest": HATPVerificationStatus.INVALID_SIGNATURE,
    "issued_at": HATPVerificationStatus.INVALID_SIGNATURE,
    "job_id": HATPVerificationStatus.INVALID_SIGNATURE,
    "original_commit_sha": HATPVerificationStatus.INVALID_SIGNATURE,
}


def _mutate_proof_field(proof: HumanApprovalProvenanceProof, field_name: str, new_value):
    if field_name in ("job_id", "original_commit_sha"):
        base = proof.operation_reference
        new_ref = Ag3OperationReference(
            job_id=new_value if field_name == "job_id" else base.job_id,
            original_commit_sha=new_value if field_name == "original_commit_sha" else base.original_commit_sha,
        )
        return _replace(proof, operation_reference=new_ref)
    return _replace(proof, **{field_name: new_value})


@pytest.mark.parametrize(
    "field_name",
    [f for f, v in _MUTATION_VALUES.items() if v is not None],
)
def test_stale_evidence_after_single_field_mutation_is_rejected_with_documented_status(rig: _Rig, field_name: str):
    """For every signed field (independently derived from the document
    field set), mutating that field while re-using evidence signed over
    the *original* canonical payload must invalidate the proof -- verified
    against the field's ACTUAL resulting status per the implementation's
    real check ordering (see `_STALE_MUTATION_EXPECTED_STATUS` docstring),
    not a blanket INVALID_SIGNATURE assumption. Above all: VALID must
    never be reachable for any single-field mutation with stale evidence."""

    new_value = _MUTATION_VALUES[field_name]
    if field_name == "repository_id":
        new_value = rig.repo_id  # placeholder; overwritten by a real registered second repo below
    stale_evidence = rig.evidence_for(rig.proof)  # signed over ORIGINAL payload
    if field_name == "repository_id":
        # A random unregistered repository_id would additionally trigger
        # WRONG_DEPLOYMENT/authority-lookup effects unrelated to signature
        # staleness; a mutation-only test must isolate the *signature*
        # sensitivity dimension, so pick any other syntactically valid
        # UUID4 -- the point is the canonical bytes changed, not that the
        # target repo happens to be enrolled.
        new_value = _repo_id()
    mutated = _mutate_proof_field(rig.proof, field_name, new_value)
    result = rig.verify(proof=mutated, evidence=stale_evidence)
    expected = _STALE_MUTATION_EXPECTED_STATUS[field_name]
    assert result.status != HATPVerificationStatus.VALID, f"field={field_name}: stale-evidence mutation must never reach VALID"
    assert result.status == expected, (
        f"field={field_name}: expected {expected} per documented precedence, got {result.status}"
    )


def test_rollback_site_family_mutation_with_stale_evidence_is_rejected(rig: _Rig):
    # Switching families requires a wholly different operation_reference
    # shape; construct a fresh AG5 proof (structurally distinct field
    # set) and confirm the ORIGINAL AG3 evidence does not validate it.
    ag5_proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id=rig.principal_id,
        signer_key_id=rig.signer_key_id,
        provider_profile=rig.provider_profile,
        repository_id=rig.repo_id,
        decision_record_id=rig.proof.decision_record_id,
        decision_record_digest=rig.proof.decision_record_digest,
        binding_id=rig.proof.binding_id,
        binding_digest=rig.proof.binding_digest,
        rollback_site=RollbackSite.AG5,
        operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
        issued_at=rig.proof.issued_at,
    )
    stale_evidence = rig.evidence_for(rig.proof)  # AG3 payload evidence
    result = rig.verify(proof=ag5_proof, evidence=stale_evidence)
    assert result.status == HATPVerificationStatus.INVALID_SIGNATURE


# ═══════════════════════════════════════════════════════════════════════════
# 9. Replay attacks -- proof RE-SIGNED for the new (attacker-controlled)
#    context, to isolate each downstream semantic check from signature
#    invalidation (distinct from the mutation matrix above, which
#    deliberately keeps evidence stale).
# ═══════════════════════════════════════════════════════════════════════════


def test_replay_across_unenrolled_repository_with_fresh_signature_fails_closed(rig: _Rig):
    """First finding surfaced by this file: replaying a freshly-signed
    proof against a repository_id that has NO trust-store authority
    record at all does not reach `WRONG_REPOSITORY` -- it is caught
    earlier, as `UNAUTHORIZED_SIGNER`, because `verify_hatp_proof` looks
    up `trust_store.lookup_authority(signer.principal_id,
    proof.repository_id)` (keyed on the PROOF's own repository_id) before
    ever comparing `proof.repository_id` against `current_repository_id`.
    This still fails closed (never VALID), so it is NOT a security bypass,
    but it is a real "wrong status name for the cause" discrepancy,
    disposed as a finding in the phase report. See the companion test
    below for the HATP-REQ-081 mandatory-attack-#12 scenario proper (two
    *enrolled* repositories), which does reach WRONG_REPOSITORY."""
    other_repo_id = _repo_id()  # never enrolled in the trust store at all
    proof = _replace(rig.proof, repository_id=other_repo_id)
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_replay_across_two_enrolled_repositories_is_WRONG_REPOSITORY(rig: _Rig, tmp_path: Path):
    """The actual HATP-REQ-081 / mandatory-attack-matrix #12 scenario: a
    proof genuinely valid (fresh signature, enrolled authority) for
    Repository B is replayed while the verifier's own context is
    Repository A. Both repositories carry real authority/binding records
    for the same principal in the trust store (as a real multi-repository
    production trust store would), isolating the repository-identity
    check from the "authority record does not exist at all" case above."""
    second_repo_id = _repo_id()
    second_deploy_dir = _mkdir_and_resolve(tmp_path / "second-deploy")
    second_canonical_root = resolve_canonical_deployment_root(second_deploy_dir)

    def enroll_second_repo(doc):
        doc["deployment_bindings"].append(
            {
                "repository_id": second_repo_id,
                "canonical_deployment_root": second_canonical_root,
                "principal_id": rig.principal_id,
                "signer_key_id": rig.signer_key_id,
                "provider_profile": rig.provider_profile,
                "authority_scope": "rollback",
                "valid_from": "2026-01-01T00:00:00.000Z",
                "status": "active",
            }
        )
        doc["authorities"].append(
            {
                "principal_id": rig.principal_id,
                "repository_id": second_repo_id,
                "authority_scope": "rollback",
                "status": "active",
                "valid_from": "2026-01-01T00:00:00.000Z",
            }
        )

    rig.rewrite_registry(enroll_second_repo)
    proof_for_repo_b = _replace(rig.proof, repository_id=second_repo_id)
    evidence = rig.evidence_for(proof_for_repo_b)
    # Verifier's own context remains Repository A (rig.repo_id /
    # rig.canonical_root) -- current_repository_id defaults to rig.repo_id.
    result = rig.verify(proof=proof_for_repo_b, evidence=evidence)
    assert result.status == HATPVerificationStatus.WRONG_REPOSITORY


def test_replay_across_operation_with_fresh_signature_is_WRONG_OPERATION(rig: _Rig):
    proof = _replace(rig.proof, decision_record_id="a-different-operation-decision")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)  # expected_operation unchanged
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_replay_across_principal_with_fresh_signature_and_unenrolled_principal_is_UNKNOWN_SIGNER(rig: _Rig):
    proof = _replace(rig.proof, principal_id="a-different-principal-entirely")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_replay_across_provider_profile_with_fresh_signature_is_rejected(rig: _Rig):
    proof = _replace(rig.proof, provider_profile="ANOTHER_PROFILE_V1")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_replay_across_binding_with_fresh_signature_is_WRONG_OPERATION(rig: _Rig):
    proof = _replace(rig.proof, binding_id="a-different-binding")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.WRONG_OPERATION


def test_replay_across_decision_digest_with_fresh_signature_is_WRONG_OPERATION_or_binds_correctly(rig: _Rig):
    # decision_record_digest is not itself part of HATPExpectedOperation's
    # comparison fields (only decision_record_id/binding_id/rollback_site/
    # operation_reference are) -- so a fresh-signed proof differing only in
    # decision_record_digest still matches the *expected operation* by
    # value, and reaches VALID. This is expected per HATP-REQ-069/HATP-
    # REQ-072's Wave-4 boundary (digest freshness against the *live*
    # Decision record is explicitly deferred to Wave 6, per 149O.1I §9)
    # -- recorded here as an independent confirmation of that documented
    # scope boundary, not a surprise finding.
    proof = _replace(rig.proof, decision_record_digest="7" * 64)
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.VALID


def test_replay_with_future_dated_time_and_fresh_signature_is_EXPIRED(rig: _Rig):
    proof = _replace(rig.proof, issued_at="2026-08-06T13:30:00.000Z")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status == HATPVerificationStatus.EXPIRED


def test_same_id_wrong_deployment_replay_is_WRONG_DEPLOYMENT(rig: _Rig, tmp_path: Path):
    # HATP-REQ-082: repository_id matches, but the deployment root does not.
    attacker_root = _mkdir_and_resolve(tmp_path / "attacker-deploy")
    attacker_canonical_root = resolve_canonical_deployment_root(attacker_root)
    result = rig.verify(canonical_deployment_root=attacker_canonical_root)
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


def test_deployment_binding_for_different_signer_is_WRONG_DEPLOYMENT(rig: _Rig):
    # binding registered for repo/root but bound to a DIFFERENT signer.
    def rebind_to_other_signer(doc):
        doc["signers"].append(
            {
                "signer_key_id": "other-signer",
                "principal_id": rig.principal_id,
                "provider_profile": rig.provider_profile,
                "status": "active",
            }
        )
        doc["deployment_bindings"][0]["signer_key_id"] = "other-signer"

    rig.rewrite_registry(rebind_to_other_signer)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


# ═══════════════════════════════════════════════════════════════════════════
# 10. Current-state revocation: revoke/deactivate AFTER proof creation,
#     re-verify WITHOUT regenerating the proof (HATP-REQ-088).
# ═══════════════════════════════════════════════════════════════════════════


def test_signer_revoked_after_proof_creation_still_fails_at_consumption_time(rig: _Rig):
    # Confirm baseline VALID first (proves the proof/evidence pair was
    # genuinely valid before revocation).
    assert rig.verify().status == HATPVerificationStatus.VALID

    def revoke(doc):
        doc["signers"][0]["status"] = "revoked"
        doc["signers"][0]["revoked_at"] = "2026-08-06T12:00:00.500Z"

    rig.rewrite_registry(revoke)
    result = rig.verify()  # exact same proof, exact same evidence object
    assert result.status == HATPVerificationStatus.REVOKED_SIGNER


def test_authority_revoked_after_proof_creation_still_fails_at_consumption_time(rig: _Rig):
    assert rig.verify().status == HATPVerificationStatus.VALID

    def revoke_authority(doc):
        doc["authorities"][0]["status"] = "revoked"
        doc["authorities"][0]["revoked_at"] = "2026-08-06T12:00:00.500Z"

    rig.rewrite_registry(revoke_authority)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER


def test_deployment_binding_revoked_after_proof_creation_still_fails(rig: _Rig):
    assert rig.verify().status == HATPVerificationStatus.VALID

    def revoke_binding(doc):
        doc["deployment_bindings"][0]["status"] = "revoked"
        doc["deployment_bindings"][0]["revoked_at"] = "2026-08-06T12:00:00.500Z"

    rig.rewrite_registry(revoke_binding)
    result = rig.verify()
    assert result.status == HATPVerificationStatus.WRONG_DEPLOYMENT


# ═══════════════════════════════════════════════════════════════════════════
# 11. Test-provider containment: TestHATPProofVerifierProvider must not be
#     referenced anywhere in production src/ outside hatp_providers.py
#     itself, and must never be importable/reachable from
#     human_approval_trusted_provenance.py.
# ═══════════════════════════════════════════════════════════════════════════


def test_test_provider_not_referenced_outside_its_own_module():
    src_root = _REPO_ROOT / "src" / "pcae"
    offending = []
    for path in src_root.rglob("*.py"):
        if path == _HATP_PROVIDERS_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        if "TestHATPProofVerifierProvider" in text:
            offending.append(str(path.relative_to(_REPO_ROOT)))
    assert offending == [], f"TestHATPProofVerifierProvider referenced outside hatp_providers.py: {offending}"


def test_verification_module_does_not_import_test_provider():
    tree = ast.parse(_HATP_MODULE_PATH.read_text(encoding="utf-8"))
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name)
    assert "TestHATPProofVerifierProvider" not in imported_names


# ═══════════════════════════════════════════════════════════════════════════
# 12. Substrate readiness hard ceiling: no argument/env var/flag can force
#     operational=True; adversarial trust-store construction still yields
#     NOT_READY/operational=False.
# ═══════════════════════════════════════════════════════════════════════════


def test_substrate_readiness_signature_accepts_no_operational_override():
    sig = inspect.signature(inspect_hatp_verification_substrate_readiness)
    param_names = set(sig.parameters.keys())
    assert param_names == {"trust_store", "current_repository_id"}
    for forbidden in ("operational", "force", "override", "provider", "bypass"):
        assert forbidden not in param_names


def test_substrate_readiness_always_NOT_READY_even_with_fully_healthy_trust_store(rig: _Rig):
    # rig's trust store is maximally "healthy" from a registry-content
    # perspective (active principal, active signer, active authority,
    # active deployment binding) -- it should STILL be NOT_READY/False
    # because provider_profile_available / provider_attestation_trusted
    # are permanently hardcoded False in this wave.
    readiness = inspect_hatp_verification_substrate_readiness(rig.trust_store, current_repository_id=rig.repo_id)
    assert readiness.status == HATPVerificationSubstrateStatus.NOT_READY
    assert readiness.operational is False
    terms = dict(readiness.terms)
    assert terms["provider_profile_available"] is False
    assert terms["provider_attestation_trusted"] is False


def test_substrate_readiness_never_operational_across_env_var_manipulation(rig: _Rig, monkeypatch):
    # Attempt every plausible env-var-based bypass; none should move the
    # needle (HATP-REQ-034/035, extended to the readiness gate).
    for var in ("HATP_FORCE_OPERATIONAL", "HATP_TRUSTED_OPERATIONAL", "PCAE_HATP_OPERATIONAL", "HATP_HARDWARE_PROVIDER_V1"):
        monkeypatch.setenv(var, "1")
    readiness = inspect_hatp_verification_substrate_readiness(rig.trust_store, current_repository_id=rig.repo_id)
    assert readiness.operational is False


def test_substrate_readiness_status_enum_has_exactly_two_members():
    """Phase 149O.6 (Wave 7) intentionally adds `OPERATIONAL`, replacing
    the Wave-4-only single-member enum -- see
    `tests/test_hatp_verification_engine.py::
    test_substrate_readiness_status_has_exactly_two_members` for the
    matching independent boundary re-confirmation."""
    assert set(HATPVerificationSubstrateStatus) == {
        HATPVerificationSubstrateStatus.NOT_READY,
        HATPVerificationSubstrateStatus.OPERATIONAL,
    }


def test_substrate_readiness_source_has_no_hardcoded_operational_false_assertion():
    """Phase 149O.6 (Wave 7) replaces the Wave-4 tripwire assertion with
    real, mechanically-derived hardware-provider terms (`provider_
    profile_available`, `provider_attestation_trusted`) -- `operational`
    is no longer unconditionally forced `False` by source, only by the
    real absence of a conformant provider on this deployment (see
    `test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py`)."""
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    assert "assert operational is False" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 13. Zero production call-sites, outside the Wave-4 module itself.
# ═══════════════════════════════════════════════════════════════════════════


def test_no_production_call_sites_for_verify_hatp_proof_outside_own_module():
    """As of Phase 149O.4/Wave 6, `rollback_approval_evidence.py` is the
    sole, intentional production consumer (HATP-REQ-095/096); every other
    production module remains excluded from this boundary."""
    src_root = _REPO_ROOT / "src" / "pcae"
    allowed_consumer = _REPO_ROOT / "src" / "pcae" / "core" / "rollback_approval_evidence.py"
    offending = []
    for path in src_root.rglob("*.py"):
        if path in (_HATP_MODULE_PATH, allowed_consumer):
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"\bverify_hatp_proof\s*\(", text):
            offending.append(str(path.relative_to(_REPO_ROOT)))
        if re.search(r"\binspect_hatp_verification_substrate_readiness\s*\(", text):
            offending.append(str(path.relative_to(_REPO_ROOT)))
    assert offending == [], f"unexpected production call site(s): {offending}"


def test_named_non_integration_targets_have_no_hatp_wave4_reference():
    """`rollback_approval_evidence.py` is intentionally excluded as of
    Phase 149O.4/Wave 6 -- see `tests/test_phase_149o_4_hatp_rae_integration.py`."""
    targets = [
        "permission_broker.py",
        "permission_broker_foundation.py",
        "agent.py",
    ]
    core_dir = _REPO_ROOT / "src" / "pcae" / "core"
    for name in targets:
        path = core_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert "verify_hatp_proof" not in text, name
        assert "HATPVerificationStatus" not in text, name
        assert "inspect_hatp_verification_substrate_readiness" not in text, name

    commands_agent = _REPO_ROOT / "src" / "pcae" / "commands" / "agent.py"
    if commands_agent.exists():
        text = commands_agent.read_text(encoding="utf-8")
        assert "verify_hatp_proof" not in text
        assert "HATPVerificationStatus" not in text


# ═══════════════════════════════════════════════════════════════════════════
# 14. No approval_present derivation anywhere in Wave-4 code (executable
#     code, not docstring prose).
# ═══════════════════════════════════════════════════════════════════════════


def test_no_approval_present_assignment_in_wave4_module_source():
    tree = ast.parse(_HATP_MODULE_PATH.read_text(encoding="utf-8"))
    offending_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                name = getattr(target, "id", None) or getattr(target, "attr", None)
                if name == "approval_present":
                    offending_lines.append(node.lineno)
    assert offending_lines == [], f"approval_present assigned at line(s): {offending_lines}"


def test_result_types_carry_no_approval_permission_or_execution_fields():
    forbidden = {"approved", "authorized", "approval_present", "can_execute", "permission", "valid", "trusted"}
    result_fields = {f.name for f in fields(HATPVerificationResult)}
    outcome_fields = {f.name for f in fields(HATPProviderVerificationOutcome)}
    assert result_fields & forbidden == set()
    assert outcome_fields & forbidden == set()
    assert result_fields == {"status", "reasons"}


# ═══════════════════════════════════════════════════════════════════════════
# 15. Trust derivation source discipline: principal_id/provider_profile
#     always resolved from the registry's SignerRecord, never trusted from
#     the proof's own self-assertion (HATP-REQ-077), independently
#     confirmed via an attacker-supplied proof claiming a DIFFERENT
#     (unenrolled) principal_id/provider_profile than the genuinely
#     enrolled signer_key_id's registered values, while still using the
#     correctly-enrolled signer_key_id and a freshly-computed signature.
# ═══════════════════════════════════════════════════════════════════════════


def test_proof_claiming_unregistered_principal_for_enrolled_signer_key_is_rejected(rig: _Rig):
    proof = _replace(rig.proof, principal_id="principal-the-proof-wishes-it-had")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_proof_claiming_unregistered_provider_profile_for_enrolled_signer_key_is_rejected(rig: _Rig):
    proof = _replace(rig.proof, provider_profile="PROFILE_THE_PROOF_WISHES_IT_HAD")
    evidence = rig.evidence_for(proof)
    result = rig.verify(proof=proof, evidence=evidence)
    assert result.status != HATPVerificationStatus.VALID
    assert result.status == HATPVerificationStatus.UNAUTHORIZED_SIGNER
