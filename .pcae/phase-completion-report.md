# Phase 149O.20L.7O.3U Complete — Real Runtime Dispatch Authority and Permission Contract Architecture

**Verdict: COMPLETE. READ-ONLY ARCHITECTURE/CONTRACT-DESIGN. NO SRC/PCAE MODIFIED. NO PB ACTION IMPLEMENTED. NO AUTHORITY ARTIFACT CREATED. EXECUTION NOT ACTIVATED.**

Phase 149O.20L.7O.3U made the two decisions Phase 3T deliberately
deferred: a Permission Broker (PB) real-dispatch redesign option and a
human runtime-authority artifact design, and defined the binding between
them, preserving `human authority != PB permission != runtime capability
!= Runtime Enforcement decision != dispatch != execution` throughout. No
implementation was performed.

**Phase-entry SHA:** `8adf11afbdcc87f30dd5969620ea5fda57bb2241`.
**v0.4.3 public state:** unchanged, `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
**Runtime state:** `Observed` / `observe` / `unavailable`, unchanged at
phase entry and phase close. **Production dry consumer state:**
IMPLEMENTED, VERIFIED, PRODUCTION-CONSUMED (unchanged from 3S.2/3S.2.1),
untouched by this phase.

## RPAC-REQ-044/045/046 (re-derived, exact wording, unchanged)

Quoted verbatim from `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
lines 334/341/346: RPAC-REQ-044 (PB request-shape gap, must bind target/
adapter/prompt-digest/repository/effects/network-filesystem/credentials/
budget/idempotency); RPAC-REQ-045 (Runtime Enforcement is the sole final
whether-to-invoke gate, after human approval/target facts/PB permission,
before any adapter effect); RPAC-REQ-046 (Runtime Enforcement must
evaluate the complete bound request, all effect-specific permissions,
freshness, approval validity, no-go evidence; a positive decision expires
and is single-attempt scoped). None makes PB or human approval
authoritative by itself.

## POL-005 exact semantics (unmodified)

Confirmed by direct source read of
`src/pcae/core/permission_broker_foundation.py` lines 489-518
(`ExecutionDisabledRule`): unconditional `DECISION_DENY` for any
non-`simulation_only` request, for every `execution_class`, reason
`"execution_boundary_unavailable"`. Classified as an invariant condition
tied to the missing `COMP-002` execution boundary, not a permanent
universal deny and not a reversible kill-switch flag — its own
`required_remediation` names the exact unblock condition. Not modified by
this phase.

## Current PB action/execution-class inventory

10 `action_types` (`read`, `source_mutation`, `docs_mutation`,
`test_mutation`, `commit`, `push`, `rollback`, `shell_command`,
`backend_invocation`, `adapter_invocation`); 6 `execution_classes`
(`none`, `mutation`, `shell`, `backend`, `adapter`, `rollback`). Decision
vocabulary confirmed by direct source read: `ALLOW`/`DENY`/`HUMAN_REVIEW`,
composed with precedence `DENY > HUMAN_REVIEW > ALLOW`; `ALLOW` is
annotated `INV-008`, "Never an executable authorization." POL-004
(`MissingHumanApprovalRule`) is the existing rule that resolves
`HUMAN_REVIEW` to not-triggered exactly when `approval_present` is
`True`, for `{shell, backend, adapter, rollback}` execution classes.

## PB redesign: 3 options evaluated, Option A selected

**Option A (selected) — dedicated `runtime_dispatch` action.** Scored
across 9 criteria (semantic clarity, backward compatibility, policy
complexity, least privilege, future CLI/API support, local CLI
compatibility, API provider compatibility, auditability, risk of
authority conflation) against **Option B** (existing `adapter_invocation`
+ `invocation_mode` enum) and **Option C** (composite per-effect
permissions for adapter/process/network/filesystem). Option A selected
because it closes RPAC-REQ-044 with high semantic clarity and low
authority-conflation risk while keeping PB's own scope narrow (per
RPAC-REQ-085's "one granted effect SHALL not imply another") — process
authority stays with Shell Gate, network authority is explicitly deferred
as an open dependency, filesystem-mutation authority stays with the
existing, unmodified mutation actions. Full Matrix B in the phase
document Section 10.

## Human authority: 3 options evaluated, Option A selected

**Option A (selected) — dedicated, one-shot `RuntimeInvocationApproval`
artifact.** Rejected **Option B** (extend CHGR-001 — its own README
explicitly disclaims "authority resolution" and "runtime consumption")
and **Option C** (bind to phase/session approval — too coarse, blurs the
`registered != ... != authorized != dispatched` distinction). Subject
bound to a five-fact tuple: `invocation_id`, `runtime_target`,
`prompt_hash`, `repo_identity`, `task_id`. One-shot only for v1 (no
session-wide or phase-wide reuse), narrowest-authority default.

## One-shot/reusable, subject, freshness, revocation, storage, trust

**Scope:** one invocation per approval (§17 of the phase document).
**Subject:** the five-tuple above; changing any member invalidates the
approval entirely (a different subject, not merely stale). **Freshness:**
7 mandatory-for-v1 invalidating conditions (HEAD change, task-state
change, prompt change, runtime-target change, adapter-config change,
policy-version change, timeout/expiry) — none deferred. **Revocation:**
no explicit revoke command required for v1; one-shot consumption plus
bounded expiry are sufficient to avoid stale authority. **Storage:** the
`.pcae` canonical governance store pattern (sibling to, not merged with,
`RuntimeInvocationStore` or CHGR). **Trust:** reuse of the existing
schema/manifest/tamper-detection pattern already proven for CHGR; no
signature required for v1.

## Approval creation/consumption; PB/authority relationship

**Creation:** PCAE presents bound facts (target, prompt/hash, repo/task,
effect class) to an identified human, who explicitly approves; a
canonical artifact is created (design only, no CLI built). **Consumption:**
lookup by reference → subject-tuple exact match → freshness check →
one-shot-not-already-consumed check; fails closed on any failure, with no
partial-credit state. **PB/authority relationship:** PB independently
validates a *reference* to the approval, never receives the raw artifact
or a caller-supplied boolean; the approval-validation step and PB
evaluation remain separately owned, feeding into the same existing
`approval_present` field POL-004 already consumes.

## Gate ordering (frozen)

Prompt prepared → explicit runtime target selected → static
capability/preflight → human authority created → approval validated →
Permission Broker (`runtime_dispatch`) → Runtime Enforcement (sole final
whether-to-invoke gate) → process/network containment (Shell Gate /
future network mediation) → durable pre-dispatch record → adapter
dispatch → untrusted result capture → existing Stage-B intake. Capability
preflight runs before human authority (cheap, avoids wasting human
attention on a structurally incapable target) but is re-checked live
immediately before dispatch. PB runs before Runtime Enforcement, matching
RPAC-REQ-045's literal ordering.

## Runtime Enforcement handoff projection

Runtime Enforcement must not infer authority from PB ALLOW alone or from
approval alone. It receives: the full bound request; PB's decision value
and matched-policy IDs as evidence (not authority); the validated-approval
reference plus its freshness verdict, independently re-verified; fresh
live-preflight facts. Only Runtime Enforcement's own decision can produce
a "may dispatch" outcome.

## Execution Attempt Boundary mapping

Read from `docs/PHASE_99_GOVERNED_EXECUTION_ATTEMPT_BOUNDARY_DESIGN.md`
without redefinition: gates 1-6 (prompt through PB) sit entirely "before
execution attempt"; gate 7 (Runtime Enforcement's decision) is the
execution-attempt decision point; gate 10 (adapter dispatch) is the first
external effect.

## Durable-before-effect requirements

Must be durable before any real external effect: invocation ID;
repo/task binding; runtime target; prompt hash (new field); human-authority
reference (new); PB decision + digest (new); Runtime Enforcement decision
+ digest (new); dispatch-intent marker written immediately before the
process/network call (new, most safety-critical addition).

## TOCTOU findings

Must be snapshot-bound at authorization time: HEAD, prompt hash, runtime
target, adapter config identity. Must be freshly re-checked immediately
before dispatch, not merely snapshot-bound: task state, adapter executable
identity/hash, policy/decision freshness. Full Matrix E in the phase
document Section 33.

## Prompt hash / repo / task / runtime binding

Prompt hash: covers only semantically load-bearing content, excludes
unstable formatting/environment metadata. Repository binding: git-derived
fingerprint (reusing the dry consumer's existing pattern), never a raw
path. Task/phase bound always; session bound only when session-scoped
work exists. Runtime target: exact match, no fallback (mirrors the
already-proven dry-consumer no-fallback design).

## PB HUMAN_REVIEW semantics (resolved from source, not guessed)

POL-004 (`MissingHumanApprovalRule`) already resolves `HUMAN_REVIEW` to
not-triggered exactly when `approval_present` is `True`. **Frozen
meaning:** a valid, matching, current, unconsumed `RuntimeInvocationApproval`
is precisely what sets `approval_present=True`; this is not additional
review beyond the approval already obtained, not policy escalation, and
not automatically reusable for a different request — the exact-tuple
binding prevents cross-request reuse.

## Simulation/backward compatibility

The dry (`simulation_only=True`) path is entirely untouched — no field,
gate, or artifact from this design is retrofitted onto it. No existing PB
behavior changes for rollback, push, publication, or the existing
mutation-root actions. The new `runtime_dispatch` action is strictly
additive.

## Policy/authority versioning; crash/retry semantics

Policy version must be bound to the Runtime Enforcement decision, which
must re-evaluate (not cache) across a policy-version change. Approval
consumption is tied to the same durable write that marks "dispatch
attempted" (not earlier, at PB or Runtime Enforcement ALLOW alone; not
later, only after confirmed dispatch) — this was chosen after analyzing
all four candidate consumption points' crash windows. Crash-before-dispatch
and crash-after-dispatch both require fresh human authorization on retry;
no automatic replay is permitted (RPAC-REQ-072).

## Local CLI specialization / API extension path

v1 local-CLI fields: exact runtime target, command descriptor identity,
repo/task, prompt hash, no network field required true, bounded
filesystem scope. API extension (out of v1 scope): provider/model
identity (mandatory for API targets only), network permission, cost/
budget, credential reference — additive to the same action, never
mandatory universally.

## Network permission disposition (open dependency)

No PB network action or execution_class exists today. This phase
explicitly does **not** resolve network-egress permission — it is flagged
as an unresolved, deliberately deferred dependency, out of scope for the
local-CLI-only v1 path (which needs no network PB action at all) and
blocking for any future API-provider path.

## Filesystem/process authority distinction

`runtime_dispatch` PB permission never implies mutation authority (the
existing `source_mutation`/`docs_mutation`/`test_mutation` actions remain
the sole mutation gate, unmodified) or process/shell authority (Shell
Gate or an equivalent enforcing process-construction policy remains
independently required, unmodified, and non-enforcing today).

## Two 3S.2.1 MUST-FIX findings — disposition unchanged

Recovered verbatim again: (1) uncaught `AttributeError` on a malformed
non-mock adapter result — unaffected by this architecture, still becomes
a de facto blocker only once a second (real) adapter is registered. (2)
`invocation_id` path-traversal in `RuntimeInvocationStore` — unaffected;
this design's new fields do not introduce any caller-supplied
`invocation_id` surface. Neither repaired this phase.

## Runtime-inspect limitation disposition — unchanged

`TRUTHFUL_WITH_LIMITATION` unaffected in substance by this phase; still
must be repaired before the first real adapter is registered, not before
release and not "not required."

## Authority / permission / cross-gate threat models

Authority threat model: 8 threats (forged/stale/reused approval, approval
for a different runtime/prompt/repo-task, tampering, replay after crash),
each mitigated by the subject-tuple binding, freshness set, and one-shot
consumption. Permission threat model: 6 threats (request manipulation,
simulation-flag confusion, execution-class/action-type confusion, policy
drift, decision replay), each mitigated by existing structural validation
plus the new action's distinctness. Cross-gate threat model: all 3 named
confusions (approval-as-permission, PB-ALLOW-as-authorization,
RE-ALLOW-as-both) made structurally impossible by construction — full
justification in the phase document Sections 59-61.

## Security invariants (Matrix F)

10 invariants frozen, including: no approval → no real dispatch; stale/
mismatched approval → no real dispatch; PB DENY or failure → no real
dispatch; PB ALLOW without approval → no real dispatch (already enforced
by POL-004 today for the relevant classes); approval without PB ALLOW →
no real dispatch; Runtime Enforcement deny → no real dispatch; runtime
unavailable → no dispatch; adapter cannot self-authorize. Full matrix in
the phase document Section 62.

## Combined-artifact decision

Assessed and rejected: approval and PB decision must never live in one
artifact (different lifecycles, different provenance, different trust
boundaries). Separate provenance with linkage (references/hashes) is
preferred.

## Future contract artifacts recommended

Runtime Invocation Human Authority Contract; PB Runtime Dispatch
Extension Contract; Dispatch Gate Ordering Contract; invocation authority
schema. None frozen this phase.

## Contract-freeze readiness (split verdict)

**Outcome A (ready to freeze in the next phase)** for the local-CLI-only
v1 path. **Outcome B (one more architecture-clarification phase
required)** for the API-provider path, blocked on the open
network-egress-permission dependency.

## Implementation dependency order

Authority artifact + storage → PB request-shape support → approval-
validation logic → independent verification → Runtime Enforcement
integration → Shell Gate enforcement / local-CLI target descriptor
(parallel), converging at the first real adapter (RPAC-REQ-095).

## Production source modified / execution activated / external invocation

**Production source modified: NO** (`git diff --stat -- src/pcae tests`
confirmed empty). **Execution activated: NO.** **External runtime
invocation: NONE.** Runtime remains `Observed`/`observe`/`unavailable`,
unchanged throughout. **Version/release: unchanged**, v0.4.3 still
resolves to `63580893b1de4782a694ab802ff7bdebdf29b0e6`. Article remains
STOPPED; private research repository (`~/repos/pcae-deepseek-research`)
untouched, not inspected.

## Checks run

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings limited to pre-existing
`tasks/DONE.md` synchronization debt (unrelated to this phase). `pcae
push check`: clean. `pcae runtime inspect`: unchanged
(`not_implemented`/`Observed`/`observe`/`unavailable`). Telegram:
configured, enabled, outbound-ready.

## Commits, pushed, origin/main..HEAD

Commits and push state recorded in `.pcae/phase-completion-metadata.json`
(`phase_commits`, `pushed_status`, `origin_main_head`,
`origin_main_head_count`).

**REAL RUNTIME AUTHORITY/PERMISSION ARCHITECTURE: COMPLETE**
**REAL EXECUTION: UNAVAILABLE**
**PB REAL-DISPATCH MODEL: Option A — dedicated `runtime_dispatch` action**
**HUMAN RUNTIME AUTHORITY: Option A — dedicated, one-shot `RuntimeInvocationApproval` artifact**
**AUTHORITY: SEPARATE FROM PB PERMISSION**
**PB PERMISSION: SEPARATE FROM RUNTIME CAPABILITY**
**RUNTIME ENFORCEMENT: SEPARATE PRE-DISPATCH GATE**
**APPROVAL SCOPE: one-shot**
**DISPATCH BINDING: repo + task + runtime target + prompt/invocation identity**
**POL-005: UNCHANGED**
**SIMULATION PATH: UNCHANGED**
**TOCTOU: EXPLICITLY BOUND / REVALIDATED**
**NEXT: PB Runtime Dispatch + Human Authority Contract Freeze (local-CLI-only v1 scope)**
**EXECUTION ACTIVATION: NOT PERFORMED**
**HUMAN DECISION: REQUIRED**
