"""
Gate-7 Runtime Enforcement coordinator — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.13.2.

Implements RDGO-001 v3.0 §8 Gate 7 (Runtime Enforcement) as the single,
independent, **non-consuming** "final whether-to-invoke" decision over the
complete bound ``runtime_dispatch`` request, exactly as frozen by the
``.1R.13.1`` planning document (§4, §6, §7, §8, §9, §10, §13, §24). It
mirrors the shape of ``runtime_dispatch_gate5.run_gate5`` and
``runtime_dispatch_permission.run_gate6_permission_broker``:

``run_gate7_runtime_enforcement`` is the frozen **sole** production owner of
the RDGO-001 §8 Gate-7 runtime-enforcement consumption boundary for
``runtime_dispatch``. It:

* consumes a registry-provenanced :class:`~runtime_dispatch_permission.Gate6Decision`
  **only** via ``runtime_dispatch_permission.is_gate6_decision`` — the exact
  object a prior successful ``run_gate6_permission_broker`` returned. A
  caller-built ``Gate6Decision``, a field-equivalent reconstruction, a copy,
  a ``deepcopy``, a serialized clone, or a bare ``decision="ALLOW"`` object
  all fail closed (RDGO-001 §8; PBRD-001 §14; the B1 defect class);
* consumes a registry-provenanced :class:`~runtime_dispatch_gate5.Gate5Result`
  **only** via ``runtime_dispatch_gate5.is_gate5_result``, and re-trusts +
  revalidates its ``ValidatedAuthorityProjection`` at Gate 7's own point of
  use (possession of a ``Gate5Result`` is never sufficient — HPAC-REQ-097 /
  §40.2). The projection revalidation re-runs ``validate_approval``
  internally, so a projection that was valid at Gate 5/6 but was
  revoked/expired or whose PB policy context drifted before Gate 7 fails
  closed here;
* preserves the exact invocation lineage from Gate 6 (``invocation_id`` and
  ``attempt_id`` equal across ``Gate5Result`` / ``Gate6Decision`` /
  ``identity``) and recomputes the ``subject_scope_binding_digest`` from
  ``identity`` + ``inputs`` (mirrors ``project_human_authority_binding``);
* implements the PBRD-001 §14 four-item Gate-6 -> Gate-7 projection: (1) the
  full immutable request + fourteen binding facts (via ``identity`` +
  ``inputs``), (2) the PB decision / causing policy IDs / matched no-go IDs
  / decision digest (via the trusted ``Gate6Decision``), (3) the validated
  approval reference + freshness verdict digest (via the re-trusted
  ``Gate5Result.projection``), and (4) static + current live-preflight
  target/status facts (resolved by this coordinator itself from the trusted
  runtime-introspection surface — never a caller-supplied
  ``execution_available=True``);
* enforces the frozen Gate-6 decision semantics: ``DENY`` and
  ``HUMAN_REVIEW`` are rejected **before** any runtime-enforcement
  evaluation (only the literal string ``"ALLOW"``, by exact equality, on a
  registry-provenanced ``Gate6Decision``, permits Gate 7 to continue). No
  code path in this module converts ``HUMAN_REVIEW`` or ``DENY`` into a
  positive ``Gate7Result``. A POL-005 hard ``DENY`` therefore can never
  reach a successful Gate-7 path (RDGO-001 §19; §15 of the plan);
* independently evaluates the current **fail-closed runtime posture**: it
  resolves the canonical ``runtime_introspection`` posture
  (``Observed / observe / unavailable``) and maps the current
  authorization-flag / safety-flag snapshot to its ``RE-NOGO-*`` id via the
  **design-only** ``runtime_enforcement_safety_authorization`` vocabulary
  (consumed, never re-defined). Under the current posture at least
  ``RE-NOGO-001``, ``RE-NOGO-002``, ``RE-NOGO-010`` and ``RE-NOGO-011`` are
  matched, so Gate 7 **always** returns a negative
  ``Gate7Result(decision="DENY", ...)``. **No legitimate positive
  production Gate-7 success is possible today** — two independent reasons,
  either sufficient: (a) the real ``Gate6Decision`` is ``DENY`` (POL-005),
  so Gate 7 short-circuits before its own evaluation; (b) even given a
  hypothetical ``ALLOW``, the current posture matches multiple blocking
  ``RE-NOGO-*`` ids. The positive branch exists for structural completeness
  only and is unreachable on the production path;
* returns exactly one ephemeral, identity-only, non-serializable,
  registry-provenanced :class:`Gate7Result` on any completed evaluation
  (``decision`` in ``{"ALLOW", "DENY"}`` — Gate 7 is a binary
  whether-to-invoke gate, no ``HUMAN_REVIEW``), or ``(None, reasons)`` on
  any pre-evaluation fail-closed rejection — creating no ``Gate7Result``
  and consuming nothing. A ``Gate7Result`` is **not an execution token**:
  an ``ALLOW`` would mean only "Runtime Enforcement would permit the
  invocation if execution capability existed"; it is not runtime
  capability, not process containment (Gate 8), not durable authority
  consumption (Gate 9), and not dispatch (Gate 10).

**Gate 7 consumes nothing.** No approval, HPAC proof, presentation,
challenge, nonce, ``Gate5Result``, ``Gate6Decision``, authority record, or
lifecycle record is created, deleted, or mutated. No ``consumption.json`` is
written. No Gate-9 primitive is called. Gate 7 is idempotently repeatable:
under an unchanged posture, ``attempt 1 -> reject`` and ``attempt 2 ->
reject`` with no state mutation; a prior ``Gate7Result`` is never a cache
and is invalid across any relevant input, PB, authority, or posture change
(RDGO-001 §8, §15, §17).

**No effect.** This module imports no ``subprocess``, ``socket``,
``os.system``/``popen``/``spawn``/``exec*``, ``pty``, provider SDK, or HTTP
client, and calls no Gate-8 (Shell Gate), Gate-9 atomic-consumption, or
Gate-10 adapter/subprocess/provider/network/credential/hardware primitive
(enforced by an AST guard in the ``.1R.13.2`` suite). Runtime posture
resolution is a read of already-frozen introspection constants; it never
registers a capability, enables a backend, or promotes an implementation
status. Runtime remains ``not_implemented / Observed / observe /
unavailable``; POL-005 unchanged; real execution UNAVAILABLE.

F7 boundary (carried verbatim, threat model NOT broadened): the
``_GATE7_RESULTS`` identity registry and this module's consumption of
``Gate5Result`` / ``Gate6Decision`` run under the same-account
autonomous-agent assumption. They resist caller-supplied **data** forgery
(reconstruction, copy, serialized clone, duck-typed lookalike), **not**
arbitrary same-process Python code execution. No UID / username /
process-ownership / stdio / Git identity / PCAE session identity / producer
identity is trusted; only the verified HPAC provenance chain establishes
human authentication and only exact-object registry membership establishes
gate-result provenance. A process-isolation / hardening chapter is a
separate, unscheduled, non-prerequisite topic.

Explicit design decisions this phase makes (open questions in ``.1R.13.1``
§10.4 / §21):

* **Freshness re-resolution (§10.4):** Gate 7 re-trusts + revalidates the
  referenced ``ValidatedAuthorityProjection`` (``is_trusted_validated_authority_projection``
  + ``revalidate_validated_authority_projection``); it does **not** re-run
  the full ``run_gate5`` coordinator. ``revalidate_validated_authority_projection``
  re-runs ``validate_approval`` (re-resolving credential / proof / approval
  / expiry / consumption state and PB ``policy_version`` drift), which
  satisfies RDGO-001 §8 item 3 "validated approval reference plus
  validation/freshness verdict digest". Re-running ``run_gate5`` (idempotent)
  would also be acceptable but is not required.
* **PB policy-version drift (§10.7):** ``Gate6Decision`` does not retain a
  ``policy_version`` field and adding one is outside the ``.1R.13.1`` §28
  frozen file matrix (``runtime_dispatch_permission.py``: "None
  anticipated"). Gate 7 covers policy drift **transitively** through the
  projection revalidation above — a projection whose policy context drifted
  no longer revalidates cleanly and is rejected as
  ``gate7_stale_validated_authority_projection``. The reason id
  ``gate7_pb_decision_stale_policy_version`` is reserved for a future
  ``Gate6Decision`` that carries the field.
* **Runtime-posture source (§14):** always resolved internally from
  ``pcae.core.runtime_introspection`` + the design-only
  ``runtime_enforcement_safety_authorization`` DEFAULT flag tables. There is
  no caller parameter that carries posture and no ``execution_available``
  request field. One coherent snapshot is taken per evaluation (no
  multi-read TOCTOU); because the current result is always reject the
  window is inert regardless.
* **Expiry / single-attempt (§21):** ``Gate7Result`` expiry is
  **context/lifecycle-based, not wall-clock**: the result is invalid the
  moment any bound input, the PB decision digest, the authority freshness
  digest, or the runtime posture changes. ``expires_at`` is set to the
  evaluation instant (``authority_current_time``) to make "valid only as of
  this evaluation" explicit; a future Gate 8 MUST re-run Gate 7 rather than
  reuse a ``Gate7Result``. "Single-attempt" is enforced structurally
  (exact-object registry membership + the bound digests); no durable
  "attempt consumed" state is created, so Gate 7 stays idempotently
  repeatable.
"""

from __future__ import annotations

from typing import Optional

from pcae.core.runtime_authority import (
    compute_canonical_digest,
    is_trusted_validated_authority_projection,
    revalidate_validated_authority_projection,
)
from pcae.core.runtime_dispatch_permission import (
    RuntimeDispatchIdentity,
    RuntimeDispatchRequestConstructionInput,
    RuntimeDispatchConstructionError,
    _expected_subject_scope_binding_digest,
    _validate_construction_inputs,
)
from pcae.core.runtime_enforcement_safety_authorization import (
    AUTH_FLAG_TO_NO_GO,
    AUTHORIZATION_FLAG_NAMES,
    DEFAULT_AUTHORIZATION_FLAGS,
    DEFAULT_SAFETY_FLAGS,
    SAFETY_FLAG_NAMES,
    SAFETY_FLAG_TO_NO_GO,
)

__all__ = [
    "Gate7Result",
    "is_gate7_result",
    "run_gate7_runtime_enforcement",
    "RuntimeEnforcementPosture",
    "resolve_runtime_enforcement_posture",
    "GATE7_DECISION_VALUES",
]

#: Gate 7 is a binary whether-to-invoke gate (RDGO-001 §8 / §14): there is
#: no ``HUMAN_REVIEW`` at Gate 7. ``HUMAN_REVIEW`` is a Gate-6 concept and
#: is a hard stop before Gate-7 evaluation.
GATE7_DECISION_VALUES: frozenset[str] = frozenset({"ALLOW", "DENY"})


# ═══════════════════════════════════════════════════════════════════════
# Runtime posture resolution (RDGO-001 §8 item 4; §13 of the plan)
# Resolved by this coordinator itself from the trusted, already-frozen
# runtime-introspection surface — never a caller-supplied fact bundle.
# ═══════════════════════════════════════════════════════════════════════


class RuntimeEnforcementPosture:
    """A closed, coordinator-resolved snapshot of the current runtime
    posture and the design-only authorization/safety flag state, plus the
    matched blocking ``RE-NOGO-*`` set.

    Read-only. Constructed only by :func:`resolve_runtime_enforcement_posture`.
    ``execution_available`` is a *derived* boolean
    (``execution_availability == "available"``); it is never read from a
    request parameter.
    """

    __slots__ = (
        "runtime_status",
        "runtime_state",
        "execution_availability",
        "maximum_plugin_capability",
        "governance_posture",
        "permission_broker_status",
        "authorization_flags",
        "safety_flags",
        "matched_no_go_ids",
        "execution_available",
    )

    def __init__(
        self,
        *,
        runtime_status: str,
        runtime_state: str,
        execution_availability: str,
        maximum_plugin_capability: str,
        governance_posture: str,
        permission_broker_status: str,
        authorization_flags: dict[str, bool],
        safety_flags: dict[str, bool],
        matched_no_go_ids: tuple[str, ...],
    ) -> None:
        self.runtime_status = runtime_status
        self.runtime_state = runtime_state
        self.execution_availability = execution_availability
        self.maximum_plugin_capability = maximum_plugin_capability
        self.governance_posture = governance_posture
        self.permission_broker_status = permission_broker_status
        self.authorization_flags = dict(authorization_flags)
        self.safety_flags = dict(safety_flags)
        self.matched_no_go_ids = tuple(matched_no_go_ids)
        self.execution_available = execution_availability == "available"

    def digest(self) -> str:
        return compute_canonical_digest(
            {
                "runtime_status": self.runtime_status,
                "runtime_state": self.runtime_state,
                "execution_availability": self.execution_availability,
                "maximum_plugin_capability": self.maximum_plugin_capability,
                "governance_posture": self.governance_posture,
                "permission_broker_status": self.permission_broker_status,
                "authorization_flags": self.authorization_flags,
                "safety_flags": self.safety_flags,
                "matched_no_go_ids": list(self.matched_no_go_ids),
            }
        )


def _matched_blocking_no_go_ids(
    authorization_flags: dict[str, bool], safety_flags: dict[str, bool]
) -> tuple[str, ...]:
    """Map the current design-only flag snapshot to the blocking
    ``RE-NOGO-*`` set, consuming the frozen
    ``runtime_enforcement_safety_authorization`` vocabulary (Phase 104B/104C)
    verbatim — this coordinator re-defines none of it.

    An authorization flag that is ``False`` means the corresponding
    execution capability is **absent**, so its mapped no-go is active. A
    safety flag that is ``True`` means the corresponding safety brake is
    still engaged, so its mapped no-go is active. Under the current posture
    every authorization flag is ``False`` and every safety flag is ``True``,
    so the matched set is a superset of
    ``{RE-NOGO-001, RE-NOGO-002, RE-NOGO-010, RE-NOGO-011}``.
    """
    matched: list[str] = []
    for name in AUTHORIZATION_FLAG_NAMES:
        if not authorization_flags.get(name, False):
            no_go = AUTH_FLAG_TO_NO_GO.get(name)
            if no_go and no_go not in matched:
                matched.append(no_go)
    for name in SAFETY_FLAG_NAMES:
        if safety_flags.get(name, True):
            no_go = SAFETY_FLAG_TO_NO_GO.get(name)
            if no_go and no_go not in matched:
                matched.append(no_go)
    return tuple(sorted(matched))


def resolve_runtime_enforcement_posture() -> RuntimeEnforcementPosture:
    """Resolve one coherent snapshot of the current runtime posture from the
    trusted, already-frozen ``runtime_introspection`` surface and the
    design-only ``runtime_enforcement_safety_authorization`` DEFAULT flag
    tables.

    This is a read of frozen constants and a pure introspection call. It
    registers no capability, enables no backend, promotes no implementation
    status, and performs no runtime execution. It accepts no caller input.
    """
    from pcae.core import runtime_introspection as ri
    from pcae.core.runtime_registry import RuntimeRegistry

    governance = ri.get_governance()
    state = ri.get_state()
    try:
        health = ri.get_health(RuntimeRegistry())
        runtime_status = health.runtime_status
        maximum_plugin_capability = health.current_maximum_plugin_capability
    except Exception:  # pragma: no cover - introspection is inert today
        runtime_status = "not_implemented"
        maximum_plugin_capability = ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY

    authorization_flags = dict(DEFAULT_AUTHORIZATION_FLAGS)
    safety_flags = dict(DEFAULT_SAFETY_FLAGS)
    matched = _matched_blocking_no_go_ids(authorization_flags, safety_flags)

    return RuntimeEnforcementPosture(
        runtime_status=runtime_status,
        runtime_state=state.current_state,
        execution_availability=ri.EXECUTION_AVAILABILITY,
        maximum_plugin_capability=maximum_plugin_capability,
        governance_posture="non-executing" if governance.non_executing_posture else "unknown",
        permission_broker_status=governance.broker_implementation_status,
        authorization_flags=authorization_flags,
        safety_flags=safety_flags,
        matched_no_go_ids=matched,
    )


# ═══════════════════════════════════════════════════════════════════════
# Gate7Result — ephemeral, identity-only, non-serializable, registry-
# provenanced (mirrors Gate5Result / Gate6Decision; RDGO-001 §8, §10 item 7)
# ═══════════════════════════════════════════════════════════════════════

_GATE7_RESULT_CONSTRUCTOR_SEAL = object()

#: The provenance boundary for a Gate-7 result: exact-object membership,
#: keyed by identity (``Gate7Result.__hash__`` / ``__eq__`` are ``id(self)``
#: / ``self is other``). The only insertion point is
#: :func:`run_gate7_runtime_enforcement`'s evaluation-completed return path;
#: nothing outside this module adds to it. ``shape != provenance``.
_GATE7_RESULTS: "set[Gate7Result]" = set()


class Gate7Result:
    """The ephemeral, non-transferable evidence Gate 7 emits after it
    independently evaluates one bound ``runtime_dispatch`` request
    (``.1R.13.1`` §10.2; RDGO-001 §8 / §10 item 7).

    Like ``Gate5Result`` / ``Gate6Decision`` / ``ValidatedAuthorityProjection``
    / ``AuthenticatedHumanPrincipal`` this type is:

    * **not** caller-constructable — the ``_seal`` guard rejects direct
      construction, and :func:`is_gate7_result` checks membership in this
      module's process-local identity registry, which only
      :func:`run_gate7_runtime_enforcement` populates;
    * **not** serializable — ``__reduce__`` raises;
    * identity-only for ``==`` / ``hash`` — a copy, ``deepcopy``, or
      field-reconstructed lookalike is a different object and is never a
      registry member, whatever its fields say;
    * **not** subclassable — ``__init_subclass__`` raises;
    * **not** an execution token — an ``ALLOW`` here means only "Runtime
      Enforcement would permit the invocation if execution capability
      existed" (RDGO-001 §0 wall ``Runtime Enforcement ALLOW != process
      permission``). It is not runtime capability, not process containment,
      not durable authority consumption, and not dispatch. A negative
      ``Gate7Result`` (``decision="DENY"``) is a structured audit record
      carrying ``matched_no_go_ids`` / ``causing_reason_ids`` — a downstream
      gate MUST NOT treat it as partial success.
    """

    __slots__ = (
        "decision",
        "matched_no_go_ids",
        "causing_reason_ids",
        "invocation_id",
        "attempt_id",
        "request_id",
        "pb_decision_digest",
        "authority_freshness_digest",
        "evaluated_input_digest",
        "runtime_posture_digest",
        "expires_at",
        "evaluated_at",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Gate7Result must not be subclassed")

    def __init__(
        self,
        *,
        decision: str,
        matched_no_go_ids: tuple[str, ...],
        causing_reason_ids: tuple[str, ...],
        invocation_id: str,
        attempt_id: str,
        request_id: str,
        pb_decision_digest: str,
        authority_freshness_digest: str,
        evaluated_input_digest: str,
        runtime_posture_digest: str,
        expires_at: str,
        evaluated_at: str,
        _seal: object,
    ) -> None:
        if _seal is not _GATE7_RESULT_CONSTRUCTOR_SEAL:
            raise TypeError(
                "Gate7Result cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_gate7.run_gate7_runtime_enforcement"
            )
        if decision not in GATE7_DECISION_VALUES:
            raise TypeError(f"Gate7Result decision must be ALLOW or DENY, got {decision!r}")
        self.decision = decision
        self.matched_no_go_ids = tuple(matched_no_go_ids)
        self.causing_reason_ids = tuple(causing_reason_ids)
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.request_id = request_id
        self.pb_decision_digest = pb_decision_digest
        self.authority_freshness_digest = authority_freshness_digest
        self.evaluated_input_digest = evaluated_input_digest
        self.runtime_posture_digest = runtime_posture_digest
        self.expires_at = expires_at
        self.evaluated_at = evaluated_at
        self._seal = _seal

    def __reduce__(self):
        raise TypeError(
            "Gate7Result is ephemeral and non-serializable; Runtime "
            "Enforcement must be re-evaluated over a freshly re-resolved "
            "Gate-6 decision and Gate-5 projection by every consumer "
            "(RDGO-001 §8, §15)"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<Gate7Result decision={self.decision!r} "
            f"invocation_id={self.invocation_id!r} identity={id(self):#x}>"
        )


def is_gate7_result(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past
    :func:`run_gate7_runtime_enforcement` call returned on a completed
    evaluation — never based on ``isinstance``, fields, equality, or any
    shape property. Fails closed for a forgery, a copy, a reconstruction,
    ``object.__new__``, or a stale handle.
    """
    return isinstance(candidate, Gate7Result) and candidate in _GATE7_RESULTS


# ═══════════════════════════════════════════════════════════════════════
# The Gate-7 coordinator
# ═══════════════════════════════════════════════════════════════════════


def _bounded_string(value: object, maximum: int = 64) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip()


def _pb_decision_digest(gate6_decision: object) -> str:
    """Canonical digest over the PB decision evidence Gate 7 consumes (never
    re-runs PB). RDGO-001 §8 item 2 / §14."""
    pb = gate6_decision.pb_decision
    return compute_canonical_digest(
        {
            "decision": pb.decision,
            "decision_reason": pb.decision_reason,
            "causing_policy_ids": list(pb.causing_policy_ids),
            "matched_no_go_ids": list(pb.matched_no_go_ids),
            "requires_human": bool(pb.requires_human),
            "simulation_only": bool(pb.simulation_only),
            "implementation_status": pb.implementation_status,
            "request_id": gate6_decision.request_id,
            "invocation_id": gate6_decision.invocation_id,
            "attempt_id": gate6_decision.attempt_id,
        }
    )


def run_gate7_runtime_enforcement(
    gate6_decision: object,
    *,
    gate5_result: object,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    authority_current_time: str,
) -> tuple[Optional[Gate7Result], tuple[str, ...]]:
    """Run RDGO-001 v3.0 Gate 7 (Runtime Enforcement) for one
    ``runtime_dispatch`` request.

    Returns ``(Gate7Result, reasons)`` on a completed evaluation — where
    ``Gate7Result.decision`` is ``"DENY"`` under the current fail-closed
    posture (always, today) or ``"ALLOW"`` on the structurally-present but
    production-unreachable positive branch — and ``(None, reasons)`` on any
    pre-evaluation fail-closed rejection, creating no ``Gate7Result`` and
    consuming nothing.

    Fail-closed reason ids (``.1R.13.1`` §10.8), each returned as a
    single-element tuple:

    * ``gate7_untrusted_gate6_decision`` — missing / non-registry
      ``Gate6Decision``;
    * ``gate7_pb_decision_not_allow:<value>`` — ``DENY`` / ``HUMAN_REVIEW`` /
      any non-``ALLOW`` decision, rejected **before** runtime-enforcement
      evaluation;
    * ``gate7_untrusted_gate5_result`` — missing / non-registry
      ``Gate5Result``;
    * ``gate7_invocation_binding_mismatch`` — ``invocation_id`` /
      ``attempt_id`` not equal across ``Gate5Result`` / ``Gate6Decision`` /
      ``identity``;
    * ``gate7_invalid_authority_current_time`` / ``gate7_invalid_identity`` /
      ``gate7_invalid_construction_input`` — structural input guards;
    * ``gate7_stale_validated_authority_projection`` — the referenced
      projection is not (or no longer) a trusted, revalidating
      ``ValidatedAuthorityProjection`` at Gate 7's own point of use
      (covers revoked / expired / PB-policy-drifted);
    * ``gate7_authority_subject_scope_mismatch`` — the recomputed
      ``subject_scope_binding_digest`` disagrees with the projection;
    * ``gate7_request_currentness_drift:<fact>`` — ``inputs`` fail the
      canonical construction re-check;
    * ``gate7_runtime_target_ineligible`` — target/effect-class not
      representable within local-CLI-v1 scope;
    * ``gate7_internal_error_fail_closed`` — any unexpected exception from
      the bounded evaluation path; no partial output.

    On a completed evaluation the accompanying ``reasons`` tuple is ``()``
    for the (production-unreachable) ``ALLOW`` branch, or
    ``("gate7_runtime_execution_unavailable",)`` for the current-posture
    ``DENY``.
    """
    try:
        # 1. Provenance — only the exact object a successful
        #    run_gate6_permission_broker returned (function-local import so
        #    the module-load import graph adds no new edge, mirroring .1R.12).
        from pcae.core.runtime_dispatch_permission import Gate6Decision, is_gate6_decision
        from pcae.core.runtime_dispatch_gate5 import Gate5Result, is_gate5_result

        if not is_gate6_decision(gate6_decision):
            return None, ("gate7_untrusted_gate6_decision",)
        assert isinstance(gate6_decision, Gate6Decision)

        if type(identity) is not RuntimeDispatchIdentity:
            return None, ("gate7_invalid_identity",)
        if type(inputs) is not RuntimeDispatchRequestConstructionInput:
            return None, ("gate7_invalid_construction_input",)
        if not _bounded_string(authority_current_time, 64):
            return None, ("gate7_invalid_authority_current_time",)

        # 2. Gate-6 decision semantics — DENY / HUMAN_REVIEW / any non-ALLOW
        #    value is a hard stop BEFORE any runtime-enforcement evaluation.
        #    Only the literal string "ALLOW", by exact equality, on a
        #    registry-provenanced Gate6Decision, permits Gate 7 to continue.
        #    No code path converts DENY / HUMAN_REVIEW into a positive result;
        #    a POL-005 hard DENY therefore never reaches a successful path.
        if gate6_decision.decision != "ALLOW":
            return None, (f"gate7_pb_decision_not_allow:{gate6_decision.decision}",)

        # 3. Gate-5 provenance + exact invocation lineage (RDGO-001 §10a:
        #    invocation_id and attempt_id are equal across every gate).
        if not is_gate5_result(gate5_result):
            return None, ("gate7_untrusted_gate5_result",)
        assert isinstance(gate5_result, Gate5Result)

        if (
            gate5_result.invocation_id != identity.invocation_id
            or gate6_decision.invocation_id != identity.invocation_id
            or gate6_decision.attempt_id != identity.attempt_id
        ):
            return None, ("gate7_invocation_binding_mismatch",)

        # 4. Structural re-check of the fourteen construction facts
        #    (RDGO-001 §8 item 1). This module performs no repository / task
        #    / registry resolution of its own — mirroring the whole chain's
        #    discipline (RuntimeDispatchRequestConstructionInput docstring).
        try:
            _validate_construction_inputs(inputs)
        except RuntimeDispatchConstructionError as exc:
            return None, (f"gate7_request_currentness_drift:{exc}",)

        if (
            inputs.effect_class != "bounded_local_process_dispatch"
            or inputs.network_requirement is not False
            or not _bounded_string(inputs.runtime_target_id, 128)
        ):
            return None, ("gate7_runtime_target_ineligible",)

        # 5. Freshness re-resolution at Gate 7's own point of use (RDGO-001
        #    §8 item 3, §15). Possession of a Gate5Result is never enough:
        #    re-trust + revalidate the referenced projection. The revalidate
        #    re-runs validate_approval, so a projection revoked / expired /
        #    PB-policy-drifted after Gate 5/6 fails closed here.
        projection = gate5_result.projection
        if not is_trusted_validated_authority_projection(projection):
            return None, ("gate7_stale_validated_authority_projection",)
        if not revalidate_validated_authority_projection(
            projection, current_time=authority_current_time
        ):
            return None, ("gate7_stale_validated_authority_projection",)

        # 6. Recompute the subject/scope binding digest from identity +
        #    inputs and compare (mirrors project_human_authority_binding).
        #    Gate-5 authority for invocation A / scope A cannot drive a
        #    Gate-7 evaluation for a changed permission-relevant field.
        expected_binding = _expected_subject_scope_binding_digest(
            identity=identity, inputs=inputs
        )
        if projection.subject_scope_binding_digest != expected_binding:
            return None, ("gate7_authority_subject_scope_mismatch",)

        # 7. Independent runtime-enforcement posture evaluation (RDGO-001 §8
        #    item 4; §13 of the plan). Resolved by this coordinator itself
        #    from the trusted runtime-introspection surface — never a
        #    caller-supplied "eligible=true". One coherent snapshot.
        posture = resolve_runtime_enforcement_posture()

        pb_digest = _pb_decision_digest(gate6_decision)
        freshness_digest = projection.freshness_verdict_digest or projection.evidence_digest()
        evaluated_input_digest = compute_canonical_digest(
            {
                "invocation_id": identity.invocation_id,
                "attempt_id": identity.attempt_id,
                "idempotency_key": identity.idempotency_key,
                "subject_scope_binding_digest": expected_binding,
                "runtime_target_id": inputs.runtime_target_id,
                "requested_capability": inputs.requested_capability,
                "prompt_hash": inputs.prompt_hash,
                "repository_identity": inputs.repository_identity,
                "base_commit": inputs.base_commit,
                "task_id": inputs.task_id,
                "task_contract_digest": inputs.task_contract_digest,
                "adapter_descriptor_digest": inputs.adapter_descriptor_binding.descriptor_digest,
                "adapter_target_config_digest": inputs.adapter_descriptor_binding.target_config_digest,
                "pb_decision_digest": pb_digest,
                "authority_freshness_digest": freshness_digest,
                "runtime_posture_digest": posture.digest(),
            }
        )

        blocking_no_gos = tuple(posture.matched_no_go_ids)
        if not posture.execution_available or blocking_no_gos:
            causing = ["gate7_runtime_execution_unavailable"]
            if not _bounded_string(posture.execution_availability, 64):  # pragma: no cover
                causing.append("gate7_runtime_posture_unresolved")
            for no_go in blocking_no_gos:
                causing.append(f"gate7_safety_no_go:{no_go}")
            result = Gate7Result(
                decision="DENY",
                matched_no_go_ids=blocking_no_gos,
                causing_reason_ids=tuple(causing),
                invocation_id=identity.invocation_id,
                attempt_id=identity.attempt_id,
                request_id=gate6_decision.request_id,
                pb_decision_digest=pb_digest,
                authority_freshness_digest=freshness_digest,
                evaluated_input_digest=evaluated_input_digest,
                runtime_posture_digest=posture.digest(),
                expires_at=authority_current_time,
                evaluated_at=authority_current_time,
                _seal=_GATE7_RESULT_CONSTRUCTOR_SEAL,
            )
            _GATE7_RESULTS.add(result)
            return result, ("gate7_runtime_execution_unavailable",)

        # 8. Positive branch — structurally present, PRODUCTION-UNREACHABLE.
        #    Reached only if execution is available AND no blocking RE-NOGO
        #    is matched, which cannot happen while the runtime is
        #    not_implemented / Observed / observe / unavailable. Even then
        #    the real Gate-6 decision is DENY (POL-005), so control never
        #    arrives here on the production path. An ALLOW is NOT an
        #    execution token (RDGO-001 §0).
        result = Gate7Result(  # pragma: no cover - unreachable in production
            decision="ALLOW",
            matched_no_go_ids=(),
            causing_reason_ids=(),
            invocation_id=identity.invocation_id,
            attempt_id=identity.attempt_id,
            request_id=gate6_decision.request_id,
            pb_decision_digest=pb_digest,
            authority_freshness_digest=freshness_digest,
            evaluated_input_digest=evaluated_input_digest,
            runtime_posture_digest=posture.digest(),
            expires_at=authority_current_time,
            evaluated_at=authority_current_time,
            _seal=_GATE7_RESULT_CONSTRUCTOR_SEAL,
        )
        _GATE7_RESULTS.add(result)
        return result, ()
    except Exception:
        # Fail closed on any unexpected exception from the bounded
        # evaluation path — no partial output, no Gate7Result (RDGO-001
        # §0, §19).
        return None, ("gate7_internal_error_fail_closed",)
