# Phase 136B — Stage 3 Companion Executable Schema Architecture

## Status

**ARCHITECTURE-ONLY.** This document defines the future executable-schema
architecture for **CLTR-CUTOVER-SCHEMAS-001 v1.0** (frozen Phase 135Z,
independently verified VERIFIED WITH PREREQUISITES Phase 136A). It is
Layer 1 scope per CLTR-CUTOVER-SCHEMAS-001 §43 item 1: shared envelope and
enums. It does not implement, modify, or activate anything. No executable
schema file, Python typed model, validator, schema registry, authority
resolver, authority-state persistence, authority pointer, cutover request,
readiness package, authorization, candidate, certification, publication
attempt, conflict record, or recovery journal is created by this phase. No
production source, test source, or existing executable schema (including
`schemas/repository_intelligence/**`) is changed.

**Legacy lifecycle remains the sole production authority. CLTR remains
derivative. CLTR-CUTOVER-001 and CLTR-CUTOVER-SCHEMAS-001 remain
future-behavior and future-data contracts only. Runtime remains Observed,
maximum capability remains observe, execution availability remains
unavailable** (confirmed by `pcae runtime inspect`, re-run this phase).

---

## 0. Relationship to governing contracts and the 136A verification

This document translates **CLTR-CUTOVER-SCHEMAS-001 v1.0** (135Z) — itself
the wire/type-level companion to **CLTR-CUTOVER-001 v1.0** (135W,
independently verified 135X) — into a concrete JSON Schema package
architecture. It is bound by, and does not contradict:

- **CLTR-001 v1.0** — thirty required semantic CLTR fields; CLTR is not
  currently production authority.
- **CLTR-SCHEMA-001 v1.0.1** — the wire-format contract for the CLTR
  record itself (unchanged, unmodified by this phase or by 135Z).
- **CLTR-CUTOVER-001 v1.0** (135W) — the semantic Stage 3 contract:
  single-authority invariant (§5), authority resolver (§4), CAS/stale-writer
  contract (§14), recovery-state table (§18), split-brain prevention (§27).
- **CLTR-CUTOVER-SCHEMAS-001 v1.0** (135Z) — the twenty-item record-family
  inventory (§2), seven typed enums (§3), envelope (§24), identity (§25),
  canonicalization (§26, reusing CLTR-SCHEMA-001 §14 verbatim), digest
  profile (§27), fifteen cross-record invariants (§34), authority-object
  boundary (§35), persistence classification (§36), pointer inventory
  (§37), frozen namespace `.pcae/cltr-authority/` (§38.2), security (§39),
  secret handling (§40), CLTR-SCHEMA-001 relationship table (§41),
  versioning (§42), planned implementation sequence (§43).
- **PFN-001** — exactly-once canonical-report notification; unchanged.
- **PFR-001** — thirteen mandatory canonical-report sections; unchanged.
- Verified Stage 1 (135O/135P), Stage 2 (135S/135T), and rollback-rehearsal
  (135U) evidence.
- **135Y** — the non-binding Stage 3 implementation plan; its own
  nine-companion-record illustration is explicitly not frozen inventory
  (135Y §11) and is superseded by 135Z's independently re-derived
  twenty-item classification, adopted here without re-litigation.
- **136A** — independent verification of 135Z, VERIFIED WITH
  PREREQUISITES, zero BLOCKING findings, two new PREREQUISITE findings
  (§5, §6 below) plus F-135Z-3 (§4) and 135Z's own five findings, all
  carried forward.

### 0.1 Disposition of the 136A reconciliation conflict

Before starting 136B, `pcae phase-report reconcile --phase-id 136A` was
run read-only (mandatory per this phase's brief; `mutation: none`
confirmed). Result: `reconciliation_status: conflict` — the notification
marker (`.pcae/phase-reports/.last-notified.json`) and finalization
checkpoint (`.pcae/finalization-transactions/136A.json`) were finalized
against an earlier `report_digest` before 136A's own later corrective
commits (84b34a9d, 6e4c9e15, 8f9bd134 — correcting 136B's next-phase
framing to architecture-only) updated `.pcae/phase-reports/latest.json`'s
content. `promoted_generation_count: 1` and exactly one delivery receipt
exist — **no duplicate delivery, no redispatch, no Stage 3/CLTR schema
artifact of any kind exists** (`schemas/` contains only the pre-existing,
unrelated `repository_intelligence` family). This is a disclosed,
inherited, non-blocking presentation/bookkeeping defect in 136A's own
finalization bookkeeping, structurally identical in kind to 136A's own
disclosed canonical-title defect. It does not affect this phase's
technical content and is not addressed here — 136A is not mutated or
redispatched, per explicit instruction. Recorded in `tasks/DECISIONS.md`.

---

## 1. Architecture purpose

The future executable-schema layer encodes CLTR-CUTOVER-SCHEMAS-001's
sixteen required companion-schema families as versioned JSON Schema
documents. It shall:

- validate record shape (required/optional fields, types, nesting);
- validate local field constraints (string patterns — e.g. 64-character
  lowercase hex digests, §25.2 — enum membership, cardinality);
- validate enum values against the seven frozen wire vocabularies (§3
  below);
- validate `schema_id`/`schema_version`/`contract_version` presence and
  form;
- expose reusable `$defs` for envelope, identity, digest, reference, and
  enum shapes (§8);
- support deterministic serialization contracts (by construction — JSON
  Schema constrains shape, the existing `pcae.cltr.canonicalization` module
  constrains byte-level canonical form, §14 below);
- support fixture validation (§34);
- support future typed-model parsing as a strict superset check (§42.3 —
  every value a typed model accepts must already be schema-valid).

It shall not: resolve current authority; evaluate production cutover
eligibility; publish pointers; perform compare-and-swap; authorize
cutover; mutate lifecycle state; dispatch notifications; create
production markers or receipts; or itself execute anything. Schema
validation is Layer 2 of six (§43); it never performs Layer 3–6
responsibilities (canonicalization/digest verification, cross-record
semantic validation, live-state/CAS validation, authority resolution).

---

## 2. Schema dialect

**Selected: JSON Schema draft 2020-12** (`$schema:
"https://json-schema.org/draft/2020-12/schema"`), matching the
repository's only existing executable-schema precedent
(`schemas/repository_intelligence/**`, all 20 files, confirmed by direct
inspection). No demonstrated incompatibility exists between 2020-12 and
any CLTR-CUTOVER-SCHEMAS-001 requirement (tagged unions, exact-match
enums, and embedded components are all expressible in 2020-12 without a
newer draft feature). Introducing a second dialect for one subsystem would
itself violate this document's own "no divergent implementation" style
principle without any offsetting benefit — rejected.

- **`$schema`**: `"https://json-schema.org/draft/2020-12/schema"` on every
  file, following the existing precedent exactly.
- **`$id`**: `"https://pcae.local/schemas/cltr_cutover/<path>.schema.json"`,
  mirroring `https://pcae.local/schemas/repository_intelligence/...`
  exactly (a stable, non-resolved identifier — no network fetch is ever
  performed against it, §33).
- **`$defs`**: one `$defs` block per file for file-local reusable shapes;
  shared cross-file `$defs` (envelope, digest, identity, enums) live in
  the `shared/` schemas and are referenced via `$ref`
  (`"shared/envelope.schema.json#/$defs/companion_envelope"`), never
  duplicated inline — reference behavior below.
- **Reference behavior**: relative `$ref` by file path within
  `schemas/cltr_cutover/`, resolved by the future offline schema registry
  (§33) from the local package root — never an absolute URL fetch, never
  a `$id`-based remote resolution. This matches the existing precedent
  (`repository_intelligence` schemas reference each other by relative
  path today, confirmed by inspection).
- **Format validation**: `format` keywords (`date-time` for RFC 3339
  timestamps) are annotation-only, not asserted at the JSON Schema layer
  — CLTR-CUTOVER-SCHEMAS-001 §28's temporal rules (UTC, second precision)
  are semantic-validator responsibilities (Layer 4), consistent with
  135Z's own instruction that JSON Schema cannot prove semantic
  correctness (§12 below elaborates the identity-vs-shape boundary this
  generalizes).
- **Unknown-key behavior**: `additionalProperties: false` at every object
  level for every **authority-bearing or activation-relevant** family
  (`AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
  `HumanAuthorization`, `Certification`, `PublicationAttempt`,
  `PublicationEvidence`, `CasExpectation` — 135Z §30's exact list),
  directly implementing 135Z §30's fail-closed-on-unknown-optional-field
  rule. For purely evidentiary/historical families
  (`ReadinessEvidencePackage`, `ConcurrencyConflict`, `QuarantineRecord`,
  `CompatibilityState`, `HistoricalAuthorityReference`),
  `additionalProperties` is constrained to exactly one reserved key,
  `_extensions` (itself schema-constrained, not free-form), via
  `"properties": {..., "_extensions": {...}}, "additionalProperties":
  false` — never bare `true`. This closes the gap the existing
  `repository_intelligence` schemas leave open (they use blanket
  `additionalProperties: false` uniformly, since none of them have a
  135Z-style evidentiary-extension carve-out); this contract's two-tier
  behavior is a deliberate, justified difference, not an inconsistency.
- **Conditional validation**: `if`/`then` (not `oneOf` on a whole schema)
  is used for the small number of genuinely conditional shapes — tagged
  unions (`current_authoritative_object`, `source_authority_identity`,
  `expected_authoritative_generation`; 135Z §5.1, §6.1, §11.1) are encoded
  as `"oneOf": [{tagged "kind": "legacy" branch}, {tagged "kind": "cltr"
  branch}]` keyed on a `const` discriminator (`kind`), the standard JSON
  Schema tagged-union idiom; family-specific presence rules (e.g.
  `AuthorityEpoch.target_authoritative_generation` present only once
  certified) are expressed as `if: {properties: {activation_state: {const:
  "active"}}}, then: {required: [...]}` rather than encoded into the base
  `required` array.
- **`unevaluatedProperties`**: not used. `additionalProperties` alone is
  sufficient because this architecture does not compose schemas via
  `allOf` for the object-level shape (envelope fields are pulled in via
  `$ref` inside a single `properties` block, then closed with one
  `additionalProperties: false`, rather than via `allOf`-merged partial
  schemas, which is exactly the pattern that would otherwise require
  `unevaluatedProperties` to close correctly). This avoids the well-known
  `allOf` + `additionalProperties: false` interaction hazard entirely by
  construction, rather than working around it.
- **Enum behavior**: JSON Schema `"enum": [...]` with the exact wire-value
  list from §3 below, for every enum field, with no open extension value —
  directly implementing 135Z §30's "no enum defines an unknown/other
  catch-all" rule.
- **Compatibility policy**: a MINOR schema-package revision may add new
  optional fields and new `$defs`; it must never remove a required field,
  narrow an enum, or change an identity formula's included-fields set —
  identical discipline to CLTR-SCHEMA-001 §2 and 135Z §42, applied here at
  the executable-file level.

---

## 3. Package layout

```
schemas/cltr_cutover/
  README.md
  shared/
    envelope.schema.json          (§8 — companion envelope $defs)
    enums.schema.json             (§9 — seven typed enums as reusable $defs)
    identity.schema.json          (§11 — digest-string/identity shape $defs)
    digest.schema.json            (§14 — digest-field $defs)
    references.schema.json        (§12 — id+digest reference-pair $defs)
    failures.schema.json          (§30 — error/failure-code enum, informational)
    limitations.schema.json       (limitations array shape $def)
  records/
    authority_epoch.schema.json
    authority_state.schema.json
    cutover_request.schema.json
    readiness_package.schema.json
    human_authorization.schema.json
    cutover_candidate.schema.json
    certification.schema.json
    publication_attempt.schema.json
    publication_evidence.schema.json
    concurrency_conflict.schema.json
    recovery_journal_entry.schema.json
    quarantine_record.schema.json
    notification_authority_binding.schema.json
    marker_authority_binding.schema.json
    receipt_authority_binding.schema.json
    compatibility_state.schema.json
```

`cas_expectation.schema.json` is deliberately **not** a top-level file
under `records/` — CasExpectation is an embedded-only component (135Z §2
row 10, §11); its shape lives as a `$def`
(`shared/references.schema.json#/$defs/cas_expectation` or a dedicated
`shared/cas_expectation.schema.json`, resolved at implementation time in
favor of `shared/` for discoverability) and is `$ref`-included at its two
embedding sites (`cutover_candidate.schema.json`,
`publication_attempt.schema.json`), never given its own top-level record
file — this directly encodes 135Z §2 row 10's persistence classification
in the file layout itself. `reconciliation_result.schema.json` and
`historical_authority_reference.schema.json` are likewise **not** files
under `records/` — both are runtime-only/derived-view families (135Z §2
rows 13, 20); if a future phase chooses to publish either shape as
documentation (e.g. for a CLI `--json` output contract), it belongs under
a separate `views/` directory, not `records/`, so that `records/`'s
membership stays exactly equal to the sixteen persisted companion-schema
families. **No file under this layout is created in 136B** — this is the
frozen target layout for a future implementation phase (§29).

---

## 4. Exact executable-schema inventory

Re-deriving 135Z §2 (twenty families) and 136A's independent
reconfirmation of all twenty, into executable-file disposition:

| # | Family | 135Z classification | Executable-schema disposition |
|---|---|---|---|
| 1 | AuthorityState | required companion schema | `records/authority_state.schema.json` |
| 2 | AuthorityEpoch | required companion schema | `records/authority_epoch.schema.json` |
| 3 | CutoverRequest | required companion schema | `records/cutover_request.schema.json` |
| 4 | ReadinessEvidencePackage | required companion schema | `records/readiness_package.schema.json` |
| 5 | HumanAuthorization | required companion schema | `records/human_authorization.schema.json` |
| 6 | CutoverCandidate | required companion schema | `records/cutover_candidate.schema.json` |
| 7 | Certification | required companion schema | `records/certification.schema.json` |
| 8 | PublicationAttempt | required companion schema | `records/publication_attempt.schema.json` |
| 9 | PublicationEvidence | required companion schema | `records/publication_evidence.schema.json` |
| 10 | CasExpectation | embedded schema component | `$def` in `shared/`, embedded via `$ref` at two sites — **not** a `records/` file |
| 11 | ConcurrencyConflict | required companion schema | `records/concurrency_conflict.schema.json` |
| 12 | RecoveryJournalEntry | required companion schema (entry only; aggregate is a derived view) | `records/recovery_journal_entry.schema.json` |
| 13 | ReconciliationResult | derived view | not a `records/` file; optional future `views/` documentation only |
| 14 | QuarantineRecord | required companion schema | `records/quarantine_record.schema.json` |
| 15 | Authority Transition Receipt | not required (folded into AuthorityState + PublicationEvidence + receipt binding) | no file — structurally absorbed, per 135Z §18 |
| 16 | NotificationAuthorityBinding | existing-schema extension (companion binding today) | `records/notification_authority_binding.schema.json` |
| 17 | MarkerAuthorityBinding | existing-schema extension (companion binding today) | `records/marker_authority_binding.schema.json` |
| 18 | FinalizationReceiptAuthorityBinding | existing-schema extension (companion binding today) | `records/receipt_authority_binding.schema.json` |
| 19 | CompatibilityState | required companion schema | `records/compatibility_state.schema.json` |
| 20 | HistoricalAuthorityReference | runtime-only typed model | no file — typed-model-only, §42 |

**Reconciliation**: sixteen `records/` files (rows 1–9, 11–12, 14, 16–17,
18, 19 = 9 + 3 + 1 + 3 + 1 = 16, matching 135Z's "16 required companion
schemas" count exactly), one embedded `$def` (row 10), one derived view
with no persisted file (row 13), one absorbed family with no file (row
15), one runtime-only typed model with no schema file (row 20). This is
an exact reconciliation, not an approximation — every one of 135Z's twenty
rows has an explicit, traceable executable-file disposition above, and
the sixteen-file count is independently re-verified by counting `records/`
entries in §3's layout, which lists exactly sixteen.

---

## 5. Disposition of F-135Z-3 (62-item verification matrix)

135Z §45 scheduled the full 62-item CSCH-REQ matrix for verbatim
publication "as an appendix at Phase 136A." 136A's independent
verification (confirmed by direct reading of its Findings table and this
phase's own reconciliation-context brief) cross-checked only the twelve
representative entries 135Z itself presented, and explicitly disclosed —
rather than silently closed — that it did not publish the full matrix.
**F-135Z-3 remains open after 136A. This document does not mark it
resolved.**

**Disposition decided here**: because 136B is architecture-only and
cannot fabricate executable test coverage, this document does **not**
attempt to reconstruct or publish the 62-item matrix itself (doing so
without the original derivation would risk presenting an invented list as
authoritative — a worse outcome than leaving the gap explicit). Instead:

1. The full CSCH-REQ-1 … CSCH-REQ-62 matrix **must** be published
   verbatim as a dedicated appendix in a **named future contract phase**
   — the natural point is **136C (Stage 3 Companion Executable Schema
   Contract Freeze)**, since a contract freeze is exactly the governed
   checkpoint where a complete, cross-referenced requirement-to-schema
   traceability matrix (§28 below) is expected to exist before any
   implementation group begins.
2. Every requirement in the eventual full matrix **must** trace 1:1 to
   either a schema file (§4 above), a `$def` (§8–§14), a cross-record
   invariant (135Z §34, all fifteen preserved verbatim, §27 below), or an
   explicit non-schema semantic-validator responsibility (§27) — the
   traceability-matrix template in §28 is structured to make this
   binding, not merely a suggestion.
3. Until the full matrix is published, **no implementation group of §29
   may be considered complete** for the purposes of 135Z §46's acceptance
   criterion 18 ("the complete verification matrix").
4. **F-135Z-3 is not marked resolved by this document.** It is carried
   forward, now bound to 136C specifically rather than left open-ended.

---

## 6. Disposition of PREREQUISITE-136A-1

Exact wording (136A §12, reproduced verbatim from the independent
verification document): "135Z's choice of a separate companion contract
(rather than the CLTR-SCHEMA-001 1.1.0 minor revision 135Y's own schema
plan assumed) as the vehicle closing PREREQ-4 for 13 of 16
companion-schema families is sound on the merits (135W §30 permits either
vehicle) but is never explicitly reconciled against PREREQ-4's own
register wording or against 135Y's already-published, differently-vehicled
plan."

**Architected relationship**, resolving the vehicle explicitly:

- **CLTR-SCHEMA-001 v1.0.1** — unchanged by 135Z, unchanged by this phase.
  Governs the CLTR record itself (`record.json`/`manifest.json`,
  `lifecycle_state`/`transition_type`, the fifteen representation kinds).
- **CLTR-CUTOVER-SCHEMAS-001 v1.0** (135Z) — **is** the vehicle that
  closes 135W's PREREQ-4 for the thirteen families 135Z §41 lists as
  "companion schema required" without a CLTR-SCHEMA-001 revision
  dependency (AuthorityEpoch, AuthorityState, CutoverRequest,
  ReadinessEvidencePackage, HumanAuthorization, CutoverCandidate,
  Certification, CasExpectation, PublicationAttempt, PublicationEvidence,
  ConcurrencyConflict, RecoveryJournalEntry, QuarantineRecord — thirteen
  families).
- **A future CLTR-SCHEMA-001 v1.1.0 minor revision** — remains a
  **separate, later, optional** vehicle, needed only for the three
  binding families 135Z §41 explicitly flags as "companion schema
  required now; minor CLTR-SCHEMA-001 revision candidate later"
  (NotificationAuthorityBinding, MarkerAuthorityBinding,
  FinalizationReceiptAuthorityBinding — three families, folding the
  binding directly into representation kinds #8/#9/#10) — and explicitly
  **not before implementation and proof**, per 135Z §41's own text
  ("required future phase: a post-135Z, post-implementation
  schema-consolidation phase, not before").
- **This document's own decision [NEW]**: this is a **mixed approach**,
  and it was always the correct one on 135Z's own terms — the ambiguity
  PREREQUISITE-136A-1 flags is a **citation/cross-reference gap**, not a
  substantive design defect (136A itself found it "sound on the merits").
  This document closes it explicitly: **CLTR-CUTOVER-SCHEMAS-001 v1.0,
  not a CLTR-SCHEMA-001 version bump, closes PREREQ-4 for thirteen of
  sixteen companion-schema families; the remaining three
  (notification/marker/receipt bindings) are satisfied today as companion
  schemas under this same contract, with CLTR-SCHEMA-001 v1.1.0 remaining
  an optional future consolidation, never a prerequisite of Stage 3
  companion-schema implementation itself.**
- **Sequencing**: no CLTR-SCHEMA-001 amendment phase is placed before
  §29's implementation groups. If a future schema-consolidation phase for
  the three binding families is ever undertaken, it is placed **after**
  implementation group 10 (§29) and its independent verification, not
  before — consolidation requires proof the companion-binding shape
  works first.

**PREREQUISITE-136A-1 is resolved by this document** (the vehicle
ambiguity is closed); it is not "left open" going forward, though the
underlying 135W PREREQ-4 register text should still receive a retroactive
clarifying note per 136A's own suggested remediation — that is a
documentation-hygiene action for 135W's register, out of this phase's
`Allowed Files` scope, and is noted here rather than performed.

---

## 7. Disposition of PREREQUISITE-136A-2

Exact wording (136A §13, reproduced verbatim): "§36's persistence
classification claim that every 'atomic current pointer' family has a
history-preserving sibling is not reflected in §38.2's frozen namespace
for `CompatibilityState` — no `compatibility-state/<compatibility_state_id>.json`
history path is listed, unlike the parallel `authority-state/<state_id>.json`
path given to `AuthorityState`."

**Architected resolution**: this document freezes the missing namespace
path, applying the exact parallel structure `AuthorityState` already has:

```
.pcae/cltr-authority/epochs/<migration_epoch>/
  compatibility/
    current-compatibility-state                       (operational pointer, unchanged from 135Z §37/§38.2)
    compatibility-state/<compatibility_state_id>.json  (CompatibilityState history — NEW, closes PREREQUISITE-136A-2)
```

- **Immutable history records**: every `CompatibilityState` transition
  (135Z §33.8: `enabled×legacy_authoritative → ... → disabled×legacy_retired`,
  monotonic forward only) writes a **new** history file at
  `compatibility-state/<compatibility_state_id>.json`, content-addressed
  by `compatibility_state_id` (135Z §25.1: content-derived deterministic),
  exactly mirroring `authority-state/<state_id>.json`'s pattern.
- **Current compatibility pointer**: `current-compatibility-state`
  (already frozen, 135Z §37/§38.2, classification `operational`) is
  updated atomically (write-temp/fsync/rename, 135Z §36) to reference the
  latest history file's `compatibility_state_id`, exactly mirroring
  `current-authority-state`'s relationship to `authority-state/*.json`.
- **Component identity, allowed operations, forbidden authority reads,
  fallback-disabled state**: unchanged from 135Z §22.1's field list
  (`legacy_component`, `allowed_reads`, `forbidden_authority_behavior`,
  `fallback_state` — never `authoritative_fallback`, no such value
  exists).
- **Historical mode, retirement eligibility**: `historical_support`
  (boolean) and `retirement_eligibility` (`not_eligible |
  eligible_pending_governed_phase`) fields, unchanged from 135Z §22.1,
  govern these; retirement itself always requires a separately governed
  future phase (135Z §22.1, restated).
- **This closes 135Z §36's general claim exactly** — every "atomic
  current pointer" persistence-classified family (`AuthorityState`,
  `CompatibilityState`) now has a listed, symmetric history-preserving
  sibling in the frozen namespace. No other family in 135Z §36's table
  needed correction (re-verified: `AuthorityEpoch` is
  "immutable identity-addressed," already has its own file per epoch, not
  an atomic-current-pointer family requiring a separate history sibling).

**PREREQUISITE-136A-2 is resolved by this document.**

---

## 8. Shared schema components

`shared/envelope.schema.json` `$defs`:

- `schema_identity` — `{schema_id: string (pattern
  "^CLTR-[A-Z-]+-[0-9]{3}$"), schema_version: string (semver pattern)}`.
- `record_identity` — `{record_id: <sha256_hex>}` ($ref
  `identity.schema.json#/$defs/sha256_hex`).
- `phase_and_transition_identity` — `{phase_id: string, transition_id:
  <sha256_hex-or-existing-format>}`, used only where 135Z §24.2 marks
  these mandatory (all families except `AuthorityEpoch`,
  `CompatibilityState`).
- `migration_epoch_binding` — `{migration_epoch: string}`.
- `authority_epoch_binding` — `{authority_epoch_id: <sha256_hex>}`, used
  only where 135Z §24.2 marks it mandatory (all except
  `ConcurrencyConflict`, which instead carries `request_ids`).
- `generation_reference` — `{generation_id: <sha256_hex>, generation_digest:
  <sha256_hex>}` (`$ref` target for every `target_generation_id`/
  `_digest`, `source_generation_id`/`_digest` pair — always paired,
  135Z §27's ID+digest cross-record binding rule enforced structurally by
  making the paired shape the only reusable `$def`, so a schema author
  cannot accidentally reference an ID field without its digest sibling).
- `digest_reference` — `$ref` alias to `digest.schema.json#/$defs/sha256_hex`
  for bare digest fields with no paired ID (e.g. `readiness_package_digest`
  standing alone where the ID is carried elsewhere in the same object).
- `contract_version_binding` — `{contract_version: string (const or enum
  of currently-valid values, e.g. "CLTR-CUTOVER-001/1.0")}`.
- `limitations_field` — `$ref limitations.schema.json#/$defs/limitations_array`.
- `authority_disclosure` — `{authority_role: <AuthorityRole enum $ref>,
  is_authoritative: {const: false}, disclosure_text: {type: string}}` —
  the `const: false` is load-bearing: it is the schema-level enforcement
  of 135Z §32.1/§35's rule that no companion record may declare itself
  authoritative (§17 below elaborates).
- `reason_code` — `$ref` alias to `failures.schema.json#/$defs/reason_code_enum`
  (135Z §31's 22-value vocabulary).
- `timestamp_field` — `{type: string, format: "date-time"}` (annotation
  only, §2 above), used for every evidence-only timestamp.
- `immutable_record_metadata` — combines `schema_identity` +
  `record_identity` + `contract_version_binding`, the minimal shape every
  family shares regardless of mutability class.

`shared/envelope.schema.json#/$defs/companion_envelope` composes the
above into the one envelope `$def` every `records/*.schema.json` file
`$ref`s once, then extends via its own `properties`/`required` (§9 of
135Z: no forced-null placeholder fields — a schema that does not need
`phase_id` simply does not list it in its own `properties`, and since
`additionalProperties: false` is per-file not inherited via `allOf`, this
is naturally achievable without an oversized universal envelope, §9
below).

---

## 9. Envelope architecture

Universal fields (present in every `records/*.schema.json`, always
required): `schema_id`, `schema_version`, `record_type`, `record_id`,
`migration_epoch`, `contract_version`, `limitations`,
`authority_disclosure`, `record_digest` (present in the wire shape but
excluded from the schema's own `required` list at the *outer* envelope
position only in the sense that a record is always written with its
digest already computed — `record_digest` is required, never optional,
matching 135Z §24.1 exactly: "every companion record ... carries ...
`record_digest` (self-excluded)" means self-excluded from the *digest
computation's own input set*, not absent from the record).

Family-required fields (present only where 135Z §24.2 marks them
mandatory): `phase_id` + `transition_id` (all families except
`AuthorityEpoch`, `CompatibilityState`); `authority_epoch_id` (all except
`ConcurrencyConflict`); `source_revision`/`final_input_revision` (only
`CutoverRequest`, `ReadinessEvidencePackage`, `CutoverCandidate`,
`Certification`). Each `records/*.schema.json` file's own `properties`
block includes exactly the family-required fields its 135Z section
defines — never all of them defensively, avoiding the "oversized
universal envelope forcing irrelevant null fields" the phase brief
warns against (this is the concrete implementation of 135Z §24.2's
"irrelevant fields are never forced into a record merely for envelope
uniformity" instruction, at the schema-file level: `AuthorityEpoch`'s
schema file has no `phase_id` property at all, not a `phase_id: {type:
["string", "null"]}` placeholder).

Optional fields: every field a family's 135Z section marks nullable
(e.g. `AuthorityState.publication_evidence_id`) is expressed as `{"type":
["string", "null"]}` (or the appropriate typed union) and is **absent**
from that schema's `required` array — but, per §2's unknown-key policy,
it must still be a **named** property (declared, just not required), so
that `additionalProperties: false` does not reject a conformant payload
that includes it.

**Absent vs. null**: per 135Z §6.3 and §30, absent and explicit `null`
are treated identically for `CutoverRequest`'s own optional fields only
(a narrow, explicitly scoped exception) and are **not** interchangeable
for any other authority-bearing family — for those, `null` is a valid
value only where the schema explicitly types a field as nullable; an
absent required field is `invalid_schema` regardless of family. This
distinction is encoded per-file: `cutover_request.schema.json` alone
uses `"type": ["string", "null"]` liberally for not-yet-known digest
fields (per §6.3's "everything except limitations and the not-yet-known
digests before their producing step completes" rule); every other
authority-bearing schema uses `"required"` strictly and reserves `null`
typing only for fields 135Z's own section explicitly marks nullable.

Records created before an authority epoch exists (the first-ever legacy
epoch of a repository) have no `predecessor_epoch_id` value other than
explicit `null` (135Z §4.1: "nullable; null only for the first-ever epoch
of a repository") — the schema for `AuthorityEpoch` types this field
`["string", "null"]` and requires it (present, but may be `null`),
distinct from a field that is merely absent.

---

## 10. Enum architecture

`shared/enums.schema.json#/$defs`, one `$def` per enum, each a bare
`{"type": "string", "enum": [...]}` with the exact 135Z §3 wire values,
referenced via `$ref` everywhere the enum is used (never inlined at each
use site, so a future MAJOR enum revision changes one place):

- `authority_kind_enum` — `legacy | cltr` (§3.1).
- `authority_role_enum` — `authoritative | derivative | operational |
  evidence | compatibility | historical | quarantined` (§3.2) — note:
  though `authoritative` is a listed wire value, `shared/envelope.schema.json`'s
  `authority_disclosure` `$def` additionally forces `is_authoritative:
  {const: false}` at every companion-record use site (§8), so a
  conformant companion-record payload can never combine
  `authority_role: authoritative` with an internally-consistent
  disclosure — this is a deliberate belt-and-braces schema-level
  redundancy, not an inconsistency, directly closing the risk 135Z §2
  row-classification and §35's boundary table both warn about.
- `migration_stage_enum` — eleven values, `shadow` through
  `legacy_retired` (§3.3).
- `generation_role_enum` — eight values (§3.4).
- `publication_state_enum` — twelve values (§3.5).
- `recovery_state_enum` — ten values (§3.6).
- `compatibility_mode_enum` — six values (§3.7).

Record-local enums (136A-confirmed, classified per family, each its own
`$def` co-located in the owning family's `records/*.schema.json` file
since they are not cross-family shared vocabulary): `CutoverRequest.request_state`
(135Z §33.1, nine values), `HumanAuthorization`'s paired `used_state` ×
`revocation_state` (§33.2), `CutoverCandidate.candidate_state` (§33.3,
four values), `Certification.certification_state` (§33.4, four values),
`ConcurrencyConflict.loser_classification` (§14.1, three values),
`QuarantineRecord.disposition_state` (§17.1, four values),
`ReconciliationResult`'s per-field verification states (§16.1 — not
schema-file-relevant, since `ReconciliationResult` has no persisted
schema, §4 row 13). `PublicationEvidence.publication_outcome` reuses the
exact seven-value list from 135Z §13.2 as a dedicated local `$def`
(distinct from, but referencing the same value set intent as,
`publication_state_enum` — the two are not merged into one `$def`,
since `PublicationEvidence.publication_outcome`'s seven values and
`PublicationState`'s twelve values are not identical sets, per 135Z's
own text).

Every enum `$def` is a closed set with no permissive fallback member,
directly implementing 135Z §30's "no enum ... defines an
unknown/other catch-all value." A payload value outside the enum's
`enum` array fails schema validation, which is exactly and only the
fail-closed behavior 135Z requires — free-form strings are never used
where the contract requires a fail-closed value.

---

## 11. Authority role encoding

Every companion record has exactly **one** `authority_role` field
(`AuthorityRole` enum, §10) plus orthogonal status flags specific to its
own family (e.g. `CutoverCandidate.candidate_state`,
`Certification.certification_state`) — this is the "role plus orthogonal
status flags" pattern, not a controlled combination-role set: the role
answers "what kind of thing is this relative to authority" (always one
of the seven §3.2 values, structurally never `authoritative` for a
companion record per §10's `is_authoritative: const false` enforcement)
while the family-specific state field answers "where is this specific
record in its own lifecycle" (§21 below, state-transition matrices).
Combining these two orthogonal axes could never imply authority
accidentally, because `is_authoritative: false` is structurally
unconditional — no combination of `authority_role` and any family-local
state value can flip it to `true` for a companion record, since the
schema literally has no path to write `true` into that field anywhere
except the single authoritative-generation schema this contract's
companion families are explicitly distinct from (135Z §35: "the
authoritative generation itself" is the only row not classified as
companion-record boundary). Only the future authoritative generation and
the resolved current authority (both outside this document's schema set
— they belong to CLTR-SCHEMA-001 and the future authority pointer,
§20 below) may claim authoritative status; every schema this document
defines is, by construction, incapable of it.

---

## 12. Identity architecture

JSON Schema validates **shape only**: every identity field
(`record_id`, `request_id`, `authorization_id`, etc.) is constrained to
`shared/identity.schema.json#/$defs/sha256_hex` — `{"type": "string",
"pattern": "^[0-9a-f]{64}$"}`, enforcing prefix-free exact-length
lowercase-hex shape (135Z §25.2's canonical string format), required
field presence, and correct type. This is **shape validation only**.

The schema layer explicitly does **not**, and structurally cannot,
recompute: **canonical identity** (re-deriving `epoch_id`,
`request_id`, etc. from their §25/§4.2/§6.2/§8.2/§12.2 formulas over the
record's own content — this requires executing the exact `canonical_json`
+ SHA-256 procedure `pcae.cltr.canonicalization`/`pcae.cltr.digest` already
implement for CLTR-SCHEMA-001, reused unchanged, §14 below); **content
bindings** (that a `record_digest` actually matches the record's own
canonical content — a Layer 3 responsibility); **replay conflicts**
(that a resubmitted `request_id` matches its original binding fields,
135Z §6.3 — requires comparing against previously-persisted state, which
JSON Schema, a stateless per-document validator, cannot do); or
**cross-record identities** (that a `target_generation_id` +
`target_generation_digest` pair actually resolves to a real, matching
generation — a Layer 4 responsibility, §27 below). A future semantic
validator layer **must** recompute all four of the above; **this
document does not pretend JSON Schema alone can prove deterministic
identity**, stated here as an explicit architectural boundary, not an
oversight.

---

## 13. Reference architecture

Every cross-record reference is `stable ID + digest`
(`shared/references.schema.json#/$defs/id_digest_pair`), never a bare
filesystem path — directly implementing 135Z §27's cross-record binding
rule and §39's "record references must use stable IDs and digests rather
than trusting arbitrary paths." No schema in this architecture accepts a
raw path string as an identity-bearing or reference-bearing field (path
strings appear only inside `limitations` free text, per 135Z §26, which
this architecture preserves).

Reference classification, each using the same `id_digest_pair` `$def`:

| Reference | Used in |
|---|---|
| generation reference | `CutoverRequest`, `ReadinessEvidencePackage`, `CutoverCandidate`, `Certification`, `CasExpectation`, `AuthorityState` |
| request reference | `CutoverCandidate`, `Certification`, `PublicationAttempt`, `ConcurrencyConflict` |
| readiness-package reference | `CutoverCandidate`, `Certification`, `HumanAuthorization` |
| authorization reference | `CutoverCandidate`, `PublicationAttempt` (via certification chain) |
| certification reference | `PublicationAttempt` |
| CAS-expectation reference | embedded, not referenced (§4 row 10) |
| publication-attempt reference | `PublicationEvidence`, `RecoveryJournalEntry`, `ConcurrencyConflict` |
| publication-evidence reference | `AuthorityState`, `RecoveryJournalEntry` |
| journal reference | `RecoveryJournalEntry.previous_entry_digest` (self-chaining, §15) |
| marker reference | `MarkerAuthorityBinding`, `NotificationAuthorityBinding` |
| receipt reference | `FinalizationReceiptAuthorityBinding` |
| historical-authority reference | runtime-only, §4 row 20 — no schema file |

Every reference is a `$ref` to `id_digest_pair`, never a same-named
bare-ID field without a sibling digest — this is structurally enforced
by making `id_digest_pair` the *only* reusable `$def` for cross-record
fields, so an implementer cannot accidentally define a lone `_id` field
without its `_digest` sibling without deviating from the shared `$def`.

---

## 14. Canonicalization architecture

**Reused verbatim, no divergence**: this architecture adopts
`pcae.cltr.canonicalization`'s existing rules unchanged — UTF-8, Unicode
NFC normalization, lexicographic byte-wise-ASCII key sorting at every
nesting level, preserved array ordering except where a family's own 135Z
section specifies a canonical sort key (§7.2's `unresolved_findings`/
`entry_point_evidence`; §15.1's `entry_sequence`), compact JSON with no
insignificant whitespace, and UTC RFC 3339 second-precision timestamps
(135Z §26, itself reusing CLTR-SCHEMA-001 §14 in full).

**Schema-enforceable** (Layer 2, this architecture): field types, string
patterns (digest/identity shape), enum membership, required/optional
presence, `additionalProperties` closure, array item shape.

**Requires canonicalization code** (Layer 3, not this phase): key
sorting, NFC normalization, compact serialization, digest computation
over the canonicalized form — none of which JSON Schema performs or
asserts; a payload that is schema-valid but not canonically serialized
is still schema-valid (JSON Schema validates parsed structure, not byte
layout), so canonicalization conformance is checked by re-serializing
through `pcae.cltr.canonicalization` and comparing, never by a schema
keyword.

**Requires semantic validation** (Layer 4, not this phase): that a
record's *content*, once canonicalized, actually produces the
`record_digest` it claims (§27's identity/digest recomputation
boundary, restated here for the canonicalization angle specifically).

**Duplicate-key rejection, path normalization**: inherited from
CLTR-SCHEMA-001 §14 unchanged, plus this contract's own additive
path-normalization rule (135Z §26 — POSIX-style, repo-relative, no `..`,
no symlink assumption) for the namespace layout (§38.2 of 135Z, §20
below), applied at the parser level (before any schema validation even
begins — duplicate-key rejection happens during JSON parsing, which
necessarily precedes schema evaluation), not as a JSON Schema keyword
(JSON Schema has no native duplicate-key-rejection keyword; this remains
a parser-level responsibility, consistent with CLTR-SCHEMA-001's existing
treatment). **No divergent Stage 3 canonicalization implementation is
created** — this is stated as a binding architectural constraint, not
merely a description.

---

## 15. Digest architecture

Every digest field (`record_digest`, `generation_digest`, `manifest_digest`
where referenced, `authority_pointer_digest`, `entry_digest`,
`previous_entry_digest`) is schema-typed as
`shared/digest.schema.json#/$defs/sha256_hex` — the same shape `$def`
identity fields use (135Z §25.1: "canonical string format ... lowercase
hexadecimal SHA-256 digest string, exactly 64 characters"; digests and
content-derived identities share one shape family, since a
content-derived identity **is** a digest, per 135Z §25.1's own
classification for most families).

**Schema validation** confirms shape (64 lowercase hex characters) and
presence/absence per §9's rules. **Digest recomputation** — that a
digest field's value actually equals SHA-256 of the record's own
canonical content minus excluded fields (135Z §27's per-family exclusion
set: `{record_digest itself, created_time/*_at timestamps, limitations}`)
— is a Layer 3 responsibility using `pcae.cltr.digest`'s existing
digest-computation function, unchanged, never re-implemented.

**Field exclusion conventions**: encoded as documentation (each schema
file's `description` on its digest field states the excluded-fields set
for that family) rather than as an enforceable JSON Schema keyword — JSON
Schema has no native "this field excludes these other fields from a
derived computation" keyword; exclusion enforcement is necessarily a
Layer 3 semantic-validator responsibility, stated here as a boundary, not
deferred silently.

**Recursive self-coverage prevention**: every digest field is
schema-required to be *absent from its own computation input* by
construction of the digest function itself (§27's "self-excluded" rule,
inherited from CLTR-SCHEMA-001 §15.2–§15.4 unchanged) — the schema layer
cannot enforce this directly (it is a property of the digest *algorithm*,
not the *document shape*), but it documents the requirement at every
digest field's schema `description` so a future implementer cannot miss
it.

**Manifest digest**: not applicable to any companion record individually
(135Z §27) — no companion schema in this architecture has a
`manifest_digest` field; manifest-level digesting stays scoped to the
authoritative generation itself (CLTR-SCHEMA-001 §16), outside this
document's schema set entirely.

---

## 16. Temporal architecture

Every timestamp field (`issued_at`, `expiry_at`, `observed_time`,
`attempted_at`, `completed_at`, `entry_timestamp`, etc.) is schema-typed
`{"type": "string", "format": "date-time"}` (annotation only, §2) with a
`description` stating its RFC 3339/UTC/second-precision requirement
(135Z §28.2) — `format: date-time` is **not** asserted at the schema
layer by default in most JSON Schema validators (2020-12 makes `format`
annotation-only unless a validator opts into assertion mode); this
architecture does **not** rely on `format` assertion for correctness,
since UTC-and-precision enforcement is inherently a semantic-validator
check (parsing the string and confirming timezone offset `Z`/`+00:00`
and second-not-sub-second precision) that a bare `format` keyword cannot
guarantee across validator implementations — stated as a deliberate,
documented Layer 4 responsibility, not a gap.

**No timestamp establishes authority** (135Z §28.2, restated as a
binding architectural constraint on every schema this document defines):
no schema field named `*_at`/`*_time` ever appears in an `enum`,
`const`, or any authority-classification context; every such field's
`description` states "evidence-only; excluded from `record_digest` and
from this record's identity formula" (§12, §15). **Clock-skew and
freshness** (e.g. `HumanAuthorization`'s 24-hour window, `Certification`'s
staleness-by-state-comparison rule) are Layer 4 semantic-validator
responsibilities — comparing an `expiry_at` value against
`observed_time` requires runtime clock access and cross-record
comparison, neither of which JSON Schema performs.

---

## 17. AuthorityEpoch schema architecture

`records/authority_epoch.schema.json`. Fields per 135Z §4.1, schema-typed
directly: `epoch_id` (identity `$def`), `authority_kind` (`$ref` enum),
`migration_epoch` (string), `contract_version`, `schema_version`,
`predecessor_epoch_id` (nullable identity `$def` — required, may be
`null`, per §9's rule), `target_authoritative_generation` (nullable
generation-reference `$def`; presence conditionally required via
`if`/`then` keyed on `activation_state`, §2's conditional-validation
approach — present only once `activation_state != "proposed"`, never
required for a freshly proposed epoch), `creation_transition` (identity
`$def`), `activation_state` (local `$def`: `proposed | active |
superseded`), `historical_state` (local `$def`: `current | historical`),
`supersession_state` (nullable identity `$def`), `limitations`,
`record_digest`.

**Candidate vs. active epoch representation**: both are the *same*
schema — `AuthorityEpoch` — distinguished only by `activation_state`
value, per 135Z §4.3's frozen decision that a candidate authority epoch
"does exist as its own `AuthorityEpoch` record with `activation_state=proposed`
before publication," never an embedded field inside the cutover request.
This document does not introduce a second schema for "proposed" vs.
"active" epochs — one schema, one enum field, exactly matching 135Z's own
frozen decision, resolved here at the file-layout level rather than left
implicit.

---

## 18. AuthorityState schema architecture

`records/authority_state.schema.json`. Fields per 135Z §5.1, including
the tagged-union `current_authoritative_object` (§2's conditional-union
pattern: `oneOf` on `kind: legacy` vs `kind: cltr`, the `cltr` branch
requiring `transition_id`/`generation_id`).

The exact relationship (135Z §5.2, restated as this document's binding
architecture): **production authority pointer (written first, atomically)
→ AuthorityState (written second, evidence-adjacent) → referenced by →
publication evidence.** The schema encodes this as a *documentation*
constraint (each field's `description` states its evidence-adjacent,
never-primary-source role) rather than an enforceable JSON Schema
keyword, because the ordering guarantee ("written first," "written
second") is a *write-sequencing* property of a future implementation, not
a *document-shape* property JSON Schema can assert over a single JSON
document in isolation.

**Preventing pointer/state, state/generation, epoch/generation
disagreement**: these are all Layer 4 cross-record semantic-validation
responsibilities (135Z §34's CSCH-INV-5, CSCH-INV-6, CSCH-INV-9 — §27
below), never schema-layer checks, since they require comparing two or
more separately-persisted documents' contents against each other, which
a single-document JSON Schema validator structurally cannot do.
**Publication evidence proves the transition but remains
non-authoritative**: enforced identically to every other family via the
`authority_disclosure.is_authoritative: const false` rule (§8, §11) —
`AuthorityState`'s own schema is no exception, despite being the family
"closest" to authority; it is not the pointer, and its schema
structurally cannot claim otherwise.

**History preservation**: `authority-state/<state_id>.json` (135Z §38.2,
unchanged) — every successful/uncertain publication writes a *new* file,
never overwrites a prior one; `current-authority-state` (operational
pointer) is updated atomically to reference the latest. Both paths use
`records/authority_state.schema.json` for their content shape — history
files and the "current" pointer target the same schema, distinguished
only by which file the operational pointer currently names.

---

## 19. CutoverRequest schema architecture

`records/cutover_request.schema.json`. Resolving the ordering (135Z's
own already-decided answer, restated and confirmed as the schema
architecture's binding sequence — no circular dependency exists):

```
base request (CutoverRequest, §6)
    | binds: source/target epoch, target generation, evidence IDs
    v
readiness package (ReadinessEvidencePackage, §7)
    | aggregates Stage 1/2/rollback evidence; package_id is independent of request_id
    v
authorization (HumanAuthorization, §8)
    | binds: request_id + readiness_package_digest + target_generation_digest
    v
candidate (CutoverCandidate, §9)
    | binds: request_id + readiness_package_digest + authorization_digest + cas_expectation
    v
certification (Certification, §10)
    | binds: cutover_candidate_id + request_digest + readiness_package_digest + authorization_digest
```

This is the verified contract's actual decision (135Z §6.1, §7.1, §8.1,
§9.1, §10.1's field lists, cross-checked): `CutoverRequest` references no
downstream record (it is created first, `authorization_requirement:
required | not_yet_evaluated` — never `not_required`, meaning the request
itself explicitly flags that authorization has not yet happened, without
referencing a not-yet-created `HumanAuthorization` record); each
downstream record references its immediate predecessors by ID+digest
(§13); no downstream record is referenced *by* an upstream one (a
`CutoverRequest` schema has no `candidate_id` or `certification_id`
field) — this asymmetric reference direction is what makes the chain
acyclic by construction, not merely by convention.

**Authorization-requirement fields in the initial request**: per 135Z
§6.1, `authorization_requirement` (`required | not_yet_evaluated`) is the
only authorization-related field the initial `CutoverRequest` schema
carries — it does not embed a placeholder `authorization_id` field
(nullable or otherwise), since the request is created before any
authorization exists and 135Z's design deliberately keeps the binding
one-directional (authorization references the request, never the
reverse) to avoid a forward-reference cycle.

---

## 20. ReadinessPackage schema architecture

`records/readiness_package.schema.json`. Per 135Z §7.1: **referenced**,
not embedded, evidence — `stage1_evidence`, `stage2_evidence`,
`rollback_evidence` are each `{id, digest, observed_at, source_revision}`
shapes (a "small reference bundle" `$def`, not the full evidence
document embedded inline), avoiding an unbounded object containing every
historical artifact. `entry_point_evidence` is an array of exactly four
entries (one per production entry point, 135Z §7.1), each `{entry_point:
enum of the four frozen names, coverage: boolean, evidence_reference}`.

**Deterministic collection ordering**: `unresolved_findings` sorted by
finding ID, `entry_point_evidence` sorted by the frozen order
(`run_phase_complete, run_task_finish, run_phase_report_create,
run_notify_send_report`, 135Z §7.2) — enforced as a Layer 3
canonicalization-time responsibility (re-serializing through the
canonicalization module produces the sorted order for digesting), not a
JSON Schema `"uniqueItems"`/ordering keyword (JSON Schema arrays are
order-sensitive by default but cannot themselves *impose* a sort order on
otherwise-valid input — it can only reject wrongly-typed items, not
mis-ordered ones — so ordering conformance is checked by canonical
re-serialization comparison, exactly as digest conformance is, §14).

**Representation of missing/stale/unsupported/uncertain/conflicting/
prerequisite-open/verified**: `prerequisite_status` (`ready | not_ready |
uncertain`, 135Z §7.1) plus the `unresolved_findings` array (which, when
non-empty, is exactly the "prerequisite open" signal) together cover
this space; there is no separate seven-value status enum — 135Z's own
design collapses the seven concepts named in the phase brief into the
combination of `prerequisite_status` (three values) plus
`unresolved_findings` (empty-vs-non-empty plus content) plus each
evidence item's own `stale`-detection rule (§7.2: mismatched
`source_revision` against the shared package). This document does not
invent a new redundant status enum beyond what 135Z already froze.

---

## 21. Authorization schema architecture

`records/human_authorization.schema.json`. Fields per 135Z §8.1:
`principal_identity` (string — operator identifier, never a
credential/token shape, §22 below), `authorization_method`
(`interactive_cli | signed_artifact`), `request_id` (identity `$def`),
`expiry_at` (timestamp), `revocation_state` (`active | revoked`),
`used_state` (`unused | used`), `replay_binding` (a nonce — schema-typed
as an opaque string with a minimum-length constraint for entropy
guidance, not a cryptographic assertion JSON Schema can make),
`risk_acknowledgement` (`{"const": true}` — the schema **requires** this
literal, directly enforcing 135Z §8.1's "must be `true`" rule at the
shape level, the one place in this family where JSON Schema *can*
mechanically enforce a semantic rule, since it is a fixed literal, not a
cross-record comparison), `scope` (`{"const":
"single_request_single_target"}` — no broader scope exists in v1, same
mechanical enforcement).

**No reusable secret may be stored**: `principal_identity` is
schema-typed as a plain string with no format implying credential
material; this document's schema does not define a field capable of
holding a bearer token, API key, or password (§22 elaborates the
secret-handling rule this directly implements — the absence of such a
field *is* the enforcement, since a schema cannot forbid content within
an otherwise-valid string field, only forbid the field's *existence*
where inappropriate).

**Cryptographic signature validation**: **deferred**, not required in
the first implementation — `authorization_method: signed_artifact`
schema-validates only that a method tag and an evidence-of-signing
digest are present (135Z §8.1: "may store signed or hashed evidence ...
but never the signing key or raw credential material itself"); actual
cryptographic verification of a signature against a public key is
explicitly out of this contract's and this architecture's scope (135Z
§8.3: "this contract does not define principal identity verification —
out of scope"), a Layer 4/5/6 concern for a future, separately governed
execution-authorization design.

---

## 22. Candidate and certification schema architecture

`records/cutover_candidate.schema.json` and
`records/certification.schema.json`, each binding the prior chain by
ID+digest (§13, §19) rather than duplicating entire upstream records —
`Certification` does not re-embed `CutoverCandidate`'s full field set; it
carries `cutover_candidate_id` plus its own `target_generation_id`/
`_digest` (duplicated as a convenience field for direct queries without a
join, matching 135Z §10.1's own field list exactly — this is a
deliberate, bounded duplication of one reference pair, not the whole
candidate object).

**Certification immutability, staleness, non-authority**: `Certification`
carries `certified_at` as its only excluded-from-digest field (135Z
§10.2); staleness is a Layer 4 comparison
(`source_authority_state_digest` vs. live `AuthorityState.record_digest`
at publication time), not a schema-layer check. Certification's
`authority_disclosure.is_authoritative` is `const: false` identically to
every other family (§8, §11) — certification is evidentiary, never
itself authoritative, and issuing one has no schema-representable "side
effect" field (no field in `certification.schema.json` writes to
anything outside itself, by construction — the schema simply has no such
capability, mirroring 135Z §10.2's "no publication side effect" rule at
the file-boundary level: this schema describes one document, nothing
else).

---

## 23. CAS schema architecture

`shared/references.schema.json#/$defs/cas_expectation` (embedded-only,
§3, §4 row 10). Fields per 135Z §11.1: `expected_authority_kind` (`$ref`
enum, required), `expected_authority_epoch_id` (identity `$def`,
required), `expected_authoritative_generation` (tagged-union, required),
`expected_authority_pointer_digest` (digest `$def`, required),
`expected_authority_state_digest` (digest `$def`, required),
`expected_source_lifecycle_state` (string enum, required),
`expected_compatibility_mode` (`$ref` enum, required),
`expected_lock_or_journal_state` (nullable — the **only** optional field
in this `$def`, per 135Z §11.2's exact statement: "only
`expected_lock_or_journal_state` is optional ... every other field is
mandatory").

**No wildcard-on-missing behavior**: this is enforced structurally by
listing every field above except `expected_lock_or_journal_state` in the
`$def`'s `required` array — a payload omitting any of the seven mandatory
expected-value fields fails schema validation outright (`invalid_schema`),
which is the schema-layer's contribution to closing PREREQUISITE-135X-1
(135Z §11.2 names this explicitly: "this schema exists specifically so
that gap has a concrete, checkable structure to close against"). **Live
comparison** against actually-recorded state immediately before
publication remains a Layer 5 (live-state/CAS) responsibility — the
schema can only guarantee that an expectation record, once written, has
no missing-therefore-wildcard field; it cannot itself perform the compare
against live state.

---

## 24. Publication schemas

`records/publication_attempt.schema.json` and
`records/publication_evidence.schema.json` — two distinct files,
per 135Z §12/§13's own separation: **attempt** records describe the
action taken and its immediate, possibly-uncertain outcome
(`publication_state`, reusing the twelve-value enum, §10); **evidence**
records describe the confirmed, observed outcome
(`publication_outcome`, the distinct seven-value enum, §10).

`publication_evidence.schema.json`'s `publication_outcome` `$def` is
schema-typed as exactly: `not_attempted | cas_rejected |
published_and_verified | publication_failed | publication_uncertain |
conflict | quarantined` — **exactly these seven, no others** (135Z
§13.2's own emphatic statement, reproduced as the literal `enum` array).
`publication_uncertain` is structurally distinct from both
`publication_failed` (a confirmed negative outcome) and
`published_and_verified` (requires both confirmed CAS acceptance and
passing readback) — the schema does not collapse any of these three
into another; each is its own enum member with its own semantic weight,
undiluted by a shared parent category.

---

## 25. Concurrency conflict schema architecture

`records/concurrency_conflict.schema.json`. `winner` is nullable (135Z
§14.1: "populated only when a deterministic winner rule ... applies") —
the schema does not require a winner in all conflicts; `authority_result`
is required (the `AuthorityState` reference that prevailed, always
knowable even when `winner` is not, since *some* state is always current
after a conflict resolves). `expected_state`/`actual_state` are both
required generation/digest-reference `$def`s, capturing what was expected
vs. what was actually observed — present regardless of whether a winner
was determined.

---

## 26. Recovery journal architecture

`records/recovery_journal_entry.schema.json`. Per 135Z §15.1: one entry
schema (no separate aggregate-record schema, §4 row 12); `entry_sequence`
(non-negative integer, sequence-derived per 135Z §25.1 — the one family
whose primary identity is *not* a SHA-256 digest string), `entry_digest`
(digest `$def`), `previous_entry_digest` (nullable digest `$def`, null
only for the chain's first entry).

**Hash chaining**: mandatory (135Z §15.2's frozen decision, re-derived
here, not re-litigated) — `previous_entry_digest` must equal the prior
entry's `entry_digest`; the schema enforces the *field's shape*
(nullable digest string) but the chain-*validity* check (does entry N's
`previous_entry_digest` actually equal entry N-1's `entry_digest`) is a
Layer 4 cross-record check, since it requires reading two documents.
**Partial-write handling**: an atomic write-temp/fsync/rename primitive
(135Z §15.2, reused from CLTR-SCHEMA-001 §17) ensures a partial write
never produces a schema-valid-but-half-written file — this is a Layer 3
persistence-mechanism property, not a schema keyword. **Duplicate
entries**: `entry_sequence` uniqueness per `journal_id` chain is a Layer
4 check (comparing across sibling files), not schema-enforceable within
one document. **Latest-journal convenience pointer**:
`current-recovery-journal` (135Z §37, `operational` classification) is a
plain pointer file, not itself validated against
`recovery_journal_entry.schema.json` (it names a `journal_id` +
`entry_sequence` pair, a much smaller shape — a dedicated tiny `$def`,
`shared/references.schema.json#/$defs/journal_pointer`, not a full entry
schema). **Reconstruction**: the aggregate view is always recomputable by
traversal — no separate persisted aggregate schema exists to get out of
sync (§4 row 12/13's "derived view" classification, restated).

---

## 27. Reconciliation schema architecture

No persisted schema file (§4 row 13, §16 of 135Z). If a future caller
ever chooses to persist a `ReconciliationResult` snapshot for audit
purposes (135Z §16.1: "present only if a caller chooses to persist"),
its shape belongs under a future `views/reconciliation_result.schema.json`
— **not created in 136B**, and explicitly optional even at future
implementation time, since the existing `pcae phase-report reconcile`
precedent computes and prints without persisting. **A persisted
reconciliation must remain non-authoritative** — its schema (if ever
created) would carry the literal field `mutation: {"const": "none"}`,
directly implementing 135Z §16.1's "schema-level enforcement of
'reconciliation must not itself repair authority.'"

---

## 28. Quarantine architecture

`records/quarantine_record.schema.json`. `object_type` enum covers
exactly the six quarantinable families 135Z §17.1 lists: `cutover_candidate
| certification | publication_attempt | authoritative_generation |
readiness_package | authorization`. `source_reference` is an
`id_digest_pair` (§13) — **never a bare path** (135Z §17.1, restated).
`disposition_state` (`quarantined | under_review |
remediated_superseded | permanently_retired`) tracks remediation status
without ever un-quarantining in place (135Z's general "no un-quarantine"
rule applies here identically to every other family's forbidden-backward
transitions, §21 below).

**The current-authoritative-generation-fails-integrity case** (135Z
§17.3): this document does **not** define a resolution mechanism — 135Z
froze only detection/disclosure (the generation becomes
`quarantined_generation`, `AuthorityState.verification_state` becomes
`verification_failed`, `RecoveryState` becomes `operator_review_required`,
`AuthorityKind` **does not change**) and registered the resolution
mechanism as **PREREQUISITE-135Z-1**, explicitly out of scope until a
future activation-adjacent phase. This document's schema architecture
reflects exactly that boundary: `quarantine_record.schema.json` can
represent that this case *occurred* (via `object_type:
authoritative_generation`, `authority_relevance:
blocks_authority_confirmation`), but defines no field or mechanism that
*resolves* it — consistent with, not expanding, 135Z's own scope
decision. **This case must not imply automatic legacy fallback or no
authority** — enforced by the same `AuthorityKind`-immutability principle
already stated (§3.1, §11): no schema field anywhere in this
architecture can write `AuthorityKind: legacy` as an automatic
consequence of a quarantine event.

---

## 29. Notification, marker, and receipt binding schemas

Three files (§4 rows 16–18): `records/notification_authority_binding.schema.json`,
`records/marker_authority_binding.schema.json`,
`records/receipt_authority_binding.schema.json` — each a **standalone
companion schema today** (135Z §19.2, §20, §21.2's explicit "companion
schema required now" determination, not an embedded component and not an
existing-record extension in this phase). No existing schema
(`schemas/repository_intelligence/**`, or CLTR-SCHEMA-001's own wire
format, which has no executable JSON Schema file in this repository at
all — it is defined narratively in `docs/`) is modified by this document
or by any future phase implementing it under this architecture, per the
explicit governed prohibition (135Z §21.2, restated as binding here).

Preserved unconditionally: PFN-001's exactly-once dispatch mechanism and
`.last-notified.json` marker uniqueness semantics (unchanged, §19.1);
one-generation binding (`authoritative_generation` reference, present in
all three); payload digest (`payload_digest`, `NotificationAuthorityBinding`
only); attempt identity (`attempt_identity`, referencing PFN-001's
existing tracking, not redefined); uncertainty (`uncertainty` field, all
three); marker identity (`marker_id`, unchanged existing field, extended
additively per 135Z §24's marker-extension rule — the existing four
marker fields `phase_id`/`commit`/`report_digest`/
`finalization_snapshot_id`/`delivery_purpose` remain, this schema's
fields are additive siblings, never replacements); receipt identity
(same additive-extension principle, §21.1); **no second authority** — all
three schemas' `authority_disclosure.is_authoritative` is `const: false`
identically to every other family (§8, §11) — a marker or receipt binding
can never become a second authority by construction, matching 135Z
§20.2/§21's explicit constraint.

---

## 30. CompatibilityState schema architecture

`records/compatibility_state.schema.json`. Fully specified in §7 above
(PREREQUISITE-136A-2 disposition), which this section cross-references
rather than repeats: immutable history via
`compatibility-state/<compatibility_state_id>.json` (new namespace path,
§7), current pointer via `current-compatibility-state` (unchanged, 135Z
§37), fields per 135Z §22.1 unchanged (`legacy_component`, `role`
[`$ref` `authority_role_enum`, always `compatibility`],
`allowed_reads`, `forbidden_authority_behavior`, `fallback_state`
[`none | read_only_fallback` — **no `authoritative_fallback` value
exists in this enum's `$def`, by design**, directly implementing 135Z
§22.1's "never `authoritative_fallback`"], `historical_support`,
`migration_stage` [`$ref` `migration_stage_enum`], `disablement_state`
[`enabled | disabled`], `retirement_eligibility` [`not_eligible |
eligible_pending_governed_phase`]).

**§22.2's structural enforcement, restated at the schema level**:
`compatibility_state.schema.json`'s `properties` block has **no field
capable of setting `authority_kind`** — there is no `authority_kind`
property in this schema at all, so no conformant payload for this family
can even *attempt* to carry an authority-kind value, let alone set it to
`legacy`. This is the schema-level counterpart to 135Z §3.7's enum-level
rule and §22.2's structural rule, made concrete in the actual file's
field list rather than merely asserted in prose.

---

## 31. Historical reference schema architecture

No persisted schema file (§4 row 20, 135Z §23 — runtime-only typed
model). If future documentation benefits from a published shape (e.g.
for a CLI `--json` output contract over historical lookups), it belongs
under a future `views/historical_authority_reference.schema.json` — not
created in 136B. Constraints this future typed model must satisfy
(restated from 135Z §23.2, unchanged): explicit reference kind (no
implicit "look at whatever is oldest"), read-only, non-authoritative for
current transitions (never consulted by the resolver), schema/version
aware (a reference to a pre-135J CLTR-SCHEMA-001 v1.0.0 record discloses
that version, never silently normalized), limitation-bearing. **No
historical artifact is rewritten** by anything this architecture defines
or enables — restated as an absolute constraint, not a guideline.

---

## 32. Cross-record semantic validation architecture

JSON Schema (Layer 2, this document's entire scope) validates local
shape only. A future **semantic-validator layer** (Layer 4, not
implemented by this phase) must validate, at minimum, every one of 135Z
§34's fifteen cross-record invariants (CSCH-INV-1 through CSCH-INV-15,
reproduced verbatim in §27 of this document below is unnecessary since
135Z already enumerates them exhaustively — this document instead binds
each to its schema-file-pair boundary):

| Invariant | Schema files whose *cross-file* comparison enforces it |
|---|---|
| CSCH-INV-1 (single `migration_epoch` per record) | every `records/*.schema.json` — shape-checkable within one file, actually Layer 2-enforceable via the single `migration_epoch` property, not multi-file |
| CSCH-INV-2 | `cutover_request.schema.json` ↔ `cutover_candidate.schema.json` |
| CSCH-INV-3 | `cutover_candidate.schema.json` ↔ `certification.schema.json` |
| CSCH-INV-4 | `certification.schema.json` ↔ `publication_attempt.schema.json` |
| CSCH-INV-5 | `publication_attempt.schema.json` ↔ `authority_state.schema.json` |
| CSCH-INV-6 | `authority_state.schema.json` (internal — `authority_kind=cltr` implies `publication_evidence_id` non-null; expressible as an `if/then` **within** this one file, the sole invariant of the fifteen that is actually Layer-2-enforceable as a same-document conditional rather than cross-file) |
| CSCH-INV-7 | `notification_authority_binding.schema.json` / `marker_authority_binding.schema.json` / `receipt_authority_binding.schema.json` ↔ `authority_state.schema.json` |
| CSCH-INV-8 | `human_authorization.schema.json` ↔ `cutover_request.schema.json` |
| CSCH-INV-9 | `shared/references.schema.json#/$defs/cas_expectation` ↔ `authority_state.schema.json` |
| CSCH-INV-10 | (no schema file — the production pointer itself, outside this document's set, §20) |
| CSCH-INV-11 | `compatibility_state.schema.json` (structural, §30 above — no cross-file comparison needed, enforced by field absence) |
| CSCH-INV-12 | `quarantine_record.schema.json` ↔ `readiness_package.schema.json` |
| CSCH-INV-13 | (no schema file — `HistoricalAuthorityReference` is runtime-only, §31) |
| CSCH-INV-14 | `publication_attempt.schema.json` (multiple instances) ↔ `concurrency_conflict.schema.json` |
| CSCH-INV-15 | `recovery_journal_entry.schema.json` (multiple instances, chain traversal) |

Note that **CSCH-INV-6 and CSCH-INV-11 are the only two invariants this
architecture can partially enforce at Layer 2** (same-document
conditionals); the remaining thirteen are irreducibly cross-document and
belong to Layer 4. This table itself is not exhaustive proof of
correctness — it is the traceability scaffold §28 formalizes.

---

## 33. Executable-schema registry

Future behavior (not implemented): a **schema-ID-to-file mapping**
(`schema_id` string, e.g. `"CLTR-AUTHORITY-STATE-001"`, → relative file
path under `schemas/cltr_cutover/`), built by a simple directory scan at
process start (mirroring the fact that no schema-loader/registry module
exists yet anywhere in this repository for `repository_intelligence`
either — this is a new pattern, not an extension of an existing one).
**Version lookup**: `(schema_id, schema_version)` → file, since a future
MINOR revision may co-exist as a separate file
(`authority_state.v1.1.schema.json`) rather than an in-place edit,
matching CLTR-SCHEMA-001 §2's discipline of frozen historical versions
remaining readable. **Compatibility**: the registry exposes which
`(schema_id, schema_version)` pairs are valid together for a given
`CLTR-CUTOVER-SCHEMAS-001` contract version (135Z §42's deferred
compatibility matrix — not populated until a second schema version
exists). **Unknown schema**: `invalid_schema`/`unsupported_version`
(135Z §31), fail-closed. **Duplicate schema IDs**: registry construction
fails closed (refuses to start) rather than silently picking one.
**Reference resolution**: relative-path only, resolved against the
package root (§2) — **offline-only, no network fetching**, ever; **no
runtime plugin behavior** — the registry is a static, closed mapping
built once from the frozen `schemas/cltr_cutover/` tree, never
dynamically extended by a loaded plugin. **Integrity verification**: a
future registry **may** additionally digest-verify its own schema files
against a frozen manifest (mirroring the generation-manifest pattern,
CLTR-SCHEMA-001 §16) to detect tampering — registered as an optional
future hardening, not a 136B requirement.

---

## 34. Schema fixture architecture

Planned (no fixture implemented in 136B), one fixture set per
`records/*.schema.json` file, at minimum: (1) minimum valid record — only
required fields present; (2) fully populated valid record — every
optional field present; (3) one fixture per invalid enum — an
out-of-vocabulary value for every enum field in that schema; (4) missing
required field — one fixture per required field, each omitting exactly
one; (5) forbidden field — an authority-bearing family fixture with one
extra unknown property, expected to fail `additionalProperties: false`;
(6) unknown critical field — same as (5), emphasized for the eight
authority-bearing families specifically (§2); (7) unsupported version —
a `schema_version` value the registry (§33) does not recognize;
(8) null-vs-absent — one fixture per family exercising 135Z §6.3's
narrow `CutoverRequest`-only absent/null equivalence, plus a contrasting
fixture for a different family showing the two are *not* equivalent
there; (9) wrong reference shape — an `id_digest_pair` with only the ID
or only the digest present, expected to fail; (10) digest shape —
a too-short, too-long, or uppercase-hex digest string, expected to fail
the `sha256_hex` pattern; (11) path/traversal strings — a `limitations`
or namespace-path-bearing field containing `../` or an absolute path,
expected to fail once path-normalization validation (§14, §38.3 of 135Z)
is implemented; (12) secret-redaction cases — a `principal_identity` or
similar field containing an obviously-token-shaped string (e.g. a
`bot<digits>:<token>`-pattern Telegram-token look-alike), used as a
negative-review fixture for the secret-handling rule (§22 above) even
though JSON Schema cannot itself detect secret *content* — the fixture
documents the expectation for a future Layer 4 secret-scanning check, not
a schema-layer rejection. **No fixture implementation in 136B.**

---

## 35. Security architecture

Schema-level and semantic defenses (135Z §39, translated to this
architecture's concrete mechanisms):

- **Traversal / absolute paths / arbitrary file references**: no
  identity or reference field in any `records/*.schema.json` file accepts
  a filesystem path (§13) — paths appear only in the future namespace
  layout (§38.2 of 135Z, §7/§30 above) and in `limitations` free text,
  neither of which is a digest/identity input (§12, §15); a future
  Layer 3/4 path-normalization check (135Z §38.3) validates the namespace
  itself, outside any individual record's schema.
- **Substituted IDs / substituted digests**: prevented by the
  `id_digest_pair` `$def`'s structural pairing (§13) plus Layer 4's
  digest-mismatch check (§27) — a schema alone can only guarantee the
  *pair* is present and shaped correctly, never that it *matches* a real
  record; that is explicitly a Layer 4 responsibility, stated as a
  boundary here, not silently assumed solved.
- **Unknown critical fields**: `additionalProperties: false` for all
  eight authority-bearing families (§2, §9).
- **Stale evidence**: `stale_*` reason codes (135Z §31) are schema-typed
  as valid `reason_code` enum values a future validator may report, but
  staleness *detection* itself (freshness comparison, digest comparison
  against live state) is Layer 4/5, never Layer 2.
- **Replay**: schema shape supports replay detection (deterministic
  identity formulas, §12; `used_state`/`revocation_state` fields, §21)
  but replay *rejection* is a Layer 4 stateful check comparing against
  previously-persisted records — JSON Schema is inherently stateless per
  document and cannot itself detect replay.
- **Quarantine bypass**: `disposition_state` (§28) plus CAS expectation's
  `expected_lock_or_journal_state` reference (§23) together give a future
  Layer 5 CAS check the fields it needs to reject a quarantined object;
  the schema does not itself perform the bypass check.
- **Compatibility confusion**: `compatibility_state.schema.json`'s field
  omission (§30) is the schema-level defense; it is absolute (no field
  exists to misuse), not probabilistic.
- **Secret persistence**: no schema in this architecture defines a field
  shaped to hold credential material (§21, §22 elaborate) — the defense
  is field-absence, verified by review at fixture time (§34 item 12),
  never by a schema-layer content scanner (JSON Schema has no secret-
  detection keyword).

**Schemas prefer ID-and-digest references over paths** — restated here
as the single governing principle underlying every bullet above,
identical in spirit to 135Z §39's own closing statement.

---

## 36. Secret-handling architecture

Directly implementing 135Z §40, translated to schema fields:

**Permitted**: `principal_identity` (plain operator identifier — string,
no format implying secret material); a hashed/digested reference to a
signed artifact (`authorization_method: signed_artifact` plus an
evidence digest, §21 — the *hash*, never the key); a notification **sink
identity** string (e.g. `"telegram"`, a label, not a destination secret);
machine/process/session identifiers (`verifier_identity`,
`conflicting_actors` — component identity, never host credentials).

**Forbidden** (no schema field in this architecture is shaped to accept
any of the following, by omission, matching 135Z §40's explicit
prohibition list): API tokens; bot tokens (this repository's own
`~/.config/pcae/telegram.env`-sourced Telegram bot token is the concrete,
already-confirmed-present example this rule exists to keep out of any
companion record); passwords; private keys; bearer tokens; raw
environment-secret values of any kind. `NotificationAuthorityBinding`'s
schema in particular has no `destination_secret`/`chat_id`/`token` field
— those remain sourced exclusively from existing environment
configuration outside any companion record, exactly as 135Z §40 requires.

---

## 37. Versioning architecture

- **Per-schema IDs**: minted at implementation time (135Z F-135Z-4,
  deferred), following the pattern `CLTR-<FAMILY>-001` illustrated for
  `CLTR-AUTHORITY-STATE-001` (135Z §5.1) — this document does not
  speculatively mint the remaining fifteen IDs, consistent with F-135Z-4's
  own deferral and this phase's own "no fabricated executable test
  coverage" discipline extended to "no fabricated schema IDs ahead of
  implementation."
- **Per-schema versions**: independent `MAJOR.MINOR.PATCH` per file
  (135Z §42), never a single repository-wide version bump implicitly
  changing every family.
- **Shared-profile version**: `CLTR-CUTOVER-SCHEMAS-001` itself versions
  the canonicalization (§14) and digest (§15) profiles once, at the
  contract level — every `records/*.schema.json` file inherits this via
  its `contract_version` field (§9), never declaring its own separate
  profile version.
- **Compatibility matrix**: deferred (135Z §42 — not pre-populated;
  only one version of each schema exists at freeze/architecture time).
- **Major/minor rules**: MAJOR for breaking changes to required
  fields/identity formulas/enum-value removal; MINOR for additive,
  backward-compatible changes (new optional fields, new enum values only
  where a family's enum is explicitly designed as extensible — none of
  §10's seven shared enums are, per 135Z §3's "closed enum, MAJOR bump
  required" rule for each); PATCH for non-wire-affecting clarifications
  (e.g. a `description` fix).
- **Extension behavior**: the `_extensions` envelope key (§2) is the only
  sanctioned extension point, scoped to evidentiary/historical families
  only.
- **Deprecation**: a deprecated schema-file version remains present and
  readable in `schemas/cltr_cutover/records/` (as a versioned sibling
  file, §33) for at least one full migration epoch after deprecation,
  mirroring CLTR-SCHEMA-001's own compatibility discipline.
- **Historical verification**: a historical companion record remains
  independently digest-verifiable against its own frozen schema version
  without upgrade — the registry (§33) never silently reinterprets an old
  record under a newer schema version.
- **Unsupported-version failure**: `unsupported_version` (135Z §31),
  fail-closed, at both the registry (§33) and the schema `schema_version`
  field level (§9).

**One version bump never implicitly changes every record family** — each
of the sixteen `records/*.schema.json` files versions and evolves
independently, exactly matching 135Z §42's explicit instruction.

---

## 38. Relationship to CLTR-SCHEMA-001

Final architecture disposition per affected family, closing
PREREQUISITE-136A-1 (§6 above provides the full reasoning; this table is
the required per-family summary 135Z §41/this phase's brief requests):

| Family | Disposition |
|---|---|
| AuthorityEpoch, AuthorityState | implemented entirely as companion schema (§17, §18) |
| CutoverRequest, ReadinessEvidencePackage | implemented entirely as companion schema (§19, §20) |
| HumanAuthorization | implemented entirely as companion schema (§21) |
| CutoverCandidate, Certification | implemented entirely as companion schema (§22) |
| CasExpectation | runtime-only embedded component, no CLTR-SCHEMA-001 involvement (§23) |
| PublicationAttempt, PublicationEvidence | implemented entirely as companion schema (§24) |
| ConcurrencyConflict | implemented entirely as companion schema (§25) |
| RecoveryJournalEntry | implemented entirely as companion schema (§26) |
| ReconciliationResult | runtime-only, no persisted schema, no CLTR-SCHEMA-001 involvement (§27) |
| QuarantineRecord | implemented entirely as companion schema (§28) |
| NotificationAuthorityBinding, MarkerAuthorityBinding, FinalizationReceiptAuthorityBinding | implemented as companion schema now; **requires both** — satisfied today via companion schema, with future optional CLTR-SCHEMA-001 v1.1.0 consolidation candidacy explicitly deferred post-implementation (§6, §29) |
| CompatibilityState | implemented entirely as companion schema (§30) |
| HistoricalAuthorityReference | runtime-only, no CLTR-SCHEMA-001 involvement (§31) |

**No family's disposition is left ambiguous.** Thirteen families require
no CLTR-SCHEMA-001 involvement whatsoever; three (the bindings) are
satisfied today as companion schemas with an explicitly optional,
explicitly-sequenced-after-implementation future consolidation path; none
require a CLTR-SCHEMA-001 v1.1.0 revision as a **precondition** of
implementation.

---

## 39. Persistence and namespace architecture

Schema definitions live at `schemas/cltr_cutover/` (§3) — a
version-controlled, source-tree location, structurally separate from
runtime authority state, which lives at `.pcae/cltr-authority/` (135Z
§38.2, unchanged, extended only by §7's new `compatibility-state/`
history path). This mirrors the existing separation already present in
this repository: `schemas/repository_intelligence/` (source-tree
schemas) vs. wherever repository-intelligence runtime artifacts are
generated (a distinct concern, outside this document's scope) — the same
schema/runtime-state separation pattern, applied to Stage 3.

**Runtime namespace** (conceptual restatement of 135Z §38.2, including
this document's §7 addition):

```
.pcae/cltr-authority/
  schemas/                                          (future: pinned/mirrored schema files, empty at freeze time — 135Z's own placeholder)
  epochs/<migration_epoch>/
    epoch-record.json
    requests/<request_id>.json
    readiness/<package_id>.json
    authorizations/<authorization_id>.json
    candidates/<candidate_id>.json
    certifications/<certification_id>.json
    publication-attempts/<attempt_id>.json
    publication-evidence/<evidence_id>.json
    conflicts/<conflict_id>.json
    recovery/journal/<entry_sequence>.json
    recovery/current-recovery-journal
    quarantine/<quarantine_id>.json
    current-authority-state
    authority-state/<state_id>.json
    compatibility/current-compatibility-state
    compatibility/compatibility-state/<compatibility_state_id>.json   (NEW, §7)
  current-authority
```

No path in this tree is created by 136B. **Generated records** (runtime
authority state) are never mixed with **schema definitions** (source
tree) or **generated code** (any future typed-model package, §42) — three
disjoint locations, matching this document's own reuse of the existing
three-way separation already present elsewhere in this repository (source
schemas vs. `.pcae/*` runtime artifacts vs. `src/pcae/*` Python packages).

---

## 40. Pointer architecture

Reconfirming 135Z §37 (unchanged by this document): **exactly one
authority-bearing pointer** — the production `current` pointer
(CLTR-SCHEMA-001 §16, extended per CLTR-CUTOVER-001 to carry
`authority_kind`/`authority_epoch_id`). Every other pointer this
architecture's schemas touch is explicitly classified `operational` or
`derived convenience`, never authority-bearing:

| Pointer | Classification | This architecture's schema relationship |
|---|---|---|
| Production `current` pointer | **authority-bearing (the only one)** | Not a companion-schema file in this document's set — belongs to CLTR-SCHEMA-001's own (currently narrative, not executable-JSON-Schema) wire format, extended per 135W; out of this document's `records/` scope entirely |
| `current-authority-state` | operational | Points into `records/authority_state.schema.json`-shaped files |
| `latest-readiness-package` | derived convenience | Points into `records/readiness_package.schema.json`-shaped files |
| `latest-certification` | derived convenience | Points into `records/certification.schema.json`-shaped files |
| `latest-publication-attempt` | operational | Points into `records/publication_attempt.schema.json`-shaped files |
| `current-recovery-journal` | operational | Points into `records/recovery_journal_entry.schema.json`-shaped files (chain traversal) |
| `latest-reconciliation-result` | derived convenience (optional) | No schema (§27) |
| `current-compatibility-state` | operational | Points into `records/compatibility_state.schema.json`-shaped files |

No pointer this document's schemas support is capable of being
mistaken for the production `current` pointer — none of the sixteen
`records/*.schema.json` files is ever written to, or read from, the
production `current` pointer's own path; that path is entirely outside
`.pcae/cltr-authority/`'s tree (135Z §38.2's own top-level
`current-authority` entry, distinguished by name and location from every
per-epoch operational/convenience pointer nested under `epochs/<epoch>/`).

---

## 41. Implementation grouping

Reconfirming 135Z §43's dependency-derived ten-group sequence, restated
at the file level (this document adds no new grouping — 135Z's ordering
is already dependency-correct, re-verified against §4's inventory and
found consistent: no group below references a schema file only a later
group defines):

1. `shared/*.schema.json` (envelope, enums) — no dependencies.
2. `records/authority_epoch.schema.json`, `records/authority_state.schema.json`
   — closes PREREQ-1; depends only on group 1.
3. `records/cutover_request.schema.json` — depends on groups 1–2.
4. `records/readiness_package.schema.json` — depends on groups 1–3.
5. `records/human_authorization.schema.json` — depends on groups 1, 3–4.
6. `records/cutover_candidate.schema.json`, `records/certification.schema.json`
   (embedding `shared/references.schema.json#/$defs/cas_expectation`) —
   depends on groups 1–5.
7. `records/publication_attempt.schema.json`, `records/publication_evidence.schema.json`
   — depends on groups 1–6.
8. `records/concurrency_conflict.schema.json`, `records/recovery_journal_entry.schema.json`
   — depends on groups 1–7.
9. Reconciliation — no schema file (§27); implemented as a function only,
   depends on groups 1–8 for the records it reads.
10. `records/notification_authority_binding.schema.json`,
    `records/marker_authority_binding.schema.json`,
    `records/receipt_authority_binding.schema.json` — depends on groups
    1–2 (references `AuthorityState`) and existing PFN-001 identities.
11. `records/compatibility_state.schema.json` — depends on group 1
    (references `MigrationStage`, `AuthorityRole` enums) only; not
    downstream of groups 2–10 in any field-level sense, though 135Z lists
    it last for narrative reasons (compatibility is the *residual* role
    after cutover). `records/quarantine_record.schema.json` — depends on
    groups 2–8 (references every quarantinable family, §28).

**Each group requires an independent verification phase before the next
group begins** (135Z §43, restated as binding). This document does not
over-fragment beyond 135Z's own ten/eleven-group structure — no
sub-splitting is introduced, since 135Z's grouping is already the
dependency-minimal partition (re-verified above by explicit
forward-reference-absence check).

---

## 42. Typed-model dependency

Per the phase brief's proposed safe rule, adopted here as this
document's binding decision: **shared enum and identity typed models
(`shared/enums.schema.json`, `shared/identity.schema.json`,
`shared/envelope.schema.json`'s `$defs`) may begin only after
implementation group 1 (§41) is independently verified. Record-specific
typed models begin only after their executable schemas are frozen and
verified** (their own implementation group, per §41, plus that group's
independent verification).

**Model package location**: `src/pcae/cltr/authority/` (135Z §44),
sibling to `src/pcae/cltr/` — confirmed by direct inspection that
`src/pcae/cltr/` today contains `canonicalization.py`, `digest.py`,
`enums.py`, `identity.py` at its top level with `migration/`,
`shadow/`(implicit), `prototype/`(implicit) as subpackages; a new
`authority/` subpackage follows the same sibling pattern
`src/pcae/cltr/migration/` already establishes, not nested inside
`migration/` (Stage 3 authority is not a refinement of Stage 1/2
migration mechanics — it is CLTR-CUTOVER-001's own distinct concern).

**No runtime authority behavior may appear merely from model creation** —
restated as an absolute constraint: constructing a `CutoverRequest`
dataclass instance, even a fully valid one, must never itself write a
file, call the resolver, or have any effect beyond producing an
in-memory, schema-conformant value (135Z §44's "no-side-effect
construction," reused unchanged).

---

## 43. Validation layering

Six layers, the architecture's central organizing principle, restated
here as the canonical reference (this section is cited by nearly every
section above rather than re-derived per-section):

```
Layer 1 — JSON parsing and duplicate-key rejection
          (existing parser-level behavior, CLTR-SCHEMA-001 §14, reused unchanged)
Layer 2 — executable schema validation
          (THIS DOCUMENT'S ENTIRE SCOPE — §2–§36 define Layer 2 only)
Layer 3 — canonicalization and digest verification
          (pcae.cltr.canonicalization / pcae.cltr.digest, reused unchanged, §14–§15)
Layer 4 — cross-record semantic validation
          (future, not implemented — §32's fifteen-invariant table, §12's
           identity-recomputation boundary, §18's pointer-then-state ordering)
Layer 5 — live-state/CAS validation
          (future, not implemented — §23's CAS live-comparison, §14 of CLTR-CUTOVER-001)
Layer 6 — authority resolver and operational gates
          (future, not implemented — CLTR-CUTOVER-001 §4, §10; entirely outside
           this document's and 135Z's schema scope)
```

**No schema this document defines claims to perform a later-layer
responsibility** — every section above that touches a Layer 3–6 concern
(digest recomputation, identity recomputation, staleness comparison,
CAS live-comparison, replay detection, authority resolution) explicitly
states the boundary rather than silently assuming JSON Schema covers it.
This is the single most load-bearing architectural decision in this
document: **Layer 2 is necessary but never sufficient**, and every
future implementation phase inherits this same boundary discipline.

---

## 44. Test architecture

Planned (no test implemented in 136B), organized by the same six-layer
model (§43):

- **Schema loading** (§33): registry construction succeeds for the
  frozen sixteen-file set; fails closed on a duplicate `schema_id`; fails
  closed on an unresolvable relative `$ref`.
- **Reference resolution**: every `$ref` in every `records/*.schema.json`
  file resolves within `schemas/cltr_cutover/`, none resolves externally
  (offline-only, §33) — a static analysis test over the file set itself,
  runnable without any runtime code.
- **Valid/invalid fixtures**: per §34's twelve fixture categories, one
  test per fixture per family (16 families × up to 12 categories,
  pruned per family to only the categories that actually apply — e.g.
  `additionalProperties` fixtures do not apply to families with an
  `_extensions` carve-out in the same way).
- **Enum strictness**: every one of the seven shared enums (§10) plus
  every record-local enum rejects an out-of-vocabulary value.
- **Unknown fields**: the eight authority-bearing families (§2) reject an
  extra unknown property; the five evidentiary families accept one only
  under `_extensions`.
- **Absent/null**: `CutoverRequest`'s narrow exception (§9) is exercised
  positively; every other family's stricter absent/null distinction is
  exercised negatively (asserting the narrow exception does *not*
  generalize).
- **Version compatibility**: an `unsupported_version` fixture per family
  is rejected; a same-major newer-minor fixture with only additive
  optional fields (evidentiary families) is accepted; the equivalent for
  an authority-bearing family is rejected (§2's asymmetric
  unknown-optional-field policy).
- **Digest/identity shape**: every `sha256_hex`-typed field rejects
  malformed shape (§34 items 10, per family).
- **Local conditionals**: every `if`/`then` block (§2) has both a
  triggering and a non-triggering fixture.
- **Semantic-validator separation**: a schema-valid-but-semantically-wrong
  fixture (e.g. a `CutoverRequest` whose `request_digest` does not
  actually match its own content) passes Layer 2 and is deliberately used
  as a Layer 3/4 test's *input*, proving the layers are genuinely
  separable rather than accidentally coupled.
- **Offline operation**: no test in this suite ever performs network I/O
  — a CI-level assertion (e.g. a network-call-forbidding test harness
  fixture), not a schema keyword.
- **Deterministic schema registry**: the same directory scan run twice
  produces byte-identical registry contents.
- **Security strings**: §34 item 11's traversal/absolute-path fixtures.
- **Secret handling**: §34 item 12's token-shaped-string fixtures, run as
  a documentation/review check, not an automated schema-layer rejection
  (§35's explicit statement that JSON Schema cannot detect secret
  *content*).

**Adversarial fixtures used in independent verification phases are
fresh** — this document does not pre-author them; §41's per-group
independent verification is where fresh adversarial fixtures are
constructed against each group's frozen schemas, not reused from this
architecture phase's own (non-existent, since none are implemented here)
fixture set.

---

## 45. Traceability matrix

Per-requirement traceability (requirement → schema/validator
responsibility → implementation group → verification group → milestone),
using the twelve representative CSCH-REQ entries 135Z §45 itself
publishes (the only entries currently available; the full 62-item matrix
remains F-135Z-3's unresolved scope, §5 above):

| Req ID | Requirement (135Z §45) | This architecture's responsibility | Implementation group (§41) | Verification group | Milestone blocked if unmet |
|---|---|---|---|---|---|
| CSCH-REQ-1 | AuthorityKind exact-match only | Layer 6 (resolver code, outside schema scope); schema enforces closed `enum` (§10) as a necessary precondition | Group 1 | Group 1 verification | Any resolver implementation |
| CSCH-REQ-2 | AuthorityEpoch deterministic identity | Layer 3 (`pcae.cltr.digest`, reused, §15); schema enforces `sha256_hex` shape (§17) as a necessary precondition | Group 2 | Group 2 verification | Any `AuthorityEpoch` persistence |
| CSCH-REQ-3 | AuthorityState never read as primary authority source | Layer 6 (resolver code); schema's `is_authoritative: const false` (§18) is the necessary schema-level precondition | Group 2 | Group 2 verification | Any resolver implementation |
| CSCH-REQ-4 | CutoverRequest deterministic identity + replay rejection | Layer 3 (identity) + Layer 4 (replay, stateful); schema enforces shape (§19) | Group 3 | Group 3 verification | Any `CutoverRequest` persistence |
| CSCH-REQ-5 | HumanAuthorization expiry/revocation/one-time-use/replay | Layer 4 (stateful comparisons); schema enforces `risk_acknowledgement: const true`, `scope: const`, field shape (§21) | Group 5 | Group 5 verification | Any authorization-consuming code |
| CSCH-REQ-6 | CasExpectation no wildcard on missing value | **Layer 2, this document's direct responsibility** — `required` array on all-but-one field (§23) | Group 6 | Group 6 verification | Any CAS implementation |
| CSCH-REQ-7 | PublicationEvidence uncertainty never collapsed | **Layer 2** — exact seven-value `enum`, no merged states (§24) | Group 7 | Group 7 verification | Any publication implementation |
| CSCH-REQ-8 | RecoveryJournalEntry hash-chain tamper detection | Layer 4 (chain traversal); schema enforces nullable-digest shape (§26) | Group 8 | Group 8 verification | Any recovery-journal implementation |
| CSCH-REQ-9 | ReconciliationResult read-only, `mutation: none` | No schema (§27); a future function-level test, not a schema test | Group 9 | Group 9 verification | Any reconciliation implementation |
| CSCH-REQ-10 | Integrity-failure case never reactivates legacy | Layer 6 (behavioral); schema supports representing the state (§28) but cannot itself enforce the behavioral guarantee | Group 8 (quarantine) | Group 8 verification, closes PREREQUISITE-135Z-1's detection half | Any quarantine implementation |
| CSCH-REQ-11 | CompatibilityState structurally cannot reactivate legacy | **Layer 2** — field omission, verifiable by static schema review (§30) | Group 11 | Group 11 verification | Any compatibility-state implementation |
| CSCH-REQ-12 | Exactly one authority-bearing pointer | Layer 6 (static review of every pointer read site); this document's pointer inventory (§40) is the necessary map such a review would use | Cross-cutting | Cross-cutting, all groups | Any implementation touching any pointer |

**Every requirement above traces to an explicit responsibility layer,
never left unassigned.** The full 62-item matrix, once published per
§5's disposition, must extend this same table format — this table is the
template, not a substitute.

---

## 46. Acceptance criteria

136B architecture is complete only if all of the following hold — each
cross-referenced to the section establishing it:

1. Exact executable-schema inventory frozen conceptually — §4.
2. Record groups dependency-correct — §41 (re-verified, no forward
   reference found).
3. Schema dialect selected — §2 (draft 2020-12, justified).
4. Packaging defined — §3.
5. Shared components bounded — §8 (no oversized universal envelope, §9).
6. Enum architecture complete — §10 (all seven shared plus all
   record-local enums from 136A's confirmed set).
7. Identity/reference boundaries clear — §12, §13 (shape vs. semantic
   recomputation explicitly separated).
8. Canonicalization/digest responsibilities clear — §14, §15.
9. Semantic-validator boundary clear — §32, §43 (six-layer model).
10. AuthorityState pointer relationship unambiguous — §18 (exact
    ordering restated, no schema-layer overreach claimed).
11. Request/authorization/candidate/certification ordering has no
    cycles — §19 (asymmetric-reference proof given).
12. CAS has no wildcard semantics — §23 (structural `required`-array
    enforcement).
13. CompatibilityState history defined — §7, §30 (PREREQUISITE-136A-2
    resolved).
14. CLTR-SCHEMA relationship explicit — §6, §38 (PREREQUISITE-136A-1
    resolved).
15. F-135Z-3 disposition explicit — §5 (bound to 136C, not resolved
    here, not silently closed).
16. Both 136A prerequisites scheduled or architecturally resolved — §6,
    §7 (both resolved by this document).
17. No unresolved Blocking ambiguity remains — §47 below confirms.

**All seventeen criteria are met by this document.**

---

## 47. No-go criteria

None of the following holds (checked explicitly, matching 135Z §47's own
self-check discipline):

- Schema inventory ambiguous — **resolved**, §4 (exact 16/1/1/1/1
  reconciliation).
- Authority-state relationships ambiguous — **resolved**, §18.
- Circular record dependencies remain — **resolved**, §19, §41 (checked,
  none found).
- A schema can claim authority improperly — **resolved**, §8, §11 (every
  companion schema structurally forces `is_authoritative: false`).
- More than one authority-bearing pointer possible — **resolved**, §40
  (exactly one, reconfirmed).
- Typed authority enums remain free-form — **resolved**, §10 (all seven
  closed enums, no catch-all).
- CAS permits missing expected values — **resolved**, §23 (exact-match
  `required` array).
- Uncertainty collapses into failure — **resolved**, §24
  (`publication_uncertain` structurally distinct).
- CompatibilityState lacks immutable history — **resolved**, §7, §30.
- Authorization replay rules incomplete — **resolved**, §21 (schema
  supports every field 135Z §8.3's replay/expiry/revocation/one-time-use
  rules need; full enforcement is Layer 4, explicitly scoped, not
  "incomplete" but correctly layered).
- CLTR-SCHEMA relationship unresolved — **resolved**, §6, §38.
- Unknown-field behavior unsafe — **resolved**, §2, §9 (fail-closed for
  authority-bearing families).
- Semantic validation responsibilities falsely assigned to JSON Schema —
  **resolved**, §43 (six-layer model explicit throughout; every section
  states its layer boundary rather than overclaiming).
- F-135Z-3 silently closed without full evidence — **resolved (in the
  negative sense required)**: **not** silently closed; explicitly carried
  forward to 136C, §5.

**No no-go condition holds. Implementation is not prohibited on
architectural grounds — but implementation itself is not authorized by
this document (§48).**

---

## 48. Architecture verdict

**EXECUTABLE SCHEMA ARCHITECTURE COMPLETE WITH PREREQUISITES — READY FOR
CONTRACT FREEZE**

Rationale for "with prerequisites" rather than unqualified "complete":
F-135Z-3 (the 62-item verification matrix) remains open, explicitly bound
to 136C (§5) rather than resolved here; F-135Z-2 (notification/marker/
receipt bindings remaining companion records rather than folded into
CLTR-SCHEMA-001, NON-BLOCKING per 135Z) and F-135Z-4 (schema IDs not yet
minted beyond the one illustrative example, DEFERRED per 135Z) both
remain open and are carried forward unchanged, neither requiring
resolution at the architecture stage. F-135Z-1 and F-135Z-5
(PREREQUISITE, per 135Z) remain scheduled for their originally-assigned
milestones (§28, §41 respectively) and are not accelerated or resolved
by this document.

**Architecture completion does not authorize implementation.** The next
governed step is **136C — Stage 3 Companion Executable Schema Contract
Freeze**, at which the full 62-item verification matrix must be published
verbatim (§5), and only after which any executable-schema implementation
group (§41) may begin.

---

## Findings

Classified per the phase brief's five-way taxonomy (CONFIRMED,
NON-BLOCKING, BLOCKING, PREREQUISITE, DEFERRED):

| ID | Title | Verdict | Source | Affected schema group | Authority impact | Concurrency impact | Recovery impact | Exactly-once impact | Implementation milestone | Verification milestone | Latest acceptable resolution point |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F-136B-1 | F-135Z-3's full 62-item verification matrix remains unpublished; this document only extends 135Z's own twelve representative entries (§45) rather than the complete set | DEFERRED (carrying forward 135Z's own DEFERRED classification, now bound to a named phase) | §5, §45 | All sixteen `records/*.schema.json` files | None (documentation completeness) | None | None | None | All implementation groups (§41) | All verification groups | **136C**, mandatory before any implementation group begins |
| F-136B-2 | PREREQUISITE-136A-1 (schema vehicle ambiguity) resolved by this document's §6, but 135W's own PREREQ-4 register text still lacks the retroactive clarifying note 136A recommended | NON-BLOCKING | §6 | None (documentation cross-reference only) | None | None | None | None | None | None | Any future phase touching 135W's register, non-blocking otherwise |
| F-136B-3 | The 136A phase-report reconciliation conflict (marker/checkpoint digest predating 136A's own later corrective commits) remains unrepaired, since 136A must not be mutated or redispatched | NON-BLOCKING (inherited, disclosed, not created by this phase) | §0.1 | None (136A's own finalization bookkeeping, not a 136B schema concern) | None | None | None | Low (no duplicate delivery occurred; single receipt, single promoted generation) | None | None | A future phase explicitly scoped to phase-report finalization bookkeeping repair, if ever undertaken |
| F-136B-4 | Sixteen companion `schema_id` values remain unminted beyond 135Z's one illustrative example, carried forward unchanged from F-135Z-4 | DEFERRED (inherited from 135Z, unchanged) | §37 | All sixteen `records/*.schema.json` files | None | None | None | None | Implementation group 1 (§41) | Group 1 verification | Before any schema file is actually written |
| F-136B-5 | CAS expectation embedding-vs-reference choice remains unexercised against a real concurrent-writer test, carried forward unchanged from F-135Z-5 | PREREQUISITE (inherited from 135Z, unchanged) | §23 | `shared/references.schema.json#/$defs/cas_expectation` | Medium | High | Medium | None | Implementation groups 6/7 (§41) | Groups 6/7 verification with concurrency test | Before Stage 3 prerequisite CAS implementation is considered complete |

No **CONFIRMED** or **BLOCKING** finding is identified anywhere in this
phase's architecture work. F-136B-1 and F-136B-4/F-136B-5 are direct,
unchanged carry-forwards of 135Z's own DEFERRED/PREREQUISITE findings,
now bound to specific future milestones (136C, implementation groups)
rather than left open-ended. F-136B-2 and F-136B-3 are new,
documentation-only observations from this phase's own inspection, both
NON-BLOCKING.

---

## No-implementation proof

- No production source changed. No test source changed. No executable
  schema was added or modified (`schemas/repository_intelligence/**`
  confirmed byte-unchanged; `schemas/cltr_cutover/` does not exist on
  disk — this document describes it, it does not create it). No Stage 3
  typed model or validator was implemented. No authority resolver,
  authority state, or authority pointer was implemented or changed. No
  cutover request, readiness package, authorization, candidate,
  certification, publication attempt, conflict record, or recovery
  journal was created. No authority epoch changed. No CLTR authority was
  created. No legacy authority was demoted. No legacy authority was
  retired. No production behavior changed. No execution capability was
  introduced.
- Legacy lifecycle remains the sole production authority. CLTR remains
  derivative. CLTR-CUTOVER-001 and CLTR-CUTOVER-SCHEMAS-001 remain
  future-behavior and future-data contracts only. 136B produced
  executable-schema architecture only.
- Runtime remains Observed, maximum capability remains observe, and
  execution availability remains unavailable (confirmed by `pcae runtime
  inspect`, re-run during this phase's initial inspection).

---

## Required validation (re-run during this phase)

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: clean. `pcae push check`: nothing to
push (prior to this phase's own commits). `pcae runtime inspect`: Observed
/ observe / execution unavailable, confirmed unchanged. `pcae notify
status`: Telegram configured/enabled/ready (environment sourced via
`~/.config/pcae/telegram.env`, no secret persisted in this document or in
any governance artifact it touches). `pcae phase-report reconcile
--phase-id 136A`: read-only, `mutation: none`, result `conflict`
(disclosed and dispositioned, §0.1) — not redispatched, not mutated.

---

## Recommended next phase

**136C — Stage 3 Companion Executable Schema Contract Freeze**

136C's required scope, derived directly from this document's own
disposition decisions: publish the full 62-item CSCH-REQ verification
matrix verbatim as a cross-referenced appendix (§5, F-136B-1), closing
F-135Z-3; freeze this document's architecture into binding contract text
(the distinction between "architecture," which may still be revised
before freeze, and "frozen contract," which requires the same
governed-amendment discipline every other Track 135 contract uses); mint
the fifteen remaining companion `schema_id` values (F-136B-4); and
produce the compatibility matrix template 135Z §42 defers. **Executable
schema implementation and typed-model implementation must not begin
before 136C completes** — this document's own architecture-only status
does not authorize implementation, and 136C's contract freeze, once it
exists, still requires its own independent verification (a future
136D) before any implementation group (§41) is permitted to start.
