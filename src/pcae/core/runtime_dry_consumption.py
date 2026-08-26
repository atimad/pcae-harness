"""
Production Dry-Lifecycle Runtime Adapter Consumption — Phase 149O.20L.7O.3S.2.

Wires the RPAC-001 v1.0 mock/dry adapter (implemented in Phase
149O.20L.7O.3S, independently verified in 149O.20L.7O.3S.1) into exactly
one narrow production consumer: the existing compact session-bootstrap
prompt lifecycle (`pcae session bootstrap --compact`). This is the
trusted-kernel-side production integration point that
`pcae.core.runtime_invocation`'s module docstring describes as "a live
builder reading real git/task state ... explicitly deferred" -- that
deferral ends here, in production integration code, not inside the pure
mock-v1 data/persistence module itself.

This module is a thin service layer only. It never duplicates
`simulate_invocation`'s gate sequence (RPAC-REQ-034); it constructs the
`AuthoritySnapshot` from real PCAE-owned repository/task state and then
delegates every governance decision to the existing, unmodified
`pcae.core.runtime_adapter.simulate_invocation` coordinator, the existing
`RuntimeAdapterResolver`, and the existing `MockDryRuntimeAdapter` --
exactly the RPAC registry/adapter abstraction already verified in 3S/3S.1.

Explicit-intent only (RPAC-REQ-053, 3S.2 spec Sections 5/7/24): this
module's one entry point, `run_production_dry_invocation`, is reached ONLY
when a caller supplies an explicit `runtime_target_id` that exactly
matches a known mock-v1 fixture ID. There is no default target, no
first-registered-adapter fallback, no agent-identity-derived target
inference, and no silent revert to the ordinary non-dry prompt flow on
failure -- unknown-target and missing-authority requests fail closed with
`UnknownRuntimeTargetError` and never construct or dispatch a request.

Nothing here changes canonical execution availability, Permission Broker
policy, Runtime Enforcement, Shell Gate, or touches subprocess, network,
or credentials. `AuthoritySnapshot.base_commit` and `.repository_fingerprint`
are derived via `pcae.core.intake`'s existing, already-governed
`current_head_commit`/`compute_repo_fingerprint` helpers -- the same git
subprocess PCAE already runs for ordinary generic-intake and push-check
operations, not a new "runtime dispatch" subprocess surface (RPAC-REQ-090
and 3S.2 spec Section 28 both concern the *adapter's* transport, not the
kernel's own pre-existing repository-state helpers).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from .intake import compute_repo_fingerprint, current_head_commit
from .mock_runtime_adapter import (
    KNOWN_MOCK_TARGET_FIXTURES,
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from .paths import HarnessPath
from .runtime_adapter import (
    RuntimeAdapterResolver,
    RuntimeTargetConfiguration,
    SimulationOutcome,
    simulate_invocation,
)
from .runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    RuntimeInvocationStore,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)
from .runtime_registry import RuntimeRegistry
from .tasks import find_latest_active_task

#: The one production entry point this phase creates (Matrix A). Recorded
#: here, not inferred, so tests and the canonical report cite the exact
#: same string.
DRY_CONSUMER_ENTRY_POINT = "pcae session bootstrap --compact --dry-runtime --runtime-target <id>"
DRY_PROMPT_GENERATION_METHOD = "bootstrap_compact_dry"
DRY_PROMPT_GENERATION_VERSION = "1.0"
DRY_RUNTIME_TIMEOUT_SECONDS = 30


class UnknownRuntimeTargetError(ValueError):
    """Explicit target resolution or authority derivation failed closed.
    No fallback, default adapter, or alternate runtime is ever consulted
    (RPAC-REQ-053, 3S.2 spec Section 24)."""


@dataclass(frozen=True)
class DryConsumerContext:
    """The PCAE-owned facts this production consumer derives itself. None
    of these fields is ever accepted from CLI/user payload (RPAC-REQ-026);
    the only caller-supplied values anywhere in this module are
    `agent_id`, `runtime_target_id`, and `prompt_content`."""

    repository_id: str
    repository_fingerprint: str
    base_commit: str
    task_id: str
    task_contract_digest: str


def resolve_dry_consumer_context(root: HarnessPath) -> DryConsumerContext | None:
    """Derive the authoritative repository/task binding from real PCAE
    state (RPAC-REQ-078). Returns `None` -- never a partial/best-effort
    binding -- when there is no active task or no resolvable HEAD, so the
    dry lifecycle fails closed rather than binding to absent authority."""
    active_task = find_latest_active_task(root)
    if active_task is None:
        return None
    head = current_head_commit(root)
    if head is None:
        return None
    fingerprint = compute_repo_fingerprint(root)
    if fingerprint is None:
        return None
    task_contract_digest = hashlib.sha256(
        active_task.path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    return DryConsumerContext(
        repository_id=str(root.path),
        repository_fingerprint=fingerprint,
        base_commit=head,
        task_id=active_task.task_id,
        task_contract_digest=task_contract_digest,
    )


def _utc_clock() -> str:
    """The only wall-clock read in this module. Injected as `clock` into
    every pure runtime_invocation/runtime_adapter builder below, which
    never read the clock themselves (module contract preserved)."""
    return datetime.now(timezone.utc).isoformat()


def run_production_dry_invocation(
    *,
    root: HarnessPath,
    agent_id: str,
    runtime_target_id: str,
    prompt_content: str,
) -> SimulationOutcome | UnknownRuntimeTargetError:
    """The one production entry point that reaches RPAC's
    `simulate_invocation` (Matrix A). `runtime_target_id` must be an exact
    known mock-v1 fixture ID -- no default, no first-registered adapter,
    no agent-identity inference (RPAC-REQ-053). `agent_id` is carried as
    descriptive `AgentIdentity` only (RPAC-REQ-006/007/008); it never
    selects a target, provider, or model, and `codex-ox` gains no special
    handling here or anywhere downstream in `simulate_invocation`.

    Delegates all governance/gate logic to the existing, unmodified
    `simulate_invocation` coordinator; this function only assembles the
    PCAE-owned inputs it requires (RPAC-REQ-034: the coordinator, never
    this wrapper, owns record persistence and gate ordering).

    Split into two phases so tests can prove the pure RPAC-consuming phase
    (`_run_with_context`, below) makes zero subprocess/network calls
    independent of `resolve_dry_consumer_context`'s legitimate, pre-existing
    use of PCAE's own git-HEAD helper (`pcae.core.intake.current_head_commit`,
    the same subprocess PCAE already runs for push-check/generic-intake --
    not a new "runtime dispatch" subprocess surface).
    """
    if runtime_target_id not in KNOWN_MOCK_TARGET_FIXTURES:
        return UnknownRuntimeTargetError(f"unknown_runtime_target:{runtime_target_id}")

    context = resolve_dry_consumer_context(root)
    if context is None:
        return UnknownRuntimeTargetError("no_active_task_authority")

    return _run_with_context(
        root=root, context=context, agent_id=agent_id,
        runtime_target_id=runtime_target_id, prompt_content=prompt_content,
    )


def _run_with_context(
    *,
    root: HarnessPath,
    context: DryConsumerContext,
    agent_id: str,
    runtime_target_id: str,
    prompt_content: str,
) -> SimulationOutcome | UnknownRuntimeTargetError:
    """The pure RPAC-consuming phase: registry/resolver/prompt/approval/
    request construction and the `simulate_invocation` call. No
    subprocess, socket, or credential access anywhere in this function or
    anything it calls (verified by
    `test_run_with_context_zero_subprocess_network`)."""
    clock = _utc_clock

    registry = RuntimeRegistry()
    descriptor = build_mock_descriptor()
    registry.register_adapter_descriptor(descriptor)
    resolver = RuntimeAdapterResolver(registry)
    config = RuntimeTargetConfiguration(
        runtime_target_id, "1.0", MOCK_ADAPTER_ID, runtime_target_id
    )
    resolver.register_target(config)
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())

    authority = AuthoritySnapshot(
        repository_id=context.repository_id,
        repository_fingerprint=context.repository_fingerprint,
        base_commit=context.base_commit,
        task_id=context.task_id,
        task_contract_digest=context.task_contract_digest,
    )
    prompt = build_prompt_artifact(
        content=prompt_content,
        generation_method=DRY_PROMPT_GENERATION_METHOD,
        generation_version=DRY_PROMPT_GENERATION_VERSION,
        authority=authority,
        clock=clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt,
        authority=authority,
        runtime_target_id=runtime_target_id,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(),
        clock=clock,
    )
    request, issues = build_invocation_request(
        authority=authority,
        requester_agent_id=agent_id,
        runtime_target_id=runtime_target_id,
        expected_adapter_id=MOCK_ADAPTER_ID,
        descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(),
        prompt=prompt,
        approval=approval,
        requested_capability=MOCK_CAPABILITY,
        expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=DRY_RUNTIME_TIMEOUT_SECONDS,
    )
    if request is None:
        return UnknownRuntimeTargetError(f"invalid_request:{','.join(issues)}")

    store = RuntimeInvocationStore(root.path)
    return simulate_invocation(
        request=request,
        prompt_digest=prompt.content_digest,
        approval=approval,
        resolver=resolver,
        store=store,
        clock=clock,
    )
