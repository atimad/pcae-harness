"""
Gate-10 Pre-Effect Eligibility and Dispatch-Envelope coordinator — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.17 (Slice A of the ``.1R.16`` Gate-10 plan).

This module implements the **front half of RDGO-001 v3.1 §11 Gate 10** —
the six-item pre-effect read-back battery (§11 items 1–6), the §16/§17
containment and executable-identity read-back, and the RPAC-REQ-029
``DispatchEnvelope`` mint — and **nothing else**. It is strictly
non-effecting:

* it contains **no** ``adapter.dispatch()`` call site — not "unreachable",
  *absent* (a stronger property; ``.1R.16`` §24.2);
* it imports and calls **no** external-effect primitive at all — no
  ``subprocess`` / process spawn / ``os.system`` / ``os.popen`` / ``exec*``
  / ``spawn*`` / ``socket`` / ``ssl`` / provider SDK / HTTP client /
  credential resolver / FIDO2 / WebAuthn / CTAP / smartcard / USB (enforced
  by an AST guard in the ``.1R.17`` suite);
* it registers, enables, activates, or implements **no** adapter;
* it elevates **no** runtime capability and performs **no** ``Observed ->
  Approved/Executable`` transition;
* it writes **nothing** durable — it only *reads* the canonical
  ``consumption.json`` (``HPAC-AUTHORITY-CONSUMPTION/2.1``) that Gate 9
  created, re-derives current authority-generation / runtime-capability /
  containment state, and returns an immutable, non-authoritative
  ``DispatchEnvelope`` **or** a structured fail-closed reason.

**The dispatch-attempt durable lifecycle (mirror ``RuntimeInvocationRecord``,
``PREPARED -> EFFECT_ATTEMPT_STARTED -> {...}``, crash/restart determination,
``DISPATCH_UNCERTAIN``, the two 3S.2.1 MUST-FIX repairs, the runtime-inspect
repair) is Slice B (``.1R.19``) and is NOT implemented here.** The single
``adapter.dispatch(envelope)`` call site and a real (non-mock)
``RuntimeAdapter`` are Slice C (no phase ID) and are NOT implemented here.

**No positive production Gate-10 path exists** (``.1R.16`` §23): the
deterministic HPAC mechanism is permanently NON_REAL, the real Gate-7
coordinator always returns ``Gate7Result(decision="DENY")``, runtime
capability is ``unavailable``, no real adapter is registered, POL-005 is a
hard DENY at Gate 6, and there is no protected human-approval UI / real
FIDO2. ``run_gate9_atomic_authority_consumption`` is therefore structurally
unreachable, so a valid ``Gate9Result(status="consumed")`` — this
coordinator's mandatory input — cannot be produced in production. The
positive branches here are exercised **only** through a clearly-labelled
test-only substitution of the upstream provenance predicates + a
``tmp_path`` consumption store, exactly as Gates 5–9 are (``.1R.16`` §23;
``runtime_dispatch_gate9.py`` docstring). Runtime remains
``not_implemented / Observed / observe / unavailable``; POL-005 unchanged
and still hard DENY; 0 plugins / 0 capabilities.

**Semantic walls (``.1R.16`` §20, §30).**

* ``DispatchEnvelope != permission != human approval != PB ALLOW != Runtime
  Enforcement capability != consumed authority != permission to call
  adapter.dispatch()``. It is a non-authoritative, pre-effect
  binding/description artifact. :func:`is_dispatch_envelope` proves
  **process-local provenance only** — never effect authority. Constructing,
  copying, serializing, reproducing, or obtaining one from a fixture
  authorizes no effect (and there is no effect path here regardless).
* ``consumed human authority != runtime capability``. No amount of trusted
  ``Gate9Result`` / ``consumption.json`` / generation-snapshot state
  overrides ``execution_availability == "unavailable"``.
* ``dispatch attempted (Gate 9) != effect succeeded``. This module attempts
  nothing.

**F7 boundary (carried verbatim from ``runtime_dispatch_gate9.py``; threat model NOT broadened).**
The ``_DISPATCH_ENVELOPES`` identity registry and
this module's consumption of the upstream trusted objects run under the
same-account autonomous-agent assumption. They resist caller-supplied
**data** forgery (reconstruction, copy, serialized clone, duck-typed
lookalike, a schema-valid ``consumption.json`` planted outside the
authoritative writer); they do **not** resist arbitrary same-process Python code execution.
No UID / username / process-ownership / stdio / Git
identity / PCAE session identity / producer identity is trusted; only the
verified HPAC provenance chain establishes human authentication, only
exact-object registry membership establishes gate-result provenance, only
the store's create-only atomic primitive establishes consumed state, and
only a re-``stat`` / re-``sha256`` establishes executable identity at the
boundary. A process-isolation / hardening chapter is a separate,
unscheduled, non-prerequisite topic.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Optional

from pcae.core.runtime_authority import (
    compute_canonical_digest,
    is_trusted_validated_authority_projection,
    revalidate_validated_authority_projection,
)
from pcae.core.runtime_dispatch_gate9 import (
    _bounded_string,
    _consumption_generation_token,
    _lifecycle_generation_token,
    _runtime_execution_unavailable,
    build_production_authority_generation_resolver,
)
from pcae.core.runtime_dispatch_permission import (
    RuntimeDispatchConstructionError,
    RuntimeDispatchIdentity,
    RuntimeDispatchRequestConstructionInput,
    _expected_subject_scope_binding_digest,
    _validate_construction_inputs,
)
from pcae.core.runtime_invocation_authority_consumption import (
    AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION,
    CONSUMPTION_SCHEMA_VERSION,
    RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
    RuntimeInvocationAuthorityConsumptionStore,
    _validate_authority_generation_binding,
)

__all__ = [
    "DispatchEnvelope",
    "is_dispatch_envelope",
    "run_gate10_pre_effect_eligibility",
    "build_gate10_authority_generation_resolver",
    "build_gate10_capability_snapshot_resolver",
    "DISPATCH_ENVELOPE_SCHEMA_VERSION",
    "GATE10_ADVISORY_REASONS",
    "GATE10_ELIGIBILITY_REASON_IDS",
]

#: Schema identity stamped into every minted :class:`DispatchEnvelope`. A
#: closed field set; additive-only future evolution requires a new MINOR.
#: RPAC-001 v1.0 RPAC-REQ-029 (no normative contract change: RPAC-REQ-029
#: already names every field this envelope carries).
DISPATCH_ENVELOPE_SCHEMA_VERSION = "RPAC-DISPATCH-ENVELOPE/1.0"

#: The RDGO / HPAC / RPAC contract versions this coordinator was derived
#: against (``.1R.16`` §2.1). Stamped into the envelope's ``contract_versions``
#: for a downstream (Slice C) adapter's RPAC-REQ-030 version check.
_RDGO_VERSION = "RDGO-001/3.1"
_HPAC_VERSION = "HPAC-001/2.1"
_RPAC_VERSION = "RPAC-001/1.0"

#: Advisory (non-fatal) reasons this coordinator may surface alongside a
#: minted envelope — mirrors ``runtime_dispatch_gate9.GATE9_ADVISORY_REASONS``.
#: A PB ``policy_version`` drift after Gate 6 is resolved by **re-entering
#: Gate 6**, never by Gate 10; it is surfaced here only so an audit reader
#: knows the context drifted, and is **never** a licence to skip a check or
#: a positive basis for eligibility (``.1R.16`` §18 / F-G10-12).
GATE10_ADVISORY_REASONS: frozenset[str] = frozenset(
    {"gate10_policy_drift_requires_fresh_pb_re_evaluation"}
)

#: The stable fail-closed reason taxonomy (``.1R.16`` §21 / §35). Every one
#: produces **no external effect** and does **not** un-consume Gate-9
#: authority (``.1R.16`` §14 / F-G10-8). Parameterised ids
#: (``...:<detail>``) are listed by their stem.
GATE10_ELIGIBILITY_REASON_IDS: frozenset[str] = frozenset(
    {
        "gate10_untrusted_gate9_result",
        "gate10_gate9_status_not_consumed",
        "gate10_untrusted_gate8_result",
        "gate10_gate8_containment_not_established",
        "gate10_untrusted_gate7_result",
        "gate10_gate7_decision_not_allow",
        "gate10_untrusted_gate6_decision",
        "gate10_gate6_decision_not_allow",
        "gate10_untrusted_gate5_result",
        "gate10_invalid_identity",
        "gate10_invalid_construction_input",
        "gate10_invalid_authority_current_time",
        "gate10_invalid_repo_root",
        "gate10_invalid_effect_plan",
        "gate10_invalid_descriptor_resolver",
        "gate10_invalid_lifecycle_store",
        "gate10_invalid_consumption_store",
        "gate10_invalid_capability_snapshot_resolver",
        "gate10_invalid_authority_generation_resolver",
        "gate10_invocation_binding_mismatch",
        "gate10_request_currentness_drift",  # :<fact>
        "gate10_gate7_lineage_mismatch",
        "gate10_consumption_record_read_back_failed",
        "gate10_consumption_record_generation_snapshot_absent",
        "gate10_consumption_snapshot_malformed",
        "gate10_lineage_binding_mismatch",
        "gate10_authority_generation_snapshot_incomplete",
        "gate10_authority_generation_drift",  # :<source>
        "gate10_consumption_state_inconsistent",
        "gate10_stale_validated_authority_projection",
        "gate10_containment_recomputation_failed",
        "gate10_containment_evidence_recomputation_mismatch",
        "gate10_executable_identity_drift",
        "gate10_effect_plan_requires_credentials",
        "gate10_runtime_capability_not_unavailable",
        "gate10_pb_lineage_not_allow",
        "gate10_re_lineage_not_allow",
        "gate10_re_decision_expired",
        "gate10_internal_error_fail_closed",
    }
)

#: The five current authority-generation markers a trusted Gate-10
#: ``authority_generation_resolver`` MUST return (``.1R.16`` §11 /
#: F-G10-5). Superset of the Gate-9 three-marker shape
#: (``runtime_dispatch_gate9._AUTHORITY_GENERATION_KEYS``): the Gate-10
#: battery additionally re-derives ``lifecycle_generation`` and
#: ``consumption_generation``.
_GATE10_AUTHORITY_GENERATION_KEYS: frozenset[str] = frozenset(
    {
        "principal_generation",
        "credential_generation",
        "approval_generation",
        "lifecycle_generation",
        "consumption_generation",
    }
)

#: The order authority-generation markers are compared in; the first
#: differing marker is named in ``gate10_authority_generation_drift:<source>``
#: (``.1R.16`` §11). ``consumption_generation`` is compared separately (the
#: durable snapshot is ``"absent"`` and Gate 10 expects to see the record it
#: is validating as ``"present"`` — an expected transition, not drift;
#: ``.1R.16`` §11 last row).
_GATE10_AUTHORITY_GENERATION_DRIFT_ORDER: tuple[str, ...] = (
    "principal_generation",
    "credential_generation",
    "approval_generation",
    "lifecycle_generation",
)


# ═══════════════════════════════════════════════════════════════════════
# DispatchEnvelope — immutable, non-authoritative, identity-only,
# non-serializable, registry-provenanced (RPAC-REQ-029; ``.1R.16`` §29–§33)
# ═══════════════════════════════════════════════════════════════════════

_DISPATCH_ENVELOPE_CONSTRUCTOR_SEAL = object()

#: The provenance boundary for a ``DispatchEnvelope``: exact-object
#: membership, keyed by identity (``__hash__`` / ``__eq__`` are ``id(self)``
#: / ``self is other``). The only insertion point is
#: :func:`run_gate10_pre_effect_eligibility`'s eligible return path; nothing
#: outside this module adds to it. ``shape != provenance``;
#: ``provenance != effect authority`` (``.1R.16`` §33 / F-G10-16 pattern).
_DISPATCH_ENVELOPES: "set[DispatchEnvelope]" = set()


class DispatchEnvelope:
    """The immutable, non-authoritative pre-effect binding artifact
    :func:`run_gate10_pre_effect_eligibility` mints when — and only when —
    the full RDGO-001 v3.1 §11 items 1–6 + §16/§17 read-back battery passes
    (RPAC-REQ-029).

    It **describes** the exact effect a future Slice-C
    ``adapter.dispatch(envelope)`` call site *would* cross the boundary for
    — the immutable invocation identity, the durably-consumed authority
    record digest, the recomputed effect-plan / containment-evidence /
    executable-identity digests, the frozen PB / RE decision digests, the
    fresh runtime-capability snapshot digest, and an expiration. It
    **authorizes** nothing (``.1R.16`` §30):

    * ``DispatchEnvelope != permission != human approval != PB ALLOW !=
      Runtime Enforcement capability != consumed authority != permission to
      call adapter.dispatch()``;
    * like ``Gate5Result`` … ``Gate9Result`` it is **not** caller-
      constructable (the ``_seal`` guard rejects direct construction;
      :func:`is_dispatch_envelope` checks membership in this module's
      process-local identity registry), **not** serializable (``__reduce__``
      raises), identity-only for ``==`` / ``hash``, and **not**
      subclassable;
    * copying, serializing, reproducing its fields, or obtaining one from a
      test fixture does not by itself authorize any effect — and there is no
      effect path in this phase regardless (``.1R.16`` §31).
    """

    __slots__ = (
        "envelope_schema_version",
        "invocation_id",
        "attempt_id",
        "idempotency_key",
        "proof_id",
        "approval_id",
        "runtime_target_id",
        "adapter_id",
        "descriptor_digest",
        "target_config_digest",
        "consumption_record_digest",
        "durable_record_reference",
        "authority_projection_digest",
        "approval_digest",
        "authority_generation_snapshot_digest",
        "pb_request_digest",
        "pb_decision_digest",
        "re_decision_digest",
        "re_expires_at",
        "effect_plan_digest",
        "containment_evidence_digest",
        "live_preflight_digest",
        "executable_identity_digest",
        "runtime_capability_snapshot_digest",
        "target_status_digest",
        "contract_versions",
        "minted_at",
        "expires_at",
        "envelope_digest",
        "advisory_reasons",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("DispatchEnvelope must not be subclassed")

    def __init__(self, *, _seal: object, **fields: object) -> None:
        if _seal is not _DISPATCH_ENVELOPE_CONSTRUCTOR_SEAL:
            raise TypeError(
                "DispatchEnvelope cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_gate10_eligibility."
                "run_gate10_pre_effect_eligibility"
            )
        for name in self.__slots__:
            if name == "_seal":
                continue
            object.__setattr__(self, name, fields[name])
        self._seal = _seal

    def __reduce__(self):
        raise TypeError(
            "DispatchEnvelope is ephemeral and non-serializable; it is a "
            "non-authoritative pre-effect binding artifact, not a bearer "
            "token. The durable truth is consumption.json, which every "
            "consumer must re-read (RDGO-001 v3.1 §11; RPAC-REQ-029)."
        )

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_seal", None) is _DISPATCH_ENVELOPE_CONSTRUCTOR_SEAL:
            raise AttributeError("DispatchEnvelope is immutable")
        object.__setattr__(self, name, value)

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<DispatchEnvelope invocation_id={self.invocation_id!r} "
            f"attempt_id={self.attempt_id!r} identity={id(self):#x}>"
        )

    def to_reference_document(self) -> dict:
        """A plain-``dict`` projection of every bound digest/identifier — for
        audit display and for a future Slice-C adapter's RPAC-REQ-030
        syntactic check. This is **not** deserialization back into a trusted
        envelope: reconstructing this dict grants nothing
        (:func:`is_dispatch_envelope` would return ``False``)."""
        return {
            name: getattr(self, name)
            for name in self.__slots__
            if name != "_seal"
        }


def is_dispatch_envelope(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past
    :func:`run_gate10_pre_effect_eligibility` call minted on an eligible
    read-back — never based on ``isinstance``, fields, equality, or any
    shape property. Fails closed for a forgery, a copy, a reconstruction,
    ``object.__new__``, or a stale handle.

    **Provenance only.** A ``True`` result means "this object was minted by
    this coordinator", **not** "an effect is authorized". There is no effect
    path in this phase; a future Slice-C dispatch call site would re-run the
    executable-identity read-back (F-G10-11) and the full battery
    immediately before any ``adapter.dispatch()`` (``.1R.16`` §33).
    """
    return isinstance(candidate, DispatchEnvelope) and candidate in _DISPATCH_ENVELOPES


# ═══════════════════════════════════════════════════════════════════════
# N-16-1 — production Gate-10 resolver factories (``.1R.16`` §11.1)
# ═══════════════════════════════════════════════════════════════════════


def build_gate10_capability_snapshot_resolver() -> Callable[[], dict]:
    """Return the trusted ``capability_snapshot_resolver`` a real Gate-10
    caller MUST pass to :func:`run_gate10_pre_effect_eligibility` (N-16-1,
    ``.1R.16`` §13 / §11.1).

    Each call re-reads the **canonical** runtime-capability constants from
    ``pcae.core.runtime_introspection`` — the exact same source and dict
    shape ``runtime_dispatch_gate9._runtime_execution_unavailable`` already
    checks. It creates no new capability source, reads no registry, mutates
    nothing, and today resolves to::

        {"current_runtime_state": "Observed",
         "current_maximum_plugin_capability": "observe",
         "execution_availability": "unavailable"}

    so Gate-10 eligibility's capability sub-check (F-G10-7) only ever passes
    for the current non-executing posture, and any drift away from it fails
    closed (``.1R.16`` §12 / §13 / §19).
    """

    def _resolve() -> dict:
        from pcae.core import runtime_introspection as ri

        return {
            "current_runtime_state": ri.CURRENT_RUNTIME_STATE,
            "current_maximum_plugin_capability": ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
            "execution_availability": ri.EXECUTION_AVAILABILITY,
        }

    return _resolve


def build_gate10_authority_generation_resolver(
    *,
    principal_registry: object,
    principal_id: str,
    credential_id: str,
    approval_store: object,
    approval_id: str,
    lifecycle_store: object,
    consumption_store: object,
    proof_id: str,
) -> Callable[[], dict]:
    """Return the trusted five-marker ``authority_generation_resolver`` a
    real Gate-10 caller MUST pass to
    :func:`run_gate10_pre_effect_eligibility` (N-16-1, ``.1R.16`` §11 /
    §11.1 / F-G10-5).

    Composed from the frozen Gate-9 production factory
    (``runtime_dispatch_gate9.build_production_authority_generation_resolver``
    — ``principal_generation`` / ``credential_generation`` /
    ``approval_generation``, byte-for-byte the same tokens, **no Gate-9
    behaviour change**) plus the two markers the Gate-10 battery adds:

    * ``lifecycle_generation`` — digest over the ordered
      ``(sequence, state, event_digest)`` triples of the entire canonical,
      provenance-checked proof lifecycle chain
      (``runtime_dispatch_gate9._lifecycle_generation_token``, reused);
    * ``consumption_generation`` — the current canonical consumption-record
      state for ``proof_id``: ``"present:<record_digest>"`` once Gate 9's
      immutable record exists (the expected Gate-10 observation), or
      ``"absent"`` if it does not
      (``runtime_dispatch_gate9._consumption_generation_token``, reused).

    Each call re-reads canonical durable state only. Removal / quarantine /
    unreadable principal / credential / approval / lifecycle → the store
    raises → the resolver raises → the coordinator fails closed
    (``gate10_internal_error_fail_closed``), producing no envelope. No wall
    clock, mtime, nonce, or process identity enters any token.
    """

    _base = build_production_authority_generation_resolver(
        principal_registry=principal_registry,
        principal_id=principal_id,
        credential_id=credential_id,
        approval_store=approval_store,
        approval_id=approval_id,
    )

    def _resolve() -> dict:
        markers = dict(_base())  # principal / credential / approval
        markers["lifecycle_generation"] = _lifecycle_generation_token(
            lifecycle_store, proof_id
        )
        token = _consumption_generation_token(consumption_store, proof_id)
        if token and token[0] == "present":
            markers["consumption_generation"] = "present:" + (
                token[1] if len(token) > 1 else ""
            )
        else:
            markers["consumption_generation"] = "absent"
        return markers

    return _resolve


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _hash_file_sha256(path: str) -> Optional[str]:
    """Re-``stat`` + re-``sha256`` the exact resolved executable immediately
    before the (non-existent, Slice-C) effect (F-G10-11 / RDGO-001 v3.1
    §15 TOCTOU row). Pure inspection — opens the file read-only for hashing,
    exactly as ``runtime_dispatch_gate8._hash_file`` does; spawns no
    process. Returns ``None`` on absence / permission change / symlink / any
    read error → the caller fails closed (``gate10_executable_identity_drift``).
    """
    try:
        p = Path(path)
        if p.is_symlink() or not p.is_file():
            return None
        digest = hashlib.sha256()
        with open(p, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _executable_identity_digest(resolved: object) -> str:
    """Recompute the ``target_binding.executable_identity_digest`` exactly as
    ``runtime_dispatch_gate9`` step 15 does — a canonical digest over the
    resolved executable's ``sha256`` / ``path`` / ``version``."""
    return compute_canonical_digest(
        {
            "sha256": getattr(resolved, "sha256", ""),
            "path": getattr(resolved, "path", ""),
            "version": getattr(resolved, "version", ""),
        }
    )


def _validate_gate10_generation_markers(markers: object) -> Optional[str]:
    """Shape-check the trusted resolver's return (F-G10-5). Returns a
    fail-closed reason id or ``None``."""
    if not isinstance(markers, dict) or set(markers) != _GATE10_AUTHORITY_GENERATION_KEYS:
        return "gate10_authority_generation_snapshot_incomplete"
    for key in _GATE10_AUTHORITY_GENERATION_KEYS:
        if not _bounded_string(markers[key], 320):
            return "gate10_authority_generation_snapshot_incomplete"
    return None


def _first_generation_drift(durable: dict, current: dict) -> Optional[str]:
    """Return the first authority-generation marker whose durable-snapshot
    value differs from the freshly re-derived current value (excluding
    ``consumption_generation``), else ``None`` (``.1R.16`` §11 / §12)."""
    for key in _GATE10_AUTHORITY_GENERATION_DRIFT_ORDER:
        if durable.get(key) != current.get(key):
            return key
    return None


# ═══════════════════════════════════════════════════════════════════════
# The Gate-10 pre-effect eligibility coordinator
# ═══════════════════════════════════════════════════════════════════════


def run_gate10_pre_effect_eligibility(
    gate9_result: object,
    *,
    gate8_result: object,
    gate7_result: object,
    gate6_decision: object,
    gate5_result: object,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    authority_current_time: str,
    repo_root: Path,
    effect_plan: object,
    descriptor_resolver: Callable[[RuntimeDispatchRequestConstructionInput], object],
    lifecycle_store: object,
    consumption_store: object,
    capability_snapshot_resolver: Callable[[], object],
    authority_generation_resolver: Callable[[], object],
    validated_authority_projection: object = None,
) -> tuple[Optional["DispatchEnvelope"], tuple[str, ...]]:
    """Run the front half of RDGO-001 v3.1 §11 Gate 10 — the pre-effect
    eligibility + read-back battery (§11 items 1–6) + §16/§17 containment
    and executable-identity read-back — for one bound ``runtime_dispatch``
    request, and mint the RPAC-REQ-029 ``DispatchEnvelope`` **or** return a
    structured fail-closed reason.

    **This function never crosses an external effect boundary.** It contains
    no ``adapter.dispatch()`` call site, spawns no process, and writes
    nothing durable. A minted ``DispatchEnvelope`` is a non-authoritative
    description; the actual effect (Slice C) is a separate, unbuilt,
    human-authority-gated boundary.

    Returns ``(DispatchEnvelope, advisory_reasons)`` when — and only when —
    **all** of the following hold (``.1R.16`` §6, §8–§13, §16–§19):

    1. ``is_gate9_result(gate9_result)`` **and** ``gate9_result.status ==
       "consumed"`` — provenance is not success; ``already_consumed`` is
       never a re-entry licence (F-G10-1);
    2. the upstream ``Gate8Result`` (``containment_established is True``) /
       ``Gate7Result`` (``ALLOW``) / ``Gate6Decision`` (``ALLOW``) /
       ``Gate5Result`` are exact-object registry members and the invocation
       identity is consistent across every link + ``identity`` (RDGO-001
       §10a);
    3. the canonical construction re-check passes; the handed ``Gate8Result``
       was produced over exactly this ``Gate7Result``
       (``gate10_gate7_lineage_mismatch``);
    4. a fresh re-read of the durable canonical ``consumption.json``
       (``resolve(gate9_result.proof_id)``) returns a ``/2.1`` record with a
       present, valid ``authority_generation_binding``; its ``record_digest``
       byte-verifies against ``gate9_result.record_digest``; the
       ``invocation_id`` / ``attempt_id`` / ``idempotency_key`` / ``proof_id``
       / ``approval_id`` / ``runtime_target_id`` / ``task_id`` /
       ``prompt_hash`` / ``dispatch_binding.state`` all match the durable
       record **and** the live request (F-G10-2 / F-G10-3 / lineage);
    5. the durable Gate-6 lineage's ``pb_binding.decision == "ALLOW"`` and
       the Gate-7 lineage's ``runtime_enforcement_binding.verdict == "ALLOW"``
       with ``expires_at`` strictly after ``authority_current_time``
       (F-G10-12 / F-G10-13). Gate 10 does **not** re-run PB or RE policy;
    6. the fresh runtime-capability snapshot is exactly ``Observed /
       observe / unavailable`` (F-G10-7) — any drift fails closed;
    7. the freshly re-derived current authority-generation vector
       (principal / credential / approval / lifecycle) equals the durable
       ``authority_generation_binding`` snapshot; ``consumption_generation``
       has transitioned ``"absent" -> "present:<this record's digest>"``
       (expected, not drift) (F-G10-4 / F-G10-5);
    8. when a trusted ``validated_authority_projection`` is supplied,
       ``revalidate_validated_authority_projection`` still passes at
       ``authority_current_time`` (post-Gate-9 revocation / expiry fails
       closed) (``.1R.16`` §12);
    9. re-running ``run_gate8_process_containment`` over freshly re-resolved
       descriptor / executable / repository-scoped cwd reproduces the
       durable ``containment_evidence_digest`` / ``live_preflight_digest`` /
       ``gate7_result_digest`` and the handed ``Gate8Result``'s digests
       (F-G10-10); the effect plan requires no credentials (F-G10-17);
    10. a fresh re-``stat`` + re-``sha256`` of the exact resolved executable
        reproduces the durable ``target_binding.executable_identity_digest``
        (F-G10-11).

    Returns ``(None, (reason_id,))`` — creating no envelope — on any
    fail-closed rejection. The reason ids are in
    :data:`GATE10_ELIGIBILITY_REASON_IDS`; ``gate10_authority_generation_drift``
    and ``gate10_request_currentness_drift`` carry a ``:<detail>`` suffix. A
    rejection produces **no external effect** and does **not** un-consume
    Gate-9 authority (the immutable ``consumption.json`` is byte-unchanged);
    any new attempt requires a fresh ``invocation_id`` / ``attempt_id`` /
    approval / proof (``.1R.16`` §14 / §15).
    """
    try:
        from pcae.core.runtime_dispatch_gate5 import Gate5Result, is_gate5_result
        from pcae.core.runtime_dispatch_gate7 import Gate7Result, is_gate7_result
        from pcae.core.runtime_dispatch_gate8 import (
            Gate8EffectPlan,
            Gate8Result,
            _gate7_result_digest,
            is_gate8_result,
            run_gate8_process_containment,
        )
        from pcae.core.runtime_dispatch_gate9 import Gate9Result, is_gate9_result
        from pcae.core.runtime_dispatch_permission import Gate6Decision, is_gate6_decision

        # 1. Gate-9 provenance + exact success status (F-G10-1). Provenance is
        #    NOT success: is_gate9_result is True for both "consumed" and
        #    "already_consumed"; only "consumed" is a Gate-10 input.
        if not is_gate9_result(gate9_result):
            return None, ("gate10_untrusted_gate9_result",)
        assert isinstance(gate9_result, Gate9Result)
        if gate9_result.status != "consumed":
            return None, ("gate10_gate9_status_not_consumed",)

        # 2. Upstream lineage provenance + exact decisions (RDGO-001 §11
        #    item 4; §16). A trusted NEGATIVE Gate8Result is a hard stop.
        if not is_gate8_result(gate8_result):
            return None, ("gate10_untrusted_gate8_result",)
        assert isinstance(gate8_result, Gate8Result)
        if gate8_result.containment_established is not True:
            return None, ("gate10_gate8_containment_not_established",)
        if not is_gate7_result(gate7_result):
            return None, ("gate10_untrusted_gate7_result",)
        assert isinstance(gate7_result, Gate7Result)
        if gate7_result.decision != "ALLOW":
            return None, ("gate10_gate7_decision_not_allow",)
        if not is_gate6_decision(gate6_decision):
            return None, ("gate10_untrusted_gate6_decision",)
        assert isinstance(gate6_decision, Gate6Decision)
        if gate6_decision.decision != "ALLOW":
            return None, ("gate10_gate6_decision_not_allow",)
        if not is_gate5_result(gate5_result):
            return None, ("gate10_untrusted_gate5_result",)
        assert isinstance(gate5_result, Gate5Result)

        # 3. Structural input guards.
        if type(identity) is not RuntimeDispatchIdentity:
            return None, ("gate10_invalid_identity",)
        if type(inputs) is not RuntimeDispatchRequestConstructionInput:
            return None, ("gate10_invalid_construction_input",)
        if not _bounded_string(authority_current_time, 64):
            return None, ("gate10_invalid_authority_current_time",)
        if not isinstance(repo_root, Path):
            return None, ("gate10_invalid_repo_root",)
        if type(effect_plan) is not Gate8EffectPlan:
            return None, ("gate10_invalid_effect_plan",)
        if not callable(descriptor_resolver):
            return None, ("gate10_invalid_descriptor_resolver",)
        if type(lifecycle_store) is not _lifecycle_store_type():
            return None, ("gate10_invalid_lifecycle_store",)
        if type(consumption_store) is not RuntimeInvocationAuthorityConsumptionStore:
            return None, ("gate10_invalid_consumption_store",)
        if not callable(capability_snapshot_resolver):
            return None, ("gate10_invalid_capability_snapshot_resolver",)
        if not callable(authority_generation_resolver):
            return None, ("gate10_invalid_authority_generation_resolver",)

        # 4. Single consistent invocation across every link (RDGO-001 §10a).
        if (
            gate9_result.invocation_id != identity.invocation_id
            or gate5_result.invocation_id != identity.invocation_id
            or gate6_decision.invocation_id != identity.invocation_id
            or gate7_result.invocation_id != identity.invocation_id
            or gate8_result.invocation_id != identity.invocation_id
            or gate9_result.attempt_id != identity.attempt_id
            or gate6_decision.attempt_id != identity.attempt_id
            or gate7_result.attempt_id != identity.attempt_id
            or gate8_result.attempt_id != identity.attempt_id
            or gate7_result.request_id != gate6_decision.request_id
            or gate8_result.request_id != gate6_decision.request_id
        ):
            return None, ("gate10_invocation_binding_mismatch",)

        # 5. Canonical construction re-check (RDGO-001 §15 TOCTOU; F-G10-2).
        try:
            _validate_construction_inputs(inputs)
        except RuntimeDispatchConstructionError as exc:
            return None, (f"gate10_request_currentness_drift:{exc}",)

        # 6. Gate-7 lineage digest cross-check — the handed Gate8Result must
        #    have been produced over exactly this Gate7Result.
        if gate8_result.gate7_result_digest != _gate7_result_digest(gate7_result):
            return None, ("gate10_gate7_lineage_mismatch",)

        # 7. Fresh durable re-read of the canonical consumption.json
        #    (F-G10-2). Gate 10 trusts THE DURABLE RECORD, re-derived from
        #    disk — never the in-memory Gate9Result fields beyond using them
        #    as the lookup + comparison key (``.1R.16`` §8).
        proof_id = gate9_result.proof_id
        try:
            record = consumption_store.resolve(proof_id)
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate10_consumption_record_read_back_failed",)
        if record is None:
            # Absent is NOT "unconsumed authority to reuse" — a fresh
            # invocation is required (``.1R.16`` §8).
            return None, ("gate10_consumption_record_read_back_failed",)

        # 8. /2.0 ineligibility + durable generation-snapshot presence
        #    (F-G10-3 / F-G10-4). No compatibility fallback.
        if (
            record.consumption_schema_version != CONSUMPTION_SCHEMA_VERSION
            or record.authority_generation_binding is None
        ):
            return None, ("gate10_consumption_record_generation_snapshot_absent",)
        try:
            _validate_authority_generation_binding(record.authority_generation_binding)
        except Exception:
            return None, ("gate10_consumption_snapshot_malformed",)
        durable_snapshot = record.authority_generation_binding
        if durable_snapshot.get("snapshot_schema_version") != (
            AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION
        ):
            return None, ("gate10_consumption_snapshot_malformed",)
        # Gate 9 only ever writes ``consumption_generation == "absent"`` (a
        # present/uncertain record short-circuits before its create) — the
        # record's own creation was the transition (``.1R.16`` §10).
        if durable_snapshot.get("consumption_generation") != "absent":
            return None, ("gate10_consumption_snapshot_malformed",)

        # 9. Exact digest + lineage binding: durable record <-> Gate9Result
        #    <-> live request (F-G10-2 / RDGO-001 §11 item 4).
        ident = record.request_identity
        auth = record.authority_binding
        if (
            record.record_digest != gate9_result.record_digest
            or ident.get("invocation_id") != identity.invocation_id
            or ident.get("attempt_id") != identity.attempt_id
            or ident.get("idempotency_key") != identity.idempotency_key
            or auth.get("proof_id") != proof_id
            or auth.get("approval_id") != gate9_result.approval_id
            or auth.get("approval_id") != gate5_result.approval_id
            or record.target_binding.get("runtime_target_id") != inputs.runtime_target_id
            or record.repository_task_binding.get("task_id") != inputs.task_id
            or record.prompt_binding.get("prompt_hash") != inputs.prompt_hash
            or record.dispatch_binding.get("state") != gate9_result.dispatch_state
            or record.dispatch_binding.get("state") != "dispatch_attempted"
        ):
            return None, ("gate10_lineage_binding_mismatch",)

        # 10. POL-005 / Gate-6 lineage (F-G10-12). Trust the durable Gate-6
        #     decision; require ALLOW; do NOT re-run PB policy (Gate 6 owns
        #     it exclusively). A record exists only because Gate 6 ALLOWed —
        #     impossible today for a truthful non-simulation request
        #     (POL-005 hard DENY). Trusted consumed authority does not
        #     override POL-005.
        if record.pb_binding.get("decision") != "ALLOW":
            return None, ("gate10_pb_lineage_not_allow",)

        # 11. Runtime Enforcement lineage (F-G10-13). Re-check FROM Gate 7's
        #     durable decision: verdict ALLOW, not expired at Gate-10 entry.
        #     ``matched_no_go_ids`` is a per-decision diagnostic, NOT an
        #     authority input — not consulted here.
        re_binding = record.runtime_enforcement_binding
        if re_binding.get("verdict") != "ALLOW":
            return None, ("gate10_re_lineage_not_allow",)
        re_expires_at = re_binding.get("expires_at")
        if not _bounded_string(re_expires_at, 64) or re_expires_at <= authority_current_time:
            return None, ("gate10_re_decision_expired",)

        # 12. Final runtime-capability re-read INSIDE the battery, immediately
        #     before minting the envelope (F-G10-6 / F-G10-7). Gate-7's
        #     earlier decision is NOT trusted indefinitely. ``consumed human
        #     authority != runtime capability``: no upstream state overrides
        #     ``execution_availability == "unavailable"``. Any drift away
        #     from the canonical non-executing posture fails closed.
        capability_snapshot = capability_snapshot_resolver()
        if not _runtime_execution_unavailable(capability_snapshot):
            return None, ("gate10_runtime_capability_not_unavailable",)

        # 13. Current authority-generation vector re-derivation + compare
        #     against the durable snapshot (F-G10-4 / F-G10-5). From durable
        #     stores only — restart-safe (every token a digest over durable
        #     state, no wall clock / nonce / process identity).
        current_markers = authority_generation_resolver()
        shape_reason = _validate_gate10_generation_markers(current_markers)
        if shape_reason is not None:
            return None, (shape_reason,)
        drift = _first_generation_drift(durable_snapshot, current_markers)
        if drift is not None:
            return None, (f"gate10_authority_generation_drift:{drift}",)
        # ``consumption_generation``: durable snapshot is "absent"; Gate 10
        # expects to see the exact record it is validating as
        # "present:<record_digest>" — an EXPECTED transition, not drift
        # (``.1R.16`` §11 last row). Anything else is inconsistency.
        if current_markers["consumption_generation"] != "present:" + record.record_digest:
            return None, ("gate10_consumption_state_inconsistent",)

        # 14. Optional trusted-projection revalidation at Gate-10 entry
        #     (``.1R.16`` §12 / §30.1 point 4). Covers post-Gate-9 principal
        #     / credential revocation, approval wall-clock expiry, lifecycle
        #     invalidation for the in-process (non-restart) path;
        #     restart-safe drift is already covered by step 13.
        if validated_authority_projection is not None:
            if not is_trusted_validated_authority_projection(
                validated_authority_projection
            ):
                return None, ("gate10_stale_validated_authority_projection",)
            if not revalidate_validated_authority_projection(
                validated_authority_projection, current_time=authority_current_time
            ):
                return None, ("gate10_stale_validated_authority_projection",)

        # 15. Executable identity re-stat / re-sha256 (F-G10-11 / RDGO-001
        #     v3.1 §15 TOCTOU row "exact hash before spawn"). Pure
        #     inspection; spawns nothing. Checked before the containment
        #     re-run so executable drift is attributed to its own specific
        #     reason id (the Gate-8 re-run would also catch it, less
        #     specifically). A future Slice-C dispatch call site re-runs this
        #     re-hash a second time immediately before ``adapter.dispatch()``
        #     with no intervening effectful I/O (``.1R.16`` §17).
        resolved = descriptor_resolver(inputs)
        live_sha256 = _hash_file_sha256(getattr(resolved, "path", ""))
        if live_sha256 is None or live_sha256 != getattr(resolved, "sha256", None):
            return None, ("gate10_executable_identity_drift",)
        executable_identity_digest = _executable_identity_digest(resolved)
        if executable_identity_digest != record.target_binding.get(
            "executable_identity_digest"
        ):
            return None, ("gate10_executable_identity_drift",)

        # 16. Final containment / effect-plan read-back (F-G10-10 / §16).
        #     Re-run the Gate-8 containment ESTABLISHMENT mechanism over
        #     freshly re-resolved inputs and recompute the evidence digest —
        #     NOT a Gate-8 policy re-decision, and never trusting the
        #     ephemeral handed Gate8Result's stored digests as
        #     self-authenticating. Mirrors ``runtime_dispatch_gate9.py``
        #     step 8 exactly.
        fresh_gate8, _fresh_reasons = run_gate8_process_containment(
            gate7_result,
            gate5_result=gate5_result,
            identity=identity,
            inputs=inputs,
            authority_current_time=authority_current_time,
            repo_root=repo_root,
            effect_plan=effect_plan,
            descriptor_resolver=descriptor_resolver,
        )
        if fresh_gate8 is None or fresh_gate8.containment_established is not True:
            return None, ("gate10_containment_recomputation_failed",)
        if (
            fresh_gate8.containment_evidence_digest
            != gate8_result.containment_evidence_digest
            or fresh_gate8.effect_plan_digest != gate8_result.effect_plan_digest
            or fresh_gate8.live_preflight_digest != gate8_result.live_preflight_digest
            or fresh_gate8.gate7_result_digest != gate8_result.gate7_result_digest
            or fresh_gate8.containment_evidence_digest
            != record.dispatch_binding.get("containment_evidence_ref", {}).get("digest")
            or fresh_gate8.live_preflight_digest
            != record.dispatch_binding.get("containment_evidence_ref", {}).get(
                "live_preflight_digest"
            )
        ):
            return None, ("gate10_containment_evidence_recomputation_mismatch",)

        # 17. Credential boundary (F-G10-17). The first effect MUST be a
        #     no-credential local process. Any credential requirement ->
        #     fail closed (a credential-backed effect needs a separate
        #     governed credential boundary — RPAC-REQ-058/084).
        if getattr(effect_plan, "credentials_required", True) is not False:
            return None, ("gate10_effect_plan_requires_credentials",)
        if getattr(effect_plan, "network_denied", False) is not True:
            return None, ("gate10_containment_evidence_recomputation_mismatch",)

        # 18. Every check passed. Mint the immutable, non-authoritative
        #     DispatchEnvelope (RPAC-REQ-029). NO adapter.dispatch() call
        #     site exists in this module; the envelope authorizes nothing
        #     (``.1R.16`` §30 / §31).
        advisory = tuple(
            r
            for r in getattr(gate5_result, "advisory_reasons", ())
            if ("gate10_" + r) in GATE10_ADVISORY_REASONS
            or r in GATE10_ADVISORY_REASONS
        )
        capability_snapshot_digest = compute_canonical_digest(capability_snapshot)
        target_status_digest = compute_canonical_digest(
            {
                "runtime_capability_snapshot": capability_snapshot,
                "runtime_target_id": inputs.runtime_target_id,
                # No real adapter is registered (RuntimeRegistry empty);
                # adapter-instance registration is re-checked at the Slice-C
                # dispatch call site, which does not exist yet.
                "adapter_registration": "none",
            }
        )
        durable_record_reference = f"proofs/v2/{proof_id}/consumption.json"
        contract_versions = {
            "rdgo": _RDGO_VERSION,
            "hpac": _HPAC_VERSION,
            "rpac": _RPAC_VERSION,
            "consumption_schema": CONSUMPTION_SCHEMA_VERSION,
            "authority_generation_snapshot_schema": (
                AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION
            ),
            "envelope_schema": DISPATCH_ENVELOPE_SCHEMA_VERSION,
        }

        fields = {
            "envelope_schema_version": DISPATCH_ENVELOPE_SCHEMA_VERSION,
            "invocation_id": identity.invocation_id,
            "attempt_id": identity.attempt_id,
            "idempotency_key": identity.idempotency_key,
            "proof_id": proof_id,
            "approval_id": gate9_result.approval_id,
            "runtime_target_id": inputs.runtime_target_id,
            "adapter_id": record.target_binding.get("adapter_id"),
            "descriptor_digest": record.target_binding.get("descriptor_digest"),
            "target_config_digest": record.target_binding.get("target_config_digest"),
            "consumption_record_digest": record.record_digest,
            "durable_record_reference": durable_record_reference,
            "authority_projection_digest": auth.get("authority_projection_digest"),
            "approval_digest": auth.get("approval_digest"),
            "authority_generation_snapshot_digest": compute_canonical_digest(
                durable_snapshot
            ),
            "pb_request_digest": record.pb_binding.get("request_digest"),
            "pb_decision_digest": record.pb_binding.get("decision_digest"),
            "re_decision_digest": re_binding.get("decision_digest"),
            "re_expires_at": re_expires_at,
            "effect_plan_digest": fresh_gate8.effect_plan_digest,
            "containment_evidence_digest": fresh_gate8.containment_evidence_digest,
            "live_preflight_digest": fresh_gate8.live_preflight_digest,
            "executable_identity_digest": executable_identity_digest,
            "runtime_capability_snapshot_digest": capability_snapshot_digest,
            "target_status_digest": target_status_digest,
            "contract_versions": contract_versions,
            "minted_at": authority_current_time,
            # The envelope MUST NOT outlive the Runtime Enforcement decision
            # it is bound to (RDGO-001 §8 "single-attempt, expiring";
            # RPAC-REQ-029 "expiration").
            "expires_at": re_expires_at,
            "advisory_reasons": advisory,
        }
        fields["envelope_digest"] = compute_canonical_digest(
            {k: v for k, v in fields.items() if k not in ("advisory_reasons",)}
        )

        envelope = DispatchEnvelope(_seal=_DISPATCH_ENVELOPE_CONSTRUCTOR_SEAL, **fields)
        _DISPATCH_ENVELOPES.add(envelope)
        return envelope, advisory
    except Exception:
        # Fail closed on any unexpected exception — no partial output, no
        # DispatchEnvelope (RDGO-001 §0, §11; ``.1R.16`` §34).
        return None, ("gate10_internal_error_fail_closed",)


def _lifecycle_store_type():
    # Reuse the Gate-9 accessor rather than importing ``hpac_lifecycle``
    # directly — this module's only need for the lifecycle store is a
    # structural type guard, identical to Gate 9's.
    from pcae.core.runtime_dispatch_gate9 import _lifecycle_store_type as _g9_lst

    return _g9_lst()
