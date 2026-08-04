"""Phase 149L -- Rollback Approval Evidence Implementation: data model
tests (RAE-001 v1.0 Sec.7-Sec.11; 149K plan Sec.7-Sec.10, Sec.26).

Covers: the frozen `rollback-approval` Decision Template constant, the
closed `RollbackDecisionType`/`BindingDecision` vocabularies, the
`RollbackApprovalBinding` dataclass's conditional-field
(`revocation_metadata`/`use_binding`) and family-lock
(`rollback_operation_reference`) `__post_init__` invariants, and
`decision_maker_identity_evidence` passthrough via the real CHGR
publication pipeline (RAE-REQ-006).
"""
from __future__ import annotations

import pytest

from pcae.core import rollback_approval_evidence as rae


# ─────────────────────────────────────────────────────────────────────────
# Decision Template constant (RAE-REQ-011, RAE-REQ-012, RAE-REQ-013)
# ─────────────────────────────────────────────────────────────────────────


def test_template_id_and_version_frozen():
    assert rae.ROLLBACK_APPROVAL_TEMPLATE_ID == "rollback-approval"
    assert rae.ROLLBACK_APPROVAL_TEMPLATE["template_id"] == "rollback-approval"
    assert rae.ROLLBACK_APPROVAL_TEMPLATE["template_version"] == rae.ROLLBACK_APPROVAL_TEMPLATE_VERSION


def test_template_has_exactly_two_options():
    option_ids = [option["option_id"] for option in rae.ROLLBACK_APPROVAL_TEMPLATE["options"]]
    assert option_ids == ["approve_rollback", "deny_rollback"]


def test_template_eligible_authority_is_present_and_honest():
    text = rae.ROLLBACK_APPROVAL_TEMPLATE["eligible_authority"]
    assert isinstance(text, str) and text.strip()
    assert "no stronger authority-registry check exists today" in text.lower()


# ─────────────────────────────────────────────────────────────────────────
# Closed decision vocabulary (RAE-REQ-013, item 62)
# ─────────────────────────────────────────────────────────────────────────


def test_rollback_decision_type_closed_vocabulary():
    assert rae.RollbackDecisionType("approve_rollback") is rae.RollbackDecisionType.APPROVE_ROLLBACK
    assert rae.RollbackDecisionType("deny_rollback") is rae.RollbackDecisionType.DENY_ROLLBACK
    with pytest.raises(ValueError):
        rae.RollbackDecisionType("approve_everything")
    with pytest.raises(ValueError):
        rae.RollbackDecisionType("approved")


def test_binding_decision_vocabulary_distinct_from_selected_option_id():
    # RAE-001's own field table keeps these two vocabularies textually
    # distinct (149K plan Sec.10) -- APPROVE/DENY is never the same string
    # as approve_rollback/deny_rollback.
    assert {member.value for member in rae.BindingDecision} == {"APPROVE", "DENY"}
    assert {member.value for member in rae.RollbackDecisionType} == {"approve_rollback", "deny_rollback"}


def test_validation_result_vocabulary_is_exactly_rae_reqs_036_eight_values():
    assert {member.value for member in rae.RollbackApprovalValidationResult} == {
        "VALID",
        "MISSING",
        "INVALID",
        "STALE",
        "REVOKED",
        "UNAUTHORIZED_APPROVER",
        "WRONG_SCOPE",
        "SUPERSEDED",
    }


def test_validation_result_vocabulary_disjoint_from_broker_vocabulary():
    broker_vocabulary = {"ALLOW", "DENY", "HUMAN_REVIEW"}
    rae_vocabulary = {member.value for member in rae.RollbackApprovalValidationResult}
    assert not (broker_vocabulary & rae_vocabulary)


# ─────────────────────────────────────────────────────────────────────────
# Family-locked AG3/AG5 operation references (RAE-REQ-020/021/022)
# ─────────────────────────────────────────────────────────────────────────


def _repo_state() -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha="deadbeef", branch="main")


def _decision_ref() -> rae.RollbackApprovalDecisionRef:
    return rae.RollbackApprovalDecisionRef(record_id="chgr-fake", record_digest="a" * 64)


def _binding_kwargs(**overrides):
    kwargs = dict(
        evidence_id="rae-" + "0" * 32,
        governance_record_reference=_decision_ref(),
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(job_id="job-1", original_commit_sha="abc123"),
        task_id="task-1",
        repository_state_binding=_repo_state(),
        created_at="2026-08-04T10:00:00Z",
        expires_at="2026-08-05T10:00:00Z",
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.APPROVE,
        replay_binding="raerep-" + "0" * 32,
    )
    kwargs.update(overrides)
    return kwargs


def test_ag3_binding_constructs_with_ag3_operation_reference():
    binding = rae.RollbackApprovalBinding(**_binding_kwargs())
    assert isinstance(binding.rollback_operation_reference, rae.Ag3OperationReference)


def test_ag5_binding_constructs_with_ag5_operation_reference():
    binding = rae.RollbackApprovalBinding(
        **_binding_kwargs(
            rollback_site=rae.RollbackSite.AG5,
            rollback_operation_reference=rae.Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
        )
    )
    assert isinstance(binding.rollback_operation_reference, rae.Ag5OperationReference)


def test_ag3_site_rejects_ag5_operation_reference():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(
            **_binding_kwargs(
                rollback_site=rae.RollbackSite.AG3,
                rollback_operation_reference=rae.Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
            )
        )


def test_ag5_site_rejects_ag3_operation_reference():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(
            **_binding_kwargs(
                rollback_site=rae.RollbackSite.AG5,
                rollback_operation_reference=rae.Ag3OperationReference(job_id="job-1", original_commit_sha="abc123"),
            )
        )


def test_cross_family_reference_is_a_structurally_different_python_type():
    ag3_ref = rae.Ag3OperationReference(job_id="job-1", original_commit_sha="abc123")
    ag5_ref = rae.Ag5OperationReference(per_id="per-1", ecp_id="ecp-1")
    assert type(ag3_ref) is not type(ag5_ref)
    with pytest.raises(AttributeError):
        ag5_ref.job_id  # type: ignore[attr-defined]


# ─────────────────────────────────────────────────────────────────────────
# Conditional fields (RAE-REQ-017's revocation_metadata/use_binding rows)
# ─────────────────────────────────────────────────────────────────────────


def test_revoked_state_requires_revocation_metadata():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(**_binding_kwargs(state=rae.BindingState.REVOKED))


def test_revocation_metadata_forbidden_unless_revoked():
    metadata = rae.RevocationMetadata(revoked_at="2026-08-04T11:00:00Z", revoked_by="alice", reason_code="mistake")
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(**_binding_kwargs(revocation_metadata=metadata))


def test_revoked_state_with_metadata_constructs():
    metadata = rae.RevocationMetadata(revoked_at="2026-08-04T11:00:00Z", revoked_by="alice", reason_code="mistake")
    binding = rae.RollbackApprovalBinding(
        **_binding_kwargs(state=rae.BindingState.REVOKED, revocation_metadata=metadata)
    )
    assert binding.revocation_metadata is metadata


def test_used_state_requires_use_binding():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(**_binding_kwargs(state=rae.BindingState.USED))


def test_use_binding_forbidden_unless_used():
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.RollbackApprovalBinding(**_binding_kwargs(use_binding="outcome-1"))


def test_used_state_with_use_binding_constructs():
    binding = rae.RollbackApprovalBinding(
        **_binding_kwargs(state=rae.BindingState.USED, use_binding="outcome-1")
    )
    assert binding.use_binding == "outcome-1"


def test_binding_is_frozen():
    binding = rae.RollbackApprovalBinding(**_binding_kwargs())
    with pytest.raises(Exception):
        binding.evidence_id = "rae-other"  # type: ignore[misc]


# ─────────────────────────────────────────────────────────────────────────
# Canonical creation + decision_maker_identity_evidence passthrough
# (RAE-REQ-006, RAE-REQ-030, RAE-REQ-026/027)
# ─────────────────────────────────────────────────────────────────────────


def _publication_store(tmp_path):
    from pcae.governance.publication.storage import PublicationRecordStore

    return PublicationRecordStore(root=tmp_path / "pub-exec")


def test_create_rollback_approval_decision_publishes_a_real_chgr_record(tmp_path):
    store = _publication_store(tmp_path)
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="AG3 rollback job_id=job-1 commit=abc123",
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": "2026-08-04T10:00:00Z",
        },
        operator_id="alice",
        publication_store=store,
    )
    assert ref.record_id.startswith("chgr-")
    record_path = store.root / "records" / f"{ref.record_id}.json"
    assert record_path.exists()
    import json

    record = json.loads(record_path.read_text())
    assert record["template_ref"] == {
        "template_id": "rollback-approval",
        "version": rae.ROLLBACK_APPROVAL_TEMPLATE_VERSION,
    }
    assert record["selected_option_id"] == "approve_rollback"
    assert record["lifecycle_state"] == "published"
    assert record["record_digest"] == ref.record_digest


def test_create_rollback_approval_decision_rejects_non_enum_decision(tmp_path):
    store = _publication_store(tmp_path)
    with pytest.raises(rae.RollbackApprovalDecisionCreationError):
        rae.create_rollback_approval_decision(
            decision="approve_everything",  # type: ignore[arg-type]
            decision_subject="subject",
            decision_maker_identity_evidence={
                "evidence_kind": "typed_confirmation_only",
                "identifier": "human-1",
                "captured_at": "2026-08-04T10:00:00Z",
            },
            operator_id="alice",
            publication_store=store,
        )


def test_binding_creation_captures_task_id_from_caller(tmp_path):
    store = _publication_store(tmp_path)
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="AG5 rollback per_id=per-1 ecp_id=ecp-1",
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": "2026-08-04T10:00:00Z",
        },
        operator_id="alice",
        publication_store=store,
    )
    evidence_store = rae.RollbackApprovalEvidenceStore(root=tmp_path / "rae")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=rae.Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
        task_id="task-42",
        repository_state_binding=_repo_state(),
        publication_root=store.root,
        evidence_store=evidence_store,
    )
    assert binding.task_id == "task-42"

    binding_no_task = rae.create_rollback_approval_binding(
        decision_ref=rae.create_rollback_approval_decision(
            decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
            decision_subject="AG5 rollback per_id=per-2 ecp_id=ecp-2",
            decision_maker_identity_evidence={
                "evidence_kind": "typed_confirmation_only",
                "identifier": "human-1",
                "captured_at": "2026-08-04T10:00:00Z",
            },
            operator_id="alice",
            publication_store=store,
        ),
        rollback_site=rae.RollbackSite.AG5,
        rollback_operation_reference=rae.Ag5OperationReference(per_id="per-2", ecp_id="ecp-2"),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=store.root,
        evidence_store=evidence_store,
    )
    assert binding_no_task.task_id is None


def test_ttl_hours_is_not_caller_overridable(tmp_path):
    store = _publication_store(tmp_path)
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="AG3 rollback job_id=job-9 commit=abc999",
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": "2026-08-04T10:00:00Z",
        },
        operator_id="alice",
        publication_store=store,
    )
    evidence_store = rae.RollbackApprovalEvidenceStore(root=tmp_path / "rae")
    with pytest.raises(rae.RollbackApprovalBindingConstructionError):
        rae.create_rollback_approval_binding(
            decision_ref=ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=rae.Ag3OperationReference(job_id="job-9", original_commit_sha="abc999"),
            task_id=None,
            repository_state_binding=_repo_state(),
            ttl_hours=48,  # type: ignore[arg-type]
            publication_root=store.root,
            evidence_store=evidence_store,
        )
