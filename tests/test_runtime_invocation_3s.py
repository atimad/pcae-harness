"""
Phase 149O.20L.7O.3S — RPAC-001 mock-v1 invocation data/lifecycle unit
tests: PromptArtifact, simulation approval binding, requests/envelopes,
canonical digests/IDs, the append-only simulation state log, and the
persistent `RuntimeInvocationStore` (replay, restart, collision).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core.runtime_invocation import (
    FAILURE_SIMULATION_AMBIGUOUS,
    MOCK_DRY_EFFECT_PROFILE,
    SIM_APPROVAL_BOUND,
    SIM_DISPATCH_INTENT,
    SIM_PREPARED,
    PRODUCTION_STATES_FORBIDDEN_IN_MOCK,
    AuthoritySnapshot,
    InvocationIntegrityError,
    RuntimeInvocationStore,
    SimulationStateObservation,
    approval_binding_issues,
    build_invocation_request,
    build_prompt_artifact,
    build_runtime_invocation_result,
    build_simulation_approval_evidence,
    compute_idempotency_key,
    derive_intake_candidate_id,
    is_valid_generated_id,
    new_attempt_id,
    new_invocation_id,
    next_state_observation,
    reject_untrusted_request_payload,
)


def fixed_clock():
    return "2026-01-01T00:00:00Z"


def _authority() -> AuthoritySnapshot:
    return AuthoritySnapshot(
        repository_id="repo-1", repository_fingerprint="fp-1", base_commit="c" * 40,
        task_id="task-1", task_contract_digest="digest-1",
    )


# ── IDs (RPAC-REQ-064) ───────────────────────────────────────────────────


def test_invocation_and_attempt_identity():
    invocation_id = new_invocation_id()
    attempt_id = new_attempt_id()
    assert is_valid_generated_id(invocation_id, prefix="inv")
    assert is_valid_generated_id(attempt_id, prefix="att")
    assert new_invocation_id() != invocation_id


def test_invalid_generated_id_format_rejected():
    assert not is_valid_generated_id("not-a-real-id", prefix="inv")
    assert not is_valid_generated_id(12345, prefix="inv")


# ── PromptArtifact (RPAC-REQ-020/021) ───────────────────────────────────


def test_prompt_artifact_binding_and_digest():
    authority = _authority()
    prompt = build_prompt_artifact(
        content="hello world", generation_method="bootstrap", generation_version="1.0",
        authority=authority, clock=fixed_clock,
    )
    assert prompt.repository_id == authority.repository_id
    assert prompt.task_id == authority.task_id
    assert prompt.content_digest == build_prompt_artifact(
        content="hello world", generation_method="bootstrap", generation_version="1.0",
        authority=authority, clock=fixed_clock,
    ).content_digest


def test_request_requires_prompt_artifact_not_raw_string():
    authority = _authority()
    approval = build_simulation_approval_evidence(
        prompt=build_prompt_artifact(
            content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
        ),
        authority=authority, runtime_target_id="mock-dry.no-change.v1",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id="mock-dry.no-change.v1",
        expected_adapter_id="pcae.mock-dry", descriptor_digest="d", target_config_digest="c",
        prompt="raw string, not a PromptArtifact",  # type: ignore[arg-type]
        approval=approval, requested_capability="simulation.dry_dispatch",
        expected_result_format="rpac.terminal-result.v1", timeout_seconds=30,
    )
    assert request is None
    assert any("prompt_must_be_prompt_artifact" in i for i in issues)


# ── Simulation approval binding (RPAC-REQ-022/023) ──────────────────────


def test_simulated_approval_exact_binding():
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id="mock-dry.no-change.v1",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    issues = approval_binding_issues(
        approval, prompt=prompt, authority=authority, runtime_target_id="mock-dry.no-change.v1",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(),
    )
    assert issues == ()


def test_binding_change_invalidates_simulated_approval():
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id="mock-dry.no-change.v1",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    issues = approval_binding_issues(
        approval, prompt=prompt, authority=authority, runtime_target_id="mock-dry.synthetic-change.v1",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(),
    )
    assert "approval_target_mismatch" in issues


def test_simulation_approval_must_stay_simulation_only():
    from pcae.core.runtime_invocation import SimulationApprovalEvidence

    with pytest.raises(ValueError):
        SimulationApprovalEvidence(
            approval_id="a", bound_prompt_digest="p", bound_repository_id="r",
            bound_task_id="t", bound_runtime_target_id="rt", bound_effect_profile_digest="e",
            created_at=fixed_clock(), simulation_only=False,
        )


# ── Untrusted payload rejection (RPAC-REQ-026) ──────────────────────────


def test_adapter_cannot_rebind_request_via_untrusted_payload():
    issues = reject_untrusted_request_payload({"execution_allowed": True, "path": "x"})
    assert any("execution_allowed" in i for i in issues)


# ── Idempotency key (RPAC-REQ-065/066) ──────────────────────────────────


def test_idempotency_key_stability():
    projection = {"a": 1, "b": 2}
    assert compute_idempotency_key(projection) == compute_idempotency_key({"b": 2, "a": 1})


def test_idempotency_key_changes_with_content():
    assert compute_idempotency_key({"a": 1}) != compute_idempotency_key({"a": 2})


# ── Simulation state order (RPAC-REQ-039/040/041) ───────────────────────


def test_simulation_state_order():
    first = next_state_observation(None, SIM_PREPARED, fixed_clock())
    second = next_state_observation(first, SIM_APPROVAL_BOUND, fixed_clock())
    assert second.sequence == 2
    assert second.prior_digest == first.digest()


def test_state_log_rejects_out_of_order():
    first = next_state_observation(None, SIM_PREPARED, fixed_clock())
    with pytest.raises(ValueError):
        next_state_observation(first, SIM_PREPARED, fixed_clock())


def test_mock_never_emits_production_runtime_states():
    from pcae.core.runtime_invocation import SIMULATION_STATE_ORDER

    assert PRODUCTION_STATES_FORBIDDEN_IN_MOCK.isdisjoint(set(SIMULATION_STATE_ORDER))
    for state in SIMULATION_STATE_ORDER:
        assert state.startswith("SIM_")


# ── Store: create-only, replay, collision, restart (RPAC-REQ-061/066-069) ──


def _sample_request(store_root: Path, target: str = "mock-dry.no-change.v1"):
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=target,
        expected_adapter_id="pcae.mock-dry", descriptor_digest="d", target_config_digest="c",
        prompt=prompt, approval=approval, requested_capability="simulation.dry_dispatch",
        expected_result_format="rpac.terminal-result.v1", timeout_seconds=30,
    )
    assert issues == ()
    return request


def test_persistent_record_integrity():
    with tempfile.TemporaryDirectory() as tmp:
        store = RuntimeInvocationStore(Path(tmp))
        request = _sample_request(Path(tmp))
        store.create_request_record(request)
        stored = store.read_request(request.invocation_id)
        assert stored["idempotency_key"] == request.idempotency_key


def test_same_id_replay_and_collision():
    with tempfile.TemporaryDirectory() as tmp:
        store = RuntimeInvocationStore(Path(tmp))
        request = _sample_request(Path(tmp))
        store.create_request_record(request)
        store.create_request_record(request)  # idempotent replay, no error

        from dataclasses import replace

        conflicting = replace(request, idempotency_key="different-key-forces-collision")
        with pytest.raises(InvocationIntegrityError):
            store.create_request_record(conflicting)


def test_append_event_rejects_chain_break():
    with tempfile.TemporaryDirectory() as tmp:
        store = RuntimeInvocationStore(Path(tmp))
        request = _sample_request(Path(tmp))
        store.create_request_record(request)
        obs1 = next_state_observation(None, SIM_PREPARED, fixed_clock())
        store.append_event(request.invocation_id, request.attempt_id, obs1)
        forged = SimulationStateObservation(
            sequence=2, state=SIM_APPROVAL_BOUND, observed_at=fixed_clock(),
            prior_digest="not-the-real-prior-digest",
        )
        with pytest.raises(InvocationIntegrityError):
            store.append_event(request.invocation_id, request.attempt_id, forged)


def test_restart_boundaries():
    with tempfile.TemporaryDirectory() as tmp:
        store = RuntimeInvocationStore(Path(tmp))
        request = _sample_request(Path(tmp))
        store.create_request_record(request)
        assert store.restart_disposition(request.invocation_id, request.attempt_id) == "not_started"

        obs1 = next_state_observation(None, SIM_PREPARED, fixed_clock())
        store.append_event(request.invocation_id, request.attempt_id, obs1)
        assert (
            store.restart_disposition(request.invocation_id, request.attempt_id)
            == "pending_pre_dispatch"
        )

        obs2 = next_state_observation(obs1, SIM_APPROVAL_BOUND, fixed_clock())
        store.append_event(request.invocation_id, request.attempt_id, obs2)
        for state in (
            "SIM_CAPABLE", "SIM_PB_EVALUATED", "SIM_FRESH", "SIM_ENFORCEMENT_EVALUATED",
            SIM_DISPATCH_INTENT,
        ):
            obs2 = next_state_observation(obs2, state, fixed_clock())
            store.append_event(request.invocation_id, request.attempt_id, obs2)
        assert (
            store.restart_disposition(request.invocation_id, request.attempt_id)
            == FAILURE_SIMULATION_AMBIGUOUS
        )

        result = build_runtime_invocation_result(
            request=request, terminal_outcome="success", structured_payload={"x": 1},
            requesting_agent_id="codex-ox", producer_claim="pcae.mock-dry-fixture",
        )
        store.write_result(request.invocation_id, request.attempt_id, result)
        assert store.restart_disposition(request.invocation_id, request.attempt_id) == "completed"


def test_duplicate_completion_semantics():
    with tempfile.TemporaryDirectory() as tmp:
        store = RuntimeInvocationStore(Path(tmp))
        request = _sample_request(Path(tmp))
        store.create_request_record(request)
        result = build_runtime_invocation_result(
            request=request, terminal_outcome="success", structured_payload={"x": 1},
            requesting_agent_id="codex-ox", producer_claim="pcae.mock-dry-fixture",
        )
        store.write_result(request.invocation_id, request.attempt_id, result)
        store.write_result(request.invocation_id, request.attempt_id, result)  # idempotent replay

        conflicting = build_runtime_invocation_result(
            request=request, terminal_outcome="success", structured_payload={"x": 2},
            requesting_agent_id="codex-ox", producer_claim="pcae.mock-dry-fixture",
        )
        with pytest.raises(InvocationIntegrityError):
            store.write_result(request.invocation_id, request.attempt_id, conflicting)


def test_intake_candidate_identity_is_stable():
    candidate_id_1 = derive_intake_candidate_id("inv-1", "att-1", "digest-1")
    candidate_id_2 = derive_intake_candidate_id("inv-1", "att-1", "digest-1")
    candidate_id_3 = derive_intake_candidate_id("inv-1", "att-1", "digest-2")
    assert candidate_id_1 == candidate_id_2
    assert candidate_id_1 != candidate_id_3


def test_only_controlled_record_store_changes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sentinel = root / "outside-the-store.txt"
        sentinel.write_text("do not touch", encoding="utf-8")
        store = RuntimeInvocationStore(root)
        request = _sample_request(root)
        store.create_request_record(request)
        assert sentinel.read_text(encoding="utf-8") == "do not touch"
        expected_root = root / ".pcae" / "runtime-invocations" / "mock-v1"
        for path in root.rglob("*"):
            if path.is_file() and path != sentinel:
                assert str(path).startswith(str(expected_root))


def test_result_remains_untrusted():
    request = _sample_request(Path(tempfile.mkdtemp()))
    result = build_runtime_invocation_result(
        request=request, terminal_outcome="success", structured_payload={"x": 1},
        requesting_agent_id="codex-ox", producer_claim="pcae.mock-dry-fixture",
    )
    assert result.untrusted is True
    field_names = set(result.__dataclass_fields__.keys())
    assert field_names.isdisjoint({"accepted_change", "promoted", "task_complete"})
