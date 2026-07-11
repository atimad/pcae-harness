# Phase 134E.8.1 — Duplicate Terminal Delivery and Mixed-Evidence Report Repair

## Outcome

The first trust-complete Phase 134E.8 report remains authoritative. The later
report was a newly generated, invalid ordinary duplicate, not a replay. It was
produced by the task-finish finalization path after the canonical Markdown had
been replaced for 134E.8 while `.pcae/phase-completion-metadata.json` still
contained 134E.7V evidence in every material field except phase identity.

No external notification was sent during this investigation. Both historical
reports and all archived report builds remain unmodified.

## Safety and preserved evidence

Ordinary pytest execution clears external notification configuration unless an
explicit live-test override is supplied (Phase 134B.1/134B.2). All probes in
this phase used direct pure functions, temporary marker paths, or filesystem
sinks. The inactive `delivery_pipeline.py` and `delivery_receipt.py` modules
remain disconnected from `commands.phase`, `commands.task`, notification
dispatch, and production lifecycle authority.

Preserved source artifacts:

| UTC time | Artifact | SHA-256 | Classification |
|---|---|---|---|
| 14:37:46 | `.pcae/phase-reports/20260711-143746-134E.8.md` | `8c90e7b6ef9eb7089e7841ab719c0792bbad75b64072bb25151193f855e5d5dd` | correct evidence, partial pre-final build |
| 14:38:17 | `.pcae/phase-reports/20260711-143817-134E.8.md` | `e247d3a30ef0f106b218b00dbf6486f30e5c5636bb410018ef7419f10` | first trusted terminal report; canonical authority |
| 14:40:17 | `.pcae/phase-reports/20260711-144017-134E.8.md` | `a282ece862bca3b9565b45baebc8d0b3600e439d5fa20fd383370ce79fe27775` | invalid mixed-evidence ordinary duplicate |

The matching timestamped JSON artifacts, canonical completion Markdown,
completion metadata, provenance history, task contract, and current
`.last-notified.json` marker are retained. The active notification system has
no historical physical-attempt ledger, so exact Telegram request/response
reconstruction is unavailable; the two externally observed messages plus the
artifact/provenance chronology establish two logical ordinary sends.

## Chronology and exact paths

1. Phase 134E.8 implementation commit `160f91bf` landed with its correct task
   evidence.
2. A pre-final build at 14:37:46 was partial.
3. `pcae phase complete` built the trust-complete report at 14:38:17 from the
   correct 134E.8 evidence and dispatched it. Provenance records the associated
   `phase_completed` event at 14:38:24. Its ordinary idempotency identity was
   `(134E.8, 160f91bf)`.
4. The lifecycle-close task hand-authored commit `de506304` at 14:39:55. Its
   diff changed only the three metadata identity fields from 134E.7V to 134E.8;
   summary, files, tests, No-Go, and next-phase fields remained 134E.7V.
5. `pcae task finish --commit` ran the second finalization path. At 14:40:17 it
   called `finalize_phase_report()`, which loaded the newly correct canonical
   134E.8 Markdown, generated a fresh Architecture Status, and combined those
   with the stale structured metadata. The report was newly generated; it was
   not a replay of either earlier payload.
6. The shared marker considered `(134E.8, de506304)` different from
   `(134E.8, 160f91bf)`, certified another ordinary notification, dispatched
   it, and overwrote the single marker. Provenance records the second
   `phase_completed` event at 14:40:17.

## Field-by-field comparison

| Field | Trusted 14:38:17 report | Invalid 14:40:17 report | Source of invalid field |
|---|---|---|---|
| Phase identity/title/status | 134E.8 / Architecture Status repair / completed | same | three hand-changed metadata identity fields plus canonical title |
| Summary | full 134E.8 repair | short correct 134E.8 summary | task-finish command summary/provenance |
| Architecture Status | absent in first generated payload | corrected 134E.8/134E.8V status | fresh `build_architecture_status()` call |
| Files changed | 10 | 9 | stale 134E.7V completion metadata |
| Commits | `160f91bf` | `de506304`, `160f91bf`, `836f1e96`, `8f616d4a`, `56ddcae6` | task-finish/git fallback and lifecycle commit |
| Tests | 51 + 16 + 914 + 4390/4390 | 134E.7/7V: 48, 110, 1216, 4389/4390 | stale 134E.7V metadata |
| Governance | correct 134E.8 final state | mechanically current state | mutable completion metadata/live reconciliation |
| No-Go | denies activation; says no 134E.8V | says no Architecture Status repair and no 134E.8 work | stale 134E.7V metadata |
| Recommended next | 134E.8V | 134E.8 (self) | stale 134E.7V metadata |
| Completeness/consistency | complete/consistent | incorrectly complete/consistent | presence-oriented trust plus optional-overlap consistency checks |
| Logical notification key | phase + `160f91bf` | phase + `de506304` | shared last-notified marker |

## Root causes

Two BLOCKING defects compounded:

1. Ordinary terminal delivery identity was `(phase_id, commit)`. A bookkeeping
   commit therefore created a second logical completion for the same phase.
   Every dispatching call site shared the marker, but the shared invariant was
   wrong.
2. Trust validation checked required-field presence, canonical title identity,
   push state, and a few optional text overlaps. It did not reject explicit
   completed-phase denial, self-recommendation, or test evidence linked only to
   another phase. Canonical Markdown and mutable structured metadata were read
   at different times without one semantic snapshot identity.

Architecture Status inspection was not causal and remains side-effect-free.
It imports no report writer, finalizer, promotion, or dispatcher. Its fresh
generation merely made the mixed report more visibly contradictory.

## Repair

`phase_already_notified()` now defines an ordinary completion at phase scope.
A later commit cannot create another ordinary completion. Corrections and
supersessions are explicitly distinguished by `delivery_purpose`; they are not
silently treated as another ordinary send.

Successful marker writes now bind:

- phase identity;
- source commit (audit context, no longer logical identity);
- exact rendered report digest;
- deterministic finalization snapshot identity; and
- delivery purpose.

All four active dispatch call sites (`phase complete`, `task finish`, manual
`phase-report create`, and `notify send-report`) write the same bound marker.
The snapshot covers phase/title/status, summary, files, tests, governance,
commits, No-Go evidence, Architecture Status, next phase, and semantic
metadata; volatile creation/attempt/trust-display fields are excluded.

The finalization gate now calls `validate_internal_report_coherence()`. It
fails closed when a completed phase is explicitly denied by No-Go evidence,
when a completed phase recommends itself, when phase-linked tests name only
other phases in the same series, or when snapshot metadata identity disagrees
with report identity. A contradiction forces `report_completeness` to
`incomplete` and records `internal_evidence_coherence`; metadata presence can
no longer restore `complete`.

## Answers to the incident questions

1. The second report came from `pcae task finish --commit`'s
   `_finalize_task_report_and_notify()` path.
2. It was newly generated, not replayed.
3. Its summary came from the 134E.8 task-finish/provenance summary.
4. Architecture Status came from a fresh `build_architecture_status()` call.
5. Test Results came from stale 134E.7V completion metadata.
6. No-Go came from stale 134E.7V completion metadata.
7. Recommended Next Phase came from stale 134E.7V completion metadata.
8. Validation was presence-oriented and compared only selected overlaps.
9. It checked identity/metadata mechanically, not internal evidence coherence.
10. The reports represented one logical completion but had different legacy
    phase+commit marker identities.
11. This was not a transport retry; it was a second certified ordinary send.
12. It was treated as a new delivery due to the new bookkeeping commit.
13. The canonical completion Markdown was replaced before first delivery; the
    timestamped trusted payload remained immutable. The later generated latest
    report was a distinct body under the same phase identity.
14. Architecture Status generation participated only in the second build; it
    did not independently trigger regeneration or promotion.
15. `architecture-status inspect` is side-effect-free.
16. Yes. The 134E.7V metadata remained active except for three identity fields.
17. Phase completion ran once for the trusted terminal build; task-finish ran a
    second independent finalization path.
18. Yes. Task finish redispatched because the commit-qualified marker missed.
19. Before this repair any later phase could reproduce the incident.
20. Before this repair every configured adapter would have received the second
    fan-out; the repair is shared and transport-neutral.

## Correction, authority, and limitations

The 14:38:17 report is canonical. The 14:40:17 report is preserved as invalid
incident evidence and must not be used as phase authority. No corrective
external notice was sent in this phase because the operator explicitly required
avoiding further duplicates. If one is later authorized, it must use purpose
`correction`, visibly say that the earlier mixed report is invalid, and bind to
the trusted digest/snapshot.

The legacy marker is a single durable summary, not a physical-attempt ledger.
It cannot prove an exact network attempt count or atomically couple a remote
Telegram acceptance with local persistence. The repair guarantees one logical
ordinary completion across all current call sites and fails closed on payload
change; richer attempt recovery belongs to the future delivery-receipt
integration and remains inactive here.

## Validation

Focused incident/report/notification tests cover phase-level logical identity,
changed bookkeeping commits, explicit correction purpose, digest/snapshot
binding, evidence mutation, mixed phase evidence, No-Go contradiction,
self-recommendation, side-effect-free inspection, inactive Track 134 delivery
modules, and existing phase/task/Telegram behavior. Broader affected suites and
fast-green results are recorded in `PROJECT_STATUS.md`.

Runtime remains Observed, maximum capability `observe`, execution unavailable.
Phase 134E.8V was not begun.
