"""
Gate-8 Process Containment (Shell Gate) coordinator — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.13.4.

Implements RDGO-001 v3.0 §9 Gate 8 (process containment and live preflight —
the Shell Gate boundary) as the single, **non-consuming** process-containment
establishment boundary for one bound ``runtime_dispatch`` request, exactly as
frozen by the ``.1R.13.1`` planning document (§5, §11, §12, §16, §25). It
mirrors the shape of ``runtime_dispatch_gate5.run_gate5`` and the Gate-6 / Gate-7 coordinators:

``run_gate8_process_containment`` is the frozen **sole** production owner of
the RDGO-001 §9 Gate-8 process-containment / Shell-Gate consumption boundary
for ``runtime_dispatch``. It:

* consumes a registry-provenanced :class:`~runtime_dispatch_gate7.Gate7Result`
  **only** via ``runtime_dispatch_gate7.is_gate7_result`` — the exact object
  a prior successful Gate-7 runtime-enforcement evaluation returned. A
  caller-built ``Gate7Result``, a field-equivalent reconstruction, a copy, a
  ``deepcopy``, a serialized clone, or a bare ``decision="ALLOW"`` object all
  fail closed (RDGO-001 §9; the B1 defect class). ``is_gate7_result`` proves
  *provenance only* — Gate 8 **additionally** requires
  ``gate7_result.decision == "ALLOW"`` by exact string equality. A trusted
  **negative** ``Gate7Result(decision="DENY")`` is rejected
  (``gate8_gate7_decision_not_allow``) **before** any Shell Gate evaluation;
* consumes a registry-provenanced :class:`~runtime_dispatch_gate5.Gate5Result`
  **only** via ``runtime_dispatch_gate5.is_gate5_result`` and re-trusts +
  revalidates its ``ValidatedAuthorityProjection`` at Gate 8's own point of
  use (possession is never sufficient — HPAC-REQ-097 / §40.2). It re-checks
  the §9 "recheck … current policy/RE decision" by requiring a live trusted
  ``Gate7Result(decision="ALLOW")`` and a still-revalidating projection;
* preserves the exact invocation lineage (``invocation_id`` and
  ``attempt_id`` equal across ``Gate5Result`` / ``Gate7Result`` /
  ``identity``) and recomputes the ``subject_scope_binding_digest`` from
  ``identity`` + ``inputs`` via the shared
  ``runtime_dispatch_permission._expected_subject_scope_binding_digest``
  (mismatch → ``gate8_authority_subject_scope_mismatch``);
* re-resolves the exact descriptor/config and the exact executable through a
  **trusted, coordinator-supplied** ``descriptor_resolver`` (never a caller
  shell string); verifies executable identity/hash against the resolved pin
  (RDGO-001 §9); refuses any caller-supplied shell string or shell
  metacharacter in the argument vector (``gate8_caller_shell_string_rejected``);
* consumes the **mature 88P** :func:`pcae.core.shell_gate.build_shell_gate`
  classifier read-only for a defensive command-category cross-check of the
  resolved executable + argv (it must classify as an allowlisted
  governed / read-only / test category, never as a mutation / network /
  secret / destructive category). Shell Gate remains the single owner of
  command classification; this coordinator re-implements none of it. Shell
  Gate never executes classified command text — this coordinator refuses any
  argv whose program would drive Shell Gate's ``pcae doctor test-run`` lock
  probe, so ``build_shell_gate`` is called only on a proven-inert input
  (RDGO-001 §9 "A live preflight check is an observation of readiness, never
  authority or permission");
* establishes and attests one exact bounded launch environment — executable
  identity, argument vector, cwd (canonical, repository-scoped), environment
  allowlist, child-process prohibition/limit, resource/time limit,
  supervision, ``network_denied=True``, ``credentials_required=False`` — and
  binds that containment evidence to the invocation, returning exactly one
  ephemeral, identity-only, non-serializable, registry-provenanced
  :class:`Gate8Result` (``containment_established`` ∈ ``{True, False}``), or
  ``(None, reasons)`` on any pre-establishment fail-closed rejection —
  creating no ``Gate8Result`` and consuming nothing.

**No positive production Gate-8 path today.** Under the current runtime
posture Gate 7 always returns ``Gate7Result(decision="DENY")`` (RDGO-001
§8; ``.1R.13.2`` / ``.1R.13.3``), and the real ``run_gate5`` never returns a
``Gate5Result`` on any obtainable path (permanent NON-REAL upstream), so
``run_gate8_process_containment`` is **structurally unreachable** on the
production path: every real call fails closed at the
``gate8_untrusted_gate7_result`` / ``gate8_gate7_decision_not_allow`` hard
stop. The containment-establishment branches exist for structural
completeness and are exercised only through a clearly-labelled test-only
provenance substitution; no runtime capability, execution availability,
supported backend, or positive ``Gate7Result`` is fabricated.

**Gate 8 consumes nothing.** No approval, HPAC proof, presentation,
challenge, nonce, ``Gate5Result``, the Gate-6 decision, ``Gate7Result``,
authority record, or lifecycle record is created, deleted, or mutated. It
consumes no Gate-6 decision object at all (RDGO-001 §9; plan §26). No
durable authority-consumption record is written and no Gate-9
atomic-consumption primitive is called. Establishing containment is not a
one-shot resource here (that belongs to Gate 9's durable pre-dispatch
record). Gate 8 is idempotently repeatable; a prior
``Gate8Result`` is never a cache and is invalid across any relevant input,
descriptor, executable, repository, policy, or RE-decision change (RDGO-001
§9, §15).

**No effect.** This module imports no ``subprocess``, ``socket``,
``os.system``/``popen``/``spawn``/``exec*``, ``pty``, provider SDK, or HTTP
client, and calls no Gate-9 atomic-consumption or Gate-10
adapter/subprocess/provider/network/credential/hardware primitive (enforced
by an AST guard in the ``.1R.13.4`` suite). Executable-identity verification
is a file stat + hash read, never an execution. Gate 10 remains the first
external effect. Runtime remains ``not_implemented / Observed / observe /
unavailable``; POL-005 unchanged; real execution UNAVAILABLE.

F7 boundary (carried verbatim, threat model NOT broadened): the
``_GATE8_RESULTS`` identity registry and this module's consumption of
``Gate7Result`` / ``Gate5Result`` run under the same-account
autonomous-agent assumption. They resist caller-supplied **data** forgery
(reconstruction, copy, serialized clone, duck-typed lookalike), **not**
arbitrary same-process Python code execution. No UID / username /
process-ownership / stdio / Git identity / PCAE session identity / producer
identity is trusted; only the verified HPAC provenance chain establishes
human authentication and only exact-object registry membership establishes
gate-result provenance. A process-isolation / hardening chapter is a
separate, unscheduled, non-prerequisite topic.

Gate 8 → Gate 9 handoff (``.1R.13.1`` §16 — Gate 9 NOT implemented here):
``run_gate8_process_containment`` terminates after its own containment
decision. The ``Gate8Result`` carries exactly the fields the future Gate-9
coordinator will need to re-establish Gate-8 provenance, the exact
invocation, the exact process/effect plan, the Gate-7 lineage/currentness,
and the containment decision — but this phase creates no consumer, no
serialization, and no persisted handoff.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pcae.core.runtime_authority import (
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
    "Gate8Result",
    "is_gate8_result",
    "run_gate8_process_containment",
    "Gate8EffectPlan",
    "ResolvedExecutable",
    "GATE8_ALLOWED_SHELL_GATE_CATEGORIES",
    "GATE8_ALLOWED_SHELL_GATE_DECISIONS",
    "GATE8_DENIED_SHELL_GATE_CATEGORIES",
]

# ═══════════════════════════════════════════════════════════════════════
# Shell Gate category / decision allowlists (RDGO-001 §9 defensive
# cross-check; consumed from the 88P classifier vocabulary, not redefined)
# ═══════════════════════════════════════════════════════════════════════

#: The resolved executable + argv must classify as one of these read-only /
#: governed / test categories under the mature ``shell_gate`` 88P classifier.
GATE8_ALLOWED_SHELL_GATE_CATEGORIES: frozenset[str] = frozenset(
    {"read_only_inspection", "pcae_governed_lifecycle"}
)

#: …and the classifier's decision must be one of these.
GATE8_ALLOWED_SHELL_GATE_DECISIONS: frozenset[str] = frozenset(
    {"allow_read_only", "allow_governed"}
)

#: Any of these categories is an unconditional Gate-8 reject
#: (``gate8_shell_gate_category_denied``), fail-closed.
GATE8_DENIED_SHELL_GATE_CATEGORIES: frozenset[str] = frozenset(
    {
        "source_mutation",
        "test_mutation",
        "docs_mutation",
        "filesystem_write",
        "destructive_filesystem",
        "policy_forbidden_file_mutation",
        "backend_invocation",
        "prompt_send",
        "output_capture",
        "intake_adoption",
        "package_install",
        "network_access",
        "secret_access",
        "environment_mutation",
        "raw_git_commit",
        "raw_git_push",
        "force_push",
        "git_history_rewrite",
        "test_execution",
        "unknown",
    }
)

#: Shell metacharacters whose presence in the resolved executable path or any
#: argv element means a caller shell string leaked in — RDGO-001 §9 / §11
#: "SHALL use an argument vector, not unrestricted shell evaluation".
_SHELL_METACHARACTERS: frozenset[str] = frozenset(
    ";&|<>$`\n\r\t*?()[]{}!\\\"'"
)

#: Program basenames that would drive ``shell_gate``'s ``pcae doctor
#: test-run`` lock probe (its only ``subprocess.run`` call, for expensive
#: pytest classification). A ``runtime_dispatch`` adapter effect plan is
#: never one of these; Gate 8 refuses them **before** calling
#: ``build_shell_gate`` so the classifier is invoked only on a proven-inert
#: input.
_SHELL_GATE_PREFLIGHT_TRIGGER_PROGRAMS: frozenset[str] = frozenset(
    {"pytest", "py.test", "tox", "nox", "unittest"}
)

#: Accepted child-process containment policies (RDGO-001 §9 "child-process
#: prohibition/limit").
_GATE8_CHILD_PROCESS_POLICIES: frozenset[str] = frozenset(
    {"prohibited", "single_child_limit"}
)


# ═══════════════════════════════════════════════════════════════════════
# Coordinator inputs — plain frozen value objects (NOT trust objects).
# ``descriptor_resolver`` is trusted-caller-supplied, exactly like
# ``run_gate5``'s ``lifecycle_store``.
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ResolvedExecutable:
    """The exact executable resolved from the pinned adapter
    descriptor/config by a trusted, coordinator-supplied
    ``descriptor_resolver`` (RDGO-001 §9 "resolve the exact executable
    without accepting a caller shell string"). ``path`` is an absolute
    filesystem path; ``sha256`` is the descriptor-pinned executable hash;
    ``descriptor_digest`` / ``target_config_digest`` echo the resolved
    descriptor for drift detection against ``inputs``; ``runtime_target_id``
    echoes the resolved runtime target."""

    path: str
    sha256: str
    version: str
    descriptor_digest: str
    target_config_digest: str
    runtime_target_id: str
    installed: bool


@dataclass(frozen=True)
class Gate8EffectPlan:
    """The exact process / effect description Gate 8 validates and contains
    (RDGO-001 §9). It is an **argument vector**, never a shell string:
    ``executable_path`` must equal the ``ResolvedExecutable.path`` the
    trusted ``descriptor_resolver`` returned, and no element may contain a
    shell metacharacter. ``env_allowlist`` is the exact set of environment
    variable **names** permitted into the bounded process — never the
    ambient process environment."""

    executable_path: str
    argv: tuple[str, ...]
    cwd: str
    env_allowlist: tuple[str, ...]
    child_process_policy: str
    resource_limit_ref: str
    time_limit_ref: str
    supervision_ref: str
    network_denied: bool
    credentials_required: bool


# ═══════════════════════════════════════════════════════════════════════
# Gate8Result — ephemeral, identity-only, non-serializable, registry-
# provenanced (mirrors Gate5Result / the Gate-6 decision / Gate7Result;
# RDGO-001 §9, §10 item 8)
# ═══════════════════════════════════════════════════════════════════════

_GATE8_RESULT_CONSTRUCTOR_SEAL = object()

#: The provenance boundary for a Gate-8 result: exact-object membership,
#: keyed by identity (``Gate8Result.__hash__`` / ``__eq__`` are ``id(self)``
#: / ``self is other``). The only insertion point is
#: :func:`run_gate8_process_containment`'s completed-establishment return
#: path; nothing outside this module adds to it. ``shape != provenance``.
_GATE8_RESULTS: "set[Gate8Result]" = set()


class Gate8Result:
    """The ephemeral, non-transferable evidence Gate 8 emits after it
    attempts to establish process containment for one bound
    ``runtime_dispatch`` request (``.1R.13.1`` §12.6; RDGO-001 §9 / §10
    item 8).

    Like ``Gate5Result`` / the Gate-6 decision / ``Gate7Result`` this type is:

    * **not** caller-constructable — the ``_seal`` guard rejects direct
      construction, and :func:`is_gate8_result` checks membership in this
      module's process-local identity registry, which only
      :func:`run_gate8_process_containment` populates;
    * **not** serializable — ``__reduce__`` raises;
    * identity-only for ``==`` / ``hash`` — a copy, ``deepcopy``, or
      field-reconstructed lookalike is a different object and is never a
      registry member, whatever its fields say;
    * **not** subclassable — ``__init_subclass__`` raises;
    * **not** an execution token — ``containment_established=True`` means
      only "a bounded launch environment is established and attested"
      (RDGO-001 §0 wall ``process permission != dispatch completion``); it is
      not the process running, not durable authority consumption (Gate 9),
      and not dispatch (Gate 10). :func:`is_gate8_result` proves provenance
      only; a future Gate 9 MUST additionally require
      ``containment_established is True``. A ``Gate8Result`` with
      ``containment_established=False`` is a structured audit record carrying
      ``causing_reason_ids`` — a downstream gate MUST NOT treat it as
      partial success.
    """

    __slots__ = (
        "containment_established",
        "causing_reason_ids",
        "invocation_id",
        "attempt_id",
        "request_id",
        "gate7_result_digest",
        "effect_plan_digest",
        "containment_evidence_digest",
        "live_preflight_digest",
        "shell_gate_decision",
        "shell_gate_category",
        "expires_at",
        "evaluated_at",
        "_seal",
    )

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Gate8Result must not be subclassed")

    def __init__(
        self,
        *,
        containment_established: bool,
        causing_reason_ids: tuple[str, ...],
        invocation_id: str,
        attempt_id: str,
        request_id: str,
        gate7_result_digest: str,
        effect_plan_digest: str,
        containment_evidence_digest: str,
        live_preflight_digest: str,
        shell_gate_decision: str,
        shell_gate_category: str,
        expires_at: str,
        evaluated_at: str,
        _seal: object,
    ) -> None:
        if _seal is not _GATE8_RESULT_CONSTRUCTOR_SEAL:
            raise TypeError(
                "Gate8Result cannot be caller-constructed; it is producible "
                "only by runtime_dispatch_gate8.run_gate8_process_containment"
            )
        if not isinstance(containment_established, bool):
            raise TypeError("Gate8Result.containment_established must be a bool")
        self.containment_established = containment_established
        self.causing_reason_ids = tuple(causing_reason_ids)
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.request_id = request_id
        self.gate7_result_digest = gate7_result_digest
        self.effect_plan_digest = effect_plan_digest
        self.containment_evidence_digest = containment_evidence_digest
        self.live_preflight_digest = live_preflight_digest
        self.shell_gate_decision = shell_gate_decision
        self.shell_gate_category = shell_gate_category
        self.expires_at = expires_at
        self.evaluated_at = evaluated_at
        self._seal = _seal

    def __reduce__(self):
        raise TypeError(
            "Gate8Result is ephemeral and non-serializable; process "
            "containment must be re-established over a freshly re-resolved "
            "descriptor, executable, repository state, and Gate-7 decision by "
            "every consumer (RDGO-001 §9, §15)"
        )

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return (
            f"<Gate8Result containment_established={self.containment_established!r} "
            f"invocation_id={self.invocation_id!r} identity={id(self):#x}>"
        )


def is_gate8_result(candidate: object) -> bool:
    """Return ``True`` only for the literal object a past
    :func:`run_gate8_process_containment` call returned on a completed
    containment establishment — never based on ``isinstance``, fields,
    equality, or any shape property. Fails closed for a forgery, a copy, a
    reconstruction, ``object.__new__``, or a stale handle.

    Provenance only: a ``True`` result does **not** mean containment
    succeeded. A future Gate 9 MUST additionally check
    ``candidate.containment_established is True``.
    """
    return isinstance(candidate, Gate8Result) and candidate in _GATE8_RESULTS


# ═══════════════════════════════════════════════════════════════════════
# The Gate-8 coordinator
# ═══════════════════════════════════════════════════════════════════════


def _bounded_string(value: object, maximum: int = 128) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum and value == value.strip()


def _has_shell_metacharacter(text: str) -> bool:
    return any(ch in _SHELL_METACHARACTERS for ch in text)


def _gate7_result_digest(gate7_result: object) -> str:
    """Canonical digest over the trusted Gate-7 decision evidence Gate 8
    consumes (never re-runs Gate 7). RDGO-001 §9 "recheck … current
    policy/RE decision"; §10 item 7."""
    return compute_canonical_digest(
        {
            "decision": gate7_result.decision,
            "matched_no_go_ids": list(gate7_result.matched_no_go_ids),
            "causing_reason_ids": list(gate7_result.causing_reason_ids),
            "invocation_id": gate7_result.invocation_id,
            "attempt_id": gate7_result.attempt_id,
            "request_id": gate7_result.request_id,
            "pb_decision_digest": gate7_result.pb_decision_digest,
            "authority_freshness_digest": gate7_result.authority_freshness_digest,
            "evaluated_input_digest": gate7_result.evaluated_input_digest,
            "runtime_posture_digest": gate7_result.runtime_posture_digest,
            "expires_at": gate7_result.expires_at,
        }
    )


def _effect_plan_digest(plan: Gate8EffectPlan) -> str:
    return compute_canonical_digest(
        {
            "executable_path": plan.executable_path,
            "argv": list(plan.argv),
            "cwd": plan.cwd,
            "env_allowlist": sorted(plan.env_allowlist),
            "child_process_policy": plan.child_process_policy,
            "resource_limit_ref": plan.resource_limit_ref,
            "time_limit_ref": plan.time_limit_ref,
            "supervision_ref": plan.supervision_ref,
            "network_denied": bool(plan.network_denied),
            "credentials_required": bool(plan.credentials_required),
        }
    )


def _canonical_cwd_within_repository(cwd: str, repo_root: Path) -> Optional[Path]:
    """Canonical path resolution (RDGO-001 §9). Returns the resolved cwd
    only if it is the repository root or a directory beneath it; ``None``
    otherwise (path substitution / traversal)."""
    try:
        resolved_root = repo_root.resolve()
        resolved_cwd = Path(cwd).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if resolved_cwd == resolved_root:
        return resolved_cwd
    if resolved_root in resolved_cwd.parents:
        return resolved_cwd
    return None


def _hash_file(path: str) -> Optional[str]:
    """File stat + hash read — never an execution (RDGO-001 §9 "verify
    executable identity/hash/version")."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    if not (st.st_mode & 0o170000) == 0o100000:  # not a regular file
        return None
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _shell_gate_command_text(executable_path: str, argv: tuple[str, ...]) -> str:
    """A plain space-joined representation for the read-only 88P classifier
    cross-check. Every token has already been proven metacharacter-free, so
    this is not a shell string and cannot be evaluated as one."""
    return " ".join((executable_path,) + tuple(argv))


def run_gate8_process_containment(
    gate7_result: object,
    *,
    gate5_result: object,
    identity: RuntimeDispatchIdentity,
    inputs: RuntimeDispatchRequestConstructionInput,
    authority_current_time: str,
    repo_root: Path,
    effect_plan: Gate8EffectPlan,
    descriptor_resolver: Callable[[RuntimeDispatchRequestConstructionInput], ResolvedExecutable],
) -> tuple[Optional[Gate8Result], tuple[str, ...]]:
    """Run RDGO-001 v3.0 Gate 8 (process containment and live preflight) for
    one ``runtime_dispatch`` request.

    Returns ``(Gate8Result, reasons)`` on a completed containment
    establishment — where ``Gate8Result.containment_established`` is
    ``False`` on any containment failure (a structured audit record) or, on
    the structurally-present but production-unreachable positive branch,
    ``True`` — and ``(None, reasons)`` on any pre-establishment fail-closed
    rejection, creating no ``Gate8Result`` and consuming nothing.

    Fail-closed reason ids (``.1R.13.1`` §12.10 / §25), each returned as a
    single-element tuple unless noted:

    * ``gate8_untrusted_gate7_result`` — missing / non-registry ``Gate7Result``;
    * ``gate8_gate7_decision_not_allow`` — a trusted ``Gate7Result`` whose
      ``decision != "ALLOW"`` (a trusted ``DENY`` is a hard stop **before**
      Shell Gate evaluation);
    * ``gate8_untrusted_gate5_result`` — missing / non-registry ``Gate5Result``;
    * ``gate8_invalid_identity`` / ``gate8_invalid_construction_input`` /
      ``gate8_invalid_authority_current_time`` / ``gate8_invalid_repo_root`` /
      ``gate8_invalid_effect_plan`` / ``gate8_invalid_descriptor_resolver`` —
      structural input guards;
    * ``gate8_invocation_binding_mismatch`` — ``invocation_id`` /
      ``attempt_id`` not equal across ``Gate5Result`` / ``Gate7Result`` /
      ``identity``;
    * ``gate8_request_currentness_drift:<fact>`` — ``inputs`` fail the
      canonical construction re-check;
    * ``gate8_runtime_target_ineligible`` — target/effect-class not
      representable within local-CLI-v1 scope;
    * ``gate8_stale_validated_authority_projection`` — the referenced
      projection is not (or no longer) trusted/revalidating at Gate 8's own
      point of use;
    * ``gate8_authority_subject_scope_mismatch`` — the recomputed
      ``subject_scope_binding_digest`` disagrees with the projection;
    * ``gate8_caller_shell_string_rejected`` — a shell metacharacter in the
      resolved executable path or any argv element;
    * ``gate8_internal_error_fail_closed`` — any unexpected exception from
      the bounded establishment path; no partial output.

    On a completed establishment the accompanying ``reasons`` tuple is
    ``()`` for the (production-unreachable) success branch, or the ordered
    containment-failure reason ids for
    ``containment_established=False`` (e.g.
    ``gate8_executable_identity_mismatch``, ``gate8_descriptor_config_drift``,
    ``gate8_runtime_target_drift``, ``gate8_executable_not_installed``,
    ``gate8_cwd_outside_repository_scope``, ``gate8_environment_not_allowlisted``,
    ``gate8_containment_profile_invalid``, ``gate8_network_not_deniable``,
    ``gate8_credentials_required``, ``gate8_shell_gate_preflight_side_effect_refused``,
    ``gate8_shell_gate_internal_error``, ``gate8_shell_gate_category_denied``).
    """
    try:
        # 1. Provenance — only the exact object a successful
        #    Gate-7 runtime-enforcement evaluation returned (function-local import so
        #    the module-load import graph adds no new edge, mirroring .1R.12
        #    / .1R.13.2).
        from pcae.core.runtime_dispatch_gate5 import Gate5Result, is_gate5_result
        from pcae.core.runtime_dispatch_gate7 import Gate7Result, is_gate7_result

        if not is_gate7_result(gate7_result):
            return None, ("gate8_untrusted_gate7_result",)
        assert isinstance(gate7_result, Gate7Result)

        if type(identity) is not RuntimeDispatchIdentity:
            return None, ("gate8_invalid_identity",)
        if type(inputs) is not RuntimeDispatchRequestConstructionInput:
            return None, ("gate8_invalid_construction_input",)
        if not _bounded_string(authority_current_time, 64):
            return None, ("gate8_invalid_authority_current_time",)
        if not isinstance(repo_root, Path):
            return None, ("gate8_invalid_repo_root",)
        if type(effect_plan) is not Gate8EffectPlan:
            return None, ("gate8_invalid_effect_plan",)
        if not callable(descriptor_resolver):
            return None, ("gate8_invalid_descriptor_resolver",)

        # 2. Trusted-provenance is NOT enough — Gate 8 additionally requires
        #    the Gate-7 decision to be the literal string "ALLOW", by exact
        #    equality. A trusted NEGATIVE Gate7Result(decision="DENY") is a
        #    hard stop BEFORE any Shell Gate evaluation. No code path in this
        #    module converts a non-ALLOW Gate7Result into a positive
        #    containment result (RDGO-001 §9; §15 of the plan).
        if gate7_result.decision != "ALLOW":
            return None, ("gate8_gate7_decision_not_allow",)

        # 3. Gate-5 provenance + exact invocation lineage (RDGO-001 §10a:
        #    invocation_id and attempt_id equal across every gate).
        if not is_gate5_result(gate5_result):
            return None, ("gate8_untrusted_gate5_result",)
        assert isinstance(gate5_result, Gate5Result)

        if (
            gate5_result.invocation_id != identity.invocation_id
            or gate7_result.invocation_id != identity.invocation_id
            or gate7_result.attempt_id != identity.attempt_id
        ):
            return None, ("gate8_invocation_binding_mismatch",)

        # 4. Structural re-check of the fourteen construction facts
        #    (RDGO-001 §9 "re-resolve the exact descriptor/config and verify
        #    no drift"). This module performs no repository / task / registry
        #    resolution of its own beyond the canonical re-checks below.
        try:
            _validate_construction_inputs(inputs)
        except RuntimeDispatchConstructionError as exc:
            return None, (f"gate8_request_currentness_drift:{exc}",)

        if (
            inputs.effect_class != "bounded_local_process_dispatch"
            or inputs.network_requirement is not False
            or not _bounded_string(inputs.runtime_target_id, 128)
        ):
            return None, ("gate8_runtime_target_ineligible",)

        # 5. Freshness re-resolution at Gate 8's own point of use (RDGO-001
        #    §9 "recheck … current policy/RE decision", §15). Possession of a
        #    Gate5Result is never enough: re-trust + revalidate the
        #    referenced projection. The revalidate re-runs validate_approval,
        #    so a projection revoked / expired / consumed / principal-drifted
        #    after Gate 5/6/7 fails closed here.
        projection = gate5_result.projection
        if not is_trusted_validated_authority_projection(projection):
            return None, ("gate8_stale_validated_authority_projection",)
        if not revalidate_validated_authority_projection(
            projection, current_time=authority_current_time
        ):
            return None, ("gate8_stale_validated_authority_projection",)

        # 6. Recompute the subject/scope binding digest from identity +
        #    inputs and compare (mirrors Gate 6 / Gate 7). Gate-5 authority
        #    for invocation A / scope A cannot drive a Gate-8 containment for
        #    a changed permission-relevant field (runtime target, prompt,
        #    repository, task, capability, effect class, adapter binding).
        expected_binding = _expected_subject_scope_binding_digest(
            identity=identity, inputs=inputs
        )
        if projection.subject_scope_binding_digest != expected_binding:
            return None, ("gate8_authority_subject_scope_mismatch",)

        # 7. Resolve the exact executable through the trusted,
        #    coordinator-supplied descriptor_resolver (RDGO-001 §9 "resolve
        #    the exact executable without accepting a caller shell string").
        resolved = descriptor_resolver(inputs)
        if type(resolved) is not ResolvedExecutable:
            return None, ("gate8_invalid_descriptor_resolver",)

        # 8. Refuse any caller-supplied shell string / shell metacharacter —
        #    the effect plan is an argument vector, never a shell string
        #    (RDGO-001 §9 / §11).
        if not _bounded_string(effect_plan.executable_path, 4096):
            return None, ("gate8_caller_shell_string_rejected",)
        if _has_shell_metacharacter(effect_plan.executable_path):
            return None, ("gate8_caller_shell_string_rejected",)
        for token in effect_plan.argv:
            if not isinstance(token, str) or _has_shell_metacharacter(token):
                return None, ("gate8_caller_shell_string_rejected",)

        # ── From here a completed establishment always returns a Gate8Result
        #    (containment_established True or False); failures below are a
        #    structured audit record, never (None, reasons).

        failure_reasons: list[str] = []

        # 8a. Exact executable binding: the plan's executable must be the
        #     resolved one, not a caller substitution (RDGO-001 §9).
        if effect_plan.executable_path != resolved.path:
            failure_reasons.append("gate8_effect_plan_binding_mismatch")

        # 8b. Descriptor/config drift re-resolution (RDGO-001 §9).
        adapter = inputs.adapter_descriptor_binding
        if (
            resolved.descriptor_digest != adapter.descriptor_digest
            or resolved.target_config_digest != adapter.target_config_digest
        ):
            failure_reasons.append("gate8_descriptor_config_drift")

        # 8c. Runtime-target drift since Gate 7 (RDGO-001 §9).
        if resolved.runtime_target_id != inputs.runtime_target_id:
            failure_reasons.append("gate8_runtime_target_drift")

        # 8d. Executable supply-chain identity: hash vs descriptor pin +
        #     installation / current local availability (RDGO-001 §9). File
        #     stat + hash read only — never an execution.
        if not resolved.installed:
            failure_reasons.append("gate8_executable_not_installed")
        else:
            observed_hash = _hash_file(resolved.path)
            if observed_hash is None:
                failure_reasons.append("gate8_executable_not_installed")
            elif observed_hash != resolved.sha256:
                failure_reasons.append("gate8_executable_identity_mismatch")

        # 8e. Exact cwd — canonical path resolution, repository-scoped
        #     (RDGO-001 §9 "establish exact cwd").
        canonical_cwd = _canonical_cwd_within_repository(effect_plan.cwd, repo_root)
        if canonical_cwd is None:
            failure_reasons.append("gate8_cwd_outside_repository_scope")

        # 8f. Environment allowlist — exact names only, never the ambient
        #     process environment (RDGO-001 §9 "environment allowlist").
        if not all(
            isinstance(name, str) and name and name == name.strip()
            for name in effect_plan.env_allowlist
        ):
            failure_reasons.append("gate8_environment_not_allowlisted")

        # 8g. Child-process prohibition/limit, resource/time limit,
        #     supervision (RDGO-001 §9).
        if effect_plan.child_process_policy not in _GATE8_CHILD_PROCESS_POLICIES or not all(
            _bounded_string(ref, 256)
            for ref in (
                effect_plan.resource_limit_ref,
                effect_plan.time_limit_ref,
                effect_plan.supervision_ref,
            )
        ):
            failure_reasons.append("gate8_containment_profile_invalid")

        # 8h. Network remains denied; no credential access required
        #     (RDGO-001 §9).
        if effect_plan.network_denied is not True:
            failure_reasons.append("gate8_network_not_deniable")
        if effect_plan.credentials_required is not False:
            failure_reasons.append("gate8_credentials_required")

        # 8i. Defensive Shell Gate category cross-check via the mature 88P
        #     classifier (RDGO-001 §9; consumed read-only, not re-implemented,
        #     never executed). Refuse any argv that would drive the
        #     classifier's `pcae doctor test-run` lock probe BEFORE calling
        #     it, so build_shell_gate runs only on a proven-inert input.
        program_basename = os.path.basename(effect_plan.executable_path or "")
        shell_gate_decision = "not_evaluated"
        shell_gate_category = "not_evaluated"
        if program_basename in _SHELL_GATE_PREFLIGHT_TRIGGER_PROGRAMS or any(
            os.path.basename(t) in _SHELL_GATE_PREFLIGHT_TRIGGER_PROGRAMS
            for t in effect_plan.argv
        ):
            failure_reasons.append("gate8_shell_gate_preflight_side_effect_refused")
        else:
            try:
                from pcae.core.shell_gate import build_shell_gate

                envelope = build_shell_gate(
                    repo_root,
                    _shell_gate_command_text(effect_plan.executable_path, effect_plan.argv),
                )
                sg = envelope["shell_gate"]
                shell_gate_decision = sg["decision"]
                shell_gate_category = sg["command_category"]
            except Exception:
                failure_reasons.append("gate8_shell_gate_internal_error")
                sg = None

            if sg is not None:
                mutation_flags = any(
                    sg.get(flag_name, False)
                    for flag_name in (
                        "filesystem_write_detected",
                        "source_mutation_detected",
                        "test_mutation_detected",
                        "docs_mutation_detected",
                        "policy_forbidden_file_detected",
                        "raw_git_commit_detected",
                        "raw_git_push_detected",
                        "force_push_detected",
                        "history_rewrite_detected",
                        "destructive_filesystem_detected",
                        "backend_invocation_detected",
                        "prompt_send_detected",
                        "capture_detected",
                        "intake_adoption_detected",
                        "package_install_detected",
                        "network_access_detected",
                        "secret_access_detected",
                        "environment_mutation_detected",
                    )
                )
                if (
                    sg.get("hard_block_present", False)
                    or bool(sg.get("test_run_preflight_required", False))
                    or mutation_flags
                    or shell_gate_category in GATE8_DENIED_SHELL_GATE_CATEGORIES
                    or shell_gate_category not in GATE8_ALLOWED_SHELL_GATE_CATEGORIES
                    or shell_gate_decision not in GATE8_ALLOWED_SHELL_GATE_DECISIONS
                ):
                    failure_reasons.append("gate8_shell_gate_category_denied")

        # 9. Assemble the containment evidence + digests (RDGO-001 §9 "bind
        #    the established containment evidence to the invocation"; §10
        #    item 8).
        gate7_digest = _gate7_result_digest(gate7_result)
        effect_digest = _effect_plan_digest(effect_plan)
        live_preflight_digest = compute_canonical_digest(
            {
                "executable_path": resolved.path,
                "executable_sha256": resolved.sha256,
                "executable_version": resolved.version,
                "installed": bool(resolved.installed),
                "descriptor_digest": resolved.descriptor_digest,
                "target_config_digest": resolved.target_config_digest,
                "runtime_target_id": resolved.runtime_target_id,
                "cwd": str(canonical_cwd) if canonical_cwd is not None else None,
                "network_denied": bool(effect_plan.network_denied),
                "credentials_required": bool(effect_plan.credentials_required),
                "shell_gate_decision": shell_gate_decision,
                "shell_gate_category": shell_gate_category,
            }
        )
        containment_evidence_digest = compute_canonical_digest(
            {
                "executable": {
                    "path": resolved.path,
                    "sha256": resolved.sha256,
                    "version": resolved.version,
                },
                "argv": list(effect_plan.argv),
                "cwd": str(canonical_cwd) if canonical_cwd is not None else None,
                "env_allowlist": sorted(effect_plan.env_allowlist),
                "child_process_policy": effect_plan.child_process_policy,
                "resource_limit_ref": effect_plan.resource_limit_ref,
                "time_limit_ref": effect_plan.time_limit_ref,
                "supervision_ref": effect_plan.supervision_ref,
                "network_denied": True,
                "credentials_required": False,
                "invocation_id": identity.invocation_id,
                "attempt_id": identity.attempt_id,
                "gate7_result_digest": gate7_digest,
                "effect_plan_digest": effect_digest,
                "subject_scope_binding_digest": expected_binding,
            }
        )

        established = not failure_reasons
        if established:  # pragma: no cover - production-unreachable positive branch
            result = Gate8Result(
                containment_established=True,
                causing_reason_ids=(),
                invocation_id=identity.invocation_id,
                attempt_id=identity.attempt_id,
                request_id=gate7_result.request_id,
                gate7_result_digest=gate7_digest,
                effect_plan_digest=effect_digest,
                containment_evidence_digest=containment_evidence_digest,
                live_preflight_digest=live_preflight_digest,
                shell_gate_decision=shell_gate_decision,
                shell_gate_category=shell_gate_category,
                expires_at=authority_current_time,
                evaluated_at=authority_current_time,
                _seal=_GATE8_RESULT_CONSTRUCTOR_SEAL,
            )
            _GATE8_RESULTS.add(result)
            return result, ()

        ordered_reasons = tuple(dict.fromkeys(failure_reasons))
        result = Gate8Result(
            containment_established=False,
            causing_reason_ids=ordered_reasons,
            invocation_id=identity.invocation_id,
            attempt_id=identity.attempt_id,
            request_id=gate7_result.request_id,
            gate7_result_digest=gate7_digest,
            effect_plan_digest=effect_digest,
            containment_evidence_digest=containment_evidence_digest,
            live_preflight_digest=live_preflight_digest,
            shell_gate_decision=shell_gate_decision,
            shell_gate_category=shell_gate_category,
            expires_at=authority_current_time,
            evaluated_at=authority_current_time,
            _seal=_GATE8_RESULT_CONSTRUCTOR_SEAL,
        )
        _GATE8_RESULTS.add(result)
        return result, ordered_reasons
    except Exception:
        # Fail closed on any unexpected exception from the bounded
        # establishment path — no partial output, no Gate8Result (RDGO-001
        # §0, §9).
        return None, ("gate8_internal_error_fail_closed",)
