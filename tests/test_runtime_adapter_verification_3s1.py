"""
Phase 149O.20L.7O.3S.1 — Independent End-to-End Deterministic Mock/Dry
Runtime Adapter Verification.

Fresh, independently-authored adversarial tests against the RPAC-001
v1.0 mock-v1 slice built by Phase 3S (`runtime_adapter.py`,
`runtime_invocation.py`, `mock_runtime_adapter.py`,
`runtime_registry.py`, `intake.py`). These tests are deliberately NOT a
rerun of 3S's own test suite (`tests/test_runtime_adapter_e2e_3s.py`
etc.) — they probe scenarios 3S.1 identified as independently
verification-worthy: authority-field injection into frozen/closed
schemas, a malicious "always-allow" enforcement-double injection
combined with a forced Permission Broker DENY, no-fallback resolution
under typo/agent-id/empty targets, duplicate adapter-descriptor
admission, import-time side effects (subprocess/socket), dual-registry
separation (`_plugins` vs `_adapter_descriptors`), and semantic
determinism across independently constructed stacks.

See docs/PHASE_149O_20L_7O_3S_1_INDEPENDENT_END_TO_END_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_VERIFICATION.md
for the full verification narrative and matrices this suite supports.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core.mock_runtime_adapter import (
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    TARGET_NO_CHANGE,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.runtime_adapter import (
    ResolutionFailure,
    RuntimeAdapterResolver,
    RuntimeTargetConfiguration,
    simulate_invocation,
)
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    RuntimeInvocationStore,
    SimulationEnforcementEvaluator,
    SimulationEnforcementObservation,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)
from pcae.core.runtime_registry import RuntimeRegistry
from pcae.core.permission_broker_foundation import (
    PermissionBroker,
    PermissionBrokerDecision,
)


def make_clock():
    counter = [0]

    def clock() -> str:
        counter[0] += 1
        return f"2026-01-01T00:00:{counter[0]:02d}Z"

    return clock


def _authority(task_id: str = "task-3s1") -> AuthoritySnapshot:
    return AuthoritySnapshot(
        repository_id="repo-3s1",
        repository_fingerprint="fp-3s1",
        base_commit="e" * 40,
        task_id=task_id,
        task_contract_digest="digest-3s1",
    )


def _build_stack():
    registry = RuntimeRegistry()
    descriptor = build_mock_descriptor()
    reg_result = registry.register_adapter_descriptor(descriptor)
    resolver = RuntimeAdapterResolver(registry)
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    resolver.register_target(config)
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    return registry, descriptor, resolver, config, reg_result


def _build_request(clock, agent_id: str = "codex-ox"):
    registry, descriptor, resolver, config, _ = _build_stack()
    authority = _authority()
    prompt = build_prompt_artifact(
        content="run", generation_method="bootstrap", generation_version="1.0",
        authority=authority, clock=clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=TARGET_NO_CHANGE,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id=agent_id, runtime_target_id=TARGET_NO_CHANGE,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert issues == ()
    return request, resolver, prompt, approval


# ── Registry dual-surface reconciliation (Matrix B) ─────────────────────


def test_adapter_catalog_and_plugin_registry_are_distinct_namespaces():
    registry, descriptor, _resolver, _config, reg_result = _build_stack()
    assert reg_result.accepted
    assert len(registry.list_adapter_descriptors()) == 1
    assert len(registry.list_plugins()) == 0, (
        "registering an RPAC adapter descriptor must not populate the legacy "
        "Plugin Model collection `pcae runtime inspect` reports from"
    )


def test_runtime_inspect_registry_is_fresh_and_never_sees_mock_adapter():
    """`run_runtime_inspect` constructs `RuntimeRegistry()` fresh per
    invocation and no production module ever calls
    `register_adapter_descriptor(build_mock_descriptor())` outside tests
    -- so 0 plugins / 0 capabilities remains truthful, not merely an
    artifact of a fresh object."""
    from pcae.commands.runtime_inspect import _build_snapshot

    snapshot = _build_snapshot(RuntimeRegistry())
    assert snapshot["registry"]["registered_plugin_count"] == 0
    assert snapshot["registry"]["registered_capability_count"] == 0


# ── Authority injection (adversarial) ───────────────────────────────────


def test_authority_field_cannot_be_set_on_frozen_request():
    clock = make_clock()
    request, *_ = _build_request(clock)
    with pytest.raises(FrozenInstanceError):
        setattr(request, "authorized", True)


def test_authority_kwarg_rejected_by_closed_request_builder():
    clock = make_clock()
    registry, descriptor, resolver, config, _ = _build_stack()
    authority = _authority()
    prompt = build_prompt_artifact(
        content="run", generation_method="bootstrap", generation_version="1.0",
        authority=authority, clock=clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=TARGET_NO_CHANGE,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock,
    )
    with pytest.raises(TypeError):
        build_invocation_request(
            authority=authority, requester_agent_id="codex-ox", runtime_target_id=TARGET_NO_CHANGE,
            expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
            target_config_digest=config.digest(), prompt=prompt, approval=approval,
            requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
            timeout_seconds=30,
            authorized=True,  # forbidden field: no such parameter exists
        )


# ── No silent fallback (adversarial) ────────────────────────────────────


@pytest.mark.parametrize(
    "bad_target",
    ["totally-unknown-target-xyz", "codex-ox", "claude-local", "", "mock-dry.no-change.v2"],
)
def test_unresolvable_targets_fail_closed_with_no_fallback(bad_target):
    _registry, _descriptor, resolver, _config, _ = _build_stack()
    result = resolver.resolve_exact(bad_target)
    assert isinstance(result, ResolutionFailure)
    assert result.category == "no_adapter_configured"


def test_duplicate_target_registration_rejected_not_last_writer_wins():
    _registry, _descriptor, resolver, config, _ = _build_stack()
    with pytest.raises(ValueError):
        resolver.register_target(config)


def test_duplicate_adapter_descriptor_same_digest_is_idempotent_not_overwrite():
    registry, descriptor, *_ = _build_stack()
    second = registry.register_adapter_descriptor(descriptor)
    assert second.accepted
    assert "idempotent_replay" in second.issues


# ── Enforcement seam adversarial verification ───────────────────────────


def test_malicious_always_allow_enforcement_double_cannot_cross_pb_deny():
    """A caller-injected enforcement evaluator that always claims
    `would_allow_simulation` must not be able to force dispatch when the
    Permission Broker independently denies -- `simulate_invocation`
    checks `pb_would_allow` itself, before the double is ever consulted."""

    class AlwaysAllowEnforcement(SimulationEnforcementEvaluator):
        def evaluate(self, *, pb_would_allow, approval_binding_ok, freshness_ok):
            return SimulationEnforcementObservation(
                outcome="would_allow_simulation",
                simulation_only=True,
                non_authorizing=True,
                evidence_digest="forced-allow-by-adversarial-double",
            )

    class AlwaysDenyPB(PermissionBroker):
        def evaluate(self, request):
            return PermissionBrokerDecision(
                decision="DENY", decision_reason="adversarial_forced_deny",
                matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
                requires_human=False, simulation_only=True, causing_policy_id="ADV-3S1",
            )

    clock = make_clock()
    request, resolver, prompt, approval = _build_request(clock)
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock,
        enforcement_evaluator=AlwaysAllowEnforcement(),
        permission_broker=AlwaysDenyPB(),
    )
    assert outcome.accepted is False
    assert outcome.failure_category == "permission_denied"
    assert outcome.adapter_call_count == 0, (
        "an injected always-allow enforcement double must not cause the "
        "adapter to be called when PB independently denied"
    )


def test_pb_deny_fails_closed_zero_adapter_calls():
    class AlwaysDenyPB(PermissionBroker):
        def evaluate(self, request):
            return PermissionBrokerDecision(
                decision="DENY", decision_reason="adversarial_forced_deny_2",
                matched_no_go_ids=(), matched_invariants=(), required_remediation=(),
                requires_human=False, simulation_only=True, causing_policy_id="ADV-3S1-B",
            )

    clock = make_clock()
    request, resolver, prompt, approval = _build_request(clock)
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=clock, permission_broker=AlwaysDenyPB(),
    )
    assert not outcome.accepted
    assert outcome.failure_category == "permission_denied"
    assert outcome.adapter_call_count == 0
    assert outcome.result is None


# ── Determinism across independently constructed stacks ────────────────


def test_semantic_result_deterministic_across_independent_stacks():
    clock_a = make_clock()
    request_a, resolver_a, prompt_a, approval_a = _build_request(clock_a)
    store_a = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    outcome_a = simulate_invocation(
        request=request_a, prompt_digest=prompt_a.content_digest, approval=approval_a,
        resolver=resolver_a, store=store_a, clock=clock_a,
    )

    clock_b = make_clock()
    request_b, resolver_b, prompt_b, approval_b = _build_request(clock_b)
    store_b = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    outcome_b = simulate_invocation(
        request=request_b, prompt_digest=prompt_b.content_digest, approval=approval_b,
        resolver=resolver_b, store=store_b, clock=clock_b,
    )

    assert outcome_a.accepted and outcome_b.accepted
    assert outcome_a.result.structured_payload == outcome_b.result.structured_payload
    assert outcome_a.result.terminal_outcome == outcome_b.result.terminal_outcome
    assert outcome_a.result.changed_files == outcome_b.result.changed_files
    assert outcome_a.trace == outcome_b.trace


# ── Import-side-effect audit ─────────────────────────────────────────────


def test_reimporting_runtime_adapter_modules_makes_no_subprocess_or_socket_call():
    """Import the three 3S runtime-adapter modules fresh and run a full
    E2E simulation in an isolated child process with `subprocess.Popen`
    and `socket.socket` construction blocked at the interpreter level.
    An isolated process (rather than `importlib.reload()` in-process) is
    used deliberately: reloading these modules in the shared pytest
    process would rebind their classes to new identities and break
    `isinstance`/exception-type checks in every other test module that
    already imported the pre-reload classes, corrupting unrelated tests
    that happen to run afterward in the same session."""
    script = """
import sys, subprocess, socket, tempfile
sys.path.insert(0, "src")

calls = {"subprocess": 0, "socket": 0}

def _blocked_popen_init(self, *a, **kw):
    calls["subprocess"] += 1
    raise AssertionError("subprocess.Popen constructed during import/use")

def _blocked_socket_init(self, *a, **kw):
    calls["socket"] += 1
    raise AssertionError("socket.socket constructed during import/use")

subprocess.Popen.__init__ = _blocked_popen_init
socket.socket.__init__ = _blocked_socket_init

from pathlib import Path
from pcae.core.mock_runtime_adapter import (
    MOCK_ADAPTER_ID, MOCK_CAPABILITY, MOCK_RESULT_FORMAT, TARGET_NO_CHANGE,
    MockDryRuntimeAdapter, build_mock_descriptor,
)
from pcae.core.runtime_adapter import RuntimeAdapterResolver, RuntimeTargetConfiguration, simulate_invocation
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE, AuthoritySnapshot, RuntimeInvocationStore,
    build_invocation_request, build_prompt_artifact, build_simulation_approval_evidence,
)
from pcae.core.runtime_registry import RuntimeRegistry

c = [0]
def clock():
    c[0] += 1
    return f"2026-01-01T00:00:{c[0]:02d}Z"

registry = RuntimeRegistry()
descriptor = build_mock_descriptor()
registry.register_adapter_descriptor(descriptor)
resolver = RuntimeAdapterResolver(registry)
config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
resolver.register_target(config)
resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())

authority = AuthoritySnapshot(repository_id="repo", repository_fingerprint="fp", base_commit="e"*40, task_id="task-import-audit", task_contract_digest="digest")
prompt = build_prompt_artifact(content="run", generation_method="bootstrap", generation_version="1.0", authority=authority, clock=clock)
approval = build_simulation_approval_evidence(prompt=prompt, authority=authority, runtime_target_id=TARGET_NO_CHANGE, effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=clock)
request, issues = build_invocation_request(
    authority=authority, requester_agent_id="codex-ox", runtime_target_id=TARGET_NO_CHANGE,
    expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
    target_config_digest=config.digest(), prompt=prompt, approval=approval,
    requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT, timeout_seconds=30,
)
assert issues == ()
store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
outcome = simulate_invocation(request=request, prompt_digest=prompt.content_digest, approval=approval, resolver=resolver, store=store, clock=clock)
assert outcome.accepted
assert calls == {"subprocess": 0, "socket": 0}, calls
print("OK")
"""
    repo_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-c", script], cwd=str(repo_root),
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert proc.stdout.strip().endswith("OK")


# ── Producer provenance / Stage-B non-authority ─────────────────────────


def test_intake_stage_b_builder_never_escalates_to_accepted_intake():
    from pcae.core import intake as intake_module

    handoff = intake_module.build_intake_candidate_from_changes(
        repository_fingerprint="fp-3s1", base_commit="e" * 40, task_id="task-3s1",
        candidate_id="cand-3s1-adv", changed_files=[
            {"path": "x.txt", "operation": "create", "content_after": "y", "content_hash_after": "z"}
        ],
        producer_kind="codex-ox", producer_source="rpac_runtime_adapter", summary="adv probe",
    )
    assert handoff["disposition"] == "candidate_built"
    assert handoff["candidate"]["producer_claims"]["self_reported_complete"] is False
    assert "accepted" not in handoff
    assert "promoted" not in handoff
    assert "task_complete" not in str(handoff).lower().replace("declared_goal", "")


def test_intake_stage_b_builder_rejects_malformed_operation_gracefully():
    from pcae.core import intake as intake_module

    with pytest.raises((KeyError, ValueError, TypeError)):
        intake_module.build_intake_candidate_from_changes(
            repository_fingerprint="fp-3s1", base_commit="e" * 40, task_id="task-3s1",
            candidate_id="cand-3s1-malformed", changed_files=[{"path": "x.txt"}],  # missing "operation"
            producer_kind="codex-ox",
        )


# ── No CLI exposure ──────────────────────────────────────────────────────


def test_mock_adapter_not_referenced_in_cli_module_source():
    cli_source = (Path(__file__).resolve().parents[1] / "src" / "pcae" / "cli.py").read_text()
    for forbidden in ("mock_runtime_adapter", "mock-dry", "simulate_invocation", "MockDryRuntimeAdapter"):
        assert forbidden not in cli_source, f"{forbidden!r} must not be exposed via the public CLI yet"
