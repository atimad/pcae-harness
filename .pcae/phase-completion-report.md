# Phase 150J Complete — Phase-Report Rehydration Identity Repair IV

Canonical Phase ID: `150J`
Alias: PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR-IV
Status: COMPLETE — NOT VERIFIED / BLOCKED.

Phase 150I production diff independently reconstructed across 93424bea..841c61e1:
only src/pcae/core/phase_reports.py (+238/-2) and
src/pcae/commands/phase_reports.py (+49/-44). Selection/history/rehydration,
checkpoint/receipt reconciliation and read-only consistency/snapshot changes
are lifecycle scoped; no unrelated product changes.

The selector is deterministic over checkpoint digest/snapshot equality, paired
generation structure, declared state, chronology, and commit subset. It rejects
mtime/filename selection, symlinks, unmatched complete generations and ambiguity.
However, checkpoint JSON and pending-history declarations are not authenticated
against actual certification/promotion provenance. Matching hashes can therefore
be forged together.

Blocking findings:
- F1: invented pending history with arbitrary conclusion, empty commits, old
  timestamp and nonexistent source revision is accepted and reconciled.
- F2: invented terminal/report/checkpoint with public recomputed hashes and
  nonexistent commit is selected and reconciled with the original receipt.
- F3: stored complete claim with empty trust evidence is selected even though
  full completeness assessment rejects it.
- F4: latest.json with a nonobject [] root is ignored.
- F5: an unbound same-phase marker is accepted as already_dispatched; inherited
  compatibility must not be presented as authenticated notification provenance.

Checkpoint is a completed transaction snapshot/current selector; pending
historical checkpoint selection is rejected. Global notification marker rotates
and receipt records delivery evidence. Reconciler validates receipt self-digest,
phase/logical identity and path but not its selected report/evidence relationship.
Historical validity is inferred from self-declared pending state, timestamp and
commit subset, insufficient to prove governed origin. Backward compatibility is
structural for one/two/three generations; absent checkpoint fails closed. Migration
necessity is not established.

Actual Phase 150G remains clean without mutation:
- historical 20260922-203915-150G, Markdown SHA-256
  da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551;
- terminal 20260922-210046-150G, Markdown SHA-256
  5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1;
- completed checkpoint snapshot
  232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8;
- finalized receipt ed1ac26782164d4f443356bdf99a7aa57e96a45b56e139745bd82c202b18d23e;
- trust complete, consistency consistent, reconcile reconciled, mutation=false.

Fresh IV suite: 35 passed. Exploit witnesses passing means defects reproduced,
not security criteria satisfied. Combined lifecycle selection: 416 passed /
2 baseline-preexisting Phase 150H moving-marker failures; both reproduced at
fixed entry 841c61e1. No test was skipped, xfailed, deleted, or repaired.
Additional finalization, notification, push, post-push and transition tests:
154 passed; total selected regressions 570 passed / 2 baseline-preexisting failures.
Phase 150I test audit: fake complete generations are covered but forged pending
history/coordinated checkpoint replacement are omitted; source/fixed-digest checks
do not authenticate provenance. Full 20-row matrix and artifact hashes:
docs/PHASE_150J_REHYDRATION_IDENTITY_REPAIR_IV.md.

Fresh Phase 150J Fast Green baseline/candidate/artifact and final governance/push
results are recorded in structured metadata after the governed attribution run.
Canonical Fast Green PASS: baseline 841c61e1, candidate 5f193983,
artifact c734e000752eb7ce37e6c64efb994a2b1432d1c732185f375de5e37a980df020;
attributable_failures=[]; raw 359 failures / 9 errors, baseline-preexisting
plus the predicted not-yet-pushed HEAD assertion. Prior failed artifact f762d4be
is retained; isolated shell-audit reruns passed at entry and candidate, and that
candidate-only failure did not recur in final collection. No suppression or repair.
All Phase 150J commits, including final bookkeeping commits after report creation,
are available in the bounded entry..HEAD history.

This IV changes zero production source and zero normative contracts. Canonical
Phase 150G artifact bytes remain unchanged; attacks used scratch copies. No manual
checkpoint/marker/pointer mutation. Runtime Observed / observe / unavailable.
N-16-5 OPEN; N-16-6/N-16-7 untouched. Recognition-core IV remains on hold.

Recommended next phase: narrow lifecycle provenance and certification-link repair;
derive its identity at future preflight. No successor begun.

HASH CONSISTENCY != PROVENANCE
DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
