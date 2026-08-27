# Phase 149O.20L.7O.3U — Real Runtime Dispatch Authority and Permission Contract Architecture

**Status: READ-ONLY ARCHITECTURE/CONTRACT-DESIGN PHASE — COMPLETE.**
**PRODUCTION SOURCE MODIFIED: NO. EXECUTION ACTIVATED: NO. RUNTIME REMAINS Observed / observe / unavailable.**
**NO PB ACTION IMPLEMENTED. NO AUTHORITY ARTIFACT CREATED. ARCHITECTURE ONLY.**

## 1. Objective

Design and freeze the minimum contract *architecture* (not implementation)
for a future human-authorized real-runtime invocation. This phase makes
the two decisions Phase 3T deliberately deferred — a PB real-dispatch
redesign option (3T §42 A/B/C) and a human runtime-authority artifact
design (3T §43 A/B/C) — and defines the binding between them, preserving
throughout: `human authority != PB permission != runtime capability !=
Runtime Enforcement decision != dispatch != execution`. No PB action is
implemented, no authority artifact is created, no policy is changed. This
phase produces architecture only.

## 2. Baseline

Verified at phase entry (2026-08-27):

- `git status --short`: clean. `git status --branch --short`:
  `## main...origin/main` (no ahead/behind).
- `git rev-list --count origin/main..HEAD`: `0`.
- `git rev-parse HEAD` == `git rev-parse origin/main` ==
  `8adf11afbdcc87f30dd5969620ea5fda57bb2241`.
- `git rev-parse v0.4.3^{commit}` == `63580893b1de4782a694ab802ff7bdebdf29b0e6`
  — unchanged from the last released version.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: warnings limited to pre-existing
  historical `tasks/DONE.md` synchronization debt across 60+ prior
  entries, none attributable to this phase. `pcae push check`: clean,
  nothing to push. `pcae runtime inspect`: `not_implemented` / `Observed`
  / `observe` / `unavailable`; registry empty, 0 plugins, 0 capabilities.
  Telegram sink: configured, enabled, outbound-ready. `pcae phase-report
  show --latest`: 149O.20L.7O.3T, completed, report complete, recommending
  exactly this phase ("Real Runtime Dispatch Authority and Permission
  Contract Architecture").
- Two active-task entries were found at startup (`20260827-0016-...`
  and `20260827-0933-...`, both stale idle placeholders); both were
  closed via `pcae task close` before opening this phase's task
  contract, per the governed lifecycle.

All Step 1 preconditions held: clean repository, zero ahead of
origin/main, v0.4.3 unchanged, runtime unchanged, no genuine active
governed phase before startup.

## 3. Phase 3T dependency result (recap, not re-derived)

Phase 3T re-derived all 16 RPAC-001 real-runtime prerequisites (RPAC-REQ-014/
028/044/045/046/047/048/057/058/059/071/072/084/086/095/097), built the
dependency DAG, and identified **RPAC-REQ-044** (PB request-shape amendment)
as the first structural blocker on the dependency graph, sitting immediately
upstream of **POL-005** (`ExecutionDisabledRule`), the first hard *decision*
blocker: any non-`simulation_only` request is unconditionally denied by
POL-005 today, for every `execution_class`, because no execution boundary
(`COMP-002`) exists. 3T also established that **no existing PCAE artifact
authorizes a specific real runtime invocation** (CHGR-001 is schema-only by
its own README disclaimer; Interactive Workflow Confirmation is explicitly
barred by RWMPC-REQ-023 from populating `approval_present`). 3T recommended
exactly this combined phase because RPAC-REQ-045 requires Runtime
Enforcement to sit "after human approval ... and Permission Broker
permission" — the two gates are adjacent and interdependent, not
sequential-and-separable, so PB redesign cannot be soundly chosen without
also fixing what the human-authority artifact will bind against. This
phase does not re-derive 3T's evidence; it builds directly on it and cites
it by section (`3T §N`) throughout.

## 4. RPAC-REQ-044/045/046 (re-derived, exact wording)

Quoted verbatim from `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
(grep-confirmed at lines 334, 341, 346 respectively — unchanged since 3T):

> **RPAC-REQ-044:** "The existing Permission Broker action/execution-class
> vocabulary (`adapter_invocation`/`backend_invocation`; `adapter`/
> `backend`) is a useful starting point but insufficient for RPAC dispatch
> because its request does not bind target, adapter, prompt digest,
> repository, effects, network/filesystem, credentials, budget, or
> idempotency. That contract gap SHALL be closed in a separate future
> phase without changing policy in 3Q."

> **RPAC-REQ-045:** "Runtime Enforcement SHALL be the final whether-to-invoke
> gate, after human approval, target facts, and Permission Broker
> permission, and before any adapter effect. The current evidence-only,
> non-authorizing, zero-consumer implementation SHALL NOT be treated as
> that future gate."

> **RPAC-REQ-046:** "Runtime Enforcement SHALL evaluate the complete bound
> request, all effect-specific permission decisions, target/status
> freshness, repository/task/HEAD freshness, approval validity, and no-go
> evidence. A positive decision SHALL expire and SHALL be single-attempt
> scoped."

**Exact responsibilities (not paraphrased into stronger authority than the
text supports):**

- RPAC-REQ-044 is a *contract-gap* requirement about the **PB request
  shape**, not a mandate to invent a new action type — it says the gap
  "SHALL be closed," not which specific mechanism closes it. It names the
  missing bound facts exhaustively: target, adapter, prompt digest,
  repository, effects, network/filesystem, credentials, budget,
  idempotency.
- RPAC-REQ-045 assigns Runtime Enforcement — and *only* Runtime
  Enforcement — the role of "final whether-to-invoke gate." It explicitly
  orders it *after* human approval, target facts, and PB permission, and
  *before* any adapter effect. It does **not** say PB or human approval is
  itself sufficient to invoke; it names Runtime Enforcement as the single
  terminal decision point.
- RPAC-REQ-046 constrains what Runtime Enforcement's decision must
  consider (the *complete* bound request, effect-specific permissions,
  freshness of target/status/repo/task/HEAD, approval validity, no-go
  evidence) and imposes two hard properties on a positive decision:
  **expiry** and **single-attempt scope**. It does not describe how PB or
  human authority are structured — only what Runtime Enforcement must
  evaluate once they exist.

None of these three requirements makes PB or human approval authoritative
for dispatch by itself; each is deliberately scoped to leave Runtime
Enforcement as the sole final "whether" gate, which this phase's design
preserves.

## 5. Current PB request model (reconstructed from source)

From `src/pcae/core/permission_broker_foundation.py` (`PermissionBrokerRequest`,
lines 142–162, unchanged since 3T's citation):

```
request_id: str
timestamp: str
action_type: str
execution_class: str
task_id: str | None
phase_id: str | None
requested_component: str
requested_capability: str
requested_resource: str | None
evidence_available: bool
approval_present: bool
simulation_only: bool = True
```

- **action_type / execution_class:** present, but coarse (see §6).
- **Mutation/effect metadata:** none beyond the `action_type` string itself
  (e.g. `source_mutation`) — no structured effect list, no
  network/filesystem/process distinction.
- **Simulation-only field:** `simulation_only: bool`, defaults `True`.
  This is the *entire* real-vs-simulated distinction today — a single
  boolean, not a graded mode.
- **Actor/principal:** none. No `agent_id`/caller-identity field exists on
  `PermissionBrokerRequest` itself (identity is carried elsewhere, e.g. in
  the invocation record, not in the PB request).
- **Repository/task binding:** `task_id` and `phase_id` exist; no
  repository-identity field, no HEAD/commit binding, no runtime-target
  field.
- **Approval evidence field:** `approval_present: bool` exists, but per
  RWMPC-REQ-023 (§12 below) nothing today may set it `True` from a
  Confirmation/IWC/AESIC-derived signal; only `MissingHumanApprovalRule`
  (POL-004) consumes it, generically, unrelated to runtime dispatch.
- **Capability evidence field:** `evidence_available: bool` exists but is
  a generic evidence-presence flag, not a runtime-capability/preflight
  signal.

**Insufficient for real adapter dispatch:** target identity, adapter
descriptor identity/version, prompt digest, repository identity/HEAD,
structured effect list (network/filesystem/process), credential
reference, budget, idempotency key, and human-authority artifact
reference are all absent. This matches RPAC-REQ-044's own enumeration
exactly — confirmed independently by direct source read, not merely
cited from 3T.

## 6. PB action vocabulary (Matrix B — PB redesign options; vocabulary table)

Current vocabulary, read directly from `permission_broker_foundation.py`
lines 94–134 (unchanged since 3T):

| Value | Current meaning | Real dispatch applicable? | Why/why not |
|---|---|---|---|
| `action_type = read` | Read-only access | No | No execution effect |
| `action_type = source_mutation` | Source file mutation | No (separate concern) | Governs repo writes, not invocation |
| `action_type = docs_mutation` | Docs file mutation | No | Same as above |
| `action_type = test_mutation` | Test file mutation | No | Same as above |
| `action_type = commit` | Git commit | No | Post-effect, not invocation |
| `action_type = push` | Git push | No | Post-effect, not invocation |
| `action_type = rollback` | Governed rollback | No | Distinct mutation-root concern |
| `action_type = shell_command` | Shell command policy | Partial (adjacent) | Overlaps process construction, not adapter dispatch itself |
| `action_type = backend_invocation` | Generic backend call | Partial | Closest existing sibling; no target/effect binding |
| `action_type = adapter_invocation` | Adapter call | **Yes, base** | Closest match; structurally insufficient per RPAC-REQ-044 (§5) |
| `execution_class = none/mutation/shell/backend/adapter/rollback` | Coarse effect-class tag | `adapter`/`backend` relevant | No sub-effect granularity (network vs process vs filesystem) |
| `simulation_only = True/False` | Binary real/sim gate | Yes — the only real/sim signal today | All-or-nothing; cannot express bounded real dispatch |

**Policy rules relevant to runtime dispatch** (from the same file, POL-001
through POL-005, `implementation_status = IMPLEMENTED`):

- **POL-004 (`MissingHumanApprovalRule`)** — scoped to
  `{shell, backend, adapter, rollback}` execution classes; if
  `approval_present` is `False`, returns `DECISION_HUMAN_REVIEW`
  (`requires_human=True`); if `True`, not triggered. This is the
  **only** existing rule that reads `approval_present` for
  execution-adjacent classes.
- **POL-005 (`ExecutionDisabledRule`)** — no execution-class restriction
  (`applicable_execution_classes` unset ⇒ applies to all); if
  `simulation_only` is `False`, unconditionally `DECISION_DENY`
  (`decision_reason="execution_boundary_unavailable"`); if `True`, not
  triggered.
- **Decision composition** (`_compose`, lines ~778–835): precedence is
  **DENY > HUMAN_REVIEW > ALLOW**; an empty policy result set fails
  closed to DENY; `ALLOW` is annotated `"policy_would_allow_if_execution_existed"`
  and is explicitly **never** an executable authorization (`INV-008`).

## 7. POL-005 contract role

POL-005 is an **invariant condition tied to a named missing component
(`COMP-002`, the execution boundary), not a permanent universal deny and
not merely a "temporary kill switch" in the reversible-flag sense.** Its
own `required_remediation` states the exact unblock condition: "This gate
cannot be satisfied until a future phase implements and verifies
`COMP-002`." It is "Unconditionally active by construction (NG-025)" —
by design, not by oversight — for every request where `simulation_only`
is `False`, regardless of `execution_class`. **What must change before it
can stop denying:** `COMP-002` (a real execution boundary) must exist and
be verified; POL-005 itself is not modified by this phase and this
architecture does not propose modifying POL-005 — it proposes what a
*future* real (non-simulation) request must look like and how it earns
the right to reach a policy state where POL-005 no longer denies it
(i.e., a future phase would need to either retire/scope POL-005 once
`COMP-002` exists, or add a new rule that governs the bounded conditions
under which a real request is permitted — that decision belongs to the
implementation phase, not this one).

## 8. Real dispatch effect decomposition

One "runtime dispatch" is not one effect. Decomposition, and where each
belongs, following the instruction to avoid overloading PB with effects
that belong elsewhere:

| Effect | Belongs to |
|---|---|
| Adapter invocation (call `adapter.dispatch()`) | **PB real-dispatch permission** (the coarse "may PCAE attempt this class of external effect at all" gate, 3T §11) + Runtime Enforcement (final whether-to-invoke) |
| Process spawn (local CLI) | **Shell Gate / equivalent process-construction policy** (RPAC-REQ-047/048) — PB permission is a precondition, not a substitute |
| Network egress (API provider) | **A future, separate network-permission mechanism** (RPAC-REQ-085) — not part of this phase's frozen dispatch-permission scope (see §52 disposition below); explicitly an open dependency |
| Provider request (API call itself) | **Adapter implementation**, gated by the network permission above once it exists |
| Filesystem mutation capability | **Existing `source_mutation`/`docs_mutation`/`test_mutation` PB actions**, applied unchanged to any runtime-produced change (3T §34) — not a new runtime-specific mutation permission |
| Credential use | **A future credential-reference architecture** (RPAC-REQ-084/058/059) — entirely unimplemented; out of scope for this phase's binding beyond referencing it |

This decomposition directly implements RPAC-REQ-085 ("Network, subprocess,
shell, filesystem mutation, outside-repo access, paid usage, and provider
selection SHALL each be explicit and default denied. One granted effect
SHALL not imply another.") by keeping PB's own scope narrow (adapter
dispatch permission only) rather than folding every effect into one PB
grant.

## 9. PB redesign options (evaluated)

**Option A — Dedicated real-runtime-dispatch action.** New
`action_type = "runtime_dispatch"` (or reuse `execution_class = "adapter"`
with the new action_type), carrying an enriched, composite request shape
bound to the immutable facts in §11 (target, adapter descriptor identity,
prompt digest, repository/task, human-authority reference, etc.), closing
RPAC-REQ-044 directly, without introducing new PB permissions for network/
process/filesystem (those remain owned elsewhere per §8).

**Option B — Existing `adapter_invocation` + `invocation_mode` enum.**
Keep the existing action_type; replace the binary `simulation_only` with
a normative `invocation_mode` enum (`simulation` / `real`), plus the
missing RPAC-REQ-044 fields bolted onto the existing request type.

**Option C — Composite permission model.** Separate PB permissions for
adapter dispatch, process, network, and repository mutation, each
independently deny-by-default, mirroring RPAC-REQ-085's "one granted
effect SHALL not imply another" literally inside PB itself.

## 10. PB redesign recommendation (Matrix B)

| Option | Semantic clarity | Backward compat. | Policy complexity | Least privilege | Future CLI/API support | Local CLI compat. | API provider compat. | Auditability | Risk of authority conflation | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| A — Dedicated action | High — new action name makes intent explicit | High — existing `adapter_invocation` callers (there are none in production per 3T §7) untouched | Moderate — one new action, existing rules extend via the action_type/execution_class match already in place | High — action is the coarse "may attempt at all" gate only; process/network/filesystem stay separately owned (§8) | High — new fields can grow without touching unrelated actions | High | High | High — one clearly-named action to trace in audit logs | Low — no ambiguity with existing `adapter_invocation` semantics | **Recommended** |
| B — Mode enum on existing action | Moderate — overloads an existing type's meaning; a reader must know the mode to know the semantics | High — POL-005's `if simulation_only` branch generalizes naturally | Lower — reuses existing structure | Moderate — mode enum still one action, less naturally separable from other adapter_invocation semantics | Moderate | Moderate | Moderate | Moderate — one action_type must be read alongside mode | Moderate — future non-runtime `adapter_invocation` callers (if any appear) inherit ambiguity | Not recommended (viable fallback) |
| C — Composite per-effect permissions | Highest in isolation — mirrors RPAC-REQ-085 exactly | Moderate — most new surface, more rules to keep in sync | Highest — N new rules, N request shapes | Highest in principle, but risks PB scope creep into process/network concerns already assigned elsewhere (§8) | Highest | Moderate — most implementation weight for the local-CLI-only v1 scope (§50/§62) | Highest (natural fit for network egress) | Highest per-effect, but most surface to audit-drift | Low per-effect, but highest overall implementation risk of one gate silently substituting for another during a large build | Deferred — right shape for **network egress specifically** (§52), wrong shape for the *core* dispatch-permission gate itself |

**Selected: Option A — Dedicated real-runtime-dispatch action
(`runtime_dispatch`).** Justification: RPAC-REQ-044's own text asks for a
request-shape amendment, not a proliferation of PB permission types; Step
7/§8's instruction to keep PB narrow (adapter dispatch only, not
process/network/filesystem) argues against Option C's most literal
reading (folding process/network into PB itself) even though C's
*principle* (deny-by-default, no effect implies another) is preserved —
just enforced by keeping those effects **outside** PB rather than by
multiplying PB actions. Option A gets Option C's core safety property
(no accidental broadening) at lower implementation and conflation risk,
by scoping the one new PB action narrowly to "may this specific,
human-authorized adapter dispatch be attempted at all," and by explicitly
deferring network-egress permission to a separate future mechanism (§52)
rather than inventing it here.

## 11. PB request binding (Matrix C — Authority binding, columns 1–2)

Minimum immutable facts a real-dispatch PB request must carry, each
justified:

| Bound fact | Included? | Justification |
|---|---|---|
| Invocation ID | Yes | Ties this specific request to one `RuntimeInvocationStore` record (3T §19); required for idempotency/audit (§54). |
| Repo identity | Yes | RPAC-REQ-013/044; without it PB cannot bind "this repository," only "some repository." |
| Task ID | Yes | Already present on `PermissionBrokerRequest`; needed for governed-lifecycle traceability. |
| Phase/session ID | Yes (phase; session only if session-scoped work exists at dispatch time) | Already present (`phase_id`); RPAC-REQ-046 requires "repository/task/HEAD freshness," which implies phase-lifecycle context. |
| Runtime target | Yes | RPAC-REQ-035's own no-fallback principle (already proven for the dry consumer, 3S.2.1) requires exact target binding; §35 below forbids "approve codex → dispatch claude." |
| Adapter descriptor identity/version | Yes (identity; version at preflight, not authorization time — see §36) | RPAC-REQ-086 requires supply-chain pinning; the *identity* must be bound at authorization time so approval cannot silently apply to a different adapter. |
| Prompt hash | Yes | RPAC-REQ-072's "changed prompt ... requires a new logical invocation and approval." |
| Requested capability | Yes | Distinguishes "invoke this adapter" from finer-grained capability classes as they are introduced. |
| Transport type | Yes (local-CLI vs API, coarse) | Needed to route to the correct downstream chain (3T §29) without conflating local-CLI and API trust requirements. |
| Network requirement | Yes, as a boolean/flag only (not a granted permission — see §8) | Lets PB/Runtime Enforcement see "this dispatch will need network" even though the actual network-egress grant lives outside PB (§52). |
| Filesystem scope | Yes, as a declared scope reference (e.g. "isolated worktree X"), not a grant | RPAC-REQ-082's anti-scope-broadening invariant; needed for audit even though the mutation grant itself stays with existing `source_mutation`/`docs_mutation` actions (§8). |
| Human-authority artifact reference | Yes | The entire point of this phase — PB must know *which* approval it is evaluating against, without embedding the approval itself (§23). |

**Excluded, with justification:** raw credential values (RPAC-REQ-084 —
never present in any request, ever); provider/model fields as a
*universal* requirement (§37 — only required when the target is an API
provider, not for local CLI, to avoid forcing irrelevant fields onto every
request); budget/cost fields as mandatory for v1 (§53 — deferred until an
API adapter exists, not needed for the local-CLI-only v1 scope of §50).

## 12. Human authority universe (Matrix A)

| Artifact/state | What it actually authorizes | Can authorize runtime invocation? | Why/why not |
|---|---|---|---|
| CHGR-001 (Canonical Human Governance Record) | Schema/artifact representation of a governance act | No | Own README: "Not implemented ... runtime consumption, or authority resolution." Successful validation proves shape conformance only, never that "the represented governance act was valid, applicable, current, or performed by an authorized human." |
| Interactive Workflow Confirmation (IWC) | Workflow-state/content acceptance ("I have read this") | No | RWMPC-REQ-023: "Confirmation is not approval ... SHALL NOT populate `approval_present`, regardless of which operation needs approval." |
| `approval_present` field on `PermissionBrokerRequest` | Generic missing-human-approval flag consumed by POL-004 | Not today | No current production caller sets it `True` from any runtime-invocation-specific human act (3T §12); it exists as a hook, not a populated authority signal. |
| Governed phase start/complete human decisions | Authorizes beginning/ending a *phase* of work | No | Coarser than one invocation; nothing in the phase lifecycle is scoped to "this specific external runtime invocation is authorized" (3T §12). |
| Task contract lifecycle (`pcae task new/close`) | Authorizes/scopes a unit of governed work | No | Same granularity problem as phase approval; task scope, not invocation scope. |
| AESIC / Authority Evaluation results | Disclosure of authority-relevant facts | No | RWMPC-REQ-023: "Authority Evaluation / AESIC results SHALL NOT be treated as permission or approval evidence — AESIC remains disclosure-only." |
| `--promotion-authorized`/`--reviewed-by`/`--approved-by` CLI flags (legacy) | Unauthenticated CLI self-declaration | No | RWMPC-REQ-024/025: no identity binding exists; not trusted approval evidence for any execution class today. |

**Gap column (all rows):** no existing mechanism produces a
subject-scoped, freshness-checkable, single-invocation authority artifact.
This is the gap §13–§22 close architecturally (without implementing it).

## 13. Preserve Confirmation boundary

Re-confirmed unweakened, verbatim: RWMPC-REQ-023 — "Confirmation is not
approval. Interactive Workflow Confirmation, task-finish health/check
validation, and any other process-hygiene confirmation artifact SHALL NOT
populate `approval_present`, regardless of which operation needs
approval. Authority Evaluation / AESIC results SHALL NOT be treated as
permission or approval evidence — AESIC remains disclosure-only." This
design does not propose any path by which IWC, task-finish validation, or
AESIC output can set `approval_present` or satisfy the new
`RuntimeInvocationApproval` artifact defined below (§14 selects a wholly
separate artifact precisely to avoid any temptation to reuse IWC for
this purpose).

## 14. Human runtime-authority requirements

A valid future human runtime authorization must prove, at minimum:

- **Who approved** — an identified human actor, not an unauthenticated
  CLI self-declaration (per RWMPC-REQ-024/025's own rejection of the
  weaker legacy flags).
- **What exact invocation** — bound to one `invocation_id`.
- **Which runtime target** — bound to one exact target identity, no
  fallback (§35).
- **Which repo/task** — bound to a specific repository identity and task
  ID (§34).
- **Which prompt/instruction hash** — bound to a canonical hash (§32).
- **Which capability/effect class** — at minimum "adapter dispatch, local
  CLI, no network," growing only as later phases add capability classes.
- **Validity/freshness** — an explicit freshness boundary (§17), not an
  implicit "still true" assumption.
- **One-shot or reusable** — must be explicit, not left ambiguous (§15).
- **Revocation/expiry** — an explicit lifecycle, even if v1 relies on
  short expiry plus one-shot consumption rather than an active revoke
  command (§18).

## 15. Human authority options (evaluated)

**Option A — Dedicated `RuntimeInvocationApproval` artifact.** A new,
narrowly-scoped record whose sole subject is "this invocation_id, this
target, this prompt digest, is authorized," with expiry and single-attempt
scope.

**Option B — Extend CHGR with a new record type/subject.** Add a
"runtime invocation authorization" record type to the existing CHGR
schema family, reusing its manifest/digest machinery.

**Option C — Bind to existing phase/session approval.** Treat the
governed-phase-start human decision as also covering a specific,
pre-declared invocation.

## 16. Human authority recommendation

**Selected: Option A — Dedicated `RuntimeInvocationApproval` artifact.**
Justification:

- Option C is rejected outright: 3T §43 already found it "weakest" because
  phase-level approval is categorically coarser than one invocation and
  would blur exactly the distinction (`registered != ... != authorized !=
  dispatched`) this phase is required to preserve. It also conflicts with
  §15's narrowest-authority default (below).
- Option B is rejected for this phase, not permanently: CHGR-001's own
  README explicitly disclaims "authority resolution" and "runtime
  consumption" as **not implemented**, and reusing CHGR's schema/manifest
  machinery for authority-*resolution* semantics it was never built to
  carry would require CHGR to gain a first authority-resolution consumer
  — a larger, separately-contracted change than this phase's scope. CHGR
  remains architecturally *reusable* as a schema-shape reference (Option
  B's representation ideas are not wasted — see §62's recommended future
  artifacts), but is not selected as the runtime-authority vehicle now.
- Option A is selected because it is the cleanest separation from CHGR/IWC's
  existing, deliberately non-authorizing scope (§13), and because
  RPAC-REQ-045's requirement that Runtime Enforcement evaluate "approval
  validity" as one bound, freshness-checked input is most naturally
  satisfied by a purpose-built, invocation-scoped artifact rather than a
  generic governance-record type or a coarse phase-level decision.

## 17. One-shot vs reusable approval

**Selected: one-shot (one invocation per approval).** Per the instruction's
own default ("prefer narrowest authority unless evidence supports broader
reuse") and 3T §62's already-established v1 scope restriction ("explicit
human approval every invocation ... no session-level or phase-level
standing approval"), no evidence in this repository supports session-wide
or phase-wide reuse for a first real-runtime capability. A positive
Runtime Enforcement decision must independently "expire" and be
"single-attempt scoped" per RPAC-REQ-046 regardless of the approval's own
scope — so even if a broader-scope approval existed, Runtime Enforcement
would still only ever authorize one attempt from it. One-shot approval
keeps the *human-authority* layer's scope no broader than the
*enforcement* layer's own single-attempt guarantee, avoiding a mismatch
where the human believes they approved "one thing" but the artifact could
be replayed for a second.

## 18. Approval subject identity

The subject of authorization is the tuple **(invocation_id, runtime_target,
prompt_hash, repo_identity, task_id)** — all five bound together, not any
one alone. Exact binding rule: an approval is valid **only** for the exact
combination it was issued against; changing *any* member of the tuple
(a different prompt, a different target, a different repository/task)
invalidates it (§19), consistent with RPAC-REQ-072's "a changed prompt,
target, provider/model, repository/task, effects, or budget requires a
new logical invocation and approval." The authorization is never reusable
for a different prompt, runtime, or repository — this is a hard binding,
not a soft hint.

## 19. Approval freshness

| Invalidating change | Classification |
|---|---|
| HEAD changes (new commit lands) | Mandatory for v1 — 3T §48 requires HEAD to be snapshot-bound at authorization time and re-checked; a HEAD drift invalidates. |
| Task state changes (closed/reassigned) | Mandatory for v1 — must be re-checked at dispatch time, not just authorization time (3T §48). |
| Prompt changes | Mandatory for v1 — prompt hash is part of the subject tuple (§18); any change is a different subject entirely, not merely "stale." |
| Runtime target changes | Mandatory for v1 — target is part of the subject tuple (§18); no fallback (§35). |
| Adapter config changes | Mandatory for v1 — RPAC-REQ-028's fail-closed-on-mismatch rule already requires this class of drift to be treated as invalidating. |
| Policy version changes | Mandatory for v1 — RPAC-REQ-046 requires the *decision* (not the approval per se) to be freshly evaluated, not cached; a policy-version change between approval and dispatch must force re-evaluation. |
| Timeout/expiry | Mandatory for v1 — an explicit, short validity window (§18's one-shot scope plus a bounded wall-clock expiry) is the minimum defense against a stale, forgotten approval being consumed much later. |

No item is deferred to "future extension" for v1 — all seven are load-bearing
given the TOCTOU analysis (§31) and RPAC-REQ-046's freshness language; a
narrower initial set was considered and rejected because RPAC-REQ-046
already names most of these facts explicitly ("target/status freshness,
repository/task/HEAD freshness, approval validity").

## 20. Approval revocation

**No explicit revocation mechanism is required before the first real
runtime capability.** One-shot consumption (§17) plus a short, bounded
expiry window (§19) together avoid stale authority without needing an
active "revoke" command: an approval that is never consumed simply
expires; an approval that is consumed is immediately no longer valid for
any subsequent attempt (§45's consumption-timing decision). An explicit
revocation command is a plausible **future extension** (e.g., a human
changes their mind after issuing approval but before dispatch) but is not
architected here — this phase records it as future work (§62), not as a
v1 requirement, because expiry-based staleness avoidance is sufficient
for the narrowest-authority v1 scope (§17/§62).

## 21. Authority storage

**Recommended: the `.pcae` canonical governance store**, alongside (but
architecturally distinct from) the existing `RuntimeInvocationStore`
pattern (3T §19) — i.e., a sibling record type under a canonical,
create-only, atomic-write directory structure (mirroring
`_write_create_only`'s `.tmp`-then-`Path.replace()` pattern already
proven safe), **not** folded into the CHGR store (§16 already rejected
CHGR as the authority-resolution vehicle for v1) and **not** attached
directly onto the invocation record itself (an approval must be
independently addressable and independently freshness-checkable *before*
an invocation record for that attempt necessarily exists — see the
creation-path ordering in §24). This phase does not implement any
storage location; it identifies the canonical-pattern family the future
implementation phase should reuse.

## 22. Authority artifact trust

Reusable/needed trust mechanisms:

- **Schema validation:** reuse the existing `schema_runtime` manifest/
  validation pattern already used by CHGR (`load_and_verify_manifest`,
  `validate_record_shape`) — the *pattern* is reusable even though CHGR
  itself is not the storage vehicle (§16/§21).
- **Subject binding:** the five-tuple in §18, hashed/embedded directly in
  the artifact, not inferred from filename or path alone.
- **Provenance:** the identified human actor (§14) recorded directly in
  the artifact, not resolved later from an external system.
- **Signature:** not required for v1 — the artifact lives in the same
  trust boundary as the rest of `.pcae`'s canonical governance store
  (repository-local, admin-controlled per §33), which today relies on
  filesystem/git provenance rather than cryptographic signing for
  equivalent artifacts (e.g. CHGR records); a future hardening phase
  could add signing without changing this architecture's shape.
- **Tamper detection:** reuse the existing digest/manifest pattern
  (already proven for CHGR/CLTR schema families) rather than inventing a
  new one.
- **Repo/task authority:** the artifact must be created only through a
  future, separately-designed human-facing creation flow (§24) bound to
  the same repository the invocation targets — no cross-repository reuse.

## 23. Approval creation path (design only, no CLI)

Future product flow: PCAE prepares a candidate invocation (prompt +
target selected, §24 of 3T's gate ordering) → PCAE presents the human with
the exact bound facts (target, prompt content/hash, repo/task, declared
effect class) → the human explicitly approves (an affirmative, identified
act — not a passive confirmation per §13) → a canonical
`RuntimeInvocationApproval` artifact is created, subject-bound per §18,
in the storage location of §21. This phase designs the flow; it does not
implement any CLI command for it (per Step 66/67's hard constraints).

## 24. Approval consumption path

Future flow: a runtime invocation request arrives → PCAE looks up the
referenced authority artifact by the reference carried in the PB request
(§11) → validates: artifact exists; artifact's subject tuple exactly
matches the current invocation's tuple (§18); artifact has not expired
(§19); artifact has not already been consumed (§17's one-shot rule) → only
if all validations pass does the approval "count" as present for PB
purposes (§26). **Fail-closed on**: artifact absent; artifact invalid
(schema/tamper); artifact stale (any §19 invalidating change detected);
subject mismatch; already-consumed (one-shot). Any of these results in
the same outcome as no approval at all — no distinct "partial credit"
state exists.

## 25. PB relationship to authority

**PB must independently validate approval; it does not receive the raw
approval artifact as an opaque trust token, and it does not merely trust
a caller-supplied boolean.** Concretely: the PB request (§11) carries a
**reference** to the authority artifact (an ID/digest), not the artifact's
full content and not a pre-computed "approved" boolean from an untrusted
caller. The approval-validation logic of §24 runs as an independent step
(logically prior to or alongside PB evaluation, not owned by PB itself)
and its *result* — specifically, whether `approval_present` may be set
`True` for this specific bound request — is what PB's existing
`MissingHumanApprovalRule` (POL-004) consumes. This preserves a clear
responsibility boundary: **the approval-validation step decides "is there
a valid, matching, fresh, unconsumed human authorization"; PB decides "is
this class of action currently permitted given all applicable policy,
including that validated authority signal."** PB never re-derives *who*
approved or *why*; it only consumes the fact of valid-and-current
approval, exactly as POL-004 already does today for `approval_present` in
general.

## 26. Gate sequencing (Matrix D)

Frozen conceptual order (extends 3T §45's candidate flow, now with the
approval-validation step made explicit as its own entry rather than
folded into "human authority"):

| Gate | Owner | Input | Output | Can authorize? | Failure effect |
|---|---|---|---|---|---|
| 1. Prompt prepared | PCAE core | Task/phase context | Prompt + hash | No | N/A (no dispatch attempted yet) |
| 2. Explicit runtime target selected | Caller (`--runtime-target`, no fallback) | Target ID | Bound target | No | Unknown/ambiguous target → stop before any gate |
| 3. Capability/preflight (static) | Runtime Registry / descriptor | Target descriptor | Static capability verdict | No | Structurally incapable target → stop before asking for human approval (§27) |
| 4. Human authority (creation, §23) | Human + PCAE presentation layer | Prompt/target/repo/task facts | `RuntimeInvocationApproval` artifact | **Yes — the only gate that can produce authority** | No artifact created → no further gate proceeds |
| 5. Approval consumption/validation (§24) | Approval-validation logic (owned separately from PB, §25) | Approval reference + current invocation facts | Valid/invalid verdict | No (validates existing authority, does not itself grant) | Invalid/stale/mismatched/consumed → fail closed, no PB request proceeds with `approval_present=True` |
| 6. Permission Broker (`runtime_dispatch`, §9/§10) | Permission Broker | Bound request incl. validated-approval signal | ALLOW / DENY / HUMAN_REVIEW | No (structural class-level permission only, §27 finding, `INV-008`) | DENY or unresolved HUMAN_REVIEW → no dispatch |
| 7. Runtime Enforcement (final gate) | Runtime Enforcement Coordinator | Complete bound request + PB decision + approval reference | Final whether-to-invoke decision, expiring, single-attempt (RPAC-REQ-046) | **Yes — the sole final "whether" authority (RPAC-REQ-045)** | Deny/blocked → no dispatch |
| 8. Process/network containment | Shell Gate (local CLI) / future network mediation (API) | Fixed argv / endpoint policy | Enforced "how" boundary | No | Non-conforming construction → stop before spawn |
| 9. Durable pre-dispatch record | `RuntimeInvocationStore` (extended, §30) | All gate outputs/digests | Durable "dispatch attempted" marker | No | Write failure → no dispatch attempted |
| 10. Adapter dispatch | Adapter implementation | Enforced request | External effect | No | N/A — first true external effect boundary |
| 11. Result capture + intake | Existing Stage-B pipeline (unmodified) | Untrusted result | Intake candidate | No | Malformed result → fail closed, not silently accepted |

**Justification for ordering:** gates 1–3 are cheap and reversible (no
human time or policy evaluation spent on a structurally impossible
target); gate 4 must precede gate 5 (nothing to validate before it
exists); gate 5 must precede gate 6 (PB's `approval_present` signal is a
*consumer* of validated authority, never a raw claim); gate 6 must precede
gate 7 per RPAC-REQ-045's explicit text ("after ... Permission Broker
permission ... [before Runtime Enforcement]"); gate 7 must precede gate 8
per RPAC-REQ-047 ("Runtime Enforcement determines whether invocation may
happen. Shell Gate ... constrains how ... Neither substitutes for the
other."); gate 9 must precede gate 10 for the durable-before-effect
property (§30); gates 10/11 are the effect and its (always-untrusted)
aftermath.

## 27. Capability before authority

**Yes — static/cheap capability preflight (gate 3) runs before human
authority (gate 4).** It is semantically safe because a static descriptor
check answers only "can this target structurally execute at all"
(RPAC-REQ-011's "immutable descriptive facts"), never "is this
invocation currently permitted" — asking a human to approve a target that
cannot possibly execute wastes their attention and risks approval fatigue
without any compensating safety benefit. **Dynamic capability must still
be rechecked immediately before dispatch** (gate 8/9 boundary, matching
3T §16): RPAC-REQ-012 forbids descriptors from carrying live availability/
authentication/dispatch state, so a **live preflight** is required late in
the pipeline (after human authority and PB/Runtime Enforcement, before the
actual spawn) to catch drift between authorization time and dispatch time
— this is also required independently by the TOCTOU analysis (§31).

## 28. PB before Runtime Enforcement

**Yes, PB runs before Runtime Enforcement (gate 6 before gate 7),
matching RPAC-REQ-045's explicit ordering.** Justification: failure-before-
effect economics favor evaluating the coarser, cheaper structural
question (PB: "may PCAE attempt this class of action at all, given
policy and the validated-approval signal") before the more expensive,
fully-bound final evaluation (Runtime Enforcement: "the complete bound
request, all effect-specific permission decisions, target/status
freshness, repository/task/HEAD freshness, approval validity, and no-go
evidence," per RPAC-REQ-046). This mirrors the existing architecture's own
intent (RPAC-REQ-045's literal ordering) and is not overridden by any
contract evidence found in this phase.

## 29. Runtime Enforcement handoff (evidence projection)

Runtime Enforcement must **not** infer authority from PB ALLOW alone
(PB's own composition logic already documents this: `ALLOW` means only
`"policy_would_allow_if_execution_existed"`, annotated `INV-008`, "Never
an executable authorization") and must **not** infer authority from
approval alone (approval only proves a human authorized this specific
invocation subject — it says nothing about current policy state, target
freshness, or no-go evidence). The exact **projection** — the subset of
facts that crosses the PB→Runtime-Enforcement boundary — is:

- The full bound request (§11's fact set), unchanged.
- PB's decision value (`ALLOW`/`DENY`/`HUMAN_REVIEW`) and its
  `causing_policy_ids`/`matched_no_go_ids` (existing `PermissionBrokerDecision`
  shape, unmodified) — as **evidence**, not as an authority Runtime
  Enforcement merely rubber-stamps.
- The validated-approval reference (not the raw artifact) plus its
  freshness verdict from gate 5 — so Runtime Enforcement can
  independently re-verify "approval validity" per RPAC-REQ-046's own
  text, rather than trusting PB's prior read of it.
- Target/status freshness facts captured at gate 3/8 (live preflight),
  re-verified, not merely passed through from an earlier snapshot.

Runtime Enforcement's own decision remains the only value that can
produce a "may dispatch" outcome; PB's role is strictly evidentiary input
to that decision, consistent with 3T §44's finding that the existing
design-only evidence-bundle vocabulary (`adapter_execution_authorized`,
`network_authorized`, etc.) is a good target shape for this projection
via an adapter-specific translation layer, not a wholesale replacement of
the existing Runtime Enforcement Coordinator/evidence-bundle family.

## 30. Execution Attempt Boundary mapping

Read from `docs/PHASE_99_GOVERNED_EXECUTION_ATTEMPT_BOUNDARY_DESIGN.md`:
"A governed execution attempt is a **future**, explicitly scoped,
human-approved, ..." boundary; the design explicitly enumerates what is
**not** an execution attempt (§23 of that document) to keep the boundary
narrow. Mapping this phase's gates onto that existing boundary, without
redefining it:

- **Before execution attempt:** gates 1–6 (prompt prep, target selection,
  static preflight, human authority creation, approval validation, PB
  permission) — all of these occur before anything Phase 99 would
  recognize as an "attempt."
- **Execution-attempt decision point:** gate 7 (Runtime Enforcement's
  final whether-to-invoke decision) — this is the moment Phase 99's
  "human-approved" boundary condition is fully discharged, matching
  RPAC-REQ-045's "final whether-to-invoke gate" framing exactly.
- **First external effect:** gate 10 (adapter dispatch) — the actual
  process spawn or network call, after containment (gate 8) and durable
  persistence (gate 9).

This phase does not redefine Phase 99's boundary; it places the new gates
(4–9) entirely within the "before execution attempt" region that Phase 99
already anticipated but left unspecified in detail.

## 31. Invocation record binding

A future persistent `RuntimeInvocationRecord` should link, by
**reference/hash, not by duplicating full content** (per the instruction's
own preference): the approval artifact (by its own ID/digest, not a copied
approval document — avoiding two authoritative copies of the same fact);
the PB decision (by digest, extending `RuntimeInvocationStore`'s existing
atomic-write pattern, §21 of 3T); the Runtime Enforcement decision (by
digest, same extension); the adapter target (by descriptor identity/version,
already the pattern for the mock adapter); the prompt hash (already
identified as a new required field, 3T §47). This avoids the invocation
record becoming a second authoritative copy of the approval or PB/RE
decisions — it becomes the durable *index* that ties references together,
which is exactly the atomic, timestamped, per-attempt document model
`RuntimeInvocationStore` already implements (3T §19/§55), extended with
new fields rather than a new mechanism.

## 32. Durable-before-effect (minimum set)

Must be durably persisted **before** any real external effect (extends 3T
§47's set with the approval reference made explicit as its own item):

1. Invocation ID (already the case today).
2. Repository/task binding (already the case today, per the dry
   consumer's `resolve_dry_consumer_context` pattern).
3. Runtime target identity (already the case for the request record).
4. Prompt hash (new field — not currently persisted).
5. Human-authority artifact reference/digest (new).
6. PB decision + digest (new — PB decisions are not persisted to the
   invocation store today).
7. Runtime Enforcement decision + digest (new — same gap).
8. Dispatch intent/state marker ("dispatch attempted," written
   immediately before the process/network call — new, and the single
   most safety-critical addition per the crash-window analysis, §46/§47).

Credential *values* must never appear in this set (RPAC-REQ-084) — only
references, once a credential-reference architecture exists (out of scope
here).

## 33. TOCTOU model (Matrix E)

| Mutable fact | Approval bound? | Revalidate before PB? | Revalidate before dispatch? |
|---|---|---|---|
| HEAD | Yes — snapshot-bound at authorization time (part of repo binding, §34) | Yes | Yes — must match at dispatch, not just at authorization |
| Task state | No (not part of the subject tuple itself, but a freshness condition, §19) | Yes | Yes — task could close/reassign between PB and dispatch |
| Prompt | Yes — hash is part of the subject tuple (§18) | Yes (hash re-derived and compared) | Yes |
| Runtime target | Yes — part of the subject tuple (§18) | Yes | Yes — no fallback (§35) |
| Adapter config | Snapshot-bound at authorization time (RPAC-REQ-028) | Yes (fail-closed on mismatch) | Yes — live preflight (§27) |
| Adapter executable identity | Pinned at descriptor level, not authorization time | N/A (belongs to preflight, §36) | Yes — hash-check immediately before spawn (§36/3T §50) |
| Policy version | Not bound to the approval itself | Yes — Runtime Enforcement decision must not be cached (RPAC-REQ-046 "SHALL expire") | Yes |

**Must be snapshot-bound (at authorization time):** HEAD, prompt hash,
runtime target, adapter config identity. **Must be freshly re-checked
immediately before dispatch (not merely snapshot-bound):** task state,
adapter executable identity/hash, policy/decision freshness — this list
matches 3T §48 exactly and is not altered by this phase, since 3T's
TOCTOU analysis is evidence-derived and unchanged by the PB/authority
design decisions made here.

## 34. Prompt hash semantics

Canonical hashing rule: hash **only the semantically load-bearing prompt
content** the adapter will actually receive (the resolved instruction
text/context that determines behavior) — **not** unstable formatting or
environment metadata that does not change what is being asked (e.g.
timestamp strings embedded purely for display, ephemeral request IDs
generated after the hash would be computed). This avoids two failure
modes: hashing too little (missing a semantically meaningful change,
defeating RPAC-REQ-072's "changed prompt ... requires a new ... approval")
and hashing too much (invalidating approval on cosmetic/non-semantic
noise, undermining the narrowest-but-still-usable authority goal of §17).
This phase does not specify the exact algorithm or canonicalization
procedure — that is implementation detail for a future phase — only the
*inclusion/exclusion principle*.

## 35. Repository binding

Canonical repository identity must **not** be trusted from path alone if
a stronger mechanism exists. This repository already has a stronger
pattern: the dry-runtime consumer's `resolve_dry_consumer_context`
(3S.2 design, corroborated at 3T §23/§28) derives repository/HEAD facts
from the real git repository state, not from a caller-supplied path
string — that same pattern (git-derived repository fingerprint, not a
raw path) is the correct binding mechanism to reuse for the human-authority
and PB binding here, rather than inventing a new repository-identity
primitive.

## 36. Task/session/phase binding

**Task ID and phase ID** must be bound (both already exist as fields on
`PermissionBrokerRequest`, and RPAC-REQ-046 explicitly names "repository/
task/HEAD freshness"). **Session ID** is bound only when the invocation
occurs within an explicitly session-scoped interactive workflow context
(per the Interactive Workflow Confirmation architecture, 143K–143P) —
requiring a session ID universally would force irrelevant fields onto a
plain governed-phase-driven invocation that has no interactive session at
all. This is a deliberate "avoid requiring all three if one is not
relevant" application per the instruction's own guidance.

## 37. Runtime target binding

Approval and PB must bind to the **exact** runtime target — no fallback,
matching the already-proven no-fallback pattern from the dry consumer
(3S.2.1's ten tested unknown/case/whitespace/typo/identity/provider-name
variants, all correctly rejected with no fallback). "Approve codex →
dispatch claude" must be structurally impossible: the subject tuple (§18)
includes the exact target, and gate 5's approval-validation step fails
closed on any mismatch (§24).

## 38. Adapter descriptor/config binding

Human approval should bind to the **adapter ID/identity only** (a stable,
human-meaningful name — "this local CLI target"), **not** to a specific
descriptor hash/version or executable path/version. Rationale: version/hash
pinning is a **preflight/Runtime-Enforcement-time** concern (RPAC-REQ-086,
already assigned there in 3T §50/§51), not something a human should have
to re-approve every time the executable is patched — requiring the human
to re-approve on every version bump would create approval fatigue that
degrades the value of the one-shot narrow-authority model (§17) without a
matching safety benefit, since the *identity-drift* risk this would guard
against is already independently caught by the mandatory pre-dispatch
hash-check (§33/§36 of 3T).

## 39. Provider/model binding

For a future API adapter, human approval **must** include provider/model
identity, since RPAC-REQ-028 requires provider/model to be "snapshotted
... with fail-closed mismatch detection" and a human cannot meaningfully
approve "call some AI provider" without knowing which one. For local CLI,
provider/model concepts are **opaque and not required** — forcing a
universal provider/model field onto every request (including local CLI,
which has no such concept) would violate the instruction's own guidance
("design extensibly without forcing provider/model fields universally").
The request shape (§11) therefore treats provider/model as
**target-type-conditional**, not universal.

## 40. Permission failure semantics

Existing exact vocabulary, verified by direct source read (§6): `ALLOW`,
`DENY`, `HUMAN_REVIEW` (`DECISION_VALUES` in
`permission_broker_foundation.py`), composed with precedence
**DENY > HUMAN_REVIEW > ALLOW**. For real dispatch:

- **DENY** (e.g. POL-005 today) → no dispatch, unconditionally, regardless
  of any human authority state (§45's invariants).
- **ALLOW** → never itself an executable authorization (`INV-008`,
  unchanged) — it means only that no rule currently blocks this class of
  action; Runtime Enforcement's separate decision is still required.
- **HUMAN_REVIEW** → see §41 (mandatory dedicated analysis).

## 41. HUMAN_REVIEW semantics (mandatory)

**Direct source evidence, not guessed:** `MissingHumanApprovalRule`
(POL-004) is the existing rule that produces `HUMAN_REVIEW`, and its own
logic is exactly: `if request.approval_present: return _not_triggered(...)`
— i.e., **`HUMAN_REVIEW` from POL-004 already means "no valid human
approval signal is present for this request"; a valid, matching,
current, unconsumed `RuntimeInvocationApproval` (per gate 5's validation,
§24–§25) is precisely the condition under which `approval_present`
becomes `True` and POL-004 resolves to not-triggered instead.**

**Frozen intended meaning:** if the runtime invocation already has
explicit, valid human authorization (gate 4/5 passed), **POL-004's
`HUMAN_REVIEW` for this action does not fire at all** — the same
authorization artifact that satisfies gate 4/5 is exactly what makes
`approval_present=True` true for POL-004's evaluation. This is **not**
"additional review beyond the approval already obtained," and it is
**not** "policy escalation on top of a satisfied approval" — those
readings would create a contradictory design where obtaining approval
somehow triggers a *different* human-review requirement, defeating the
approval's purpose. It is also **not** treated as automatically
reusable-for-a-different-request "if bound strongly enough" — the binding
(§18) is exact-tuple-only; a `HUMAN_REVIEW` on a *different* request
(different prompt/target/repo/task) is a wholly separate evaluation and
is not satisfied by an approval scoped to a different tuple. If some
*other*, currently-unspecified future policy rule independently produces
`HUMAN_REVIEW` for reasons unrelated to `approval_present` (e.g. a future
budget-threshold rule), that is a distinct future policy decision, out of
scope here, and must not be conflated with POL-004's existing, narrower
meaning.

## 42. Approval vs PB HUMAN_REVIEW relationship

The loop the instruction warns against ("human approves → PB says
HUMAN_REVIEW → same approval is reinterpreted as satisfying it, unless
explicitly contracted to do so") is **explicitly contracted to occur, by
design, for POL-004 specifically** — this is not an accidental
reinterpretation; it is POL-004's documented, pre-existing behavior
(§41), which this phase's authority design deliberately feeds. No other
policy rule's `HUMAN_REVIEW` is reinterpreted this way by this
architecture — only POL-004's own, narrowly-scoped
"is `approval_present` true" question is resolved by gate 5's validated
authority signal. This is not a new loophole; it uses the *existing*
`approval_present` consumption contract exactly as already implemented
and does not extend it to any other rule.

## 43. Simulation compatibility

The dry (`simulation_only=True`) path is **entirely untouched** by this
architecture: every new field, gate, and artifact type described above
applies only when a request is being constructed as a **real**
(`runtime_dispatch`, non-simulation) request. `pcae session bootstrap
--compact --dry-runtime --runtime-target <id>` continues to build
`simulation_only=True` requests exactly as today (3S.2/3S.2.1, unmodified);
POL-005 continues to not-trigger for those requests exactly as today;
no new required field is retrofitted onto the existing dry-consumer code
path. This phase's design adds a **new**, additive action/request shape
(§9's Option A) rather than mutating the existing `adapter_invocation`
shape the dry consumer already uses.

## 44. Backward compatibility

No existing PB behavior changes for: rollback (unrelated `execution_class
= rollback`, untouched); push (unrelated `action_type = push`, untouched);
publication (uses existing, unrelated action types); other mutation roots
(`source_mutation`/`docs_mutation`/`test_mutation`, untouched, and
explicitly reused unchanged for runtime-produced changes per §8); dry
runtime simulation (§43). The new `runtime_dispatch` action type is
strictly additive — no existing `KNOWN_ACTION_TYPES`/`KNOWN_EXECUTION_CLASSES`
member is removed, renamed, or redefined by this design.

## 45. Policy/authority versioning

**Policy versioning:** PB policy/version identity must be bound to
dispatch evidence — specifically, the Runtime Enforcement decision (gate
7) must record which policy version it evaluated against, and RPAC-REQ-046's
"SHALL expire" requirement means a policy change after approval but
before dispatch invalidates any cached decision; the correct behavior is
**re-evaluation, not silent continuation** — Runtime Enforcement must
re-run against current policy immediately before dispatch (already
implied by §33's TOCTOU table).

## 46. Authority versioning

If the `RuntimeInvocationApproval` artifact type is introduced (§16), it
must follow the same additive-evolution discipline already established
for CHGR/CLTR schema families in this repository (versioned schema,
backward-compatible field addition only, no silent redefinition of an
existing field's meaning) — this phase does not freeze that schema (Step
62 forbids prematurely freezing a production contract), only the
principle that it must be versioned like its siblings.

## 47. Invocation consumption semantics

**Selected consumption point: immediately before dispatch (gate 9,
durable "dispatch attempted" marker), not at PB ALLOW and not at Runtime
Enforcement ALLOW alone, and not only after confirmed dispatch.**
Crash-window analysis (extends 3T §20/§56):

| Consumption point | Crash window analyzed | Verdict |
|---|---|---|
| At PB ALLOW | If PCAE crashes between PB ALLOW and Runtime Enforcement, the approval is already "spent" even though Runtime Enforcement never ran — a legitimate retry would need fresh approval for no real reason (Runtime Enforcement, not PB, is the authoritative "may proceed" gate) | Rejected — spends authority too early |
| At Runtime Enforcement ALLOW | Crash between RE ALLOW and the actual spawn leaves the approval consumed with zero external effect having occurred — recoverable, but conflates "PCAE decided to attempt" with "an attempt happened" | Rejected — still slightly too early relative to the effect boundary |
| **Immediately before dispatch (with durable marker)** | Crash after the marker is written but before/during spawn is the genuinely dangerous, unavoidable uncertain-outcome window (3T §20) — but this window exists *regardless* of when consumption happens, so tying consumption to the same moment as the durable marker keeps the "was this attempted" question and the "is this authority spent" question answered by the *same* durable write, avoiding a second, separately-inconsistent bookkeeping state | **Selected** |
| After confirmed dispatch | If PCAE crashes after spawn but before confirming, the approval remains technically "unconsumed" despite an external effect having already been attempted — this is the worst option, since a naive retry-on-restart could use the *same*, still-valid approval to attempt a duplicate effect | Rejected — highest duplicate-effect risk |

Consuming the approval **at the same durable write that marks "dispatch
attempted"** (gate 9) is the only option that ties authority-spending to
the actual effect boundary rather than to an internal decision that could
occur without any external effect happening at all.

## 48. Crash-before-dispatch

If approval is marked consumed at gate 9 (durable marker written) but the
spawn never actually happens (e.g., crash between marker-write and
process-start), recovery must treat this as: no external effect occurred
(consistent with 3T §20's "record persisted → process not started:
recoverable"), but the *approval itself* is now consumed and **must not**
be silently reused — retry requires **fresh** human authorization (§21 of
3T: retry after any uncertain-outcome crash window requires fresh
authorization unless the prior approval's attempt limit/expiry explicitly
covers it, and this design's one-shot approval, §17, has no such
"attempt limit" beyond one, so a fresh approval is always required after
this crash window). This deliberately trades a small amount of
convenience (one wasted approval on a no-op crash) for eliminating any
path where a marker-write ambiguity could be exploited to bypass fresh
authorization.

## 49. Crash-after-dispatch

If the process/provider call may have happened (the dangerous window
identified at 3T §20), the durable record transitions to an explicit
**uncertain/recovery state** distinct from both "not attempted" and
"completed" — matching 3T §56's restart/recovery matrix finding that this
window currently has no representation at all ("N/A — no dispatch layer
exists"). The approval remains consumed (§47) and must **never** be
treated as authorizing a blind replay; any subsequent attempt is a
logically new invocation requiring fresh authorization (§48), and the
uncertain-outcome record itself becomes a durable audit artifact a human
must review before any related retry is authorized.

## 50. Retry authority

**Selected: fresh approval, always, for the first version** — no reuse of
the original approval and no "explicit retry approval linked to the
original invocation" shortcut for v1. This is the safety-preferring
option explicitly invited by the instruction ("Prefer safety") and is
directly consistent with RPAC-REQ-072 ("Every retry requires ... human
authorization when the prior approval's attempt limit/expiry does not
cover it") combined with this design's one-shot approval having no
attempt-limit headroom at all (§17). A future, separately-authorized
extension could define a narrower "linked retry approval" concept once
real-world experience justifies it (§62) — this phase does not design
that extension now.

## 51. Multi-effect invocations

**Selected: one bounded external dispatch per invocation for v1** — no
process+network combination, no multiple subprocesses, no multiple
provider calls within a single invocation. This directly matches 3T §62's
already-established v1 scope restriction ("no parallel invocations") and
simplifies both the TOCTOU surface (§33) and the process-supervision
surface (3T §22/§37) to a single, auditable effect boundary per approval.

## 52. Local CLI specialization

Minimum authority/permission fields for the initial generic local
executable (per §11, specialized): runtime target (exact, no fallback,
§37); command descriptor identity (adapter ID, §38); repo/task (§35/§36);
prompt hash (§34); **no network field required to be `True`** (a
no-network local executable simply never sets the network-requirement
flag, and no network PB action is invoked at all — 3T §26/§29's finding
that local CLI can be satisfied "without ever needing a network PB action
at all"); bounded filesystem scope (declared isolated-worktree reference,
§8/3T §25/§33). This phase does **not** design full API-provider
complexity (credential reference, cost/budget, provider/model mandatory
fields) into the v1 shape — those fields are present in the schema only
as target-type-conditional additions (§39), never mandatory for a local
CLI request.

## 53. API-provider extension

A future API provider extends the same request shape with: network
permission (a still-undesigned, separate mechanism — §54); provider/model
identity (mandatory for API targets only, §39); cost/budget fields
(RPAC-REQ-044's own list; entirely deferred, §56); credential reference
(RPAC-REQ-084/059, entirely unimplemented — deferred). These are
additive extensions to the same `runtime_dispatch` action (§9's Option A),
not a parallel action family, keeping one auditable action type across
both target-type chains while allowing target-type-conditional fields.
This phase keeps all of this **outside** the initial v1 design, per the
instruction's own guidance and 3T §62's local-CLI-only v1 scope.

## 54. Network permission disposition

**Explicitly flagged as an open dependency, not resolved by this phase.**
3T found no PB network action exists at all (confirmed independently
again in §6/§8 above: no "network" string in `KNOWN_ACTION_TYPES`/
`KNOWN_EXECUTION_CLASSES`). This phase's decomposition (§8) assigns
network egress to "a future, separate network-permission mechanism,"
deliberately outside the frozen `runtime_dispatch` PB action's scope,
because designing the network path prematurely — before its own dedicated
architecture phase — risks exactly the effect-conflation Option C (§9)
was built to avoid, folded into the wrong action. **This phase does not
design the API-provider runtime path first, and flags network permission
as a hard, unresolved prerequisite of any future API-provider capability**
(consistent with 3T §26/§58's classification of this as "Yes — blocking"
for any API provider). The local-CLI v1 path requires no resolution of
this dependency at all (§52).

## 55. Filesystem mutation authority

Real runtime dispatch permission (the new `runtime_dispatch` PB action)
must **not** automatically authorize arbitrary repository mutation.
Runtime write capability remains represented by the **existing, separate**
`source_mutation`/`docs_mutation`/`test_mutation` PB actions, applied
identically to any file a runtime or its output touches (§8, matching 3T
§34's "existing intake/review/promotion gates remain fully intact and
unmodified"). A `runtime_dispatch` ALLOW never implies a mutation-action
ALLOW, and vice versa — this is the concrete instance of RPAC-REQ-085's
"one granted effect SHALL not imply another" for the mutation case
specifically.

## 56. Shell/process authority

PB `runtime_dispatch` permission likewise does **not** mean "any
subprocess command permitted." The adapter's configured command/process
boundary remains independently constrained by Shell Gate or an equivalent
enforcing process-construction policy (§8/§26 of this document; RPAC-REQ-047's
"Shell Gate or an equivalent local process policy constrains how a local
command is constructed/launched. Neither substitutes for the other.").
Today's Shell Gate remains, unmodified by this phase, "a read-only
command classifier ... Never executes command text. Never grants
authorization" (`shell_gate.py` docstring, re-confirmed unchanged) —
real local-CLI dispatch remains forbidden until Shell Gate or its
equivalent becomes enforcing (RPAC-REQ-048), independent of whatever PB
decides.

## 57. Two 3S.2.1 MUST-FIX findings (disposition)

Recovered verbatim again, directly from
`docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md`
§62/§63 (via 3T §40, cross-checked, unchanged):

- **Finding 1 — malformed adapter result crashes uncaught** (`simulate_invocation`
  → `write_result` `AttributeError` instead of `FAILURE_MALFORMED_RESULT`).
  **Does this new authority/permission architecture make it reachable?**
  No — this architecture governs *whether* a dispatch may be attempted
  (gates 1–9); it does not change how `simulate_invocation`/`write_result`
  handle a non-conforming adapter return value. It remains unreachable
  until a second (real, non-mock) adapter is registered — the same
  disposition 3T recorded. **Classification: PREREQUISITE REPAIR, not
  performed in this phase** — required before or as part of the first
  real adapter implementation, per 3T's own ordering, unchanged here.
- **Finding 2 — `invocation_id` path-traversal in `RuntimeInvocationStore`.**
  **Does this architecture make it reachable?** No — this design's new
  fields (prompt hash, approval reference, PB/RE decision digests, §32)
  extend the record schema but do not introduce any new caller-supplied-
  `invocation_id` surface; `invocation_id` remains internally generated
  (`new_invocation_id()`) in every gate described above. **Classification:
  unchanged — non-blocking until a future surface accepts an
  externally-influenced `invocation_id`.** Neither finding is repaired in
  this phase (Step 55 explicitly forbids repair here); both are carried
  forward as prerequisite items for whichever future phase implements the
  first real adapter or a resume/retry surface.

## 58. Runtime inspect limitation disposition

The `TRUTHFUL_WITH_LIMITATION` verdict (3S.2.1/3T §41: the dry consumer's
transient per-call registry is structurally disconnected from the
persisted registry `pcae runtime inspect` queries) is **unaffected in
substance by this phase's architecture** — this phase adds no new
registry-consuming code path. Its **urgency is unchanged, not increased or
decreased**: it must still be repaired **before the first real adapter is
registered** (3T's conclusion, reconfirmed here), because once a real
adapter and a real `RuntimeInvocationApproval`/PB/Runtime-Enforcement
chain exist, an operator relying on `runtime inspect` to answer "is real
execution available" needs the tool to see the actual capability in
question. This phase does not implement that repair (Step 55/66 forbid
it).

## 59. Authority threat model

| Threat | Mitigation in this architecture |
|---|---|
| Forged approval | Schema/tamper-detection reuse (§22); subject-tuple binding (§18) means a forged artifact must also forge a matching, currently-valid tuple, which is only creatable through the human-facing creation flow (§23) |
| Stale approval | Explicit freshness set (§19) plus bounded expiry (§20); gate 5 fails closed on any staleness signal |
| Approval reuse | One-shot consumption at gate 9 (§47); a consumed approval fails gate 5 on any subsequent attempt |
| Approval for different runtime | Exact-tuple binding, no fallback (§18/§37) — a mismatch on `runtime_target` fails gate 5 |
| Approval for changed prompt | Exact-tuple binding on prompt hash (§18/§34) — any prompt change fails gate 5 |
| Repo/task swap | Exact-tuple binding on repo/task (§18/§35/§36) — a mismatch fails gate 5 |
| Approval tampering | Same tamper-detection reuse as "forged approval" |
| Approval replay after crash | §48/§49's explicit consumption-at-effect-boundary rule plus mandatory fresh-authorization-on-retry (§50) — a replayed, already-consumed approval fails gate 5's one-shot check |

## 60. Permission threat model

| Threat | Mitigation |
|---|---|
| PB request manipulation | Structural validation already exists in `PermissionBroker.evaluate` (fails closed on non-`PermissionBrokerRequest` input, §6); new fields (§11) are part of the same immutable, `frozen=True` dataclass discipline already used for `PermissionBrokerRequest` |
| Simulation flag downgrade/upgrade | `simulation_only`/the future real-request path (§9 Option A) are structurally distinct action types once implemented — a "downgrade" from real to simulation is not meaningful (simulation is strictly less capable), and an "upgrade" from simulation to real requires constructing an entirely different, gate-4/5-validated request, not flipping a flag on an existing one |
| Execution-class confusion | The new `runtime_dispatch` action (§9/§10) is deliberately distinct from existing `adapter_invocation`/`backend_invocation`, avoiding ambiguity about which semantics apply |
| Action-type confusion | Same as above — Option A was selected specifically to avoid the moderate action-type-confusion risk Option B carried (§10's Matrix B) |
| Policy-version drift | §45's re-evaluation requirement (Runtime Enforcement decision must not be cached across a policy-version change) |
| PB decision replay | PB decisions are per-request evaluations with no side effects (`PermissionBroker.evaluate` "Never executes them, never has side effects") and must be freshly persisted per invocation (§32) — a "replayed" decision from a different invocation would fail the invocation-ID binding at the invocation-record layer |

## 61. Cross-gate threat model

All three confusions named by the instruction are made structurally
impossible by this design, not merely discouraged by convention:

- **Approval interpreted as permission:** impossible by construction —
  approval only ever feeds gate 5's validation, which produces a
  `approval_present` *signal* for PB to consume (§25); approval itself
  never appears as a PB decision, and PB's own `ALLOW` is independently
  annotated `INV-008` ("Never an executable authorization") regardless of
  why it fired.
- **PB ALLOW interpreted as authorization:** impossible by construction —
  PB `ALLOW` is defined, unchanged, as
  `"policy_would_allow_if_execution_existed"`; this design does not
  modify that semantic, and Runtime Enforcement (gate 7) is the only
  component this architecture assigns the power to authorize dispatch
  (§29).
- **Runtime Enforcement ALLOW interpreted as both authority and
  permission:** guarded by §29's explicit non-inference rule ("must NOT
  infer authority from PB ALLOW alone, or from approval alone") — Runtime
  Enforcement's decision is a *third*, independently-computed value that
  consumes both prior signals as evidence, never substitutes for either,
  and its own positive decision is itself scoped and expiring
  (RPAC-REQ-046), never treated as a standing grant of either PB
  permission or human authority for a future, different invocation.

## 62. Authority/permission security invariants (Matrix F)

| Threat | Contract invariant | Existing control | Missing control |
|---|---|---|---|
| No approval → real dispatch | No approval → no real dispatch | POL-004's `approval_present` gate (existing) | Runtime-invocation-specific approval production (§23, not implemented) |
| Stale approval → real dispatch | Stale approval → no real dispatch | None today (no approval type exists to be stale) | Gate 5 validation logic (§24, designed not implemented) |
| Approval mismatch → real dispatch | Mismatch → no real dispatch | None today | Subject-tuple exact-match check (§18/§24) |
| PB DENY → real dispatch | PB DENY → no real dispatch | Existing `DECISION_DENY` precedence (`_compose`, unchanged) | None — already enforced today for every request shape |
| PB failure → real dispatch | PB failure/empty-registry → no real dispatch | Existing fail-closed-to-DENY on empty `results` (`_compose`, "An empty `results` tuple ... fails closed to DENY") | None |
| PB ALLOW without approval → real dispatch | Must not happen | POL-004 already fires `HUMAN_REVIEW` (not ALLOW) when `approval_present=False`, for the relevant execution classes | None additional — existing behavior already prevents this for the classes POL-004 covers |
| Approval without PB ALLOW → real dispatch | Must not happen | Gate 6 (§26) is a required step in the frozen ordering — approval alone never reaches gate 10 | Enforcement of the gate ordering itself (implementation, not this phase) |
| Runtime Enforcement deny → real dispatch | RE deny → no real dispatch | Existing REC_STATUS_*/REC_RESULT_* vocabulary has no "granted" terminal state at all today (3T §14) — fail-closed by construction | A real "authorized" terminal state must be added when RE becomes a real consumer (future phase, not this one) |
| Runtime unavailable → dispatch | Unavailable runtime → no dispatch | `pcae runtime inspect`'s `execution_availability` reporting (existing, though `TRUTHFUL_WITH_LIMITATION`, §58) | Registry `LIFECYCLE_STATES` widening to represent policy/trust-blocked states (3T §18, not this phase) |
| Adapter cannot self-authorize | Adapter output is never authority evidence | Existing untrusted-result treatment (§31 of 3T; `build_intake_handoff` never trusts adapter output structurally) | None — already enforced |

## 63. Combined authority/permission artifact?

**Assessed: NO — approval and PB decision must never live in one
artifact.** Reasons: (1) they have different lifecycles — an approval is
created once by a human and consumed once (§47), while a PB decision is
recomputed on every evaluation and has explicitly no persistent side
effects (`PermissionBroker.evaluate`'s own docstring: "Never executes
them, never has side effects"); merging them would force a
side-effect-free evaluator to co-own a stateful, consumable record. (2)
Different provenance — approval provenance is a human act (§14); PB
decision provenance is a deterministic policy evaluation over
machine-readable facts; conflating them would blur exactly the
`human authority != PB permission` distinction this entire phase exists
to preserve (Objective, §1). (3) Different trust boundaries — an approval
artifact needs subject-binding/tamper-detection trust (§22); a PB
decision needs only reproducibility from its inputs (already the case).
**Preferred approach: separate provenance with linkage** — references/
hashes (§31), never merged records, matching the instruction's own stated
preference.

## 64. Future contract artifacts to recommend

- **Runtime Invocation Human Authority Contract** — freezes the
  `RuntimeInvocationApproval` schema (subject tuple, freshness rules,
  one-shot consumption semantics) selected in §16–§20.
- **PB Runtime Dispatch Extension Contract** — freezes the `runtime_dispatch`
  action type, its request-shape fields (§11), and its interaction with
  POL-004/POL-005 (§25/§41/§42), selected in §9–§10.
- **Dispatch Gate Ordering Contract** — freezes the gate sequence (§26),
  the Runtime-Enforcement-handoff projection (§29), and the
  durable-before-effect minimum set (§32).
- **Invocation authority schema** (a `schema_resources`-family JSON
  schema, mirroring CHGR's pattern per §22, without adopting CHGR's own
  runtime-consumption disclaimer).

This phase creates the architecture doc above but deliberately does
**not** freeze any of these four as a production contract yet (Step 62's
explicit instruction) — one dependency remains genuinely open (§54's
network-permission disposition), which is exactly the ambiguity Step 63
below resolves toward Outcome B for the API-provider path while allowing
Outcome A for the local-CLI-only path.

## 65. Contract-freeze readiness

**Split verdict, stated precisely:**

- **For the local-CLI-only v1 path (§52):** **Outcome A** — architecture
  is mature enough to freeze the four contracts of §64 in the very next
  phase, because no unresolved dependency blocks the local-CLI chain
  (§54's network gap is explicitly irrelevant to a no-network local
  executable, per 3T §26/§29 and this phase's §52).
- **For the API-provider path:** **Outcome B** — one real ambiguity
  remains open (§54's network-permission mechanism is explicitly
  unresolved, by design, to avoid conflating it into the wrong PB action)
  and must be resolved by a dedicated architecture-clarification phase
  before any API-provider-scoped contract is frozen.

**Overall recommendation: proceed to contract freeze scoped to the
local-CLI-only v1 path (Outcome A for that scope only)**, explicitly
deferring API-provider contract freeze until the network-permission
dependency (§54) is separately architected (Outcome B for that scope).
This split verdict is itself evidence-derived, not a hedge: 3T §29 already
established that local CLI has "strictly fewer unique blockers" and "can
be satisfied without ever needing a network PB action at all," so the two
paths genuinely have different readiness levels.

## 66. Implementation dependency order

After contracts are frozen (in a future phase), the likely exact order,
extending 3T §60's DAG with this phase's two selected artifacts inserted
at their correct dependency points:

1. `RuntimeInvocationApproval` artifact type + storage (§16/§21) —
   independent of PB, can start first.
2. PB `runtime_dispatch` request-shape support (§9/§11) — depends on (1)
   only for the authority-reference field's existence, not its full
   validation logic.
3. Approval-validation logic (gate 5, §24) — depends on both (1) and (2).
4. Independent verification of (1)–(3) (matching this repository's
   established pattern of an independent-verification phase following
   every implementation phase).
5. Runtime Enforcement integration (§29/3T §44) — depends on (2)/(3)
   being real and bound, per RPAC-REQ-045's explicit ordering.
6. Shell Gate enforcement (RPAC-REQ-048) and local-CLI target descriptor
   (RPAC-REQ-057/058/086) — proceeds in parallel with (1)–(5), converges
   at the first real adapter (RPAC-REQ-095), matching 3T §60's DAG
   unchanged.

## 67. First implementation stop (guardrail)

Even after (1)–(3) above are implemented and independently verified,
**real external execution must remain unavailable** until Runtime
Enforcement integration (5), Shell Gate/process containment (6), and the
local-executable-adapter prerequisites (RPAC-REQ-057/058/086) are
*separately* completed and independently verified. This phase explicitly
states this as a guardrail for future phases: implementing the
authority/PB half of this architecture does **not**, by itself, make real
execution available, and no future phase should treat authority/PB
completion alone as sufficient grounds to flip
`execution_availability` to `available`.

## 68. No production changes (confirmed)

`git diff --stat -- src/pcae tests` was verified empty before this
phase's commits (0 lines changed in either directory). No PB policy, RPAC
contract, Runtime Enforcement code, production schema, or version/build
config was modified. Allowed-changed files this phase: this document,
`PROJECT_STATUS.md`, `CHANGELOG.md`, `.pcae/phase-completion-metadata.json`,
`.pcae/phase-completion-report.md`, `tasks/DONE.md`, and task-lifecycle
contract files.

## 69. No-Go verification (Step 67 hard constraints)

None of the following occurred this phase: POL-005 was not removed or
relaxed (read-only, quoted verbatim, §7); no new PB action was
implemented (only designed, §9/§10 — no code change); no authority
artifact was created (only designed, §16 — no file, no schema, no code);
CHGR was not modified; Runtime Enforcement was not activated (read-only,
§29); Shell Gate was not activated (read-only, §56); no Codex/Claude
runtime was invoked; no subprocess was launched for real execution; no
credential was accessed; no runtime network was enabled; real execution
was not activated; HATP/HMIC/Class-B were not altered; CLTR was not cut
over; Dell was not contacted; the private research repository
(`pcae-deepseek-research`) was not inspected; the article was not
resumed.

## 70. Testing

Read-only architecture phase. Verification performed: direct source
reads of `permission_broker_foundation.py`, `runtime_invocation.py`,
`runtime_registry.py`, `backend_invocations.py`, `shell_gate.py`; direct
contract reads of `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`,
`REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`, CHGR README,
`PHASE_99_GOVERNED_EXECUTION_ATTEMPT_BOUNDARY_DESIGN.md`; cross-checked
every quoted line number against the live file content (all matched
3T's citations, unchanged since 3T). No mutation performed. Full Fast
Green not required (no production source changed).

## 71. Governance / exit gates

`pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor
task-memory`, `pcae push check`, `pcae runtime inspect`, and
`pcae notify status` were run before and will be re-run after
finalization, per Step 69's requirement. No `--no-verify`, no force-push,
no history rewrite were used at any point.

## 72. Final verdict

**Architecture COMPLETE for the local-CLI-only v1 scope (Outcome A);
API-provider scope requires a further architecture-clarification phase
first (Outcome B, §65).** Selected PB redesign: **Option A — dedicated
`runtime_dispatch` action** (§9/§10). Selected human authority design:
**Option A — dedicated `RuntimeInvocationApproval` artifact**, one-shot
(§16/§17). Binding: five-tuple subject (§18), consumed at the
durable-pre-dispatch-marker boundary (§47), validated independently
before PB, projected (not merged) into Runtime Enforcement (§29). No
production change was made. No PB action was implemented. No authority
artifact was created. Real execution remains unavailable.

## Recommended next phase

For the local-CLI-only path: proceed to freeze the four contract
artifacts named in §64 (a "PB Runtime Dispatch + Human Authority Contract
Freeze" phase), scoped strictly to local-CLI, followed by independent
verification, per the dependency order in §66. The API-provider path
requires a separate, prior "Network Egress Permission Architecture" phase
(resolving §54's open dependency) before any API-scoped contract may be
frozen.

## Human decision required

**YES.** A human decision is required to authorize: (a) which contract-
freeze phase to begin next (local-CLI-scoped, per §65/§72); (b) whether
to also authorize a separate network-egress-permission architecture
phase now or defer it; (c) whether the two 3S.2.1 MUST-FIX findings
should be scheduled for repair alongside the first real-adapter phase, as
recommended (§57), or on a different timeline. No autonomous continuation
is authorized by this document. This phase stops here, as instructed.
