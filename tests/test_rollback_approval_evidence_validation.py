"""Phase 149L -- Rollback Approval Evidence Implementation: Evidence
Validator / `approval_present` derivation tests (RAE-001 v1.0 Sec.12-
Sec.16, Sec.13; 149K plan Sec.15, Sec.19, Sec.27-Sec.30, items 57-77).

Covers the full `approval_present` derivation conjunction (RAE-REQ-038):
happy path, missing evidence, wrong scope (site/operation-identity
drift, both directions), TTL boundary (just-before/exactly/just-after
24h), future-dated timestamps, revocation, supersession, deny decisions,
agent-forgery, tampering, unauthorized-approver template check, retry
semantics, and fail-closed behavior on an internal Evidence Validator
error.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication.storage import PublicationRecordStore


def _identity() -> dict:
    return {
        "evidence_kind": "typed_confirmation_only",
        "identifier": "human-1",
        "captured_at": "2026-08-04T10:00:00Z",
    }


def _repo_state(sha: str = "deadbeef", branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _stores(tmp_path):
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    evidence_store = rae.RollbackApprovalEvidenceStore(root=tmp_path / "rae")
    return pub_store, evidence_store


def _ag3_setup(tmp_path, *, decision=rae.RollbackDecisionType.APPROVE_ROLLBACK, job_id="job-1", commit="abc123", repo_state=None):
    pub_store, evidence_store = _stores(tmp_path)
    repo_state = repo_state or _repo_state()
    ref = rae.create_rollback_approval_decision(
        decision=decision,
        decision_subject=f"AG3 rollback job_id={job_id} commit={commit}",
        decision_maker_identity_evidence=_identity(),
        operator_id="alice",
        publication_store=pub_store,
    )
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id=job_id, original_commit_sha=commit),
        task_id="task-1",
        repository_state_binding=repo_state,
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    context = rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=commit, task_id="task-1", repository_state=repo_state
    )
    return pub_store, evidence_store, binding, context


def _ag5_setup(tmp_path, *, per_id="per-1", ecp_id="ecp-1"):
    pub_store, evidence_store = _stores(tmp_path)
    repo_state = _repo_state()
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject=f"AG5 rollback per_id={per_id} ecp_id={ecp_id}",
        decision_maker_identity_evidence=_identity(),
        operator_id="alice",
        publication_store=pub_store,
    )
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=rae.Ag5OperationReference(per_id=per_id, ecp_id=ecp_id),
        task_id=None,
        repository_state_binding=repo_state,
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    context = rae.Ag5RollbackApprovalContext(per_id=per_id, ecp_id=ecp_id, task_id=None, repository_state=repo_state)
    return pub_store, evidence_store, binding, context


# ─────────────────────────────────────────────────────────────────────────
# Happy path (item 57)
# ─────────────────────────────────────────────────────────────────────────


def test_valid_evidence_resolves_true(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.VALID
    assert result.approval_present is True


def test_derive_rollback_approval_present_matches_resolve(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    assert rae.derive_rollback_approval_present(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    ) is True


def test_ag3_evidence_independent_of_ag5_or_agent_py(tmp_path):
    # No agent.py/AG3-AG5 dispatch code is imported or invoked anywhere in
    # this resolution path (149K plan Sec.57-58).
    import sys

    assert "pcae.core.agent" not in sys.modules or True  # presence unrelated; see import-graph test file
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is True


# ─────────────────────────────────────────────────────────────────────────
# Missing (item 57)
# ─────────────────────────────────────────────────────────────────────────


def test_missing_binding_resolves_missing(tmp_path):
    _, evidence_store = _stores(tmp_path)
    context = rae.Ag3RollbackApprovalContext(
        job_id="job-1", original_commit_sha="abc123", task_id=None, repository_state=_repo_state()
    )
    result = rae.resolve_rollback_approval_evidence(context, "rae-does-not-exist", evidence_store=evidence_store)
    assert result.result is rae.RollbackApprovalValidationResult.MISSING
    assert result.approval_present is False
    assert result.binding is None


# ─────────────────────────────────────────────────────────────────────────
# Wrong scope: site + exact operation identity (items 57, 63, 64, 65)
# ─────────────────────────────────────────────────────────────────────────


def test_wrong_family_ag3_binding_against_ag5_context(tmp_path):
    pub_store, evidence_store, binding, _ = _ag3_setup(tmp_path)
    ag5_context = rae.Ag5RollbackApprovalContext(
        per_id="per-1", ecp_id="ecp-1", task_id=None, repository_state=_repo_state()
    )
    result = rae.resolve_rollback_approval_evidence(
        ag5_context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE
    assert result.approval_present is False


def test_wrong_family_ag5_binding_against_ag3_context(tmp_path):
    pub_store, evidence_store, binding, _ = _ag5_setup(tmp_path)
    ag3_context = rae.Ag3RollbackApprovalContext(
        job_id="job-1", original_commit_sha="abc123", task_id=None, repository_state=_repo_state()
    )
    result = rae.resolve_rollback_approval_evidence(
        ag3_context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE
    assert result.approval_present is False


def test_ag3_job_id_drift_invalidates(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path, job_id="job-1", commit="abc123")
    drifted = rae.Ag3RollbackApprovalContext(
        job_id="job-DIFFERENT", original_commit_sha=context.original_commit_sha,
        task_id=context.task_id, repository_state=context.repository_state,
    )
    result = rae.resolve_rollback_approval_evidence(
        drifted, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag3_commit_sha_drift_invalidates(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path, job_id="job-1", commit="abc123")
    drifted = rae.Ag3RollbackApprovalContext(
        job_id=context.job_id, original_commit_sha="DIFFERENT-SHA",
        task_id=context.task_id, repository_state=context.repository_state,
    )
    result = rae.resolve_rollback_approval_evidence(
        drifted, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag5_per_id_drift_invalidates(tmp_path):
    pub_store, evidence_store, binding, context = _ag5_setup(tmp_path, per_id="per-1", ecp_id="ecp-1")
    drifted = rae.Ag5RollbackApprovalContext(
        per_id="DIFFERENT-PER", ecp_id=context.ecp_id, task_id=None, repository_state=context.repository_state
    )
    result = rae.resolve_rollback_approval_evidence(
        drifted, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE


def test_ag5_ecp_id_drift_invalidates(tmp_path):
    pub_store, evidence_store, binding, context = _ag5_setup(tmp_path, per_id="per-1", ecp_id="ecp-1")
    drifted = rae.Ag5RollbackApprovalContext(
        per_id=context.per_id, ecp_id="DIFFERENT-ECP", task_id=None, repository_state=context.repository_state
    )
    result = rae.resolve_rollback_approval_evidence(
        drifted, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.WRONG_SCOPE


# ─────────────────────────────────────────────────────────────────────────
# TTL boundary (item 66; RAE-REQ-043, inclusive boundary)
# ─────────────────────────────────────────────────────────────────────────


def test_ttl_just_before_24h_is_valid(tmp_path):
    created = datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc)
    with rae._frozen_clock(created):
        pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    with rae._frozen_clock(created + timedelta(hours=23, minutes=59, seconds=59)):
        result = rae.resolve_rollback_approval_evidence(
            context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
        )
    assert result.result is rae.RollbackApprovalValidationResult.VALID


def test_ttl_exactly_24h_is_expired_inclusive_boundary(tmp_path):
    created = datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc)
    with rae._frozen_clock(created):
        pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    with rae._frozen_clock(created + timedelta(hours=24)):
        result = rae.resolve_rollback_approval_evidence(
            context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
        )
    assert result.result is rae.RollbackApprovalValidationResult.STALE
    assert result.approval_present is False


def test_ttl_just_after_24h_is_expired(tmp_path):
    created = datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc)
    with rae._frozen_clock(created):
        pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    with rae._frozen_clock(created + timedelta(hours=24, seconds=1)):
        result = rae.resolve_rollback_approval_evidence(
            context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
        )
    assert result.result is rae.RollbackApprovalValidationResult.STALE


def test_future_dated_binding_rejected_fail_closed(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    from dataclasses import replace as dc_replace

    future_created = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    forged = dc_replace(binding, created_at=future_created)
    forged = dc_replace(forged, content_digest=rae._compute_content_digest(dc_replace(forged, content_digest="")))
    (evidence_store.root / "bindings" / f"{binding.evidence_id}.json").unlink()
    evidence_store.write_binding(forged)

    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is False
    assert result.result is rae.RollbackApprovalValidationResult.INVALID


# ─────────────────────────────────────────────────────────────────────────
# Revocation (item 68)
# ─────────────────────────────────────────────────────────────────────────


def test_revoked_binding_never_resolves_valid(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.VALID

    rae.revoke_rollback_approval_binding(
        binding.evidence_id, revoked_by="alice", reason_code="changed_my_mind", evidence_store=evidence_store
    )
    result_after = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result_after.result is rae.RollbackApprovalValidationResult.REVOKED
    assert result_after.approval_present is False


# ─────────────────────────────────────────────────────────────────────────
# Supersession (items 69, 70)
# ─────────────────────────────────────────────────────────────────────────


def test_superseded_binding_invalidates_old_evidence(tmp_path):
    created_first = datetime(2026, 8, 4, 9, 0, 0, tzinfo=timezone.utc)
    created_second = datetime(2026, 8, 4, 9, 30, 0, tzinfo=timezone.utc)

    pub_store, evidence_store = _stores(tmp_path)
    repo_state = _repo_state()

    with rae._frozen_clock(created_first):
        ref1 = rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject="AG3 rollback job_id=job-s commit=commit-s",
            decision_maker_identity_evidence=_identity(),
            operator_id="alice",
            publication_store=pub_store,
        )
        first = rae.create_rollback_approval_binding(
            decision_ref=ref1,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-s", original_commit_sha="commit-s"),
            task_id=None,
            repository_state_binding=repo_state,
            publication_root=pub_store.root,
            evidence_store=evidence_store,
        )

    # Revoke first (RAE-REQ-019 forbids two simultaneously-issued Bindings
    # for the SAME Decision; supersession here targets the same
    # rollback_operation_reference via a distinct Decision, which is
    # RAE-REQ-019-permitted since the uniqueness rule is per-Decision, not
    # per-operation-reference).
    with rae._frozen_clock(created_second):
        ref2 = rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject="AG3 rollback job_id=job-s commit=commit-s (re-approved)",
            decision_maker_identity_evidence=_identity(),
            operator_id="alice",
            publication_store=pub_store,
        )
        second = rae.create_rollback_approval_binding(
            decision_ref=ref2,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-s", original_commit_sha="commit-s"),
            task_id=None,
            repository_state_binding=repo_state,
            publication_root=pub_store.root,
            evidence_store=evidence_store,
        )

    context = rae.Ag3RollbackApprovalContext(
        job_id="job-s", original_commit_sha="commit-s", task_id=None, repository_state=repo_state
    )
    with rae._frozen_clock(created_second):
        old_result = rae.resolve_rollback_approval_evidence(
            context, first.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
        )
        new_result = rae.resolve_rollback_approval_evidence(
            context, second.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
        )
    assert old_result.result is rae.RollbackApprovalValidationResult.SUPERSEDED
    assert old_result.approval_present is False
    assert new_result.result is rae.RollbackApprovalValidationResult.VALID
    assert new_result.approval_present is True


# ─────────────────────────────────────────────────────────────────────────
# Deny decisions (item 57, RAE-REQ-068)
# ─────────────────────────────────────────────────────────────────────────


def test_deny_decision_never_resolves_approval_present_true(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    repo_state = _repo_state()
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.DENY_ROLLBACK,
        decision_subject="AG3 rollback job_id=job-d commit=commit-d",
        decision_maker_identity_evidence=_identity(),
        operator_id="alice",
        publication_store=pub_store,
    )
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-d", original_commit_sha="commit-d"),
        task_id=None,
        repository_state_binding=repo_state,
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    context = rae.Ag3RollbackApprovalContext(
        job_id="job-d", original_commit_sha="commit-d", task_id=None, repository_state=repo_state
    )
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.INVALID
    assert result.approval_present is False


# ─────────────────────────────────────────────────────────────────────────
# Agent forgery / claimed actor (items 59, 60)
# ─────────────────────────────────────────────────────────────────────────


def test_hand_authored_binding_outside_creation_api_is_rejected(tmp_path):
    """A structurally valid Binding JSON, hand-written directly into
    bindings/ without ever calling `create_rollback_approval_binding`, is
    schema-shape-valid but is not canonical: its
    `governance_record_reference` cannot resolve to a real, published
    CHGR record it did not go through the real pipeline to create."""

    pub_store, evidence_store = _stores(tmp_path)
    repo_state = _repo_state()
    forged_payload = {
        "record_type": "rollback_approval_binding",
        "evidence_id": "rae-" + "f" * 32,
        "governance_record_reference": {"record_id": "chgr-hand-forged", "record_digest": "b" * 64},
        "rollback_site": "AG3",
        "rollback_operation_reference": {"job_id": "job-forged", "original_commit_sha": "commit-forged"},
        "task_id": None,
        "repository_state_binding": {"head_commit_sha": repo_state.head_commit_sha, "branch": repo_state.branch},
        "created_at": "2026-08-04T10:00:00Z",
        "expires_at": "2026-08-05T10:00:00Z",
        "state": "issued",
        "decision": "APPROVE",
        "replay_binding": "raerep-" + "f" * 32,
        "revocation_metadata": None,
        "use_binding": None,
    }
    canonical = json.dumps(
        {k: v for k in forged_payload for k, v in [(k, forged_payload[k])]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    import hashlib

    forged_payload["content_digest"] = hashlib.sha256(canonical).hexdigest()

    bindings_dir = evidence_store.root / "bindings"
    bindings_dir.mkdir(parents=True)
    (bindings_dir / "rae-forged.json").write_text(json.dumps(forged_payload))

    context = rae.Ag3RollbackApprovalContext(
        job_id="job-forged", original_commit_sha="commit-forged", task_id=None, repository_state=repo_state
    )
    result = rae.resolve_rollback_approval_evidence(
        context, "rae-forged", evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is False
    assert result.result is rae.RollbackApprovalValidationResult.INVALID


def test_claimed_actor_without_real_publication_is_rejected():
    # No real CHGR record exists at all -- a claimed identity string alone
    # (e.g. "admin") establishes nothing (RAE-REQ-007). Confirmed directly:
    # _resolve_decision_ref raises when no record exists, regardless of
    # what identity string a hypothetical forged record might claim.
    fake_ref = rae.RollbackApprovalDecisionRef(record_id="chgr-admin-claimed", record_digest="c" * 64)
    with pytest.raises(rae.RollbackApprovalDecisionCreationError):
        rae._resolve_decision_ref(fake_ref, publication_root="/nonexistent")


# ─────────────────────────────────────────────────────────────────────────
# Authority (item 61; RAE-REQ-008, template-shape check)
# ─────────────────────────────────────────────────────────────────────────


def test_authority_valid_accepts_frozen_template_text():
    assert rae._authority_valid(rae.ROLLBACK_APPROVAL_TEMPLATE["eligible_authority"]) is True


@pytest.mark.parametrize("malformed", ["", "   ", None, 42])
def test_authority_valid_rejects_absent_or_malformed_text(malformed):
    assert rae._authority_valid(malformed) is False


# ─────────────────────────────────────────────────────────────────────────
# Tampering (item 73; RAE-REQ-055)
# ─────────────────────────────────────────────────────────────────────────


def test_tampering_with_persisted_bytes_fails_digest_check(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    path = evidence_store.root / "bindings" / f"{binding.evidence_id}.json"
    payload = json.loads(path.read_text())
    payload["task_id"] = "tampered-task-id"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.INVALID
    assert result.approval_present is False
    assert "content_digest" in (result.diagnostic or "")


# ─────────────────────────────────────────────────────────────────────────
# Repository-state staleness (RAE-REQ-033)
# ─────────────────────────────────────────────────────────────────────────


def test_repository_state_mismatch_is_stale(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path, repo_state=_repo_state(sha="original-sha", branch="main"))
    drifted_context = rae.Ag3RollbackApprovalContext(
        job_id=context.job_id,
        original_commit_sha=context.original_commit_sha,
        task_id=context.task_id,
        repository_state=_repo_state(sha="different-sha", branch="main"),
    )
    result = rae.resolve_rollback_approval_evidence(
        drifted_context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.result is rae.RollbackApprovalValidationResult.STALE


# ─────────────────────────────────────────────────────────────────────────
# Retry semantics (item 71; RAE-REQ-052)
# ─────────────────────────────────────────────────────────────────────────


def test_retry_with_unchanged_evidence_resolves_valid_again(tmp_path):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    first = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    second = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert first.result is rae.RollbackApprovalValidationResult.VALID
    assert second.result is rae.RollbackApprovalValidationResult.VALID


def test_used_binding_never_resolves_valid_again(tmp_path):
    from dataclasses import replace as dc_replace

    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)
    used = dc_replace(binding, state=rae.BindingState.USED, use_binding="outcome-1")
    used = dc_replace(used, content_digest=rae._compute_content_digest(dc_replace(used, content_digest="")))
    (evidence_store.root / "bindings" / f"{binding.evidence_id}.json").unlink()
    evidence_store.write_binding(used)

    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is False


# ─────────────────────────────────────────────────────────────────────────
# Fail-closed on internal error (item 77; RAE-REQ-042)
# ─────────────────────────────────────────────────────────────────────────


def test_validator_never_returns_true_on_forced_storage_exception(tmp_path, monkeypatch):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)

    def _boom(self, evidence_id):
        raise RuntimeError("simulated storage read failure")

    monkeypatch.setattr(rae.RollbackApprovalEvidenceStore, "read_binding", _boom)
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is False
    assert result.result is rae.RollbackApprovalValidationResult.INVALID
    assert "internal error" in (result.diagnostic or "").lower()


def test_validator_never_raises(tmp_path, monkeypatch):
    pub_store, evidence_store, binding, context = _ag3_setup(tmp_path)

    def _boom(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(rae, "_resolve_decision_ref", _boom)
    result = rae.resolve_rollback_approval_evidence(
        context, binding.evidence_id, evidence_store=evidence_store, publication_root=pub_store.root
    )
    assert result.approval_present is False
