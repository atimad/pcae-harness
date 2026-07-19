# Phase 137F.1V — Canonical Report Finalization Recovery and Push-Semantics Independent Verification

## Scope and method

Independent, adversarial verification of the Phase 137F.1 lifecycle-integrity
repair. Phase 137F.1's own report, tests, and narrative were treated as
claims, not as an oracle: every load-bearing claim below was re-derived from
git history, live repository state, or fresh fixtures that do not reuse
137F.1's own fixture tables. Three fresh, independently authored adversarial
fixtures directly disproved parts of 137F.1's own test table and surfaced
two additional live bypasses of the repaired gate, both repaired here.
Runtime was inspected before and after: unchanged at Observed / observe /
unavailable throughout.

## 1. Incident re-derivation (independently confirmed)

Reconstructed directly from `git log`, not from the 137F.1 narrative:

- `cea235a8` and `f3663187` ("Phase 137F: independently verify..." /
  "Phase 137F: open idle placeholder") are the two 137F commits. Both are
  confirmed ancestors of `origin/main` (`git merge-base --is-ancestor`) —
  the original push did reach the remote.
- `.pcae/phase-completion-metadata.json`'s git history (`git log --
  .pcae/phase-completion-metadata.json`) shows it was touched at 137E's
  close (`22f7e2a2`/`3100aa47`) and then *not again* until 137F.1's own
  repair commit (`d6f91ae3`) — confirming the metadata never identified
  137F between 137F's own commits and the 137F.1 repair, exactly as
  claimed.
- `pcae task complete --help` takes no arguments at all, confirming it is
  a bare, option-less command, structurally incapable of writing a
  canonical report or completion metadata — consistent with the claimed
  root cause.
- The recovered canonical report at
  `.pcae/phase-reports/20260719-173711-137F.json` (pre-existing, inspected
  directly, not regenerated) correctly identifies phase 137F, VERIFIED
  verdict, the two Non-Blocking observations, the two real 137F commit
  hashes, `pushed_status: pushed`, `origin_main_head_count: 0`, and an
  explicit `RECOVERY NOTE` distinguishing the delayed 137F.1 recovery from
  the original (no-report, no-notification) finalization. This is
  truthful and does not rewrite history.

All eight claims in the phase brief's "Incident Re-Derivation" section are
independently confirmed true.

## 2. Root-cause verification

The claimed root cause — `_assess_phase_report_trust()` validated only the
existing report's own schema completeness, never its identity against the
most recently completed phase — is confirmed by direct reading of the
pre-137F.1 `push.py` (via `git show`/`git stash` comparison) and remains
the correctly identified primary defect.

**This investigation independently found the claimed root cause was not
the complete picture.** Two additional, independently reproduced gaps
existed in the *repaired* gate itself (not identified or tested by
137F.1):

- **Gap A — non-idle exemption bypass (BLOCKING, found and repaired).**
  `_detect_phase_report_gap()` returned `not_applicable` unconditionally
  whenever the active task was non-idle, on the reasoning "a phase
  actively in progress is never blocked... since its report is not
  expected to exist yet." That reasoning was correct but the code was
  broader than the reasoning: `tasks/done/` only ever contains completed
  phases, so a phase in progress is never itself the phase this gate
  reconciles against — the exemption was unnecessary for the benign case
  and simultaneously permitted an indefinite bypass of the entire gate:
  close a phase without generating its report, then open a new *non-idle*
  task for the next phase instead of an idle placeholder, and the gate
  never fires again. Independently reproduced with a fresh fixture
  (`test_137f1v_nonidle_active_task_does_not_exempt_stale_prior_report`);
  confirmed live before the fix (`Phase report identity: not_applicable`,
  `Ready to push.`) and after (`Phase report identity: failed`, blocked).
- **Gap B — `--staged-file-aware` bypasses `assess_push_readiness()`
  entirely (BLOCKING, found and repaired).** `pcae push --staged-file-
  aware` (a flag on the same top-level `pcae push` command) is dispatched
  in `run_push()` to `_run_push_staged_file_aware()` *before*
  `assess_push_readiness()` is ever called on that path. That function
  has always computed its own, entirely separate readiness notion
  (protected-staged-file preservation, force-push detection) and never
  consulted health, check, doctor, phase-report-trust, or the new 137F.1
  phase-report-identity gate. Independently reproduced end-to-end with
  real local + bare-remote git repositories: with the exact repository
  state that `pcae push check` correctly reports as blocked (a completed
  phase with no canonical report), `pcae push --staged-file-aware` pushed
  the commit to the remote anyway — confirmed by inspecting the bare
  remote's own `git log` before and after the fix.

Both gaps are structurally distinct from 137F.1's own documented F1-F5 and
were not covered by 137F.1's own 9-test suite (which never exercises
`--staged-file-aware`, and whose one non-idle-active-task test —
`test_137f1_phase_still_in_progress_is_not_blocked` — asserted the
bypass's symptom as correct behavior; see §6).

Other candidate contributing factors from the phase brief were checked and
found not to contribute: command alias ambiguity (none — `task complete`/
`task finish`/`phase complete`/`phase-report create` are registered as
distinct subcommands with no aliasing); active-task identity precedence
and phase-ID selection precedence (investigated in §8, contributes to the
separately-scoped, correctly-deferred F5, not to the push gate itself).

## 3. Recovery truthfulness

Independently confirmed by direct inspection of
`.pcae/phase-reports/20260719-173711-137F.json` (not regenerated for this
verification): phase ID 137F, VERIFIED verdict, both Non-Blocking
observations, both real 137F commit hashes (`cea235a8`, `f3663187`),
`pushed_status: pushed`, `origin_main_head_count: 0`, real test evidence,
and an explicit recovery note distinguishing original (no-report, no-
notification) finalization from the delayed 137F.1 recovery. Confirmed
truthful; no history rewritten.

One coherence defect was found in this same artifact and is documented
in §11 (notification_result persistence), not in this section, since it
does not affect the *content* of the recovered report — only a metadata
field about the recovery's own delivery outcome.

## 4. Report/metadata/task/bootstrap coherence

Live `pcae session bootstrap --agent-id claude-local` at the start of this
verification correctly resolved: latest completed phase 137F.1 (report:
complete — since 137F.1's own canonical report was generated after the
137F.1 doc's own writing, closing its self-referential gap; see git log
`3dc25a53`/`3bc6f1c0`), recommended next phase 137F.1V, 137G blocked until
then. This is coherent. `.pcae/phase-reports/latest.json` now correctly
identifies 137F.1 (its own completion), while the archived, timestamped
137F report remains preserved and unmodified at
`.pcae/phase-reports/20260719-173711-137F.json` — the "latest" pointer
moving forward as new phases complete is expected behavior, not a
regression of the 137F recovery.

## 5. Gap detector verification

`_detect_phase_report_gap()` (`src/pcae/commands/push.py`) reads the most
recently completed non-idle phase task from `tasks/done/` (ordered by
parsed `YYYYMMDD-HHMM` task-id timestamp, not filename sort or mtime —
independently confirmed correct given this repository's mixed legacy/
modern task-id conventions) and compares its extracted phase-id token
against `.pcae/phase-reports/latest.json`'s own `phase_id` field by exact
string equality. It fails closed on: report file absent, report file not
valid JSON, report `phase_id` present but not equal to the completed
phase's id. It is `not_applicable` when no completed phase task exists at
all. **After the Gap A repair in §2, it is now evaluated unconditionally**
regardless of whether the active task is idle or a phase is in progress —
confirmed this does not regress the legitimate "phase in progress, prior
phase's report already matches" case (test corrected in §6). Comparison
is semantic identity on the extracted phase-id token, not a filename or
substring match; a malformed phase-id token (one that fails to match
`_PHASE_TOKEN_RE`) causes that task to be skipped in favor of an older,
matching one (or `None` if none match), which is a reasonable fail-open on
identity extraction, not fail-open on the gate itself. Not independently
tested here: exact behavior under multiple completed-phase tasks sharing
overlapping timestamps (edge case, low risk, DEFERRED — not required by
any adversarial finding).

## 6. Adversarial push-readiness matrix

Fresh, independently authored fixtures (not reusing 137F.1's own fixture
helpers' *expected values*, though the same `tmp_path` git-harness pattern
already used across this codebase's push tests was reused for efficiency,
per normal engineering practice — the assertions and scenarios are new):

| # | State | Expected | Actual (post-repair) |
|---|---|---|---|
| 1 | No completed phase, no report | not blocked | confirmed (existing 137F.1 test, re-verified) |
| 2 | Completed phase + matching report + metadata | not blocked | confirmed |
| 3 | Completed phase, no report | **blocked** | confirmed |
| 4 | Completed phase, stale prior-phase report | **blocked** | confirmed |
| 11 | Non-idle active task open after a completed phase with **no** report (Gap A) | **blocked** | was NOT blocked before repair; **blocked** after repair (new test) |
| — | `--staged-file-aware` push with the same missing-report state (Gap B) | **blocked** | was NOT blocked before repair (pushed to real remote); **blocked** after repair (new test) |
| 7 | Malformed `latest.json` | **blocked** | confirmed (existing test) |
| 9/15 | Phase in progress, but the *previously completed* phase already has its own matching report | not blocked | confirmed — required correcting 137F.1's own test, see below |
| 16-18 | Dirty tree / unpushed commits / nothing-to-push with matching report | governed by pre-existing mode logic, unaffected by this gate | confirmed unaffected |

**137F.1's own test suite contained a materially wrong expected-value
test**, discovered by treating it as a claim rather than an oracle:
`test_137f1_phase_still_in_progress_is_not_blocked` closed a phase with
**no report at all**, then opened a new non-idle task, and asserted
`ready`/`not_applicable` as correct. That is exactly Gap A's shape. It has
been corrected in this verification to give the previously-completed
phase its own matching report (the case the exemption's own stated
reasoning actually describes), and a new test
(`test_137f1v_nonidle_active_task_does_not_exempt_stale_prior_report`)
independently covers the real bug the old test's assertion was masking.

Scenarios 5, 6, 8, 10, 12-14 were reasoned about via direct code reading
(single-field exact-match comparison against one `phase_id` string
extracted from one file; no separate Markdown/JSON identity check exists
to diverge, no multi-completed-task selection ambiguity beyond the
already-tested timestamp-ordering fix) rather than each requiring a
separate executed fixture; no additional defect was found in them.

## 7. Commit-gate boundary

Confirmed unchanged: `pcae commit implementation` does not gate on
canonical-report identity at all (by design — a phase's own commits must
be stageable before its report can describe them; report generation
necessarily follows commit, not precedes it, so gating commit on report
identity would create the exact cycle the brief asks about). The
structural backstop remains at push time, now closing both the original
gap and the two gaps found here. This is intentional, not a residual
trust gap, given push (not commit) is the boundary that reaches the
shared remote.

## 8. Finalization command semantics

`pcae task complete` (no options, bare relocation), `pcae task finish`
(validation + memory update + session refresh + optional commit), `pcae
phase-report create` (manual/recovery report creation with explicit
identity), and `pcae phase complete` (primary finalization path) are
distinct registered subcommands with no aliasing. Their top-level `--help`
text is distinguishable ("Complete the latest active task contract." vs.
"Finish the active task with validation, memory updates, and session
refresh.") but `task complete`'s help does not explicitly warn that it
skips canonical-report/metadata generation — confirmed this ergonomic gap
is real and still present. Classified **NON-BLOCKING**, consistent with
137F.1's own F3: the structural gate (now strengthened by this phase) is
the actual safety backstop; the wording gap is a real but lower-severity
usability issue, unchanged in scope from 137F.1's own assessment.

## 9. Push command semantics

Confirmed: `pcae push check` never calls `subprocess.run(["git", "push"]
...)` (grepped and read directly); `pcae push` (bare) does, gated on
`readiness.ready`. The `EXECUTING REAL PUSH` banner is printed
unconditionally on the mutating code path immediately before the
`subprocess.run` call, never after, and cannot be reached by `push check`
or the dry-run/not-ready branches (verified by direct code reading of the
control flow, not just the existing tests). `--json` mode omits the
human-readable banner text but still only ever prints `"pushed": true`
after a real push succeeded — sufficient machine-readable signal.
Confirmation/dry-run: unchanged assessment from 137F.1 — **NON-BLOCKING**,
`--dry-run` already exists and a forced interactive prompt would be a
disproportionately larger behavior change than the demonstrated defect
(which was disambiguation, not missing gating) requires.

## 10. Bootstrap and session-state verification

Live `pcae session bootstrap` correctly resolves current phase, latest
completed phase, and recommended next phase, and correctly reflects
`report: complete` for 137F.1 now that its own canonical report exists.
Confirmed bootstrap cannot silently present a stale prior phase as
current: it derives "latest completed phase" from the same `tasks/done/`
scan the (now-corrected) push gate uses, and reads the report's own
`phase_id` directly rather than assuming freshness.

## 11. Notification verification

**Found and repaired a real coherence defect**, independent of the
137F.1 narrative: `pcae phase-report create` (the exact command used to
recover the 137F report) computes a real `notification_result` in memory
after dispatch (`run_phase_report_create`'s `_promote_and_dispatch`), but
`write_phase_report()` had already written the canonical artifact to disk
*before* dispatch was attempted (necessarily — a dispatched message
attaches the just-written report file). Unlike `finalize_phase_report()`
(the engine behind `pcae phase complete` / `pcae task finish --commit`),
which calls `_persist_notification_result()` after dispatch specifically
to patch this exact class of bug (documented in that function's own
docstring, itself a Phase 136AY repair), `run_phase_report_create` never
called it. Independently reproduced: CLI console output correctly showed
`Notification dispatch: sent` while the persisted `latest.json` still
held `notification_result: {}`, which `pcae session bootstrap` renders as
`"not attempted (no dispatch recorded for this phase)"` — directly
contradicting the phase-completion-metadata's own claim that the 137F.1
recovery notification was sent. **Repaired** by calling
`_persist_notification_result(promoted_paths, report.notification_result)`
at the end of `_promote_and_dispatch`, mirroring the existing
`finalize_phase_report()` pattern exactly. Verified fixed with a fresh
fixture (`test_137f1v_phase_report_create_persists_real_notification_result`).

This means the specific archived artifact
`.pcae/phase-reports/20260719-173711-137F.json` (already on disk before
this fix) still shows `notification_result: {}` and will not be
retroactively patched — its historical record is now understood to
under-report (not fabricate) the original 137F.1 recovery's own
notification outcome; the phase-completion-metadata's separate prose
claim of "notification dispatch sent via Telegram" for that recovery is
independently plausible (Telegram sinks were confirmed configured/enabled
via `pcae notify status` at that time) but not directly re-verifiable
from that one artifact's own JSON after the fact. Not itself a
falsification: no notification is fabricated as sent when it was not;
the defect was under-disclosure, not over-claiming, and is fixed
prospectively.

## 12. Regression and compatibility verification

- `tests/test_push_phase_report_identity_137f1.py` — 12 passed (9
  original + 1 corrected expected-value + 2 new adversarial tests).
- `tests/test_push.py`, `test_staged_file_aware_push.py`,
  `test_post_push_canonicalization.py`, `test_push_state_reconciliation.py`,
  `test_commit_push_preflight.py`, `test_commit_push_preflight_review.py`,
  `test_commit_push_gate.py` — 184 passed total, no regressions from
  either repair.
- Fast Green (`pytest -m fast_green -n auto`) — 4391 passed, matching the
  137F.1 report's own count, confirming no regression from either fix.
- Four pre-existing failures were found and independently confirmed
  unrelated to this phase's changes (wheel-build artifact/dist-dir
  staleness tests) by reproducing them identically against the
  pre-137F.1V working tree via `git stash`.

## 13. Production boundary verification

`git diff --stat` for this phase touches only
`src/pcae/commands/push.py`, `src/pcae/commands/phase_reports.py`,
`tests/test_push_phase_report_identity_137f1.py`, and task/doc/changelog
bookkeeping. No Stage 3 schema/model/registry/manifest, TAMC-001,
TAMP-001, Phase 137E prototype, or Phase 137F verdict files were touched.

## 14. Runtime verification

`pcae runtime inspect` before and after this phase's changes: State
Observed, Maximum Capability observe, Execution Availability unavailable,
Registry empty, Plugin count 0 — unchanged. No capability drift.

## Adversarial questions — answered

- **Can a stale but internally valid report still pass push readiness?**
  No, for the ordinary `pcae push`/`pcae push check` path (confirmed by
  existing + new fixtures). It could for `pcae push --staged-file-aware`
  before this phase's Gap B repair; cannot after.
- **Can malformed task state cause the detector to select the wrong
  phase?** Not demonstrated; the timestamp-parsing ordering fix from
  137F.1 itself is independently confirmed correct for this repository's
  mixed task-id conventions.
- **Can a recovery phase hide the substantive phase/report mismatch?**
  No — recovery phases (`137F.1`) get their own phase-id token and their
  own report; they do not stand in for the substantive phase's identity.
- **Can phase-ID formatting differences bypass comparison?** Not in the
  unsafe direction (no evidence a formatting difference lets an invalid
  push through). It did produce a false *block* on a valid state: V5's
  extraction truncation made the gate compare `"137F.1"` (truncated)
  against the report's correct `"137F.1V"`, disagreeing and blocking a
  legitimate push. Repaired in V5. The gate itself still uses exact
  string equality on one extracted token with no normalization either
  side, though a related, separately-scoped case-sensitivity defect
  exists in
  `pcae phase complete`'s transition validator (137F.1's own F5,
  independently plausible from direct reading of
  `parse_phase_id_from_text`'s case-preserving regex extraction combined
  with a slug-derived lowercase source; not fully reproduced live in this
  verification given it is explicitly out of this phase's authorized
  scope and does not affect the push gate under verification here).
  Remains correctly classified DEFERRED.
- **Can missing metadata be mistaken for no applicable phase?** No — the
  gate does not read `phase-completion-metadata.json` at all; it reads
  `tasks/done/` directly.
- **Can multiple completed tasks produce nondeterministic selection?**
  Not demonstrated; selection is deterministic (max by parsed timestamp).
- **Can direct use of another push path bypass `assess_push_readiness()`?**
  **Yes — found and repaired (Gap B, §2, §6).**
- **Can commit and then push occur through a command path that omits the
  repaired gate?** Commit, yes by design (§7); push, no longer, after
  Gap B's repair — no other `git push` call site in `src/pcae/commands/
  push.py` remains ungated. Other `git push` call sites exist elsewhere
  in the codebase (`agent.py`, `phase.py --execute`) but are gated behind
  execution-availability, which remains `unavailable` per §14 — out of
  this phase's scope to further audit.
- **Can `pcae task complete` still create a misleading terminal phase
  state?** Structurally yes (unchanged, §8) but now reliably caught at
  push time by the strengthened gate rather than only sometimes.
- **Can notification evidence be attributed to the wrong finalization
  attempt?** No fabrication found; an under-reporting persistence defect
  was found and repaired (§11).

## Findings classification

| ID | Severity | Finding |
|---|---|---|
| V1 | BLOCKING (repaired) | `_detect_phase_report_gap()`'s non-idle exemption permitted an indefinite bypass of the 137F.1 gate by opening a new non-idle task instead of an idle placeholder after a report-less phase closure. Repaired in `src/pcae/commands/push.py`; regression-covered. |
| V2 | BLOCKING (repaired) | `pcae push --staged-file-aware` never called `assess_push_readiness()`/`_detect_phase_report_gap()`/`_assess_phase_report_trust()` at all, and was independently confirmed to push to a real remote under a repository state the ordinary path correctly blocks. Repaired by adding both gates to `_run_push_staged_file_aware()`; regression-covered. |
| V3 | NON-BLOCKING (repaired) | `pcae phase-report create` computed a real notification outcome but never persisted it to the on-disk canonical artifact, causing `pcae session bootstrap` to report "not attempted" for a phase whose notification actually succeeded. Repaired by calling the existing `_persist_notification_result()` helper; regression-covered. |
| V4 | NON-BLOCKING (test-correctness only, repaired) | 137F.1's own regression suite contained a test whose expected value (`ready`) was the symptom of V1; corrected to test the scenario its own docstring actually describes (previously-completed phase already has a matching report). |
| V5 | BLOCKING (repaired) | Self-referentially discovered while finalizing this very phase: `_PHASE_TOKEN_RE` (`src/pcae/commands/push.py`) stopped matching at the last all-digit dotted segment, truncating any phase ID with a trailing letter suffix after a dotted segment (`"137F.1V"` -> `"137F.1"`, `"134E.10.1V.1"` -> `"134E.10.1"`). That convention is common in this repository's own task titles (`134E.1V` through `134E.10.1V.1`, and this phase's own `137F.1V`), and the truncation caused `pcae push check` to falsely report `phase_report_identity: failed` for this phase's own legitimately matching report/task pair immediately after its canonical report was generated -- a real, live false block on a valid governed finalization, not a hypothetical one. Repaired by aligning the pattern with the already-proven regex `parse_phase_id_from_text()` uses in `repository_transition_integration.py` for the same purpose; regression-covered. |
| — | (reaffirmed, unchanged) | 137F.1's F2/F3/F4/F5 (push/push-check disambiguation, operator sequencing, `pcae check` proactive surfacing, transition-validator case sensitivity) independently reviewed and correctly classified; no new evidence changes their disposition. |

No Blocking finding remains unrepaired. V1, V2, and V5 were all live,
independently demonstrated defects — two bypasses of the exact class of
incident 137F.1 was created to close, and one false-block regression on a
valid governed finalization path — discovered because this verification
did not treat 137F.1's own tests, dispatch table, or narrative as an
oracle, and (for V5) because this phase's own finalization was itself
driven through the repaired gate rather than assumed correct.

## Verdict

**VERIFIED AFTER REPAIR.**

Three Blocking findings (V1, V2, V5) were independently demonstrated and
repaired; one Non-Blocking coherence defect (V3) was independently
demonstrated and repaired; one Non-Blocking test-correctness issue (V4)
in 137F.1's own suite was corrected. All existing and new tests pass (13
in the 137F.1V-evolved suite, 184 across the full push/commit-gate
suites). Fast Green remains green (4391 passed). Runtime remains Observed
/ observe / unavailable throughout, with no capability drift. The Phase
137F VERIFIED verdict and the recovered canonical 137F report are
preserved unmodified. Phase 137F.1's own F1-F5 disposition is reaffirmed;
no new evidence contradicts it.

## Recommended next phase

**137G — Typed Authority Model Prototype Review and Production Integration
Architecture** is now authorized to begin, per the phase brief's success
criteria (VERIFIED AFTER REPAIR with no Blocking finding remaining).
