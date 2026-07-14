# Phase 135U Complete — Rollback Rehearsal Implementation and Independent Verification

## Phase identity

- Phase ID: `135U`
- Status: completed
- Classification: implementation
- Report completeness: complete

## Summary

Phase 135U implements the rollback-rehearsal capability 135Q §33/§36/§37/§38
froze and 135T's F-135R-4 disposition confirmed 135S left unimplemented,
then independently attacks that implementation within the same governed
phase. Re-derived the frozen rollback contract directly from 135Q's own
text rather than inventing a new model. Implemented in
`src/pcae/cltr/migration/rehearsal/rollback.py` (new): a deterministic
rollback-request identity (pure function of phase_id, transition_id,
migration_epoch, authority_epoch, source/target generation IDs, and
reason; confirmed stable across a fresh Python subprocess); strict
target validation (schema, digest recomputed fresh from disk,
epoch/transition binding, quarantine rejection, symlink containment);
an 11-step atomic rollback sequence reusing the exact same
`os.replace`-backed pointer primitive and containment/verification
logic ordinary forward publication uses; a §33-shaped rollback
evidence record; idempotent replay with zero evidence duplication;
fail-closed conflicting-replay detection; a full crash-injection
matrix with correct recovery, including for a rollback whose atomic
pointer replace had already durably succeeded before a crash
interrupted evidence persistence; and the
`pcae cltr migration rehearsal rollback`/`rollback-status` CLI
(operator-command-only). A separately-written adversarial verification
module then attacked the new capability and found two genuine,
Non-Blocking defects, both repaired within this same phase: (1)
post-rollback `reconcile`/`rollback-status` silently lost the
requesting `phase_id`; (2) the authority-epoch validation used a
substring check bypassable by `"cltr|not-legacy"`.

## Evidence and validation

- Governed phase commits: `053c0cf4` (rollback implementation and
  adversarial tests), `d1d6ca50` (task-contract cleanup), `7ffb313e`
  (canonical phase-completion metadata), `4cdc2d4f` (pushed-status
  metadata correction) — 19 files changed.
- Rollback focused implementation tests: 43/43 passed
  (`tests/test_cltr_rehearsal_rollback.py`).
- Rollback independent adversarial tests: 26/26 passed
  (`tests/test_cltr_rehearsal_135u_independent_verification.py`); found
  and drove the repair of F-135U-1 and F-135U-2.
- Stage 2 focused tests (existing, unmodified except the `pointer.py`
  refactor): 44/44 passed.
- Combined migration suite: 214/214 passed.
- Production CLTR combined regression: 499/499 passed.
- Affected finalization regression (exact 135S/135T node set): 117/117
  passed.
- Notification/marker/receipt/phase-report/Architecture-Status
  regression: 1185/1185 passed.
- Fast Green (`python -m pytest -m "fast_green" -n auto`): **4391/4391
  passed**, unchanged.
- Live filesystem-snapshot proof: `pcae cltr migration rehearsal
  rollback-status`/`reconcile --phase-id 135U` against the real
  repository (no Stage 2 namespace present) confirmed `.pcae/cltr-
  migration` absent before and after both commands, `found: false`
  reported honestly, zero mutation.
- `pcae health` healthy; `pcae check` passed; task memory clean; push
  check clean; runtime inspect Observed/observe/execution unavailable;
  Telegram outbound delivery configured, enabled, ready.

Full disposition and every verification area's evidence in
`docs/PHASE_135_ROLLBACK_REHEARSAL_IMPLEMENTATION_AND_INDEPENDENT_VERIFICATION.md`.

## Findings (full detail in the phase document §14)

- **F-135U-1 (CONFIRMED, Non-Blocking, repaired):** post-rollback
  `reconcile`/`rollback-status` lost the requesting `phase_id` because
  phase-to-transition resolution only checked the *current* generation's
  own embedded phase_id, not rollback history. Repaired:
  `reconciliation.py` now also matches against persisted rollback
  evidence.
- **F-135U-2 (CONFIRMED, Non-Blocking, repaired):** authority-epoch
  validation used a substring check (`"legacy" in value`) bypassable by
  `"cltr|not-legacy"`. Repaired: exact `"legacy|..."` prefix check.

No other Blocking or Non-Blocking defect was found.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority; CLTR remains
derivative. Rollback rehearsal affected only the non-authoritative
rehearsal namespace and did not roll back production lifecycle state.
No production phase report, completion metadata, Architecture Status,
checkpoint, pointer, marker, or receipt changed because of rollback
rehearsal. No external notification originated from rollback rehearsal
— confirmed by static import-graph inspection (no `subprocess`,
`socket`, `urllib`, `requests`, or `telegram` reference anywhere in
`rollback.py`) and live filesystem-snapshot-equality tests. No
immutable rehearsal generation was rewritten or deleted. No Stage 3
implementation, authority cutover, legacy demotion, or legacy
retirement occurred. No execution capability was introduced. Runtime
remains Observed, maximum capability observe, execution availability
unavailable throughout. No raw `git commit` or `git push` was used; no
`--no-verify` hook bypass; no force push.

## Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS** (implementation plus
independent verification within the same governed phase; two
Non-Blocking defects found and repaired; zero Blocking defects
survive).

## Recommended next phase

A small, bounded follow-on closing the disclosed cross-epoch-rollback
and concurrent-rollback-vs-forward-race gaps, or Phase 135V — Stage 3
Authority-Cutover Readiness Architecture (not started; a design
judgment for the next contract/planning phase to confirm, not asserted
as final by this phase).
