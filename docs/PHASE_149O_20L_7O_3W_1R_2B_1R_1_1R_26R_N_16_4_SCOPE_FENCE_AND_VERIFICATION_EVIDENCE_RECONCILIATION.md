# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R — N-16-4 Scope-Fence / Verification-Evidence Reconciliation and Repair

## 1. Purpose

This phase exists solely because `149O.20L.7O.3W.1R.2B.1R.1.1R.27`'s
independent verification (RE-DERIVE discipline) discovered one undisclosed
`.1R.26`-attributable stale point-in-time scope-fence guard and BLOCKED,
referring the narrow repair here per its own report and per this repo's
`.1R.18` / `.1R.20` / `.1R.23` precedent. This phase repairs the guard only;
it does not resume `.1R.27`'s adjudication and does not reopen N-16-4
technical semantics.

Phase-entry SHA: `9d28f7ef` (`.1R.26` finalized head; also current
`origin/main` before this repair — `origin/main..HEAD = 0` at entry).

## 2. Preserved current state (not reopened)

| Item | State |
|---|---|
| N-16-3 | CLOSED |
| N-16-4 implementation | IMPLEMENTED / IV BLOCKED |
| N-16-4 | NOT CLOSED |
| N-16-5 / N-16-6 / N-16-7 | OPEN |
| REPRC-001 v1.0 | AUTHORED |
| B1-B / B2-D / Currentness B | IMPLEMENTED |
| Production `Gate7Result(ALLOW)` | UNREACHABLE |
| Synthetic `Gate7Result(ALLOW)` | REACHABLE (test-only) |
| First external effect | ABSENT |
| Runtime | Observed / observe / unavailable |

## 3. `.1R.27` BLOCKED discovery (authoritative input, independently reproduced)

`.1R.27`'s canonical BLOCKED report identified:

`tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py::test_runtime_posture_unchanged_and_no_new_first_effect_call_site`

Independently reproduced by this phase, in a dedicated `git worktree` at the
immutable pre-`.1R.26` baseline:

- At `28b8b2b7` (pre-`.1R.26` baseline): **1 passed**.
- At `9d28f7ef` (`.1R.26` finalized head / entry SHA of this phase):
  **1 failed** —
  `AssertionError: {'src/pcae/core/permission_broker_foundation.py',
  'src/pcae/core/runtime_dispatch_gate7.py',
  'src/pcae/core/runtime_dispatch_permission.py'}` vs. the frozen expected set
  `{'src/pcae/core/permission_broker_foundation.py',
  'src/pcae/core/runtime_dispatch_permission.py'}` — extra item
  `src/pcae/core/runtime_dispatch_gate7.py`.

## 4. `.1R.27` evidence disposition (superseded by primary-operator governed action)

At phase entry (before this repair phase's task was opened), the working
tree carried one untracked file:
`tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py`
(`.1R.27`'s own new independent-verification suite, 37 tests, all passing —
left in place by the BLOCKED `.1R.27` session as reusable evidence). This
draft section originally proposed leaving it untracked, mirroring an earlier
interim state; the **primary human-authorized operator instead finalized
`.1R.27` under its own dedicated governed phase** (mirroring the `.1R.18`
BLOCKED-finalization precedent) — committing the evidence file, the BLOCKED
canonical report, and completion metadata, then pushing, all attributed
to `.1R.27`, entirely before this `.1R.26R` phase's own task was opened.

The file is therefore now **tracked**, committed under a `.1R.27` commit
subject (never a `.1R.26R` one — verified directly by
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py::test_17_...`,
which checks `git log -1 --format=%s` attribution rather than mere
untracked-ness), and was **not** folded into this phase's changes, not
renamed, not deleted, and not used as a `.1R.26R` repair test. This is a
strictly better disposition than leaving it untracked: it eliminates the
`pcae health`/`pcae check` unhealthy state an untracked out-of-task-scope
file previously caused (which the original draft of this section traced to
`test_pcae_cli_health_and_check_work_with_no_device_attached`), while still
preserving `.1R.27`'s BLOCKED verdict as historical record and its evidence
suite for a future `.1R.27`-restart phase to reuse unmodified.

## 5. Guard purpose (re-derived from source, not assumed)

`test_runtime_posture_unchanged_and_no_new_first_effect_call_site` makes
three independent assertions, all originating at `.1R.22` phase-entry
`8603fe6a`:

1. **Runtime posture unchanged** — `runtime_introspection`'s
   `CURRENT_RUNTIME_STATE` / `CURRENT_MAXIMUM_PLUGIN_CAPABILITY` /
   `EXECUTION_AVAILABILITY` still equal `("Observed", "observe",
   "unavailable")`.
2. **No first-effect call site** — no `adapter.dispatch(` line was added to
   `src/pcae` since `8603fe6a`, and `src/pcae/core/runtime_dispatch_gate10.py`
   (a hypothetical real-effect module) does not exist.
3. **Exact current-state `src/pcae` file-set fence** — the `git diff
   --name-only 8603fe6a HEAD -- src/pcae` result equals an exact, explicit
   set of authorized files.

Assertion 3 is the one that went stale: it is a **current-state** freeze
(evolves forward as later phases legitimately touch `src/pcae`), not a
**historical** freeze of what `.1R.22` itself touched — but its exact set was
never revisited after `.1R.26` legitimately added
`runtime_dispatch_gate7.py`. Assertions 1 and 2 were never false and remain
correct evidence of the same underlying security property (no runtime
posture mutation, no new effect call site) throughout.

## 6. Broad whole-tree re-derivation — true attributable count

A whole-tests-tree search for the same guard class (`git diff --name-only`
exact-set assertions against `src/pcae`) matched 67 test files. A
deterministic, no-xdist fixed-SHA A/B was run over that file set at
`28b8b2b7` (baseline, in a worktree) vs. the repaired tree (candidate):

- Baseline: 174 failed / 3133 passed / 2 skipped.
- Candidate (pre-repair HEAD `9d28f7ef` state, same file set): 173 failed /
  3264 passed / 2 skipped.
- **Candidate-only failures (2):**
  1. The known node (§3) — repaired in this phase.
  2. `test_pcae_cli_health_and_check_work_with_no_device_attached` — traced
     to the untracked `.1R.27` evidence file (§4), not a `.1R.26`-attributable
     regression; no repair needed or performed.
- **Baseline-only failures (3):** all three are `git worktree`-environment
  artifacts (a `NotADirectoryError` on a stray `.git/_r22r_ab_wt` path
  reachable only inside the throwaway worktree, and two failures caused by
  `.pcae/phase-reports/*` being gitignored — absent from a fresh worktree
  checkout — rather than a real behavioral difference at that historical
  point in the actual working tree). None reproduce at HEAD in the real
  working tree; none are `.1R.26`-attributable; no action required.

### 6a. Second discovery (primary-operator direct verification, post-draft)

After this phase's `.1R.27` evidence-file disposition was resolved by
finalizing `.1R.27` under its own governed phase (§4 amended below — the
file is now tracked, not left untracked), the primary operator ran the
combined Gate-7-referencing suite family directly and found one further
stale guard of the **identical class**, plus one **unrelated pre-existing**
finding:

- **`tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py::test_53_test_importers_of_gate7_symbols_are_a_known_finite_set`** —
  `.1R.26`'s own finite `AUTHORIZED_GATE7_TEST_IMPORTERS` allowlist did not
  admit the (legitimately authorized) `.1R.27` independent-verification
  suite, which imports Gate-7 symbols for its production-bypass and
  new-slot-transplant challenges. Same mechanical class as §3/§7: an exact,
  finite allowlist never widened to admit a later authorized file. **Repaired**
  by adding exactly one entry —
  `tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py`
  — with an explicit `.1R.26R` citation comment; the allowlist stays exact
  and finite (no wildcard); every other unauthorized importer still fails.
- **`tests/test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py::test_no_downstream_production_consumer_of_gate6_symbols`** —
  fails because `src/pcae/core/runtime_dispatch_gate10_eligibility.py`
  references `Gate6Decision`/related Gate-6 symbols and is not in that
  guard's frozen subset allowlist. **Independently confirmed via a clean
  `git worktree` at `9d28f7ef` (the unmodified `.1R.26` finalized head, zero
  `.1R.26R` changes applied) that this failure already exists there
  identically** — it is unrelated to `runtime_dispatch_gate7.py`, unrelated
  to any `.1R.26` or `.1R.26R` change, and pre-dates both. **NOT
  `.1R.26`-attributable — out of scope for `.1R.26R`; not repaired.**
  Disclosed as a carried, unattributed pre-existing finding (tracked
  informationally, no phase ID assigned by this repair).

**True attributable stale-guard count for this class: 2** (the node in §3
+ the `AUTHORIZED_GATE7_TEST_IMPORTERS` node in §6a). Combined with `.1R.26`'s
originally-disclosed 40, the running total of `.1R.26`-attributable guard
nodes reconciled across `.1R.26` + `.1R.26R` is **42**. No other same-class
stale guard needing reconciliation was found in either sweep. No production,
contract, effect-path, runtime-capability, or trust-boundary defect was
found — every defect found remains a verification-evidence scope-fence (or,
for the Gate-6/Gate-10-eligibility finding, an out-of-scope pre-existing
issue this phase does not own).

## 7. Repair

`tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py`,
function `test_runtime_posture_unchanged_and_no_new_first_effect_call_site`:
the exact-set assertion was widened from

```python
assert changed == {
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py",
}, changed
```

to

```python
assert changed == {
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/runtime_dispatch_permission.py",
    "src/pcae/core/runtime_dispatch_gate7.py",
}, changed
```

with an explanatory comment citing the `.1R.26` authorization and this
`.1R.26R` reconciliation. Exact-set equality (`==`) is preserved — no
wildcard, `fnmatch`, prefix, or subset/superset tolerance was introduced. The
test's other two assertions, its name, and its location are unchanged. No
other line in the file was touched.

## 8. Exact reconciliation table

| Node | Test file | Purpose | Old frozen set | Authorized `.1R.26` change | Why stale | Repair | Unauthorized-file challenge |
|---|---|---|---|---|---|---|---|
| `test_runtime_posture_unchanged_and_no_new_first_effect_call_site` | `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` | Runtime-posture / no-first-effect / exact current-state `src/pcae` file-set fence rooted at `.1R.22` entry `8603fe6a` | `{permission_broker_foundation.py, runtime_dispatch_permission.py}` | `runtime_dispatch_gate7.py` (N-16-4, single-file, `git diff 28b8b2b7 9d28f7ef -- src/pcae`) | Set never widened after `.1R.26` landed | Widened by exactly `{runtime_dispatch_gate7.py}`; exact-equality preserved | A synthetic 4th unauthorized file, a missing authorized file, and a substituted (wrong) runtime module were all adversarially tested (§9) — the guard rejects all three |
| `test_53_test_importers_of_gate7_symbols_are_a_known_finite_set` | `tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py` | Exact, finite allowlist of test files authorized to import Gate-7 module/symbols | 9-entry finite set (§6a) | The `.1R.27` independent-verification suite (authorized, finalized under its own governed phase) | Allowlist never widened after `.1R.27` was authored | Widened by exactly `{tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py}`; exact/finite preserved, no wildcard | Guard's own `test_54_consumer_allowlists_are_exact_and_finite` continues to assert no glob metacharacter in any entry; an unauthorized importer would still fail `test_53`'s exact-set-difference checks |

## 9. Adversarial guard-strength challenge

New dedicated suite
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` proves,
against the repaired guard's exact-set logic (re-implemented against the
live `git diff --name-only` mechanism, not a mock):

- The authorized exact 3-file set → **passes**.
- Adding a synthetic unauthorized 4th file
  (`src/pcae/core/runtime_dispatch_fake_effect.py`) to the set → **fails**.
- Removing one authorized file from the set → **fails**.
- Substituting `runtime_dispatch_gate7.py` for a different runtime module
  (`runtime_dispatch_gate8.py`) → **fails**.
- The repaired node itself, re-run directly → **passes**.
- The runtime-posture and no-first-effect assertions remain intact and were
  not weakened.

See §11 for the full suite contents and pass count.

## 10. No-test-weakening audit

Diff of this phase's changes (`git diff 9d28f7ef HEAD -- tests`, once
committed) against the guard file:

- `def test_` removed: **0**
- Test renamed: **0**
- `xfail` added: **0**
- `skip`-to-pass added: **0**
- Wildcard / `fnmatch` / prefix broadening: **0**
- Any other exact-freeze weakened: **0** (only the one node's set was
  touched, and only by exact-set widening)

## 11. Meta-guard search and results

Searched for meta-guards referencing this test file's basename, freezing its
byte identity, or scanning its allowed source set. None was found scoped to
`test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` specifically (it
is not enumerated in the `.1R.18` / `.1R.19R` / `.1R.19R.1` / `.1R.22R` /
`.1R.22R.1` meta-guard inventories — those track a different, disjoint guard
population). No meta-guard run was therefore required for this specific
repair; the containing suite (§12) and the broad A/B (§6, §13) are the
authoritative evidence instead.

## 12. Containing-suite and relevant-suite reruns

- `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` (full
  file, no xdist): **43 passed**.
- New `tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py`: see
  §13 for pass count.
- Core N-16-4 semantic smoke (§14): all green, no production change made.

## 13. New `.1R.26R` repair suite

`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` — 20 test
cases covering: baseline/candidate SHA reconstruction; known-node
baseline-PASS / candidate-FAIL reproduction; exact stale-set failure
semantics; the new authorized exact 3-file set; the 4th-unauthorized-file /
missing-authorized-file / substituted-file adversarial challenges;
runtime-posture and no-first-effect assertion preservation; test-basename
and no-wildcard/no-fnmatch/no-skip/no-xfail audits; the historical/current
distinction (§5); the broad-A/B true attributable count (§6); the repaired
node passing at HEAD; original `.1R.26` report preservation; the erratum's
presence and quantitative content; `.1R.27` BLOCKED-record preservation; no
production/contract diff; runtime unchanged; first-effect absence; N-16-5/6/7
untouched; N-23-2 carried. All 20 pass.

## 14. Core N-16-4 semantics smoke

Re-confirmed unchanged (no production edit was made in this phase):

- REPRC-001 v1.0 text: unchanged (`git diff 9d28f7ef HEAD --
  docs/contracts` = empty).
- B1-B / B2-D / Currentness B: unchanged (no `src/pcae` edit).
- Synthetic `Gate7Result(ALLOW)`: still reachable via the documented
  test-only `resolve_runtime_enforcement_posture` substitution.
- Production `Gate7Result(ALLOW)`: still unreachable (no production change).
- PB not re-run inside Gate 7: unchanged (no `runtime_dispatch_gate7.py`
  edit).
- Hard no-go semantics: unchanged.
- Gate 8 / Gate 9 / Gate 10 independence: unchanged.
- Runtime: `not_implemented / Observed / observe / unavailable`; 0 plugins;
  0 capabilities; `pcae runtime inspect` byte-identical before and after.
- First external effect: ABSENT.

## 15. Hard requirements verified

- `git diff 9d28f7ef HEAD -- src/pcae` = **empty**. No production source
  change.
- `git diff 9d28f7ef HEAD -- docs/contracts` = **empty**. No normative
  contract change.
- N-16-5 / N-16-6 / N-16-7: **OPEN**, untouched.
- N-23-2: **INFO / DEFERRED NORMALIZATION DEBT** — carried; no contract
  wording changed.

## 16. Historical vs. repaired fixed-SHA A/B

- **Historical A/B (preserved, not overwritten):** `28b8b2b7` baseline vs.
  the *original, unrepaired* `.1R.26` head `9d28f7ef` — 31 failed / 1836
  passed / 3 skipped (baseline) vs. 28 failed / 1915 passed / 3 skipped
  (unrepaired candidate), 27 common, 4 baseline-only (non-reproducing), **1
  candidate-only** = the node this phase repairs. This remains the accurate
  historical record of what `.1R.27` found; it is not rewritten.
- **Repaired-tree A/B:** `28b8b2b7` baseline vs. this phase's repaired HEAD,
  over the narrower 67-file exact-set-guard scope (§6): 174 failed (baseline)
  vs. 173 failed (repaired candidate) — 172 common (pre-existing,
  unrelated), 3 baseline-only (worktree artifacts, §6), **0 candidate-only
  unexplained** (the one candidate-only failure that remained,
  `test_pcae_cli_health_and_check_work_with_no_device_attached`, is the
  traced session-state artifact from §4/§6, not an unexplained functional
  regression). Zero N-16-4-attributable stale-guard failures remain.

## 17. Push-state A/B/C

Deferred to the parent session's governed push step (this phase does not
commit or push). Once pushed: A = `28b8b2b7`, B = this phase's finalized
`.1R.26R` SHA, C = `origin/main` post-push; B and C are required to be
functionally equivalent (identical commit).

## 18. Files created / modified

- `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` —
  repaired (exact-set widened by one entry; comment added).
- `tests/test_gate7_positive_runtime_enforcement_implementation_3w1r2b1r1_1r26.py`
  — `AUTHORIZED_GATE7_TEST_IMPORTERS` widened by exactly one entry (§6a).
- `tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py` — new
  repair/adversarial suite (20 cases; test 17 rewritten by the primary
  operator to check commit attribution rather than untracked-ness, per §4).
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26_N_16_4_REAL_POSITIVE_SINGLE_ATTEMPT_RUNTIME_ENFORCEMENT_GATE_IMPLEMENTATION.md`
  — additive erratum appended (§21); original content unchanged.
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_26R_N_16_4_SCOPE_FENCE_AND_VERIFICATION_EVIDENCE_RECONCILIATION.md`
  — this new canonical doc.
- `PROJECT_STATUS.md` — Current Phase replaced with `.1R.26R`; `.1R.27`
  (finalized separately in between, §4) demoted to a new first "Prior Phase"
  entry.
- `CHANGELOG.md` — new entry (see repository CHANGELOG).

Not part of this phase's commit scope:
`tests/test_gate7_positive_runtime_enforcement_independent_verification_3w1r2b1r1_1r27.py`
(`.1R.27` evidence — already tracked and committed under `.1R.27`'s own
phase before this phase began, §4; only referenced/allowlisted here, never
authored or re-attributed by `.1R.26R`).

## 19. Disposition

| Item | State |
|---|---|
| N-16-4 implementation semantics | UNCHANGED |
| `.1R.26` verification-evidence / scope-fence defect | **REPAIRED — INDEPENDENT VERIFICATION PENDING `.1R.26R.1`** |
| N-16-4 | NOT CLOSED |
| `.1R.27` historical verdict | BLOCKED — preserved, not converted; separately finalized under its own governed phase |
| True attributable stale-guard count (this class) | 42 (40 original `.1R.26` + 2 this phase: §3/§7 and §6a) |
| Additional same-class stale guards found | 1 (§6a, repaired) |
| Unrelated pre-existing finding (not `.1R.26`-attributable, not repaired) | 1 (§6a — Gate-6/Gate-10-eligibility consumer guard, confirmed present at unmodified `9d28f7ef`) |
| Production/contract defect found | 0 |
| Production diff | empty |
| Contract diff | empty |
| Runtime | Observed / observe / unavailable |
| First external effect | ABSENT |
| N-16-5 / N-16-6 / N-16-7 | OPEN |
| N-23-2 | INFO / DEFERRED |
| `.3` delegated finalization / commit / push | **UNAUTHORIZED** — preserved |

## 20. Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1` — Independent Verification of the
N-16-4 Scope-Fence / Verification-Evidence Reconciliation. Not begun. After
it closes, recommend a fresh/restarted `.1R.27` IV from the repaired
baseline — do not skip directly to N-16-5.

## 21. No-go confirmations

- No production `src/pcae` file was created, modified, or deleted.
- No normative contract file was created, modified, or deleted.
- No test was renamed, removed, or had assertions weakened; no `xfail` /
  `skip` added; no wildcard / `fnmatch` / prefix broadening introduced
  anywhere.
- The original `.1R.26` canonical report was not deleted or rewritten; only
  an additive erratum was appended.
- `.1R.27`'s BLOCKED verdict was not converted into a successful IV.
- The `.1R.27` untracked evidence file was not deleted, renamed, or folded
  into this phase's commit scope.
- N-16-4 was not closed in this phase.
- `.1R.26R.1` was not begun.
- `.1R.27` was not resumed.
- N-16-5 / N-16-6 / N-16-7 were not begun.
- Slice C was not begun; no first external effect was implemented or called;
  execution was not enabled.
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no
  history rewrite, no hook bypass — governed `pcae` lifecycle only.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
