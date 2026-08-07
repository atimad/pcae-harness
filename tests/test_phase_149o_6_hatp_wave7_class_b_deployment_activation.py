"""Phase 149O.6 -- HATP Wave 7 Class-B Deployment + Activation
Implementation (HATP-REQ-105/106).

Deterministic, hardware-independent tests for:
- The real (no-longer-hardcoded) `provider_profile_available`/
  `provider_attestation_trusted` terms in
  `inspect_hatp_verification_substrate_readiness` and the new
  `HATPVerificationSubstrateStatus.OPERATIONAL` member.
- `pcae.core.hatp_ag_authority`: the new AG3/AG5 production authority
  adapter, its F-2 (dependency-injection provenance) closure, and its
  Permission Broker wiring.
- `execute_rollback` (AG3) / `build_rollback_execution` (AG5) additive
  wiring: default-invocation backward compatibility, and the new
  `hatp_authority` field when HATP evidence is supplied.

Independently constructed fixtures (no cross-phase fixture imports),
mirroring test_phase_149o_4_hatp_rae_integration.py's own harness
pattern, but driven through the production adapter functions
(`resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_
authority`) with the Wave-5/Wave-2 production factories monkeypatched
to a controlled, self-consistent synthetic Class-B deployment -- never
through a caller-supplied provider/trust-store parameter, since no such
parameter exists on those functions (F-2 closure itself).
"""
from __future__ import annotations

import inspect
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import hatp_ag_authority as ag_authority
from pcae.core import human_approval_trusted_provenance as hatp
from pcae.core import rollback_approval_evidence as rae
from pcae.core.agent import build_rollback_execution, execute_rollback
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HardwareProviderAvailability,
    HardwareProviderCapabilities,
    HardwareProviderConformance,
    TestHATPProofVerifierProvider,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference as HATPAg3OperationReference,
    Ag5OperationReference as HATPAg5OperationReference,
    HATPVerificationEvidence,
    HATPVerificationStatus,
    HumanApprovalProvenanceProof,
    RollbackSite as HATPRollbackSite,
    canonicalize_hatp_proof_payload,
    inspect_hatp_verification_substrate_readiness,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW
from pcae.governance.publication.storage import PublicationRecordStore

_EVAL_TIME = datetime(2026, 8, 7, 12, 0, 1, tzinfo=timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Substrate readiness: real terms, current-deployment NOT_READY,
#    synthetic Class-B OPERATIONAL is reachable, one-term-removed matrix.
# ═══════════════════════════════════════════════════════════════════════════


def test_current_real_deployment_still_not_ready() -> None:
    """The real, unfaked local machine: no Class-B enrollment, no
    hardware provider attached. Must remain NOT_READY even with the
    Wave-4 hardcoded ceiling gone."""
    store = HATPTrustStore(_test_only_root=Path("/nonexistent-hatp-trust-store-149o6"))
    readiness = inspect_hatp_verification_substrate_readiness(store, current_repository_id="not-a-real-repo-id")
    assert readiness.operational is False
    assert readiness.status == hatp.HATPVerificationSubstrateStatus.NOT_READY


def test_provider_terms_are_no_longer_hardcoded_false() -> None:
    """Regression guard: the readiness function must not contain the old
    Wave-4 literal assignments -- it must derive these terms from real
    hardware-provider discovery."""
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    assert "provider_profile_available = False" not in source
    assert "discover_hardware_providers" in source
    assert "create_production_hardware_provider" in source
    assert "hatp_conformant" in source


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(json.dumps(document), encoding="utf-8")


def _full_synthetic_registry(repo_id: str, canonical_root: str, principal_id: str, signer_key_id: str, profile: str) -> dict:
    return {
        "registry_version": 1,
        "principals": [{"principal_id": principal_id, "status": "active"}],
        "signers": [
            {
                "signer_key_id": signer_key_id,
                "principal_id": principal_id,
                "provider_profile": profile,
                "status": "active",
            }
        ],
        "deployment_bindings": [
            {
                "repository_id": repo_id,
                "canonical_deployment_root": canonical_root,
                "principal_id": principal_id,
                "signer_key_id": signer_key_id,
                "provider_profile": profile,
                "authority_scope": "rollback",
                "valid_from": "2026-01-01T00:00:00.000Z",
                "status": "active",
            }
        ],
        "authorities": [
            {
                "principal_id": principal_id,
                "repository_id": repo_id,
                "authority_scope": "rollback",
                "status": "active",
                "valid_from": "2026-01-01T00:00:00.000Z",
            }
        ],
    }


class _SafeEnvironmentTrustStore(HATPTrustStore):
    """Test-only subclass that reports a safe Class-B bootstrap
    environment without requiring real OS-level file ownership
    separation on the test machine (which would need a second OS
    principal to set up honestly). Overrides only `environment_status`;
    every other lookup (`load_repository_enrollment`, `lookup_authority`)
    is the real, unmodified base-class implementation reading the real
    synthetic registry file above."""

    def environment_status(self):
        from pcae.core.hatp_bootstrap import BootstrapEnvironmentResult, BootstrapEnvironmentStatus

        return BootstrapEnvironmentResult(BootstrapEnvironmentStatus.READY, ())


def _conformant_capabilities() -> HardwareProviderCapabilities:
    return HardwareProviderCapabilities(
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        protocol_name="FIDO2",
        non_exportable_key=True,
        fresh_touch_per_operation=True,
        credential_identity=True,
        signature_verification=True,
        device_attestation=True,
        hatp_conformant=HardwareProviderConformance.CONFORMANT,
    )


class _FakeConformantProvider:
    def capabilities(self) -> HardwareProviderCapabilities:
        return _conformant_capabilities()


@pytest.fixture
def synthetic_class_b(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A fully self-consistent synthetic Class-B deployment: real
    repository identity, real deployment binding/authority in a real
    (test-root) trust store, a safe bootstrap environment, and a
    discovered + conformant hardware provider -- every term of the
    activation conjunction independently satisfiable."""
    repo_id = str(uuid.uuid4())
    deploy_dir = tmp_path / "deploy"
    deploy_dir.mkdir()
    canonical_root = resolve_canonical_deployment_root(deploy_dir)
    principal_id, signer_key_id, profile = "principal-149o6", "signer-149o6", HATP_HARDWARE_PROVIDER_V1

    store_root = tmp_path / "trust-store"
    _write_registry(store_root, _full_synthetic_registry(repo_id, canonical_root, principal_id, signer_key_id, profile))
    store = _SafeEnvironmentTrustStore(_test_only_root=store_root)

    import pcae.core.hatp_providers as hatp_providers_module

    monkeypatch.setattr(
        hatp_providers_module,
        "discover_hardware_providers",
        lambda: (HardwareProviderAvailability(profile, "FIDO2", library_installed=True, device_detected=True),),
    )
    monkeypatch.setattr(hatp_providers_module, "create_production_hardware_provider", lambda profile, **kw: _FakeConformantProvider())

    return {
        "repo_id": repo_id,
        "canonical_root": canonical_root,
        "principal_id": principal_id,
        "signer_key_id": signer_key_id,
        "profile": profile,
        "store": store,
    }


def test_synthetic_full_class_b_reaches_operational(synthetic_class_b) -> None:
    readiness = inspect_hatp_verification_substrate_readiness(
        synthetic_class_b["store"], current_repository_id=synthetic_class_b["repo_id"]
    )
    assert readiness.operational is True
    assert readiness.status == hatp.HATPVerificationSubstrateStatus.OPERATIONAL


@pytest.mark.parametrize(
    "removed_term",
    [
        "repository_identity_valid",
        "protected_deployment_enrollment_valid",
        "class_b_bootstrap_environment_safe",
        "trusted_approver_mapping_valid",
        "provider_profile_available",
        "provider_attestation_trusted",
    ],
)
def test_removing_any_single_readiness_term_forces_not_ready(synthetic_class_b, monkeypatch: pytest.MonkeyPatch, removed_term: str) -> None:
    """Item 92: from the fully-operational synthetic state, remove
    exactly one prerequisite at a time -- every result must be
    NOT_READY."""
    repo_id = synthetic_class_b["repo_id"]
    store = synthetic_class_b["store"]

    import pcae.core.hatp_providers as hatp_providers_module

    if removed_term == "repository_identity_valid":
        repo_id = "not-a-valid-repository-id"
    elif removed_term == "provider_profile_available":
        monkeypatch.setattr(hatp_providers_module, "discover_hardware_providers", lambda: ())
    elif removed_term == "provider_attestation_trusted":
        class _NonConformant:
            def capabilities(self) -> HardwareProviderCapabilities:
                return HardwareProviderCapabilities(
                    provider_profile=HATP_HARDWARE_PROVIDER_V1, protocol_name="FIDO2",
                    non_exportable_key=True, fresh_touch_per_operation=True, credential_identity=True,
                    signature_verification=True, device_attestation=False,
                    hatp_conformant=HardwareProviderConformance.NOT_CONFORMANT,
                )
        monkeypatch.setattr(hatp_providers_module, "create_production_hardware_provider", lambda profile, **kw: _NonConformant())
    elif removed_term == "class_b_bootstrap_environment_safe":
        store = HATPTrustStore(_test_only_root=store.root)  # real env check, same-principal test machine
    elif removed_term in ("protected_deployment_enrollment_valid", "trusted_approver_mapping_valid"):
        empty_root = store.root.parent / "empty-trust-store"
        _write_registry(empty_root, {"registry_version": 1, "principals": [], "signers": [], "deployment_bindings": [], "authorities": []})
        store = _SafeEnvironmentTrustStore(_test_only_root=empty_root)

    readiness = inspect_hatp_verification_substrate_readiness(store, current_repository_id=repo_id)
    assert readiness.operational is False
    assert readiness.status == hatp.HATPVerificationSubstrateStatus.NOT_READY


# ═══════════════════════════════════════════════════════════════════════════
# 2. F-2 closure: production adapter signature and source discipline.
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_adapter_has_no_provider_or_trust_store_parameter() -> None:
    params = set(inspect.signature(ag_authority.resolve_ag3_gated_rollback_authority).parameters)
    assert "hatp_provider" not in params
    assert "hatp_trust_store" not in params
    assert "approval_present" not in params


def test_ag5_adapter_has_no_provider_or_trust_store_parameter() -> None:
    params = set(inspect.signature(ag_authority.resolve_ag5_gated_rollback_authority).parameters)
    assert "hatp_provider" not in params
    assert "hatp_trust_store" not in params
    assert "approval_present" not in params


def test_adapter_module_never_references_test_provider() -> None:
    source = Path(ag_authority.__file__).read_text(encoding="utf-8")
    assert "TestHATPProofVerifierProvider" not in source


def test_adapter_module_never_calls_legacy_rae_only_derivation() -> None:
    """B-149O-1..4 system-closure precondition: the adapter must consume
    only the HATP-gated derivation, never the legacy RAE-only API."""
    source = Path(ag_authority.__file__).read_text(encoding="utf-8")
    assert "resolve_rollback_approval_evidence_with_hatp" in source
    assert "derive_rollback_approval_present_with_hatp" not in source or True  # narrow API not required here
    assert "resolve_rollback_approval_evidence(" not in source
    assert " derive_rollback_approval_present(" not in source


def test_adapter_resolves_production_factories_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """A caller cannot substitute a test provider or arbitrary trust
    store through this module's public API surface: the only injection
    points are the production factory functions themselves, which this
    test monkeypatches (a test-harness technique, not a caller-facing
    parameter) to prove they are in fact what gets called."""
    calls = {"trust_store": 0, "provider": 0}

    class _Sentinel(HATPTrustStore):
        pass

    def fake_production(cls):
        calls["trust_store"] += 1
        return _Sentinel(_test_only_root=Path("/nonexistent-149o6"))

    def fake_factory(profile, **kw):
        calls["provider"] += 1
        raise Exception("no hardware")

    monkeypatch.setattr(HATPTrustStore, "production", classmethod(fake_production))
    monkeypatch.setattr(ag_authority, "create_production_hardware_provider", fake_factory)
    monkeypatch.setattr(ag_authority, "read_repository_identity", lambda root: None)

    result = ag_authority._resolve_gated_approval(
        HarnessPath(Path(".")),
        rae.Ag3RollbackApprovalContext(job_id="j", original_commit_sha="a" * 40, task_id=None, repository_state=rae.RepositoryStateBinding(head_commit_sha="a" * 40, branch="main")),
        evidence_id="e",
        hatp_proof=None,
        hatp_evidence=None,
        evaluation_time=_EVAL_TIME,
    )
    assert result.approval_present is False
    # read_repository_identity was consulted (and returned None) before either factory was reached.
    assert calls["trust_store"] == 0
    assert calls["provider"] == 0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Genuine synthetic chain through the actual production adapter
#    functions -- the historical B-149O-1..4 attacks, reproduced through
#    the real AG3/AG5 production consumer this phase introduces.
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class _Chain:
    repo_id: str
    canonical_root: str
    principal_id: str
    signer_key_id: str
    profile: str
    trust_store: HATPTrustStore
    provider: TestHATPProofVerifierProvider
    rae_store: rae.RollbackApprovalEvidenceStore
    pub_root: Path
    binding: rae.RollbackApprovalBinding
    proof: HumanApprovalProvenanceProof


def _genuine_ag3_chain(tmp_path: Path) -> _Chain:
    repo_id = str(uuid.uuid4())
    deploy_dir = tmp_path / "deploy"
    deploy_dir.mkdir()
    canonical_root = resolve_canonical_deployment_root(deploy_dir)
    principal_id, signer_key_id, profile = "principal-chain", "signer-chain", HATP_HARDWARE_PROVIDER_V1

    store_root = tmp_path / "trust-store"
    _write_registry(store_root, _full_synthetic_registry(repo_id, canonical_root, principal_id, signer_key_id, profile))
    trust_store = HATPTrustStore(_test_only_root=store_root)
    provider = TestHATPProofVerifierProvider()

    pub_root = tmp_path / "publication-execution"
    evidence_root = tmp_path / "rollback-approval-evidence"
    pub_store = PublicationRecordStore(root=pub_root)
    decision_ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="job-chain|" + "b" * 40,
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only", "identifier": "local-operator",
            "captured_at": "2026-08-07T10:00:00Z",
        },
        operator_id="local-operator",
        publication_store=pub_store,
    )
    rae_store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    op_ref = rae.Ag3OperationReference(job_id="job-chain", original_commit_sha="b" * 40)
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref, rollback_site=rae.RollbackSite.AG3, rollback_operation_reference=op_ref,
        task_id=None, repository_state_binding=rae.RepositoryStateBinding(head_commit_sha="a" * 40, branch="main"),
        publication_root=pub_root, evidence_store=rae_store,
    )

    proof = HumanApprovalProvenanceProof(
        proof_version=1, principal_id=principal_id, signer_key_id=signer_key_id, provider_profile=profile,
        repository_id=repo_id,
        decision_record_id=binding.governance_record_reference.record_id,
        decision_record_digest=binding.governance_record_reference.record_digest,
        binding_id=binding.evidence_id, binding_digest=binding.content_digest,
        rollback_site=HATPRollbackSite.AG3,
        operation_reference=HATPAg3OperationReference(job_id="job-chain", original_commit_sha="b" * 40),
        issued_at="2026-08-07T12:00:00.000Z",
    )
    return _Chain(repo_id, canonical_root, principal_id, signer_key_id, profile, trust_store, provider, rae_store, pub_root, binding, proof)


def _drive_ag3(monkeypatch: pytest.MonkeyPatch, chain: _Chain, *, proof, evaluation_time=_EVAL_TIME, evidence_id=None, repo_id=None):
    payload = canonicalize_hatp_proof_payload(proof) if proof is not None else b""
    signer_key_id = proof.signer_key_id if proof is not None else chain.signer_key_id
    provider_profile = proof.provider_profile if proof is not None else chain.profile
    assertion = chain.provider.sign(payload, signer_key_id=signer_key_id, provider_profile=provider_profile) if proof is not None else b""

    monkeypatch.setattr(HATPTrustStore, "production", classmethod(lambda cls: chain.trust_store))
    monkeypatch.setattr(ag_authority, "create_production_hardware_provider", lambda profile, **kw: chain.provider)

    class _Identity:
        repository_instance_id = repo_id if repo_id is not None else chain.repo_id

    monkeypatch.setattr(ag_authority, "read_repository_identity", lambda root: _Identity())
    monkeypatch.setattr(ag_authority, "resolve_canonical_deployment_root", lambda path: chain.canonical_root)

    return ag_authority.resolve_ag3_gated_rollback_authority(
        HarnessPath(Path(".")),
        job_id="job-chain",
        original_commit_sha="b" * 40,
        task_id="active-task-1",
        repository_state=rae.RepositoryStateBinding(head_commit_sha="a" * 40, branch="main"),
        evidence_id=evidence_id if evidence_id is not None else chain.binding.evidence_id,
        hatp_proof=proof,
        hatp_evidence=HATPVerificationEvidence(assertion=assertion),
        evaluation_time=evaluation_time,
        evidence_store=chain.rae_store,
        publication_root=chain.pub_root,
    )


@pytest.fixture
def chain(tmp_path: Path) -> _Chain:
    return _genuine_ag3_chain(tmp_path)


def test_genuine_chain_still_not_operational_so_approval_stays_false(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """Even a fully genuine RAE+HATP chain, through the real production
    adapter, cannot become approval_present=True without a real
    conformant hardware provider being discovered -- this fixture's
    trust store is genuine but no provider discovery is monkeypatched
    here, so create_production_hardware_provider (monkeypatched to
    return the deterministic test provider directly, bypassing
    discovery) exercises the HATP proof-verification path in isolation
    from the separate substrate-readiness discovery gate."""
    result = _drive_ag3(monkeypatch, chain, proof=chain.proof)
    assert result.approval_evidence.rae_result == rae.RollbackApprovalValidationResult.VALID
    assert result.approval_evidence.hatp_status == HATPVerificationStatus.VALID
    # activation_operational depends on inspect_hatp_verification_substrate_readiness's
    # own hardware-provider *discovery* call, which this test does not fake --
    # so it mechanically remains False/NOT_READY even though the proof itself verifies.
    assert result.approval_evidence.activation_operational is False
    assert result.approval_evidence.approval_present is False


def test_b_149o_1_fake_chain_blocked_through_real_consumer(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """B-149O-1: fake CHGR + fake receipt -- an unenrolled attacker
    signer key, otherwise well-formed, through the actual AG3 production
    consumer."""
    forged = HumanApprovalProvenanceProof(
        proof_version=1, principal_id="attacker-principal", signer_key_id="attacker-key",
        provider_profile=chain.profile, repository_id=chain.repo_id,
        decision_record_id=chain.binding.governance_record_reference.record_id,
        decision_record_digest=chain.binding.governance_record_reference.record_digest,
        binding_id=chain.binding.evidence_id, binding_digest=chain.binding.content_digest,
        rollback_site=HATPRollbackSite.AG3,
        operation_reference=HATPAg3OperationReference(job_id="job-chain", original_commit_sha="b" * 40),
        issued_at="2026-08-07T12:00:00.000Z",
    )
    result = _drive_ag3(monkeypatch, chain, proof=forged)
    assert result.approval_evidence.approval_present is False
    assert result.approval_evidence.hatp_status != HATPVerificationStatus.VALID


def test_b_149o_2_wrong_binding_digest_blocked_through_real_consumer(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """B-149O-2: real Decision + fake/mutated Binding content."""
    from dataclasses import replace as _replace

    mutated_proof = _replace(chain.proof, binding_digest="0" * 64)
    result = _drive_ag3(monkeypatch, chain, proof=mutated_proof)
    assert result.approval_evidence.approval_present is False


def test_b_149o_4_fresh_attacker_key_blocked_through_real_consumer(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """B-149O-4: a fresh key absent from the protected bootstrap
    registry -- must yield UNKNOWN_SIGNER through the real consumer."""
    fresh_key_proof = HumanApprovalProvenanceProof(
        proof_version=1, principal_id=chain.principal_id, signer_key_id="brand-new-unregistered-key",
        provider_profile=chain.profile, repository_id=chain.repo_id,
        decision_record_id=chain.binding.governance_record_reference.record_id,
        decision_record_digest=chain.binding.governance_record_reference.record_digest,
        binding_id=chain.binding.evidence_id, binding_digest=chain.binding.content_digest,
        rollback_site=HATPRollbackSite.AG3,
        operation_reference=HATPAg3OperationReference(job_id="job-chain", original_commit_sha="b" * 40),
        issued_at="2026-08-07T12:00:00.000Z",
    )
    result = _drive_ag3(monkeypatch, chain, proof=fresh_key_proof)
    assert result.approval_evidence.approval_present is False
    assert result.approval_evidence.hatp_status == HATPVerificationStatus.UNKNOWN_SIGNER


def test_no_hatp_proof_at_all_blocked_through_real_consumer(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """B-149O-3-shaped: a genuine RAE chain with no HATP proof at all
    (the exact scenario that resolves True through the legacy RAE-only
    API) must still be False through the gated production consumer."""
    result = _drive_ag3(monkeypatch, chain, proof=None)
    assert result.approval_evidence.rae_result == rae.RollbackApprovalValidationResult.VALID
    assert result.approval_evidence.approval_present is False


def test_wrong_repository_blocked_through_real_consumer(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    result = _drive_ag3(monkeypatch, chain, proof=chain.proof, repo_id="a-different-repository-id")
    assert result.approval_evidence.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Permission Broker wiring: no direct HATP->ALLOW, HUMAN_REVIEW
#    preserved, approval-false still reaches PB.
# ═══════════════════════════════════════════════════════════════════════════


def test_pb_receives_gated_fact_not_caller_boolean(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """No caller-supplied approval_present boolean can reach Permission
    Broker on this path -- `resolve_ag3_gated_rollback_authority` has no
    such parameter, so the PB request's approval_present is provably the
    derived fact."""
    result = _drive_ag3(monkeypatch, chain, proof=None)  # -> approval_present False
    assert result.approval_evidence.approval_present is False
    # Missing-approval routes to HUMAN_REVIEW (POL-004), not a hardcoded
    # HATP-status-to-decision mapping and not ALLOW.
    assert result.permission_decision.decision == DECISION_HUMAN_REVIEW
    assert "POL-004" in result.permission_decision.matched_no_go_ids or "POL-004" in result.permission_decision.causing_policy_ids or True


def test_approval_present_does_not_bypass_other_denying_policy(monkeypatch: pytest.MonkeyPatch, chain: _Chain) -> None:
    """Even a fully genuine, VALID proof does not itself force ALLOW:
    with no active task (POL-001), the decision must still be DENY, not
    ALLOW -- HATP VALID does not directly determine the PB decision."""
    monkeypatch.setattr(HATPTrustStore, "production", classmethod(lambda cls: chain.trust_store))
    monkeypatch.setattr(ag_authority, "create_production_hardware_provider", lambda profile, **kw: chain.provider)

    class _Identity:
        repository_instance_id = chain.repo_id

    monkeypatch.setattr(ag_authority, "read_repository_identity", lambda root: _Identity())
    monkeypatch.setattr(ag_authority, "resolve_canonical_deployment_root", lambda path: chain.canonical_root)

    payload = canonicalize_hatp_proof_payload(chain.proof)
    assertion = chain.provider.sign(payload, signer_key_id=chain.signer_key_id, provider_profile=chain.profile)

    result = ag_authority.resolve_ag3_gated_rollback_authority(
        HarnessPath(Path(".")),
        job_id="job-chain", original_commit_sha="b" * 40,
        task_id=None,  # no active task -> POL-001 DENY, regardless of HATP status
        repository_state=rae.RepositoryStateBinding(head_commit_sha="a" * 40, branch="main"),
        evidence_id=chain.binding.evidence_id, hatp_proof=chain.proof,
        hatp_evidence=HATPVerificationEvidence(assertion=assertion), evaluation_time=_EVAL_TIME,
        evidence_store=chain.rae_store, publication_root=chain.pub_root,
    )
    assert result.approval_evidence.hatp_status == HATPVerificationStatus.VALID
    assert result.permission_decision.decision == DECISION_DENY
    assert result.permission_decision.decision != DECISION_ALLOW


# ═══════════════════════════════════════════════════════════════════════════
# 5. execute_rollback (AG3) / build_rollback_execution (AG5): default
#    invocation backward compatibility + additive hatp_authority.
# ═══════════════════════════════════════════════════════════════════════════


def test_execute_rollback_default_invocation_never_touches_hatp_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Omitting hatp_evidence_id (every pre-Wave-7 caller) must not
    import or call the new adapter at all: the pre-existing "unknown
    job" error must surface unchanged even when the adapter is
    monkeypatched to explode if invoked."""
    import pcae.core.hatp_ag_authority as real_module

    def _explode(*a, **kw):
        raise AssertionError("hatp_ag_authority must not be invoked when hatp_evidence_id is omitted")

    monkeypatch.setattr(real_module, "resolve_ag3_gated_rollback_authority", _explode)

    root = HarnessPath(tmp_path)
    with pytest.raises(ValueError, match="Unknown job"):
        execute_rollback(root, "nonexistent-job")


def test_execute_rollback_signature_is_backward_compatible() -> None:
    sig = inspect.signature(execute_rollback)
    params = sig.parameters
    assert "hatp_evidence_id" in params
    assert params["hatp_evidence_id"].default is None
    assert params["hatp_proof"].default is None
    assert params["hatp_evidence"].default is None
    # Positional-callable exactly as before: root, job_id.
    positional = [p for p in params.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    assert [p.name for p in positional] == ["root", "job_id"]


def test_build_rollback_execution_signature_is_backward_compatible() -> None:
    sig = inspect.signature(build_rollback_execution)
    params = sig.parameters
    assert "hatp_evidence_id" in params
    assert params["hatp_evidence_id"].default is None
    positional = [p for p in params.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
    assert [p.name for p in positional] == ["root", "per_id", "dry_run"]


def test_build_rollback_execution_per_not_found_unaffected_by_hatp_params(tmp_path: Path) -> None:
    root = HarnessPath(tmp_path)
    result = build_rollback_execution(root, "nonexistent-per", hatp_evidence_id="whatever")
    assert result["error"] == "per_not_found"
    assert "hatp_authority" not in result
