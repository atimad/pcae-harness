"""Adversarial tests for `runtime_invocation_authority_consumption.py` —
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import json

import pytest

from pcae.core.hpac_foundation import HPACDuplicateError, canonical_digest
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumption,
    RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
    RuntimeInvocationAuthorityConsumptionStore,
    new_inert_consumption_record,
)


def _record(**overrides) -> RuntimeInvocationAuthorityConsumption:
    kwargs = dict(
        request_identity={"invocation_id": "inv-1", "attempt_id": "att-1", "idempotency_key": "idem-1"},
        repository_task_binding={
            "repository_identity": "repo-1",
            "head_commit": "a" * 40,
            "task_id": "task-1",
            "task_contract_digest": "b" * 64,
            "phase_id": "phase-1",
            "session_id": None,
        },
        target_binding={
            "runtime_target_id": "target-1",
            "adapter_id": "adapter-1",
            "descriptor_version": "v1",
            "descriptor_digest": "c" * 64,
            "target_config_digest": "d" * 64,
            "executable_identity_digest": "e" * 64,
        },
        prompt_binding={"prompt_hash": "f" * 64, "prompt_hash_profile": "pcae.prompt-semantic.v1"},
        authority_binding={
            "approval_id": "ria-" + "1" * 32,
            "approval_digest": "g" * 64,
            "authority_projection_id": "proj-1",
            "authority_projection_digest": "h" * 64,
            "authority_contract_version": "RIHAC-001/2.0",
            "proof_id": "hap-" + "1" * 32,
            "proof_digest": "i" * 64,
            "proof_validation_digest": "j" * 64,
            "registry_state_digest": "k" * 64,
            "approval_subject_digest": "l" * 64,
            "trusted_presentation_ref": {"presentation_id": "hpe-" + "1" * 32, "presentation_digest": "m" * 64},
            "challenge_digest": "n" * 64,
        },
        pb_binding={
            "request_digest": "o" * 64,
            "decision_digest": "p" * 64,
            "decision": "ALLOW",
            "policy_version": "v1",
            "causing_policy_ids": [],
            "matched_no_go_ids": [],
        },
        runtime_enforcement_binding={
            "decision_id": "dec-1",
            "decision_digest": "q" * 64,
            "verdict": "ALLOW",
            "expires_at": "2026-08-28T00:10:00Z",
            "evaluated_input_digest": "r" * 64,
        },
        dispatch_binding={
            "containment_evidence_ref": {"id": "cont-1", "digest": "s" * 64},
            "state": "dispatch_attempted",
            "consumed_at": "2026-08-28T00:00:00Z",
        },
    )
    kwargs.update(overrides)
    return new_inert_consumption_record(**kwargs)


def test_valid_record_creates_and_resolves(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    record = _record()
    store.create("hap-" + "1" * 32, record)
    resolved = store.resolve("hap-" + "1" * 32)
    assert resolved == record


def test_no_record_means_not_consumed(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    assert store.resolve("hap-" + "2" * 32) is None


def test_duplicate_gate9_two_racing_creates_produce_exactly_one_winner(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    record = _record()
    store.create("hap-" + "1" * 32, record)
    with pytest.raises(HPACDuplicateError):
        store.create("hap-" + "1" * 32, record)


def test_partial_corrupt_record_is_durability_uncertain_not_consumed_or_unconsumed(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    record = _record()
    store.create("hap-" + "1" * 32, record)
    path = store._path("hap-" + "1" * 32)
    original = path.read_text(encoding="utf-8")
    path.write_text(original[: len(original) // 2], encoding="utf-8")
    with pytest.raises(RuntimeInvocationAuthorityConsumptionDurabilityUncertainError):
        store.resolve("hap-" + "1" * 32)


def test_missing_binding_field_rejected():
    with pytest.raises(Exception):
        new_inert_consumption_record(
            request_identity={"invocation_id": "i"},  # missing attempt_id/idempotency_key
            repository_task_binding={},
            target_binding={},
            prompt_binding={},
            authority_binding={},
            pb_binding={},
            runtime_enforcement_binding={},
            dispatch_binding={},
        )


def test_conflicting_digest_tamper_detected(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    record = _record()
    store.create("hap-" + "1" * 32, record)
    path = store._path("hap-" + "1" * 32)
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["record_digest"] = "0" * 64
    path.unlink()
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(RuntimeInvocationAuthorityConsumptionDurabilityUncertainError):
        store.resolve("hap-" + "1" * 32)


def test_record_digest_mismatch_rejected_at_create(tmp_path):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    record = _record()
    import dataclasses

    forged = dataclasses.replace(record, record_digest="0" * 64)
    with pytest.raises(Exception):
        store.create("hap-" + "9" * 32, forged)
