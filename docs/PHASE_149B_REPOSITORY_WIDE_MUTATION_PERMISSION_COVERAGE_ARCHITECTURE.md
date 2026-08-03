# Phase 149B — Repository-Wide Mutation Permission Coverage Architecture

## 0. Post-Chapter-148 / Post-149A Capability Statement

PCAE has one production Permission Broker consumer: `pcae push` (both
dispatch sites), certified in Chapter 148. This phase does **not**
implement anything, does **not** modify `src/pcae/**`, does **not**
modify `docs/contracts/**`, does **not** enable execution capability,
does **not** invoke agents, and adds **no** new Permission Broker
consumer. Runtime remains `Observed` / `observe` / `unavailable`
throughout, before and after this phase.

## 1. Purpose and Boundary

This is a bounded **architecture and inventory** phase. Per Phase 149A's
selection, it independently reconstructs the repository-wide mutation
inventory (not trusting 149A's summary as ground truth — every claim
below was re-derived from direct source inspection in this phase),
defines a mutation taxonomy, evaluates current Permission Broker /
Runtime Enforcement coverage, selects a target architecture, and
recommends the next chapter phase. Predecessor: Phase 149A (Next
Strategic Capability Reassessment — selected this capability,
architecture/inventory first, not authorized for implementation).

## 2. Bootstrap / Confirmed Position

- `git status --short`: clean. `git status --branch --short`: `##
  main...origin/main` (0 ahead/behind). `git rev-list --count
  origin/main..HEAD`: `0`. HEAD: `45e32236`.
- `pcae health`: healthy. `pcae check`: passed. `pcae status
  coherence`: coherent. `pcae doctor task-memory`: clean.
- `pcae push check`: `Mode: nothing_to_push`, 0 unpushed commits.
- `pcae runtime inspect`: `Runtime state: Observed`, `Execution
  capability: unavailable`, `Maximum plugin capability: observe`,
  `Permission Broker status: execution_unavailable`. (Reconfirmed
  unchanged at phase close, §Runtime State below.)
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest`: Phase 149A, status `completed`,
  report completeness `complete`, `origin/main..HEAD: 0`.
- `pcae phase-report reconcile --phase-id 149A`: `reconciled`,
  `Mutation: none (inspection only)`.

**Confirmed:** repository clean; 149A complete and pushed; 149B is the
canonical planned phase (per `pcae phase-report show --latest`'s
"Planned" section and `PROJECT_STATUS.md`); Chapter 148 remains
certified; runtime remains Observed/observe/unavailable.

## 3. Strategic Requirement (Reconstructed From Primary Evidence)

Chapter 148 built exactly one Permission Broker production consumer:
`pcae push`, both dispatch sites (`push.py:698`, `push.py:898`),
freshness-bound, POL-001..012-evaluated. `docs/contracts/
PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` §25
(PBPC-REQ-085/086) is explicit that this is a narrow MVP and that
Runtime Enforcement (`backend_invocations.py`,
`runtime_enforcement_safety_authorization.py`) is an unconnected,
design-only, parallel track not required for it.

The v0.2 autonomy roadmap (`docs/PHASE_107_V0_2_EXECUTION_CAPABILITY_
GAP_ANALYSIS.md`, `docs/V0_2_AUTONOMY_ROADMAP.md`) targets Level 3
("human-approved bounded execution"). Any future bounded execution —
an agent editing files, committing, and pushing — will dispatch through
the *same* mutation primitives already live in this repository today
(git add/commit/push/revert, arbitrary file write). Those primitives
already exist, are already CLI-reachable, and are already exercised by
real workflows (`pcae remote *`, `pcae task finish --commit`, `pcae
promote`, the backend-created-output-adoption pipeline). If a future
Prompt-Dispatch/agent-invocation chapter is built before this perimeter
is understood and (eventually) closed, it will land directly on top of
an already-fragmented, partially-ungated mutation surface. That is why
repository-wide mutation coverage was selected ahead of Prompt Creation
(second-ranked, not foreclosed, `docs/PHASE_149A_...md` §7/§16).

## 4. Mutation Definition and Taxonomy

Not every filesystem write is equivalent. Using repository-native
vocabulary where it already exists (`permission_broker_foundation.py`'s
`ACTION_*`/`EXECUTION_CLASS_*` constants, §18 below) plus categories the
codebase does not yet name, this phase adopts:

| ID | Category | Repository-native anchor | Example |
|---|---|---|---|
| M1 | Working-tree mutation (file content) | `ACTION_SOURCE_MUTATION` / `ACTION_DOCS_MUTATION` / `ACTION_TEST_MUTATION` (defined, unused in production) | `build_promotion_execution` writing `full_path.write_text(...)` |
| M2 | Git index mutation | none named | `git add` |
| M3 | Local history mutation (commit) | `ACTION_COMMIT` (defined, unused) | `_run_git_commit`, `task.py` `git commit --no-verify` |
| M4 | Remote repository mutation (push) | `ACTION_PUSH` (defined, **consumed**) | `pcae push`, `agent.py:_run_git_push`, `phase.py` push sites |
| M5 | Rollback / recovery mutation | `ACTION_ROLLBACK` / `EXECUTION_CLASS_ROLLBACK` (defined, unused) | `execute_rollback` (`git revert`), `push_rollback` |
| M6 | PCAE lifecycle-state mutation (bookkeeping JSON under `.pcae/`) | none named | task/phase/report artifact writes |
| M7 | Canonical artifact publication | `ArtifactState` transition (Ch. 114/144-146) | `canonical_artifact_promotion.py` |
| M8 | External-system mutation | none named | Telegram outbound notification |

M1-M5 are **repository mutation** (the literal subject of this
chapter). M6-M8 are **governed-but-different** — each already has its
own authority model (task/phase lifecycle contracts, CHGR/publication
state machine, notification foundation) and is a **scope-boundary**
question (§14), not automatically folded in.

## 5. Repository-Wide Mutation Inventory (Independently Reconstructed)

Direct source inspection in this phase, not a re-statement of 149A's
count. New findings beyond 149A's inventory are marked **[NEW]**.

| # | Path (file:line) | Mutation | Class | CLI entry point | Production? | PB-gated? |
|---|---|---|---|---|---|---|
| 1 | `commands/push.py:698` | `git push` | M4 | `pcae push` | Yes | **Yes** (PBPC-001 v1.2) |
| 2 | `commands/push.py:898` | staged-file-aware `git push` | M4 | `pcae push` | Yes | **Yes** (PBPC-001 v1.2) |
| 3 | `core/agent.py:4559` (`_run_git_add`) + `4572` (`_run_git_commit`) | `git add` + `git commit` | M2+M3 | `pcae remote commit` | Yes | No |
| 4 | `core/agent.py:4732` (`_run_git_push`) | `git push <remote> HEAD:<branch>` | M4 | `pcae remote push` | Yes | No |
| 5 | `core/agent.py:5099` (`execute_rollback`) | `git revert --no-edit` | M5 | `pcae remote rollback execute` | Yes | No |
| 6 | `core/agent.py:5219` area (`push_rollback`, reuses `_run_git_push`) | `git push` (post-rollback) | M4/M5 | `pcae remote rollback push` | Yes | No |
| 7 **[NEW]** | `core/agent.py:93390-93417` (`build_promotion_execution`) | arbitrary file write/delete (`write_text`/`write_bytes`/`unlink`) into any non-`.git/`/`.pcae/` repo path, **including `src/pcae/**`** | M1 | `pcae promote --epr-id ...` | Yes | No |
| 8 **[NEW]** | `commands/task.py:297-316` (`run_task_finish`) | `git add` + `git commit --no-verify` | M2+M3 | `pcae task finish --commit MSG [--staged-file-aware]` | Yes | No |
| 9 **[NEW]** | `commands/task.py:1092-1105` (`run_task_finish_recover`) | `git add` + `git commit --no-verify` | M2+M3 | `pcae task finish recover --message MSG` | Yes | No |
| 10 | `commands/phase.py:17585` (`_build_backend_created_output_adoption_execution`) | `git add -f` | M2 | `pcae phase backend-created-output-adoption-execution --execute` | Yes | No |
| 11 | `commands/phase.py:18457` (`_build_backend_created_output_adoption_commit_execution`) | `git commit --no-verify` | M3 | `pcae phase backend-created-output-adoption-commit-execution --execute` | Yes | No |
| 12 | `commands/phase.py:19563` (`_build_backend_created_output_adoption_push_execution`) | `git push origin main` | M4 | `pcae phase backend-created-output-adoption-push-execution --execute` | Yes | No |
| 13 | `commands/phase.py:20295` (`_build_final_verification_tooling_push_decision`) | `git push origin main` | M4 | `pcae phase final-verification-tooling-push-decision --execute-push` | Yes | No |

**Result: 13 real, CLI-reachable mutation dispatch sites identified
across 4 files (`push.py`, `agent.py`, `task.py`, `phase.py`) — larger
than 149A's "≥8" framing, itself larger than Chapter 148's "5 push
sites" framing. Exactly 2 (both `pcae push`) are Permission-Broker-
gated. 11 are not.** Sites 7-9 are genuinely new findings this phase
adds to the inventory (a real arbitrary-file-write/apply mechanism that
can target `src/pcae/**` itself, and two `commands/task.py` commit
sites 149A did not enumerate).

`cli.py`'s `main()` dispatches directly to `args.handler(args)` — there
is no global interception wrapper; every gate above exists only because
that specific command inlines it.

## 6. Deep Surfaces

### 6.1 Agent Mutation Surface (`core/agent.py`, "remote" job pipeline)

`commit_file_changes` / `push_file_changes` / `execute_rollback` /
`push_rollback` back the `pcae remote *` CLI group — PCAE's mechanism
for adopting changes produced by a remote/external execution job. Each
has real structural guards: `commit_file_changes` requires
`change_approval_state == "approved"`, non-empty `changed_files`, valid
`scope_validation`, and an exact working-tree match to the approved
file set; `push_file_changes` requires a recorded `commit_sha`, a clean
tree, and commit-ancestry verification before invoking
`_run_git_push`. None imports `permission_broker` or
`permission_broker_foundation`. All four are live, documented,
human-invokable CLI verbs today — not legacy, not unreachable.

**Approval-evidence weakness:** `approve_file_changes` /
`deny_changes` / `approve_rollback` / `deny_rollback` set a bare
`change_approval_state` / `rollback_approval_state` string field with
no identity or reason capture — any caller of the CLI verb can flip
the flag. This is weaker evidence than `final-verification-tooling-
push-decision`'s `--approve-keep --approved-by REASON --reason TEXT`
triple (§10). Both are still ultimately self-declared CLI flags with no
authentication, but the latter at least records who and why.

### 6.2 Promotion Execution Surface (`core/agent.py`, ECP/EPR/PER pipeline) — new finding

`pcae promote --epr-id <id>` calls `build_promotion_execution`, whose
own docstring states: *"The only PCAE code path that mutates root."*
It writes (`write_text`/`write_bytes`) or deletes (`unlink`) files at
arbitrary repo-relative paths drawn from an
`ExecutionChangePackage`'s (ECP) `file_entries`, filtered only by hard
exclusions (`.git/`, `.pcae/`, external symlinks) and default exclusions
(toolchain/gitignored/oversized binary) — **`src/pcae/**` itself is not
excluded**. Gated on an `ExecutionPromotionReview` (EPR) with
`promotion_authorized is True`, itself set via
`pcae promotion-review create --promotion-authorized` (a bare boolean
flag) and `--reviewed-by NAME` (free-text, unverified). No subprocess
is invoked (`execution_allowed=False` throughout); it never commits or
pushes. This is PCAE's only real production **file-apply** mechanism
(answers §12/§63's "does one exist?": **yes**), and it is
CLI-reachable, ungated by the Permission Broker, and structurally
capable of writing into production source. This is the single most
autonomy-relevant finding of this phase, ahead of the already-known
commit/push/rollback surface.

### 6.3 Task-Lifecycle Commit Surface (`commands/task.py`) — new finding

`pcae task finish --commit MESSAGE` and `pcae task finish recover
--message MESSAGE` each perform a real `git add` + `git commit
--no-verify`. Scope is narrow and structurally bounded — only the
task's own closure files (`result.updated_files`, the completed-task
destination path, and, for `recover`, `plan.closure_files`) are staged,
with a `git check-ignore` filter and (for `--staged-file-aware`) a
protected-staged-file conflict check. This is real commit capability,
but it is lifecycle-internal bookkeeping closure, not general source
mutation — see scope-boundary discussion (§14).

### 6.4 Phase-Command Mutation Surface (`commands/phase.py`)

Two related but distinct pipelines exist, both hand-rolled ("Gate
1-7/1-8") rather than PBPC-pattern:

- **Backend-created-output adoption** (`_build_backend_created_output_
  adoption_execution` → `..._commit_execution` → `..._push_execution`):
  a 3-stage `git add -f` → `git commit --no-verify` → `git push origin
  main` pipeline whose own naming ("backend-created-output") signals it
  exists specifically to adopt output **produced by a real backend
  (`--source-backend claude|codex`, per `preflight mutation`'s own
  flag)** into the repository. This is not legacy bookkeeping — it is a
  second, independently-built real-backend-output-adoption path, parallel
  to (and inconsistent with) the ECP/EPR/PER pipeline in §6.2. Gates
  include audit-warning checks, `real-execution-disabled-proofs`,
  `runner-executions` refusal checks, and an already-committed guard —
  none of them Permission-Broker calls.
- **Final-verification-tooling push** (`_build_final_verification_
  tooling_push_decision`): pushes already-existing local commits after
  verification, requiring `--approve-keep --approved-by --reason` — the
  one path in the entire inventory with named, explicit approval
  evidence fields (still unauthenticated, but structurally the
  strongest).

## 7. File-Write Surface Classification

`write_text`/`write_bytes` occur ~325 times across `src/pcae/`. The
overwhelming majority (222 in `phase.py`, 58 in `backend_invocations.py`,
most of `agent.py`'s 13) write JSON bookkeeping artifacts under
`.pcae/**` (task contracts, phase reports, audits, backend-invocation
records) — canonical PCAE lifecycle bookkeeping (M6), not autonomous
coding mutation. The exceptions that write outside `.pcae/**` into
real repository content are: `build_promotion_execution` (§6.2, can
target anywhere including `src/pcae/**`) and
`canonical_artifact_promotion.py` (writes versioned/canonical artifact
paths — publication, M7, see §14). No other production function was
found writing arbitrary source-file content.

## 8. Patch / Apply Surface

Answering §12/§63 directly: PCAE's only production code-**apply**
mechanism is the promotion pipeline in §6.2 (`pcae promote`). There is
no `git apply`/unified-diff-application mechanism anywhere in
`src/pcae/` — `_difflib.unified_diff(...)` at `agent.py:92591` only
*generates* a diff for display/audit, it does not apply one. So the
correct framing is not "no code-apply path exists" (149A's assumption)
but "exactly one exists, and it is currently outside Permission Broker
coverage."

## 9. Rollback Surface

`execute_rollback` (`git revert --no-edit`) and `push_rollback` (reuses
`_run_git_push`) are real, live, `pcae remote rollback execute|push`
reachable. `approve_rollback`/`deny_rollback` gate a
`rollback_approval_state` flag with the same weak-evidence pattern as
§6.1. Separately, `build_rollback_governance` (`agent.py:4989`) and
`build_write_rollback_validation_design` (`agent.py:23928`) are
advisory/design-only functions describing rollback governance intent —
they do not gate the real `execute_rollback`/`push_rollback` functions
today. Critically, **PBPA-001 already defines `EXECUTION_CLASS_ROLLBACK`
as one of the four execution classes POL-004 ("Missing Human Approval")
applies to** — meaning the policy vocabulary already anticipates that
rollback, unlike push (`EXECUTION_CLASS_MUTATION`, explicitly excluded
from POL-004), should require real `approval_present` evidence before
a broker would ALLOW it (§13).

## 10. Publication / Lifecycle / External Scope Boundaries

- **Publication (M7):** `canonical_artifact_promotion.py` writes
  versioned/canonical artifact paths through an `ArtifactState`
  transition (CERTIFIED → CANONICAL), Chapter 114/144-146's own
  authority model. **OUT of Chapter 149 scope** — it is governed writes
  under an existing, different, purpose-built state machine, not
  autonomous source mutation; folding it in would collapse two
  authorities into one without evidence that is correct (§15's
  general principle).
- **Lifecycle-state (M6):** task/phase/report bookkeeping writes
  (§7) are governed by their own lifecycle contracts (PFR-001,
  task-contract lifecycle) already. **OUT of scope**, with one
  carve-out: `commands/task.py`'s `git commit` calls (§6.3) are real
  git mutation, not just JSON bookkeeping — noted as a borderline case,
  recommended disposition KEEP_SEPARATE / LIFECYCLE_INTERNAL for now
  (§16), not silently ignored.
- **External (M8):** Telegram outbound (`core/notifications.py`) is a
  side effect on an external system, not repository mutation. **OUT of
  scope**, stated explicitly per the task's own instruction.
- **Test scratch / manual human git:** excluded per instructions —
  `tests/` fixtures and arbitrary human shell use are not production
  PCAE mutation paths.

## 11. Actual vs Potential Mutation Classification

| Path | Classification |
|---|---|
| `pcae push` (both sites) | REAL_PRODUCTION_MUTATION (gated) |
| `pcae remote commit/push/rollback execute/rollback push` | REAL_PRODUCTION_MUTATION (ungated) |
| `pcae promote` | REAL_PRODUCTION_MUTATION (ungated) |
| `pcae task finish --commit` / `finish recover` | REAL_PRODUCTION_MUTATION (ungated, narrow scope) |
| backend-created-output-adoption add/commit/push | REAL_PRODUCTION_MUTATION (ungated) |
| final-verification-tooling-push | REAL_PRODUCTION_MUTATION (ungated, strongest approval evidence) |
| `pcae preflight commit` / `pcae preflight push` | READ_ONLY (evaluates a *hypothetical* commit/push against evidence; does not mutate) |
| `build_rollback_governance`, `build_write_rollback_validation_design` | DESIGN_ONLY |
| Runtime Enforcement (`backend_invocations.py`, `runtime_enforcement_safety_authorization.py`) | DESIGN_ONLY |
| `canonical_artifact_promotion.py` | REAL_PRODUCTION_MUTATION, different authority (M7, out of scope) |
| `.pcae/**` bookkeeping writes | REAL_PRODUCTION_MUTATION, different authority (M6, out of scope) |
| Test/fixture git operations | TEST_ONLY |

## 12. Current Permission-Broker Coverage Matrix

| Mutation path | Action/class (existing PBPA vocabulary) | PB consumer today? | PBPC coverage |
|---|---|---|---|
| `pcae push` (×2) | `ACTION_PUSH` / `EXECUTION_CLASS_MUTATION` | **Yes** | PBPC-001 v1.2 |
| `pcae remote commit` | `ACTION_COMMIT` (defined, unconsumed) | No | none |
| `pcae remote push` | `ACTION_PUSH` (defined, unconsumed here) | No | none |
| `pcae remote rollback execute/push` | `ACTION_ROLLBACK` / `EXECUTION_CLASS_ROLLBACK` (defined, unconsumed) | No | none |
| `pcae promote` | `ACTION_SOURCE_MUTATION` (or docs/test variant; defined, unconsumed) | No | none |
| `pcae task finish --commit` / `finish recover` | `ACTION_COMMIT` (defined, unconsumed) | No | none |
| backend-created-output-adoption (add/commit/push) | `ACTION_SOURCE_MUTATION`+`ACTION_COMMIT`+`ACTION_PUSH` | No | none (bespoke Gate 1-7/1-8 instead) |
| final-verification-tooling-push | `ACTION_PUSH` | No | none (bespoke `--approve-keep` gate instead) |

Every non-push action type this table needs (`ACTION_COMMIT`,
`ACTION_ROLLBACK`, `ACTION_SOURCE_MUTATION`, `ACTION_DOCS_MUTATION`,
`ACTION_TEST_MUTATION`) is **already defined** in
`permission_broker_foundation.py`'s `KNOWN_ACTIONS_91A`-equivalent
registry (actually the older `permission_broker.py` prototype defines
the frozensets; `permission_broker_foundation.py` — the one PBPC-001
actually consumes — defines the individual `ACTION_*`/`EXECUTION_
CLASS_*` module constants used by `build_permission_broker_request`).
None of it is wired to a real caller outside `push.py`.

## 13. Current Runtime-Enforcement Coverage Matrix

| Mutation path | Runtime Enforcement involved? | Execution class | Execution availability |
|---|---|---|---|
| All 13 sites in §5 | No | N/A (RE not wired to any of them) | `unavailable` (hardcoded in `runtime_context.py`) |

Runtime Enforcement (`backend_invocations.py` — component registry,
invocation modes, `GovernedExecutionAttemptBoundary` `design_only=True`
at line ~9505; `runtime_enforcement_safety_authorization.py` — every
readiness/authorization function returns "design-only, non-executing")
remains, per PBPC-001 §25, an unconnected parallel track. It could in
principle later serve as the execution-mediation layer for
`EXECUTION_CLASS_SHELL`/`BACKEND`/`ADAPTER` actions (subprocess/backend/
adapter invocation) — but none of the 13 real mutation sites in §5 are
shell/backend/adapter invocations in that sense; they are direct git/
filesystem calls. Wiring RE in as the mutation boundary now would be
new scope Chapter 148 explicitly declined, not a natural extension.

## 14. Authority / Approval Matrix

| Path | Confirmation | Approval evidence | Authority Evaluation/AESIC | Permission Broker |
|---|---|---|---|---|
| `pcae push` | Interactive Workflow (where applicable) | none required (`EXECUTION_CLASS_MUTATION` excluded from POL-004) | disclosure-only | consumed |
| `pcae remote commit/push` | none | none | none | not consumed |
| `pcae remote rollback execute/push` | none | bare state flag (`approve_rollback`, no identity/reason) | none | not consumed (POL-004 *would* apply if wired — rollback is in its applicable set) |
| `pcae promote` | none | bare `--promotion-authorized` flag + free-text `--reviewed-by` | none | not consumed |
| `pcae task finish --commit` | task-finish validation checks (health/check, unless `--skip-checks`) | none | none | not consumed |
| backend-created-output-adoption | bespoke Gate 1-7 (audit, real-execution-disabled, runner-refusal) | none | none | not consumed |
| final-verification-tooling-push | none | named `--approve-keep --approved-by --reason` | none | not consumed |

**Distinctions preserved, per instruction:** *confirmation* (Interactive
Workflow, task-finish health checks) is process hygiene, not
authorization. *Approval* means a recorded disposition with identity/
reason; only final-verification-tooling-push has that shape today, and
even it is a self-declared CLI flag, not independently verified.
*Permission* means a Permission-Broker `ALLOW`/`DENY`/`HUMAN_REVIEW`
decision; only `pcae push` has this. *Capability*/`execution` remain
`unavailable` for all paths (Runtime state).

## 15. Legacy Approval Flags

`--approve-keep`, `--approved-by`, `--reason`
(final-verification-tooling-push) and `--promotion-authorized`,
`--reviewed-by` (promotion review) are **mechanical override /
self-declared evidence**, not verified human approval — nothing
authenticates the caller. They are the closest thing to genuine
approval evidence in the repository today (named fields, explicit
intent) but should not be assumed equivalent to a future broker-grade
`approval_present=True`. `--skip-checks` (`task finish`) and
`--staged-file-aware` are mechanical/structural flags, not approval.
`--force` does not appear on any mutation path in this inventory (no
force-push flag was found wired to a CLI argument in the mutation
sites above; `push.py`'s force-push guard is a *hard block*, per
`permission_broker.py`'s `CMD_FORCE_PUSH`, not an override flag).

## 16. Mutation Critical-Path Analysis and Legacy Disposition

| Path | Autonomy-critical? | Disposition |
|---|---|---|
| `pcae push` | Yes (already the MVP) | done (BROKER_WIRE, certified) |
| `pcae remote commit/push/rollback execute/rollback push` | **Yes** — literal remote/agent-job adoption pipeline | BROKER_WIRE |
| `pcae promote` (ECP/EPR/PER) | **Yes** — real file-apply into any path incl. `src/pcae/**` | BROKER_WIRE (highest priority) |
| backend-created-output-adoption (add/commit/push) | **Yes** — real-backend-output adoption, parallel to `pcae remote`/`pcae promote` | push site: ROUTE_TO_CANONICAL_COMMAND (share the push adapter `pcae push`/`pcae remote push` will use, rather than a third push implementation); add/commit sites: BROKER_WIRE, but consolidate with §6.2/§6.1 rather than building a fourth parallel path |
| final-verification-tooling-push | Legacy support (post-verification local-commit push) | ROUTE_TO_CANONICAL_COMMAND (reuse the canonical push adapter; keep its stronger `--approved-by/--reason` evidence as an input to `approval_present`) |
| `pcae task finish --commit` / `finish recover` | LIFECYCLE_INTERNAL, narrow closure-file scope | KEEP_SEPARATE (governed by task-lifecycle contracts); revisit only if this path is ever asked to commit non-closure files |

**Finding:** PCAE currently has **three independently-built** real or
near-real "adopt externally/remotely produced changes" pipelines —
`pcae remote *` (§6.1), `pcae promote`/ECP-EPR-PER (§6.2), and
backend-created-output-adoption (§6.4) — none of which share code or a
common permission gate, and none of which is the certified `pcae push`
pattern. This is the single strongest architectural argument in this
phase: multiplying enforcement adapters (Model A, unchecked) is already
happening organically; a shared adapter is needed before a fourth one
appears.

## 17. Candidate Architecture Models

**Model A — Per-command PB integration.** Mirrors Chapter 148 exactly:
each of the 11 ungated sites independently builds its own
`PermissionBrokerRequest` and calls `PermissionBroker().evaluate()`
inline, as `push.py` does today. *Risk, confirmed by evidence in this
phase (§16):* `push.py` already has two near-duplicate call sites
(698, 898); three independent adoption pipelines already exist without
sharing code. Model A would legitimize and multiply that duplication
across 11 more sites rather than fixing it.

**Model B — Shared Mutation Permission Adapter.** One function builds
the canonical request and calls the broker for every mutation type;
callers all invoke it before dispatching. Fixes request-construction
duplication, but *by itself* does not stop a caller from mutating
below the adapter (e.g., calling `_run_git_commit` directly) — the
existing 11 ungated call sites already prove direct-dispatch bypass is
easy to reach without noticing (agent.py's own functions never import
the broker at all).

**Model C — Centralized Mutation Execution Boundary.** One governed
executor performs normalization, permission check, freshness binding,
dispatch, and receipt for *all* repository mutation. Strongest
non-bypassability, but the evidence in §6.1/§6.2/§6.4 shows the
existing mutation functions already carry meaningfully different
structural validation (`commit_file_changes`'s scope/approval-state
checks vs. `build_promotion_execution`'s ECP/EPR divergence checks vs.
`execute_rollback`'s ancestry checks) that a single universal executor
would either have to reimplement wholesale or abstract away —
substantial rewrite risk for a phase whose own instructions forbid
touching `src/pcae/**`.

**Model D — Runtime Enforcement as canonical mutation boundary.**
Rejected on direct evidence: PBPC-001 §25 explicitly treats RE as
parallel/unconnected and states it is *not required* for v1.0; none of
the 13 real mutation sites in this inventory are shell/backend/adapter
invocations (RE's actual domain) — they are direct git/filesystem
calls. Routing them through RE would require contract changes to both
PBPC-001 and RE's own design, out of scope for architecture-only work.

**Model E — Hybrid.** `command/agent intent → canonical mutation
request (reuse `PermissionBrokerRequest`, no new schema) → Permission
Broker decision (reuse `permission_broker_foundation`, POL-001..012
as-is) → thin per-mutation-class adapter (one for commit, one for
rollback, one for file-apply/promotion; push's adapter already exists
as `push.py`'s pattern and should be the template) → existing
structural-validation + dispatch functions (unchanged)`. Runtime
Enforcement stays reserved for shell/backend/adapter execution classes
if and when those become real.

## 18. Selected Architecture

**SELECTED MUTATION PERMISSION ARCHITECTURE: Model E — Hybrid
(canonical request → Permission Broker decision → per-class adapter →
existing dispatch).**

**RATIONALE:**
1. Reuses the proven, certified PBPC-001/`push.py` pattern rather than
   inventing new machinery — `push.py`'s
   `_evaluate_push_permission`-then-`_validate_push_permission_
   freshness`-then-dispatch shape is exactly the adapter template each
   mutation class needs.
2. The request schema (`PermissionBrokerRequest`) and policy vocabulary
   (`ACTION_COMMIT`, `ACTION_ROLLBACK`, `ACTION_SOURCE_MUTATION`, etc.,
   POL-001..012 including POL-004's existing mutation/rollback
   distinction) already exist and already anticipate every mutation
   class found in this inventory — no new contract semantics are
   required to *start* (§20 flags where gaps remain).
3. It directly answers §16's strongest finding: three independently-
   built adoption pipelines exist today with zero shared code. A
   per-class adapter (one canonical commit adapter, one canonical
   rollback adapter, one canonical push adapter, one canonical
   file-apply adapter) collapses that duplication going forward without
   requiring the existing structural-validation logic inside
   `commit_file_changes`/`execute_rollback`/`build_promotion_execution`
   to be rewritten — those functions keep their mechanical checks and
   simply gain a broker call before dispatch, exactly as `push.py`
   already demonstrates is possible.
4. It does not disturb Runtime Enforcement's declared-parallel status
   (Model D rejected) and does not require a single universal executor
   to absorb genuinely different mutation semantics (Model C rejected;
   Model B alone insufficient; Model A's duplication risk is empirically
   already occurring, §16/§17).

**REJECTED:** Model A (duplication risk, already observed in the
existing codebase). Model B alone (does not prevent below-adapter
bypass; the ungated sites in this inventory prove bypass already
happens by simple omission, not malice). Model C (larger rewrite than
architecture-only evidence justifies; risks collapsing genuinely
distinct mechanical semantics). Model D (explicitly out of scope per
PBPC-001 §25; wrong domain — RE governs shell/backend/adapter
invocation, not direct git/file mutation).

## 19. Canonical Mutation Boundary Concept

```
command / agent intent (pcae push | pcae remote commit/push/rollback |
                         pcae promote | pcae task finish --commit |
                         backend-created-output-adoption commands)
        |
        v
canonical mutation request  (reuse PermissionBrokerRequest — task_id,
        |                     phase_id, action_type, execution_class,
        |                     requested_component/capability/resource,
        |                     evidence_available, approval_present)
        v
Permission Broker decision  (permission_broker_foundation.PermissionBroker
        |                     .evaluate() — POL-001..012, unchanged)
        v
operation-bound ALLOW / DENY / HUMAN_REVIEW
        |
        v
per-mutation-class adapter  (thin — one per M2/M3/M4/M5/M1, modeled on
        |                     push.py's freshness-then-dispatch shape)
        v
mechanical validation        (existing: scope_validation, approval_state,
        |                     working-tree checks, ECP/EPR divergence
        |                     checks, ancestry checks — UNCHANGED)
        v
mutation dispatch            (existing subprocess/file-write calls —
        |                     UNCHANGED)
        v
result / receipt
```

Runtime Enforcement is not in this chain. It remains reserved for a
future chapter that actually mediates shell/backend/adapter execution,
if one is separately authorized.

## 20. Relationship to PBPC-001 and PBPA-001

**PBPC-001** should **remain push-specific** (v1.2, unamended). A
future contract (tentatively `RWMPC-001` — exact ID per repository
convention at contract-freeze time, not invented normatively here)
should generalize the *pattern* PBPC-001 proved, not rewrite PBPC-001
itself — per instruction, "do not casually rewrite a certified push
contract into a generic mutation contract." PBPC-001's push-specific
freshness/dispatch details stay as-is; the new contract documents the
per-class adapter shape and how it reuses the same request/decision
model.

**PBPA-001** appears **largely sufficient as-is** for commit and
rollback: `ACTION_COMMIT`, `ACTION_ROLLBACK`, `EXECUTION_CLASS_ROLLBACK`
are already defined, and POL-004's existing exclusion of
`EXECUTION_CLASS_MUTATION` / inclusion of `EXECUTION_CLASS_ROLLBACK`
already encodes the correct policy distinction between "push/commit
don't require approval evidence" and "rollback does." One real gap:
`build_promotion_execution` (file-apply, §6.2) does not cleanly map to
an existing `ACTION_*`/`EXECUTION_CLASS_*` pair — it is closest to
`ACTION_SOURCE_MUTATION` with `EXECUTION_CLASS_MUTATION`, but that
pairing has never been exercised in production (only `ACTION_PUSH` has).
This is flagged as an open mapping question for the next phase (§21),
not resolved here.

## 21. Execution Class Mapping (Using Existing PBPA Vocabulary)

| Operation | `action_type` | `execution_class` | Status |
|---|---|---|---|
| push (any adapter) | `ACTION_PUSH` | `EXECUTION_CLASS_MUTATION` | proven in production (`pcae push`) |
| commit | `ACTION_COMMIT` | `EXECUTION_CLASS_MUTATION` (by analogy to push) | defined, never exercised — **flag: confirm classification** |
| rollback | `ACTION_ROLLBACK` | `EXECUTION_CLASS_ROLLBACK` | defined, never exercised — POL-004 *would* require `approval_present` |
| file apply (`pcae promote`) | `ACTION_SOURCE_MUTATION` / `ACTION_DOCS_MUTATION` / `ACTION_TEST_MUTATION` (by path) | `EXECUTION_CLASS_MUTATION`? | **undefined in practice — STRATEGIC POLICY GAP, §22** |

## 22. Gaps in Existing POL Coverage

- **STRATEGIC POLICY GAP:** No policy or documented convention says
  whether `build_promotion_execution` (arbitrary file write/delete,
  potentially into `src/pcae/**`) should be classified
  `EXECUTION_CLASS_MUTATION` (like push/commit, no approval required
  under current POL-004) or should be treated as needing the stronger
  `EXECUTION_CLASS_ROLLBACK`-style approval requirement given it can
  touch production source directly. This is exactly the kind of
  question this phase is instructed to surface, not resolve — no
  POL-013+ is proposed here.
- **STRATEGIC POLICY GAP:** No policy captures what "real" `approval_
  present` evidence should look like for `pcae promote`/`pcae remote
  rollback`/backend-created-output-adoption — today's `--promotion-
  authorized`/`approve_rollback` are bare flags with no identity
  verification. POL-004 asks "is approval present," but nothing in the
  Foundation defines what a legitimate `approval_present=True` *source*
  is beyond "the request builder said so." This is a evidence-quality
  gap, not a missing policy rule.
- No gap was found in the request schema itself (§20) — it already
  carries every field a commit/rollback/file-apply adapter would need.

## 23. Approval vs. Confirmation Semantics

Preserved throughout this document (§14): Interactive Workflow
confirmation and task-finish health/check validation are process
hygiene, never relabeled as approval. Where a mutation path has only
confirmation-shaped evidence (all of them except final-verification-
tooling-push) and a future broker policy would require approval (e.g.
rollback under POL-004), that is a real gap to close in a future
contract/implementation phase — not something to paper over by calling
today's flags "approval" now.

## 24. Agent Self-Permission — Principle and Findings

**Principle (must hold regardless of selected model):** agent requests
mutation ≠ agent grants permission. An agent must not be able to select
policies, fabricate approval, choose a weaker execution class, or
bypass the mutation service.

**Finding:** today's architecture does not yet enforce this, because
today's architecture does not yet gate these paths at all. But the
*shape* of the risk is visible now: `approve_file_changes`,
`approve_rollback`, and `build_promotion_review`'s `promotion_
authorized` parameter are all plain function parameters / CLI flags —
nothing distinguishes "a human typed this flag" from "a script/agent
typed this flag." Any future architecture (§18-19) must ensure
`approval_present` on the canonical request is derived from a source an
agent cannot control end-to-end (e.g., a separate human-invoked CLI
verb, a distinct identity channel) — this is a **required property**
of the eventual implementation, not something 149B builds.

## 25. Commit/Push Relationship

`push_file_changes` already requires a recorded `commit_sha` from a
prior `commit_file_changes` call and verifies ancestry before pushing —
i.e., today's `pcae remote` pipeline already treats commit and push as
two separate decisions bound to one operation (the job), not a single
combined grant. The architecture in §18-19 should preserve this:
separate Permission Broker evaluations for commit and push, not one
token covering both — consistent with §39/40 (decision lifetime, no
reusable broad token).

## 26. Rollback Permission Relationship

Per §9/§21, rollback already sits in POL-004's applicable set —
existing policy semantics already say rollback should require real
approval evidence before a broker would ALLOW it. Whether rollback is
allowed *after* a failure, and whether it needs an independent
broker evaluation separate from the original mutation's decision, are
implementation-phase questions; this phase records only that existing
contracts already point rollback toward the approval-required branch,
distinct from push/commit's currently-approval-exempt branch.

## 27. Operation Freshness and Decision Lifetime

Chapter 148 introduced decision-state freshness validation for push
(`_validate_push_permission_freshness`, reusing `PermissionBrokerDecision`
fields, not new POL logic). Given §25's finding that commit and push
are already separately decided in the `pcae remote` pipeline, a
generalized architecture should apply freshness validation to each
adapter's own decision, not push alone — but this phase does not mandate
copying push's exact freshness mechanics onto every class unexamined,
per instruction. **Principle:** a permission decision belongs to one
concrete mutation attempt; no reusable broad "agent is allowed to
mutate" token should exist in any future implementation.

## 28. Mutation Receipts and Audit

No canonical "mutation receipt" schema currently spans commit/push/
rollback/file-apply uniformly. `push_file_changes` records `pushed_at`/
`push_status`/`remote_branch` onto the job; `build_promotion_execution`
already produces a structured Promotion Execution Record (PER) with
per-file before/after hashes and a terminal status — arguably a
stronger receipt model than push's. A future contract phase should
decide whether PER's shape (or something equivalent) becomes the
general receipt, rather than inventing a new one from scratch. Per
Chapter 148 precedent (in-process decision only, no durable Permission
Broker decision evidence required), this phase does not mandate durable
broker-decision audit — that remains an open question for the next
phase to resolve with evidence, not decided here.

## 29. Mutation Failure Semantics and Atomicity

Push is discrete (one dispatch, one outcome). Commit/rollback involve
at least two steps (add+commit; revert+optional push). File-apply
(§6.2) already loops per-file and records partial outcomes
(`final_status = "partial"` when some files succeed and others fail) —
i.e., the existing PER model already has multi-step partial-failure
semantics designed in. Any future architecture must fail closed on
broker failure, malformed decision, or stale operation, and must keep
permission failure (broker said no) distinct from execution failure
(git/filesystem error) — both already distinguished today in existing
code (`ValueError` for precondition failures vs. `CalledProcessError`/
`git` non-zero exit for execution failures).

## 30. Verification Strategy for Future Coverage

A future implementation phase should be able to assert "all autonomy-
critical mutation dispatches route through the canonical boundary" by
construction, not by an ever-growing string-grep test. Concretely: once
each of the 5 mutation-class adapters exists, every one of the 13 sites
in §5 should call its class's adapter and nowhere else construct a
`PermissionBrokerRequest` inline (Chapter 148's per-site duplication in
`push.py:698`/`push.py:898` should itself be an early candidate for
consolidation onto the shared adapter). This phase records the
principle; it does not implement the assertion mechanism.

## 31. Mutation Registry

A static registry (operation ID, mutation class, entry function,
execution class, permission owner, adapter, status) would be useful
documentation, mirroring how `HARD_BLOCK_REGISTRY` and `POLICY_
REGISTRY` already exist as static registries in this codebase. §5's
table in this document effectively *is* that registry today; whether it
becomes a first-class production artifact is a future-phase decision,
not built here.

## 32. Chapter 149 Proposed Scope

```
Chapter 149: Repository-Wide Mutation Permission Coverage
IN:
  - commit (agent.py, task.py)
  - push (agent.py, phase.py duplicate sites — consolidate onto the
    canonical push adapter alongside pcae push)
  - rollback (agent.py)
  - file-apply / promotion (agent.py ECP/EPR/PER pipeline — highest
    priority, can already write into src/pcae/**)
  - backend-created-output-adoption add/commit/push sites (consolidate,
    do not leave as a fourth independent pipeline)
OUT:
  - lifecycle-state/bookkeeping writes under .pcae/** (M6)
  - canonical artifact publication (M7, Ch. 114/144-146 authority)
  - external notifications (M8)
  - manual human git usage
  - tests/fixtures
  - Prompt Creation/Dispatch, agent invocation, runtime capability
    activation (all separately gated, separately authorized)
  - pcae task finish --commit / finish recover (LIFECYCLE_INTERNAL,
    narrow scope, KEEP_SEPARATE unless future evidence changes this)
```

## 33. Threat Model

| Threat | Control (architectural) |
|---|---|
| Direct mutation bypass (caller reaches git/file mutation below the permission layer) | Per-class adapters become the only sanctioned dispatch path; existing direct-call sites (§5) are the migration list |
| Agent self-permission (agent controls approval/class/policy) | `approval_present` must derive from a source the requesting agent cannot itself set end-to-end (§24) |
| Legacy alternate path (old helper bypasses canonical service) | Explicit disposition per path (§16) — route or consolidate rather than leave parallel |
| Stale ALLOW (decision reused for a changed operation) | Freshness validation, generalized from push's existing mechanism (§27) |
| Policy downgrading (caller picks a weaker execution class) | Execution-class mapping fixed per operation type by the adapter, not caller-selectable (§21) |
| Approval fabrication (confirmation relabeled as approval) | Confirmation and approval kept structurally distinct (§23); today's bare-flag approval evidence flagged as weak, not treated as sufficient |
| Partial mutation | PER's existing partial-status model (§29) is a usable precedent |
| Rollback abuse (rollback as a privileged bypass) | Rollback already sits in POL-004's approval-required set (§26) — must not be weakened |
| Mechanical override bypassing structural validation | Existing structural checks (scope_validation, approval_state, ancestry, ECP/EPR divergence) are preserved unchanged, not replaced by the broker call (§19) |

## 34. Findings Classification

- **STRATEGIC_GAP (highest priority):** `pcae promote` (ECP/EPR/PER,
  §6.2) is a real, CLI-reachable, ungated file-write/delete mechanism
  that can target `src/pcae/**` directly — the strongest evidence yet
  found for why this chapter is needed.
- **STRATEGIC_GAP:** three independently-built adoption pipelines exist
  (`pcae remote *`, `pcae promote`, backend-created-output-adoption)
  with no shared code or common gate (§16/§17).
- **STRATEGIC_GAP:** `commands/task.py`'s two commit sites were not
  previously inventoried (149A) — now recorded (§6.3).
- **STRATEGIC_POLICY_GAP:** no execution-class classification exists
  for file-apply (`pcae promote`) (§21/§22).
- **STRATEGIC_POLICY_GAP:** no defined standard for what constitutes
  legitimate `approval_present` evidence beyond a self-declared flag
  (§22/§24).
- **OBSERVATION:** PBPA-001's existing vocabulary (`ACTION_COMMIT`,
  `ACTION_ROLLBACK`, `EXECUTION_CLASS_ROLLBACK`, POL-004's mutation/
  rollback distinction) already anticipates most of this chapter's
  needs and appears not to require new policy semantics to *begin*
  wiring commit/rollback (§20).
- **OBSERVATION:** Runtime Enforcement remains correctly out of scope
  for this chapter's boundary (§13/§17 Model D).
- **DEFERRED:** Prompt Creation, Prompt Dispatch, agent invocation,
  runtime capability activation — untouched, per 149A.
- **NON-BLOCKING:** the maintenance-debt items 149A already separated
  out (§13 of that document) remain unaddressed and out of this
  phase's scope.

## 35. Architecture Verdict

**REPOSITORY-WIDE MUTATION PERMISSION COVERAGE ARCHITECTURE: DEFINED.**

Selected model: **E — Hybrid** (canonical request → Permission Broker
decision → per-mutation-class adapter → existing dispatch), per §18.

## 36. Required Final Strategic Output

1. **What real mutation paths exist?** 13 (§5): 2 push (gated), 11
   ungated across commit/push/rollback/file-apply in `agent.py`,
   `task.py`, and `phase.py`.
2. **Which are autonomy-critical?** `pcae remote *`, `pcae promote`,
   and backend-created-output-adoption (§16) — all three are real or
   near-real "adopt externally-produced changes" pipelines. `pcae task
   finish` paths are lifecycle-internal, not autonomy-critical.
3. **Which are currently permission-governed?** Only `pcae push` (both
   sites), via PBPC-001 v1.2.
4. **Which are not?** The other 11 (§5/§12).
5. **Retire vs. route vs. broker-cover?** §16: `pcae remote *` and
   `pcae promote` → BROKER_WIRE. Backend-created-output-adoption push →
   ROUTE_TO_CANONICAL_COMMAND; its add/commit → BROKER_WIRE, consolidated
   rather than left parallel. Final-verification-tooling-push → ROUTE_
   TO_CANONICAL_COMMAND. `pcae task finish` → KEEP_SEPARATE.
6. **What canonical mutation boundary should future PCAE use?** The
   Model-E chain in §19: canonical request → broker decision →
   per-class adapter → existing dispatch.
7. **Does existing PBPA suffice?** Largely yes for commit/push/rollback
   (§20); file-apply's classification is an open mapping question
   (§21/§22), not a missing-schema problem.
8. **Is a new broader contract required?** Yes — a new, additive
   contract generalizing PBPC-001's pattern (not amending PBPC-001
   itself), tentatively `RWMPC-001` (exact ID per next phase's
   convention check).
9. **What exact phase comes next?** See §37.

## 37. Recommended Next Phase

**149C — Repository-Wide Mutation Permission Coverage Contract Freeze**
(exact title per repository convention at that time), scoped to: define
the per-class adapter contract (commit, rollback, file-apply, and
push-consolidation) reusing `PermissionBrokerRequest`/
`permission_broker_foundation` unchanged; resolve the file-apply
execution-class mapping gap (§21/§22); define what constitutes
legitimate `approval_present` evidence for rollback and file-apply
(§22/§24); require no change to PBPC-001 or PBPA-001 text, only an
additive contract. Each phase in this sequence (Contract Freeze →
Independent Contract Verification → Implementation Plan →
Implementation → Independent Implementation Verification → Operational
Readiness → Certification) requires its own separate authorization;
none is pre-authorized by this document.

## 38. Runtime State (Confirmed Unchanged)

Before and after this phase: `pcae runtime inspect` reports `Runtime
state: Observed`, `Execution capability: unavailable`, `Maximum plugin
capability: observe`, `Permission Broker status:
execution_unavailable`. No runtime capability elevation occurred or is
authorized by this document.

## 39. Boundary Verification

- `git diff --name-only 55a1f8aa..HEAD -- src/pcae/`: empty (no
  production code modified by this phase).
- `git diff --name-only 55a1f8aa..HEAD -- docs/contracts/`: empty (no
  contract modified; PBPC-001 remains v1.2; PBPA-001 remains v1.0).
- No POL-001..012 meaning changed. No POL-013+ added. No new Permission
  Broker production consumer added. No existing mutation path was
  modified, activated, or exercised — every finding above is pre-
  existing code, independently observed only. No Prompt Generation,
  Prompt Dispatch, or agent invocation capability implemented. No
  runtime execution capability enabled.
