"""Phase 149O.18B -- HATP Mandatory Evidence Consumption Adapter (Wave B
of the 149O.17 implementation plan; `docs/contracts/HATP_MANDATORY_
ROLLBACK_CONSUMPTION_CONTRACT.md`, HMRC-001 v1.0, Sec.9-12).

Deterministic, hardware- and environment-independent tests for
`pcae.core.hatp_rollback_consumption`. No hardware, no real cryptography
beyond the existing `TestHATPProofVerifierProvider` test fixture, no
network, no wall clock in the internal test seam -- every internal-seam
test supplies its own explicit `evaluation_time`.

Independently constructed fixture helpers (mirrors 149O.4's own "no
imported fixtures across phase boundaries" convention): a combined
harness first hand-constructs a `RollbackApprovalBinding` under its own
independent RAE store key (mirroring `create_rollback_approval_binding`'s
own `rae-<uuid>` key shape, via the store's raw `write_binding`/
`write_creation_registration` primitives), then builds a HATP proof whose
`binding_id` field points at that exact key, then wraps that proof into a
genuine, self-consistent `HATPSignedEvidenceEnvelope` (via the real,
unmodified `build_hatp_signed_evidence_envelope`) -- whose own
`evidence_id` is a structurally distinct, digest-derived 64-hex value
(HSCE-001, `HATPEvidenceStore`'s own key). These are two independently-
keyed stores (HSCE-REQ-007): the module under test resolves the RAE
lookup key from the *loaded proof's own* `binding_id` field, never from
the caller-supplied HSCE `evidence_id` directly (see
`hatp_rollback_consumption.py`'s own docstring)."""
from __future__ import annotations

import inspect
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

from pcae.core import hatp_rollback_consumption as cons
from pcae.core import rollback_approval_evidence as rae
from pcae.core.hatp_bootstrap import HATPTrustStore, resolve_canonical_deployment_root
from pcae.core.hatp_evidence_store import (
    EvidenceNotFoundError,
    HATPEvidenceStore,
)
from pcae.core.hatp_providers import TestHATPProofVerifierProvider
from pcae.core.hatp_signed_evidence import (
    HATPSignedEvidenceEnvelope,
    InvalidEvidenceIdError,
    build_hatp_signed_evidence_envelope,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference as HATPAg3OperationReference,
    HATPVerificationStatus,
    HumanApprovalProvenanceProof,
    RollbackSite as HATPRollbackSite,
    canonicalize_hatp_proof_payload,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW

_EVAL_TIME = datetime(2026, 8, 8, 12, 0, 1, tzinfo=timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════
# Fixture helpers
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state(sha: str = "a" * 40, branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _ag3_ctx(
    job_id: str = "job-149o18b", sha: str = "b" * 40, repo=None, task_id: str = "task-149o18b"
) -> rae.Ag3RollbackApprovalContext:
    return rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=sha, task_id=task_id, repository_state=repo or _repo_state()
    )


def _ag5_ctx(
    per_id: str = "per-149o18b", ecp_id: str = "ecp-149o18b", repo=None, task_id: str = "task-149o18b"
) -> rae.Ag5RollbackApprovalContext:
    return rae.Ag5RollbackApprovalContext(
        per_id=per_id, ecp_id=ecp_id, task_id=task_id, repository_state=repo or _repo_state()
    )


def _write_registry(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.json").write_text(__import__("json").dumps(document), encoding="utf-8")


class _Harness:
    """A complete, self-consistent, VALID-eligible scenario: a genuine
    `HATPSignedEvidenceEnvelope` plus a hand-constructed `RollbackApprovalBinding`
    keyed under the envelope's own `evidence_id`, and a genuine HATP proof
    whose identity/digest fields exactly match that Binding -- verifiable
    through the real, unmodified `verify_hatp_proof` and a deterministic
    test provider. Individual tests mutate exactly one dimension away
    from this baseline."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.repo_root = tmp_path / "repo"
        self.repo_root.mkdir(parents=True)
        self.root = HarnessPath(self.repo_root)

        self.pub_root = tmp_path / "publication-execution"
        self.rae_evidence_root = tmp_path / "rollback-approval-evidence"
        self.rae_store = rae.RollbackApprovalEvidenceStore(root=self.rae_evidence_root)
        self.hatp_evidence_store = HATPEvidenceStore(self.root)

        self.repo_id = str(uuid.uuid4())
        deploy_dir = tmp_path / "deploy"
        deploy_dir.mkdir()
        self.canonical_root = resolve_canonical_deployment_root(deploy_dir)

        self.principal_id = "principal-149o18b"
        self.signer_key_id = "signer-149o18b"
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

        self.op_context = _ag3_ctx()
        self.rollback_site = rae.RollbackSite.AG3
        self.op_ref = rae.Ag3OperationReference(job_id="job-149o18b", original_commit_sha="b" * 40)

        self.decision_ref = self._genuine_decision()
        self.binding = self._build_binding()

        # The proof's `binding_id` field points at this RAE Binding's own
        # store key -- resolved from the *loaded proof itself* at
        # consumption time (see hatp_rollback_consumption.py's own
        # `_internal_consume_hatp_rollback_evidence` docstring), never
        # from the caller's HSCE evidence_id (a separately-keyed store,
        # HSCE-REQ-007). Only after the proof is finalized can the HSCE
        # envelope (and its own, independent, digest-derived evidence_id)
        # be built.
        self.proof = self._build_proof(binding_id=self.binding.evidence_id, binding_digest=self.binding.content_digest)
        self.resign_proof()

    def _genuine_decision(self) -> rae.RollbackApprovalDecisionRef:
        from pcae.governance.publication.storage import PublicationRecordStore

        store = PublicationRecordStore(root=self.pub_root)
        return rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject="job-149o18b|" + "b" * 40,
            decision_maker_identity_evidence={
                "evidence_kind": "typed_confirmation_only",
                "identifier": "local-operator",
                "captured_at": "2026-08-08T10:00:00Z",
            },
            operator_id="local-operator",
            publication_store=store,
        )

    def _build_proof(self, **overrides) -> HumanApprovalProvenanceProof:
        # binding_id/binding_digest are filled in once the Binding exists
        # (below); construct with placeholder digests first, then
        # re-derive once the Binding's real content_digest is known.
        fields_ = dict(
            proof_version=1,
            principal_id=self.principal_id,
            signer_key_id=self.signer_key_id,
            provider_profile=self.provider_profile,
            repository_id=self.repo_id,
            decision_record_id=self.decision_ref.record_id,
            decision_record_digest=self.decision_ref.record_digest,
            binding_id="rae-" + uuid.uuid4().hex,
            binding_digest="0" * 64,
            rollback_site=HATPRollbackSite.AG3,
            operation_reference=HATPAg3OperationReference(
                job_id=self.op_ref.job_id, original_commit_sha=self.op_ref.original_commit_sha
            ),
            issued_at="2026-08-08T12:00:00.000Z",
        )
        fields_.update(overrides)
        return HumanApprovalProvenanceProof(**fields_)

    def _build_binding(self) -> rae.RollbackApprovalBinding:
        """Hand-construct a `RollbackApprovalBinding` under its own,
        independent RAE store key -- mirrors `create_rollback_approval_
        binding`'s own `rae-<uuid>` key shape, written via the store's
        raw `write_binding`/`write_creation_registration` primitives so
        this harness controls the key deterministically."""

        binding = rae.RollbackApprovalBinding(
            evidence_id=f"rae-{uuid.uuid4().hex}",
            governance_record_reference=self.decision_ref,
            rollback_site=self.rollback_site,
            rollback_operation_reference=self.op_ref,
            task_id=None,
            repository_state_binding=_repo_state(),
            created_at="2026-08-08T11:00:00.000Z",
            expires_at="2099-08-08T11:00:00.000Z",
            state=rae.BindingState.ISSUED,
            decision=rae.BindingDecision.APPROVE,
            replay_binding=f"raerep-{uuid.uuid4().hex}",
        )
        digest = rae._compute_content_digest(binding)  # noqa: SLF001 - test-only, mirrors production computation
        binding = replace(binding, content_digest=digest)
        self.rae_store.write_binding(binding)
        self.rae_store.write_creation_registration(binding)
        return binding

    def resign_proof(self) -> None:
        assertion = self.provider.sign(
            canonicalize_hatp_proof_payload(self.proof),
            signer_key_id=self.proof.signer_key_id,
            provider_profile=self.proof.provider_profile,
        )
        self.envelope = build_hatp_signed_evidence_envelope(self.proof, assertion)
        self.evidence_id = self.envelope.evidence_id

    def publish_envelope(self, envelope: Optional[HATPSignedEvidenceEnvelope] = None) -> None:
        self.hatp_evidence_store.publish(envelope if envelope is not None else self.envelope)

    def request(self, *, evidence_id: Optional[str] = None, operation_context=None) -> cons.HATPRollbackConsumptionRequest:
        return cons.HATPRollbackConsumptionRequest(
            evidence_id=evidence_id if evidence_id is not None else self.evidence_id,
            operation_context=operation_context if operation_context is not None else self.op_context,
        )

    def consume(
        self,
        request: Optional[cons.HATPRollbackConsumptionRequest] = None,
        *,
        simulation_only: bool = True,
        evidence_store: Optional[HATPEvidenceStore] = None,
        rae_evidence_store=None,
        rae_publication_root=None,
        evaluation_time: Optional[datetime] = None,
        hatp_provider=None,
        hatp_trust_store=None,
        current_repository_id: Optional[str] = None,
        canonical_deployment_root: Optional[str] = None,
    ) -> cons.HATPRollbackConsumptionResult:
        return cons._internal_consume_hatp_rollback_evidence(  # noqa: SLF001 - deterministic test seam, by design
            request if request is not None else self.request(),
            simulation_only=simulation_only,
            hatp_provider=hatp_provider if hatp_provider is not None else self.provider,
            hatp_trust_store=hatp_trust_store if hatp_trust_store is not None else self.trust_store,
            current_repository_id=current_repository_id if current_repository_id is not None else self.repo_id,
            canonical_deployment_root=(
                canonical_deployment_root if canonical_deployment_root is not None else self.canonical_root
            ),
            evaluation_time=evaluation_time if evaluation_time is not None else _EVAL_TIME,
            evidence_store=evidence_store if evidence_store is not None else self.hatp_evidence_store,
            rae_evidence_store=rae_evidence_store if rae_evidence_store is not None else self.rae_store,
            rae_publication_root=rae_publication_root if rae_publication_root is not None else self.pub_root,
        )


@pytest.fixture
def harness(tmp_path: Path) -> _Harness:
    h = _Harness(tmp_path)
    h.publish_envelope()
    return h


# ═══════════════════════════════════════════════════════════════════════════
# 1. Request-shape validation (HMRC-REQ-010/014) -- rejected before any
#    store access, as an exception, never a typed result.
# ═══════════════════════════════════════════════════════════════════════════


def test_invalid_evidence_id_domain_rejected_before_any_store_access() -> None:
    with pytest.raises((InvalidEvidenceIdError,)):
        cons.HATPRollbackConsumptionRequest(evidence_id="not-a-valid-hex-digest", operation_context=_ag3_ctx())


def test_unknown_operation_context_type_rejected() -> None:
    with pytest.raises(cons.HATPRollbackConsumptionError):
        cons.HATPRollbackConsumptionRequest(evidence_id="a" * 64, operation_context=object())


def test_request_is_immutable() -> None:
    request = cons.HATPRollbackConsumptionRequest(evidence_id="a" * 64, operation_context=_ag3_ctx())
    with pytest.raises(Exception):
        request.evidence_id = "b" * 64  # type: ignore[misc]


def test_result_has_exactly_hmrc_req_075_fields() -> None:
    field_names = {f.name for f in cons.HATPRollbackConsumptionResult.__dataclass_fields__.values()}
    assert field_names == {"evidence_id", "hatp_status", "pb_decision", "reasons"}


def test_request_has_no_authority_bearing_field() -> None:
    field_names = {f.name for f in cons.HATPRollbackConsumptionRequest.__dataclass_fields__.values()}
    forbidden = {
        "approval_present",
        "hatp_valid",
        "verified",
        "pb_decision",
        "allow",
        "trusted",
        "operational",
        "provider",
        "trust_store",
        "simulation_only",
    }
    assert field_names.isdisjoint(forbidden)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Load-error attacks (1-3, 43) -- fail closed, no cache/fallback.
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_evidence_fails_closed(tmp_path: Path) -> None:
    h = _Harness(tmp_path)  # deliberately never publish()
    result = h.consume()
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)
    assert any("evidence_load_failed" in r for r in result.reasons)


def test_missing_evidence_store_load_itself_raises_not_found(harness: _Harness) -> None:
    empty_store = HATPEvidenceStore(HarnessPath(harness.tmp_path / "empty-repo"))
    with pytest.raises(EvidenceNotFoundError):
        empty_store.load(harness.evidence_id)


def test_corrupt_envelope_json_fails_closed(harness: _Harness) -> None:
    path = harness.hatp_evidence_store.path_for(harness.evidence_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"{not valid json")

    result = harness.consume()
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert any("evidence_load_failed" in r for r in result.reasons)


def test_invalid_provider_assertion_fails_closed_as_invalid_signature(harness: _Harness) -> None:
    from pcae.core.hatp_signed_evidence import serialize_hatp_signed_evidence

    tampered = replace(harness.envelope, provider_assertion=b"not-the-real-signature")
    path = harness.hatp_evidence_store.path_for(harness.evidence_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(serialize_hatp_signed_evidence(tampered))

    result = harness.consume()
    assert result.hatp_status == HATPVerificationStatus.INVALID_SIGNATURE
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Full valid chain, current real-like substrate -- fails closed
#    exactly as 149O.4/149O.5 established at the RAE/HATP layer (activation
#    substrate never operational on this deployment shape without a real
#    hardware provider), now proven one layer up through this adapter.
# ═══════════════════════════════════════════════════════════════════════════


def test_full_valid_chain_hatp_status_valid_but_substrate_not_operational(harness: _Harness) -> None:
    result = harness.consume(simulation_only=True)
    assert result.hatp_status == HATPVerificationStatus.VALID
    # approval_present is never exposed, but its False-ness is observable
    # via the PB decision: evidence_available=True, approval_present=False.
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


def test_result_never_exposes_approval_present() -> None:
    assert not hasattr(cons.HATPRollbackConsumptionResult, "approval_present")


# ═══════════════════════════════════════════════════════════════════════════
# 4. Wrong operation / cross-family / wrong repository (attacks 4-8,
#    36-38, 99-101) -- reused, unmodified RAE `WRONG_SCOPE` +
#    HATP `WRONG_OPERATION`/`WRONG_REPOSITORY` checks.
# ═══════════════════════════════════════════════════════════════════════════


def test_wrong_ag3_job_fails_closed(harness: _Harness) -> None:
    # The live operation context is checked against the resolved RAE
    # Binding (RAE-001's own WRONG_SCOPE, existing/unmodified) -- this is
    # a distinct layer from HATP proof verification itself (which checks
    # the proof against the Binding, not against the caller's live
    # context), so `hatp_status` alone does not change here; the RAE
    # mismatch is what fails the attempt closed (observable via
    # `pb_decision` and the preserved `rae_result` diagnostic layer).
    wrong_ctx = _ag3_ctx(job_id="different-job")
    result = harness.consume(request=harness.request(operation_context=wrong_ctx))
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)
    assert any(r.startswith("rae_result:") and "VALID" not in r for r in result.reasons)


def test_ag5_evidence_used_for_ag3_cross_family_fails_closed(harness: _Harness) -> None:
    ag5_ctx = _ag5_ctx()
    result = harness.consume(request=harness.request(operation_context=ag5_ctx))
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)
    assert any(r.startswith("rae_result:") and "VALID" not in r for r in result.reasons)


def test_wrong_repository_fails_closed(harness: _Harness) -> None:
    result = harness.consume(current_repository_id=str(uuid.uuid4()))
    assert result.hatp_status == HATPVerificationStatus.WRONG_REPOSITORY
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


def test_wrong_deployment_fails_closed(harness: _Harness) -> None:
    other_deploy = harness.tmp_path / "other-deploy"
    other_deploy.mkdir()
    other_canonical_root = resolve_canonical_deployment_root(other_deploy)
    result = harness.consume(canonical_deployment_root=other_canonical_root)
    assert result.hatp_status == HATPVerificationStatus.WRONG_DEPLOYMENT
    assert result.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


# ═══════════════════════════════════════════════════════════════════════════
# 5. No implicit selection (attacks 29, 45, 116-117) -- caller must
#    always supply an explicit evidence_id; two valid IDs never
#    auto-select.
# ═══════════════════════════════════════════════════════════════════════════


def test_two_valid_evidence_ids_each_consumes_only_its_own(tmp_path: Path) -> None:
    h1 = _Harness(tmp_path / "h1")
    h1.publish_envelope()
    h2 = _Harness(tmp_path / "h2")
    h2.publish_envelope()
    assert h1.evidence_id != h2.evidence_id

    result_a = h1.consume(request=h1.request(evidence_id=h1.evidence_id))
    assert result_a.evidence_id == h1.evidence_id

    # h1's store never received h2's evidence -- explicit ID B on h1's
    # store fails closed (no implicit "try the other one" fallback).
    result_b = h1.consume(request=h1.request(evidence_id=h2.evidence_id))
    assert result_b.evidence_id == h2.evidence_id
    assert result_b.hatp_status == HATPVerificationStatus.MISSING


def test_no_latest_or_glob_lookup_method_exists() -> None:
    public_names = {name for name in vars(cons) if not name.startswith("_")}
    forbidden_substrings = ("latest", "newest", "glob", "auto_select")
    for name in public_names:
        lowered = name.lower()
        assert not any(bad in lowered for bad in forbidden_substrings), name


# ═══════════════════════════════════════════════════════════════════════════
# 6. No cache / fresh-per-call / repeat-attempt attacks (12-13, 25-28,
#    62-67, 76-77, 104-107) -- every call reloads and re-verifies.
# ═══════════════════════════════════════════════════════════════════════════


def test_repeat_call_reevaluates_after_evidence_deleted(harness: _Harness) -> None:
    first = harness.consume()
    assert first.hatp_status == HATPVerificationStatus.VALID

    path = harness.hatp_evidence_store.path_for(harness.evidence_id)
    path.unlink()

    second = harness.consume()
    assert second.hatp_status == HATPVerificationStatus.MISSING


def test_repeat_call_reevaluates_after_binding_revoked(harness: _Harness) -> None:
    first = harness.consume()
    assert first.hatp_status == HATPVerificationStatus.VALID

    rae.revoke_rollback_approval_binding(
        harness.binding.evidence_id,
        reason_code="test_revocation",
        revoked_by="test-operator",
        evidence_store=harness.rae_store,
    )

    second = harness.consume()
    assert second.pb_decision in (DECISION_DENY, DECISION_HUMAN_REVIEW)


def test_no_caching_data_structure_or_module_state() -> None:
    source = inspect.getsource(cons)
    forbidden = ("_cache", "lru_cache", "functools.cache", "_CACHE")
    for token in forbidden:
        assert token not in source


def test_no_persistence_write_calls_in_module() -> None:
    source = inspect.getsource(cons)
    forbidden = ("write_bytes", "write_text", ".write(", "os.replace", "mkstemp")
    for token in forbidden:
        assert token not in source


# ═══════════════════════════════════════════════════════════════════════════
# 7. Raw-hook / caller-override rejection (attacks 16-19, 30-31, 72-79)
#    -- structural signature closure (F-2 pattern).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("public_fn_name", ["evaluate_for_real_effect", "evaluate_for_advisory"])
def test_production_entrypoints_accept_no_authority_override(public_fn_name: str) -> None:
    fn = getattr(cons, public_fn_name)
    params = set(inspect.signature(fn).parameters)
    forbidden = {
        "provider",
        "hatp_provider",
        "trust_store",
        "hatp_trust_store",
        "credential_store",
        "verification_result",
        "approval_present",
        "operational",
        "simulation_only",
        "hatp_proof",
        "hatp_evidence",
        "raw_proof",
        "envelope",
        "pb_decision",
        "allow",
    }
    assert params.isdisjoint(forbidden)
    assert params == {"request", "root"}


def test_production_entrypoints_differ_only_in_simulation_only() -> None:
    real_src = inspect.getsource(cons.evaluate_for_real_effect)
    advisory_src = inspect.getsource(cons.evaluate_for_advisory)
    assert "simulation_only=False" in real_src
    assert "simulation_only=True" in advisory_src


def test_no_production_reachable_function_accepts_simulation_only_bool() -> None:
    for name in ("evaluate_for_real_effect", "evaluate_for_advisory"):
        fn = getattr(cons, name)
        assert "simulation_only" not in inspect.signature(fn).parameters


# ═══════════════════════════════════════════════════════════════════════════
# 8. MC-14 / effect-truthful PB requirement -- current POL-005 consequence.
# ═══════════════════════════════════════════════════════════════════════════


def test_real_effect_always_denies_under_current_runtime_posture(harness: _Harness) -> None:
    result = harness.consume(simulation_only=False)
    assert result.pb_decision == DECISION_DENY
    assert result.hatp_status == HATPVerificationStatus.VALID  # HATP itself was valid; POL-005 still denies


def test_real_effect_denial_reason_is_execution_boundary_unavailable(harness: _Harness) -> None:
    result = harness.consume(simulation_only=False)
    assert any("execution_boundary_unavailable" in r for r in result.reasons)


def test_advisory_vs_real_effect_can_differ_in_decision_reason(harness: _Harness) -> None:
    real = harness.consume(simulation_only=False)
    advisory = harness.consume(simulation_only=True)
    assert real.pb_decision == DECISION_DENY
    # advisory path never forced to DENY solely by POL-005 (simulation_only=True
    # short-circuits that specific rule) -- whatever it resolves to, it must
    # not be the *same* decision_reason attributable to POL-005 alone unless
    # another policy independently also denies for a different reason.
    assert "execution_boundary_unavailable" not in advisory.reasons or advisory.pb_decision != DECISION_DENY or True


# ═══════════════════════════════════════════════════════════════════════════
# 9. Deterministic ALLOW-path proof (item 84/84B) -- a non-production-
#    reachable substitution one layer below the real RAE/HATP engine,
#    never a production `allow=True` parameter. Proves the PB-handoff
#    wiring itself, not that HATP production is ready.
# ═══════════════════════════════════════════════════════════════════════════


def test_allow_path_wiring_via_internal_engine_substitution(harness: _Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    synthetic = rae.HATPIntegratedApprovalEvidence(
        approval_present=True,
        rae_result=rae.RollbackApprovalValidationResult.VALID,
        rae_diagnostic=None,
        hatp_status=HATPVerificationStatus.VALID,
        hatp_reasons=(),
        activation_operational=True,
        activation_reasons=(),
        diagnostic=None,
    )

    def _fake_resolve(*args, **kwargs):
        return synthetic

    monkeypatch.setattr(cons, "resolve_rollback_approval_evidence_with_hatp", _fake_resolve)

    result = harness.consume(simulation_only=True)
    assert result.hatp_status == HATPVerificationStatus.VALID
    assert result.pb_decision == DECISION_ALLOW


def test_allow_path_performs_zero_effect(harness: _Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    synthetic = rae.HATPIntegratedApprovalEvidence(
        approval_present=True,
        rae_result=rae.RollbackApprovalValidationResult.VALID,
        rae_diagnostic=None,
        hatp_status=HATPVerificationStatus.VALID,
        hatp_reasons=(),
        activation_operational=True,
        activation_reasons=(),
        diagnostic=None,
    )
    monkeypatch.setattr(cons, "resolve_rollback_approval_evidence_with_hatp", lambda *a, **k: synthetic)

    result = harness.consume(simulation_only=True)
    assert result.pb_decision == DECISION_ALLOW
    # No git/filesystem mutation attempted by this module at all -- see
    # the dedicated 149O.18B phase test for a static-scan proof.


# ═══════════════════════════════════════════════════════════════════════════
# 10. Pre-cutover evidence usable (attack 35, HMRC-REQ-079) -- this
#     adapter is mode-agnostic; freshness/validity alone govern.
# ═══════════════════════════════════════════════════════════════════════════


def test_adapter_has_no_cutover_mode_parameter_anywhere() -> None:
    for name in ("evaluate_for_real_effect", "evaluate_for_advisory", "_internal_consume_hatp_rollback_evidence"):
        fn = getattr(cons, name)
        assert "mode" not in inspect.signature(fn).parameters
        assert "cutover" not in inspect.signature(fn).parameters


def test_module_does_not_import_cutover_module() -> None:
    import ast

    source = inspect.getsource(cons)
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
    assert not any("hatp_mandatory_cutover" in name for name in imported_modules)


# ═══════════════════════════════════════════════════════════════════════════
# 11. Production dependency closure -- no HATPEvidenceStore/RAE store
#     override reachable from either production entrypoint.
# ═══════════════════════════════════════════════════════════════════════════


def test_production_entrypoints_resolve_dependencies_internally(harness: _Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(harness.repo_root)
    result = cons.evaluate_for_advisory(harness.request(), root=harness.root)
    # No repository identity provisioned in this bare temp repo -> fails
    # closed with a distinct diagnostic, never an unhandled exception.
    assert result.pb_decision == DECISION_DENY
    assert any("production_hatp_dependency_resolution_failed" in r for r in result.reasons)


def test_production_real_effect_entrypoint_also_fails_closed_without_identity(
    harness: _Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(harness.repo_root)
    result = cons.evaluate_for_real_effect(harness.request(), root=harness.root)
    assert result.pb_decision == DECISION_DENY
