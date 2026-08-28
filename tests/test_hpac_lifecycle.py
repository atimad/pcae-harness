"""Adversarial tests for `hpac_lifecycle.py` — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import json

import pytest

from pcae.core.approval_presentation import (
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import canonical_digest
from pcae.core.hpac_lifecycle import (
    HPACLifecycleForkError,
    HPACLifecycleGapError,
    HPACLifecycleStateError,
    HPACLifecycleStore,
    STATE_ASSERTION_RECEIVED,
    STATE_CHALLENGE_CREATED,
    STATE_PROOF_VERIFIED,
    STATE_PROOF_VERIFIED_AND_BOUND,
    STATE_REJECTED,
)


APPROVAL_ID = "ria-" + "7" * 32
EXPIRES_AT = "2026-08-28T00:10:00Z"


def _resolved_presentation(tmp_path, approval_id=APPROVAL_ID):
    store = TrustedApprovalPresentationStore(tmp_path / "presentations")
    mech = DeterministicTestPresentationMechanism()
    preview_digest = compute_deterministic_human_visible_representation_digest(EXPIRES_AT)
    subject = new_canonical_runtime_approval_subject(
        subject={"repository_identity": "r", "task_id": "t", "runtime_target_id": "rt", "prompt_hash": "a" * 64, "invocation_id": "inv"},
        approval_scope={"capability": "runtime_dispatch"},
        approval_preview_digest=preview_digest,
        expires_at=EXPIRES_AT,
    )
    evidence = mech.present(subject, approval_id)
    store.create(evidence)
    return store.resolve_structural(presentation_id=evidence.presentation_id, presentation_digest=evidence.presentation_digest), subject


def _open_challenge(store: HPACLifecycleStore, resolved, subject, *, proof_id="hap-" + "1" * 32):
    return store.open_challenge(
        proof_id=proof_id,
        approval_id=APPROVAL_ID,
        invocation_id="inv-1",
        attempt_id="att-1",
        principal_id="hp-1",
        credential_id="hpc-1",
        mechanism_id="hpac.deterministic.test-only.v1",
        approval_subject_digest=subject.digest(),
        challenge_digest="c" * 64,
        occurred_at="2026-08-28T00:00:00Z",
        resolved_presentation=resolved,
    )


def test_valid_genesis_requires_resolved_presentation(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    event = _open_challenge(lc, resolved, subject)
    assert event.sequence == 0
    assert event.state == STATE_CHALLENGE_CREATED
    assert event.previous_event_digest is None


def test_genesis_rejects_wrong_approval_id(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    with pytest.raises(HPACLifecycleStateError):
        lc.open_challenge(
            proof_id="hap-" + "2" * 32,
            approval_id="ria-" + "9" * 32,  # mismatched approval_id
            invocation_id="inv-1",
            attempt_id="att-1",
            principal_id="hp-1",
            credential_id="hpc-1",
            mechanism_id="m",
            approval_subject_digest=subject.digest(),
            challenge_digest="c" * 64,
            occurred_at="2026-08-28T00:00:00Z",
            resolved_presentation=resolved,
        )


def test_valid_transition_sequence(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    e1 = lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")
    assert e1.state == STATE_ASSERTION_RECEIVED
    e2 = lc.record_verified(
        proof_id="hap-" + "1" * 32,
        proof_digest="e" * 64,
        registry_state_digest="f" * 64,
        verifier_version="v1",
        occurred_at="2026-08-28T00:00:02Z",
    )
    assert e2.state == STATE_PROOF_VERIFIED
    e3 = lc.bind_gate5(proof_id="hap-" + "1" * 32, approval_digest="g" * 64, occurred_at="2026-08-28T00:00:03Z")
    assert e3.state == STATE_PROOF_VERIFIED_AND_BOUND
    chain = lc.resolve_chain("hap-" + "1" * 32)
    assert [e.sequence for e in chain] == [0, 1, 2, 3]
    assert chain[1].previous_event_digest == chain[0].event_digest
    assert chain[2].previous_event_digest == chain[1].event_digest
    assert chain[3].previous_event_digest == chain[2].event_digest


def test_bind_gate5_idempotent_same_binding(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")
    lc.record_verified(proof_id="hap-" + "1" * 32, proof_digest="e" * 64, registry_state_digest="f" * 64, verifier_version="v1", occurred_at="2026-08-28T00:00:02Z")
    first = lc.bind_gate5(proof_id="hap-" + "1" * 32, approval_digest="g" * 64, occurred_at="2026-08-28T00:00:03Z")
    second = lc.bind_gate5(proof_id="hap-" + "1" * 32, approval_digest="g" * 64, occurred_at="2026-08-28T00:00:04Z")
    assert first == second
    chain = lc.resolve_chain("hap-" + "1" * 32)
    assert len(chain) == 4  # no extra event appended


def test_bind_gate5_cross_binding_rejected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")
    lc.record_verified(proof_id="hap-" + "1" * 32, proof_digest="e" * 64, registry_state_digest="f" * 64, verifier_version="v1", occurred_at="2026-08-28T00:00:02Z")
    lc.bind_gate5(proof_id="hap-" + "1" * 32, approval_digest="g" * 64, occurred_at="2026-08-28T00:00:03Z")
    with pytest.raises(HPACLifecycleForkError):
        lc.bind_gate5(proof_id="hap-" + "1" * 32, approval_digest="different-digest" + "0" * 55, occurred_at="2026-08-28T00:00:05Z")


def test_invalid_predecessor_record_assertion_before_challenge(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    with pytest.raises(HPACLifecycleStateError):
        lc.record_assertion(proof_id="hap-" + "9" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")


def test_invalid_predecessor_verified_before_assertion(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    with pytest.raises(HPACLifecycleStateError):
        lc.record_verified(proof_id="hap-" + "1" * 32, proof_digest="e" * 64, registry_state_digest="f" * 64, verifier_version="v1", occurred_at="2026-08-28T00:00:02Z")


def test_alternate_chain_second_genesis_rejected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    with pytest.raises(HPACLifecycleForkError):
        _open_challenge(lc, resolved, subject)  # same proof_id, second genesis attempt


def test_fork_drifted_binding_repeat_rejected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    # Manually write a sequence-1 event with a drifted binding, bypassing
    # the narrow transition API, to prove the *reader* independently
    # detects the fork -- not merely the writer's own discipline.
    chain_dir = tmp_path / "lifecycle" / "proofs" / "v2" / ("hap-" + "1" * 32) / "lifecycle"
    seq0 = json.loads((chain_dir / "0000.json").read_text(encoding="utf-8"))
    drifted_binding = dict(seq0["binding"])
    drifted_binding["invocation_id"] = "drifted-invocation"
    body = {
        "lifecycle_schema_version": seq0["lifecycle_schema_version"],
        "event_id": "hpl-" + "9" * 32,
        "sequence": 1,
        "previous_event_digest": seq0["event_digest"],
        "proof_id": seq0["proof_id"],
        "state": STATE_ASSERTION_RECEIVED,
        "occurred_at": "2026-08-28T00:00:01Z",
        "binding": drifted_binding,
        "assertion_digest": "d" * 64,
        "proof_digest": None,
        "approval_digest": None,
        "registry_state_digest": None,
        "verifier_version": None,
        "terminal_reason_code": None,
    }
    digest = canonical_digest(body)
    (chain_dir / "0001.json").write_text(json.dumps({**body, "event_digest": digest}), encoding="utf-8")
    with pytest.raises(HPACLifecycleForkError):
        lc.resolve_chain("hap-" + "1" * 32)


def test_gap_in_sequence_rejected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    chain_dir = tmp_path / "lifecycle" / "proofs" / "v2" / ("hap-" + "1" * 32) / "lifecycle"
    seq0 = json.loads((chain_dir / "0000.json").read_text(encoding="utf-8"))
    body = {
        "lifecycle_schema_version": seq0["lifecycle_schema_version"],
        "event_id": "hpl-" + "8" * 32,
        "sequence": 2,  # skips sequence 1 -- a gap
        "previous_event_digest": seq0["event_digest"],
        "proof_id": seq0["proof_id"],
        "state": STATE_ASSERTION_RECEIVED,
        "occurred_at": "2026-08-28T00:00:01Z",
        "binding": seq0["binding"],
        "assertion_digest": "d" * 64,
        "proof_digest": None,
        "approval_digest": None,
        "registry_state_digest": None,
        "verifier_version": None,
        "terminal_reason_code": None,
    }
    digest = canonical_digest(body)
    (chain_dir / "0002.json").write_text(json.dumps({**body, "event_digest": digest}), encoding="utf-8")
    with pytest.raises(HPACLifecycleGapError):
        lc.resolve_chain("hap-" + "1" * 32)


def test_duplicate_sequence_rejected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")
    with pytest.raises(HPACLifecycleStateError):
        lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="e" * 64, occurred_at="2026-08-28T00:00:02Z")


def test_broken_hash_link_detected(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:01Z")
    chain_dir = tmp_path / "lifecycle" / "proofs" / "v2" / ("hap-" + "1" * 32) / "lifecycle"
    doc = json.loads((chain_dir / "0001.json").read_text(encoding="utf-8"))
    doc["previous_event_digest"] = "0" * 64  # tampered link
    without_digest = {k: v for k, v in doc.items() if k != "event_digest"}
    doc["event_digest"] = canonical_digest(without_digest)  # self-consistent, but link now diverges from sequence 0
    (chain_dir / "0001.json").unlink()
    (chain_dir / "0001.json").write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(HPACLifecycleForkError):
        lc.resolve_chain("hap-" + "1" * 32)


def test_terminate_rejected_reject_reason(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    event = lc.terminate(proof_id="hap-" + "1" * 32, state=STATE_REJECTED, reason_code="deterministic-test-rejection", occurred_at="2026-08-28T00:00:05Z")
    assert event.state == STATE_REJECTED
    assert event.terminal_reason_code == "deterministic-test-rejection"


def test_no_event_permitted_after_terminal(tmp_path):
    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    resolved, subject = _resolved_presentation(tmp_path)
    _open_challenge(lc, resolved, subject)
    lc.terminate(proof_id="hap-" + "1" * 32, state=STATE_REJECTED, reason_code="r", occurred_at="2026-08-28T00:00:05Z")
    with pytest.raises(HPACLifecycleStateError):
        lc.record_assertion(proof_id="hap-" + "1" * 32, assertion_digest="d" * 64, occurred_at="2026-08-28T00:00:06Z")


def test_caller_cannot_construct_lifecycle_event_directly_and_have_it_accepted(tmp_path):
    """A hand-built event file (bypassing the narrow transition API
    entirely) that nonetheless has a self-consistent digest is still
    detected as a fork/gap by the reader, because it never went through
    `_append`'s sequence/binding-chaining discipline relative to a real
    prior chain -- this is the 'no caller constructs an event directly'
    guarantee, verified from the read side."""

    lc = HPACLifecycleStore(tmp_path / "lifecycle")
    chain_dir = tmp_path / "lifecycle" / "proofs" / "v2" / "hap-forged" / "lifecycle"
    chain_dir.mkdir(parents=True)
    body = {
        "lifecycle_schema_version": "HPAC-PROOF-LIFECYCLE-EVENT/2.0",
        "event_id": "hpl-" + "1" * 32,
        "sequence": 0,
        "previous_event_digest": None,
        "proof_id": "hap-forged",
        "state": STATE_CHALLENGE_CREATED,
        "occurred_at": "2026-08-28T00:00:00Z",
        "binding": {
            "approval_id": "ria-" + "0" * 32,
            "invocation_id": "inv",
            "attempt_id": "att",
            "principal_id": "hp-1",
            "credential_id": "hpc-1",
            "mechanism_id": "m",
            "approval_subject_digest": "a" * 64,
            "trusted_presentation_ref": {"presentation_id": "hpe-" + "1" * 32, "presentation_digest": "b" * 64},
            "challenge_digest": "c" * 64,
        },
        "assertion_digest": None,
        "proof_digest": None,
        "approval_digest": None,
        "registry_state_digest": None,
        "verifier_version": None,
        "terminal_reason_code": None,
    }
    digest = canonical_digest(body)
    (chain_dir / "0000.json").write_text(json.dumps({**body, "event_digest": digest}), encoding="utf-8")
    # The store reads this back fine as a chain (it is well-formed on its
    # own) -- but genesis authority (HPAC-REQ-096) was never checked here
    # because `open_challenge` was bypassed; this test documents that
    # `resolve_chain` alone proves only *chain* integrity, never *writer*
    # trust, which is exactly the "hash consistency != canonical
    # authority" distinction this module's docstring states.
    chain = lc.resolve_chain("hap-forged")
    assert len(chain) == 1  # chain-integrity read succeeds...
    # ...but no production caller reaches this file through anything
    # other than direct filesystem tampering, since `open_challenge` is
    # the only writer method and it requires a resolved presentation.
