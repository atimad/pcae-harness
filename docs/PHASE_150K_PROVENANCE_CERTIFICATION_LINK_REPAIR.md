# Phase 150K — Lifecycle Provenance/Certification-Link Repair

Alias: PCAE-LIFECYCLE-PHASE-REPORT-PROVENANCE-CERTIFICATION-LINK-REPAIR.
Disposition: COMPLETE — NOT VERIFIED / BLOCKED (architectural stop; no repair).

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED

## 1. Preflight and scope

Entry HEAD = origin/main = c90254a2648e4afb263373fd4aff2afb48946e2e;
clean main, zero outgoing commits, expected idle post-150J task, agent lock
available. No held/recovery checkout or unrelated main-local commits. Historical
worktrees/branches were inspected only and never merged/cherry-picked.
Trust: 150J complete, repair_required=false. Consistency: consistent, source
2023fc3b, digest e9ae3888..., snapshot 37e5f4a5.... Reconcile 150G: reconciled,
2 generations, marker not_dispatched (rotated global pointer), checkpoint
completed, receipt finalized, mutation=false. Phase 150J is canonically complete
and pushed with its blocked technical conclusion unchanged.

150K was derived from parsed canonical 150J: valid, compare(150J,150K)=less,
equal=false, same_series=true. No collision in all Git subjects or docs/tasks.
Governed TODO entry, task transition/update and codex-local phase start activated
exactly this phase. No successor, helper or recognition-core IV was activated.

All 35 Phase 150J tests reproduced before production changes (0.26s), including
forged pending history, coordinated terminal/checkpoint with unchanged receipt,
incomplete trust accepted as complete, and latest.json=[] acceptance. Production
has not changed, so the witnesses remain reproducible after the architectural stop.

## 2. Current trust graph

This graph classifies actual persisted edges, not the names used by APIs:

| Node / creator / moment | Edge to another node | Edge classification |
|---|---|---|
| Repository commit / governed commit+push | tracked completion metadata, task and evidence blobs | lifecycle provenance for committed bytes within the verified repository history; not an unrecorded promotion event |
| Completion metadata / primary operator before/after closure | phase, commit list, tests, summary, pushed state | descriptive; no per-generation payload/role/predecessor certificate |
| Task completion / governed transition | task ID, title, completion state | lifecycle provenance for committed task state; generation binding missing |
| Phase completion / CLI transition validator | trial report and intended canonical promotion | in-process validation; durable authenticated transition-to-generation edge missing |
| Versioned report / write_phase_report + promote_artifact | paired JSON/Markdown; current/latest copies | cryptographic identity/structure only on re-read; source_state=CERTIFIED is supplied as enum |
| Pending report / allow_pending_push path | later terminal commits/timestamp | descriptive subset/chronology only; no checkpoint or predecessor certificate |
| Terminal checkpoint / run_finalization_transaction | report Markdown digest and semantic snapshot | cryptographic identity only; plain ignored JSON is not an independent root |
| Checkpoint | evidence_id, extraction/view/rendering digests | cryptographic identity of deterministic derivations; origin/event proof missing |
| CanonicalEngineeringEvidence / _capture_evidence(report) | supplied report fields | descriptive provenance strings; pure report-to-evidence derivation, not independent evidence capture |
| Receipt / post-dispatch synthetic delivery model | operator rendering, delivery plan/logical ID | cryptographic identity and immutable-through-store evidence; no authenticated promotion/task predecessor |
| Notification marker / successful notification callback | phase/report/snapshot/purpose | descriptive delivery/idempotency evidence; rotates globally; legacy unbound entries accepted |
| latest.json/latest.md / promotion | selected current report bytes | cache-like rotating copies, not independent provenance; nonobject JSON is currently ignored by selector |
| Promoted-generation index | every generation and predecessor/role | missing |
| Provenance history / append_provenance_event | event summary/task/branch/time | descriptive ignored JSON; no report digest/transition certificate/signature |
| Shadow CLTR observation | terminal transition values | advisory/non-blocking, missing independent ownership proof; not adopted as a root here |

```text
verified repository history --> metadata/task/evidence bytes
                           -X-> per-generation lifecycle certificate (missing)

report --> deterministic evidence --> extraction --> view --> rendering
   ^                                                        |
   |                                                        v
checkpoint -- hash/snapshot equality -------------------- receipt
   |
   +--> terminal selection --> latest copies

pending report -- timestamp/commit subset --> historical classification
notification marker -- phase/hash claims --> dispatch bookkeeping
```

The hash graph is useful consistency evidence but does not terminate in an
independent persisted root proving every governed generation event. No signing
or authenticated issuance primitive is supplied by these legacy paths.

## 3. Exact source and reachable behavior

Inspected current phase_reports.py loader/selector/write/latest/marker/trust/
finalization/snapshot paths; commands/phase_reports.py trust/consistency/reconcile;
finalization_transaction.py pre-promotion, checkpoint/resume, receipt and shadow
paths; canonical_artifact_promotion.py; repository_transition_integration.py;
notification_certification.py; canonical_engineering_evidence.py;
evidence_extraction.py; delivery_receipt.py; CLTR migration configuration.

write_phase_report() checks PhaseReport.validate(), then calls promote_artifact()
with source_state=CERTIFIED. The promotion API checks the enum and writes the
versioned/latest content; it does not persist a generation certificate or chain
index. The pending_push branch calls that writer while the final gate is not
finalizable, outside the terminal transaction, and suppresses notification.

_build_pre_promotion_artifacts() is a deterministic derivation of supplied report
content. Fresh tests derive identical valid extraction/rendering digests twice
from an invented conclusion. Adding checks for these hashes alone cannot prove
that the supplied report was genuinely issued by the lifecycle.

Checkpoint saves are atomic plain JSON. Resume/terminal selection trusts matching
report_digest and finalization_snapshot_id. Full PhaseReport.assess_completeness()
is not re-run by the selector; a stored complete claim can survive missing tests,
governance and commits. Receipt reconciliation verifies its self-digest, phase,
logical ID and canonical storage path, not a selected-generation issuance root.

Runtime artifact directories and provenance-history.json are ignored and have no
tracked files. a6d475ef's committed Phase 150G metadata has no generation index,
terminal payload certificate or predecessor relationship. The structured metadata
commits 3300cd81/a6d475ef and source revisions 4b56c18f/2969be8e establish the
implementation/closure timeline, not every report issuance event.

Phase 150H and 150J committed inventories independently record the known 150G
bytes. This permits auditing those specific historical bytes; it does NOT define
a generic normative certificate format binding arbitrary historical generations
to their task/event/predecessor. Parsing ad-hoc prose as such a certificate would
be a new contract, not reuse of an established validation primitive. No 150G
digest, filename, body, generation count or phase special case is implemented.

## 4. Architectural blocker and missing minimum relationship

An available candidate root is verified repository history for committed lifecycle
records. The missing edge is an explicitly governed, durably anchored issuance
record binding generation payload identity, phase/task/transition identity, role
and predecessor (or root), with a defined terminal transition and receipt relation.
The current formats do not carry that record for every historical generation.

Adding self-hashed adjacent JSON, ordinals, event strings or caller-supplied seals
would simply move the forgery. Joining extraction and receipt hashes would
strengthen consistency but leave origin circular/recomputable. Promoting shadow
CLTR or unrelated infrastructure into production authority is outside this scope.

Therefore STOP before production repair under request sections 7, 17 and 31:
historical provenance cannot generically be reconstructed from existing structured
records; schema/provenance contract and legacy acceptance/migration semantics need
separate adjudication. No schema or contract was changed, no migration performed,
and no historical provenance retroactively fabricated.

The missing link above is a required relationship, not an adopted schema, trust
root selection, new authority, or implementation freeze. A successor architecture
phase must choose and independently verify its root and bootstrap/migration rules.

## 5. Current rules and P1-P10 disposition

| Rule | Current behavior | Required property / disposition |
|---|---|---|
| P1 generation ancestry | no verified predecessor/root | BLOCKED |
| P2 terminal proof | local checkpoint hashes and self-asserted complete/pushed fields | BLOCKED |
| P3 historical proof | pending claim, timestamp, commit subset | BLOCKED |
| P4 checkpoint binding | reproducible identity, no issuance root | BLOCKED |
| P5 receipt replay | phase/logical/self-digest checks; no selected-generation provenance | BLOCKED; unchanged receipt exploit reproduced |
| P6 notification | marker cannot select terminal, but unbound marker accepted | authority separation preserved; linkage incomplete |
| P7 latest | same-phase pair mismatch fails; [] root ignored | BLOCKED malformed state |
| P8 mandatory limbs | stored complete trusted by selector | BLOCKED |
| P9 ambiguity | duplicate matching terminal candidates rejected | existing defense passes |
| P10 extra unlinked artifacts | invented pending artifact accepted as history | BLOCKED |

No repaired proof rules are claimed. Existing CLI statuses remain mechanically
unchanged; public schema evolution and error taxonomy were not improvised.

## 6. Fresh attack matrix

Pass = existing security expectation met; Fail = defect reproduced; Unproved =
architectural stop prevents a provenance claim. Synthetic identity 181Q is used
for fresh selector tests; 150J independently reproduces real CLI behavior.

| # | Attack / case | Expected | Observed | Invariant / result |
|---|---|---|---|---|
| 1 | forged pending history | reject unissued | accepted | P3/P10 Fail |
| 2 | copy from another phase | reject | identity mismatch | P1 Pass |
| 3 | fabricated same-phase report | reject | accepted pending | P3 Fail |
| 4 | coordinated terminal/checkpoint | reject | invented terminal selected | P2/P4 Fail |
| 5 | forged terminal, legitimate unchanged receipt | reject | 150J CLI reconciled | P5 Fail |
| 6 | forged terminal, copied receipt reference | no selector root from receipt | selector accepts; real copied-byte CLI witness in 150J; no generic provenance proved | P5 Fail |
| 7 | forged completion metadata claim | reject | selector ignores adjacent claim | P1/P2 Fail |
| 8 | incomplete provenance chain | not trusted | selected without chain | P1/P8 Fail |
| 9 | missing mandatory trust edge | not complete | selected | P8 Fail |
| 10 | malformed latest [] | explicit failure | ignored | P7 Fail |
| 11 | stale same-phase latest | conflict | conflict | P7 Pass |
| 12 | forged same-phase latest pair | conflict | conflict | P7 Pass |
| 13 | digest-valid / origin-invalid | reject | accepted | P1 Fail |
| 14 | mtime manipulation | no selection influence | unchanged terminal | P2 Pass |
| 15 | filename ordering | no selection influence | unchanged terminal | P2 Pass |
| 16 | forged top-level ordinal | reject | schema rejection | P2 Pass |
| 17 | symlink artifact | reject | rejected | P1 Pass |
| 18 | traversal phase | reject | no terminal | P1 Pass |
| 19 | duplicate terminal candidates | fail closed | ambiguity rejected | P9 Pass |
| 20 | broken predecessor metadata | reject | ignored/accepted | P1 Fail |
| 21 | cycle metadata | reject | ignored/accepted | P1 Fail |
| 22 | future/nonexistent predecessor | reject | ignored/accepted | P1 Fail |
| 23 | honest historical pending | preserve valid evidence | actual 150G retained; structural synthetic acceptance | P3 Unproved generically |
| 24 | honest terminal | preserve | actual 150G reconciled | existing compatibility Pass; root criterion unproved |
| 25 | three-generation chain | provenance-validated | unissued third generation accepted | P1/P3 Fail |
| 26 | historical wrong task | reject | task metadata ignored | P1 Fail |
| 27 | historical wrong phase | reject | rejected | P1 Pass |
| 28 | notification marker replay/unbound | never authority; reject unbound proof | 150J already_dispatched | P6 linkage Fail |
| 29 | receipt replay | reject unrelated generation | unchanged receipt accepted by real CLI | P5 Fail |
| 30 | checkpoint replay/coordinated claims | reject unissued terminal | local claims sufficient | P4 Fail |

Receipt-reference synthetic tests establish selector non-consumption, not CLI
acceptance of arbitrary invalid receipts. Actual unchanged/copy receipt behavior
is established by the real-artifact 150J CLI fixture. No accepted forged fixture
is promoted into canonical repository storage.

## 7. Honest 150G, compatibility and preservation

Reconcile remains clean/read-only with both original generations. Single-generation,
two-generation and no-notification selector structures still work, but no authenticated
origin is inferred from that structural success. Absent checkpoint currently fails
closed. Older formats have no generic mandatory issuance/predecessor record; no
optional-checkpoint or all-legacy-provenance compatibility guarantee is made.
No mass rewriting, migration, new third 150G report, marker/checkpoint edit or
historical deletion was performed. Global latest/notification pointers may advance
only through THIS phase's normal lifecycle, not manual 150G repair.

| Artifact | SHA-256 preserved |
|---|---|
| A JSON 20260922-203915-150G | 5509cb71fab2ad6bc0f6474fda3bb08bea2ead17a8c2ddd2d8c96ff25a5a3c12 |
| A Markdown | da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551 |
| B JSON 20260922-210046-150G | deafa34cd8d4c7802def8445308b502c9c93603fdc622e1b28bae79a5ed5651d |
| B Markdown | 5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1 |
| completed checkpoint | d0bbbb3e2719352ce2f54e3b63f10d16bf739671b00ceb441dd82d06d8e327da |
| finalized receipt | 057a4539d89d0c4aceb55dde87857f508b36ff87cb7b47a424088304a51e4881 |

Receipt records synthetic operator-rendering delivery only; immutable through
DeliveryReceiptStore.save once finalized, but not an authenticated terminal
issuance certificate. Its operator rendering c5340b47... differs intentionally
from the legacy Markdown digest 5b954816...; no equality substitution was made.

## 8. Tests, failure attribution and lifecycle

Fresh Phase 150K: 37 tests. Combined fresh K + unchanged historical J: 72 passed.
Broader report/trust/consistency/reconcile/rehydration/finalization/checkpoint/
receipt/notification/promotion/task/filename/transition/extraction selection:
870 passed / 4 failed / 2 collection warnings (44.06s). All four failed nodes
reproduced at fixed entry c90254a2 in detached worktree
/private/tmp/pcae-150k-baseline.UKlk3Y with canonical artifact copies: two stale
150H global-marker assertions and two old receipt 'no active integration except
transaction' assertions. Neither test nor production was repaired/suppressed.

Initial fresh-suite construction issues (unsupported ordinal passed into the
fixture renderer; no-notification fixture Markdown digest not updated) were
corrected in new test fixture setup, preserving the tested security properties.
One regression invocation used an absent guessed receipt filename and collected
zero tests; the complete selection above used the actual canonical receipt files.

Fresh canonical Fast Green and final lifecycle outputs are appended during
governed closure; prior Phase 150J attribution is not reused.

## 9. Disposition and successor

COMPLETE — NOT VERIFIED / BLOCKED. Production repair STOPPED because the independent
generation-issuance/root relationship and historical compatibility contract are
missing. Post-fix exploit rejection is NOT claimed; no fix exists in this phase.
Recommend a separately governed lifecycle provenance-root, generation-certificate
and historical acceptance/migration architecture adjudication. Its phase ID must
be derived at future preflight. No architecture/schema freeze or successor begun.
Implementation and independent verification must follow an adequate adjudication;
the implementation-IV successor is not yet applicable to this blocked phase.

Recognition-core IV remains on hold pending independent verification of this
lifecycle provenance repair. Runtime Observed / observe / unavailable. N-16-5
OPEN; N-16-6/N-16-7 untouched. No HPAC, helper admission, step 9-prime, foundation,
runtime/PB/POL-005, contract, host/deployment, release/publication or external runtime
effect delta. No production source changed.

HASH CONSISTENCY != PROVENANCE.
FILE LOCATION != TRUSTED ORIGIN.
STRUCTURALLY VALID OBJECT != TRUSTED CANONICAL STATE.
receipt = evidence != authority.
