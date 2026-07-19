# Phase 137F.1 — Canonical Report Finalization Recovery and Push-Semantics Repair

## Incident identity

**Phase:** 137F.1
**Trigger:** after Phase 137F's substantive verification work was committed
and pushed, the canonical Phase 137F report was found absent, session/report
state continued to expose Phase 137E as latest, no canonical-report
notification was sent, and `pcae push` (invoked expecting a readiness check)
performed a real push to `origin/main`.
**Scope:** bounded lifecycle-integrity repair. Phase 137G is not begun. The
Phase 137F verification verdict (VERIFIED, no Blocking finding, two
Non-Blocking observations) is not altered — no evidence surfaced in this
investigation contradicts it.

## 1. Reconstructed finalization path

The exact command sequence run during Phase 137F's closure, reconstructed
directly from this session's own transcript and confirmed against `git log`
and `.pcae/` state (not from narrative memory):

1. `pcae task complete` — closes the active task contract and moves it to
   `tasks/done/`. **This is not `pcae task finish`.** `pcae task complete`
   takes no options and performs no validation, no memory-file
   synchronization beyond the move, and — critically — no read or write of
   `.pcae/phase-completion-metadata.json`.
2. Manual edits to `PROJECT_STATUS.md`, `tasks/TODO.md`, `tasks/DONE.md`,
   `tasks/DECISIONS.md`, `CHANGELOG.md`, and the new verification report.
3. `pcae commit implementation` (twice) — a staged-file-aware governed
   commit. Neither invocation reads or requires a canonical phase report.
4. `pcae push` (bare, no `check` subcommand) — executed a real `git push`
   because `assess_push_readiness()` returned `ready=True` (mode
   `active_task`, since an idle placeholder task was open, working tree was
   clean, and two local commits existed unpushed).

At no point in this sequence was `pcae phase-report create`, `pcae phase
complete`, or `pcae task finish` invoked. Those are the only commands in
this codebase that write `.pcae/phase-reports/latest.json` or
`.pcae/phase-completion-metadata.json` for a newly completed phase (verified
by `grep` across `src/pcae/commands/` and `src/pcae/core/`).

## 2. Root cause: two independent, compounding gaps

### 2a. Operator sequencing (contributing, not sole cause)

`pcae task complete` and `pcae task finish` are both valid task-closure
commands with materially different scope: `task finish` is documented as
"Finish the active task with validation, memory updates, and session
refresh" and is the command that reads/reconciles
`.pcae/phase-completion-metadata.json` (confirmed at
`src/pcae/commands/task.py:583,612,617`). `task complete` is a bare
task-file relocation. Using `task complete` instead of `task finish` (or,
further, `pcae phase complete`) is what actually skipped canonical-report
generation in this instance.

### 2b. Gate defect (the demonstrated, reproducible root cause)

Independent of which closure command was used, **nothing in the commit or
push path verifies that a canonical report exists for the phase that was
just completed.** Specifically, `_assess_phase_report_trust()` in
`src/pcae/commands/push.py` (used by both `pcae check`'s conceptual
neighbor and, more importantly, `assess_push_readiness()`) only validates
the **schema completeness** of whatever `.pcae/phase-reports/latest.json`
currently contains — via `validate_phase_report_trust()` /
`compute_final_trust()` in `src/pcae/core/phase_report_trust.py`. It never
compares the report's own `phase_id` field against the phase identity of
the most recently completed task. Because the stale 137E report was
itself schema-complete, `phase_report_trust_status` read `"passed"`, and
push readiness proceeded.

This is a **reproducible defect**, not merely an operator mistake: any
sequence of governed commands that completes phase N without invoking
`phase complete`/`task finish`, then commits and pushes, reaches this exact
state. Reproduced directly in
`tests/test_push_phase_report_identity_137f1.py::test_137f1_missing_canonical_report_blocks_push_after_idle_closure`
and `::test_137f1_stale_prior_phase_report_blocks_push` (both failed against
the pre-137F.1 code, in that push readiness reported `ready` despite the
stale/missing report — see §5 for the fix and §7 for post-fix results).

## 3. Why 136AX/136AY did not catch this

`docs/PHASE_136AY_LIFECYCLE_BOOTSTRAP_SESSION_STATE_REPORTING_INDEPENDENT_VERIFICATION.md`
independently verified phase-ID grammar parsing, current-phase/
recommended-next-phase extraction, notification-outcome wording, and
malformed-phase-completion-metadata *display* handling for `pcae session
bootstrap` and related reporting surfaces. Its scope is **reading and
rendering** already-written report/metadata state coherently, including
under malformed or stale input.

It never asserted (and was not scoped to assert) a **gate**: that commit or
push eligibility itself must be conditioned on a canonical report matching
the currently completed phase existing at all. That is a property of
`pcae push`'s readiness assessment and (arguably) `pcae check`, not of
bootstrap/session *reporting*. This incident is therefore not a regression
of 136AX/136AY's verified scope — it is a gap in a different, previously
unexamined control (push-readiness / phase-report-trust gating) that
136AX/136AY's own verification boundary explicitly did not cover. Verdict:
**this is a previously untested command path**, not an incomplete repair of
136AX/136AY.

## 4. `pcae push` semantics investigation

`src/pcae/cli.py` registers `push` as a top-level command whose bare
invocation (`pcae push`, no subcommand) is handled by `run_push()`
(`src/pcae/commands/push.py:358`), which **executes a real `git push`**
whenever `assess_push_readiness()` reports `ready=True` and `--dry-run` was
not passed. `pcae push check` is a distinct subcommand handled by
`run_push_check()`, which never mutates.

Before this repair, both paths printed a near-identical header ("Push
readiness check" / "... / Ready to push.") and the CLI's own top-level help
text for `push` read only "Governed push: validate readiness and push to
the remote" — technically accurate but easy to skim past, especially
alongside `push check`'s near-identical phrasing ("Check whether the
repository is ready to push (no push)."). A reasonable operator (human or
agent) issuing the bare form while thinking of it as a status check is a
predictable failure mode, and it is exactly what happened in this session.

**Verdict: NON-BLOCKING but real usability defect, repaired.** `pcae push`
was already correctly load-bearing on `readiness.ready` before mutating —
it never pushed a dirty or not-ready tree — so this is not a Blocking
correctness defect. It is a disambiguation defect, repaired in §5.

## 5. Repairs applied

### 5a. Push-readiness phase-identity gate (`src/pcae/commands/push.py`)

Added `_detect_phase_report_gap()`, evaluated only when the active task is
idle (a phase actively in progress is never blocked — its report is not
expected yet). It:

- finds the most recently completed non-idle phase task in `tasks/done/`
  and extracts its phase-id token (`Phase 137F` → `"137F"`);
- fails closed (`status: "failed"`) if no canonical report exists at all,
  if the file is not valid JSON, or if the report's `phase_id` does not
  match that phase-id token;
- is otherwise `"not_applicable"` (no completed phase task yet, or a phase
  is still in progress) or `"passed"` (report and completed-phase identity
  agree).

Wired into `assess_push_readiness()` exactly like the pre-existing content
trust gate: a `"failed"` status forces `ready=False`, `mode="not_ready"`.
Surfaced in both human-readable (`_print_readiness`) and `--json` output as
`phase_report_identity_status`/`phase_report_identity_reason`.

This directly closes §2b: a stale-but-complete report, or a missing report,
now blocks push exactly as a partial/placeholder report already did.

### 5b. `pcae push` / `pcae push check` disambiguation

- CLI help text (`src/pcae/cli.py`) for both commands now leads with
  `MUTATING:` / `READ-ONLY:` and states plainly what each does and does
  not do, with a `description=` so it also appears in `pcae push --help`
  and `pcae push check --help` directly (previously only visible in the
  parent's own `--help` listing).
- `pcae push` now prints an explicit `EXECUTING REAL PUSH: N unpushed
  commit(s) to origin/<branch>. This is not a check -- pass --dry-run to
  preview without pushing.` banner immediately before it runs `git push`,
  and reports completion as `PUSH EXECUTED.` rather than the previously
  generic `Pushed:` label that could visually blend into an otherwise
  check-shaped report.
- `--dry-run` already existed and is unchanged; it is now more prominently
  cross-referenced from both the help text and the new banner.

No interactive confirmation prompt was added. That would be a materially
larger behavior change (breaking any existing non-interactive/scripted
caller of `pcae push`) than the demonstrated defect requires; the disclosed
banner plus corrected help text is the minimum repair that makes the two
commands unmistakable, per the phase's own success criterion ("a reasonable
operator cannot mistake the mutating command for the read-only check").
Not reverting the already-valid 137F push, per instruction.

## 6. Regression tests

Added `tests/test_push_phase_report_identity_137f1.py` (9 tests):

- completed phase task + idle active task + **no** canonical report → blocked
- completed phase task + idle active task + canonical report naming the
  **previous** phase → blocked, message names both the stale and correct id
- completed phase task + idle active task + **matching** canonical report → not blocked
- phase still **in progress** (active task not idle) → not blocked (gate not applicable)
- **no completed phase task at all** (fresh repo) → not blocked (gate not applicable)
- malformed (non-JSON) `latest.json` → blocked, message does not crash
- bare `pcae push` prints the `EXECUTING REAL PUSH` / `PUSH EXECUTED.` banner
- `pcae push check` never prints that banner
- `pcae push --help` / `pcae push check --help` each disclose their own semantics

## 7. Test results

- New suite: `tests/test_push_phase_report_identity_137f1.py` — 9 passed.
- `tests/test_push.py`, `tests/test_staged_file_aware_push.py`,
  `tests/test_post_push_canonicalization.py`,
  `tests/test_push_state_reconciliation.py`,
  `tests/test_commit_push_preflight.py`,
  `tests/test_commit_push_preflight_review.py`,
  `tests/test_commit_push_gate.py` — all passing (no regression introduced
  by the new gate or the disambiguated output/help text).
- `fast_green` (`pytest -m fast_green`) — passing (see governance section
  for the exact count captured for this phase's own canonical report).

## 8. Canonical report recovery

The original Phase 137F finalization produced **no canonical report and no
report notification** — that is the incident, not a success later relabeled.
This phase does not fabricate an original notification outcome. Recovery
proceeds through the governed lifecycle command (`.pcae/phase-completion-
metadata.json` corrected to accurately describe Phase 137F, then `pcae
phase complete` run to generate the canonical report and attempt
notification), producing a **delayed, 137F.1-recovered** canonical report
and a **separate, explicitly labeled recovery notification** — distinct
from (and never presented as) the original 137F finalization outcome. The
recovered report preserves: phase identity 137F, the VERIFIED verdict, both
recorded Non-Blocking observations, the two already-pushed 137F commit
hashes, `pushed: pushed`, `origin/main..HEAD: 0`, and the real test evidence
gathered during 137F and 137F.1.

## 9. Findings classification

| ID | Severity | Finding |
|---|---|---|
| F1 | BLOCKING | Push/commit eligibility had no gate verifying that a canonical phase report exists and identifies the most recently completed phase. A stale-but-schema-complete report passed the pre-existing trust check silently. Repaired in §5a; regression-covered in §6. |
| F2 | NON-BLOCKING | `pcae push` (mutating) and `pcae push check` (read-only) were too easy to conflate: near-identical output, help text that did not lead with the mutation/no-mutation distinction. Repaired in §5b; regression-covered in §6. |
| F3 | NON-BLOCKING | Operator sequencing used `pcae task complete` where `pcae task finish` or `pcae phase complete` was required to reach canonical-report generation. Documented here as contributing context; not a code defect, and not independently repairable by this phase (it is a "use the right command" issue, not a missing capability — `task finish`/`phase complete` already exist and already do the right thing when invoked). F1's gate is the structural backstop for this class of operator error. |
| F4 | DEFERRED | Whether `pcae check` (not just `pcae push`) should also surface this phase-report-identity gap proactively, before an operator ever reaches the push step, is left for a future phase to evaluate — out of the bounded scope authorized here (repair the minimum lifecycle defect independently demonstrated). |

No Blocking finding remains unrepaired. The substantive Phase 137F
verification result (VERIFIED, no Blocking finding, two Non-Blocking
observations) is unchanged; no evidence uncovered here bears on the
prototype's actual TAMC-001/TAMP-001 compliance.

## 10. Verdict

**Root cause independently demonstrated and repaired.** Canonical Phase
137F report recovered truthfully via the governed lifecycle, distinguishing
the original (no-report, no-notification) outcome from this phase's
delayed recovery. `pcae push` and `pcae push check` can no longer
reasonably be confused. Regression tests cover the demonstrated failure
paths. Fast Green remains green. Runtime remains Observed / observe /
unavailable throughout.

## Recommended next phase

**137F.1V — Canonical Report Finalization Recovery and Push-Semantics
Independent Verification.** 137G is not authorized to begin until 137F.1V
independently confirms this repair and no Blocking finding remains.
