# Phase 135S Complete — Atomic Publication Rehearsal Implementation

## Phase identity

- Phase ID: `135S`
- Status: completed
- Classification: implementation
- Report completeness: complete

## Summary

Phase 135S implements Stage 2 ("Atomic Publication Rehearsal, Legacy
Authority") under `src/pcae/cltr/migration/rehearsal/`, per the
contract 135Q froze and 135R independently verified. Legacy lifecycle
remains the sole production authority throughout; the rehearsal
generation and rehearsal pointer are non-authoritative by construction,
never merely by policy. Implements: a 10-file candidate-artifact
inventory (of the 23-item inventory 135Q §9 names; the remaining 13
items bound into the manifest/evidence record, disclosed in
`docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_IMPLEMENTATION.md` §11);
deterministic rehearsal-generation identity; manifest and
per-artifact/generation SHA-256 digests with split-brain cross-reference
checks; directory-level atomic finalization (`candidates/` →
`generations/`, disclosed per F-135R-1 as a new, unprecedented — though
still POSIX-atomic — primitive, with a bounded retry for the disclosed
Windows-transient-`PermissionError` caveat); an atomic, per-transition,
non-authoritative `current-rehearsal` pointer rejecting
dangling/digest-mismatched/quarantined targets; precondition/mismatch/
quarantine/idempotent-replay handling; test-only fault injection; and
one shared coordinator invoked identically from all four production
finalization entry points (`phase_complete`, `task_finish`,
`phase_report_create`, `notify_send_report`), gated behind
`PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` (disabled by default, invalid
configuration fails closed). Adds read-only
`pcae cltr migration rehearsal status` and
`pcae cltr migration rehearsal reconcile --phase-id`.

Also resolves the four findings 135Q/135R identified as Blocking
prerequisites for Stage 2 implementation: F-135P-1 (entry-point
recovery classification now correctly maps `phase_report_create`/
`notify_send_report`), F-135P-2's `EXPECTED_REPRESENTATION_DIFFERENCE`
half (wired for notification/marker/receipt candidate comparisons),
F-135P-3 (`derive_cltr` no longer crashes on non-empty commit
ownership), and F-135P-4 (one shared
`pcae.cltr.migration.disclosure.NON_AUTHORITY_DISCLOSURE` constant
replaces five independently hardcoded copies).

## Evidence and validation

- Governed phase commits: `bfb943a9` (implementation), `ec846dc0`
  (task-contract cleanup) — 34 files changed.
- Stage 2 focused tests: 28/28 passed
  (`tests/test_cltr_rehearsal_coordinator.py`).
- Combined migration suite (`tests/test_cltr_migration_*.py
  tests/test_cltr_135o_integration.py
  tests/test_cltr_rehearsal_coordinator.py`): 121/129 passed. 8
  failures are pre-existing and 135S-unrelated (a sandbox-local defect
  in `run_finalization_transaction`'s post-dispatch receipt-modeling
  step, `completed_receipt_best_effort_incomplete`), independently
  confirmed via `git stash` to reproduce identically on unmodified
  `main` before this phase's changes.
- Production CLTR combined regression (`tests/test_cltr_*.py`):
  406/414 passed; same 8 pre-existing failures.
- Affected finalization regression (`test_finalization_transaction_134e10`,
  `test_finalization_gate_enforcement`,
  `test_finalization_notification_guarantee`,
  `test_finalization_configuration_identity_cross_agent_134b3`,
  `test_phase_113v_n_notification_finalization_repair`): 112/117
  passed; 5 pre-existing failures, same root cause, confirmed via `git
  stash`.
- Notification/marker/receipt/phase-report/Architecture-Status
  regression: 1173/1183 passed; 10 pre-existing failures, same root
  cause.
- Fast Green (`python -m pytest -m "fast_green" -n auto`):
  **4391/4391 passed**, unchanged from the inherited 135P/135Q/135R
  baseline.
- `pcae health` healthy; `pcae check` passed; task memory clean; push
  check clean; runtime inspect Observed/observe/execution unavailable;
  Telegram outbound delivery configured, enabled, ready.

No baseline failure is hidden inside an aggregate count above; every
failing node ID was individually identified and independently
confirmed pre-existing via `git stash` before being excluded from this
phase's own claim of correctness. Full disposition in
`docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_IMPLEMENTATION.md` §29.

## F-135P finding dispositions (full detail in the phase document §16)

- **F-135P-1 (fixed):** `_ENTRY_POINT_RECOVERY_CLASSIFICATION` now maps
  all four entry points; regression test added.
- **F-135P-2, `EXPECTED_REPRESENTATION_DIFFERENCE` half (fixed for
  Stage 2's own comparison surface):** wired in
  `rehearsal.comparison.classify_candidate_field` for the three
  representation kinds (notification, marker, receipt) 135Q §31
  specifies. `TEMPORAL_ORDER_MISMATCH` remains disclosed-unreachable,
  per 135Q/135R's own disposition (not required by any Stage 2
  contract area).
- **F-135P-3 (fixed):** raw commit-hash strings are normalized into
  typed `CommitOwnershipEntry` values before CLTR derivation; a
  non-empty `phase_commit_ownership` no longer crashes `derive_cltr`.
- **F-135P-4 (fixed for the five Stage 1 copies):** one shared
  `disclosure.py` constant; the two additional Stage 0 copies 135R's
  F-135R-2 disclosed remain correctly out of scope.

## Disclosed scope decisions (full detail in the phase document §11, §27)

The 23-item candidate inventory is implemented as 10 stored file
artifacts (matching 135Q §7's own example directory listing exactly)
plus 13 items bound into the manifest/evidence record rather than
emitted as 23 separate files; this mapping is disclosed inside every
manifest's own `limitations` field. Comparison against the
authoritative production artifact reuses Stage 1's already-normalized
`LegacyDerivationResult` rather than independently re-parsing raw
production files a second time. Full state-based *resumption* of an
interrupted candidate is not implemented (recovery-state
*classification* is); fault-injection coverage exercises a
representative subset of 135Q §52's full boundary list, not every
individual boundary as a separately named test case. None of these
decisions weakens the safety properties 135R's contract verified:
legacy remains sole production authority; the rehearsal generation and
pointer are non-authoritative by construction; no production pointer,
marker, receipt, or notification path is touched; preconditions fail
closed before any candidate directory exists; a partial or blocked
candidate can never become `current-rehearsal`.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. The Stage 2 rehearsal generation and rehearsal pointer
remain non-authoritative. No production phase report, completion
metadata, Architecture Status, or checkpoint was created or modified
by Stage 2. No production pointer changed because of Stage 2. No
external delivery originated from Stage 2 — no Telegram or other
notification sink was invoked from any rehearsal module (confirmed by
static import-graph inspection and source-grep tests). No production
notification marker was created or modified by Stage 2. No production
receipt was created or finalized by Stage 2. No Stage 3 implementation,
authority cutover, legacy demotion, or legacy retirement occurred. No
execution capability was introduced — no subprocess, shell, socket, or
network call exists anywhere in the rehearsal package (confirmed by
test). No raw `git commit` or `git push` was used; no `--no-verify`
hook bypass; no force push. Runtime remains Observed, maximum
capability observe, execution availability unavailable throughout.

## Recommended next phase

Phase 135T — Atomic Publication Rehearsal Independent Verification
(not started). 135T must independently attack this implementation
against live source before any Stage 3 design, authority-cutover
planning, CLTR authority activation, legacy-authority demotion, or
legacy-authority retirement.
