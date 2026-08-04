"""Phase 149N -- Rollback Approval Evidence Canonical-Provenance Hardening.

Dedicated hardening test suite closing the four BLOCKING findings recorded
by Phase 149M's independent verification
(`docs/PHASE_149M_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_INDEPENDENT_VERIFICATION.md`):

- B-149M-1 -- hand-authored Binding referencing a genuine Decision.
- B-149M-2 -- hand-authored CHGR record accepted as canonical.
- B-149M-3 -- copied Binding accepted under a new evidence_id.
- B-149M-4 -- forged-later-timestamp Binding superseding legitimate evidence.

Independently constructed: no fixtures or helpers are imported from
`tests/test_rollback_approval_evidence_*.py` (149L) or
`tests/test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`
(149M's own suite, re-run unmodified elsewhere and expected to now pass in
full). Every negative (attack) test is paired with a positive (canonical)
control per the governing phase prompt's item 79.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication.storage import PublicationRecordStore


# ═══════════════════════════════════════════════════════════════════════════
# Fixture helpers (independently written for this suite)
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state(sha: str = "c" * 40, branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _ag3_ref(job_id: str = "job-149n", sha: str = "d" * 40) -> rae.Ag3OperationReference:
    return rae.Ag3OperationReference(job_id=job_id, original_commit_sha=sha)


def _ag3_ctx(job_id: str = "job-149n", sha: str = "d" * 40, repo=None) -> rae.Ag3RollbackApprovalContext:
    return rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=sha, task_id=None, repository_state=repo or _repo_state()
    )


def _make_decision(
    pub_root: Path,
    decision: rae.RollbackDecisionType = rae.RollbackDecisionType.APPROVE_ROLLBACK,
    subject: str = "job-149n|" + "d" * 40,
) -> rae.RollbackApprovalDecisionRef:
    store = PublicationRecordStore(root=pub_root)
    return rae.create_rollback_approval_decision(
        decision=decision,
        decision_subject=subject,
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "local-operator",
            "captured_at": "2026-08-04T10:00:00Z",
        },
        operator_id="local-operator",
        publication_store=store,
    )


def _make_binding(
    pub_root: Path,
    evidence_root: Path,
    decision_ref: rae.RollbackApprovalDecisionRef = None,
    op_ref: rae.Ag3OperationReference = None,
) -> tuple:
    if decision_ref is None:
        decision_ref = _make_decision(pub_root)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=op_ref or _ag3_ref(),
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
# B-149M-1 -- hand-authored Binding referencing a genuine Decision
# ═══════════════════════════════════════════════════════════════════════════


def test_149n_b1_hand_authored_binding_rejected(pub_root, evidence_root):
    """A hand-authored Binding file, referencing a genuine published
    Decision but never created through `create_rollback_approval_binding`,
    has no canonical creation registration and MUST NOT resolve VALID,
    even with an arbitrary/mismatched operation reference removed (i.e.
    even in the *best case* for the attacker, where every other field is
    a faithful, correctly-computed copy)."""

    decision_ref = _make_decision(pub_root)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)

    evidence_id = f"rae-{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    binding = rae.RollbackApprovalBinding(
        evidence_id=evidence_id,
        governance_record_reference=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=_ag3_ref(),
        task_id=None,
        repository_state_binding=_repo_state(),
        created_at=now.isoformat(),
        expires_at=(now + timedelta(hours=24)).isoformat(),
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.APPROVE,
        replay_binding=f"raerep-{uuid.uuid4().hex}",
    )
    from dataclasses import replace as _replace

    binding = _replace(binding, content_digest=rae._compute_content_digest(binding))
    store.write_binding(binding)  # direct filesystem write, bypassing create_rollback_approval_binding

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result != rae.RollbackApprovalValidationResult.VALID


def test_149n_b1_positive_control_canonical_binding_still_valid(pub_root, evidence_root):
    """Pairing control for B1: a Binding created through the real
    `create_rollback_approval_binding` API against a genuine Decision
    still resolves VALID after hardening."""

    _decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is True
    assert result.result == rae.RollbackApprovalValidationResult.VALID


# ═══════════════════════════════════════════════════════════════════════════
# B-149M-2 -- hand-authored CHGR record accepted as canonical
# ═══════════════════════════════════════════════════════════════════════════


def test_149n_b2_hand_authored_chgr_record_rejected(pub_root, evidence_root):
    """A fully hand-authored CHGR-record-shaped file, written directly to
    `<publication_root>/records/<record_id>.json` (never through
    `PublicationCoordinator`), has no matching `published/<package_id>.json`
    idempotency-marker receipt naming its record_id, and a Binding
    referencing it (even one legitimately created through
    `create_rollback_approval_binding`, since that call itself no longer
    depends on the receipt check) MUST NOT resolve VALID."""

    pub_root.mkdir(parents=True, exist_ok=True)
    records_dir = pub_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    record_id = "chgr-" + uuid.uuid4().hex
    body = {
        "record_id": record_id,
        "template_ref": {"template_id": "rollback-approval", "version": "1.0"},
        "selected_option_id": "approve_rollback",
        "lifecycle_state": "published",
        "decision_subject": "job-149n|" + "d" * 40,
    }
    digest = hashlib.sha256(
        json.dumps({k: v for k, v in body.items() if k != "record_digest"}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    body["record_digest"] = digest
    (records_dir / f"{record_id}.json").write_text(json.dumps(body, indent=2, sort_keys=True))

    decision_ref = rae.RollbackApprovalDecisionRef(record_id=record_id, record_digest=digest)
    _decision_ref, binding, store = _make_binding(pub_root, evidence_root, decision_ref=decision_ref)

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_149n_b2_positive_control_genuine_chgr_pipeline_still_validates(pub_root, evidence_root):
    """Pairing control for B2: a Decision produced through the real,
    unmodified CHGR Confirmation->Publication pipeline still validates
    (the hardening must not make canonical evidence itself unresolvable)."""

    _decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is True


# ═══════════════════════════════════════════════════════════════════════════
# B-149M-3 -- copied Binding accepted under a new evidence_id
# ═══════════════════════════════════════════════════════════════════════════


def test_149n_b3_copied_binding_new_id_rejected(pub_root, evidence_root):
    """A verbatim byte-for-byte copy of a legitimate Binding's serialized
    content, placed under a brand-new evidence_id filename (its internal
    `evidence_id` field left untouched), MUST NOT resolve VALID under the
    new filename -- closing the "one underlying record presented under an
    unbounded number of distinct evidence_ids" attack."""

    _decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    original_path = store._binding_path(binding.evidence_id)  # test-internal introspection only
    new_evidence_id = f"rae-{uuid.uuid4().hex}"
    new_path = store._binding_path(new_evidence_id)
    new_path.write_text(original_path.read_text(encoding="utf-8"))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), new_evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID

    # The original evidence_id must remain unaffected and still valid.
    original_result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert original_result.approval_present is True


def test_149n_b3_same_id_content_replacement_rejected(pub_root, evidence_root):
    """Item 57: modifying a genuine Binding's content (operation
    reference) and recomputing a self-consistent digest under the SAME
    evidence_id must still fail -- content-tampering was already caught
    pre-149N (RAE-REQ-055) but is re-confirmed here alongside the
    canonicality hardening to guard against regression."""

    _decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    from dataclasses import replace as _replace

    tampered = _replace(binding, rollback_operation_reference=_ag3_ref(job_id="job-attacker"))
    tampered = _replace(tampered, content_digest=rae._compute_content_digest(tampered))
    path = store._binding_path(binding.evidence_id)
    path.write_text(json.dumps(rae._binding_to_dict(tampered, include_digest=True), indent=2, sort_keys=True))

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is False


# ═══════════════════════════════════════════════════════════════════════════
# B-149M-4 -- forged-later-timestamp Binding superseding legitimate evidence
# ═══════════════════════════════════════════════════════════════════════════


def test_149n_b4_noncanonical_newer_binding_cannot_supersede(pub_root, evidence_root):
    """A hand-authored Binding file, written directly into the canonical
    bindings/ directory, referencing the same Decision and operation
    reference as a legitimate, still-fresh Binding but carrying a forged
    `created_at` one hour later, MUST NOT cause the legitimate Binding to
    resolve SUPERSEDED."""

    decision_ref = _make_decision(pub_root)
    _decision_ref, legitimate, store = _make_binding(pub_root, evidence_root, decision_ref=decision_ref)

    from dataclasses import replace as _replace

    forged_created_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    forged = _replace(
        legitimate,
        evidence_id=f"rae-{uuid.uuid4().hex}",
        created_at=forged_created_at,
        replay_binding=f"raerep-{uuid.uuid4().hex}",
    )
    forged = _replace(forged, content_digest=rae._compute_content_digest(forged))
    store.write_binding(forged)  # direct write -- no canonical creation registration

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), legitimate.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is True
    assert result.result == rae.RollbackApprovalValidationResult.VALID

    forged_result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), forged.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert forged_result.approval_present is False


def test_149n_b4_positive_control_legitimate_later_binding_still_supersedes(pub_root, evidence_root):
    """Pairing control for B4: a genuinely later Binding, created through
    the real API for the same operation reference, still correctly
    supersedes the earlier one (the hardening must not break legitimate
    supersession)."""

    decision_ref = _make_decision(pub_root)
    op_ref = _ag3_ref()
    _decision_ref, earlier, store = _make_binding(pub_root, evidence_root, decision_ref=decision_ref, op_ref=op_ref)

    later_decision_ref = _make_decision(pub_root, subject="job-149n|" + "e" * 40)
    later = rae.create_rollback_approval_binding(
        decision_ref=later_decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=op_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )

    earlier_result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), earlier.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert earlier_result.result == rae.RollbackApprovalValidationResult.SUPERSEDED

    later_result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), later.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert later_result.approval_present is True


# ═══════════════════════════════════════════════════════════════════════════
# Additional hardening controls (items 46, 51, 34-38)
# ═══════════════════════════════════════════════════════════════════════════


def test_149n_directory_injection_extra_file_ignored(pub_root, evidence_root):
    """Item 51: an arbitrary extra file dropped into the canonical
    bindings/ directory that is not valid Binding JSON at all must not be
    treated as a resolvable candidate, and must not crash resolution of
    unrelated, legitimate evidence."""

    _decision_ref, binding, store = _make_binding(pub_root, evidence_root)
    injected = store._binding_path("not-a-real-evidence-id")
    injected.write_text("{ not json")

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is True


def test_149n_atomic_creation_failure_leaves_no_orphan_binding(pub_root, evidence_root, monkeypatch):
    """Items 34-38: if canonical creation registration fails after the
    Binding file was written, the Binding MUST be rolled back -- no
    Binding file may exist on disk without a matching registration."""

    decision_ref = _make_decision(pub_root)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)

    def _boom(self, binding):
        raise OSError("simulated registration failure")

    monkeypatch.setattr(rae.RollbackApprovalEvidenceStore, "write_creation_registration", _boom)

    with pytest.raises(rae.RollbackApprovalStorageError):
        rae.create_rollback_approval_binding(
            decision_ref=decision_ref,
            rollback_site=rae.RollbackSite.AG3,
            rollback_operation_reference=_ag3_ref(),
            task_id=None,
            repository_state_binding=_repo_state(),
            publication_root=pub_root,
            evidence_store=store,
        )

    assert store.list_bindings() == []
    bindings_dir = evidence_root / "bindings"
    assert not bindings_dir.exists() or list(bindings_dir.glob("*.json")) == []


def test_149n_forged_deny_binding_cannot_invalidate_canonical_approval(pub_root, evidence_root):
    """Item 46: a forged (hand-authored, noncanonical) DENY binding for
    the same operation reference must not affect resolution of a
    legitimate, canonical APPROVE binding -- forged records are excluded
    from consideration entirely, not merely from supersession."""

    decision_ref = _make_decision(pub_root)
    op_ref = _ag3_ref()
    _decision_ref, approved, store = _make_binding(pub_root, evidence_root, decision_ref=decision_ref, op_ref=op_ref)

    deny_decision_ref = _make_decision(
        pub_root, decision=rae.RollbackDecisionType.DENY_ROLLBACK, subject="job-149n|" + "d" * 40 + "-deny"
    )
    from dataclasses import replace as _replace

    forged_deny = rae.RollbackApprovalBinding(
        evidence_id=f"rae-{uuid.uuid4().hex}",
        governance_record_reference=deny_decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=op_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        created_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.DENY,
        replay_binding=f"raerep-{uuid.uuid4().hex}",
    )
    forged_deny = _replace(forged_deny, content_digest=rae._compute_content_digest(forged_deny))
    store.write_binding(forged_deny)

    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(), approved.evidence_id, evidence_store=store, publication_root=pub_root
    )
    assert result.approval_present is True
    assert result.result == rae.RollbackApprovalValidationResult.VALID
