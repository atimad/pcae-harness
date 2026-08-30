"""
Runtime Adapter Interface and Simulation Coordinator — Phase 149O.20L.7O.3S.

Implements the RPAC-001 v1.0 (docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md)
mock-v1 target configuration, dynamic status, the frozen five-operation
adapter Protocol (RPAC-REQ-031), the explicit no-fallback resolver
(RPAC-REQ-053), and `simulate_invocation()` -- the trusted-kernel-side
coordinator that runs the mock-v1 gate sequence (3R plan §23) in frozen
order and calls exactly one explicitly selected, already-registered mock
adapter.

The coordinator owns record persistence, gate ordering, and intake
handoff; it never delegates authority to the adapter (RPAC-REQ-034). It
imports the existing `PermissionBroker` in `simulation_only=True` mode
only, and never touches Permission Broker policy, Runtime Enforcement
production models, Shell Gate, or any credential/network/subprocess
surface. Nothing in this module can make `pcae runtime inspect` report
real execution availability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from .permission_broker_foundation import (
    ACTION_ADAPTER_INVOCATION,
    EXECUTION_CLASS_ADAPTER,
    PermissionBroker,
    build_permission_broker_request,
)
from . import intake as intake_module
from .runtime_invocation import (
    SIM_APPROVAL_BOUND,
    SIM_CAPABLE,
    SIM_COMPLETED,
    SIM_DISPATCH_INTENT,
    SIM_DISPATCHED,
    SIM_ENFORCEMENT_EVALUATED,
    SIM_FRESH,
    SIM_INTAKE_CANDIDATE_BUILT,
    SIM_PB_EVALUATED,
    SIM_PREPARED,
    SIM_RESULT_CAPTURED,
    AuthoritySnapshot,
    Clock,
    FAILURE_ENFORCEMENT_DENIED,
    FAILURE_MALFORMED_RESULT,
    FAILURE_NO_ADAPTER_CONFIGURED,
    FAILURE_PERMISSION_DENIED,
    FAILURE_UNSUPPORTED_CAPABILITY,
    InvocationRequest,
    RuntimeInvocationResult,
    RuntimeInvocationStore,
    SimulationApprovalEvidence,
    SimulationDispatchEnvelope,
    SimulationEnforcementEvaluator,
    SimulationEnforcementObservation,
    approval_binding_issues,
    build_dispatch_envelope,
    derive_intake_candidate_id,
    next_state_observation,
    validate_dispatch_envelope,
)
from .runtime_registry import RuntimeDescriptor, RuntimeRegistry

_ = AuthoritySnapshot  # re-exported for callers that import from this module


# ═══════════════════════════════════════════════════════════════════════
# Target configuration (RPAC-REQ-013)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RuntimeTargetConfiguration:
    """Minimal mock-v1 `RuntimeTargetConfiguration` projection
    (RPAC-REQ-013). Real command/endpoint/process-supervision fields are
    Real-Runtime-Prerequisite and absent by design; `fixture_name`
    selects the exact deterministic response scenario."""

    runtime_target_id: str
    config_version: str
    adapter_id: str
    fixture_name: str
    enabled: bool = True

    def digest(self) -> str:
        import hashlib
        import json

        return hashlib.sha256(
            json.dumps(
                {
                    "runtime_target_id": self.runtime_target_id,
                    "config_version": self.config_version,
                    "adapter_id": self.adapter_id,
                    "fixture_name": self.fixture_name,
                    "enabled": self.enabled,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Dynamic status (RPAC-REQ-015/016/017)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RuntimeStatus:
    """Dynamic, timestamped facts only (RPAC-REQ-015). No approval,
    Permission Broker permission, Runtime Enforcement authorization, or
    dispatch fact ever appears here (RPAC-REQ-016). `real_execution_available`
    is hard-fixed `False` for every mock-v1 status; `simulation_ready` is
    a distinct, non-collapsing term (RPAC-REQ-017)."""

    runtime_target_id: str
    adapter_id: str
    descriptor_digest: str
    registered: bool
    installed: bool
    configured: bool
    authentication: str  # "not_required" for mock-v1
    simulation_ready: bool
    health: str  # "healthy" | "unhealthy" | "unknown"
    observed_capabilities: tuple[str, ...]
    real_execution_available: bool
    source: str
    observed_at: str

    def __post_init__(self) -> None:
        if self.real_execution_available:
            raise ValueError("mock_v1_status_must_report_real_execution_unavailable")

    def digest(self) -> str:
        import hashlib
        import json

        return hashlib.sha256(
            json.dumps(
                {
                    "runtime_target_id": self.runtime_target_id,
                    "adapter_id": self.adapter_id,
                    "descriptor_digest": self.descriptor_digest,
                    "registered": self.registered,
                    "installed": self.installed,
                    "configured": self.configured,
                    "authentication": self.authentication,
                    "simulation_ready": self.simulation_ready,
                    "health": self.health,
                    "observed_capabilities": list(self.observed_capabilities),
                    "real_execution_available": self.real_execution_available,
                    "source": self.source,
                    "observed_at": self.observed_at,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()


def build_mock_status(
    *, descriptor: RuntimeDescriptor, config: RuntimeTargetConfiguration, clock: Clock
) -> RuntimeStatus:
    return RuntimeStatus(
        runtime_target_id=config.runtime_target_id,
        adapter_id=descriptor.adapter_id,
        descriptor_digest=descriptor.catalog_digest(),
        registered=True,
        installed=True,
        configured=config.enabled,
        authentication="not_required",
        simulation_ready=config.enabled,
        health="healthy" if config.enabled else "unknown",
        observed_capabilities=descriptor.supported_capabilities,
        real_execution_available=False,
        source="mock_v1_fixed_fixture",
        observed_at=clock(),
    )


# ═══════════════════════════════════════════════════════════════════════
# Adapter Protocol (RPAC-REQ-031/032) — exactly five operations
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AdapterPreflightResult:
    capable: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class DispatchReceipt:
    invocation_id: str
    attempt_id: str
    accepted: bool
    simulation_only: bool = True


@dataclass(frozen=True)
class RuntimeCancellationResult:
    attempt_id: str
    outcome: str  # "completed_before_cancel" | "unsupported" | "unknown_attempt"


@runtime_checkable
class RuntimeAdapter(Protocol):
    """The frozen v1 adapter interface (RPAC-REQ-031). Exactly these five
    operations -- no authorization, approval, Permission Broker, Runtime
    Enforcement, intake, promotion, commit, push, or task-outcome method
    exists on this Protocol (RPAC-REQ-001/003), and no implementation of
    it may add one and still satisfy `test_adapter_surface_has_no_authority_methods`."""

    def describe(self) -> RuntimeDescriptor: ...

    def preflight(self, request: InvocationRequest) -> AdapterPreflightResult: ...

    def dispatch(self, envelope: SimulationDispatchEnvelope) -> DispatchReceipt: ...

    def collect(self, attempt_id: str) -> "RuntimeInvocationResult": ...

    def cancel(self, attempt_id: str) -> RuntimeCancellationResult: ...


_FORBIDDEN_ADAPTER_PROTOCOL_METHODS: frozenset[str] = frozenset(
    {
        "approve",
        "authorize",
        "permit",
        "enforce",
        "ingest",
        "promote",
        "commit",
        "push",
        "complete_task",
        "grant_permission",
    }
)


def adapter_protocol_operation_names() -> frozenset[str]:
    return frozenset({"describe", "preflight", "dispatch", "collect", "cancel"})


# ═══════════════════════════════════════════════════════════════════════
# Explicit resolver — no fallback (RPAC-REQ-053)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ResolvedTarget:
    descriptor: RuntimeDescriptor
    config: RuntimeTargetConfiguration
    adapter: RuntimeAdapter


@dataclass(frozen=True)
class ResolutionFailure:
    runtime_target_id: str
    category: str
    reasons: tuple[str, ...]


class RuntimeAdapterResolver:
    """Composes the canonical `RuntimeRegistry` adapter catalog with an
    explicit target-configuration table and a trusted-kernel-held
    callable-instance table (RPAC-REQ-050/053). There is no priority
    fallback, provider fallback, model fallback, or agent-name fallback:
    `resolve_exact` takes only an explicit `runtime_target_id`."""

    def __init__(self, registry: RuntimeRegistry):
        self._registry = registry
        self._targets: dict[str, RuntimeTargetConfiguration] = {}
        self._adapter_instances: dict[str, RuntimeAdapter] = {}

    def register_target(self, config: RuntimeTargetConfiguration) -> None:
        if config.runtime_target_id in self._targets:
            raise ValueError(f"duplicate_runtime_target_id:{config.runtime_target_id}")
        self._targets[config.runtime_target_id] = config

    def register_adapter_instance(self, adapter_id: str, adapter: RuntimeAdapter) -> None:
        if adapter_id in self._adapter_instances:
            raise ValueError(f"duplicate_adapter_instance:{adapter_id}")
        self._adapter_instances[adapter_id] = adapter

    def resolve_exact(self, runtime_target_id: str) -> ResolvedTarget | ResolutionFailure:
        config = self._targets.get(runtime_target_id)
        if config is None:
            return ResolutionFailure(
                runtime_target_id, FAILURE_NO_ADAPTER_CONFIGURED, ("unknown_runtime_target",)
            )
        descriptor = self._registry.get_adapter_descriptor(config.adapter_id)
        if descriptor is None:
            return ResolutionFailure(
                runtime_target_id, FAILURE_NO_ADAPTER_CONFIGURED, ("unregistered_adapter",)
            )
        adapter = self._adapter_instances.get(config.adapter_id)
        if adapter is None:
            return ResolutionFailure(
                runtime_target_id, FAILURE_NO_ADAPTER_CONFIGURED, ("no_callable_instance",)
            )
        live_descriptor = adapter.describe()
        if live_descriptor.catalog_digest() != descriptor.catalog_digest():
            return ResolutionFailure(
                runtime_target_id, FAILURE_NO_ADAPTER_CONFIGURED, ("descriptor_digest_drift",)
            )
        return ResolvedTarget(descriptor=descriptor, config=config, adapter=adapter)


# ═══════════════════════════════════════════════════════════════════════
# Capability/effect matching (RPAC-REQ-019)
# ═══════════════════════════════════════════════════════════════════════


def validate_request_against_target(
    request: InvocationRequest, descriptor: RuntimeDescriptor, config: RuntimeTargetConfiguration
) -> tuple[str, ...]:
    issues: list[str] = []
    if request.expected_adapter_id != descriptor.adapter_id:
        issues.append(FAILURE_NO_ADAPTER_CONFIGURED + ":adapter_id_mismatch")
    if request.descriptor_digest != descriptor.catalog_digest():
        issues.append(FAILURE_NO_ADAPTER_CONFIGURED + ":descriptor_digest_mismatch")
    if request.target_config_digest != config.digest():
        issues.append(FAILURE_NO_ADAPTER_CONFIGURED + ":config_digest_mismatch")
    if request.requested_capability not in descriptor.supported_capabilities:
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":capability_not_supported")
    if request.expected_result_format not in descriptor.supported_result_formats:
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":result_format_not_supported")
    if not request.effect_profile.is_all_denied_zero():
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":effect_profile_not_none")
    if descriptor.execution_effect != "none":
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":descriptor_execution_effect_not_none")
    if not config.enabled:
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":target_disabled")
    return tuple(issues)


# ═══════════════════════════════════════════════════════════════════════
# Simulation outcome + coordinator (RPAC-REQ-002/042/043)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SimulationOutcome:
    accepted: bool
    final_state: str
    result: "RuntimeInvocationResult | None"
    failure_category: str | None
    failure_reasons: tuple[str, ...]
    adapter_call_count: int
    trace: tuple[str, ...]


def simulate_invocation(
    *,
    request: InvocationRequest,
    prompt_digest: str,
    approval: SimulationApprovalEvidence,
    resolver: RuntimeAdapterResolver,
    store: RuntimeInvocationStore,
    clock: Clock,
    enforcement_evaluator: SimulationEnforcementEvaluator | None = None,
    permission_broker: PermissionBroker | None = None,
) -> SimulationOutcome:
    """Run the mock-v1 gate sequence (3R plan §23) in frozen order,
    stopping at the first failed gate (RPAC-REQ-002/043) with the adapter
    call counter left at zero. Only step 8 (the in-process mock dispatch)
    may call the adapter, and only after every earlier step accepted.
    """
    trace: list[str] = []
    adapter_calls = 0
    enforcement_evaluator = enforcement_evaluator or SimulationEnforcementEvaluator()
    permission_broker = permission_broker or PermissionBroker()

    store.create_request_record(request)
    observation = next_state_observation(None, SIM_PREPARED, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_PREPARED)

    binding_issues = approval_binding_issues(
        approval,
        prompt=_SimpleNamespace(content_digest=prompt_digest),  # type: ignore[arg-type]
        authority=_SimpleNamespace(
            repository_id=request.repository_id, task_id=request.task_id
        ),  # type: ignore[arg-type]
        runtime_target_id=request.runtime_target_id,
        effect_profile_digest=request.effect_profile.digest(),
    )
    if binding_issues:
        return _fail(
            trace, adapter_calls, "invalid_request", binding_issues, observation.state
        )
    observation = next_state_observation(observation, SIM_APPROVAL_BOUND, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_APPROVAL_BOUND)

    resolved = resolver.resolve_exact(request.runtime_target_id)
    if isinstance(resolved, ResolutionFailure):
        return _fail(trace, adapter_calls, resolved.category, resolved.reasons, observation.state)

    preflight_issues = validate_request_against_target(request, resolved.descriptor, resolved.config)
    if preflight_issues:
        return _fail(
            trace, adapter_calls, FAILURE_UNSUPPORTED_CAPABILITY, preflight_issues, observation.state
        )
    preflight = resolved.adapter.preflight(request)
    if not preflight.capable:
        return _fail(
            trace, adapter_calls, FAILURE_UNSUPPORTED_CAPABILITY, preflight.reasons, observation.state
        )
    status = build_mock_status(descriptor=resolved.descriptor, config=resolved.config, clock=clock)
    observation = next_state_observation(observation, SIM_CAPABLE, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_CAPABLE)

    pb_request = build_permission_broker_request(
        action_type=ACTION_ADAPTER_INVOCATION,
        execution_class=EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006",
        requested_capability=request.requested_capability,
        task_id=request.task_id,
        phase_id=request.phase_id,
        evidence_available=True,
        approval_present=True,
        simulation_only=True,
    )
    pb_decision = permission_broker.evaluate(pb_request)
    pb_would_allow = pb_decision.decision == "ALLOW"
    if not pb_would_allow:
        return _fail(
            trace, adapter_calls, FAILURE_PERMISSION_DENIED,
            (pb_decision.decision_reason,), observation.state,
        )
    observation = next_state_observation(
        observation, SIM_PB_EVALUATED, clock(), {"pb_decision": pb_decision.decision}
    )
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_PB_EVALUATED)

    freshness_ok = (
        request.descriptor_digest == resolved.descriptor.catalog_digest()
        and request.target_config_digest == resolved.config.digest()
    )
    if not freshness_ok:
        return _fail(
            trace, adapter_calls, "integrity_failure", ("stale_descriptor_or_config",), observation.state
        )
    observation = next_state_observation(observation, SIM_FRESH, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_FRESH)

    enforcement = enforcement_evaluator.evaluate(
        pb_would_allow=pb_would_allow, approval_binding_ok=True, freshness_ok=freshness_ok
    )
    if enforcement.outcome != "would_allow_simulation":
        return _fail(
            trace, adapter_calls, FAILURE_ENFORCEMENT_DENIED, (enforcement.outcome,), observation.state
        )
    observation = next_state_observation(
        observation, SIM_ENFORCEMENT_EVALUATED, clock(), {"outcome": enforcement.outcome}
    )
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_ENFORCEMENT_EVALUATED)

    pb_decision_digest = pb_decision.decision
    if pb_decision.causing_policy_id:
        pb_decision_digest = f"{pb_decision.decision}:{pb_decision.causing_policy_id}"
    envelope = build_dispatch_envelope(
        request=request,
        target_status_digest=status.digest(),
        pb_decision_digest=pb_decision_digest,
        enforcement_digest=enforcement.evidence_digest,
        record_reference=f"{request.invocation_id}/{request.attempt_id}",
        clock=clock,
    )
    envelope_issues = validate_dispatch_envelope(envelope, expected_request=request)
    if envelope_issues:
        return _fail(trace, adapter_calls, "integrity_failure", envelope_issues, observation.state)

    observation = next_state_observation(observation, SIM_DISPATCH_INTENT, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_DISPATCH_INTENT)

    try:
        receipt = resolved.adapter.dispatch(envelope)
    except Exception as exc:  # noqa: BLE001 - adapter is untrusted; fail closed
        return _fail(
            trace, adapter_calls, FAILURE_MALFORMED_RESULT,
            (f"dispatch_raised:{type(exc).__name__}",), observation.state,
        )
    adapter_calls += 1
    if not isinstance(receipt, DispatchReceipt) or not getattr(receipt, "accepted", False):
        return _fail(
            trace, adapter_calls, FAILURE_MALFORMED_RESULT, ("dispatch_not_accepted",), observation.state
        )
    observation = next_state_observation(observation, SIM_DISPATCHED, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_DISPATCHED)

    try:
        result = resolved.adapter.collect(request.attempt_id)
    except Exception as exc:  # noqa: BLE001 - adapter is untrusted; fail closed
        return _fail(
            trace, adapter_calls, FAILURE_MALFORMED_RESULT,
            (f"collect_raised:{type(exc).__name__}",), observation.state,
        )
    malformed_reasons = malformed_adapter_result_reasons(result, request)
    if malformed_reasons:
        # 3S.2.1 MUST-FIX #1: a non-conforming adapter.collect() return
        # (e.g. a plain dict, wrong ids, wrong effect, an exception) fails
        # closed with a clean FAILURE_MALFORMED_RESULT SimulationOutcome
        # BEFORE any state transition or store.write_result() -- never an
        # uncaught AttributeError inside the store, and never a persisted
        # result.json / intake-handoff.json.
        return _fail(
            trace, adapter_calls, FAILURE_MALFORMED_RESULT, malformed_reasons, observation.state
        )
    observation = next_state_observation(observation, SIM_COMPLETED, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_COMPLETED)

    store.write_result(request.invocation_id, request.attempt_id, result)
    observation = next_state_observation(observation, SIM_RESULT_CAPTURED, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_RESULT_CAPTURED)

    handoff = build_intake_handoff(result, authority_repo_binding=(
        request.repository_fingerprint, request.base_commit, request.task_id
    ))
    store.write_intake_handoff(request.invocation_id, request.attempt_id, handoff)
    observation = next_state_observation(observation, SIM_INTAKE_CANDIDATE_BUILT, clock())
    store.append_event(request.invocation_id, request.attempt_id, observation)
    trace.append(SIM_INTAKE_CANDIDATE_BUILT)

    return SimulationOutcome(
        accepted=True,
        final_state=SIM_RESULT_CAPTURED,
        result=result,
        failure_category=None,
        failure_reasons=(),
        adapter_call_count=adapter_calls,
        trace=tuple(trace),
    )


def build_intake_handoff(
    result: RuntimeInvocationResult,
    *,
    authority_repo_binding: tuple[str, str, str],
) -> dict:
    """Map a normalized `RuntimeInvocationResult` to the existing
    producer-neutral generic intake candidate shape (RPAC-REQ-080, Stage
    B, 3R plan §20). Never calls `validate_and_ingest_intake_candidate`;
    the resulting document is Stage-B evidence only. A text-only,
    no-change result returns the explicit `not_applicable_no_changes`
    disposition instead of a fabricated candidate (RPAC-REQ-081)."""
    repository_fingerprint, base_commit, task_id = authority_repo_binding
    changed_files = [
        {
            "path": entry.path,
            "operation": entry.operation,
            "content_after": entry.content_after,
            "content_hash_after": entry.content_hash_after,
        }
        for entry in result.changed_files
    ]
    candidate_id = derive_intake_candidate_id(
        result.invocation_id, result.attempt_id, result.result_digest
    )
    return intake_module.build_intake_candidate_from_changes(
        repository_fingerprint=repository_fingerprint,
        base_commit=base_commit,
        task_id=task_id,
        candidate_id=candidate_id,
        changed_files=changed_files,
        producer_kind=result.requesting_agent_id,
        producer_source="rpac_runtime_adapter",
        summary=str(result.structured_payload.get("message", "")),
        adapter_version=f"{result.adapter_id}/1.0",
    )


#: The terminal outcomes a conforming mock-v1 `RuntimeInvocationResult`
#: may carry (`accepted`/`terminal_outcome` are distinct axes -- a
#: `failure` content outcome is still a well-formed, accepted simulation).
_KNOWN_TERMINAL_OUTCOMES: frozenset[str] = frozenset({"success", "failure"})


def malformed_adapter_result_reasons(
    result: object, request: InvocationRequest
) -> tuple[str, ...]:
    """3S.2.1 MUST-FIX #1 — strict, fail-closed validation of an
    `adapter.collect()` return before `store.write_result()` is ever
    reached (RPAC-REQ-035/036/037; RDGO-001 v3.1 §12 "Malformed output
    fails closed and must never be persisted as a successful result").

    Returns an empty tuple for a conforming `RuntimeInvocationResult`
    bound to exactly this request, or a tuple of stable reason stems
    otherwise. Never raises. Acceptance is NOT loosened to preserve an
    old test: a plain `dict`, a wrong-id result, a non-simulation result,
    an effecting result, an unknown terminal outcome, or a structurally
    incomplete result all fail closed here."""
    reasons: list[str] = []
    if not isinstance(result, RuntimeInvocationResult):
        return (f"not_a_runtime_invocation_result:{type(result).__name__}",)
    if result.invocation_id != request.invocation_id:
        reasons.append("invocation_id_mismatch")
    if result.attempt_id != request.attempt_id:
        reasons.append("attempt_id_mismatch")
    if result.idempotency_key != request.idempotency_key:
        reasons.append("idempotency_key_mismatch")
    if result.contract_version != request.contract_version:
        reasons.append("contract_version_mismatch")
    if result.runtime_target_id != request.runtime_target_id:
        reasons.append("runtime_target_id_mismatch")
    if result.simulation_only is not True:
        reasons.append("not_simulation_only")
    if result.execution_effect != "none":
        reasons.append("execution_effect_not_none")
    if result.untrusted is not True:
        reasons.append("result_not_untrusted")
    if result.terminal_outcome not in _KNOWN_TERMINAL_OUTCOMES:
        reasons.append("unknown_terminal_outcome")
    if not isinstance(result.result_digest, str) or not result.result_digest:
        reasons.append("missing_result_digest")
    if not isinstance(result.payload_digest, str) or not result.payload_digest:
        reasons.append("missing_payload_digest")
    if not isinstance(result.structured_payload, Mapping):
        reasons.append("structured_payload_not_mapping")
    if not isinstance(result.changed_files, tuple):
        reasons.append("changed_files_not_tuple")
    return tuple(reasons)


def _fail(
    trace: list[str], adapter_calls: int, category: str, reasons: tuple[str, ...], last_state: str
) -> SimulationOutcome:
    return SimulationOutcome(
        accepted=False,
        final_state=last_state,
        result=None,
        failure_category=category,
        failure_reasons=reasons,
        adapter_call_count=adapter_calls,
        trace=tuple(trace),
    )


class _SimpleNamespace:
    """A minimal duck-typed stand-in used only to reuse
    `approval_binding_issues()`'s attribute-based comparison without
    constructing a full `PromptArtifact`/`AuthoritySnapshot` from
    already-digested request fields."""

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
