"""
Runtime Dispatch Permission — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7.

Implements PBRD-001 v1.1's `runtime_dispatch` request architecture
extension: the trusted construction of a `PermissionBrokerRequest`
carrying the exact fourteen immutable binding facts
(`permission_broker_foundation.RuntimeDispatchRequestFacts`), and the
trusted approval projection adapter (PBRD-001 §7 / §22) that is the only
path by which `approval_present` may ever become true for this action.

This module is a construction/evaluation boundary. It never spawns a
process, never touches the network, and never reads credentials directly.
Before projecting an existing `ValidatedAuthorityProjection`, it asks the
authority boundary to re-resolve and revalidate every canonical dependency;
that is a B1 currentness check, not Gate-5 coordinator wiring. It then
constructs the already-existing PB request shape, preserving RIHAC-001's
wall that human approval is not PB permission. This phase changes no PB
policy or evaluator.

POL-005 (`ExecutionDisabledRule`) is untouched by this module and by
design: every `runtime_dispatch` request built here with
`simulation_only=False` is denied by the unmodified existing rule,
exactly like every other action type (PBRD-001 §12/§24).
"""

from __future__ import annotations

import json
import os
import re
import stat
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path

from .permission_broker_foundation import (
    PermissionBrokerRequest,
    RuntimeDispatchAdapterDescriptorBinding,
    RuntimeDispatchFilesystemScopeRef,
    RuntimeDispatchHumanAuthorityBinding,
    RuntimeDispatchLifecycleContext,
    RuntimeDispatchRequestFacts,
    _build_runtime_dispatch_permission_broker_request,
)
from .runtime_authority import (
    ValidatedAuthorityProjection,
    compute_canonical_digest,
    is_trusted_validated_authority_projection,
    revalidate_validated_authority_projection,
)
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


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


def _bounded_string(value: object, maximum: int = 256) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip()


def _digest_string(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _valid_ref(value: object) -> bool:
    return (
        type(value) is RuntimeDispatchFilesystemScopeRef
        and _bounded_string(value.scope_id)
        and _digest_string(value.scope_digest)
    )


def _validate_construction_inputs(inputs: object) -> None:
    if type(inputs) is not RuntimeDispatchRequestConstructionInput:
        raise RuntimeDispatchConstructionError("invalid_construction_input")
    assert isinstance(inputs, RuntimeDispatchRequestConstructionInput)
    adapter = inputs.adapter_descriptor_binding
    lifecycle = inputs.lifecycle_context
    valid = (
        _digest_string(inputs.repository_identity)
        and isinstance(inputs.base_commit, str)
        and bool(_COMMIT_RE.fullmatch(inputs.base_commit))
        and _bounded_string(inputs.task_id)
        and _digest_string(inputs.task_contract_digest)
        and type(lifecycle) is RuntimeDispatchLifecycleContext
        and _bounded_string(lifecycle.phase_id)
        and (lifecycle.session_id is None or _bounded_string(lifecycle.session_id))
        and _bounded_string(inputs.runtime_target_id, 128)
        and type(adapter) is RuntimeDispatchAdapterDescriptorBinding
        and _bounded_string(adapter.adapter_id, 128)
        and _bounded_string(adapter.descriptor_version, 128)
        and _digest_string(adapter.descriptor_digest)
        and _digest_string(adapter.target_config_digest)
        and _digest_string(inputs.prompt_hash)
        and _bounded_string(inputs.requested_capability, 128)
        and _valid_ref(inputs.filesystem_scope_ref)
        and _valid_ref(inputs.process_profile_ref)
        and inputs.effect_class == "bounded_local_process_dispatch"
        and inputs.network_requirement is False
        and _valid_ref(inputs.resource_budget)
    )
    if not valid:
        raise RuntimeDispatchConstructionError("invalid_construction_input_facts")


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
    base_commit: str
    task_id: str
    task_contract_digest: str
    lifecycle_context: RuntimeDispatchLifecycleContext
    runtime_target_id: str
    adapter_descriptor_binding: RuntimeDispatchAdapterDescriptorBinding
    prompt_hash: str
    requested_capability: str
    filesystem_scope_ref: RuntimeDispatchFilesystemScopeRef
    process_profile_ref: RuntimeDispatchFilesystemScopeRef
    effect_class: str
    network_requirement: bool
    resource_budget: RuntimeDispatchFilesystemScopeRef


def canonical_runtime_dispatch_projection(
    inputs: RuntimeDispatchRequestConstructionInput, *, invocation_id: str
) -> dict:
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
        "invocation_id": invocation_id,
        "repository_identity": inputs.repository_identity,
        "base_commit": inputs.base_commit,
        "task_id": inputs.task_id,
        "task_contract_digest": inputs.task_contract_digest,
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
        "process_profile_ref": {
            "scope_id": inputs.process_profile_ref.scope_id,
            "scope_digest": inputs.process_profile_ref.scope_digest,
        },
        "effect_class": inputs.effect_class,
        "network_requirement": inputs.network_requirement,
        "resource_budget": {
            "scope_id": inputs.resource_budget.scope_id,
            "scope_digest": inputs.resource_budget.scope_digest,
        },
    }


def _expected_subject_scope_binding_digest(
    *, identity: RuntimeDispatchIdentity, inputs: RuntimeDispatchRequestConstructionInput
) -> str:
    return compute_canonical_digest(
        {
            "subject": {
                "invocation_id": identity.invocation_id,
                "runtime_target_id": inputs.runtime_target_id,
                "prompt_hash": inputs.prompt_hash,
                "repository_identity": inputs.repository_identity,
                "task_id": inputs.task_id,
            },
            "approval_scope": {
                "requested_capability": inputs.requested_capability,
                "transport_type": "local_cli",
                "effect_class": inputs.effect_class,
                "dispatch_limit": 1,
                "network_required": inputs.network_requirement,
                "filesystem_scope_ref": {
                    "artifact_id": inputs.filesystem_scope_ref.scope_id,
                    "artifact_digest": inputs.filesystem_scope_ref.scope_digest,
                },
                "process_profile_ref": {
                    "artifact_id": inputs.process_profile_ref.scope_id,
                    "artifact_digest": inputs.process_profile_ref.scope_digest,
                },
            },
            "adapter_binding": {
                "adapter_id": inputs.adapter_descriptor_binding.adapter_id,
                "descriptor_version": inputs.adapter_descriptor_binding.descriptor_version,
                "descriptor_digest": inputs.adapter_descriptor_binding.descriptor_digest,
                "target_config_digest": inputs.adapter_descriptor_binding.target_config_digest,
            },
        }
    )


_RUNTIME_DISPATCH_IDENTITY_SEAL = object()


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
    _identity_seal: object | None = field(default=None, repr=False, compare=False)
    _registration_digest: str = field(default="", repr=False, compare=False)
    _identity_tracker: RuntimeDispatchIdentityTracker | None = field(
        default=None, repr=False, compare=False
    )


def _identity_registration_digest(identity: RuntimeDispatchIdentity) -> str:
    return compute_canonical_digest(
        {
            "invocation_id": identity.invocation_id,
            "attempt_id": identity.attempt_id,
            "idempotency_key": identity.idempotency_key,
        }
    )


def new_runtime_dispatch_identity(
    inputs: RuntimeDispatchRequestConstructionInput,
    *,
    identity_tracker: RuntimeDispatchIdentityTracker,
    invocation_id: str | None = None,
) -> RuntimeDispatchIdentity:
    """Mint (or, for a genuine same-logical-request retry, reuse) the
    identity triple at gate 2. Passing an existing `invocation_id` models
    a retry of the same logical invocation (RDGO-001 §10a "Retry
    relationship"): `attempt_id` is always freshly minted; `idempotency_key`
    is a pure function of `inputs` and is therefore identical for an
    unchanged logical request and different for any changed one, with no
    possibility of the two diverging."""
    _validate_construction_inputs(inputs)
    resolved_invocation_id = invocation_id or new_invocation_id()
    if not is_valid_generated_id(resolved_invocation_id, prefix="inv"):
        raise RuntimeDispatchConstructionError(
            f"invalid_invocation_id:{resolved_invocation_id!r}"
        )
    identity = RuntimeDispatchIdentity(
        invocation_id=resolved_invocation_id,
        attempt_id=new_attempt_id(),
        idempotency_key=compute_runtime_dispatch_idempotency_key(
            canonical_runtime_dispatch_projection(inputs, invocation_id=resolved_invocation_id)
        ),
        _identity_seal=_RUNTIME_DISPATCH_IDENTITY_SEAL,
        _identity_tracker=identity_tracker,
    )
    identity_tracker.register(identity)
    return replace(identity, _registration_digest=_identity_registration_digest(identity))


class RuntimeDispatchIdentityTracker:
    """Construction-time collision guard for `attempt_id`/`idempotency_key`
    uniqueness (PBRD-001 §15, RPAC-REQ-066). This is explicitly NOT the
    durable RDGO-001 gate-9 pre-dispatch record -- that record does not
    exist yet (3V.2 §16/§28 staging) and requires gate 8 as an input. This
    tracker is a gate-2 append-only collision registry, not the gate-9
    dispatch-attempt record and not approval consumption. Create-exclusive
    records make the same collision result deterministic across processes."""

    STORE_ROOT = Path(".pcae") / "runtime-dispatch-identities" / "v1"

    def __init__(self, root: Path) -> None:
        self._repository_root = Path(root)
        self._root = self._repository_root / self.STORE_ROOT

    def _ensure_directory(self, path: Path) -> None:
        try:
            root_stat = self._repository_root.lstat()
        except FileNotFoundError as exc:
            raise RuntimeDispatchConstructionError("identity_store_root_missing") from exc
        if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
            raise RuntimeDispatchConstructionError("identity_store_root_untrusted")
        current = self._repository_root
        relative = path.relative_to(self._repository_root)
        for component in relative.parts:
            current = current / component
            try:
                entry_stat = current.lstat()
            except FileNotFoundError:
                try:
                    current.mkdir(mode=0o700)
                except FileExistsError:
                    pass
                entry_stat = current.lstat()
            if not stat.S_ISDIR(entry_stat.st_mode) or stat.S_ISLNK(entry_stat.st_mode):
                raise RuntimeDispatchConstructionError("identity_store_path_untrusted")

    def _require_directory(self, path: Path) -> None:
        """Verify every existing registry path component without creating it."""
        try:
            root_stat = self._repository_root.lstat()
        except FileNotFoundError as exc:
            raise RuntimeDispatchConstructionError("identity_store_root_missing") from exc
        if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
            raise RuntimeDispatchConstructionError("identity_store_root_untrusted")
        current = self._repository_root
        for component in path.relative_to(self._repository_root).parts:
            current = current / component
            try:
                entry_stat = current.lstat()
            except FileNotFoundError as exc:
                raise RuntimeDispatchConstructionError("identity_store_record_missing") from exc
            if not stat.S_ISDIR(entry_stat.st_mode) or stat.S_ISLNK(entry_stat.st_mode):
                raise RuntimeDispatchConstructionError("identity_store_path_untrusted")

    def _read_record(self, path: Path) -> dict:
        try:
            entry_stat = path.lstat()
            if (
                not stat.S_ISREG(entry_stat.st_mode)
                or stat.S_ISLNK(entry_stat.st_mode)
                or entry_stat.st_nlink != 1
            ):
                raise RuntimeDispatchConstructionError("identity_record_untrusted")
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                payload = b""
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    payload += chunk
            finally:
                os.close(fd)
            parsed = json.loads(payload.decode("utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeDispatchConstructionError("identity_store_record_missing") from exc
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeDispatchConstructionError("identity_record_corrupt") from exc
        if not isinstance(parsed, dict):
            raise RuntimeDispatchConstructionError("identity_record_corrupt")
        return parsed

    def _create_or_compare(
        self, path: Path, record: dict, *, collision: str, allow_identical: bool
    ) -> None:
        self._ensure_directory(path.parent)
        payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
        fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            prior = self._read_record(path)
            if not allow_identical or prior != record:
                raise RuntimeDispatchConstructionError(collision)
        except OSError as exc:
            raise RuntimeDispatchConstructionError("identity_record_create_failed") from exc
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def register(self, identity: RuntimeDispatchIdentity) -> None:
        invocation_record = {
            "invocation_id": identity.invocation_id,
            "idempotency_key": identity.idempotency_key,
        }
        self._create_or_compare(
            self._root / "invocations" / f"{identity.invocation_id}.json",
            invocation_record,
            collision=f"invocation_id_collision_conflicting_content:{identity.invocation_id}",
            allow_identical=True,
        )
        self._create_or_compare(
            self._root / "idempotency" / f"{identity.idempotency_key}.json",
            invocation_record,
            collision=(
                "idempotency_key_collision_different_invocation:"
                f"{identity.idempotency_key}"
            ),
            allow_identical=True,
        )
        self._create_or_compare(
            self._root / "attempts" / f"{identity.attempt_id}.json",
            {**invocation_record, "attempt_id": identity.attempt_id},
            collision=f"attempt_id_collision:{identity.attempt_id}",
            allow_identical=False,
        )

    def revalidate(self, identity: RuntimeDispatchIdentity) -> None:
        """Re-read and exactly match all three durable identity records.

        This is the B7 dispatch-time check, separate from construction-time
        registration.  Missing, substituted, extended, corrupt, linked, or
        symlinked state fails closed; no registry directory or record is
        recreated by revalidation.
        """

        if (
            type(identity) is not RuntimeDispatchIdentity
            or identity._identity_tracker is not self
            or identity._registration_digest != _identity_registration_digest(identity)
        ):
            raise RuntimeDispatchConstructionError("untrusted_runtime_dispatch_identity")
        invocation_record = {
            "invocation_id": identity.invocation_id,
            "idempotency_key": identity.idempotency_key,
        }
        expected_records = (
            (
                self._root / "invocations" / f"{identity.invocation_id}.json",
                invocation_record,
            ),
            (
                self._root / "idempotency" / f"{identity.idempotency_key}.json",
                invocation_record,
            ),
            (
                self._root / "attempts" / f"{identity.attempt_id}.json",
                {**invocation_record, "attempt_id": identity.attempt_id},
            ),
        )
        for path, expected in expected_records:
            self._require_directory(path.parent)
            if self._read_record(path) != expected:
                raise RuntimeDispatchConstructionError(
                    f"identity_registry_mismatch:{path.parent.name}"
                )


def project_human_authority_binding(
    validated_authority: ValidatedAuthorityProjection | None,
    *,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    current_time: str | None = None,
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
    if not is_trusted_validated_authority_projection(validated_authority):
        raise RuntimeDispatchConstructionError("untrusted_validated_authority_projection")
    if current_time is None or not revalidate_validated_authority_projection(
        validated_authority, current_time=current_time
    ):
        raise RuntimeDispatchConstructionError("stale_validated_authority_projection")
    expected_binding = _expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    if validated_authority.subject_scope_binding_digest != expected_binding:
        raise RuntimeDispatchConstructionError("validated_authority_subject_scope_mismatch")
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
    authority_current_time: str | None = None,
    simulation_only: bool = True,
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
    _validate_construction_inputs(inputs)
    if (
        type(identity) is not RuntimeDispatchIdentity
        or identity._identity_seal is not _RUNTIME_DISPATCH_IDENTITY_SEAL
        or identity._registration_digest != _identity_registration_digest(identity)
    ):
        raise RuntimeDispatchConstructionError("untrusted_runtime_dispatch_identity")
    if type(identity._identity_tracker) is not RuntimeDispatchIdentityTracker:
        raise RuntimeDispatchConstructionError("runtime_dispatch_identity_tracker_missing")
    if not is_valid_generated_id(identity.invocation_id, prefix="inv"):
        raise RuntimeDispatchConstructionError(f"invalid_invocation_id:{identity.invocation_id!r}")
    if not is_valid_generated_id(identity.attempt_id, prefix="att"):
        raise RuntimeDispatchConstructionError(f"invalid_attempt_id:{identity.attempt_id!r}")

    expected_key = compute_runtime_dispatch_idempotency_key(
        canonical_runtime_dispatch_projection(inputs, invocation_id=identity.invocation_id)
    )
    if identity.idempotency_key != expected_key:
        raise RuntimeDispatchConstructionError(
            "idempotency_key_does_not_match_canonical_content: "
            f"presented={identity.idempotency_key!r} expected={expected_key!r}"
        )

    # B7: identity construction is not cached authority.  Re-read the
    # append-only durable registry at the dispatch-request choke point.
    identity._identity_tracker.revalidate(identity)

    human_authority_binding, approval_present = project_human_authority_binding(
        validated_authority,
        identity=identity,
        inputs=inputs,
        current_time=authority_current_time,
    )

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
        network_requirement=inputs.network_requirement,
    )

    return _build_runtime_dispatch_permission_broker_request(
        requested_component=REQUESTED_COMPONENT_ADAPTER_BOUNDARY,
        requested_capability=inputs.requested_capability,
        task_id=inputs.task_id,
        phase_id=inputs.lifecycle_context.phase_id,
        requested_resource=None,
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=simulation_only,
        runtime_dispatch_context=facts,
    )
