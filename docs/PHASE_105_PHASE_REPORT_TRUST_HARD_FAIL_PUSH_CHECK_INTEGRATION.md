# Phase 105D — Phase Report Trust Gate Hard-Fail / Push-Check Integration

## Purpose

Move PCAE from warning-only report-trust validation (105B, 105C, 105C.1) to
a controlled hard-fail gate: incomplete, partial, push-pending, or
placeholder-containing phase reports can no longer be treated as a final,
release-ready completion by `pcae phase complete`, and cannot pass
`pcae push check`'s content-completeness gate.

## Scope

- Hard-fail `pcae phase complete` by default when report trust is
  incomplete/invalid (both the OLD 95M.1 schema and the 105A/105B schema),
  with an explicit, logged `--allow-partial-report` opt-out.
- Add a phase-report-trust gate to `pcae push check` (content completeness
  only — see "push-check integration decision" below for why).
- Keep `pcae task finish --commit` exactly as 105C.1 left it: warning-only
  for push-state fields, since it legitimately runs before every push.
- Promote the 105C.1 push-state gate (`_apply_push_state_gate`,
  `_PUSH_STATE_FIELDS`) from `commands/task.py` to `core/phase_report_trust.py`
  (`apply_push_state_gate`, `PUSH_STATE_FIELDS`, `compute_final_trust`) so
  `commands/push.py` can reuse it without duplicating logic; `commands/task.py`
  keeps its old private names as thin aliases for backward compatibility.

## Non-goals

105D does not implement runtime enforcement, autonomous execution, backend
invocation, adapter execution, shell mediation, Telegram inbound/polling,
rollback execution, or apply/commit/push authorization beyond what already
governs these lifecycle commands. It does not add an execution enablement
flag or toggle. Telegram remains outbound-only. All authorization flags
remain False; `simulation_only`, `no_execution`, `evidence_only`,
`non_authorizing`, and `design_only` remain True where applicable.

## Relationship to 105A / 105B / 105C / 105C.1

- **105A** (`core/phase_report_trust.py`): `validate_phase_report_trust()` /
  `select_active_phase_report()` — unchanged in behavior; extended with
  `apply_push_state_gate()` and `compute_final_trust()`.
- **105B**: `pcae phase-report trust`, `show --trust`, and the "Trust gate
  (105B, advisory)" line in `pcae phase complete` — the CLI commands are
  unchanged; the advisory line in `phase complete` is replaced by the new
  hard-fail "Trust gate (105D)" line (same underlying validator, now
  authoritative for the command's exit code).
- **105C**: `_finalize_task_report_and_notify()` in `commands/task.py` —
  unchanged in structure; its push-state gate helpers are now thin
  wrappers around the promoted core functions.
- **105C.1**: `_apply_push_state_gate()` — promoted to
  `core/phase_report_trust.py` as `apply_push_state_gate()`, reused by both
  `commands/task.py` (dispatch decision) and `commands/phase.py` (hard-fail
  decision). `commands/push.py` deliberately does **not** reuse the
  push-state fold — see below.

## Current lifecycle flow (after 105D)

```
pcae commit implementation --path ... --message "..."
pcae task finish --staged-file-aware --commit "..."
    → finalizes report, trust-validates (105A/105B + push-state fold),
      warning-only: writes report regardless, suppresses Telegram if
      incomplete (unchanged from 105C.1)
pcae push check
    → NEW: fails if the latest phase report is CONTENT-incomplete
      (missing fields / placeholders), regardless of push-state fields
pcae push
```

```
pcae phase complete --summary "..."
    → NEW: hard-fails (exit 1) by default if report trust is
      incomplete/invalid (95M.1 gate OR 105A/105B+push-state gate);
      --allow-partial-report overrides the exit code only — Telegram
      dispatch is still suppressed for incomplete reports either way
```

## Hard-fail placement decision

Two commands could plausibly hard-fail: `pcae phase complete` and `pcae
push check`. `pcae task finish --commit` deliberately does **not**, because
of a structural constraint explained below.

### `pcae phase complete`: hard-fail by default

`phase complete` is the "final completion" command — it releases the agent
lock, records `phase_completed` provenance, and (per 105C's docs) remains
available as a manual/ad hoc finalization path. It is not part of the
mandatory, must-run-before-every-push sequence the way `task finish` is, so
requiring full trust (including push-state) here does not create a
deadlock: a user can run it after pushing, or explicitly opt out with
`--allow-partial-report` if they need to run it early.

Implementation: `_finalize_report_and_notify()` now builds a no-I/O trial
report (via `make_phase_report()` + `_apply_canonical_and_trust()` — the
same helper `finalize_phase_report()` uses internally) to compute both the
95M.1 gate and the 105A/105B+push-state trust result *before* calling
`finalize_phase_report()` for real. This lets it decide, in one place,
whether to suppress dispatch and what exit code to return, without
duplicating `finalize_phase_report()`'s write/dispatch logic.

`run_phase_complete()` previously always `return 0`; it now returns
`0 if finalizable else 1`, where `finalizable = (gate["finalizable"] and
trust_result.complete) or allow_partial_report`.

### `pcae push check`: content-completeness gate only

`push check` gains a new `phase_report_trust` field: `passed` / `failed` /
`skipped`. **Deliberately, this does not apply the 105C.1 push-state
fold.** Reasoning: `pushed_status`/`origin_main_head`/`pcae_push_check`
inside the *stored* report are, by construction, always going to read
"pending"/"not_pushed" at the exact moment `pcae task finish --commit`
just wrote them — that is the normal, expected pre-push state, and
`push check` runs precisely to gate the push that would resolve it. If
`push check`'s phase-report-trust gate required those fields to already
say "pushed", `push check` (and therefore `pcae push`, which uses the same
`assess_push_readiness()`) would be permanently unpassable for every phase
that uses the task-finish integration — a hard deadlock, not a safety
improvement. `push check` already has its own live, authoritative
push-state signals (`unpushed` commit count, working-tree `clean` flag) —
it does not need the report's stale snapshot of the same thing.

What `push check`'s gate *does* still catch: missing `files_changed`,
`tests_run`, `commits`, governance/test result keys, and disallowed
placeholders (`TBD`, `pending`, `not captured`, `unknown`) anywhere in the
latest report — i.e. genuinely broken or rushed metadata, independent of
push timing.

### `pcae task finish --commit`: unchanged, warning-only

Per 105C.1, and preserved here exactly: task finish still finalizes and
trust-validates the report (105A/105B + push-state fold, as before), still
writes the report regardless of trust outcome (visible, not hidden), and
still suppresses Telegram (`skipped_incomplete`) when the report is
incomplete for any reason, including pending push state. It does not
hard-fail the command itself. This is the correct behavior for the moment
it legitimately runs in — before the actual push — and 105D does not
change it.

## Telegram outbound behavior

Unchanged principle from 105C.1, now enforced in one more place: a partial
report is never dispatched as a final trusted handoff, from either command.
In `phase complete`, dispatch suppression is keyed off the same trust
result used for the exit code (`gate["finalizable"] and trust_result.complete`)
— note this is checked *regardless* of `--allow-partial-report`, so passing
that flag lets the *command* proceed but still never sends a partial
report via Telegram. In `task finish`, nothing changed: 105C.1's suppression
logic is reused as-is.

## Repair guidance

Both hard-fail paths print the same shape of guidance: `Trust gate (105D):
<status>`, missing/placeholder fields, `Repair required: yes/no`, `Can be
active/latest: yes/no`, and (for `phase complete`) an explicit refusal
message pointing at `--allow-partial-report` as the (discouraged) override.
`push check` prints `Phase report trust: failed` with the same
missing/placeholder fields and repair-required flag, plus an entry in the
"Not ready to push" reason list.

## Residual risks

1. `pcae phase complete` and `pcae task finish --commit` can now disagree
   about whether "the same underlying report data" is dispatch-ready:
   `phase complete` requires full push-state completeness (since it's not
   structurally pre-push), `task finish` does not (since it structurally
   is). This is intentional, not a bug, but is a real asymmetry worth
   remembering when debugging a "why didn't this send" question.
2. `push check`'s phase-report-trust gate only looks at
   `.pcae/phase-reports/latest.json` (the single latest report record),
   not history — a stale-but-old-complete report sitting as "latest" from
   an unrelated earlier phase would pass the gate even though it doesn't
   describe the current change set. Cross-checking phase identity against
   the active/recent task is not implemented here; flagged for a future
   phase if it proves to be a real problem in practice.
3. `--allow-partial-report` is a blunt, whole-report override (skip content
   AND push-state completeness both at once) — there is no finer-grained
   "allow this specific missing field" option. Given 105D's brief asked
   for a single opt-out flag, this is intentionally simple; a more
   granular override was judged to be overbuilding for this phase.

## Recommended next phase

106A — v0.1 Release Scope Freeze. Report trust is now visible (105A/105B),
task-finish-integrated (105C), notification-order-safe (105C.1), and
hard-fail/push-check-gated (105D) — PCAE can move from lifecycle hardening
to freezing v0.1 release scope.
