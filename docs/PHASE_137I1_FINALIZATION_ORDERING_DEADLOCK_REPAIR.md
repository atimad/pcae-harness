# Phase 137I.1 — Finalization Ordering Deadlock Repair

## Incident identity

- **Phase:** 137I.1 (lifecycle repair phase; not TAMPC-001 contract work).
- **Trigger state (live, reproduced before any change):** Phase 137I (an
  independent-verification phase) completed with 5 local commits ahead of
  `origin/main`, working tree clean, its task relocated into `tasks/done/`,
  but `.pcae/phase-reports/latest.json` still identified Phase **137H**
  (stale). `pcae push` refused; `pcae phase complete` refused. The
  repository could not be finalized through any governed workflow.
- **Runtime throughout:** State `Observed`, Maximum Capability `observe`,
  Execution Availability `unavailable` — unchanged.

## 1. Live reproduction (primary evidence, run before theorizing)

```
$ pcae push check
  Phase report trust: passed
  Phase report identity: failed
    Canonical phase report identifies phase '137H', but the latest completed
    phase task is Phase '137I' (...). ... run `pcae phase complete` ... before pushing.
  Mode: not_ready        (exit 1)

$ pcae phase complete --summary "..."      # for 137I
  Repository transition validator: Transition rejected
    Violation: phase_identity_consistency - Disagreeing phase identity sources: ['137I', '137i']
    Violation: report_completeness - report_completeness is 'partial' (partial validation)
  Phase report: BLOCKED by finalization gate
    Blocker: pushed_status is 'not_pushed', not pushed/clean
    Blocker: origin/main..HEAD is 5, not 0
    Blocker: report completeness is 'partial', not complete
    Blocker: missing trust fields: pushed_status, origin_main_head
  Phase completion rejected -- latest.md/latest.json were NOT written.
```

`latest.json` remained `137H`. Both governed exits are non-recovering: push
needs a canonical report that finalization refuses to write until pushed.

## 2. Root cause

The deadlock is a genuine, code-level circular dependency, exposed (not
caused) by an operator-sequencing violation.

### 2a. The circular dependency

1. **Push readiness — phase-report-identity gate** (`_detect_phase_report_gap`,
   `src/pcae/commands/push.py`, added Phase 137F.1, hardened 137F.1V):
   blocks push unless `latest.json.phase_id` equals the **latest completed
   phase in `tasks/done/`**. For 137I in `done` with `latest.json = 137H`,
   this fails.
2. **Writing `latest.json`** is only done by `finalize_phase_report`
   (`src/pcae/core/phase_reports.py`), which **quarantines** (writes nothing
   to `latest.*`) whenever the finalization gate is not finalizable
   (Phase 113X.1; hardened 135H.2 so even `--allow-partial-report` cannot
   confer the canonical write).
3. **The finalization gate** (`validate_finalization_gate`) hard-blocks on
   `origin/main..HEAD > 0` and `pushed_status not in {pushed, clean,
   nothing_to_push}` — i.e. it is unsatisfiable until the phase is pushed.
4. **Pushing** requires (1). Cycle closed.

The cycle is only reachable when a phase's task is in `tasks/done/` **while
the repo is unpushed and `latest.json` does not yet identify it**. In the
healthy flow this never happens (see §3), so the cycle stayed latent from
137F.1 until 137I tripped it.

### 2b. Why `.pcae/phase-reports/latest.json` being gitignored matters

`latest.json` is **not tracked** (`.pcae/phase-reports/latest.json` is in
`.gitignore`). Writing it therefore creates no commit. The healthy flow
depends on this: the report is (re)written locally *after* a push without
producing new unpushed commits. The identity gate, however, made the
*existence and correctness* of that untracked file a precondition of push —
which is exactly what closes the loop.

### 2c. Secondary defect — case-sensitive phase identity

`_check_phase_identity_consistency` (`repository_transition_validator.py`)
deduplicated identity sources by exact string. The idle-placeholder task
slug (`...-post-137i`) yields `137i`; metadata yields `137I`. These are the
**same** phase, but the set `{'137I','137i'}` was reported as a
disagreement, adding a second, independent hard rejection to any
finalization attempted while an idle placeholder is active.

### 2d. Which gate introduced the dependency (git archaeology)

- `_detect_phase_report_gap` — Phase **137F.1** (`git log` subjects
  reference 137F.1 / 137F.1V); made unconditional in 137F.1V, deliberately
  closing the "close a phase without a report, then open a non-idle task"
  bypass — the very shape 137I hit. The gate is working as designed; the
  missing piece is a governed way to *produce* the report pre-push.
- Quarantine-on-blocked-gate — Phase **113X.1**; `--allow-partial-report`
  neutered for promotion in **135H.2**.
- Push-state hard blockers in the gate — Phase **95I.1 / 105C.1 / 114C**.

## 3. Why previous phases (137F.1 … 137H) never exposed it

The healthy ordering is: **push while the phase task is still active**, then
finalize, then relocate the task to `done`. At push time the *latest
completed* phase is the **previous** (already-finalized) phase, so
`latest.json` matches and the identity gate passes; the current phase's
report is written locally *after* the push (gate now satisfiable) and only
then is its task closed to `done`. 137I violated this: it relocated its task
to `done` and opened an idle placeholder **before** pushing and **before**
finalizing, landing the repository directly on the one state the cycle needs.
So the deadlock is a real code gap (no governed recovery once that state is
reached) surfaced by an ordering violation.

## 4. Lifecycle ordering graph (as-built, per code + live run)

```
task work ──▶ commit (pcae commit implementation)          [tree, unpushed commits]
     │
     ├─(healthy)──▶ push (task ACTIVE; identity gate vs PREVIOUS phase ✓)
     │                    │  origin/main..HEAD → 0
     │                    ▼
     │             phase complete / task finish             ── writes latest.* (COMPLETE, authoritative)
     │                    │                                    ── dispatch exactly-once notification
     │                    ▼
     │             close task → tasks/done ; open idle
     │
     └─(137I mis-order)─▶ close task → done ; open idle  BEFORE push/finalize
                          │
                          ▼   DEADLOCK: latest.json ≠ latest-done, and
                              finalize refuses to write it until pushed.
```

Transition authority summary (owner / input → output / rollback):

| Transition | Owner | Authority state after | Rollback |
|---|---|---|---|
| commit | `pcae commit implementation` | none | git (uncommitted work) |
| **pending stage (137I.1, new)** | `finalize_phase_report(allow_pending_push)` | **pending_push (NON-authoritative, no notify)** | overwrite/quarantine on next finalize |
| push | `pcae push` (governed) | commits durable | n/a (git push atomic) |
| promote | `finalize_phase_report` (gate finalizable) | **COMPLETE / authoritative** | quarantine if gate fails |
| notify | notification certification + finalize | dispatched exactly once (marker) | idempotent skip on replay |
| relocate task | `pcae task close/finish` | phase in `done` | task reopen (manual) |

The **only** point at which a report becomes authoritative is the
post-push promotion. The new pending state is explicitly *before* and
*below* authority.

## 5. Repair applied (narrow, additive)

The fix adds a governed intermediate lifecycle state — a **pending canonical
report** — filling the gap the lifecycle architecture omitted. No existing
gate is weakened.

### 5a. `finalize_phase_report(..., allow_pending_push=False)` (`phase_reports.py`)

When (and only when) the finalization gate's **entire** blocker set is
push-state (`blockers_are_push_state_only`, a new closed classifier) **and**
the report is otherwise fully complete (identity, coherence, governance,
no-go, and every non-push trust field), the report is written to the
canonical `latest.*` slot with `report_completeness = "pending_push"` (a new,
explicitly **non-authoritative** completeness state) instead of being
quarantined. A pending report is **never** trust-complete, **never**
authoritative, and **never** notified. Any genuine integrity blocker still
quarantines exactly as before. `allow_pending_push` defaults to `False`, so
every existing caller and test is behaviorally unchanged.

### 5b. `--stage-pending-report` on `pcae phase complete` (`cli.py`, `commands/phase.py`)

A new opt-in flag. It treats the transition's `report_completeness` as
`--allow-partial-report` already does (push fields are legitimately not yet
final) and sets `allow_pending_push` — but *only* passes it through when the
gate's blockers are push-state-only. The command prints a clear "STAGED
PENDING PUSH (not authoritative, not notified)" outcome and instructs the
operator to push then re-run `pcae phase complete` (no flag) to promote to
COMPLETE and dispatch exactly one notification.

### 5c. Case-insensitive phase identity (`repository_transition_validator.py`)

`_check_phase_identity_consistency` now deduplicates identity sources
case-insensitively (canonical form is upper-case). `137I` vs `137i` no
longer falsely disagree; a genuine cross-phase disagreement (e.g. `137I`
vs `137I.1`) still blocks.

### Governed recovery sequence (used live for this incident)

1. `pcae phase complete --phase-id 137I ... --stage-pending-report`
   → `latest.json` = 137I (`pending_push`); no notification.
2. commit the 137I.1 repair; `pcae push check` → identity **passed**.
3. `pcae push` (governed) → `origin/main..HEAD = 0`.
4. `pcae phase complete` (137I.1) → COMPLETE, authoritative, one notification.

No raw `git push`/`git commit`, no manual file editing, no manual lifecycle
override.

## 6. Alternatives considered and rejected

- **(H) Weaken the identity gate to accept a stale/absent report when
  unpushed** — rejected: reopens exactly the 137F.1V bypass (close without
  report, open non-idle task). The gate must stay strict.
- **(B/C/D) Transactional pre-finalization / two-phase publication /
  pre-push staging as a separate artifact store** — the pending state
  achieves the same guarantee reusing the existing canonical writer and the
  existing `push_state_aware=False` trust read (`_assess_phase_report_trust`
  already anticipates pending pre-push reports), so a parallel store is
  unnecessary surface area.
- **(E/F) Push-intent receipts / transaction journal** — heavier machinery
  for a problem that is fully solved by one non-authoritative completeness
  state plus one classifier.
- **Auto-stage pending on every push-blocked `phase complete` (no flag)** —
  rejected for this repair to keep blast radius minimal and the authority
  transition explicit; the opt-in flag is sufficient and auditable.
- **Reopen 137I by moving its task file `done → active`** — rejected: a
  manual lifecycle override (No-Go), and no governed `task reopen` exists.

## 7. Transaction guarantees preserved

No authority before successful push (pending is non-authoritative); no
notification before push (pending never notifies); exactly-once publication
(promotion overwrites the pending slot; timestamped artifacts are distinct);
exactly-once notification (notification-certification marker unchanged — the
pending stage records a skip, the post-push promotion is the first and only
dispatch); no stale bootstrap/metadata after completion (promotion rewrites
`latest.*`); no orphan receipts; genuine integrity defects still quarantine.

## 8. Regression + adversarial evidence

- **New unit tests** — `tests/test_phase_137i1_finalization_ordering_deadlock.py`
  (11 tests): the push-state-only classifier (pure push, `pcae_push_check`,
  integrity-mixed, non-push-missing-field, empty); pending write is
  non-authoritative + never notified; pending requires opt-in; an integrity
  blocker is never staged even with opt-in; case-variant identities agree
  while distinct ones disagree. All pass.
- **Targeted suites (971 passed):** `test_finalization_gate_enforcement`,
  `test_phase_report_trust_hard_fail`, `test_phase`, `test_phase_reports_cli`,
  `test_canonical_phase_identity_source_repair`,
  `test_repository_transition_validator_task_finish_integration`.
- **Push / notification / task-finish suites (124 passed):** `test_push`,
  `test_task_finish_notification_ordering`,
  `test_notification_certification_idempotency`,
  `test_task_finish_report_trust_notification`,
  `test_phase_113v_n_notification_finalization_repair`,
  `test_push_state_reconciliation`.
- **Live adversarial:** the actual deadlocked repository was recovered end
  to end through the governed sequence in §5, ending pushed and green.

Pre-existing/inherited failures (documented against the unmodified tree in
137I's own metadata; not introduced here): 3 `test_bootstrap_todo_consistency`
regex-signature assertions and 1 `test_phase_reports.py` notification-marker
checkpoint test.

## 9. Findings classification

- **BLOCKING:** none remaining. The circular dependency is eliminated by a
  governed, deterministic escape; push readiness, report integrity, metadata
  integrity, lifecycle authority, notification exactly-once, and bootstrap
  correctness are all preserved.
- **NON-BLOCKING:** the case-sensitive identity comparison (§2c) — repaired.
- **DEFERRED:** an optional *preventive* guard that refuses to relocate a
  phase task to `tasks/done/` before it is pushed+finalized (defense in
  depth; the pending-report escape already makes the mis-ordered state
  recoverable without it). Phase 137I's own historical commits remain in
  `done` without a standalone COMPLETE report; superseded by 137I.1 as the
  authoritative latest phase.

## 10. Verdict

The finalization-ordering deadlock was a **genuine code defect** (a real
circular dependency with no governed recovery), surfaced by an operator
sequencing violation. It is repaired narrowly and additively via a
non-authoritative pending canonical-report state plus a case-insensitive
identity fix, with every prior trust guarantee (134A–134F, 135A–135Z,
137F/137F.1/137F.1V) preserved. Runtime remained Observed / observe /
unavailable throughout.

## Recommended next phase

**137I.1V — Finalization Ordering Deadlock Independent Verification.**
Implementation planning (137J) remains blocked until that independent
verification completes cleanly.
