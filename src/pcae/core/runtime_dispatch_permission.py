"""
Runtime Dispatch Permission — Phase 149O.20L.7O.3W.

Implements PBRD-001 v1.1's `runtime_dispatch` request architecture
extension: the trusted construction of a `PermissionBrokerRequest`
carrying the exact fourteen immutable binding facts
(`permission_broker_foundation.RuntimeDispatchRequestFacts`), and the
trusted approval projection adapter (PBRD-001 §7 / §22) that is the only
path by which `approval_present` may ever become true for this action.

This module is a pure construction/evaluation boundary. It never spawns a
process, never touches the network, never reads credentials, and never
calls `pcae.core.runtime_authority`'s validator itself -- it *consumes*
that validator's output (`ValidatedAuthorityProjection`), matching
RIHAC-001's wall: "human approval != PB permission" (gate 5 and gate 6
are independent gates; this module implements gate 6 only).

POL-005 (`ExecutionDisabledRule`) is untouched by this module and by
design: every `runtime_dispatch` request built here with
`simulation_only=False` is denied by the unmodified existing rule,
exactly like every other action type (PBRD-001 §12/§24).
"""

from __future__ import annotations

from dataclasses import dataclass

from .permission_broker_foundation import (
    EXECUTION_CLASS_ADAPTER,
    ACTION_TYPE_RUNTIME_DISPATCH,
    PermissionBrokerRequest,
    RuntimeDispatchAdapterDescriptorBinding,
    RuntimeDispatchFilesystemScopeRef,
    RuntimeDispatchHumanAuthorityBinding,
    RuntimeDispatchLifecycleContext,
    RuntimeDispatchRequestFacts,
    build_permission_broker_request,
)
from .runtime_authority import ValidatedAuthorityProjection, compute_canonical_digest
from .runtime_invocation import (
    compute_runtime_dispatch_idempotency_key,
    is_valid_generated_id,
    new_attempt_id,
    new_invocation_id,
)

#: PCAE `COMP-006` -- "Adapter Boundary" -- the existing component
#: registry entry `runtime_dispatch` is mediated through (matches
#: PBRD-001 §1's "existing adapter execution class").
REQUESTED_COMPONENT_ADAPTER_BOUNDARY = "COMP-006"


class RuntimeDispatchConstructionError(Exception):
    """Raised for any attempt to construct a `runtime_dispatch` request
    from an invalid or untrusted identity, or for a detected identity
    collision (PBRD-001 §15). Never silently corrected."""


@dataclass(frozen=True)
class RuntimeDispatchRequestConstructionInput:
    """The subset of the fourteen PBRD-001 facts that are NOT identity
    (`invocation_id`/`attempt_id`/`idempotency_key` are minted separately,
    see `new_runtime_dispatch_identity`) or the human-authority binding
    (projected separately from `ValidatedAuthorityProjection`). Every
    field here is trusted-caller-resolved state, exactly mirroring
    `runtime_authority.InvocationRequestContext`'s discipline: this module
    performs no repository/task/registry resolution of its own."""

    repository_identity: str
    task_id: str
    lifecycle_context: RuntimeDispatchLifecycleContext
    runtime_target_id: str
    adapter_descriptor_binding: RuntimeDispatchAdapterDescriptorBinding
    prompt_hash: str
    requested_capability: str
    filesystem_scope_ref: RuntimeDispatchFilesystemScopeRef


def canonical_runtime_dispatch_projection(inputs: RuntimeDispatchRequestConstructionInput) -> dict:
    """RDGO-001 §10a / RPAC-REQ-065's canonical-content projection for the
    real-dispatch idempotency key: excludes `attempt_id` and any
    timestamp; includes repository/task/target/prompt/adapter/scope
    facts. A change to any field here always produces a different
    `idempotency_key` -- this is a pure function, so "same key with a
    changed field" is structurally impossible to construct through this
    module (PBRD-001 §15's "hard collision" only arises from a caller
    forging a mismatched key directly against the store, tested in
    `test_runtime_dispatch_attempt_idempotency.py`)."""
    return {
        "repository_identity": inputs.repository_identity,
        "task_id": inputs.task_id,
        "lifecycle_context": {
            "phase_id": inputs.lifecycle_context.phase_id,
            "session_id": inputs.lifecycle_context.session_id,
        },
        "runtime_target_id": inputs.runtime_target_id,
        "adapter_descriptor_binding": {
            "adapter_id": inputs.adapter_descriptor_binding.adapter_id,
            "descriptor_version": inputs.adapter_descriptor_binding.descriptor_version,
            "descriptor_digest": inputs.adapter_descriptor_binding.descriptor_digest,
            "target_config_digest": inputs.adapter_descriptor_binding.target_config_digest,
        },
        "prompt_hash": inputs.prompt_hash,
        "requested_capability": inputs.requested_capability,
        "filesystem_scope_ref": {
            "scope_id": inputs.filesystem_scope_ref.scope_id,
            "scope_digest": inputs.filesystem_scope_ref.scope_digest,
        },
    }


@dataclass(frozen=True)
class RuntimeDispatchIdentity:
    """The gate-2-minted immutable request-identity triple (RDGO-001 §3 /
    §10a): `invocation_id` (stable across attempts), `attempt_id` (unique
    per concrete try), `idempotency_key` (stable across safe retries of an
    unchanged logical request). All three PCAE-owned; never adapter,
    runtime, or caller-supplied."""

    invocation_id: str
    attempt_id: str
    idempotency_key: str


def new_runtime_dispatch_identity(
    inputs: RuntimeDispatchRequestConstructionInput,
    *,
    invocation_id: str | None = None,
) -> RuntimeDispatchIdentity:
    """Mint (or, for a genuine same-logical-request retry, reuse) the
    identity triple at gate 2. Passing an existing `invocation_id` models
    a retry of the same logical invocation (RDGO-001 §10a "Retry
    relationship"): `attempt_id` is always freshly minted; `idempotency_key`
    is a pure function of `inputs` and is therefore identical for an
    unchanged logical request and different for any changed one, with no
    possibility of the two diverging."""
    return RuntimeDispatchIdentity(
        invocation_id=invocation_id or new_invocation_id(),
        attempt_id=new_attempt_id(),
        idempotency_key=compute_runtime_dispatch_idempotency_key(
            canonical_runtime_dispatch_projection(inputs)
        ),
    )


class RuntimeDispatchIdentityTracker:
    """Construction-time collision guard for `attempt_id`/`idempotency_key`
    uniqueness (PBRD-001 §15, RPAC-REQ-066). This is explicitly NOT the
    durable RDGO-001 gate-9 pre-dispatch record -- that record does not
    exist yet (3V.2 §16/§28 staging) and requires gate 8 as an input. This
    tracker is a lighter-weight, process-local integrity check available
    before gate 9 exists, proving the collision-detection *logic* end to
    end without claiming durable, crash-safe, cross-process enforcement."""

    def __init__(self) -> None:
        self._attempt_fingerprint: dict[str, str] = {}
        self._idempotency_invocation: dict[str, str] = {}

    def register(self, identity: RuntimeDispatchIdentity) -> None:
        fingerprint = compute_canonical_digest(
            {"invocation_id": identity.invocation_id, "idempotency_key": identity.idempotency_key}
        )
        prior_fingerprint = self._attempt_fingerprint.get(identity.attempt_id)
        if prior_fingerprint is not None and prior_fingerprint != fingerprint:
            raise RuntimeDispatchConstructionError(
                f"attempt_id_collision_conflicting_content:{identity.attempt_id}"
            )
        self._attempt_fingerprint[identity.attempt_id] = fingerprint

        prior_invocation = self._idempotency_invocation.get(identity.idempotency_key)
        if prior_invocation is not None and prior_invocation != identity.invocation_id:
            raise RuntimeDispatchConstructionError(
                f"idempotency_key_collision_different_invocation:{identity.idempotency_key}"
            )
        self._idempotency_invocation[identity.idempotency_key] = identity.invocation_id


def project_human_authority_binding(
    validated_authority: ValidatedAuthorityProjection | None,
) -> tuple[RuntimeDispatchHumanAuthorityBinding, bool]:
    """PBRD-001 §7/§22: the ONLY function in this module (indeed, in this
    phase's entire surface) that may cause `approval_present=True`. It
    reads exclusively the gate-5 `ValidatedAuthorityProjection` -- never
    raw approval prose, never a caller-supplied boolean. Missing, stale,
    mismatched, or unvalidated authority (`validated_authority is None`)
    always yields `approval_present=False` and an empty-reference binding;
    there is no other code path to a `True` value anywhere in this
    codebase (verified by the "caller-supplied approval_present shortcut"
    adversarial test)."""
    if validated_authority is None:
        return (
            RuntimeDispatchHumanAuthorityBinding(
                approval_id="", approval_record_digest="", validation_evidence_digest=""
            ),
            False,
        )
    return (
        RuntimeDispatchHumanAuthorityBinding(
            approval_id=validated_authority.approval_id,
            approval_record_digest=validated_authority.record_digest,
            validation_evidence_digest=validated_authority.evidence_digest(),
        ),
        True,
    )


def build_runtime_dispatch_permission_broker_request(
    *,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    validated_authority: ValidatedAuthorityProjection | None,
    simulation_only: bool = True,
    identity_tracker: RuntimeDispatchIdentityTracker | None = None,
) -> PermissionBrokerRequest:
    """The trusted, contract-fixed PCAE integration point for
    `runtime_dispatch` requests (PBRD-001 §5). Only this function may
    construct a `RuntimeDispatchRequestFacts`-bearing
    `PermissionBrokerRequest`; there is no generic/dict-based construction
    path an adapter or caller payload could use to set any of the fourteen
    facts directly.

    `simulation_only` defaults to `True` (policy-evaluable without a real
    dispatch attempt). Passing `False` models a real, non-simulation
    request -- POL-005 (unmodified) always denies it (proved by
    `test_runtime_dispatch_permission.py`'s POL-005 regression case).
    """
    if not is_valid_generated_id(identity.invocation_id, prefix="inv"):
        raise RuntimeDispatchConstructionError(f"invalid_invocation_id:{identity.invocation_id!r}")
    if not is_valid_generated_id(identity.attempt_id, prefix="att"):
        raise RuntimeDispatchConstructionError(f"invalid_attempt_id:{identity.attempt_id!r}")

    expected_key = compute_runtime_dispatch_idempotency_key(
        canonical_runtime_dispatch_projection(inputs)
    )
    if identity.idempotency_key != expected_key:
        raise RuntimeDispatchConstructionError(
            "idempotency_key_does_not_match_canonical_content: "
            f"presented={identity.idempotency_key!r} expected={expected_key!r}"
        )

    if identity_tracker is not None:
        identity_tracker.register(identity)

    human_authority_binding, approval_present = project_human_authority_binding(validated_authority)

    facts = RuntimeDispatchRequestFacts(
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
        idempotency_key=identity.idempotency_key,
        repository_identity=inputs.repository_identity,
        task_id=inputs.task_id,
        lifecycle_context=inputs.lifecycle_context,
        runtime_target_id=inputs.runtime_target_id,
        adapter_descriptor_binding=inputs.adapter_descriptor_binding,
        prompt_hash=inputs.prompt_hash,
        requested_capability=inputs.requested_capability,
        filesystem_scope_ref=inputs.filesystem_scope_ref,
        human_authority_binding=human_authority_binding,
    )

    return build_permission_broker_request(
        action_type=ACTION_TYPE_RUNTIME_DISPATCH,
        execution_class=EXECUTION_CLASS_ADAPTER,
        requested_component=REQUESTED_COMPONENT_ADAPTER_BOUNDARY,
        requested_capability=inputs.requested_capability,
        task_id=inputs.task_id,
        phase_id=inputs.lifecycle_context.phase_id,
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=simulation_only,
        runtime_dispatch_context=facts,
    )
