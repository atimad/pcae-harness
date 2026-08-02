# Permission Broker Production Consumption Contract

## Contract identity and status

**Contract:** PBPC-001
**Version:** 1.2
**Status:** FROZEN (amended; Finding B-1 is CLOSED — see Section 8.1)
**Frozen by:** Phase 148B — Permission Broker Production Consumption Contract
Freeze
**Amended by:** Phase 148C.1 — Permission Broker Production Consumption
Contract Clarification and Repair (corrects Section 8's `POL-004`
disposition and coverage-table traceability, and Section 26/30's
compatibility/verdict claims; does NOT close Finding B-1 — see
`docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`);
further amended by Phase 148C.9 — Permission Broker Production Consumption
Contract v1.2 Reconciliation (B-1 Closure Ratification) (updates Section
8's `POL-004` row, Section 8.1, Section 26, and Section 30 to record
Finding B-1 CLOSED per Phase 148C.8's independent adjudication, adds a
normative dependency on PBPA-001 v1.0, and reconciles simulation_only/
`evaluated_policy_ids` prose to PBPA-aware semantics; introduces no new
permission semantics — see
`docs/PHASE_148C.9_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_V1_2_RECONCILIATION.md`)

PBPC-001 v1.0 is the sole authoritative contract governing how the first
real production mutation command, `pcae push`, consumes the Permission
Broker Foundation as its mandatory centralized permission-decision
boundary. Future implementation phases SHALL cite PBPC-001 and SHALL NOT
reinterpret Phase 148A's architecture, or the Permission Broker Foundation
contracts (Phase 108A-C), locally.

The Phase 148A architecture document
(`docs/architecture/PHASE_148A_NEXT_STRATEGIC_CAPABILITY_ARCHITECTURE.md`)
is the approved design basis for this contract. Where its prose and this
contract differ in force, this contract is normative; Section 5 documents
every point where independent reconstruction from primary source diverged
from Phase 148A's prose.

This is contract text only. It does not implement, activate, authorize, or
wire the Permission Broker into `pcae push`. It grants no runtime,
lifecycle, or execution capability, and it does not itself authorize an
implementation phase — Section 27 fixes the exact preconditions a future
implementation phase must satisfy.

Runtime posture, unaffected by this contract:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, and **MAY**
are normative. `SHALL`/`MUST` state binding requirements; `SHALL NOT`/`MUST
NOT` state binding prohibitions; `MAY` states a discretionary permission.
This contract does not use `SHOULD`: every mandatory behavior is stated as
`SHALL`/`SHALL NOT`.

Every mandatory behavior receives a unique, sequential, stable,
non-reused, independently traceable requirement identifier of the form
`PBPC-REQ-###`. Identifiers are never renumbered or reused across
revisions.

## 1. Purpose

PBPC-REQ-001: This contract SHALL govern the mandatory consumption of the
existing, already-frozen Permission Broker Foundation
(`src/pcae/core/permission_broker_foundation.py`, Phase 108A-C) by the
existing, already-shipping production mutation command `pcae push`
(`src/pcae/commands/push.py`).

PBPC-REQ-002: This contract SHALL centralize permission evaluation for the
push conditions the Permission Broker Foundation is currently capable of
representing (Section 4), preserve every existing push hard-block-like
condition's current enforcement (Section 4), introduce no new mutation
capability, introduce no autonomous authority, and not elevate runtime
capability.

PBPC-REQ-003: Conformance with PBPC-001, alone, SHALL NOT authorize
implementation. Section 27 states the complete precondition set.

PBPC-REQ-003A (added, v1.2, Phase 148C.9): Policy applicability for
`pcae push` requests under this contract SHALL be determined according to
PBPA-001 v1.0 (`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`)
or its contract-authorized successor. This contract SHALL NOT duplicate
PBPA-001's applicability matrix, predicate, or ordering; it depends on
PBPA-001 rather than forking it. Section 8's `POL-004` disposition and
Section 8.1's B-1 closure rationale are stated in PBPA-001's own
terminology (**applicable** / **not applicable**, `execution_class`) for
exactly this reason.

## 2. Independent Reconstruction Methodology

This contract was authored by direct inspection of the following primary
sources, not by trusting Phase 148A's own summary prose: `src/pcae/core/
permission_broker_foundation.py` (788 lines, read in full); `src/pcae/core/
permission_broker.py` (the legacy/prototype broker, `HARD_BLOCK_REGISTRY`
and `HardBlockPolicy`, read in full); `src/pcae/commands/permission_broker.py`
(command layer); `src/pcae/commands/push.py` (895 lines, read in full,
including both git-push dispatch sites); `src/pcae/core/
command_path_observation.py` (`observe()`, `INTEGRATION_REGISTRY`);
`src/pcae/core/backend_invocations.py` (Runtime Enforcement Coordinator/
Decision Engine sections); `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`
(IWC-REQ-029 and neighbors); `src/pcae/authority_evaluation/__init__.py` and
`src/pcae/aesic/__init__.py`; `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md`;
`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`;
`docs/PHASE_109_OBSERVATION_INTEGRATION_HARDENING.md`;
`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(structural template for this contract); and `docs/architecture/
PHASE_148A_NEXT_STRATEGIC_CAPABILITY_ARCHITECTURE.md` in full.

## 3. Scope (MVP)

PBPC-REQ-004: This contract SHALL apply to exactly one production consumer:
`pcae push`, including both of its internal git-push dispatch code paths
identified in Section 7 (the ordinary path and the `--staged-file-aware`
path). No additional production consumer is in scope of PBPC-001 v1.0.

PBPC-REQ-005: This contract SHALL NOT apply to `pcae commit`, arbitrary Git
commands, shell execution, filesystem mutation generally, backend
invocation generally, runtime adapters generally, Telegram commands, or
generic command dispatch. Those become consumers only through separately
governed future phases (148D+), which SHALL NOT be pre-authorized by this
contract.

## 4. Terminology and Semantic Separation

PBPC-REQ-006: This contract SHALL freeze five distinct concepts so they
cannot silently collapse into one another:

- **Confirmed** — Interactive Workflow Confirmation (IWC) Decision Session
  semantics, where applicable. It is not permission.
- **Authorized** — authority granted by the applicable authority-owning
  lifecycle/contract (e.g. a phase authorization). It is not automatically
  Permission Broker permission.
- **Permitted** — the Permission Broker Foundation's decision
  (`ALLOW`/`DENY`/`HUMAN_REVIEW`) for one specifically bound
  `PermissionBrokerRequest`. It is not runtime capability.
- **Capable** — what the runtime can actually perform, per the runtime
  capability model (`pcae runtime inspect`: State/Maximum Capability/
  Execution Availability). It is not permission.
- **Executed** — an operation actually attempted/performed. It cannot be
  inferred merely from permission.

PBPC-REQ-007: The following inequalities SHALL hold and SHALL NOT be
collapsed by any future implementation: confirmation ≠ authorization;
authorization ≠ permission; permission ≠ capability; capability ≠
execution. No unified state machine combining them is authorized by this
contract.

PBPC-REQ-007A (added, v1.1, Phase 148C.1): A sixth concept SHALL be
frozen as distinct from, and non-substitutable for, all five above:

- **Git Approval** — approval that a proposed change to the repository's
  version-controlled content is correct and should be merged/pushed
  (PR review approval, or, in the current transitional posture, the
  Owner's own governed push), per
  `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5. It is
  distinct from **Permission Broker approval** (`approval_present` on a
  `PermissionBrokerRequest`, which `POL-004`/`MissingHumanApprovalRule`
  evaluates) — the latter, per that same document's frozen text, means
  **execution approval**: *"approval that a specific, proposed execution
  action... may proceed... These are never interchangeable."* `pcae
  push` is governed by Git Approval today (branch protection, PR review,
  the Owner's transitional direct-push exemption, `pcae push check`); it
  is not, and this contract does not make it, a mediated execution action
  within `docs/V0_2_AUTONOMY_CONTRACT.md`'s execution lifecycle. Git
  Approval SHALL NOT be treated as satisfying `POL-004`'s
  `approval_present` field, and `POL-004`'s `approval_present` SHALL NOT
  be treated as a statement about Git Approval. See Section 8.1.

## 5. Independent Reconstruction Findings — Where This Phase Diverges from Phase 148A's Prose

PBPC-REQ-008: This contract SHALL document, rather than silently resolve,
every point where direct source inspection produced a different result
than Phase 148A §14's summary prose. Two are recorded:

- **Finding F-1 (decision vocabulary).** Phase 148A §14 describes the
  "foundation model" decision vocabulary as `ALLOW / DENY / HUMAN_REVIEW /
  MORE_EVIDENCE`. Direct inspection of `permission_broker_foundation.py:46-50`
  confirms `DECISION_VALUES = (DECISION_ALLOW, DECISION_DENY,
  DECISION_HUMAN_REVIEW)` — **three** values. `MORE_EVIDENCE` (as
  `BROKER_MORE_EVIDENCE`) exists only in the separate, legacy 4-outcome
  model inside `permission_broker.py` (`evaluate_permission_broker`,
  Phase 91A), not in the foundation. This contract uses the verified
  three-value foundation vocabulary (Section 8) and does not reference
  `MORE_EVIDENCE` as a foundation-model concept. Classification: **OBSERVATION**
  (Phase 148A's architecture-level conclusions are unaffected; only one
  descriptive sentence in its prose was imprecise).
- **Finding F-2 (registry cardinality and identity).** Phase 148A §14
  describes "an 11-item `HARD_BLOCK_REGISTRY`." Direct inspection of
  `permission_broker.py:744-829` and the registry's own test
  (`tests/test_permission_broker.py:1374`, `assert len(HARD_BLOCK_REGISTRY)
  == 12`) confirms **12** entries (enumerated in Section 6). Classification:
  **OBSERVATION** (a miscount in prose; the registry's own code and test
  are dispositive and are what this contract binds to).

PBPC-REQ-009: Neither finding is Blocking. Neither required narrowing this
contract's MVP scope beyond what Section 3 already states.

## 6. Two Broker Implementations — Consolidation Decision

PBPC-REQ-010: Two independent Permission Broker implementations coexist in
this repository: the legacy/prototype model (`src/pcae/core/
permission_broker.py`, Phases 88R/90A/91A/91C — a 24-outcome and a
separate 4-outcome decision model, plus the 12-entry `HARD_BLOCK_REGISTRY`/
`HardBlockPolicy` vocabulary), and the frozen foundation model
(`src/pcae/core/permission_broker_foundation.py`, Phase 108A-C — the
3-outcome `ALLOW`/`DENY`/`HUMAN_REVIEW` model, `PermissionBrokerRequest`/
`PermissionBrokerDecision`, and policy rules `POL-001` through `POL-012`).
This is Phase 148A §33's "broker consolidation" open question, which this
contract resolves as follows.

PBPC-REQ-011: `pcae push`'s Permission Broker Production Consumption SHALL
be built exclusively on the Permission Broker Foundation
(`permission_broker_foundation.py`: `PermissionBroker`,
`PermissionBrokerRequest`, `PermissionBrokerDecision`, `POL-001..012`).

PBPC-REQ-012: The legacy `permission_broker.py` module (including
`HARD_BLOCK_REGISTRY`, `HardBlockPolicy`, `build_permission_broker`,
`evaluate_permission_broker`) is NOT formally deprecated by this contract
and SHALL NOT be modified, removed, or reinterpreted by any implementation
conforming to PBPC-001. It SHALL continue to serve its existing role as
richer, evidence-oriented diagnostic tooling (`pcae permission-broker
evaluate/status/explain/check/hard-blocks`), unaffected by this contract.

**Rationale.** The foundation model, not the legacy model, is the one
Phase 108A-C froze as "the single policy decision point for future
execution" (`permission_broker_foundation.py:1-6`), the one Phase 109A/109B/
109C's command-path integration design and observation-only precedent
(`pcae health`/`pcae check`/`pcae doctor task-memory`/`pcae push check`)
already consult exclusively, and the one Phase 148A §14/§18/§19
independently concluded Chapter 148 "should consume." The legacy model's
12-entry `HARD_BLOCK_REGISTRY` and the foundation's 12 `POL-` identifiers
are coincidentally equal in count and are **not the same vocabulary** —
conflating them would itself be a semantic-drift risk (Section 8).

## 7. Existing Production Mutation Boundary — `pcae push`

PBPC-REQ-013: The following are the exact, independently verified,
existing production `git push` dispatch sites in `src/pcae/commands/
push.py`, both of which this contract's non-bypassability requirements
(Section 9) govern:

- **Path A — ordinary push.** `run_push()` calls `assess_push_readiness(root)`
  (`push.py:406`), gates on `readiness.ready` (`:408`) and `dry_run`
  (`:426`), then dispatches `subprocess.run(["git", "push"], ...)` at
  `push.py:454-460`.
- **Path B — `--staged-file-aware` push.** `run_push()` dispatches to
  `_run_push_staged_file_aware()` (`push.py:404`) **before**
  `assess_push_readiness()` is ever called on this path. That function
  computes its own, narrower, independently-maintained readiness (phase-
  report trust, phase-report identity, protected-staged-file preservation,
  force-push-required detection only — it never checks `health_ok`,
  `check_ok`, `doctor_ok`, or lifecycle review), then dispatches
  `subprocess.run(["git", "push", "origin", "main"], ...)` at
  `push.py:604-612`.

PBPC-REQ-014: Path B is a genuine second production mutation boundary, not
an alias of Path A. A future implementation conforming to this contract
SHALL insert the Decision Consumption Point (Section 9) immediately before
**both** Path A's dispatch (`push.py:454-460`) and Path B's dispatch
(`push.py:604-612`). An implementation that wires only Path A leaves Path B
as an unaddressed, unauthorized bypass of this contract's central
guarantee and does not conform to PBPC-001.

**Rationale for this finding.** The prompt's conceptual flow diagram and
Phase 148A's own canonical data flow (§20) both depict a single "existing
push dispatch path." Direct inspection shows two. This is exactly the
class of discrepancy Section 9's Non-Bypassability requirements exist to
close — an implementation that trusted the single-path assumption would
ship a broker integration with a known, pre-existing bypass route already
in production.

PBPC-REQ-015: The existing observation-only touchpoint at
`push.py:303-313` (`run_push_check()`'s call to `observe(...)`, Phase 109C
INT-004) is unaffected by this contract. It remains scoped to `pcae push
check` only, its decision remains discarded, and it SHALL NOT be treated as
prior art for `pcae push`'s own consumption — `run_push()` has no
comparable call today, which is precisely the gap this contract governs.

## 8. Existing HARD_BLOCK_REGISTRY / Policy Mapping

PBPC-REQ-016: The following table maps the legacy `HARD_BLOCK_REGISTRY`'s
12 entries (`permission_broker.py:744-829`) against the Permission Broker
Foundation's `POL-001..012` (`permission_broker_foundation.py:577-590`) and
against `pcae push`'s own existing readiness conditions
(`assess_push_readiness`, `push.py:208-291`). This is the authoritative
disposition of every existing push-relevant gating condition under PBPC-001
v1.1. (v1.1, Phase 148C.1: all 12 `HARD_BLOCK_REGISTRY` entries are now
given an explicit disposition — see the 8 "out of scope" rows appended
below the original 4 — closing the traceability gap Phase 148C's §9
identified as Non-Blocking.)

| Existing condition | Current source | Current enforcement mechanism | Foundation POL-rule equivalent | PBPC-001 v1.1 disposition |
|---|---|---|---|---|
| Raw `git push` (bypassing `pcae push`) | `HARD_BLOCK_REGISTRY: blocked_by_raw_git_push` | Shell-gate/hook layer, outside any command's control flow | none (out of the broker's domain — the broker is never consulted for a raw shell invocation) | **Unchanged by this contract.** Not a `pcae push` condition; PBPC-001 neither weakens nor duplicates it. |
| Force push | `HARD_BLOCK_REGISTRY: blocked_by_force_push` | Shell-gate/hook layer | none | **Unchanged.** `pcae push`'s own `git push` calls (Section 7) never pass `--force`; not applicable to this MVP's request shape. |
| `--no-verify` | `HARD_BLOCK_REGISTRY: blocked_by_no_verify` | Shell-gate/hook layer | none | **Unchanged.** Not applicable — `pcae push`'s dispatch calls never pass `--no-verify`. |
| Missing active task | `HARD_BLOCK_REGISTRY: blocked_by_missing_task` (legacy) | Not currently checked by `push.py` directly (push has no explicit "no active task" hard block today; `assess_push_readiness` does not require an active task per se, though most of its readiness computation assumes one exists) | **POL-001** `MissingActiveTaskRule` (implemented) — DENY on `task_id` falsy | **Newly bound.** This is the one condition where the Foundation has an implemented, non-stub rule directly applicable to a push request. Section 10's request model binds `task_id` from the same active-task lookup `assess_push_readiness` already performs (`push.py:242-243`). |
| Working tree not clean / nothing meaningfully changed | `push.py` own logic (`clean`, `mode` computation) | `assess_push_readiness` | none (`POL-002` "Task Outside Scope" is a registered stub, `POLICY_STATUS_NOT_IMPLEMENTED`, never triggers) | **Remains push-owned.** No POL rule represents this; adding one is out of scope (Section 3, "no new push policy"). |
| Health/check/doctor failing | `push.py` own logic | `assess_push_readiness` | none | **Remains push-owned.** Same reasoning. |
| Lifecycle review required-and-failed | `push.py` own logic (Phase policy-gated) | `assess_push_readiness` | none | **Remains push-owned.** |
| Phase-report trust incomplete/placeholder | `push.py` own logic (Phase 105D) | `assess_push_readiness` | none | **Remains push-owned.** |
| Phase-report identity (stale/wrong phase) | `push.py` own logic (Phase 137F.1) | `assess_push_readiness` | none | **Remains push-owned.** |
| Structurally invalid / unrecognized action or component | n/a (not previously a push concept) | n/a | **POL-006/POL-007** (implemented) | **Newly applicable** as general request-validity denial paths every `PermissionBrokerRequest` is subject to; not push-specific but inherited automatically by binding to the Foundation. |
| Missing evidence | n/a | n/a | **POL-003** `MissingEvidenceRule` (implemented) — DENY on `not evidence_available` | **Newly applicable.** Section 10 fixes `evidence_available=True` for a well-formed push request (the Evidence Adapter, by construction, never emits a request without the evidence it is required to gather first). |
| Missing human approval | n/a | n/a | **POL-004** `MissingHumanApprovalRule` (implemented) — `HUMAN_REVIEW` on `not approval_present`, when applicable | **RESOLVED (Finding B-1 CLOSED, v1.2 reconciliation).** Under PBPA-001 v1.0 (`applicable_execution_classes = {shell, backend, adapter, rollback}`), `POL-004` is **not applicable** to a `pcae push` request (`execution_class=EXECUTION_CLASS_MUTATION`, PBPC-REQ-034) — not applicability=ALLOW; `POL-004` simply does not govern this operation profile (Section 8.1). `approval_present` remains fixed `False` (PBPC-REQ-046, unchanged) and is not, and was never, the cause of non-applicability. See Section 8.1. |
| Non-simulation execution attempt | n/a | n/a | **POL-005** `ExecutionDisabledRule` (implemented) — DENY on `not simulation_only` | **Resolved explicitly** — Section 10.1. |
| `blocked_by_raw_git_commit` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (commit, not push). Added v1.1. |
| `blocked_by_destructive_filesystem` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (filesystem-scoped, not a `pcae push` condition). Added v1.1. |
| `blocked_by_unknown_command_class` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (generic command classification, a different enforcement layer than either `push.py` or the `POL-` rules). Added v1.1. |
| `blocked_by_out_of_scope` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (path-scoped). Added v1.1. |
| `blocked_by_policy_forbidden_file` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (path-scoped). Added v1.1. |
| `blocked_by_forbidden_path` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (path-scoped). Added v1.1. |
| `blocked_by_enforcement_not_ready` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (generic enforcement-readiness gate, shell-gate layer). Added v1.1. |
| `blocked_by_enforcement_not_authorized` (`HARD_BLOCK_REGISTRY`) | Shell-gate/hook layer | n/a | none | **Out of scope, not push-relevant** (generic enforcement-authorization gate, shell-gate layer). Added v1.1. |

### 8.1 Finding B-1 Status (v1.1 origin, Phase 148C.1; CLOSED and ratified v1.2, Phase 148C.9)

`POL-004`'s `approval_present` field, per its own upstream lineage
(`NG-008` → `INV-003` → `COMP-003`), means **execution approval** — a
concept `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5
freezes as explicitly, permanently non-interchangeable with **Git
Approval** (PBPC-REQ-007A), the concept that actually governs `pcae
push` today. No authoritative source establishes execution approval for
`pcae push` (no such source exists: `COMP-003` is not implemented), so
`approval_present` cannot legitimately be set `True` for a `pcae push`
request without fabricating an equivalence this repository's own frozen
sources forbid, and this contract does not do so — `approval_present`
remains fixed `False` (PBPC-REQ-046, unchanged).

**Original finding (v1.1, Phase 148C.1).** At the time PBPC-001 v1.1 was
frozen, the Permission Broker Foundation's rule-evaluation model had no
mechanism to exempt `POL-004` from applying to a specific operation
profile — every rule evaluated on every request unconditionally
(`PolicyRegistry.evaluate_all`, pre-148C.6). Finding B-1 was therefore
**BLOCKING**: no conformant `pcae push` request could reach `ALLOW` under
this contract. Full v1.1-era analysis:
`docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`.

**Closure (v1.2, Phase 148C.9, ratifying Phase 148C.8's independent
adjudication).** PBPA-001 v1.0
(`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
frozen Phase 148C.3, independently adversarially verified Phase 148C.4)
amended the Permission Broker Foundation additively with an
**applicability** layer, distinct from and evaluated strictly before
**evaluation** (PBPA-001 §4A): a policy that is not applicable to a
request's `execution_class` is never passed to its own `evaluate()`
method and contributes no `triggered` judgment. Phase 148C.6
independently implemented this layer in
`src/pcae/core/permission_broker_foundation.py` (verified Phase 148C.7);
Phase 148C.8 independently re-executed the live, unmodified
`PermissionBroker` against the canonical PBPC push-shaped request and
confirmed, by fresh evaluation rather than citation, that `POL-004` now
resolves **not applicable** (`applicable_execution_classes =
{EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER,
EXECUTION_CLASS_ROLLBACK}`, PBPA-001 §18; `EXECUTION_CLASS_MUTATION` —
`pcae push`'s fixed value, PBPC-REQ-034 — is not a member) and the
request reaches `ALLOW`. This phase (148C.9) independently re-executed
the same canonical request against the unmodified Foundation and
reconfirmed the identical result (Section 30A).

**148C-B-1 CLOSED.** Narrow scope, exactly as Phase 148C.8 adjudicated
and this phase ratifies in contract text: the original universal `POL-004`
applicability contradiction is removed by PBPA-001 v1.0 and its
independently verified production implementation — the contradiction no
longer makes every conformant `pcae push` request unsatisfiable. This
closure is discovered and adjudicated by Phase 148C.8, not by this phase;
148C.9's own contribution is textual ratification of an
already-established, already-independently-verified fact (Section 27).
This is **not** a claim that PBPC-001 is implemented, that `pcae push` is
wired to the broker, that Chapter 148D is authorized, or that every future
Permission Broker issue is foreclosed — see Section 30 and Section 29's
unchanged Explicit Non-Goals.

**Applicability is not a permission vote.** `POL-004` being "not
applicable" means the policy is silent about this request — it has
expressed no opinion, permissive or otherwise (PBPA-001 §5, PBPA-REQ-016).
`ALLOW` for a `pcae push` request results from `_compose`'s existing
"nothing triggered among the applicable set" rule (unchanged,
`permission_broker_foundation.py`), not from `POL-004` voting `ALLOW`.
`POL-004` retains its full, unweakened `HUMAN_REVIEW`-on-missing-approval
behavior for every request to which it **is** applicable (Section 37 of
PBPA-001; reconfirmed by this phase's own control-case test, Section 30A).

**`evaluated_policy_ids` semantics (reconciled).** Consistent with
PBPA-001 §26 (PBPA-REQ-081), `PermissionBrokerDecision.evaluated_policy_ids`
means, from the Foundation's applicability implementation forward, exactly
the set of policies actually applicable to and evaluated for this
request — not "every registered policy," and not a v1.1-era assumption
that all default policies always evaluate. For the canonical `pcae push`
request this is eleven of the twelve registered policies (`POL-004`
excluded as not applicable). `applicable_policy_ids` and
`non_applicable_policy_ids` (PBPA-001 §26, additive `PermissionBrokerDecision`
fields, live in the current Foundation) are available for diagnostic and
audit explanation of exactly which policies governed a given decision and
why `POL-004` did not participate; this contract recognizes them
normatively for that purpose without requiring their durable persistence
(Section 24 remains unamended — see also Section 27's Finding disposition).

Resolving Finding B-1 required a separately authorized Permission Broker
Foundation policy-applicability amendment (PBPA-001, Phase 148C.2-148C.7)
— that amendment has now been made and independently verified. It did not
require, and this contract still does not authorize, deferring `pcae
push`'s Permission Broker consumption until `COMP-003` is genuinely
implemented; that alternative closure path, considered by PBPC-001 v1.1,
is superseded by the applicability-layer path actually taken.

PBPC-REQ-017: No existing hard-block-like condition listed above SHALL be
made weaker, broader, or silently removed by an implementation conforming
to this contract. Every condition currently enforced by `push.py`'s own
logic (`assess_push_readiness`) SHALL continue to be enforced by that same
logic, unchanged, in addition to (not instead of) the Permission Broker
consumption this contract adds (Section 9, Ownership Model).

PBPC-REQ-018: This contract does NOT claim full push-condition coverage by
the Permission Broker Foundation. Section 8's table is the honest
disposition: exactly one existing push-relevant condition (missing active
task) gains a directly corresponding, currently-implemented `POL-` rule;
the remainder have no Foundation counterpart today and are explicitly
**not** centralized by this MVP. Extending Foundation policy coverage to
represent them (additive `POL-013+` rules) is out of scope for v1.0
(Section 3) and is identified as future work (Section 26), not a defect in
this contract.

**Ratified, v1.2 (Phase 148C.9):** Phase 148C.8 independently re-confirmed
this disposition against the legacy `permission_broker.py`
`HARD_BLOCK_REGISTRY` (12 entries) and found the true centralization
target this requirement already states is **permission-bearing
judgments** — genuine approval/authority-bearing gates (of which
`POL-001`'s missing-active-task condition is the sole currently-implemented
example) — not **mechanical or structural push checks** (dirty working
tree, health/check/doctor status, phase-report trust/identity, and the
shell-gate/hook-layer conditions), which may remain command-owned or
hook-owned without independently establishing permission. This contract
does NOT claim that all twelve `HARD_BLOCK_REGISTRY` entries become
Foundation policies; PBPC-REQ-018 above already forecloses that broader
claim, and this ratification does not expand it. No hard block's
current ownership is reclassified by this ratification.

## 9. Non-Bypassability

PBPC-REQ-019: Once an implementation conforming to this contract is
shipped, every real `pcae push` mutation attempt — both Path A and Path B
(Section 7) — SHALL cross the Permission Broker enforcement boundary
(Section 12, Decision Consumption Point) before any `git push` subprocess
is dispatched.

PBPC-REQ-020: No alternate `pcae push` code path SHALL dispatch `git push`
without first obtaining a valid, freshly bound `PermissionBrokerDecision`.

PBPC-REQ-021: No fallback SHALL convert a broker evaluation failure,
exception, or malformed result into a permission to push. Any such failure
SHALL fail closed to a result equivalent to `DENY` (Section 15).

PBPC-REQ-022: A malformed `PermissionBrokerRequest` SHALL fail closed
(this already holds today — `PermissionBroker.evaluate()`'s top-level
structural-validity check, `permission_broker_foundation.py:744-787`,
DENYs any non-`PermissionBrokerRequest` object; this contract requires the
Command Evidence Adapter (Section 11) to never emit such an object, and
requires the Decision Consumption Point to never bypass `.evaluate()`'s
own validation).

PBPC-REQ-023: Missing applicable policy SHALL fail closed (already holds:
an empty `PolicyRegistry` composes to DENY, `permission_broker_foundation.py:
662-736`, `_compose`, empty-results branch).

PBPC-REQ-024: Ambiguous or duplicate policy resolution SHALL fail closed
(already holds via `_compose`'s deterministic DENY > HUMAN_REVIEW > ALLOW
precedence — there is no code path by which two rules disagreeing produces
anything other than the higher-precedence outcome).

PBPC-REQ-025: A broker-internal error (an individual `PolicyRule.evaluate()`
raising or returning a malformed result) SHALL fail closed (already holds
via `_sanitize_result`, `permission_broker_foundation.py:598-629`).

PBPC-REQ-026: An unknown/unrecognized decision value returned from any
future modification of the broker SHALL be treated as `DENY` by the
Decision Consumption Point, never as `ALLOW`.

PBPC-REQ-027: A stale decision (Section 15) SHALL NOT authorize a push it
was not evaluated against.

PBPC-REQ-028: An operation-identity mismatch between the bound decision and
the operation about to be dispatched (Section 13, Section 16) SHALL fail
closed — no push.

PBPC-REQ-029: Direct reuse of `push.py`'s lower-level, module-private
helper functions (e.g. `_count_unpushed_commits`, `_staged_file_snapshot`,
`_unpushed_commit_lines`) SHALL NOT constitute a bypass, because none of
them independently dispatch `git push` — only `run_push()`'s two
identified sites (Section 7) do, and both are in scope of Section 9's
requirements. A future implementation SHALL NOT introduce any new
push-dispatching helper outside the two Decision Consumption Points this
contract requires.

PBPC-REQ-030: Recovery or retry logic SHALL NOT bypass enforcement — any
retried push attempt SHALL re-enter the full evidence-gathering →
request-construction → broker-evaluation → decision-consumption sequence
(Section 20, Replay and Restart); no retry path may reuse a prior decision
without satisfying Section 15's freshness requirements.

PBPC-REQ-031: A diagnostic- or reporting-layer failure (e.g. `_reconcile_
post_push` failing, notification dispatch failing) SHALL NOT retroactively
create, revoke, or alter the permission decision that already gated the
completed `git push` dispatch. Post-dispatch failures are governed by
Section 22 (Failure Ownership), not by this section.

## 10. Existing Permission Broker Vocabulary — Reuse, No Second Taxonomy

PBPC-REQ-032: An implementation conforming to this contract SHALL reuse the
Permission Broker Foundation's existing request vocabulary
(`PermissionBrokerRequest`), decision vocabulary (`DECISION_ALLOW`,
`DECISION_DENY`, `DECISION_HUMAN_REVIEW`), policy vocabulary
(`POL-001..012`), and reason/failure vocabulary (`decision_reason`,
`matched_no_go_ids`, `matched_invariants`, `required_remediation`,
`reason_chain`) exactly as frozen by Phase 108A-C. This contract SHALL NOT
create, and no implementation conforming to it SHALL create, a second
decision taxonomy specific to `pcae push`.

PBPC-REQ-033: `action_type` for every `pcae push` request SHALL be the
existing `ACTION_PUSH = "push"` constant
(`permission_broker_foundation.py:101`) — already part of
`KNOWN_ACTION_TYPES`. No new action type is introduced.

PBPC-REQ-034: `execution_class` for every `pcae push` request SHALL be the
existing `EXECUTION_CLASS_MUTATION = "mutation"` constant — already part of
`KNOWN_EXECUTION_CLASSES`. No new execution class is introduced.

PBPC-REQ-035: `requested_component` for every `pcae push` request SHALL be
the existing `"COMP-001"` (Permission Broker) — the component identifying
who is asked to decide, consistent with the existing `push_check`
observation call's usage (`push.py:307`).

### 10.1 Resolving the POL-005 Misclassification Risk (Phase 148A §33)

PBPC-REQ-036: `simulation_only` on every `pcae push` `PermissionBrokerRequest`
— including requests representing a genuine, about-to-execute git push,
not merely a diagnostic check — SHALL be set to `True`.

**Rationale.** `simulation_only`, as frozen by Phase 108A, means "no
execution boundary (`COMP-002`) exists to carry this out" — it is a
statement about the Foundation's own current implementation status, not a
statement about whether `pcae push`'s own, already-shipping, non-broker
execution path is about to run. `pcae push` has always been able to
execute a real `git push` (Section 7); that capability belongs entirely to
`push.py`, not to the Permission Broker, and pre-dates this contract.
Setting `simulation_only=False` for a real push request would incorrectly
claim the broker itself possesses execution capability it does not have,
and — per `ExecutionDisabledRule`'s frozen semantics
(`permission_broker_foundation.py:446-475`, POL-005) — would
unconditionally DENY every push, permanently, misclassifying a legitimate,
already-authorized git mutation as an attempted runtime-execution-boundary
bypass. Freezing `simulation_only=True` for all push requests preserves
POL-005's original intent (deny attempts to claim execution capability that
does not exist) while correctly reflecting that `pcae push`'s git mutation
capability is external to, and does not depend on, the Foundation's
`COMP-002` execution boundary.

PBPC-REQ-037: Consistent with PBPC-REQ-036, an `ALLOW` decision under this
contract SHALL continue to carry `implementation_status=
"execution_unavailable"` exactly as the Foundation already stamps every
decision (`permission_broker_foundation.py:247`). This is not a defect;
Section 14 defines precisely what `ALLOW` does and does not mean.

PBPC-REQ-037A (added, v1.2, Phase 148C.9 — disposition of Finding
F-148C.8-1): Phase 148C.8 independently discovered, and this phase
independently re-confirmed (Section 30A), that a request otherwise shaped
like a `pcae push` request but with `simulation_only=False` resolves
`DENY` via `POL-005` (`ExecutionDisabledRule`, universal — PBPA-001 §15,
§20) given the runtime's current `Observed/observe/unavailable` posture.
This is classified **EXPECTED_CONTRACT_BEHAVIOR**, not a defect requiring
repair: `POL-005`'s applicability is unaffected by PBPA-001 (`simulation_only`
is never an applicability input, PBPA-001 §20, PBPA-REQ-068), and its
evaluation logic is unmodified. This finding is corroborating evidence for,
not a challenge to, PBPC-REQ-036's fixed `simulation_only=True` value: it
demonstrates the fixed value is load-bearing, not merely a descriptive
label — setting it dishonestly would not "unlock" anything, it would
correctly fail closed. This contract does not weaken `POL-005`, does not
change `simulation_only`'s fixed value, and does not broaden the push
request's field values to avoid this behavior.

**Simulation truthfulness (clarified, v1.2).** `simulation_only=True` on a
`pcae push` request states only that the **Permission Broker Foundation's
own execution boundary** (`COMP-002`) does not carry out the push
(PBPC-REQ-036's rationale, unchanged) — it is not, and SHALL NOT be read
as, a statement that `git push` itself will not actually occur. `pcae
push`'s real `git push` subprocess dispatch (Section 7) is external to,
and executes independently of, the broker's `simulation_only` field. This
distinction is PBPA-001 §21's "broker execution" vs. "requested operation"
separation (PBPA-REQ-070/071), which this contract adopts by reference
rather than restating.

## 11. Ownership Model

PBPC-REQ-038: Exactly one owner SHALL exist per responsibility. No dual
ownership is authorized.

| Responsibility | Owner |
|---|---|
| Push operation observation (git state, task state, health/check/doctor results) | `push.py`'s existing `assess_push_readiness()` (Path A) / existing Path-B-local checks (unchanged) |
| Request construction | Command Evidence Adapter (new, not built in 148B — Section 24) |
| Operation identity construction | Command Evidence Adapter |
| Policy resolution | Permission Broker Foundation (`PolicyRegistry`) |
| Policy evaluation | Permission Broker Foundation (`PermissionBroker.evaluate()`) |
| Permission decision | Permission Broker Foundation — sole authority |
| Enforcement of decision before mutation | Decision Consumption Point (new, Section 12) |
| User-facing diagnostic rendering | `push.py` command layer |
| Retry classification | `push.py` command layer (unchanged retry/rerun idiom — Section 20) |
| Malformed-request handling | Command Evidence Adapter (must never construct an invalid request); `PermissionBroker.evaluate()` as a second, defense-in-depth layer (already fails closed) |
| Broker-internal failure handling | Decision Consumption Point, treating any broker exception/malformed result as `DENY`-equivalent |
| `git push` dispatch | `push.py` (`run_push()` / `_run_push_staged_file_aware()`), unchanged |
| `git push` result handling | `push.py`, unchanged |
| Lifecycle/reporting after push | `push.py`'s existing `_reconcile_post_push()`, unchanged |

PBPC-REQ-039: The Permission Broker Foundation and `push.py`'s existing
readiness logic SHALL NOT both independently establish permission truth.
The broker owns the `POL-001..012`-representable questions (Section 8);
`push.py`'s existing readiness logic owns every other existing gating
condition, unchanged. A push SHALL be dispatched only when **both**
(a) the broker's decision is `ALLOW`, and (b) `push.py`'s existing
`readiness.ready` (or Path B's equivalent local checks) is satisfied — the
broker's `ALLOW` is necessary but, given Section 8's honest coverage
disposition, not by itself sufficient.

## 12. Production Consumption Boundary

PBPC-REQ-040: The Decision Consumption Point SHALL be positioned
immediately before each of Section 7's two dispatch sites, after all of
`push.py`'s existing readiness computation and after final pre-dispatch
validation (Section 17), per this ordering:

```
resolve operation (pcae push invoked, Path A or Path B selected)
      |
observe required state (existing assess_push_readiness / Path B checks)
      |
construct canonical PermissionBrokerRequest (Command Evidence Adapter)
      |
PermissionBroker.evaluate()
      |
validate decision binding/freshness (Section 15)
      |
ALLOW?
 |------------------|
 no                 yes
 |                   |
DENY / HUMAN_REVIEW  final pre-dispatch validation (Section 17)
 |                   |
stop, no push        AND existing readiness.ready still true?
                      |-------|
                      no      yes
                      |        |
                     stop   git push (existing dispatch call, unchanged)
```

PBPC-REQ-041: The exact insertion points a future implementation SHALL use
are `push.py:454` (before the Path A `subprocess.run(["git", "push"], ...)`
call) and `push.py:604` (before the Path B `subprocess.run(["git", "push",
"origin", "main"], ...)` call). This contract fixes the boundary's
position in the control flow; it does not itself insert code.

## 13. Canonical Push Operation Identity

PBPC-REQ-042: The minimum identity fields required to bind one broker
decision to one actual push operation, with traceable justification for
each, are:

| Field | Canonical source | Normalization | Absent behavior | Mismatch behavior | Freshness requirement | Security relevance |
|---|---|---|---|---|---|---|
| Repository root | `HarnessPath.cwd()` (existing) | absolute path | request construction fails closed | decision invalid | must match at dispatch time | prevents cross-repository replay |
| Local branch | `read_git_branch(root)` (existing) | as returned by git | request construction fails closed | decision invalid | must match at dispatch time | prevents cross-branch replay |
| Remote name | fixed `"origin"` (existing convention — both dispatch sites hardcode `origin`) | literal | n/a — always `"origin"` today | n/a | n/a | prevents remote substitution once a non-`origin` remote is ever introduced (out of scope today) |
| Local HEAD revision | `git rev-parse HEAD` (not currently captured by `assess_push_readiness`; a required new observation, not a new `PermissionRequest` field beyond `requested_resource`) | full SHA | request construction fails closed | decision invalid, re-evaluation required | must match immediately before dispatch (Section 16) | the central TOCTOU-relevant identity field |
| Unpushed commit count | `_count_unpushed_commits(root)` (existing) | integer | `0` is a valid, meaningful value (nothing-to-push) | decision invalid if it changed and is now nonzero where it was zero, or vice versa | must match at dispatch time | detects concurrent local commits between decision and dispatch |
| Active task ID | `find_latest_active_task(root)` (existing) | task-contract ID string or `None` | maps to `PermissionBrokerRequest.task_id=None`, triggering `POL-001` DENY | decision invalid if task changed | must match at dispatch time | the field `POL-001` evaluates |
| Push mode | `_determine_mode(...)` (existing: `nothing_to_push` / `active_task` / `post_finish_closure` / `not_ready`) | string enum | request construction fails closed if `not_ready` (no request is constructed — Section 19) | decision invalid if mode changed materially | must match at dispatch time | distinguishes routine push from post-finish-closure push |
| Force/non-force | fixed `False` for both existing dispatch calls (neither passes `--force`) | boolean | n/a | n/a | n/a | confirms this MVP never represents a force-push request; a future force-push consumer is out of scope |

PBPC-REQ-043: No field SHALL be added to this identity set without a
traceable reason recorded in this contract or a future amendment. This
contract does NOT authorize a general execution-intent schema — only the
fields listed above.

PBPC-REQ-044: Identity SHALL NOT be inferred from titles, recent Git
history, stale metadata, filenames, or report prose. Every field's
canonical source is a live, direct observation at request-construction
time (as listed above).

## 14. Request Construction

PBPC-REQ-045: The Command Evidence Adapter (Section 24, not built in
148B) SHALL translate `push.py`'s already-gathered readiness state
(Section 13) into a `PermissionBrokerRequest` using the existing
`build_permission_broker_request(...)` constructor
(`permission_broker_foundation.py:165-192`), unmodified.

PBPC-REQ-046: Required fields for a `pcae push` request: `action_type=
ACTION_PUSH`, `execution_class=EXECUTION_CLASS_MUTATION`,
`requested_component="COMP-001"`, `requested_capability="pcae_push"` (a new
string literal identifying the specific capability being requested, distinct
from the existing `"pcae_push_check"` used by the observation-only
touchpoint), `task_id` (Section 13), `evidence_available=True` (the
Evidence Adapter, by construction, never emits a request before readiness
evidence has already been gathered), `approval_present` (Section 11 of the
IWC boundary — see Section 21; for v1.0, `False` unless a future,
separately-governed mechanism supplies it), `simulation_only=True`
(Section 10.1).

PBPC-REQ-047: Optional field: `requested_resource` — MAY carry the target
ref (e.g. `"refs/heads/main"`) for diagnostic clarity; its absence SHALL
NOT change the decision, since no `POL-` rule currently inspects it.

PBPC-REQ-048: Prohibited fields: none beyond `PermissionBrokerRequest`'s
existing fixed dataclass shape (`permission_broker_foundation.py:141-162`)
— the Command Evidence Adapter SHALL NOT attach ad hoc extra data via any
mechanism (e.g. subclassing, monkey-patching, side-channel globals).

PBPC-REQ-049: `request_id` and `timestamp` SHALL be generated exactly as
`build_permission_broker_request` already generates them (`pbr-<uuid12>`,
UTC ISO-8601) — no alternate identity scheme is authorized.

PBPC-REQ-050: The request carries no separate "freshness" field; freshness
is enforced structurally by binding evaluation and dispatch within the same
synchronous CLI invocation (Section 16, Section 20) and by final
pre-dispatch validation (Section 17), not by a request-embedded expiry
value.

## 15. Decision Semantics

PBPC-REQ-051: `PermissionBroker.evaluate()` SHALL be called exactly once
per push attempt, producing one `PermissionBrokerDecision` for one fully
bound request, consistent with its existing deterministic, pure-function
contract (`permission_broker_foundation.py:744-787`).

PBPC-REQ-052: The Decision Consumption Point SHALL branch on
`decision.decision` using the existing three values only:
`DECISION_ALLOW` → proceed to final pre-dispatch validation (Section 17);
`DECISION_DENY` → abort, no `git push` attempted, `decision.decision_reason`
and `decision.matched_no_go_ids` surfaced (Section 18); `DECISION_HUMAN_REVIEW`
→ abort (Section 11 of Section 21 — v1.0 has no interactive resolution).

PBPC-REQ-053: This contract distinguishes a genuine policy `DENY` (a `POL-`
rule triggered and determined the decision, `decision.causing_policy_ids`
non-empty and traceable) from an evaluation failure that the Foundation
itself already routes to `DENY` via `_sanitize_result`
(`decision_reason="invalid_policy_result"`, `matched_no_go_ids=("NG-024",)`).
Both SHALL prevent push, but the Decision Consumption Point's diagnostic
output SHALL preserve `decision_reason` so an operator can distinguish
"policy denied this push" from "permission evaluation could not complete,"
consistent with the Foundation's own existing distinction — this contract
does not invent a new failure category, it surfaces the one the Foundation
already produces.

PBPC-REQ-054: `decision.reason_chain`, `decision.matched_component_ids`,
`decision.evaluated_policy_ids`, and `decision.precedence_reason` SHALL be
preserved unmodified through to any diagnostic surface (Section 18) — the
Decision Consumption Point SHALL NOT summarize, filter, or reinterpret
them.

## 16. TOCTOU Analysis

PBPC-REQ-055: Threats analyzed between broker decision and actual `git
push` dispatch: local HEAD mutation after decision; branch/ref mutation;
remote configuration mutation; refspec mutation; policy-state mutation
(not applicable — `POL-001..012` are code, not runtime-mutable
configuration); repository-state mutation generally; concurrent process
activity (out of scope — unchanged from today's single-agent-lock model,
Phase 148A §27); lower-level helper invocation (addressed, Section 9);
process crash/restart (Section 20); remote state changing independently
(cannot be transactionally controlled — see below).

PBPC-REQ-056: PCAE can transactionally bind, locally, immediately before
dispatch: local HEAD revision, local branch, unpushed-commit count, active
task ID, and push mode (all of Section 13's fields except remote name and
force/non-force, which are today fixed constants, not observed state).

PBPC-REQ-057: PCAE cannot transactionally bind remote Git state — a
concurrent push from elsewhere to `origin`, between this contract's
decision-consumption point and the local `git push` dispatch, is an
external race this contract does not and cannot close. This is an explicit
limitation, not a guarantee this contract makes. `git push`'s own
non-fast-forward rejection (already existing, unmodified git behavior)
remains the actual safety net for that specific race, unrelated to the
Permission Broker.

PBPC-REQ-058: The frozen guarantee is: **a broker decision must be bound to
the locally observable material identity of the intended push (Section 13)
immediately before dispatch; remote-state races that cannot be
transactionally locked remain an explicit, documented limitation, not a
closed guarantee.**

## 17. Final Pre-Dispatch Validation

PBPC-REQ-059: Immediately before each dispatch site (Section 12), a future
implementation SHALL re-observe: local HEAD revision, local branch,
unpushed-commit count, and active task ID (the four fields Section 16
identifies as locally, transactionally bindable).

PBPC-REQ-060: A mismatch between any re-observed field and the value bound
into the evaluated request SHALL constitute a material mismatch.

PBPC-REQ-061: On material mismatch: the existing `ALLOW` decision SHALL be
treated as invalid; no `git push` SHALL be dispatched using it; a fresh
request/evaluation cycle (Section 14/Section 15) SHALL be required before
any further dispatch attempt. This contract does NOT authorize silently
updating the bound operation underneath an existing decision.

## 18. Failure Ownership

PBPC-REQ-062: The following failure-ownership matrix is normative.

| Failure | Owner | Push allowed? | Diagnostic source | Retry/recovery owner | Audit expectation |
|---|---|---|---|---|---|
| Malformed request | Command Evidence Adapter (must not construct one); `PermissionBroker.evaluate()` structural check as defense-in-depth | No | `PermissionBrokerDecision.decision_reason="invalid_request_object"` | `push.py` command layer (surfaces error, user reruns) | logged as denial (148C-scoped persistence) |
| Missing required request field | Command Evidence Adapter | No (dataclass construction fails before reaching broker) | Python `TypeError` surfaced by `push.py` | `push.py` command layer | n/a — never reaches broker |
| Unsupported action/execution class | `PermissionBroker` (`POL-006`) | No | `decision_reason="unknown_action_type"` / `"unsupported_execution_class"` | not applicable (fixed constants, Section 10 — should never trigger for `pcae push`) | logged as denial |
| Missing policy | `PermissionBroker` (`_compose` empty-results branch) | No | `decision_reason="no_applicable_policy"` | not applicable (registry is fixed, non-empty) | logged as denial |
| Duplicate/ambiguous policy | `PermissionBroker` (`_compose` precedence rule) | Follows precedence outcome | `precedence_reason` | not applicable — deterministic | logged with full `reason_chain` |
| Policy parse/load failure | not applicable — `DEFAULT_POLICY_RULES` is a fixed, in-memory Python tuple, not parsed from external config | n/a | n/a | n/a | n/a |
| Broker evaluation failure (rule raises) | `PermissionBroker` (`_sanitize_result`) | No | `decision_reason="invalid_policy_result"` | `push.py` command layer | logged as denial |
| Broker `DENY` | `PermissionBroker` (sole authority) | No | `decision_reason`, `matched_no_go_ids` | operator resolves underlying condition, reruns `pcae push` | logged as denial |
| `HUMAN_REVIEW` | `PermissionBroker` | No (v1.0 has no resolution mechanism — Section 21) | `decision_reason="missing_human_approval"` | undefined in v1.0; deferred to a future phase | logged as review-required |
| Unknown broker result | Decision Consumption Point (treats as `DENY`) | No | synthetic diagnostic: "broker returned an unrecognized decision" | `push.py` command layer | logged as denial |
| Stale decision | Decision Consumption Point (Section 17) | No | "material mismatch; re-evaluation required" | operator reruns `pcae push` | logged as denial |
| Operation-binding mismatch | Decision Consumption Point (Section 17) | No | same as above | operator reruns `pcae push` | logged as denial |
| Repository observation failure (e.g. git command fails while gathering evidence) | `push.py`'s existing evidence-gathering functions, unchanged | No (existing behavior: readiness computation already fails safe today) | existing `push.py` diagnostics, unchanged | operator, unchanged | unchanged |
| Repository changed after decision | Decision Consumption Point (Section 17) | No | material-mismatch diagnostic | operator reruns | logged as denial |
| Remote resolution failure | `push.py`'s existing `git push` invocation (unchanged — this is a git-level failure, not a broker concern) | No (git itself fails) | existing `subprocess.CalledProcessError` handling, unchanged | operator, unchanged | unchanged |
| `git push` dispatch failure | `push.py`, unchanged | Push did not succeed | existing error handling (`push.py:462-471`), unchanged | operator, unchanged | unchanged |
| Uncertain `git push` outcome (e.g. process crash mid-dispatch) | `push.py` / underlying git, unchanged — Section 20 | Uncertain; not assumed successful | existing reconciliation logic (`_reconcile_post_push`), unchanged | operator + existing reconciliation, unchanged | unchanged |
| Post-push reporting failure | `push.py`'s existing `_reconcile_post_push`, unchanged | Push already happened; not retroactively revoked (PBPC-REQ-031) | existing reconciliation diagnostics, unchanged | existing lifecycle tooling, unchanged | unchanged |
| Lifecycle finalization failure | existing `_finalize_report_and_notify`, unchanged | Push already happened; not retroactively revoked | existing diagnostics, unchanged | existing lifecycle tooling, unchanged | unchanged |

PBPC-REQ-063: No failure category above SHALL be owned by more than one
component. Where a row's owner is "unchanged," this contract explicitly
declines to alter existing, already-correct failure ownership.

## 19. Diagnostics Contract

PBPC-REQ-064: A denied `pcae push` SHALL expose: that permission was not
granted; the decision value (`DENY`/`HUMAN_REVIEW`); `decision_reason`;
the triggering `POL-` rule ID(s) (`causing_policy_ids`); the operation
identity at the level of branch and unpushed-commit count (not raw
internal request fields); and, where deterministic and safe, a remediation
string already present in the existing `POL-` rules' output
(`required_remediation`, e.g. `POL-001`'s "Create and activate a task
contract (pcae task new)").

PBPC-REQ-065: Diagnostics SHALL NOT expose credentials, tokens, secret
environment values, private keys, sensitive remote credentials, full
secret-bearing remote URLs, or unnecessary internal configuration. No field
in `PermissionBrokerRequest`/`PermissionBrokerDecision` carries any such
value today, and the Command Evidence Adapter SHALL NOT introduce one.

PBPC-REQ-066: A policy `DENY` SHALL be diagnostically distinguishable from
"permission evaluation could not complete" wherever the Foundation's own
`decision_reason` already distinguishes them (Section 15, PBPC-REQ-053) —
the diagnostics layer SHALL NOT collapse this distinction for brevity.

## 20. Replay and Restart

PBPC-REQ-067: **Decision obtained, process crashes before push.** No git
mutation occurred (Section 7's dispatch always follows decision
consumption in the same synchronous call). On restart, the prior decision
is discarded (never persisted, Section 23); a fresh evaluation is required.

PBPC-REQ-068: **Local operation changes before push.** Per Section 17,
this is a material mismatch — the prior decision is invalid; a fresh
evaluation is required.

PBPC-REQ-069: **Push fails before remote mutation.** Retry requires
re-running `pcae push` from the top — full re-observation and a fresh
broker evaluation (unchanged from today's existing retry idiom: rerunning
`pcae push` after a failed attempt already re-executes
`assess_push_readiness()` from scratch).

PBPC-REQ-070: **Push succeeds, local result persistence fails.** This
SHALL NOT be treated as "push did not happen." A repeat `pcae push` SHALL
NOT be blindly attempted merely because local post-push evidence
(provenance event, phase-report reconciliation) is incomplete; this is
classified as an uncertain post-mutation state requiring reconciliation via
`push.py`'s existing `_reconcile_post_push`/finalization mechanisms
(unchanged by this contract), not as a Permission Broker concern.

PBPC-REQ-071: **Process crashes during `git push`.** Whether remote
mutation occurred SHALL NOT be inferred. Recovery SHALL NOT convert this
uncertainty into permission to replay; the existing `pcae push check`/
`pcae push` idempotent-rerun behavior (already correct: rerunning after an
actually-successful push reports `nothing_to_push`, confirmed live —
Section 2) is the existing, unchanged mechanism that safely resolves this
case without needing new Permission-Broker-specific replay semantics.

PBPC-REQ-072: **Identical retry.** An existing decision SHALL NOT be
reused across separate `pcae push` invocations. Each invocation SHALL
trigger a fresh evidence-gather → request-construct → evaluate → consume
cycle. This contract prefers deterministic safety over optimization and
does not authorize any decision-caching mechanism.

PBPC-REQ-073: This contract does NOT require or authorize any durable
replay-tracking artifact beyond what Section 23 assesses.

## 21. Confirmation Independence

PBPC-REQ-074: This contract SHALL NOT redefine Interactive Workflow
Confirmation, SHALL NOT create confirmation semantics, and SHALL NOT
consume confirmation as implicit permission — `pcae push` has no existing
Confirmation/Decision Session dependency today, and this contract does not
introduce one.

PBPC-REQ-075: Broker permission (`ALLOW`) SHALL NOT be treated as
equivalent to, or a replacement for, Confirmation. Confirmation SHALL NOT
be treated as equivalent to, or a replacement for, broker permission.

PBPC-REQ-076: `IWC-REQ-029` (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md:
1063-1065`: "No Decision Session state, before or after `Confirmed`, SHALL
be visible to, consumable by, or capable of triggering any runtime
capability change") is preserved unmodified. This contract introduces no
code path by which a Decision Session's state becomes visible to or
consumable by the Permission Broker, and no code path by which a
`PermissionBrokerDecision` becomes visible to or consumable by a Decision
Session. **No amendment to `IWC-REQ-029` is required**, and none is made by
this contract.

PBPC-REQ-077: `approval_present` on a `pcae push` request (Section 14)
SHALL NOT be sourced from any Decision Session or Confirmation state in
v1.0. It SHALL default `False` unless a future, separately-governed
mechanism is contracted to supply it — this contract does not authorize
any such mechanism today, consistent with Section 3's "no interactive
resolution mechanism beyond abort-and-report."

## 22. Authority Evaluation Independence

PBPC-REQ-078: Chapter 147's Authority Evaluation Model (`src/pcae/
authority_evaluation/`) and its integration layer (AESIC,
`src/pcae/aesic/`, governed by `docs/contracts/
AESIC-001-authority-evaluation-service-integration-contract.md`) remain
disclosure/citation-only, per their own frozen module docstrings ("never
grants, blocks, or conditions Confirmation, Readiness, Authorization, or
Publication").

PBPC-REQ-079: Authority Evaluation SHALL NOT create Permission Broker
permission, SHALL NOT be a push eligibility gate, SHALL NOT determine
`ALLOW`/`DENY`/`HUMAN_REVIEW`, SHALL NOT elevate capability, and SHALL NOT
authorize execution, under this contract.

PBPC-REQ-080: This contract does NOT introduce a new dependency on AESIC.
Direct inspection confirms current `push.py`/`permission_broker_foundation.py`
have zero references to `authority_evaluation`/`aesic`, and this contract
requires none be added. If Authority Evaluation is ever surfaced alongside
a push decision by a future phase, it SHALL remain disclosure-only,
following the existing `authority_evaluation.stage_1_omitted_on_confirm`
logging pattern (`src/pcae/commands/decision_session.py:698`) — never a
gating input.

## 23. Runtime Capability Boundary

PBPC-REQ-081: `PermissionBroker` `ALLOW` ≠ runtime capability elevation.
This contract does not modify runtime state, maximum capability, execution
availability, backend invocation availability, shell availability, or
generic mutation capability.

PBPC-REQ-082: Runtime remains **Observed / observe / unavailable** after
this contract is frozen, and after any future implementation conforming to
it, unless a separately authorized future phase explicitly changes runtime
posture (out of scope here).

PBPC-REQ-083: The apparent tension — `pcae push` already performs a real,
governed mutation while generic runtime execution remains unavailable — is
accurate and is not "resolved" by this contract. `pcae push`'s git-mutation
capability is a pre-existing, narrowly-scoped, command-specific capability
that predates and is independent of the generic runtime-plugin capability
model (`RuntimeEnforcementCoordinator`/`RuntimeEnforcementDecision`,
Section 25). This contract governs the former; it does not touch, extend,
or redefine the latter.

## 24. Durable Decision Artifact Assessment

PBPC-REQ-084: This contract evaluates, and selects, **Option A**: the
existing `PermissionBrokerDecision` object plus `push.py`'s existing
diagnostic output and provenance-event stream (unchanged) are sufficient
for v1.0. **No new durable canonical permission-decision artifact is
authorized by this contract.**

**Rationale.** Section 20's replay/restart analysis shows no scenario
requiring durable decision persistence to remain safe — the existing
provenance-event stream already records `pcae push` outcomes, and a
broker `DENY` that aborts a push produces the same "nothing happened"
state persistence already handles correctly today (Phase 148A §23,
independently confirmed). `src/pcae/core/enforcement_audit.py` exists as a
design-only, not-yet-consulted module; this contract does not require it
for v1.0 and does not wire it. A durable, replayable, per-decision audit
record — Option B — is identified as a **148C-scoped enhancement**
(auditability, not correctness), not required for this MVP to deliver
value, consistent with Phase 148A §23/§29. No artifact proliferation is
introduced by this contract.

## 25. Relationship to Runtime Enforcement

PBPC-REQ-085: The Runtime Enforcement Decision Engine
(`RuntimeEnforcementDecision`, Phase 102A) and Coordinator
(`RuntimeEnforcementCoordinator`, Phase 103A), both in `src/pcae/core/
backend_invocations.py`, are **orthogonal** to this contract. Direct
inspection confirms neither `push.py` nor `commit.py` imports or
references either class; both remain contract-complete, non-executing
dataclasses whose authorization fields are forced `False` by construction
(`simulation_only=True`, `design_only=True`), modeling *runtime-plugin*
invocation authorization — a different, broader problem domain than "should
this git push proceed."

PBPC-REQ-086: This contract SHALL NOT route `pcae push`'s Permission
Broker consumption through Runtime Enforcement. Runtime Enforcement is not
required for v1.0. This contract does not silently rewrite Phase 101–104
semantics, and no eventual dependency between them is asserted — if one is
ever needed, it is future work for a separately governed phase, not
implied or pre-authorized here.

## 26. Compatibility Review

PBPC-REQ-087: Compatibility classification against every relevant existing
contract/architecture:

| Predecessor | Classification |
|---|---|
| Permission Broker Foundation (Phase 108A-C, `POL-001..012`) | **Consumed, unchanged.** No `POL-` rule semantics modified. Any future `POL-013+` additions are additive, out of scope for v1.0. |
| Phase 109 command-path integration design (`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`) | **Additive dependency.** This contract fulfills exactly the `pcae push` integration point that design already anticipated ("Would construct a request with `action_type=push`"). |
| Runtime Enforcement Decision Engine / Coordinator (Phases 101-104) | **Compatible unchanged.** Orthogonal (Section 25); no amendment. |
| `HARD_BLOCK_REGISTRY` / legacy `permission_broker.py` | **Compatible unchanged.** Not consolidated, not modified (Section 6). |
| Task/phase lifecycle | **Compatible unchanged.** `POL-001`'s `task_id` binding reuses the exact existing active-task lookup `push.py` already performs. |
| Interactive Workflow Confirmation / `IWC-REQ-029` | **Compatible unchanged; no amendment required** (Section 21). |
| Authority Evaluation / AESIC-001 | **Compatible unchanged; not reopened** (Section 22). |
| Canonical finalization / phase reporting | **Compatible unchanged.** `pcae push`'s external contract (CLI surface, exit codes on the `ALLOW` success path) is preserved; new `DENY`/`HUMAN_REVIEW` exit paths are additive. Finding B-1 is CLOSED as of v1.2 (Section 8.1): the `ALLOW` path is now reachable by the canonical conformant request, independently re-confirmed this phase (Section 30A). |
| `push check`'s existing observation-only touchpoint (INT-004, Phase 109C) | **Compatible unchanged.** Remains scoped to `push check`; unaffected by this contract's `pcae push` consumption. |
| `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` (Phase 107E) | **Consumed, unchanged (added v1.1).** This contract's Git Approval / execution approval separation (PBPC-REQ-007A) and Finding B-1's diagnosis (Section 8.1) rest on this document's own frozen text; no amendment to it is made or needed. |
| PBPA-001 v1.0 (`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`, Phase 148C.3, added v1.2) | **Normative dependency (additive).** PBPC-001 depends on PBPA-001 for policy-applicability determination (PBPC-REQ-003A); it does not duplicate PBPA-001's matrix or predicate. PBPA-001 remains v1.0, unamended by this contract. |

PBPC-REQ-088: No amendment to any existing FROZEN contract is required or
made by PBPC-001 v1.1. (v1.0's Section 8/26/30 claims about `pcae push`
compatibility and "no Blocking finding" are corrected, not because any
*other* contract required amendment, but because those claims about
PBPC-001's own internal satisfiability were factually wrong — see
Section 8.1.)

## 27. Requirement Traceability and Implementation Acceptance Preconditions

PBPC-REQ-089: Every normative requirement in this contract traces to one
or more of: the Phase 148A architectural decision; the existing Permission
Broker Foundation contract (Phase 108A-C); an existing `POL-` requirement;
existing `pcae push` hard-block/readiness behavior; existing lifecycle
contracts; or a security/non-bypassability requirement independently
derived during this phase's reconstruction (Section 2). Sections 4–26 above
constitute this contract's traceability matrix; no requirement in this
document lacks a stated source.

PBPC-REQ-090: Before an implementation conforming to this contract may be
authorized, all of the following preconditions SHALL be independently
verified (148D, not this phase): complete `HARD_BLOCK_REGISTRY`/`POL-`
mapping (Section 8) confirmed unchanged from this contract's table; no
semantic drift; Foundation vocabulary reuse (no second taxonomy); ownership
consistency (Section 11); operation-identity sufficiency (Section 13);
non-bypassability design covering both Path A and Path B (Section 9);
fail-closed semantics; freshness/binding (Section 15-17); TOCTOU treatment
(Section 16); replay/restart (Section 20); failure ownership (Section 18);
diagnostics (Section 19); security (Section 28); capability separation
(Section 23); Confirmation independence (Section 21); Authority Evaluation
independence (Section 22); Runtime Enforcement compatibility (Section 25);
lifecycle compatibility (Section 26); no hidden policy expansion (Section
8's "no `POL-013+` added").

PBPC-REQ-091: A future implementation, once built, SHALL additionally
demonstrate: every real `pcae push` (both dispatch paths) crosses the
broker; all existing hard-block-like conditions retain their current
semantics (Section 8); no broker decision means no push; broker failure
cannot cause push; direct helper reuse cannot bypass enforcement (Section
9); stale/mismatched decisions cannot authorize a changed operation
(Section 17); `DENY` produces no push; `ALLOW` does not alter runtime
capability (Section 23); `ALLOW` does not prove execution; Confirmation
remains independent (Section 21); AESIC remains disclosure-only (Section
22); no new push restriction was introduced accidentally; diagnostics are
safe (Section 19); restart/replay behavior is deterministic (Section 20);
existing push behavior remains compatible for the common already-permitted
case (Section 30 operational note, Phase 148A); existing lifecycle/
reporting behavior remains correct; no execution capability is introduced.

## 28. Security Threat Model

PBPC-REQ-092: The following threats are analyzed and mitigated or
explicitly deferred.

- **Bypass — alternate push path.** Mitigated: Section 9 binds both known
  dispatch sites (Path A and Path B). No other dispatch site exists in
  `push.py` (confirmed by direct inspection, Section 7).
- **Bypass — direct helper invocation.** Mitigated: Section 9,
  PBPC-REQ-029 — no helper function independently dispatches `git push`.
- **Bypass — fallback execution.** Mitigated: PBPC-REQ-021.
- **Bypass — exception-based bypass.** Mitigated: PBPC-REQ-025,
  PBPC-REQ-021 (broker exceptions fail closed via `_sanitize_result` and
  the Decision Consumption Point's own fail-closed treatment).
- **Bypass — recovery bypass.** Mitigated: PBPC-REQ-030.
- **Bypass — test/debug bypass leaking into production.** Deferred to
  148D (implementation) — no test/debug flag exists in this contract; a
  future implementation SHALL NOT introduce one that skips the Decision
  Consumption Point.
- **Bypass — environment flag bypass.** Same as above — none authorized.
- **Bypass — stale cached decision.** Mitigated: PBPC-REQ-072 (no
  decision caching authorized).
- **Identity substitution — repository/branch/remote/ref.** Mitigated:
  Section 13, Section 17.
- **Identity substitution — phase/task/session.** Mitigated: `task_id`
  binding, Section 13/17.
- **TOCTOU — repository/configuration changes after evaluation.**
  Addressed with an explicit limitation for remote state (Section 16).
- **TOCTOU — concurrent local mutation.** Addressed by final
  pre-dispatch validation (Section 17); deferred for true multi-process
  concurrency (unchanged from today's single-agent-lock model).
- **Policy attacks — missing/duplicate/malformed policy.** Mitigated:
  existing `_compose`/`_sanitize_result` fail-closed behavior, unchanged
  and reused (Section 18).
- **Policy attacks — substitution/downgrade/unsupported version.** Not
  applicable — `DEFAULT_POLICY_RULES` is a fixed, versioned-by-code-review
  tuple, not runtime-configurable.
- **Diagnostic leakage — credentials, secrets, sensitive config.**
  Mitigated: Section 19 (PBPC-REQ-065).
- **Replay — stale decision reuse.** Mitigated: PBPC-REQ-072,
  Section 17.
- **Replay — cross-repository/branch/remote/operation.** Mitigated:
  Section 13's identity fields.
- **Authority confusion — Confirmation/Authorization/AESIC/capability/
  execution treated as permission, or vice versa.** Mitigated: Section 4
  (terminology), Section 21, Section 22, Section 23.
- **Capability leakage — PBPC enabling generic execution.** Not present:
  this contract's MVP scope is exactly `pcae push`'s existing capability
  (Section 3); no generic shell/backend/adapter dispatch is introduced.

## 29. Explicit Non-Goals

PBPC-REQ-093: PBPC-001 v1.0 does NOT: enable runtime execution; elevate
runtime capability; enable backend invocation; enable shell execution;
mediate arbitrary shell commands; govern arbitrary filesystem mutation;
integrate `pcae commit`; introduce automatic push authority; redefine human
authorization; redefine Interactive Workflow Confirmation; modify
`IWC-REQ-029`; make Authority Evaluation a permission gate; make AESIC
authoritative; create generic execution evidence; create multi-agent
execution; create Telegram inbound control; create remote shell; add
`/run`; create unrestricted command dispatch; implement Runtime Enforcement
changes; cut over lifecycle authority; modify CLTR authority; introduce new
`HARD_BLOCK_REGISTRY` or `POL-013+` policy; consolidate or remove the
legacy `permission_broker.py`; define a `HUMAN_REVIEW` interactive
resolution mechanism beyond "abort and report"; or implement any of the
above in production source.

## 30. Verdict and No-Go Confirmation

**v1.2 (Phase 148C.9) supersedes v1.1's verdict below.** Phase 148C
independently found, and Phase 148C.1 independently re-confirmed and
re-derived to root cause, one Blocking finding, B-1: `POL-004` evaluated
unconditionally on every `pcae push` request; `approval_present` was fixed
`False` (PBPC-REQ-046) with no authorized or legitimate mechanism to set
it `True` (Section 8.1); therefore no conformant `pcae push` request could
reach `ALLOW` under v1.1 of this contract. **Finding B-1 is now CLOSED.**
PBPA-001 v1.0 (Phase 148C.3, independently adversarially verified Phase
148C.4) amended the Permission Broker Foundation with an applicability
layer under which `POL-004` is not applicable to
`execution_class=EXECUTION_CLASS_MUTATION` requests (Section 8.1); Phase
148C.6 independently implemented this layer (verified Phase 148C.7); Phase
148C.8 independently adjudicated B-1 CLOSED by fresh, live re-execution of
the canonical PBPC push request against the unmodified Foundation; this
phase (148C.9) independently re-executed the same request (Section 30A) and
ratifies that closure in this contract's own normative text — this phase
did not itself discover the closure. **PBPC-001 v1.2 is classified
SATISFIABLE AND TEXTUALLY RECONCILED** (Section 30A, Section 30B). Findings
F-1 and F-2 (Section 5) remain classified OBSERVATION, unaffected. The
Section 8 coverage-gap disposition remains complete and ratified (Section
18) and the Section 7 two-dispatch-site finding remains NON-BLOCKING,
resolved normatively (Sections 9, 11). The 148C-scoped audit-persistence
deferral (Section 24) remains classified DEFERRED, re-evaluated and
ratified unchanged this phase (Section 30B), consistent with Phase 148A
§23/§29. Finding F-148C.8-1 (`simulation_only=False` → `POL-005` fail-closed
DENY) is classified EXPECTED_CONTRACT_BEHAVIOR, disposed in Section 10.1
(PBPC-REQ-037A) — not a defect, not repaired, not bypassed.

PBPC-001 governs only the existing `pcae push` production mutation path.
No production Permission Broker consumption was implemented during Phase
148B, 148C, 148C.1, or 148C.9. No new push permission policy was
introduced. Existing `HARD_BLOCK_REGISTRY`/readiness semantics remain the
policy source for every condition the Permission Broker Foundation does
not yet formally represent (Section 8, Section 18). Permission Broker
permission remains distinct from confirmation, authorization, runtime
capability, Git approval, and execution (Section 4, PBPC-REQ-007A).
Applicability remains distinct from decision (Section 8.1; PBPA-001 §4A).
Interactive Workflow Confirmation semantics, including `IWC-REQ-029`,
remain unchanged (Section 21). Authority Evaluation/AESIC remains
disclosure-only and does not create permission or push eligibility
(Section 22). Permission Broker `ALLOW` does not elevate runtime
capability and does not prove that push executed (Section 23) — and, with
B-1 now closed, is genuinely reachable by the canonical conformant
request, independently re-confirmed this phase (Section 30A), without that
reachability constituting execution, wiring, or authorization of any kind.
No generic shell, filesystem, backend, command-dispatch, or execution
capability was introduced (Section 29). Runtime remains Observed, maximum
capability remains observe, and execution availability remains
unavailable.

**PBPC-001 v1.2 is READY FOR IMPLEMENTATION PLANNING** (Section 30B):
B-1 is closed, stale prose is reconciled, no new Blocking finding was
introduced by this phase, the PBPA-001 dependency is coherent, simulation
semantics are coherent (Section 10.1), hard-block ownership wording is
precise and unchanged in substance (Section 18), and non-bypassability
requirements (Section 9) remain fully coherent and unweakened.

**148D (implementation planning) is still NOT recommended directly from
this phase.** Because this phase amends a frozen normative contract, a
dedicated independent contract-verification phase — **148C.10 —
Permission Broker Production Consumption Contract v1.2 Independent
Verification** — SHALL occur first, per this repository's established
adversarial-verification discipline (the same discipline PBPC-001 v1.0→
independent-verification and PBPA-001 v1.0→148C.4 both followed). 148C.10
is not pre-authorized by this contract; it requires its own separately
authorized task. See
`docs/PHASE_148C.9_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_V1_2_RECONCILIATION.md`
for the full reconciliation record.

### 30A. Independent Satisfiability Re-Verification (added, v1.2, Phase 148C.9)

PBPC-REQ-089A: This phase independently re-executed the live, unmodified
`PermissionBroker` (`src/pcae/core/permission_broker_foundation.py`,
unmodified by this phase) against three requests, fresh, not by citation of
148C.6/148C.7/148C.8's numbers:

| Test | Request shape | Result | Confirms |
|---|---|---|---|
| Canonical PBPC push request | `action_type=ACTION_PUSH`, `execution_class=EXECUTION_CLASS_MUTATION`, `approval_present=False`, `simulation_only=True`, `evidence_available=True`, `task_id` present | `decision=ALLOW`, `non_applicable_policy_ids=('POL-004',)`, `causing_policy_ids=()` | B-1 CLOSED; PBPC-001 v1.2 request shape reaches valid `ALLOW` for an otherwise eligible push state (contract satisfiability, not production wiring). |
| In-scope `POL-004` control | `execution_class=EXECUTION_CLASS_SHELL`, `approval_present=False` | `decision=HUMAN_REVIEW`, `causing_policy_ids=('POL-004',)` | `POL-004` retains unweakened `HUMAN_REVIEW` behavior for every request it still governs — the reconciliation did not weaken PBPA-001/`POL-004` semantics generally, only clarified applicability for `pcae push` specifically. |
| `POL-005` control | Canonical push request with `simulation_only=False` | `decision=DENY`, `causing_policy_ids=('POL-005',)`, `decision_reason=execution_boundary_unavailable` | Finding F-148C.8-1 (Section 10.1, PBPC-REQ-037A) independently reconfirmed; `simulation_only=True` remains the correct, load-bearing fixed value for `pcae push` requests. |

PBPC-REQ-089B: No new contradiction was found. **PBPC-001 v1.2 Satisfiability
Verdict: SATISFIABLE AND TEXTUALLY RECONCILED.**

### 30B. Implementation-Planning Readiness and Independent Verification Decision (added, v1.2, Phase 148C.9)

PBPC-REQ-089C: Implementation-planning readiness is evaluated against six
criteria, all satisfied: (1) B-1 closed (Section 8.1); (2) stale prose
reconciled (Section 30A, this phase's full diff — Section 34 of the
companion phase document); (3) no new Blocking finding introduced by this
phase (Section 30A; F-148C.8-1 disposed EXPECTED_CONTRACT_BEHAVIOR, Section
10.1); (4) PBPA-001 dependency coherent (Section 1, PBPC-REQ-003A; Section
26); (5) simulation semantics coherent (Section 10.1); (6) hard-block
ownership wording precise, unweakened, and not inflated (Section 18);
non-bypassability requirements (Section 9) remain fully unweakened. **Verdict:
READY FOR IMPLEMENTATION PLANNING.**

PBPC-REQ-089D: Because this phase amends a frozen normative contract, an
independent contract-verification phase is required before implementation
planning proceeds, following this repository's established discipline of
never accepting a contract's own reconciliation of itself as sufficient
(the same discipline every prior PBPC-001/PBPA-001 revision has followed).
**148C.10 — Permission Broker Production Consumption Contract v1.2
Independent Verification — is the required next phase, not 148D.** This
default applies even though the v1.2 changes are textual/reconciliation-only
— no repository precedent was found that permits skipping independent
verification for a frozen-contract amendment merely because the change is
narrow.

## 31. Phase 148B Freeze Confirmation

**Version:** 1.0
**Frozen by:** Phase 148B — Permission Broker Production Consumption
Contract Freeze
**Predecessor:** Phase 148A — Next Strategic Capability Architecture
(commit `658324c7`)

This freeze introduces no production source change. `git diff --name-only`
against the pre-148B baseline is limited to this contract file, the Phase
148B phase document, and governed task/status/changelog bookkeeping
artifacts (Section 32 confirms the exact list).

**148C — Permission Broker Production Consumption Contract Independent
Verification** is the recommended next governed phase. It shall
independently re-derive and adversarially attack PBPC-001 v1.0 — not
accepting this document's own claims as an oracle — specifically
challenging: `HARD_BLOCK_REGISTRY`/`POL-` semantic equivalence and the
Section 8 coverage-gap disposition; the Section 7 two-dispatch-site
finding and Section 9 non-bypassability design; the Section 10.1
`simulation_only=True` resolution of the `POL-005` misclassification risk;
replay and restart (Section 20); TOCTOU (Section 16); authority confusion
(Sections 4, 21, 22); capability leakage (Section 23); the Runtime
Enforcement compatibility claim (Section 25); and lifecycle compatibility
(Section 26). This recommendation is not authorization; 148C requires a
separately authorized task.

## 32. No Production Source Changes

PBPC-REQ-094: This phase's changes SHALL be limited to: this contract
file (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`);
the Phase 148B phase document (`docs/PHASE_148B_PERMISSION_BROKER_
PRODUCTION_CONSUMPTION_CONTRACT_FREEZE.md`); `PROJECT_STATUS.md`;
`CHANGELOG.md`; `tasks/DONE.md`; the active task contract; and finalization
artifacts (`.pcae/phase-completion-report.md`,
`.pcae/phase-completion-metadata.json`). No file under `src/pcae/**` SHALL
be modified by this phase. This SHALL be confirmed by `git diff --name-only
<pre-148B-baseline>..HEAD` before this phase is reported complete.

## 33. Version History

- **v1.0** (Phase 148B, commit `9200187b`). Initial freeze. Verdict: no
  Blocking finding (later shown incorrect).
- **v1.0, independently verified** (Phase 148C, commit `d45d9fd8`).
  Verification-only; no contract text changed. Found Finding B-1
  (Blocking) and two Non-Blocking findings (Section 8 traceability gap;
  `simulation_only=True` diagnostic-honesty observation). Recommended
  148C.1.
- **v1.1** (Phase 148C.1). Amends Section 4 (adds Git Approval/execution
  approval separation, PBPC-REQ-007A), Section 8 (corrects `POL-004`'s
  disposition; adds explicit "out of scope" rows for the 8 previously
  unnamed `HARD_BLOCK_REGISTRY` entries, closing the traceability gap;
  adds Section 8.1, Finding B-1 status), Section 26 (corrects
  compatibility claims), and Section 30 (corrects the verdict to
  disclose B-1). **Does not close Finding B-1** — see
  `docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`
  for the full repair-category analysis and the reasons Categories A and
  B were foreclosed. No `POL-001..012` rule was modified; no
  `src/pcae/**` file was modified. Recommended next phase: 148C.2 —
  Permission Broker Foundation Policy Applicability Model Design (a
  design phase, not pre-authorized here).
- **v1.2** (Phase 148C.9, PBPA-aware reconciliation after B-1 closure).
  Ratifies Finding B-1 CLOSED (adjudicated by Phase 148C.8, not
  discovered by this phase). Amends: Section 1 (adds PBPC-REQ-003A,
  normative dependency on PBPA-001 v1.0); Section 8 (`POL-004` row
  updated to reflect PBPA-001 non-applicability rather than universal
  evaluation); Section 8.1 (rewritten: closure lineage, PBPA-001
  dependency, applicability-vs-decision clarification,
  `evaluated_policy_ids` semantics reconciled to PBPA-001 §26); Section
  10.1 (adds PBPC-REQ-037A, disposes Finding F-148C.8-1 as
  EXPECTED_CONTRACT_BEHAVIOR, clarifies simulation truthfulness); Section
  18 (ratifies PBPC-REQ-018's existing permission-bearing-vs-mechanical
  distinction against Phase 148C.8's hard-block reconstruction, without
  reclassifying any hard block); Section 26 (adds PBPA-001 compatibility
  row; updates finalization-compatibility row to reflect `ALLOW`
  reachability); Section 30 (verdict rewritten: B-1 CLOSED, PBPC-001 v1.2
  classified SATISFIABLE AND TEXTUALLY RECONCILED and READY FOR
  IMPLEMENTATION PLANNING); adds Section 30A (independent satisfiability
  re-verification — three fresh control evaluations against the live
  unmodified Foundation) and Section 30B (implementation-planning
  readiness verdict and independent-verification-next-step decision).
  **Introduces no new permission semantics, no new `POL-` policy, no
  weakening of `POL-004`/`POL-005`, no runtime capability change, and no
  `src/pcae/**` modification.** No `POL-001..012` rule was modified.
  PBPA-001 remains v1.0, unamended. Recommended next phase: 148C.10 —
  Permission Broker Production Consumption Contract v1.2 Independent
  Verification (not 148D) — see
  `docs/PHASE_148C.9_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_V1_2_RECONCILIATION.md`.
