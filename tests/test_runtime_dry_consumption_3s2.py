"""
Phase 149O.20L.7O.3S.2 — Production Dry-Lifecycle Runtime Adapter
Consumption: core service-layer tests.

Proves `pcae.core.runtime_dry_consumption` is a real, narrow production
consumer of the verified RPAC-001 mock/dry adapter: explicit target
selection only (no fallback), authority derived from real PCAE-owned
repository/task state, zero subprocess/network/credential access in the
RPAC-consuming phase, deterministic semantic output, no runtime-inspect
contamination, and no accidental widening of adapter/security invariants
already verified in 3S/3S.1.
"""

from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core.mock_runtime_adapter import (
    KNOWN_MOCK_TARGET_FIXTURES,
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import (
    PermissionBroker,
    PermissionBrokerDecision,
)
from pcae.core.runtime_adapter import (
    RuntimeAdapterResolver,
    RuntimeTargetConfiguration,
    SimulationOutcome,
    simulate_invocation,
)
from pcae.core.runtime_dry_consumption import (
    DRY_PROMPT_GENERATION_METHOD,
    DRY_PROMPT_GENERATION_VERSION,
    DRY_RUNTIME_TIMEOUT_SECONDS,
    DryConsumerContext,
    UnknownRuntimeTargetError,
    _run_with_context,
    resolve_dry_consumer_context,
    run_production_dry_invocation,
)
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    RuntimeInvocationStore,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
    reject_untrusted_request_payload,
)
from pcae.core.runtime_registry import RuntimeRegistry


def _init_repo(tmp_path: Path) -> HarnessPath:
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return HarnessPath(tmp_path)


def _make_active_task(root: HarnessPath, task_id: str = "task-3s2-e2e") -> None:
    active_dir = root.path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / f"{task_id}.md").write_text(
        "# Task Contract\n\n## Task ID\n\n" + task_id + "\n\n## Title\n\nTest\n\n## Status\n\nactive\n",
        encoding="utf-8",
    )


# ── Explicit target selection / no-fallback (RPAC-REQ-053, spec §7/§24) ─


def test_unknown_target_fails_closed_no_context_derivation(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root)
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox", runtime_target_id="totally-bogus-target",
        prompt_content="p",
    )
    assert isinstance(outcome, UnknownRuntimeTargetError)
    assert "unknown_runtime_target" in str(outcome)


def test_no_active_task_fails_closed(tmp_path):
    root = _init_repo(tmp_path)
    # No tasks/active/*.md created.
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox",
        runtime_target_id=next(iter(KNOWN_MOCK_TARGET_FIXTURES)),
        prompt_content="p",
    )
    assert isinstance(outcome, UnknownRuntimeTargetError)


def test_all_known_fixtures_are_valid_explicit_targets(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root)
    for target in KNOWN_MOCK_TARGET_FIXTURES:
        outcome = run_production_dry_invocation(
            root=root, agent_id="codex-ox", runtime_target_id=target, prompt_content="p",
        )
        assert isinstance(outcome, SimulationOutcome)
        assert outcome.accepted


# ── Successful dry E2E through the real production entry point ─────────


def test_successful_production_dry_e2e(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root)
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="bootstrap prompt content",
    )
    assert isinstance(outcome, SimulationOutcome)
    assert outcome.accepted
    assert outcome.adapter_call_count == 1
    assert outcome.result.runtime_target_id == "mock-dry.no-change.v1"
    assert outcome.result.untrusted is True
    # Evidence confined to the controlled store tree.
    store_root = root.path / ".pcae" / "runtime-invocations" / "mock-v1"
    assert store_root.is_dir()
    for path in store_root.rglob("*"):
        if path.is_file():
            assert str(path).startswith(str(store_root))


# ── Custom / codex-ox identity regressions (RPAC-REQ-006/007/008) ──────


def test_custom_agent_identity_same_semantic_output(tmp_path):
    root_a = _init_repo(tmp_path / "a")
    _make_active_task(root_a)
    outcome_a = run_production_dry_invocation(
        root=root_a, agent_id="codex-ox",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="same prompt",
    )
    root_b = _init_repo(tmp_path / "b")
    _make_active_task(root_b)
    outcome_b = run_production_dry_invocation(
        root=root_b, agent_id="custom-review-agent-17",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="same prompt",
    )
    assert outcome_a.accepted and outcome_b.accepted
    assert outcome_a.result.structured_payload == outcome_b.result.structured_payload
    assert outcome_a.result.payload_digest == outcome_b.result.payload_digest


def test_codex_ox_gains_no_provider_or_model_inference(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root)
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="p",
    )
    assert outcome.accepted
    assert outcome.result.requesting_agent_id == "codex-ox"
    assert outcome.result.provider_id is None
    assert outcome.result.model_id is None
    assert "openrouter" not in outcome.result.adapter_id.lower()


# ── Zero subprocess/network/credential in the RPAC-consuming phase ─────


def test_run_with_context_zero_subprocess_network(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("RPAC-consuming phase must never touch subprocess/network")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)

    root = HarnessPath(tmp_path)
    context = DryConsumerContext(
        repository_id=str(tmp_path), repository_fingerprint="fp-fixture",
        base_commit="c" * 40, task_id="task-fixture", task_contract_digest="d" * 64,
    )
    outcome = _run_with_context(
        root=root, context=context, agent_id="codex-ox",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="p",
    )
    assert isinstance(outcome, SimulationOutcome)
    assert outcome.accepted


# ── Runtime introspection unaffected (Matrix D) ─────────────────────────


def test_runtime_inspect_unchanged_after_dry_consumption(tmp_path):
    from pcae.core import runtime_introspection
    from pcae.core.runtime_registry import RuntimeRegistry

    before = runtime_introspection.get_health(RuntimeRegistry())

    root = _init_repo(tmp_path)
    _make_active_task(root)
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox",
        runtime_target_id="mock-dry.synthetic-change.v1", prompt_content="p",
    )
    assert outcome.accepted

    after = runtime_introspection.get_health(RuntimeRegistry())
    assert before.current_runtime_state == after.current_runtime_state == "Observed"
    assert (
        before.current_maximum_plugin_capability
        == after.current_maximum_plugin_capability
        == "observe"
    )
    assert before.execution_availability == after.execution_availability == "unavailable"


# ── Authority derivation is PCAE-owned, not caller-supplied ─────────────


def test_resolve_dry_consumer_context_uses_real_head_and_task(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root, task_id="task-authority-check")
    context = resolve_dry_consumer_context(root)
    assert context is not None
    assert context.task_id == "task-authority-check"
    assert len(context.base_commit) == 40  # a real git SHA, not a placeholder
    assert context.repository_fingerprint


def test_resolve_dry_consumer_context_none_without_active_task(tmp_path):
    root = _init_repo(tmp_path)
    assert resolve_dry_consumer_context(root) is None


# ── Failure fixture / determinism ───────────────────────────────────────


# ── PB DENY E2E, built through the same production construction path ───


def _build_production_shaped_request(root: HarnessPath, context: DryConsumerContext, target: str):
    """Mirror `_run_with_context`'s construction exactly, but return the
    intermediate pieces so a test can inject a DENY-forcing broker into
    `simulate_invocation` directly -- proving the PB DENY gate fails
    closed on the *actual* production request shape, not a synthetic one.
    This injection point is test-only; the CLI/service surface
    (`run_production_dry_invocation`) has no parameter that could ever
    carry a caller-supplied broker or enforcement evaluator into
    production (Section 14 -- see `test_production_entry_point_accepts_no_injected_authority`)."""
    registry = RuntimeRegistry()
    descriptor = build_mock_descriptor()
    registry.register_adapter_descriptor(descriptor)
    resolver = RuntimeAdapterResolver(registry)
    config = RuntimeTargetConfiguration(target, "1.0", MOCK_ADAPTER_ID, target)
    resolver.register_target(config)
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())

    authority = AuthoritySnapshot(
        repository_id=context.repository_id, repository_fingerprint=context.repository_fingerprint,
        base_commit=context.base_commit, task_id=context.task_id,
        task_contract_digest=context.task_contract_digest,
    )
    clock = [0]

    def _clock():
        clock[0] += 1
        return f"2026-01-01T00:00:{clock[0]:02d}Z"

    prompt = build_prompt_artifact(
        content="p", generation_method=DRY_PROMPT_GENERATION_METHOD,
        generation_version=DRY_PROMPT_GENERATION_VERSION, authority=authority, clock=_clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=target,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=DRY_RUNTIME_TIMEOUT_SECONDS,
    )
    assert issues == ()
    return request, resolver, prompt, approval, _clock


def test_pb_deny_e2e_fails_closed_zero_adapter_calls(tmp_path):
    class AlwaysDenyPB(PermissionBroker):
        def evaluate(self, request):
            return PermissionBrokerDecision(
                decision="DENY", decision_reason="3s2_pb_deny_e2e",
                matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
                requires_human=False, simulation_only=True, causing_policy_id="ADV-3S2",
            )

    root = _init_repo(tmp_path)
    _make_active_task(root)
    context = resolve_dry_consumer_context(root)
    assert context is not None
    target = "mock-dry.no-change.v1"
    request, resolver, prompt, approval, clock = _build_production_shaped_request(root, context, target)
    store = RuntimeInvocationStore(root.path)
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock, permission_broker=AlwaysDenyPB(),
    )
    assert not outcome.accepted
    assert outcome.failure_category == "permission_denied"
    assert outcome.adapter_call_count == 0
    assert outcome.result is None
    # Product-visible: dry simulation stopped, no adapter effect beyond
    # the allowed pre-dispatch evidence trace already written.
    assert "SIM_DISPATCH_INTENT" not in outcome.trace


# ── Authority-spoofing / injection safety (Section 14/48) ──────────────


def test_authority_spoofing_fields_rejected_by_existing_guard():
    forged_payload = {
        "runtime_target_id": "mock-dry.no-change.v1",
        "authorized": True,
        "permission": "ALLOW",
        "execution_allowed": True,
        "approved": True,
    }
    issues = reject_untrusted_request_payload(forged_payload)
    assert len(issues) == 4
    assert all(issue.startswith("forbidden_authority_field:") for issue in issues)


def test_production_entry_point_accepts_no_injected_authority():
    """Structural guarantee (Section 14): the one production-facing
    function has no parameter through which a caller could smuggle a
    permissive enforcement evaluator or Permission Broker instance."""
    import inspect

    params = set(inspect.signature(run_production_dry_invocation).parameters)
    assert params == {"root", "agent_id", "runtime_target_id", "prompt_content"}
    assert "enforcement_evaluator" not in params
    assert "permission_broker" not in params


def test_failure_fixture_target_still_completes_gate_sequence(tmp_path):
    root = _init_repo(tmp_path)
    _make_active_task(root)
    outcome = run_production_dry_invocation(
        root=root, agent_id="codex-ox",
        runtime_target_id="mock-dry.failure.v1", prompt_content="p",
    )
    assert outcome.accepted  # gate sequence succeeds; simulated *target* fails
    assert outcome.result.terminal_outcome == "failure"
    assert outcome.result.error_category == "runtime_failure"
