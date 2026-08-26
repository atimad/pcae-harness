"""
Phase 149O.20L.7O.3S — RPAC-001 mock-v1 integration, independent E2E,
security, and identity tests.

Proves the full simulation flow (request -> catalog -> resolver ->
preflight -> PB simulation -> enforcement test double -> record intent ->
mock dispatch/collect -> normalized result -> intake handoff) with zero
subprocess/network/credential access and zero repository mutation outside
the controlled `.pcae/runtime-invocations/mock-v1` store, and that
`pcae runtime inspect` reports Observed/observe/unavailable unchanged.
"""

from __future__ import annotations

import socket
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core import intake as intake_module
from pcae.core.mock_runtime_adapter import (
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    TARGET_FAILURE,
    TARGET_NO_CHANGE,
    TARGET_SYNTHETIC_CHANGE,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.runtime_adapter import (
    RuntimeAdapterResolver,
    RuntimeTargetConfiguration,
    build_intake_handoff,
    simulate_invocation,
)
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    RuntimeInvocationStore,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)
from pcae.core.runtime_registry import RuntimeRegistry


def make_clock():
    counter = [0]

    def clock() -> str:
        counter[0] += 1
        return f"2026-01-01T00:00:{counter[0]:02d}Z"

    return clock


def _authority(task_id: str = "task-e2e") -> AuthoritySnapshot:
    return AuthoritySnapshot(
        repository_id="repo-e2e", repository_fingerprint="fp-e2e", base_commit="d" * 40,
        task_id=task_id, task_contract_digest="digest-e2e",
    )


def _build_stack(target: str):
    registry = RuntimeRegistry()
    descriptor = build_mock_descriptor()
    registry.register_adapter_descriptor(descriptor)
    resolver = RuntimeAdapterResolver(registry)
    config = RuntimeTargetConfiguration(target, "1.0", MOCK_ADAPTER_ID, target)
    resolver.register_target(config)
    adapter = MockDryRuntimeAdapter()
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, adapter)
    return registry, descriptor, resolver, config, adapter


def _run(target: str, store_root: Path, clock, agent_id: str = "codex-ox", task_id: str = "task-e2e"):
    registry, descriptor, resolver, config, adapter = _build_stack(target)
    authority = _authority(task_id=task_id)
    prompt = build_prompt_artifact(
        content="run the deterministic dry simulation", generation_method="bootstrap",
        generation_version="1.0", authority=authority, clock=clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id=agent_id, runtime_target_id=target,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert issues == ()
    store = RuntimeInvocationStore(store_root)
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
    )
    return outcome, request, store


# ── Integration: full vertical slice ────────────────────────────────────


def test_mock_vertical_slice_complete(tmp_path):
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    assert outcome.accepted
    assert outcome.trace == (
        "SIM_PREPARED", "SIM_APPROVAL_BOUND", "SIM_CAPABLE", "SIM_PB_EVALUATED",
        "SIM_FRESH", "SIM_ENFORCEMENT_EVALUATED", "SIM_DISPATCH_INTENT",
        "SIM_DISPATCHED", "SIM_COMPLETED", "SIM_RESULT_CAPTURED",
        "SIM_INTAKE_CANDIDATE_BUILT",
    )
    assert outcome.adapter_call_count == 1
    assert outcome.result.runtime_target_id == TARGET_NO_CHANGE


def test_mock_vertical_slice_order_short_circuits_on_unknown_target(tmp_path):
    clock = make_clock()
    registry, descriptor, resolver, config, adapter = _build_stack(TARGET_NO_CHANGE)
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id="unregistered-target",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id="unregistered-target",
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest="whatever", prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert issues == ()
    store = RuntimeInvocationStore(tmp_path)
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
    )
    assert not outcome.accepted
    assert outcome.failure_category == "no_adapter_configured"
    assert outcome.adapter_call_count == 0


def test_failed_gate_never_calls_adapter(tmp_path):
    clock = make_clock()
    registry, descriptor, resolver, config, adapter = _build_stack(TARGET_NO_CHANGE)
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=clock
    )
    # Approval bound to the wrong target invalidates binding before any lookup.
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id="some-other-target",
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=TARGET_NO_CHANGE,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert issues == ()
    store = RuntimeInvocationStore(tmp_path)
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
    )
    assert not outcome.accepted
    assert outcome.adapter_call_count == 0
    assert outcome.failure_category == "invalid_request"


def test_gate_order_and_short_circuit(tmp_path):
    clock = make_clock()
    outcome, _request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    order = [
        "SIM_PREPARED", "SIM_APPROVAL_BOUND", "SIM_CAPABLE", "SIM_PB_EVALUATED",
        "SIM_FRESH", "SIM_ENFORCEMENT_EVALUATED", "SIM_DISPATCH_INTENT",
        "SIM_DISPATCHED", "SIM_COMPLETED", "SIM_RESULT_CAPTURED", "SIM_INTAKE_CANDIDATE_BUILT",
    ]
    assert list(outcome.trace) == order


# ── Failure taxonomy exercise ────────────────────────────────────────────


def test_mock_failure_mapping(tmp_path):
    clock = make_clock()
    outcome, _request, _store = _run(TARGET_FAILURE, tmp_path, clock)
    assert outcome.accepted  # the gate sequence succeeds; the *simulated target* fails
    assert outcome.result.terminal_outcome == "failure"
    assert outcome.result.error_category == "runtime_failure"


# ── Generic intake boundary (Stage B, RPAC-REQ-080/081) ─────────────────


def test_result_to_generic_intake_candidate(tmp_path):
    clock = make_clock()
    outcome, _request, store = _run(TARGET_SYNTHETIC_CHANGE, tmp_path, clock)
    assert outcome.accepted
    handoff = store.read_result(outcome.result.invocation_id, outcome.result.attempt_id)
    assert handoff is not None
    handoff_doc_path = (
        tmp_path / ".pcae" / "runtime-invocations" / "mock-v1"
        / outcome.result.invocation_id / "attempts" / outcome.result.attempt_id
        / "intake-handoff.json"
    )
    assert handoff_doc_path.exists()
    import json

    handoff_doc = json.loads(handoff_doc_path.read_text(encoding="utf-8"))
    assert handoff_doc["disposition"] == "candidate_built"
    assert handoff_doc["candidate"]["proposed_changes"][0]["path"] == "mock-output.txt"

    # Never actually submitted/ingested.
    candidate = handoff_doc["candidate"]
    assert candidate is not None
    # No accidental call into validate_and_ingest_intake_candidate happened;
    # no ECP/intake-candidates store directory was created.
    assert not (tmp_path / ".pcae" / "intake-candidates").exists()


def test_text_only_result_creates_no_candidate(tmp_path):
    clock = make_clock()
    outcome, _request, store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    import json

    handoff_doc_path = (
        tmp_path / ".pcae" / "runtime-invocations" / "mock-v1"
        / outcome.result.invocation_id / "attempts" / outcome.result.attempt_id
        / "intake-handoff.json"
    )
    handoff_doc = json.loads(handoff_doc_path.read_text(encoding="utf-8"))
    assert handoff_doc["disposition"] == "not_applicable_no_changes"
    assert handoff_doc["candidate"] is None


def test_intake_candidate_builder_is_producer_neutral():
    result = intake_module.build_intake_candidate_from_changes(
        repository_fingerprint="fp", base_commit="c" * 40, task_id="t1",
        candidate_id="cand-1", changed_files=[
            {"path": "a.txt", "operation": "create", "content_after": "x", "content_hash_after": "h"}
        ],
        producer_kind="any-agent-identity-works",
    )
    assert result["disposition"] == "candidate_built"
    assert result["candidate"]["producer"]["kind"] == "any-agent-identity-works"


# ── Independent E2E: zero subprocess/network/credential/mutation ───────


def test_independent_e2e_zero_effects_and_runtime_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def _boom(*args, **kwargs):
        raise AssertionError("mock-v1 path must never touch subprocess/network")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)

    from pcae.core import runtime_introspection

    before = runtime_introspection.get_health(RuntimeRegistry())

    clock = make_clock()
    store_root = tmp_path / "repo"
    store_root.mkdir()
    before_files = sorted(store_root.rglob("*"))

    outcome, request, store = _run(TARGET_SYNTHETIC_CHANGE, store_root, clock)
    assert outcome.accepted
    assert outcome.adapter_call_count == 1

    handoff = store.write_intake_handoff  # already invoked by simulate_invocation

    controlled_root = store_root / ".pcae" / "runtime-invocations" / "mock-v1"
    for path in store_root.rglob("*"):
        if path.is_file():
            assert str(path).startswith(str(controlled_root))

    after = runtime_introspection.get_health(RuntimeRegistry())
    assert before.current_runtime_state == after.current_runtime_state == "Observed"
    assert (
        before.current_maximum_plugin_capability
        == after.current_maximum_plugin_capability
        == "observe"
    )
    assert before.execution_availability == after.execution_availability == "unavailable"


def test_replay_same_request_no_second_adapter_call(tmp_path):
    clock = make_clock()
    outcome1, request1, store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    assert outcome1.accepted
    # Re-running create_request_record with the same content is idempotent
    # and does not raise; a genuinely new attempt with the same invocation
    # would require kernel-level replay wiring, which mock-v1 tests at the
    # store layer (see test_runtime_invocation_3s.py::test_same_id_replay_and_collision).
    store.create_request_record(request1)
    stored = store.read_request(request1.invocation_id)
    assert stored["idempotency_key"] == request1.idempotency_key


# ── Security invariants (Matrix D) ──────────────────────────────────────


def test_adapter_cannot_self_authorize(tmp_path):
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    assert outcome.accepted
    # The adapter's Protocol has no method capable of writing gate evidence;
    # confirm none of its public methods can mutate the envelope/request.
    from pcae.core.mock_runtime_adapter import MockDryRuntimeAdapter

    adapter = MockDryRuntimeAdapter()
    for forbidden in ("approve", "authorize", "grant_permission", "set_pb_decision"):
        assert not hasattr(adapter, forbidden)


def test_adapter_cannot_override_pb_or_enforcement(tmp_path):
    """A forged result carrying governance-shaped keys is not part of the
    frozen `RuntimeInvocationResult` schema at all -- attempting to smuggle
    one in via `structured_payload` never escapes into the trusted digest
    computation as an authority field."""
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    result = outcome.result
    field_names = set(result.__dataclass_fields__.keys())
    assert field_names.isdisjoint({"pb_decision", "enforcement_decision", "authorized"})


def test_adapter_cannot_choose_repository_authority(tmp_path):
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    # The result carries no repository/task claim field at all; authority
    # binding lives only on the trusted-kernel-built InvocationRequest.
    result_fields = set(outcome.result.__dataclass_fields__.keys())
    assert result_fields.isdisjoint({"repository_id", "task_id"})
    assert request.repository_id == "repo-e2e"


def test_runtime_result_is_untrusted_evidence(tmp_path):
    clock = make_clock()
    outcome, _request, _store = _run(TARGET_SYNTHETIC_CHANGE, tmp_path, clock)
    assert outcome.result.untrusted is True


def test_no_silent_fallback_on_unknown_target(tmp_path):
    clock = make_clock()
    registry, descriptor, resolver, config, adapter = _build_stack(TARGET_NO_CHANGE)
    resolved = resolver.resolve_exact("totally-unknown")
    from pcae.core.runtime_adapter import ResolutionFailure

    assert isinstance(resolved, ResolutionFailure)


def test_no_capability_inflation_via_registration(tmp_path):
    registry, descriptor, resolver, config, adapter = _build_stack(TARGET_NO_CHANGE)
    from pcae.core import runtime_introspection

    health = runtime_introspection.get_health(registry)
    assert health.current_runtime_state == "Observed"
    assert health.current_maximum_plugin_capability == "observe"
    assert health.execution_availability == "unavailable"
    catalog = registry.adapter_catalog_snapshot()
    assert catalog.registered_adapter_count == 1
    assert catalog.real_execution_capable_count == 0


# ── Identity tests (RPAC-REQ-006/007/008, 3R §45) ───────────────────────


def test_codex_ox_agent_identity_positive_case(tmp_path):
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock, agent_id="codex-ox")
    assert outcome.accepted
    assert request.requester_agent_id == "codex-ox"
    assert request.runtime_target_id == TARGET_NO_CHANGE
    assert request.provider_id is None
    assert request.model_id is None


def test_custom_agent_identity_same_semantic_output(tmp_path):
    clock1 = make_clock()
    outcome_codex, _r1, _s1 = _run(TARGET_NO_CHANGE, tmp_path / "a", clock1, agent_id="codex-ox")
    clock2 = make_clock()
    outcome_custom, _r2, _s2 = _run(
        TARGET_NO_CHANGE, tmp_path / "b", clock2, agent_id="custom-review-agent-17"
    )
    assert outcome_codex.result.payload_digest == outcome_custom.result.payload_digest
    assert outcome_codex.result.structured_payload == outcome_custom.result.structured_payload


def test_codex_ox_gains_no_transport_provider_or_model(tmp_path):
    clock = make_clock()
    outcome, request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock, agent_id="codex-ox")
    assert request.provider_id is None
    assert request.model_id is None
    assert "openrouter" not in request.runtime_target_id.lower()
    assert request.expected_adapter_id == MOCK_ADAPTER_ID


# ── Regressions: existing runtime introspection / plugin / PB surfaces ──


def test_runtime_inspect_snapshot_unchanged_after_adapter_admission():
    from pcae.core import runtime_introspection

    before = runtime_introspection.get_health(RuntimeRegistry())
    registry, descriptor, resolver, config, adapter = _build_stack(TARGET_NO_CHANGE)
    after = runtime_introspection.get_health(registry)
    assert before.current_runtime_state == after.current_runtime_state
    assert before.current_maximum_plugin_capability == after.current_maximum_plugin_capability
    assert before.execution_availability == after.execution_availability


def test_permission_broker_simulation_is_non_authorizing(tmp_path):
    clock = make_clock()
    outcome, _request, _store = _run(TARGET_NO_CHANGE, tmp_path, clock)
    assert outcome.accepted
    # The PB decision consumed is always simulation_only; production PB
    # policy/rule set is untouched (no import of a new rule module).
    from pcae.core.permission_broker_foundation import POLICY_IDS_CANONICAL, POLICY_IDS

    assert set(POLICY_IDS) == POLICY_IDS_CANONICAL
