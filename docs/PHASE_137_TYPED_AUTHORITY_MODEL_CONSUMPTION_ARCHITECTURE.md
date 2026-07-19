# Phase 137A: Typed Authority Model Consumption Architecture

## 1. Purpose and boundaries

Stage 3 (136A-136AW) produced the Typed Authority Model: sixteen frozen
executable schemas, sixteen typed Python models
(`src/pcae/cltr/authority/*.py`), a schema registry, a manifest,
serialization/deserialization, recursive immutability, reference
validation, and package/distribution verification. `pcae phase-report
show --latest` and a direct `git grep` of `src/pcae` (outside
`src/pcae/cltr/authority/` itself) for `pcae.cltr.authority` confirm,
again, zero hits: no production runtime, command, lifecycle,
publication, notification, recovery, compatibility, or quarantine path
currently imports the package. The model exists; nothing yet reads it.

This phase's purpose is to define the architecture governing how
existing and future PCAE components **may** read Typed Authority Model
records, before any such reading is implemented. It is an architecture
phase only:

- It does not define authority activation.
- It does not introduce runtime behavior.
- It does not modify lifecycle semantics.
- It does not implement a single consumer.
- It does not change `src/pcae/cltr/authority/*.py` or any frozen schema.

Everything below is a constraint on future work, not a description of
work performed in this phase.

## 2. Why typed models exist, why they are consumed, what they solve, what they do not

**Why typed models exist.** Prior to Stage 3, cutover-relevant facts
(authority epochs, readiness, authorization, candidates, certification,
publication, recovery) had no canonical machine-checkable
representation. Stage 3 gives each fact family a frozen JSON Schema, a
matching immutable Python model, and a manifest/registry that ties
schema identity, version, and digest together. This is the same
Schema -> Typed Model layering already established for PFR-001 phase
reports (Track 133) and canonical lifecycle transitions (Track 134):
representation is built once, precisely, and independently of whatever
later reads it.

**Why they are consumed.** A typed model is only useful once something
reads it — to report it, display it, validate it, or reason about it.
Consumption is the point of building the model at all; an
unconsumed model is inert data sitting in `src/pcae/cltr/authority/`
and `src/pcae/schema_resources/cltr_cutover/`.

**What problems this architecture solves.** It defines, in advance of
any implementation, which categories of components may read typed
authority records, under what guarantees, with what provenance
obligations, and with what boundary against authority itself — so that
the first real consumer (whichever phase implements it) has an
existing contract to satisfy rather than an ad hoc decision to make.

**What this architecture explicitly does not solve.**

- It does not decide whether authority ever gets activated, or how.
- It does not decide when Stage 3 records start being *written* by a
  runtime process (that is a future migration/cutover concern, Section
  10).
- It does not repair, extend, or reinterpret any Stage 3 schema.
- It does not grant any component new capability; `pcae runtime
  inspect` continues to report `Observed` / `observe` /
  `unavailable` unaffected by this phase.

## 3. Governing hierarchy

The separation this phase must not weaken:

```
Schema
    defines shape
Typed Model
    defines representation
Validation
    proves representation
Lifecycle
    determines authority
Authority
    determines behavior
```

A typed authority record is data that *represents* an authority-related
fact (an epoch, a readiness package, a certification). It does not, by
existing, being valid, or being read, *establish* that fact as
operative. Only governed lifecycle semantics (`pcae task`, `pcae
phase-report`, `pcae phase complete`, and their successors) determine
authority. This phase's every subsequent section is downstream of this
one paragraph.

## 4. Consumption principles

Every future consumer of a Typed Authority Model record — without
exception — must satisfy all of the following:

1. **Read-only.** A consumer reads a record; it never constructs a
   record for the purpose of asserting a new fact into the system. (A
   *producer* that persists a new record is a different, not-yet-
   architected role; see Section 10.)
2. **Deterministic.** Given the same record bytes, a consumer produces
   the same output every time. No consumer may vary its output by wall
   clock, random state, or non-reproducible environment lookups.
3. **Side-effect free.** Reading a record must not write a file,
   mutate `.pcae/` state, open a network connection, or launch a
   process. This mirrors the side-effect-freedom already independently
   verified for package import/construction in 136AW Section 10 and
   extends it to every future reader.
4. **Immutable-respecting.** A consumer must never attempt to bypass
   the frozen-dataclass immutability of a typed model (e.g. via
   `object.__setattr__`, pickling around `__init__`, or copying then
   mutating a `to_dict()` result) to simulate a write.
5. **Explainable.** A consumer's output must be traceable back to the
   specific fields of the specific record(s) it read — no consumer may
   produce a conclusion that cannot be pointed back to record content.
6. **Provenance-preserving.** See Section 7 in full; briefly, a
   consumer must carry forward source identity, record identity,
   schema version, digest, and any disclosed limitations rather than
   silently dropping them.
7. **Authority-neutral.** A consumer's output must never be phrased or
   used as an authority determination. A consumer may say "this record
   states epoch E is `authoritative`"; it may never say or act as if
   "epoch E is therefore active."
8. **Execution-neutral.** A consumer must not trigger, schedule, or
   gate any executable action based on what it reads. This includes
   not conditionally invoking other governed commands based on record
   content.

Any component that cannot honor all eight principles is not a
Consumer under this architecture and requires its own, separately
governed architecture phase (see Section 3's "Authority" layer and
Section 14's No-Go list).

## 5. Consumer classification

### 5.1 Allowed consumers (permitted now, subject to Section 4 and this document)

- Bootstrap reporting (`pcae session bootstrap`) — may display typed
  authority record content as observed state.
- Session-state reporting (`.pcae/session.json` snapshotting/display)
  — may reference record identity/provenance in session narrative.
- Report generation (PFR-001 phase reports, Architecture Status) — may
  cite record content as supporting evidence, never as the report's
  own authority.
- CLI display (any `pcae ... show`/`pcae ... inspect` surface) — may
  render record fields for human reading.
- Diagnostics (`pcae doctor ...`, `pcae health`, `pcae check`) — may
  read records to check internal consistency (e.g. digest matches
  schema, references resolve structurally) without asserting authority
  outcomes.
- Reconciliation (comparing two records, or a record against another
  representation, for consistency) — read-only comparison, no
  resolution of which is "correct" from an authority standpoint.
- Schema validation — validating a record against its frozen schema.
- Serialization/deserialization — the existing `to_dict()`/`from_dict()`
  round-trip already implemented and verified in Stage 3.
- Packaging (wheel/sdist inclusion, distribution) — already verified
  in 136AW Section 8; unaffected by this phase.
- Inspection (`pcae runtime inspect` and similar observation-only
  surfaces) — may report on record presence/shape without granting
  execution capability.
- Future read-only repository intelligence (the query/advisory
  surfaces built in Tracks 118-132) — may treat typed authority records
  as one more read-only data source, subject to the same Section 4
  principles already governing every other repository-intelligence
  consumer.

### 5.2 Future consumers (not authorized by this phase; require their own architecture phase before implementation)

- Shadow comparison (comparing a typed authority record against a
  legacy/parallel representation without acting on the result).
- Semantic validation (validating cross-record meaning beyond schema
  shape — e.g. "does this readiness package's epoch reference match a
  known epoch record").
- Cutover analysis (evaluating whether stated conditions for a future
  cutover appear met, for human review only).
- Migration planning (identifying what would need to happen to move
  from the current unconsumed state to an active-consumption state).

Each of these remains read-only and authority-neutral in principle,
but each requires its own dedicated architecture/contract-freeze pair
before any implementation, per the same discipline used for every
prior Stage 1-3 chapter. This phase does not pre-approve their design.

### 5.3 Forbidden consumers (categorically prohibited; implementing any of these requires reversing this architecture, not extending it)

A component is a forbidden consumer if it does any of the following:

- Activates authority (causes any epoch/state to become operative).
- Modifies lifecycle (writes a task/phase/session state transition
  based on record content).
- Changes authority state (persists a new or altered authority record
  as a side effect of reading one).
- Executes runtime actions (publication, notification dispatch, marker
  write, finalization receipt, recovery, quarantine) conditioned on
  record content.
- Bypasses lifecycle (reaches an authority-relevant outcome without
  going through `pcae task`/`pcae phase-report`/`pcae phase complete`
  or their governed successors).
- Infers authority solely from model presence (treats "a
  `CutoverCandidate` record exists and is valid" as equivalent to "this
  candidate is authorized" — validity is a schema/model property;
  authorization is a lifecycle property, and the two must never be
  conflated).

## 6. Ownership boundaries

Every responsibility below has exactly one owner. No two rows may
overlap.

| Responsibility | Owner |
|---|---|
| Executable schemas (shape, required/optional fields, enums, discriminators) | `src/pcae/schema_resources/cltr_cutover/**` (frozen, Stage 3) |
| Typed models (representation, immutability, serialization) | `src/pcae/cltr/authority/*.py` (frozen per-family, Stage 3) |
| Validators (schema conformance) | The Draft 2020-12 validation engine established in Stage 3 (136 schema-track); schema validation only, never semantic or authority validation |
| Lifecycle | `pcae task`, `pcae phase-report`, `pcae phase complete`, and the canonical lifecycle-transition architecture (Track 134) |
| Runtime | `pcae runtime inspect` and the Runtime Architecture (Track 110-113); currently Observed/observe/unavailable |
| Governance | `pcae health`, `pcae check`, `pcae doctor`, `pcae status coherence`, `AGENTS.md` |
| Authority | Governed lifecycle semantics alone (Section 3); no schema, model, or consumer module |
| Reporting | Consumers listed in Section 5.1, each individually, for their own output surface only |

No consumer may take on schema ownership (redefining shape), model
ownership (redefining representation), or authority ownership
(deciding what is active). A consumer that needs a schema or model
change must route that change through the existing Stage 3 governance
process, not implement a local workaround.

## 7. Authority boundary

Typed models may **represent**:

- authority epochs
- authority state
- requests
- readiness
- authorization
- candidates
- certification
- publication
- recovery

Representation never establishes authority. A `Certification` record
that is schema-valid, digest-consistent, and successfully deserialized
is a well-formed *statement* that certification occurred as described
within that record — it is not, by itself, a lifecycle fact that
certification is currently in effect. Authority always comes from
governed lifecycle semantics: the same `pcae task`/`pcae
phase-report`/`pcae phase complete` path already used for every
existing governed decision in this repository, and no other path.

This boundary applies uniformly across all sixteen record families;
no family is exempt, and no future family may be exempt without a
new architecture phase revisiting this section.

## 8. Validation responsibilities

Five distinct kinds of validation exist over this model; none may be
conflated with another, and each belongs to a specific layer:

| Validation kind | Question it answers | Belongs to |
|---|---|---|
| Schema validation | Does this JSON document conform to its frozen JSON Schema (Draft 2020-12)? | The Stage 3 validation engine; schema owner |
| Model validation | Does this Python object satisfy its dataclass's own `__post_init__` invariants (required fields present, locally forbidden enum values excluded, discriminator consistent)? | The typed model itself (`src/pcae/cltr/authority/*.py`), already implemented per family |
| Semantic validation | Do this record's *meanings* hold in context (e.g. does a referenced epoch actually correspond to a plausible readiness state)? | Not yet architected — a Section 5.2 future consumer, requiring its own phase |
| Lifecycle validation | Is this record's existence consistent with the governed lifecycle state (task/phase/session)? | `pcae check`, `pcae doctor`, `pcae status coherence` — existing governance surfaces, extended only if a future phase explicitly adds record-aware checks |
| Governance validation | Does reading/using this record comply with this architecture (Sections 4-5, 14)? | Code review and this document itself; no automated enforcement is introduced by this phase |

A consumer may rely on schema and model validation having already
occurred (both are enforced at construction/deserialization time by
the existing Stage 3 code). A consumer must never claim to perform
semantic or lifecycle validation unless a dedicated future phase has
defined that responsibility for it.

## 9. Provenance model

Every consumer must preserve, and never silently discard, the
following for every record it touches:

- **Source identity** — where the record came from (file path, API
  call, or other originating location), if known to the consumer.
- **Record identity** — the record's own identity fields (as defined
  by `identity.py`/`envelope.py` in the shared core), not a
  consumer-invented substitute.
- **Schema version** — the `schema_version` the record was validated
  against (per manifest, currently `"1.0"` for all sixteen families).
- **Derivation** — whether the consumer's output is a direct
  restatement of record fields or a computed summary over them; the
  two must be distinguishable in the consumer's own output.
- **Digest** — the record's `file_digest`/`record_digest` where
  present, so a downstream reader can independently confirm which
  exact record content was used.
- **Limitations** — any `limitations.py`-shaped disclosure already
  present on the record (Stage 3's existing limitations/uncertainty
  primitive) must be carried into consumer output, not dropped for
  brevity.
- **Uncertainty** — any field the record itself marks as tentative,
  opaque (`OpaqueJsonValue`), or deferred (e.g. `DEFERRED-136T-1`,
  `DEFERRED-136V-1`, both still open per 136AW Section 5) must be
  reported as such, not silently resolved.
- **Authority disclosures** — per Section 7, a consumer's output must
  explicitly disclose that it is reporting a *representation*, not an
  authority determination, whenever its output could plausibly be
  misread as the latter.

No consumer may summarize a record in a way that would prevent a
reader from reconstructing which of the above was true of the
original record.

## 10. Runtime boundary

The following are explicitly prohibited for every Typed Authority
Model consumer under this architecture, without exception:

- execution
- mutation
- persistence
- authority activation
- runtime decisions
- automatic cutover
- publication
- recovery actions

Runtime remains, unaffected by this phase and by anything this
architecture permits:

- **State:** Observed
- **Maximum capability:** observe
- **Execution:** unavailable

`pcae runtime inspect` is itself an Allowed consumer (Section 5.1);
this phase does not change what it reports, and no future consumer
architected under this document may cause it to report differently
without a separate, dedicated Runtime Architecture phase (Track
110-113's own governance, not this one).

## 11. Lifecycle boundary

Typed authority records may be *referenced by* — but never become —
lifecycle authority for:

- **Reports** (PFR-001 phase reports may cite a record's content as
  supporting evidence, the same way 136AW Section 17 cites its own
  canonical report as authoritative for *that phase's completion*,
  never for authority activation).
- **Metadata** (`.pcae/phase-completion-metadata.json` and similar may
  note that a record was read, without treating the record as the
  metadata's own authority).
- **Receipts** (a `FinalizationReceiptAuthorityBinding` record may be
  read and reported on; the actual finalization receipt lifecycle
  event remains owned by the existing finalization path, per Section
  6).
- **Markers** (a `MarkerAuthorityBinding` record may be read and
  reported on; writing an actual marker remains a lifecycle action,
  not a consumption action).
- **Checkpoints** (any future checkpoint concept may reference record
  identity/digest without deriving checkpoint authority from it).
- **Notifications** (a `NotificationAuthorityBinding` record may be
  read and reported on, distinct from the existing, already-governed
  Telegram notification dispatch path, which does not currently read
  this model at all).
- **Architecture Status** (may list Stage 3's own completion the same
  way it lists every other completed chapter, without treating any
  individual authority record as changing Architecture Status's own
  phase-count derivation).

In every one of these cases, the typed record is *cited*, never
*substituted* for the lifecycle mechanism that actually produces the
report, metadata, receipt, marker, checkpoint, notification, or status
entry today.

## 12. Migration boundary

Future interaction with shadow operation, migration, rehearsal, and
authority cutover is anticipated but **not implemented, scheduled, or
designed in any detail by this phase**:

- **Shadow operation** — running a future consumer alongside existing
  behavior to compare outputs without acting on the comparison. Its
  architecture, contract, and prototype would each need their own
  phase, following the same architecture -> contract-freeze ->
  contract-verification -> prototype -> prototype-verification
  sequence already used for every prior Stage 1-3 and repository-
  intelligence chapter.
- **Migration** — any process that would cause a component currently
  reading legacy (non-typed) state to instead read Typed Authority
  Model records. Not designed here; would itself need a Section 5.2-
  style future-consumer phase per affected component.
- **Rehearsal** — exercising a future cutover path without granting it
  effect. Requires its own architecture once (and only once) a
  concrete cutover mechanism is itself architected — which this phase
  explicitly is not doing.
- **Authority cutover** — the eventual transfer of real authority from
  legacy lifecycle mechanisms to Typed Authority Model-backed ones, if
  ever pursued. This phase does not define when, how, or whether that
  happens; it only guarantees that nothing in Sections 4-11 would need
  to be violated to eventually design it.

## 13. Error handling

Consumers must fail deterministically, never guess, on:

- **Unknown schema versions** — a consumer encountering a
  `schema_version` other than a version it recognizes must reject the
  record (deterministic failure), not attempt best-effort parsing.
- **Unknown model versions** — analogous to the above for any future
  model-level versioning; no consumer may silently assume forward or
  backward compatibility it has not been explicitly built to handle.
- **Malformed models** — any Python object failing a typed model's own
  `__post_init__`/deserialization checks must be rejected at that
  layer; a consumer must never catch and paper over such a rejection
  by substituting a default record.
- **Incompatible records** — a record whose declared `record_type`
  does not match the family a consumer expects must be rejected, not
  coerced.
- **Missing references** — per `references.py`'s existing
  disclaimed-lookup design (id+digest(+family) tuples only, no
  dereferencing), a consumer must not attempt to resolve a reference
  and treat resolution failure as "the referenced thing doesn't
  exist" — reference validation is structural only, per Stage 3's own
  documented boundary, and consumers inherit that same boundary rather
  than inventing dereferencing behavior of their own.
- **Partial models** — a record missing a schema-required field must
  already fail at model-construction time (existing Stage 3
  behavior); a consumer must never accept a partially-constructed
  record by relaxing that requirement itself.

In every case, "fail deterministically" means: the same malformed
input produces the same rejection, with no consumer-side retry,
fallback, or silent substitution that could make behavior depend on
timing, ordering, or environment.

## 14. Extensibility

Future record families must be able to integrate without changing any
existing consumer's code, by construction:

- A new family adds a new frozen schema (`records/*.schema.json`), a
  new manifest entry, and a new typed model class — following exactly
  the same per-family pattern already used sixteen times in Stage 3.
- A consumer that is family-generic (e.g. schema validation,
  serialization, packaging, or a provenance-preserving CLI display)
  continues to work unchanged, since it operates on shared primitives
  (`envelope.py`, `identity.py`, `digest.py`, `references.py`,
  `limitations.py`) rather than hardcoding a fixed family list.
- A consumer that is family-specific (e.g. a report section describing
  `AuthorityEpoch` fields by name) must explicitly opt in to a new
  family; it must not implicitly and silently start describing a
  family it was never built to describe. This mirrors the existing
  Stage 3 precedent of per-family independent verification rather than
  a single generic verifier assumed to cover all sixteen (now
  seventeen-plus) families equally.
- No existing consumer's Allowed/Forbidden classification (Section 5)
  changes merely because a new family is added; classification is by
  consumer behavior, not by which families currently exist.

## 15. Security

- **Immutability.** Every typed model is a frozen dataclass
  (`immutable.py`'s `freeze_json_value`/`thaw_json_value` discipline,
  already independently verified in 136AW Section 7); no consumer may
  construct a mechanism (subclassing, monkeypatching,
  `object.__setattr__`) to defeat this.
- **Digest preservation.** A consumer must carry forward, not
  recompute-and-discard, a record's declared digest (Section 9); this
  preserves the ability of any downstream party to independently
  confirm record content.
- **Provenance preservation.** Per Section 9 in full; a security
  property because losing provenance is how an authority-neutral
  representation could later be mistaken for an authority
  determination.
- **Replay neutrality.** Reading the same record twice, or reading it
  again after a process restart, must produce the same consumer output
  and no additional side effect — consumption must be idempotent by
  construction (a direct consequence of Section 4's determinism and
  side-effect-freedom principles).
- **Authority neutrality.** Per Section 7; the single most important
  security property of this entire architecture; a consumer that
  blurs this line is the primary risk this document exists to
  prevent.
- **No privilege escalation.** A consumer process must never gain
  execution, mutation, or governance capability *because* it read a
  Typed Authority Model record — reading remains, and must remain, a
  strictly weaker capability than the governed lifecycle actions
  listed in Section 6's "Authority" row.

## 16. No-Go conditions

The following are explicitly forbidden, for this phase and for any
future phase claiming to build on it, unless and until a new,
dedicated architecture phase revisits this document:

- Authority resolver (any component that decides which of several
  candidate records is "the" active one).
- Authority persistence (any component that writes a new authority
  record as a side effect of consumption).
- Authority pointer (any mechanism that names a "current" authority
  record outside governed lifecycle state).
- Runtime execution (any change to Runtime's Observed/observe/
  unavailable posture).
- Semantic decision engine (any component that evaluates record
  meaning to produce an actionable recommendation beyond human-
  readable reporting).
- Lifecycle mutation (any consumer that writes to task/phase/session
  state as a consequence of what it reads).
- Execution adapters (any bridge from a typed record to an executable
  action).
- Cutover activation (any component that flips behavior from
  legacy-authoritative to typed-model-authoritative).
- Legacy retirement (removing or bypassing any existing
  non-typed-model lifecycle mechanism).
- Publication runtime (any component that performs an actual
  publication action based on a `PublicationAttempt`/
  `PublicationEvidence` record).
- Recovery runtime (any component that performs an actual recovery
  action based on a `RecoveryJournalEntry`/`ConcurrencyConflict`
  record).

## 17. Success criteria confirmation

- A complete Typed Authority Model Consumption Architecture is
  documented (this file). ✅
- All consumer classes are identified (Section 5: Allowed, Future,
  Forbidden). ✅
- Ownership boundaries are explicit (Section 6, one owner per row). ✅
- Authority boundaries remain intact (Sections 3, 7, 16). ✅
- Runtime boundaries remain intact (Section 10; `pcae runtime
  inspect` unaffected, confirmed live during this phase). ✅
- Lifecycle boundaries remain intact (Section 11). ✅
- Provenance requirements are defined (Section 9). ✅
- Extensibility is documented (Section 14). ✅
- No execution capability is introduced (Sections 10, 16; confirmed —
  this phase changed no `src/pcae/cltr/authority` or
  `src/pcae/schema_resources` file). ✅
- No authority activation is introduced (Sections 3, 7, 16). ✅
- Runtime remains Observed / observe / execution unavailable
  (re-confirmed live via `pcae runtime inspect` during this phase). ✅

## 18. No-go confirmation (this phase's own execution)

- No authority resolution, activation, or transfer occurred.
- No cutover authorization or execution occurred.
- No publication, notification dispatch, marker write, or receipt
  finalization occurred (beyond this phase's own standard governed
  finalization path).
- No lifecycle mutation occurred outside the standard governed `pcae
  task`/`pcae phase-report`/`pcae phase complete` path.
- No migration, recovery, rollback, compatibility calculation, or
  quarantine operation occurred.
- No Stage 3 schema, typed model, registry, or manifest file was
  modified.
- Runtime remains Observed / observe / unavailable, confirmed live via
  `pcae runtime inspect` both before and after this phase's document
  authoring.

## 19. Recommended next phase

**137B — Typed Authority Model Consumption Contract Freeze.**

Its purpose: convert this architecture's Allowed-consumer categories
(Section 5.1) into a frozen, testable contract — analogous to how
every prior Stage 1-3 architecture phase was followed by a
contract-freeze phase before any prototype was implemented. Phase 137B
is **not** begun by this phase.
