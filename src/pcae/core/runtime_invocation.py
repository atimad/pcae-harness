"""
Runtime Invocation — Phase 149O.20L.7O.3S.

Implements the RPAC-001 v1.0 (docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md)
mock-v1 invocation data/lifecycle boundary: `PromptArtifact`, simulation
approval evidence, the trusted `AuthoritySnapshot`, the immutable
`InvocationRequest`, the `SimulationDispatchEnvelope`, the normalized
`RuntimeInvocationResult`, append-only simulation state observations, and
the persistent `RuntimeInvocationStore`.

This module is a pure data/persistence boundary. It imports no
`subprocess`, `socket`, `os.environ`, provider SDK, or execution-adjacent
module, and it never reads a live git/OS clock itself — every timestamp is
supplied by an injected clock so behavior is deterministic and testable.
It never calls a `RuntimeAdapter`; orchestration lives in
`runtime_adapter.py`.

Every persisted document is immutable, canonical-JSON-serializable, and
digest-bearing. Only the exact tree

    .pcae/runtime-invocations/mock-v1/<invocation_id>/

is ever written. Nothing here has any effect on `pcae runtime inspect`,
Permission Broker policy, Runtime Enforcement, or canonical execution
availability, which remain Observed/observe/unavailable throughout.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    require_safe_relative_id_component,
)

Clock = Callable[[], str]
"""An injected clock: a zero-argument callable returning a fixed,
deterministic ISO-8601 UTC timestamp string. No function in this module
reads the wall clock directly."""

CONTRACT_VERSION = "RPAC-001/1.0"
SUPPORTED_CONTRACT_MAJORS: frozenset[str] = frozenset({"RPAC-001/1.0"})


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def new_invocation_id() -> str:
    """An opaque, cryptographically strong logical invocation identity
    (RPAC-REQ-064). Never derived from a mutable timestamp alone."""
    return f"inv-{uuid.uuid4().hex}"


def new_attempt_id() -> str:
    """A unique attempt identity for one dispatch try (RPAC-REQ-064)."""
    return f"att-{uuid.uuid4().hex}"


def is_valid_generated_id(value: object, *, prefix: str) -> bool:
    if not isinstance(value, str) or not value.startswith(f"{prefix}-"):
        return False
    suffix = value[len(prefix) + 1 :]
    return len(suffix) == 32 and all(c in "0123456789abcdef" for c in suffix)


# ═══════════════════════════════════════════════════════════════════════
# Failure taxonomy (RPAC-REQ-073/074)
# ═══════════════════════════════════════════════════════════════════════

FAILURE_NO_ADAPTER_CONFIGURED = "no_adapter_configured"
FAILURE_UNSUPPORTED_CAPABILITY = "unsupported_capability"
FAILURE_PERMISSION_DENIED = "permission_denied"
FAILURE_ENFORCEMENT_DENIED = "enforcement_denied"
FAILURE_DISPATCH_ERROR = "dispatch_error"
FAILURE_RUNTIME_FAILURE = "runtime_failure"
FAILURE_MALFORMED_RESULT = "malformed_result"
FAILURE_RESULT_INGESTION_FAILURE = "result_ingestion_failure"
FAILURE_INTEGRITY_FAILURE = "integrity_failure"
FAILURE_SIMULATION_AMBIGUOUS = "simulation_ambiguous"
FAILURE_INVALID_REQUEST = "invalid_request"

COMMON_FAILURE_CATEGORIES: frozenset[str] = frozenset(
    {
        FAILURE_NO_ADAPTER_CONFIGURED,
        FAILURE_UNSUPPORTED_CAPABILITY,
        FAILURE_PERMISSION_DENIED,
        FAILURE_ENFORCEMENT_DENIED,
        FAILURE_DISPATCH_ERROR,
        FAILURE_RUNTIME_FAILURE,
        FAILURE_MALFORMED_RESULT,
        FAILURE_RESULT_INGESTION_FAILURE,
    }
)
ADDITIVE_FAILURE_CATEGORIES: frozenset[str] = frozenset(
    {FAILURE_INTEGRITY_FAILURE, FAILURE_SIMULATION_AMBIGUOUS, FAILURE_INVALID_REQUEST}
)
ALL_FAILURE_CATEGORIES: frozenset[str] = COMMON_FAILURE_CATEGORIES | ADDITIVE_FAILURE_CATEGORIES


# ═══════════════════════════════════════════════════════════════════════
# Simulation state model (RPAC-REQ-039/040/041)
# ═══════════════════════════════════════════════════════════════════════

SIM_PREPARED = "SIM_PREPARED"
SIM_APPROVAL_BOUND = "SIM_APPROVAL_BOUND"
SIM_CAPABLE = "SIM_CAPABLE"
SIM_PB_EVALUATED = "SIM_PB_EVALUATED"
SIM_FRESH = "SIM_FRESH"
SIM_ENFORCEMENT_EVALUATED = "SIM_ENFORCEMENT_EVALUATED"
SIM_DISPATCH_INTENT = "SIM_DISPATCH_INTENT"
SIM_DISPATCHED = "SIM_DISPATCHED"
SIM_COMPLETED = "SIM_COMPLETED"
SIM_RESULT_CAPTURED = "SIM_RESULT_CAPTURED"
SIM_INTAKE_CANDIDATE_BUILT = "SIM_INTAKE_CANDIDATE_BUILT"

SIMULATION_STATE_ORDER: tuple[str, ...] = (
    SIM_PREPARED,
    SIM_APPROVAL_BOUND,
    SIM_CAPABLE,
    SIM_PB_EVALUATED,
    SIM_FRESH,
    SIM_ENFORCEMENT_EVALUATED,
    SIM_DISPATCH_INTENT,
    SIM_DISPATCHED,
    SIM_COMPLETED,
    SIM_RESULT_CAPTURED,
    SIM_INTAKE_CANDIDATE_BUILT,
)

#: Production runtime semantic states (RPAC-REQ-039) that mock-v1 SHALL
#: NEVER emit (RPAC-REQ-041). Kept here only as a negative-assertion
#: fixture for tests -- this module has no code path that can write one.
PRODUCTION_STATES_FORBIDDEN_IN_MOCK: frozenset[str] = frozenset(
    {
        "PREPARED",
        "APPROVED",
        "CAPABLE",
        "PERMITTED",
        "AUTHORIZED",
        "DISPATCHED",
        "ACCEPTED",
        "RUNNING",
        "COMPLETED",
        "RESULT_CAPTURED",
        "INGESTED",
    }
)


@dataclass(frozen=True)
class SimulationStateObservation:
    """One append-only, chained simulation-lifecycle observation
    (RPAC-REQ-040). `sequence` is 1-based and `prior_digest` chains to the
    previous observation's own digest (or `None` for the first), so any
    reordering or tampering is detectable independent of storage."""

    sequence: int
    state: str
    observed_at: str
    prior_digest: str | None
    detail: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in SIMULATION_STATE_ORDER:
            raise ValueError(f"not_a_simulation_state:{self.state}")
        object.__setattr__(self, "detail", dict(self.detail))

    def digest(self) -> str:
        return _digest(
            {
                "sequence": self.sequence,
                "state": self.state,
                "observed_at": self.observed_at,
                "prior_digest": self.prior_digest,
                "detail": self.detail,
            }
        )


def next_state_observation(
    prior: SimulationStateObservation | None,
    state: str,
    observed_at: str,
    detail: Mapping[str, object] | None = None,
) -> SimulationStateObservation:
    """Append one state observation after `prior` (or the first if
    `prior is None`), enforcing frozen forward order (RPAC-REQ-039/040):
    the new state's index must be strictly greater than the prior
    state's index -- no skipping backward, no repeats out of order."""
    if prior is None:
        if state != SIM_PREPARED:
            raise ValueError("first_state_must_be_sim_prepared")
        return SimulationStateObservation(
            sequence=1, state=state, observed_at=observed_at,
            prior_digest=None, detail=detail or {},
        )
    prior_index = SIMULATION_STATE_ORDER.index(prior.state)
    new_index = SIMULATION_STATE_ORDER.index(state)
    if new_index <= prior_index:
        raise ValueError(f"out_of_order_state:{prior.state}->{state}")
    return SimulationStateObservation(
        sequence=prior.sequence + 1, state=state, observed_at=observed_at,
        prior_digest=prior.digest(), detail=detail or {},
    )


# ═══════════════════════════════════════════════════════════════════════
# Authority snapshot (RPAC-REQ-078) — trusted-kernel-only construction
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AuthoritySnapshot:
    """Repository/task/session binding derived by the trusted coordinator
    from PCAE-owned state, never from adapter/runtime/result input
    (RPAC-REQ-078). Mock-v1 unit/integration/E2E tests construct this from
    controlled fixtures; a live builder reading real git/task state is
    explicitly deferred (3R §22) because existing generic-intake HEAD
    helpers invoke `git` subprocesses, which would violate this module's
    zero-process guarantee."""

    repository_id: str
    repository_fingerprint: str
    base_commit: str
    task_id: str
    task_contract_digest: str
    phase_id: str | None = None
    session_id: str | None = None


# ═══════════════════════════════════════════════════════════════════════
# PromptArtifact (RPAC-REQ-020/021)
# ═══════════════════════════════════════════════════════════════════════

PROMPT_ARTIFACT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class PromptArtifact:
    schema_version: str
    artifact_id: str
    content: str
    content_digest: str
    generation_method: str
    generation_version: str
    repository_id: str
    task_id: str
    phase_id: str | None
    created_at: str
    provenance: tuple[str, ...]
    human_edited: bool
    target_agent_hint: str | None = None
    """Non-binding hint only (RPAC-REQ-021) -- never consulted for target
    selection anywhere in this module."""


def build_prompt_artifact(
    *,
    content: str,
    generation_method: str,
    generation_version: str,
    authority: AuthoritySnapshot,
    clock: Clock,
    provenance: tuple[str, ...] = (),
    human_edited: bool = False,
    target_agent_hint: str | None = None,
) -> PromptArtifact:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    artifact_id = f"prompt-{uuid.uuid4().hex}"
    return PromptArtifact(
        schema_version=PROMPT_ARTIFACT_SCHEMA_VERSION,
        artifact_id=artifact_id,
        content=content,
        content_digest=digest,
        generation_method=generation_method,
        generation_version=generation_version,
        repository_id=authority.repository_id,
        task_id=authority.task_id,
        phase_id=authority.phase_id,
        created_at=clock(),
        provenance=tuple(provenance),
        human_edited=human_edited,
        target_agent_hint=target_agent_hint,
    )


# ═══════════════════════════════════════════════════════════════════════
# Simulation approval evidence (RPAC-REQ-022/023/024)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SimulationApprovalEvidence:
    """A test/simulation stand-in for a real `InvocationApproval`
    (RPAC-REQ-022). It binds the exact prompt digest, repository/task,
    runtime target, and effect profile it approves. It is NOT a
    production human-approval artifact and SHALL NOT be treated as one;
    that remains an explicit real-runtime prerequisite (Matrix E)."""

    approval_id: str
    bound_prompt_digest: str
    bound_repository_id: str
    bound_task_id: str
    bound_runtime_target_id: str
    bound_effect_profile_digest: str
    created_at: str
    simulation_only: bool = True

    def __post_init__(self) -> None:
        if not self.simulation_only:
            raise ValueError("simulation_approval_must_be_simulation_only")


def build_simulation_approval_evidence(
    *,
    prompt: PromptArtifact,
    authority: AuthoritySnapshot,
    runtime_target_id: str,
    effect_profile_digest: str,
    clock: Clock,
) -> SimulationApprovalEvidence:
    return SimulationApprovalEvidence(
        approval_id=f"sim-approval-{uuid.uuid4().hex}",
        bound_prompt_digest=prompt.content_digest,
        bound_repository_id=authority.repository_id,
        bound_task_id=authority.task_id,
        bound_runtime_target_id=runtime_target_id,
        bound_effect_profile_digest=effect_profile_digest,
        created_at=clock(),
    )


def approval_binding_issues(
    approval: SimulationApprovalEvidence,
    *,
    prompt: PromptArtifact,
    authority: AuthoritySnapshot,
    runtime_target_id: str,
    effect_profile_digest: str,
) -> tuple[str, ...]:
    """Every mismatch between the approval's bound scope and the current
    request scope (RPAC-REQ-023): a changed prompt, target,
    repository/task, or effect profile invalidates the approval."""
    issues: list[str] = []
    if approval.bound_prompt_digest != prompt.content_digest:
        issues.append("approval_prompt_digest_mismatch")
    if approval.bound_repository_id != authority.repository_id:
        issues.append("approval_repository_mismatch")
    if approval.bound_task_id != authority.task_id:
        issues.append("approval_task_mismatch")
    if approval.bound_runtime_target_id != runtime_target_id:
        issues.append("approval_target_mismatch")
    if approval.bound_effect_profile_digest != effect_profile_digest:
        issues.append("approval_effect_profile_mismatch")
    return tuple(issues)


# ═══════════════════════════════════════════════════════════════════════
# Effect profile (RPAC-REQ-027/061/085) — default-deny, closed
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class EffectProfile:
    network_allowed: bool = False
    repository_write_allowed: bool = False
    temp_write_allowed: bool = False
    outside_repository_allowed: bool = False
    process_allowed: bool = False
    paid_budget_cents: int = 0

    def digest(self) -> str:
        return _digest(
            {
                "network_allowed": self.network_allowed,
                "repository_write_allowed": self.repository_write_allowed,
                "temp_write_allowed": self.temp_write_allowed,
                "outside_repository_allowed": self.outside_repository_allowed,
                "process_allowed": self.process_allowed,
                "paid_budget_cents": self.paid_budget_cents,
            }
        )

    def is_all_denied_zero(self) -> bool:
        return (
            not self.network_allowed
            and not self.repository_write_allowed
            and not self.temp_write_allowed
            and not self.outside_repository_allowed
            and not self.process_allowed
            and self.paid_budget_cents == 0
        )


MOCK_DRY_EFFECT_PROFILE = EffectProfile()
"""The only effect profile mock-v1 ever constructs: every effect denied,
zero budget (RPAC-REQ-027/061/085). `build_invocation_request` rejects any
other profile with `unsupported_capability`."""


# ═══════════════════════════════════════════════════════════════════════
# Invocation request (RPAC-REQ-025/026/028)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class InvocationRequest:
    contract_version: str
    invocation_id: str
    attempt_id: str
    idempotency_key: str
    repository_id: str
    repository_fingerprint: str
    base_commit: str
    task_id: str
    task_contract_digest: str
    requester_agent_id: str
    runtime_target_id: str
    expected_adapter_id: str
    descriptor_digest: str
    target_config_digest: str
    prompt_artifact_id: str
    prompt_digest: str
    approval_id: str
    approval_digest: str
    requested_capability: str
    expected_result_format: str
    working_directory: str
    effect_profile: EffectProfile
    timeout_seconds: int
    cancellation_required: bool
    provider_id: str | None = None
    model_id: str | None = None
    phase_id: str | None = None
    session_id: str | None = None

    def canonical_projection(self) -> dict:
        """The canonical, version-tagged content used for the idempotency
        digest (RPAC-REQ-065): excludes `attempt_id` and any mutable
        observation, includes everything that defines *what* is being
        requested."""
        return {
            "contract_version": self.contract_version,
            "invocation_id": self.invocation_id,
            "repository_id": self.repository_id,
            "repository_fingerprint": self.repository_fingerprint,
            "base_commit": self.base_commit,
            "task_id": self.task_id,
            "task_contract_digest": self.task_contract_digest,
            "runtime_target_id": self.runtime_target_id,
            "expected_adapter_id": self.expected_adapter_id,
            "descriptor_digest": self.descriptor_digest,
            "target_config_digest": self.target_config_digest,
            "prompt_digest": self.prompt_digest,
            "approval_digest": self.approval_digest,
            "requested_capability": self.requested_capability,
            "expected_result_format": self.expected_result_format,
            "working_directory": self.working_directory,
            "effect_profile": self.effect_profile.digest(),
            "provider_id": self.provider_id,
            "model_id": self.model_id,
        }


def compute_idempotency_key(projection: Mapping[str, object]) -> str:
    return _digest(dict(projection))


def compute_runtime_dispatch_idempotency_key(projection: Mapping[str, object]) -> str:
    """RDGO-001 §10a / RPAC-REQ-065, widened for the real-dispatch fact
    set (Phase 149O.20L.7O.3W): a SHA-256 digest over canonical-content
    fields only -- repository fingerprint/base commit, `task_id`,
    `prompt_hash`, `runtime_target_id`, adapter/descriptor/config digests,
    requested effect/capability profile, and approval scope -- excluding
    `attempt_id` and any timestamp or other attempt-specific mutable
    observation. Kept as a sibling function rather than widening
    `compute_idempotency_key` itself: that function's existing canonical
    shape belongs exclusively to the mock-v1 dry path (PBRD-001 §13
    forbids migrating the dry path onto real-dispatch fact shapes), so the
    real-dispatch projection needs its own explicitly-scoped function even
    though the hashing *mechanism* (sorted-key canonical JSON, SHA-256) is
    identical and reused as-is."""
    return _digest(dict(projection))


#: Fields an untrusted caller (adapter, runtime response, external
#: payload) must never be able to set on a request via generic/dict
#: construction (RPAC-REQ-026, §13 of the 3R plan).
_FORBIDDEN_UNTRUSTED_REQUEST_FIELDS: frozenset[str] = frozenset(
    {
        "permission",
        "authorized",
        "pb_allow",
        "execution_allowed",
        "authorization",
        "approved",
    }
)


def reject_untrusted_request_payload(payload: Mapping[str, object]) -> tuple[str, ...]:
    """Fail-closed strict check used wherever an `InvocationRequest`
    might otherwise be reconstructed from an untrusted mapping
    (RPAC-REQ-026): any authority-shaped key is rejected outright rather
    than silently ignored."""
    return tuple(
        f"forbidden_authority_field:{key}"
        for key in payload
        if key in _FORBIDDEN_UNTRUSTED_REQUEST_FIELDS
    )


def build_invocation_request(
    *,
    authority: AuthoritySnapshot,
    requester_agent_id: str,
    runtime_target_id: str,
    expected_adapter_id: str,
    descriptor_digest: str,
    target_config_digest: str,
    prompt: PromptArtifact,
    approval: SimulationApprovalEvidence,
    requested_capability: str,
    expected_result_format: str,
    timeout_seconds: int,
    effect_profile: EffectProfile = MOCK_DRY_EFFECT_PROFILE,
    provider_id: str | None = None,
    model_id: str | None = None,
) -> tuple[InvocationRequest | None, tuple[str, ...]]:
    """Construct the immutable mock-v1 `InvocationRequest`. Returns
    `(request, ())` on success or `(None, issues)` fail-closed. Only the
    trusted coordinator calls this; an adapter has no constructor access
    (RPAC-REQ-026)."""
    issues: list[str] = []
    if not effect_profile.is_all_denied_zero():
        issues.append(FAILURE_UNSUPPORTED_CAPABILITY + ":effect_profile_not_default_deny")
    if timeout_seconds <= 0:
        issues.append(FAILURE_INVALID_REQUEST + ":non_positive_timeout")
    if provider_id is not None:
        issues.append(FAILURE_INVALID_REQUEST + ":mock_provider_must_be_absent")
    if model_id is not None:
        issues.append(FAILURE_INVALID_REQUEST + ":mock_model_must_be_absent")
    if not isinstance(prompt, PromptArtifact):
        issues.append(FAILURE_INVALID_REQUEST + ":prompt_must_be_prompt_artifact")
    if issues:
        return None, tuple(issues)

    invocation_id = new_invocation_id()
    attempt_id = new_attempt_id()
    partial = InvocationRequest(
        contract_version=CONTRACT_VERSION,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        idempotency_key="",
        repository_id=authority.repository_id,
        repository_fingerprint=authority.repository_fingerprint,
        base_commit=authority.base_commit,
        task_id=authority.task_id,
        task_contract_digest=authority.task_contract_digest,
        requester_agent_id=requester_agent_id,
        runtime_target_id=runtime_target_id,
        expected_adapter_id=expected_adapter_id,
        descriptor_digest=descriptor_digest,
        target_config_digest=target_config_digest,
        prompt_artifact_id=prompt.artifact_id,
        prompt_digest=prompt.content_digest,
        approval_id=approval.approval_id,
        approval_digest=_digest(
            {
                "approval_id": approval.approval_id,
                "bound_prompt_digest": approval.bound_prompt_digest,
                "bound_repository_id": approval.bound_repository_id,
                "bound_task_id": approval.bound_task_id,
                "bound_runtime_target_id": approval.bound_runtime_target_id,
                "bound_effect_profile_digest": approval.bound_effect_profile_digest,
            }
        ),
        requested_capability=requested_capability,
        expected_result_format=expected_result_format,
        working_directory=".",
        effect_profile=effect_profile,
        timeout_seconds=timeout_seconds,
        cancellation_required=False,
        provider_id=None,
        model_id=None,
        phase_id=authority.phase_id,
        session_id=authority.session_id,
    )
    key = compute_idempotency_key(partial.canonical_projection())
    request = InvocationRequest(**{**partial.__dict__, "idempotency_key": key})
    return request, ()


# ═══════════════════════════════════════════════════════════════════════
# Dispatch envelope (RPAC-REQ-029/030)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SimulationDispatchEnvelope:
    contract_version: str
    request: InvocationRequest
    target_status_digest: str
    approval_digest: str
    pb_decision_digest: str
    enforcement_digest: str
    record_reference: str
    expires_at: str
    simulation_only: bool = True

    def __post_init__(self) -> None:
        if not self.simulation_only:
            raise ValueError("mock_envelope_must_be_simulation_only")


def build_dispatch_envelope(
    *,
    request: InvocationRequest,
    target_status_digest: str,
    pb_decision_digest: str,
    enforcement_digest: str,
    record_reference: str,
    clock: Clock,
    ttl_marker: str = "single-attempt",
) -> SimulationDispatchEnvelope:
    return SimulationDispatchEnvelope(
        contract_version=request.contract_version,
        request=request,
        target_status_digest=target_status_digest,
        approval_digest=request.approval_digest,
        pb_decision_digest=pb_decision_digest,
        enforcement_digest=enforcement_digest,
        record_reference=record_reference,
        expires_at=f"{clock()}::{ttl_marker}",
    )


def validate_dispatch_envelope(
    envelope: SimulationDispatchEnvelope | None,
    *,
    expected_request: InvocationRequest,
) -> tuple[str, ...]:
    """Everything an adapter must check before accepting an envelope
    (RPAC-REQ-030): missing, version-mismatched, or digest-inconsistent
    envelopes are rejected. This is a syntactic check only -- it never
    grants the adapter authority."""
    if envelope is None:
        return (FAILURE_INTEGRITY_FAILURE + ":missing_envelope",)
    issues: list[str] = []
    if envelope.contract_version not in SUPPORTED_CONTRACT_MAJORS:
        issues.append(FAILURE_INTEGRITY_FAILURE + ":unsupported_contract_version")
    if envelope.request.invocation_id != expected_request.invocation_id:
        issues.append(FAILURE_INTEGRITY_FAILURE + ":invocation_id_mismatch")
    if envelope.request.idempotency_key != expected_request.idempotency_key:
        issues.append(FAILURE_INTEGRITY_FAILURE + ":idempotency_key_mismatch")
    if envelope.approval_digest != expected_request.approval_digest:
        issues.append(FAILURE_INTEGRITY_FAILURE + ":approval_digest_mismatch")
    if not envelope.simulation_only:
        issues.append(FAILURE_INTEGRITY_FAILURE + ":not_simulation_only")
    return tuple(issues)


# ═══════════════════════════════════════════════════════════════════════
# Simulation enforcement test double (RPAC-REQ-045/046)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SimulationEnforcementObservation:
    outcome: str
    simulation_only: bool
    non_authorizing: bool
    evidence_digest: str

    def __post_init__(self) -> None:
        if self.outcome not in ("would_allow_simulation", "deny_simulation"):
            raise ValueError(f"unknown_enforcement_outcome:{self.outcome}")
        if not self.simulation_only or not self.non_authorizing:
            raise ValueError("enforcement_double_must_stay_non_authorizing")


class SimulationEnforcementEvaluator:
    """A tiny, explicitly non-authorizing test seam standing in for a
    future real Runtime Enforcement positive gate (RPAC-REQ-045/046).
    Existing production Runtime Enforcement models are NOT invoked here
    -- they are evidence-only/non-authorizing and under-bound for RPAC,
    per 3Q/3R. This double never mints `AUTHORIZED`."""

    def evaluate(
        self,
        *,
        pb_would_allow: bool,
        approval_binding_ok: bool,
        freshness_ok: bool,
    ) -> SimulationEnforcementObservation:
        bound_evidence = {
            "pb_would_allow": pb_would_allow,
            "approval_binding_ok": approval_binding_ok,
            "freshness_ok": freshness_ok,
        }
        outcome = (
            "would_allow_simulation"
            if (pb_would_allow and approval_binding_ok and freshness_ok)
            else "deny_simulation"
        )
        return SimulationEnforcementObservation(
            outcome=outcome,
            simulation_only=True,
            non_authorizing=True,
            evidence_digest=_digest(bound_evidence),
        )


# ═══════════════════════════════════════════════════════════════════════
# Runtime invocation result (RPAC-REQ-035/036/037)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ChangedFileEntry:
    path: str
    operation: str
    content_after: str | None
    content_hash_after: str | None


@dataclass(frozen=True)
class RuntimeInvocationResult:
    contract_version: str
    invocation_id: str
    attempt_id: str
    idempotency_key: str
    runtime_target_id: str
    adapter_id: str
    descriptor_digest: str
    target_config_digest: str
    provider_id: None
    model_id: None
    simulation_only: bool
    execution_effect: str
    terminal_outcome: str
    structured_payload: Mapping[str, object]
    changed_files: tuple[ChangedFileEntry, ...]
    payload_digest: str
    result_digest: str
    requesting_agent_id: str
    producer_claim: str
    error_category: str | None
    error_subcode: str | None
    retryable_hint: bool
    untrusted: bool = True

    def __post_init__(self) -> None:
        if not self.simulation_only:
            raise ValueError("mock_result_must_be_simulation_only")
        if self.execution_effect != "none":
            raise ValueError("mock_result_execution_effect_must_be_none")
        if not self.untrusted:
            raise ValueError("runtime_result_must_remain_untrusted")


def derive_intake_candidate_id(invocation_id: str, attempt_id: str, result_digest: str) -> str:
    """A deterministic candidate identity derived from invocation ID,
    attempt ID, and result digest (RPAC-REQ-070), so repeated handoff
    mapping for the same completed attempt always yields the same
    candidate ID -- compatible with existing generic-intake replay
    semantics even though mock-v1 never calls
    `validate_and_ingest_intake_candidate`."""
    return "mock-dry-" + _digest(
        {"invocation_id": invocation_id, "attempt_id": attempt_id, "result_digest": result_digest}
    )[:32]


def _result_payload_digest(structured_payload: Mapping[str, object]) -> str:
    return _digest(dict(structured_payload))


def build_runtime_invocation_result(
    *,
    request: InvocationRequest,
    terminal_outcome: str,
    structured_payload: Mapping[str, object],
    changed_files: tuple[ChangedFileEntry, ...] = (),
    error_category: str | None = None,
    error_subcode: str | None = None,
    requesting_agent_id: str,
    producer_claim: str,
) -> RuntimeInvocationResult:
    payload_digest = _result_payload_digest(structured_payload)
    result_digest = _digest(
        {
            "invocation_id": request.invocation_id,
            "attempt_id": request.attempt_id,
            "terminal_outcome": terminal_outcome,
            "payload_digest": payload_digest,
            "changed_files": [
                {
                    "path": c.path,
                    "operation": c.operation,
                    "content_hash_after": c.content_hash_after,
                }
                for c in changed_files
            ],
            "error_category": error_category,
        }
    )
    return RuntimeInvocationResult(
        contract_version=request.contract_version,
        invocation_id=request.invocation_id,
        attempt_id=request.attempt_id,
        idempotency_key=request.idempotency_key,
        runtime_target_id=request.runtime_target_id,
        adapter_id=request.expected_adapter_id,
        descriptor_digest=request.descriptor_digest,
        target_config_digest=request.target_config_digest,
        provider_id=None,
        model_id=None,
        simulation_only=True,
        execution_effect="none",
        terminal_outcome=terminal_outcome,
        structured_payload=dict(structured_payload),
        changed_files=changed_files,
        payload_digest=payload_digest,
        result_digest=result_digest,
        requesting_agent_id=requesting_agent_id,
        producer_claim=producer_claim,
        error_category=error_category,
        error_subcode=error_subcode,
        retryable_hint=False,
    )


# ═══════════════════════════════════════════════════════════════════════
# Append-only invocation store (RPAC-REQ-061/067/068/069)
# ═══════════════════════════════════════════════════════════════════════

STORE_ROOT = Path(".pcae") / "runtime-invocations" / "mock-v1"


class InvocationIntegrityError(Exception):
    """Raised for any conflicting/corrupt persisted record. Callers must
    treat this as `integrity_failure` and never auto-repair or
    redispatch."""


def _require_safe_store_component(value: object, *, context: str) -> str:
    """3S.2.1 MUST-FIX #2 (defense-in-depth path containment). Require an
    identifier that will be joined onto the store root to be exactly one
    safe filesystem path segment -- rejecting `.`, `..`, and any path
    separator *before* the join, using the repository's canonical
    `require_safe_relative_id_component` grammar (the same helper the
    canonical HPAC consumption store uses). A crafted `invocation_id` /
    `attempt_id` such as `../../../../tmp/x` therefore can never select a
    location outside `.pcae/runtime-invocations/mock-v1/`. Production
    callers always pass `new_invocation_id()` / `new_attempt_id()` values,
    which satisfy this grammar unchanged; this guard only matters for any
    future caller that relays the field from less-trusted input."""
    try:
        return require_safe_relative_id_component(value, context=context)
    except HPACMalformedError as exc:
        raise InvocationIntegrityError(f"unsafe_path_component:{context}:{exc}") from exc


class RuntimeInvocationStore:
    """Append-only, create-only, repository-local persistence for mock-v1
    invocation records (RPAC-REQ-067). Every document under its root is
    written once and never mutated in place. This is audit evidence, not
    an authority source (RPAC-REQ-077, RPAC-REQ-083)."""

    def __init__(self, root: Path):
        self._invocations_root = Path(root) / STORE_ROOT

    def _invocation_dir(self, invocation_id: str) -> Path:
        safe = _require_safe_store_component(invocation_id, context="invocation_id")
        return self._invocations_root / safe

    def _attempt_dir(self, invocation_id: str, attempt_id: str) -> Path:
        safe_attempt = _require_safe_store_component(attempt_id, context="attempt_id")
        return self._invocation_dir(invocation_id) / "attempts" / safe_attempt

    def _assert_within_root(self, path: Path) -> None:
        """Post-join containment check on the *resolved* path (not a string
        prefix): every persisted document SHALL live strictly beneath the
        store root even if a component check is ever bypassed or a symlink
        is involved."""
        root = self._invocations_root.resolve(strict=False)
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise InvocationIntegrityError(f"path_escapes_store_root:{path}") from exc

    def _write_create_only(self, path: Path, document: Mapping[str, object]) -> None:
        self._assert_within_root(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise InvocationIntegrityError(f"record_already_exists:{path}")
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(_canonical_json(document), encoding="utf-8")
        tmp.replace(path)

    def create_request_record(self, request: InvocationRequest) -> None:
        """Create the immutable `request.json` for a new logical
        invocation, or, if one already exists, enforce
        same-ID/same-content idempotent resume vs. hard collision
        (RPAC-REQ-066)."""
        path = self._invocation_dir(request.invocation_id) / "request.json"
        existing = self.read_request(request.invocation_id)
        if existing is not None:
            if existing.get("idempotency_key") != request.idempotency_key:
                raise InvocationIntegrityError(
                    f"id_collision_conflicting_content:{request.invocation_id}"
                )
            return
        self._write_create_only(path, request.canonical_projection() | {
            "idempotency_key": request.idempotency_key,
            "attempt_id": request.attempt_id,
        })

    def read_request(self, invocation_id: str) -> dict | None:
        path = self._invocation_dir(invocation_id) / "request.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_events(self, invocation_id: str, attempt_id: str) -> list[dict]:
        directory = self._attempt_dir(invocation_id, attempt_id)
        if not directory.exists():
            return []
        events = sorted(
            p for p in directory.glob("[0-9][0-9][0-9][0-9]-*.json") if p.is_file()
        )
        return [json.loads(p.read_text(encoding="utf-8")) for p in events]

    def append_event(
        self, invocation_id: str, attempt_id: str, observation: SimulationStateObservation
    ) -> None:
        events = self.list_events(invocation_id, attempt_id)
        if events:
            last = events[-1]
            if last["sequence"] != observation.sequence - 1:
                raise InvocationIntegrityError("event_sequence_gap")
            if last["digest"] != observation.prior_digest:
                raise InvocationIntegrityError("event_chain_digest_mismatch")
        directory = self._attempt_dir(invocation_id, attempt_id)
        path = directory / f"{observation.sequence:04d}-{observation.state.lower()}.json"
        document = {
            "sequence": observation.sequence,
            "state": observation.state,
            "observed_at": observation.observed_at,
            "prior_digest": observation.prior_digest,
            "detail": observation.detail,
            "digest": observation.digest(),
        }
        self._write_create_only(path, document)

    def latest_state(self, invocation_id: str, attempt_id: str) -> str | None:
        events = self.list_events(invocation_id, attempt_id)
        return events[-1]["state"] if events else None

    def write_result(
        self, invocation_id: str, attempt_id: str, result: RuntimeInvocationResult
    ) -> None:
        path = self._attempt_dir(invocation_id, attempt_id) / "result.json"
        existing = self.read_result(invocation_id, attempt_id)
        document = {
            "invocation_id": result.invocation_id,
            "attempt_id": result.attempt_id,
            "terminal_outcome": result.terminal_outcome,
            "payload_digest": result.payload_digest,
            "result_digest": result.result_digest,
            "structured_payload": result.structured_payload,
            "changed_files": [
                {
                    "path": c.path,
                    "operation": c.operation,
                    "content_after": c.content_after,
                    "content_hash_after": c.content_hash_after,
                }
                for c in result.changed_files
            ],
            "error_category": result.error_category,
            "error_subcode": result.error_subcode,
        }
        if existing is not None:
            if existing["result_digest"] != result.result_digest:
                raise InvocationIntegrityError(
                    f"conflicting_completion:{invocation_id}/{attempt_id}"
                )
            return
        self._write_create_only(path, document)

    def read_result(self, invocation_id: str, attempt_id: str) -> dict | None:
        path = self._attempt_dir(invocation_id, attempt_id) / "result.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_intake_handoff(
        self, invocation_id: str, attempt_id: str, handoff: Mapping[str, object]
    ) -> None:
        path = self._attempt_dir(invocation_id, attempt_id) / "intake-handoff.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing.get("candidate_id") != handoff.get("candidate_id"):
                raise InvocationIntegrityError("conflicting_intake_handoff")
            return
        self._write_create_only(path, dict(handoff))

    def restart_disposition(self, invocation_id: str, attempt_id: str) -> str:
        """Resume semantics after a process restart (RPAC-REQ-068):
        `not_started`, `pending_pre_dispatch` (resume validation, no
        adapter call), `simulation_ambiguous` (a dispatch intent was
        persisted but no terminal result exists -- never
        auto-redispatched), or `completed`."""
        latest = self.latest_state(invocation_id, attempt_id)
        if latest is None:
            return "not_started"
        if self.read_result(invocation_id, attempt_id) is not None:
            return "completed"
        state_index = SIMULATION_STATE_ORDER.index(latest)
        dispatch_intent_index = SIMULATION_STATE_ORDER.index(SIM_DISPATCH_INTENT)
        if state_index >= dispatch_intent_index:
            return FAILURE_SIMULATION_AMBIGUOUS
        return "pending_pre_dispatch"
