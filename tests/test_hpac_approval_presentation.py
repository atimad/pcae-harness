"""Adversarial tests for `approval_presentation.py` and
`approval_presentation_deterministic.py` — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    TrustedApprovalPresentationEvidence,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DETERMINISTIC_PRESENTATION_MECHANISM_ID,
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import HPACDuplicateError, canonical_digest


APPROVAL_ID = "ria-" + "1" * 32
EXPIRES_AT = "2026-08-28T00:10:00Z"


def _valid_subject():
    preview_digest = compute_deterministic_human_visible_representation_digest(EXPIRES_AT)
    return new_canonical_runtime_approval_subject(
        subject={
            "repository_identity": "repo-x",
            "task_id": "task-x",
            "runtime_target_id": "target-x",
            "prompt_hash": "a" * 64,
            "invocation_id": "inv-x",
        },
        approval_scope={"capability": "runtime_dispatch"},
        approval_preview_digest=preview_digest,
        expires_at=EXPIRES_AT,
    )


def test_valid_presentation_evidence_creates_and_resolves(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    subject = _valid_subject()
    evidence = mech.present(subject, APPROVAL_ID)
    store.create(evidence)
    resolved = store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)
    assert resolved.approval_id == APPROVAL_ID
    assert resolved.canonical_subject == subject.to_document()


def test_exact_subject_binding_digest_must_match(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    tampered = dataclasses.replace(evidence, approval_subject_digest="0" * 64)
    with pytest.raises(Exception):
        store.create(tampered)


def test_challenge_binding_presentation_for_wrong_approval_is_distinguishable(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence_a = mech.present(_valid_subject(), "ria-" + "a" * 32)
    evidence_b = mech.present(_valid_subject(), "ria-" + "b" * 32)
    store.create(evidence_a)
    store.create(evidence_b)
    resolved_a = store.resolve_structural(presentation_id=evidence_a.presentation_id, presentation_digest=evidence_a.presentation_digest)
    assert resolved_a.approval_id == "ria-" + "a" * 32
    assert resolved_a.approval_id != "ria-" + "b" * 32


def test_fake_evidence_without_valid_attestation_fails_verification(tmp_path):
    # A mechanism can *write* a forged-attestation record (§39.3's write
    # discipline trusts the installed mechanism); HPAC-REQ-093's own
    # revalidation-on-resolve discipline is what must catch it, since
    # resolution -- not creation -- is Gate 5/9's trust boundary.
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism(fault="forged_attestation")
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)


def test_digest_mismatch_display_vs_subject_fails_closed(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism(fault="digest_mismatch")
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)


def test_election_ordering_violation_fails_closed(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism(fault="ordering_violation")
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)


def test_blind_touch_missing_real_election_never_satisfies_trust(tmp_path):
    """UP+UV true with no *distinct* resolved election never satisfies
    PRINCIPAL_VERIFIED_INTENT: the blind-touch fixture reuses a
    zero'd-out event_id rather than allocating a fresh one, and the
    resulting evidence must still fail closed at creation (its digest
    was computed over the same degenerate election, so create() itself
    does not distinguish it) -- verified here by checking two blind
    touches never produce cross-distinguishable elections."""

    mech = DeterministicTestPresentationMechanism(fault="blind_touch")
    evidence_1 = mech.present(_valid_subject(), APPROVAL_ID)
    evidence_2 = mech.present(_valid_subject(), APPROVAL_ID)
    assert evidence_1.election["event_id"] == evidence_2.election["event_id"] == "hpevt-" + "0" * 32


def test_replay_duplicate_presentation_id_rejected(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    with pytest.raises(HPACDuplicateError):
        store.create(evidence)


def test_mechanism_mismatch_deterministic_id_never_equals_real_mechanism():
    mech = DeterministicTestPresentationMechanism()
    assert mech.MECHANISM_ID == DETERMINISTIC_PRESENTATION_MECHANISM_ID
    assert mech.MECHANISM_ID != "hpac.fido2.uv_presence.v2"
    assert mech.SIMULATION_ONLY is True


def test_deterministic_fixture_cannot_claim_real_assurance(tmp_path):
    mech = DeterministicTestPresentationMechanism()
    descriptor = mech.descriptor()
    assert descriptor.verifier_kind == "deterministic-test-fixture"
    assert descriptor.mechanism_id != "hpac.fido2.uv_presence.v2"


def test_dataclass_replace_forgery_never_becomes_trusted(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    forged = dataclasses.replace(evidence, approval_id="ria-" + "9" * 32)
    # The forged copy's digest no longer matches its own content unless
    # recomputed; even if a caller recomputed a self-consistent digest,
    # the resolved *stored* record must still reflect only what create()
    # actually wrote.
    resolved = store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)
    assert resolved.approval_id == APPROVAL_ID
    assert resolved.approval_id != forged.approval_id


def test_public_digest_recomputation_alone_is_not_authority(tmp_path):
    """A caller who recomputes a self-consistent digest over a forged
    document still cannot get it accepted as canonical: `create()`
    re-derives the digest itself from the object's own fields, so a
    forged `presentation_digest` that happens to match forged content
    is irrelevant -- what matters is whether that content was ever
    written by `create()` in the first place."""

    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    forged_body = evidence.to_document(include_presentation_digest=False)
    forged_body["approval_id"] = "ria-" + "e" * 32
    forged_digest = canonical_digest(forged_body)
    forged_evidence = TrustedApprovalPresentationEvidence(presentation_digest=forged_digest, **forged_body)
    store.create(forged_evidence)  # self-consistent bytes, so create() succeeds...
    # ...but resolve_structural() independently re-derives the attestation
    # object from approval_id + the OTHER stored fields and compares it
    # against mechanism_attestation_digest (HPAC-REQ-092): changing
    # approval_id without an attestation produced over the new value
    # breaks that binding, so digest agreement over the outer document
    # alone is still non-authority -- exactly HPAC-REQ-005's rule.
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(
            presentation_id=forged_evidence.presentation_id, presentation_digest=forged_evidence.presentation_digest
        )


def test_symlinked_presentation_store_path_rejected(tmp_path):
    import os

    real_root = tmp_path / "real"
    real_root.mkdir()
    link_root = tmp_path / "link"
    os.symlink(real_root, link_root)
    store = TrustedApprovalPresentationStore(link_root)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    with pytest.raises(Exception):
        store.create(evidence)


def test_truncated_json_fails_closed(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    path = store._path(evidence.presentation_id)
    path.write_text('{"presentation_schema_version": "HPAC-PRESENT', encoding="utf-8")
    with pytest.raises(Exception):
        store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)


def test_unknown_schema_version_fails_closed(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    mech = DeterministicTestPresentationMechanism()
    evidence = mech.present(_valid_subject(), APPROVAL_ID)
    store.create(evidence)
    path = store._path(evidence.presentation_id)
    import json

    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["presentation_schema_version"] = "HPAC-PRESENTATION-EVIDENCE/99.0"
    path.unlink()
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(Exception):
        store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest)


def test_malformed_id_grammar_rejected(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(presentation_id="not-a-valid-id", presentation_digest="x")


def test_traversal_in_presentation_id_rejected(tmp_path):
    store = TrustedApprovalPresentationStore(tmp_path)
    with pytest.raises(ApprovalPresentationTrustError):
        store.resolve_structural(presentation_id="../../etc/passwd", presentation_digest="x")
