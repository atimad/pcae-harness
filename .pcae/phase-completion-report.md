# Phase 150I Complete — Phase-Report Rehydration Identity Repair

Canonical Phase ID: `150I`

Alias: **PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR**

Status: **COMPLETE — PHASE-REPORT REHYDRATION IDENTITY REPAIR IMPLEMENTED**.

Report completeness: **complete** after governed push and terminal promotion.

## Outcome

Phase 150I independently reconstructed and repaired the reusable Class B
multi-generation defect established by Phase 150H. PCAE legitimately retains
an earlier `pending_push` promoted generation and a later terminal promoted
generation. The old reconciler selected a report by caller path/latest state
and re-rendered lossy JSON, then treated a differing historical digest as a
conflict. The repair preserves every generation and reasons over trust,
generation role, chronology, and lifecycle linkage.

The deterministic terminal-generation rule requires exactly one trusted
promoted generation matching the completed finalization checkpoint's exact
stored-Markdown SHA-256 digest and semantic snapshot. It rejects symlink/path
substitution, missing or malformed artifacts, forged latest pointers,
unbound complete generations, duplicate terminal candidates, and ambiguity.
Filename order, filesystem mtime, arbitrary directory order, digest magnitude,
and untrusted generation ordinals are never selection primitives.

Earlier generations are historical only when they are governed
`pending_push` artifacts, precede the checkpoint-bound terminal generation,
and their commit set is a subset of the terminal generation's commit set.
Historical generation does not mean invalid generation; promoted generation
does not automatically mean current.

## Checkpoint, notification, and rehydration semantics

The checkpoint is immutable snapshot evidence of the report generation
certified at finalization. It selects the terminal generation only when both
its exact report digest and semantic snapshot match one trusted promoted
generation. Reconciliation never rewrites it.

The notification marker/receipt records what was actually delivered and is
evidence, not authority. A globally rotating latest-notification marker may
legitimately move to a later phase. For an older phase, reconciliation accepts
the checkpoint-selected report's successful notification only when the
canonical finalized receipt validates its digest, phase identity, logical
notification identity, and canonical receipt path. An arbitrary historical
digest or forged marker still conflicts.

Rehydration keeps all trusted generations inspectable, returns the unique
checkpoint-bound terminal generation for current state, and fails closed on
ambiguity or missing/malformed terminal evidence. Snapshot and consistency
inspection now operate on copies and do not mutate rehydrated report state.

## Real Phase 150G regression

Before this repair, `pcae phase-report reconcile --phase-id 150G` reported
`CONFLICT` despite trust being complete and consistency being consistent.
After the repair, the unchanged two-generation record reconciles cleanly:

- terminal: `20260922-210046-150G.json`;
- terminal Markdown digest:
  `5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1`;
- terminal semantic snapshot:
  `232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8`;
- historical generations: 1;
- mutation: none.

No Phase 150G report, generation, checkpoint, receipt, notification marker, or
latest/current pointer was edited, deleted, regenerated, or fabricated.

## Tests and attribution

- Focused Phase 150I + Phase 150H + phase-report lifecycle selection:
  **177 passed**.
- Broader selected lifecycle suite: **579 passed / 3 failed**; all three
  failures reproduced at the entry commit
  `93424bea862aab27fcb2401a5e83e28481b1929a` and are baseline-pre-existing.
- Canonical Fast Green: baseline
  `93424bea862aab27fcb2401a5e83e28481b1929a`, candidate
  `371bc0d0244fdd8323a160cf9ce96543de93cc28`,
  **`attributable_failures: []`**.
- Fast Green artifact:
  `.pcae/fast-green-attribution/64329546c6dab9d7e0e0156169fda8cec88431ef97aadfaf3d87316a6bc374db.json`.

Adversarial coverage includes single- and multi-generation cases, ambiguous
terminal candidates, forged promoted files, mtime and filename manipulation,
forged ordinals/latest pointers/checkpoints, unrelated historical linkage,
missing and malformed terminal content, symlink substitution, arbitrary
notification-marker linkage, historical retrieval, and the real immutable
Phase 150G record. Existing trust and consistency rejection behavior remains
enabled.

## Files and commits

Production lifecycle changes are limited to:

- `src/pcae/core/phase_reports.py`;
- `src/pcae/commands/phase_reports.py`.

Fresh/updated verification and evidence:

- `tests/test_phase_150i_phase_report_rehydration_identity_repair.py`;
- `tests/test_phase_150h_pcae_lifecycle_phase_150g_report_identity_reconciliation.py`;
- `docs/PHASE_150I_PCAE_LIFECYCLE_PHASE_REPORT_REHYDRATION_IDENTITY_REPAIR.md`;
- project/task lifecycle bookkeeping and the Phase 150I Fast Green artifact.

Governed Phase 150I commits begin with:

- `371bc0d0244fdd8323a160cf9ce96543de93cc28` — implementation and tests;
- `884e8dd82efede1d92b0a8a60cf42cca9dea1093` — Fast Green evidence;
- `a1187f1c64f404f2f8248bd6cef3c42fe1dedef2` — governed task completion;
- `59f82f851e65754b187071a3ed924b2d99bde479` — stable historical assertion.

The final metadata/report and closure commits are recorded in the promoted
structured report after governed push. Final state: pushed, clean, and
`origin/main..HEAD == 0`.

## Preserved boundaries

No HPAC recognition-core, protected-admin-writer, helper, foundation, runtime,
PB, or POL-005 behavior changed. No normative contract changed. Runtime
remains **Observed / observe / unavailable**. N-16-5 remains **OPEN**;
N-16-6 and N-16-7 are untouched. No helper admission, step 9-prime,
foundation repair, release, publication, host, deployment, or external-effect
work was begun.

`HASH CONSISTENCY != PROVENANCE`

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`

## Recommended next phase

Independently derive and execute an independent verification phase for this
Phase 150I lifecycle repair. The recognition-core IV remains on hold pending
successful independent verification of this lifecycle repair.
