# Phase 135T Complete — Atomic Publication Rehearsal Independent Verification

## Phase identity

- Phase ID: `135T`
- Status: completed
- Classification: implementation
- Report completeness: complete

## Summary

Phase 135T independently verifies Phase 135S ("Atomic Publication
Rehearsal, Legacy Authority"). Re-derived 135Q's Stage 2 contract
directly from its own text — never from 135S's paraphrase — and
attacked 135S's implementation instead of trusting its own claims.
Found and repaired two Blocking defects within the Stage 2
implementation boundary (independent verification plus bounded
repair): (1) a real, live-reproduced symlink-escape containment gap —
`coordinator.py` wrote every candidate artifact and the manifest via a
bare `Path.write_text`/`write_bytes` call, bypassing
`persistence.write_candidate_artifact`'s pre-existing-symlink abort
entirely (the helper existed but was never called from the coordinator);
repaired by wiring the coordinator to the existing helper. (2) 135S's
own regression-baseline claim (5/8/10 "pre-existing, sandbox-local,
receipt-modeling" failures across four named regression suites) did
not reproduce on independent re-run — the actual 2 failures were a
genuine, small, Stage-2-caused regression (two stale test assertions
in `tests/test_cltr_migration_135p_verification.py` left over from
before F-135P-1's fix landed), independently confirmed via an isolated
`git worktree` at the exact pre-135S baseline commit (`7fb4dbc1`),
never mutating the primary repository: all 4 parametrized cases pass
there; 2 fail on the unrepaired 135S tree; repaired by correcting the
two assertions.

## Evidence and validation

- Governed phase commits: `8670312e` (independent verification
  implementation and repairs), `e0484051` (task-contract cleanup) — 9
  files changed.
- Stage 2 focused tests: 44/44 passed (28 inherited from 135S in
  `tests/test_cltr_rehearsal_coordinator.py` + 16 fresh adversarial
  tests in `tests/test_cltr_rehearsal_135t_independent_verification.py`:
  symlink-escape regression, identity determinism incl. cross-process
  stability, honest 23-item inventory disclosure, live on-disk
  manifest-tamper detection).
- Combined migration suite: 129/129 passed (0 failures after repair;
  was 2 failures on the unrepaired tree, which 135S's own report had
  misclassified as 8 pre-existing/unrelated).
- Production CLTR combined regression: 414/414 passed (0 failures
  after repair).
- Affected finalization regression: 117/117 passed; 0 failures — 135S's
  claimed 5 pre-existing failures did not independently reproduce.
- Notification/marker/receipt/phase-report/Architecture-Status
  regression: 1183/1183 passed (0 failures after repair; was 2 on the
  unrepaired tree, misclassified by 135S as 10 pre-existing).
- Independent baseline reproduction (isolated `git worktree` at
  pre-135S commit `7fb4dbc1`, never mutating the primary repository):
  101/101 passed on the combined migration suite; the specific
  4-case parametrized test passed 4/4 there, confirming the repaired
  regression was newly introduced by 135S, not inherited.
- Fast Green (`python -m pytest -m "fast_green" -n auto`): **4391/4391
  passed**, unchanged.
- Live filesystem-snapshot proof: `pcae cltr migration rehearsal
  status`/`reconcile` against an empty temp directory left it
  byte-for-byte unchanged (0 entries before and after).
- `pcae health` healthy; `pcae check` passed; task memory clean; push
  check clean; runtime inspect Observed/observe/execution unavailable;
  Telegram outbound delivery configured, enabled, ready.

Full disposition, the node-by-node baseline reproduction table, and
every verification area's evidence in
`docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_INDEPENDENT_VERIFICATION.md`.

## Findings (full detail in the phase document §32)

- **F-135T-1 (CONFIRMED, BLOCKING, repaired):** candidate-artifact and
  manifest writes bypassed the pre-existing-symlink abort. Repaired:
  `coordinator.py` now calls `write_candidate_artifact` for every write.
- **F-135T-2 (CONFIRMED, BLOCKING, repaired):** 135S's regression-baseline
  claim did not reproduce; the real 2 failures were a self-caused
  regression misclassified as inherited. Repaired: two stale test
  assertions corrected.
- **F-135T-3 (NON-BLOCKING, honestly disclosed, no repair needed):**
  135Q §9's 23-item inventory is implemented as 10 file-backed items
  plus manifest/evidence-record-bound fields, with items 11–14
  folded/deferred — independently confirmed genuinely disclosed in a
  real end-to-end-produced manifest.
- **F-135R-4 (inherited, non-blocking, correctly deferred):**
  rollback-rehearsal-vs-ordinary-publication race not yet reachable
  since rollback rehearsal is not implemented in 135S.

## Disposition of 135S's own F-135P-1..4 and 135R's F-135R-1..4 findings (full detail §25–§26)

All four F-135P findings independently re-verified against current
source (not accepted from 135S's claim): F-135P-1, F-135P-3, F-135P-4
genuinely fixed; F-135P-2's Stage-2-facing half genuinely wired,
`TEMPORAL_ORDER_MISMATCH` correctly still deferred. All four F-135R
findings independently re-read from 135R's own text: F-135R-1's
disclosed Windows-transient-rename mitigation is actually implemented
(beyond what was required); F-135R-2's two-Stage-0-copy disclosure
confirmed still accurate and correctly out of scope; F-135R-3 is
documentation-only, no code implication; F-135R-4 remains correctly
deferred since rollback rehearsal is not yet built.

## Safety and no-go confirmation

No lifecycle authority other than legacy exists; legacy lifecycle
remains the sole production authority. No CLTR authority exists; CLTR
remains derivative. No authoritative status was granted to the Stage 2
rehearsal generation; it remains non-authoritative. No authoritative
status was granted to the Stage 2 rehearsal pointer; it remains
non-authoritative. No production pointer changed because of Stage 2.
No external delivery originated from Stage 2 — no Telegram or other
notification sink was invoked from any rehearsal module (confirmed by
static import-graph inspection and a live filesystem-snapshot-equality
test on the CLI). No production marker was created or modified by
Stage 2. No production receipt was created or finalized by Stage 2. No
Stage 3 implementation was begun in this phase. No authority-cutover
design work was performed in this phase. No legacy authority was
demoted. No legacy authority was retired. No execution capability was
introduced — no subprocess, shell, socket, or network call exists
anywhere in the rehearsal package (confirmed by grep and by the
existing structural no-execution test). No raw `git commit` or `git
push` was used; no `--no-verify` hook bypass; no force push. Runtime
remains Observed, maximum capability observe, execution availability
unavailable throughout.

## Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS** (independent verification plus
bounded repair). No unresolved Blocking finding remains.

## Recommended next phase

Phase 135U — Rollback Rehearsal Implementation and Independent
Verification (not started; a design judgment for the next
contract/planning phase to confirm, not asserted as final by this
phase). 135M's remaining migration plan, 135Q/135R's deferrals (F-135R-4),
and 135S's own disclosed limitation (no rollback-rehearsal
implementation yet) together point to rollback rehearsal as the most
load-bearing remaining gap before any Stage 3 authority-cutover
readiness discussion.
