"""Phase 149L -- Rollback Approval Evidence Implementation: persistence
tests (RAE-001 v1.0 Sec.8, Sec.12-Sec.17; 149K plan Sec.12-Sec.14,
Sec.19, Sec.24).

Covers: canonical, non-arbitrary storage layout; atomic-write
immutability (no overwrite of an existing evidence_id); the
at-most-one-active-Binding-per-Decision rule (RAE-REQ-019); and
resolver-visible lookup ordering (never mtime/"latest").
"""
from __future__ import annotations

import json

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication.storage import PublicationRecordStore


def _repo_state(sha: str = "deadbeef", branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _identity() -> dict:
    return {
        "evidence_kind": "typed_confirmation_only",
        "identifier": "human-1",
        "captured_at": "2026-08-04T10:00:00Z",
    }


def _publish_decision(pub_store: PublicationRecordStore, subject: str, decision=rae.RollbackDecisionType.APPROVE_ROLLBACK):
    return rae.create_rollback_approval_decision(
        decision=decision,
        decision_subject=subject,
        decision_maker_identity_evidence=_identity(),
        operator_id="alice",
        publication_store=pub_store,
    )


def _stores(tmp_path):
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    evidence_store = rae.RollbackApprovalEvidenceStore(root=tmp_path / "rae")
    return pub_store, evidence_store


# ─────────────────────────────────────────────────────────────────────────
# Canonical storage layout (RAE-REQ-056)
# ─────────────────────────────────────────────────────────────────────────


def test_store_writes_under_bindings_subdirectory(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-1 commit=abc123")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-1", original_commit_sha="abc123"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    expected_path = evidence_store.root / "bindings" / f"{binding.evidence_id}.json"
    assert expected_path.exists()
    assert binding.evidence_id.startswith("rae-")


def test_round_trip_through_storage_is_unchanged(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-2 commit=abc456")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-2", original_commit_sha="abc456"),
        task_id="task-1",
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    reloaded = evidence_store.read_binding(binding.evidence_id)
    assert reloaded == binding


def test_read_binding_returns_none_for_missing_evidence_id(tmp_path):
    _, evidence_store = _stores(tmp_path)
    assert evidence_store.read_binding("rae-does-not-exist") is None


# ─────────────────────────────────────────────────────────────────────────
# Atomic write / immutability (RAE-REQ-057, item 72)
# ─────────────────────────────────────────────────────────────────────────


def test_write_binding_refuses_to_overwrite_existing_evidence_id(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-3 commit=abc789")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-3", original_commit_sha="abc789"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    with pytest.raises(rae.RollbackApprovalStorageError):
        evidence_store.write_binding(binding)


def test_no_partial_file_visible_at_final_path_on_write_failure(tmp_path, monkeypatch):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-4 commit=abcaaa")

    real_replace = __import__("os").replace

    def _boom(*args, **kwargs):
        raise OSError("simulated interruption before os.replace")

    monkeypatch.setattr(rae.os, "replace", _boom)
    with pytest.raises(rae.RollbackApprovalStorageError):
        rae.create_rollback_approval_binding(
            decision_ref=ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-4", original_commit_sha="abcaaa"),
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=pub_store.root,
            evidence_store=evidence_store,
        )
    monkeypatch.setattr(rae.os, "replace", real_replace)
    assert list((evidence_store.root / "bindings").glob("*.json")) == []


def test_revocation_record_is_append_only_not_an_in_place_edit(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-5 commit=abcbbb")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-5", original_commit_sha="abcbbb"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    original_bytes = (evidence_store.root / "bindings" / f"{binding.evidence_id}.json").read_bytes()
    rae.revoke_rollback_approval_binding(
        binding.evidence_id, revoked_by="alice", reason_code="changed_my_mind", evidence_store=evidence_store
    )
    assert (evidence_store.root / "bindings" / f"{binding.evidence_id}.json").read_bytes() == original_bytes
    assert evidence_store.is_revoked(binding.evidence_id)
    revocation = evidence_store.read_revocation(binding.evidence_id)
    assert revocation.revoked_by == "alice"
    assert revocation.reason_code == "changed_my_mind"


def test_revoking_twice_is_rejected(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-6 commit=abcccc")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-6", original_commit_sha="abcccc"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    rae.revoke_rollback_approval_binding(binding.evidence_id, revoked_by="alice", reason_code="r1", evidence_store=evidence_store)
    with pytest.raises(rae.RollbackApprovalStorageError):
        rae.revoke_rollback_approval_binding(binding.evidence_id, revoked_by="alice", reason_code="r2", evidence_store=evidence_store)


# ─────────────────────────────────────────────────────────────────────────
# At-most-one-active-Binding-per-Decision (RAE-REQ-019)
# ─────────────────────────────────────────────────────────────────────────


def test_second_issued_binding_for_same_decision_is_rejected(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(pub_store, "AG3 rollback job_id=job-7 commit=abcddd")
    rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-7", original_commit_sha="abcddd"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.create_rollback_approval_binding(
            decision_ref=ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-7", original_commit_sha="abcddd"),
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=pub_store.root,
            evidence_store=evidence_store,
        )


def test_deny_decision_binding_permitted_for_audit(tmp_path):
    pub_store, evidence_store = _stores(tmp_path)
    ref = _publish_decision(
        pub_store, "AG3 rollback job_id=job-8 commit=abceee", decision=rae.RollbackDecisionType.DENY_ROLLBACK
    )
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-8", original_commit_sha="abceee"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    assert binding.decision is rae.BindingDecision.DENY


def test_orphan_binding_rejected_when_decision_does_not_resolve(tmp_path):
    _, evidence_store = _stores(tmp_path)
    fake_ref = rae.RollbackApprovalDecisionRef(record_id="chgr-does-not-exist", record_digest="a" * 64)
    with pytest.raises(rae.RollbackApprovalDecisionCreationError):
        rae.create_rollback_approval_binding(
            decision_ref=fake_ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-x", original_commit_sha="abcfff"),
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=tmp_path / "pub-exec",
            evidence_store=evidence_store,
        )


# ─────────────────────────────────────────────────────────────────────────
# list_bindings ordering discipline (RAE-REQ-041 restated at storage layer)
# ─────────────────────────────────────────────────────────────────────────


def test_list_bindings_source_never_uses_mtime_or_sorted_latest_heuristic():
    import inspect

    source = inspect.getsource(rae.RollbackApprovalEvidenceStore.list_bindings)
    assert "mtime" not in source
    assert "st_mtime" not in source
    assert "[-1]" not in source
