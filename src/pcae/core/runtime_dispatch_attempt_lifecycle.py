"""
Dispatch-Attempt Durable Lifecycle — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19
(Slice B of the ``.1R.16`` Gate-10 plan).

This module implements the **non-authoritative, append-only repository-side
mirror** the ``.1R.16`` architecture (§20, §22, §24, §36) calls for: a
persistent ``RuntimeInvocationRecord`` (RPAC-REQ-067) carrying the
dispatch-attempt state-transition log

    PREPARED
       -> EFFECT_ATTEMPT_STARTED
             -> RECEIPT_CAPTURED        (terminal)
             -> DISPATCH_UNCERTAIN      (terminal)
       -> DISPATCH_NOT_STARTED          (terminal)

plus the **write-before-effect at-most-once dispatch-attempt guard**, the
crash / restart determination, and the deterministic idempotency identity.

**Semantic wall (``.1R.16`` §5 / §20 / §33; phase prompt §5).**
``RuntimeInvocationRecord != permission != human approval != PB ALLOW !=
runtime capability != authorization to dispatch``. It is a durable
*evidence / coordination* record. Possessing, reconstructing, copying, or
parsing one grants **nothing**. The authoritative at-most-once
authority-consumption truth stays the create-only, immutable
``consumption.json`` (``HPAC-AUTHORITY-CONSUMPTION/2.1``) that Gate 9
writes; this mirror never authorizes an effect and this module contains
**no** ``adapter.dispatch()`` call site, spawns **no** process, opens
**no** socket, and imports **no** external-effect primitive.

**Guarantee (``.1R.16`` §25.1; phase prompt §10 / §11).** PCAE guarantees
**at-most-once dispatch attempt with fail-closed uncertainty** — *not*
generic exactly-once external effect. Once ``EFFECT_ATTEMPT_STARTED`` is
durable for an attempt identity: automatic duplicate dispatch is
prohibited; a restart observes that durable fact; an unresolved attempt
resolves to ``DISPATCH_UNCERTAIN`` and never retries automatically.

**Write-before-effect (Model A + Model C; ``.1R.16`` §22.2).** The durable
``EFFECT_ATTEMPT_STARTED`` transition is written **before** any future
external effect boundary (which is Slice C and is NOT present here):

    PREPARED persisted
      -> EFFECT_ATTEMPT_STARTED persisted
      -> [future first external effect — NOT IN THIS PHASE]

Model A's failure mode (a false "attempted" after a crash) is fail-closed
(``DISPATCH_UNCERTAIN`` + fresh human authority); Model B's (a duplicate
external effect) is fail-open and is rejected.

**Append-only (``.1R.16`` §22.3; phase prompt §15 / §16).** Every
transition is an immutable, digest-chained observation written through a
create-only ``O_EXCL``-class primitive. There is no mutable state machine
that can go backwards or erase a prior ``EFFECT_ATTEMPT_STARTED``.
``RECEIPT_CAPTURED`` / ``DISPATCH_UNCERTAIN`` / ``DISPATCH_NOT_STARTED``
are terminal.

**F7 boundary (carried verbatim from ``runtime_dispatch_gate9.py``; threat
model NOT broadened).** This module resists caller-supplied **data**
forgery of the durable record (reconstruction, copy, a schema-valid
document planted outside the store) — a reconstructed record authorizes
nothing because nothing here consults it for authority. It does **not**
resist arbitrary same-process Python code execution. Process isolation is
a separate, unscheduled topic.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

from pcae.core.hpac_foundation import (
    HPACMalformedError,
    canonical_digest,
    read_canonical_json_document,
    reject_symlink,
    require_safe_relative_id_component,
)

__all__ = [
    "DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION",
    "PREPARED",
    "EFFECT_ATTEMPT_STARTED",
    "RECEIPT_CAPTURED",
    "DISPATCH_UNCERTAIN",
    "DISPATCH_NOT_STARTED",
    "DISPATCH_ATTEMPT_STATES",
    "DISPATCH_ATTEMPT_TERMINAL_STATES",
    "DISPATCH_ATTEMPT_TRANSITIONS",
    "DispatchAttemptLifecycleError",
    "DispatchAttemptIntegrityError",
    "DispatchAttemptTransitionError",
    "DispatchAttemptAlreadyStartedError",
    "RuntimeInvocationRecordBinding",
    "RuntimeInvocationRecord",
    "DispatchAttemptTransition",
    "DispatchAttemptDisposition",
    "RuntimeInvocationRecordStore",
    "derive_dispatch_attempt_record_id",
    "record_grants_no_effect_authority",
]

#: Closed schema identity stamped into every mirror record header. Additive
#: evolution requires a new MINOR (RPAC-REQ-067 names every field below).
DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION = "RPAC-RUNTIME-INVOCATION-RECORD/1.0"

#: Repository-local store root (never the HPAC protected root — this is a
#: non-authoritative mirror, ``.1R.16`` §22.3).
_STORE_ROOT = Path(".pcae") / "runtime-dispatch-attempts"


# ═══════════════════════════════════════════════════════════════════════
# State model (``.1R.16`` §22.3; phase prompt §6 / §16 / §17 / §18 / §19)
# ═══════════════════════════════════════════════════════════════════════

PREPARED = "PREPARED"
EFFECT_ATTEMPT_STARTED = "EFFECT_ATTEMPT_STARTED"
RECEIPT_CAPTURED = "RECEIPT_CAPTURED"
DISPATCH_UNCERTAIN = "DISPATCH_UNCERTAIN"
DISPATCH_NOT_STARTED = "DISPATCH_NOT_STARTED"

DISPATCH_ATTEMPT_STATES: frozenset[str] = frozenset(
    {
        PREPARED,
        EFFECT_ATTEMPT_STARTED,
        RECEIPT_CAPTURED,
        DISPATCH_UNCERTAIN,
        DISPATCH_NOT_STARTED,
    }
)

#: Terminal states: no successor transition is ever valid from them
#: (``.1R.16`` §22.3 "``DISPATCH_UNCERTAIN`` and ``DISPATCH_NOT_STARTED``
#: are terminal"; ``RECEIPT_CAPTURED`` is likewise a terminal mirror
#: state — a captured receipt hands off to Gate 11 intake, never a new
#: attempt).
DISPATCH_ATTEMPT_TERMINAL_STATES: frozenset[str] = frozenset(
    {RECEIPT_CAPTURED, DISPATCH_UNCERTAIN, DISPATCH_NOT_STARTED}
)

#: The exact allowed ``source -> {destinations}`` transition map. ``None``
#: is the pre-lifecycle (no transition yet) source. Anything not in this
#: map is rejected: backwards transitions, terminal mutation, duplicate
#: terminal transitions, and skipping a required state.
DISPATCH_ATTEMPT_TRANSITIONS: Mapping[Optional[str], frozenset[str]] = {
    None: frozenset({PREPARED}),
    PREPARED: frozenset({EFFECT_ATTEMPT_STARTED, DISPATCH_NOT_STARTED}),
    EFFECT_ATTEMPT_STARTED: frozenset({RECEIPT_CAPTURED, DISPATCH_UNCERTAIN}),
    RECEIPT_CAPTURED: frozenset(),
    DISPATCH_UNCERTAIN: frozenset(),
    DISPATCH_NOT_STARTED: frozenset(),
}


# ═══════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════


class DispatchAttemptLifecycleError(Exception):
    """Base class for every dispatch-attempt-lifecycle failure. Callers
    SHALL treat any subclass as fail-closed and never auto-repair or
    auto-redispatch."""


class DispatchAttemptIntegrityError(DispatchAttemptLifecycleError):
    """A conflicting / corrupt / truncated persisted record or transition,
    or an id-collision with different content. Quarantine; never reuse
    (RPAC-REQ-069)."""


class DispatchAttemptTransitionError(DispatchAttemptLifecycleError):
    """A requested state transition is not in
    :data:`DISPATCH_ATTEMPT_TRANSITIONS` for the current durable state
    (backwards, terminal-mutating, duplicate-terminal, or state-skipping)."""


class DispatchAttemptAlreadyStartedError(DispatchAttemptLifecycleError):
    """The write-before-effect at-most-once guard fired: an
    ``EFFECT_ATTEMPT_STARTED`` transition is already durable for this
    attempt identity, so a second attempt to start is rejected
    (``.1R.16`` §25.1; phase prompt §10 / §26 / §27)."""


# ═══════════════════════════════════════════════════════════════════════
# Attempt identity (``.1R.16`` §12 / §25.3; phase prompt §12 / §13)
# ═══════════════════════════════════════════════════════════════════════


def derive_dispatch_attempt_record_id(invocation_id: str, attempt_id: str) -> str:
    """A deterministic, restart-stable mirror-record identity derived
    purely from ``(invocation_id, attempt_id)`` — the same pair that keys
    the consumed attempt at Gate 9 (``.1R.16`` §25.3). No wall clock, no
    mtime, no nonce, no process id enters it, so a fresh process
    reconstructs the identical id from durable state alone (phase prompt
    §13 / §16 / §20 / §45)."""
    if not isinstance(invocation_id, str) or not invocation_id:
        raise DispatchAttemptIntegrityError("invocation_id must be a non-empty string")
    if not isinstance(attempt_id, str) or not attempt_id:
        raise DispatchAttemptIntegrityError("attempt_id must be a non-empty string")
    digest = canonical_digest(
        {"invocation_id": invocation_id, "attempt_id": attempt_id}
    )
    return "dar-" + digest[:32]


# ═══════════════════════════════════════════════════════════════════════
# RuntimeInvocationRecord — the non-authoritative durable mirror header
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RuntimeInvocationRecordBinding:
    """The immutable identity/lineage binding a trusted Gate-10 caller
    supplies when it opens the mirror record. Every value is PCAE-derived
    (from the ``DispatchEnvelope`` and the durable ``consumption.json``),
    never adapter / runtime / result input (RPAC-REQ-067 / RPAC-REQ-078)."""

    invocation_id: str
    attempt_id: str
    idempotency_key: str
    proof_id: str
    approval_id: str
    runtime_target_id: str
    adapter_id: str
    task_id: str
    consumption_record_digest: str
    envelope_digest: str

    def _fields(self) -> dict:
        return {
            "invocation_id": self.invocation_id,
            "attempt_id": self.attempt_id,
            "idempotency_key": self.idempotency_key,
            "proof_id": self.proof_id,
            "approval_id": self.approval_id,
            "runtime_target_id": self.runtime_target_id,
            "adapter_id": self.adapter_id,
            "task_id": self.task_id,
            "consumption_record_digest": self.consumption_record_digest,
            "envelope_digest": self.envelope_digest,
        }

    def __post_init__(self) -> None:
        for name, value in self._fields().items():
            if not isinstance(value, str) or not value or value != value.strip():
                raise DispatchAttemptIntegrityError(
                    f"binding.{name} must be a non-empty, unpadded string"
                )
            if len(value) > 512:
                raise DispatchAttemptIntegrityError(f"binding.{name} exceeds 512 chars")


@dataclass(frozen=True)
class RuntimeInvocationRecord:
    """The durable, non-authoritative mirror-record header (RPAC-REQ-067).

    **It authorizes nothing.** There is deliberately no ``approve`` /
    ``authorize`` / ``permit`` / ``grant`` / ``consume`` method and no
    ``execution_allowed`` / ``permission`` / ``authorized`` field;
    :data:`GRANTS_NO_EFFECT_AUTHORITY` is a permanent, load-bearing marker
    and :func:`record_grants_no_effect_authority` always returns ``True``.
    The durable authoritative truth is ``consumption.json`` — every
    consumer re-reads it (RDGO-001 v3.1 §11)."""

    #: Load-bearing invariant, asserted by the ``.1R.19`` suite.
    GRANTS_NO_EFFECT_AUTHORITY: bool = field(default=True, init=False, repr=False)

    record_schema_version: str
    record_id: str
    binding: RuntimeInvocationRecordBinding
    created_at: str
    record_integrity_digest: str

    def to_reference_document(self) -> dict:
        """A plain-``dict`` projection for audit display. Reconstructing
        this dict grants nothing (there is no trust registry to join, and
        the record authorizes no effect regardless)."""
        return {
            "record_schema_version": self.record_schema_version,
            "record_id": self.record_id,
            "binding": self.binding._fields(),
            "created_at": self.created_at,
            "record_integrity_digest": self.record_integrity_digest,
            "grants_no_effect_authority": True,
        }


def record_grants_no_effect_authority(record: object) -> bool:
    """Always ``True``. A :class:`RuntimeInvocationRecord` — genuine,
    copied, or reconstructed — never authorizes an external effect
    (``.1R.16`` §5 / §20; phase prompt §5 / §18 / §19)."""
    return True


@dataclass(frozen=True)
class DispatchAttemptTransition:
    """One append-only, digest-chained dispatch-attempt state observation
    (RPAC-REQ-040-style, mirroring
    ``runtime_invocation.SimulationStateObservation``). ``sequence`` is
    1-based; ``prior_digest`` chains to the previous transition's own
    :meth:`digest` (or ``None`` for the first), so any reordering,
    insertion, or tampering is detectable independent of storage."""

    sequence: int
    state: str
    observed_at: str
    prior_digest: Optional[str]
    detail: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in DISPATCH_ATTEMPT_STATES:
            raise DispatchAttemptTransitionError(f"not_a_dispatch_attempt_state:{self.state}")
        if not isinstance(self.sequence, int) or self.sequence < 1:
            raise DispatchAttemptIntegrityError("transition.sequence must be a positive int")
        if not isinstance(self.observed_at, str) or not self.observed_at:
            raise DispatchAttemptIntegrityError("transition.observed_at must be a non-empty string")
        object.__setattr__(self, "detail", dict(self.detail))

    def digest(self) -> str:
        return canonical_digest(
            {
                "sequence": self.sequence,
                "state": self.state,
                "observed_at": self.observed_at,
                "prior_digest": self.prior_digest,
                "detail": self.detail,
            }
        )


def next_dispatch_attempt_transition(
    prior: Optional[DispatchAttemptTransition],
    state: str,
    observed_at: str,
    detail: Optional[Mapping[str, object]] = None,
) -> DispatchAttemptTransition:
    """Build the transition that follows ``prior`` (or the first if
    ``prior is None``), enforcing :data:`DISPATCH_ATTEMPT_TRANSITIONS`
    exactly. Rejects a backwards move, a move out of a terminal state, a
    duplicate terminal, and any state skip."""
    source = prior.state if prior is not None else None
    allowed = DISPATCH_ATTEMPT_TRANSITIONS.get(source, frozenset())
    if state not in allowed:
        raise DispatchAttemptTransitionError(
            f"invalid_transition:{source}->{state}"
        )
    return DispatchAttemptTransition(
        sequence=(prior.sequence + 1) if prior is not None else 1,
        state=state,
        observed_at=observed_at,
        prior_digest=prior.digest() if prior is not None else None,
        detail=dict(detail or {}),
    )


# ═══════════════════════════════════════════════════════════════════════
# Crash / restart disposition (``.1R.16`` §22.1 / §31; phase prompt §20-§25)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DispatchAttemptDisposition:
    """The determination a restarted process derives from durable state
    **only** (never process memory). ``automatic_retry_permitted`` is
    ``False`` for every state once a record exists — the objective is
    at-most-once *attempt*, and any prior consumed authority is spent
    (``.1R.16`` §14 / §15; RDGO-001 v3.1 §18)."""

    record_id: str
    durable_state: str  # "none" or a member of DISPATCH_ATTEMPT_STATES
    disposition: str
    terminal: bool
    automatic_retry_permitted: bool
    fresh_human_authority_required: bool
    external_effect_possible: bool
    detail: str

    #: Disposition constants — aligned with RDGO-001 v3.1 §17 crash states.
    NOT_STARTED = "not_started"
    DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER = "DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER"
    DISPATCH_UNCERTAIN = "DISPATCH_UNCERTAIN"
    RECEIPT_CAPTURED = "RECEIPT_CAPTURED"
    DISPATCH_NOT_STARTED = "DISPATCH_NOT_STARTED"


# ═══════════════════════════════════════════════════════════════════════
# The append-only mirror store
# ═══════════════════════════════════════════════════════════════════════


def _require_safe_component(value: object, *, context: str) -> str:
    try:
        return require_safe_relative_id_component(value, context=context)
    except HPACMalformedError as exc:
        raise DispatchAttemptIntegrityError(
            f"unsafe_path_component:{context}:{exc}"
        ) from exc


class RuntimeInvocationRecordStore:
    """Append-only, create-only, repository-local persistence for the
    non-authoritative dispatch-attempt mirror record. Every document is
    written once through an ``O_EXCL``-class primitive
    (``write_atomic_create_only``) and never mutated in place, so a
    concurrent race to create a record or to start an attempt has exactly
    one winner and every loser fails closed (``.1R.16`` §22.3 / §25.1;
    phase prompt §27).

    Layout, one directory per ``(invocation_id, attempt_id)`` identity::

        .pcae/runtime-dispatch-attempts/<record_id>/record.json
        .pcae/runtime-dispatch-attempts/<record_id>/transitions/0001-prepared.json
        .pcae/runtime-dispatch-attempts/<record_id>/transitions/0002-effect_attempt_started.json
        ...
    """

    def __init__(self, root: Path):
        self._root = Path(root) / _STORE_ROOT

    # ── path helpers ────────────────────────────────────────────────
    def _record_dir(self, record_id: str) -> Path:
        return self._root / _require_safe_component(record_id, context="record_id")

    def _record_path(self, record_id: str) -> Path:
        return self._record_dir(record_id) / "record.json"

    def _transitions_dir(self, record_id: str) -> Path:
        return self._record_dir(record_id) / "transitions"

    def _assert_within_root(self, path: Path) -> None:
        root = self._root.resolve(strict=False)
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise DispatchAttemptIntegrityError(
                f"path_escapes_store_root:{path}"
            ) from exc

    def _write_create_only(self, path: Path, document: Mapping[str, object]) -> None:
        """Atomically create ``path`` with ``document`` or fail closed if it
        already exists. Uses ``O_CREAT | O_EXCL`` on a temp sibling followed
        by ``os.link`` into the absent final name, so a concurrent race to
        create the same path has exactly one winner (``.1R.16`` §25.1;
        phase prompt §27). This is a repository-side mirror, not the HPAC
        protected root, so it does not reject a symlink in an *ancestor*
        path component (temp roots under ``/var`` on macOS are symlinks);
        it does reject a symlink at the final name."""
        self._assert_within_root(path)
        directory = path.parent
        directory.mkdir(parents=True, exist_ok=True)
        reject_symlink(path)
        if path.exists():
            raise DispatchAttemptIntegrityError(f"record_already_exists:{path}")
        data = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        tmp = directory / (path.name + f".tmp-{os.getpid()}-{os.urandom(4).hex()}")
        try:
            fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                os.write(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            try:
                os.link(tmp, path)
            except FileExistsError as exc:
                raise DispatchAttemptIntegrityError(
                    f"record_already_exists:{path}"
                ) from exc
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    # ── record header ──────────────────────────────────────────────
    def _record_integrity_digest(
        self, binding: RuntimeInvocationRecordBinding, created_at: str
    ) -> str:
        return canonical_digest(
            {
                "record_schema_version": DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
                "binding": binding._fields(),
                "created_at": created_at,
            }
        )

    def create_record(
        self, binding: RuntimeInvocationRecordBinding, *, created_at: str
    ) -> RuntimeInvocationRecord:
        """Open the immutable mirror-record header for one attempt identity,
        or — if an identical one already exists — return it (RPAC-REQ-066
        idempotent resume). A same ``record_id`` with any different bound
        content is a hard collision and fails closed
        (``DispatchAttemptIntegrityError``)."""
        if not isinstance(binding, RuntimeInvocationRecordBinding):
            raise DispatchAttemptIntegrityError("binding must be a RuntimeInvocationRecordBinding")
        if not isinstance(created_at, str) or not created_at:
            raise DispatchAttemptIntegrityError("created_at must be a non-empty string")
        record_id = derive_dispatch_attempt_record_id(
            binding.invocation_id, binding.attempt_id
        )
        integrity_digest = self._record_integrity_digest(binding, created_at)
        existing = self.read_record(record_id)
        if existing is not None:
            if existing.record_integrity_digest != integrity_digest:
                raise DispatchAttemptIntegrityError(
                    f"id_collision_conflicting_content:{record_id}"
                )
            return existing
        document = {
            "record_schema_version": DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
            "record_id": record_id,
            "binding": binding._fields(),
            "created_at": created_at,
            "record_integrity_digest": integrity_digest,
            "grants_no_effect_authority": True,
        }
        self._write_create_only(self._record_path(record_id), document)
        return RuntimeInvocationRecord(
            record_schema_version=DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION,
            record_id=record_id,
            binding=binding,
            created_at=created_at,
            record_integrity_digest=integrity_digest,
        )

    def read_record(self, record_id: str) -> Optional[RuntimeInvocationRecord]:
        path = self._record_path(record_id)
        if not path.exists():
            return None
        reject_symlink(path)
        try:
            document = read_canonical_json_document(path)
        except Exception as exc:  # noqa: BLE001 - corrupt on-disk record fails closed
            raise DispatchAttemptIntegrityError(
                f"unreadable_record:{record_id}:{type(exc).__name__}"
            ) from exc
        if not isinstance(document, dict):
            raise DispatchAttemptIntegrityError(f"malformed_record:{record_id}")
        try:
            b = document["binding"]
            binding = RuntimeInvocationRecordBinding(
                invocation_id=b["invocation_id"],
                attempt_id=b["attempt_id"],
                idempotency_key=b["idempotency_key"],
                proof_id=b["proof_id"],
                approval_id=b["approval_id"],
                runtime_target_id=b["runtime_target_id"],
                adapter_id=b["adapter_id"],
                task_id=b["task_id"],
                consumption_record_digest=b["consumption_record_digest"],
                envelope_digest=b["envelope_digest"],
            )
            record = RuntimeInvocationRecord(
                record_schema_version=document["record_schema_version"],
                record_id=document["record_id"],
                binding=binding,
                created_at=document["created_at"],
                record_integrity_digest=document["record_integrity_digest"],
            )
        except (KeyError, TypeError, DispatchAttemptLifecycleError) as exc:
            raise DispatchAttemptIntegrityError(
                f"malformed_record:{record_id}:{exc}"
            ) from exc
        if record.record_id != record_id:
            raise DispatchAttemptIntegrityError(f"record_id_mismatch:{record_id}")
        if record.record_schema_version != DISPATCH_ATTEMPT_RECORD_SCHEMA_VERSION:
            raise DispatchAttemptIntegrityError(
                f"unknown_record_schema_version:{record.record_schema_version}"
            )
        if self._record_integrity_digest(binding, record.created_at) != (
            record.record_integrity_digest
        ):
            raise DispatchAttemptIntegrityError(
                f"record_integrity_digest_mismatch:{record_id}"
            )
        return record

    # ── transition log ────────────────────────────────────────────
    def list_transitions(self, record_id: str) -> list[dict]:
        directory = self._transitions_dir(record_id)
        if not directory.exists():
            return []
        files = sorted(
            p for p in directory.glob("[0-9][0-9][0-9][0-9]-*.json") if p.is_file()
        )
        transitions: list[dict] = []
        for index, path in enumerate(files, start=1):
            reject_symlink(path)
            try:
                document = read_canonical_json_document(path)
            except Exception as exc:  # noqa: BLE001
                raise DispatchAttemptIntegrityError(
                    f"unreadable_transition:{record_id}:{path.name}:{type(exc).__name__}"
                ) from exc
            if not isinstance(document, dict) or document.get("state") not in (
                DISPATCH_ATTEMPT_STATES
            ):
                raise DispatchAttemptIntegrityError(
                    f"malformed_transition:{record_id}:{path.name}"
                )
            if document.get("sequence") != index:
                raise DispatchAttemptIntegrityError(
                    f"transition_sequence_gap:{record_id}:{path.name}"
                )
            prior_digest = transitions[-1]["digest"] if transitions else None
            if document.get("prior_digest") != prior_digest:
                raise DispatchAttemptIntegrityError(
                    f"transition_chain_digest_mismatch:{record_id}:{path.name}"
                )
            rebuilt = DispatchAttemptTransition(
                sequence=document["sequence"],
                state=document["state"],
                observed_at=document["observed_at"],
                prior_digest=document.get("prior_digest"),
                detail=document.get("detail", {}),
            )
            if rebuilt.digest() != document.get("digest"):
                raise DispatchAttemptIntegrityError(
                    f"transition_digest_mismatch:{record_id}:{path.name}"
                )
            # A durable log must never contain two terminal transitions, or
            # any transition after a terminal one.
            if index > 1 and transitions[-1]["state"] in DISPATCH_ATTEMPT_TERMINAL_STATES:
                raise DispatchAttemptIntegrityError(
                    f"transition_after_terminal:{record_id}:{path.name}"
                )
            transitions.append(document)
        return transitions

    def latest_state(self, record_id: str) -> Optional[str]:
        transitions = self.list_transitions(record_id)
        return transitions[-1]["state"] if transitions else None

    def _latest_transition_object(
        self, record_id: str
    ) -> Optional[DispatchAttemptTransition]:
        transitions = self.list_transitions(record_id)
        if not transitions:
            return None
        last = transitions[-1]
        return DispatchAttemptTransition(
            sequence=last["sequence"],
            state=last["state"],
            observed_at=last["observed_at"],
            prior_digest=last.get("prior_digest"),
            detail=last.get("detail", {}),
        )

    def _append_transition(
        self,
        record_id: str,
        state: str,
        observed_at: str,
        detail: Optional[Mapping[str, object]],
    ) -> DispatchAttemptTransition:
        if self.read_record(record_id) is None:
            raise DispatchAttemptIntegrityError(f"no_such_record:{record_id}")
        prior = self._latest_transition_object(record_id)
        transition = next_dispatch_attempt_transition(prior, state, observed_at, detail)
        document = {
            "sequence": transition.sequence,
            "state": transition.state,
            "observed_at": transition.observed_at,
            "prior_digest": transition.prior_digest,
            "detail": transition.detail,
            "digest": transition.digest(),
        }
        path = (
            self._transitions_dir(record_id)
            / f"{transition.sequence:04d}-{transition.state.lower()}.json"
        )
        self._write_create_only(path, document)
        return transition

    def _append_transition_idempotent(
        self,
        record_id: str,
        state: str,
        observed_at: str,
        detail: Optional[Mapping[str, object]],
    ) -> DispatchAttemptTransition:
        """Append ``state``; if the current durable latest state is
        already ``state``, treat a matching ``detail`` digest as an
        idempotent replay (RPAC-REQ-069) and a differing one as a
        conflicting completion → integrity failure."""
        prior = self._latest_transition_object(record_id)
        if prior is not None and prior.state == state:
            rebuilt = DispatchAttemptTransition(
                sequence=prior.sequence,
                state=state,
                observed_at=prior.observed_at,
                prior_digest=prior.prior_digest,
                detail=dict(detail or {}),
            )
            if rebuilt.digest() != prior.digest():
                raise DispatchAttemptIntegrityError(
                    f"conflicting_transition_replay:{record_id}:{state}"
                )
            return prior
        return self._append_transition(record_id, state, observed_at, detail)

    # ── the governed transitions ──────────────────────────────────
    def prepare(
        self, record_id: str, *, observed_at: str, detail: Optional[Mapping[str, object]] = None
    ) -> DispatchAttemptTransition:
        """Record ``PREPARED`` — all pre-effect material needed to identify
        the future attempt is durably recorded; **no external effect has
        been attempted** (phase prompt §7). Idempotent if already the sole
        durable state."""
        return self._append_transition_idempotent(record_id, PREPARED, observed_at, detail)

    def begin_effect_attempt(
        self,
        record_id: str,
        *,
        observed_at: str,
        detail: Optional[Mapping[str, object]] = None,
    ) -> DispatchAttemptTransition:
        """Record ``EFFECT_ATTEMPT_STARTED`` — the decisive, write-before-
        effect transition after which automatic retry of this exact attempt
        is prohibited (phase prompt §8). It does **not** mean an external
        effect occurred, that an adapter accepted the request, or that a
        result exists.

        The at-most-once guard: if an ``EFFECT_ATTEMPT_STARTED`` transition
        is already durable for this attempt, raise
        :class:`DispatchAttemptAlreadyStartedError` (fail closed). Concurrent
        contenders racing to start the same attempt: the create-only
        primitive gives exactly one winner; every loser gets the same
        error (phase prompt §26 / §27)."""
        if self.read_record(record_id) is None:
            raise DispatchAttemptIntegrityError(f"no_such_record:{record_id}")
        if self._effect_attempt_started_is_durable(record_id):
            raise DispatchAttemptAlreadyStartedError(
                f"effect_attempt_already_started:{record_id}"
            )
        try:
            return self._append_transition(
                record_id, EFFECT_ATTEMPT_STARTED, observed_at, detail
            )
        except DispatchAttemptTransitionError as exc:
            # N-20-4 (.1R.19R): a concurrent contender persisted
            # EFFECT_ATTEMPT_STARTED in the window between our
            # ``_effect_attempt_started_is_durable`` pre-check and our own
            # transition derivation, so ``next_dispatch_attempt_transition``
            # now sees EFFECT_ATTEMPT_STARTED as the prior state and rejects a
            # second start. That is semantically identical to the durability
            # guard above — this exact attempt has already crossed
            # EFFECT_ATTEMPT_STARTED — so normalise it to the duplicate-start
            # error. Only the EFFECT_ATTEMPT_STARTED -> EFFECT_ATTEMPT_STARTED
            # edge is remapped; every other invalid transition keeps its own
            # fail-closed semantics.
            if str(exc) == (
                f"invalid_transition:{EFFECT_ATTEMPT_STARTED}->{EFFECT_ATTEMPT_STARTED}"
            ):
                raise DispatchAttemptAlreadyStartedError(
                    f"effect_attempt_already_started:{record_id}"
                ) from exc
            raise
        except DispatchAttemptIntegrityError as exc:
            # A concurrent contender created the transition file between the
            # durability check and our create — the guard still holds.
            if "record_already_exists" in str(exc):
                raise DispatchAttemptAlreadyStartedError(
                    f"effect_attempt_already_started:{record_id}"
                ) from exc
            raise

    def _effect_attempt_started_is_durable(self, record_id: str) -> bool:
        return any(
            t["state"] == EFFECT_ATTEMPT_STARTED for t in self.list_transitions(record_id)
        )

    def record_receipt_captured(
        self,
        record_id: str,
        *,
        observed_at: str,
        detail: Optional[Mapping[str, object]] = None,
    ) -> DispatchAttemptTransition:
        """Record the terminal ``RECEIPT_CAPTURED`` — a future effect-bearing
        component produced a receipt/evidence object and the mirror captured
        it. ``receipt != authority`` (phase prompt §19)."""
        return self._append_transition_idempotent(
            record_id, RECEIPT_CAPTURED, observed_at, detail
        )

    def record_dispatch_uncertain(
        self,
        record_id: str,
        *,
        observed_at: str,
        detail: Optional[Mapping[str, object]] = None,
    ) -> DispatchAttemptTransition:
        """Record the terminal ``DISPATCH_UNCERTAIN`` — PCAE cannot establish
        whether a future external effect occurred after the attempt-start
        boundary. Automatic retry prohibited; manual / governed resolution
        required (phase prompt §18 / §24 / §25)."""
        return self._append_transition_idempotent(
            record_id, DISPATCH_UNCERTAIN, observed_at, detail
        )

    def record_dispatch_not_started(
        self,
        record_id: str,
        *,
        observed_at: str,
        detail: Optional[Mapping[str, object]] = None,
    ) -> DispatchAttemptTransition:
        """Record the terminal ``DISPATCH_NOT_STARTED`` — the durable attempt
        lifecycle can prove no external effect was started (only valid from
        ``PREPARED``; never for an ambiguous failure — phase prompt §17)."""
        return self._append_transition_idempotent(
            record_id, DISPATCH_NOT_STARTED, observed_at, detail
        )

    # ── crash / restart determination ─────────────────────────────
    def resolve_disposition(self, record_id: str) -> DispatchAttemptDisposition:
        """Derive the retry/renewal determination from **durable state
        only** — never process memory or a live object handle (``.1R.16``
        §31; phase prompt §20-§25 / §45).

        * no record / no transition  -> ``not_started``
        * latest ``PREPARED``        -> ``DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER``
          (the effect boundary was never crossed; no automatic retry)
        * latest ``EFFECT_ATTEMPT_STARTED`` (unresolved) -> ``DISPATCH_UNCERTAIN``
          (the boundary may have been crossed; fail closed, human decision)
        * latest terminal           -> as recorded
        """
        if self.read_record(record_id) is None:
            return DispatchAttemptDisposition(
                record_id=record_id,
                durable_state="none",
                disposition=DispatchAttemptDisposition.NOT_STARTED,
                terminal=False,
                automatic_retry_permitted=False,
                fresh_human_authority_required=False,
                external_effect_possible=False,
                detail="no mirror record exists for this attempt identity",
            )
        state = self.latest_state(record_id)
        if state is None or state == PREPARED:
            return DispatchAttemptDisposition(
                record_id=record_id,
                durable_state=state or PREPARED,
                disposition=(
                    DispatchAttemptDisposition.NOT_STARTED
                    if state is None
                    else DispatchAttemptDisposition.DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER
                ),
                terminal=False,
                automatic_retry_permitted=False,
                fresh_human_authority_required=state is not None,
                external_effect_possible=False,
                detail=(
                    "record opened but no PREPARED transition yet"
                    if state is None
                    else "PREPARED durable, no EFFECT_ATTEMPT_STARTED — the effect "
                    "boundary was never crossed; a fresh invocation/approval is "
                    "required for any new attempt"
                ),
            )
        if state == EFFECT_ATTEMPT_STARTED:
            return DispatchAttemptDisposition(
                record_id=record_id,
                durable_state=state,
                disposition=DispatchAttemptDisposition.DISPATCH_UNCERTAIN,
                terminal=False,
                automatic_retry_permitted=False,
                fresh_human_authority_required=True,
                external_effect_possible=True,
                detail="EFFECT_ATTEMPT_STARTED durable with no terminal outcome — "
                "the outcome is uncertain; automatic retry prohibited; a human "
                "decision is required on whether a new attempt is safe",
            )
        # Terminal states.
        disposition = {
            RECEIPT_CAPTURED: DispatchAttemptDisposition.RECEIPT_CAPTURED,
            DISPATCH_UNCERTAIN: DispatchAttemptDisposition.DISPATCH_UNCERTAIN,
            DISPATCH_NOT_STARTED: DispatchAttemptDisposition.DISPATCH_NOT_STARTED,
        }[state]
        return DispatchAttemptDisposition(
            record_id=record_id,
            durable_state=state,
            disposition=disposition,
            terminal=True,
            automatic_retry_permitted=False,
            fresh_human_authority_required=True,
            external_effect_possible=state in (RECEIPT_CAPTURED, DISPATCH_UNCERTAIN),
            detail=f"terminal state {state} recorded; retry prohibited without fresh "
            "human approval",
        )
