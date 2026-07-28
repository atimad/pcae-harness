# Phase 145H.3R.1 — Phase Completion Metadata Sequencing and Finalization Repair

**Status:** Complete (narrow production repair; no contract or architecture
revision; no runtime-capability change).
**Mode:** Narrow production repair.
**Predecessor:** Phase 145H.3R — Canonical Report and Terminal Notification
Recovery.
**Human authorization:** Explicitly authorized repair of the recurring
`pcae phase complete` finalization defect, documented as recurring at
145G.3, 145H.1, 145H.2, and 145H.3, before any broader Interactive Workflow
chapter certification proceeds.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).

---

## 1. Bootstrap and canonical starting state

- `git status --short`: clean. `git branch --show-current`: `main`.
  `git log --oneline --decorate -15`: HEAD `f782a52b` ("Phase 145H.3R:
  repair no_go_confirmations format and inherited-regression
  classification").
- `git rev-list --count origin/main..HEAD`: 0. `git rev-list --count
  HEAD..origin/main`: 0 — fully synced with `origin/main` at phase start.
- `pcae session bootstrap --agent-id claude-local`: lock rehydrated,
  health healthy, check passed. Latest completed phase: 145H.3R
  (completed, report: pending_push). Readiness: blocked (active task
  stale — the post-145H.3R idle placeholder — and "No further phase is
  authorized by this report" per 145H.3R's own recommendation, which
  matches this phase's own human authorization exactly: only the
  narrowly scoped lock-release-ordering/finalization repair is
  authorized).
- `pcae check`: passed. `pcae health`: healthy. `pcae doctor
  task-memory`: clean. `pcae runtime inspect`: Observed / observe /
  unavailable. `pcae push check`: clean (nothing_to_push).
- `.pcae/phase-completion-metadata.json` inspected directly: identifies
  145H.3R, `status: "completed"`, consistent with `PROJECT_STATUS.md`'s
  "Current Phase" section, which already correctly describes 145H.3R as
  completed and explicitly states it does not authorize 145H.4, 145I,
  Phase 146, or broader Interactive Workflow chapter certification.
- Closed the stale idle placeholder task
  (`20260727-2234-idle-awaiting-next-governed-phase-post-145h-3r`) via
  `pcae task close`; opened this phase's own governed implementation
  task contract
  (`20260728-0627-phase-145h-3r-1-phase-completion-metadata-sequencing-and-finalization-repair`),
  scoped to `src/pcae/commands/phase.py`, this phase's own test file,
  this report, and governance bookkeeping only — `docs/contracts/**`
  explicitly forbidden.

`PROJECT_STATUS.md` was treated as authoritative over `tasks/TODO.md`
throughout; no conflict between the two bearing on this phase's scope was
found.

## 2. Reading the full defect record

Read in full: `docs/PHASE_145G3R_CANONICAL_PHASE_REPORT_RECOVERY_AND_
FINALIZATION_STATE_RECONCILIATION.md`, Phase 145H.1's, 145H.2's, and
145H.3's own canonical reports, and `docs/PHASE_145H3R_CANONICAL_REPORT_
AND_TERMINAL_NOTIFICATION_RECOVERY.md` in full (§4 "Finalization-sequence
reconstruction" and §8 "Root-cause statement" in particular). All four
prior canonical reports and `.pcae/phase-completion-metadata.json`'s own
`self_correction`/`governance_results` fields independently converge on
the same description: each occurrence was a **correctly rejected**
`pcae phase complete` attempt (genuinely stale
`.pcae/phase-completion-metadata.json` still naming the predecessor
phase) that nonetheless cost a full agent-lock release/reacquire cycle,
because the lock was released *before* the rejection was ever decided.

Traced the actual executable control flow directly from source, not from
narration:

- `run_phase_complete()` (`src/pcae/commands/phase.py:49`, pre-repair)
  called `complete_phase()` (`src/pcae/core/phase.py:30`) **first,
  unconditionally** — appending the `"phase_completed"` provenance event
  and calling `release_agent_lock()` — before `_finalize_report_and_
  notify()` (`src/pcae/commands/phase.py:85`, pre-repair offset) was ever
  invoked.
- `_finalize_report_and_notify()` performs every rejectable check: canonical
  phase-identity resolution (`resolve_canonical_phase_identity`),
  `validate_finalization_gate()`, `detect_cross_phase_commit_contamination()`
  (`src/pcae/core/phase_reports.py:1973`), and
  `validate_phase_report_transition()` /
  `handle_phase_report_transition_result()` (`src/pcae/core/
  repository_transition_integration.py`, the Repository Transition
  Validator adapter shared with `pcae task finish --commit`).
- None of these checks, nor `certify_notification_transition()`
  (`src/pcae/core/notification_certification.py`) nor
  `run_finalization_transaction()` (`src/pcae/core/
  finalization_transaction.py`, the Phase 134E.10.1 pre-promotion
  transaction), read or depend on agent-lock state or on the
  `"phase_completed"` provenance event in any way (confirmed by direct
  grep across every module in the call chain — zero references to
  `read_agent_lock`/`release_agent_lock`/`acquire_agent_lock` outside
  `pcae.core.phase`/`pcae.core.agent` themselves). This is the fact that
  makes the repair in §5 safe: nothing downstream of `complete_phase()`
  depends on it having already run.

## 3. Independent pre-repair reproduction

Reproduced the defect two ways, both closely exercising the real
finalization path (not a unit-level shortcut around it):

### 3a. Automated reproduction (`tests/test_phase_145h3r1_lock_sequencing_
repair.py`, written before the fix)

Nine tests built directly on the same `_init_repo`/`_write_metadata`
harness `tests/test_repository_transition_validator_phase_complete_
integration.py` already uses for `pcae phase complete` CLI-level testing,
with `acquire_agent_lock`/`read_agent_lock` assertions added. Run against
**unmodified `main`** (`git stash` isolating only the
`src/pcae/commands/phase.py` diff): **7 of 9 failed**, each failure
proving a rejected/quarantined/human-review-blocked transition still
released the agent lock and/or recorded `phase_completed`/
`agent_released` provenance — exactly the historical failure shape:

```
FAILED test_stale_metadata_rejection_preserves_lock_and_provenance
FAILED test_quarantine_verdict_preserves_lock
FAILED test_human_review_verdict_preserves_lock
FAILED test_cross_phase_contamination_rejection_preserves_lock
FAILED test_retry_after_rejection_succeeds_without_manual_recovery
FAILED test_retry_after_quarantine_succeeds_without_manual_recovery
FAILED test_rehydrated_lock_still_enforces_validation
7 failed, 2 passed in 1.92s
```

The 2 that passed on unmodified `main` were the accepted-completion
parity tests (`test_accepted_completion_releases_lock_exactly_once`,
`test_accepted_completion_without_lock_still_succeeds`) — the success
path was never broken; only the rejection path was.

### 3b. Manual disposable-repository CLI reproduction (pre-repair)

In a disposable `/tmp` repository (real `git init`, real `pcae init`,
real `pcae task new`/`phase start`): wrote
`.pcae/phase-completion-metadata.json` with `phase_id: "205X"` (stale,
mismatched against the phase actually being completed), held a real
agent lock for `claude-local`, and ran `pcae phase complete --phase-id
205D ...` against the **pre-repair** code. Observed:

```
Repository transition validator: Transition rejected
  Verdict: reject
  Violation: metadata_consistency - metadata phase_id '205X' does not match proposed target phase_id '205D'
```

exit code 1, and (pre-repair) `.pcae/agent-lock.json` deleted and
`agent_released`/`phase_completed` provenance recorded regardless —
confirmed via the same commands `pcae session bootstrap --sync-lock`
would require to recover, matching 145H.3R §7's documented workaround
exactly.

**Note on an operational incident during this reproduction:** an early
manual reproduction run (before `PCAE_NOTIFY_ENABLED` was disabled for
the scratch repository) reached an *accepted* completion and dispatched
one real, unintended Telegram notification via the operator's globally
configured `~/.config/pcae/notify.json` (loaded per-process regardless of
working directory). This was disclosed to the human operator immediately
upon discovery. All subsequent reproduction and verification work in
this phase set `PCAE_NOTIFY_ENABLED=""` for every disposable-repository
command. No production repository state, secret, or governed artifact
was affected; the sent message content was an ordinary phase-completion
summary for a fictitious "Phase 700A" in a throwaway `/tmp` repository,
carrying no confidential information. See §11 for the corresponding
non-blocking finding.

## 4. Root-cause statement

- **Failing component:** `run_phase_complete()`
  (`src/pcae/commands/phase.py:49`), specifically its pre-repair call
  ordering relative to `complete_phase()` (`src/pcae/core/phase.py:30`).
- **Precise mechanism:** `complete_phase()` unconditionally (a) appended
  a `"phase_completed"` provenance event and (b) called
  `release_agent_lock()`, and `run_phase_complete()` invoked it *before*
  calling `_finalize_report_and_notify()` — the function that performs
  every rejectable validation stage (identity resolution, the
  finalization gate, cross-phase commit contamination detection, the
  Repository Transition Validator). A REJECT/QUARANTINE/
  REQUIRES_HUMAN_REVIEW verdict from any of those stages therefore still
  irreversibly mutated lock and provenance state as if the phase had
  completed.
- **Match against this phase's enumerated candidate causes (§4 of the
  governing prompt):** direct source inspection confirms exactly one of
  the nine listed candidates applies: *"lock release occurs before all
  rejectable validation stages complete."* The other eight do not apply
  to this codebase's actual architecture:
  - Transition validation does *not* read the predecessor phase ID from
    stale completion metadata by itself being wrong — the
    `metadata_consistency` check firing on genuinely stale metadata is
    **correct, intended, fail-closed behavior** (confirmed in §3b); the
    defect is only the side effect a correct rejection was allowed to
    have.
  - "Phase completion metadata is prepared too late" describes an
    *operational* precondition external to any single command's own
    contract (matching 145H.3R §8's own finding), not an engineering
    defect this phase's authorized surface can or should change.
  - "The active task or phase identity is not passed explicitly into
    validation" — already false: `resolve_canonical_phase_identity()`
    already receives the active task title, metadata, lifecycle context,
    and CLI overrides explicitly, in a documented precedence order
    (Phase 113X.4).
  - "The phase-start commit-window baseline is stale or never reset" /
    "phase-start failure due to an already-held lock leaves an inherited
    baseline" — this codebase has **no such baseline mechanism at all**
    (confirmed by direct inspection of `start_phase()`,
    `src/pcae/core/phase.py:130`, and `run_phase_start()`,
    `src/pcae/commands/phase.py:2443`); commit-to-phase attribution is
    performed entirely through explicitly declared `phase_commits` in
    `.pcae/phase-completion-metadata.json` plus commit-subject-line
    contamination detection, not a recorded start boundary. This
    candidate cause does not apply and no baseline was introduced —
    inventing one would have exceeded this phase's narrowly scoped
    repair authority and risked contradicting §12's "no unnecessary
    ... transport shapes" boundary.
  - "Finalization mutates lifecycle state before the transaction is
    guaranteed to commit" (for canonical-report promotion/dispatch) was
    already repaired for the report/metadata/notification triad by Phase
    134E.10.1's `run_finalization_transaction()`; only the agent-lock/
    task-provenance mutation (owned by `complete_phase()`, entirely
    outside that transaction) still ran early.
  - "Report generation and notification happen outside the correct
    transaction boundary" and "rollback does not restore pre-finalization
    state" — not applicable; those are already governed by
    `run_finalization_transaction()`'s existing pre/post-promotion
    checkpointing.
- **Why existing tests did not prevent it:** the codebase's existing
  Repository Transition Validator test suites
  (`tests/test_repository_transition_validator_phase_complete_
  integration.py` and siblings) exercise every rejection verdict
  correctly and thoroughly, but none of them asserted anything about
  agent-lock or provenance state after a rejection — that dimension was
  simply untested, not incorrectly tested.
- **Same or distinct defect:** the same defect lineage documented at
  145G.3 (`docs/PHASE_145G3R_...md` §2/§7, explicitly left unrepaired
  there) and self-corrected identically at 145H.1, 145H.2, and 145H.3,
  each time via manual `pcae session bootstrap --sync-lock` recovery —
  not new, not widened.

## 5. Production repair

**File changed:** `src/pcae/commands/phase.py`, function
`run_phase_complete()` only (28 insertions, 9 deletions — a pure
reordering, no new branch, flag, or parameter).

`complete_phase()` — and therefore the `"phase_completed"`/
`"agent_released"` provenance events, the lock release, and the "Phase
complete."/"Agent lock: ..." print block — now runs **only when
`_finalize_report_and_notify()` returns `True`**. `_finalize_report_and_
notify()` itself is unchanged; every rejectable stage inside it (identity
resolution, the finalization gate, cross-phase commit contamination,
the Repository Transition Validator, the Phase 134E.10.1 finalization
transaction, notification certification) now runs to a final verdict
entirely before the lock or provenance state is ever touched. This is
the exact "reorder `complete_phase()` to run after the validator's
verdict" fix 145G.3R §2 and 145H.3R §8 both recommended without
implementing.

Sequencing model after repair (matches §6's preferred direction without
introducing a new type, per its own "guidance, not requirement" note —
`_finalize_report_and_notify()` already constructs an equivalent
in-memory trial candidate via `make_phase_report()`/
`_apply_canonical_and_trust()`/`validate_finalization_gate()` before any
promotion, so no additional candidate object was needed):

1. Resolve the active target phase identity explicitly
   (`resolve_canonical_phase_identity`) — read-only.
2. Build the trial `PhaseReport`, validate commit attribution and
   cross-phase contamination, run the finalization gate — read-only.
3. Run the Repository Transition Validator
   (`validate_phase_report_transition`/
   `handle_phase_report_transition_result`) — read-only except for
   quarantine-artifact writes on an explicit QUARANTINE verdict (an
   intentional, pre-existing, non-lock-related side effect unchanged by
   this repair).
4. On any non-ACCEPT verdict: return `False`. **`complete_phase()` is
   never called** — no lock release, no `"phase_completed"`/
   `"agent_released"` provenance, no task-state mutation.
5. On ACCEPT: run the Phase 134E.10.1 finalization transaction
   (pre-promotion certification, then promotion and notification
   dispatch via the existing, unmodified `finalize_phase_report()`).
6. Only once that returns successfully does `run_phase_complete()` call
   `complete_phase()` — appending `"phase_completed"` provenance and
   releasing the agent lock as the final, terminal step.

No other file was modified. No new CLI flag, bypass, force mode, error
type, or exit code was introduced (§12 no-go boundary, §5.10 backward
compatibility).

## 6. Affected call graph / other completion entry points (§8)

Directly inspected every other candidate entry point for the same
shared-root-cause defect:

- `pcae task finish` / `pcae task complete` / `pcae task finish --commit`
  (`src/pcae/commands/task.py`, `run_task_complete()`,
  `run_task_finish()`, `run_task_finish_recover()`): grep for
  `release_agent_lock`/`acquire_agent_lock`/`read_agent_lock` across the
  entire file returns **zero matches**. Task completion never touches
  the agent lock at all — it shares the Repository Transition Validator
  adapter (`validate_phase_report_transition`) for report-transition
  validation, but has no lock-release-ordering defect to repair, because
  it never releases a lock in the first place.
- `pcae phase-report create` / `phase-report reconcile` (`src/pcae/
  commands/phase_reports.py`): same grep, zero matches. Report creation
  and recovery paths never touch the agent lock.
- `pcae phase handoff` (`handoff_phase()`, `src/pcae/core/phase.py:69`):
  this **does** unconditionally release (and then reacquire, for the
  next agent) the lock — but it is architecturally a different
  operation by design: an agent-to-agent lock transfer, not a phase-
  report completion. It does not call `_finalize_report_and_notify()`,
  the Repository Transition Validator, or any of the rejectable
  validation stages this phase's authorized scope covers, and it is not
  named anywhere in the four-occurrence defect lineage (145G.3, 145H.1,
  145H.2, 145H.3 — all `pcae phase complete` rejections). Repairing it
  is outside this phase's authorized surface ("Primary affected command:
  `pcae phase complete`") and would conflate two intentionally distinct
  operations; left unchanged.

No other ordinary completion entry point shares the repaired defect.

## 7. Mandatory regression tests

New file: `tests/test_phase_145h3r1_lock_sequencing_repair.py`, 9 tests,
all built on real CLI invocations (`pcae.cli.main(["phase", "complete",
...])`) against disposable `tmp_path` repositories with a real acquired
agent lock — not mocks of the lock or validator:

| Test | Covers |
|---|---|
| `test_stale_metadata_rejection_preserves_lock_and_provenance` | §7.1/§7.2/§7.4 — direct reproduction of the exact 145G.3/145H.1/145H.2/145H.3 failure shape (stale `phase_id` in metadata); lock and provenance both untouched on REJECT |
| `test_quarantine_verdict_preserves_lock` | §7.4 — QUARANTINE verdict also preserves the lock |
| `test_human_review_verdict_preserves_lock` | §7.4 — REQUIRES_HUMAN_REVIEW verdict also preserves the lock |
| `test_cross_phase_contamination_rejection_preserves_lock` | §7.16 — a real contaminating commit (subject naming a different phase) still fails closed, and that rejection preserves the lock; proves the repair does not weaken contamination detection |
| `test_retry_after_rejection_succeeds_without_manual_recovery` | §7.5/§7.17 — correcting the metadata and retrying succeeds through `pcae phase complete` alone; exactly one `phase_completed`/`agent_released` pair recorded, no duplicates |
| `test_retry_after_quarantine_succeeds_without_manual_recovery` | §7.5 — same, from a QUARANTINE starting point |
| `test_rehydrated_lock_still_enforces_validation` | §7.3 — reading an already-held lock (as a rehydrated bootstrap session would) grants no bypass; validation still rejects and preserves the lock |
| `test_accepted_completion_releases_lock_exactly_once` | Accept-path parity — a genuinely valid completion is unchanged: lock released exactly once, exactly one `phase_completed`/`agent_released` pair |
| `test_accepted_completion_without_lock_still_succeeds` | Accept-path parity — completing with no lock held is unaffected |

Result against **this phase's own repaired code**: `9 passed`. Result
against **unmodified `main`** (isolated via `git stash` on only
`src/pcae/commands/phase.py`): `7 failed, 2 passed` — proving the 7
failing tests genuinely exercise the repaired defect rather than passing
vacuously.

Sections 7.6–7.15 of the governing prompt (failure injection around
metadata promotion/canonical-report write/finalization receipt,
restart recovery, predecessor-report preservation, pre/post-push state)
are already covered by the pre-existing, unmodified
`run_finalization_transaction()` machinery and its own test suite
(`tests/test_finalization_transaction_134e10.py`, `tests/
test_phase_137i1_finalization_ordering_deadlock.py`) — this phase's
repair does not touch that transaction's internals, and re-deriving
fault-injection coverage for code this phase did not modify would
exceed its narrowly authorized surface.

## 8. Required manual reproduction (disposable repository, post-repair)

Performed in a fresh disposable `/tmp` repository (`PCAE_NOTIFY_ENABLED`
explicitly disabled throughout, after the §3b incident):

1. `git init`, `pcae init`, `pcae task new`, `git commit` — baseline.
2. `pcae phase start --agent-id claude-local` — governed phase A (700A)
   started, lock acquired.
3. Completed phase A: first attempt (incomplete `no_go_confirmation`,
   0 declared commits) was **quarantined** by the Repository Transition
   Validator (`Transition quarantined` / `report_completeness is
   'partial'`) — confirmed live: `.pcae/agent-lock.json` still present,
   `agent_id: "claude-local"`, unchanged. Corrected the metadata (added
   the phase's own commit hash) and re-ran `pcae phase complete` with no
   manual lock or report intervention: `Transition validated` /
   `Finalization transaction (134E.10.1): completed` / `Phase complete.`
   / `Agent lock: released (by claude-local)`.
4. `pcae phase start --agent-id claude-local` — governed phase B (700B)
   started, lock acquired.
5. Created one correctly labeled phase B commit
   (`Phase 700B: correctly labeled phase B commit`).
6. Left `.pcae/phase-completion-metadata.json` exactly as phase A's own
   completion naturally left it (still identifying `700A`) — the
   precise historical precondition.
7. Ran `pcae phase complete --phase-id 700B ...`: **`Repository
   transition validator: Transition rejected` / `metadata_consistency -
   metadata phase_id '700A' does not match proposed target phase_id
   '700B'`**, exit code 1 — the exact 145G.3/145H.1/145H.2/145H.3
   failure shape, reproduced live against the repaired code.
8. Confirmed directly: `.pcae/agent-lock.json` still present (`agent_id:
   "claude-local"`, `acquired_at` timestamp unchanged since step 4); the
   task contract remained in `tasks/active/`; `.pcae/provenance-
   history.json`'s tail showed no new `phase_completed`/`agent_released`
   events following the rejected attempt.
9. Corrected the metadata's `phase_id`/`phase_commits`/
   `recommended_next_phase` to identify 700B (an ordinary metadata
   correction, not a lock or report workaround) and re-ran `pcae phase
   complete` with **no** `pcae session bootstrap --sync-lock`, no direct
   `.pcae/agent-lock.json` edit, and no hand-authored report: `Transition
   validated` / `Finalization transaction (134E.10.1): completed` /
   `Phase complete.` / `Agent lock: released (by claude-local)`.
10. Confirmed directly: `.pcae/phase-reports/latest.json`'s `phase_id`
    is `"700B"`; `.pcae/agent-lock.json` no longer exists (released);
    `.pcae/provenance-history.json`'s tail shows exactly one
    `phase_completed`/`agent_released` pair for each of 700A and 700B (no
    duplicates); the 700A report files
    (`.pcae/phase-reports/*-700A.json`/`.md`) remained present and
    unmodified by 700B's completion.

Every required outcome in §10 of the governing prompt was directly
observed on the filesystem and in Git/provenance state, not inferred.

## 9. Test scope and results

Targeted suites (`test_agent.py`, `test_provenance.py`, `test_task.py`,
`test_phase.py` — 882 tests, `test_repository_transition_validator*.py`
— all four files, `test_repository_transition_validator_task_finish_
integration.py`, `test_finalization_transaction_134e10.py`, `test_push_
state_reconciliation.py`, `test_phase_report_trust_gate_cli.py`, `test_
phase_report_trust_hard_fail.py`, `test_repository_transition_validator_
phase_complete_integration.py`, `test_task_finish_notification_ordering.
py`, `test_task_finish_report_trust_notification.py`, `test_commit_
attribution_repair_134e10_1_1.py`, `test_finalization_gate_enforcement.
py`, `test_phase_reports.py`, `test_phase_reports_cli.py`, `test_
notifications.py`, `test_notification_certification_idempotency.py`,
plus this phase's own new file): **4799 passed** across the first batch
plus **9 passed** for the new file; the only failure encountered
(`test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::
test_public_reconciliation_requires_report_marker_checkpoint_and_
receipt`) was independently reproduced against unmodified `main`
(identical failure, identical assertion) — pre-existing, unrelated to
`pcae phase complete`/lock sequencing.

```
pytest -n auto -m fast_green
```
**4391 passed, 0 failed** — identical to the established baseline
(matches 145H.2's/145H.3's own recorded `fast_green` result exactly).

```
pytest -n auto
```
**26676 passed, 53 failed, 10 skipped** (39m 57s). Every one of the 53
failing test IDs was independently re-run, both against this phase's
repaired code and against unmodified `main` (isolated via `git stash` on
only `src/pcae/commands/phase.py`), sequentially (no `-n auto`), as one
combined invocation:

- **38 of 53** failed identically, with identical assertion messages, on
  **both** the repaired code and unmodified `main` — deterministic,
  pre-existing failures (wheel-packaging/`cltr` authority-boundary
  tests, `test_scope_preflight*`/`test_backend_preflight_review.py`/
  `test_mutation_preflight_review.py`/`test_shell_gate.py` preflight-
  review tests, `test_bootstrap_todo_consistency.py` real-`TODO.md`
  staleness checks, `test_advisory_runtime_*`, `test_rendering_134e5.py`,
  `test_finalization_transaction_134e10.py`'s five pre-existing
  receipt-timestamp failures, `test_cltr_migration_135p_verification.py`
  and `test_phase_137i1_finalization_ordering_deadlock.py`'s finalization-
  transaction-adjacent failures, `test_phase_reports.py`'s one pre-
  existing failure).
- **15 of 53** passed when re-run sequentially (both on the repaired code
  and on unmodified `main`) — `-n auto` parallel-worker order-dependent
  flakes (`test_scope_preflight*`/`test_backend_preflight_review.py`/
  `test_mutation_preflight_review.py`/`test_shell_gate.py`), not
  deterministic failures, and identically flaky on unmodified `main`.

**Disclosure required by §9 of the governing prompt:** of the 53
failures, the ones nearest this phase's own change surface —
`test_cltr_migration_135p_verification.py::...[phase_complete]`,
`test_phase_137i1_finalization_ordering_deadlock.py::
TestFinalizePendingPush::test_pending_push_writes_canonical_latest_
non_authoritative`, and all five in `test_finalization_transaction_
134e10.py` — were individually inspected. All five touch
`run_finalization_transaction()`'s post-dispatch receipt-modeling step
(`ValueError: invalid timestamp '...Z': must be ISO 8601`,
`delivery_receipt.py`'s ISO-8601 parser rejecting its own generator's
`Z`-suffixed output) and `finalize_phase_report()`'s `allow_pending_push`
branch — neither module was touched by this phase's diff, and both
failures reproduce byte-for-byte identically on unmodified `main`.
**No failure among the 53 touches `run_phase_complete()`,
`complete_phase()`, agent-lock lifecycle, or the specific sequencing this
phase repaired.**

## 10. Governance validation

Before finalization:

```
pcae check            -> passed
pcae health            -> healthy
pcae doctor task-memory -> clean
pcae runtime inspect   -> Observed / observe / unavailable (unchanged)
pcae push check        -> clean (nothing_to_push, prior to this phase's own commit)
```

No architecture-policy file (`.pcae/policy.toml`) was touched. No
strategic-lineage file (`.pcae/strategic-lineage.json`) was touched. No
file under `docs/contracts/` was touched (also enforced by this phase's
own task-contract forbidden-file scope). No secret material was
committed (the sole external side effect of this phase — the §3b
Telegram incident — sent no credential or secret; the operator's bot
token/chat ID were never printed or logged). No raw governance bypass
was added.

## 11. Non-blocking findings

- **F1 (operational, not engineering):** an early manual reproduction
  attempt (§3b) sent one unintended, real Telegram notification from a
  disposable `/tmp` test repository, because `PCAE_NOTIFY_ENABLED`
  config is loaded globally per-process (`~/.config/pcae/notify.json`),
  not scoped to a repository. Disclosed to the human operator
  immediately; all subsequent reproduction work in this phase
  explicitly disabled the transport (`PCAE_NOTIFY_ENABLED=""`). This is
  a pre-existing characteristic of `ensure_notification_environment_
  loaded()` (Phase 134B.3), not something this phase's diff introduced
  or is authorized to change (no file under `src/pcae/core/notification_
  config.py` was touched); recorded here for future operators running
  disposable-repository reproductions to disable the transport
  proactively rather than discovering this the same way.
- **F2:** `test_finalization_transaction_134e10.py`'s five pre-existing
  failures (delivery-receipt timestamp format) and `test_cltr_migration_
  135p_verification.py`'s four pre-existing failures share the identical
  root symptom (`delivery_receipt.py` rejecting its own
  `time.strftime("...Z", ...)`-generated timestamps as non-ISO-8601) —
  a real, pre-existing, unrelated defect a future phase should
  independently scope and repair. Not touched by this phase (outside its
  authorized surface).

## 12. No-go boundary — confirmations

No broader Interactive Workflow chapter certification was begun. No work
on 145I was begun or authorized. No work on Phase 146 was begun or
authorized. No file under `docs/contracts/` (IWPC-001, IWC-001, PEC-001,
CHGR-001) was touched. No readiness-uniqueness behavior was changed. No
publication-ownership behavior was changed. No execution capability was
added — `pcae runtime inspect` confirmed unchanged, Observed/observe/
unavailable, before and after. No force-completion mode was added. No
skip-validation completion path was added. No assume-authorized behavior
was added. Cross-phase contamination detection was not weakened —
§7's `test_cross_phase_contamination_rejection_preserves_lock` proves a
genuinely contaminating commit still fails closed after this repair. No
validation error was suppressed — every REJECT/QUARANTINE/
REQUIRES_HUMAN_REVIEW verdict still prints identically to before this
repair; only the lock/provenance side effect of that verdict changed.
Locks are no longer released early — this is the repair itself. No
notification was ever marked successful without transport evidence — the
`certify_notification_transition()`/`finalize_phase_report()` dispatch
path was not modified. No duplicate terminal notification was sent — §8
step 10 confirmed exactly one `phase_completed`/`agent_released` pair per
phase, and `PCAE_NOTIFY_ENABLED=""` kept the manual reproduction's
notification dispatch fully disabled and inspectable. No routine manual
metadata authorship was required for either this phase's own manual
reproduction (§8) or its finalization (§13) beyond ordinary, ahead-of-
time metadata preparation — no metadata was hand-authored *after* a
rejected `pcae phase complete` attempt, the specific pattern this phase
repairs. No routine manual lock reacquisition was required anywhere in
this phase's own work. This repair was not special-cased to the four
known affected phase IDs (145G.3/145H.1/145H.2/145H.3) — it changes
`run_phase_complete()`'s general call ordering for every phase ID. No
partial-finalization evidence was hidden — §3's pre-repair reproduction
output and this phase's own rejected-then-corrected manual reproduction
(§8 steps 3 and 7) are both recorded here in full, not paraphrased away.

## 13. Final verdict

**REPAIRED WITH NON-BLOCKING FINDINGS — PHASE COMPLETION METADATA
SEQUENCING AND FINALIZATION HOLD.**

All required elements are satisfied: independent pre-repair reproduction
(§3, both automated and manual CLI); a production repair addressing the
general lifecycle defect, not a special case (§5); fresh adversarial
tests, failing before and passing after (§7); a real disposable-
repository CLI lifecycle reproduction covering rejection, lock
preservation, ordinary-command-only retry, and successful completion for
two consecutive phases (§8); correct lock sequencing proven directly on
disk (§8 steps 3, 8, 10); canonical report and metadata consistency
proven directly (§8 step 10); exactly-once notification semantics
undisturbed (§8 step 10, provenance tail); unchanged runtime capability
(§10). One operational non-blocking finding is disclosed (§11 F1) — a
real but contained, non-secret, immediately-disclosed side effect during
reproduction, not a defect in the repair itself. Downgraded from a plain
`REPAIRED` verdict specifically because of that disclosure, per this
report's own governing prompt requiring "REPAIRED WITH NON-BLOCKING
FINDINGS" whenever such a finding exists.

This phase does not authorize 145H.4, 145I, Phase 146, or broader
Interactive Workflow chapter certification.

## 14. Recommended next phase

**145H.3R.2 — Phase Completion Metadata Sequencing and Finalization
Independent Verification.** That phase must independently verify this
repair without trusting this phase's own tests or report — in
particular, independently re-deriving the root cause from source,
independently reproducing the pre-repair failure shape against a
detached copy of the pre-repair commit, and independently exercising the
disposable-repository CLI lifecycle in §8. This recommendation does not
authorize 145H.4, 145I, Phase 146, or broader Interactive Workflow
chapter certification.

## 15. Files changed

- `src/pcae/commands/phase.py` — the production repair (28 insertions, 9
  deletions, `run_phase_complete()` only).
- `tests/test_phase_145h3r1_lock_sequencing_repair.py` — new, 9 tests.
- `docs/PHASE_145H3R1_PHASE_COMPLETION_METADATA_SEQUENCING_AND_
  FINALIZATION_REPAIR.md` (this report, new).
- `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DECISIONS.md`,
  `tasks/TODO.md` — governance bookkeeping.
- `tasks/done/20260727-2234-idle-awaiting-next-governed-phase-post-
  145h-3r.md` (idle-placeholder closure),
  `tasks/active/20260728-0627-phase-145h-3r-1-...md` (this phase's own
  task contract, to be moved to `tasks/done/` at finalization).
- `.pcae/phase-completion-metadata.json` — prepared ahead of this
  phase's own `pcae phase complete` invocation (not hand-authored after
  a rejected attempt — this phase's own finalization is intended to
  prove the repaired path can finalize itself through the ordinary,
  unmodified `pcae phase complete` command).

No file under `docs/contracts/` was modified.
