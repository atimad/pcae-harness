# PCAE Repository Transition Validator — Contract Freeze

**Status:** Contract frozen. Architecture/design only — no implementation.
**Supersedes:** Nothing. **Extends:** `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR.md` (113S).
**Origin:** Phase 113T, elevating an asymmetry discovered during 113S's own
finalization from an implementation detail to a frozen architectural
invariant.

## 0. Core Principle (Frozen)

> Repository state is authoritative. Commands are merely transition
> requests. No command owns canonical state. Every canonical state
> transition must be validated through exactly one Repository
> Transition Validator.

This restates 113S's principle ("Model proposes, PCAE validates") one
level more strictly: it is not just models that must not self-certify —
**no command**, regardless of how it was invoked (human, script,
scheduler, future automation), may write canonical state without
passing through the same validation path as every other command.

## 1. The 113S Asymmetry (Elevated to Contract Requirement)

### 1.1 What was observed

During 113S's own finalization, two independent paths were found to
write `.pcae/phase-reports/latest.json`/`latest.md`:

1. **`pcae phase complete`** — resolves canonical phase identity via
   `resolve_canonical_phase_identity()` (113X.4's precedence: active
   task contract > phase-completion metadata > active lifecycle context
   > explicit CLI argument), then builds and writes the report.
2. **`pcae task finish --commit`** (`_finalize_task_report_and_notify()`
   in `commands/task.py`) — writes `latest.json`/`latest.md` directly
   from `.pcae/phase-completion-metadata.json`'s raw fields, without
   consulting the active task contract, PROJECT_STATUS.md, or any CLI
   argument.

Because the operating convention at the time was to revert
`.pcae/phase-completion-metadata.json` to its stale prior-phase content
immediately after `pcae phase complete` ran (to keep that file's git
history quiet), and `pcae task finish --commit` was run *after* that
revert, `task finish`'s independent write silently overwrote the
correct, freshly-certified 113S report with stale content belonging to
an earlier phase. This was caught by manual re-inspection, not by any
mechanism — the finalization gate that validated `phase complete`'s
own report had no visibility into `task finish`'s separate write path
at all.

### 1.2 Why this is not "just a bug"

The immediate cause (reverting a metadata file at the wrong moment) is
a process error. But the *structural* fact that made the process error
possible — **two independently-implemented code paths, each capable of
writing the same canonical artifact, using different identity-derivation
logic** — is an architecture defect, not a process defect. A process
fix (don't revert metadata before task finish) only closes this one
instance. The contract requirement below closes the category.

### 1.3 Frozen requirement — Canonical Transition Authority (first-class requirement)

> **There must never exist two independent canonical report promotion paths.**

This is a first-class requirement, not an implementation detail. Every
code path capable of writing `latest.json`/`latest.md` (or any future
canonical artifact) must call through the same Repository Transition
Validator evaluation, using the same identity resolution, before any
write occurs. The following must all pass through exactly the same
validation path: `pcae phase complete`, `pcae task finish --commit`,
future automation, future scheduler, future Telegram completion,
future REST completion, future agent completion, and future execution
engine completion. `pcae phase complete` and `pcae task finish
--commit` are the two paths that exist *today*; the requirement is
written generally because it must also bind every future path just
listed, per §4.

## 2. Transition Validator Interface (Frozen)

```
validate_transition(
    current_state:          RepositoryState,
    proposed_transition:     ProposedTransition,
    expected_target_state:   RepositoryState,
    invariants:              InvariantSet,
) -> TransitionVerdict
```

`TransitionVerdict` is exactly one of, frozen, no fifth value:

- **Accept** — `expected_target_state` may become canonical.
- **Reject** — refused; no canonical state changes at all.
- **Quarantine** — an artifact is retained for inspection but never
  promoted to `latest`/canonical.
- **Requires Human Review** — cannot proceed without explicit human
  approval; no canonical state changes until approval is recorded.

This is unchanged from 113S (§3 of the architecture document) and is
now frozen: future phases may add invariants to `InvariantSet` but may
not add a fifth verdict, change the meaning of an existing verdict, or
introduce a verdict-bypassing code path.

## 3. Repository State (Frozen)

Each canonical repository object below is frozen with an explicit
owner, authoritative source, lifecycle, and mutability rule. This
extends 113S §1's list (which named the components) with the
ownership/lifecycle/mutability detail 113S left implicit.

| Object | Owner | Authoritative source | Lifecycle | Mutability |
|---|---|---|---|---|
| Git state | Git | `git log`/`git status`/`git rev-list` | Append-only (commits), reversible only via explicit git operations | Immutable once committed; working tree mutable |
| Working tree | Task lifecycle | Filesystem, scoped by active task contract | Created by `modify_files` transitions, cleared by `commit`/`finish_task` | Mutable only within active task's allowed-files/zones |
| Active task | Task lifecycle | `tasks/active/*.md` (task contract) | `start_task` → `modify_files`* → `finish_task` | One active task at a time; contract fields replace (not append) on update |
| Phase identity | Identity Authority (§6) | `resolve_canonical_phase_identity()`'s single precedence chain | Resolved once per `complete_phase` transition | Immutable once resolved for a given transition; never re-derived from free text |
| Project status | Phase lifecycle | `PROJECT_STATUS.md` | One `## Current Phase` section, growing list of `## Phase X Complete` sections | Append-only for completed-phase sections; `## Current Phase` replaced each phase |
| Phase reports | Canonical Promotion Authority (§5) | `.pcae/phase-reports/latest.{md,json}` + `quarantine/*` | Draft → Blocked/Quarantined/Certified → Canonical | Canonical location overwritten only by an Accept verdict |
| Phase-completion metadata | Metadata Authority (§6) | `.pcae/phase-completion-metadata.json` | Written fresh per phase, read once at `complete_phase` transition time | Single source; never partially patched, never read by more than one promotion path |
| Architecture status | Phase lifecycle (derived) | `build_architecture_status()` | Recomputed every `complete_phase` transition | Fully derived; never hand-edited |
| Test results | Validation subsystem | Live pytest re-runs + structured `test_results` | Captured once per `complete_phase` transition | Immutable once captured for that transition |
| Governance checks | Validation subsystem | `pcae health`/`check`/`doctor task-memory` | Re-run on demand | Read-only observations, never stored as mutable state |
| Notification state | Notification Authority (§7) | `.pcae/phase-reports/.last-notified.json` + `notification_result` | Set once per certified, push-clean phase | Write-once per phase; never re-dispatched |
| Push state | Git + push governance | `origin/main..HEAD`, `pcae push check` | Recomputed on every push attempt | Read-only observation of git state |
| Runtime state | Runtime Snapshot (out of scope) | `pcae runtime inspect` | Unaffected by this contract | Not touched by the validator |
| Execution availability | Permission Broker (out of scope) | Broker status | Unaffected by this contract | Not touched by the validator; assumed `unavailable` per invariant §8's no-execution rule |

## 4. Transition Contracts (Frozen)

Every lifecycle operation is a **proposed transition only** — none of
them may write canonical state directly. Frozen list of transition
kinds (extends 113S §2's 10 kinds with explicit promotion/notification
splits called out by this phase's brief):

- `start_task`
- `modify_files`
- `run_validation`
- `commit`
- `finish_task`
- `complete_phase`
- `report_generation` — producing a Draft artifact
- `report_promotion` — Draft/Certified → Canonical (§5)
- `push`
- `notify`
- `status_update`
- `roadmap_update`

**No command may bypass the validator.** This is the frozen form of
§1.3's requirement, restated per-transition: `finish_task`'s report
side-effects and `complete_phase`'s report side-effects are the *same*
`report_generation`/`report_promotion` transitions, evaluated the same
way, regardless of which command triggered them.

## 5. Canonical Promotion Contract (Frozen)

Six states, frozen, one-directional:

1. **Draft** — in-progress artifact, not yet submitted for validation.
2. **Blocked** — submitted, Reject verdict. Not retained as a
   distinguishable artifact.
3. **Rejected** — synonym for Blocked's terminal outcome, listed
   separately per this phase's brief to make explicit that Reject is a
   named artifact state, not merely a verdict in transit.
4. **Quarantined** — submitted, Quarantine verdict. Retained on disk
   (mirrors `.pcae/phase-reports/quarantine/`), never overwrites
   `latest`.
5. **Certified** — submitted, Accept verdict. Passed every invariant;
   eligible for promotion.
6. **Canonical** (`latest.*`) — a Certified artifact has been promoted.

**Only Certified may become Canonical.** Frozen without exception: no
future transition kind, automation, or agent may promote a
Draft/Blocked/Rejected/Quarantined artifact to Canonical through any
path.

## 6. Identity Contract (Frozen)

Four singular authorities, frozen:

1. **Single identity source** — `resolve_canonical_phase_identity()`'s
   precedence chain (active task contract > phase-completion metadata
   > active lifecycle context > explicit CLI argument) is the *only*
   place phase identity may be derived. No command computes identity
   independently.
2. **Single report promotion source** — one promotion function decides
   Draft → Certified → Canonical for every transition kind in §4. Today
   this function is `finalize_phase_report()`; the contract requirement
   is that it remains the only writer of `latest.json`/`latest.md`,
   called by every command in §4's list, not reimplemented per-command.
3. **Single metadata source** — `.pcae/phase-completion-metadata.json`
   is read exactly once per `complete_phase`/`finish_task` transition,
   by exactly one reader, at transition-evaluation time. It is never
   read a second time by a second, independent path for the same
   transition.
4. **Single canonical report source** — `.pcae/phase-reports/latest.{md,json}`
   is written by exactly one code path (the promotion function in
   point 2), never by two.

**No alternate identity derivation. No alternate promotion pipeline.**
This directly closes the 113S asymmetry: `pcae task finish --commit`'s
own report-writing logic is no longer permitted to exist as a second,
independent pipeline — its `report_generation`/`report_promotion`
transitions must route through the same single pipeline `pcae phase
complete` uses.

## 7. Notification Contract (Frozen)

Extends 113S §7 with idempotency and certification made explicit as
frozen contract terms, not just architectural description:

- **Notification eligibility** — dispatch only when: phase finalized
  (Accept verdict reached) + canonical report Certified (§5) + push
  state clean + not already dispatched + transport configured/enabled.
  All five, simultaneously.
- **Notification idempotency** — at most one canonical "phase complete"
  notification per phase, ever, regardless of how many commands
  attempt to trigger it (`phase complete`, `task finish --commit`, any
  future automation). This closes the idempotency-guard asymmetry
  documented but not fixed in 113XR (`task finish --commit`'s
  `.last-notified.json` guard existed; `phase complete`'s did not) —
  under this contract, idempotency is enforced once, centrally, by the
  same single notification-eligibility check every transition path
  shares, not per-command.
- **Single external notification** — same phase, same verdict, same
  dispatch, exactly once.
- **Notification certification** — a notification may only reference a
  Certified, Canonical report. It may never reference a Draft, Blocked,
  or Quarantined artifact.
- **No intermediate external notification.** A quarantined or
  blocked-then-repaired report never generates a normal "Phase
  COMPLETED" external notification for its intermediate state — only
  the distinctly-titled, severity-flagged partial-warning event (113X.3)
  may fire for a partial state, and only once.

## 8. Invariant Contract (Frozen)

Every invariant family from 113S §4 is frozen here with an explicit
classification. This is new relative to 113S, which listed invariants
without classifying their force:

| Invariant family | Class |
|---|---|
| Phase identity consistency | Mandatory, blocking |
| Active task consistency | Mandatory, blocking |
| Allowed file scope | Mandatory, blocking |
| Commit lineage | Mandatory, blocking |
| Report completeness | Mandatory, blocking |
| Report trust | Mandatory, blocking |
| Metadata consistency | Mandatory, blocking |
| Architecture status consistency | Derived, blocking |
| Recommended-next-phase consistency | Derived, warning |
| Test result consistency | Mandatory, blocking |
| Push state consistency | Derived, blocking |
| Notification eligibility | Mandatory, blocking |
| Single final notification | Mandatory, blocking |
| No execution availability unless explicitly enabled by future contract | Mandatory, blocking |
| No canonical artifact promotion when blocked | Mandatory, blocking |
| Single canonical transition authority (new, §1.3/§4) | Mandatory, blocking |
| Single identity/promotion/metadata source (new, §6) | Mandatory, blocking |
| Notification idempotency across all trigger paths (new, §7) | Mandatory, blocking |
| Architecture-Status-as-dedicated-service | Future, informational (113X.5's own open question, still deferred) |

Classification legend:

- **Mandatory** — must hold for Accept; violation forces Reject/
  Quarantine/Human-Review per §9.
- **Derived** — computed from other mandatory invariants; its own
  violation is only ever a symptom, never checked independently of its
  inputs.
- **Optional** — may be waived by explicit human override (none exist
  in the frozen set today; reserved for future use).
- **Future** — not yet enforced; documented so a later phase doesn't
  have to rediscover the gap.
- **Blocking** — failure forces Reject or Quarantine (never silently
  ignored).
- **Warning** — failure is surfaced but does not by itself force
  Reject (e.g. recommended-next-phase mismatches are flagged but a
  report already Certified on every mandatory invariant is not undone
  by this alone — mirrors 113X.5's design, where check #3 was
  deliberately kept informational).
- **Informational** — surfaced for awareness only, never gates a
  verdict.

## 9. Failure Contract (Frozen)

Every failure mode below resolves deterministically to exactly one of
Reject, Quarantine, or Requires Human Review. **Undefined behavior is
not a permitted outcome under this contract.**

| Failure mode | Resolves to |
|---|---|
| Identity mismatch (report vs. PROJECT_STATUS.md vs. metadata vs. active task) | Reject |
| Metadata mismatch (metadata phase_id disagrees with resolved identity) | Reject |
| Commit mismatch (commit message references a different phase than the report claims) | Reject |
| Report mismatch (structural fields disagree with each other, e.g. test_results contradicts summary) | Quarantine |
| Architecture mismatch (impossible completed/in_progress/planned combination) | Reject |
| Notification mismatch (eligibility conditions not simultaneously met) | Reject (for the notify transition only; does not by itself reject the underlying phase-complete transition) |
| Validator unavailable (the validation path itself cannot run — e.g. required file missing, exception raised) | Requires Human Review |
| Missing evidence (a mandatory invariant has no data to evaluate, e.g. no test results captured at all) | Reject |
| Partial validation (some invariants evaluated, others could not be evaluated for a structural reason) | Quarantine |

No failure mode maps to Accept, and no failure mode is left unmapped.

## 10. Semantic Boundary (Frozen)

Unchanged from 113S §8, restated as a frozen rule rather than a
description:

> Models perform semantic work (code design, implementation strategy,
> explanations, remediation, prose). The Repository Transition
> Validator certifies structural correctness (identity, lifecycle,
> scope, reports, commits, pushes, notifications, canonical state).
> **Models never certify themselves.** A model's own claim that its
> work is correct, complete, or trustworthy has no bearing on the
> validator's verdict.

## 11. Future Integration (Frozen Scope, Not Frozen Design)

The validator's eventual integration points are frozen as a *scope*
(these subsystems will integrate with it) without freezing *how* (that
remains open for the phases that build each integration):

- **Task lifecycle** — `start_task`/`modify_files`/`finish_task`
  transitions route through the validator; `check_task_zone_scope()`/
  `check_task_file_scope()` become one invariant family.
- **Phase lifecycle** — `complete_phase` transitions route through the
  validator; `validate_finalization_gate()`/`validate_phase_identity()`
  become the report-completeness/identity invariant families.
- **Runtime Snapshot** — remains a read-only input the validator may
  consult for context (e.g. confirming `execution_availability`) but
  never mutates.
- **Runtime Inspect** — remains a read-only observation surface;
  `pcae runtime inspect` output may be an evidence source for an
  invariant, never a target the validator writes to.
- **Advisory Runtime** — remains entirely out of scope for the
  validator's content; the validator may confirm Advisory Runtime made
  no unauthorized state changes, but does not evaluate advisory
  recommendations themselves.
- **Permission Broker** — remains the sole authority for execution
  authorization; the validator's "no execution availability" invariant
  (§8) is a *check that the Broker's posture hasn't silently changed*,
  never a mechanism that grants or denies execution itself.
- **Execution runtime** (future) — when introduced, "propose an
  execution" becomes a `run_execution` transition kind; the validator
  gains an execution-authorization invariant family without changing
  its own shape.
- **Approval runtime** (future) — "Requires Human Review" verdicts
  route to whatever approval mechanism is eventually built; the
  validator's contract is that it *asks*, not that it implements the
  asking.
- **Future execution** — every future execution-capable transition is
  automatically subject to the same single validator, the same
  invariant-classification discipline (§8), and the same failure
  contract (§9) as every transition that exists today.

## 12. Non-Goals (This Phase)

Explicitly out of scope for Phase 113T:

- No `validate_transition()` implementation.
- No change to `pcae phase complete`, `pcae task finish --commit`, or
  any other existing command's actual behavior. The asymmetry
  described in §1 is *documented and frozen as a requirement to close*,
  not closed by this phase.
- No change to Advisory Runtime, Runtime Snapshot, Runtime Context,
  Runtime Registry, Permission Broker, execution capability, plugins,
  Telegram inbound, REST, Web UI, or execution behavior.
- No change to any existing finalization-gate, phase-identity, or
  push-check code path.

Execution capability remains unavailable; this phase does not change
that in any way.
