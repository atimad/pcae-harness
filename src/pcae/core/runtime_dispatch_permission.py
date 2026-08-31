"""
Runtime Dispatch Permission — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.7,
extended by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.12 (Gate-6).

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

Gate 6 (Phase `.1R.12`, `.1R.9` §16.1 slice 2 / §16.2): `run_gate6_permission_broker`
is the frozen single owner of RDGO-001 v3.0 §7 Permission Broker
production consumption for `runtime_dispatch`. It consumes an
independently-verified Gate-5 `Gate5Result` (`runtime_dispatch_gate5.run_gate5`
success output — never a caller `Gate5Result`, a field-equivalent
reconstruction, a copy, or a bare `validated=true`), re-binds its
`ValidatedAuthorityProjection` to the exact canonical invocation through
the already-verified `.1R.7` trusted builder (which re-checks
`is_trusted_validated_authority_projection` + `revalidate_validated_authority_projection`
+ the subject/scope digest and performs the B7 dispatch-identity reread at
its own point of use), evaluates the request through the **unmodified**
Permission Broker evaluator, and returns exactly one ephemeral,
non-transferable `Gate6Decision`. Gate 6 authenticates no human, parses no
FIDO2 assertion, reads no HPAC registry, establishes no approval, creates
no HPAC / RIHAC authority, consumes no proof or approval, replicates no
DENY / HUMAN_REVIEW / ALLOW / POL rule, changes no policy, and dispatches
nothing. `DENY > HUMAN_REVIEW > ALLOW` precedence and the POL-005 hard DENY
of every `simulation_only=False` request are owned entirely by the PB
evaluator and are preserved unchanged. This module calls no Gate-7
(Runtime Enforcement), no Gate-8 (Shell Gate), no Gate-9 atomic-consumption
primitive, and no Gate-10 adapter / subprocess / provider / network /
credential / hardware operation; a PB `ALLOW` remains "policy would allow
this if execution existed", never runtime capability and never execution.
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
    ADMISSION_CLASS_UNADMITTED,
    DECISION_VALUES,
    PermissionBroker,
    PermissionBrokerDecision,
    PermissionBrokerRequest,
    RuntimeDispatchAdapterDescriptorBinding,
    RuntimeDispatchFilesystemScopeRef,
    RuntimeDispatchHumanAuthorityBinding,
    RuntimeDispatchLifecycleContext,
    RuntimeDispatchRequestFacts,
    _build_runtime_dispatch_permission_broker_request,
    derive_runtime_dispatch_local_cli_v1_classification,
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


# ═══════════════════════════════════════════════════════════════════════════
# N-16-6 supply-chain admission binding — INTERFACE + fail-closed stub
# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3). PBRD-001 v3.0 §12a /
# PBNDE-001. N-16-6 (RPAC-REQ-054 / -086 / -095) will later supply the real
# canonical supply-chain admission store and at least one admitted
# `local_fixed_argv` executable. Until then the ONLY production implementation
# is the non-admitting stub below: it admits NOTHING, so the
# `RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow profile stays UNSATISFIABLE in
# production (POL-013 DENYs on `P_supply_chain_admission`; POL-005 keeps its
# hard-DENY match). No public production parameter can flip this -- the
# resolver is a module-private default and the only override is the
# clearly-marked TEST-BOUNDARY `_supply_chain_admission_resolver` argument.
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SupplyChainAdmissionResult:
    """The outcome of resolving one adapter id against the (future) N-16-6
    canonical supply-chain admission store. `admitted=False` -> the request
    carries no admission binding and cannot classify as the narrow profile."""

    admitted: bool
    admission_record_digest: str
    admission_class: str


class SupplyChainAdmissionResolver:
    """N-16-6 INTERFACE. `resolve(adapter_id)` maps an adapter id to its
    canonical supply-chain admission record. The sole production
    implementation is :class:`_NonAdmittingSupplyChainAdmissionResolver`."""

    def resolve(self, adapter_id: str) -> SupplyChainAdmissionResult:  # pragma: no cover - interface
        raise NotImplementedError("n16_6_supply_chain_admission_resolver_not_implemented")


class _NonAdmittingSupplyChainAdmissionResolver(SupplyChainAdmissionResolver):
    """Fail-closed. Admits NOTHING for any adapter id. N-16-6's real
    admission store is not implemented; every adapter is `unadmitted`."""

    def resolve(self, adapter_id: str) -> SupplyChainAdmissionResult:
        return SupplyChainAdmissionResult(
            admitted=False,
            admission_record_digest="",
            admission_class=ADMISSION_CLASS_UNADMITTED,
        )


#: The single production N-16-6 resolver. Non-admitting by construction.
_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER: SupplyChainAdmissionResolver = (
    _NonAdmittingSupplyChainAdmissionResolver()
)


def _resolve_supply_chain_admission(
    adapter_id: str, resolver: SupplyChainAdmissionResolver | None
) -> SupplyChainAdmissionResult:
    """Resolve the admission binding for `adapter_id`. `resolver` is a
    TEST-BOUNDARY substitution only -- `None` (the sole production value)
    uses the fail-closed non-admitting resolver. A non-`SupplyChainAdmissionResolver`
    or a resolver returning a malformed / admitting-but-wrong-class result
    fails closed to `unadmitted`."""
    active = resolver if resolver is not None else _PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER
    if not isinstance(active, SupplyChainAdmissionResolver):
        return SupplyChainAdmissionResult(False, "", ADMISSION_CLASS_UNADMITTED)
    try:
        result = active.resolve(adapter_id)
    except Exception:
        return SupplyChainAdmissionResult(False, "", ADMISSION_CLASS_UNADMITTED)
    if type(result) is not SupplyChainAdmissionResult or not result.admitted:
        return SupplyChainAdmissionResult(False, "", ADMISSION_CLASS_UNADMITTED)
    if not (
        _digest_string(result.admission_record_digest)
        and isinstance(result.admission_class, str)
        and result.admission_class != ""
    ):
        return SupplyChainAdmissionResult(False, "", ADMISSION_CLASS_UNADMITTED)
    return result


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
        # PBRD-001 v3.0 §12a: the N-16-6 admission sub-fields are populated
        # ONLY by this module's trusted builder from the admission resolver.
        # A caller that pre-sets them on the construction input is rejected.
        and adapter.admission_record_digest == ""
        and adapter.admission_class == ""
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
    inputs: RuntimeDispatchRequestConstructionInput,
    *,
    invocation_id: str,
    _supply_chain_admission_resolver: SupplyChainAdmissionResolver | None = None,
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
            # PBRD-001 v3.0 §12a: the resolved N-16-6 admission binding is part
            # of the canonical request content. Deterministic per adapter id
            # (the production resolver admits nothing).
            "admission_record_digest": _resolve_supply_chain_admission(
                inputs.adapter_descriptor_binding.adapter_id, _supply_chain_admission_resolver
            ).admission_record_digest,
            "admission_class": _resolve_supply_chain_admission(
                inputs.adapter_descriptor_binding.adapter_id, _supply_chain_admission_resolver
            ).admission_class,
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
    _supply_chain_admission_resolver: SupplyChainAdmissionResolver | None = None,
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
            canonical_runtime_dispatch_projection(
                inputs,
                invocation_id=resolved_invocation_id,
                _supply_chain_admission_resolver=_supply_chain_admission_resolver,
            )
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
    _supply_chain_admission_resolver: SupplyChainAdmissionResolver | None = None,
) -> PermissionBrokerRequest:
    """The trusted, contract-fixed PCAE integration point for
    `runtime_dispatch` requests (PBRD-001 §5). Only this function may
    construct a `RuntimeDispatchRequestFacts`-bearing
    `PermissionBrokerRequest`; there is no generic/dict-based construction
    path an adapter or caller payload could use to set any of the fourteen
    facts directly.

    `simulation_only` defaults to `True` (policy-evaluable without a real
    dispatch attempt). Passing `False` models a real, non-simulation
    request -- POL-005 (PBRD-001 v3.0 §12a) still denies it unless it is the
    fully bound, trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile,
    which is unsatisfiable in production.

    `_supply_chain_admission_resolver` is a TEST-BOUNDARY substitution ONLY.
    Its sole production value is `None` -> the fail-closed non-admitting
    N-16-6 resolver. No public parameter can flip an adapter to `admitted`;
    this argument is underscore-private, documented as test-only, and is the
    exact isolation boundary PBNDE-001 §7 requires.
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
        canonical_runtime_dispatch_projection(
            inputs,
            invocation_id=identity.invocation_id,
            _supply_chain_admission_resolver=_supply_chain_admission_resolver,
        )
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

    # PBRD-001 v3.0 §12a: resolve the N-16-6 supply-chain admission binding
    # for the executable and stamp it onto the adapter descriptor binding.
    # Caller-supplied admission fields were already rejected by
    # `_validate_construction_inputs`; the resolved values are the trusted
    # ones. The production resolver admits nothing.
    admission = _resolve_supply_chain_admission(
        inputs.adapter_descriptor_binding.adapter_id, _supply_chain_admission_resolver
    )
    admitted_adapter_binding = replace(
        inputs.adapter_descriptor_binding,
        admission_record_digest=admission.admission_record_digest,
        admission_class=admission.admission_class,
    )

    facts = RuntimeDispatchRequestFacts(
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
        idempotency_key=identity.idempotency_key,
        repository_identity=inputs.repository_identity,
        task_id=inputs.task_id,
        lifecycle_context=inputs.lifecycle_context,
        runtime_target_id=inputs.runtime_target_id,
        adapter_descriptor_binding=admitted_adapter_binding,
        prompt_hash=inputs.prompt_hash,
        requested_capability=inputs.requested_capability,
        filesystem_scope_ref=inputs.filesystem_scope_ref,
        human_authority_binding=human_authority_binding,
        network_requirement=inputs.network_requirement,
    )

    def _assemble(context: RuntimeDispatchRequestFacts) -> PermissionBrokerRequest:
        return _build_runtime_dispatch_permission_broker_request(
            requested_component=REQUESTED_COMPONENT_ADAPTER_BOUNDARY,
            requested_capability=inputs.requested_capability,
            task_id=inputs.task_id,
            phase_id=inputs.lifecycle_context.phase_id,
            requested_resource=None,
            evidence_available=True,
            approval_present=approval_present,
            simulation_only=simulation_only,
            runtime_dispatch_context=context,
        )

    # PBRD-001 v3.0 §12a: derive the narrow-profile classification LAST, from
    # the fully bound provisional request. Never accepted as caller input.
    provisional = _assemble(facts)
    marker = derive_runtime_dispatch_local_cli_v1_classification(provisional)
    if not marker:
        return provisional
    return _assemble(replace(facts, profile_classification=marker))


# ═══════════════════════════════════════════════════════════════════════════
# Gate 6 — Permission Broker production consumption
# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.12 (RDGO-001 v3.0 §7 / PBRD-001 v2.0
# §7, §9, §10, §14 / `.1R.9` §16.1 slice 2, §16.2, §22).
# ═══════════════════════════════════════════════════════════════════════════

_GATE6_DECISION_CONSTRUCTOR_SEAL = object()

#: The provenance boundary for a Gate-6 decision: exact-object membership,
#: keyed by identity (`Gate6Decision.__hash__`/`__eq__` are `id(self)` /
#: `self is other`). The only insertion point is
#: :func:`run_gate6_permission_broker`'s success return path; nothing
#: outside this module adds to it.
_GATE6_DECISIONS: "set[Gate6Decision]" = set()


class Gate6Decision:
    """The ephemeral, non-transferable evidence Gate 6 emits after the
    Permission Broker evaluates one `runtime_dispatch` request (`.1R.9` §8
    discipline, applied to the Gate-6 output; PBRD-001 §5/§9).

    It wraps the immutable :class:`PermissionBrokerDecision` returned by the
    unmodified evaluator and normalises the fields a caller needs
    (`decision`, `causing_policy_ids`, `matched_no_go_ids`, `requires_human`,
    `approval_present`). Like ``Gate5Result`` / ``ValidatedAuthorityProjection``
    / ``AuthenticatedHumanPrincipal`` this type is:

    * **not** caller-constructable — the ``_seal`` guard rejects direct
      construction, and :func:`is_gate6_decision` checks membership in this
      module's process-local identity registry, which only
      :func:`run_gate6_permission_broker`'s own success path populates;
    * **not** serializable — ``__reduce__`` raises;
    * identity-only for ``==`` / ``hash`` — a copy, ``deepcopy``, or
      field-reconstructed lookalike is a different object and is never a
      registry member, whatever its fields say;
    * **not** an execution token — an ``ALLOW`` here means only "PB policy
      would permit this if execution existed" (``implementation_status``
      stays ``execution_unavailable``). It is not runtime capability, not
      Runtime Enforcement approval, not process containment, and not
      dispatch permission (PBRD-001 §10, §11). A later gate consumes it only
      through its own coordinator path, re-resolving the authority freshly.
    """

    __slots__ = (
        "_pb_decision",
        "decision",
        "decision_reason",
        "approval_present",
        "invocation_id",
        "attempt_id",
        "request_id",
        "causing_policy_ids",
        "matched_no_go_ids",
        "requires_human",
        "simulation_only",
        "evaluated_at",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Gate6Decision must not be subclassed")

    def __init__(
        self,
        *,
        pb_decision: PermissionBrokerDecision,
        approval_present: bool,
        invocation_id: str,
        attempt_id: str,
        request_id: str,
        simulation_only: bool,
        evaluated_at: str,
        _seal: object,
    ) -> None:
        if _seal is not _GATE6_DECISION_CONSTRUCTOR_SEAL:
            raise TypeError(
                "Gate6Decision cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_permission.run_gate6_permission_broker"
            )
        self._pb_decision = pb_decision
        self.decision = pb_decision.decision
        self.decision_reason = pb_decision.decision_reason
        self.approval_present = approval_present
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.request_id = request_id
        self.causing_policy_ids = tuple(pb_decision.causing_policy_ids)
        self.matched_no_go_ids = tuple(pb_decision.matched_no_go_ids)
        self.requires_human = bool(pb_decision.requires_human)
        self.simulation_only = simulation_only
        self.evaluated_at = evaluated_at
        self._seal = _seal

    @property
    def pb_decision(self) -> PermissionBrokerDecision:
        """The immutable evaluator result. Reading it is not authority — a
        PB ``ALLOW`` never authorises execution (PBRD-001 §10/§11)."""
        return self._pb_decision

    def __reduce__(self):
        raise TypeError(
            "Gate6Decision is ephemeral and non-serializable; the Permission "
            "Broker must be re-evaluated over a freshly re-resolved Gate-5 "
            "projection by every consumer (PBRD-001 §7, §10)"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<Gate6Decision decision={self.decision!r} "
            f"invocation_id={self.invocation_id!r} identity={id(self):#x}>"
        )


def is_gate6_decision(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past
    :func:`run_gate6_permission_broker` call returned on success — never
    based on ``isinstance``, fields, equality, or any shape property. Fails
    closed for a forgery, a copy, a reconstruction, or a stale handle."""
    return isinstance(candidate, Gate6Decision) and candidate in _GATE6_DECISIONS


def run_gate6_permission_broker(
    gate5_result: object,
    *,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    authority_current_time: str,
    simulation_only: bool = False,
    broker: PermissionBroker | None = None,
) -> tuple[Gate6Decision | None, tuple[str, ...]]:
    """Run RDGO-001 v3.0 Gate 6 (Permission Broker production consumption)
    for one ``runtime_dispatch`` request.

    Gate 6 consumes already-validated authority and produces a PB decision
    only. It:

    1. accepts ``gate5_result`` **only** if :func:`runtime_dispatch_gate5.is_gate5_result`
       vouches for it — the exact identity object a prior successful
       ``run_gate5`` returned. A caller-built ``Gate5Result``, a
       field-equivalent reconstruction, a copy, a serialized clone, a bare
       ``validated=true`` object, or a caller-provided ``ValidatedAuthorityProjection``
       all fail closed here (RDGO-001 §7; PBRD-001 §7; the B1 defect class);
    2. re-binds the referenced projection to the exact canonical invocation
       — ``gate5_result.invocation_id`` must equal ``identity.invocation_id``,
       and (inside the trusted builder) the projection's
       ``subject_scope_binding_digest`` must equal the digest recomputed from
       ``identity`` + ``inputs``. Gate-5 authority for invocation A cannot
       drive a PB request for invocation B, and no changed permission-relevant
       field is accepted (PBRD-001 §15; RDGO-001 §7);
    3. constructs the ``PermissionBrokerRequest`` through the already-verified
       ``.1R.7`` trusted builder only — never from a caller-supplied request.
       The builder re-checks ``is_trusted_validated_authority_projection`` and
       re-runs ``revalidate_validated_authority_projection`` at its own point
       of use, and performs the B7 durable dispatch-identity reread. A stale,
       mutated, or untrusted projection yields request-construction failure,
       reported here as a fail-closed reason (PBRD-001 §7);
    4. evaluates the request through the **unmodified** Permission Broker
       evaluator. The evaluator owns every policy semantic — POL-005's hard
       DENY of each ``simulation_only=False`` request (never overridden by
       validated human authority), POL-004's HUMAN_REVIEW when no
       ``approval_present``, and the ``DENY > HUMAN_REVIEW > ALLOW``
       precedence. Gate 6 replicates none of it and introduces no
       caller-controlled precedence (PBRD-001 §9, §12; RDGO-001 §7);
    5. returns exactly one ephemeral, non-transferable :class:`Gate6Decision`
       on success, or ``(None, reasons)`` on any fail-closed rejection —
       creating no ``Gate6Decision`` and consuming nothing.

    ``simulation_only`` defaults to ``False`` (a real local-CLI request);
    with the frozen POL-005 that truthfully produces ``DENY`` (PBRD-001 §4,
    §12). Passing ``True`` models a policy simulation.

    Gate 6 consumes nothing: no approval, proof, presentation, challenge, or
    nonce state changes, and no ``consumption.json`` is created (RDGO-001 §7;
    PBRD-001 §7 "PB evaluation never consumes an approval or HPAC proof").
    It calls no Gate-7, Gate-8, Gate-9, or Gate-10 primitive.
    """
    # 1. Provenance — only the exact object a successful run_gate5 returned.
    from .runtime_dispatch_gate5 import Gate5Result, is_gate5_result

    if not is_gate5_result(gate5_result):
        return None, ("gate6_untrusted_gate5_result",)
    assert isinstance(gate5_result, Gate5Result)

    if type(identity) is not RuntimeDispatchIdentity:
        return None, ("gate6_untrusted_runtime_dispatch_identity",)
    if type(inputs) is not RuntimeDispatchRequestConstructionInput:
        return None, ("gate6_invalid_construction_input",)
    if not _bounded_string(authority_current_time, 64):
        return None, ("gate6_invalid_authority_current_time",)
    if type(simulation_only) is not bool:
        return None, ("gate6_invalid_simulation_only",)

    # 2. Exact invocation binding (the subject/scope digest is re-checked
    #    inside the trusted builder; this is the precise invocation-id guard).
    if gate5_result.invocation_id != identity.invocation_id:
        return None, ("gate6_invocation_binding_mismatch",)

    # 3. Build the request through the trusted .1R.7 builder ONLY. Authority
    #    derives from the registry-provenanced projection the Gate-5 result
    #    references — never from a caller-supplied request or boolean. The
    #    builder re-resolves is_trusted_validated_authority_projection +
    #    revalidate_validated_authority_projection + the subject/scope digest
    #    and performs the B7 dispatch-identity reread at its own point of use.
    projection = gate5_result.projection
    try:
        request = build_runtime_dispatch_permission_broker_request(
            identity=identity,
            inputs=inputs,
            validated_authority=projection,
            authority_current_time=authority_current_time,
            simulation_only=simulation_only,
        )
    except RuntimeDispatchConstructionError as exc:
        return None, (f"gate6_request_construction_failed:{exc}",)

    # 4. Evaluate through the UNMODIFIED Permission Broker evaluator. Gate 6
    #    owns only trusted request construction and the normalised decision
    #    envelope; all DENY / HUMAN_REVIEW / ALLOW / POL semantics and the
    #    DENY > HUMAN_REVIEW > ALLOW precedence stay in the evaluator.
    evaluator = broker if broker is not None else PermissionBroker()
    if type(evaluator) is not PermissionBroker:
        return None, ("gate6_untrusted_permission_broker",)
    pb_decision = evaluator.evaluate(request)
    if (
        type(pb_decision) is not PermissionBrokerDecision
        or pb_decision.decision not in DECISION_VALUES
    ):
        return None, ("gate6_invalid_permission_broker_decision",)

    result = Gate6Decision(
        pb_decision=pb_decision,
        approval_present=request.approval_present,
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
        request_id=request.request_id,
        simulation_only=request.simulation_only,
        evaluated_at=authority_current_time,
        _seal=_GATE6_DECISION_CONSTRUCTOR_SEAL,
    )
    _GATE6_DECISIONS.add(result)
    return result, ()
