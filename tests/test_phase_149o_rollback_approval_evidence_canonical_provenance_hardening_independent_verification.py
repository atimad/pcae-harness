"""Phase 149O -- Rollback Approval Evidence Canonical-Provenance Hardening
Independent Verification.

Independently constructed: no fixtures or helpers are imported from
`tests/test_rollback_approval_evidence_*.py` (149L),
`tests/test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`
(149M), or
`tests/test_phase_149n_rollback_approval_evidence_canonical_provenance_hardening.py`
(149N). Re-derives its own fixture helpers from the production source and
the RAE-001 contract only.

This suite reconstructs the original four 149M BLOCKING findings (now
closed by 149N) as positive-closure tests, and goes one layer further per
the governing 149O phase prompt's "Critical New Adversarial Question":
can an attacker manufacture the *new* provenance objects 149N introduced
(the CHGR publication receipt marker, and the Binding canonical-creation
registration) using the same class of direct-filesystem-write capability
149M/149N already treat as in-scope?

Tests that encode a required security property and are expected to PASS
against a correctly-hardened implementation, but instead FAIL (via
`pytest.fail("BLOCKING ...")`) because the exploit succeeds, are
intentional, repo-conventional (see 149M's own suite) documented evidence
of a BLOCKING finding -- not a defect in this test file.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication.storage import PublicationRecordStore


# ═══════════════════════════════════════════════════════════════════════════
# Independently authored fixture helpers
# ═══════════════════════════════════════════════════════════════════════════


def _repo_state(sha: str = "a" * 40, branch: str = "main") -> rae.RepositoryStateBinding:
    return rae.RepositoryStateBinding(head_commit_sha=sha, branch=branch)


def _ag3_ref(job_id: str = "job-149o", sha: str = "b" * 40) -> rae.Ag3OperationReference:
    return rae.Ag3OperationReference(job_id=job_id, original_commit_sha=sha)


def _ag3_ctx(job_id: str = "job-149o", sha: str = "b" * 40, repo=None) -> rae.Ag3RollbackApprovalContext:
    return rae.Ag3RollbackApprovalContext(
        job_id=job_id, original_commit_sha=sha, task_id=None, repository_state=repo or _repo_state()
    )


def _genuine_decision(
    pub_root: Path,
    decision: rae.RollbackDecisionType = rae.RollbackDecisionType.APPROVE_ROLLBACK,
    subject: str = "job-149o|" + "b" * 40,
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


def _genuine_binding(
    pub_root: Path,
    evidence_root: Path,
    decision_ref: rae.RollbackApprovalDecisionRef = None,
    op_ref: rae.Ag3OperationReference = None,
) -> tuple:
    if decision_ref is None:
        decision_ref = _genuine_decision(pub_root)
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


def _hand_author_chgr_record(pub_root: Path, *, record_id: str = None, digest: str = None) -> tuple:
    """Fully hand-authored CHGR record -- no PublicationCoordinator call."""
    record_id = record_id or ("fake-record-" + uuid.uuid4().hex)
    records_dir = pub_root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    body = {
        "record_id": record_id,
        "template_ref": {"template_id": "rollback-approval", "version": "1.0"},
        "selected_option_id": "approve_rollback",
        "lifecycle_state": "published",
        "decision_subject": "job-149o|" + "b" * 40,
    }
    body["record_digest"] = digest or hashlib.sha256(
        json.dumps({k: v for k, v in body.items() if k != "record_digest"}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    (records_dir / f"{record_id}.json").write_text(json.dumps(body, indent=2, sort_keys=True))
    return record_id, body["record_digest"]


def _hand_author_publication_receipt(pub_root: Path, *, record_id: str, package_id: str = None) -> Path:
    """Fully hand-authored publication idempotency marker -- no
    PublicationCoordinator/PublicationRecordStore.commit_publication call."""
    package_id = package_id or ("fake-pkg-" + uuid.uuid4().hex)
    published_dir = pub_root / "published"
    published_dir.mkdir(parents=True, exist_ok=True)
    marker = {"record_id": record_id, "package_id": package_id}
    path = published_dir / f"{package_id}.json"
    path.write_text(json.dumps(marker, indent=2, sort_keys=True))
    return path


def _hand_author_binding(
    evidence_root: Path,
    *,
    evidence_id: str,
    decision_ref: rae.RollbackApprovalDecisionRef,
    op_ref: rae.Ag3OperationReference,
    created_at: str = None,
) -> rae.RollbackApprovalBinding:
    now = datetime.now(timezone.utc)
    binding = rae.RollbackApprovalBinding(
        evidence_id=evidence_id,
        governance_record_reference=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=op_ref,
        task_id=None,
        repository_state_binding=_repo_state(),
        created_at=created_at or rae.chgr_timestamp(now.isoformat()),
        expires_at=rae.chgr_timestamp((now + timedelta(hours=24)).isoformat()),
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.APPROVE,
        replay_binding="raerep-" + uuid.uuid4().hex,
    )
    binding = replace(binding, content_digest=rae._compute_content_digest(binding))
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    store.write_binding(binding)
    return binding


def _hand_author_registration(evidence_root: Path, binding: rae.RollbackApprovalBinding, *, key: str = None) -> Path:
    """Fully hand-authored canonical creation registration -- no
    RollbackApprovalEvidenceStore.write_creation_registration call."""
    key = key or binding.evidence_id
    payload = rae._registration_to_dict(binding)
    payload["evidence_id"] = key
    path = evidence_root / "creation-registry" / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


@pytest.fixture
def pub_root(tmp_path: Path) -> Path:
    return tmp_path / "publication-execution"


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    return tmp_path / "rollback-approval-evidence"


# ═══════════════════════════════════════════════════════════════════════════
# Part 1 -- independent reconstruction of the original four 149M findings
# (now expected CLOSED)
# ═══════════════════════════════════════════════════════════════════════════


def test_149o_b1_hand_authored_binding_referencing_genuine_decision_rejected(pub_root, evidence_root):
    decision_ref = _genuine_decision(pub_root)
    evidence_id = f"rae-{uuid.uuid4().hex}"
    _hand_author_binding(evidence_root, evidence_id=evidence_id, decision_ref=decision_ref, op_ref=_ag3_ref())
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_149o_b2_hand_authored_chgr_record_no_receipt_rejected(pub_root, evidence_root):
    record_id, digest = _hand_author_chgr_record(pub_root)
    decision_ref = rae.RollbackApprovalDecisionRef(record_id=record_id, record_digest=digest)
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root, decision_ref=decision_ref)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_149o_b3_copied_binding_new_filename_rejected(pub_root, evidence_root):
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    original_path = store._binding_path(binding.evidence_id)
    new_id = f"rae-{uuid.uuid4().hex}"
    copy_path = store._binding_path(new_id)
    copy_path.write_text(original_path.read_text())
    result_new = rae.resolve_rollback_approval_evidence(_ag3_ctx(), new_id, evidence_store=store, publication_root=pub_root)
    result_orig = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result_new.approval_present is False
    assert result_orig.approval_present is True


def test_149o_b4_forged_newer_noncanonical_binding_cannot_supersede(pub_root, evidence_root):
    decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    future = rae.chgr_timestamp((datetime.now(timezone.utc) + timedelta(days=365)).isoformat())
    forged_id = f"rae-{uuid.uuid4().hex}"
    _hand_author_binding(
        evidence_root, evidence_id=forged_id, decision_ref=decision_ref, op_ref=_ag3_ref(), created_at=future
    )
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is True
    assert result.result == rae.RollbackApprovalValidationResult.VALID


# ═══════════════════════════════════════════════════════════════════════════
# Part 2 -- CRITICAL NEW ADVERSARIAL QUESTION: forging the new provenance
# objects themselves. Both mandatory attacks and both succeed against the
# current implementation -- documented as BLOCKING findings.
# ═══════════════════════════════════════════════════════════════════════════


def test_149o_fake_chgr_record_plus_fake_publication_receipt(pub_root, evidence_root):
    """CRITICAL TEST. Hand-author BOTH a fake CHGR record AND a matching
    fake publication idempotency-marker receipt (no PublicationCoordinator
    call anywhere), then create the Binding through the REAL
    create_rollback_approval_binding API. If this resolves
    approval_present=True, the CHGR-side hardening's trust root has merely
    relocated to another equally-forgeable file."""
    record_id, digest = _hand_author_chgr_record(pub_root)
    _hand_author_publication_receipt(pub_root, record_id=record_id)
    decision_ref = rae.RollbackApprovalDecisionRef(record_id=record_id, record_digest=digest)

    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    binding = rae.create_rollback_approval_binding(
        decision_ref=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=_ag3_ref(),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    print(f"[149O finding] fake CHGR record + fake receipt -> {result.result}, approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING: a fully hand-authored CHGR record paired with a fully hand-authored "
            "publication idempotency-marker receipt (published/<package_id>.json) -- neither "
            "ever produced by PublicationCoordinator.execute/PublicationRecordStore.commit_publication "
            "-- was accepted by _chgr_record_has_publication_receipt and resolved "
            "approval_present=True. The Phase 149N CHGR-side hardening's trust root is not "
            "anchored to anything a direct-filesystem-write attacker cannot also produce: it "
            "merely relocated the forgery target from records/<id>.json to a second, equally "
            "unauthenticated file, published/<package_id>.json, that need only structurally "
            "agree with the first. B-149M-2's root cause persists one layer outward."
        )


def test_149o_fake_binding_plus_fake_creation_registration(pub_root, evidence_root):
    """CRITICAL TEST. Publish a genuine Decision, then hand-author BOTH a
    fake Binding AND a matching fake canonical creation registration (no
    create_rollback_approval_binding call). If this resolves
    approval_present=True, the Binding-side hardening's trust root has
    merely relocated to another equally-forgeable file."""
    decision_ref = _genuine_decision(pub_root)
    evidence_id = f"rae-{uuid.uuid4().hex}"
    binding = _hand_author_binding(evidence_root, evidence_id=evidence_id, decision_ref=decision_ref, op_ref=_ag3_ref())
    _hand_author_registration(evidence_root, binding)

    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root)
    print(f"[149O finding] fake Binding + fake registration -> {result.result}, approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING: a fully hand-authored Binding paired with a fully hand-authored canonical "
            "creation registration (creation-registry/<evidence_id>.json) -- never produced by "
            "create_rollback_approval_binding -- was accepted by _binding_is_canonically_created "
            "and resolved approval_present=True. The Phase 149N Binding-side hardening's trust "
            "root is not anchored to anything a direct-filesystem-write attacker cannot also "
            "produce: it merely relocated the forgery target from bindings/<id>.json to a second, "
            "equally unauthenticated file that need only structurally agree with the first, self-"
            "computed digest included. B-149M-1's root cause persists one layer outward."
        )


def test_149o_full_end_to_end_forgery_zero_legitimate_api_calls(pub_root, evidence_root):
    """CRITICAL TEST. The strongest form: EVERY artifact (CHGR record,
    publication receipt, Binding, creation registration) is hand-authored.
    Zero calls to create_rollback_approval_decision or
    create_rollback_approval_binding anywhere in this test. If this
    resolves approval_present=True, an attacker with filesystem write
    access equivalent to 149M's original threat model can manufacture a
    fully trusted rollback approval without ever touching the real CHGR
    Confirmation->Publication pipeline or the real Binding creation API."""
    record_id, digest = _hand_author_chgr_record(pub_root)
    _hand_author_publication_receipt(pub_root, record_id=record_id)
    decision_ref = rae.RollbackApprovalDecisionRef(record_id=record_id, record_digest=digest)

    evidence_id = f"rae-{uuid.uuid4().hex}"
    binding = _hand_author_binding(evidence_root, evidence_id=evidence_id, decision_ref=decision_ref, op_ref=_ag3_ref())
    _hand_author_registration(evidence_root, binding)

    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), evidence_id, evidence_store=store, publication_root=pub_root)
    print(f"[149O finding] full end-to-end forgery -> {result.result}, approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING: full end-to-end forgery -- every artifact hand-authored, zero calls to "
            "create_rollback_approval_decision or create_rollback_approval_binding -- resolved "
            "approval_present=True. The trust chain terminates only in more writable, self-"
            "describing files, not in an independently governed canonical creation fact."
        )


def test_149o_real_chgr_record_forged_publication_receipt(pub_root, evidence_root):
    """Attack #25 variant: a GENUINE CHGR record's record_id claimed by a
    hand-authored receipt for a DIFFERENT, fake record. Must not let the
    fake record borrow the genuine record's... no -- this constructs the
    inverse: real record_id, but the receipt itself is still hand-authored
    rather than PublicationCoordinator-produced, isolating whether receipt
    *authorship* (not just content agreement) is checked at all."""
    decision_ref = _genuine_decision(pub_root)
    # Remove no real marker; instead simulate an attacker who additionally
    # hand-authors a SECOND marker for the same genuine record_id (e.g. to
    # confirm hand-authored markers for real record_ids are equally
    # accepted, not just for fake ones -- receipt authorship is unchecked
    # either way).
    _hand_author_publication_receipt(pub_root, record_id=decision_ref.record_id, package_id="attacker-pkg-" + uuid.uuid4().hex)
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root, decision_ref=decision_ref)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    # This one is expected VALID regardless (a genuine record with a
    # genuine coordinator-written marker already resolves VALID); recorded
    # as supporting evidence that receipt authorship is never distinguished
    # from receipt content, not as an independent blocking finding.
    assert result.approval_present is True


def test_149o_copied_registration_under_new_key_with_matching_fields_rejected(pub_root, evidence_root):
    """Copy a legitimate registration's content under a new key/evidence_id
    combination, self-consistent with a hand-authored Binding at that new
    key. This is the registration-side analogue of B-149M-3 and should be
    rejected the same way a copied Binding is -- but only if it does not
    ALSO succeed as fresh forgery (see the fake+fake tests above, which
    already show it succeeds)."""
    decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    new_id = f"rae-{uuid.uuid4().hex}"
    forged = _hand_author_binding(evidence_root, evidence_id=new_id, decision_ref=decision_ref, op_ref=_ag3_ref(sha="c" * 40))
    _hand_author_registration(evidence_root, forged, key=new_id)
    result = rae.resolve_rollback_approval_evidence(
        _ag3_ctx(sha="c" * 40), new_id, evidence_store=store, publication_root=pub_root
    )
    print(f"[149O finding] copied/forged registration under new key -> {result.result}, approval_present={result.approval_present}")
    if result.approval_present is True:
        pytest.fail(
            "BLOCKING: a hand-authored Binding at a new evidence_id, paired with a hand-authored "
            "registration whose fields are self-consistent with it, resolved approval_present=True. "
            "Registration-key binding does not defend against fresh forgery of the (key, "
            "registration) pair -- only against reusing an existing registration under a "
            "mismatched key."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Part 3 -- provenance mismatch / missing-provenance negative controls
# (expected CLOSED: these must remain INVALID)
# ═══════════════════════════════════════════════════════════════════════════


def test_149o_registration_missing_genuine_binding_file_copied_without_registration(pub_root, evidence_root):
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    reg_path = evidence_root / "creation-registry" / f"{binding.evidence_id}.json"
    assert reg_path.exists()
    reg_path.unlink()
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_149o_orphan_registration_without_binding_is_not_valid_evidence(pub_root, evidence_root):
    decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    orphan_id = f"rae-{uuid.uuid4().hex}"
    _hand_author_registration(evidence_root, binding, key=orphan_id)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), orphan_id, evidence_store=store, publication_root=pub_root)
    assert result.result == rae.RollbackApprovalValidationResult.MISSING
    assert result.approval_present is False


def test_149o_registration_mismatch_wrong_digest_rejected(pub_root, evidence_root):
    decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    reg_path = evidence_root / "creation-registry" / f"{binding.evidence_id}.json"
    payload = json.loads(reg_path.read_text())
    payload["binding_content_digest"] = "0" * 64
    reg_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is False
    assert result.result == rae.RollbackApprovalValidationResult.INVALID


def test_149o_atomic_creation_registration_failure_rolls_back_binding(pub_root, evidence_root, monkeypatch):
    decision_ref = _genuine_decision(pub_root)
    store = rae.RollbackApprovalEvidenceStore(root=evidence_root)

    def _boom(self, binding):
        raise OSError("simulated durable-write failure")

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
    assert list((evidence_root / "bindings").glob("*.json")) == []


def test_149o_forged_later_denial_cannot_invalidate_canonical_approval(pub_root, evidence_root):
    decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    future = rae.chgr_timestamp((datetime.now(timezone.utc) + timedelta(days=1)).isoformat())
    forged_id = f"rae-{uuid.uuid4().hex}"
    forged = rae.RollbackApprovalBinding(
        evidence_id=forged_id,
        governance_record_reference=decision_ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=_ag3_ref(),
        task_id=None,
        repository_state_binding=_repo_state(),
        created_at=future,
        expires_at=rae.chgr_timestamp((datetime.now(timezone.utc) + timedelta(days=2)).isoformat()),
        state=rae.BindingState.ISSUED,
        decision=rae.BindingDecision.DENY,
        replay_binding="raerep-" + uuid.uuid4().hex,
    )
    forged = replace(forged, content_digest=rae._compute_content_digest(forged))
    rae.RollbackApprovalEvidenceStore(root=evidence_root).write_binding(forged)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is True
    assert result.result == rae.RollbackApprovalValidationResult.VALID


def test_149o_invalid_newer_candidate_does_not_suppress_older_valid_one(pub_root, evidence_root):
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    bindings_dir = evidence_root / "bindings"
    (bindings_dir / "garbage.json").write_text("{not valid json")
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.approval_present is True


def test_149o_canonical_positive_control_still_valid(pub_root, evidence_root):
    _decision_ref, binding, store = _genuine_binding(pub_root, evidence_root)
    result = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result.result == rae.RollbackApprovalValidationResult.VALID
    assert result.approval_present is True


def test_149o_canonical_supersession_still_works(pub_root, evidence_root):
    decision_ref, binding1, store = _genuine_binding(pub_root, evidence_root)
    decision_ref2 = _genuine_decision(pub_root, subject="job-149o|" + "b" * 40)
    binding2 = rae.create_rollback_approval_binding(
        decision_ref=decision_ref2,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=_ag3_ref(),
        task_id=None,
        repository_state_binding=_repo_state(),
        publication_root=pub_root,
        evidence_store=store,
    )
    result1 = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding1.evidence_id, evidence_store=store, publication_root=pub_root)
    result2 = rae.resolve_rollback_approval_evidence(_ag3_ctx(), binding2.evidence_id, evidence_store=store, publication_root=pub_root)
    assert result1.result == rae.RollbackApprovalValidationResult.SUPERSEDED
    assert result2.approval_present is True
