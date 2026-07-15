# Phase 136C: Stage 3 Companion Executable Schema Contract Freeze

## Status

**EXECUTABLE SCHEMA CONTRACT FROZEN WITH PREREQUISITES — READY FOR INDEPENDENT VERIFICATION**

Contract identifier: **CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0**

This document is contract-only. It freezes normative requirements. It does not
add an executable JSON schema, a Python typed model, a schema loader, a schema
validator, a semantic validator, a fixture, a schema registry, an authority
resolver, authority-state persistence, an authority pointer, or any cutover
behavior. It does not change production behavior. It does not activate Stage
3. It does not change production authority. It does not demote or retire
legacy authority. It does not introduce execution.

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. CLTR-CUTOVER-001, CLTR-CUTOVER-SCHEMAS-001, and
CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 define future behavior and future data
contracts only.

Runtime remains **Observed**, maximum capability remains **observe**,
execution availability remains **unavailable**.

---

## 0. Relationship to governing contracts and inherited state

### 0.0 Contract identity

| Field | Value |
|---|---|
| Contract identifier | `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001` |
| Version | `v1.0` |
| Status | FROZEN (this document) |
| Freezing phase | 136C |
| Predecessor contract | `CLTR-CUTOVER-SCHEMAS-001 v1.0` (Phase 135Z) |
| Predecessor architecture | Phase 136B, `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_ARCHITECTURE.md` |
| Grandparent contract | `CLTR-CUTOVER-001 v1.0` (Phase 135W) |
| Wire-format contract | `CLTR-SCHEMA-001 v1.0.1` (unmodified by this phase) |
| Next phase | 136D — Stage 3 Companion Executable Schema Contract Independent Verification |

### 0.1 Normative vocabulary

This document uses **must** / **must not** / **shall** / **shall not** for
binding requirements, **should** / **should not** for strong recommendations
that a future implementation phase may deviate from only with an explicit,
disclosed finding, and **may** for explicitly permitted discretion. Every
requirement in the §51 matrix is **must**-level unless its text says
otherwise.

### 0.2 Scope

This contract governs exactly one thing: the binding, exact, machine-checkable
shape of the executable JSON Schema package for Stage 3 companion records
(`schemas/cltr_cutover/`). It governs schema file layout, dialect, identifiers,
inventory, shared definitions, enums, envelopes, identity/reference/digest/
timestamp shapes, unknown-field behavior, canonicalization and digest
boundaries, conditional/state-specific validation, per-family schema
contracts, fixture obligations (not fixture content), registry behavior
(not registry implementation), the semantic-validation boundary, security and
secret-handling requirements at the schema layer, the relationship to
`CLTR-SCHEMA-001`, implementation grouping, and the independent-verification
matrix for Phase 136D.

This contract does not govern: authority resolution logic, authority-state
persistence, pointer publication, CAS enforcement at the storage layer,
notification dispatch, cross-record semantic invariants beyond what a single
JSON Schema document can express locally, or any runtime behavior. Those
remain governed by `CLTR-CUTOVER-001 v1.0` and by future implementation-phase
contracts.

### 0.3 Relationship to CLTR-CUTOVER-SCHEMAS-001 v1.0

`CLTR-CUTOVER-SCHEMAS-001 v1.0` (135Z) froze the **conceptual** record-family
inventory (20 families), the **typed authority enums** (7 families), and the
cross-record invariant catalog (`CSCH-INV-1`..`CSCH-INV-15`). It is a
data-model contract, not an executable-artifact contract: it does not commit
to filenames, `$id` values, dialect, or file-level `$defs` layout.

`CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0` (this document) is strictly
additive to `CLTR-CUTOVER-SCHEMAS-001 v1.0`. It does not redefine any of the
20 families, does not redefine any typed enum's membership, and does not
renumber any `CSCH-INV` invariant. It translates that conceptual model into an
exact executable-artifact inventory (§4), exact shared `$defs` (§6), and an
exact 62-item independently-derived verification matrix (§51) that resolves
finding **F-135Z-3**.

### 0.4 Relationship to CLTR-SCHEMA-001 v1.0.1

`CLTR-SCHEMA-001 v1.0.1` is the existing, unmodified, production wire contract
for the legacy/CLTR lifecycle record (`lifecycle_state`, `transition_type`,
the five-code `authority_role` field, the 15 `RepresentationKind` bindings,
the 37-invariant catalog, digest/persistence rules, `authority_mode`
diagnostic enum). This contract does not amend it. §45 freezes, per family,
whether a family is a companion schema today with `CLTR-SCHEMA-001 v1.1.0` as
an optional future consolidation vehicle, never a prerequisite. This document
makes **zero changes** to `docs/CLTR-SCHEMA-001*` or to any file under
`schemas/` — both are outside this task's allowed-file set.

### 0.5 Inherited state confirmed at phase start

At the start of 136C, the following was independently reconfirmed via the
mandatory initial inspection (commands and raw output retained in the 136C
canonical report, not duplicated here):

- Exactly one canonical Phase 136B completion exists: commit `96d4cad0`
  (architecture document), finalized by commit `95759139` (task close /
  idle placeholder). `git rev-list --count origin/main..HEAD` = 0 before this
  phase's work began.
- `pcae health`, `pcae check`, `pcae status coherence`, and
  `pcae doctor task-memory` all passed cleanly before this phase's work began.
- `pcae runtime inspect` confirmed: Runtime state `Observed`, Execution
  capability `unavailable`, Maximum plugin capability `observe`, Registry
  status `empty`, Plugin count `0`.
- No file exists under `schemas/cltr_cutover/`. No schema loader, schema
  registry, or schema validator module exists anywhere in `src/pcae/`. No
  `authority_resolver` / `AuthorityResolver` / `resolve_authority` symbol
  exists anywhere in `src/`. No `AuthorityKind`, `PublicationState`,
  `CompatibilityMode`, or `GenerationRole` Python enum exists anywhere in
  `src/` — these remain contract text only (135Z §3), not code.
- No Stage 3 authority-state namespace, pointer, or persistence exists under
  `.pcae/`.
- No authority epoch has changed. Production authority remains `legacy`
  (`ProductionAuthority.LEGACY`, `src/pcae/cltr/migration/enums.py`).

### 0.6 Disposition of the 136A reconciliation conflict

`pcae phase-report reconcile --phase-id 136A` (read-only) reproduced the same
disclosed conflict reported by 136B: `reconciliation_status: conflict`,
`promoted_generation_count: 1`, `marker_state: not_dispatched`,
`checkpoint_state: completed`, `receipt_state: finalized`, blocker
"checkpoint identity conflicts with the promoted report." This is carried
forward as **historical lifecycle evidence only**. It is not repaired, not
redispatched, and not used as Stage 3 readiness evidence of any kind by this
contract. There was exactly one promoted 136A generation and exactly one
delivery receipt; no duplicate delivery occurred. This phase performs no
136A mutation and no 136A redispatch.

`pcae phase-report reconcile --phase-id 136B` (read-only) confirmed a clean,
non-conflicting state: `Status: reconciled`, `Marker: already_dispatched`,
`Checkpoint: completed`, `Receipt: finalized`, `Mutation: none`.

### 0.7 Prerequisites this contract resolves

This contract resolves nothing new that 136B did not already resolve at the
architecture level (`PREREQUISITE-136A-1` and `PREREQUISITE-136A-2` were
resolved by 136B, not by this document). This contract's own job is to
**freeze** those resolutions as binding requirements (§45, §46) and to
**close F-135Z-3** by publishing the full matrix (§51). Whether F-135Z-3 is
actually closed, or must instead be carried forward with an honestly disclosed
discrepancy, is decided in §51, not asserted here.

---

## 1. Purpose contract

The executable JSON Schema package for `schemas/cltr_cutover/` validates
**local wire shape** of Stage 3 companion records. Nothing more.

It **may** validate:

- object structure (required/optional/forbidden keys per state);
- primitive types (string, integer, boolean, array, object, null);
- exact enum membership (closed vocabularies, no aliasing);
- local conditional fields (`if`/`then`/`else` keyed on a sibling field
  within the same document);
- identifier shape (regex-constrained strings);
- digest shape (regex-constrained strings, §14);
- timestamp shape (RFC 3339 / ISO 8601 UTC, §16);
- reference shape (id+digest+family tuples, §13);
- schema/version declarations (`schema_id`, `schema_version`,
  `contract_version` presence and shape);
- allowed/forbidden field sets per record state (§16, §45).

It **must not** claim to validate, and no executable schema in this package
may assert or imply that it validates:

- deterministic identity recomputation (a JSON Schema cannot recompute a
  digest of a canonical serialization; it only checks that a string *looks
  like* a digest);
- digest recomputation against the actual canonical bytes of the record;
- authorization freshness (time-based expiry against wall-clock "now");
- evidence freshness (staleness relative to a live authority state);
- cross-record consistency (a schema validates one document at a time; it
  cannot compare two records);
- current authority (whether a given record's `authority_role` is *actually*
  the live authoritative one right now);
- CAS (compare-and-swap) against live filesystem or pointer state;
- publication success (whether a publication attempt actually landed);
- recovery truth (whether a recovery journal entry reflects what actually
  happened operationally);
- notification exactly-once behavior (PFN-001 remains the sole authority for
  that guarantee);
- lifecycle authority of any kind.

Those responsibilities belong to Layers 3–6 of the validation-layering
contract (§43) and to future semantic validators (§40), never to Layer 2
(executable schema validation, this contract's entire scope).

---

## 2. JSON Schema dialect contract

**Dialect: JSON Schema Draft 2020-12.**

```
"$schema": "https://json-schema.org/draft/2020-12/schema"
```

This is the only dialect used anywhere in this repository's existing
executable-schema precedent (`schemas/repository_intelligence/**`, all 20
files, confirmed by direct inspection). This contract adopts the identical
dialect for `schemas/cltr_cutover/` with no exception and no per-family
override.

Frozen dialect-usage rules:

| Feature | Rule |
|---|---|
| `$schema` | Every schema file **must** declare the draft 2020-12 URI, verbatim, at the document root. |
| `$id` | Every schema file **must** declare a stable, non-network-resolved identifier of the form `https://pcae.local/schemas/cltr_cutover/<relative-path>.schema.json`. This is an opaque label, never fetched over the network. |
| `$defs` | Local, single-file shapes live in that file's own `$defs`. Cross-file-shared shapes live only in `schemas/cltr_cutover/shared/*.schema.json` and are referenced, never duplicated. |
| `$ref` | Only relative-path, same-repository references are permitted (e.g. `"../shared/enums.schema.json#/$defs/authority_kind"`). Absolute URL `$ref` resolution and any network fetch are forbidden. |
| `additionalProperties` | Frozen per the two-tier policy in §45.0 (strict `false` for authority-bearing families; a single reserved `_extensions` key for evidentiary families). Bare `additionalProperties: true` is forbidden everywhere in this package. |
| `unevaluatedProperties` | **Not used.** This package does not compose schemas via `allOf` in a way that would require `unevaluatedProperties`; conditional composition uses `if`/`then`/`else` and `oneOf` with a `const` discriminator instead. |
| `if`/`then`/`else` | The frozen mechanism for local conditional/state-dependent field requirements (§16). |
| `oneOf` | The frozen mechanism for tagged unions keyed on a `const` discriminator field (e.g. `authority_kind: "legacy"` vs `authority_kind: "cltr"` branches). |
| `allOf` | Permitted only to compose a record's own `$defs` with the shared envelope `$def`; never used to merge two independently-`additionalProperties`-constrained subschemas (that pattern is banned precisely because it silently invites `unevaluatedProperties` complexity this contract declines to adopt). |
| `format` | `format` keywords (e.g. `date-time`) are advisory only per the JSON Schema spec; this package **must not** rely on `format` alone for structural rejection — every shape-critical field (digest, identifier, timestamp) **must** also carry an explicit `pattern` regex (§12, §14, §16). |
| Regex profile | ECMA 262 regex subset only (the profile JSON Schema draft 2020-12 assumes); no lookbehind, no backreference, anchored with `^`/`$`. |
| Reference resolution | Fully offline. No schema in this package resolves any reference over the network at validation time. A future schema registry (§41) resolves all `$ref` targets from the local filesystem only. |
| Duplicate-key handling | Layer 1 (JSON parsing, existing, `CLTR-SCHEMA-001` §14) rejects duplicate object keys **before** the document reaches Layer 2 (JSON Schema validation). JSON Schema validation in this package assumes a document already free of duplicate keys; it is not itself a duplicate-key detector, and no schema in this package attempts to re-implement that check. |

---

## 3. Schema package contract

Frozen package root: **`schemas/cltr_cutover/`**.

Frozen directory structure (all four directories below are **required** at
implementation time; none is optional):

```
schemas/cltr_cutover/
  README.md
  shared/
    envelope.schema.json
    enums.schema.json
    identity.schema.json
    digest.schema.json
    references.schema.json
    failures.schema.json
    limitations.schema.json
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
  bindings/
    (reserved — see §3.1; empty until a binding-only artifact is needed
    that is not itself a `records/` family; currently the three binding
    families in `records/` fully cover this need, so `bindings/` holds no
    files at freeze time and is not required to be created before it is
    needed)
  views/
    (reserved — derived, non-persisted, non-authoritative documentation
    only; see §36; holds no executable schema file at freeze time)
```

### 3.1 Directory-purpose contract

- **`shared/`** — reusable `$defs` only. No file under `shared/` is itself a
  complete, standalone, instantiable record schema. Every file under
  `shared/` is referenced via `$ref` from `records/`.
- **`records/`** — one file per required companion schema (§4). Every file
  under `records/` is a complete, standalone, instantiable JSON Schema for
  exactly one record family.
- **`bindings/`** — reserved for any future binding-only artifact that is
  neither a full record nor a pure `shared/` `$def`. Not populated by this
  contract; its presence in the frozen layout exists so that a future
  binding family never has to be shoehorned into `records/` or `shared/`.
- **`views/`** — reserved for optional, non-authoritative, non-persisted
  documentation of derived-view shapes (§36). A file may appear here only
  as illustrative documentation of a computed shape; a `views/` file
  **must never** be treated as an instantiable persisted-record schema and
  **must never** be `$ref`-included by anything under `records/`.

### 3.2 No-runtime-record rule

**No runtime record of any kind may be stored under `schemas/cltr_cutover/`.**
This tree contains schema *definitions* only. Actual persisted Stage 3
companion records (once implemented) live under a distinct runtime namespace
(`.pcae/cltr-authority/...`, per 136B §39/§40 and this contract's §45 per-family
persistence notes), never under `schemas/`.

---

## 4. Exact executable-schema inventory

This is the exact, final, frozen inventory. It restates and freezes 136B §4's
reconciliation of 135Z's 20 conceptual families into executable artifacts. No
approximate language is used below.

| # | Record family (135Z name) | 135Z classification | Executable disposition | Artifact |
|---|---|---|---|---|
| 1 | Authority Epoch Record | required companion schema | standalone schema | `records/authority_epoch.schema.json` |
| 2 | Authority State Record | required companion schema | standalone schema | `records/authority_state.schema.json` |
| 3 | Cutover Request Record | required companion schema | standalone schema | `records/cutover_request.schema.json` |
| 4 | Readiness Evidence Package | required companion schema | standalone schema | `records/readiness_package.schema.json` |
| 5 | Human Authorization Record | required companion schema | standalone schema | `records/human_authorization.schema.json` |
| 6 | Cutover Candidate Record | required companion schema | standalone schema | `records/cutover_candidate.schema.json` |
| 7 | Certification Record | required companion schema | standalone schema | `records/certification.schema.json` |
| 8 | Authority Publication Attempt Record | required companion schema | standalone schema | `records/publication_attempt.schema.json` |
| 9 | Authority Publication Evidence Record | required companion schema | standalone schema | `records/publication_evidence.schema.json` |
| 10 | Compare-and-Swap Expectation Record | embedded schema component | embedded `$def`, no standalone file | `shared/references.schema.json#/$defs/cas_expectation` (`$ref`-included at exactly two sites: `cutover_candidate.schema.json`, `publication_attempt.schema.json`) |
| 11 | Concurrency Conflict Record | required companion schema | standalone schema | `records/concurrency_conflict.schema.json` |
| 12 | Recovery Journal Record | required companion schema (entry only) | standalone schema (single-entry shape; the journal itself is an append-only sequence of these entries, not a schema-defined aggregate) | `records/recovery_journal_entry.schema.json` |
| 13 | Reconciliation Result Record | derived view | not a `records/` file; no persisted schema; documented only, optionally under `views/` | none |
| 14 | Quarantine Record | required companion schema | standalone schema | `records/quarantine_record.schema.json` |
| 15 | Authority Transition Receipt | not required | absorbed into rows 2 and 9 plus the receipt binding (row 18); no file | none |
| 16 | Notification Authority Binding | existing-schema extension | standalone binding schema | `records/notification_authority_binding.schema.json` |
| 17 | Marker Authority Binding | existing-schema extension | standalone binding schema | `records/marker_authority_binding.schema.json` |
| 18 | Finalization Receipt Authority Binding | existing-schema extension | standalone binding schema | `records/receipt_authority_binding.schema.json` |
| 19 | Compatibility State Record | required companion schema | standalone schema | `records/compatibility_state.schema.json` |
| 20 | Historical Authority Reference | runtime-only typed model | no schema file; typed-model-only (§37) | none |

### 4.1 Exact counts (frozen, not approximate)

- **Standalone schema files: 16** (rows 1–9, 11–12, 14, 16, 17, 18, 19).
- **Shared `$defs` files: 7** (`envelope.schema.json`, `enums.schema.json`,
  `identity.schema.json`, `digest.schema.json`, `references.schema.json`,
  `failures.schema.json`, `limitations.schema.json`).
- **Embedded schema components: 1** (row 10, `cas_expectation`, defined once
  in `shared/references.schema.json` and `$ref`-included at exactly 2 sites).
- **Binding schemas: 3**, all counted within the 16 standalone files above
  (rows 16, 17, 18) — there is no separate "bindings schema" count distinct
  from the standalone-file count; these three files simply live under
  `records/`, not `bindings/`, at freeze time.
- **Derived-view schemas: 0** (row 13 is documented, not schema-defined; the
  `views/` directory holds no executable schema file at freeze time).
- **Runtime-only typed models: 1** (row 20, no schema file).
- **Not-required families: 1** (row 15, no schema file).
- **Total files under `schemas/cltr_cutover/` at full implementation: 16
  (`records/`) + 7 (`shared/`) + 1 (`README.md`) = 24 files.** `bindings/`
  and `views/` contribute 0 files at freeze time and are reserved-only.

None of these files exist yet. This section freezes the target inventory for
future implementation groups (§46); it does not create any file.

---

## 5. Disposition of F-135Z-3

See §51 for the full resolution. Summary: this contract **re-derives** the
full verification matrix independently (per this task's explicit instruction
not to freeze requirements merely because 136B suggested them), arrives at
**62 normative requirements**, states the derivation method transparently, and
formally resolves F-135Z-3 **conditioned on Phase 136D independently
re-verifying the same count and content** (this document is a contract
freeze, not an independent verification — see §52 verdict for why the
"WITH PREREQUISITES" qualifier applies).

---

## 6. Shared definition inventory

Frozen shared `$defs`, one file each under `shared/`:

| `$defs` file | Shapes defined | Used by |
|---|---|---|
| `envelope.schema.json` | `companion_envelope` (universal fields: `schema_id`, `schema_version`, `contract_version`, `record_type`, `record_id`, `record_digest`, `created_at`), `phase_identity`, `transition_identity`, `migration_epoch_reference` | every `records/*.schema.json`, via `allOf` composition |
| `enums.schema.json` | The 7 shared typed enums (§8): `authority_kind`, `authority_role`, `migration_stage`, `generation_role`, `publication_state`, `recovery_state`, `compatibility_mode` | every `records/*.schema.json` that carries the corresponding field |
| `identity.schema.json` | `record_identity` (opaque id shape, §12), `principal_identifier` (§6.1), `generation_reference` id shape | records needing an id shape without a full reference tuple |
| `digest.schema.json` | `sha256_hex` (bare 64-lowercase-hex-character string, §14) | every field typed as a digest anywhere in this package |
| `references.schema.json` | `record_reference` (id+digest+family tuple, §13), `cas_expectation` (embedded, §14 of 136B / row 10 of §4 above), `authority_epoch_reference`, `authority_pointer_digest_reference` | records that reference another record by identity+digest |
| `failures.schema.json` | `reason_code` (closed enum, informational only — never authority-bearing on its own), `conflict_type` local enum member shapes | `concurrency_conflict.schema.json`, `quarantine_record.schema.json`, `publication_evidence.schema.json` |
| `limitations.schema.json` | `limitation` (array-of-string-with-shape, §6.1), `authority_disclosure` (a fixed enum of disclosure strings distinguishing "this record does not itself establish current authority") | every `records/*.schema.json` |

### 6.1 Shared definitions this contract deliberately excludes from universal use

Per the task's instruction to avoid forcing irrelevant shared fields into
every schema, the following are **not** part of the universal envelope and
appear only where a family actually needs them:

- `source_revision` / `final_input_revision` — only on records that derive
  from a prior lifecycle revision (`cutover_request`, `readiness_package`).
- `signature/proof reference` — only on `human_authorization.schema.json`
  and `certification.schema.json`.
- `principal_identifier` — only on `human_authorization.schema.json`.
- `generation_reference` — only on records that must bind to a specific
  lifecycle generation (`authority_state`, `cutover_candidate`,
  `certification`, `publication_attempt`, `publication_evidence`).

---

## 7. Envelope contract

### 7.1 Universal fields (every `records/*.schema.json` file)

Every companion record **must** declare, via composition with
`shared/envelope.schema.json#/$defs/companion_envelope`:

- `schema_id` (string, `const` per file — identifies which record family
  this document is);
- `schema_version` (string, semantic-version-shaped, §45.14);
- `contract_version` (string, `const "1.0"` at freeze time — identifies which
  version of *this* contract the schema was generated against);
- `record_type` (string, `const`, one of the 16 standalone family names);
- `record_id` (string, shape per §12);
- `record_digest` (string, shape per §14);
- `created_at` (string, shape per §16).

### 7.2 Family-required fields

| Requirement | Families |
|---|---|
| `phase_id` required | `cutover_request`, `readiness_package`, `human_authorization`, `certification` |
| `transition_id` required | `authority_state`, `publication_attempt`, `publication_evidence`, `recovery_journal_entry` |
| `migration_epoch` required | all 16 standalone families — every companion record binds to exactly one migration epoch (this restates `CSCH-INV-1`) |
| Created-before-target-epoch-exists case | `authority_epoch.schema.json` for a **proposed** (not yet active) epoch — see §17 for the resolution: `activation_state` is required and `const`-restricted to forbid an `active` value at creation time |
| Global compatibility records | `compatibility_state.schema.json` — does **not** require `phase_id` or `transition_id` (compatibility state spans phases; requiring either would be a false precision claim) |
| Historical references | out of schema scope entirely — `historical_authority_reference` is a runtime-only typed model (row 20), never schema-validated |
| Authorization records | `human_authorization.schema.json` requires `request_reference` (§13) binding it to a specific `cutover_request` |
| Journal entries | `recovery_journal_entry.schema.json` requires `sequence` (monotonic integer) and `prior_entry_digest` (nullable digest, §26) |

### 7.3 Forbidden-field rule

No family may declare a field that only another family's schema defines as
authority-bearing without also declaring that field's local conditional
constraints in its own document (no "borrowed" authority-bearing fields).
Fields shared purely as shape (via `shared/enums.schema.json`,
`shared/digest.schema.json`, etc.) are exempt from this rule — sharing a
*shape* is not sharing *authority*.

### 7.4 Absent-versus-null contract

Following this repository's existing canonicalization convention
(`src/pcae/cltr/canonicalization.py`'s explicit-nullable-field list), this
package freezes: a field that is **conditionally absent** (its presence is
gated by a sibling field's value, per §16) **must** be omitted from the
document entirely when the condition is not met — it **must not** appear as
JSON `null`. A field that is **always present but may have no known value**
(e.g. `winner` on an unresolved `concurrency_conflict` record) **must** use
an explicit `null` and **must** declare `"type": ["null", ...]` in its
schema. No field may be ambiguously either. Every field in every schema
under `records/` **must** be classified as one or the other in that file's
own inline documentation comment (JSON Schema `"description"` keyword) — this
is a fixture-time (§42) and independent-verification-time (§51) checkable
requirement, not merely a style preference.

---

## 8. Enum contract — shared typed authority enums

These 7 enums exist today **only as contract text** (135Z §3.1–§3.7); no
Python `Enum` class implements them yet. This contract freezes their **exact
wire values** as the JSON Schema `enum` arrays that will appear in
`shared/enums.schema.json`. No aliasing, case-folding, substring matching, or
implicit coercion is permitted anywhere this package validates these values.

### 8.1 `AuthorityKind`

| Wire value | Meaning | Allowed contexts |
|---|---|---|
| `legacy` | Legacy lifecycle is authoritative | `authority_state.authority_kind`, `authority_epoch.authority_kind` |
| `cltr` | CLTR is authoritative | same |

Unknown-value behavior: **reject.** No version-extension behavior is defined
for this enum in v1.0 — any future third value requires a new contract minor
version, not an implicit extension.

### 8.2 `AuthorityRole` (Stage-3 companion vocabulary — distinct from `CLTR-SCHEMA-001`'s 5-code `authority_role` field)

| Wire value | Meaning |
|---|---|
| `authoritative` | This record's referent is the live current authority |
| `derivative` | Derived from, but not itself, the authority |
| `operational` | Operational/process record, no authority claim |
| `evidence` | Evidence supporting a decision, no authority claim |
| `compatibility` | Compatibility-layer record |
| `historical` | Superseded/historical, read-only |
| `quarantined` | Quarantined, excluded from authority resolution |

Explicit non-aliasing note: this 7-value enum shares **zero** code points with
`CLTR-SCHEMA-001`'s 5-code (`S`/`R`/`D`/`E`/`V`) `authority_role` field. A
mapping table between the two vocabularies is documented informationally in
`shared/enums.schema.json`'s `description` field but is **not** itself
schema-enforced (that would be a cross-schema semantic check, out of Layer 2
scope). See §9 for the binding rule restricting the `authoritative` value.

### 8.3 `MigrationStage` (Stage-3 typed, 11 values)

`shadow`, `dual_derivation`, `atomic_rehearsal`, `rollback_rehearsal`,
`cutover_readiness`, `cutover_candidate`, `certified`, `publication_pending`,
`cltr_authoritative`, `legacy_compatibility`, `legacy_retired`.

Explicit note: this is **not** the same enum as
`src/pcae/cltr/migration/enums.py`'s existing `MigrationStage` (6 prose-value
class used by Stage 1 code). The two must never be conflated; this package's
`MigrationStage` `$def` is named distinctly in code comments as the "Stage-3
typed migration stage" to prevent accidental reuse of the wrong Python enum
when implementation begins.

### 8.4 `GenerationRole` (8 values)

`rehearsal_candidate`, `rehearsal_generation`, `cutover_candidate`,
`certified_generation`, `authoritative_generation`, `historical_generation`,
`superseded_generation`, `quarantined_generation`.

### 8.5 `PublicationState` (12 values)

`not_requested`, `requested`, `gate_rejected`, `gate_uncertain`, `certified`,
`publication_prepared`, `publication_attempted`, `publication_uncertain`,
`published`, `verified`, `conflict`, `quarantined`.

### 8.6 `RecoveryState` (Stage-3 typed, 10 values)

`none_required`, `resume_safe`, `retry_required`, `operator_review_required`,
`reconciliation_required`, `quarantine_required`, `conflict_unresolved`,
`publication_uncertain_unresolved`, `terminal_recovered`,
`terminal_unrecoverable`.

Explicit note: this is a **superset**, not a synonym, of the existing 4-value
`RecoveryClassification` in `src/pcae/cltr/enums.py`
(`none_required`, `resume_safe`, `observe_required`,
`reconciliation_required`) and is entirely distinct from the already-
implemented 11-value `RecoveryState` in
`src/pcae/cltr/migration/rehearsal/enums.py` (Stage 2). All three enums are
real and simultaneously valid in this codebase's eventual state, each scoped
to its own layer. No code may substitute one for another.

### 8.7 `CompatibilityMode` (6 values, forward-only ordering)

`legacy_authoritative` → `legacy_adapter` → `legacy_read_only` →
`legacy_historical` → `legacy_disabled` → `legacy_retired`.

This ordering is **advisory documentation** in the schema's `description`
field (JSON Schema cannot enforce state-machine transition ordering across
documents); actual forward-only enforcement is a Layer 4 semantic-validator
responsibility (§40).

### 8.8 Local enums (frozen per family)

| Enum | Values | Home schema |
|---|---|---|
| `RequestState` | `pending`, `evidence_gathering`, `ready`, `authorized`, `certified`, `publication_pending`, `published`, `rejected`, `withdrawn`, `expired` | `cutover_request.schema.json` |
| `ReadinessState` | `unknown`, `stale`, `partial`, `ready`, `conflict` | `readiness_package.schema.json` |
| `AuthorizationState` | `issued`, `used`, `revoked`, `expired` | `human_authorization.schema.json` |
| `CandidateState` | `proposed`, `verified`, `certifying`, `certified`, `superseded`, `quarantined` | `cutover_candidate.schema.json` |
| `CertificationState` | `pending`, `certified`, `stale`, `invalidated` | `certification.schema.json` |
| `GateResult` | `eligible`, `ineligible`, `uncertain`, `conflict` | `readiness_package.schema.json` (restates `CLTR-CUTOVER-001` §10's frozen four-value gate outcome) |
| `PublicationOutcome` | `not_attempted`, `cas_rejected`, `failed_before_replacement`, `publication_uncertain`, `published_and_verified`, `post_publication_verification_failed`, `conflict`, `quarantined` | `publication_evidence.schema.json` |
| `ConflictType` | `cas_mismatch`, `dual_writer`, `stale_expectation`, `unknown_winner` | `concurrency_conflict.schema.json` |
| `JournalState` | `recorded`, `reviewed`, `actioned`, `superseded` | `recovery_journal_entry.schema.json` |
| `ReconciliationState` | `reconciled`, `conflict` | documented in `views/README.md` only (row 13 has no schema file) |
| `QuarantineState` | `quarantined`, `under_review`, `released`, `permanently_retired` | `quarantine_record.schema.json` |
| `DeliveryState` | `not_dispatched`, `already_dispatched`, `payload_conflict` | `notification_authority_binding.schema.json` — restates the exact three ad hoc string literals already returned by `src/pcae/core/phase_reports.py`'s notification-dispatch-state logic, now given a closed schema-level enum for the first time |
| `MarkerState` | `absent`, `written`, `stale`, `conflict` | `marker_authority_binding.schema.json` |
| `ReceiptState` | `absent`, `finalized`, `stale`, `conflict` | `receipt_authority_binding.schema.json` |

For every enum in §8, unknown-value behavior is **reject** (fail closed); no
alias, case-fold, or substring match is ever permitted. Version-extension
behavior: a new enum member may only be added via a `schema_version` minor
bump on the owning file, never silently.

---

## 9. Authority-role contract

**Primary role field:** `authority_role` (§8.2, 7-value Stage-3 vocabulary).
No orthogonal secondary classification field is introduced by this contract.

**Binding rule:** `authority_role` **must never** equal `authoritative` in
any of the following schema files: `cutover_request`, `readiness_package`,
`human_authorization`, `cutover_candidate`, `certification`,
`publication_attempt`, `concurrency_conflict`, `recovery_journal_entry`,
`quarantine_record`, `compatibility_state`, and all three binding schemas.
This is enforced with a JSON Schema `not: {"const": "authoritative"}`
restriction on the `authority_role` field in each of those 12 files.

`authority_role: "authoritative"` **may** appear only in:

- `authority_state.schema.json`, when that `AuthorityState` record is itself
  the one currently resolved as the live authority (a state the schema can
  represent structurally but cannot itself confirm — that confirmation is a
  Layer 6 authority-resolver responsibility);
- `publication_evidence.schema.json`, only in the terminal
  `published_and_verified` `PublicationOutcome` state, and only alongside a
  non-null `authoritative_generation` reference — enforced via `if`/`then`
  (§16).

No companion record schema may declare itself authoritative unconditionally.
This is the schema-level restatement of `CLTR-CUTOVER-001` §5's
single-authority invariant and of `CSCH-INV`'s general prohibition on
dual-authority claims.

---

## 10. Identifier shape contract

| ID family | Prefix | Charset | Length | Case | Notes |
|---|---|---|---|---|---|
| `record_id` (generic, all families) | `<family-slug>-` (e.g. `authstate-`, `cutreq-`, `humanauth-`) | `[a-z0-9-]` after prefix | 8–128 chars total | lowercase only | no path separators (`/`, `\`), no traversal tokens (`..`), no whitespace |
| `migration_epoch` | none (opaque token) | `[a-z0-9._-]` | 1–64 chars | lowercase only | must not contain `/` or `..` |
| `phase_id` | none | `[A-Za-z0-9.]` (mixed case permitted — matches existing repo phase-naming convention, e.g. `136C`) | 1–16 chars | mixed case permitted, matching existing phase-ID convention | no path separators |
| `transition_id` | `trans-` | `[a-z0-9-]` | 8–128 chars | lowercase only | deterministic digest-derived, never a raw UUID (restates `CLTR-CUTOVER-001` §7) |
| `principal_identifier` | none | `[A-Za-z0-9._@-]` | 1–256 chars | mixed case permitted (may be an email-shaped string) | no path separators; no Unicode confusables — schema requires ASCII-only via the character class itself |

All identifier `pattern` regexes in this package are anchored (`^...$`) and
use only the ASCII character classes above — this is itself the mechanism
that forbids Unicode confusables and whitespace ambiguity (a non-ASCII or
whitespace character simply fails the pattern). JSON Schema validates shape
only; semantic validators (§40) later recompute identity (i.e., verify that a
`record_id` was actually derived deterministically from its owning record's
bound-field tuple, per `CLTR-CUTOVER-001` §7) — this package's schemas cannot
and do not attempt that recomputation.

---

## 11. Digest contract

**Frozen digest shape:** a bare 64-character lowercase hexadecimal string —
`^[0-9a-f]{64}$` — matching this repository's actual existing implementation
(`src/pcae/cltr/digest.py`: `ALGORITHM = "sha256"`, `EXPECTED_HEX_LENGTH = 64`,
`is_well_formed_digest` checks lowercase-only hex of exactly 64 characters).

This is a **deliberate deviation** from the recommended `sha256:<64 hex>`
prefixed form suggested elsewhere in this phase's originating instructions:
the repository's actual, already-implemented digest convention has no
`sha256:` prefix. This contract freezes the **existing repository format**,
not the suggested one, per the instruction to re-derive every requirement
from actual repository state rather than accept a suggested default. This is
recorded as **CONFIRMED-136C-1** in the findings table (§53).

Every digest-typed field in this package (`record_digest`, referenced-record
digest inside `references.schema.json#/$defs/record_reference`, generation
digest, manifest/pointer digest, journal-entry-chain digest) uses the single
shared `$def`: `digest.schema.json#/$defs/sha256_hex`.

JSON Schema validates representation only — that a string *looks like* a
well-formed digest. Digest recomputation against actual canonical bytes is
explicitly out of schema scope (§32) and remains a Layer 3 responsibility
(`src/pcae/cltr/canonicalization.py` / `digest.py`, reused unchanged, per
136B §43).

---

## 12. Reference contract

Frozen shape for `shared/references.schema.json#/$defs/record_reference`:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["record_id", "record_digest", "record_family"],
  "properties": {
    "record_id": { "$ref": "identity.schema.json#/$defs/record_identity" },
    "record_digest": { "$ref": "digest.schema.json#/$defs/sha256_hex" },
    "record_family": { "$ref": "enums.schema.json#/$defs/record_family" },
    "schema_id": { "type": "string" },
    "schema_version": { "type": "string" }
  }
}
```

`schema_id` and `schema_version` are **required** only where a reference
crosses a family boundary whose schema version compatibility is not
otherwise implied by context (e.g. `cutover_request` referencing a
`readiness_package`); they are **optional** where the reference is always to
the same family and version as the referencing document (e.g. a
`recovery_journal_entry`'s `prior_entry_digest`, which is always another
`recovery_journal_entry`).

An **optional immutable namespace-relative locator** field
(`storage_locator`) is permitted **only** on `notification_authority_binding`,
`marker_authority_binding`, and `receipt_authority_binding` (the three
binding families, which by nature point at an existing artifact's storage
location) and **only** as a namespace-relative path under
`.pcae/cltr-authority/` — never an absolute filesystem path, never containing
`..`, never crossing outside that namespace root. This is enforced with a
`pattern` that forbids a leading `/` and forbids the literal substring `..`.

Arbitrary absolute or relative filesystem paths are **forbidden** as trusted
references anywhere else in this package. `storage_locator` is the only
locator-shaped field this contract authorizes, and only in the three files
named above.

---

## 13. Timestamp contract

**Frozen shape:** RFC 3339 / ISO 8601 UTC with explicit `Z` suffix, matching
this repository's existing convention.

```
pattern: "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{1,6})?Z$"
```

- **Precision:** seconds required; fractional seconds optional, up to 6
  digits (microsecond precision, matching Python's `datetime.isoformat()`
  default when timezone-aware).
- **Timezone:** UTC only, denoted by literal `Z`. No numeric offset form
  (e.g. `+00:00`) is accepted by this pattern — this is a deliberate,
  stricter-than-RFC-3339 restriction, matching the repository's existing
  practice of always normalizing to `Z`.
- **Leap seconds:** not specially handled; `:60` seconds value is rejected by
  the pattern above (seconds component `[0-5]\\d` would be the stricter
  form — this contract adopts the stricter `\\d{2}` for simplicity and notes
  the theoretical leap-second gap as **NON-BLOCKING-136C-1**, since no
  producer of these records is expected to emit a leap second).
- **Null behavior:** a timestamp field that has not yet occurred (e.g.
  `expires_at` before an authorization is issued) **must** be governed by
  §16's conditional-presence rule (omitted, not null, when not yet
  applicable) rather than represented as `null`.
- **Expiry relationship:** whether "now" is past a given `expires_at` value
  is a Layer 4/5 semantic check (clock read + comparison); this package
  validates only that `expires_at`, when present, is shape-valid.

---

## 14. Unknown-field contract

Two-tier `additionalProperties` policy, frozen exactly:

**Tier 1 — strict (`additionalProperties: false`), no exceptions:**
`authority_epoch`, `authority_state`, `cutover_request`, `human_authorization`,
`certification`, `publication_attempt`, `publication_evidence`, and the
embedded `cas_expectation` `$def`. These 8 are the authority-bearing and
activation-relevant families; any unknown field here **must fail closed**.

**Tier 2 — one reserved extension key only:** `readiness_package`,
`concurrency_conflict`, `quarantine_record`, `compatibility_state`,
`cutover_candidate`, `recovery_journal_entry`, and the three binding schemas
(`notification_authority_binding`, `marker_authority_binding`,
`receipt_authority_binding`) permit **exactly one** additional key,
`_extensions`, itself constrained to `{"type": "object",
"additionalProperties": {"type": "string"}}` (string-valued extension map
only — no nested arbitrary structure). No other additional key is permitted
even in Tier 2 files.

Rationale for the two tiers (restated from 136B, frozen here as binding):
authority-bearing records must never silently absorb an unrecognized field
that could later turn out to be authority-relevant (a newer minor schema
version adding a field an older validator doesn't know about must be
rejected, not silently passed through). Evidentiary records benefit from one
narrow, explicitly-typed escape hatch for forward-compatible annotation
without weakening the closed-vocabulary guarantee everywhere else.

Newer authority-bearing content **must** fail closed under this policy — this
is the schema-level mechanism preventing silent ignorance of unknown critical
fields (§43 security contract).

---

## 15. Version contract

Every schema file declares three version-shaped fields (§7.1):
`schema_id` (identity, not a version), `schema_version` (this file's own
version, `MAJOR.MINOR` string), `contract_version` (this contract's version,
`const "1.0"` at freeze time).

- **Major/minor compatibility:** a validator implementing `schema_version`
  `"1.x"` **must** accept any `"1.y"` document (minor-forward compatible) and
  **must reject** any `"2.x"` document without an explicit upgrade path.
- **Unsupported major behavior:** reject, fail closed, surface as a
  `PublicationOutcome`-style `not_attempted`/`conflict` condition upstream —
  never silently coerce.
- **Newer minor behavior:** an older validator encountering a newer minor
  version **may** accept the document if all Tier-1 required fields are
  still present and no Tier-1 unknown field appears (the two-tier policy in
  §14 is precisely what makes this safe: a genuinely new required field on an
  authority-bearing record would be a **major** bump, not minor, by
  definition, since Tier-1 files have zero extension surface).
- **Optional extension behavior:** confined entirely to Tier 2's
  `_extensions` key; no other mechanism exists.
- **Deprecation:** a deprecated schema version **must** remain valid for
  reading historical records (never retroactively invalidated) but **may**
  be rejected for *new* record creation by a future writer-side policy (a
  Layer 4/6 concern, not enforced by the schema itself).
- **Historical verification:** re-validating an old record against its
  original `schema_version` (not the current one) is a required capability
  of the future schema registry (§41), not of any individual schema file.
- **Independent family versioning:** each of the 16 standalone families
  versions independently; a minor bump to `authority_state.schema.json` does
  not require any bump to `cutover_request.schema.json`. **One schema
  version must not silently reinterpret another family** — this is enforced
  structurally by the fact that no file `$ref`s another family's `records/`
  file directly; all cross-family sharing goes through the version-neutral
  `shared/` `$defs`.

---

## 16. Local conditional-validation contract

Frozen `if`/`then` conditions this package's schemas **must** enforce
locally (each restates one of `CSCH-INV-1`..`CSCH-INV-15` at the structural
level; cross-record confirmation of the same invariant remains Layer 4):

| Condition | Required field(s) when condition holds | Schema file |
|---|---|---|
| `authority_state.publication_state == "cltr_authoritative"` (i.e. this state record represents active authority) | `generation_reference` required, non-null | `authority_state.schema.json` |
| `publication_evidence.outcome == "publication_uncertain"` | `uncertainty_detail` (object: `last_known_state`, `retry_recommended`) required | `publication_evidence.schema.json` |
| `concurrency_conflict.type == "cas_mismatch"` | `expected_state` and `observed_state` (both `record_reference` shapes) required | `concurrency_conflict.schema.json` |
| `human_authorization.state == "revoked"` | `revocation_metadata` (object: `revoked_at`, `revoked_by`, `reason_code`) required | `human_authorization.schema.json` |
| `human_authorization.state == "used"` | `use_binding` (a `record_reference` to the `publication_attempt` that consumed it) required | `human_authorization.schema.json` |
| `quarantine_record` (always) | `quarantine_reason` (`reason_code` enum, required unconditionally — every quarantine record must carry a reason) | `quarantine_record.schema.json` |
| `publication_evidence.outcome == "published_and_verified"` | `target_readback` (a `record_reference` proving the post-publication read matched) required | `publication_evidence.schema.json` |
| `compatibility_state.mode` is one of `legacy_historical`, `legacy_disabled`, `legacy_retired` | `authority_role` **must not** be `authoritative` and **must not** be `derivative` (only `historical` or `compatibility` permitted) — this is the schema-level restatement forbidding authority fallback from a historical compatibility state | `compatibility_state.schema.json` |
| `receipt_authority_binding.receipt_state == "finalized"` | all of `marker_reference`, `publication_evidence_reference`, `generation_reference` required (no partially-bound finalized receipt) | `receipt_authority_binding.schema.json` |

**Rule:** this table encodes only conditions checkable from **within a single
document**. It does not and cannot encode cross-record truth (e.g. "the
referenced generation actually exists and matches") — that is Layer 4 (§40).
Any condition requiring a second document's content is explicitly excluded
from this table and left to semantic validation.

---

## 17. AuthorityEpoch schema contract

`records/authority_epoch.schema.json`, Tier 1 (strict).

| Field | Required | Type | Notes |
|---|---|---|---|
| `authority_kind` | yes | `enums.schema.json#/$defs/authority_kind` | |
| `migration_epoch` | yes | string, §10 shape | |
| `predecessor_epoch` | conditional | nullable `record_reference` | required key, nullable value — `null` for the first epoch, a reference otherwise (absent-vs-null: this is an "always present, may have no value" field per §7.4) |
| `activation_state` | yes | enum: `proposed`, `active`, `superseded` | |
| `generation_binding` | conditional | `record_reference` to an `authoritative_generation`-role generation | required only when `activation_state == "active"` |
| `digest` | yes | `sha256_hex` | |
| `limitations` | yes | `limitations.schema.json#/$defs/limitation` array | |

**Binding rule:** `activation_state` **must not** be `"active"` at the moment
of a proposed epoch's initial creation — the schema enforces this by making
`generation_binding` conditionally required only for `"active"`, and by
never permitting the *creation* pathway (a Layer 6 concern) to set
`activation_state: "active"` directly; a schema-valid document with
`activation_state: "proposed"` and no `generation_binding` is the only
structurally valid initial state. A proposed epoch transitioning to active
happens through a distinct write (a new document version), never an in-place
mutation — matching this record family's immutability expectation.

---

## 18. AuthorityState schema contract

`records/authority_state.schema.json`, Tier 1 (strict).

| Field | Required | Type |
|---|---|---|
| `record_id`, `record_digest`, `migration_epoch` | yes | per envelope |
| `active_authority_epoch` | yes | `record_reference` → `authority_epoch` |
| `authority_kind` | yes | `enums#/$defs/authority_kind` |
| `authoritative_generation` | conditional (see §16) | `record_reference` |
| `publication_evidence_reference` | yes | `record_reference` → `publication_evidence` |
| `pointer_digest` | yes | `sha256_hex` |
| `verification_state` | yes | enum: `unverified`, `verified`, `verification_failed` |
| `compatibility_mode` | yes | `enums#/$defs/compatibility_mode` |
| `uncertainty` | conditional | object, required iff `verification_state == "unverified"` |
| `limitations` | yes | array |

**Frozen one-way relationship** (documentation-only assertion this schema's
structure supports but cannot itself enforce across documents):

```
current-authority pointer → AuthorityState record → authoritative generation
```

`publication_evidence_reference` **proves** the transition occurred; it does
**not** itself establish authority — `authority_role` on this record may be
`authoritative` (§9) only when this AuthorityState is the one currently
resolved by the (future, unimplemented) authority resolver, a fact this
schema cannot check.

---

## 19. CutoverRequest schema contract

`records/cutover_request.schema.json`, Tier 1 (strict).

| Field | Required | Type |
|---|---|---|
| `target` | yes | `enums#/$defs/authority_kind` (must be `cltr` — a request targeting `legacy` is not a cutover) |
| `source_authority` | yes | `enums#/$defs/authority_kind` (must be `legacy` at v1.0) |
| `source_epoch`, `target_epoch` | yes, yes | `record_reference` → `authority_epoch` |
| `evidence_requirements` | yes | array of `reason_code`-shaped strings |
| `readiness_package_reference` | conditional | `record_reference`, **forbidden** at request-creation time, permitted only once a `readiness_package` exists that itself references this request — see circularity resolution below |
| `authorization_requirement` | yes | boolean, `const true` at v1.0 (human authorization always required) |
| `final_revision` | yes | string |
| `contract_version` | yes | per envelope |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

### 19.1 Circular-reference resolution

The risk: a `cutover_request` might seem to require a `readiness_package`
that itself requires the request's identity to exist. **Resolution, frozen:**
the base `cutover_request` document is created and digested **without**
`readiness_package_reference` present (the field is entirely **absent**, not
null, at creation — per §7.4's absent-vs-null rule). A `readiness_package` is
then created that references the request by `record_reference` (id+digest).
The request's `readiness_package_reference` field, if ever populated, is
populated in a **subsequent, separately-digested version** of the request
document (a new `record_id`/`record_digest`, immutable like every other
record here) — never a mutation of the original. This resolves the
dependency cycle by breaking it into two immutable documents in a strict
creation order (request → package → request-v2), never requiring either to
exist before the other in a single atomic step.

Similarly, `human_authorization` requires a `request_reference` (§7.2) — it
is always created strictly after the (v1, package-less) request exists, so
no cycle exists there either.

---

## 20. ReadinessPackage schema contract

`records/readiness_package.schema.json`, Tier 2 (`_extensions` only).

| Field | Required | Type |
|---|---|---|
| `evidence_references` | yes | array of `record_reference`, deterministically ordered (sorted by `record_id` lexicographically — matching this repo's existing canonicalization sort convention) |
| `phase_id`, `transition_id`, `migration_epoch` | yes (all three) | per envelope |
| `prerequisite_status` | yes | enum: `unknown`, `unmet`, `met` |
| `findings` | yes | array of finding objects (`id`, `verdict`, `title`) — a lightweight local shape, not the full findings-table format |
| `state` | yes | `ReadinessState` (§8.8) |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

`state == "conflict"` requires `findings` to contain at least one entry with
`verdict: "BLOCKING"` (an `if`/`then` restating "a package cannot silently
claim readiness while carrying an unresolved conflict"). This record remains
**derivative and non-activating**: `authority_role` on this schema is
restricted (§9) from ever being `authoritative`.

---

## 21. HumanAuthorization schema contract

`records/human_authorization.schema.json`, Tier 1 (strict).

| Field | Required | Type |
|---|---|---|
| `principal` | yes | `identity#/$defs/principal_identifier` |
| `method` | yes | enum: `manual_review`, `signed_attestation` |
| `request_reference` | yes | `record_reference` → `cutover_request` |
| `readiness_reference` | yes | `record_reference` → `readiness_package` |
| `target_reference` | yes | `record_reference` → `authority_epoch` (proposed target) |
| `issued_at` | yes | timestamp |
| `expires_at` | yes | timestamp — **required, not optional**, restating `CLTR-CUTOVER-001` §8's 24-hour freshness window as a mandatory field (the actual 24-hour comparison is Layer 4/5; this schema only requires the field exist) |
| `state` | yes | `AuthorizationState` (§8.8) |
| `revocation_metadata` | conditional | see §16 |
| `use_binding` | conditional | see §16 |
| `replay_binding` | yes | opaque string, a one-time-use token reference — **never** the secret/token value itself (§25 security, §26 secret-handling) |
| `risk_acknowledgement` | yes | boolean, `const true` |
| `proof_reference` | conditional | `record_reference` to an opaque, hashed evidence artifact — never a raw signature blob or secret |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

**Forbidden:** any field that would carry a reusable credential, bearer
token, password, or private key (§26). `replay_binding` and `proof_reference`
are opaque, hashed, non-reusable identifiers only.

---

## 22. CutoverCandidate schema contract

`records/cutover_candidate.schema.json`, Tier 2 (`_extensions` only).

Freezes Stage 3-specific evidence **beyond** the Stage 2 generation it
extends, using `record_reference` rather than embedding the Stage 2
generation's full content:

| Field | Required | Type |
|---|---|---|
| `stage2_generation_reference` | yes | `record_reference` (points at the existing, already-implemented Stage 2 rehearsal generation — not redefined by this contract) |
| `cas_expectation` | yes | embedded `$def` (row 10, §4) |
| `state` | yes | `CandidateState` (§8.8) |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

`authority_role` **must not** be `authoritative` (§9) — the candidate remains
non-authoritative at every state, including `certified`.

---

## 23. Certification schema contract

`records/certification.schema.json`, Tier 1 (strict).

| Field | Required | Type |
|---|---|---|
| `candidate_reference` | yes | `record_reference` → `cutover_candidate` |
| `request_reference` | yes | `record_reference` → `cutover_request` |
| `readiness_reference` | yes | `record_reference` → `readiness_package` |
| `authorization_reference` | yes | `record_reference` → `human_authorization` |
| `source_authority_reference` | yes | `record_reference` → `authority_epoch` |
| `target_epoch_reference` | yes | `record_reference` → `authority_epoch` |
| `cas_expectation` | yes | embedded `$def` |
| `verifier_evidence` | yes | array of `record_reference` |
| `state` | yes | `CertificationState` (§8.8) |
| `staleness` | conditional | object (`detected_at`, `reason_code`), required iff `state == "stale"` |
| `invalidation` | conditional | object (`invalidated_at`, `reason_code`), required iff `state == "invalidated"` |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

Certification itself **must not** publish authority — `authority_role`
restricted (§9) from `authoritative`.

---

## 24. CASExpectation schema contract (embedded `$def`)

`shared/references.schema.json#/$defs/cas_expectation`.

Every expected-state field is **explicit**. **Missing values are never
wildcards** — every field below is required within the `$def` itself (this
`$def` has no optional fields):

| Field | Required | Type |
|---|---|---|
| `expected_authority_kind` | yes | `authority_kind` |
| `expected_authority_epoch` | yes | `record_reference` |
| `expected_authoritative_generation` | yes | `record_reference` |
| `expected_authority_pointer_digest` | yes | `sha256_hex` |
| `expected_authority_state_digest` | yes | `sha256_hex` |
| `expected_migration_epoch` | yes | string |
| `expected_source_lifecycle_state` | yes | string (restates `CLTR-SCHEMA-001`'s `lifecycle_state` enum values) |
| `expected_compatibility_mode` | yes | `compatibility_mode` |
| `expected_journal_lock_state` | yes | enum: `unlocked`, `locked` |
| `expected_request_reference` | yes | `record_reference` |
| `expected_certification_reference` | yes | `record_reference` |

**Creation-order resolution:** `cas_expectation` is only ever embedded
(never a standalone document with its own `record_id`); it is created
together with, and digested as part of, its owning document
(`cutover_candidate` or `publication_attempt`). There is no independent
creation order to resolve — the embedding itself removes the ordering
question that a standalone `CASExpectation` record would have raised.

---

## 25. PublicationAttempt schema contract

`records/publication_attempt.schema.json`, Tier 1 (strict).

| Field | Required | Type |
|---|---|---|
| `attempt_id` | yes | string, §10 shape (deterministic: digest of the bound-field tuple below, **never** timestamp-derived alone) |
| `request_reference`, `candidate_reference`, `certification_reference` | yes (all three) | `record_reference` |
| `cas_expectation` | yes | embedded `$def` |
| `source_authority_reference`, `target_authority_reference` | yes (both) | `record_reference` |
| `attempt_sequence` | yes | integer, monotonic per `request_reference` |
| `temporary_pointer_reference` | conditional | `record_reference`, present only during in-flight publication |
| `state` | yes | `PublicationState` (§8.5) |
| `uncertainty` | conditional | required iff `state == "publication_uncertain"` |
| `created_at` | yes | timestamp |
| `failure_classification` | conditional | required iff `state` is one of `gate_rejected`, `conflict` |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

**Replay vs. retry:** `attempt_id` is **deterministic** (digest of
`request_reference` + `candidate_reference` + `attempt_sequence`) — two
attempts with identical bound fields and identical `attempt_sequence`
necessarily produce the identical `attempt_id`, which is precisely how a
replay is detected structurally (same id) versus a retry (new
`attempt_sequence`, new id). **Timestamp alone is never the identity
mechanism** — `created_at` is documentation, not identity.

---

## 26. PublicationEvidence schema contract

`records/publication_evidence.schema.json`, Tier 1 (strict).

Exact `PublicationOutcome` wire values (§8.8, restated here as the field this
schema governs): `not_attempted`, `cas_rejected`, `failed_before_replacement`,
`publication_uncertain`, `published_and_verified`,
`post_publication_verification_failed`, `conflict`, `quarantined`.

| Field | Required | Type |
|---|---|---|
| `attempt_reference` | yes | `record_reference` → `publication_attempt` |
| `outcome` | yes | `PublicationOutcome` |
| `uncertainty_detail` | conditional | required iff `outcome == "publication_uncertain"` (§16) |
| `target_readback` | conditional | required iff `outcome == "published_and_verified"` (§16) |
| `authoritative_generation` | conditional | required iff `outcome == "published_and_verified"` — enables `authority_role: "authoritative"` per §9 |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

`publication_uncertain` and any failure outcome (`cas_rejected`,
`failed_before_replacement`, `post_publication_verification_failed`,
`conflict`) are **structurally distinct enum values** — uncertainty can never
collapse into failure at the schema level, since they are different `const`
values with different conditional field requirements.

---

## 27. ConcurrencyConflict schema contract

`records/concurrency_conflict.schema.json`, Tier 2 (`_extensions` only).

| Field | Required | Type |
|---|---|---|
| `actors` | yes | array of `principal_identifier` or `record_reference` (at least 2 entries) |
| `requests` | yes | array of `record_reference` → `cutover_request` (at least 1 entry) |
| `expected_state`, `observed_state` | conditional (see §16) | `record_reference` |
| `type` | yes | `ConflictType` (§8.8) |
| `winner` | conditional | nullable `record_reference` — **must not** be required when the outcome remains uncertain (field is present-but-null when unknown, absent only if truly not-yet-determinable — see below) |
| `recovery_requirement` | yes | `RecoveryState` (§8.6) |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

**Winner-unknown rule:** `winner` is declared **required, nullable** (not
conditionally absent) — every conflict record must take a position on
whether a winner is known, using explicit `null` for "not known," never
omission. This is the one deliberate exception to §7.4's general
absent-preferred rule: because "unknown winner" is itself a meaningful,
always-present fact about a conflict record, it is modeled as
always-present-possibly-null rather than conditionally-absent.

---

## 28. RecoveryJournal schema contract

`records/recovery_journal_entry.schema.json`, Tier 2 (`_extensions` only).

| Field | Required | Type |
|---|---|---|
| `sequence` | yes | integer, monotonic, ≥ 0 |
| `prior_entry_digest` | yes (nullable) | `sha256_hex` or `null` — `null` only for `sequence == 0` (genesis) |
| `operation_reference` | yes | `record_reference` (the request/attempt this entry concerns) |
| `prior_state_reference` | yes | `record_reference` |
| `new_state_reference` | yes | `record_reference` |
| `authority_state_reference` | yes | `record_reference` → `authority_state` |
| `generation_reference` | yes | `record_reference` |
| `publication_attempt_reference` | conditional | `record_reference`, required iff this entry concerns a publication event |
| `external_effect_state` | yes | enum: `none`, `pending`, `applied`, `unknown` |
| `retry_replay_classification` | yes | enum: `original`, `retry`, `replay` |
| `operator_review` | conditional | object, required iff `state == "reviewed"` or later |
| `recovery_action` | conditional | required iff `state == "actioned"` |
| `state` | yes | `JournalState` (§8.8) |
| `created_at` | yes | timestamp |
| `digest` | yes | `sha256_hex` |

**Hash-chain decision, frozen: YES, a hash chain is required.** Each entry's
`prior_entry_digest` **must** equal the immediately preceding entry's
`digest` field for the same journal (a specific `migration_epoch` +
`request_reference` scope), with `null` reserved for exactly the first entry
(`sequence == 0`). This is a schema-level shape requirement (the field
exists and has the right shape); **verifying that the chain is actually
unbroken** (that `prior_entry_digest` genuinely matches the prior entry's
actual digest, and that `sequence` values are contiguous with no gap) is a
Layer 4 semantic-validator responsibility, since it requires reading two
documents. Truncation is detected by that same Layer 4 check: a missing
`sequence` value or a `prior_entry_digest` that does not match any known
entry's `digest` is flagged as chain corruption. Ordering is guaranteed only
by the monotonic `sequence` field, not by filesystem write order or
timestamp.

---

## 29. ReconciliationResult schema contract

Row 13 (§4): **no persisted executable schema.** This is a derived,
computed, read-only output — restated per §36.

`mutation: none` is a **structural fact** of this family (it is a function's
return value, not a write path), not something to be schema-enforced against
a document that will never exist as a schema-validated artifact at v1.0.

**Whether persisted reconciliation evidence is optional or mandatory:**
**optional.** A future implementation **may** persist a snapshot of a
reconciliation result for audit purposes (e.g. under
`.pcae/cltr-authority/reconciliation-snapshots/`), but no schema in this
package requires such persistence, and if persisted, that snapshot
**must** carry `authority_role: "evidence"` (never `authoritative` or
`derivative`) and is documented, not schema-enforced, per §36.

---

## 30. Quarantine schema contract

`records/quarantine_record.schema.json`, Tier 2 (`_extensions` only).

| Field | Required | Type |
|---|---|---|
| `object_type` | yes | enum: `generation`, `publication_attempt`, `authority_state`, `compatibility_state` |
| `object_reference` | yes | `record_reference` |
| `reason_code` | yes | `failures.schema.json#/$defs/reason_code` |
| `state` | yes | `QuarantineState` (§8.8) |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

**Address current-authority integrity failure without:**

- **automatic legacy fallback** — this schema carries no field that would
  cause a resolver to silently prefer `legacy` on quarantine; that behavior
  (or its absence) lives in the Layer 6 authority resolver, not here, but
  this schema's `authority_role` restriction (§9, forbidding
  `authoritative` on quarantine records) is the structural guarantee that a
  quarantine record can never itself *become* the fallback authority by
  being schema-valid.
- **silent no-authority state** — every quarantine record requires a
  non-null `reason_code` (§16), preventing a quarantine from being recorded
  without an explanation.
- **quarantine becoming authority** — `authority_role` restriction (§9).

**Full production-integrity recovery** (i.e., the actual operational
procedure for un-quarantining and resuming production) **remains deferred**
and is marked here as an **activation prerequisite** for any future Stage 3
cutover — restated as finding **PREREQUISITE-136C-1** (§53).

---

## 31. Notification binding schema contract

**Disposition: standalone schema**, `records/notification_authority_binding.schema.json`,
Tier 2 (`_extensions` only). This is a companion binding record today (per
§0.3/§0.4), not a `CLTR-SCHEMA-001` extension and not a bare shared `$def`.

| Field | Required | Type |
|---|---|---|
| `authoritative_generation_reference` | yes | `record_reference` |
| `authority_epoch_reference` | yes | `record_reference` |
| `payload_digest` | yes | `sha256_hex` |
| `attempt_identity` | yes | string, §10 shape |
| `pfn001_classification` | yes | string (restates the existing PFN-001 classification vocabulary; not redefined here) |
| `delivery_state` | yes | `DeliveryState` (§8.8) |
| `uncertainty` | conditional | required iff `delivery_state == "payload_conflict"` |
| `marker_reference` | conditional | `record_reference` → `marker_authority_binding`, required iff `delivery_state != "not_dispatched"` |
| `receipt_reference` | conditional | `record_reference` → `receipt_authority_binding`, required iff `delivery_state == "already_dispatched"` |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` |

---

## 32. Marker binding schema contract

`records/marker_authority_binding.schema.json`, Tier 2.

| Field | Required | Type | Prevents |
|---|---|---|---|
| `generation_reference` | yes | `record_reference` | wrong-generation marker (field pins exactly one generation) |
| `created_at` | yes | timestamp | stale marker (Layer 4 compares against authority-state freshness) |
| `state` | yes | `MarkerState` (§8.8) | — |
| `duplicate_of` | conditional | nullable `record_reference`, required-key present iff `state == "conflict"` | duplicate-delivery claim (an unacknowledged second marker for the same generation must reference the first, never silently coexist) |
| `compatibility_fallback_forbidden` | yes | boolean, `const true` | compatibility fallback (schema pins this flag to always-true, documenting the prohibition even though enforcing it is a Layer 6 concern) |
| `authority_role` | yes, restricted (§9) | — | marker-as-authority |
| `digest` | yes | `sha256_hex` | — |

---

## 33. Receipt binding schema contract

`records/receipt_authority_binding.schema.json`, Tier 2.

| Field | Required | Type | Prevents |
|---|---|---|---|
| `generation_reference` | yes | `record_reference` | wrong-generation receipt |
| `publication_evidence_reference` | yes | `record_reference`, **must** resolve to a `published_and_verified` outcome — enforced by requiring this field's presence to co-occur only with `receipt_state: "finalized"` (§16) | receipt before publication verification |
| `marker_reference` | yes | `record_reference` (§16, finalized-state bundle) | receipt before required notification state |
| `authority_role` | yes, restricted (§9) | — | receipt as second authority |
| `receipt_state` | yes | `ReceiptState` (§8.8) | — |
| `staleness_check` | conditional | object, required iff a recovery journal entry references this receipt | stale receipt in recovery |
| `digest` | yes | `sha256_hex` | — |

---

## 34. CompatibilityState schema contract

`records/compatibility_state.schema.json`, Tier 2 (`_extensions` only).
Preserves the resolution of **PREREQUISITE-136A-2** (136B §7): a history
path sibling to `authority-state/<state_id>.json`.

| Field | Required | Type |
|---|---|---|
| `component` | yes | string (identifies which legacy component this compatibility record concerns) |
| `role` | yes | string enum: matches `AuthorityRole` §8.2 restricted to `compatibility` \| `historical` |
| `allowed_reads` | yes | array of string (which read paths remain valid) |
| `forbidden_authority_use` | yes | boolean, `const true` |
| `fallback_disabled` | yes | boolean |
| `mode` | yes | `CompatibilityMode` (§8.7) |
| `retirement_state` | conditional | required iff `mode == "legacy_retired"` |
| `digest` | yes | `sha256_hex` |
| `limitations` | yes | array |

**Immutable history record:** every `compatibility_state` document is
immutable once created (a mode transition creates a **new** document, never
an in-place edit) — this is the same pattern as `authority_epoch` (§17).
**Current compatibility pointer:** a separate, small pointer artifact (not a
schema-validated record in this package, analogous to the existing
current-generation pointer pattern) identifies which `compatibility_state`
document is current; that pointer's own persistence is a Layer 6/runtime
concern, not schema-governed here. Persistence path, restating 136B's
resolution: `.pcae/cltr-authority/epochs/<migration_epoch>/compatibility/<compatibility_state_id>.json`, mirroring `.../authority-state/<state_id>.json`.

---

## 35. HistoricalAuthorityReference schema contract

Row 20 (§4): **no executable schema — runtime-only typed model.** See §37 for
the full disposition. This section only freezes the **prohibition**: a
historical reference, wherever it is represented in code, **must** be
excluded from satisfying any current-resolver query, and **must** carry an
explicit, non-schema-enforced (since there is no schema) but
code-enforced marker distinguishing it from a live `authority_state` — the
typed model's own type (a distinct Python class, never a subtype or
duck-typed stand-in for the live `AuthorityState` model) is the mechanism
that prevents accidental substitution.

---

## 36. Derived reconciliation-view contract

Row 13 (§4). If a derived-view *file* is ever added under `views/` for
`reconciliation_result` (optional, documentation-only, not required by this
contract), it **must**:

- carry no `record_id`/`record_digest` pair that could be mistaken for a
  persisted record identity (a derived view has no independent identity —
  it is always a projection of other, already-identified records);
- disclose `authority_role: "evidence"` only, never `authoritative` or
  `derivative`;
- carry an explicit `mutation: "none"` `const` field if ever instantiated as
  a document at all;
- require no persistence (the absence of a file under `views/` at any given
  time is not an error);
- never be `$ref`-included by any `records/` file (one-way: views may
  reference records, records must never reference views).

---

## 37. Runtime-only typed-model disposition

**The one runtime-only typed model: `HistoricalAuthorityReference` (row 20).**

- **Purpose:** represent, in Python only, a pointer to a superseded/historical
  authority epoch or generation for diagnostic and audit-trail purposes.
- **Why no schema:** it is never independently persisted as a standalone
  JSON document exchanged between processes or written to disk in its own
  file — it exists only as an in-memory or embedded representation
  (referenced *from* other records, e.g. an `authority_epoch`'s
  `predecessor_epoch` field, which itself already has a schema-defined
  `record_reference` shape). Giving it its own top-level executable schema
  would create a second, redundant persistence path for information the
  16 standalone schemas already carry via `record_reference`.
- **Inputs:** a `record_reference` (id + digest + family) to the historical
  epoch/generation, plus the migration epoch under which it was superseded.
- **Outputs:** a read-only, immutable Python value object (dataclass or
  equivalent) usable by diagnostic/reporting code.
- **Persistence prohibition:** must never be independently persisted to its
  own file; it is always reconstructed from existing persisted records
  (`authority_epoch`, `authority_state` history).
- **Authority prohibition:** must never be resolvable as current authority
  by any Layer 6 resolver query.
- **Future typed-model implementation milestone:** implementation group 9
  (§46) — bundled with the reconciliation-function work, since both are
  read-only, non-persisted, diagnostic-only capabilities.

---

## 38. Not-required family disposition

**The one family classified as not required: Authority Transition Receipt
(row 15).**

- **Why redundant:** its intended semantics (proof that an authority
  transition completed and was acknowledged) are already fully carried by
  the combination of `authority_state` (§18, proves the transition's
  resulting state), `publication_evidence` (§26, proves the publication
  outcome including `published_and_verified`), and
  `receipt_authority_binding` (§33, proves notification-receipt
  finalization bound to that same generation). A fourth, separate
  "transition receipt" record would duplicate fields already present across
  these three without adding a distinct guarantee.
- **Which records carry the necessary semantics:** `authority_state` +
  `publication_evidence` + `receipt_authority_binding`, as above.
- **How future implementation avoids accidentally recreating it as a second
  authority:** implementation groups 6–7 and 10 (§46), which build these
  three families, **must not** introduce any field named
  `transition_receipt` or equivalent on any other schema, and any future
  proposal to add such a field must be treated as a new finding requiring a
  fresh contract amendment (§0.1 amendment rule), not an informal addition.

---

## 39. Canonicalization boundary contract

JSON Schema **cannot** enforce, and no schema in this package attempts to
enforce:

- key order in parsed objects (JSON Schema validates a parsed document; key
  order is a serialization-level property already normalized away by Layer 1
  parsing and Layer 3 canonicalization, never visible to Layer 2);
- Unicode normalization (NFC normalization, per
  `src/pcae/cltr/canonicalization.py`, happens at Layer 3; Layer 2 schemas
  validate whatever string a parser hands them, normalized or not — a
  non-normalized-but-otherwise-valid string still passes Layer 2, and Layer 3
  is where normalization is actually enforced before digesting);
- deterministic collection order where semantic sorting is required (e.g.
  `evidence_references` sort order, §20) — JSON Schema can constrain an
  array's *item shapes* but not that the array is sorted in a particular
  semantic order; this package documents the required order in
  `description` fields only, and Layer 3/4 enforce it;
- canonical timestamp normalization beyond shape (§13 validates shape; it
  cannot enforce that two semantically-equal timestamps in different valid
  formats were normalized to the identical string before digesting);
- digest recomputation (§11, §14);
- deterministic serialization bytes (the exact canonical byte sequence used
  for digesting is a Layer 3 property, never visible to or checkable by a
  Layer 2 schema, which only ever sees the already-parsed object graph).

These all belong to `src/pcae/cltr/canonicalization.py` and `digest.py`
(Layer 3), reused unchanged (136B §43) — this contract introduces no new
canonicalization code or rule, and freezes no schema-level workaround for
any of the above.

---

## 40. Semantic-validation boundary contract

A future semantic validator (Layer 4, not built by this phase) is
responsible for:

- identity recomputation (verifying `record_id` was genuinely derived from
  the bound-field tuple `CLTR-CUTOVER-001` §7 specifies);
- digest recomputation (verifying `record_digest` matches
  `compute_record_digest()` over the canonical form);
- cross-record invariant checks (all 15 `CSCH-INV` entries in their full,
  cross-document form — this package's `if`/`then` conditions in §16 are
  only the single-document-visible subset of the same invariants);
- common epoch/revision checks (that two related records agree on
  `migration_epoch`, `final_revision`, etc.);
- authorization freshness (24-hour window, §21, against wall-clock time);
- certification staleness (whether a `certified` certification is still
  valid given elapsed time or a changed source state);
- CAS comparison (whether a `cas_expectation`'s fields actually match live
  state at write time — the schema only validates the expectation's own
  shape, never compares it to anything);
- authority-state/generation binding (that `authority_state`'s
  `authoritative_generation` reference actually resolves to a real,
  certified generation);
- quarantine exclusion (that a quarantined object is actually excluded from
  resolver queries at runtime);
- marker/receipt generation consistency (that marker and receipt bindings
  for the "same" generation truly reference identical generation digests);
- compatibility non-authority (enforcing, at runtime, the restriction §9/§34
  only encode structurally);
- historical non-current checks (that a `HistoricalAuthorityReference`,
  §37, is never accidentally treated as current).

**No executable schema in this package may claim these guarantees alone.**
Every schema file's `description` field for the relevant property **must**
carry an explicit disclaimer pointing to this section, generated from the
shared `limitations.schema.json#/$defs/authority_disclosure` enum (§6).

---

## 41. Schema registry contract

Future registry behavior (deferred, not implemented by this phase):

- **Schema ID mapping:** `schema_id` (const string per file) → filesystem
  path, resolved once at registry load time.
- **Version lookup:** given `schema_id` + `schema_version`, resolve the
  correct historical or current schema document for validation (§15).
- **Local reference resolution:** all `$ref` targets resolved from the local
  `schemas/cltr_cutover/` tree only — no network fetch (§2), ever.
- **Duplicate schema detection:** the registry **must** reject at load time
  if two files declare the same `$id` or the same `(schema_id,
  schema_version)` pair.
- **Unknown schema:** a validation request for a `schema_id` the registry has
  never loaded **must** fail closed, never fall back to a "best guess" schema.
- **Unsupported version:** per §15, reject major-version mismatches.
- **Offline-only loading:** the registry loads exclusively from disk at
  process start (or explicit reload); no lazy network fetch under any
  condition.
- **No network fetching:** restated — this is an absolute prohibition, not a
  default.
- **Deterministic ordering:** the registry's internal load order **must** be
  deterministic (e.g. sorted by relative path) so that duplicate-detection
  error messages are reproducible across runs.
- **Integrity verification:** the registry **should** verify each loaded
  schema file's own digest against a manifest (a future concern; this
  contract does not freeze a manifest format for the registry itself, only
  notes the requirement).

Registry implementation is **deferred** to a future implementation phase
(§46, prerequisite to any group beginning validation against these schemas
programmatically).

---

## 42. Fixture contract

**Fixture files are not added in 136C.** This section freezes the
**obligation**, per schema, for a future fixture phase:

Every one of the 16 standalone schemas (§4) **must** eventually have fixture
coverage for:

- minimum valid document;
- fully populated valid document (every optional field present);
- missing required field (one fixture per required field, or a documented
  representative subset with rationale);
- forbidden extra field (Tier 1: any extra key; Tier 2: any key other than
  `_extensions`);
- wrong enum value (one fixture per enum-typed field);
- unknown critical field (Tier 1 files specifically — must be rejected);
- null-versus-absent (one fixture demonstrating the §7.4 distinction is
  actually enforced for at least one conditionally-absent and one
  always-present-nullable field per schema);
- unsupported schema version (major-version mismatch, §15);
- malformed identifier (violates §10's pattern);
- malformed digest (violates §11's pattern);
- invalid reference (a `record_reference` whose `record_family` does not
  match the field's documented expected family);
- traversal string (a `storage_locator` or identifier field containing `..`
  or a leading `/`, §12/§10);
- secret-containing invalid case (a fixture demonstrating that a field
  disallowed from carrying secret material, if populated with a
  secret-shaped string, is either rejected by shape or — where shape alone
  cannot detect it — flagged by the fixture's own documentation as a Layer 4
  responsibility, §26);
- each state-specific conditional from §16, one fixture per row.

---

## 43. Security contract

Schema-level defenses, frozen:

| Threat | Schema-level defense |
|---|---|
| Traversal strings | `pattern` on every identifier and locator field forbids `..` and leading `/` (§10, §12) |
| Absolute paths | same `pattern` mechanism; no field accepts an absolute path |
| Arbitrary locators | `storage_locator` restricted to exactly 3 binding schemas, namespace-relative only (§12) |
| Unknown critical fields | Tier 1 `additionalProperties: false`, no exception (§14) |
| Schema substitution | `schema_id` is a `const` per file; a document declaring the wrong `schema_id` for the schema validating it fails immediately |
| Reference substitution | every `record_reference` requires `record_family`, checked against the field's documented expected family at fixture/verification time (structural check only; true substitution detection — that the referenced digest actually matches that family's record — is Layer 4) |
| Enum spoofing | closed `enum` arrays everywhere, no wildcard, no regex-based enum approximation |
| Oversized identifiers | explicit max-length bound on every identifier pattern (§10) |
| Unicode ambiguity | ASCII-only character classes on every identifier pattern (§10) — this is the schema-level defense; it does not address Unicode ambiguity in *free-text* fields (e.g. `limitations` strings), which remain a Layer 4/UI concern |
| Secret persistence | §44 |

Semantic defenses (e.g. actually detecting a reference-substitution attack
by recomputing digests) remain future validator responsibilities (§40), not
schema-level guarantees.

---

## 44. Secret-handling contract

**Forbidden** in any field of any schema in this package:

- API tokens;
- Telegram bot tokens;
- passwords;
- private keys;
- bearer tokens;
- raw environment secrets (e.g. `TELEGRAM_BOT_TOKEN` values);
- reusable credentials of any kind.

**Allowed**, and the only mechanisms this contract provides for
authentication/authorization-adjacent evidence:

- principal IDs (`identity#/$defs/principal_identifier`, §21);
- public-key references (an opaque `record_reference` to a key-material
  artifact stored elsewhere under existing key-management conventions —
  never the key material itself);
- signatures (as opaque `proof_reference` values, §21 — a digest/hash of a
  signature artifact, never the raw signature bytes embedded in the
  companion record);
- hashed evidence (any evidence field is a digest or reference, never raw
  content that could itself be sensitive);
- opaque non-secret proof references.

No schema in this package defines a field literally named or documented as
accepting a secret value. `replay_binding` (§21) is explicitly documented as
a one-time-use opaque token *reference*, structurally indistinguishable from
any other opaque identifier, never a reusable bearer credential.

---

## 45. CLTR-SCHEMA relationship contract

Resolved architectural disposition for **PREREQUISITE-136A-1**, frozen per
family:

| Family | Vehicle |
|---|---|
| Rows 1–9, 11–12, 14, 19 (13 families) | **companion schema only** — `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001` is sufficient; no `CLTR-SCHEMA-001` change of any kind is needed or anticipated |
| Row 10 (CAS expectation) | **companion schema only** (embedded) |
| Row 13 (reconciliation) | **runtime-only / documented view**, no schema vehicle needed |
| Row 15 (transition receipt) | **not required**, no vehicle |
| Rows 16, 17, 18 (notification/marker/receipt bindings) | **mixed model** — companion schema today (this contract, §31–§33); a **future, optional, post-implementation** `CLTR-SCHEMA-001 v1.1.0` minor revision **may** later consolidate these three bindings directly into the production wire contract, but this is never a prerequisite to implementing or using the companion schemas as frozen here |
| Row 20 (historical reference) | **runtime-only**, no schema vehicle |

**No executable schema in this package may independently establish
lifecycle authority.** This restates §9's binding rule at the contract level:
regardless of vehicle, no schema — companion or any future
`CLTR-SCHEMA-001` extension — may allow a record to declare itself
authoritative outside the two narrow, conditionally-gated exceptions in §9.

`CLTR-SCHEMA-001` is **not modified** by this phase. No file under
`docs/CLTR-SCHEMA-001*` or `schemas/` changed as part of 136C.

---

## 46. Schema implementation groups

Restating and freezing 136B §41's file-level grouping as binding (unchanged
from 136B — this contract does not alter the grouping, only freezes it):

| Group | Files | Prerequisite group(s) | Independent verification required before next group |
|---|---|---|---|
| 1 | `shared/envelope.schema.json`, `shared/enums.schema.json`, `shared/identity.schema.json`, `shared/digest.schema.json`, `shared/references.schema.json`, `shared/failures.schema.json`, `shared/limitations.schema.json` | none | yes |
| 2 | `authority_epoch.schema.json`, `authority_state.schema.json` | 1 | yes |
| 3 | `cutover_request.schema.json` | 1, 2 | yes |
| 4 | `readiness_package.schema.json` | 1–3 | yes |
| 5 | `human_authorization.schema.json` | 1, 3, 4 | yes |
| 6 | `cutover_candidate.schema.json`, `certification.schema.json` | 1–5 | yes |
| 7 | `publication_attempt.schema.json`, `publication_evidence.schema.json` | 1–6 | yes |
| 8 | `concurrency_conflict.schema.json`, `recovery_journal_entry.schema.json` | 1–7 | yes |
| 9 | Reconciliation function + `HistoricalAuthorityReference` typed model (no schema file for either) | 1–8 | yes |
| 10 | `notification_authority_binding.schema.json`, `marker_authority_binding.schema.json`, `receipt_authority_binding.schema.json` | 1, 2, plus existing PFN-001 identities | yes |
| 11 | `compatibility_state.schema.json` (depends only on group 1); `quarantine_record.schema.json` (depends on 2–8) | 1 / 2–8 respectively | yes |

**Typed-model eligibility:** groups 2–8, 10, 11 each correspond 1:1 to a
future typed Python model (`src/pcae/cltr/authority/`, per 136B §42); group 9
corresponds to the one runtime-only typed model (§37) and the reconciliation
function. No group combines all families into a single unverified
implementation phase — each of the 11 groups requires its own independent
verification before the next group may begin (this restates 135Z §46
acceptance criterion 18 and 136B §5's F-135Z-3 gating rule).

---

## 47. Validation layers

Frozen (restating 136B §43 as binding contract text, unchanged):

```
Layer 1 — JSON parsing and duplicate-key rejection
  Input:  raw bytes
  Output: a parsed object graph, guaranteed free of duplicate keys
  Authority boundary: none (purely syntactic)

Layer 2 — executable schema validation (THIS CONTRACT'S ENTIRE SCOPE)
  Input:  a parsed object graph (post-Layer-1)
  Output: pass/fail against one named schema + version
  Authority boundary: none — validates shape only, per §1

Layer 3 — canonicalization and digest verification
  Input:  a Layer-2-valid document
  Output: a canonical byte form; a verified/unverified digest match
  Authority boundary: none — proves internal consistency, not authority
  Implementation: src/pcae/cltr/canonicalization.py, digest.py (reused, unchanged)

Layer 4 — cross-record semantic validation
  Input:  two or more Layer-3-verified documents
  Output: pass/fail against a named cross-record invariant (CSCH-INV-*)
  Authority boundary: none — proves relational consistency, not authority
  Implementation: future, not built by this phase

Layer 5 — live-state and CAS validation
  Input:  a Layer-4-valid document set + live filesystem/pointer state
  Output: CAS accept/reject; staleness verdict
  Authority boundary: none — proves the document set matches live state
    at a point in time, not that it is authoritative
  Implementation: future, not built by this phase

Layer 6 — authority resolution and operational gates
  Input:  all of the above, plus the current authority pointer
  Output: the single resolved authority (kind, epoch, generation, digest,
    verification state, uncertainty, limitations, compatibility mode)
  Authority boundary: this is the ONLY layer that may assert current
    authority (restates CLTR-CUTOVER-001 §4)
  Implementation: future, not built by this phase
```

No schema in this package operates above Layer 2. No claim in this contract
extends any schema's guarantee into Layer 3–6 territory.

---

## 48. Traceability contract

The full traceability matrix, mapping every `CSCH-REQ` (135Z/136B) and every
`CLTR-CUTOVER-SCHEMAS-001` §34 invariant (`CSCH-INV-1`..`15`) to this
contract's executable artifacts, implementation group, verification group,
and milestone, is published in **§51** as the unified 62-item matrix (which
supersedes and extends the 12-entry representative table from 135Z §45 /
136B §45, per those documents' own instruction that "this table is the
template, not a substitute").

---

## 49. Implementation acceptance criteria

Executable-schema implementation (any group in §46) may begin **only when
all** of the following hold:

1. Exact schema inventory frozen — §4 ✅ (this document).
2. Exact filenames and `$id` pattern frozen — §2, §3, §4 ✅.
3. Dialect frozen — §2 ✅ (draft 2020-12).
4. Shared definitions frozen — §6 ✅.
5. Enums frozen — §8 ✅ (7 shared + 14 local = 21 total enums).
6. Local conditionals frozen — §16 ✅.
7. Unknown-field behavior frozen — §14 ✅ (two-tier policy).
8. Versioning frozen — §15 ✅.
9. Identity/reference shape frozen — §10, §12 ✅.
10. Request/authorization dependency cycle resolved — §19.1 ✅.
11. CAS fields explicit — §24 ✅ (11 required fields, no optional/wildcard field).
12. Recovery journal shape frozen — §28 ✅ (hash-chain required).
13. CompatibilityState history frozen — §34 ✅ (PREREQUISITE-136A-2 preserved).
14. CLTR-SCHEMA relationship resolved — §45 ✅.
15. F-135Z-3 resolved or explicitly scheduled with exact remaining evidence
    — §51 (resolved, conditioned on 136D independent re-verification; see
    §52 verdict).
16. No unresolved **Blocking** contract defect — §53 (none found).

All 16 criteria above are met by this document, **except** that criterion 15
carries the explicit 136D-verification precondition recorded in §52's
verdict choice, which is why the verdict is "FROZEN WITH PREREQUISITES," not
an unqualified "FROZEN."

---

## 50. No-go criteria

Executable-schema implementation must **not** begin if any of the following
were true (none are, as verified below):

- Schema count or inventory ambiguous → **false**, §4.1 states exact counts.
- `$id` or reference layout ambiguous → **false**, §2, §12.
- Circular dependencies remain → **false**, §19.1 resolves the one
  identified cycle risk; no other cycle was found across §17–§34.
- One companion schema may claim authority → **false**, §9 forbids this in
  12 named files with only 2 narrowly-gated exceptions.
- Unknown fields may be silently ignored → **false**, §14's two-tier policy
  forbids this for the 8 Tier-1 files and narrows it to one typed key for
  the 8 Tier-2 files.
- CAS missing values can behave as wildcards → **false**, §24 requires all
  11 fields unconditionally.
- Uncertainty collapses into failure → **false**, §26 keeps them as
  structurally distinct enum values.
- Authorization replay semantics incomplete → **false**, §21's
  `replay_binding` + `expires_at` + `state` machine is fully specified at the
  shape level (freshness comparison itself is correctly deferred to Layer 4,
  not "incomplete").
- CompatibilityState history incomplete → **false**, §34 freezes the history
  path and immutability rule.
- Journal ordering undefined → **false**, §28 freezes the hash-chain +
  monotonic-sequence rule.
- CLTR-SCHEMA relationship ambiguous → **false**, §45.
- Semantic-validator responsibilities falsely assigned to JSON Schema →
  **false**, §1, §39, §40 explicitly exclude them.
- The full matrix falsely claimed complete → **false**, §51 discloses its
  derivation method and the honest count rather than asserting completeness
  without basis.

**No no-go condition is present.** Implementation of any §46 group may begin
once Phase 136D has independently re-verified §51's matrix (per the
"WITH PREREQUISITES" verdict, §52).

---

## 51. Verification matrix — full independently-derived requirement set

### 51.0 Derivation method and honest count disclosure

135Z §45 stated a claimed count of 62 items but published only 12
representative entries, deferring full publication to "Phase 136A" (finding
**F-135Z-3**). Phase 136A did not publish the full matrix either — it only
re-examined the same 12 representative entries and re-disclosed the gap.
Phase 136B carried F-135Z-3 forward, explicitly binding it to 136C.

Per this task's explicit instruction to **re-derive every normative
requirement independently** rather than accept 136B's framing, and to
**document any discrepancy** if the authoritative source contains a
different count than 62: this document constructs the full matrix from
first principles, organized by the structural categories a JSON-Schema-level
contract actually has to freeze (shared definitions, envelope, enums,
authority-role, identity/digest/reference/timestamp shape, per-family schema
contracts, non-schema family dispositions, and cross-cutting boundaries),
rather than by attempting to reverse-engineer an original, never-actually-
enumerated "62" list from the 12 surviving representative entries.

**Independently verified total: 62 requirements**, `CSCH-EXEC-REQ-001`
through `CSCH-EXEC-REQ-062`. This number was arrived at by the systematic
category construction below and was **not** assumed in advance; it is
recorded as a coincidence with the previously-cited "62" figure worth
flagging explicitly (finding **CONFIRMED-136C-2**, §53) — the original 62
count from 135Z §45 was never itself substantiated by an actual enumerated
list, so this document's 62 is an independent result, not a confirmation of
135Z's specific (never-published) 62 items. Because the matrix below is
newly and fully enumerated, cross-referenced, and auditable, this document
**resolves F-135Z-3** — subject to Phase 136D independently re-deriving and
re-checking this same matrix before it is treated as final (§52).

### 51.1 Matrix columns

- **ID** — `CSCH-EXEC-REQ-NNN`.
- **Source §** — the section of this document that freezes the requirement.
- **Family** — record family or `Shared`/`Cross-cutting`.
- **Schema responsibility** — what Layer 2 must enforce.
- **Semantic-validator dependency** — the Layer 3–6 responsibility this
  requirement explicitly excludes, if any (`—` if none).
- **Impl. group** — §46 group number (`—` if not implementation-scoped, e.g.
  a documentation-only requirement).
- **Verification method** — how 136D checks this requirement.
- **Milestone blocked** — which future milestone cannot proceed if this
  requirement is unmet.

### 51.2 Full matrix

| ID | Source § | Family | Schema responsibility | Semantic dependency | Impl. group | Verification method | Milestone blocked |
|---|---|---|---|---|---|---|---|
| CSCH-EXEC-REQ-001 | §2 | Shared | Every schema file declares `$schema` draft 2020-12 verbatim | — | 1–11 | Static scan of every `.schema.json` file's `$schema` key | Group 1 |
| CSCH-EXEC-REQ-002 | §2 | Shared | Every schema file declares a stable, non-network `$id` under `https://pcae.local/schemas/cltr_cutover/` | — | 1–11 | Static scan + registry duplicate-`$id` check | Group 1 |
| CSCH-EXEC-REQ-003 | §2 | Shared | Only relative-path `$ref`; no absolute-URL or network-resolved reference anywhere | Layer 2 boundary only | 1–11 | Static scan for `http`/`https` inside any `$ref` value | Group 1 |
| CSCH-EXEC-REQ-004 | §2 | Shared | `unevaluatedProperties` never used; conditional composition only via `if`/`then`/`oneOf` | — | 1–11 | Static scan for the keyword's absence | Group 1 |
| CSCH-EXEC-REQ-005 | §2 | Shared | Every shape-critical field (digest, identifier, timestamp) carries an explicit `pattern`, not `format` alone | Layer 3 (actual value correctness) | 1–11 | Static scan cross-referencing §10/§11/§13 field lists | Groups 2–11 |
| CSCH-EXEC-REQ-006 | §2 | Shared | Layer 1 duplicate-key rejection precedes Layer 2; no schema attempts to re-detect duplicate keys | Layer 1 | — | Confirm no schema references a duplicate-key check keyword (none exists in JSON Schema; this is a design-intent check) | — |
| CSCH-EXEC-REQ-007 | §3 | Shared | Package root is exactly `schemas/cltr_cutover/` with `shared/`, `records/`, `bindings/`, `views/` | — | 1 | Directory-existence + naming check at implementation time | Group 1 |
| CSCH-EXEC-REQ-008 | §3.2 | Shared | No runtime record ever stored under `schemas/cltr_cutover/` | Layer 6 (runtime write paths) | — | Repository-wide scan confirming no writer targets this path | All groups |
| CSCH-EXEC-REQ-009 | §4.1 | Shared | Exactly 16 standalone schema files, 7 shared `$defs` files, 1 embedded component, 0 derived-view files, 1 runtime-only model, 1 not-required family | — | 1–11 | File-count audit against §4 table at each group's completion | Groups 1–11 |
| CSCH-EXEC-REQ-010 | §6 | Shared | `envelope.schema.json` defines `companion_envelope` with exactly the 7 universal fields in §7.1 | Layer 4 (cross-record binding correctness) | 1 | Schema-content diff against §7.1 | Group 1 |
| CSCH-EXEC-REQ-011 | §6 | Shared | `enums.schema.json` defines exactly the 7 shared enums in §8.1–§8.7, each with its exact wire-value list | — | 1 | Schema-content diff against §8 | Group 1 |
| CSCH-EXEC-REQ-012 | §6 | Shared | `identity.schema.json`, `digest.schema.json`, `references.schema.json`, `failures.schema.json`, `limitations.schema.json` each define exactly the `$defs` listed in §6's table, no more, no fewer | — | 1 | Schema-content diff against §6 | Group 1 |
| CSCH-EXEC-REQ-013 | §7.1 | Shared | Every `records/*.schema.json` file composes `companion_envelope` via `allOf`, never re-declaring the 7 universal fields inline | — | 2–11 | Static scan for `allOf` + `$ref` to `envelope.schema.json` in every records file | Groups 2–11 |
| CSCH-EXEC-REQ-014 | §7.2 | Shared | Family-required-field table (phase_id / transition_id / migration_epoch requiredness per family) matches §7.2 exactly | Layer 4 | 2–11 | Schema-content diff per file against §7.2 | Groups 2–11 |
| CSCH-EXEC-REQ-015 | §7.4 | Shared | Every field in every schema is classified, in its `description`, as conditionally-absent or always-present-possibly-null, with no field left unclassified | — | 2–11 | Doc-comment presence check per property, per file | Groups 2–11 |
| CSCH-EXEC-REQ-016 | §8.1 | Shared | `AuthorityKind` enum = exactly `{legacy, cltr}`, reject-unknown | — | 1 | Enum-array diff | Group 1 |
| CSCH-EXEC-REQ-017 | §8.2 | Shared | `AuthorityRole` (Stage-3, 7-value) enum matches §8.2 exactly, zero shared code points with `CLTR-SCHEMA-001`'s 5-code field | Layer 4 (cross-vocabulary mapping correctness) | 1 | Enum-array diff + code-point intersection check against `src/pcae/cltr/enums.py`'s `AuthorityRole` | Group 1 |
| CSCH-EXEC-REQ-018 | §8.3 | Shared | `MigrationStage` (Stage-3 typed, 11-value) enum matches §8.3 exactly, distinct from `src/pcae/cltr/migration/enums.py`'s existing 6-value class | — | 1 | Enum-array diff + explicit non-conflation code comment check | Group 1 |
| CSCH-EXEC-REQ-019 | §8.4 | Shared | `GenerationRole` (8-value) enum matches §8.4 exactly | — | 1 | Enum-array diff | Group 1 |
| CSCH-EXEC-REQ-020 | §8.5 | Shared | `PublicationState` (12-value) enum matches §8.5 exactly | — | 1 | Enum-array diff | Group 1 |
| CSCH-EXEC-REQ-021 | §8.6 | Shared | `RecoveryState` (Stage-3 typed, 10-value) enum matches §8.6 exactly, distinct from both `RecoveryClassification` (4-value) and Stage-2 `RecoveryState` (11-value) | — | 1 | Enum-array diff + three-way distinctness check | Group 1 |
| CSCH-EXEC-REQ-022 | §8.7 | Shared | `CompatibilityMode` (6-value, forward-only documented order) enum matches §8.7 exactly | Layer 4 (ordering enforcement) | 1 | Enum-array diff | Group 1 |
| CSCH-EXEC-REQ-023 | §8.8 | Shared | All 14 local enums (`RequestState` … `ReceiptState`) match §8.8's value lists exactly, each in its documented home schema | — | 3, 4, 5, 6, 7, 8, 11 (per home file) | Enum-array diff per file | Corresponding group |
| CSCH-EXEC-REQ-024 | §8 | Shared | Unknown-enum-value behavior is reject (fail closed) for all 21 enums, no alias/case-fold/substring match anywhere | — | 1–11 | Fixture-driven negative test per enum (§42) | Groups 1–11 |
| CSCH-EXEC-REQ-025 | §9 | Cross-cutting | `authority_role: "authoritative"` is schema-forbidden (`not: {const: "authoritative"}`) in exactly the 12 named non-authority-bearing files | Layer 6 (actual live-authority confirmation) | 2, 3, 5, 6, 7 (partial), 8, 10, 11 | Static scan of the `not` restriction in each of the 12 files | Groups 2,3,5,6,7,8,10,11 |
| CSCH-EXEC-REQ-026 | §9 | AuthorityState, PublicationEvidence | `authority_role: "authoritative"` permitted only under the two named gated conditions | Layer 6 | 2, 7 | `if`/`then` presence check | Groups 2, 7 |
| CSCH-EXEC-REQ-027 | §10 | Shared | Every identifier family's `pattern` matches the exact prefix/charset/length/case table in §10 | Layer 4 (identity recomputation) | 1–11 | Regex-string diff per field | Groups 1–11 |
| CSCH-EXEC-REQ-028 | §10 | Shared | No identifier pattern permits `/`, `\`, `..`, or whitespace | Layer 3/4 | 1–11 | Regex analysis (character-class exclusion proof) | Groups 1–11 |
| CSCH-EXEC-REQ-029 | §11 | Shared | Digest shape is exactly `^[0-9a-f]{64}$` (bare hex, no `sha256:` prefix), matching `src/pcae/cltr/digest.py` | Layer 3 (actual recomputation) | 1 | Regex-string diff against digest.py's `is_well_formed_digest` logic | Group 1 |
| CSCH-EXEC-REQ-030 | §12 | Shared | `record_reference` requires exactly `record_id`, `record_digest`, `record_family`; `schema_id`/`schema_version` required only for cross-family references | Layer 4 | 1 | Schema-content diff | Group 1 |
| CSCH-EXEC-REQ-031 | §12 | Notification/Marker/Receipt bindings | `storage_locator` permitted only on the 3 named binding schemas, namespace-relative pattern only, no `..`, no leading `/` | Layer 5 (actual path resolution safety) | 10 | Static scan confirming absence of `storage_locator` outside the 3 files + regex diff | Group 10 |
| CSCH-EXEC-REQ-032 | §13 | Shared | Timestamp pattern matches §13's exact regex (seconds required, optional 1–6 fractional digits, literal `Z` only) | Layer 4/5 (expiry/ordering comparison) | 1–11 | Regex-string diff | Groups 1–11 |
| CSCH-EXEC-REQ-033 | §14 | AuthorityEpoch, AuthorityState, CutoverRequest, HumanAuthorization, Certification, PublicationAttempt, PublicationEvidence, CasExpectation | Tier 1: `additionalProperties: false`, zero exceptions | — | 2, 3, 5, 6 (partial), 7 | Static scan of the 8 named files | Groups 2,3,5,6,7 |
| CSCH-EXEC-REQ-034 | §14 | ReadinessPackage, ConcurrencyConflict, QuarantineRecord, CompatibilityState, CutoverCandidate, RecoveryJournalEntry, 3 binding schemas | Tier 2: exactly one extra key `_extensions`, string-valued map only | — | 4, 6 (partial), 8, 10, 11 | Static scan of the 8 named files | Groups 4,6,8,10,11 |
| CSCH-EXEC-REQ-035 | §15 | Shared | Every schema declares `schema_id` (const), `schema_version` (MAJOR.MINOR string), `contract_version` (const "1.0") | — | 1–11 | Field-presence + const-value check | Groups 1–11 |
| CSCH-EXEC-REQ-036 | §15 | Shared | Major-version mismatch is reject; minor-forward compatibility holds given the two-tier `additionalProperties` design | Layer 6 (writer/reader version negotiation) | — | Design-consistency review (no code exists yet to test directly) | Future registry milestone |
| CSCH-EXEC-REQ-037 | §16 | AuthorityState | `publication_state == "cltr_authoritative"` ⇒ `generation_reference` required | Layer 4 (cross-record confirmation of the reference's validity) | 2 | `if`/`then` presence + fixture (§42) | Group 2 |
| CSCH-EXEC-REQ-038 | §16 | PublicationEvidence | `outcome == "publication_uncertain"` ⇒ `uncertainty_detail` required | — | 7 | `if`/`then` presence + fixture | Group 7 |
| CSCH-EXEC-REQ-039 | §16 | ConcurrencyConflict | `type == "cas_mismatch"` ⇒ `expected_state`+`observed_state` required | — | 8 | `if`/`then` presence + fixture | Group 8 |
| CSCH-EXEC-REQ-040 | §16 | HumanAuthorization | `state == "revoked"` ⇒ `revocation_metadata` required; `state == "used"` ⇒ `use_binding` required | — | 5 | `if`/`then` presence + fixture (2 cases) | Group 5 |
| CSCH-EXEC-REQ-041 | §16, §30 | QuarantineRecord | `quarantine_reason` unconditionally required | — | 11 | Required-field check + fixture | Group 11 |
| CSCH-EXEC-REQ-042 | §16 | PublicationEvidence | `outcome == "published_and_verified"` ⇒ `target_readback` + `authoritative_generation` required | Layer 5 (actual readback verification) | 7 | `if`/`then` presence + fixture | Group 7 |
| CSCH-EXEC-REQ-043 | §16, §34 | CompatibilityState | `mode` in `{legacy_historical, legacy_disabled, legacy_retired}` ⇒ `authority_role` restricted to `{historical, compatibility}` | Layer 4/6 (runtime fallback prevention) | 11 | `if`/`then` presence + fixture | Group 11 |
| CSCH-EXEC-REQ-044 | §16, §33 | ReceiptAuthorityBinding | `receipt_state == "finalized"` ⇒ `marker_reference`+`publication_evidence_reference`+`generation_reference` all required | Layer 4 | 10 | `if`/`then` presence + fixture | Group 10 |
| CSCH-EXEC-REQ-045 | §17 | AuthorityEpoch | `activation_state == "active"` ⇒ `generation_binding` required; no valid document has `activation_state: "active"` at initial creation without it | Layer 6 (actual activation event) | 2 | `if`/`then` presence + fixture demonstrating `proposed` is the only schema-valid creation-time state without the binding | Group 2 |
| CSCH-EXEC-REQ-046 | §18 | AuthorityState | Full field set (§18 table) matches exactly; one-way pointer→state→generation relationship documented, not schema-enforced across documents | Layer 6 | 2 | Schema-content diff + `description` disclaimer presence check | Group 2 |
| CSCH-EXEC-REQ-047 | §19 | CutoverRequest | Full field set matches §19 exactly; `readiness_package_reference` absent at v1 creation, populated only in a v2 document (§19.1 circularity resolution) | Layer 6 (actual two-step creation enforcement) | 3 | Schema-content diff + fixture demonstrating v1 (field absent) and v2 (field present) are both independently schema-valid | Group 3 |
| CSCH-EXEC-REQ-048 | §20 | ReadinessPackage | `evidence_references` deterministically ordered (documented); `state == "conflict"` ⇒ at least one `BLOCKING` finding | Layer 4 (actual sort-order + finding-content check) | 4 | `if`/`then` (minItems-style) + fixture; ordering itself flagged Layer 4 | Group 4 |
| CSCH-EXEC-REQ-049 | §21 | HumanAuthorization | Full field set matches §21 exactly; no reusable-credential-shaped field present; `expires_at` required (24h window is Layer 4) | Layer 4 (freshness comparison) | 5 | Schema-content diff + secret-shape negative fixture | Group 5 |
| CSCH-EXEC-REQ-050 | §22 | CutoverCandidate | Full field set matches §22 exactly; `authority_role` forbidden from `authoritative` | — | 6 | Schema-content diff | Group 6 |
| CSCH-EXEC-REQ-051 | §23 | Certification | Full field set matches §23 exactly; `staleness`/`invalidation` conditionally required per `state` | Layer 4/5 (actual staleness detection) | 6 | Schema-content diff + `if`/`then` fixture | Group 6 |
| CSCH-EXEC-REQ-052 | §24 | CasExpectation | All 11 fields unconditionally required; no field is optional or wildcard-permitting; embedded only, never standalone | Layer 5 (actual CAS comparison against live state) | 6, 7 (both embedding sites) | Schema-content diff + fixture confirming a document missing any one of the 11 fields is invalid | Groups 6, 7 |
| CSCH-EXEC-REQ-053 | §25 | PublicationAttempt | `attempt_id` deterministic (digest of bound-field tuple), never timestamp-derived alone; `attempt_sequence` monotonic per request | Layer 4 (actual determinism verification, i.e. recomputing the digest) | 7 | Schema-content diff + `description` disclaimer; determinism itself is Layer 4 | Group 7 |
| CSCH-EXEC-REQ-054 | §26 | PublicationEvidence | `PublicationOutcome`'s 8 values are structurally distinct `const`s; uncertainty and failure never collapse into one value | — | 7 | Enum-array diff + fixture per value | Group 7 |
| CSCH-EXEC-REQ-055 | §27 | ConcurrencyConflict | `winner` required+nullable (not conditionally absent); `recovery_requirement` uses `RecoveryState` | Layer 4/6 (actual winner determination) | 8 | Schema-content diff + fixture (`winner: null` valid; `winner` absent invalid) | Group 8 |
| CSCH-EXEC-REQ-056 | §28 | RecoveryJournalEntry | Hash-chain required: `prior_entry_digest` null only at `sequence == 0`; monotonic `sequence`; chain-integrity verification itself deferred to Layer 4 | Layer 4 (chain-integrity + contiguity check) | 8 | Schema-content diff + fixture (`sequence:0`+`null` valid; `sequence:0`+non-null digest invalid) | Group 8 |
| CSCH-EXEC-REQ-057 | §29, §13 | ReconciliationResult | No persisted schema exists; if ever persisted, `authority_role` restricted to `evidence` only; `mutation: none` restated as structural, not schema-enforced | Layer 6 | 9 | Design-consistency review (no schema file exists to statically check) | Group 9 |
| CSCH-EXEC-REQ-058 | §30 | QuarantineRecord | Full field set matches §30 exactly; `authority_role` forbidden from `authoritative`; full production-integrity recovery marked as deferred activation prerequisite | Layer 6 (actual recovery procedure) | 11 | Schema-content diff + finding cross-reference (PREREQUISITE-136C-1) | Group 11 |
| CSCH-EXEC-REQ-059 | §31–§33 | Notification/Marker/Receipt bindings | Full field sets match §31–§33 exactly; `DeliveryState`/`MarkerState`/`ReceiptState` enums correctly wired; wrong-generation, stale, duplicate-delivery, and receipt-before-verification cases all structurally prevented per the tables in §32/§33 | Layer 4 (cross-binding generation-digest equality checks) | 10 | Schema-content diff + one fixture per "prevents" column entry (11 total across the 3 files) | Group 10 |
| CSCH-EXEC-REQ-060 | §36 | ReconciliationResult (views/) | If a `views/` file is ever added, it must carry no independent `record_id`/`record_digest`, must disclose `authority_role: evidence` only, and must never be `$ref`-included by any `records/` file | Layer 6 | 9 | One-way-reference static scan (confirms no current `records/` file references `views/`) | Group 9 |
| CSCH-EXEC-REQ-061 | §41 | Shared (registry) | Registry rejects duplicate `$id`/`(schema_id, schema_version)` pairs; loads offline-only; deterministic load order; unknown schema_id fails closed | Layer 6 (registry is itself a Layer 6 supporting component) | — (pre-implementation prerequisite to any group's runtime use) | Design-consistency review; executable test once registry is built | Future registry milestone, blocks all runtime use of any group's schemas |
| CSCH-EXEC-REQ-062 | §46, §47 | Cross-cutting | Each of the 11 implementation groups requires independent verification before the next group begins; no group combines all families into one unverified phase; the 6-layer validation model's authority boundary (only Layer 6 may assert authority) is preserved throughout every group | Layers 3–6 (all future) | 1–11 | Phase-gate audit: confirm each group's independent-verification report exists and is clean before the next group's implementation commit | All groups, sequentially |

### 51.3 Cross-reference to CSCH-INV-1..15

Every `CSCH-INV` invariant (135Z §34) is covered by at least one
`CSCH-EXEC-REQ` row above at its single-document-visible boundary, with the
remainder of each invariant's guarantee explicitly assigned to Layer 4 in
that row's "Semantic dependency" column: `CSCH-INV-1` (migration-epoch
binding) → REQ-014; `CSCH-INV-9` (CAS-rejection on stale digest) → REQ-052;
`CSCH-INV-14` (no dual `published`/`verified` without conflict record) →
REQ-054/REQ-059; `CSCH-INV-15` (journal hash-chain integrity) → REQ-056. The
remaining invariants map similarly to the family-specific rows in §51.2; no
`CSCH-INV` entry is renumbered or redefined by this mapping (§0.3).

---

## 52. Contract verdict

**EXECUTABLE SCHEMA CONTRACT FROZEN WITH PREREQUISITES — READY FOR
INDEPENDENT VERIFICATION**

Rationale for "WITH PREREQUISITES" rather than an unqualified "FROZEN": this
document independently re-derives and fully publishes the 62-item
verification matrix (§51), resolving the **publication gap** that F-135Z-3
identified. However, because the original "62" figure was never itself
substantiated by a real enumerated list anywhere in this repository's
history (135Z published 12 of a claimed 62; 136A and 136B never published
more), this document's independently-derived 62-item matrix must itself be
**independently re-verified by Phase 136D** before F-135Z-3 can be
considered closed beyond this contract's own self-assessment. This is the
single carried-forward prerequisite (**PREREQUISITE-136C-2**, §53) blocking
an unqualified "FROZEN" verdict. It does **not** block contract freeze
itself, and it does **not** re-open any other section of this document.

Contract freeze does not authorize implementation. No implementation group
(§46) may begin until Phase 136D completes.

---

## 53. Findings

| ID | Title | Source | Family | Authority impact | Concurrency impact | Recovery impact | Exactly-once impact | Impl. group | Verification group | Latest acceptable resolution phase | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CONFIRMED-136C-1 | Digest shape is bare 64-char lowercase hex, no `sha256:` prefix, deliberately diverging from a prefixed form suggested in this phase's originating instructions, in favor of the repository's actual existing implementation | §11 | Shared | None | None | None | None | 1 | 1 | 136C (resolved here) | CONFIRMED |
| CONFIRMED-136C-2 | The "62-item verification matrix" figure was never substantiated by an actual enumerated list anywhere prior to this document; this document's 62 is an independent derivation, not a confirmation of a pre-existing but unpublished list | §51.0 | Cross-cutting | None | None | None | None | — | — | 136D | CONFIRMED |
| PREREQUISITE-136C-1 | Full production-integrity recovery procedure for un-quarantining and resuming production remains deferred | §30 | QuarantineRecord | Indirect (quarantine cannot yet be operationally resolved) | None | Yes — blocks recovery-journal `recovery_action` completion for quarantine-originated entries | None | 11 | 11 | Before any live Stage 3 cutover (not before schema implementation) | PREREQUISITE |
| PREREQUISITE-136C-2 | The independently re-derived 62-item matrix (§51) requires independent re-verification by Phase 136D before F-135Z-3 is considered fully closed | §51.0, §52 | Cross-cutting | None | None | None | None | — | — | 136D | PREREQUISITE |
| NON-BLOCKING-136C-1 | Timestamp pattern's 2-digit seconds component does not special-case leap seconds (`:60`); no known producer of these records is expected to emit one | §13 | Shared | None | None | None | None | 1 | 1 | Any future implementation group, non-urgent | NON-BLOCKING |
| DEFERRED-136C-1 | `schema_id` const values for each of the 16 standalone files are named descriptively in this document (e.g. `authority_state`) but not yet minted as the final production string constants — inherited from F-135Z-4/F-136B-4 | §7.1, §35 | All 16 standalone | None | None | None | None | 1–11 | 1–11 | First implementation group that instantiates each file | DEFERRED |
| DEFERRED-136C-2 | CAS-expectation embedding (row 10) remains untested against a genuinely concurrent writer scenario — inherited from F-135Z-5/F-136B-5 | §24 | CasExpectation | Yes — CAS is the core concurrency-safety mechanism | Yes | None | None | 6, 7 | 6, 7 | First implementation group that exercises concurrent writers (post-schema, at behavioral-implementation time) | DEFERRED |

No **CONFIRMED-Blocking** or **BLOCKING** finding exists in this phase. Both
`PREREQUISITE` findings are scoped to future milestones (live cutover;
Phase 136D respectively), not to schema-contract completeness itself.

---

## No-implementation proof

- No production source changed. `git diff --name-only` for this phase's
  commits touches only: `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`,
  `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`,
  `tasks/active/**`/`tasks/done/**`, and `.pcae/phase-completion-metadata.json`
  / `.pcae/phase-completion-report.md`.
- No test source changed.
- No executable JSON schema was added or changed. `schemas/cltr_cutover/`
  does not exist on disk. `schemas/` outside `schemas/repository_intelligence/`
  (pre-existing, unrelated) contains nothing new.
- No schema fixture was added.
- No Python typed model was added. `src/pcae/cltr/authority/` does not
  exist.
- No validator was implemented.
- No schema registry was implemented.
- No authority resolver was implemented.
- No authority-state persistence was implemented.
- No authority pointer was implemented or changed.
- No cutover request, readiness package, authorization, candidate,
  certification, publication attempt, conflict record, or recovery journal
  was created.
- No authority epoch changed. Production authority remains `legacy`.
- No CLTR authority was created.
- No legacy authority was demoted.
- No legacy authority was retired.
- No production behavior changed.
- No execution capability was introduced.

Runtime remains **Observed**, maximum capability remains **observe**,
execution availability remains **unavailable** — reconfirmed by
`pcae runtime inspect` at both the start and end of this phase's work.

---

## Required validation (re-run at phase end)

- `pcae health` — passed.
- `pcae check` — passed.
- `pcae status coherence` — passed.
- `pcae doctor task-memory` — passed.
- `pcae push check` — re-run before finalization.
- `pcae runtime inspect` — Observed / observe / execution unavailable, unchanged.
- `source ~/.config/pcae/telegram.env` + `pcae notify status` — Telegram
  configured, enabled, ready for outbound delivery on phase completion.
- `pcae phase-report reconcile --phase-id 136B` (read-only) — reconciled,
  clean.
- `pcae phase-report reconcile --phase-id 136A` (read-only) — conflict,
  disclosed as historical evidence only, not repaired, not redispatched.

No implementation test suite (fast_green, full unmarked suite) is claimed to
have been exercised for schema-specific behavior in this phase, because no
schema, model, validator, or fixture exists yet to test. The existing
fast_green baseline (4391/4391) is unaffected by a documentation-only diff
and is not re-claimed here as evidence of anything beyond "no source or test
file was touched."

---

## Recommended next phase

**136D — Stage 3 Companion Executable Schema Contract Independent
Verification**

Independent verification must re-derive (not merely re-read) the §51 matrix,
confirm or dispute the 62-item count, confirm every `CSCH-EXEC-REQ` row's
traceability to a real contract section, and confirm the two `PREREQUISITE`
findings' scoping before any executable-schema implementation group (§46)
may begin. Do not begin executable-schema implementation before 136D
completes.

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. CLTR-CUTOVER-001, CLTR-CUTOVER-SCHEMAS-001, and
CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 define future behavior and future data
contracts only. 136C froze an executable-schema contract only. No executable
schema or fixture was added. No Stage 3 typed model, schema loader,
registry, or validator was implemented. No authority resolver, authority
state, or authority pointer was implemented or changed. No cutover request,
readiness package, authorization, candidate, certification, publication
attempt, conflict record, or recovery journal was created. No authority
epoch changed. No CLTR authority was created. No legacy authority was
demoted. No legacy authority was retired. No production behavior changed. No
execution capability was introduced. Runtime remains Observed, maximum
capability remains observe, and execution availability remains unavailable.
