# Phase 150J — Phase-Report Rehydration Identity Repair IV

Alias: PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR-IV.
Disposition: COMPLETE — NOT VERIFIED / BLOCKED.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED

## Canonical preflight

Entry HEAD/origin/main: 841c61e13b20132896b4b9674e4add58544364ac.
Clean main, zero outgoing commits, no held/recovery checkout, available agent
lock, expected idle post-150I task. Trust complete; consistency consistent;
150G reconciliation reconciled with two generations, completed checkpoint,
finalized receipt, mutation=false. Phase 150I is complete/pushed/current.
150J was independently derived using CPIPC parse/is_valid/compare/equals/
same_series: valid, greater than 150I, unequal, same series, no collision in
all Git subjects or repository phase evidence. Activation used governed task
transition, task update, and phase start with codex-local.

## Exact Phase 150I production diff

Historical range: 93424bea862aab27fcb2401a5e83e28481b1929a to
841c61e13b20132896b4b9674e4add58544364ac.

| File | Diff | Classification and observable impact |
|---|---|---|
| src/pcae/core/phase_reports.py | +238/-2 | Generation discovery/load/selection/history; snapshot deep-copy purity. New selector requires checkpoint and paired stored Markdown; missing checkpoints now fail closed. |
| src/pcae/commands/phase_reports.py | +49/-44 | Reconcile uses selector and stored digest; canonical receipt path/self-digest checks; global marker rotation support; consistency validates a copy. |

All production changes are lifecycle infrastructure. No HPAC/helper/foundation,
runtime/PB/POL, dependency, or normative contract delta. This IV changes zero
production source and zero normative contracts.

## Actual model and provenance boundary

Discovery glob is '*-<safe phase ID>.json'. Each JSON/Markdown pair is checked
for symlinks, direct report-directory containment, parse/schema validity, and
matching title/phase ID. `PhaseReport.validate()` checks presence, status, and
schema; it does not authenticate promotion or recompute full trust completeness.

Terminal selection compares stored Markdown SHA-256 and semantic JSON snapshot
to caller-supplied checkpoint fields. Status/step strings, creation chronology,
pushed-state claims, zero outgoing claims, and source-revision prefix membership
are additional checks. No repository commit existence/ancestry lookup,
certification extraction lookup, or authenticated checkpoint-origin check runs.
The CLI loads a plain canonical-path JSON checkpoint and rejects symlinks.

Historical selection accepts pending_push, non-pushed state, an earlier embedded
timestamp, and a commit set contained in terminal commits. These are all mutable
self-declarations. Empty commit sets pass subset validation. Historical Markdown
content has no certified digest binding and can carry unrelated technical content.

Thus the actual flow is paired structure -> self-declared role -> digest/snapshot
agreement with plain checkpoint -> timestamp/commit-set comparisons -> receipt
self-digest and phase/logical-ID/path checks -> reconciliation. This establishes
consistency, but does not establish authenticated lifecycle origin under the
requested forgery threat model.

Checkpoint semantics: completed transaction snapshot/current selector; historical
pending checkpoint selection is rejected. Finalization saves plain JSON atomically
and records extraction/view/rendering digests. The reconciler does not validate
those recorded certification links. Terminal ambiguity correctly fails closed.

Notification semantics: global latest marker rotates; receipt is durable per logical
delivery. Missing marker can be legitimate for older phases. The receipt is checked
for self-digest, phase, finalized state, logical ID, and canonical path, but it is
not rebound to the selected report's digest/snapshot/evidence. Legacy unbound
markers are still considered already_dispatched. Malformed marker JSON becomes
absent. These legacy behaviors must not be represented as proof of provenance.

## Blocking findings

F1 — Forged historical generation accepted. In a copied real 150G fixture, add a
pending report whose summary is an invented technical conclusion, commits=[],
source_revision='not-a-repository-commit', and created_at=2000. Selector accepts
it as a second historical generation and CLI returns reconciled. No governed
promotion occurred. This directly violates the historical provenance criterion.

F2 — Forged report/checkpoint accepted as terminal and reconciled. Replace copied
terminal JSON/Markdown with invented conclusion and nonexistent ffffffff commit;
recompute public hashes into copied checkpoint; empty the earlier commit set.
Original finalized receipt remains byte-unchanged. Selector chooses the forged
terminal and CLI returns reconciled. Checkpoint matching alone becomes the trust
root; matching public hashes do not prove lifecycle legitimacy.

F3 — Full trust completeness is not recomputed. A copied terminal claiming complete
with empty tests/governance/commits and absent source revision is selected after
checkpoint hash synchronization, even though assess_completeness rejects it.
Reconciler trusts the stored report_completeness field.

F4 — latest.json containing [] is silently accepted. The selector checks same-phase
pointer consistency only for dictionary roots. Malformed JSON text conflicts, but
a structurally wrong JSON root does not.

F5 — Unbound same-phase marker with authority=true and no digest/snapshot is treated
as already_dispatched. The arbitrary authority field is not consumed, but identity
absence is not rejected. This is inherited compatibility, not newly authenticated
notification linkage. A forged certification evidence_id and wrong checkpoint
phase_name also do not block selection.

Production repair is required for F1/F2/F3. No production repair was attempted.

## Real 150G inventory and preservation

| Role | Path suffix | JSON SHA-256 | Markdown SHA-256 |
|---|---|---|---|
| Historical pending | 20260922-203915-150G | 5509cb71fab2ad6bc0f6474fda3bb08bea2ead17a8c2ddd2d8c96ff25a5a3c12 | da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551 |
| Terminal complete | 20260922-210046-150G | deafa34cd8d4c7802def8445308b502c9c93603fdc622e1b28bae79a5ed5651d | 5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1 |

Paths are under .pcae/phase-reports, timestamps are 2026-09-22T20:39:15.634476Z
and 2026-09-22T21:00:46.220209Z. Source revisions are 4b56c18f and 2969be8e;
historical commits are 31ebe985/40efd807/4b56c18f; terminal adds 3300cd81/2969be8e.
Snapshots e847581a476f7640a542f5dcb048675626be2abbe30166f77a50803363fd5238 and
232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8.

Checkpoint .pcae/finalization-transactions/150G.json SHA-256:
d0bbbb3e2719352ce2f54e3b63f10d16bf739671b00ceb441dd82d06d8e327da.
Receipt ed1ac26782164d4f443356bdf99a7aa57e96a45b56e139745bd82c202b18d23e,
SHA-256 057a4539d89d0c4aceb55dde87857f508b36ff87cb7b47a424088304a51e4881.
Both bind actual terminal lifecycle evidence. Tracked 150G completion metadata
in a6d475ef confirms terminal state; no completion metadata was rewritten.
Global latest report and notification pointer now name 150I from its normal
completion; those are rotating pointers rather than immutable 150G artifacts.
Phase 150H's archived hashes independently match both report pairs. Actual
canonical artifacts were read only; all attacks used disposable test copies.

## Attack matrix

Pass means security expectation met; Fail means reproduced defect.

| Attack | Expected | Observed | Result / invariant |
|---|---|---|---|
| Extra promoted-looking pending file | reject unauthenticated origin | accepted historical and reconciled | Fail F1 / origin |
| Forged digest metadata | reject without certification provenance | coordinated report/checkpoint accepted | Fail F2 / hash wall |
| Forged generation ordinal | no selection authority | unsupported schema rejected | Pass |
| Manipulated mtime | same terminal | same terminal | Pass |
| Lexical filename manipulation | same terminal | same terminal | Pass |
| Forged latest pointer | conflict | mismatching same-phase pair conflicts | Pass |
| Stale latest pointer | conflict | pending pointer conflicts | Pass |
| Symlink JSON/Markdown | conflict | both rejected | Pass |
| Traversal phase ID | reject | no terminal selected | Pass |
| Historical copy from other phase | reject | phase mismatch rejected | Pass |
| Same ID, wrong technical content | reject provenance | pending arbitrary summary accepted | Fail F1 |
| Valid digest, wrong provenance | reject | invented terminal accepted | Fail F2 |
| Checkpoint points to historical pending | reject | trust-complete requirement rejects | Pass |
| Notification arbitrary digest | conflict | payload_conflict | Pass |
| Missing terminal | conflict | missing terminal | Pass |
| Two terminal candidates | conflict | ambiguity rejects | Pass |
| Metadata/source points nowhere | reject | historical metadata ignored | Fail F1 |
| Historical claims complete | reject unbound terminal | rejected | Pass |
| Notification claims authority/unbound identity | no authority; reject unbound proof | already_dispatched without binding | Fail F5 |
| Malformed generation-set state | conflict | malformed terminal rejected; [] latest ignored | Mixed F4 |

## Independent tests, audit, compatibility

Fresh suite tests behavior against isolated real artifacts; it imports no Phase
150I test helpers. Finding tests preserve executable defect witnesses and explicitly
assert the unsafe observed outcome. Passing pytest does not imply security IV
success. Single generation (historical deleted), two generations, and three
generations are supported structurally. Three-generation acceptance lacks origin
proof. Missing checkpoint fails closed; no optional-checkpoint backward compatibility
is proved. No migration was performed or recommended as an assumed requirement.

Phase 150I tests are mostly behavioral but construct their own reports/checkpoints
and treat matching hashes as provenance. Forgery coverage targets extra complete
generations; it omits forged pending history and coordinated report/checkpoint
replacement. The older-complete checkpoint test passes because another unbound
complete report remains, not because the checkpoint is authenticated. Source and
fixed-digest tests prove scope/real artifact identity only. Two Phase 150H marker
assertions hardcode global marker rotation to 150H and fail after legitimate 150I
notification; they are baseline-preexisting and are preserved without repair.

Fresh suite: 35 passed. Combined required lifecycle selection: 416 passed / 2 failed;
both failures are the historical Phase 150H moving-marker assertions. Both exact
nodes also fail at fixed entry commit 841c61e13b20132896b4b9674e4add58544364ac
in detached worktree /private/tmp/pcae-150j-baseline.rDzKHh with copied canonical
artifact fixtures (2 failed). An additional finalization, notification, push,
post-push and repository-transition selection passed all 154 tests. Thus the
selected lifecycle regressions total 570 passed / 2 baseline-preexisting failures.
The first Fast Green attempt against e9fad74a was correctly rejected with
"HEAD moved during baseline capture" after governed task closure created
5f193983. No rejected result is used as attribution evidence. A fresh run holds
the new candidate HEAD fixed until both isolated collections finish.
The next canonical attribution produced artifact
`.pcae/fast-green-attribution/f762d4be09892077acb1d8a2c1634bf61bd668fc75941116017fdab824fc52d2.json`
with one additional shell-audit test failure. It is retained, not suppressed.
`TestAuditPersistence::test_verify_detects_tampered_record` passed in isolated
reruns at both entry and candidate. Its first sorted audit record is not
necessarily a deny record, so assigning allow can leave content unchanged.
Neither its source nor shell-gate source changed in this IV. Canonical attribution
is rerun with the supported bounded `--rerun-node` option for this exact node;
only the command's resulting classification is accepted.
Final canonical attribution PASS: baseline 841c61e13b20132896b4b9674e4add58544364ac,
candidate 5f1939836c4ee964c246dee615178ba4038c1f8a, artifact
`.pcae/fast-green-attribution/c734e000752eb7ce37e6c64efb994a2b1432d1c732185f375de5e37a980df020.json`.
Both runs have 359 raw failures and 9 errors; candidate failures are baseline
pre-existing except the closed, predicted not-yet-pushed HEAD assertion.
`attributable_failures: []`; `excluded_environment_failures: []`. The prior
shell-audit candidate-only failure did not recur; no test was changed or suppressed.
Trust command still reports complete and consistency still
reports consistent for real 150I; these do not refute the adversarial findings.

## Governed lifecycle closure

Task finish closed the IV task in commit 5f193983. Its early report attempt was
quarantined; no incomplete report was notified. Same-phase finalization bookkeeping
then transitioned to idle through the governed task lifecycle. Completion metadata
explicitly names the fresh Phase 150J evidence and preserves the blocked result.
The normal pending-push ceremony accepted only push-state blockers; the governed
push of e9fad74a, 5f193983, 7e9e6b88 and 2023fc3b succeeded. Fetch verified zero
outgoing commits; health/check/coherence and push readiness passed, with only
pre-existing task-memory warnings. Final pushed-state metadata/report closure is
bookkeeping only. No production or contract path changed. The remote reported
its configured main/PR-rule bypass; no operator hook bypass or force option was
used. Historical 150G artifacts remain byte-identical.
Normal post-push completion promoted `20261004-172223-150J` with complete trust,
accepted transition, completed finalization transaction and certified Telegram
summary/document delivery. The transaction reported the existing independent
rendering-stage byte-divergence limitation, not a certification failure.
Trust: Phase 150J complete, repair_required=false. Consistency: consistent,
source revision 2023fc3be44b2301d40ce8b32524622ba1b7056b, report digest
e9ae3888942f14c36b92d3d39051d143154dc41209f26fd02e4635260dde6321,
snapshot 37e5f4a5dbd8be229b1725aeac7dbd88b2d6de3550ca82e7d483c57baf3e8ad0.
150J reconcile: reconciled, 2 generations, already_dispatched marker, completed
checkpoint, finalized receipt, mutation=false. 150G reconcile: reconciled,
2 generations, rotated marker/not_dispatched, completed checkpoint, finalized
receipt, mutation=false. Report completeness does not mean the repaired security
properties passed this independent verification.

## Final disposition

COMPLETE — NOT VERIFIED / BLOCKED. Recommend a narrow lifecycle provenance repair
that authenticates pending promotion and terminal certification links, validates
full trust, binds receipts to selected evidence, and rejects malformed pointer
roots. Determine whether existing governed evidence provides the primitive; if
not, adjudicate the missing metadata contract before implementation.

Recognition-core IV remains on hold. N-16-5 OPEN; N-16-6/N-16-7 untouched.
Runtime Observed / observe / unavailable. No helper admission, step 9-prime,
foundation, PB/runtime/POL, host/deployment, or product closure action.

HASH CONSISTENCY != PROVENANCE.
FILE LOCATION != TRUSTED ORIGIN.
STRUCTURALLY VALID OBJECT != TRUSTED CANONICAL STATE.
