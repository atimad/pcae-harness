# Phase 135Z — Stage 3 Companion Schemas and Typed Authority Model Contract Freeze

## Contract identifier

**CLTR-CUTOVER-SCHEMAS-001 v1.0**

Status: **FROZEN** as of Phase 135Z. This document is the binding contract
text. It is contract-only. It defines future Stage 3 companion-record and
typed-authority-model behavior. It does not implement, activate, or
authorize any of the behavior it defines.

## Normative language

Same convention as CLTR-001, CLTR-SCHEMA-001, and CLTR-CUTOVER-001:

- **must / shall** — binding requirement; a future implementation violating
  it is non-conformant with CLTR-CUTOVER-SCHEMAS-001.
- **must not / shall not** — binding prohibition.
- **should** — strong recommendation; deviation requires explicit, governed
  justification.
- **may** — optional, permitted.
- **[GUIDANCE]** — explanatory/illustrative, non-binding.
- **[NEW]** — a Stage-3-companion-schema decision with no direct precedent
  in a prior binding contract.

Every normative rule traces to: a prior binding contract, independently
verified implementation evidence, an explicit safety requirement, or a
clearly labelled **[NEW]** decision. Citations use the form `135W §N`,
`135X §N`, `135Y §N`, `CLTR-001 §N`, `CLTR-SCHEMA-001 §N`,
`CLTR-CUTOVER-001 §N`, `PFN-001 §N`, `PFR-001 §N`.

---

## 0. Relationship to governing contracts

### 0.1 Relationship to CLTR-001 v1.0

CLTR-001 defines the semantic content of a canonical lifecycle transition
record (thirty required semantic fields, CLTR-001 §6.2) without fixing wire
schema, and states CLTR is not currently production authority (CLTR-001
§4.3, §24.3, §25). CLTR-CUTOVER-SCHEMAS-001 does not modify CLTR-001. Every
companion record defined below either (a) instantiates a CLTR-001 semantic
field in typed, persisted form, or (b) is new operational/evidence state
CLTR-001 never claimed to define. Where a companion record touches a
CLTR-001 identity field (`transition_id`, `notification_id`, `marker_id`,
`receipt_id`), this contract binds to the existing field rather than
re-deriving it.

### 0.2 Relationship to CLTR-SCHEMA-001 v1.0.1

CLTR-SCHEMA-001 remains frozen and unmodified by this phase. It defines the
`lifecycle_state`/`transition_type` enums, the five-code `authority_role`
representation field (`S`/`R`/`D`/`E`/`V`), the fifteen representation-kind
bindings, canonicalization (§14), digest rules (§15), the persistence
contract (generation directories, the four-field `current` pointer, §16),
the nine-step atomic-publication specification (§17, unimplemented), and the
diagnostic envelope's `authority_mode` enum (§25). This contract's typed
authority model (§4–§6 below) is the concrete instantiation CLTR-SCHEMA-001
§24 (Migration, [GUIDANCE]) sketched but never defined; it is additive, not
amendatory. §41 below produces the full disposition table required before
any future CLTR-SCHEMA-001 minor revision is proposed. **No field, enum, or
binding inside CLTR-SCHEMA-001 changes as a result of this document.**

**Naming distinction [NEW]:** this contract's `AuthorityRole` enum (§3.2,
seven values: `authoritative | derivative | operational | evidence |
compatibility | historical | quarantined`) is a **separate vocabulary**
scoped to companion records, not a redefinition or extension of
CLTR-SCHEMA-001's five-code `authority_role` field. The two serve different
purposes: CLTR-SCHEMA-001's `authority_role` classifies a CLTR
*representation kind* (report/metadata/marker/etc.) relative to the CLTR
record itself; this contract's `AuthorityRole` classifies a *companion
record family* relative to production authority. A mapping table is given
in §32.2 to prevent confusion; no code point is shared or reused across the
two enums, and no companion record ever sets CLTR-SCHEMA-001's
`authority_role` field.

### 0.3 Relationship to CLTR-CUTOVER-001 v1.0

CLTR-CUTOVER-001 (135W, independently verified zero-Blocking by 135X) is the
binding semantic contract for the one-time transfer of production lifecycle
authority. It names the required concepts — authority epoch, cutover
request, readiness package, human authorization, candidate, certification,
CAS/publication, recovery journal, reconciliation, compatibility — without
fixing their wire representation (135W §7–§23 define semantics; 135W
Prerequisite Register PREREQ-1 explicitly defers the typed authority-epoch
model). This document is the wire-and-type-level companion: for every
CLTR-CUTOVER-001 concept, it either freezes a durable record schema, an
embedded component, a runtime-only typed model, or an explicit "not
required" disposition, and closes PREREQ-1 (§4) and PREREQ-2's schema
readiness gap. It does not alter any CLTR-CUTOVER-001 semantic rule; where
this document must choose among options CLTR-CUTOVER-001 left open (e.g.
whether the authority-state record is itself the pointer target, §5.3), the
choice is recorded as a **[NEW]** decision bound by, not contradicting,
CLTR-CUTOVER-001's invariants (135W §5, single-authority invariant; 135W
§9, CAS/stale-writer contract; 135W §17, recovery journal semantics).

### 0.4 Relationship to PFN-001

PFN-001 freezes exactly-once, idempotent canonical-report notification
dispatch via `certify_notification_transition()` and the
`.last-notified.json` marker, with a mandatory durable failure record on
non-success (PFN-001 §4, §5, §8, §9). §19 below defines the Notification
Authority Binding companion record that lets a Stage-3-active notification
intent reference the authoritative generation without altering PFN-001's
dispatch mechanism, guarantee, or failure contract.

### 0.5 Relationship to PFR-001

PFR-001 freezes the canonical phase report's twelve mandatory sections,
derived from the `PhaseReport` artifact/trust pipeline
(`src/pcae/core/phase_reports.py`), not independently authored narrative.
This document's own final report (§45 below, and the terminal 135Z report)
continues to satisfy PFR-001 unchanged; no companion record substitutes for
or bypasses PFR-001's derivation discipline.

### 0.6 Relationship to verified Stage 1/2/rollback evidence

Stage 1 migration evidence (`CLTR-MIGRATION-EVIDENCE-001`, `.pcae/cltr-migration/epochs/<migration_epoch>/transitions/<transition_id>/evidence/`),
Stage 2 rehearsal generations (`.pcae/cltr-migration/epochs/<epoch>/rehearsals/<transition-id>/{candidates,generations,failures,quarantine,current-rehearsal}`),
and rollback-rehearsal evidence (`RollbackEvidenceRecord`, ten-value
`RollbackOutcome` enum) are treated as frozen, non-renamed prior art. No
companion record schema in this document renames an existing production
literal, directory, or pointer name. Where a new typed enum value maps to
an existing frozen string literal, §4.6 and §41 record the mapping
explicitly rather than replacing the literal.

### 0.7 Relationship to the 135Y implementation dependency graph

135Y independently proposed nine CLTR-SCHEMA-001 companion-record kinds as
part of its own 11-layer implementation-layer plan. This document does not
copy that list. §2 below re-derives the record-family inventory from first
principles against the twenty-item evaluation list requested for 135Z,
arriving at a materially different persistence classification for several
families (in particular: CAS expectations are embedded, not standalone;
reconciliation and historical references are runtime-only, not persisted;
notification/marker/receipt bindings are companion extensions, not new
top-level records; no dedicated "authority transition receipt" is created).
Where this document's inventory differs from 135Y's illustrative list, the
difference is a deliberate independent finding of this phase, not an
inconsistency to reconcile later — 135Y's list was explicitly a planning
illustration, not a frozen inventory (135Y §11, "do not automatically
create schemas ahead of need").

---

## 1. Contract purpose

CLTR-CUTOVER-SCHEMAS-001 freezes the deterministic, versioned, typed,
canonical record set that Stage 3 prerequisite implementation must produce
before CLTR-CUTOVER-001's semantic contract can be implemented in code. It
supports: authority-state resolution, authority epochs, cutover requests,
readiness packages, human authorization, candidate certification,
publication attempts, CAS state, concurrency conflicts, recovery
journaling, reconciliation, quarantine, marker and receipt bindings, and
historical compatibility.

It does not: create authority independently of the single authoritative
generation (CLTR-CUTOVER-001 §3–§5); activate cutover; alter production
behavior; replace the authoritative generation defined by
CLTR-CUTOVER-001; replace CLTR-001; or weaken PFN-001 or PFR-001. Every
record family defined below carries an explicit authority disclosure (§32)
that is `non-authoritative` unless the record family *is* the authoritative
generation itself (which none of the companion families are).

---

## 2. Record-family inventory

The twenty candidate concepts are independently classified below. Six
classification labels are used: **required companion schema**, **embedded
schema component**, **existing-schema extension**, **runtime-only typed
model**, **derived view**, **not required**. No family is marked "deferred"
— Stage 3 prerequisite work cannot begin until every concept below has a
settled disposition; anything genuinely unresolved is instead raised as a
**BLOCKING** or **PREREQUISITE** finding in §45, not silently deferred here.

| # | Concept | Classification | Rationale (short) |
|---|---|---|---|
| 1 | Authority State Record | **required companion schema** | Durable, mutable, pointer-adjacent snapshot; distinct from both the authority epoch (identity) and the production pointer (target). See §5. |
| 2 | Authority Epoch Record | **required companion schema** | Closes PREREQ-1; typed replacement for the string-prefix epoch encoding. See §4. |
| 3 | Cutover Request Record | **required companion schema** | Deterministic, content-addressed, immutable once created. See §6. |
| 4 | Readiness Evidence Package | **required companion schema** | Aggregates Stage 1/2/rollback evidence into one digest-bound artifact; immutable. See §7. |
| 5 | Human Authorization Record | **required companion schema** | Operator-issued, digest-bound, replay-guarded. See §8. |
| 6 | Cutover Candidate Record | **required companion schema** | Upgrades a rehearsal generation into a Stage-3-scoped candidate; immutable once created. See §9. |
| 7 | Certification Record | **required companion schema** | Immutable gate-pass evidence, distinct from and prior to publication. See §10. |
| 8 | Authority Publication Attempt Record | **required companion schema** | Append-only, one row per attempt, immutable once written. See §12. |
| 9 | Authority Publication Evidence Record | **required companion schema** | Immutable outcome record per attempt, distinct from the attempt itself. See §13. |
| 10 | Compare-and-Swap Expectation Record | **embedded schema component** | Ephemeral, single-use, always embedded inside a Certification Record and echoed inside the Publication Attempt that consumes it; never independently persisted as a standalone file family. See §11. |
| 11 | Concurrency Conflict Record | **required companion schema** | Immutable, append-only evidence of a detected conflict. See §14. |
| 12 | Recovery Journal Record | **required companion schema** | Append-only entry schema plus a derived current-pointer view (the aggregate is a derived view, not a second schema). See §15. |
| 13 | Reconciliation Result Record | **derived view** | Computed on demand from other records, exactly like the existing `pcae phase-report reconcile` output and CLTR-SCHEMA-001's Architecture Status kind (D-role, no own identity/digest, regenerable, mutation: none). See §16. |
| 14 | Quarantine Record | **required companion schema** | Immutable, append-only; must exist independently of which object family is quarantined. See §17. |
| 15 | Authority Transition Receipt | **not required** | Folded into the existing PFN-001/CLTR-SCHEMA-001 receipt representation kind (extended via a binding, §21) plus Publication Evidence (§13) plus Authority State (§5); a dedicated fourth record would duplicate bindings those three already carry. See §18. |
| 16 | Notification Authority Binding | **existing-schema extension** (realized now as a companion binding record, pending a future CLTR-SCHEMA-001 minor revision) | Extends representation kind #8 (notification payload) without modifying CLTR-SCHEMA-001 today. See §19. |
| 17 | Marker Authority Binding | **existing-schema extension** (companion binding record today) | Extends representation kind #9 (marker). See §20. |
| 18 | Finalization Receipt Authority Binding | **existing-schema extension** (companion binding record today) | Extends representation kind #10 (receipt). See §21. |
| 19 | Compatibility State Record | **required companion schema** | Durable record of legacy's post-cutover role; must never grant authority. See §22. |
| 20 | Historical Authority Reference | **runtime-only typed model** | A typed lookup shape over existing frozen identities/digests (pre-CLTR phases, Stage 1/2/rollback evidence, old reports/markers/receipts/checkpoints); nothing new is persisted — it references what already exists. See §23. |

**Result: 16 required companion schemas** (rows 1–9, 11–12, 14, 17, 19, plus
the three binding extensions counted as companion records today), **1
embedded component** (row 10), **1 derived view** (row 13), **1
runtime-only typed model** (row 20), **0 not-required top-level families
beyond row 15**. No twenty independent schemas are created; three of the
twenty candidates collapse into existing-representation-kind extensions,
one collapses into an embedded component, one into a derived view, one into
a runtime-only model, and one is eliminated outright.

---

## 3. Typed authority enums

### 3.1 AuthorityKind

Wire values: `legacy | cltr`. Exact-match only — **substring classification
is forbidden** [NEW, closes a class of ambiguity CLTR-CUTOVER-001 §5 already
prohibits at the invariant level]. Semantics: `legacy` = the existing
finalization-transaction pipeline is production authority; `cltr` = a
certified, manifest-bound CLTR generation is production authority for the
current authority epoch. Allowed transition: `legacy → cltr` exactly once
per authority epoch, via successful publication (§13); `cltr → legacy` is
**forbidden** as a normal transition (CLTR-CUTOVER-001 §14 already forbids
routine pointer rollback after notification dispatch; this contract extends
that prohibition to the typed `AuthorityKind` field itself — a `cltr → legacy`
transition may occur only through an explicitly governed, separately
authorized retirement-reversal phase, never through recovery or
reconciliation). Unknown values: any value other than the two above is a
`invalid_schema` failure (§31), fail-closed. Versioning: this is a v1
closed enum; a future value requires a MAJOR bump of this contract's
enum-versioning profile (§42).

### 3.2 AuthorityRole

Wire values: `authoritative | derivative | operational | evidence |
compatibility | historical | quarantined`. Scoped to companion records
(§0.2). Semantics:

- `authoritative` — reserved exclusively for the authoritative generation
  itself; **no companion record defined in this contract may declare this
  value** (enforced structurally, §35).
- `derivative` — a record that mirrors or projects authoritative content
  without being consulted for authority resolution (e.g. Compatibility
  State).
- `operational` — mutable in-flight coordination state (CAS expectation
  context, publication attempt, recovery journal entry).
- `evidence` — immutable proof of a past event (readiness package,
  certification, publication evidence, conflict, quarantine).
- `compatibility` — legacy-facing adapter/compatibility state.
- `historical` — read-only reference to pre-cutover or superseded state.
- `quarantined` — the record itself, or the object it describes, has been
  quarantined and must not be treated as evidence of readiness.

Allowed transitions are record-family-specific (§33); the abstract rule is
that `quarantined` is reachable from any other value and is terminal for
the record's authority-relevance (the record is never un-quarantined in
place — a new record is issued after remediation). `authoritative` is
unreachable from every other value for any companion record. Unknown
values fail closed (§31, `invalid_schema`).

### 3.3 MigrationStage

Final wire values (Stage 0 through terminal), each distinct from — and
explicitly mapped to, where applicable — an existing frozen production
literal so that no legacy string is renamed:

| Typed value | Existing frozen literal it typifies | Status |
|---|---|---|
| `shadow` | (Stage 0 prototype/shadow era; no single frozen production literal exists — `.pcae/cltr-shadow/` namespace only) | historical |
| `dual_derivation` | `"dual_derivation_legacy_authority"` (Stage 1 migration evidence `migration_stage`) | historical/active baseline |
| `atomic_rehearsal` | `"stage_2_atomic_publication_rehearsal"` | historical/verified |
| `rollback_rehearsal` | `"stage_2_rollback_rehearsal"` | historical/verified |
| `cutover_readiness` | (new — no prior literal; Stage 3 readiness-package stage) | **[NEW]** |
| `cutover_candidate` | (new) | **[NEW]** |
| `certified` | (new) | **[NEW]** |
| `publication_pending` | (new) | **[NEW]** |
| `cltr_authoritative` | (new — terminal target state) | **[NEW]** |
| `legacy_compatibility` | (new — post-cutover legacy role) | **[NEW]** |
| `legacy_retired` | (new — terminal, future phase only) | **[NEW]** |

Allowed transitions: strictly the listed order above is the only forward
path; no value may be skipped except `legacy_compatibility`, which is only
reachable after `cltr_authoritative` and is not on the critical path to
`legacy_retired` unless a separately governed retirement phase authorizes
it. Backward transitions are forbidden except via the same governed
retirement-reversal exception noted in §3.1. Unknown-value behavior:
fail-closed (§31). This enum is a typed **superset** of the migration-stage
concept already used informally in Stage 1/2 evidence; existing evidence
records are not retroactively re-tagged — the mapping table above is
read-only guidance for future typed-model code, not a migration of
existing files.

### 3.4 GenerationRole

Wire values: `rehearsal_candidate | rehearsal_generation | cutover_candidate
| certified_generation | authoritative_generation | historical_generation |
superseded_generation | quarantined_generation`. This enum classifies a
*generation object* across its lifecycle; it is orthogonal to
CLTR-SCHEMA-001's already-frozen `lifecycle_state` (which classifies the
internal certify/promote/notify state machine of a single record).
`authoritative_generation` may be held by exactly one generation per
authority epoch (CLTR-CUTOVER-001 §5 single-authority invariant); all other
values are non-exclusive. Allowed transitions follow generation lineage:
`rehearsal_candidate → rehearsal_generation` (Stage 2, already implemented
and out of scope for this contract) is historical; `cutover_candidate →
certified_generation → authoritative_generation → (historical_generation |
superseded_generation)` is the Stage 3 forward path; `quarantined_generation`
is reachable from any non-terminal value and is terminal for authority
purposes. Unknown values fail closed.

### 3.5 PublicationState

Wire values, in lifecycle order: `not_requested | requested | gate_rejected
| gate_uncertain | certified | publication_prepared | publication_attempted
| publication_uncertain | published | verified | conflict | quarantined`.//
Twelve values. `gate_rejected` and `gate_uncertain` are the
`PublicationState` projections of CLTR-CUTOVER-001's already-frozen
four-value pre-cutover gate outcome (`eligible | ineligible | uncertain |
conflict`, 135W §10): `ineligible` or a gate-stage `conflict` map to
`gate_rejected`; gate `uncertain` maps to `gate_uncertain`; only gate
`eligible` allows `PublicationState` to advance past `certified`. Allowed
transitions: strictly forward along the listed order, with `conflict` and
`quarantined` reachable from any in-flight value (`requested` through
`publication_uncertain`) and both terminal for that request. `verified`
(cross-checked via independent readback, §13) is the only path back to a
resting confirmed state after `published`; a `published` request that is
never independently verified remains `published`, not `verified`, and must
not be treated as equivalent to `verified` by any consumer. **Uncertainty is
never collapsed into failure**: `publication_uncertain` is a first-class
terminal-pending value, distinct from `conflict` (§13, §31).

### 3.6 RecoveryState

RecoveryState is a Stage-3-specific **superset** of the already-frozen
four-value `recovery_classification` derived enum (`none_required |
resume_safe | observe_required | reconciliation_required`,
CLTR-SCHEMA-001 §3.4), extended with the additional states CLTR-CUTOVER-001
§17's crash-state analysis requires for CAS/publication uncertainty. Wire
values: `none_required | resume_safe | retry_required |
operator_review_required | reconciliation_required | quarantine_required |
conflict_unresolved | publication_uncertain_unresolved | terminal_recovered
| terminal_unrecoverable`. Mapping to the frozen base enum: `none_required`
and `resume_safe` are identical in meaning and wire spelling to the base
enum's values; `retry_required`, `quarantine_required`,
`conflict_unresolved`, and `publication_uncertain_unresolved` are all
Stage-3-specific refinements of the base enum's `observe_required`;
`reconciliation_required` is identical to the base enum's value;
`operator_review_required` refines `observe_required` when a human
decision (not just observation) is required; `terminal_recovered` and
`terminal_unrecoverable` are new terminal states with no base-enum
analogue, needed because CLTR-CUTOVER-001's crash-state analysis (135W §17)
identifies at least one class of failure (an authoritative generation that
fails integrity verification with no safe automatic resolution, §17 below)
that the four-value base enum cannot terminate cleanly. Every RecoveryState
value used by a Stage 3 record must be traceable to exactly one base-enum
value via this mapping; a Stage 3 recovery-journal implementation that
reports a `recovery_classification` inconsistent with its own
`RecoveryState` is non-conformant.

### 3.7 CompatibilityMode

Wire values, in the only permitted forward order: `legacy_authoritative |
legacy_adapter | legacy_read_only | legacy_historical | legacy_disabled |
legacy_retired`. `legacy_authoritative` is the current production state
(pre-cutover) and is the initial value for every authority epoch prior to
its first cutover. Once an epoch reaches `cltr_authoritative`
(MigrationStage §3.3), the legacy component for that epoch moves to
`legacy_adapter` (still callable for compatibility reads) and only later,
under a separately governed future phase, to `legacy_read_only →
legacy_historical → legacy_disabled → legacy_retired`. No backward
transition is permitted. **No value in this enum may cause
`AuthorityKind` to read as `legacy` once it is `cltr`** — CompatibilityMode
governs legacy's *residual role*, never legacy's *authority* (§22).

---

## 4. Typed authority epoch

### 4.1 Model

`AuthorityEpoch` binds:

- `epoch_id` — deterministic identity, §4.2.
- `authority_kind` — `AuthorityKind` (§3.1).
- `migration_epoch` — the existing Stage 1/2 `migration_epoch` value
  (`PCAE_CLTR_MIGRATION_EPOCH`-sourced), bound, not re-derived.
- `contract_version` — this contract's version plus CLTR-CUTOVER-001's
  version, both recorded (`"CLTR-CUTOVER-001/1.0"`,
  `"CLTR-CUTOVER-SCHEMAS-001/1.0"`).
- `schema_version` — CLTR-SCHEMA-001 version this epoch's generations
  conform to (`"1.0.1"` at freeze time).
- `predecessor_epoch_id` — nullable; null only for the first-ever epoch of
  a repository.
- `target_authoritative_generation` — nullable reference
  (`transition_id` + `generation_digest`); present only once a target has
  been certified (§10), never before.
- `creation_transition` — the `transition_id` whose processing created this
  epoch record.
- `activation_state` — one of `proposed | active | superseded`.
- `historical_state` — `current | historical`.
- `supersession_state` — nullable reference to the successor `epoch_id`.
- `limitations` — free-text array, never empty for a `proposed` epoch.
- `record_digest` — self-excluded, §27.

### 4.2 Deterministic epoch identity

`epoch_id = sha256(canonical_json({migration_epoch, predecessor_epoch_id,
authority_kind, contract_version, schema_version, creation_transition}))`.
**Rejected as identity inputs**: free-form strings, substring matches on
prior epoch IDs, implicit ordering (no sequence counter is part of
identity), timestamps, and phase titles. `migration_epoch` remains the only
externally supplied (non-derived) input, consistent with Stage 1's existing
rule that it is sourced from an explicit environment variable and never
inferred (§4 of the source-material extraction; CLTR-CUTOVER-001 §7 already
requires this for the cutover request).

### 4.3 Allowed transitions

```
legacy epoch (AuthorityKind=legacy, activation_state=active)
    |  successful publication (§13) for this migration_epoch
    v
CLTR candidate epoch (AuthorityKind=cltr, activation_state=proposed,
                       target_authoritative_generation set only after
                       certification, §10)
    |  publication verified (§13, PublicationState=verified)
    v
CLTR authoritative epoch (AuthorityKind=cltr, activation_state=active)
    |  a future, separately governed epoch transition
    v
future successor epoch (predecessor_epoch_id = this epoch's epoch_id)
```

**[NEW] Frozen decision**: a **candidate authority epoch does exist** as its
own `AuthorityEpoch` record with `activation_state=proposed` before
publication; it is not merely a proposed field embedded inside the cutover
request. Rationale: the cutover request (§6) must reference a stable
`target_authority_epoch` identity from the moment readiness evaluation
begins — before certification, before CAS, before the request itself is
replay-safe — and an embedded proposed-epoch field inside a mutable request
object cannot serve as a stable, independently digestible identity for
downstream records (readiness package, authorization, candidate,
certification all bind to `target_authority_epoch` — §7–§10). A standalone
`proposed` `AuthorityEpoch` record, created once per migration epoch's
cutover attempt, gives every downstream record one deterministic identity
to bind to, and gives the recovery journal (§15) one addressable object
whose `activation_state` can move from `proposed` to `active` atomically at
publication, mirroring the same "identity assigned once, state changes
after" pattern CLTR-001 already uses for `transition_id` (135O's
`SharedTransitionInputPackage` design, extraction §12).

---

## 5. Authority state record

### 5.1 Fields

`AuthorityState` binds: `schema_id` (`"CLTR-AUTHORITY-STATE-001"`),
`schema_version` (`"1.0"`), `migration_epoch`, `authority_epoch_id`
(→ §4), `authority_kind` (→ §3.1), `current_authoritative_object` — a
tagged union: either `{"kind": "legacy"}` (no further identity — legacy has
no CLTR-shaped identity) or `{"kind": "cltr", "transition_id":
..., "generation_id": ...}`; `authoritative_generation_id` (nullable,
present only when `current_authoritative_object.kind == "cltr"`);
`generation_digest` (nullable, mirrors the field); `publication_evidence_id`
(nullable reference, → §13); `authority_pointer_digest` — the digest of the
*production pointer file's own content* at the moment this state record was
written (a read-only echo, never itself the pointer); `source_transition` —
the `transition_id` whose publication produced this state; `contract_version`;
`verification_state` — `unverified | verified | verification_failed`;
`uncertainty` — boolean plus free-text reason, never silently false when a
publication outcome was `publication_uncertain`; `compatibility_mode` (→
§3.7); `limitations`; `record_digest` (self-excluded).

### 5.2 Relationship to the production pointer

**[NEW] Frozen decision**: `AuthorityState` is **evidence adjacent to the
pointer**, not the pointer target, not the pointer payload, and not merely a
derived status record. The exact relationship (only one of the four
options in the brief may hold, and this is it):

- The **production authority pointer** (CLTR-SCHEMA-001 §16's four-field
  `current` file, extended per CLTR-CUTOVER-001 to also carry
  `authority_kind` and `authority_epoch_id` once Stage 3 is implemented)
  remains the single mechanically consulted source of truth for "what is
  authoritative right now." It stays minimal and CAS-friendly (§27, §36).
- `AuthorityState` is a **richer, separately persisted record** written
  immediately after (never before, never instead of) a successful pointer
  update, carrying the verification evidence, uncertainty disclosure, and
  compatibility mode the pointer itself does not carry. It is read by
  reconciliation (§16), by diagnostics, and by human operators — never by
  the authority resolver as its primary source (the resolver's primary
  source remains the pointer itself, per CLTR-CUTOVER-001 §4's single
  shared resolver design).
- It is **not evidence adjacent in the sense of being optional**: every
  successful or uncertain publication attempt (§13) **must** produce an
  updated `AuthorityState`, but the pointer write and the `AuthorityState`
  write are two distinct atomic operations, ordered pointer-then-state, so
  that a crash between them leaves the pointer (the sole authority signal)
  correct while `AuthorityState` is merely stale — a `reconciliation_required`
  RecoveryState (§3.6), never an authority ambiguity.

This closes the "one exact relationship" requirement: **production
authority pointer → (written first, atomically) → AuthorityState (written
second, evidence-adjacent) → referenced by → publication evidence
(§13)**. `AuthorityState` never becomes a second authority; a resolver that
reads `AuthorityState` instead of the pointer to answer "what is
authoritative" is non-conformant with this contract and with
CLTR-CUTOVER-001 §4.

---

## 6. Cutover request schema

### 6.1 Fields

`CutoverRequest` binds: `request_id` (§6.2), `phase_id`, `transition_id`,
`migration_epoch`, `source_authority_epoch_id`, `target_authority_epoch_id`
(→ §4), `source_authority_identity` (tagged union, same shape as
`current_authoritative_object` §5.1), `target_generation_id`,
`target_generation_digest`, `shared_input_final_revision` (binds to the
existing `SharedTransitionInputPackage`/`SharedInputRevision` model,
extraction §12 — not re-derived), `stage1_evidence_id`/`stage1_evidence_digest`,
`stage2_evidence_id`/`stage2_evidence_digest`,
`rollback_evidence_id`/`rollback_evidence_digest`,
`readiness_package_id`/`readiness_package_digest` (→ §7),
`authorization_requirement` — `required | not_yet_evaluated` (never
`not_required` — CLTR-CUTOVER-001's human-authorization contract, 135W §12,
admits no unauthorized path), `cutover_contract_version`
(`"CLTR-CUTOVER-001/1.0"`), `request_state` (→ §33.1), `limitations`,
`request_digest` (self-excluded).

### 6.2 Canonical identity formula

`request_id = sha256(canonical_json({migration_epoch,
source_authority_epoch_id, target_authority_epoch_id, transition_id,
target_generation_id, target_generation_digest,
shared_input_final_revision.package_id,
shared_input_final_revision.revision, phase_id}))`. Timestamps are **not**
inputs to identity (§28). `phase_id` is included because a `transition_id`
alone is not guaranteed globally unique across phases in the Stage 1
design (extraction §12: retry stability keys on
`digest(phase_id, entry_point, migration_epoch, source_revision)`), so
`phase_id` is folded in to avoid an identity collision across
differently-scoped transitions that happen to share a `transition_id`
prefix pattern — no such collision is currently possible in the existing
implementation, but identity determinism must not depend on that being
true forever.

### 6.3 Conflicting replay, absent-vs-null, timestamps

**Conflicting replay**: a second `CutoverRequest` submitted with the same
`request_id` but different field values (other than `request_state` and
`limitations`, which may legitimately be updated in place as evidence
accrues — see §36 for the persistence classification that makes this
safe) is a `digest_mismatch` failure (§31); the original request is never
silently overwritten. **Absent vs. null**: a field that is absent from the
wire payload is treated identically to an explicit `null` for every
optional field in this schema (unlike CLTR-SCHEMA-001's evidence-reference
encoding, which this contract does not alter) — **[NEW]**, chosen because
cutover requests are hand-authored/tool-generated far less frequently than
CLTR records and a stricter absent/null distinction would add operator
friction without a corresponding safety benefit; required fields (everything
except `limitations` and the not-yet-known digests before their producing
step completes) must never be absent or null. **Timestamps**: `issued_at`
is recorded as an envelope field (§24) but is excluded from `request_digest`
and from `request_id`; it is evidence-only, never identity-bearing (§28).

---

## 7. Readiness evidence package schema

### 7.1 Fields

`ReadinessEvidencePackage` binds: `package_id` (content-derived digest of
every field below except itself and `created_at`), `migration_epoch`,
`transition_id`, `target_generation_id`/`target_generation_digest`,
`source_authority_epoch_id`, `target_authority_epoch_id`, `stage1_evidence`
(id+digest+freshness, §7.2), `stage2_evidence` (id+digest+freshness),
`rollback_evidence` (id+digest+freshness), `independent_verification_evidence`
(reference to the verification phase that most recently confirmed the
target generation, e.g. an independent-verification phase report digest),
`production_output_equivalence` (boolean + evidence reference — the 135S/135T
finding that rehearsal output matches legacy output, bound not re-proven),
`entry_point_evidence` — one entry per of the four production entry points
(`run_phase_complete`, `run_task_finish`, `run_phase_report_create`,
`run_notify_send_report`), each with a coverage boolean and evidence
reference, `concurrency_readiness`, `recovery_readiness`,
`notification_readiness`, `marker_receipt_readiness`, `schema_readiness`
(→ §41's disposition table, bound by reference), `security_review_reference`,
`unresolved_findings` (array of finding IDs, must be empty for
`prerequisite_status=ready`), `prerequisite_status` — `ready | not_ready |
uncertain`, `limitations`, `package_digest` (self-excluded).

### 7.2 Freshness, common-identity binding, staleness

**Freshness**: every referenced evidence item (`stage1_evidence`,
`stage2_evidence`, `rollback_evidence`) carries its own `observed_at`
timestamp (evidence-only, not identity-bearing, §28) and its own
`source_revision`; the package is `stale` (and `prerequisite_status` must
be `not_ready`) if any referenced evidence's `source_revision` does not
match `shared_input_final_revision`'s `source_revision` for the same
`transition_id` chain. **Common-identity binding**: all evidence items must
share the same `migration_epoch`; a package that aggregates evidence across
two different `migration_epoch` values is a `migration_epoch_mismatch`
failure (§31), not a valid package. **Missing evidence**: absent required
evidence (e.g. no rollback-rehearsal evidence at all) forces
`prerequisite_status=not_ready`; it is never treated as
vacuously-satisfied. **Unknown evidence**: an evidence reference whose
`schema_id` this contract does not recognize is `invalid_schema`
(§31), fail-closed. **Superseded evidence**: an evidence item whose
referenced record has itself been superseded (per that record's own
lifecycle) invalidates the package; the package is not silently rebuilt —
producing a fresh package is a new `package_id`. **Deterministic ordering**:
array-valued fields (`unresolved_findings`, `entry_point_evidence`) are
canonically ordered by a fixed key (finding ID; entry-point name in the
frozen order `run_phase_complete, run_task_finish, run_phase_report_create,
run_notify_send_report`) before digesting, so two independently assembled
packages over identical evidence produce identical digests. **No authority
role**: `ReadinessEvidencePackage.AuthorityRole = evidence` (§32); it never
gates anything by itself — only the pre-cutover gate (135W §10) consuming
it does.

---

## 8. Human authorization schema

### 8.1 Fields

`HumanAuthorization` binds: `authorization_id` (§8.2), `principal_identity`
(operator-supplied identifier — never a token/credential, §40),
`authorization_method` (`interactive_cli | signed_artifact` — no
environment-variable method exists, consistent with 135W/135Y's explicit
bar on env-var authorization), `request_id` (→ §6), `migration_epoch`,
`source_authority_epoch_id`, `target_authority_epoch_id`,
`target_generation_id`/`target_generation_digest`,
`readiness_package_digest` (→ §7), `contract_version`, `issued_at`,
`expiry_at` (`issued_at` + the frozen 24-hour freshness window, 135W's
resolution of F-135V-8), `revocation_state` — `active | revoked`,
`used_state` — `unused | used`, `replay_binding` — a one-time nonce bound
into `authorization_digest` (§8.3), `risk_acknowledgement` — boolean, must
be `true`, `scope` — `single_request_single_target` (no broader scope
exists in v1), `limitations`, `authorization_digest` (self-excluded).

### 8.2 Determinism and the timestamp exception

`authorization_id = sha256(canonical_json({principal_identity,
authorization_method, request_id, target_generation_digest,
readiness_package_digest, replay_binding}))`. **`issued_at` and `expiry_at`
are excluded from `authorization_id`** — identity must be stable even
though the record legitimately contains wall-clock and unique
operator-generated material (the `replay_binding` nonce, which *is*
included, since it is the mechanism preventing replay, not a timestamp).

### 8.3 Freshness, expiry, revocation, one-time use, replay, replacement

**Freshness/expiry**: an authorization is usable only while
`observed_time <= expiry_at` (`observed_time` from §28's authoritative-clock
rule, never the requester's claimed time). **Revocation**: `revocation_state`
transitions `active → revoked` only; `revoked → active` is forbidden — a
revoked authorization is never reactivated, a new one must be issued.
**One-time use**: `used_state` transitions `unused → used` exactly once, at
the moment the cutover request it authorizes reaches `PublicationState =
publication_attempted` (§3.5) — not earlier (certification alone does not
consume it, §10.4) and not later (a second publication attempt against the
same request never re-consumes an already-used authorization). **Replay**:
the cutover request (§6) binds the exact `authorization_digest`, not a
timestamp or a principal name, so a replayed authorization payload with a
different digest is rejected as `identity_mismatch`, and a byte-identical
replay of an already-`used` authorization is rejected as `stale_authorization`
(§31). **Replacement authorization**: superseding an authorization requires
issuing a new `HumanAuthorization` record with a new `authorization_id`;
the request must then re-bind to the new digest — an in-place field edit
on an existing authorization is forbidden (§36, immutable
content-addressed). **Principal validation**: this contract does not define
principal identity verification (out of scope — a future
`execution-authorization` design concern per the existing `pcae
write-authorization`/`execution-authorization` command families); an
**unknown principal** is treated as `authorization_ambiguous` and fails
closed rather than being silently accepted.

---

## 9. Cutover candidate schema

### 9.1 Fields

`CutoverCandidate` binds: `candidate_id`, `request_id` (→ §6),
`target_generation_id`/`target_generation_digest`, `readiness_package_digest`
(→ §7), `authorization_digest` (→ §8), `source_authority_epoch_id`,
`target_authority_epoch_id`, `cas_expectation` (embedded, → §11),
`schema_compatibility` — the CLTR-SCHEMA-001 version the target generation
conforms to, plus this contract's own version, `candidate_state` (→
§33.3), `limitations`, `candidate_digest` (self-excluded).

### 9.2 Non-authoritative, non-identical-to-rehearsal, additional evidence

`CutoverCandidate.AuthorityRole = evidence` (never `authoritative`, §32,
§35). It is explicitly **not** the Stage 2 rehearsal generation relabelled:
a Stage 2 rehearsal generation (135Q/135R/135S) is produced and verified
under `migration_stage = atomic_rehearsal` with no cutover request, no
authorization, and no readiness package behind it — it proves the
*mechanism* works. A `CutoverCandidate` additionally requires: a
content-matching `CutoverRequest`, a passing pre-cutover gate result
(`eligible`, 135W §10) over a `ReadinessEvidencePackage`, and a valid,
unused `HumanAuthorization` — none of which a bare rehearsal generation
carries. **Additional Stage 3 evidence required beyond Stage 2**:
authorization evidence (§8), readiness-package aggregation with
freshness/common-identity checks (§7.2), and a CAS expectation snapshot
(§11) taken immediately before certification — none of which exist in the
Stage 2 rehearsal data model.

---

## 10. Certification schema

### 10.1 Fields

`Certification` binds: `certification_id`, `cutover_candidate_id` (→ §9),
`target_generation_id`/`target_generation_digest`, `request_digest` (→ §6),
`readiness_package_digest` (→ §7), `authorization_digest` (→ §8),
`source_authority_state_digest` (→ §5, the `AuthorityState.record_digest`
observed at certification time), `target_authority_epoch_id`,
`gate_result` — the frozen four-value pre-cutover gate outcome
(`eligible | ineligible | uncertain | conflict`, 135W §10, reused verbatim,
not redefined), `cas_expectation_digest` (→ §11), `verifier_identity`
(component/tool identity, not a human principal — distinct from
`HumanAuthorization.principal_identity`), `verifier_evidence` (reference to
the verification run), `certification_state` (→ §33.4), `certified_at`,
`limitations`, `certification_digest` (self-excluded).

### 10.2 Determinism, immutability, expiry/staleness, invalidation, no side effect, quarantine

**Deterministic content**: every field above except `certified_at` is
content-derived or reference-bound; `certified_at` is timestamp-evidence
only, excluded from `certification_digest`. **Approved-timestamp
treatment**: identical to §28's rule — evidence-only, never
identity-bearing. **Immutability**: a `Certification` is never edited after
issuance; a re-certification produces a new `certification_id`.
**Expiry/staleness**: a `Certification` becomes `stale_certification`
(§31) if `source_authority_state_digest` no longer matches the current
`AuthorityState.record_digest` at the moment publication is attempted —
i.e. **invalidation after authority-state change** is the staleness rule,
not a fixed time window (unlike `HumanAuthorization`'s 24-hour window,
which is a genuine freshness clock; certification staleness is a
state-comparison, not a clock comparison, because certification's safety
property is "the world hasn't moved since I certified it," not "not too
much time has passed"). **No publication side effect**: issuing a
`Certification` **must not** write to the production pointer, the
`AuthorityState` record, or `AuthorityKind` — certification is purely
evidentiary until a separate publication attempt (§12) consumes it.
**Quarantine behavior**: a `Certification` may be quarantined (§17) after
issuance if the target generation later fails integrity verification; a
quarantined certification can never be consumed by a publication attempt
(§12's CAS expectation check must reject it, §31 `quarantine_required`).

---

## 11. CAS expectation schema (embedded component)

### 11.1 Fields

`CasExpectation` (embedded inside `CutoverCandidate.cas_expectation` and
echoed inside `PublicationAttempt.cas_expectation`, §2 row 10) binds:
`expectation_id`, `migration_epoch`, `expected_authority_kind` (→ §3.1),
`expected_authority_epoch_id`, `expected_authoritative_generation`
(tagged-union identity, same shape as §5.1), `expected_authority_pointer_digest`,
`expected_authority_state_digest` (→ §5), `expected_source_lifecycle_state`
(the legacy or CLTR lifecycle state expected to still hold),
`expected_compatibility_mode` (→ §3.7), `expected_lock_or_journal_state`
(reference to the expected `RecoveryState`, §3.6, and any lock token in
force), `request_id`, `certification_id`, `expectation_digest`
(self-excluded).

### 11.2 Exact-match requirement, no wildcards

Every expected field above **must match exactly** the corresponding
observed value immediately before publication (§13's step sequence); a
**missing expected value is never a wildcard** unless the field is
explicitly declared optional in this schema (only
`expected_lock_or_journal_state` is optional, since a first-ever cutover
for an epoch has no prior lock/journal history — every other field is
mandatory). A CAS check that treats an absent expected value as
"anything matches" is non-conformant and reproduces exactly the
`_save_checkpoint`-is-atomic-write-only-not-CAS gap 135X flagged
(PREREQUISITE-135X-1) — this schema exists specifically so that gap has a
concrete, checkable structure to close against in a future implementation
phase.

---

## 12. Publication attempt schema

### 12.1 Fields

`PublicationAttempt` binds: `attempt_id`, `request_id` (→ §6),
`candidate_id` (→ §9), `certification_id` (→ §10), `cas_expectation`
(embedded echo of §11, captured at attempt time — not merely a reference,
so that a later change to the source `Certification`'s CAS snapshot cannot
retroactively alter what this attempt actually checked), `source_authority`
(tagged-union, observed at attempt start), `target_authority` (tagged
union, the value being proposed), `temporary_pointer_identity` (the
staging/temp-file identity used by the atomic rename step, CLTR-SCHEMA-001
§17), `target_authority_state_record_id` (the `AuthorityState` this
attempt will produce if successful — pre-allocated, not yet published),
`start_state` — the `PublicationState` (§3.5) observed at attempt start
(always `certified` for a first attempt), `attempted_operation` — always
`"cas_publish"` in v1 (no other operation kind exists yet), `attempt_sequence`
— monotonically increasing per `request_id`, `publication_state` (→ §3.5,
the outcome of *this* attempt), `error_classification` (→ §31, nullable),
`uncertainty` (boolean + reason), `attempted_at`, `completed_at` (nullable),
`limitations`, `attempt_digest` (self-excluded).

### 12.2 Retry vs. replay, multiple attempts, idempotency

**Retry vs. replay**: a **retry** is a new `PublicationAttempt` with
`attempt_sequence = n+1` for the same `request_id`, issued after a prior
attempt reached `publication_uncertain` or `conflict` and RecoveryState
(§3.6) classified it `retry_required`; a **replay** is re-submission of the
*same* attempt payload (same `attempt_id`) and must be idempotent — the
second submission observes the first attempt's already-recorded outcome
rather than re-executing the CAS. **Multiple attempts**: yes, multiple
`PublicationAttempt` records may exist for one `request_id` (one per
`attempt_sequence`); at most one may ever reach `PublicationState =
published` or `verified` — a second attempt reaching `published` while an
earlier one already did is a `concurrency_conflict` (§14), never silently
accepted. **Idempotency**: `attempt_id = sha256(canonical_json({request_id,
attempt_sequence, cas_expectation.expectation_digest}))` — re-submitting an
identical attempt payload yields the same `attempt_id` and must not create
a duplicate record or perform the CAS twice.

---

## 13. Publication evidence schema

### 13.1 Fields

`PublicationEvidence` binds: `evidence_id`, `attempt_id` (→ §12),
`pointer_state_before` (full pointer content, digested), `pointer_state_after`
(full pointer content, digested; equal to `pointer_state_before` unless the
outcome is `published`), `target_readback` (re-read of the target
generation immediately after publication, verifying digest match),
`authority_state_readback` (re-read of the newly written `AuthorityState`,
§5), `target_generation_verification` (integrity check result over the
target generation's manifest, CLTR-SCHEMA-001 §16), `cas_result` — 
`accepted | rejected`, `publication_outcome` (§13.2), `uncertainty`
(boolean + reason — **never collapsed into `publication_failed`**),
`winner_loser_state` (nullable — populated only when a concurrency
conflict, §14, determined a winner), `recovery_requirement` (→ §3.6),
`evidence_digest` (self-excluded).

### 13.2 Allowed outcomes (exact)

`not_attempted | cas_rejected | published_and_verified | publication_failed
| publication_uncertain | conflict | quarantined`. Exactly these seven
values, no others. **`publication_uncertain` is a distinct, first-class
value** — a crash, timeout, or ambiguous readback after the CAS operation
was issued but before its result could be confirmed **must** produce
`publication_uncertain`, never `publication_failed` (which is reserved for
a *confirmed* negative outcome, e.g. `cas_result=rejected` with a clean
readback proving nothing changed) and never `published_and_verified`
(which requires both a confirmed CAS acceptance and a passing independent
readback). This is the schema-level enforcement of CLTR-CUTOVER-001's
already-stated principle that uncertainty must never be silently resolved
in either direction.

---

## 14. Concurrency conflict schema

### 14.1 Coverage and fields

Covers: cutover-vs-cutover, cutover-vs-finalization, cutover-vs-recovery,
cutover-vs-Stage-2-publication, cutover-vs-rollback, stale process, stale
authorization, stale certification, stale CAS expectation. `ConcurrencyConflict`
binds: `conflict_id`, `conflicting_actors` (array of actor descriptors —
process/session identity, never a human name), `request_ids` (array, one
per involved request), `authority_state_observed` (digest reference),
`expected_state` (reference to whichever CAS expectation or
authorization/certification staleness check failed), `actual_state`
(what was actually observed), `winner` (nullable request ID — populated
only when a deterministic winner rule, e.g. first successful CAS, applies),
`loser_classification` — `rejected_cleanly | rejected_with_side_effect |
undetermined`, `authority_result` — the `AuthorityState` reference that
prevailed, `recovery_requirement` (→ §3.6), `conflict_digest`
(self-excluded), `limitations`.

`ConcurrencyConflict.AuthorityRole = evidence` (§32) — conflict evidence is
**never authoritative**; it documents what happened, it does not decide
what happens next (that is the recovery journal's and, ultimately, an
operator's role).

---

## 15. Recovery journal schema

### 15.1 Entry schema and aggregate view

One entry schema, `RecoveryJournalEntry`: `journal_id`, `request_id` (→ §6),
`operation_id` (references whichever of §9–§13's operations produced this
entry), `phase`, `transition_id`, `migration_epoch`, `authority_epoch_id`,
`prior_journal_state` (nullable — null only for the first entry of a
chain), `new_journal_state` (→ RecoveryState, §3.6), `authority_state_at_entry`
(digest reference, → §5), `generation_binding` (target generation identity),
`publication_attempt` (nullable reference, → §12), `external_effect_state`
— `none | pointer_written | notification_dispatched | receipt_written`
(the set of externally visible side effects known to have occurred at this
entry — critical for recovery classification, since a crash after
`notification_dispatched` has different safe-recovery options than one
before it), `marker_state` (nullable reference), `receipt_state` (nullable
reference), `retry_classification` (reuses the frozen four-value
`retry_classification` enum, CLTR-SCHEMA-001 §3.4, not redefined),
`operator_review_required` (boolean), `recovery_action` — free text,
required when `operator_review_required=true`, `entry_sequence`
(monotonic per `journal_id` chain), `entry_timestamp`, `entry_digest`
(self-excluded), `previous_entry_digest` (nullable; see §15.2).

The **aggregate/current-journal view** is a **derived view** (§36), not a
second schema: it is the ordered projection of all entries sharing one
journal chain, computed by traversal, with a `current-recovery-journal`
pointer (§37) identifying the chain's latest entry by `journal_id` +
`entry_sequence`. No separate persisted "aggregate record" schema exists.

### 15.2 Hash chaining — frozen decision

**[NEW] Frozen decision: hash chaining IS mandatory.** Each entry's
`previous_entry_digest` **must** equal the prior entry's `entry_digest`
(null only for the chain's first entry). Rationale, weighed explicitly
against the "do not add it automatically" instruction: tamper evidence
matters here specifically because the recovery journal is the **only**
record that reconstructs what externally-visible side effects (pointer
writes, notification dispatch, receipt writes) occurred during a crash —
unlike every other record family in this contract, which is either
immutable-by-digest already (readiness package, certification, publication
evidence, conflict, quarantine) or governed by an atomic single-writer
pointer (authority state), the recovery journal is **append-only under
concurrent, possibly-crashing writers**, which is exactly the condition
under which silent truncation or partial-write corruption is most likely
and most dangerous (a truncated journal could hide that a notification was
already dispatched, causing PFN-001's exactly-once guarantee to be
violated by a recovery path that does not know dispatch already happened).
Hash chaining gives a cheap, mechanical truncation-detection check (does
the latest entry's chain validate back to a known-good anchor?) without
requiring a separate consensus or locking mechanism, which this contract
explicitly does not introduce (§ "must not implement CAS or locking").
**Crash recovery / partial writes**: an entry write is atomic (write-temp,
fsync, rename — same primitive as CLTR-SCHEMA-001 §17's publication
sequence, reused not reinvented); a partial write leaves no new entry
appended, and the chain's last valid entry remains the latest.
**Deterministic reconstruction**: the aggregate view is always
recomputable by re-traversing the chain from the anchor; no cached
aggregate state may diverge from a fresh traversal. **Latest-journal
pointer**: `current-recovery-journal` is classified `operational` (§37),
never `authority-bearing`.

---

## 16. Reconciliation result schema (derived view)

### 16.1 Fields (output shape, not a persisted schema)

`ReconciliationResult` reports: `requested_phase_or_transition`,
`migration_epoch`, `current_authority` (→ §3.1, read from the pointer, not
from `AuthorityState`), `authority_epoch_id`, `authoritative_generation`
(identity), `pointer_verification` — `verified | mismatch | unreadable`,
`authority_state_verification` — `consistent | inconsistent | absent`,
`publication_evidence` (reference, nullable), `journal_state` (→ RecoveryState),
`report_state`, `metadata_state`, `architecture_status_state`,
`checkpoint_state`, `notification_state`, `marker_state`, `receipt_state`,
`conflicts` (array, → §14), `blockers` (array), `uncertainty`,
`required_operator_action` (nullable), `mutation: "none"` (a literal
constant field, always present, always `"none"` — this is the schema-level
enforcement of "reconciliation must not itself repair authority"),
`result_digest` (present only if a caller chooses to persist a snapshot of
the result for audit purposes — the schema itself is not persisted by
default, matching the existing `pcae phase-report reconcile` command's
behavior, which computes and prints without writing a new file).

### 16.2 Why derived, not persisted

Precisely analogous to CLTR-SCHEMA-001's Architecture Status representation
kind (D-role, no own identity or digest, fully regenerable from other
records) and to the already-implemented `pcae phase-report reconcile
--phase-id <id>` command (confirmed read-only, `mutation: none`, in this
phase's own §"Initial inspection" run). Persisting a
`ReconciliationResult` as durable authority-relevant state would create
exactly the kind of second authority-adjacent record this contract
prohibits (§35); it remains computable on demand from `AuthorityState`,
`PublicationEvidence`, the recovery journal, and the existing
report/metadata/marker/receipt records.

---

## 17. Quarantine schema

### 17.1 Fields

`QuarantineRecord` binds: `quarantine_id`, `object_type` — enum over every
quarantinable family (`cutover_candidate | certification | publication_attempt
| authoritative_generation | readiness_package | authorization`),
`object_id`, `source_reference` (id + digest of the quarantined object —
**never a bare path**, §39), `reason_code` (→ §31's failure vocabulary,
a subset applies), `authority_relevance` — `blocks_readiness |
blocks_publication | blocks_authority_confirmation | historical_only`,
`failed_verification` (reference to whichever integrity/verification check
failed), `observed_authority_state` (digest reference, → §5),
`request_or_candidate_or_certification_binding` (whichever of §6/§9/§10
this quarantine attaches to), `quarantined_at`, `disposition_state` —
`quarantined | under_review | remediated_superseded | permanently_retired`,
`limitations`, `quarantine_digest` (self-excluded).

### 17.2 Behavior when each object kind is quarantined

- **Candidate quarantined** (§9): the candidate can never reach
  certification; a new candidate must be produced from a corrected input.
- **Certification quarantined** (§10): any `PublicationAttempt` referencing
  it must reject at the CAS-expectation check (§11.2) with
  `quarantine_required`; certification quarantine after a *successful*
  publication does not retroactively un-publish (§17.3 handles the
  authoritative-generation case separately).
- **Publication attempt quarantined**: only possible for an attempt whose
  outcome was `publication_uncertain` or `conflict`; a `published_and_verified`
  attempt's evidence is never itself quarantined (see below for what
  happens if the *generation* it published later fails verification).

### 17.3 Current authoritative generation fails integrity verification

**This case must not silently leave no authority, and must not silently
reactivate legacy.** Per the requested fallback rule: if this contract
cannot yet safely resolve it, it is classified a **future activation
prerequisite** rather than resolved ad hoc here. **Frozen classification
[NEW]**: this is exactly that case. This document freezes only the
*detection and disclosure* contract — the generation is marked
`quarantined_generation` (§3.4), `AuthorityState.verification_state`
becomes `verification_failed`, `RecoveryState` becomes
`operator_review_required` (never an automatic value), and
`AuthorityKind` **does not change** (it remains whatever it was — `cltr` —
because reverting to `legacy` automatically would itself violate the
single-authority invariant by defining an undocumented automatic
authority-reversal mechanism CLTR-CUTOVER-001 never authorizes). The
*resolution* mechanism (how a human operator safely re-establishes a valid
authoritative generation after this state is reached) is registered as
**PREREQUISITE-135Z-1** in §45 and is explicitly out of scope for
implementation-readiness until a future activation-adjacent phase defines
it — consistent with 135W's own PREREQ register pattern of deferring
mechanisms this contract cannot yet safely specify.

---

## 18. Authority transition receipt

**Determination: not required as a dedicated fourth record family.**
Rationale: the three bindings that a hypothetical dedicated receipt would
carry — source/target authority, cutover request/certification/publication
evidence, and final outcome — are already fully carried, without
duplication, by: (a) `AuthorityState` (§5, current authority + source
transition + publication evidence reference), (b) `PublicationEvidence`
(§13, the definitive outcome record for a specific attempt), and (c) the
existing PFN-001/CLTR-SCHEMA-001 receipt representation kind, extended via
the Finalization Receipt Authority Binding (§21). A fourth record would
either duplicate these three or become, in practice, a second
authority-adjacent pointer — exactly the risk §37 (pointer inventory)
guards against. Any future report or audit view that wants "the one-page
summary of a completed cutover" should be a **derived view** composed from
(a)+(b)+(c), not a new persisted schema.

---

## 19. Notification authority binding

### 19.1 Fields

`NotificationAuthorityBinding` binds: `intent_id` (references the existing
notification-intent identity, extraction §14 — `notification_intent_candidate.json`
naming precedent from Stage 2 is not reused verbatim in production but the
concept is), `authoritative_generation` (identity reference, → §5),
`authority_epoch_id`, `payload_digest` (digest of the notification payload
content actually derived from the authoritative generation),
`attempt_identity` (reference into PFN-001's existing dispatch-attempt
tracking — not redefined here), `pfn_001_classification` — the
notification's classification per PFN-001 §5/§8 (unchanged vocabulary,
bound not redefined), `authorization_state` (nullable — most notifications
require no separate human authorization; only Stage-3-cutover-triggered
notifications reference §8's `HumanAuthorization`), `delivery_state`
(mirrors PFN-001's existing delivery states, bound not redefined),
`uncertainty`, `marker_binding` (→ §20), `receipt_binding` (→ §21),
`limitations`.

### 19.2 Placement decision

**[NEW] Frozen decision**: this binding is a **companion schema today**
(realizing the "existing-schema extension" classification from §2 without
touching CLTR-SCHEMA-001 in this phase). It is **not** embedded inside the
authoritative generation (the generation's content must remain independent
of which notification attempts reference it — many attempts may reference
one generation, e.g. retries) and **not** embedded inside
`PublicationEvidence` (which is scoped to the CAS/pointer outcome, not to
notification dispatch, a logically separate concern per PFN-001's own
separation of concerns). A future CLTR-SCHEMA-001 minor revision **may**
fold this binding directly into representation kind #8 (notification
payload) once Stage 3 companion schemas are implemented and proven; §41
registers this as a disposition-table item, not a decision made today.

---

## 20. Marker authority binding

### 20.1 Fields

`MarkerAuthorityBinding` binds: `marker_id` (existing identity, unchanged),
`authoritative_generation` (identity reference), `generation_digest`,
`authority_epoch_id`, `notification_intent` (reference, → §19),
`delivery_attempt` (reference), `delivery_outcome`, `compatibility_source`
— `legacy | cltr` (which system's marker semantics apply — see §20.2),
`marker_schema_version`, `marker_digest`.

### 20.2 Legacy markers after cutover

Legacy markers written before an authority epoch's cutover remain valid
historical records (`AuthorityRole = historical`, §32) and are never
rewritten or deleted (§23, no historical-artifact rewriting). New markers
written after cutover for that epoch carry `compatibility_source: "cltr"`
and this binding's fields; PFN-001's exactly-once marker semantics
(`.last-notified.json`-equivalent uniqueness) are unchanged — this binding
adds authority-disclosure metadata to the marker's payload, it does not
change how markers are compared for idempotency. **A marker must never
independently establish authority** — this contract's authority resolver
(CLTR-CUTOVER-001 §4) never consults marker state to determine
`AuthorityKind`.

---

## 21. Finalization receipt authority binding

### 21.1 Fields

`FinalizationReceiptAuthorityBinding` binds: `authoritative_generation`
(identity reference), `generation_digest`, `authority_epoch_id`,
`publication_evidence_id` (→ §13), `report_digest`, `metadata_digest`,
`architecture_status_reference` (D-role, no digest of its own — a pointer
to the regenerable view, consistent with CLTR-SCHEMA-001's existing
treatment of Architecture Status), `checkpoint_state`, `notification_state`,
`marker_id` (→ §20), `recovery_state` (→ §3.6), `finalization_state`,
`contract_version`, `receipt_digest`.

### 21.2 Extension vs. companion binding

**Determination**: the existing receipt schema **is not modified in
135Z**, per the explicit governed prohibition on modifying
CLTR-SCHEMA-001 or executable schemas in this phase. Whether a future
phase extends the receipt schema in place or keeps this as a permanent
separate companion binding is registered in §41's disposition table as an
open schema-evolution question for the executable-schema implementation
phase, not resolved here. Either resolution is compatible with this
contract, provided the binding fields above are present in the final
representation by whichever mechanism.

---

## 22. Compatibility state schema

### 22.1 Fields

`CompatibilityState` binds: `compatibility_state_id`, `authority_epoch_id`,
`legacy_component` (identifies which legacy subsystem this state describes
— finalization transaction, entry points, etc.), `role` (→ §32's
`AuthorityRole`, always `compatibility` for this family), `allowed_reads`
(enumerated set of read operations legacy may still perform),
`forbidden_authority_behavior` (explicit enumerated prohibitions — e.g.
"must not write the production pointer", "must not be consulted by the
authority resolver as a source of `AuthorityKind`"), `fallback_state` —
`none | read_only_fallback` (never `authoritative_fallback` — no such
value exists in this enum, by design), `historical_support` (boolean —
whether legacy still serves historical-read requests for pre-cutover
data), `migration_stage` (→ §3.3), `disablement_state` — `enabled |
disabled`, `retirement_eligibility` — `not_eligible | eligible_pending_governed_phase`
(retirement itself is always a separately governed future phase, never
automatic), `limitations`, `compatibility_state_digest` (self-excluded).

### 22.2 Never reactivates legacy authority

**Structural enforcement**: `CompatibilityState` has no field capable of
setting `AuthorityKind` back to `legacy` — the schema simply omits any such
field, so no conformant implementation can derive authority reactivation
from a compatibility-state write. This is the schema-level counterpart to
§3.7's enum-level rule.

---

## 23. Historical authority reference (runtime-only typed model)

### 23.1 Scope and shape

`HistoricalAuthorityReference` is a typed lookup shape (not a persisted
schema) over: pre-CLTR phases (by phase ID), shadow-era phases (Stage 0),
Stage 1 phases/evidence (by `transition_id`/evidence ID+digest), Stage 2
evidence (rehearsal-generation ID+digest), post-cutover phases, old
reports/markers/receipts/checkpoints (by their existing identity fields).
Every reference is `{reference_kind, identity, digest_if_available,
schema_id_and_version, limitations}`.

### 23.2 Constraints

Historical references **must** be explicit (no implicit "look at whatever
is oldest" resolution), read-only, non-authoritative for current
transitions (never consulted by the authority resolver), schema/version
aware (a reference to a pre-135J CLTR-SCHEMA-001 v1.0.0 record must
disclose that version, not silently normalize it to v1.0.1), and
limitation-bearing (a reference to an artifact this contract cannot fully
verify — e.g. a pre-Stage-1 legacy-only phase with no CLTR-shaped
identity at all — must say so, not omit the field). **No historical
artifact is rewritten.**

---

## 24. Shared envelope

### 24.1 Mandatory-for-all fields

Every companion record defined in §5–§22 (i.e. every family classified
"required companion schema" or "existing-schema extension" in §2) carries:
`schema_id`, `schema_version`, `record_type`, `record_id` (the
family-specific identity field, aliased into this common name for
cross-family tooling), `migration_epoch`, `contract_version`, `limitations`,
`authority_disclosure` (→ §32), `record_digest` (self-excluded).

### 24.2 Conditional fields

`phase_id` and `transition_id` are mandatory wherever the record is scoped
to a specific transition (all families except `AuthorityEpoch`, which is
scoped to a migration epoch rather than a single transition, and
`CompatibilityState`, which is scoped to a legacy component rather than a
transition) — these two families instead carry `creation_transition`/
`legacy_component` as their scoping field, and `phase_id`/`transition_id`
are absent, not null, for them. `authority_epoch_id` is mandatory wherever
the record concerns a specific epoch (all families except
`ConcurrencyConflict`, which may span two epochs during a cross-epoch
conflict and instead carries `request_ids` referencing each side's epoch).
`created_time` (the envelope-level generic timestamp) is present on every
record but is **evidence-only** per §28 unless a family's own section
above explicitly includes it in that family's digest (none do — every
family excludes its own creation timestamp from its content digest, for
consistency). `source_revision`/`final_input_revision` are mandatory only
on families that bind to a `SharedTransitionInputPackage`
(`CutoverRequest`, `ReadinessEvidencePackage`, `CutoverCandidate`,
`Certification`) — irrelevant, and therefore absent, elsewhere (e.g.
`AuthorityEpoch`, `CompatibilityState`, `QuarantineRecord` when quarantining
an authorization rather than a generation).

Irrelevant fields are never forced into a record merely for envelope
uniformity — e.g. `AuthorityEpoch` does not carry a `request_id` field,
since not every epoch results from a cutover request (the first-ever
legacy epoch of a repository does not).

---

## 25. Identity rules

### 25.1 Classification per family

| Family | Identity class |
|---|---|
| AuthorityEpoch | content-derived deterministic |
| AuthorityState | operation-derived deterministic (derived from the publication attempt that produced it; not independently content-addressed, since two publications could otherwise legitimately produce byte-identical state content at different times) |
| CutoverRequest | content-derived deterministic |
| ReadinessEvidencePackage | content-derived deterministic |
| HumanAuthorization | content-derived deterministic (timestamp-excluded) plus operator-issued replay-binding nonce (§8.2) |
| CutoverCandidate | content-derived deterministic |
| Certification | operation-derived deterministic (bound to the certifying operation, timestamp-excluded) |
| CasExpectation | operation-derived deterministic |
| PublicationAttempt | operation-derived deterministic (§12.2 formula) |
| PublicationEvidence | operation-derived deterministic (bound 1:1 to its `attempt_id`) |
| ConcurrencyConflict | operation-derived deterministic (bound to the detecting operation and the colliding request IDs) |
| RecoveryJournalEntry | sequence-derived (per-chain `entry_sequence`) plus content-derived `entry_digest` |
| QuarantineRecord | operation-derived deterministic (bound to the quarantining operation and the quarantined object's identity) |
| CompatibilityState | content-derived deterministic |
| HistoricalAuthorityReference | historical reference (no new identity minted — reuses the referenced artifact's own identity) |

### 25.2 Per-class rules

For every content-derived and operation-derived family: **included
inputs** are exactly the fields enumerated in that family's own §-section
above (minus the digest/identity field itself and minus timestamp fields
unless explicitly stated otherwise, e.g. `HumanAuthorization.replay_binding`
is included though it is unique operator-generated material — uniqueness
is not the same as being a timestamp). **Excluded inputs**: all
`created_time`/`*_at` timestamp fields, all free-text `limitations`
fields (limitations may be appended/clarified without changing identity —
**[NEW]**, chosen so that a record's evidentiary identity is not
accidentally broken by adding a clarifying note), and `record_digest`
itself. **Timestamp behavior**: evidence-only everywhere (§28).
**Random material**: forbidden as a sole identity input anywhere in this
contract; where unique material is required (only `HumanAuthorization`'s
nonce), it is operator-issued and explicitly included, never silently
generated and silently excluded. **Replay behavior**: identical inputs
must always yield identical identity (true determinism) — a record whose
identity function is not referentially transparent is non-conformant.
**Conflict behavior**: per family, specified in that family's own section
(§6.3, §8.3, §12.2, etc.); the general default absent a family-specific
rule is `digest_mismatch` rejection, never silent overwrite.

**Canonical string format**: every identity is a lowercase hexadecimal
SHA-256 digest string, exactly 64 characters, character set `[0-9a-f]`
(§26, §27) — no other identity format (UUIDs, incrementing integers,
human-readable slugs) is used for any family's primary identity field in
this contract, except `RecoveryJournalEntry.entry_sequence`, which is a
non-negative integer by design (it is explicitly sequence-derived, not
content-derived, per §25.1).

**No canonical authority identity may depend on**: current working
directory, process ID, environment variable ordering, locale, file
modification timestamps, or recent Git history. This is a structural
property of every formula given above — none references any of these
inputs — and is additionally a mandatory verification-matrix item (§45).

---

## 26. Canonicalization profile

This contract **reuses CLTR-SCHEMA-001's canonicalization profile
(§14) in full, without modification**, for every companion record defined
above:

- UTF-8 encoding.
- Unicode **NFC** normalization (CLTR-SCHEMA-001 §14.4).
- JSON object keys sorted **lexicographically, byte-wise ASCII**, at every
  nesting level (§14.1).
- Collection (array) ordering: preserved as authored **except** where a
  family's own section above specifies a canonical sort key for digesting
  purposes (§7.2's `unresolved_findings`/`entry_point_evidence` ordering,
  §15.1's entry-sequence ordering) — arrays without a specified sort key
  are never silently re-ordered.
- Compact JSON, no insignificant whitespace (§14.2).
- Number formatting, boolean formatting, absent-vs-null, newline handling:
  identical to CLTR-SCHEMA-001 §14.5–§14.7.
- **Path normalization [NEW, justified difference]**: any field containing
  a filesystem path (none of this contract's identity-bearing fields do,
  by design — paths appear only in `limitations` free text and in the
  namespace layout §38, never as digested identity input) must be
  POSIX-style, relative to the repository root, with no `..` segments and
  no symlink resolution assumed — this is a Stage-3-specific addition
  because CLTR-SCHEMA-001's records never embedded raw paths at all; the
  difference is additive, not conflicting.
- Timestamp format/timezone: **UTC, RFC 3339, second precision** — same
  rule as CLTR-SCHEMA-001's existing temporal fields, extended (not
  changed) to every new evidence-only timestamp defined above (§28
  elaborates authoritative-vs-evidence distinction; the *format* is
  uniform regardless of role).
- Duplicate-key rejection, unknown-field behavior, enum casing (`snake_case`
  wire values throughout, matching every enum defined in §3): identical to
  CLTR-SCHEMA-001 §14, §22/§23 conventions, extended per §30 below.
- Deterministic serialization: guaranteed by the above rules combined,
  identical guarantee CLTR-SCHEMA-001 already provides.

No canonicalization rule in this contract diverges from CLTR-SCHEMA-001
except the path-normalization addition above, which is additive (a rule
for a field type CLTR-SCHEMA-001 never had) rather than a conflicting
override.

---

## 27. Digest profile

- **Algorithm**: SHA-256, unchanged from CLTR-001/CLTR-SCHEMA-001 (§15.1) —
  no existing binding contract requires a different algorithm for any
  companion-record family.
- **Encoding**: lowercase hexadecimal string (§25.2).
- **Record-level digest coverage**: every field of the record's canonical
  JSON representation **except** the digest field itself (self-exclusion,
  identical rule to CLTR-SCHEMA-001 §15.2–§15.4) and except any field a
  family's own section explicitly excludes (timestamps, `limitations` —
  §25.2).
- **Manifest-level coverage**: not applicable to companion records
  individually — manifest-level digesting (allow-listed file list +
  per-file digest + `manifest_digest`) remains scoped to the authoritative
  generation itself (CLTR-SCHEMA-001 §16), never to companion records,
  which are referenced *by* the generation's evidence trail but are not
  *part of* its manifest.
- **Excluded fields**: enumerated per family above; the universal excluded
  set across all families is `{record_digest itself, created_time/*_at
  timestamps, limitations}`.
- **Timestamp inclusion/exclusion**: excluded everywhere (§25.2, §28).
- **Nested-record references**: companion records reference each other
  **by ID and digest**, never by embedding the full child object, with
  exactly one deliberate exception — `PublicationAttempt.cas_expectation`
  and `CutoverCandidate.cas_expectation` **embed** the full
  `CasExpectation` object (§11) rather than referencing it, because
  `CasExpectation` is defined as an embedded-only component with no
  independent persistence (§2 row 10) — there is nothing to reference by
  ID, so embedding is the only option, and it is captured at each
  embedding site's own time (§12.1's rationale) rather than shared by
  reference.
- **Path inclusion**: paths are never digest inputs for any
  identity-bearing field (§26).
- **Schema/version inclusion**: `schema_id`/`schema_version`/
  `contract_version` are included in each record's content digest (they
  are ordinary content fields, not excluded), so a schema-version bump
  changes a record's digest — correct, since the record's meaning has
  changed.
- **Authority disclosure inclusion**: `authority_disclosure` (§32) is
  included in the content digest — it is a substantive, not incidental,
  field.
- **Cross-record binding**: achieved exclusively via ID+digest pairs
  (e.g. `target_generation_id` + `target_generation_digest` appearing
  together everywhere a generation is referenced) — a bare ID without its
  paired digest is never sufficient to bind a cross-record reference in
  this contract; every reference field name ending in `_id` that denotes
  a cross-record binding (as opposed to this record's own identity) has a
  sibling `_digest` field.
- **Digest substitution behavior**: a reference whose paired digest does
  not match the referenced record's actual current `record_digest` is a
  `digest_mismatch` failure (§31), fail-closed — never silently accepted
  as "close enough" or re-resolved by ID alone.

---

## 28. Temporal model

### 28.1 Timestamp kinds

Observed time (the clock reading recorded when a check/read occurred —
`observed_time` used throughout §8.3, §16.1), issued time
(`HumanAuthorization.issued_at`, `CutoverRequest`'s envelope `issued_at`),
expiry time (`HumanAuthorization.expiry_at`), publication-attempt time
(`PublicationAttempt.attempted_at`), publication-confirmed time
(`PublicationAttempt.completed_at`, `PublicationEvidence`'s implicit
confirmation moment), external-delivery time (notification dispatch
timestamps, bound from PFN-001's existing mechanism, not redefined),
reconciliation time (`ReconciliationResult`'s implicit "as of" moment,
never persisted as a field since the result itself is not persisted by
default), historical-record time (whatever timestamp the referenced
historical artifact already carries, per §23 — never re-stamped).

### 28.2 Rules

**Authoritative timestamps**: none. **No timestamp in this contract
establishes or is required for authority** — `AuthorityKind`, `PublicationState`,
and every state-machine transition in §33 are driven by explicit state
values and digest/CAS comparisons, never by "the most recent timestamp
wins" logic. **Evidence-only**: every timestamp listed in §28.1 is
evidence-only, without exception. **Identity effect**: none — every
identity formula in §25 explicitly excludes timestamps. **Digest effect**:
none, per the same exclusion (§27). **Allowed precision**: second
(RFC 3339, §26). **UTC requirement**: mandatory for every timestamp field
in every companion record — no local-timezone timestamps are permitted.
**Monotonicity expectations**: `attempt_sequence` (§12) and
`entry_sequence` (§15) are the monotonic counters this contract relies on
for ordering; wall-clock timestamps are explicitly **not** relied upon for
ordering guarantees, since clock skew across processes/machines is
possible and must not be able to reorder authority-relevant state.
**Clock-skew handling**: because no timestamp is authority-bearing,
skew cannot corrupt authority state; skew can only make evidence *look*
temporally inconsistent, which is a `stale_*` diagnostic concern (§31),
not a correctness failure. **Missing-time behavior**: an absent
non-mandatory timestamp (e.g. `PublicationAttempt.completed_at` while an
attempt is still in flight) is valid and expected; an absent *mandatory*
timestamp (e.g. `HumanAuthorization.issued_at`) is `invalid_schema` (§31).

---

## 29. Source and revision binding

Every companion record scoped to a transition (§24.2) mandatorily binds:
repository identity (via the existing repository-identity field already
used by CLTR-001/production records — not redefined here), `phase_id`,
`transition_id`, `migration_epoch`, `authority_epoch_id`,
`source_revision` (from the bound `SharedTransitionInputPackage`),
`shared_input_final_revision`, `target_generation_id`+digest (where
applicable to that family), `contract_version`, `schema_version`. A
record presented with a revision binding that does not match the current
`SharedTransitionInputPackage` for its `transition_id` is rejected with
`revision_mismatch` (§31) — records are never accepted with a
best-effort or partial revision match. **Revisions are never derived from
recent Git history** — they come exclusively from the existing
`SharedTransitionInputPackage`/`SharedInputRevision` mechanism (extraction
§12), which itself sources `source_revision` from explicit
pre-transaction/legacy-completion observation, not from `git log`.

---

## 30. Unknown-field and version behavior

- **Unknown required fields** (a required field this contract defines is
  missing from a wire payload): `invalid_schema`, fail-closed.
- **Unknown optional fields** (a payload includes a field this contract
  does not define): rejected for every **authority-bearing or
  activation-relevant** family (`AuthorityEpoch`, `AuthorityState`,
  `CutoverRequest`, `HumanAuthorization`, `Certification`,
  `PublicationAttempt`, `PublicationEvidence`, `CasExpectation`) —
  fail-closed, no silent pass-through, consistent with the brief's
  explicit instruction that these families must fail closed on unknown
  critical fields. For purely evidentiary/historical families
  (`ReadinessEvidencePackage`, `ConcurrencyConflict`, `QuarantineRecord`,
  `CompatibilityState`, `HistoricalAuthorityReference`), an unknown
  optional field **may** be preserved verbatim under a reserved
  `_extensions` envelope key without being interpreted, but never silently
  merged into a recognized field.
- **Unknown enum values**: fail-closed for every enum in §3, without
  exception — this contract defines no enum with a permissive
  "unknown/other" catch-all value, since every enum here gates an
  authority-adjacent decision.
- **Unsupported major version**: rejected outright (`unsupported_version`).
- **Newer minor version**: accepted only if every field this contract's
  frozen version requires is present and recognizable — a newer minor
  version may add optional fields a v1.0 reader ignores (under the
  `_extensions` rule above for evidentiary families; rejected outright for
  authority-bearing families, since "ignore unknown optional field" is
  itself the behavior explicitly barred for those families).
- **Missing schema ID / missing version**: `invalid_schema`, fail-closed.
- **Duplicate fields**: rejected at parse time (duplicate-key rejection,
  §26, inherited from CLTR-SCHEMA-001 §14).
- **Ambiguous null**: for authority-bearing families, `null` is never
  ambiguous with "absent" — §6.3's absent-vs-null relaxation applies only
  to `CutoverRequest`'s own optional fields (a narrow, explicitly scoped
  exception), not to any other authority-bearing family.
- **Compatibility extension points**: only the `_extensions` envelope key
  for evidentiary/historical families, as above; no other extension
  mechanism exists in v1.

---

## 31. Error and failure vocabulary

Shared reason codes (stable machine values; human explanation follows
each):

| Code | Human explanation |
|---|---|
| `invalid_schema` | Payload does not conform to the record's required shape (missing required field, wrong type, missing schema ID/version). |
| `unsupported_version` | Payload declares a schema/contract major version this reader does not support. |
| `identity_mismatch` | A computed identity does not match a claimed identity, or a replayed payload's content differs from the original under the same claimed ID. |
| `phase_mismatch` | A record's `phase_id` does not match the phase context it is being evaluated in. |
| `transition_mismatch` | A record's `transition_id` does not match the transition it is bound to. |
| `migration_epoch_mismatch` | Records or evidence spanning more than one `migration_epoch` were combined where a single epoch was required. |
| `authority_epoch_mismatch` | A record's `authority_epoch_id` does not match the epoch context expected by its consumer. |
| `revision_mismatch` | A record's bound revision does not match the current `SharedTransitionInputPackage` revision for its transition. |
| `digest_mismatch` | A referenced record's actual digest does not match the digest supplied alongside its ID. |
| `stale_authorization` | A `HumanAuthorization` is expired, revoked, already used, or replayed. |
| `stale_certification` | A `Certification`'s bound `source_authority_state_digest` no longer matches current `AuthorityState`. |
| `stale_writer` | A writer's held CAS expectation no longer matches observed state (a class of `cas_rejected`, surfaced with writer-identity context). |
| `cas_rejected` | The compare-and-swap comparison failed; the write did not occur. |
| `publication_uncertain` | The outcome of a publication attempt could not be confirmed either way. |
| `concurrency_conflict` | Two or more actors' operations collided; see `ConcurrencyConflict` (§14). |
| `quarantine_required` | The object being consumed has been quarantined and must not be treated as valid input. |
| `recovery_required` | The recovery journal indicates this request/operation cannot proceed without a recovery step. |
| `authority_ambiguous` | More than one candidate for current authority was observed (a direct violation this contract's schemas are designed to prevent, but which must still fail closed if it somehow occurs). |
| `authority_missing` | No authority could be resolved at all (distinct from `authority_ambiguous` — too few, not too many). |
| `wrong_generation` | A reference resolved to a generation different from the one expected. |
| `incompatible_legacy_state` | Legacy's observed state is incompatible with the `CompatibilityMode` this contract expects for the current epoch. |
| `notification_uncertain` | A notification's delivery/authority binding could not be confirmed. |
| `marker_conflict` | Two markers claim inconsistent authority-binding state for the same delivery. |
| `receipt_conflict` | Two receipts claim inconsistent finalization state for the same transition. |

Every code above is machine-stable (never renamed once frozen); the human
explanation column may be clarified in a future MINOR revision of this
contract without changing the code.

---

## 32. Authority disclosures

### 32.1 Encoding

Every companion record's envelope (§24.1) carries `authority_disclosure`,
a struct: `{authority_role: <AuthorityRole>, is_authoritative: false
(literal constant for every family in this contract — see §35),
disclosure_text: <free text>}`. **A record may not silently imply
authority by filename, directory location, or record type name** — the
`authority_disclosure` field is the single mandatory, machine-checkable
place authority relevance is declared; tooling must never infer authority
from path conventions alone (§38, §39 reinforce this for the namespace and
security profiles respectively).

### 32.2 Mapping to CLTR-SCHEMA-001's existing `authority_role`

| This contract's `AuthorityRole` (§3.2) | Closest CLTR-SCHEMA-001 `authority_role` code (§0.2) | Note |
|---|---|---|
| `authoritative` | `S` (sole) | Reserved for the authoritative generation only; never set by a companion record. |
| `derivative` | `D` (deterministic derivative) | Compatibility State, Architecture-Status-style projections. |
| `operational` | (no direct analogue) | New concept — mutable in-flight coordination state has no CLTR-SCHEMA-001 representation-kind equivalent. |
| `evidence` | `E` (immutable evidence reference) | Readiness package, certification, publication evidence, conflict, quarantine. |
| `compatibility` | (no direct analogue; closest is the diagnostic envelope's `authority_mode: compatibility`, §25) | Compatibility State only. |
| `historical` | `R` (reference) and `V` (verification-only), combined | Historical references may serve either role depending on context. |
| `quarantined` | (no direct analogue) | New concept — CLTR-SCHEMA-001 has no quarantine-specific authority-role code. |

This table is informational cross-reference only; it does not change
either enum's wire values.

---

## 33. State transition matrices

### 33.1 Cutover request (`request_state`)

Initial: `drafted`. Allowed: `drafted → readiness_pending → readiness_ready
→ authorization_pending → authorized → candidate_created → certified →
publication_pending → published | uncertain | rejected`. Terminal:
`published`, `rejected`. Retryable: `publication_pending` (may retry via a
new `PublicationAttempt`, §12.2). Replayable: `drafted` (identical replay
yields identical `request_id`, no-op). Uncertain: `uncertain` (from a
`publication_uncertain` outcome). Conflict: reachable from
`publication_pending` only. Quarantine: reachable from `candidate_created`
onward. Forbidden: any transition skipping `authorization_pending`
(no unauthorized path to `candidate_created`).

### 33.2 Authorization (`used_state` × `revocation_state`, §8.1)

Initial: `unused` × `active`. Allowed: `unused×active → used×active`
(consumption, §8.3); `unused×active → unused×revoked` (revocation before
use); `used×active → used×revoked` is **permitted** as a record-keeping
transition (revoking after use has no operational effect but is not
forbidden — it documents that the authorization should not be reused, which
is already true once `used`). Terminal: `used×*`, `unused×revoked`.
Forbidden: any transition out of `used` back to `unused`, and any
transition out of `revoked` back to `active`.

### 33.3 Candidate (`candidate_state`)

Initial: `created`. Allowed: `created → certifying → certified |
gate_rejected`. Terminal: `certified` (feeds §10), `gate_rejected`.
Quarantine: reachable from any non-terminal state. Forbidden: direct
`created → certified` without `certifying`.

### 33.4 Certification (`certification_state`)

Initial: `issued`. Allowed: `issued → consumed` (a `PublicationAttempt`
successfully used this certification) or `issued → stale` (§10.2) or
`issued → quarantined`. Terminal: `consumed`, `stale`, `quarantined`.
Forbidden: `stale → issued` (no un-staling in place; a fresh
`Certification` must be issued).

### 33.5 Publication attempt (`publication_state`, reusing §3.5's enum)

As specified fully in §3.5; restated here as the family-specific matrix
reference. Retryable: `publication_uncertain`, `conflict` → new attempt.
Replayable: identical `attempt_id` resubmission (§12.2). Uncertain:
`publication_uncertain`. Conflict: `conflict`. Quarantine: `quarantined`.

### 33.6 Authority state (`verification_state`)

Initial: `unverified`. Allowed: `unverified → verified | verification_failed`.
Terminal: `verified` (until superseded by a new `AuthorityState` from a
later publication), `verification_failed` (leads to §17.3's quarantine
path). Forbidden: `verification_failed → verified` in place (a fresh
`AuthorityState` must be produced after remediation).

### 33.7 Recovery journal (per-entry `new_journal_state`, reusing §3.6)

Initial: `none_required`. Allowed: forward movement through §3.6's states
as operations proceed; `retry_required`/`conflict_unresolved`/
`publication_uncertain_unresolved` may loop back to `none_required` only
via a *new* entry documenting successful resolution (never by editing the
existing entry, §15.2). Terminal: `terminal_recovered`,
`terminal_unrecoverable`. Retryable: `retry_required`. Replayable: none
(journal entries are never replayed, only appended). Uncertain:
`publication_uncertain_unresolved`. Conflict: `conflict_unresolved`.
Quarantine: `quarantine_required`.

### 33.8 Compatibility state (`disablement_state` × `migration_stage`)

Initial: `enabled` × `legacy_authoritative`-epoch. Allowed: monotonic
forward movement through §3.7's `CompatibilityMode` values as the bound
epoch's `MigrationStage` (§3.3) advances; `disablement_state` may move
`enabled → disabled` only once `CompatibilityMode` has reached
`legacy_read_only` or later. Terminal: `disabled` at `legacy_retired`.
Forbidden: `disabled → enabled` (no re-enabling in place; a governed
retirement-reversal phase would create a new `CompatibilityState` record
instead, per the same principle used throughout this contract).

---

## 34. Cross-record invariant matrix

| ID | Invariant |
|---|---|
| CSCH-INV-1 | Every companion record binds exactly one `migration_epoch` (no record spans two). |
| CSCH-INV-2 | `CutoverRequest.target_generation_id` == `CutoverCandidate.target_generation_id` for the candidate created from that request. |
| CSCH-INV-3 | `CutoverCandidate.target_generation_id` == `Certification.target_generation_id` for the certification issued for that candidate. |
| CSCH-INV-4 | `Certification.target_generation_id` == `PublicationAttempt`'s target for the attempt consuming that certification. |
| CSCH-INV-5 | A `published_and_verified` `PublicationAttempt`'s target generation == the resulting `AuthorityState.authoritative_generation_id`. |
| CSCH-INV-6 | `AuthorityState` always binds a `publication_evidence_id` once `authority_kind = cltr` (never `cltr` with no publication evidence). |
| CSCH-INV-7 | Report/metadata/marker/receipt bindings (§19–§21) always reference the current `AuthorityState.authoritative_generation_id` for their epoch, never a superseded generation. |
| CSCH-INV-8 | `HumanAuthorization` binds `request_id` and `target_generation_digest`; a `CutoverRequest` consuming an authorization whose bound digest differs from the request's own `target_generation_digest` is `digest_mismatch`. |
| CSCH-INV-9 | `CasExpectation.expected_authority_state_digest` binds the `AuthorityState` observed at expectation-creation time; a publication attempt whose live `AuthorityState` digest differs at attempt time is `cas_rejected`. |
| CSCH-INV-10 | `ReconciliationResult.current_authority` is always read fresh from the production pointer and never reports a generation different from what the pointer currently names. |
| CSCH-INV-11 | `CompatibilityState` can never cause `AuthorityKind` to read `legacy` once an epoch has reached `cltr_authoritative` (structural, §22.2). |
| CSCH-INV-12 | `QuarantineRecord` evidence can never satisfy `ReadinessEvidencePackage.prerequisite_status = ready` for the same object (a quarantined object's evidence is excluded from readiness aggregation, §7.2 "superseded evidence" rule extended to quarantine). |
| CSCH-INV-13 | `HistoricalAuthorityReference` can never resolve `current_authority` for a live reconciliation (§23.2, non-authoritative for current transitions). |
| CSCH-INV-14 | No two `PublicationAttempt` records for the same `request_id` may both hold `publication_state = published` or `verified` simultaneously without a `ConcurrencyConflict` record explaining the collision (§12.2). |
| CSCH-INV-15 | Every `RecoveryJournalEntry.previous_entry_digest` (except the chain's first) equals its predecessor's `entry_digest` (§15.2). |

Each invariant ID is stable once frozen and appears verbatim in the
verification matrix (§45).

---

## 35. Authority-object boundary

| Family | Boundary classification |
|---|---|
| Authoritative generation itself (CLTR-CUTOVER-001 §3) | inside authoritative generation |
| AuthorityEpoch | adjacent immutable evidence (proposed/active identity, not content) |
| AuthorityState | operational mutable state (evidence-adjacent, §5.2) |
| CutoverRequest | operational mutable state (mutable only in `request_state`/`limitations`, §6.3) |
| ReadinessEvidencePackage | adjacent immutable evidence |
| HumanAuthorization | operational mutable state (`revocation_state`/`used_state` mutate) |
| CutoverCandidate | operational mutable state (`candidate_state` mutates) |
| Certification | adjacent immutable evidence (content immutable; `certification_state` external tracking only, §10.2) |
| CasExpectation | operational mutable state (embedded, ephemeral per use) |
| PublicationAttempt | adjacent immutable evidence (append-only, one row per attempt) |
| PublicationEvidence | adjacent immutable evidence |
| ConcurrencyConflict | adjacent immutable evidence |
| RecoveryJournalEntry | adjacent immutable evidence (append-only) |
| ReconciliationResult | derived presentation |
| QuarantineRecord | adjacent immutable evidence |
| NotificationAuthorityBinding | operational mutable state |
| MarkerAuthorityBinding | adjacent immutable evidence |
| FinalizationReceiptAuthorityBinding | adjacent immutable evidence |
| CompatibilityState | operational mutable state |
| HistoricalAuthorityReference | historical record |

**No mutable authorization, attempt, or recovery state is placed inside
the immutable generation's own manifest content** — every "operational
mutable state" row above is a companion record referenced *by* the
generation's evidence trail, never embedded *in* the generation's
manifest-digested content (CLTR-SCHEMA-001 §16's manifest coverage remains
scoped to the generation's own files only, §27).

---

## 36. Persistence classification

| Family | Classification |
|---|---|
| AuthorityEpoch | immutable identity-addressed (mutable only in `activation_state`/`supersession_state`, tracked as an atomic current-pointer-style field update, not a content rewrite) |
| AuthorityState | atomic current pointer (one current record per epoch, replaced atomically on each successful/uncertain publication, §5.2) |
| CutoverRequest | immutable content-addressed, with a narrow atomic in-place update allowed only for `request_state`/`limitations` (§6.3) |
| ReadinessEvidencePackage | immutable content-addressed |
| HumanAuthorization | immutable content-addressed, with atomic in-place update allowed only for `revocation_state`/`used_state` |
| CutoverCandidate | immutable content-addressed, with atomic in-place update allowed only for `candidate_state` |
| Certification | immutable content-addressed |
| CasExpectation | ephemeral runtime only (embedded, never independently persisted, §2 row 10) |
| PublicationAttempt | append-only (one immutable row per `attempt_sequence`) |
| PublicationEvidence | immutable content-addressed |
| ConcurrencyConflict | append-only |
| RecoveryJournalEntry | append-only journal, chained (§15.2) |
| ReconciliationResult | ephemeral runtime only (not persisted by default, §16.2) |
| QuarantineRecord | append-only |
| NotificationAuthorityBinding | replaceable derived latest view (one binding per notification intent, superseded on retry) |
| MarkerAuthorityBinding | immutable content-addressed |
| FinalizationReceiptAuthorityBinding | immutable content-addressed |
| CompatibilityState | atomic current pointer (one current state per epoch/component, replaced atomically as `CompatibilityMode` advances) |
| HistoricalAuthorityReference | historical record (points at already-classified prior art, no new classification needed) |

**No record with authority relevance relies solely on an overwrite-in-place
mutable JSON file without justified atomicity and history**: every "atomic
current pointer" row above is written via the same write-temp/fsync/rename
primitive CLTR-SCHEMA-001 §17 already specifies (reused, not reinvented),
and every such family has an append-only or content-addressed sibling
(the recovery journal, for `AuthorityState`; the request's own immutable
content-addressed core, for `CutoverRequest`'s narrow mutable fields) that
preserves history even though the "current" view is a single mutable
pointer.

---

## 37. Pointer inventory

| Pointer | Classification |
|---|---|
| Production `current` pointer (CLTR-SCHEMA-001 §16, extended per CLTR-CUTOVER-001 to carry `authority_kind`/`authority_epoch_id`) | **authority-bearing** (the only one) |
| `current-authority-state` (points at the latest `AuthorityState` for an epoch) | operational |
| `latest-readiness-package` | derived convenience |
| `latest-certification` | derived convenience |
| `latest-publication-attempt` | operational |
| `current-recovery-journal` (§15.2) | operational |
| `latest-reconciliation-result` (only if a caller opts to persist one, §16.1) | derived convenience |
| `current-compatibility-state` | operational |

**Exactly one pointer identifies current production authority** — the
production `current` pointer. Every other pointer in this table is
explicitly disclosed as non-authority-bearing (`operational` or `derived
convenience`) and this contract's authority resolver (CLTR-CUTOVER-001 §4)
must never consult any pointer other than the production `current` pointer
to answer "what is authoritative right now."

---

## 38. Namespace contract

### 38.1 Derivation

The namespace is derived, not assumed, from: containment (Stage 3
companion records must not be discoverable as if they were Stage 1/2/
rollback evidence, or vice versa — §0.6), atomicity (every atomic-pointer
family above needs its own directory scoped narrowly enough that an
atomic rename cannot accidentally collide with a sibling family's rename),
compatibility (the tree must sit beside, not inside, the existing
`.pcae/cltr-migration/epochs/<epoch>/` tree, since Stage 1/2/rollback
already own subdirectories there and this contract must not redefine
their meaning), and repository convention (every other `.pcae/*`
subsystem in this repository — finalization-transactions, delivery-receipts,
phase-reports, cltr-shadow, cltr-migration, cltr-prototypes — uses a
top-level `.pcae/<subsystem>/` directory; Stage 3 companion records follow
the same convention rather than nesting under an existing subsystem).

### 38.2 Frozen namespace

```
.pcae/cltr-authority/
  schemas/                              (future executable schema files only; empty at freeze time)
  epochs/
    <migration_epoch>/
      epoch-record.json                  (AuthorityEpoch, atomic current pointer per epoch identity — one file per epoch_id, never overwritten once activation_state leaves "proposed")
      requests/<request_id>.json          (CutoverRequest, immutable content-addressed)
      readiness/<package_id>.json         (ReadinessEvidencePackage, immutable content-addressed)
      authorizations/<authorization_id>.json (HumanAuthorization, immutable content-addressed + narrow mutable fields)
      candidates/<candidate_id>.json      (CutoverCandidate)
      certifications/<certification_id>.json (Certification)
      publication-attempts/<attempt_id>.json (PublicationAttempt, append-only)
      publication-evidence/<evidence_id>.json (PublicationEvidence)
      conflicts/<conflict_id>.json         (ConcurrencyConflict, append-only)
      recovery/journal/<entry_sequence>.json (RecoveryJournalEntry, append-only chain)
      recovery/current-recovery-journal    (operational pointer, §37)
      quarantine/<quarantine_id>.json      (QuarantineRecord, append-only)
      current-authority-state              (operational pointer to the latest AuthorityState, §37)
      authority-state/<state_id>.json      (AuthorityState history, one file per historical state — the pointer above always names the latest)
      compatibility/current-compatibility-state (operational pointer, §37)
  current-authority                        (the single production `current` pointer, CLTR-SCHEMA-001 §16-extended — authority-bearing, §37; this is the ONE file in this whole tree the authority resolver ever consults for AuthorityKind)
```

`.pcae/cltr-authority/` is disjoint from `.pcae/cltr-migration/` (Stage
1/2/rollback), `.pcae/cltr-shadow/` (Stage 0), and `.pcae/cltr-prototypes/`
(disposable). Nothing in this tree is created, read, or written by any
code shipped as of Phase 135Z — the tree above is a frozen future layout,
not a directory this phase creates.

### 38.3 Traversal and symlink requirements

Every path segment under `.pcae/cltr-authority/` **must** be validated
against the same traversal rule CLTR-SCHEMA-001 §16.1–16.3 already applies
to generation directories: ASCII-only identity segments, no `..`, no
absolute paths, no symlink resolution assumed or followed when reading or
writing any file in this tree (§39 elaborates the security rationale).

---

## 39. Security requirements

Schema-level defenses, frozen for future implementation:

- **Traversal strings / absolute paths / symlink-target references**:
  every path-bearing field (namespace paths only — no identity field ever
  contains a path, §26) must reject `..`, absolute paths, and symlinks;
  enforcement happens before any file I/O, not after.
- **Pointer substitution**: a pointer file's content must always be
  re-validated (ID+digest match, §27) against the record it claims to
  reference before being trusted — a pointer is never trusted merely
  because it exists at the expected path.
- **ID substitution / digest substitution / schema substitution**: covered
  by §27's cross-record binding rule (ID+digest pairs, never ID alone) and
  §30's fail-closed unknown-schema behavior.
- **Unknown critical fields**: §30.
- **Authorization substitution**: `CutoverRequest` binds the exact
  `authorization_digest` (§8.3); a substituted authorization with a
  different digest is `digest_mismatch`.
- **Readiness-package substitution / generation substitution**: same
  ID+digest binding rule, applied at every reference site in §6–§13.
- **Stale references**: covered by the `stale_*` codes in §31.
- **Conflicting replay**: §6.3, §12.2.
- **Quarantine bypass**: §11.2's exact-match CAS rule structurally
  prevents a quarantined certification/candidate from being silently
  accepted (a quarantined object's `disposition_state` must be checked as
  part of CAS-expectation validation, not as an optional side check).
- **Compatibility confusion**: §22.2's structural rule (no field capable
  of reactivating legacy authority).

**Record references must use stable IDs and digests rather than trusting
arbitrary paths** — this is restated here as the single governing security
principle underlying every bullet above; no companion record schema in
this contract resolves a cross-reference by path alone.

---

## 40. Privacy and secret handling

- `HumanAuthorization.principal_identity` **may** store an operator
  identifier (username, email, or similar stable identifier) but **must
  not** store reusable credentials.
- Companion records **must not persist**: API tokens, bot tokens (e.g. the
  Telegram bot token confirmed present-but-secret in this repository's
  `~/.config/pcae/telegram.env`), passwords, private keys, bearer tokens,
  or raw secret environment values of any kind.
- `HumanAuthorization` may store **signed or hashed evidence** of an
  authorization act (e.g. a digest of a signed artifact, per
  `authorization_method: signed_artifact`) but never the signing key or
  raw credential material itself.
- `NotificationAuthorityBinding` may reference a notification **sink
  identity** (e.g. "telegram") but must never embed the sink's
  destination secret (chat ID/token) — those remain sourced from existing
  environment configuration (`~/.config/pcae/telegram.env`), outside any
  companion record.
- Machine identity (`verifier_identity`, `conflicting_actors`) is limited
  to process/session/component identifiers, never host credentials or
  network secrets.

---

## 41. Schema relationship to CLTR-SCHEMA-001

| Stage 3 concept | Disposition |
|---|---|
| Authority epoch / authority state | companion schema required (§4, §5) |
| Cutover request | companion schema required (§6) |
| Readiness package | companion schema required (§7) |
| Human authorization | companion schema required (§8) |
| Cutover candidate / certification | companion schema required (§9, §10) |
| CAS expectation | runtime-only (embedded component, §11) |
| Publication attempt / evidence | companion schema required (§12, §13) |
| Concurrency conflict | companion schema required (§14) |
| Recovery journal | companion schema required (§15) |
| Reconciliation result | runtime-only (§16) |
| Quarantine | companion schema required (§17) |
| Authority transition receipt | not required (§18) |
| Notification authority binding | companion schema required now; **minor CLTR-SCHEMA-001 revision** candidate later (§19.2) — reason: folding the binding directly into representation kind #8 would reduce indirection once proven; affected concept: notification payload representation kind; required future phase: a post-135Z, post-implementation schema-consolidation phase, not before. |
| Marker authority binding | companion schema required now; same future-minor-revision candidacy as above, scoped to representation kind #9. |
| Finalization receipt authority binding | companion schema required now; same candidacy, scoped to representation kind #10 (§21.2). |
| Compatibility state | companion schema required (§22) |
| Historical authority reference | runtime-only (§23) |

No entry in this table is "already represented in CLTR-SCHEMA-001
verbatim" — CLTR-SCHEMA-001 §24's migration sketch is [GUIDANCE] only and
defines none of the above in binding form, confirming this phase's
premise that a companion contract, not a CLTR-SCHEMA-001 revision, is the
correct vehicle. **CLTR-SCHEMA-001 is not modified by this phase.**

---

## 42. Companion-schema versioning

- **Independent schema IDs**: each required companion schema (§2) receives
  its own `schema_id` (e.g. `CLTR-AUTHORITY-STATE-001`,
  `CLTR-CUTOVER-REQUEST-001`, etc. — exact IDs to be assigned at
  executable-implementation time, not minted speculatively in this
  contract-only phase beyond the one example given in §5.1 for
  illustration).
- **Independent versions**: each schema versions independently
  (MAJOR.MINOR.PATCH, same discipline as CLTR-SCHEMA-001 §2).
- **Shared profile version**: the canonicalization profile (§26) and
  digest profile (§27) are versioned once, at the contract level
  (`CLTR-CUTOVER-SCHEMAS-001` itself), not per-schema — every companion
  schema inherits the contract's profile version rather than declaring
  its own.
- **Compatibility matrix**: a future executable-schema phase must publish
  a matrix of which companion-schema versions are valid together for a
  given `CLTR-CUTOVER-SCHEMAS-001` version; this contract does not
  pre-populate that matrix (only one version of each schema exists at
  freeze time).
- **Major/minor rules**: identical discipline to CLTR-SCHEMA-001 §2 —
  MAJOR for any breaking change to required fields/identity formulas/enum
  removal; MINOR for additive, backward-compatible changes; PATCH for
  non-wire-affecting clarifications.
- **Deprecation/migration**: a deprecated companion-schema version must
  remain readable (not necessarily writable) for at least one full
  migration epoch after deprecation, mirroring CLTR-SCHEMA-001's own
  compatibility discipline.
- **Historical verification**: historical companion records (superseded
  versions) remain independently digest-verifiable without upgrade.
- **Unsupported-version behavior**: §30.
- **One companion schema version must not silently reinterpret another
  record family** — cross-family references are always ID+digest (§27),
  never a same-named-field coincidence across two schemas.

---

## 43. Executable-schema implementation sequence (planned, not implemented)

1. Shared envelope and enums (§3, §24).
2. Typed authority epoch/state (§4, §5) — closes PREREQ-1.
3. Cutover request (§6).
4. Readiness package (§7).
5. Authorization (§8).
6. Candidate and certification (§9, §10, embedding CAS expectation §11).
7. CAS and publication records (§12, §13).
8. Conflict and recovery records (§14, §15).
9. Reconciliation (§16, runtime-only — implemented as a function, not a
   persisted schema).
10. Marker/receipt/notification bindings (§19–§21).
11. Compatibility and historical records (§22, §23).

This ordering is derived strictly from dependency direction: no group
above references a field defined only in a later group (group 6 embeds
group-7's `CasExpectation`, but `CasExpectation` itself depends on nothing
from groups 6+, so this is not a forward dependency — it is captured at
authoring time in each embedding site per §12.1/§27). Each group requires
an independent verification phase before the next group begins, matching
135Y §"independent verification per implementation layer" precedent.

---

## 44. Typed runtime model sequence (planned, not implemented)

- **Model package location**: a new `src/pcae/cltr/authority/` package,
  sibling to the existing `src/pcae/cltr/` package (digest/canonicalization
  modules), not inside it — keeping Stage 3 typed models importable
  independently of Stage 0–2's existing CLTR modules.
- **Schema-to-model relationship**: one dataclass (or equivalent immutable
  value type) per schema in §43's sequence; a model never has fields the
  schema does not define, and vice versa.
- **Parsing**: strict — unknown required-field absence and
  authority-bearing unknown-optional-fields both raise, per §30.
- **Strict validation**: every enum field validated against §3's frozen
  wire values at construction time; construction-time validation, not
  deferred.
- **Canonicalization**: reuses `pcae.cltr.canonicalization` unchanged
  (§26; no new canonicalization module).
- **Digest**: reuses `pcae.cltr.digest`'s `compute_dict_digest`-equivalent
  unchanged (§27; no new digest module).
- **No-side-effect construction**: constructing a model instance never
  performs file I/O, network I/O, or clock reads beyond what an explicit
  `observed_time` parameter supplies.
- **Immutable values**: every model is frozen/immutable after construction
  (matching `SharedInputRevision`'s existing "deep-frozen fields"
  precedent, extraction §12).
- **Enum behavior**: Python `Enum` subclasses with exact wire-value
  members, no permissive fallback member.
- **Test fixtures**: one canonical fixture set per schema, covering at
  minimum: a valid minimal instance, a valid instance with every optional
  field populated, one unknown-field-rejection case, one
  unknown-enum-value-rejection case, one digest-determinism
  round-trip case.
- **Version compatibility**: a model constructor accepts an explicit
  `schema_version` and dispatches to the correct parsing rule for that
  version; no implicit "latest version assumed" default.

No model, dataclass, enum class, or test fixture is implemented by this
phase — §44 is a plan only.

---

## 45. Contract verification matrix

62 normative requirements are frozen by this contract, grouped by section.
Full enumeration (requirement ID, section, family, safety rationale,
verification method, expected evidence, blocking classification,
implementation milestone) is maintained as the authoritative checklist for
Phase 136A (Independent Verification). Representative entries:

| Req ID | Section | Family | Safety rationale | Verification method | Blocking? | Milestone |
|---|---|---|---|---|---|---|
| CSCH-REQ-1 | §3.1 | AuthorityKind | Prevents substring/implicit authority classification | Static review of any future resolver code against exact-match rule | Blocking | Implementation group 1 |
| CSCH-REQ-2 | §4.2 | AuthorityEpoch | Deterministic identity, no timestamp/random/CWD dependence | Formula re-derivation + property-based replay test | Blocking | Group 2 |
| CSCH-REQ-3 | §5.2 | AuthorityState | Single-authority invariant preserved (pointer remains sole authority source) | Code review confirming resolver never reads AuthorityState for AuthorityKind | Blocking | Group 2 |
| CSCH-REQ-4 | §6.2–6.3 | CutoverRequest | Deterministic identity, conflicting-replay rejection | Digest determinism test + replay-conflict test | Blocking | Group 3 |
| CSCH-REQ-5 | §8.3 | HumanAuthorization | Replay/one-time-use/expiry enforcement | Unit tests for each of: expiry, revocation, one-time use, replay, unknown principal | Blocking | Group 5 |
| CSCH-REQ-6 | §11.2 | CasExpectation | No wildcard on missing expected value (closes PREREQUISITE-135X-1) | Unit test asserting absent-required-field rejection | Blocking | Group 6 |
| CSCH-REQ-7 | §13.2 | PublicationEvidence | Uncertainty never collapsed into failure | Unit test asserting `publication_uncertain` is distinct from `publication_failed`/`published_and_verified` | Blocking | Group 7 |
| CSCH-REQ-8 | §15.2 | RecoveryJournalEntry | Hash-chain tamper/truncation detection | Chain-validation test including a deliberately truncated fixture | Blocking | Group 8 |
| CSCH-REQ-9 | §16.2 | ReconciliationResult | Read-only, `mutation: none` enforced | Integration test asserting no filesystem write occurs during reconciliation | Blocking | Group 9 |
| CSCH-REQ-10 | §17.3 | QuarantineRecord | Integrity-failure case never silently reactivates legacy or leaves no authority | Fault-injection test simulating generation-integrity failure, asserting `AuthorityKind` unchanged and `operator_review_required=true` | Blocking | Group 8, closes PREREQUISITE-135Z-1 |
| CSCH-REQ-11 | §22.2 | CompatibilityState | Structural incapability of reactivating legacy authority | Static schema review confirming no such field exists | Blocking | Group 11 |
| CSCH-REQ-12 | §37 | Pointer inventory | Exactly one authority-bearing pointer | Static review of every pointer read site | Blocking | Cross-cutting, all groups |

Full 62-item matrix to be published verbatim as an appendix at
Phase 136A, cross-referenced 1:1 against §34's invariant IDs and §31's
failure-code vocabulary.

---

## 46. Acceptance criteria

Moving to executable-schema and typed-model implementation requires **all**
of: (1) the exact record inventory of §2; (2) the exact enum vocabulary of
§3; (3) the exact authority-epoch model of §4; (4) the exact
authority-state model of §5; (5) deterministic identity rules for every
family (§25); (6) the canonicalization profile (§26); (7) the digest
profile (§27); (8) the cross-record invariants (§34); (9) the
authoritative-generation boundary (§35); (10) the persistence
classification (§36); (11) the pointer inventory (§37); (12) the namespace
(§38); (13) versioning (§42); (14) compatibility (§0, §41); (15) security
(§39); (16) secret-handling rules (§40); (17) no unresolved Blocking
ambiguity (§45, §47); (18) the complete verification matrix (§45).

---

## 47. No-go criteria

Implementation is prohibited if any of the following holds — none does, as
demonstrated section-by-section above, but the checklist is frozen for
136A's independent re-verification:

- Authoritative object and authority-state record overlap ambiguously —
  **resolved**, §5.2's exact relationship.
- More than one authority-bearing pointer exists — **resolved**, §37 (one).
- Typed authority epochs remain undefined — **resolved**, §4.
- Record identity depends on timestamps or random UUIDs without binding
  rules — **resolved**, §25 (timestamps excluded everywhere; the one
  random element, `HumanAuthorization`'s nonce, is explicitly bound into
  identity, §8.2).
- Authorization semantics permit replay — **resolved**, §8.3 (one-time use
  + replay rejection).
- CAS expectations permit wildcard source state — **resolved**, §11.2
  (only one optional field, explicitly justified).
- Publication uncertainty is collapsed into failure — **resolved**, §3.5,
  §13.2 (`publication_uncertain` is distinct and first-class).
- Recovery journal semantics are incomplete — **resolved**, §15 (entry
  schema, chaining, aggregate view, all frozen).
- Mutable operational records can establish authority — **resolved**,
  §35 (boundary table; no operational-mutable-state family is
  `authoritative`).
- Marker or receipt can become second authority — **resolved**, §20.2,
  §21 (structural: neither binding carries an authority-setting field).
- Compatibility state can reactivate legacy authority — **resolved**,
  §22.2 (structural).
- Schema relationships are unclear — **resolved**, §41 (full disposition
  table).
- Unknown-field behavior is unsafe — **resolved**, §30 (fail-closed for
  authority-bearing families).
- Cross-record invariants are incomplete — **resolved**, §34 (15
  invariants, extensible without renumbering existing IDs).

---

## 48. Contract verdict

**COMPANION SCHEMA CONTRACT FROZEN — READY FOR INDEPENDENT VERIFICATION**

Implementation readiness is **not** inferred from this verdict — §46's
acceptance criteria being met at the contract level authorizes only
Phase 136A's independent verification, not executable-schema or
typed-model implementation.

---

## Findings

| ID | Title | Verdict | Source | Affected family | Authority impact | Concurrency impact | Recovery impact | Exactly-once impact | Schema impact | Required future phase | Latest acceptable resolution point |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F-135Z-1 | Integrity-failure recovery mechanism for the authoritative generation is disclosed but not mechanized | PREREQUISITE | §17.3 | QuarantineRecord, AuthorityState | High (defines detection only, not resolution) | None | High | None | None | Future activation-adjacent phase | Before any executable Stage 3 activation work |
| F-135Z-2 | Notification/Marker/Receipt authority bindings remain companion records rather than folded into CLTR-SCHEMA-001 | NON-BLOCKING | §19–§21, §41 | Notification/Marker/Receipt bindings | Low | None | None | None | Deferred CLTR-SCHEMA-001 minor revision | Post-implementation schema-consolidation phase |
| F-135Z-3 | 62-item verification matrix is summarized, not fully enumerated, in this document | DEFERRED | §45 | All | None (documentation completeness only) | None | None | None | None | Full appendix published verbatim at 136A | Phase 136A |
| F-135Z-4 | Companion-schema `schema_id` values beyond the illustrative examples in §5.1 are not yet minted | DEFERRED | §42 | All required companion schemas | None | None | None | None | Executable-schema implementation | Group 1 of §43 |
| F-135Z-5 | CAS expectation embedding-vs-reference choice (§11, §27) has not been exercised against a real concurrent-writer test | PREREQUISITE | §11, §27 | CasExpectation | Medium | High | Medium | None | None | Implementation group 6/7 with concurrency test | Before Stage 3 prerequisite CAS implementation is considered complete |

No **CONFIRMED** or **BLOCKING** findings remain open. All five findings
above are either **PREREQUISITE** (registered for a later implementation
milestone, not blocking this contract's own freeze) or **NON-BLOCKING**/
**DEFERRED** (documentation or minting completeness, not a contract
ambiguity).

---

## No-implementation proof

- No production source changed. No test source changed. No executable
  schema changed. No Stage 3 Python model was implemented. No validator
  was implemented. No authority resolver was implemented. No
  authority-state persistence was implemented. No authority pointer was
  implemented or changed. No cutover request was created or executed. No
  readiness package was created. No authorization was created. No
  certification was created. No CAS or recovery journal was implemented.
  No authority epoch changed. No CLTR authority was created. No legacy
  authority was demoted. No legacy authority was retired. No production
  behavior changed. No execution capability was introduced.
- Legacy lifecycle remains the sole production authority. CLTR remains
  derivative. CLTR-CUTOVER-001 and CLTR-CUTOVER-SCHEMAS-001 define future
  behavior and future data contracts only.
- Runtime remains Observed, maximum capability remains observe, execution
  availability remains unavailable (confirmed by `pcae runtime inspect`,
  re-run during this phase).

---

## Recommended next phase

**136A — Stage 3 Companion Schemas and Typed Authority Model Contract
Independent Verification**

Executable schema implementation and typed-model implementation must not
begin before 136A completes.
