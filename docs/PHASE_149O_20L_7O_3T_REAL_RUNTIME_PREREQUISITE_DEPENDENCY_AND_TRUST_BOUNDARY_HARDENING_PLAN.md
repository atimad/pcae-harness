# Phase 149O.20L.7O.3T — Real-Runtime Prerequisite Dependency and Trust-Boundary Hardening Plan

**Status: READ-ONLY STRATEGIC PLANNING PHASE — COMPLETE.**
**PRODUCTION SOURCE MODIFIED: NO. EXECUTION ACTIVATED: NO. RUNTIME REMAINS Observed / observe / unavailable.**

## 1. Objective

Produce an evidence-derived dependency graph and hardening plan for the
transition from the currently-verified production dry adapter consumer
(`pcae session bootstrap --compact --dry-runtime --runtime-target <id>`,
established by Phase 149O.20L.7O.3S.2 and independently verified by
149O.20L.7O.3S.2.1) to a future human-authorized real-runtime dispatch,
**without implementing or activating real execution**. This phase
identifies: all remaining RPAC-001 real-runtime prerequisites; their
dependency ordering; current implementation/trust state; contract gaps;
authority gaps; security/trust gaps; the first prerequisite that must be
resolved; and the smallest safe sequence toward a first real adapter.
Strict semantic distinctions are preserved throughout: `registered !=
configured != authenticated != available != capable != permitted !=
authorized != dispatched != executing != completed != accepted by PCAE`.
This phase plans these transitions; it does not collapse them.

## 2. Baseline

Verified at phase entry (2026-08-27, agent `claude-3t`):

- `git status --short`: clean.
- `git status --branch --short`: `## main...origin/main` (no ahead/behind).
- `git rev-list --count origin/main..HEAD`: `0`.
- `git rev-parse HEAD` == `git rev-parse origin/main` ==
  `c7037b388bf5ea0f0713f6e534689816e9c4885b`.
- `git rev-parse v0.4.3^{commit}` == `63580893b1de4782a694ab802ff7bdebdf29b0e6`
  — unchanged from the last released version.
- `pcae health`: healthy; active task was the idle placeholder
  `20260827-0750-idle-awaiting-human-decision-post-149o-20l-7o-3s-2-1`
  (not a mid-phase task — closed cleanly at phase start, not clobbered).
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings, all pre-existing `tasks/DONE.md`
  synchronization debt across many prior phases (37+ historical entries),
  none attributable to this phase.
- `pcae push check`: clean, nothing to push.
- `pcae runtime inspect`: `not_implemented` / `Observed` / `observe` /
  `unavailable`; registry empty, 0 plugins, 0 capabilities.
- Telegram notification sink: configured, enabled, outbound-ready.
- `pcae phase-report show --latest`: 149O.20L.7O.3S.2.1, completed,
  report complete, recommending exactly this phase.

All Step 1 preconditions held: clean repository, zero ahead of
origin/main, v0.4.3 unchanged, runtime unchanged, no genuine active
governed phase before startup.

## 3. Verified production dry state

RPAC-001 v1.0 (frozen at Phase 149O.20L.7O.3Q,
`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`) mock/dry adapter
state: **IMPLEMENTED, VERIFIED, PRODUCTION-CONSUMED.** Production entry
point: `pcae session bootstrap --compact --dry-runtime --runtime-target
<id>`. Independent verification (149O.20L.7O.3S.2.1) established:
explicit two-part opt-in (`--dry-runtime` + exact `--runtime-target`, no
fallback on 10 tested unknown/case/whitespace/typo/identity/provider-name
variants); Permission Broker (PB) simulation-only, any real
(non-simulation) request unconditionally denied by POL-005; a permissive
fake enforcement evaluator cannot override a forced PB DENY; 0 runtime
subprocess attempts, 0 network/provider calls, 0 provider credential
reads, 0 runtime source mutations in the pure RPAC-consuming call path;
ordinary bootstrap output byte-for-byte unchanged; Runtime Enforcement
never activated as real authority; `pcae runtime inspect` verdict
`TRUTHFUL_WITH_LIMITATION` (no field is false, but the dry consumer's
transient per-call registry is structurally disconnected from the
persisted registry `runtime inspect` queries). **Real-runtime readiness:
NO.**

## 4. The 16 real-runtime prerequisites

Source: `docs/PHASE_149O_20L_7O_3R_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_IMPLEMENTATION_PLAN.md`
line 93 ("Counts: 52 MOCK-V1-MANDATORY, 16 REAL-RUNTIME-PREREQUISITE, ...")
classified exactly these 16 RPAC-001 requirement IDs as
`REAL-RUNTIME-PREREQUISITE`. Exact normative wording below is quoted
verbatim from `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
(RPAC-001 v1.0, the canonical public contract).

1. **RPAC-REQ-014** — "Configuration SHALL contain references, not
   credential values. Environment-variable names alone are not a
   credential-reference abstraction." *(§4, contract line 124.)*
2. **RPAC-REQ-028** — "Provider/model values resolved from target
   configuration SHALL be snapshotted in the request when known. A
   mismatch at dispatch SHALL fail closed; an adapter SHALL NOT silently
   switch provider, model, endpoint, or target." *(§6, line 215.)*
3. **RPAC-REQ-044** — "The existing Permission Broker action/execution-class
   vocabulary (`adapter_invocation`/`backend_invocation`; `adapter`/
   `backend`) is a useful starting point but insufficient for RPAC dispatch
   because its request does not bind target, adapter, prompt digest,
   repository, effects, network/filesystem, credentials, budget, or
   idempotency. That contract gap SHALL be closed in a separate future
   phase without changing policy in 3Q." *(§9, line 334.)*
4. **RPAC-REQ-045** — "Runtime Enforcement SHALL be the final
   whether-to-invoke gate, after human approval, target facts, and
   Permission Broker permission, and before any adapter effect. The
   current evidence-only, non-authorizing, zero-consumer implementation
   SHALL NOT be treated as that future gate." *(§9, line 341.)*
5. **RPAC-REQ-046** — "Runtime Enforcement SHALL evaluate the complete
   bound request, all effect-specific permission decisions,
   target/status freshness, repository/task/HEAD freshness, approval
   validity, and no-go evidence. A positive decision SHALL expire and
   SHALL be single-attempt scoped." *(§9, line 346.)*
6. **RPAC-REQ-047** — "Runtime Enforcement determines whether invocation
   may happen. Shell Gate or an equivalent local process policy
   constrains how a local command is constructed/launched. Neither
   substitutes for the other." *(§9, line 351.)*
7. **RPAC-REQ-048** — "For a local CLI adapter, fixed argv SHALL receive
   adapter-specific validation plus enforcing process policy. Any shell
   text, expansion, pipeline, or `shell=True` form SHALL require an
   enforcing Shell Gate/equivalent; because today's Shell Gate is
   simulation-only and non-intercepting, such real dispatch is forbidden
   now." *(§9, line 355.)*
8. **RPAC-REQ-057** — "A local CLI target SHALL define a resolved/pinned
   executable, fixed argv construction without shell interpolation,
   repository-bound cwd, sanitized allowlisted environment, prompt
   transfer method, output limits, finite timeout, process-group/tree
   ownership, termination escalation, cancellation behavior, exit-status
   mapping, platform profile, filesystem and network confinement, and
   result normalization." *(§11, line 405.)*
9. **RPAC-REQ-058** — "A local adapter SHALL NOT inherit the full PCAE
   process environment. Credential values SHALL be resolved just in
   time by a future secret resolver, exposed only to the narrow child
   context, omitted from records, and redacted from captured output."
   *(§11, line 412.)*
10. **RPAC-REQ-059** — "An API/provider target SHALL define
    provider/endpoint identity, TLS/egress policy, opaque credential
    reference, request/response schema, finite connection and total
    timeouts, rate-limit handling, cancellation, ambiguous-delivery
    handling, output limits, usage/cost collection, and result
    normalization." *(§11, line 417.)*
11. **RPAC-REQ-071** — "Retryable classes MAY include unavailability
    before dispatch, rate limiting with confirmed non-acceptance,
    transient transport failure with confirmed non-delivery, and timeout
    before the effect boundary. Unknown delivery, runtime mutation,
    malformed conflicting completion, and ambiguous process termination
    SHALL NOT retry automatically." *(§13, line 477.)*
12. **RPAC-REQ-072** — "Every retry requires a new attempt ID, fresh
    capability/status, fresh Permission Broker and Runtime Enforcement
    decisions, and human authorization when the prior approval's attempt
    limit/expiry does not cover it. A changed prompt, target,
    provider/model, repository/task, effects, or budget requires a new
    logical invocation and approval." *(§13, line 483.)*
13. **RPAC-REQ-084** — "Credentials SHALL never be embedded in
    descriptors, requests, results, audit records, prompts, diffs, or
    repository configuration. PCAE has no adequate general
    credential-reference/resolution implementation today; that is an
    explicit blocker for a real authenticated adapter." *(§16, line 561.)*
14. **RPAC-REQ-086** — "Adapter code and descriptors are supply-chain
    inputs. Future admission SHALL pin implementation identity/digest
    and fail closed on drift; an adapter SHALL not mutate its own
    descriptor or status evidence during an attempt." *(§16, line 570.)*
15. **RPAC-REQ-095** — "The first post-mock process-bound implementation
    SHOULD be a generic, fixed-argv external executable adapter tested
    with a deterministic non-AI fixture. The first named AI target
    SHOULD then be an explicit Codex CLI RuntimeTarget — not
    `codex-local`/`codex-ox` identity inference — after process
    supervision, credential, PB, Runtime Enforcement, and Shell Gate
    dependencies are independently satisfied. Claude-local and API
    providers follow the same contract and receive no legacy-path
    exemption." *(§17, line 618.)*
16. **RPAC-REQ-097** — "All existing public legacy invocation paths
    remain historical execution surfaces, not RPAC-conformant adapters.
    Before any real activation, they SHALL be retired, disabled, or
    routed through one RPAC-conformant kernel and SHALL not be
    grandfathered as alternate dispatch authorities." *(§19, line 634.)*

Owner/source for all 16: RPAC-001 v1.0 (`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`),
classified by the 3R implementation plan
(`docs/PHASE_149O_20L_7O_3R_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_IMPLEMENTATION_PLAN.md`).

## 5. Prerequisite classification

| Req | Classification(s) |
|---|---|
| RPAC-REQ-014 | IMPLEMENTATION GAP + CONTRACT GAP (no credential-reference abstraction exists anywhere in `src/pcae`) |
| RPAC-REQ-028 | PARTIALLY SATISFIED (mock adapter never switches provider/model by construction; real snapshot/fail-closed compare logic does not yet exist) |
| RPAC-REQ-044 | CONTRACT GAP (PB request shape does not bind target/adapter/prompt-digest/effects/credentials/budget/idempotency — confirmed directly: `PermissionBrokerRequest` in `src/pcae/core/permission_broker_foundation.py` lines 142-162 has only `action_type`, `execution_class`, `task_id`, `phase_id`, `requested_component/capability/resource`, `evidence_available`, `approval_present`, `simulation_only`) |
| RPAC-REQ-045 | AUTHORITY GAP + IMPLEMENTATION GAP (0 production consumers of Runtime Enforcement; it is explicitly "design-only, non-executing, non-authorizing" per its own docstrings) |
| RPAC-REQ-046 | IMPLEMENTATION GAP (no expiring, single-attempt-scoped decision object exists in production) |
| RPAC-REQ-047 | CONTRACT GAP (the Runtime Enforcement/Shell Gate division of labor is stated in contract prose only; no code enforces or even represents this split today) |
| RPAC-REQ-048 | TRUST-SECURITY GAP + UNSTARTED (Shell Gate is confirmed simulation-only/non-intercepting — see §24; real dispatch is explicitly "forbidden now" by the contract's own text) |
| RPAC-REQ-057 | UNSTARTED (no local-CLI target descriptor fields exist for any of the 13 named properties) |
| RPAC-REQ-058 | UNSTARTED + EXTERNAL-ENVIRONMENT DEPENDENCY (no sanitized child-environment mechanism, no secret resolver) |
| RPAC-REQ-059 | UNSTARTED (no API/provider target descriptor exists) |
| RPAC-REQ-071 | UNSTARTED (no retry engine exists; mock adapter explicitly has none per 3R) |
| RPAC-REQ-072 | UNSTARTED + AUTHORITY GAP (retry-reauthorization semantics require the same missing human-authority artifact as §11/§43) |
| RPAC-REQ-084 | TRUST-SECURITY GAP (explicitly named by the contract itself as "an explicit blocker for a real authenticated adapter") |
| RPAC-REQ-086 | UNSTARTED (no adapter admission/supply-chain-pinning mechanism exists; only the mock descriptor is pinned, by construction, not by a general mechanism) |
| RPAC-REQ-095 | UNSTARTED but DECISION-BEARING (states the intended sequencing itself — used directly in §29/§61/§62) |
| RPAC-REQ-097 | CONTRACT GAP + IMPLEMENTATION GAP (legacy invocation paths — e.g. `pcae phase agent-invoke`/`activated-task-agent-*` command family under `pcae phase --help`, seen at baseline — have not been inventoried, retired, or routed through the RPAC kernel in this phase; inventory itself is future work) |

No prerequisite is fully "SATISFIED" — all 16 remain either unstarted,
partially satisfied only by mock-adapter absence-of-violation, or an
explicit named gap.

## 6. Dependency graph

Evidence-derived, not assumed. Edges below are load-bearing dependencies
found directly in contract text and code structure, not merely a
plausible ordering:

- RPAC-REQ-044 (PB request-shape amendment) is a **prerequisite of**
  RPAC-REQ-045/046 (Runtime Enforcement cannot evaluate "all
  effect-specific permission decisions" if PB cannot express them) and of
  RPAC-REQ-072 (retry needs "fresh Permission Broker ... decisions" over
  the same enriched shape).
- RPAC-REQ-045/046 (Runtime Enforcement becoming a real gate) is a
  **prerequisite of** RPAC-REQ-047/048 (Runtime Enforcement must exist
  as a real "whether" gate before the "how" gate — Shell Gate — has
  anything to compose with) and of RPAC-REQ-095 (first real adapter needs
  a real final gate before it, per RPAC-REQ-029/045 chain).
- RPAC-REQ-048 (Shell Gate becoming enforcing) is a **prerequisite of**
  RPAC-REQ-057 (local CLI target definition is meaningless without an
  enforcing process boundary to bind it to) and gates the entire Local
  CLI chain (§28).
- RPAC-REQ-084 (credential-reference architecture) is a **prerequisite
  of** RPAC-REQ-058 (local adapter secret injection), RPAC-REQ-059 (API
  credential reference), and RPAC-REQ-014 (config references need
  something to reference).
- RPAC-REQ-014 depends on RPAC-REQ-084 (the reference abstraction must
  exist before configuration can reference it).
- RPAC-REQ-028 depends on RPAC-REQ-057/059 (provider/model snapshot
  comparison needs a real target descriptor to snapshot from).
- RPAC-REQ-086 (supply-chain/executable pinning) is a **prerequisite of**
  RPAC-REQ-057 (a "resolved/pinned executable" cannot exist until pinning
  exists) — parallel-able with RPAC-REQ-084 (independent concerns).
- RPAC-REQ-071/072 (retry taxonomy/reauthorization) depend on
  RPAC-REQ-045/046 (Runtime Enforcement must be real before "fresh
  Runtime Enforcement decisions" on retry means anything) and on the
  human-authority artifact identified as missing in §11/§43.
- RPAC-REQ-097 (legacy path retirement) can run **in parallel** with
  everything above — it is an inventory/decommission task independent of
  the new-capability build-out, but is a **hard precondition of "any real
  activation"** per its own text (must complete before real dispatch is
  turned on, not before design work).
- RPAC-REQ-095 (first adapter class + sequencing) is the **terminal
  node** — it can only be exercised once RPAC-REQ-044/045/046/047/048/
  057/058/084/086 are all satisfied for the local-CLI chain.

**Parallelizable now (design/contract work, no shared blocking edge):**
RPAC-REQ-044 (PB contract), RPAC-REQ-084 (credential-reference
architecture design), RPAC-REQ-086 (supply-chain/pinning design), and
RPAC-REQ-097 (legacy-path inventory) can all begin independently.
**Strictly serial:** RPAC-REQ-044 → RPAC-REQ-045/046 → RPAC-REQ-047/048
→ RPAC-REQ-057 → RPAC-REQ-095.

## 7. First hard blocker

**Confirmed independently (not assumed): PB dispatch-permission
semantics, specifically POL-005 (`ExecutionDisabledRule`).** Read
directly from `src/pcae/core/permission_broker_foundation.py` lines
489-518:

```
class ExecutionDisabledRule(PolicyRule):
    """POL-005 — Execution Disabled.

    A real (non-simulation) execution attempt always denies: no execution
    boundary exists yet (COMP-002 not_implemented). Unconditionally
    active by construction (NG-025).
    """
    policy_id = "POL-005"
    ...
    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        if request.simulation_only:
            return _not_triggered(self.policy_id)
        return PolicyResult(..., decision=DECISION_DENY,
                             decision_reason="execution_boundary_unavailable", ...)
```

This rule declares no `applicable_execution_classes` override (unlike
e.g. the approval rule at line 459), so its inherited `applies_to()`
(line 383-392: `self.applicable_execution_classes is None or
request.execution_class in self.applicable_execution_classes`) returns
`True` unconditionally for every `execution_class` — matching the
docstring's claim of unconditional activation. **This is the earliest
prerequisite whose absence makes every later prerequisite meaningless**:
no matter how thoroughly RPAC-REQ-057/058/059/084/086 are satisfied, a
real (non-`simulation_only`) request reaches POL-005 and is denied
before any effect boundary is reached. It is upstream of every other
gap in the dependency graph (§6).

## 8. POL-005 deep dive

- **Action/class matched:** none specifically — `applicable_execution_classes`
  is unset (`None`), so the rule applies to every `execution_class`
  (`none`, `mutation`, `shell`, `backend`, `adapter`, `rollback`) and
  every `action_type`, contingent only on the `simulation_only` flag.
- **Simulation distinction:** binary. `request.simulation_only: bool =
  True` (default, `PermissionBrokerRequest` line 162). If `True`, POL-005
  is not triggered (`_not_triggered`); if `False`, POL-005 unconditionally
  denies.
- **Why real invocation is denied:** the rule's own `decision_reason`,
  `"execution_boundary_unavailable"`, and docstring: "no execution
  boundary exists yet (`COMP-002` not_implemented)." This is a
  structural absence, not a policy preference — there is no code path
  anywhere that could satisfy a real dispatch request today.
- **Intentional temporary safeguard:** yes. `required_remediation` reads:
  "No execution boundary exists today. This gate cannot be satisfied
  until a future phase implements and verifies COMP-002." The rule
  documents its own future removal condition (`COMP-002` becoming
  implemented and verified), not a permanent prohibition.
- **What historical architecture expected:** `COMP-002` ("Execution
  boundary") is referenced as a named, tracked component that a future
  phase is expected to implement — consistent with the 148-series
  Permission Broker Foundation phases that first introduced POL-005 as
  part of a deliberately execution-disabled foundation.
- **Existing real-dispatch action:** none. `KNOWN_ACTION_TYPES`
  (`permission_broker_foundation.py` lines 100-118) includes
  `ACTION_ADAPTER_INVOCATION = "adapter_invocation"` and
  `ACTION_BACKEND_INVOCATION = "backend_invocation"`, but every request
  built via `build_permission_broker_request()` defaults
  `simulation_only=True`; nothing in the current source ever constructs
  a request with `simulation_only=False` in a production path (confirmed
  by the 3S.2.1 verification's live instrumentation finding 0 real
  requests).
- **Can policy already represent bounded runtime dispatch?** Partially.
  The `simulation_only` boolean is a coarse, all-or-nothing gate — it
  cannot yet express "bounded" dispatch (e.g., permit adapter invocation
  but not network egress, or permit local-CLI but not API-provider). The
  richer effect vocabulary needed for that already exists one layer up,
  in the *design-only* `RuntimeEnforcementEvidenceBundle`
  (`backend_invocations.py` — see §44), which already declares
  `adapter_execution_authorized`, `network_authorized`,
  `subprocess_authorized`, `shell_authorized`, `mutation_authorized`,
  etc. as separate booleans, but that structure is not consumed by PB
  and is itself non-authorizing by construction (every one of those
  fields is asserted `False` in its own `validate()`).

## 9. PB action vocabulary

Read directly from `src/pcae/core/permission_broker_foundation.py`:

- `action_type` values (lines 94-118): `read`, `source_mutation`,
  `docs_mutation`, `test_mutation`, `commit`, `push`, `rollback`,
  `shell_command`, `backend_invocation`, `adapter_invocation`.
- `execution_class` values (lines 120-134): `none`, `mutation`, `shell`,
  `backend`, `adapter`, `rollback`.

Runtime dispatch would most naturally map to `action_type =
"adapter_invocation"` / `execution_class = "adapter"` — both already
exist. However, per RPAC-REQ-044, this existing pairing is **structurally
insufficient**: it carries no target/adapter identity, prompt digest,
repository binding, effect list (network/filesystem/process), credential
reference, budget, or idempotency key. It is best classified as an
**existing execution action that is a starting point but requires a
composite-request amendment**, not a wholly new action type by itself —
though a genuinely new *effect-scoped* action family (network, process,
filesystem-mutation-by-runtime) may be needed alongside it (see §42).

## 10. Real dispatch semantics

What PB would be permitting, disambiguated (none of the following are
interchangeable):

- **Permission to invoke the adapter object** (call `adapter.dispatch()`)
  — an in-process/library boundary.
- **Permission to start an external process** — a local CLI runtime
  effect, gated by RPAC-REQ-048/057/058 and Shell Gate.
- **Permission to contact a provider over the network** — an API/network
  effect, distinct from process start, gated by RPAC-REQ-059/084.
- **Permission to allow repository mutation** — an entirely separate
  effect from invocation itself; already has its own PB action_types
  (`source_mutation`, `docs_mutation`, `test_mutation`).
- **Permission to allow network egress generically** — currently has
  **no** PB action_type or execution_class at all (confirmed: no
  "network" string anywhere in `permission_broker_foundation.py` except
  in a docstring at line 12 describing what the broker is *not* aware
  of).

These five are separable concerns today only by convention/prose, not by
distinct machine-checkable PB permissions. RPAC-REQ-085 ("Network,
subprocess, shell, filesystem mutation, outside-repo access, paid usage,
and provider selection SHALL each be explicit and default denied. One
granted effect SHALL not imply another.") is the contract's own
requirement that these be kept separate — this phase's finding is that
**no implementation yet backs that separation.**

## 11. PB scope

Evidence supports: PB's proper scope should be "may PCAE attempt this
class of external effect at all?" — a coarse, structural permission —
**not** "is this specific execution authorized?" The latter question
belongs to a chain of Runtime Enforcement (fresh, bound, single-attempt)
plus explicit human authorization, per RPAC-REQ-045 ("Runtime Enforcement
SHALL be the final whether-to-invoke gate, after human approval, target
facts, and Permission Broker permission"). This preserves: PB ALLOW !=
human authorization != runtime capability != Runtime Enforcement ALLOW.
Today PB collapses everything to a single `simulation_only` bit, which is
consistent with "may PCAE attempt this class at all" (answer: no, not
yet) but cannot yet answer the finer-grained question once the answer
becomes "yes, for some class."

## 12. Human authority

Search performed across `docs/contracts/`, `src/pcae/schema_resources/`,
and `src/pcae/core/`. Findings:

- **CHGR (Canonical Human Governance Record, CHGR-001 v1.0):** schema
  and artifact-representation foundation only. Its own README
  (`src/pcae/schema_resources/chgr/README.md`) states explicitly: "Not
  implemented here or by any code that consumes these schemas:
  interactive decision workflows, substantive decision capture, human
  confirmation UX, production create/confirm/publish/... commands, ...
  runtime consumption, or authority resolution." And: "Successful schema
  validation means only that an artifact conforms to the CHGR
  representation contract. It does not establish that the represented
  governance act was valid, applicable, current, or performed by an
  authorized human." No runtime-invocation authorization semantics exist
  here.
- **Interactive Workflow Confirmation (IWC):** explicitly disclaimed as
  approval evidence. `docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`
  RWMPC-REQ-023 (line 311): "Confirmation is not approval. Interactive
  Workflow Confirmation, task-finish health/check validation, and any
  other process-hygiene confirmation artifact SHALL NOT populate
  `approval_present`, regardless of which operation needs approval.
  Authority Evaluation / AESIC results SHALL NOT be treated as permission
  or approval evidence — AESIC remains disclosure-only."
- **`approval_present` field** on `PermissionBrokerRequest`: exists as a
  boolean, but no current production caller sets it `True` from any
  runtime-invocation-specific human act; it is consumed today only by the
  `ApprovalRequiredRule` (line ~470) for a generic "missing human
  approval" gate unrelated to runtime dispatch.
- **Phase/session approvals:** the governed phase lifecycle
  (`pcae phase start`/`complete`) records human-driven phase transitions,
  but nothing in it is scoped to "this specific external runtime
  invocation is authorized."

**Verdict: no existing PCAE artifact cleanly authorizes real runtime
invocation. Classified CONTRACT/AUTHORITY GAP** (per instruction, no
approval semantics are invented here).

## 13. Prompt approval vs invocation authority

RWMPC-REQ-023 (§12) draws exactly this line: content-level "confirmation"
(a human reading/accepting prompt content or a workflow state) is
explicitly barred from ever populating `approval_present`. Today's
architecture has **only the first half** (a Confirmation/IWC concept for
workflow state acceptance) and **not the second half** (an
execution-attempt authority artifact). No code path currently derives
"external execution authorized" from any prompt-acceptance signal, which
is correct per RWMPC-REQ-023, but it also means the second half must be
built new — it cannot be adapted from the first.

## 14. Runtime Enforcement

Read directly from `src/pcae/core/backend_invocations.py` (lines
9887-10450, Phase 103A/101B-derived types):

- **Current input contract:** `RuntimeEnforcementCoordinator` consumes
  an evidence-bundle reference/digest and a decision-artifact
  reference/digest (both design-only dataclasses), not a live RPAC
  invocation request.
- **Current output vocabulary:** a closed enum of statuses
  (`REC_STATUS_*`: `unavailable`, `not_started`,
  `input_collection_failed`, `evidence_bundle_unavailable`,
  `decision_unavailable`, `prerequisites_failed`, `blocked`, `denied`,
  `fail_closed`, `ready_for_design_review_only`) and results
  (`REC_RESULT_*`, all `denied`/`fail_closed`/`blocked_by_*`/
  `evidence_only`/`design_review_only` — there is no "granted" or
  "authorized" terminal state at all).
- **Can it evaluate a real adapter invocation today?** No.
  `RuntimeEnforcementEvidenceBundle.validate()` (lines ~10225-10250)
  hard-asserts `execution_available` must be `False`,
  `execution_authorized` must be `False`, `push_authorized` must be
  `False`, `simulation_only` must be `True`, `no_execution` must be
  `True`, `design_only` must be `True` — the type is
  self-enforcing-non-authorizing by construction, and 0 production
  consumers call it (confirmed by the 3S.2.1 verification's call-graph
  reconstruction, which never touches this module).
- **Does an RPAC invocation request map cleanly?** Not yet — the
  evidence bundle's vocabulary (`adapter_execution_authorized`,
  `network_authorized`, `subprocess_authorized`, `shell_authorized`,
  `mutation_authorized`, `commit_authorized`, `push_authorized`) is
  encouragingly fine-grained and closely mirrors the effect distinctions
  RPAC-REQ-085 requires, but the bundle has no field for RPAC's
  target/adapter/prompt-digest/attempt-lineage concepts. **Contract
  evolution is required**, but the vocabulary shape suggests reuse
  (extend, don't replace) is architecturally viable.

## 15. Gate ordering

Normative candidate sequence, derived from RPAC-REQ-002 (canonical future
flow), RPAC-REQ-045 (Runtime Enforcement as final gate after human
approval/target facts/PB), and RPAC-REQ-047/048 (Shell Gate constrains
"how", not "whether"):

1. Prompt preparation
2. Explicit target selection (already exists: `--runtime-target`)
3. Target capability/status preflight (static descriptor check)
4. Explicit human authorization (new artifact — §12/§43)
5. Permission Broker permission (real, non-simulation request; §7-§11)
6. Runtime Enforcement final gate (§14, evaluating the complete bound
   request)
7. Process/network containment (Shell Gate for local CLI; egress
   mediation for API — §23-§26)
8. Durable pre-dispatch invocation state persisted (§18/§47)
9. Adapter dispatch (the actual effect boundary)
10. Result capture (untrusted; §30)
11. Generic/Stage-B intake (existing, unmodified consumer; §31-§32)

This matches RPAC-REQ-029's "only the trusted kernel SHALL mint a
DispatchEnvelope after all [prior gates]" framing.

## 16. Capability ordering

Capability (can this target even execute) should be checked **both**
before and after PB: a static descriptor-level check (RPAC-REQ-011:
"immutable descriptive facts") should run early to avoid asking a human
to authorize a target that structurally cannot execute (e.g. missing
executable, unpinned descriptor) — but RPAC-REQ-012 explicitly forbids
descriptors from carrying "live availability, current authentication, or
dispatch state," so a **live preflight** must also run immediately before
dispatch, after PB/Runtime Enforcement, to catch drift (executable
removed, credential revoked) between authorization and dispatch — this
is also required by the TOCTOU analysis (§48).

## 17. Runtime availability semantics

Before `execution_availability = available` can ever be truthfully
reported, all of the following must be true simultaneously (derived from
RPAC-REQ-015/016 and the current registry's status model — §17 below):
COMP-002 (execution boundary) implemented and verified; POL-005 able to
allow at least one bounded real-dispatch action class; a real
non-mock adapter registered and its descriptor pinned (RPAC-REQ-086); the
target authenticated where required (RPAC-REQ-014/084); Runtime
Enforcement able to issue a real (not just `denied`/`blocked`) decision;
Shell Gate enforcing (for local CLI) or network egress policy present
(for API). `pcae runtime inspect` itself is **not** modified this
phase, per Step 16's explicit instruction.

## 18. Runtime status model

Read directly from `src/pcae/core/runtime_registry.py` lines 108-116:
the frozen `LIFECYCLE_STATES` are `defined`, `registered`, `configured`,
`healthy`, `available`, `disabled`, `failed`, `retired`. This
vocabulary can represent *configured* and, loosely, *healthy*/*available*,
but **cannot represent**: *authenticated* (no such state — credential
status is entirely absent from the model, consistent with RPAC-REQ-084's
gap), *executable* (distinct from generically "available"), *blocked by
policy* (no state reflects a PB/POL-005 denial — the registry is
explicitly metadata-only per its own comment: "registry never computes
or polls health"), or *blocked by missing trust prerequisite*. **Gap
identified: the registry's `LIFECYCLE_STATES` enum requires extension
(or a companion status axis) before it can truthfully represent the
finer distinctions real-runtime readiness needs.** This is itself
consistent with RPAC-REQ-016 ("Runtime status SHALL NOT contain or imply
human approval, Permission Broker permission, Runtime Enforcement
authorization, or actual dispatch") — the *current* narrowness is by
design, not oversight, but it will need principled widening (new,
clearly-separated fields, not overloading existing ones) to report
policy-blocked/trust-blocked states without violating RPAC-REQ-016's own
non-implication rule.

## 19. Invocation persistence/recovery

Read directly from `src/pcae/core/runtime_invocation.py`
(`RuntimeInvocationStore`, lines 835-970+): writes go through
`_write_create_only`, which writes a `.tmp` sibling then
`Path.replace()`s it into place — atomic on POSIX; `path.exists()` is
checked before write (no silent overwrite). Request record is written
first (`create_request_record`), then one event document per gate
transition, then `result.json`/`intake-handoff.json` only after full
acceptance. This is a reasonable foundation for durability but:
**before-dispatch durability** exists (request record persists before
any gate runs); **after-dispatch uncertainty** is entirely unaddressed —
there is no "dispatch attempted, outcome unknown" intermediate state
anywhere in the schema; **replay/duplicate execution**: `create_request_record`
is idempotent on identical `(invocation_id, idempotency_key)` and raises
`InvocationIntegrityError` on conflicting reuse (fail-closed) — but this
is evaluated only at the *request* layer, not at the *dispatch* layer,
because no dispatch layer exists yet. **Required hardening before real
dispatch:** an explicit "dispatch attempted" durable marker written
*before* the process/network call, separate from "result captured"
(needed for §20's exactly-once analysis), and (§26 finding) path-traversal
sanitization of `invocation_id` at the store layer (MUST-FIX #2, §41).

## 20. At-most-once analysis

Three crash windows, analyzed per the instruction's own framing:

- **Record persisted → process not started:** recoverable — on restart,
  PCAE can see a request record with no "dispatch attempted" marker and
  safely conclude no external effect occurred; a fresh attempt can be
  authorized.
- **Process started → PCAE crashes before recording dispatch:** this is
  the dangerous window. If "dispatch attempted" is not durably recorded
  *before* the process/network call (today it is not, because no
  dispatch layer exists), a restart cannot distinguish "attempted but
  crashed immediately" from "never attempted" — risking a duplicate
  external effect (e.g., a duplicate paid API call or duplicate local
  side-effecting command) on retry.
- **Process completed → result not captured:** also dangerous — external
  effect happened but PCAE has no record of the outcome; a naive retry
  would duplicate the effect.

**Desired guarantee: at-most-once dispatch attempt per authorized
invocation, with retry requiring fresh authorization (§21) rather than
automatic replay** — the instruction is correct that **exactly-once
cannot be honestly claimed** for local-process or network dispatch
without cooperation from the external side (idempotency keys the
provider itself honors, or process supervision guaranteeing at most one
live child). This phase does **not** claim exactly-once anywhere.

## 21. Retry authority

Per RPAC-REQ-072 (quoted in full at §4.12): retry after **uncertain**
execution (the §20 dangerous windows) SHALL require fresh human
authorization whenever "the prior approval's attempt limit/expiry does
not cover it," and unconditionally requires a new logical invocation if
prompt/target/provider/model/repository/task/effects/budget changed.
Failure classes, per RPAC-REQ-071: **retryable** — pre-dispatch
unavailability, rate-limiting with confirmed non-acceptance, transient
transport failure with confirmed non-delivery, timeout strictly before
the effect boundary; **not retryable automatically** — unknown delivery,
runtime mutation, malformed/conflicting completion, ambiguous process
termination. This taxonomy already exists in contract text; it has no
implementation yet (RPAC-REQ-071 is itself one of the 16 prerequisites).

## 22. Process supervision

For a future local CLI runtime, mandatory supervision capabilities
(derived from RPAC-REQ-057, cross-checked against current code — none of
these exist in `src/pcae` today, confirmed by absence of any
`subprocess.Popen`/process-group code in the runtime-adapter modules):
process ownership (PCAE must be the direct parent, not a shell
intermediary); PID/process-tree tracking (to find and terminate
descendants); a finite timeout; explicit cancellation (SIGTERM then
escalation); signal handling; bounded stdout/stderr capture; exit-status
mapping to RPAC's failure taxonomy (§13 of the contract); detached
descendant detection/cleanup (§37); and crash cleanup (orphan process
reaping). **Hard blockers before any local CLI dispatch:** process
ownership, timeout, and detached-descendant containment — without these
three, RPAC-REQ-057 cannot be satisfied at all and a hung or orphaned
process is an unbounded resource/security risk.

## 23. Environment isolation

Required controls, mapped against what exists: **cwd binding** —
`RPAC-REQ-057` requires "repository-bound cwd"; the mock/dry consumer
already derives HEAD/repo facts from the real repository (per 3S.2's
`resolve_dry_consumer_context`), so the pattern for binding exists but is
not yet wired to a real child process. **env allowlist** — no
implementation found (`RPAC-REQ-058`: "SHALL NOT inherit the full PCAE
process environment"); nothing sanitizes environment today because
nothing spawns a real child yet. **secret injection** — depends entirely
on the still-missing credential-reference abstraction (§26/§13).
**filesystem scope / temporary directory** — no runtime-specific
sandboxing exists; PCAE's existing git-worktree-based isolation patterns
(used elsewhere in the codebase for disposable verification, per the
3S.2.1 and 3K reports' own worktree-based baseline techniques) are a
plausible reusable building block but are not wired to runtime dispatch.
**PATH/executable resolution** — RPAC-REQ-057 requires a "resolved/pinned
executable," which is unimplemented; naive PATH lookup would violate
RPAC-REQ-086 (supply-chain pinning).

## 24. Shell Gate dependency

Read directly from `src/pcae/core/shell_gate.py` (module docstring,
lines 1-6): "Shell gate prototype — read-only command classifier (Phase
88P). Classifies proposed shell commands and returns a structured gate
decision. **Never executes command text. Never grants authorization.**"
This is corroborated by RPAC-REQ-048's own text: "today's Shell Gate is
simulation-only and non-intercepting[;] such real dispatch is forbidden
now." **Classification: MANDATORY** for any local CLI adapter that
constructs shell text, expansion, pipelines, or `shell=True` forms (per
RPAC-REQ-048's explicit language); for a fixed-argv-only adapter with no
shell interpretation at all, Shell Gate's specific command-classification
function may not be the load-bearing control, but an **equivalent
enforcing process-construction policy is still MANDATORY** — RPAC-REQ-047
states "Shell Gate **or an equivalent** local process policy," so the
dependency is on the *function*, not necessarily the *named component*.

## 25. Filesystem containment

Minimum containment before allowing a runtime to modify repo state,
ranked from most to least restrictive, evidence-derived from existing
PCAE patterns (worktree-based disposable verification already used in
prior phases, e.g. 3S.2.1's and 3K's own sibling-repo/worktree probes):
(A) **isolated worktree** — reuses PCAE's own already-proven
`git worktree` pattern for disposable, observable isolation; lowest new
implementation cost since the pattern already exists elsewhere in this
repository's verification methodology. (B) **external temporary
checkout** — stronger isolation, higher implementation cost (no clean
reuse of existing patterns). (C) **same worktree under PCAE
observation** — lowest isolation, only appropriate once (A)/(B) are
proven unnecessary for a specific narrow adapter class. (D) **OS-level
sandbox/confinement** — strongest, but out of scope for a first real
adapter (external tooling dependency, platform-specific). **Recommendation
for the smallest safe first step: (A), isolated worktree**, because it
reuses an already-verified PCAE technique rather than inventing a new
containment primitive.

## 26. Network policy

For API/provider runtimes: network egress currently has **no PB action
or execution_class at all** (§9/§10 — confirmed absent from
`KNOWN_ACTION_TYPES`/`KNOWN_EXECUTION_CLASSES`). This must become an
explicit, separately-denied-by-default PB action per RPAC-REQ-085 ("Network...
SHALL each be explicit and default denied. One granted effect SHALL not
imply another."). Allowlisted domains/endpoints and proxy mediation are
unimplemented; no code references TLS/endpoint pinning anywhere in
`src/pcae/core/`. The **local CLI adapter case requires no network PB
action at all** if the executable itself makes no network calls —
this is the basis for recommending local CLI as the lower-trust-complexity
first target (§29/§62).

## 27. Credential-reference architecture

Searched `src/pcae/` and `docs/contracts/` broadly for
`credential_reference`/`CredentialReference`: the term and concept exist
**only in contract prose** (`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`,
RPAC-REQ-014/058/059/084) — **no implementation exists anywhere in
`src/pcae`.** There is no "provider account" or "local CLI authenticated
session" abstraction either. **Classified: hard dependency (missing
entirely).** RPAC-REQ-084 states this outright: "PCAE has no adequate
general credential-reference/resolution implementation today; that is an
explicit blocker for a real authenticated adapter." No secret access was
performed in confirming this (absence was confirmed by grep, not by
reading any credential value).

## 28. Provider/model identity

RPAC-REQ-006/007/008 (already frozen, not among the 16, but load-bearing
here) establish that `agent_id != runtime_target_id != provider_id`
must remain distinct, and RPAC-REQ-028 (one of the 16) requires
provider/model values to be "snapshotted in the request when known" with
fail-closed mismatch detection — **explicitly not derived from
runtime-returned claims alone.** The minimum trusted source for
provider/model/adapter-target identity must therefore be **PCAE-owned
configuration** (a `RuntimeTargetConfiguration`, per RPAC-REQ-013), never
a value the adapter or the invoked process reports about itself at
dispatch time — this is directly corroborated by the 3S.2.1 provenance-
spoofing tests, which proved the mock adapter's
`adapter_id` is fixed regardless of caller-supplied `agent_id`, precisely
because identity is never trusted from caller/runtime-reported values.

## 29. Local CLI vs API

Separate prerequisite chains, evidence-derived from RPAC-REQ-057 vs
RPAC-REQ-059's disjoint requirement sets:

**Local CLI chain:** RPAC-REQ-048 (Shell Gate/process policy) →
RPAC-REQ-057 (executable/argv/cwd/env/timeout/process-tree) →
RPAC-REQ-058 (env sanitization/secret injection) → process supervision
(§22) → filesystem containment (§25).

**API/provider chain:** RPAC-REQ-059 (endpoint/TLS/credential
reference/timeouts/rate-limits) → RPAC-REQ-084 (credential reference,
shared with local) → network policy (§26, unique to API) → cost/budget
governance (§53, unique to API).

**Shared blockers:** RPAC-REQ-044 (PB request shape), RPAC-REQ-045/046
(Runtime Enforcement real gate), RPAC-REQ-084 (credential-reference
architecture — local CLI needs it too per RPAC-REQ-058), RPAC-REQ-086
(supply-chain pinning), human authorization (§12).

**Unique to local CLI:** Shell Gate/process-construction enforcement
(§24), process supervision (§22), detached-process risk (§37).

**Unique to API:** network egress PB action (§26), TLS/endpoint pinning,
rate-limit/cost handling, provider-response-provenance trust (§52).

Local CLI has strictly fewer unique blockers and — critically — can be
satisfied **without ever needing a network PB action at all** for a
no-network local executable, making it the lower-trust-complexity chain.

## 30. First adapter class

Ranked by trust complexity (lowest first) and architecture value,
per the instruction to rank, not merely follow user interest:

1. **Generic local executable (fixed-argv, non-AI, deterministic
   fixture)** — lowest trust complexity: no credential resolution, no
   network policy, no provider-response-provenance question, exercises
   the *entire* process-supervision/containment/Shell-Gate chain in
   isolation from AI-specific concerns. This is also **exactly what
   RPAC-REQ-095 itself recommends** ("The first post-mock process-bound
   implementation SHOULD be a generic, fixed-argv external executable
   adapter tested with a deterministic non-AI fixture").
2. **Codex CLI** (named explicitly in RPAC-REQ-095 as the first *AI*
   target, "after process supervision, credential, PB, Runtime
   Enforcement, and Shell Gate dependencies are independently
   satisfied" — i.e., only after step 1's chain is proven).
3. **Claude-local** — contract-parity with Codex CLI, "no legacy-path
   exemption" (RPAC-REQ-095).
4. **API/OpenRouter-style provider** — highest trust complexity (adds
   the entire network/credential/cost chain of §26/§27/§53); ranked
   last by risk even though it may have high strategic value.

This ranking is not based on user interest in any particular provider —
it is derived directly from RPAC-REQ-095's own explicit sequencing
recommendation plus the chain-length analysis in §29.

## 31. Result capture

Contract needed for: stdout/stderr (bounded, captured, redacted per
RPAC-REQ-058); structured result (`RuntimeInvocationResult`, which
already exists in `src/pcae/core/runtime_invocation.py` for the mock
case and would need extension for real results — changed files, exit
status, partial failure, model response, patch); all of it must remain
**untrusted** per RPAC-REQ-084 (no credentials in results) and the
general PCAE principle (confirmed structurally: `build_intake_handoff`
never calls the actual ingest/acceptance entry point — §32) that no
adapter output is ever self-authorizing.

## 32. Generic intake

Read directly from the 3S.2.1 verification report (independently
confirmed): "Stage-B candidate builder is invoked on every
accepted dry invocation" via `build_intake_handoff` →
`build_intake_candidate_from_changes`, but `build_intake_handoff`'s body
"never references `validate_and_ingest_intake_candidate` (the actual
acceptance/ingest entry point) anywhere in its bytecode." **Existing
Stage-B/generic intake CAN consume a real adapter result today without
additional trust-contract evolution for the evidence-production half**
(it already produces intake-compatible evidence from any
`RuntimeInvocationResult`-shaped object) — but the **acceptance half**
(actually calling `validate_and_ingest_intake_candidate`) is a
deliberately separate, human/governance-gated step that this phase
finds **no evidence has been wired to any runtime path**, dry or real.
If a runtime mutates the worktree directly (rather than producing
file-based output PCAE ingests), this bypasses the evidence-only
intake-handoff pattern entirely — **file-based/patch-based intake is the
preferred return path**, since it composes cleanly with the existing
untrusted-evidence-only Stage-B builder without requiring the runtime to
have direct worktree-mutation trust.

## 33. Mutation containment strategies

Ranked options for where a real adapter is allowed to touch the filesystem,
consistent with §25's recommendation:

| Option | Description | Safety | Implementation cost |
|---|---|---|---|
| (A) Isolated worktree | Adapter runs in a disposable `git worktree` bound to the same repository identity; results ingested via generic intake as file/patch data | High — reuses PCAE's own already-verified worktree-isolation technique (used by 3S.2.1/3K's own sibling-repo probes); native git diff tooling preserved | Medium — lowest cost of the high-safety options since the pattern is already proven elsewhere in this repository |
| (B) External temporary checkout | Files produced entirely outside any git worktree structure, ingested purely as patch/content data | High, arguably highest (zero worktree-identity risk) | Medium-high — loses native git-diff ergonomics |
| (C) Same worktree under PCAE observation | Adapter operates directly in the authoritative working tree | Lowest — direct write access to governed source; conflicts with RPAC-REQ-082's scope-broadening prohibition if the adapter has any defect or is compromised | Lowest |
| (D) OS-level sandbox/confinement | Container/namespace confinement layered under (A) or (B) | Highest when combined with (A); adds no additional intake-compatibility benefit alone | Highest |

**Ranking: (A), then (D) layered on (A), then (B), then (C) last.** (A) is
recommended as the minimum viable choice (§62) because it reuses an
already-proven PCAE technique at the lowest added cost while remaining
compatible, unmodified, with the existing Stage-B generic-intake return path
(§32); (C) is explicitly the weakest option given RPAC-REQ-082's
anti-scope-broadening invariant. This phase does not implement any option;
only ranking is produced.

## 34. Runtime-produced change trust model

Explicit chain, preserved without collapsing: **runtime produced file**
(raw adapter output) `!=` **trusted source** (no code trusts adapter
output structurally, confirmed at §31) `!=` **accepted change**
(requires `validate_and_ingest_intake_candidate`, confirmed never called
by the runtime path at §32) `!=` **authorized commit** (requires the
existing, separate governed-phase commit/push lifecycle this very phase
is itself using). Existing intake/review/promotion gates
(Canonical Artifact Promotion & Quarantine Hardening, 114A-114R per
`pcae phase-report show --latest`'s architecture history) remain fully
intact and unmodified by this phase; a real adapter's output would need
to flow through exactly these same gates, not a new parallel path.

## 35. Human review

Mandatory human boundary after a first real adapter completes: intake
review (existing Stage-B review path, unmodified), diff inspection
(standard `git diff` review before any commit, already how every
governed phase in this repository operates — including this one), phase
review (the existing `pcae phase complete` finalization gate), and
promotion authorization (existing quarantine/promotion framework). **No
existing review step is removed or weakened by this plan** — the
recommendation is that a first real adapter's output enters exactly this
same human-reviewed pipeline, with no new auto-accept path.

## 36. Cancellation

**Local CLI:** SIGTERM first, escalate to SIGKILL after a bounded grace
period if the process tree does not exit; timeout enforcement is
mandatory (RPAC-REQ-057). **API:** client-side cancellation (closing the
connection/aborting the request) may not stop the provider from
completing or billing the request server-side — this must be recorded
as an explicit semantic distinction (RPAC-REQ-071's "confirmed
non-acceptance" vs. "unknown delivery" taxonomy already captures this:
an API cancellation lands in the "unknown delivery, SHALL NOT retry
automatically" bucket unless the provider confirms non-acceptance).

## 37. Detached/background process risk

**Mandatory before any local CLI execution.** No process-group/session
containment exists anywhere in `src/pcae` today (confirmed: no
`os.setsid`/`process_group`/`preexec_fn` usage found in the runtime
modules). Without it, a spawned child could fork a detached grandchild
that outlives PCAE's own timeout/cancellation logic entirely — silently
continuing to run, write files, or make network calls after PCAE
believes the invocation is cancelled or timed out. Required containment
evidence before real dispatch: process-group ownership at spawn time,
and a verified test that killing the tracked PID terminates the entire
process tree (not just the direct child).

## 38. Threat-model refresh

| Threat | Current exposure |
|---|---|
| Malicious prompt/context | Not yet exposed — no real dispatch exists; prompt content already flows through existing untrusted-content handling patterns |
| Provider compromise | Not yet exposed — no provider is contacted |
| Arbitrary shell/tool behavior | Would be fully exposed the moment Shell Gate is bypassed or non-enforcing — currently blocked entirely by POL-005 |
| Filesystem escape | Same-worktree execution today has zero adapter-specific containment; §25 recommends isolated worktree as first mitigation |
| Network exfiltration | No network PB action exists yet (§26) — must be built before any API adapter, and even before a local CLI adapter that might itself make network calls |
| Credential leakage | No credential-reference architecture exists (§27) — cannot leak what is never resolved; this is also why no real adapter can be authenticated yet |
| Process escape (detached descendants) | Unmitigated — see §37 |
| Result spoofing | Mitigated architecturally by treating all adapter output as untrusted (§31/§34); not yet exercised for a real (non-mock) adapter |
| Replay/duplicate execution | Partially mitigated at the request layer (idempotency key, §19); unmitigated at the dispatch layer (§20) |
| Cost abuse | No budget/cost-governance mechanism exists yet (§53) |

## 39. Existing-control reuse matrix

| Concern | Existing PCAE control | Reusable? | Gap |
|---|---|---|---|
| Authorization gating | Permission Broker (POL-005 et al.) | Yes, as the base — needs request-shape amendment (RPAC-REQ-044) | Coarse `simulation_only` bit only |
| Final invocation gate | Runtime Enforcement (design-only) | Yes, vocabulary partially reusable (§14) | 0 production consumers; input contract needs RPAC binding |
| Process-construction policy | Shell Gate (simulation-only classifier) | Yes as the intended function, per RPAC-REQ-047/048 | Never intercepts — classification only |
| Hardware/identity trust boundary | HATP/Class-B | Not directly — scoped to hardware credential enrollment, no runtime-dispatch overlap found | N/A — different problem domain |
| Task/phase authority | Governed task/phase lifecycle (this phase's own mechanism) | Yes as the *human-decision-required* wrapper around any future phase that builds real dispatch | No task-scoped invocation-authorization primitive exists within it |
| Human governance record | CHGR-001 (schema-only) | Partially — representation shape reusable; no authority-resolution logic | Explicitly disclaims runtime consumption (§12) |
| Generic intake | Stage-B intake-candidate builder + `validate_and_ingest_intake_candidate` | Yes, unmodified (§32) | Acceptance half never wired to any runtime path yet |
| Invocation evidence | `RuntimeInvocationStore` (atomic writes, §19) | Yes as the persistence foundation | No "dispatch attempted" pre-effect marker; no path-traversal sanitization (MUST-FIX #2) |
| Runtime registry | `RuntimeRegistry`/`LIFECYCLE_STATES` | Yes as the descriptor/metadata layer | Cannot represent authenticated/blocked-by-policy states (§18) |
| Backend preflight | `backend_invocations.py` evidence-bundle types | Yes, fine-grained effect vocabulary is a good design reference for PB/RE amendment (§9/§14) | Entirely design-only; 0 consumers |

## 40. 3S.2.1 MUST-FIX findings recovered

Recovered verbatim from `docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md`
§63 ("Findings", "BLOCKING: 0", "MUST-FIX: 2"):

**Finding 1 — Malformed adapter result crashes uncaught instead of
failing closed cleanly.** "`simulate_invocation` (`runtime_adapter.py`
line ~501) calls `store.write_result(...)` on whatever
`adapter.collect()` returns, without validating it is a
`RuntimeInvocationResult` first; a non-conforming return value (e.g. a
plain `dict`) raises an uncaught `AttributeError` inside
`RuntimeInvocationStore.write_result` (`runtime_invocation.py` line
~923) rather than producing a `FAILURE_MALFORMED_RESULT`
`SimulationOutcome`." Affected surface: `runtime_adapter.py`'s
`simulate_invocation` / `runtime_invocation.py`'s `write_result`.
**Why unreachable now:** "`_run_with_context` only ever instantiates
`MockDryRuntimeAdapter()`, which always returns a well-formed
`RuntimeInvocationResult`; this gap only matters for a future, non-mock
adapter implementation." **What future phase makes it reachable:** any
phase that registers a second, non-mock adapter (i.e., §29's first
real-adapter phase). **Becomes BLOCKING before real runtime:** yes —
this is precisely the failure path a real (imperfect, external) adapter
would exercise; must be repaired before or as part of the first real
adapter implementation, not after. **Required repair ordering:** before
the first real adapter is registered, not before contract/authority work
begins.

**Finding 2 — `RuntimeInvocationStore` does not sanitize `invocation_id`
against path traversal.** "`_invocation_dir`/`_write_create_only` join
the raw `invocation_id` string onto the store root with no
normalization or confinement check; a crafted ID (e.g. containing
`../../..`) resolves completely outside
`.pcae/runtime-invocations/mock-v1/`, demonstrated directly against the
store." Affected surface: `runtime_invocation.py`'s
`RuntimeInvocationStore._invocation_dir`/`_write_create_only`. **Why
unreachable now:** "both public entry points" (the production dry-runtime
CLI path) "never let a caller choose `invocation_id`" — it is always
`new_invocation_id()`-generated internally (confirmed independently by
this phase reading `runtime_invocation.py` lines 54-57: `f"inv-{uuid.uuid4().hex}"`).
**What future phase makes it reachable:** any future surface that
accepts a caller-supplied or externally-derived `invocation_id` (e.g., a
resume/retry API, or a future runtime-invocation admin command).
**Becomes BLOCKING before real runtime:** not strictly required before
the *first* real adapter (which still only uses internally-generated
IDs), but MUST be repaired before any surface is added that accepts an
externally-influenced `invocation_id`. **Required repair ordering:**
before any such surface is introduced; may be bundled with the general
persistence-hardening work of §19 rather than gating the very first
real adapter.

**Neither finding is lost or reclassified here** — both remain
non-blocking to the *already-shipped* dry consumption path, but this
phase records that Finding 1 becomes a de facto blocker specifically at
the point a second (real) adapter is registered, while Finding 2 remains
non-blocking until a caller-influenced `invocation_id` surface is added.

## 41. Runtime inspect limitation disposition

`TRUTHFUL_WITH_LIMITATION` (per 3S.2.1, §3 above) must be repaired
**before the first real adapter is registered** — not before release,
not "after adapter registration." Rationale: once a real adapter exists,
an operator relying on `pcae runtime inspect` to understand what
capabilities are live needs the dry/real distinction to be
*discoverable*, not merely *not false*; leaving the transient-registry
disconnect unrepaired past the first real adapter would mean the tool
that is supposed to answer "is real execution available" cannot see the
very capability whose availability is in question. This phase does
**not** implement that repair (Step 40/64 forbid it) — it is recorded
as a required precondition, timed at "before first real adapter,"
distinct from "before release" (which could be later) or "not required"
(rejected as too permissive given the tool's purpose).

## 42. PB redesign options

**Option A — new explicit runtime-dispatch permission action.** Add
`action_type = "runtime_dispatch"` / a new `execution_class` (or reuse
`"adapter"`) with an enriched request shape carrying target/adapter/
prompt-digest/repository/effect-list/credential-reference/budget/
idempotency fields (closing RPAC-REQ-044 directly). *Semantic clarity:*
high — a dedicated action makes intent unambiguous. *Policy
compatibility:* high — POL-005 and future policies gate cleanly on a
known action_type. *Authority safety:* high — no ambiguity with existing
`adapter_invocation` semantics used elsewhere. *Extensibility:* high —
new fields can be added without touching unrelated action types.
*Implementation scope:* moderate — one new action, but requires touching
every policy rule's classification logic.

**Option B — reuse existing `adapter_invocation` action with
simulation/real mode semantics amended.** Extend the existing
`PermissionBrokerRequest.simulation_only` boolean into a richer mode
enum (e.g. `simulation` / `bounded_real` / `real`) plus the missing
fields from RPAC-REQ-044, without introducing a new `action_type`.
*Semantic clarity:* moderate — overloads an existing type's meaning.
*Policy compatibility:* high — POL-005's existing `if
request.simulation_only` branch generalizes naturally to a mode check.
*Authority safety:* moderate — risk of accidentally weakening the
existing `adapter_invocation` semantics used by non-runtime callers, if
any exist (none found currently, but future-proofing is weaker).
*Extensibility:* moderate. *Implementation scope:* lower — reuses more
existing structure.

**Option C — separate transport/network/process permissions.** Keep
invocation-permission separate from three new, narrower permissions:
network-egress, subprocess-spawn, and filesystem-mutation-by-runtime —
each independently deny-by-default per RPAC-REQ-085. *Semantic clarity:*
highest — mirrors RPAC-REQ-085's own "one granted effect SHALL not imply
another" principle exactly, and aligns with the already-existing
fine-grained vocabulary in the design-only `RuntimeEnforcementEvidenceBundle`
(§14/§39). *Policy compatibility:* requires new policy rules per
permission, more rules to maintain. *Authority safety:* highest — most
resistant to a single compromised gate cascading into multiple effects.
*Extensibility:* highest. *Implementation scope:* highest — most new
surface area.

No option is selected here; this is a decision for the next phase, with
Option C most aligned with existing contract language (RPAC-REQ-085) and
the pre-existing fine-grained evidence-bundle vocabulary, at the cost of
more implementation surface.

## 43. Human authority options

**(A) Explicit runtime-invocation approval record** — a new,
narrowly-scoped artifact whose sole subject is "this invocation_id, this
target, this prompt digest, is authorized," bound with an expiry and
single-attempt scope (mirroring RPAC-REQ-046). Cleanest separation from
CHGR/IWC's existing, deliberately non-authorizing scope (§12/§13).

**(B) Reuse existing human governance record (CHGR) with a new
subject/action.** CHGR's schema family already models
decision/confirmation/lifecycle-event shapes generically (§12); a new
CHGR record *type* scoped to "runtime invocation authorization" could
reuse the existing schema/manifest/digest machinery without inventing a
new artifact family from scratch. Requires CHGR to gain an actual
authority-resolution consumer, which it explicitly lacks today (its
README disclaims "authority resolution").

**(C) Phase/session approval binds invocation.** Treat the existing
governed-phase-start human decision (the same mechanism gating this very
phase, e.g. "human decision required" before 3T could begin) as also
covering a specific, pre-declared invocation. Weakest option: phase-level
approval is coarser than a single invocation and would blur the
`registered != ... != authorized != dispatched` distinction this phase
is required to preserve.

No selection is made; RPAC-REQ-045's requirement that Runtime
Enforcement evaluate "approval validity" as one bound, freshness-checked
input suggests (A) or (B) are structurally preferable to (C), since both
naturally produce a validity-checkable, invocation-scoped artifact.

## 44. Runtime Enforcement integration options

Per §14's finding that the design-only evidence bundle already declares
a closely-matching fine-grained vocabulary (`adapter_execution_authorized`,
`network_authorized`, `subprocess_authorized`, `shell_authorized`,
`mutation_authorized`): the existing coordinator **cannot** consume an
RPAC invocation request directly today (input contract is
evidence-bundle-reference-based, not request-based). An **adapter-specific
projection** — a thin translation layer that maps an RPAC
`DispatchEnvelope`-shaped request into the existing
`RuntimeEnforcementEvidenceBundle` fields — appears more architecturally
economical than **contract evolution of the coordinator itself**, because
the bundle's vocabulary already anticipates most of the needed
distinctions. Either way, **no duplicate enforcement engine should be
built** — the existing Runtime Enforcement Decision Engine/Coordinator
family (103A/101B) is the correct single integration point; the decision
this phase leaves open is only "extend it" vs. "project into it,"
not "replace it."

## 45. First real dispatch gate sequence

Normative candidate flow (matches §15, restated as the full pipeline
example the instructions request):

```
prompt prepared
  -> explicit runtime target selected
  -> target preflight / capability check (static descriptor)
  -> human authority verified (fresh, invocation-scoped, §43)
  -> Permission Broker real-dispatch permission (§42)
  -> Runtime Enforcement final gate (§14/§44, complete bound request)
  -> process / network containment (Shell Gate for local CLI; egress
     mediation for API, §23-26)
  -> durable invocation state persisted ("dispatch attempted" marker, §19/§47)
  -> adapter dispatch
  -> result capture (untrusted, §31)
  -> generic / Stage-B intake (existing, unmodified, §32)
```

This is presented as a candidate, not a freeze — the instruction
explicitly permits reordering if contract evidence requires it, and none
found in this phase's evidence contradicts this ordering.

## 46. Failure-before-effect rule

Mandatory checks before each named effect boundary:

- **Before process spawn:** target preflight, human authority, PB
  ALLOW, Runtime Enforcement ALLOW, durable pre-dispatch record written,
  environment sanitized, executable identity verified (pinned/hashed).
- **Before network send:** all of the above plus explicit network-egress
  permission (§26/§42 Option A or C) and endpoint allowlist check.
- **Before provider billing:** all network-send checks plus budget/cost
  governance check (§53) — billing must never occur before every prior
  gate has passed.
- **Before repo mutation:** the existing, unmodified source/docs/test
  mutation PB actions, applied to any file the runtime or its output
  touches — no new bypass path may exist for runtime-produced changes
  (§34).

## 47. Durable-before-effect rule

Must be durably persisted **before** real dispatch (extending §19's
existing atomic-write pattern): invocation ID (already the case);
target identity (already the case for the request record); prompt hash
(not currently persisted — new field needed); authority
reference/digest (new); PB decision + digest (new — currently PB
decisions are not persisted to the invocation store at all); Runtime
Enforcement decision + digest (new, same gap); repository/task binding
(already the case, per 3S.2's `resolve_dry_consumer_context` design).
Secrets/credential values must **never** be persisted (RPAC-REQ-084) —
only credential *references*, once §27's architecture exists.

## 48. TOCTOU analysis

Mutable facts that can change between approval, permission, preflight,
and dispatch: **HEAD** (a new commit could land mid-flow — must be
snapshot-bound at authorization time, consistent with how the existing
dry consumer already snapshots `base_commit`/`repository_fingerprint`
per 3S.2's design); **task state** (task could be closed/reassigned —
must be re-checked at dispatch, not just at authorization); **prompt**
(must be hash-bound at authorization and re-verified at dispatch, per
§47); **adapter config** (target configuration could change between
authorization and dispatch — must be snapshotted, per RPAC-REQ-028's
own fail-closed-on-mismatch requirement); **credential/account** (could
be revoked between authorization and dispatch — requires a live
preflight immediately before dispatch, not reliance on the authorization-
time snapshot alone, per §16); **runtime executable** (could be
replaced/upgraded on disk between pinning and dispatch — requires a
hash-check immediately before spawn, not just at descriptor-pin time);
**policy version** (POL-005 or its successor could itself change between
authorization and dispatch in a long-running flow — the Runtime
Enforcement decision must be freshly re-evaluated, not cached, per
RPAC-REQ-046's "positive decision SHALL expire" language). **Must be
snapshot-bound:** HEAD, prompt hash, adapter/target configuration.
**Must be freshly re-checked immediately before dispatch (not just
snapshot-bound):** task state, credential/account validity, executable
identity, policy/decision freshness.

## 49. Adapter configuration trust

Must be repository-local-with-admin-control or user/admin-level
configuration — **never** accepted from untrusted task/model content.
No implementation exists yet to enforce this (no `RuntimeTargetConfiguration`
loader was found reading from task-contract or model-authored content in
`src/pcae`), but the requirement is already implicit in RPAC-REQ-013/014's
framing of configuration as PCAE-owned, referenced data, and is directly
reinforced by RPAC-REQ-028's fail-closed-on-mismatch rule (which only
makes sense if the "known" provider/model value is trusted independently
of what the runtime reports at dispatch time).

## 50. Executable trust

For local CLI runtime, required trust level for a first version:
**resolved/pinned executable with hash verification**, not bare PATH
lookup (PATH lookup alone would violate RPAC-REQ-086's supply-chain
pinning requirement and is trivially spoofable by PATH manipulation).
Absolute-path-plus-hash is the minimum viable trust level; full binary
signing is a stronger future option but not required for the narrow
first-adapter scope (§62).

## 51. Version/capability preflight

Yes — the first real adapter requires a pinned/verified CLI version to
avoid accidental behavior drift, directly per RPAC-REQ-086 ("fail closed
on drift"). A version-preflight check (comparing observed executable
version/hash against the pinned descriptor value) should run as part of
the live preflight (§16), not merely at registration time, since drift
can occur after registration.

## 52. Provider API trust

Not implemented; deferred to when an API adapter is actually built (§29
ranks it last). Minimum future requirements, derived from
RPAC-REQ-059/084: endpoint pinning (no dynamic/derived endpoints from
untrusted input); reliance on TLS for transport trust (no custom trust
override); a model allowlist (RPAC-REQ-028's snapshot/fail-closed-on-
mismatch already anticipates this); provider metadata as PCAE-owned
configuration, not runtime-reported; response provenance never
self-asserted by the provider as authoritative for anything but its own
content (§28).

## 53. Cost/budget governance

**Classification: later hardening, not a first-real-runtime hard
prerequisite for the local CLI path (which need not incur monetary
cost), but a hard prerequisite for any API/provider adapter.** No
budget/cost tracking mechanism exists in `src/pcae` beyond a `budget`
field referenced in contract prose (RPAC-REQ-044's list of missing PB
request fields) — this is currently entirely unimplemented. Because
§30 ranks a non-AI local executable as the first real adapter, cost
governance can be deferred past that milestone, but must precede any
API-provider adapter per §46's "before provider billing" rule.

## 54. Audit requirements

Real dispatch must record: requester (agent_id, already modeled);
repo/task binding (already modeled per 3S.2's design); prompt hash (new
field, §47); target (already modeled); authority reference (new, §43);
PB decision + digest (new — not currently persisted to the invocation
store); Runtime Enforcement decision + digest (new, same gap); dispatch
attempt marker (new, §19/§47); process/provider identity actually
observed at dispatch time (new); outcome (already modeled via
`RuntimeInvocationResult`); result intake reference (already modeled via
`intake-handoff.json`). **Existing audit reuse:** the atomic
`RuntimeInvocationStore` write pattern (§19) is directly reusable as the
audit-record persistence mechanism — it needs new fields, not a new
mechanism.

## 55. Explainability requirements

Operator questions and which existing framework can answer them once the
above gaps close: *"Why was this runtime selected?"* — answerable from
the (extended) request/target descriptor, already partially modeled.
*"Who authorized it?"* — requires §43's new authority artifact; currently
unanswerable. *"What permission allowed it?"* — requires PB decision
persistence (§47/§54), currently unanswerable (PB decisions are not
persisted to the invocation store today). *"What enforcement decision
occurred?"* — requires Runtime Enforcement decision persistence, same
gap. *"What external effect happened?"* — answerable once §22/§37
process-supervision evidence is captured. *"What result entered PCAE?"*
— already answerable via the existing `intake-handoff.json` pattern
(§32). **The `RuntimeInvocationStore`'s existing atomic, timestamped,
per-attempt document model is the correct framework to extend** — no new
explainability surface needs to be invented, but PB/RE decisions must
start flowing into it.

## 56. Restart/recovery matrix

| Crash point | Current behavior | Required real-runtime behavior | Risk |
|---|---|---|---|
| Before durable record | No record exists; nothing to recover | Same — safe, no action needed | None |
| After record, before dispatch | Record exists, no dispatch marker (dispatch layer does not exist yet) | Must distinguish "recorded, not yet dispatched" from "dispatched" via a new marker (§19/§47) | Low once marker exists; unbounded ambiguity until then |
| After dispatch, before confirmation | N/A — no dispatch layer exists | Must persist "dispatch attempted" before the effect boundary, so restart can flag "uncertain outcome, do not auto-retry" (§20/§21) | High — this is the exactly-once-breaking window |
| During runtime (process/request in flight) | N/A | Requires live process-tree tracking (§22) surviving a PCAE restart, or a documented "assume lost, mark uncertain" policy | High for local CLI (orphaned process, §37); moderate for API (provider continues regardless) |
| After runtime, before result persist | N/A | Same durable-marker requirement as above | High |
| After result, before intake | Result persisted (`result.json`), intake-handoff not yet written — recoverable by re-running intake-handoff construction from the persisted result (idempotent by design, per existing atomic-write pattern) | Same, extended to real results | Low |

## 57. Local CLI trust matrix

| Concern | Current control | Gap | Blocking before local CLI? |
|---|---|---|---|
| Process ownership/supervision | None | Full implementation needed (§22) | Yes |
| Shell/argv construction policy | Shell Gate (classifier only, non-enforcing) | Must become enforcing or an equivalent built (§24) | Yes |
| Environment sanitization | None | Allowlist mechanism needed (§23) | Yes |
| Executable trust/pinning | None (only mock descriptor is pinned, by construction) | General pinning/hash-verification needed (§50) | Yes |
| Filesystem containment | None runtime-specific; reusable worktree pattern exists elsewhere | Wire the existing worktree pattern to runtime dispatch (§25) | Yes |
| Detached-process containment | None | Process-group ownership + tree-kill verification (§37) | Yes |
| Cancellation/timeout | None | SIGTERM/escalation + finite timeout (§36) | Yes |

## 58. API/provider trust matrix

| Concern | Current control | Gap | Blocking before API provider? |
|---|---|---|---|
| Credential reference | None | Full architecture needed (§27) | Yes |
| Network egress permission | None (no PB action exists) | New PB action/policy needed (§26/§42) | Yes |
| Endpoint/TLS trust | None | Pinning policy needed (§52) | Yes |
| Cost/budget governance | None | Full mechanism needed (§53) | Yes |
| Response provenance trust | None (no API adapter exists) | Provenance-never-self-asserted rule needs enforcement (§28/§52) | Yes |
| Rate-limit/retry handling | Taxonomy exists in contract (RPAC-REQ-071), no implementation | Implementation needed | Yes |

## 59. 16-prerequisite matrix

| RPAC Req | Current state | Dependency | Contract work | Implementation work | Security work | Priority |
|---|---|---|---|---|---|---|
| RPAC-REQ-014 | UNSTARTED | Depends on 084 | Credential-reference contract | Config-reference type | Low (no secrets touched yet) | P2 |
| RPAC-REQ-028 | PARTIALLY SATISFIED (mock never switches) | Depends on 057/059 | Snapshot/fail-closed spec | Real snapshot+compare logic | Medium (mismatch = wrong target) | P3 |
| RPAC-REQ-044 | CONTRACT GAP | Blocks 045/046/072 | PB request-shape amendment (§42) | New/extended request fields | High (foundation for all gating) | **P0** |
| RPAC-REQ-045 | AUTHORITY GAP | Depends on 044; blocks 047/095 | RE-as-final-gate contract (§14/§44) | Wire RE to a real consumer | High | **P0** |
| RPAC-REQ-046 | IMPLEMENTATION GAP | Depends on 045 | Expiry/single-attempt spec | Decision-expiry implementation | High | P1 |
| RPAC-REQ-047 | CONTRACT GAP | Depends on 045; blocks 048 | RE/Shell-Gate division-of-labor spec | None yet | Medium | P1 |
| RPAC-REQ-048 | UNSTARTED, explicitly forbidden now | Depends on 047; blocks 057 | Shell Gate enforcement contract | Make Shell Gate intercepting | High | **P0** (for local CLI chain) |
| RPAC-REQ-057 | UNSTARTED | Depends on 048/084/086 | Local target descriptor schema | Full local-CLI target type | High | P1 |
| RPAC-REQ-058 | UNSTARTED | Depends on 084 | Env-sanitization spec | Allowlist + secret injection | High | P1 |
| RPAC-REQ-059 | UNSTARTED | Depends on 084 | API target descriptor schema | Full API-target type | High | P2 (API-only) |
| RPAC-REQ-071 | UNSTARTED | Depends on 045/046 | Retry-class taxonomy (exists in contract) | Retry classifier | Medium | P2 |
| RPAC-REQ-072 | UNSTARTED | Depends on 045/046, human authority (§43) | Reauthorization-on-retry spec | Retry-authorization wiring | Medium | P2 |
| RPAC-REQ-084 | TRUST-SECURITY GAP, explicit contract blocker | Blocks 014/058/059 | Credential-reference architecture | Resolver + reference type | **Highest** | **P0** |
| RPAC-REQ-086 | UNSTARTED | Blocks 057 | Supply-chain pinning spec | Digest-pinning + drift check | High | P1 |
| RPAC-REQ-095 | UNSTARTED, decision-bearing | Terminal — depends on nearly all above | First-adapter sequencing (already specified) | The adapter itself (future phase) | Depends on above | Terminal |
| RPAC-REQ-097 | CONTRACT GAP | Parallelizable; precondition of "any real activation" | Legacy-path inventory/retirement plan | Retire/route legacy paths | Medium | P1 (parallel) |

## 60. Dependency DAG

```
                 RPAC-044 (PB request shape)
                    |
        -----------------------------
        |                           |
   RPAC-045/046                RPAC-072 (retry reauth)
   (Runtime Enforcement            ^ (also needs human authority, §43)
    real gate)                     |
        |                     RPAC-071 (retry taxonomy)
   RPAC-047 (RE/Shell-Gate
    division of labor)
        |
   RPAC-048 (Shell Gate enforcing)  <-- FIRST HARD BLOCKER's structural
        |                                sibling for local-CLI chain
        |
   RPAC-057 (local CLI target descriptor)
        |                                  RPAC-084 (credential-reference
   RPAC-028 (provider/model snapshot) <----     architecture) ----> RPAC-014
        |                                  |                       RPAC-058
        |                                  |                       RPAC-059
   RPAC-086 (supply-chain pinning) --------
        |
   RPAC-095 (first real adapter)  <-- terminal node

   RPAC-097 (legacy-path retirement) -- parallel, precondition of "any
                                          real activation" (not of design work)
```

**Can run in parallel today (no shared blocking edge):** RPAC-REQ-044
(PB contract design), RPAC-REQ-084 (credential-reference architecture
design), RPAC-REQ-086 (supply-chain pinning design), RPAC-REQ-097
(legacy-path inventory).

**Hard serial spine:** RPAC-044 -> RPAC-045/046 -> RPAC-047 -> RPAC-048
-> RPAC-057 -> RPAC-095.

**First unblocker:** RPAC-REQ-044 (PB request-shape amendment) — nothing
downstream can be meaningfully authorized without it, and POL-005 itself
(§7) is the first-hard-blocker *decision point* that RPAC-044's amendment
must eventually be evaluated against.

**First real-adapter-ready point:** the moment RPAC-044, 045/046, 047,
048, 057, 084, and 086 are all satisfied simultaneously for the local-CLI
chain — RPAC-095's generic fixed-argv executable becomes exercisable
only at that convergence point.

## 61. Minimum viable real-runtime path

Smallest acceptable path to one human-authorized real runtime, no
autonomy expansion beyond necessary: one explicit target, selected by
exact ID with no fallback (already the pattern established by the dry
consumer); one explicit, fresh, invocation-scoped human authorization
(§43); no automatic retry (§21); one runtime target, one repository, one
task; a bounded, short timeout (§22); a bounded, sanitized environment
(§23); the result treated as fully untrusted and routed through the
existing, unmodified intake/review pipeline (§32-34) with no new
auto-accept path. This mirrors exactly the explicit-two-part-opt-in,
no-fallback design already proven safe for the dry consumer (3S.2/3S.2.1)
— the minimum viable real path is the same shape, with the mock adapter
swapped for a real, narrowly-scoped one, and every gate in §45's sequence
actually enforcing rather than simulating.

## 62. Initial scope restrictions

Deliberately narrow v1 restrictions, derived from the risk analysis
above: **local CLI only** (§29 — lower trust complexity, no network/
credential/cost chain required); **no API providers initially** (defer
until §27/§52/§53 close); **no parallel invocations** (simplifies §48's
TOCTOU surface and §37's process-supervision surface); **no automatic
retries** (§21 — every retry requires fresh authorization); **no
background/detached execution** (§37 — must be foreground, directly
supervised); **no unattended scheduling** (every dispatch requires the
fresh human act of §43, not a standing approval); **no multi-repo**
(matches the existing repo-binding design already proven in 3S.2);
**explicit human approval every invocation** (no session-level or
phase-level standing approval, per §43's rejection of Option C as
too coarse).

## 63. Release implications

No release decision is made in 3T. The real-runtime chapter (once the
prerequisites in §59/§60 are substantially closed and a first real
adapter exists, reviewed, and independently verified — likely several
governed phases away) is a plausible candidate for a future **v0.5.0**
given the magnitude of the capability shift (PCAE gaining its first real
external-execution surface is a materially larger change than the
patch-level v0.4.x releases to date), but this phase does **not** freeze
that version number or commit to it — it is a naming placeholder for
planning purposes only, subject to revision by whichever phase actually
proposes the release.

## 64. Recommended next phase

Evidence-derived selection among the three candidate shapes offered:
"if PB is first blocker -> Runtime Dispatch Permission Contract
Evolution"; "if human authority is first blocker -> Runtime Invocation
Human Authority Contract"; "if both must be designed together -> Real
Runtime Dispatch Authority and Permission Contract Architecture."

This phase's evidence (§7, §11, §12, §42, §43) shows PB (POL-005/RPAC-044)
is the *structurally* first blocker (nothing downstream is reachable
while it unconditionally denies), **but** the PB redesign options in §42
cannot be soundly chosen without first knowing what the human-authority
artifact (§43) will bind and validate against (RPAC-REQ-045 explicitly
requires Runtime Enforcement to sit "after human approval ... and
Permission Broker permission" — the two are adjacent, interdependent
gates in the same short chain, not sequential-and-separable). **Recommended
next phase: "Real Runtime Dispatch Authority and Permission Contract
Architecture"** — a combined contract-design phase (still no
implementation) that produces: (1) a selected PB redesign option
(§42 A/B/C) with a frozen request-shape contract; (2) a selected human
authority artifact design (§43 A/B/C) with a frozen record-shape
contract; (3) the binding between them (how a fresh human authorization
reference flows into a real PB request and then into Runtime
Enforcement, per §45's sequence) — all contract/design work, matching
this phase's own read-only nature, with implementation deferred to a
subsequent phase.

## 65. Human decision required

This phase makes no PB/policy change, no Runtime Enforcement change, no
new adapter, no subprocess, no provider network call, no credential
access, no `pcae runtime inspect` change, no repair of the 2 MUST-FIX
findings (recorded, not fixed, per §40), and no Shell Gate activation.
**A human decision is required** to authorize the recommended next phase
(§64) or to select a different path among the alternatives this phase
identified (§42/§43 options). No autonomous continuation is authorized
by this document.

**HUMAN DECISION: REQUIRED** before any of: (a) beginning "Real Runtime
Dispatch Authority and Permission Contract Architecture" (§64); (b)
selecting a PB redesign option (§42); (c) selecting a human-authority
artifact design (§43); (d) repairing either 3S.2.1 MUST-FIX finding
(§40) outside a separately authorized phase; (e) any Shell Gate,
Runtime Enforcement, or credential-architecture work. This phase stops
here, as instructed.
