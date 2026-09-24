# Phase 150H Complete — Phase 150G Report Identity Reconciliation

Canonical Phase ID: `150H`

Alias: **PCAE-LIFECYCLE-PHASE-150G-REPORT-IDENTITY-RECONCILIATION**

Status: **COMPLETE — NOT RECONCILED / BLOCKED**.

## Outcome

This governed phase reconstructed every Phase 150G promoted generation and
classified the identity conflict as **Class B — MULTI-GENERATION EXPECTED,
RECONCILER DEFECT**. Generation A is the legitimate pre-push
`pending_push` artifact. Generation B is the legitimate terminal pushed
artifact. The stored terminal Markdown digest
`5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1`
already matches both the finalization checkpoint and ordinary-completion
notification marker.

The read-only reconciler loads Generation B's persisted JSON into a
`PhaseReport` and re-renders it. The persisted representation omits
`canonical_report_content`, so the reconstructed Markdown loses the canonical
report-consistency section and hashes to `59dda6c6…`. The apparent linkage
conflict is therefore produced by lossy lifecycle rehydration. Consistency
inspection also mutates the rehydrated object's Fast Green lifecycle metadata
in memory, producing a different snapshot identity during inspection.

No established governed operation can rotate or update the completed 150G
checkpoint/marker, and the existing `phase-report reconcile` operation is
explicitly read-only. Manual digest substitution, deletion, re-notification,
or pointer editing would falsify history. Accordingly, this phase made no 150G
linkage mutation and recommends a dedicated lifecycle-infrastructure repair.

## Evidence and validation

- Fresh Phase 150H suite: 13 passed; the combined Phase 150H and
  report/notification lifecycle regression selection passed 185 tests.
- Fresh governed Fast Green: baseline `a6d475ef474514533e0144952d4f2f89374c3d2e`,
  candidate `4d4dafc314224e3f120ce25fff0157692435e89d`,
  `attributable_failures: []`.
- Fast Green artifact:
  `.pcae/fast-green-attribution/8e674a1f9ba3ce75f97d6a70b40d7ac6e27831be2f431a866292b49ba766ab53.json`.
- Full evidence:
  `docs/PHASE_150H_PCAE_LIFECYCLE_PHASE_150G_REPORT_IDENTITY_RECONCILIATION.md`.

## Preserved boundaries

Zero `src/pcae/**` changes and zero `docs/contracts/**` changes. Phase 150G's
technical result remains unchanged: shared recognition core implemented,
helper admission not wired, helper step 9-prime undefined, foundation blocker
unchanged, and N-16-5 OPEN. N-16-6 and N-16-7 are untouched. Runtime remains
Observed / observe / unavailable. Phase 150H / recognition-core IV was NOT
begun by this phase.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`

`HASH CONSISTENCY != PROVENANCE`

## Recommended next phase

After independently deriving its CPIPC identity, open a dedicated
`PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR` phase. Do not begin
the recognition-core IV until the 150G reconciliation command is clean.
