"""
Gate-9 Atomic Authority Consumption coordinator — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.14.

Implements RDGO-001 v3.0 §10 Gate 9 (durable pre-dispatch record + atomic
one-shot authority consumption) as the single trusted owner of the
authority-consumption boundary for one bound ``runtime_dispatch`` request,
exactly as frozen by the ``.1R.9`` planning document (§10, §11, §12, §17,
§18, §19) and the ``.1R.13.1`` §16 Gate-8 → Gate-9 handoff contract. It
mirrors the shape of ``runtime_dispatch_gate5.run_gate5`` and the
Gate-6 / Gate-7 / Gate-8 coordinators:

``run_gate9_atomic_authority_consumption`` is the frozen **sole** production
owner of the RDGO-001 §10 Gate-9 boundary for ``runtime_dispatch``. It:

* consumes a registry-provenanced
  :class:`~runtime_dispatch_gate8.Gate8Result` **only** via
  ``runtime_dispatch_gate8.is_gate8_result`` — the exact object a prior
  ``run_gate8_process_containment`` call returned — and **additionally**
  requires ``gate8_result.containment_established is True`` by identity
  check (RDGO-001 §9/§10; a trusted **negative** ``Gate8Result`` is a hard
  stop ``gate9_gate8_containment_not_established`` **before** any lock-side
  consumption attempt, and before proof or approval consumption). Provenance
  is never containment success (the B1 defect class);
* re-derives the upstream lineage exactly: the ``Gate7Result`` via
  ``runtime_dispatch_gate7.is_gate7_result`` **and**
  ``decision == "ALLOW"``; the ``Gate6Decision`` via
  ``runtime_dispatch_permission.is_gate6_decision`` **and**
  ``decision == "ALLOW"``; the ``Gate5Result`` via
  ``runtime_dispatch_gate5.is_gate5_result``. A caller-built,
  field-reconstructed, copied, ``deepcopy``-d, or serialized clone of any
  of the five trusted objects fails closed (RDGO-001 §8/§9/§10; the B1
  defect class);
* enforces a single consistent invocation: ``invocation_id`` and
  ``attempt_id`` equal across ``Gate5Result`` / ``Gate6Decision`` /
  ``Gate7Result`` / ``Gate8Result`` / ``identity``; ``request_id`` equal
  across ``Gate6Decision`` / ``Gate7Result`` / ``Gate8Result`` (RDGO-001
  §10a "Every gate from 2 through 11 … SHALL carry the same ``attempt_id``
  unchanged"). Cross-invocation consumption is refused;
* independently reconstructs the Gate-7 lineage digest and the full
  containment evidence: it re-runs the Gate-8 owner
  ``run_gate8_process_containment`` over the *same* trusted upstream objects
  + a freshly re-resolved descriptor / executable / repository-scoped cwd,
  and requires the freshly-recomputed ``containment_evidence_digest`` /
  ``effect_plan_digest`` / ``live_preflight_digest`` / ``gate7_result_digest``
  to equal the ones carried by the handed ``Gate8Result`` (V-13-5-1 — the
  ``.1R.13.5`` finding is closed here by read-back + recomputation; no
  stored digest is treated as self-authenticating);
* re-trusts + revalidates the referenced
  ``ValidatedAuthorityProjection`` at Gate 9's own point of use, **inside**
  the serialization boundary, immediately before compare-and-create
  (HPAC-REQ-099). ``revalidate_validated_authority_projection`` re-runs
  ``validate_approval``, so a principal revoked / credential revoked / proof
  expired / approval expired / consumption-state-changed after Gate 5/6/7/8
  fails closed here with **no** ``consumption.json`` written;
* re-confirms the HPAC lifecycle sequence-3 ``PROOF_VERIFIED_AND_BOUND``
  binding through a trusted, caller-supplied
  :class:`~hpac_lifecycle.HPACLifecycleStore` (read-only) — exact
  approval / invocation / principal identity, canonical event digest;
* binds the exact proof and approval of the *same* invocation/authority
  lineage: ``gate5_result.approval_id == projection.approval_id`` and
  ``gate5_result.proof_id == projection.proof_id``; a proof / approval
  from a different challenge / principal / invocation is refused
  (``gate9_proof_approval_pairing_mismatch``);
* re-reads the current runtime capability snapshot **inside** the
  serialization boundary through a trusted, caller-supplied
  ``capability_snapshot_resolver`` and fails closed if runtime execution is
  anything other than ``unavailable`` (RDGO-001 §10 last ¶; the production
  path is unreachable regardless — see below);
* captures a monotonic ``AuthorityGenerationSnapshot`` (``S1``) once the
  full battery has succeeded, from canonical durable state only — the
  trusted, caller-supplied ``authority_generation_resolver`` (current
  principal / credential / approval canonical record digests), the entire
  provenance-checked proof lifecycle chain, and the consumption-record
  absence — and re-reads it (``S2``) with **zero intervening effectful
  I/O** immediately before the create-only linearization; any change fails
  closed (V-15-1; see the serialization-semantics repair note below);
* performs one create-only, crash-consistent, read-back-verified atomic
  commit of the closed eight-item ``HPAC-AUTHORITY-CONSUMPTION/2.0`` record
  at ``<root>/proofs/v2/<proof_id>/consumption.json`` by delegating to the
  **unchanged** ``RuntimeInvocationAuthorityConsumptionStore.create``
  primitive (HPAC-REQ-098/099/100). Proof **and** approval (and
  presentation and challenge) are consumed **together** by this one write;
  there is no state in which only one of ``{proof, approval}`` is consumed
  (§11). The RIHAC repository approval store is **not** mutated
  (HPAC-REQ-102);
* returns exactly one ephemeral, identity-only, non-serializable,
  registry-provenanced :class:`Gate9Result` (``status`` ∈
  ``{"consumed", "already_consumed"}``), or ``(None, reasons)`` on any
  pre-commit fail-closed rejection — creating no ``Gate9Result`` and
  consuming nothing.

**One-shot semantics.** The first valid eligible consumption succeeds. Any
subsequent attempt — same proof + same approval, a copied / stale /
replayed ``Gate8Result``, a cross-invocation request, or a concurrent racer
— resolves to a deterministic ``already_consumed`` outcome
(``gate9_already_consumed``), never a second success and never a
retriable error. Concurrency: the per-``proof_id`` create-only primitive
(``write_atomic_create_only`` — ``O_EXCL`` temp sibling + atomic
link-if-absent) is itself the serialization boundary; exactly one racer
installs the final record, the loser gets ``HPACDuplicateError`` mapped to
``already_consumed``. No split-brain, no two canonical records, no partial
proof/approval state (§18).

**V-15-1 serialization-semantics repair (Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.15.2; `.1R.15.1` §14 Option B).** The
HPAC-REQ-099 revalidation battery is captured as a monotonic
``AuthorityGenerationSnapshot`` (``S1``) the instant it succeeds, then
re-read (``S2``) with **zero intervening effectful I/O** immediately before
the create-only linearization. Any token change — a principal / credential
revocation or disablement, an eligibility change, a canonical record
replacement, a lifecycle invalidation, or a consumption record appearing —
between ``S1`` and ``S2`` fails closed with **no** ``consumption.json``.
The per-``proof_id`` create-only primitive remains the **sole**
linearization point (no second global lock; `.1R.9` §18). This realizes
RDGO-001 §10 "revalidate … without a TOCTOU allowance" to the practical
limit. **Durable / re-readable embedding of the snapshot into the
consumption record's ``authority_binding`` for Gate 10's second line of
defense is DEFERRED to the `.1R.15.4` contract normalization**: HPAC-REQ-098
defines ``authority_binding`` as a closed 12-field set with no extensibility
clause, and ``registry_state_digest`` normatively denotes the
registry/configuration digest (HPAC-REQ-095/099), not the full
mutable-authority-generation vector — adding a field or broadening an
existing field's grammar in this phase would be normative schema drift.

**Crash semantics (HPAC-REQ-100/101; §17).** Crash *before* the atomic
commit: the final artifact is absent → ``resolve(proof_id)`` returns
``None`` → proof and approval are **unconsumed**, no Gate-10 effect
permitted; a retry MUST re-run the full in-boundary battery before another
``create``. Crash *after* the atomic commit: one complete valid record is
present → ``resolve(proof_id)`` returns it → **consumed**; a retry reports
``already_consumed`` and MUST NOT continue to any later gate. An ambiguous /
partial / corrupt record is
``RuntimeInvocationAuthorityConsumptionDurabilityUncertainError`` →
``gate9_consumption_state_durability_uncertain`` → fail closed, never a
replay. Canonical durable state is the authority across a restart — the
absence of a process-local ``Gate9Result`` never implies unconsumed.

**No positive production Gate-9 path today.** Real execution remains
unavailable; the real Gate-7 coordinator always returns
``Gate7Result(decision="DENY")`` and the real ``run_gate5`` never returns a
``Gate5Result`` on any obtainable path (permanent NON-REAL upstream), so
``run_gate9_atomic_authority_consumption`` is **structurally unreachable**
on the production path. The consumption branches are exercised only through
a clearly-labelled test-only substitution of the upstream provenance
predicates and a test-scoped temporary consumption store; no
``ValidatedAuthorityProjection``, approval, HPAC proof, runtime capability,
positive ``Gate7Result``, or positive ``Gate8Result`` is fabricated, and no
write is ever made to the production-resolved ``HPAC_PROTECTED_ROOT``. This
is not a development bypass (``.1R.9`` §21.4): it validates the store's and
coordinator's atomicity / crash / replay / concurrency behaviour against a
structurally correct payload, exactly as ``.1R.3`` did for the inert store,
and cannot produce production authority.

**Gate 9 ends after durable consumption.** No subprocess, adapter
invocation, provider / network call, external repository mutation,
credential access, or hardware access occurs here or is reachable from
here. Gate 10 (the first external effect) is a separate, unimplemented
module; it MUST NOT treat ``is_gate9_result(x) is True`` as sufficient — a
future consumer MUST additionally require ``x.status == "consumed"`` and
re-read the durable ``consumption.json`` + containment evidence. Local
canonical consumption-store writes are the expected Gate-9
authority-consumption effect and are categorically distinct from external
runtime effects. Runtime remains ``not_implemented / Observed / observe /
unavailable``; POL-005 unchanged; real execution UNAVAILABLE.

This module imports no ``subprocess``, ``socket``,
``os.system``/``popen``/``spawn``/``exec*``, ``pty``, provider SDK, HTTP
client, or FIDO2/WebAuthn/CTAP/smartcard/USB module (enforced by an AST
guard in the ``.1R.14`` suite). It calls no Gate-10
adapter/subprocess/provider primitive.

F7 boundary (carried verbatim, threat model NOT broadened): the
``_GATE9_RESULTS`` identity registry and this module's consumption of the
five upstream trusted objects run under the same-account autonomous-agent
assumption. They resist caller-supplied **data** forgery (reconstruction,
copy, serialized clone, duck-typed lookalike, a schema-valid record planted
outside the authoritative writer); they do **not** resist
arbitrary same-process Python code execution. No UID / username / process-ownership / stdio / Git
identity / PCAE session identity / producer identity is trusted; only the
verified HPAC provenance chain establishes human authentication, only
exact-object registry membership establishes gate-result provenance, and
only the store's create-only atomic primitive establishes consumed state. A
process-isolation / hardening chapter is a separate, unscheduled,
non-prerequisite topic.

V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1 / V-13-5-2 dispositions —
carried, none becomes blocking at actual consumption (see the ``.1R.14``
canonical document §"Contract-alignment debt"): Gate 9 derives authority
solely from the re-trusted ``gate5_result.projection`` object and the
trusted upstream gate objects, never the disputed "which gate creates
sequence 3" wording (V-2/V-3), never the raw 3-vs-7-field
``human_authority_binding`` shape (V-4); V-13-5-1 is **satisfied here** by
containment-evidence read-back + recomputation; V-13-5-2's transitive
attempt-identity is preserved (attempt identity is established at Gate 2 on
``RuntimeDispatchIdentity`` and carried unchanged through Gate 7 — Gate 9
confirms ``attempt_id`` equality across every link and never claims a
direct Gate-5 attempt binding).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pcae.core.runtime_authority import (
    PROMPT_HASH_PROFILE,
    compute_canonical_digest,
    is_trusted_validated_authority_projection,
    revalidate_validated_authority_projection,
)
from pcae.core.runtime_dispatch_permission import (
    RuntimeDispatchConstructionError,
    RuntimeDispatchIdentity,
    RuntimeDispatchRequestConstructionInput,
    _expected_subject_scope_binding_digest,
    _validate_construction_inputs,
)

__all__ = [
    "Gate9Result",
    "is_gate9_result",
    "run_gate9_atomic_authority_consumption",
    "GATE9_STATUS_CONSUMED",
    "GATE9_STATUS_ALREADY_CONSUMED",
    "GATE9_ADVISORY_REASONS",
]

#: The RIHAC-001 v2.0 authority contract version stamped into every
#: consumption record's ``authority_binding`` (HPAC-REQ-098; a zero-entropy
#: constant, not caller-supplied).
_AUTHORITY_CONTRACT_VERSION = "RIHAC-001/2.0"

#: The single RDGO-001 §10 durable dispatch state a Gate-9 record encodes:
#: the atomic presentation/challenge/proof/approval consumption point and
#: at-most-once guard (HPAC-REQ-098). There is no separate mutable
#: ``consumed`` field anywhere — "consumed" ≡ "one complete valid record
#: exists at the proof's protected path".
_DISPATCH_ATTEMPTED = "dispatch_attempted"

GATE9_STATUS_CONSUMED = "consumed"
GATE9_STATUS_ALREADY_CONSUMED = "already_consumed"

#: Advisory (non-fatal) reasons that ``revalidate`` may surface — mirrors
#: ``runtime_dispatch_gate5.GATE5_ADVISORY_REASONS``; surfaced so an audit
#: reader knows PB policy context drifted, never a licence to skip a check.
GATE9_ADVISORY_REASONS: frozenset[str] = frozenset(
    {"policy_drift_requires_fresh_pb_re_evaluation"}
)


# ═══════════════════════════════════════════════════════════════════════
# Gate9Result — ephemeral, identity-only, non-serializable, registry-
# provenanced (mirrors Gate5Result / the Gate-6 decision / Gate7Result /
# Gate8Result; RDGO-001 §10, §19)
# ═══════════════════════════════════════════════════════════════════════

_GATE9_RESULT_CONSTRUCTOR_SEAL = object()

#: The provenance boundary for a Gate-9 result: exact-object membership,
#: keyed by identity (``Gate9Result.__hash__`` / ``__eq__`` are ``id(self)``
#: / ``self is other``). The only insertion points are
#: :func:`run_gate9_atomic_authority_consumption`'s consumed / already-
#: consumed return paths; nothing outside this module adds to it.
#: ``shape != provenance``; ``provenance != successful consumption``.
_GATE9_RESULTS: "set[Gate9Result]" = set()


class Gate9Result:
    """The ephemeral, non-transferable receipt the Gate-9 coordinator emits
    after a completed atomic authority-consumption transition (``.1R.9``
    §19; RDGO-001 §10).

    Like ``Gate5Result`` / the Gate-6 decision / ``Gate7Result`` /
    ``Gate8Result`` this type is:

    * **not** caller-constructable — the ``_seal`` guard rejects direct
      construction, and :func:`is_gate9_result` checks membership in this
      module's process-local identity registry, which only
      :func:`run_gate9_atomic_authority_consumption` populates;
    * **not** serializable — ``__reduce__`` raises;
    * identity-only for ``==`` / ``hash`` — a copy, ``deepcopy``, or
      field-reconstructed lookalike is a different object and is never a
      registry member, whatever its fields say;
    * **not** subclassable — ``__init_subclass__`` raises;
    * **not** a reusable bearer token and **not** Gate-10 execution
      authority. ``status == "consumed"`` means only "one complete valid
      ``consumption.json`` was atomically created and read-back verified"
      (RDGO-001 §0 wall ``dispatch completion != accepted change``; §10 "a
      byte-identical record is 'already consumed', not a re-entry
      licence"). :func:`is_gate9_result` proves provenance only; a future
      Gate 10 MUST additionally require ``status == "consumed"`` **and**
      re-read the durable record + containment evidence, never trust this
      in-memory marker.
    """

    __slots__ = (
        "status",
        "proof_id",
        "approval_id",
        "record_digest",
        "dispatch_state",
        "invocation_id",
        "attempt_id",
        "consumed_at",
        "advisory_reasons",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Gate9Result must not be subclassed")

    def __init__(
        self,
        *,
        status: str,
        proof_id: str,
        approval_id: str,
        record_digest: str,
        dispatch_state: str,
        invocation_id: str,
        attempt_id: str,
        consumed_at: str,
        advisory_reasons: tuple[str, ...],
        _seal: object,
    ) -> None:
        if _seal is not _GATE9_RESULT_CONSTRUCTOR_SEAL:
            raise TypeError(
                "Gate9Result cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_gate9.run_gate9_atomic_authority_consumption"
            )
        if status not in (GATE9_STATUS_CONSUMED, GATE9_STATUS_ALREADY_CONSUMED):
            raise TypeError(f"Gate9Result.status invalid: {status!r}")
        self.status = status
        self.proof_id = proof_id
        self.approval_id = approval_id
        self.record_digest = record_digest
        self.dispatch_state = dispatch_state
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.consumed_at = consumed_at
        self.advisory_reasons = tuple(advisory_reasons)
        self._seal = _seal

    def __reduce__(self):
        raise TypeError(
            "Gate9Result is ephemeral and non-serializable; consumed state "
            "lives only in the durable canonical consumption.json, which "
            "every consumer must re-read (RDGO-001 §10; HPAC-REQ-100)"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<Gate9Result status={self.status!r} proof_id={self.proof_id!r} "
            f"identity={id(self):#x}>"
        )


def is_gate9_result(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past
    :func:`run_gate9_atomic_authority_consumption` call returned — never
    based on ``isinstance``, fields, equality, or any shape property. Fails
    closed for a forgery, a copy, a reconstruction, ``object.__new__``, or a
    stale handle.

    Provenance only: a ``True`` result does **not** mean the authority was
    successfully consumed by *this* call. A future Gate 10 MUST additionally
    check ``candidate.status == "consumed"`` and re-read the durable record.
    """
    return isinstance(candidate, Gate9Result) and candidate in _GATE9_RESULTS


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _bounded_string(value: object, maximum: int = 128) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip()


# ═══════════════════════════════════════════════════════════════════════
# V-15-1 repair — authority-generation snapshot (Option B, `.1R.15.1` §14)
#
# A monotonic snapshot of every mutable authority source, captured once
# (``S1``) *after* the full in-boundary revalidation battery has succeeded
# and re-read once (``S2``) immediately before the create-only
# linearization, with **zero intervening effectful I/O**. Any ``S2 != S1``
# fails closed with no ``consumption.json`` — this makes the validity check
# and the atomic consumption serialized with respect to each other
# (RDGO-001 §10 / HPAC-REQ-099 "no TOCTOU allowance") without inventing a
# second lock: the per-``proof_id`` create-only primitive remains the sole
# linearization point (`.1R.9` §18).
#
# Every token is a digest / tuple over *canonical durable state* and is
# reconstructible after a restart (`.1R.15.2` §40). None uses a wall-clock
# timestamp, mtime, a process-local nonce, or an incomplete selected-field
# digest (§7).
#
# Durable/re-readable embedding of the snapshot into the consumption
# record's ``authority_binding`` is **NOT** performed here: HPAC-REQ-098
# defines ``authority_binding`` as a closed 12-field set with no
# extensibility clause, and ``registry_state_digest`` normatively denotes
# the registry/configuration digest (HPAC-REQ-095/099), not the full
# mutable-authority-generation vector. Adding a field or broadening an
# existing field's grammar would be normative schema drift, forbidden in
# this phase. The durable Gate-10 second-line-of-defense representation is
# DEFERRED TO `.1R.15.4` contract normalization (`.1R.15.1` §17/§23).
# ═══════════════════════════════════════════════════════════════════════

#: Keys a trusted ``authority_generation_resolver`` MUST return, each a
#: non-empty canonical digest string over the current authoritative record
#: bytes of that mutable source. Whole-record digests, not selected-field
#: digests: any authority-relevant mutation (revocation, disablement,
#: eligibility change, record replacement, binding change) necessarily
#: changes the corresponding record's canonical bytes and therefore the
#: token (`.1R.15.2` §7–§10, §13).
_AUTHORITY_GENERATION_KEYS: frozenset[str] = frozenset(
    {"principal_generation", "credential_generation", "approval_generation"}
)


def _lifecycle_generation_token(lifecycle_store: object, proof_id: str) -> str:
    """Digest over the ordered ``(sequence, state, event_digest)`` triples of
    the *entire* canonical, provenance-checked proof lifecycle chain
    (`.1R.15.2` §11/§12).

    A new successor event, a terminal ``EXPIRED`` / ``REVOKED`` / ``REJECTED``
    append, a fork (``resolve_canonical_chain`` raises → fail closed), or any
    transition changes the tuple and therefore the token. This single
    canonical read covers both the lifecycle-head semantic (§11) and the
    proof-state semantic (§12); the proof-state projection adds no coverage
    beyond it (deduplication proven — the chain digest is a superset
    commitment over every event, including proof lifecycle status, expiry,
    revocation, and canonical identity).
    """
    chain = lifecycle_store.resolve_canonical_chain(proof_id)
    return compute_canonical_digest(
        [
            {
                "sequence": resolved.record.sequence,
                "state": resolved.record.state,
                "event_digest": resolved.record.event_digest,
            }
            for resolved in chain
        ]
    )


def _consumption_generation_token(consumption_store: object, proof_id: str) -> tuple[str, ...]:
    """Current canonical consumption-record state for ``proof_id``
    (`.1R.15.2` §14): ``("absent",)`` when genuinely absent,
    ``("present", <record_digest>)`` when one complete valid record exists.

    A ``RuntimeInvocationAuthorityConsumptionDurabilityUncertainError`` is
    **not** caught here — it propagates so the caller fails closed
    (``gate9_consumption_state_durability_uncertain``); an ambiguous /
    corrupt record is never interpreted as either absent or present.
    """
    existing = consumption_store.resolve(proof_id)
    if existing is None:
        return ("absent",)
    return ("present", existing.record_digest)


def _capture_authority_generation_snapshot(
    *,
    authority_generation_resolver: Callable[[], object],
    lifecycle_store: object,
    consumption_store: object,
    proof_id: str,
) -> tuple[dict, tuple[str, ...]]:
    """Build one immutable ``AuthorityGenerationSnapshot`` (`.1R.15.2` §15)
    from canonical current state only.

    Returns ``(snapshot, ())`` on success or ``({}, (reason,))`` when the
    trusted resolver returns a malformed shape. The consumption token may
    raise ``RuntimeInvocationAuthorityConsumptionDurabilityUncertainError``;
    that is intentionally not caught here.
    """
    resolved = authority_generation_resolver()
    if not isinstance(resolved, dict) or set(resolved) != _AUTHORITY_GENERATION_KEYS:
        return {}, ("gate9_authority_generation_snapshot_incomplete",)
    for key in _AUTHORITY_GENERATION_KEYS:
        if not _bounded_string(resolved[key], 256):
            return {}, ("gate9_authority_generation_snapshot_incomplete",)
    snapshot = {
        "principal_generation": resolved["principal_generation"],
        "credential_generation": resolved["credential_generation"],
        "approval_generation": resolved["approval_generation"],
        "lifecycle_generation": _lifecycle_generation_token(lifecycle_store, proof_id),
        "consumption_generation": _consumption_generation_token(consumption_store, proof_id),
    }
    return snapshot, ()


#: The exact order tokens are compared in — the first differing token is
#: named in the fail-closed reason id (`.1R.15.2` §32). ``consumption_generation``
#: is compared by the caller (a present record → deterministic
#: ``already_consumed``, not a drift rejection — §14/§31), so it is not in
#: this list.
_AUTHORITY_GENERATION_DRIFT_ORDER: tuple[str, ...] = (
    "principal_generation",
    "credential_generation",
    "approval_generation",
    "lifecycle_generation",
)


def _first_authority_generation_drift(s1: dict, s2: dict) -> Optional[str]:
    """Return the first token name whose value differs between ``S1`` and
    ``S2`` (excluding ``consumption_generation``), else ``None``."""
    for key in _AUTHORITY_GENERATION_DRIFT_ORDER:
        if s1.get(key) != s2.get(key):
            return key
    return None


def _runtime_execution_unavailable(snapshot: object) -> bool:
    """The caller-supplied capability snapshot must attest the runtime is
    still non-executing (RDGO-001 §10 last ¶; ``.1R.9`` §24). Anything else
    fails closed — Gate 9 never consumes authority into a runtime that could
    act on it."""
    if not isinstance(snapshot, dict):
        return False
    return (
        snapshot.get("current_runtime_state") == "Observed"
        and snapshot.get("current_maximum_plugin_capability") == "observe"
        and snapshot.get("execution_availability") == "unavailable"
    )


def _authority_binding_fields(
    *,
    gate5_result: object,
    projection: object,
    proof_id: str,
    genesis_binding: dict,
    registry_state_digest: str,
) -> dict:
    projection_digest = projection.evidence_digest()
    return {
        "approval_id": gate5_result.approval_id,
        "approval_digest": projection.record_digest,
        "authority_projection_id": f"vap-{projection_digest[:32]}",
        "authority_projection_digest": projection_digest,
        "authority_contract_version": _AUTHORITY_CONTRACT_VERSION,
        "proof_id": proof_id,
        "proof_digest": compute_canonical_digest(
            {"proof_id": proof_id, "principal_id": projection.principal_id}
        ),
        "proof_validation_digest": gate5_result.sequence3_event_digest,
        "registry_state_digest": registry_state_digest,
        "approval_subject_digest": genesis_binding.get("approval_subject_digest", ""),
        "trusted_presentation_ref": genesis_binding.get("trusted_presentation_ref", ""),
        "challenge_digest": genesis_binding.get("challenge_digest", ""),
    }


def _build_consumption_record(
    *,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    gate5_result: object,
    gate6_decision: object,
    gate7_result: object,
    fresh_gate8: object,
    projection: object,
    proof_id: str,
    executable_identity_digest: str,
    genesis_binding: dict,
    registry_state_digest: str,
    consumed_at: str,
):
    from pcae.core.runtime_invocation_authority_consumption import (
        new_inert_consumption_record,
    )

    adapter = inputs.adapter_descriptor_binding
    return new_inert_consumption_record(
        request_identity={
            "invocation_id": identity.invocation_id,
            "attempt_id": identity.attempt_id,
            "idempotency_key": identity.idempotency_key,
        },
        repository_task_binding={
            "repository_identity": inputs.repository_identity,
            "head_commit": inputs.base_commit,
            "task_id": inputs.task_id,
            "task_contract_digest": inputs.task_contract_digest,
            "phase_id": inputs.lifecycle_context.phase_id,
            "session_id": inputs.lifecycle_context.session_id,
        },
        target_binding={
            "runtime_target_id": inputs.runtime_target_id,
            "adapter_id": adapter.adapter_id,
            "descriptor_version": adapter.descriptor_version,
            "descriptor_digest": adapter.descriptor_digest,
            "target_config_digest": adapter.target_config_digest,
            "executable_identity_digest": executable_identity_digest,
        },
        prompt_binding={
            "prompt_hash": inputs.prompt_hash,
            "prompt_hash_profile": PROMPT_HASH_PROFILE,
        },
        authority_binding=_authority_binding_fields(
            gate5_result=gate5_result,
            projection=projection,
            proof_id=proof_id,
            genesis_binding=genesis_binding,
            registry_state_digest=registry_state_digest,
        ),
        pb_binding={
            "request_digest": fresh_gate8.gate7_result_digest,
            "decision_digest": gate7_result.pb_decision_digest,
            "decision": gate6_decision.decision,
            "policy_version": inputs.task_contract_digest[:16],
            "causing_policy_ids": list(gate6_decision.causing_policy_ids),
            "matched_no_go_ids": list(gate6_decision.matched_no_go_ids),
        },
        runtime_enforcement_binding={
            "decision_id": gate7_result.request_id,
            "decision_digest": fresh_gate8.gate7_result_digest,
            "verdict": gate7_result.decision,
            "expires_at": gate7_result.expires_at,
            "evaluated_input_digest": gate7_result.evaluated_input_digest,
        },
        dispatch_binding={
            "containment_evidence_ref": {
                "digest": fresh_gate8.containment_evidence_digest,
                "live_preflight_digest": fresh_gate8.live_preflight_digest,
            },
            "state": _DISPATCH_ATTEMPTED,
            "consumed_at": consumed_at,
        },
    )


# ═══════════════════════════════════════════════════════════════════════
# The Gate-9 coordinator
# ═══════════════════════════════════════════════════════════════════════


def run_gate9_atomic_authority_consumption(
    gate8_result: object,
    *,
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
) -> tuple[Optional["Gate9Result"], tuple[str, ...]]:
    """Run RDGO-001 v3.0 Gate 9 (atomic one-shot authority consumption) for
    one ``runtime_dispatch`` request.

    Returns ``(Gate9Result, advisory_reasons)`` on a completed transition —
    ``status == "consumed"`` for the (production-unreachable) first
    successful consumption, ``status == "already_consumed"`` for a
    deterministic replay / concurrency-loser / crash-after-commit retry —
    and ``(None, reasons)`` on any pre-commit fail-closed rejection,
    creating no ``Gate9Result`` and consuming nothing.

    Fail-closed reason ids (each a single-element tuple unless noted):

    * ``gate9_untrusted_gate8_result`` — missing / non-registry ``Gate8Result``;
    * ``gate9_gate8_containment_not_established`` — a trusted ``Gate8Result``
      whose ``containment_established`` is not ``True`` (hard stop **before**
      any consumption attempt);
    * ``gate9_untrusted_gate7_result`` / ``gate9_gate7_decision_not_allow``;
    * ``gate9_untrusted_gate6_decision`` / ``gate9_gate6_decision_not_allow``;
    * ``gate9_untrusted_gate5_result``;
    * ``gate9_invalid_identity`` / ``gate9_invalid_construction_input`` /
      ``gate9_invalid_authority_current_time`` / ``gate9_invalid_repo_root`` /
      ``gate9_invalid_effect_plan`` / ``gate9_invalid_descriptor_resolver`` /
      ``gate9_invalid_lifecycle_store`` / ``gate9_invalid_consumption_store`` /
      ``gate9_invalid_capability_snapshot_resolver`` — structural guards;
    * ``gate9_invocation_binding_mismatch`` — ``invocation_id`` / ``attempt_id``
      / ``request_id`` not equal across every link + ``identity``;
    * ``gate9_request_currentness_drift:<fact>`` — ``inputs`` fail the
      canonical construction re-check;
    * ``gate9_gate7_lineage_mismatch`` — the handed ``Gate8Result``'s
      ``gate7_result_digest`` disagrees with the recomputed Gate-7 lineage
      digest;
    * ``gate9_containment_recomputation_failed`` — the Gate-8 re-run did not
      return a positive containment result over freshly re-resolved inputs;
    * ``gate9_containment_evidence_recomputation_mismatch`` — a
      freshly-recomputed containment / effect-plan / live-preflight digest
      disagrees with the handed ``Gate8Result`` (V-13-5-1 read-back);
    * ``gate9_stale_validated_authority_projection`` — the referenced
      projection is not (or no longer) trusted / revalidating inside the
      boundary;
    * ``gate9_authority_subject_scope_mismatch`` — recomputed
      ``subject_scope_binding_digest`` disagrees with the projection;
    * ``gate9_sequence3_proof_verified_and_bound_absent`` /
      ``gate9_sequence3_not_bound`` / ``gate9_sequence3_cross_binding`` /
      ``gate9_sequence3_event_digest_unverified`` — sequence-3 confirmation;
    * ``gate9_proof_approval_pairing_mismatch`` — the proof and approval are
      not the exact pair for the same invocation/authority lineage;
    * ``gate9_runtime_execution_available_unexpected`` — the in-boundary
      capability snapshot no longer attests a non-executing runtime;
    * ``gate9_invalid_authority_generation_resolver`` — the trusted
      authority-generation resolver is not callable (structural guard);
    * ``gate9_authority_generation_snapshot_incomplete`` — the resolver
      returned a value that is not a mapping of exactly
      ``{principal_generation, credential_generation, approval_generation}``
      to non-empty canonical digest strings;
    * ``gate9_authority_generation_drift:<source>`` — V-15-1 repair: a
      monotonic authority-generation token (``principal_generation`` /
      ``credential_generation`` / ``approval_generation`` /
      ``lifecycle_generation``) changed between the post-battery snapshot
      ``S1`` and the pre-``create`` re-read ``S2``; fail closed, no
      ``consumption.json``, no Gate 10;
    * ``gate9_consumption_state_durability_uncertain`` — a partial / corrupt
      record was found; fail closed, never replay;
    * ``gate9_already_consumed`` — accompanies a ``Gate9Result`` with
      ``status == "already_consumed"`` (replay / concurrency loser /
      crash-after-commit retry);
    * ``gate9_atomic_commit_failed`` — the create-only primitive raised a
      non-duplicate error; nothing consumed;
    * ``gate9_read_back_verification_failed`` — the record was created but
      did not read back byte-identical; treated as durability-uncertain;
    * ``gate9_internal_error_fail_closed`` — any unexpected exception; no
      partial output, no ``Gate9Result``.
    """
    try:
        from pcae.core.hpac_lifecycle import STATE_PROOF_VERIFIED_AND_BOUND
        from pcae.core.runtime_dispatch_gate5 import Gate5Result, is_gate5_result
        from pcae.core.runtime_dispatch_gate7 import Gate7Result, is_gate7_result
        from pcae.core.runtime_dispatch_gate8 import (
            Gate8Result,
            _gate7_result_digest,
            is_gate8_result,
            run_gate8_process_containment,
        )
        from pcae.core.runtime_dispatch_permission import Gate6Decision, is_gate6_decision
        from pcae.core.runtime_invocation_authority_consumption import (
            RuntimeInvocationAuthorityConsumptionDurabilityUncertainError,
            RuntimeInvocationAuthorityConsumptionStore,
        )
        from pcae.core.hpac_foundation import HPACDuplicateError

        # 1. Gate-8 provenance — only the exact object a past
        #    run_gate8_process_containment call returned.
        if not is_gate8_result(gate8_result):
            return None, ("gate9_untrusted_gate8_result",)
        assert isinstance(gate8_result, Gate8Result)

        # 2. Provenance is NOT containment success (RDGO-001 §9/§10; the B1
        #    class). A trusted NEGATIVE Gate8Result is a hard stop BEFORE any
        #    lock-side consumption attempt, before proof or approval
        #    consumption.
        if gate8_result.containment_established is not True:
            return None, ("gate9_gate8_containment_not_established",)

        # 3. Upstream lineage provenance + exact decisions.
        if not is_gate7_result(gate7_result):
            return None, ("gate9_untrusted_gate7_result",)
        assert isinstance(gate7_result, Gate7Result)
        if gate7_result.decision != "ALLOW":
            return None, ("gate9_gate7_decision_not_allow",)

        if not is_gate6_decision(gate6_decision):
            return None, ("gate9_untrusted_gate6_decision",)
        assert isinstance(gate6_decision, Gate6Decision)
        if gate6_decision.decision != "ALLOW":
            return None, ("gate9_gate6_decision_not_allow",)

        if not is_gate5_result(gate5_result):
            return None, ("gate9_untrusted_gate5_result",)
        assert isinstance(gate5_result, Gate5Result)

        # 4. Structural input guards.
        if type(identity) is not RuntimeDispatchIdentity:
            return None, ("gate9_invalid_identity",)
        if type(inputs) is not RuntimeDispatchRequestConstructionInput:
            return None, ("gate9_invalid_construction_input",)
        if not _bounded_string(authority_current_time, 64):
            return None, ("gate9_invalid_authority_current_time",)
        if not isinstance(repo_root, Path):
            return None, ("gate9_invalid_repo_root",)
        if not callable(descriptor_resolver):
            return None, ("gate9_invalid_descriptor_resolver",)
        if type(lifecycle_store) is not _lifecycle_store_type():
            return None, ("gate9_invalid_lifecycle_store",)
        if type(consumption_store) is not RuntimeInvocationAuthorityConsumptionStore:
            return None, ("gate9_invalid_consumption_store",)
        if not callable(capability_snapshot_resolver):
            return None, ("gate9_invalid_capability_snapshot_resolver",)
        if not callable(authority_generation_resolver):
            return None, ("gate9_invalid_authority_generation_resolver",)

        # 5. Single consistent invocation across every link (RDGO-001 §10a).
        if (
            gate5_result.invocation_id != identity.invocation_id
            or gate6_decision.invocation_id != identity.invocation_id
            or gate7_result.invocation_id != identity.invocation_id
            or gate8_result.invocation_id != identity.invocation_id
            or gate6_decision.attempt_id != identity.attempt_id
            or gate7_result.attempt_id != identity.attempt_id
            or gate8_result.attempt_id != identity.attempt_id
            or gate7_result.request_id != gate6_decision.request_id
            or gate8_result.request_id != gate6_decision.request_id
        ):
            return None, ("gate9_invocation_binding_mismatch",)

        # 6. Canonical construction re-check.
        try:
            _validate_construction_inputs(inputs)
        except RuntimeDispatchConstructionError as exc:
            return None, (f"gate9_request_currentness_drift:{exc}",)

        # 7. Gate-7 lineage digest cross-check — the handed Gate8Result must
        #    have been produced over exactly this Gate7Result.
        expected_gate7_digest = _gate7_result_digest(gate7_result)
        if gate8_result.gate7_result_digest != expected_gate7_digest:
            return None, ("gate9_gate7_lineage_mismatch",)

        # 7a. Early authority pre-check (cheap; re-done inside the boundary at
        #     step 9). Reject a projection that is not trusted / not
        #     revalidating, or whose subject/scope binding no longer matches
        #     this request, BEFORE the (more expensive) Gate-8 re-run. This is
        #     an additional early stop, not a substitute for the in-boundary
        #     battery.
        projection = gate5_result.projection
        if not is_trusted_validated_authority_projection(projection):
            return None, ("gate9_stale_validated_authority_projection",)
        expected_binding = _expected_subject_scope_binding_digest(
            identity=identity, inputs=inputs
        )
        if projection.subject_scope_binding_digest != expected_binding:
            return None, ("gate9_authority_subject_scope_mismatch",)

        # 8. Independently reconstruct the full containment evidence: re-run
        #    the Gate-8 owner over the SAME trusted upstream objects + a
        #    freshly re-resolved descriptor / executable / repository-scoped
        #    cwd, and require every recomputed digest to equal the handed
        #    Gate8Result's (V-13-5-1 read-back + recomputation; §11/§12/§13).
        if type(effect_plan) is not _gate8_effect_plan_type():
            return None, ("gate9_invalid_effect_plan",)
        fresh_gate8, fresh_reasons = run_gate8_process_containment(
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
            return None, ("gate9_containment_recomputation_failed",)
        if (
            fresh_gate8.containment_evidence_digest
            != gate8_result.containment_evidence_digest
            or fresh_gate8.effect_plan_digest != gate8_result.effect_plan_digest
            or fresh_gate8.live_preflight_digest != gate8_result.live_preflight_digest
            or fresh_gate8.gate7_result_digest != gate8_result.gate7_result_digest
        ):
            return None, ("gate9_containment_evidence_recomputation_mismatch",)

        # ── SERIALIZATION BOUNDARY ──────────────────────────────────────
        # The per-proof_id create-only primitive (write_atomic_create_only:
        # O_EXCL temp sibling + atomic link-if-absent) IS the serialization
        # boundary and the sole linearization point (`.1R.9` §18 "do not
        # invent a new lock"). Every check from here to the atomic create is
        # the HPAC-REQ-099 in-boundary revalidation battery, run immediately
        # before compare-and-create.
        #
        # V-15-1 repair (`.1R.15.2`, `.1R.15.1` §14 Option B): the battery
        # (steps 9–14) is followed by an authority-generation snapshot S1
        # (step 14a); S1 is re-read as S2 (step 15a) with ZERO intervening
        # effectful I/O immediately before ``consumption_store.create``, and
        # any S2 != S1 fails closed. This makes the validity check and the
        # atomic consumption serialized with respect to each other —
        # RDGO-001 §10 "no TOCTOU allowance" — without a second lock. The
        # durable/re-readable embedding of the snapshot into the consumption
        # record is DEFERRED to `.1R.15.4` (HPAC-REQ-098 ``authority_binding``
        # is a closed field set with no extensibility clause).

        # 9. Re-trust + revalidate the projection at Gate 9's own point of
        #    use, INSIDE the boundary. revalidate re-runs validate_approval →
        #    principal / credential / proof / approval currentness, expiry,
        #    revocation, prior-consumption state (RDGO-001 §10; HPAC-REQ-099;
        #    §16-§19). A revocation / expiry that happened between step 7a and
        #    here fails closed with no consumption.json.
        if not is_trusted_validated_authority_projection(projection):
            return None, ("gate9_stale_validated_authority_projection",)
        if not revalidate_validated_authority_projection(
            projection, current_time=authority_current_time
        ):
            return None, ("gate9_stale_validated_authority_projection",)
        if projection.subject_scope_binding_digest != expected_binding:
            return None, ("gate9_authority_subject_scope_mismatch",)

        # 11. Confirm the HPAC lifecycle sequence-3 PROOF_VERIFIED_AND_BOUND
        #     binding through the trusted read-only lifecycle store.
        proof_id = gate5_result.proof_id
        event = lifecycle_store.resolve_gate5_binding_event(proof_id)
        if event is None:
            return None, ("gate9_sequence3_proof_verified_and_bound_absent",)
        record = event.record
        if record.state != STATE_PROOF_VERIFIED_AND_BOUND:
            return None, ("gate9_sequence3_not_bound",)
        genesis_binding = record.binding
        if (
            genesis_binding.get("approval_id") != gate5_result.approval_id
            or genesis_binding.get("invocation_id") != identity.invocation_id
            or genesis_binding.get("principal_id") != projection.principal_id
        ):
            return None, ("gate9_sequence3_cross_binding",)
        if record.event_digest != event.record_digest:
            return None, ("gate9_sequence3_event_digest_unverified",)
        if gate5_result.sequence3_event_digest != record.event_digest:
            return None, ("gate9_sequence3_event_digest_unverified",)

        # 12. Bind the EXACT proof + approval of the same authority lineage
        #     (RDGO-001 §10; §20). proof A + approval B, or a proof/approval
        #     from another invocation, is refused.
        if (
            gate5_result.approval_id != projection.approval_id
            or gate5_result.proof_id != projection.proof_id
            or gate5_result.invocation_id != identity.invocation_id
        ):
            return None, ("gate9_proof_approval_pairing_mismatch",)

        # 13. Re-read the current runtime capability snapshot inside the
        #     boundary — fail closed if execution is anything but
        #     unavailable (RDGO-001 §10 last ¶; §21.4 / §24).
        if not _runtime_execution_unavailable(capability_snapshot_resolver()):
            return None, ("gate9_runtime_execution_available_unexpected",)

        # 14. Absence-of-consumption-record check, immediately before create.
        try:
            existing = consumption_store.resolve(proof_id)
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate9_consumption_state_durability_uncertain",)
        advisory = tuple(
            r for r in gate5_result.advisory_reasons if r in GATE9_ADVISORY_REASONS
        )
        if existing is not None:
            # Crash-after-commit retry / prior consumption: already consumed,
            # deterministic, never a second success, never continue to Gate 10.
            return _already_consumed_result(
                proof_id=proof_id,
                approval_id=gate5_result.approval_id,
                record_digest=existing.record_digest,
                invocation_id=identity.invocation_id,
                attempt_id=identity.attempt_id,
                consumed_at=existing.dispatch_binding.get("consumed_at", authority_current_time),
                advisory_reasons=advisory,
            )

        # 14a. V-15-1 repair — capture the authority-generation snapshot S1
        #      (`.1R.15.2` §16). The full in-boundary revalidation battery
        #      (steps 9–14) has now succeeded; S1 is a monotonic snapshot of
        #      every mutable authority source (principal / credential /
        #      approval canonical record digests via the trusted resolver;
        #      the full proof lifecycle chain; consumption-record absence).
        #      It is captured ONLY after the battery, never before
        #      current-state validation.
        try:
            s1, s1_reasons = _capture_authority_generation_snapshot(
                authority_generation_resolver=authority_generation_resolver,
                lifecycle_store=lifecycle_store,
                consumption_store=consumption_store,
                proof_id=proof_id,
            )
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate9_consumption_state_durability_uncertain",)
        if s1_reasons:
            return None, s1_reasons

        # 15. Build the closed eight-item record from the five trusted
        #     objects + identity + inputs + freshly-recomputed containment
        #     evidence.
        resolved = descriptor_resolver(inputs)
        executable_identity_digest = compute_canonical_digest(
            {
                "sha256": getattr(resolved, "sha256", ""),
                "path": getattr(resolved, "path", ""),
                "version": getattr(resolved, "version", ""),
            }
        )
        registry_state_digest = compute_canonical_digest(
            {
                "projection_digest": projection.evidence_digest(),
                "sequence3_event_digest": record.event_digest,
                "gate8_containment_evidence_digest": gate8_result.containment_evidence_digest,
            }
        )
        consumed_at = authority_current_time
        consumption_record = _build_consumption_record(
            identity=identity,
            inputs=inputs,
            gate5_result=gate5_result,
            gate6_decision=gate6_decision,
            gate7_result=gate7_result,
            fresh_gate8=fresh_gate8,
            projection=projection,
            proof_id=proof_id,
            executable_identity_digest=executable_identity_digest,
            genesis_binding=genesis_binding,
            registry_state_digest=registry_state_digest,
            consumed_at=consumed_at,
        )

        # 15a. V-15-1 repair — re-read the authority-generation snapshot S2
        #      IMMEDIATELY before the create-only linearization, with ZERO
        #      intervening effectful I/O (`.1R.15.2` §18–§20). Record
        #      preparation (step 15) is complete and performed no write; the
        #      only operations between this comparison and
        #      ``consumption_store.create`` are the S2 == S1 check itself and
        #      the create call.
        #
        #      * consumption_generation now "present" → another racer /
        #        operator installed a valid canonical record after S1;
        #        deterministic ``already_consumed`` (§14/§31), never a second
        #        create, never a drift rejection.
        #      * consumption_generation durability-uncertain → fail closed.
        #      * any principal / credential / approval / lifecycle token
        #        changed → a revocation, disablement, eligibility change,
        #        record replacement, or lifecycle invalidation landed in the
        #        S1→S2 window; FAIL CLOSED, NO CONSUMPTION, NO GATE 10.
        try:
            s2, s2_reasons = _capture_authority_generation_snapshot(
                authority_generation_resolver=authority_generation_resolver,
                lifecycle_store=lifecycle_store,
                consumption_store=consumption_store,
                proof_id=proof_id,
            )
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate9_consumption_state_durability_uncertain",)
        if s2_reasons:
            return None, s2_reasons
        if s2["consumption_generation"] != ("absent",):
            _kind, s2_record_digest = s2["consumption_generation"]
            return _already_consumed_result(
                proof_id=proof_id,
                approval_id=gate5_result.approval_id,
                record_digest=s2_record_digest,
                invocation_id=identity.invocation_id,
                attempt_id=identity.attempt_id,
                consumed_at=consumed_at,
                advisory_reasons=advisory,
            )
        drift = _first_authority_generation_drift(s1, s2)
        if drift is not None:
            return None, (f"gate9_authority_generation_drift:{drift}",)

        # 16. The one atomic, create-only, crash-consistent commit
        #     (HPAC-REQ-100). Proof + approval + presentation + challenge are
        #     consumed together by this single write.
        try:
            consumption_store.create(proof_id, consumption_record)
        except HPACDuplicateError:
            # Concurrency loser / replay: exactly one racer won. Deterministic
            # already-consumed, never a retriable error, never a second write.
            try:
                winner = consumption_store.resolve(proof_id)
            except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
                return None, ("gate9_consumption_state_durability_uncertain",)
            winner_digest = (
                winner.record_digest if winner is not None else consumption_record.record_digest
            )
            return _already_consumed_result(
                proof_id=proof_id,
                approval_id=gate5_result.approval_id,
                record_digest=winner_digest,
                invocation_id=identity.invocation_id,
                attempt_id=identity.attempt_id,
                consumed_at=consumed_at,
                advisory_reasons=advisory,
            )
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate9_consumption_state_durability_uncertain",)
        except Exception:
            # A non-duplicate create error (e.g. a transient contention error
            # racing another creator for the same fresh proof directory). If
            # a complete valid record is now durably present, another racer
            # won → deterministic already-consumed; otherwise nothing was
            # consumed and we fail closed.
            try:
                raced = consumption_store.resolve(proof_id)
            except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
                return None, ("gate9_consumption_state_durability_uncertain",)
            if raced is not None:
                return _already_consumed_result(
                    proof_id=proof_id,
                    approval_id=gate5_result.approval_id,
                    record_digest=raced.record_digest,
                    invocation_id=identity.invocation_id,
                    attempt_id=identity.attempt_id,
                    consumed_at=raced.dispatch_binding.get("consumed_at", consumed_at),
                    advisory_reasons=advisory,
                )
            return None, ("gate9_atomic_commit_failed",)

        # 17. Read-back verification (RDGO-001 §10 "read-back-verified").
        try:
            written = consumption_store.resolve(proof_id)
        except RuntimeInvocationAuthorityConsumptionDurabilityUncertainError:
            return None, ("gate9_read_back_verification_failed",)
        if written is None or written.record_digest != consumption_record.record_digest:
            return None, ("gate9_read_back_verification_failed",)

        result = Gate9Result(
            status=GATE9_STATUS_CONSUMED,
            proof_id=proof_id,
            approval_id=gate5_result.approval_id,
            record_digest=consumption_record.record_digest,
            dispatch_state=_DISPATCH_ATTEMPTED,
            invocation_id=identity.invocation_id,
            attempt_id=identity.attempt_id,
            consumed_at=consumed_at,
            advisory_reasons=advisory,
            _seal=_GATE9_RESULT_CONSTRUCTOR_SEAL,
        )
        _GATE9_RESULTS.add(result)
        return result, advisory
    except Exception:
        # Fail closed on any unexpected exception — no partial output, no
        # Gate9Result (RDGO-001 §0, §10; HPAC-REQ-100).
        return None, ("gate9_internal_error_fail_closed",)


def _already_consumed_result(
    *,
    proof_id: str,
    approval_id: str,
    record_digest: str,
    invocation_id: str,
    attempt_id: str,
    consumed_at: str,
    advisory_reasons: tuple[str, ...],
) -> tuple["Gate9Result", tuple[str, ...]]:
    result = Gate9Result(
        status=GATE9_STATUS_ALREADY_CONSUMED,
        proof_id=proof_id,
        approval_id=approval_id,
        record_digest=record_digest,
        dispatch_state=_DISPATCH_ATTEMPTED,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        consumed_at=consumed_at,
        advisory_reasons=advisory_reasons,
        _seal=_GATE9_RESULT_CONSTRUCTOR_SEAL,
    )
    _GATE9_RESULTS.add(result)
    return result, ("gate9_already_consumed",) + tuple(advisory_reasons)


def _lifecycle_store_type():
    from pcae.core.hpac_lifecycle import HPACLifecycleStore

    return HPACLifecycleStore


def _gate8_effect_plan_type():
    from pcae.core.runtime_dispatch_gate8 import Gate8EffectPlan

    return Gate8EffectPlan
