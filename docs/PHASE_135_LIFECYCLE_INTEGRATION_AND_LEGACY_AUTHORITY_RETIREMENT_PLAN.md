# Phase 135H — Lifecycle Integration and Legacy Authority Retirement Plan

**Phase type:** architecture and migration planning only  
**Runtime:** Observed / observe / execution unavailable  
**Production readiness verdict:** **NOT READY FOR IMPLEMENTATION — production
schema, canonicalization, versioning, adapter, and cutover contracts are not
yet frozen.**  
**Non-goal:** implement or integrate CLTR; modify production finalization,
reports, metadata, promotion, notification, checkpoints, markers, receipts,
PFN-001, PFR-001, or CLTR-001; transfer authority; introduce execution.

## 0. Method and source boundary

This plan was re-derived from the Track 135 architecture, contract,
verification, formal model, incident investigation, prototype plan,
prototype, and independent verification (135A–135G); the Track 134 lifecycle
contract and whole-lifecycle verification; and current production source.
Prior reports were used as requirement provenance and cross-checks, not as
proof of current behavior.

The current source pass confirmed four production entry points call the one
`run_finalization_transaction()` boundary: `pcae phase complete`, `pcae task
finish`, `pcae phase-report create`, and `pcae notify send-report`. Each still
builds a legacy `PhaseReport`, gate, and callback. The transaction persists a
mutable per-phase checkpoint, runs pre-promotion evidence/view/rendering
stages, then invokes legacy promotion/dispatch. `promote_artifact()` still
writes versioned and canonical files separately with plain `write_text()`;
marker decisions still precede the shared transaction; receipt modeling still
follows dispatch; and commit contamination checking still fails open for an
unresolvable hash. No production module imports `pcae.cltr_prototype`.

Normative precedence for migration is: CLTR-001 v1.0; the verified 135D
37-invariant behavioral model; PFN-001 and PFR-001 for their unchanged narrow
domains; a future production CLTR schema/versioning contract; then
implementation. Prototype encodings and APIs are evidence, never production
contract by inheritance.

## 1. Current authority inventory

The classifications below describe current production behavior. “Canonical”
means the current system treats the artifact as authoritative for the named
fact; it does not mean CLTR-conformant future authority.

| Representation or fact | Current owner/source | Current classification | Why / migration consequence |
|---|---|---|---|
| Canonical report | `.pcae/phase-reports/latest.json` and `latest.md`, built from `PhaseReport` | Canonical authority for report content and reported completion; duplicated across two files | PFR-001 remains authoritative for content, but lifecycle status must become CLTR-derived. The pair cannot remain the authority or be published non-atomically. |
| Completion metadata | `.pcae/phase-completion-metadata.json` | Duplicated authority for identity, commits, status, successor, and evidence summaries | Becomes a CLTR derivative/adapter. Explicit fields remain inputs before certification; post-certification status and identity come from CLTR. |
| Architecture Status | Sealed `report.architecture_status`, initially generated from `PROJECT_STATUS.md` plus structured projected completion | Derived authority with independent narrative inference at generation time | It is safely sealed today, but independently parses completed/current/planned facts. It must become a pure CLTR projection; narrative parsing becomes compatibility-only. |
| Immutable snapshot | `report_digest` + `finalization_snapshot_id` and report-bound evidence | Canonical certification evidence for current transaction | Extend into CLTR evidence bindings. Do not rewrite historical snapshots or pretend they were CLTR records. |
| Checkpoint | `.pcae/finalization-transactions/<phase_id>.json` | Canonical transaction/resume authority, mutable in place by atomic replace | Replace with CLTR in-progress event/state persistence. Retain a read-only adapter during migration. |
| Promotion | `ArtifactState` plus `promote_artifact()` writes | Canonical authority for artifact publication; separate state machine | Remains a real operation, but its occurrence/result becomes a CLTR event. `latest.*` become derivatives behind one generation pointer. |
| Notification | Dispatch result on the in-memory/promoted report, certification result, and sink result | Duplicated/event authority | Delivery attempt/result becomes an append-only CLTR event bound to PFN-001 payload identity; sink evidence remains external evidence. |
| Marker | `.pcae/phase-reports/.last-notified.json` | Canonical terminal/idempotency authority for all four entry points | Central retirement target. It becomes a regenerable compatibility cache and may never decide CLTR resume state after cutover. |
| Receipt | `.pcae/delivery-receipts/` immutable receipts | Canonical authority for the narrow physical-delivery outcome | Retain as native event evidence, bind to `transition_id`; never elevate receipt presence to whole-transition authority. |
| Task state | `tasks/active/`, `tasks/done/`, task contract status, and command-selected latest task | Canonical task-workflow authority; inferred lifecycle linkage | Task workflow remains its own domain. Completion linkage and task/phase transition identity become explicit CLTR references; filename/title inference retires. |
| Transaction state | Mutable transaction checkpoint status plus callback result | Canonical transition-progress authority, duplicated with marker/report state | CLTR spine state and append-only events replace it. Legacy checkpoint status is comparison input during shadow mode only. |
| Git evidence | Explicit `phase_commits`, live Git revision/push checks, and commit-subject contamination scan | Canonical declarations + verification evidence; some inferred evidence | CLTR owns declarations and three-outcome classification. Git remains the verification source; subjects are signals only; unresolved hashes may never count as verified. |
| Planned successor | Structured report/metadata recommendation plus narrative extraction from `PROJECT_STATUS.md` | Duplicated authority/input | Human/governance proposal remains input. One machine-readable CLTR field owns the certified recommendation and projected Planned state. |
| Repository clean/pushed/ahead state | Live Git commands at certification/check time | Verification authority | Remains live V-role evidence. CLTR binds the observed value and revision/time; it never claims the historical value remains currently true. |

The current model is safe through cooperating checks, but authority is
distributed: report and metadata repeat status and identity; Architecture
Status parses lifecycle prose; checkpoint and marker independently drive
resume/terminal decisions; receipts cover delivery only; and Git declarations
and verification are not represented by one transition identity.

## 2. Legacy authority retirement

| Legacy authority | Current owner | Future owner | Migration and retirement | Compatibility duration | Rollback implication |
|---|---|---|---|---|---|
| Report lifecycle status/identity | `PhaseReport` / `latest.*` | CLTR S-role fields; report remains PFR-001 derivative | Add explicit CLTR binding, shadow compare, then prohibit report-to-state reconstruction | Read forever; dual-write only through verified shadow/cutover window | Pre-cutover, ignore shadow CLTR. Post-cutover, regenerate report from CLTR; never restore report authority. |
| Completion metadata lifecycle fields | Metadata file/command inputs | CLTR identity, evidence, and classification fields | Treat pre-certification declarations as inputs; emit post-certification metadata from sealed CLTR | Read forever; write adapter until all supported consumers migrate | Roll back consumer routing before authority cutover; after cutover only adapter rollback is allowed. |
| Architecture Status current/planned/completed | `PROJECT_STATUS.md` narrative parser + structured projection | CLTR current-record lookup and projected state | Build semantic adapter; shadow byte/semantic compare; stop narrative inference for native records | Narrative parser permanent for historical artifacts, temporary for native records | Regenerate derivative from CLTR; do not restore prose as native authority. |
| Checkpoint state | Finalization transaction file | CLTR in-progress record/event log | One-way import of active legacy checkpoint at cutover barrier; then CLTR-only state writes | Read adapter through rollback window; historical files immutable | Before first CLTR-only irreversible event, route back to legacy. Afterward, forward recovery/supersession only. |
| Marker terminal state | Notification marker | CLTR NOTIFIED / NOTIFIED_UNCONFIRMED plus notification events | In shadow, compare only. At cutover, marker is emitted from CLTR and removed from decision paths | Cache writer may remain for older clients for a declared release window | Marker corruption/missing marker is derivative repair, never authority rollback. |
| Entry-point-specific resume checks | Four commands | Shared CLTR state resolver | Route all entry points through one resolver; delete native marker/checkpoint inference after verified deprecation | One release/window behind a compatibility adapter, not two active authorities | Feature-routing rollback only before authority cutover; later failures use CLTR recovery. |
| Mutable latest inspection | Readers of `latest.md/json` | Atomic generation pointer to CLTR-bound derivatives | Publish one immutable generation and atomically switch one pointer | Human-facing files may remain indefinitely as derivatives | Re-point to prior complete generation only if no later irreversible event used the new generation; otherwise supersede. |
| Recent Git/subject inference | Contamination scan and any legacy consumers | CLTR declaration + repository-bound verifier result | Fail closed to `unverifiable`; retain subject parsing only as contamination evidence | Historical adapter only | A verifier outage downgrades conformance; it never re-enables inference. |
| Planned-successor prose | Current-phase narrative | CLTR `recommended_successor` input/binding | Freeze explicit structured value at certification; narrative display derives from it | Historical narrative reader permanent; native narrative extraction retires at cutover | Correct via a new governed transition/supersession, never edit a sealed record. |

Retirement is fact-scoped, not file-scoped. A file can remain permanently for
human compatibility while every authoritative interpretation of it retires.
No historical artifact is rewritten, backfilled silently, or labeled native.

## 3. Production integration boundary

- **Prototype boundary:** `src/pcae/cltr_prototype/`, its CLI, fixtures, and
  `.pcae/cltr-prototypes/`. It remains disposable and isolated. Production
  must not import it wholesale or treat its schema version as production.
- **Production boundary:** a future production CLTR model/store/verifier and
  one orchestration boundary used by all four entry points. The boundary
  accepts explicit normalized inputs, persists state before side effects,
  invokes existing report/promotion/notification/receipt adapters, and records
  observations afterward.
- **Authority boundary:** authority transfers per lifecycle fact only at a
  certified cutover gate. Before it, production artifacts are authoritative
  and CLTR is shadow evidence. After it, CLTR is sole lifecycle authority and
  legacy artifacts are derivatives, narrow event evidence, or compatibility.
- **Compatibility boundary:** adapters may read historical artifacts or emit
  old formats. They may not infer a native record's state, repair a record,
  strengthen `unverifiable`, or write two authorities.
- **Rollback boundary:** reversible until a CLTR-authoritative transition
  performs its first irreversible publication/dispatch event. Beyond that
  point rollback means forward recovery, quarantine, or supersession—not
  restoring a legacy authority over the same transition.

## 4. Shadow integration

Shadow mode must use real production inputs but remain observational:

1. The legacy path creates its normalized trial report, gate, projected state,
   commit declarations, and evidence references as today.
2. A production-shaped CLTR shadow builder consumes an immutable copy of those
   explicit inputs. It does not scan titles, filenames, recent Git, task state,
   markers, or latest files to fill gaps.
3. The legacy transaction remains authoritative and alone performs mutation,
   promotion, notification, marker, and receipt writes.
4. Shadow CLTR state advances only from mirrored, observed legacy outcomes.
   It never invokes an adapter or feeds a decision back into production.
5. A verifier compares CLTR facts against every relevant representation at
   defined barriers and writes a separate verification result/quarantine
   recommendation outside all canonical paths.
6. Every mismatch is classified by fact, representation, transition ID,
   generation, severity, and evidence availability. “Unsupported” is
   `unverifiable`, never conformant.

Shadow exit requires a statistically and semantically adequate run set: every
one of the 16 permitted transitions represented where production-reachable;
all failure/retry classes exercised synthetically or through hermetic fault
injection; all four entry points; simple/dotted/multi-dotted/corrective IDs;
enabled/disabled/failed/uncertain notification; exact/conflicting replay; and
zero unexplained Blocking mismatch across a predeclared consecutive window.
The future contract phase must set the window quantitatively.

## 5. Cross-representation verification

Comparison occurs at five barriers:

| Barrier | Compared facts | Failure handling |
|---|---|---|
| Pre-certification | explicit identity, prior/projected state, commit ownership, evidence references, schema/version | Block future cutover eligibility; legacy production continues in shadow mode |
| Post-certification / pre-publication | sealed content, record/report/metadata/snapshot digests, 37 invariants | Quarantine shadow generation; no production mutation caused by shadow |
| Post-promotion | generation pointer, report/metadata transition ID and digest, all-or-nothing visibility | Blocking mixed-generation finding; stop cutover campaign and retain old authority |
| Post-notification | notification identity, payload digest, attempt/result, marker cache, receipt linkage | Reconcile uncertainty; never blind retry; flag marker/receipt drift for derivative repair |
| Terminal/resume | terminal state, retry class, supersession/quarantine overlays, final revision | Reject conflicting replay; exact replay resolves; no legacy inference may strengthen state |

In shadow mode, mismatch handling is report + quarantine of the shadow record,
never mutation of production. During guarded cutover, any Blocking mismatch
before irreversible effects fails closed and invokes routing rollback. A
Blocking mismatch after promotion/notification preserves all evidence,
quarantines the record/current pointer, disables further automated transitions
for that identity, and requires forward repair or supersession. Warnings are
reserved for disclosed missing historical semantics, presentation-only drift,
or live V-role facts that changed after their bound observation.

## 6. Legacy compatibility

| Surface | Strategy | Duration / retirement order |
|---|---|---|
| Reports | Permanent PFR-001-compatible derivative; explicit transition/generation binding added only under a future contract | Permanent format support; authority retires at cutover |
| Metadata | Deterministic derivative for existing tools; pre-certification declaration adapter | Temporary native-write adapter, permanent historical reader |
| Architecture Status | CLTR-derived for native records; narrative parser only for pre-CLTR history | Native narrative inference retires before authority cutover; historical parser remains |
| Markers | Regenerable notification cache containing transition/digest binding | Emit for a declared compatibility window; decision authority retires at cutover |
| Receipts | Preserve current immutable receipt model; add explicit CLTR binding through versioned adapter/contract | Permanent narrow event evidence |
| Historical artifacts | Read-only verification adapters with explicit confidence/missing-field disclosure | Permanent; never migrated in place |

Retirement order is: freeze adapters; verify historical reads; introduce shadow
CLTR; make native derivatives CLTR-bindable; atomically publish bound
generations; centralize resume; cut over read authority; cut over write
authority; demote marker/checkpoint/latest inspection; then remove redundant
native inference. An adapter may compare semantic fields or exact bytes as its
contract requires, but cannot use byte equality where serialization is allowed
to differ or semantic equivalence where an exact digest is promised.

## 7. Authority cutover strategy

### 7.1 Prerequisites

Cutover is prohibited until all of the following are independently verified:

- production schema/canonicalization/versioning contract frozen and verified;
- 37 behavioral invariants normatively cross-walked to schema fields;
- all fifteen representation adapters specified, implemented, and tested;
- atomic immutable-generation publication and single-pointer recovery proven;
- strict identity, unknown-version/field, digest, containment, and deep-
  immutability protections proven adversarially;
- commit ownership cannot become `verified` without repository/branch/revision
  binding and hash resolvability;
- notification uncertainty and NOTIFIED_UNCONFIRMED reconciliation proven;
- shadow exit criteria met with zero unexplained Blocking mismatch;
- rollback drill and independent cutover review completed;
- PFN-001 and PFR-001 compatibility demonstrated without amendment unless a
  separate governed process explicitly decides otherwise.

### 7.2 Stages and gates

1. **Contract only:** freeze schema, serialization, versioning, adapters, and
   failure envelope. No production code.
2. **Production model, inert:** implement model/store/verifier behind no entry
   point. Independent verification required.
3. **Shadow write:** build and verify shadow records from explicit copies of
   production inputs; legacy remains authoritative.
4. **Shadow read:** tools can display comparison results, never make decisions.
5. **Atomic derivative pilot:** publish CLTR-bound generations to a disjoint
   pilot namespace; compare with legacy latest files.
6. **Read-authority cutover:** selected internal readers use CLTR; all writes
   still legacy; instant routing rollback remains available.
7. **Write-authority canary:** one explicitly bounded transition class/entry
   point writes CLTR as authority and emits legacy derivatives. All other
   paths remain legacy; cross-authority concurrency is prohibited per phase.
8. **Full authority cutover:** all four entry points use the shared CLTR
   transaction; marker/checkpoint/latest inspection becomes compatibility.
9. **Retirement:** remove native legacy inference after the declared window and
   an independent whole-lifecycle verification.

The certification gate precedes all irreversible effects. The atomic pointer
switch is irreversible only with respect to readers that acted on it; physical
notification dispatch is inherently irreversible. A cutover control-plane
flag may route *new* transitions, but may never split one transition across
authorities or move an already-authoritative transition backward.

## 8. Atomic publication

The production design should adopt **immutable generation directory + atomic
single current-pointer switch**, with the CLTR record as the authority and
report/metadata/Architecture Status as files inside or bound to the same
generation. This is preferred over independent file replacement because it
provides one visibility atom while retaining human-facing derivatives.

Required ordering:

1. persist in-progress CLTR state/event durably;
2. generate all derivatives from the sealed record and bound evidence;
3. verify record digest, derivative digests, manifest allow-list, identities,
   versions, and all applicable invariants;
4. fsync files and generation directory as required by the storage contract;
5. atomically publish the immutable generation;
6. durably record promotion success in the CLTR event history;
7. atomically switch one pointer containing transition ID, generation ID,
   record digest, and manifest digest;
8. only then begin notification; record attempt before send and observation
   after send;
9. emit marker cache and receipt binding from CLTR state.

Readers validate the pointer and manifest before use and either see the prior
complete generation or the new complete generation. Pointer loss/staleness is
recovered from verified immutable history. A complete orphan generation is
safe and recoverable; a partial staging directory is invisible and removable.
Cross-device rename, symlink traversal, concurrent writer, disk-full, fsync,
pointer-switch, and crash-at-every-boundary cases require explicit contract and
fault-injection coverage.

## 9. Resume strategy

- **Retry before certification:** create a new proposal/attempt from explicit
  inputs; failed pre-certification content is not authoritative.
- **Exact replay:** resolve to the existing transition and current state; no
  re-promotion or re-dispatch.
- **Conflicting replay:** reject and preserve both proposed/conflicting
  evidence; never overwrite.
- **Crash recovery:** read the last verified durable CLTR event and immutable
  generation, not artifact presence. Reconcile an orphan generation/pointer
  deterministically.
- **Promotion failure:** preserve CERTIFIED evidence, classify FAILED_POST_CERT,
  inspect visibility, and recover through a new governed action; do not blindly
  re-run PROMOTING.
- **Notification failure:** retry the same PROMOTED record with a new attempt
  identity only when delivery failure is known.
- **Notification uncertainty:** enter NOTIFIED_UNCONFIRMED, observe sink/marker/
  receipt evidence, then T12 self-loop or upgrade; never blindly resend.
- **Receipt/marker failure after successful delivery:** repair only the
  derivative/evidence binding; never repeat delivery.
- **Quarantined/superseded:** no normal spine continuation; superseded replay
  resolves to the successor.

The current `completed_receipt_best_effort_incomplete` transaction status maps
to NOTIFIED_UNCONFIRMED/terminal-partial policy, not to a retryable whole
transaction. This closes the current defense-in-depth dependence on four
earlier marker checks.

## 10. Rollback strategy

Rollback is stage-specific:

- **Prototype rollback:** delete/disable only disposable prototype data and
  CLI exposure. It has no production effect and is not a production fallback.
- **Shadow rollback:** stop shadow generation/comparison and preserve shadow
  evidence. Legacy production continues unchanged.
- **Production integration rollback before authority transfer:** disable inert
  or shadow hooks and pilot readers; no lifecycle data conversion is needed.
- **Read-authority rollback:** route readers to legacy only while legacy remains
  the certified writer and no CLTR-only fact has influenced an irreversible
  action.
- **Authority cutover rollback before first irreversible event:** atomically
  abort the CLTR attempt, retain its failed evidence, and route a *new* attempt
  to legacy under the cutover contract.
- **After CLTR publication or notification:** never make legacy authoritative
  for that transition. Freeze new work for the identity, recover the pointer or
  reconcile notification, quarantine if integrity is uncertain, and supersede
  with a new transition when correction is required.
- **Full-system rollback:** may route only future, not-yet-proposed transitions
  to the prior version. Mixed authority for the same phase/transition is
  forbidden.

Every rollback drill must prove evidence preservation, no duplicate external
delivery, deterministic current-pointer selection, and explicit operator
visibility of which authority owns every in-flight transition.

## 11. Production verification strategy

1. **Independent model verification:** re-derive schema/model/store behavior
   without trusting implementation tests; reproduce every 135G hazard.
2. **Shadow verification:** compare every supported representation at the five
   barriers, retain mismatch evidence, and enforce the declared exit window.
3. **Cutover verification:** before each stage, independently verify authority
   routing, atomicity, rollback readiness, no split-brain transition, all four
   entry points, PFN/PFR compatibility, runtime posture, and repository state.
4. **Rollback verification:** crash/fault drills before and after each boundary;
   demonstrate which actions are reversible and that post-effect recovery is
   forward-only.
5. **Whole-lifecycle verification:** after full cutover but before legacy
   retirement, re-run every transition/retry/replay/failure class and inspect
   source for any remaining report/metadata/marker/checkpoint/latest inference.

Verification results are V-role artifacts, not authority. A verifier reports,
quarantines through an explicit governed event, or blocks a not-yet-
irreversible transition; it never repairs sealed content silently.

## 12. Carried-forward non-blocking findings

### NB-1 — comparator semantic breadth

Production requires an adapter contract for all fifteen 135D representation
kinds. Each field is designated exact identity/digest comparison, normalized
semantic comparison, observational comparison, presentation-only, or
unsupported. Report/metadata/pointer digests require byte-exact checks where
the schema promises canonical bytes; Architecture Status, notification result,
receipt, and historical formats require field-aware semantics. Unsupported
versions/fields are preserved and produce `unverifiable` or `conflicting` as
specified, never conformant. Cutover cannot occur until every native
representation has full semantics; historical adapters may remain partial
only with explicit confidence and missing-field evidence.

### NB-2 — CLI disclosure consistency

The prototype inconsistency remains prototype-only and does not justify
production code in this phase. Production does require one standardized,
versioned diagnostic envelope for text/JSON success, validation failure,
parser failure after command dispatch, unsupported version, missing record,
and quarantine. Machine output must always state authority mode
(`shadow`/`authoritative`/`compatibility`), mutation status, schema/contract
version, transition identity when known, conformance, and limitations. Native
argument-parser usage errors may keep platform syntax, but any record-aware
error must use the envelope. This contract must be frozen with the schema.

### NB-3 — invariant inventory documentation

The verified behavioral inventory is **37**. CLTR-001 contains 34 unique IDs
despite prose saying 33; 135D contains 37 after ORDER-5/6/7 despite prose saying
36; the prototype implements 37. This is not editorial debt that may wait past
schema freeze: the production schema contract must include a normative 37-ID
crosswalk and explicitly record the frozen-source arithmetic discrepancy
without amending CLTR-001 or inventing new semantics. Any eventual editorial
correction to frozen documents requires separate governance.

## 13. Inherited production hazards from 135G

| Hazard | Production exposure | Contract and implementation protection | Adversarial/cutover acceptance | Rollback and compatibility |
|---|---|---|---|---|
| B-1 traversal/symlink escape | Record, manifest, pointer, adapter, marker, receipt paths | Safe opaque IDs; resolved-root containment; reject symlinks/absolute/separators; no caller path composition | Traversal, Unicode lookalike, symlink swap, pre-existing link, TOCTOU tests; zero write outside root | Block before visibility; historical unsafe names read only through isolated mapping |
| B-2 non-atomic publication | Current `latest.md/json` pair and future multi-file generation | Staging + full verification + fsync contract + atomic generation publish and pointer switch | Crash/fault at every write/sync/rename; readers see exactly old/new; recovery deterministic | Re-point only when no irreversible consumer acted; otherwise forward recovery |
| B-3 overlay/terminal violations | Resume paths could continue failed/quarantined/superseded states | One transition matrix; shared guards; certified-content/state prerequisites; no generic setter | All 14 forbidden transitions, overlay continuation, FAILED_PRE quarantine, replay tests | Reject/route new proposal; adapters may not weaken terminality |
| B-4 notification reconciliation | Current transaction relies on marker interception after best-effort receipt failure | NOTIFIED_UNCONFIRMED is resume-terminal; T12 observe/self-loop/upgrade; T14 explicit partial closure | Crash-before/during/after send, marker failure, receipt failure, ambiguous sink result; zero duplicate send | Forward reconcile only; legacy marker is evidence/cache, never permission to resend |
| B-5 unknown versions/fields | Readers could default/drop unknown semantics | Version allow-list; unknown contract reject; compatible unknown fields preserve without interpretation; no read-rewrite loss | Future/unknown/malformed version and required/optional-field evolution corpus | Older reader fails safely; compatibility adapter declares confidence and preservation |
| B-6 identity/digest mismatch | Cross-phase/generation substitution across all derivatives | Exact transition/phase/repository/branch binding; manifest + record + derivative digests | Wrong-phase, wrong-generation, swapped report/metadata/receipt/marker, mixed pointer | Quarantine; never auto-repair sealed record; regenerate only proven derivative |
| B-7 shallow immutability | Nested mappings/event histories could mutate sealed authority | Deep immutable model; append-only events; predecessor validation; digest over all authoritative fields | Nested mutation, aliasing, impossible predecessor, concurrent append tests | Supersede rather than mutate; historical adapters return immutable views |
| B-8 fabricated commit verification | Current contamination checker silently skips unresolvable hashes | Three outcomes; `verified` requires hash resolution and repository/branch/source-revision binding | Fabricated, ambiguous prefix, wrong repo/branch/revision, rewritten/unreachable history, verifier outage | Downgrade to `unverifiable`; never fall back to subject/recent history; policy decides whether certification blocks |

Prototype protection is not reusable proof. Every row requires a production
contract clause, independent implementation review, and fresh adversarial
evidence before shadow or cutover gates can pass.

## 14. Production schema prerequisite

The prerequisite is independently confirmed. CLTR-001 §6.1 explicitly freezes
semantic content, not wire fields; §15 does not freeze canonicalization; and
§27 governs the relationship between schema and contract without supplying a
schema. Current production contains no CLTR model/store/verifier outside the
prototype. Therefore production definitions are **not frozen** for exact wire
fields, types/requiredness, state-dependent presence, transition/enum values,
canonical serialization, ordering, null/absence semantics, digest coverage,
manifest layout, supported versions, unknown-field preservation, or adapter
schemas.

The next phase must be **135I — Production CLTR Schema, Canonicalization, and
Versioning Contract Freeze**. It must freeze those items, the 37-invariant
field crosswalk, diagnostic envelope, manifest/pointer transaction contract,
adapter comparison classes, compatibility matrix, and certified-content
conditional requirements. It must not implement them. An independent schema
contract verification phase must precede any production implementation plan.

## 15. Certified-content provenance

The semantic rule is **explicitly required by CLTR-001 and formalized by
135D**, not a new prototype semantic: CLTR-001 requires `certified_state`,
sealed report/metadata/evidence bindings, immutable CERTIFIED-or-later history,
and forbids canonical derivatives from uncertified authority; 135D §7 states
which S/R/E facts become immutable at T3 and that CERTIFIED is promotion-
eligible only after they are bound. The prototype's concrete aggregate
`certified_content` structure and shared guard are implementation hardening of
that rule.

Production schema wording must make the existing semantics mechanically
explicit: every CERTIFIED-or-later spine or overlay state requires the complete
sealed certified-content field set and digest; pre-CERTIFIED states must not
claim that binding. This is a schema-level conditional expression of existing
requirements, not a CLTR-001 amendment.

## 16. Planned-successor authority investigation

The 135G canonical `latest.json` contains both:

- limitation: `current phase section has no explicit 'Recommended next phase'
  sentence -- no planned phase disclosed`; and
- `planned: ["135H - Lifecycle Integration and Legacy Authority Retirement
  Plan"]`, with `planned_phase_ids: ["135H"]`.

They came from the **same sealed Architecture Status build**, not different
snapshots or metadata. Its source provenance identifies one read of
`PROJECT_STATUS.md`, repository revision `da3fbc8c...`, and a lifecycle
projection `completed:135G`. The base parser searches the bounded Current
Phase section with a line-anchored recommendation regex. In that revision the
words “Recommended next” followed “Runtime remains ...” mid-line (then wrapped
before `phase:`), so narrative extraction found none and correctly disclosed
the limitation. During projected completion, the structured
`PhaseReport.recommended_next_phase` value—`135H ...`—explicitly outranked
pre-transition prose and populated Planned. Completion metadata and the
canonical hand-authored completion report also carried 135H, but neither was
needed to produce this projected Planned entry.

Classification: harmless, deterministic, and correctly disclosed for 135G;
not a timing race, metadata disagreement, mixed generation, or separate
post-certification read. It nevertheless proves planned-successor authority
currently has multiple sources: human/governance intent is copied into
completion metadata, structured report state, canonical completion narrative,
and PROJECT_STATUS prose, while Architecture Status has both narrative
extraction and a structured projection override.

Future rule: the human/governance decision supplies one explicit machine-
readable `recommended_successor` input. At certification CLTR binds it (or
explicit null), validates that it is not completed/active/self, and owns the
projected Planned fact. Report, metadata, Architecture Status, completion
narrative, and project memory render from that binding. Narrative extraction
remains presentation compatibility for historical artifacts only and may
never activate a successor; the successor becomes active only through its own
governed record.

## 17. Readiness assessment and successor phases

**Assessment: architecture ready; production implementation not ready.** The
authority targets, migration boundaries, rollback point, and staged strategy
are sufficiently defined to freeze the production data contract. The missing
wire/version/adapter/atomic-publication contracts are Blocking prerequisites,
not implementation details.

Recommended sequence:

1. **135I — Production CLTR Schema, Canonicalization, and Versioning Contract
   Freeze** (next; contract only).
2. **135J — Production CLTR Schema Contract Independent Verification.**
3. **135K — Production CLTR Integration Implementation Plan.**
4. **135L — Inert Production Model and Store Implementation.**
5. **135M — Inert Model/Store Independent Verification.**
6. **135N — Production Shadow Integration.**
7. **135O — Shadow Integration Independent Verification and Cutover Readiness.**
8. Later explicitly approved canary/cutover/retirement phases, each separated
   by independent verification.

This phase authorizes none of them and stops at the 135H plan.

## 18. Decision and no-go confirmation

Adopt staged migration with production remaining authoritative through shadow
verification, immutable-generation atomic publication, fact-scoped retirement,
and a one-way authority boundary after irreversible effects. Select 135I as
the smallest next phase because no production wire contract exists.

No CLTR implementation or integration occurred. No source or test file, final
transaction, report, metadata, Architecture Status, promotion, notification,
checkpoint, marker, receipt, PFN-001, PFR-001, CLTR-001, runtime capability, or
historical artifact changed. Runtime remains Observed / observe / execution
unavailable.
