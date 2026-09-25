# Phase 150I — Phase-Report Rehydration Identity Repair

Canonical Phase ID: `150I`

Alias: **PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR**

Status: **IMPLEMENTATION COMPLETE; GOVERNED FINALIZATION IN PROGRESS**

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`

## 1. Preflight and defect reconstruction

At entry, `HEAD == origin/main == 93424bea862aab27fcb2401a5e83e28481b1929a`,
the worktree was clean, `origin/main..HEAD == 0`, the active task was the
expected idle post-150H placeholder, and governance health/coherence passed.
`150I` was independently derived with `pcae.core.phase_id`: valid, ordered
after `150H`, same series, unequal, and collision-free.

The pre-repair state reproduced Phase 150H exactly:

- report trust: complete/trusted;
- report consistency: consistent;
- `phase-report reconcile --phase-id 150G`: conflict;
- two promoted generations;
- completed checkpoint and finalized receipt;
- checkpoint identity reported as conflicting with the selected report.

The old reconciler selected the first phase-matching JSON from a reverse
filename sort and re-rendered it with `compute_report_digest(report)`. That
combined two defects: filename order was acting as a terminal-generation
selector, and JSON rehydration could not reproduce certified Markdown bytes
because `canonical_report_content` is intentionally absent from persisted
JSON. Phase 150G's stored terminal Markdown hashes to `5b954816...`; lossy
re-rendering produced `59dda6c6...`.

## 2. Terminal-generation rule

The repaired rule uses the completed finalization checkpoint as the current
architecture's terminal lifecycle provenance. A terminal candidate must be a
paired, non-symlink versioned JSON/Markdown generation and must match both:

1. the checkpoint's SHA-256 of the actual stored certified Markdown bytes; and
2. the checkpoint's semantic `finalization_snapshot_id` recomputed from the
   persisted JSON.

Exactly one candidate must match. It must also be trust-complete, pushed,
have zero outgoing commits, have creation chronology enclosed by the
checkpoint transaction (accounting for checkpoint second precision), and—if
present—bind its source revision to its phase commit inventory. A current
`latest.*` pair naming the same phase must be byte-identical to that selected
generation. Ambiguity, absence, malformed identity, symlink substitution,
missing siblings, or a mismatched current pointer fails closed.

Filename order, filesystem mtime, directory iteration, caller-selected report
paths, fabricated ordinals, digest magnitude, and notification-marker
preference have no selection role.

## 3. Historical-generation semantics

The current lifecycle explicitly creates a `pending_push` generation before
the post-push complete generation. Such an earlier generation remains valid
historical evidence only when its creation precedes the terminal generation
and its commit inventory is a subset of the terminal commit inventory. It is
never authority and never a terminal candidate. An extra complete generation
without checkpoint binding is rejected; duplicated checkpoint-matching
candidates are ambiguous and fail closed.

For Phase 150G:

| Role | Generation | Stored Markdown digest | Snapshot | Disposition |
|---|---|---|---|---|
| Historical | `20260922-203915-150G` | `da5a678c...` | `e847581a...` | preserved `pending_push` evidence |
| Terminal | `20260922-210046-150G` | `5b954816...` | `232104b6...` | uniquely checkpoint-bound complete generation |

Neither generation was edited or deleted.

## 4. Checkpoint, notification, and receipt semantics

The current finalization transaction writes its checkpoint around the one
terminal promotion/dispatch adapter call. Under this architecture the
completed checkpoint is the terminal identity, not a mutable pointer expected
to follow arbitrary later report regeneration. A checkpoint attempting to
select the earlier pending generation, or an older unbound complete
generation, fails closed.

`.last-notified.json` is a global latest-notification idempotency pointer. It
records the generation actually sent while that phase is latest, then
legitimately rotates when a later phase is notified. Its absence for an older
phase is therefore not evidence that delivery did not occur. Reconciliation
accepts historical delivery only when the checkpoint-selected report itself
records successful notification and the checkpoint binds a finalized,
self-digest-valid receipt for the same phase and logical delivery ID from the
canonical receipt store. A same-phase marker with a different report/snapshot
pair remains a conflict. The marker and receipt remain evidence, not
authority.

## 5. Rehydration and reconciliation behavior

`resolve_terminal_promoted_generation()` inventories all phase generations,
hashes the stored Markdown bytes, rehydrates the JSON for its semantic
snapshot, classifies governed pending history, and returns either one
checkpoint-bound terminal generation or explicit blockers. The reconciler
uses that stored identity instead of re-rendering JSON. Its public result now
also reports historical count/paths, rejected paths, and the terminal
selection provenance while retaining the existing status schema.

Consistency inspection now validates a deep copy. Snapshot computation also
deep-copies nested report data before removing non-identity diagnostics. Both
operations are read-only with respect to the rehydrated report object.

## 6. Adversarial verification

The fresh Phase 150I suite covers:

- real Phase 150G before/after behavior and byte preservation;
- single- and two-generation happy paths;
- mtime and lexical filename manipulation;
- extra complete generations and duplicate terminal candidates;
- forged generation ordinals;
- forged latest pointers;
- checkpoints targeting pending or older unbound complete generations;
- missing/malformed terminal generations and malformed checkpoint digests;
- JSON/Markdown disagreement and symlink substitution;
- arbitrary historical notification-marker linkage;
- read-only snapshot computation;
- unchanged HPAC/helper/foundation/runtime/PB/contracts boundaries.

Fresh focused result: **177 passed**. The broader selected lifecycle run
produced **582 passed / 3 failed**. All three failures reproduce unchanged at
the entry commit `93424bea` in an isolated worktree, so they are
baseline-pre-existing and not candidate-attributable.

The real post-repair result is:

- trust: complete/trusted;
- consistency: consistent;
- reconcile 150G: **reconciled**;
- promoted generations: 2;
- historical generations: 1;
- report digest: `5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1`;
- snapshot: `232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8`;
- mutation/redispatch: false.

Fast Green and final governed commit/push evidence are recorded during
terminal lifecycle completion.

## 7. Scope and preserved state

- No Phase 150G artifact content was rewritten or deleted.
- No checkpoint, marker, receipt, or latest pointer was manually mutated.
- No recognition-core, protected-admin-writer, helper, foundation, runtime,
  PB, POL-005, or normative contract file changed.
- Runtime remains Observed / observe / unavailable.
- N-16-5 remains OPEN; N-16-6 and N-16-7 remain untouched.
- Recognition-core IV remains on hold.

`HASH CONSISTENCY != PROVENANCE`. Digest equality identifies content; terminal
status derives from governed lifecycle provenance plus unambiguous linkage.

## 8. Recommended next phase

Independent verification of the Phase 150I phase-report rehydration identity
repair. The recognition-core IV must not resume until that lifecycle repair IV
completes successfully. No successor is activated by this phase.
