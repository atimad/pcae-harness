"""HPAC-PAWA-HELPER-001 v1.0 — protected one-shot privileged helper protocol
foundation (schema, closed operation vocabulary, dispatch, state machine,
replay/freshness, evidence-staging ordering).

Phase N16-5-F-5-TB-HELPER-IMPL. **Foundation only** (contract §2 non-goals;
phase-authorization §2/§40): this module implements the protocol/dispatch
skeleton the contract specifies. It does NOT wire the real
``HumanPrincipalRegistryStore`` / RHAMP / ``ProtectedPresentationInstallationStore``
canonical stores, does NOT install or register a live helper, and does NOT
perform any real ceremony. Every operation family in ``operations/`` acts
against an injected store abstraction (``ProtectedStoreFoundation``) so this
module can be exercised deterministically in tests without touching
``<HPAC_PROTECTED_ROOT>``. Wiring to the real stores is explicitly deferred
to the caller/client-integration phase (phase-authorization §41/§54).

**HPAC-PAWA-HELPER-REQ-033 discipline**: this module (and its OS-level
sibling ``hpac_pawa_helper_os``) is helper-local code. It deliberately does
**not** import ``pcae.core.hpac_protected_admin_writer`` (the in-process PAWA
factory module) or any of its forbidden symbols — the helper process must
not gain the old same-interpreter authority path. Because the closed
21-value ``pawa_failure_code`` vocabulary (HPAC-PAWA-REQ-121) must not be
duplicated as a *new* vocabulary (HPAC-PAWA-HELPER-REQ-004), this module
re-states the same 21 literal values locally; a test-only guard
(``tests/test_hpac_pawa_helper_protocol_foundation.py``) imports both
modules and asserts byte-for-byte equality, since the *test* file is not
subject to the agent-importability fence that binds production code.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, FrozenSet, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# §0 / §56 — closed pawa_failure_code vocabulary (re-stated, not re-invented;
# see module docstring). Exact copy of hpac_protected_admin_writer.PAWA_FAILURE_CODES.
# ---------------------------------------------------------------------------

PAWA_FAILURE_CODES: Tuple[str, ...] = (
    "protected_root_missing",              # 1
    "protected_root_untrusted",            # 2
    "agent_principal_unknown",             # 3
    "agent_has_protected_write_authority",  # 4
    "descriptor_missing",                  # 5
    "descriptor_malformed",                # 6
    "descriptor_wrong_owner",              # 7
    "descriptor_wrong_mode",               # 8
    "descriptor_root_identity_mismatch",   # 9
    "descriptor_installation_mismatch",    # 10
    "descriptor_generation_stale",         # 11
    "descriptor_revoked",                  # 12
    "write_probe_failed",                  # 13
    "current_context_is_agent",            # 14
    "unauthorized_factory_consumer",       # 15
    "operation_scope_invalid",             # 16
    "target_scope_invalid",                # 17
    "capability_stale",                    # 18
    "duplicate_bootstrap",                 # 19
    "reconstruction_attempt",              # 20
    "internal_fail_closed",                # 21
)
assert len(PAWA_FAILURE_CODES) == 21 and len(set(PAWA_FAILURE_CODES)) == 21


class HelperProtocolError(Exception):
    """A terminal HPAC-PAWA-HELPER/1.0 failure. ``code`` is exactly one
    member of :data:`PAWA_FAILURE_CODES` — never a new vocabulary entry
    (HPAC-PAWA-HELPER-REQ-004)."""

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in PAWA_FAILURE_CODES:
            raise AssertionError(f"non-vocabulary pawa_failure_code: {code!r}")
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


PROTOCOL_VERSION = "HPAC-PAWA-HELPER/1.0"
REQUEST_SCHEMA_VERSION = "HPAC-PAWA-HELPER-REQUEST/1.0"
RESPONSE_SCHEMA_VERSION = "HPAC-PAWA-HELPER-RESPONSE/1.0"

# §13 — closed 5-member operation vocabulary (HPAC-PAWA-HELPER-REQ-053).
# No sixth member; no wildcard/prefix acceptance anywhere this enum is used.


class HelperOperation(str, Enum):
    ADMIN_MUTATION = "admin_mutation"
    CERTIFICATION_WRITE = "certification_write"
    CERTIFICATION_READ = "certification_read"
    CEREMONY_ENTRY = "ceremony_entry"
    PRESENTATION_EVIDENCE_WRITE = "presentation_evidence_write"


CLOSED_OPERATIONS: FrozenSet[str] = frozenset(op.value for op in HelperOperation)
assert len(CLOSED_OPERATIONS) == 5

# §14.2 — the closed five-role certification-lifecycle allowlist
# (HPAC-PAWA-HELPER-REQ-059). ``hpac_lifecycle_terminator`` is explicitly
# NOT a member.


class CertificationRole(str, Enum):
    HPAC_CHALLENGE_COORDINATOR = "hpac_challenge_coordinator"
    HPAC_ASSERTION_RECORDER = "hpac_assertion_recorder"
    HUMAN_AUTHENTICATION_PROOF_VERIFIER = "human_authentication_proof_verifier"
    HPAC_GATE5_BINDER = "hpac_gate5_binder"
    HPAC_RHAMP_COUNTER_STATE_VERIFIER = "hpac_rhamp_counter_state_verifier"


CLOSED_CERTIFICATION_ROLES: FrozenSet[str] = frozenset(r.value for r in CertificationRole)
assert len(CLOSED_CERTIFICATION_ROLES) == 5
assert "hpac_lifecycle_terminator" not in CLOSED_CERTIFICATION_ROLES

#: §14.1 — the closed HPAC-PAWA-001 §42 admin_mutation classes this protocol
#: can transport (HPAC-PAWA-HELPER-REQ-057). Not a new vocabulary: mirrors
#: hpac_protected_admin_writer.PawaOperation's members by literal value.
CLOSED_ADMIN_MUTATIONS: FrozenSet[str] = frozenset(
    {
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
        "configure_privileged_helper",
    }
)

#: §11 per-operation ``operation_version`` constants (HPAC-PAWA-HELPER-REQ-046).
OPERATION_VERSIONS: Mapping[str, str] = {
    HelperOperation.ADMIN_MUTATION.value: "admin_mutation/1.0",
    HelperOperation.CERTIFICATION_WRITE.value: "certification_write/1.0",
    HelperOperation.CERTIFICATION_READ.value: "certification_read/1.0",
    HelperOperation.CEREMONY_ENTRY.value: "ceremony_entry/1.0",
    HelperOperation.PRESENTATION_EVIDENCE_WRITE.value: "presentation_evidence_write/1.0",
}

#: §15 — the closed enumerated read-record types (HPAC-PAWA-HELPER-REQ-063).
CLOSED_READ_RECORD_TYPES: FrozenSet[str] = frozenset(
    {
        "principal_record",
        "credential_record",
        "rhamp_credential_sidecar",
        "rhamp_counter_state",
        "presentation_installation_record",
        "presentation_mechanism_descriptor",
        "trusted_approval_presentation_record",
        "pawa_anchor_record",
        "helper_registration_record",
    }
)


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _digest(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


# ---------------------------------------------------------------------------
# §11 — closed request schema. A frozen dataclass; unknown fields are
# rejected by the strict ``from_mapping`` constructor (dataclasses alone do
# not reject stray kwargs when constructed positionally/by literal call, so
# every production-facing entry point MUST go through ``from_mapping``,
# never ``HelperRequest(**untrusted_dict)``).
# ---------------------------------------------------------------------------

_REQUEST_FIELDS = (
    "request_schema_version",
    "protocol_version",
    "operation",
    "operation_version",
    "role",
    "session_id",
    "principal_id",
    "credential_id",
    "proof_id",
    "operation_params",
    "request_id",
    "nonce",
    "expiry",
    "installation_id",
    "generation",
    "request_digest",
)


@dataclass(frozen=True)
class HelperRequest:
    request_schema_version: str
    protocol_version: str
    operation: str
    operation_version: str
    session_id: str
    operation_params: Mapping[str, object]
    request_id: str
    nonce: str
    expiry: str
    installation_id: str
    generation: int
    request_digest: str
    role: Optional[str] = None
    principal_id: Optional[str] = None
    credential_id: Optional[str] = None
    proof_id: Optional[str] = None

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> "HelperRequest":
        """§11 closed-schema ingestion. Unknown fields fail closed
        (HPAC-PAWA-HELPER-REQ-046/047)."""
        unknown = set(data) - set(_REQUEST_FIELDS)
        if unknown:
            raise HelperProtocolError(
                "operation_scope_invalid", f"unknown request field(s): {sorted(unknown)}"
            )
        missing = {
            "request_schema_version",
            "protocol_version",
            "operation",
            "operation_version",
            "session_id",
            "operation_params",
            "request_id",
            "nonce",
            "expiry",
            "installation_id",
            "generation",
            "request_digest",
        } - set(data)
        if missing:
            raise HelperProtocolError(
                "operation_scope_invalid", f"missing request field(s): {sorted(missing)}"
            )
        params = data["operation_params"]
        if not isinstance(params, Mapping):
            raise HelperProtocolError("operation_scope_invalid", "operation_params must be a mapping")
        return HelperRequest(
            request_schema_version=str(data["request_schema_version"]),
            protocol_version=str(data["protocol_version"]),
            operation=str(data["operation"]),
            operation_version=str(data["operation_version"]),
            role=None if data.get("role") is None else str(data["role"]),
            session_id=str(data["session_id"]),
            principal_id=None if data.get("principal_id") is None else str(data["principal_id"]),
            credential_id=None if data.get("credential_id") is None else str(data["credential_id"]),
            proof_id=None if data.get("proof_id") is None else str(data["proof_id"]),
            operation_params=dict(params),
            request_id=str(data["request_id"]),
            nonce=str(data["nonce"]),
            expiry=str(data["expiry"]),
            installation_id=str(data["installation_id"]),
            generation=int(data["generation"]),
            request_digest=str(data["request_digest"]),
        )

    def compute_digest(self) -> str:
        """Self-excluding SHA-256 (HPAC-PAWA-HELPER-REQ-046 request_digest)."""
        return _digest(
            self.request_schema_version,
            self.protocol_version,
            self.operation,
            self.operation_version,
            self.role or "",
            self.session_id,
            self.principal_id or "",
            self.credential_id or "",
            self.proof_id or "",
            repr(sorted(self.operation_params.items())),
            self.request_id,
            self.nonce,
            self.expiry,
            self.installation_id,
            str(self.generation),
        )


def build_signed_request(
    *,
    operation: HelperOperation,
    session_id: str,
    operation_params: Mapping[str, object],
    request_id: str,
    expiry: str,
    installation_id: str,
    generation: int,
    role: Optional[CertificationRole] = None,
    principal_id: Optional[str] = None,
    credential_id: Optional[str] = None,
    proof_id: Optional[str] = None,
    nonce: Optional[str] = None,
) -> HelperRequest:
    """Launcher-side helper: builds a canonical request with a fresh
    CSPRNG nonce (>=256 bits, HPAC-PAWA-HELPER-REQ-046) and a correct
    self-excluding digest. Test/launcher convenience only — not itself a
    trust decision."""
    nonce_value = nonce if nonce is not None else secrets.token_hex(32)  # 256 bits
    draft = HelperRequest(
        request_schema_version=REQUEST_SCHEMA_VERSION,
        protocol_version=PROTOCOL_VERSION,
        operation=operation.value,
        operation_version=OPERATION_VERSIONS[operation.value],
        role=role.value if role is not None else None,
        session_id=session_id,
        principal_id=principal_id,
        credential_id=credential_id,
        proof_id=proof_id,
        operation_params=dict(operation_params),
        request_id=request_id,
        nonce=nonce_value,
        expiry=expiry,
        installation_id=installation_id,
        generation=generation,
        request_digest="",
    )
    digest = draft.compute_digest()
    return HelperRequest(**{**draft.__dict__, "request_digest": digest})


# ---------------------------------------------------------------------------
# §12 — closed response schema.
# ---------------------------------------------------------------------------


class Decision(str, Enum):
    PERFORMED = "PERFORMED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class HelperResponse:
    response_schema_version: str
    protocol_version: str
    request_id: str
    nonce: str
    decision: str
    trusted_timestamp: str
    state_reached: str
    response_digest: str
    terminal_code: Optional[str] = None
    evidence_ref: Optional[str] = None
    evidence_digest: Optional[str] = None
    result_payload: Optional[Mapping[str, object]] = None

    def compute_digest(self) -> str:
        return _digest(
            self.response_schema_version,
            self.protocol_version,
            self.request_id,
            self.nonce,
            self.decision,
            self.terminal_code or "",
            self.evidence_ref or "",
            self.evidence_digest or "",
            repr(sorted((self.result_payload or {}).items())),
            self.trusted_timestamp,
            self.state_reached,
        )


#: §24 — names (and semantic-equivalents scanned by the no-authority-export
#: test) that may never appear as a field name or a string value anywhere in
#: a HelperResponse (PAWAH-INV-1, HPAC-PAWA-HELPER-REQ-091/092).
FORBIDDEN_AUTHORITY_TOKENS: FrozenSet[str] = frozenset(
    {
        "hpacwritercapability",
        "hpacstoreauthority",
        "productionwriterhandle",
        "certificationwriterhandle",
        "certificationreadauthority",
        "writer_capability",
        "store_authority",
        "capability_token",
        "bearer_token",
        "seal",
        "_seal",
    }
)


def _value_leaks_authority(value: object) -> bool:
    if isinstance(value, str):
        return any(tok in value.lower() for tok in FORBIDDEN_AUTHORITY_TOKENS)
    if isinstance(value, Mapping):
        for k, v in value.items():
            if any(tok in str(k).lower() for tok in FORBIDDEN_AUTHORITY_TOKENS):
                return True
            if _value_leaks_authority(v):
                return True
        return False
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_value_leaks_authority(v) for v in value)
    return False


def response_leaks_authority(response: HelperResponse) -> bool:
    """§24/§36 no-authority-export scan: true if any field name or any
    (recursively nested) string value/key in the response looks like it
    carries authority. Used both by production dispatch (defence in depth)
    and by tests."""
    for f in fields(response):
        name = f.name.lower()
        if any(tok in name for tok in FORBIDDEN_AUTHORITY_TOKENS):
            return True
        value = getattr(response, f.name)
        if _value_leaks_authority(value):
            return True
    return False


# ---------------------------------------------------------------------------
# §20 — state-transition model.
# ---------------------------------------------------------------------------


class HelperState(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    REQUEST_AUTHENTICATED = "REQUEST_AUTHENTICATED"
    OPERATION_ADMITTED = "OPERATION_ADMITTED"
    MUTATION_ATTEMPT_STARTED = "MUTATION_ATTEMPT_STARTED"
    MUTATION_COMMITTED = "MUTATION_COMMITTED"
    EVIDENCE_WRITTEN = "EVIDENCE_WRITTEN"
    RESPONSE_EMITTED = "RESPONSE_EMITTED"
    RESULT_EMITTED = "RESULT_EMITTED"  # non-mutating (read / ceremony_entry) terminal state
    INDETERMINATE = "INDETERMINATE"  # §21 crash between MUTATION_COMMITTED and EVIDENCE_WRITTEN


_MUTATING_ORDER = (
    HelperState.REQUEST_RECEIVED,
    HelperState.REQUEST_AUTHENTICATED,
    HelperState.OPERATION_ADMITTED,
    HelperState.MUTATION_ATTEMPT_STARTED,
    HelperState.MUTATION_COMMITTED,
    HelperState.EVIDENCE_WRITTEN,
    HelperState.RESPONSE_EMITTED,
)
_NON_MUTATING_ORDER = (
    HelperState.REQUEST_RECEIVED,
    HelperState.REQUEST_AUTHENTICATED,
    HelperState.OPERATION_ADMITTED,
    HelperState.RESULT_EMITTED,
)

#: The no-auto-retry boundary (HPAC-PAWA-HELPER-REQ-082/090).
NO_RETRY_BOUNDARY = HelperState.MUTATION_ATTEMPT_STARTED


class StateTransitionError(Exception):
    pass


class HelperStateMachine:
    """Explicit, forward-only state-transition tracker for one request's
    processing inside one helper process (§20). Enforces:
    - transitions only follow the frozen ordered sequence (no skipping
      forward, no going backward);
    - once ``MUTATION_ATTEMPT_STARTED`` is reached, the same instance
      SHALL NOT be reused to start a second mutation attempt for the same
      request (no-auto-retry, HPAC-PAWA-HELPER-REQ-090)."""

    def __init__(self, *, mutating: bool) -> None:
        self._order = _MUTATING_ORDER if mutating else _NON_MUTATING_ORDER
        self._index = 0
        self._retry_attempted = False
        self.state = self._order[0]

    def advance_to(self, target: HelperState) -> None:
        if target is HelperState.INDETERMINATE:
            self.state = HelperState.INDETERMINATE
            return
        try:
            target_index = self._order.index(target)
        except ValueError:
            raise StateTransitionError(f"{target} is not valid for this operation's model")
        if target_index != self._index + 1:
            raise StateTransitionError(
                f"illegal transition {self.state} -> {target} (expected next: "
                f"{self._order[self._index + 1] if self._index + 1 < len(self._order) else 'none'})"
            )
        self._index = target_index
        self.state = target

    def crossed_no_retry_boundary(self) -> bool:
        return self._order is _MUTATING_ORDER and self._index >= self._order.index(NO_RETRY_BOUNDARY)

    def assert_may_start_mutation_attempt(self) -> None:
        """Raise if a second MUTATION_ATTEMPT_STARTED is attempted on an
        instance that already crossed the boundary — this is the concrete
        no-auto-retry enforcement point (HPAC-PAWA-HELPER-REQ-082)."""
        if self.crossed_no_retry_boundary() and self.state is not HelperState.OPERATION_ADMITTED:
            raise StateTransitionError(
                "no-auto-retry: MUTATION_ATTEMPT_STARTED already crossed for this request"
            )


# ---------------------------------------------------------------------------
# §19 — replay / freshness tracking (process-local; a real helper is
# one-shot per exec so this is naturally scoped to one request, but the
# guard is expressed generally so tests can exercise duplicate/conflicting
# replay across multiple simulated helper invocations sharing one durable
# ledger, matching HPAC-PAWA-HELPER-REQ-076).
# ---------------------------------------------------------------------------


class ReplayOutcome(str, Enum):
    FRESH = "fresh"
    CONSUMED = "consumed"
    DUPLICATE_IN_FLIGHT = "duplicate_in_flight"
    EXPIRED = "expired"
    CONFLICTING = "conflicting"


@dataclass
class _LedgerEntry:
    operation: str
    session_id: str
    subject: str
    in_flight: bool
    consumed: bool


class ReplayLedger:
    """§19/§77 one-shot replay ledger.

    Two backings:

    * ``ReplayLedger()`` — the deterministic **in-memory** foundation. It is
      scoped to one process, so it CANNOT enforce §19 across the one-shot
      helper process lifetime (N16-5-F-5-TB-HELPER-IV proved a consumed
      request becomes ``FRESH`` again in a new helper process). It remains
      only as the NON_REAL deterministic harness for protocol-shape tests.
    * ``ReplayLedger(durable_store=...)`` — backed by a
      :class:`~pcae.core.hpac_pawa_helper_replay_state.DurableReplayStore`
      under the existing ``<HPAC_PROTECTED_ROOT>/pawa-helper/`` trust
      boundary. This is the only backing that satisfies
      HPAC-PAWA-HELPER-REQ-076/077 and PAWAH-INV-10. Production wiring MUST
      use :func:`~pcae.core.hpac_pawa_helper_replay_state.open_durable_replay_ledger`.

    The public surface is identical either way, so dispatch/admission code is
    unchanged by the choice of backing.
    """

    def __init__(self, *, durable_store: Optional[object] = None) -> None:
        self._entries: Dict[Tuple[str, str], _LedgerEntry] = {}
        self._durable = durable_store

    @property
    def is_durable(self) -> bool:
        """True iff spent state survives this process (and a crash)."""
        return self._durable is not None

    def check_and_mark_in_flight(self, request: HelperRequest, *, now: Optional[datetime] = None) -> ReplayOutcome:
        if self._durable is not None:
            return self._durable.check_and_reserve(request, now=now)
        now = now or datetime.now(timezone.utc)
        try:
            expiry = datetime.strptime(request.expiry, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except ValueError:
            expiry = datetime.min.replace(tzinfo=timezone.utc)
        if now > expiry:
            return ReplayOutcome.EXPIRED
        key = (request.request_id, request.nonce)
        subject = request.principal_id or request.credential_id or request.proof_id or ""
        existing = self._entries.get(key)
        if existing is None:
            self._entries[key] = _LedgerEntry(
                operation=request.operation, session_id=request.session_id, subject=subject,
                in_flight=True, consumed=False,
            )
            return ReplayOutcome.FRESH
        if existing.operation != request.operation or existing.session_id != request.session_id or existing.subject != subject:
            return ReplayOutcome.CONFLICTING
        if existing.consumed:
            return ReplayOutcome.CONSUMED
        if existing.in_flight:
            return ReplayOutcome.DUPLICATE_IN_FLIGHT
        return ReplayOutcome.CONSUMED

    def mark_consumed(self, request: HelperRequest, *, evidence_ref: Optional[str] = None) -> None:
        """Spend the ``(request_id, nonce)`` at the ``MUTATION_ATTEMPT_STARTED``
        boundary (HPAC-PAWA-HELPER-REQ-077).

        On a durable ledger the state change is persisted **before this
        returns**, i.e. before the caller performs the mutation, so a crash
        anywhere at or after the boundary leaves the request spent.
        """
        if self._durable is not None:
            from pcae.core.hpac_pawa_helper_replay_state import DurableReplayState

            self._durable.transition(
                request, DurableReplayState.MUTATION_ATTEMPT_STARTED, evidence_ref=evidence_ref
            )
            return
        key = (request.request_id, request.nonce)
        entry = self._entries.get(key)
        if entry is not None:
            entry.in_flight = False
            entry.consumed = True

    def mark_durable_state(self, request: HelperRequest, state_name: str, **fields: object) -> None:
        """Advance the durable §20 state for a spent request. A no-op on the
        in-memory backing (which has no durable state to advance)."""
        if self._durable is None:
            return
        from pcae.core.hpac_pawa_helper_replay_state import DurableReplayState

        self._durable.transition(request, DurableReplayState(state_name), **fields)

    def release_in_flight_without_consuming(self, request: HelperRequest) -> None:
        """Only valid BEFORE the no-retry boundary is crossed (a request
        that never reached MUTATION_ATTEMPT_STARTED leaves no protected-root
        effect, HPAC-PAWA-HELPER-REQ-083).

        On a durable ledger this can only ever remove a record still in
        ``REQUEST_RECEIVED`` and owned by this process — a spent record is
        never removed, so this is not a replay reset.
        """
        if self._durable is not None:
            self._durable.release_reservation(request)
            return
        key = (request.request_id, request.nonce)
        entry = self._entries.get(key)
        if entry is not None and not entry.consumed:
            del self._entries[key]


# ---------------------------------------------------------------------------
# §22 — evidence staging (ordering model A: stage before mutate, finalize
# after commit).
# ---------------------------------------------------------------------------


class EvidenceOutcome(str, Enum):
    STAGED = "staged"
    COMMITTED = "committed"


@dataclass
class EvidenceRecord:
    state: str
    request_digest: str
    operation: str
    role: Optional[str]
    session_id: str
    subject: str
    nonce: str
    expiry: str
    committed_digest: Optional[str] = None

    def digest(self) -> str:
        return _digest(
            self.state, self.request_digest, self.operation, self.role or "",
            self.session_id, self.subject, self.nonce, self.expiry, self.committed_digest or "",
        )


class EvidenceStager:
    """§22 audit-write ordering foundation. A production implementation
    durably persists staged/committed records under
    ``<HPAC_PROTECTED_ROOT>``; this in-memory stager implements the exact
    ordering and failure semantics so the state machine and dispatch logic
    can be tested deterministically (NON_REAL, phase-authorization §31)."""

    def __init__(self, *, fail_staging: bool = False, fail_finalization: bool = False) -> None:
        self._fail_staging = fail_staging
        self._fail_finalization = fail_finalization
        self.records: Dict[str, EvidenceRecord] = {}

    def stage(self, *, request: HelperRequest) -> str:
        if self._fail_staging:
            raise HelperProtocolError("internal_fail_closed", "evidence staging failed")
        subject = request.principal_id or request.credential_id or request.proof_id or ""
        record = EvidenceRecord(
            state=EvidenceOutcome.STAGED.value,
            request_digest=request.request_digest,
            operation=request.operation,
            role=request.role,
            session_id=request.session_id,
            subject=subject,
            nonce=request.nonce,
            expiry=request.expiry,
        )
        ref = f"pawa-helper/audit/{record.digest()}"
        self.records[ref] = record
        return ref

    def finalize(self, ref: str, *, committed_digest: str) -> Tuple[str, str]:
        if self._fail_finalization:
            raise HelperProtocolError("internal_fail_closed", "evidence finalization failed post-commit")
        record = self.records[ref]
        record.state = EvidenceOutcome.COMMITTED.value
        record.committed_digest = committed_digest
        return ref, record.digest()

    def is_indeterminate(self, ref: str) -> bool:
        record = self.records.get(ref)
        return record is not None and record.state == EvidenceOutcome.STAGED.value


# ---------------------------------------------------------------------------
# §13 — explicit closed-mapping dispatch. No getattr/reflection.
# ---------------------------------------------------------------------------

DispatchHandler = Callable[[HelperRequest, "HelperContext"], HelperResponse]


@dataclass
class HelperContext:
    """Bundles the process-local collaborators one dispatch call needs.
    Deliberately does not carry any OS-level authority object — those live
    only in ``hpac_pawa_helper_os`` and are consumed before dispatch, never
    passed through it (§24)."""

    replay_ledger: ReplayLedger
    evidence_stager: EvidenceStager
    supported_operations: FrozenSet[str]
    store: "ProtectedStoreFoundation"


def validate_and_admit(request: HelperRequest, context: HelperContext) -> HelperStateMachine:
    """§7/§13 admission sequence up to OPERATION_ADMITTED. Peer-credential
    and configured-agent-identity checks (§10, this module's OS-level
    sibling) MUST have already passed before this function is called —
    admission here validates the request's own well-formedness and the
    replay/freshness/operation-membership conjuncts (HPAC-PAWA-HELPER-REQ-031)."""
    if request.protocol_version != PROTOCOL_VERSION:
        raise HelperProtocolError("operation_scope_invalid", "protocol_version mismatch")
    if request.request_schema_version != REQUEST_SCHEMA_VERSION:
        raise HelperProtocolError("operation_scope_invalid", "request_schema_version mismatch")
    if request.operation not in CLOSED_OPERATIONS:
        raise HelperProtocolError("operation_scope_invalid", f"unknown operation {request.operation!r}")
    if request.operation not in context.supported_operations:
        raise HelperProtocolError("operation_scope_invalid", "operation not supported by this helper generation")
    if request.operation_version != OPERATION_VERSIONS[request.operation]:
        raise HelperProtocolError("operation_scope_invalid", "unrecognized operation_version")
    if request.operation == HelperOperation.CERTIFICATION_WRITE.value:
        if request.role not in CLOSED_CERTIFICATION_ROLES:
            raise HelperProtocolError("operation_scope_invalid", f"role {request.role!r} not in closed five-role set")
    elif request.role is not None:
        raise HelperProtocolError("operation_scope_invalid", "role is only valid for certification_write")

    mutating = request.operation in (
        HelperOperation.ADMIN_MUTATION.value,
        HelperOperation.CERTIFICATION_WRITE.value,
        HelperOperation.PRESENTATION_EVIDENCE_WRITE.value,
    )
    machine = HelperStateMachine(mutating=mutating)
    machine.advance_to(HelperState.REQUEST_AUTHENTICATED)  # caller already ran peer-auth (§10) before this call

    if request.operation != HelperOperation.CERTIFICATION_READ.value:
        outcome = context.replay_ledger.check_and_mark_in_flight(request)
        if outcome is ReplayOutcome.EXPIRED:
            raise HelperProtocolError("capability_stale", "request past expiry")
        if outcome is ReplayOutcome.CONSUMED:
            raise HelperProtocolError("capability_stale", "request already consumed")
        if outcome is ReplayOutcome.DUPLICATE_IN_FLIGHT:
            raise HelperProtocolError("capability_stale", "duplicate request in flight")
        if outcome is ReplayOutcome.CONFLICTING:
            raise HelperProtocolError("target_scope_invalid", "conflicting replay: bound fields differ")

    if request.operation_params:
        forbidden_keys = {"path", "expression", "shell", "module", "json_patch", "command", "executable"}
        if forbidden_keys & set(k.lower() for k in request.operation_params):
            raise HelperProtocolError("operation_scope_invalid", "forbidden free-form operation_params key")

    machine.advance_to(HelperState.OPERATION_ADMITTED)
    return machine


def dispatch(request: HelperRequest, context: HelperContext, handlers: Mapping[str, DispatchHandler]) -> HelperResponse:
    """§13 explicit closed-mapping dispatch — the ONLY entry point that maps
    an admitted operation to its bounded implementation. ``handlers`` MUST
    be an exact 5-key mapping matching :data:`CLOSED_OPERATIONS`; this is
    asserted so a future edit cannot silently widen or narrow the table."""
    if frozenset(handlers) != CLOSED_OPERATIONS:
        raise AssertionError("dispatch table must have exactly the 5 closed operations, no more, no fewer")
    try:
        machine = validate_and_admit(request, context)
    except HelperProtocolError as exc:
        return _rejected_response(request, exc.code)
    handler = handlers[request.operation]
    try:
        response = handler(request, context, machine)
    except HelperProtocolError as exc:
        if machine.state is HelperState.INDETERMINATE:
            # §21/§22: the mutation may have committed; this is NOT an
            # ordinary rejection and MUST NOT be silently reported as one.
            # The caller is responsible for reconciliation against the
            # durable protected-root evidence, never for auto-retry.
            raise
        if request.operation != HelperOperation.CERTIFICATION_READ.value and not machine.crossed_no_retry_boundary():
            context.replay_ledger.release_in_flight_without_consuming(request)
        return _rejected_response(request, exc.code)
    if response_leaks_authority(response):
        raise AssertionError("dispatch produced a response that leaks authority-shaped content")
    return response


def _rejected_response(request: HelperRequest, code: str) -> HelperResponse:
    resp = HelperResponse(
        response_schema_version=RESPONSE_SCHEMA_VERSION,
        protocol_version=request.protocol_version,
        request_id=request.request_id,
        nonce=request.nonce,
        decision=Decision.REJECTED.value,
        terminal_code=code,
        trusted_timestamp=_now_rfc3339(),
        state_reached=HelperState.OPERATION_ADMITTED.value,
        response_digest="",
    )
    digest = resp.compute_digest()
    return HelperResponse(**{**resp.__dict__, "response_digest": digest})


def performed_response(
    request: HelperRequest,
    *,
    state_reached: HelperState,
    evidence_ref: Optional[str] = None,
    evidence_digest: Optional[str] = None,
    result_payload: Optional[Mapping[str, object]] = None,
) -> HelperResponse:
    resp = HelperResponse(
        response_schema_version=RESPONSE_SCHEMA_VERSION,
        protocol_version=request.protocol_version,
        request_id=request.request_id,
        nonce=request.nonce,
        decision=Decision.PERFORMED.value,
        evidence_ref=evidence_ref,
        evidence_digest=evidence_digest,
        result_payload=dict(result_payload) if result_payload is not None else None,
        trusted_timestamp=_now_rfc3339(),
        state_reached=state_reached.value,
        response_digest="",
    )
    digest = resp.compute_digest()
    return HelperResponse(**{**resp.__dict__, "response_digest": digest})


# ---------------------------------------------------------------------------
# Store abstraction the bounded operation foundations run against. A real
# implementation is a thin adapter over the canonical HPAC/RHAMP/PPA stores;
# this in-memory version is what phase-authorization §31 calls a
# "deterministic test harness for the helper/protocol boundary" — it is
# never wired to a live protected root by this module.
# ---------------------------------------------------------------------------


class ProtectedStoreFoundation:
    """Deterministic, in-memory stand-in for the canonical protected
    stores this helper foundation will eventually be wired to. NON_REAL —
    never the production HumanPrincipalRegistryStore / RHAMP / PPA stores."""

    def __init__(self) -> None:
        self.records: Dict[Tuple[str, str], Mapping[str, object]] = {}
        self.ceremonies_started: Dict[str, str] = {}
        self.presentation_evidence: Dict[str, Mapping[str, object]] = {}

    def put_record(self, record_type: str, key: str, value: Mapping[str, object]) -> None:
        self.records[(record_type, key)] = dict(value)

    def get_record(self, record_type: str, key: str) -> Optional[Mapping[str, object]]:
        return self.records.get((record_type, key))
