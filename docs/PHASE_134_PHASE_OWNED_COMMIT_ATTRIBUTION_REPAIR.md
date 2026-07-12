# Phase 134E.10.1.1 — Phase-Owned Commit Attribution Repair

## 1. Executive Summary

134E.10.1's own governed canonical report cited five commits as
phase-owned, including `1844b05b`. Direct git-history inspection proves
`1844b05b` is unambiguously `134E.10V`'s own final commit — the immediate
parent of 134E.10.1's own first commit, not part of 134E.10.1's work at
all. Root cause: `commands/phase.py`'s `run_phase_complete` fell back to
an unconditional `git log --oneline -5` (`_gather_commits()`) whenever
`.pcae/phase-completion-metadata.json` lacked an explicit `phase_commits`
declaration — true of every phase in this session, since only the flat
`files_changed` list was ever hand-authored. Repaired at the actual root
cause: the blind fallback is removed (matching `commands/task.py`'s
already-safe equivalent, which never exhibited this defect); a new,
generic, additive cross-phase-commit-contamination check is now wired
into both entry points' gate computation, verified directly against real
git history to correctly flag the exact defect and clear the correct
commit set. This report is issued under its own corrective identity,
`134E.10.1.1`, and does not overwrite, resend, or create a second
ordinary completion for `134E.10.1`.

## 2. Commit-Attribution Methodology

"Re-derive from git history directly, never from a prior report's own
claim." Every one of the five originally-reported commit hashes was
independently inspected via `git log -1 --format="%ai / %s / parent:%P"
<hash>` — timestamp, subject, and parent commit — cross-referenced
against both 134E.10V's and 134E.10.1's own governed task-lifecycle
sequences (visible directly in `git log --oneline`, not inferred from
either report's own prose).

## 3. Exact Phase-Boundary Derivation

`a17efc1b`'s own parent commit is `1844b05b` — this is direct,
unambiguous proof that `1844b05b` is the repository revision 134E.10.1's
own work began *from*, not a commit 134E.10.1 itself produced. The
correct phase boundary for 134E.10.1: starts immediately after
`1844b05b` (134E.10V's own final governed commit), ends at `441a2142`
(134E.10.1's own final governed commit, immediately preceding this
corrective phase's own first commit).

## 4. Ownership Table

| Hash | Timestamp | Subject | Owning phase | Classification |
|---|---|---|---|---|
| `1844b05b` | 2026-07-12 02:51:05 +0200 | "Finish Phase 134E.10V test-evidence-key correction task" | **134E.10V** | Prior-phase commit, **incorrectly attributed** to 134E.10.1 |
| `a17efc1b` | 2026-07-12 09:46:21 +0200 | "Phase 134E.10.1: Final Lifecycle Integration Transaction-Span Repair" | 134E.10.1 | Correctly owned — implementation commit |
| `36266ac7` | 2026-07-12 09:46:26 +0200 | "Finish Phase 134E.10.1 task" | 134E.10.1 | Correctly owned — task-finish bookkeeping commit |
| `3bde236b` | 2026-07-12 09:47:58 +0200 | "Sync Phase 134E.10.1 completion metadata" | 134E.10.1 | Correctly owned — metadata-sync commit |
| `441a2142` | 2026-07-12 09:47:59 +0200 | "Finish Phase 134E.10.1 metadata sync task" | 134E.10.1 | Correctly owned — metadata-sync task-finish (bookkeeping) commit |

**Explicit classification of `1844b05b`:** 134E.10V's own final governed
commit (the corrective repair to 134E.10V's own "134E.10V test-evidence
-key phase-token collision," itself already documented in 134E.10V's own
phase report). It is not, and was never, phase-owned by 134E.10.1. Its
`~7`-hour timestamp gap from 134E.10.1's own first commit, its explicit
subject-line citation of "Phase 134E.10V," and its direct parent-commit
relationship to `a17efc1b` are three independent lines of evidence, all
concurring.

## 5. Root Cause

`commands/phase.py::run_phase_complete` (pre-repair):

```python
commit_attribution = meta.get("commit_attribution", "")
if "phase_commits" in meta:
    ...  # authoritative, correct path
else:
    commits = _gather_commits()   # <-- unconditional `git log --oneline -5`
```

`.pcae/phase-completion-metadata.json` for 134E.10.1 (as for every phase
in this session) declared `commit_attribution: "phase-owned governed
task-finish commit"` (a free-text label) but never the structured,
git-hash-bearing `phase_commits` field `run_phase_complete` treats as
authoritative — so every governed `pcae phase complete` call in this
session fell into the `else` branch, silently substituting "the last 5
commits on the branch" for "the commits this phase actually produced."
134E.10.1 happened to have exactly 4 real commits; a fixed 5-commit
window therefore always pulled in exactly one extra, prior-phase commit.
This is a **generic, systemic gap**, not specific to 134E.10.1 — every
phase in this session's own governed history (134E.9V onward) is
independently suspected to carry the same class of defect in its own
"Commits:" field, though only 134E.10.1's case was independently provable
by direct cross-reference with the immediately preceding phase's own
report.

`commands/task.py`'s equivalent fallback (`elif commit_hash: commits =
[commit_hash[:8]] else: commits = []`) never exhibited this defect — it
either uses a single, explicitly-supplied `--commit` hash or an empty
list, never a blind recent-commit guess. `commands/phase.py`'s fallback
is the sole affected shared boundary for the *root-cause* defect; both
`phase.py` and `task.py` now additionally carry the new cross-phase
contamination check (Section 7) as defense in depth, since a future,
different defect class could still produce a wrong commit list through
either entry point.

## 6. Repair

Two changes, both generic (no specific commit hash, phase identity, or
commit list hard-coded anywhere in the fix):

1. **`commands/phase.py`**: `_gather_commits()` removed entirely. The
   fallback (when `phase_commits` is absent from metadata) is now an
   explicit empty list with `commit_attribution` set to `"unresolved (no
   phase_commits declared in metadata)"` — matching `commands/task.py`'s
   already-safe precedent. Fail-closed, not silently wrong: an absent
   declaration now means the commits field is honestly unresolved, never
   a best-effort guess presented as fact.
2. **`pcae.core.phase_reports.detect_cross_phase_commit_contamination()`**
   (new, additive): for each candidate commit hash, reads its own subject
   line via `git log -1 --format=%s` (read-only) and, if the subject
   names a phase identity other than the one currently finalizing, treats
   it as a fail-closed gate blocker. Wired into both `commands/phase.py`
   and `commands/task.py`'s gate computation, applied identically at both
   entry points. Deliberately conservative: unresolvable hashes
   (synthetic/test data, or a real commit whose subject cites no phase at
   all) are silently skipped, never treated as contamination — this
   remains an additive safety net on top of, never a replacement for,
   explicit `phase_commits` declaration.

## 7. Fail-Closed Behavior and Cross-Phase Validation

Direct reproduction against real git history:

```
detect_cross_phase_commit_contamination(
    ["441a2142", "3bde236b", "36266ac7", "a17efc1b", "1844b05b"],
    "134E.10.1",
)
# -> ["commit 1844b05b subject names phase '134E.10V', not the current
#     phase '134E.10.1': 'Finish Phase 134E.10V test-evidence-key
#     correction task'"]

detect_cross_phase_commit_contamination(
    ["441a2142", "3bde236b", "36266ac7", "a17efc1b"],
    "134E.10.1",
)
# -> []
```

The original, defective five-commit list is correctly flagged with
exactly one contamination warning, for exactly the wrong commit; the
corrected four-commit list produces zero warnings. Wired as a fail-closed
gate blocker: a future phase whose declared or derived commits list
contains a provably-different-phase commit will have `gate["finalizable"]
= False`, preventing promotion, dispatch, and successful-marker
persistence — it cannot silently reach `report_completeness: complete`.

## 8. Corrected 134E.10.1 Phase-Owned Commit Set

`a17efc1b`, `36266ac7`, `3bde236b`, `441a2142` — four commits, in that
order. `1844b05b` is excluded.

## 9. Historical Preservation

`134E.10V`'s own canonical report and metadata are untouched by this
phase (this phase's diff touches zero files under `docs/PHASE_134_
FINAL_LIFECYCLE_INTEGRATION_INDEPENDENT_VERIFICATION.md` or any
134E.10V-owned artifact). `134E.10.1`'s own canonical report
(`docs/PHASE_134_FINAL_LIFECYCLE_INTEGRATION_TRANSACTION_SPAN_REPAIR.md`)
is likewise untouched — this repair does not edit, overwrite, or delete
it; the corrected commit attribution is recorded here, under this
phase's own distinct identity, not retroactively injected into 134E.10.1's
historical text. `git log --oneline --diff-filter=D -- docs/` confirms
zero deletions of any 134E.8-through-134E.10.1 document.

## 10. Correction-Purpose Identity

This report is issued under phase identity `134E.10.1.1`, a distinct
dotted-corrective identity from `134E.10.1` (matching this track's own
established convention: `134E.9` → `134E.9.1`; `134E.10` → `134E.10.1` →
`134E.10.1.1`). It does not resend `134E.10.1` as an ordinary completion,
does not create a second `.last-notified.json` ordinary-completion entry
for `134E.10.1`, and does not mutate `134E.10.1`'s own already-sealed
digest/snapshot identity. Section 13 confirms exactly one new logical
completion (for `134E.10.1.1` itself) was produced by this phase's own
governed finalization.

## 11. Incidentally Discovered and Repaired: Test Hermeticity Gap

This phase's own full-suite regression run surfaced one genuine,
pre-existing (not caused by this phase's production changes — confirmed
via `git stash`) defect in `tests/test_rc_audit_findings_repair.py`:

1. `_current_project_phase_id()`'s own regex supported at most one
   `.`-suffix group, silently truncating the real, live `PROJECT_
   STATUS.md`'s current phase (`134E.10.1`, a doubly-dotted identity —
   the first one this session ever produced) to `134E.10`.
2. `_synthetic_report()` never mocked `load_canonical_report()`, so
   `_apply_canonical_and_trust()` read this real repository's own live
   `.pcae/phase-completion-report.md` content, coincidentally colliding
   whenever that real content's own `fast_green` mention differed from
   the synthetic test's fixed `"1/1"` value.

Both repaired: the regex now supports arbitrary corrective-identity
depth (`(?:\.\d+[A-Za-z]?)*` unchanged; `_current_project_phase_id`'s own
copy widened from `?` to `*`); `load_canonical_report` is now mocked to
`None` in `_synthetic_report()`, matching the hermetic-isolation pattern
already established throughout this session's own test suite (134E.9's
`_report()`, 134E.10V's `_certified_report()`). All 18 tests in the file
now pass.

## 12. Transaction-Span Repair Re-Verification

Because this phase touches shared finalization-gate code, 134E.10.1's own
transaction-span repair was re-verified intact: the full `tests/
test_finalization_transaction_134e10.py` suite (37 tests) re-run and
passing unchanged; pre-promotion stages still gate `promote_and_dispatch`
identically; resumability, receipt honesty, and the five-parametrized
mandatory-stage-failure tests all pass unmodified.

## 13. Regression Results

- Focused: `tests/test_commit_attribution_repair_134e10_1_1.py` (12
  tests, new); `tests/test_rc_audit_findings_repair.py` (18 tests, 2
  pre-existing defects repaired); `tests/test_finalization_transaction_
  134e10.py` (37 tests, unchanged, re-confirmed passing).
- Broader affected regression (`test_phase_reports.py` +
  task-finish/notification/post-push/report-consistency suites): 306
  passed, 1 pre-existing unrelated failure.
- Full-suite regression: 19,371 passed, 182 failed — exact node-ID match
  to the established clean baseline; zero new failures, zero pollution
  (confirmed on two full runs in this phase, before and after the
  `test_rc_audit_findings_repair.py` fix).
- `fast_green`: 4391 passed, 0 failed — three consecutive runs (parallel
  twice, serial once), unaffected by the later `test_rc_audit_findings_
  repair.py` fix (confirmed out of `fast_green` scope via `--collect-only`).
- `compileall`: clean.

## 14. Governance Results

- `pcae check`, `pcae health`, `pcae doctor task-memory`, `pcae push
  check`: clean/healthy/passed throughout.
- Governed commit/push/task/phase commands only; no raw `git commit`, no
  raw `git push`, no `--no-verify`, no force push.
- Runtime remained Observed/observe/unavailable throughout — this phase
  touched zero runtime/execution code.

## 15. External-Delivery Isolation

No test in this phase's own additions sets a live notification
environment variable; `tests/conftest.py`'s autouse `_isolate_external_
notifications` fixture applies regardless. No test writes a production
receipt, marker, or checkpoint. Exactly one governed corrective terminal
delivery occurred for `134E.10.1.1` itself (Section 17) — the logical/
physical delivery distinction established in prior phases (a receipt/
marker proves a local dispatch attempt and its self-reported outcome, not
independently-verified remote acceptance or end-user receipt) applies
identically here; no stronger claim is made.

## 16. No-Go Confirmations

No 134F work began. No 134E.10.1V work began. No second ordinary
`134E.10.1` completion was created. No historical report was rewritten or
deleted. No specific commit hash, phase identity, or commit list is
hard-coded anywhere in the repair — `detect_cross_phase_commit_
contamination()` is fully generic. No new execution capability or
communication channel was introduced. No raw git commit/push,
`--no-verify`, or force push was used.

## 17. Recommended Next Phase

**134E.10.1V — Final Lifecycle Integration Transaction-Span Repair
Independent Verification** — per the corrective brief's own explicit
instruction, recommended only if this correction cleanly closes.
134E.10.1V has not begun. 134F has not begun.
