# Phase 136Y: Stage 3 Typed Authority Model Implementation Plan

## 1. Purpose and boundaries

This phase transforms the already-frozen Stage 3 typed-model architecture
and contract (`CLTR-CUTOVER-SCHEMAS-001` v1.0 Sec.43/Sec.44, independently
verified at Phase 136A) into an implementation-ready, bounded,
dependency-ordered plan, incorporating Phase 136X's ambiguity register and
hazard analysis as binding constraints. It is a **planning and
contract-translation phase only**.

Not implemented by this phase, confirmed by direct repository inspection
before and after drafting: typed record models, dataclasses, Pydantic
models, attrs models, serializers, parsers, semantic validators, derived
views, repositories, persistence, resolvers, runtime authority behavior,
or lifecycle integration. No production dependency was added. No schema
file under `src/pcae/schema_resources/cltr_cutover/` was modified. This
phase produces exactly one artifact class: documentation (the plan
itself) plus routine governance/tracking-file updates.

## 2. Binding-source hierarchy

Precedence chain applied throughout, identical in structure to 136X's own
chain and to every implementation-plan phase preceding it:

```
Frozen primary contract
  CLTR-CUTOVER-SCHEMAS-001 v1.0 (Phase 135Z, "Sec.44" typed-model sequence)
  CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 (Phase 136C)
        v
Verified contract repairs
  none outstanding against either contract above
        v
Verified architecture
  Phase 136B (executable-schema architecture); Phase 135Z Sec.2-Sec.42
  (typed-authority architecture, embedded in the same contract document)
        v
Verified implementation plan / review
  Phase 136E (executable-schema implementation plan, the direct analogue
  this phase follows in kind); Phase 136X (final review, ambiguity
  register, hazard analysis, next-phase selection)
        v
Governed phase contracts
  136F-136W (executable-schema implementation/verification pairs)
        v
Operator prompt (this phase's instructions)
```

**Document-name substitution note.** The operator prompt lists document
names that do not all exist verbatim under those exact filenames. Mapped
substitutions, by content:

| Prompt-named source | Actual document(s) found |
|---|---|
| CLTR-001 v1.0 | Not a standalone file; referenced from within `PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md` Sec.0.1 and implemented as `src/pcae/cltr/schema.py`/`src/pcae/cltr/models.py`. |
| CLTR-SCHEMA-001 v1.0.1 | Same as above; not a standalone doc file — referenced from Sec.0.2 of the same freeze document; implemented as `src/pcae/cltr/schema.py`, `src/pcae/cltr/enums.py`, `src/pcae/cltr/canonicalization.py`, `src/pcae/cltr/digest.py`. |
| CLTR-CUTOVER-001 v1.0 | `docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md`. |
| CLTR-CUTOVER-SCHEMAS-001 v1.0 | `docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md` (this is the primary source for Sec.3-4). |
| CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 | `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`. |
| Stage 3 Companion Schemas and Typed Authority Model Contract | Same as `CLTR-CUTOVER-SCHEMAS-001` row above. |
| Phase 136A verification | `docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_INDEPENDENT_VERIFICATION.md` (the operator prompt's "136A" is this document; the repository's own `136A`-numbered doc is the companion-schema contract's independent verification, matching the prompt's description of it). |
| Phase 136B architecture | `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_ARCHITECTURE.md`. |
| Phase 136C contract freeze | `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`. |
| Phase 136D independent verification and repairs | `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_INDEPENDENT_VERIFICATION.md`. |
| Phase 136E executable-schema implementation plan | `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`. |
| Executable-schema implementation/verification docs through 136W | `docs/PHASE_136_{COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE,AUTHORITY_CORE_SCHEMA,REQUEST_AND_READINESS_SCHEMA,AUTHORIZATION_AND_CANDIDATE_SCHEMA,PUBLICATION_SCHEMA,RECOVERY_SCHEMA,NOTIFICATION_MARKER_RECEIPT_*,COMPATIBILITY_STATE_QUARANTINE_RECORD_SCHEMA}_{IMPLEMENTATION,INDEPENDENT_VERIFICATION}.md` (136H-136W). |
| Phase 136X final review and next-layer readiness | `docs/PHASE_136_EXECUTABLE_SCHEMA_TRACK_FINAL_REVIEW_AND_NEXT_LAYER_READINESS.md`. |
| PFN-001 | Not a standalone file; referenced from Sec.0.4 of the companion-schema freeze document — implemented as `certify_notification_transition()` and the `.last-notified.json` marker mechanism. |
| PFR-001 | Not a standalone file; referenced from Sec.0.5 — implemented as the `PhaseReport` artifact/trust pipeline (`src/pcae/core/phase_reports.py`), which also governs `.pcae/phase-completion-report.md`. |
| Current PCAE architecture and roadmap | `docs/ARCHITECTURE.md`, `PROJECT_STATUS.md`. |

No document content was fabricated; every substitution above is a
same-content, different-filename mapping, confirmed by reading each
mapped document's own text (Sec.0.1-0.7 of the companion-schema freeze
document explicitly states which prior contracts are "not standalone doc
files").

No conflict was found between this prompt and the frozen primary
contract. Where this prompt's illustrative package layout, group
numbering, or phase-ID scheme differs from what the frozen contract or
136X actually specifies, Section 7/23/24 below resolve the difference in
favor of the frozen contract, documented as a discrepancy, never silently
substituted.

## 3. Exact typed-model contract derivation

Independently re-derived from `CLTR-CUTOVER-SCHEMAS-001` v1.0 Sec.44 (the
sole normative source — Sec.43 defines only the executable-schema
sequence, already fully implemented at 136A-136W), cross-checked against
Sec.3-42 (enums, identity, canonicalization, digest, temporal, unknown-
field, error vocabulary, authority disclosures) and 136X's hazard
analysis (Sec.6 of the 136X document):

| Topic | Contract-derived requirement | Implementation consequence |
|---|---|---|
| Model purpose | A constructed model instance asserts only "this JSON was well-formed against schema X at version Y and can be represented without loss" — never operational truth. | No model method may return or imply authority, readiness, or success. |
| Authority status | Every companion record's `authority_disclosure.is_authoritative` is schema-pinned `const: false`; no typed model may override this locally. | Models expose `is_authoritative` as a literal `False`-valued field, never computed, never settable. |
| Immutability | §44: "every model is frozen/immutable after construction." | `dataclass(frozen=True)` (or equivalent) at every level; no mutation API. |
| Wire fidelity | §44: model "never has fields the schema does not define, and vice versa"; round-trip exactness implied by "creates no lifecycle meaning" plus the executable-schema track's own `additionalProperties: false` discipline. | 1:1 field mapping per schema (Section 27 conformance matrix); no renaming, no silent coercion. |
| Validation on construction | §44: "strict — unknown required-field absence and authority-bearing unknown-optional fields both raise"; "every enum field validated ... at construction time, not deferred." | Construction path is `from_dict()`/`from_validated_dict()` over an already-schema-validated payload (Section 16); enum/identity/reference shape re-checked at the type-construction boundary, not merely trusted from schema validation. |
| Serialization | §44 implies round-trip via the reused canonicalization/digest modules; no new serialization module authorized. | `to_dict()` reuses `pcae.cltr.canonicalization` ordering/formatting rules unchanged. |
| Deserialization | §44: constructor "accepts an explicit `schema_version`... no implicit latest-version default." | Every model's construction entry point requires an explicit version argument; no default-latest fallback. |
| Absent vs null | Contract §30: "for authority-bearing families, `null` is never ambiguous with absent," with one narrow, explicitly-scoped exception (`CutoverRequest`'s own optional fields, §6.3). | Models must not collapse absent and null to the same Python `None`; Section 9 defines the sentinel design required to preserve this distinction generically, while special-casing the one narrow exception only where it is contractually named. |
| `_extensions` | §30: preserved verbatim under a reserved `_extensions` key for evidentiary/historical (Tier 2) families only, never interpreted, never merged into a recognized field. | Section 10 defines an opaque, order-preserving, deep-copied extension-mapping type used only on the Tier 2 families named in Section 4. |
| Enum coercion | §3, §30: "fail-closed for every enum ... without exception ... no permissive 'unknown/other' catch-all." | `Enum` subclasses with exact frozen wire values; construction raises on any other string, no case-folding. |
| Digest handling | §44: "reuses `pcae.cltr.digest`'s `compute_dict_digest`-equivalent unchanged; no new digest module." Contract §27: digest fields are shape-checked only at Layer 2/3, never silently recomputed to "fix" a mismatch. | Models store digest strings as opaque, pattern-validated values; digest *computation*, if planned at all, lives in a separate pure utility that delegates to `pcae.cltr.digest`, never inside `__init__`. |
| Reference resolution | §44: "a `record_reference` field stays a reference, not a resolved object"; contract §1/§40: a valid reference "never implies the referenced record exists ... or that publication succeeded." | Reference-typed fields hold id+digest(+family) tuples only; no model method fetches, dereferences, or existence-checks a reference. |
| Semantic validation | Contract §47 six-layer stack (Layer 3 = typed-model construction, confirmed unchanged by 136X Sec.7); typed models occupy Layer 3 exclusively. | No cross-record check, no repository lookup, no authority-epoch comparison inside any model class. |
| Runtime authority (forbidden) | Contract §1, §35, §47 Layer 6; 136X Sec.6's governing invariant restated verbatim in this prompt. | Section 22 defines the import-boundary isolation the package must satisfy; no production lifecycle/notification/marker/receipt/publication/recovery module may import the typed-model package in this phase or the group phases immediately following it. |

## 4. Model inventory

Base rule (contract §44, restated): **one immutable value type per
schema**, in Sec.43's group sequence (mapped 1:1 onto the executable-
schema groups actually implemented, 136X Sec.1's corrected numbering
`{1,2,3,4,5,8,9,10,11}` — there is no Group 6/7 to account for, and Group
9 remains schema-less by design). Shared definitions get typed
representations only as embedded fields of a record model, never as
independent top-level models with their own `record_id`.

| Schema family | Proposed model | Nested models | Union branches | Deferred fields | Group |
|---|---|---|---|---|---|
| `AuthorityEpoch` | `AuthorityEpoch` | `RecordEnvelope`, `epoch_reference` (nullable, self-referential), `generation_reference` (nullable) | none — single shape | none | 2 |
| `AuthorityState` | `AuthorityState` | `RecordEnvelope`, `generation_reference` | none | none | 2 |
| `CutoverRequest` | `CutoverRequest` | `RecordEnvelope` | none — but see Section 9 for the contract's one named absent-vs-null relaxation (§6.3) applying to this family's own optional fields only | none | 3 |
| `ReadinessPackage` | `ReadinessPackage` | `RecordEnvelope`, ordered evidence-array value objects | none | none | 3 |
| `HumanAuthorization` | `HumanAuthorization` | `RecordEnvelope`, `principal_identifier`-typed field | none | none | 4 |
| `CutoverCandidate` | `CutoverCandidate` | `RecordEnvelope`, embedded `CasExpectation` | none | none — the family's own known gaps (`NON-BLOCKING-136N-6/-7`, generic `stage2_generation_reference`) are field-typing decisions, not deferred-shape gaps (Section 13) | 4 |
| `Certification` | `Certification` | `RecordEnvelope`, embedded `CasExpectation` | none | none | 4 |
| `PublicationAttempt` | `PublicationAttempt` | `RecordEnvelope`, embedded `CasExpectation` | none | none | 5 |
| `PublicationEvidence` | `PublicationEvidence` | `RecordEnvelope` | one discriminated union on `PublicationState`-adjacent outcome shape if the schema's own conditional requires it (verified against the executable schema at implementation time, not invented here) | none | 5 |
| `ConcurrencyConflict` | `ConcurrencyConflict` | `RecordEnvelope`, dual epoch/request references | none | none | 8 |
| `RecoveryJournalEntry` | `RecoveryJournalEntry` | `RecordEnvelope`, chain-digest reference | none | none | 8 |
| `NotificationAuthorityBinding` | `NotificationAuthorityBinding` | `RecordEnvelope` | possible branch on delivery-state per NON-BLOCKING-136T-1 disclosure — verified, not invented, at implementation time | none | 10 |
| `MarkerAuthorityBinding` | `MarkerAuthorityBinding` | `RecordEnvelope` | possible branch on marker duplicate-state per NON-BLOCKING-136T-2/-3 | none | 10 |
| `FinalizationReceiptAuthorityBinding` | `FinalizationReceiptAuthorityBinding` | `RecordEnvelope`, conditional trio (`generation_reference` always; `publication_evidence_reference`+`marker_reference` conditionally required together, per NON-BLOCKING-136T-6) | one branch: `receipt_state == "finalized"` requires the trio; represented as an invariant-checked single model with optional fields plus a documented `__post_init__` shape check, not a discriminated union, since the branching is a required-together constraint, not an alternate shape (Section 20) | `staleness_check` — **opaque JSON, DEFERRED-136T-1** (Section 11) | 10 |
| `CompatibilityState` | `CompatibilityState` | `RecordEnvelope`, local 2-value `role` enum (`compatibility`/`historical`, NON-BLOCKING-136V-2) | one conditional: `compatibility_mode == "legacy_retired"` requires `retirement_state` (schema `if/then`, mirrored as a model invariant) | `retirement_state` — **opaque JSON, DEFERRED-136V-1** (Section 11) | 11 |
| `QuarantineRecord` | `QuarantineRecord` | `RecordEnvelope`, generic `object_reference` (no family restriction, NON-BLOCKING-136V-6) | none | none — `reason_code` only, per Section 13 (no `quarantine_reason` alias) | 11 |
| Group 9 (reconciliation) | **no model** — `HistoricalAuthorityReference` is explicitly a runtime-only typed model per contract §23/§35/§37, not backed by an executable schema; **out of scope for this implementation plan**, which covers schema-backed models only. A future, separately governed phase may plan `HistoricalAuthorityReference` once the reconciliation function itself is authorized. | — | — | — | none (schema-less by design, 136X Sec.1) |

**Total: 16 schema-backed models across 8 implementation groups**
(`{2,3,4,5,8,10,11}` for record families, plus Group 1 for shared
components below — 7 groups of record models plus one shared-core group,
matching the 136X-corrected group set exactly). No model is created for a
"Group 6" or "Group 7" — those numbers were never contract-allocated
(136X Sec.1); no model is invented to fill the gap. `CasExpectation` (row
10 of the companion-schema contract's §2 inventory) is **not** a
standalone top-level model — it is a nested value object embedded at
exactly the three sites the executable schema embeds it
(`CutoverCandidate`, `Certification`, `PublicationAttempt`), matching
`shared/references.schema.json`'s own embedding-only design.

## 5. Shared typed-component inventory

| Component | Source schema | Used by |
|---|---|---|
| `RecordEnvelope` | `shared/envelope.schema.json` (`companion_envelope`) | every one of the 16 record models |
| `RecordIdentity` (`record_id` value type) | `shared/identity.schema.json` (`record_identity`, `generation_identity`, `principal_identifier`, `migration_epoch`, `phase_identity`, `transition_identity`) | every model; family-specific identifier wrapper types per Section 13 |
| `RecordDigest` (`record_digest` value type) | `shared/digest.schema.json` (`sha256_hex` and its six named aliases) | every model; digest-typed fields distinguish `record_digest`/`referenced_record_digest`/`generation_digest`/`pointer_digest`/`journal_entry_digest` as distinct wrapper types over the same underlying shape, preventing cross-purpose mixing at the type level |
| `RecordReference` | `shared/references.schema.json` (`record_reference`) | every model with a cross-record pointer |
| `EpochReference` | `shared/references.schema.json` (`epoch_reference`) | `AuthorityEpoch` (predecessor), any epoch-scoped family |
| `GenerationReference` | `shared/references.schema.json` (`generation_reference`) | `AuthorityEpoch`, `AuthorityState`, `CasExpectation`, `QuarantineRecord.object_reference` when `object_type == "generation"` |
| `CasExpectation` | `shared/references.schema.json` (`cas_expectation`) | `CutoverCandidate`, `Certification`, `PublicationAttempt` (embedded, never standalone) |
| `AuthorityDisclosure` | `shared/limitations.schema.json` (`authority_disclosure`) | every model, always with `is_authoritative` pinned `False` |
| `Limitations` | `shared/limitations.schema.json` (`limitations_array`/`limitation_entry`) | every model |
| `ReasonCode` (enum) | `shared/failures.schema.json` | `Certification`, `QuarantineRecord`, and any other family whose executable schema references it |
| Seven shared enums (`AuthorityKind`, `AuthorityRole`, `MigrationStage`, `GenerationRole`, `PublicationState`, `RecoveryState`, `CompatibilityMode`) plus `RecordFamily` | `shared/enums.schema.json` | as referenced per family; **not** centralized further — the contract's own family-local enums (RequestState, ReadinessState, etc.) remain scoped to their owning record models, matching the schema layer's own non-centralization choice |
| `Timestamp` | `shared/envelope.schema.json` (`timestamp`) | every model's `created_at` and any family-local timestamp field |
| `OpaqueJsonValue` | none (this plan's own [NEW] component, Section 11) | `staleness_check`, `retirement_state`, and any future analogous deferred field |
| `AbsentSentinel` | none (this plan's own [NEW] component, Section 9) | any optional field on an authority-bearing family where absent must be distinguished from an explicit permitted null |
| `ExtensionMapping` | envelope `_extensions` (present on Tier 2 families only: `compatibility_state`, `quarantine_record`, and any other family whose executable schema declares `_extensions` — confirmed per-schema at implementation time, not assumed uniformly) | Tier 2 families only |

No inheritance hierarchy is introduced across these components beyond
what a plain composition (each record model *has-a* `RecordEnvelope`,
*has-a* `AuthorityDisclosure`, etc.) requires; family-specific models are
not subclasses of a shared "Record" base class, per the instruction to
prefer composition and preserve family-specific differences.

## 6. Technology decision

**Decision: frozen standard-library `dataclasses`, `dataclass(frozen=True,
slots=True)` where the target Python floor (`>=3.9`, per `pyproject.toml`)
allows, continuing the existing `src/pcae/cltr/models.py` precedent
(`SharedInputRevision`'s "deep-frozen fields" pattern, cited directly by
contract §44).**

Evaluation:

| Option | Verdict | Rationale |
|---|---|---|
| Frozen stdlib `dataclasses` | **Selected** | Zero new dependency (`pyproject.toml` declares only `jsonschema>=4.18,<5` as a runtime dependency; no `pydantic`, `attrs`, or similar appears anywhere in `src/pcae` today — confirmed by repository-wide grep, zero hits); matches the explicit, already-implemented `src/pcae/cltr/models.py` precedent contract §44 itself cites approvingly ("this review recommends continuity with that precedent"); full control over absent-vs-null representation via explicit sentinel fields (Section 9) rather than a third-party library's own `None`-handling conventions; deterministic, dependency-free serialization achieved by reusing `pcae.cltr.canonicalization`/`pcae.cltr.digest` unchanged, as §44 mandates; no risk of a validation library silently coercing/normalizing values contrary to the fail-closed contract (§30). |
| Pydantic | Rejected | Introduces a new runtime dependency the contract does not authorize (§44 explicitly states library choice is "not specified by the contract," and no acceptance criterion in this phase authorizes adding one); Pydantic's default coercive validation (e.g. permissive type coercion, alias handling, `None`-defaulting) actively works against the fail-closed, no-coercion, absent-vs-null-preserving requirements (Section 8, Section 9) unless heavily configured against its own defaults, at which point most of its ergonomic benefit is lost while its dependency-weight cost remains. |
| `attrs` | Rejected | Same new-dependency objection as Pydantic; offers no capability stdlib `dataclasses` lacks for this contract's needs (frozen instances, `__post_init__`-style validation hooks are available in both); would create an inconsistency with the existing `src/pcae/cltr/models.py` precedent for no compensating benefit. |
| Manually implemented immutable classes (no dataclass decorator) | Rejected | More boilerplate than `dataclass(frozen=True)` for identical guarantees (immutability, `__eq__`, `__repr__`, `__hash__` control); no offsetting benefit; increases maintenance burden without increasing safety. |
| `TypedDict` for wire-only representations | Rejected as the primary model type, but retained as a *documentation/type-hint* aid only for pre-validation wire payloads (a `TypedDict` is not runtime-enforced and provides no immutability, no `__post_init__` invariant hook, and cannot represent the absent-vs-null sentinel cleanly — a plain `dict` already serves that pre-validation stage; introducing `TypedDict` as the actual model type would silently reintroduce mutability and coercion risk). | — |
| Hybrid domain/wire representations (two classes per family: a wire DTO and a domain model) | Rejected as unnecessary duplication for this phase's scope — contract §44 calls for "one dataclass ... per schema," not two; a single frozen dataclass with an explicit `from_dict`/`to_dict` pair (Section 16/17) already separates the wire boundary from the in-memory representation without doubling the class count. | — |

Dependency impact: **zero**. `pyproject.toml`'s `dependencies` list
remains `["jsonschema>=4.18,<5"]`; the `dev` optional group remains
`pytest`/`pytest-xdist`. This plan does not propose adding
`pytest-timeout` or any property-based-testing library either (Section
26). Python-version support: `dataclasses` is stdlib since 3.7, well
within the `>=3.9` floor; `slots=True` on dataclasses requires 3.10+, so
this plan specifies it as a **should**, not a **must**, until the floor
is confirmed compatible at implementation time (a compatibility check,
not a design change, belongs to the first implementation group).

## 7. Package layout

```
src/pcae/cltr/authority/
    __init__.py                  # public surface only, no wildcard export
    sentinels.py                 # ABSENT sentinel (Section 9)
    opaque.py                    # OpaqueJsonValue (Section 11)
    enums.py                     # 7 shared enums + RecordFamily (Section 5)
    identity.py                  # RecordIdentity family of wrapper types (Section 13)
    digest.py                    # RecordDigest family of wrapper types (Section 14) -- wraps, does not reimplement, pcae.cltr.digest
    references.py                # RecordReference, EpochReference, GenerationReference
    cas_expectation.py           # CasExpectation embedded value object
    limitations.py               # Limitations, AuthorityDisclosure
    envelope.py                  # RecordEnvelope
    extensions.py                # ExtensionMapping (Section 10)
    errors.py                    # typed-model error hierarchy (Section 29)
    serialization.py             # shared to_dict/from_dict primitives (Section 17)
    authority_core.py            # Group 2: AuthorityEpoch, AuthorityState
    request_readiness.py         # Group 3: CutoverRequest, ReadinessPackage
    authorization_candidate.py   # Group 4: HumanAuthorization, CutoverCandidate, Certification
    publication.py               # Group 5: PublicationAttempt, PublicationEvidence
    recovery.py                  # Group 8: ConcurrencyConflict, RecoveryJournalEntry
    bindings.py                  # Group 10: NotificationAuthorityBinding, MarkerAuthorityBinding, FinalizationReceiptAuthorityBinding
    compatibility_quarantine.py  # Group 11: CompatibilityState, QuarantineRecord
```

Placed as `src/pcae/cltr/authority/`, sibling to the existing
`src/pcae/cltr/` modules (`digest.py`, `canonicalization.py`,
`enums.py`, `models.py`), exactly as contract §44 specifies — **not**
inside `src/pcae/schema_resources/` (schema resources remain pure JSON
Schema documents plus the manifest; no typed-model code is ever placed
there) and **not** merged into the existing `src/pcae/cltr/` flat module
list (the new package boundary keeps Stage 3 typed models independently
importable from Stage 0-2 modules, per §44's own stated rationale).

Import-cycle prevention: `authority_core.py` through
`compatibility_quarantine.py` (the 7 record-group modules) import only
from the shared-core modules listed above them and from each other in
strictly increasing group order (mirroring the executable-schema DAG,
136X Sec.2); no shared-core module imports any record-group module. No
record-group module is imported by `src/pcae/cltr/*.py` (the Stage 0-2
modules) — the dependency direction is one-way, authority package
depending on the existing `pcae.cltr.canonicalization`/`pcae.cltr.digest`
utilities, never the reverse. This one-way rule is also the substance of
the runtime-isolation test planned in Section 22.

Public export surface (`__init__.py`): the 16 record-model classes plus
the shared value types explicitly needed by any authorized external
caller (test code, future observation-only tooling) — no
`from .module import *` wildcard; each export is named explicitly.

## 8. Wire-fidelity rules

Every rule below is a **must-not** unless stated otherwise, matching the
prompt's own enumeration and contract §26/§27/§30:

- Field names: exact, no renaming (`reason_code` stays `reason_code`,
  never `quarantine_reason` — Section 13).
- Record-type/schema-family constants: stored verbatim from the schema's
  `const` values (`record_type`, `schema_id`), never re-derived or
  normalized.
- Field ordering: canonical serialization reuses
  `pcae.cltr.canonicalization`'s existing lexicographic key-sort rule
  unchanged (§26) — models do not re-implement ordering.
- String values: stored exactly as parsed; no trimming, case-folding, or
  Unicode re-normalization beyond what `pcae.cltr.canonicalization`
  already performs at the serialization boundary (NFC, §26) — construction
  itself performs no additional normalization.
- Enum spelling/case: exact member match only (Section 12).
- Timestamps: stored as the original wire string (Section 15); no
  timezone/format conversion at construction.
- Digest strings: stored as opaque 64-character lowercase-hex strings;
  format-validated (regex match), never recomputed to "correct" a
  mismatch (Section 14).
- Family-specific identifiers: preserved via distinct wrapper types
  (Section 13), never silently widened to a bare `str`.
- Arrays/object shape: preserved as authored, including declared-empty
  arrays/objects (`limitations: []`, `staleness_check: {}`), which are
  valid, meaningful values, not omissions.
- Absent fields: represented distinctly from `None` (Section 9).
- Explicit nulls where the schema allows them: preserved as `None`, never
  silently dropped or converted to absent.
- `_extensions`: preserved verbatim, in original key order, with deep-
  copied nested values (Section 10).
- Opaque evidence / opaque deferred fields: preserved byte-for-byte as
  parsed JSON (Section 11).
- Nested unknown values the schema permits (inside `_extensions` or an
  opaque field): never interpreted, promoted, or flattened.

No implementation may: rename fields; trim strings; change enum case;
convert absent to null or null to absent (outside the one contract-named
exception, Section 9); drop nulls; sort or dedupe arrays unless the
family's own contract section names a canonical sort key (contract §26
names exactly two: `ReadinessPackage`'s `unresolved_findings`/
`entry_point_evidence`, and `RecoveryJournalEntry`'s `entry_sequence`
ordering — no other array is ever reordered); infer defaults; compute
missing values; replace malformed values (construction raises instead,
Section 29); coerce scalar types; or discard `_extensions`.

## 9. Absent-versus-null design

**[NEW component, this plan]: `ABSENT` sentinel.**

For every optional field across all 16 families, construction must
distinguish "field not present in the wire payload" from "field present
with an explicit `null`" wherever the executable schema itself
distinguishes them (i.e., wherever the field is not `required` and the
schema's type union permits `null`). Contract §30's default rule for
every authority-bearing family is that `null` is **never** treated as
equivalent to absent; the **one** contractually named relaxation is
`CutoverRequest`'s own optional fields (§6.3) — nowhere else.

Design:

- A module-level singleton `ABSENT = _AbsentType()` (single instance,
  `sentinels.py`), distinct from Python's `None`.
- Every optional field's declared type is `Union[T, None, AbsentType]`
  with `default=ABSENT` (not `default=None`) at the dataclass level,
  except within `CutoverRequest`'s specifically named relaxation, where
  the schema itself already permits the wire-level collapse and the
  model may use ordinary `Optional[T] = None` for exactly those fields,
  documented inline with a citation to §6.3.
- **Equality**: `ABSENT != None` and `ABSENT != ABSENT`'s own type check
  is `is ABSENT`, not `==`, to avoid accidental truthy/falsy confusion;
  `__eq__` on the containing dataclass compares field-by-field including
  sentinel identity.
- **Serialization**: `to_dict()` omits any field whose value `is ABSENT`
  from the output mapping entirely (matching wire "absent field" shape);
  a field valued `None` serializes as JSON `null` explicitly.
- **Deserialization**: `from_dict()` maps a missing dict key to `ABSENT`
  and an explicit `key: null` entry to `None` — the distinction is made
  by `key in payload` (presence) versus `payload[key]` (value), never by
  `payload.get(key)` alone (which cannot distinguish the two cases).
- **Repr**: `ABSENT.__repr__()` returns `"<absent>"`, visually
  distinguishable from `None` in debugging output and never logged as if
  it were a real value.
- **Test coverage**: every optional field gets at minimum three fixture
  variants — value present, explicit `null` (where schema-permitted),
  and absent — with a round-trip assertion for each (Section 25).
- **Nested-field handling**: a nested value object embedded inside a
  record (e.g. `CasExpectation`) applies the same rule recursively for
  any of its own optional sub-fields, though contract §24's design
  (every `CasExpectation` field is unconditionally required, "no
  wildcard on missing expected value") means this component in practice
  has no optional fields to apply the sentinel to — documented, not
  assumed.

Ordinary `None` is never reused to carry both meanings on any field where
the schema itself distinguishes absent from null.

## 10. `_extensions` design

Applies only to Tier 2 families (confirmed per 136X Sec.3: at minimum
`compatibility_state`, `quarantine_record`; every other family's Tier
1/Tier 2 classification is re-confirmed against the executable schema at
implementation time, not assumed from this plan alone, since `publication_
attempt` was explicitly noted as excluded/Tier 1 despite superficially
resembling a Tier 2 family).

- **Value type**: `ExtensionMapping`, a thin immutable wrapper over a
  `Mapping[str, Any]` where `Any` is itself constrained to JSON-
  representable values only (str/int/float/bool/None/list/dict, no
  Python-specific types).
- **Mutability**: the wrapper itself is immutable (no `__setitem__`); its
  construction performs a deep copy of the input mapping so a caller's
  later mutation of their own source dict cannot retroactively alter a
  constructed model.
- **Key ordering**: preserved exactly as parsed (Python `dict` preserves
  insertion order; no re-sorting at construction — re-sorting occurs only
  at the canonical-serialization boundary via
  `pcae.cltr.canonicalization`'s existing lexicographic rule, applied
  uniformly to the whole document including `_extensions`, matching
  contract §26).
- **Nested value preservation**: deep-copied recursively; nested
  dicts/lists inside an extension value are themselves preserved verbatim
  and never interpreted.
- **Canonical serialization**: `_extensions` participates in the record's
  overall canonical JSON output exactly like any other field — no special
  exclusion, no special ordering rule beyond the uniform one.
- **Forbidden canonical-field overrides**: `maxProperties: 32` (per the
  executable schema) is enforced at construction; an `_extensions` key
  that collides with a canonical field name is rejected at construction
  (raise, never silently shadow or promote).
- **Opacity**: extension values remain opaque `Any` — a typed model never
  assigns semantic meaning to any extension key or value, never promotes
  one into a canonical field, never treats an extension as authority,
  never interprets an embedded lifecycle instruction, never executes an
  embedded command, and never resolves an embedded URL.
- **Key validation**: only the schema's own key-shape constraint (if any)
  is enforced; no semantic key validation is added.
- **Secret scanning**: none is implemented or claimed — Section 30
  explicitly prohibits claiming secret detection this phase does not
  build.
- **Hashability**: `ExtensionMapping` is **not** hashable (a `Mapping` is
  not hashable by default and this plan does not force it to be, per
  Section 19) — any containing record model with an `_extensions` field
  is therefore itself unhashable unless a future phase adds an explicit,
  justified hash strategy.

## 11. Opaque/deferred-field design

**[NEW component, this plan]: `OpaqueJsonValue`.**

Applies to exactly two fields today, per 136X's ambiguity register
(Section 32 below): `FinalizationReceiptAuthorityBinding.staleness_check`
(`DEFERRED-136T-1`) and `CompatibilityState.retirement_state`
(`DEFERRED-136V-1`).

- **Current accepted wire shape**: both are pinned to an empty-shape
  placeholder object (`additionalProperties: false`, no `properties`) at
  the executable-schema layer — the *only* value either field can
  currently validly hold on the wire is `{}` (when present at all).
- **Executable-schema constraint**: yes — both fields are already
  constrained to accept only `{}` by the frozen schema (not merely
  "any object"); a typed model must not accept a wire payload the schema
  itself would already reject, so `OpaqueJsonValue` in practice validates
  against exactly the same empty-object shape the schema enforces today,
  while remaining structurally ready (as a general-purpose wrapper type,
  not a field-specific one) to hold a richer shape without a model-class
  rewrite once a contract erratum defines one.
- **May the typed model narrow it further?** No — narrowing beyond what
  the schema already enforces would be inventing a shape the frozen
  contract does not define, explicitly prohibited by the operator prompt
  and by 136X Sec.6's hazard table ("Hiding contract ambiguity behind
  permissive types").
- **Preserved as opaque JSON**: yes, unconditionally, until an erratum
  exists.
- **`OpaqueJsonValue` type required**: yes — a single shared wrapper type
  (`opaque.py`), not two field-specific types, since both fields have an
  identical disposition (opaque object, currently empty-only, format
  unresolved).
- **Must implementation wait for contract repair?** No — per 136X Sec.12,
  this is a "soft limitation," not a hard blocker; the two model classes
  (`FinalizationReceiptAuthorityBinding`, `CompatibilityState`) may be
  implemented now with these two fields typed `OpaqueJsonValue`,
  round-trip-provable at their current `{}`-only shape.
- **Round-trip preservation provable?** Yes, at the current shape — an
  empty object round-trips trivially and losslessly; the moment a real
  shape is defined, the wrapper type's job is to keep preserving whatever
  JSON value it is given verbatim (deep copy in, deep copy out), so
  round-trip safety does not depend on knowing the eventual shape.
- **Prerequisite blocker classification**: **not** a blocker for
  implementing the two owning model families at their current schema-
  enforced shape. It **would** become a blocker only if a future phase
  tried to assign semantic meaning to either field before a contract
  erratum exists — out of scope for this plan and for the first
  implementation group.

`OpaqueJsonValue` construction never invents structure the frozen
contract does not define; it stores exactly the parsed JSON value
(constrained today to `{}` by the schema itself) and returns it verbatim
on serialization.

## 12. Enum strategy

**Representation: Python `Enum` subclasses (`str, Enum` mixin for direct
JSON-string compatibility), one class per shared/family-local enum,
exact wire-value members only** — matching contract §44 ("Python `Enum`
subclasses with exact wire-value members, no permissive fallback
member").

- **Case preservation**: enum members are declared with the exact
  lowercase `snake_case` wire spelling as both the Python member name
  (uppercased per PEP 8 convention, e.g. `AuthorityKind.LEGACY`) and the
  member **value** (`"legacy"`, unchanged case) — the value, not the
  name, is what round-trips to the wire.
- **No automatic normalization**: construction does `EnumClass(raw_str)`
  (exact `ValueError` on mismatch, including case mismatch — no
  `.lower()`/`.upper()` applied before lookup).
- **No unknown-value acceptance**: matches contract §3/§30's fail-closed
  rule for every enum without exception — construction raises
  (`TypedModelConstructionError`, Section 29) rather than falling back to
  a sentinel/"unknown" member.
- **Deterministic serialization**: `to_dict()` emits `enum_member.value`,
  always the plain wire string, never the Python member name.
- **Safe equality**: `Enum` members compare by identity/value
  automatically; no override needed.
- **No implicit authority meaning**: an enum class is a closed value
  vocabulary only; no `Enum` method returns a boolean "is this
  authoritative" — that determination, where it exists at all, belongs
  to a future Layer 4/5/6 component, never to the enum type itself.
- **No truthiness-based lifecycle decisions**: no code anywhere in this
  package tests `if some_enum_field:` to infer a lifecycle branch; every
  branch is an explicit value comparison.
- **Wire enums vs semantic state machines vs operational authority
  states, distinguished**: the seven shared enums (Section 5) are wire
  vocabularies only; contract §33's "allowed transition" tables (e.g.
  `AuthorityKind`'s `legacy → cltr` once-only rule) are **not** enforced
  by the enum type itself or by any model's `__post_init__` — transition-
  legality is explicitly a Layer 4/5 cross-record concern (contract §47),
  out of scope for a single-record typed model to check. A model
  construction call succeeding proves only that the *value* is a member
  of the closed set, never that the *transition* to that value was
  legal.

## 13. Identifier and reference strategy

Dedicated, distinct wrapper types are used for every identifier/reference
kind the schema layer itself already distinguishes (Section 5's
`RecordIdentity`/`RecordDigest`/`RecordReference`/`EpochReference`/
`GenerationReference` family), rather than a single bare `str` used
everywhere:

- `RecordId` — generic `record_id` shape (`^[a-z][a-z0-9-]{7,127}$`).
- `GenerationId` — distinct wrapper over the same charset/length rule as
  `RecordId`, kept as a separate type specifically so a generation
  identifier "can never silently masquerade as a generic record_id"
  (quoting `identity.schema.json`'s own stated purpose), matching Python
  type-checker-visible distinctness even though the two are runtime-
  identical strings.
- `MigrationEpochToken`, `PhaseIdentity`, `TransitionId`,
  `PrincipalIdentifier` — thin wrappers over their respective patterns.
- `RecordReference` (id+digest+family tuple), `EpochReference`
  (migration_epoch [+ optional epoch_digest]), `GenerationReference`
  (generation_id+generation_digest) — composite reference types, never
  collapsed into a bare ID.

**Prohibited on every reference-typed field, unconditionally**: automatic
target lookup, repository scanning, existence checks on construction,
authority resolution, reference dereferencing, network access, implicit
conversion across record families. A `record_reference`'s `record_family`
tag is validated only as a member of the closed `RecordFamily` enum
(Section 12) — never cross-checked against an actual referenced record's
real family (that is Layer 4, per contract §1/§40's "a valid reference
never implies the referenced record exists").

Family-specific references remain distinguishable exactly where the
schema distinguishes them: `expected_authority_epoch` and
`expected_request_reference` and `expected_certification_reference`
inside `CasExpectation` are each typed as `RecordReference` narrowed (at
the Python type-annotation level, via a `Literal["authority_epoch"]`-
style discriminant on the wrapper, not via three separate classes) to
their required `record_family` constant — matching the schema's own
`allOf` + `const` restriction pattern (Section 4/5 of the shared
`references.schema.json` file). `stage2_generation_reference`
(`CutoverCandidate`) and `object_reference` (`QuarantineRecord`) are
typed as the **generic, unrestricted** `RecordReference` (no family
narrowing), matching `NON-BLOCKING-136N-7`/`NON-BLOCKING-136V-6`'s
disclosed disposition exactly — this plan does not invent a "generation"
`RecordFamily` member the schema layer does not have.

## 14. Digest strategy

Contract §44/§27: models **store** digest strings; they do not compute or
verify them as a side effect of construction. This plan's disposition:

- Every digest-typed field (`record_digest`, `referenced_record_digest`,
  `generation_digest`, `pointer_digest`, `journal_entry_digest`) is a
  distinct wrapper type over the shared 64-character lowercase-hex shape
  (`sha256_hex`), format-validated at construction (regex match — the
  same pattern the schema already enforces, re-checked because
  construction accepts already-schema-valid input but does not *trust*
  that fact blindly per contract §44's "strict... at construction time,
  not deferred").
- Construction **never** computes a missing digest, replaces an incorrect
  digest, verifies external evidence, claims cryptographic trust, or
  mutates content to make it match a digest — matching 136X Sec.6's
  explicit hazard/no-go pairing.
- **If digest computation is planned at all** (it is not required by any
  acceptance criterion of this phase, but is anticipated as a near-future
  need for round-trip/determinism tests, Section 25): it lives in a
  separate, pure, observation-only utility function (e.g.
  `authority_digest.compute_record_digest(model) -> str`, calling
  `pcae.cltr.digest.compute_dict_digest`-equivalent unchanged, per
  contract §44), never inside `__init__`/`from_dict`, and never invoked
  automatically by any model method.
- Digest fields on a constructed model are exactly the string the wire
  payload supplied — proof of well-formed shape only, never proof of
  correctness (Section 3's "Model purpose" row applies identically here).

## 15. Timestamp strategy

**Representation: exact original wire string, preserved verbatim,
alongside no separate parsed-datetime field in v1 of this package** —
chosen because contract §28.2 states no timestamp in this contract
"establishes or is required for authority," every timestamp is
"evidence-only... without exception," and models must not "prove event
timing truth or ordering" (operator prompt, Section 15 heading). Storing
only the exact string avoids inventing a parsing/precision/timezone
policy this plan has no authority-bearing need to build yet.

- **No timezone normalization**: the schema's own pattern
  (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) already
  constrains every timestamp to explicit-`Z`-suffixed UTC with 0-6
  fractional digits; a model stores that string exactly as received,
  never converting `Z` to `+00:00`, never truncating or padding
  fractional-second digits, never re-deriving a different precision.
- **A future phase MAY add** a derived, non-authoritative
  `datetime.datetime` convenience accessor computed from the stored
  string on demand (a pure, cached-or-not property, never a stored
  mutable field) — **not required or built by this plan**, and if added,
  it must never replace the original string as the field of record for
  serialization (serialization always emits the original string, never a
  re-formatted datetime).
- **Ordering claims**: none — contract §28.2 explicitly relies on
  `attempt_sequence`/`entry_sequence` integer counters for ordering
  guarantees, never wall-clock timestamps; typed models make no ordering
  claim based on any timestamp field.
- **Missing-time behavior**: an absent non-mandatory timestamp is valid
  (`ABSENT` sentinel, Section 9); an absent mandatory timestamp is a
  construction-time error (`invalid_schema`-equivalent, Section 29).

## 16. Construction pipeline

Five distinct layers, matching contract §47 and 136X Sec.7's confirmed
boundary, none collapsed into another:

```
1. Raw bytes
        v  strict JSON parsing (pcae.schema_runtime.json_parser, existing, unchanged)
2. Parsed JSON value (plain dict/list/scalar tree)
        v  executable-schema validation (pcae.schema_runtime.validation, existing, unchanged)
3. Schema-validated dict
        v  typed-model construction  <-- THIS PLAN'S SCOPE
4. Immutable model instance
        v  (future, NOT this plan) local model invariant validation (Layer 4, observation-only, contract-authorized cross-record checks only)
        v  (future, NOT this plan) cross-record semantic validation (Layer 5)
        v  (future, NOT this plan, requires separate authorization) authority-truth evaluation (Layer 6)
```

Construction API for every model class: a `from_dict(payload: dict,
*, schema_version: str) -> Self` classmethod (contract §44's explicit
"constructor accepts an explicit `schema_version`... no implicit
'latest version assumed' default"). `from_dict` performs: (a) schema-
version dispatch (reject any version this model class does not
explicitly recognize — `unsupported_version`, Section 29); (b) per-field
extraction applying the absent/null/enum/reference/digest/opaque rules of
Sections 9-15; (c) enum/identity/digest/reference re-validation at the
type-construction boundary (not blind trust of upstream schema
validation, per contract §44); (d) any locally-authorized structural
invariant the *record's own* executable schema already encodes as an
`if/then` (e.g. `CompatibilityState`'s `legacy_retired` ⇒
`retirement_state` required, `FinalizationReceiptAuthorityBinding`'s
`finalized` ⇒ trio-required) — restated as a `__post_init__` check purely
because it is already a Layer-2/3 single-document shape rule the schema
itself enforces, not a new Layer 4/5 rule being introduced. No
cross-record check is ever added inside `from_dict`/`__post_init__`.

`from_json(raw: bytes, *, schema_version: str) -> Self` is a thin
convenience wrapper composing strict JSON parsing + schema validation +
`from_dict`, useful for tests and future offline tools, but does not
collapse the layer boundaries — each sub-step remains independently
callable and independently testable.

No model constructor accepts a *pre-validated-elsewhere* payload without
re-checking the fields this package itself is responsible for (enum
membership, digest shape, reference shape) — construction never blindly
trusts that "schema validation already happened so this must be fine,"
consistent with contract §44's "not deferred" instruction.

## 17. Serialization pipeline

`to_dict(self) -> dict` on every model, deterministic:

- **Field inclusion**: every field whose value is not `ABSENT`.
- **Absent-field omission**: an `ABSENT`-valued field is omitted from the
  output mapping entirely (Section 9).
- **Explicit null preservation**: a `None`-valued field (where the schema
  permits null) serializes as JSON `null`.
- **Enum serialization**: `.value` (wire string), never the Python member
  name (Section 12).
- **Nested-model serialization**: recursive `to_dict()` on every embedded
  value object (`RecordEnvelope`, `AuthorityDisclosure`, `CasExpectation`,
  reference tuples).
- **Extension serialization**: `_extensions`'s wrapped mapping is emitted
  as a plain dict, deep-copied at emission time so the caller cannot
  mutate the model's internal state through the returned dict.
- **Opaque-field serialization**: `OpaqueJsonValue` emits the exact JSON
  value it was constructed with, deep-copied at emission time.
- **Array ordering**: preserved as stored (construction already preserved
  authored order per Section 8; no additional reordering at
  serialization except where `pcae.cltr.canonicalization`'s own rule
  applies at the byte-canonicalization stage for digesting purposes,
  which is a distinct downstream step from `to_dict()`'s own plain-
  mapping output).
- **Dictionary ordering**: `to_dict()`'s own key order follows the
  model's field-declaration order (readable, stable); a **separate**
  canonical-byte-production step (`to_canonical_bytes()`, if authorized —
  see below) applies `pcae.cltr.canonicalization`'s lexicographic sort
  for digest-input purposes specifically, not for `to_dict()`'s general
  output.
- **Canonical byte production**: `to_canonical_bytes(self) -> bytes`
  reuses `pcae.cltr.canonicalization` unchanged; **only authorized** as a
  thin pass-through wrapper around the existing function, never a new
  canonicalization implementation.

**Round-trip test requirement** (Section 25 elaborates): for every
fixture, `from_dict(to_dict(from_dict(payload)))  ==  from_dict(payload)`
under Python `==` (structural dataclass equality) **and**
`to_dict(from_dict(payload))`'s JSON-serialized form matches the
original payload's schema-canonicalized form field-for-field, including
opaque-field byte-for-byte equality.

## 18. Immutability model

- **Top-level**: every dataclass is `frozen=True`.
- **Nested nested data**: `RecordEnvelope`, `AuthorityDisclosure`,
  `CasExpectation`, and every reference tuple type are themselves frozen
  dataclasses (recursively immutable), not plain mutable dicts wrapped in
  a frozen outer class.
- **Immutable collections**: array-typed fields (e.g.
  `ReadinessPackage`'s evidence arrays, `limitations`) are stored as
  `tuple`, not `list`, at the model boundary — construction converts an
  input `list` to `tuple` explicitly; `_extensions`' mapping is wrapped in
  a read-only `MappingProxyType` (or equivalent) rather than left as a
  plain mutable `dict`, specifically because contract-instruction
  "prevent mutation from invalidating record digest, identity, authority
  disclosure, conditional branch consistency, nested evidence" applies to
  exactly this class of field.
- **Defensive copies**: performed at construction (input collections
  copied before wrapping/freezing) and at `to_dict()`/opaque-field access
  (output copies so a caller cannot mutate internal state) — both
  directions covered, closing the "nested dicts/arrays remain mutable"
  loophole the prompt specifically warns against, rather than leaving it
  undocumented.
- **Hashability**: not forced (Section 19) — `eq=True` remains dataclass
  default, `unsafe_hash` is never set on a class containing an
  `_extensions`/opaque field.
- **No mutation methods**: no `set_*`/in-place mutator exists on any
  model; a "changed" record is always a new object, constructed via
  `from_dict` on a new payload (or, for narrow convenience, a documented
  `dataclasses.replace()`-based explicit copy operation, which itself
  produces a wholly new frozen instance, never mutates the original).
- **No post-construction mutation for convenience**: none is added; if a
  future consumer needs a modified copy, it must call `from_dict` on
  modified wire data or `dataclasses.replace()` explicitly — no implicit
  builder/mutable-then-freeze pattern.

## 19. Equality and hashing

- **Equality**: full structural equality (`dataclasses.dataclass`'s
  default `__eq__`, field-by-field, including nested frozen value
  objects) — **not** identity-only, **not** record-ID-only, **not**
  canonical-wire-string equality (two models are equal only if every
  field, including `limitations` and `_extensions`, matches exactly).
  Record-ID equality is explicitly **not** treated as record equality —
  two instances with the same `record_id` but different `_extensions` (a
  legitimate, if unusual, wire scenario) are unequal Python objects, per
  the prompt's own instruction "do not assume record ID equality means
  record equality."
- **Hashability**: **not forced**. Any model class containing an
  `_extensions`/`OpaqueJsonValue` field remains unhashable (the default
  dataclass behavior when `eq=True` and any field is unhashable is itself
  unhashable, or `__hash__` is explicitly set to `None` where a
  `MappingProxyType`-wrapped field would otherwise appear hashable but
  its contents are not guaranteed to be) — the ten record families
  without `_extensions` **may** be hashable if every one of their fields
  is itself hashable (a determination made per-class at implementation
  time, not assumed uniformly here).
- **Digest equality is not a substitute for cryptographic verification or
  authority truth**: `record_digest` equality between two model instances
  is a plain string comparison with the same evidentiary weight as any
  other field comparison — it does not, by itself, prove the two records
  are cryptographically verified against their content (that would
  require the separate digest-computation utility of Section 14 to be
  invoked and compared, an explicit, opt-in call, never an implicit
  consequence of `==`).

## 20. Conditional-branch representation

Reviewed against contract §16 (family-local conditional-validation
tables) and the six families the prompt specifically names:

| Family | Branch kind | Representation | Rationale |
|---|---|---|---|
| Notification delivery-state | possible optional-field branch, verified against the executable schema at implementation time (`NON-BLOCKING-136T-1` disclosed a structural-consistency choice, not a branch shape) | single model, optional fields, `__post_init__` invariant if the schema's own `if/then` requires one | Preserves exact schema legality without inventing a state-transition executor; the schema-level conditional, if any, is restated, not extended |
| Marker duplicate branches | same treatment, per `NON-BLOCKING-136T-2/-3` | single model, optional fields | as above |
| Finalized receipt bundle | `receipt_state == "finalized"` ⇒ trio required (`NON-BLOCKING-136T-6`) | single model, optional fields + `__post_init__` trio-invariant | this is a required-together constraint, not an alternate shape — a discriminated union would over-model a same-shape/different-required-set situation |
| Compatibility state branches | `compatibility_mode == "legacy_retired"` ⇒ `retirement_state` required (schema `if/then`) | single model, optional field + `__post_init__` invariant restating the schema's own `if/then` | same reasoning |
| Quarantine record branches | `object_type` variants over a generic, unrestricted `object_reference` (`NON-BLOCKING-136V-6`) | single model, no union — the reference type itself is generic/untyped by family, matching the schema's own choice not to restrict it | inventing a union here would invent a restriction the schema explicitly does not impose |
| Publication/recovery conditional structures | reviewed per-schema at implementation time; no union anticipated beyond what `PublicationEvidence`'s own conditional (if any) requires | single model with optional fields unless the executable schema itself defines a `oneOf`/discriminated shape, in which case a discriminated union is used **only there** | matches the general rule below |
| Candidate/certification conditional structures | embedded `CasExpectation`, unconditionally required (no optional sub-fields, Section 13) | single model, embedded value object | no branching exists at the schema level to represent |

**General rule**: a discriminated-union model is used **only** where the
executable schema itself expresses a `oneOf`/mutually-exclusive-shape
constraint (verified per-schema at implementation time — this plan does
not assert in advance that any of the 16 families definitely requires
one, beyond the `PublicationEvidence` possibility flagged in Section 4).
Everywhere a family's conditionality is a "these fields are required
together under this condition" pattern rather than "the record has one
of several genuinely different shapes," a single model with optional
fields plus a `__post_init__` invariant is used instead — this restates
the schema's own single-document shape rule (a Layer 2/3 concern already
fully specified) without inventing a runtime state-machine executor.
Branch models represent wire alternatives only; no branch model or its
selection logic ever triggers a side effect, notification, or lifecycle
transition.

## 21. Validation-layer separation

The six-layer stack (contract §47, re-confirmed unchanged by 136X Sec.7):

1. Strict JSON parsing — existing, `pcae.schema_runtime.json_parser`,
   unchanged.
2. Executable-schema validation — existing, `pcae.schema_runtime.
   validation`, unchanged, Groups 1-11 (136A-136W), unchanged by this
   plan.
3. **Typed-model construction — this plan's exclusive scope.**
4. Local model invariant validation — only the narrow, schema-already-
   encoded `if/then` restatements named in Section 20; no new invariant
   is introduced beyond what the record's own executable schema already
   requires.
5. Cross-record observation-only semantic validation — **not
   implemented, not designed in detail by this plan** (Section 32
   references it only to classify findings' effect on it).
6. Authority-truth evaluation — **explicitly out of scope**, requires a
   future, separately authorized layer.

Forbidden inside any typed model class, matching the prompt's explicit
list and contract §47's boundary: checking referenced records exist,
comparing authority epochs, verifying publication succeeded, asserting
notification delivery, asserting marker existence, asserting receipt
finality, deciding compatibility, enforcing quarantine, or selecting
current authority. None of these appear in any model class this plan
specifies; Section 23's implementation-group acceptance criteria include
a grep-based check for this boundary at every group's independent
verification.

## 22. Runtime isolation

The `src/pcae/cltr/authority/` package must not be imported, in this
phase or the implementation groups immediately following it, by:
production lifecycle commands, finalization commands, notification
dispatch, marker creation, receipt creation, publication, recovery,
authority selection, the execution coordinator, the permission broker, or
the runtime decision engine.

**Planned (not implemented) repository-wide import-boundary test**: a
static test (e.g. AST-walk or `grep -R "from pcae.cltr.authority" src/pcae`
excluding `src/pcae/cltr/authority` itself and its own test directory)
asserting zero import edges from any production runtime module into the
new package. This test is specified as an acceptance criterion of Group 1
(Section 23) but is not written by this planning phase.

Until an explicit future authorized observation-only adapter phase exists,
typed models may be exercised only through: unit tests, explicit offline
developer tools/scripts, and isolated developer APIs — never through any
code path a production command invokes.

## 23. Implementation grouping

Optimized for dependency correctness and independent-verification
boundaries, traceable to but not identical in numbering to the schema
groups (schema Group 1 = shared core; typed-model Group 1 covers the same
shared core plus its own construction/serialization primitives, matching
136X's confirmed group set `{1,2,3,4,5,8,9,10,11}` with 9 remaining
schema-less/model-less by design):

| Group | Inputs | Outputs | Dependencies | Files | Tests | Acceptance criteria | Independent verification | Prohibited scope |
|---|---|---|---|---|---|---|---|---|
| 1 — Shared Core | Schema Group 1 (7 shared resources); Sections 5,7-19 of this plan | `ABSENT` sentinel, `OpaqueJsonValue`, 8 enum classes, identity/digest/reference wrapper types, `Limitations`/`AuthorityDisclosure`, `RecordEnvelope`, `CasExpectation`, shared `to_dict`/`from_dict` primitives, typed-model error hierarchy | none (foundation) | `sentinels.py`, `opaque.py`, `enums.py`, `identity.py`, `digest.py`, `references.py`, `cas_expectation.py`, `limitations.py`, `envelope.py`, `extensions.py`, `errors.py`, `serialization.py` | fixture-based unit tests per component (Section 25) | Every shared component round-trips; enum fail-closed proven; absent-vs-null proven; import-boundary test passes (Section 22); zero new dependency | 136Z (proposed) | No record-family model; no schema-runtime modification |
| 2 — Authority Core | Group 1; schema Group 2 | `AuthorityEpoch`, `AuthorityState` | Group 1 | `authority_core.py` | fixture-based unit tests; conformance matrix subset (Section 27) | Both models construct/serialize/round-trip against all Group-2 fixtures; `AuthorityKind` exact-match-only proven; no epoch-selection logic present (grep-verified) | 136AB (proposed) | No authority-epoch "current" selection logic |
| 3 — Request and Readiness | Group 1-2; schema Group 3 | `CutoverRequest`, `ReadinessPackage` | Groups 1-2 | `request_readiness.py` | as above, plus explicit test of `CutoverRequest`'s §6.3 absent/null relaxation | as above; the one named absent/null relaxation is proven distinct from every other family's default rule | 136AD (proposed) | No readiness-gate decision logic |
| 4 — Authorization and Candidate | Group 1-3; schema Group 4 | `HumanAuthorization`, `CutoverCandidate`, `Certification` | Groups 1-3 | `authorization_candidate.py` | as above, plus embedded `CasExpectation` round-trip test at all three embedding sites | as above; `CasExpectation`'s "no wildcard on missing expected value" proven (every field always required) | 136AF (proposed) | No authorization replay/expiry enforcement (that is a future runtime concern, not construction-time) |
| 5 — Publication | Group 1-4; schema Group 5 | `PublicationAttempt`, `PublicationEvidence` | Groups 1-4 | `publication.py` | as above, plus explicit `publication_uncertain` vs `conflict` distinctness test | as above; uncertainty never collapsed into failure, proven at the type level | 136AH (proposed) | No publication-success assertion |
| 6 — Conflict and Recovery | Group 1-5; schema Group 8 | `ConcurrencyConflict`, `RecoveryJournalEntry` | Groups 1-5 | `recovery.py` | as above, plus hash-chain digest-field round-trip (storage only, no chain-verification logic) | as above; chain *verification* explicitly absent (Layer 4, not this group) | 136AJ (proposed) | No chain-integrity verification logic |
| 7 — Authority Bindings | Group 1-6; schema Group 10 | `NotificationAuthorityBinding`, `MarkerAuthorityBinding`, `FinalizationReceiptAuthorityBinding` | Groups 1-6 | `bindings.py` | as above, plus `staleness_check` opaque round-trip test (`DEFERRED-136T-1`) | as above; `OpaqueJsonValue` proven for `staleness_check`; no delivery/marker/receipt truth asserted | 136AL (proposed) | No notification-dispatch, marker-write, or receipt-write logic |
| 8 — Compatibility and Quarantine | Group 1-7; schema Group 11 | `CompatibilityState`, `QuarantineRecord` | Groups 1-7 | `compatibility_quarantine.py` | as above, plus `retirement_state` opaque round-trip test (`DEFERRED-136V-1`) and `reason_code`-only test (no `quarantine_reason` alias accepted) | as above; `OpaqueJsonValue` proven for `retirement_state`; no compatibility/quarantine truth asserted; full 16-model conformance matrix (Section 27) closed | 136AN (proposed) | No compatibility resolution, no quarantine execution |

Numbering rationale (Section 24 elaborates the phase-ID scheme): typed-
model implementation groups are **not** renumbered to match the schema
groups' numeric labels (2,3,4,5,8,10,11) directly as typed-model "Group
2,3,4,5,8,10,11" — instead this plan uses **sequential Groups 1-8** for
the typed-model track specifically (Group 1 = shared core through Group 8
= compatibility/quarantine), because the typed-model track has its own
internal dependency order distinct from carrying forward schema-group gap
numbers that exist only for schema-file historical reasons (Group 9 has
no schema and needs no typed-model group at all; there is no reason to
also skip typed-model "Group 6/7/9" merely to visually rhyme with the
schema track's numbering, which was itself an artifact of an early
architecture draft per 136X Sec.1, not a load-bearing scheme worth
replicating exactly). The mapping table above's own first column
preserves full traceability to the schema group each typed-model group
depends on.

## 24. Future phase sequence

**Naming-precedent check performed**: grepped `git log --oneline -a` and
`docs/` for any existing `136Z`, `136AA`, `136AB`-style (or similar
multi-letter) phase identifier. **None found** — the repository's phase
numbering has never yet advanced past a single trailing letter (`136A`
through `136Y`, this phase being the last single-letter slot in the `136`
series). This plan therefore **establishes the convention explicitly**:
after `136Z`, the next phase ID continues as `136AA`, `136AB`, `136AC`,
... (two-letter suffix, same base-26 continuation logic English chapter/
appendix numbering commonly uses — `Z` is followed by `AA`, not by
wrapping back to `A` or by changing the numeric prefix), because (a) the
numeric prefix `136` still correctly identifies "the Stage 3 typed-
authority chapter of work," consistent with every phase since `136A`; (b)
incrementing to `137` would incorrectly suggest a new, unrelated
top-level phase number when this is still squarely inside the same
chapter the `136` prefix has tracked continuously since `136A`; (c) a
two-letter suffix is the minimal extension that avoids collision with any
existing single-letter ID.

Recommended sequence (all "(proposed)" — none begun by this phase):

| Phase ID | Title |
|---|---|
| 136Z | Stage 3 Typed Authority Model Shared Core Implementation |
| 136AA | Stage 3 Typed Authority Model Shared Core Independent Verification |
| 136AB | Authority Core Typed Model Implementation |
| 136AC | Authority Core Typed Model Independent Verification |
| 136AD | Request and Readiness Typed Model Implementation |
| 136AE | Request and Readiness Typed Model Independent Verification |
| 136AF | Authorization and Candidate Typed Model Implementation |
| 136AG | Authorization and Candidate Typed Model Independent Verification |
| 136AH | Publication Typed Model Implementation |
| 136AI | Publication Typed Model Independent Verification |
| 136AJ | Conflict and Recovery Typed Model Implementation |
| 136AK | Conflict and Recovery Typed Model Independent Verification |
| 136AL | Authority Bindings Typed Model Implementation |
| 136AM | Authority Bindings Typed Model Independent Verification |
| 136AN | Compatibility and Quarantine Typed Model Implementation |
| 136AO | Compatibility and Quarantine Typed Model Independent Verification |
| 136AP (or later) | Typed-Model Track Final Review and Next-Layer Readiness (analogous to 136X) |

**Cadence decision**: bounded implementation/verification pairs **per
group**, not one final verification after all eight groups — chosen over
the alternative (all-implementations-then-one-verification) because of
PCAE's own prior defect history in this exact repository (visible in
`git log`: nearly every phase from 136L onward required one or more
follow-up "repair phase-completion metadata... for finalization gate"
commits — 16+ such repair commits across 136L-136X alone), which is
direct, repository-specific evidence that bounded, independently-
verified increments catch problems the same phase's own self-review does
not, consistently. This is the same cadence 136A-136W already used for
the executable-schema track itself, so it is also the path of least
governance-novelty.

## 25. Test strategy

Every implementation group (Section 23) requires, at minimum, for each
model in that group:

- **Exact model inventory / field mapping**: a per-field
  presence/absence assertion against the schema's own field list
  (feeds Section 27's automated conformance test).
- **Strict constructor behavior**: valid-minimal fixture, valid-full
  fixture (every optional field populated), unknown-field-rejection
  fixture, unknown-enum-value-rejection fixture (contract §44's own
  "minimum fixture set," restated).
- **Absent-versus-null**: three-way fixture per optional field (Section
  9) — present / explicit-null (where schema-permitted) / absent.
- **Enum fidelity**: every enum member exercised at least once; one
  rejected-unknown-value case per enum field.
- **Opaque/deferred fields**: `{}`-shape round-trip for
  `staleness_check`/`retirement_state`.
- **`_extensions`**: populated-extension round-trip, empty-extension
  round-trip, extension-key-collision-with-canonical-field rejection.
- **Conditional branches**: one fixture per named branch in Section 20
  (both the required-together-present and required-together-absent
  legal states, plus one illegal partial-presence rejection case).
- **Nested immutability**: attempted mutation of a nested collection
  field raises/is structurally prevented (`tuple`/`MappingProxyType`).
- **Equality**: two structurally-identical instances compare equal; two
  instances differing only in `_extensions` compare unequal.
- **Serialization / deserialization / round-trip fidelity**: the
  `from_dict(to_dict(x)) == x` and canonical-byte-equality assertions of
  Section 17, for every fixture above.
- **Family-specific IDs / wrong-family rejection**: a reference tuple
  constructed with a mismatched `record_family` tag against a narrowed
  reference field (e.g. `expected_authority_epoch` given `record_family:
  "cutover_request"`) is rejected at construction.
- **Digest storage**: digest field stores the exact input string; a
  malformed digest string (wrong length/charset) is rejected.
- **Timestamp fidelity**: original string preserved exactly through
  round-trip, including fractional-second precision variants.
- **No coercion / no normalization / no default inference**: adversarial
  fixtures asserting these negatives explicitly (e.g. a boolean-typed
  field given `"true"` as a string is rejected, not coerced).
- **No reference resolution / no network / no filesystem mutation / no
  persistence / no authority / no execution**: instrumented tests (e.g.
  monkeypatching `socket`/`open`/`subprocess` to raise if invoked during
  construction/serialization) proving zero side effects.
- **Installed-wheel operation / package contents**: an isolated,
  installed-wheel-scoped smoke test importing `pcae.cltr.authority` and
  constructing one fixture per model, run outside the repository
  checkout (matching the executable-schema track's own precedent,
  136X Sec.16's "packaging/wheel/sdist-tagged tests").

**Independently authored verification tests required per group** (not
merely re-running the implementing phase's own tests) — matching the
136A-136W precedent of a separate implementation phase followed by a
separate independent-verification phase per group (Section 24).

## 26. Property-based-testing decision

**Not authorized this phase.** Property-based/generated testing (e.g.
`hypothesis`) would usefully cover: schema-valid object generation,
round-trip preservation across many random field combinations, absent/
null combination coverage, extension-preservation across random nested
structures, enum coverage, nested-immutable-value coverage, opaque-JSON
coverage, and conditional-branch coverage — all explicitly named by the
operator prompt as candidate uses. However, `hypothesis` (or any
property-based library) is **not currently a declared dependency**
(`pyproject.toml`'s `dev` group is `pytest>=8.0`, `pytest-xdist>=3.0`
only), and this phase's own acceptance criteria and no-go boundary
prohibit introducing a new dependency during planning. **Recommendation
for a future implementation-group phase to evaluate explicitly** (not
decided here): if adopted, it should be scoped to Group 1 (shared core)
first, since that is where combinatorial coverage (absent/null/enum
combinations) has the highest payoff per test authored.

**This plan specifies deterministic adversarial fixture coverage instead**
(Section 25's per-group fixture list), matching the executable-schema
track's own precedent (contract §44's "one canonical fixture set per
schema, covering at minimum..." — a deterministic, not generated,
strategy) and requiring no new dependency.

## 27. Schema-to-model conformance matrix

**Strategy** (not the matrix itself, which is an implementation-group-1
deliverable populated from the actual executable schema field lists, not
invented in advance by this planning phase): for every one of the 16
schema-backed families, a table of exactly this shape:

| Schema field | Model attribute | Wire type | Model type | Required | Null allowed | Opaque | Round-trip rule |
|---|---|---|---|---|---|---|---|

populated by directly reading each `records/*.schema.json` file's
`properties`/`required`/`additionalProperties` block (as this plan's own
Sections 4-15 already did at the family-summary level for a
representative sample: `quarantine_record.schema.json`'s `reason_code`,
`receipt_authority_binding.schema.json`'s `staleness_check`,
`compatibility_state.schema.json`'s `retirement_state`/`role`, each
directly inspected during this phase, Section 32).

**Automated conformance test requirement** (planned, not implemented):
a test that fails when (a) a schema field has no corresponding model
attribute; (b) a model attribute has no corresponding schema field; (c)
required-status differs between schema and model; (d) an enum's member
set differs between schema and model; (e) nullability differs; (f) model
serialization renames a field relative to its schema name; (g) a new
schema field appears with no model coverage (a drift-detection test,
run as part of every future group's independent verification, not only
at initial implementation, to catch schema changes made without a
corresponding model update).

**No production models are generated automatically from schemas** by
this plan or authorized by it — every model class is planned to be
hand-authored, matching contract §44's dataclass-per-schema instruction
literally, with the conformance matrix serving as a verification
artifact, not a code-generation input.

## 28. Packaging strategy

- **Wheel inclusion**: `src/pcae/cltr/authority/` is included via the
  existing `[tool.hatch.build.targets.wheel] packages = ["src/pcae"]`
  rule — no `pyproject.toml` change is required, since the new package is
  a subpackage of the already-included `src/pcae` tree; a **verification**
  (not a change) that the wheel actually contains the new modules is an
  acceptance criterion of Group 1's independent verification.
- **sdist inclusion**: covered by the existing `[tool.hatch.build.targets.
  sdist] include = ["src/pcae", ...]` scope (Phase 106D's bounded sdist
  fix) — again, verification only, no change needed.
- **Public vs private modules**: the 16 record-model classes plus the
  named shared value types (Section 7's `__init__.py` export list) are
  public; internal helper functions inside `serialization.py`/
  `errors.py` not named in `__init__.py` are private by convention
  (leading underscore where appropriate), not enforced by `__all__`
  alone.
- **Stable API surface**: the module layout of Section 7 is intended to
  be stable across the eight implementation groups (new modules are
  additive per group, no existing module is renamed mid-track).
- **Versioning**: model classes track `pyproject.toml`'s package version
  (`0.2.0` today) implicitly, with no independent versioning scheme of
  their own — a model's own `schema_version` field is a wire-data
  concept (Section 16), distinct from the package's own release version.
- **Schema-version compatibility**: each model's `from_dict` explicitly
  dispatches on `schema_version` (Section 16); a model built against a
  schema version it does not recognize raises `unsupported_version`
  (Section 29), never silently assumes latest.
- **Dependency declarations**: none added (Section 6, Section 26).
- **No checkout-path assumptions**: models take only in-memory
  dict/bytes input (Section 16); no model or its construction path reads
  any repository-relative path.
- **Isolated installed-wheel tests**: planned (Section 25's "Installed-
  wheel operation" row) for Group 1 onward, run outside the checkout,
  matching the executable-schema track's own packaging-test precedent.
- **No broad wildcard export**: `__init__.py` names every export
  explicitly (Section 7); `from pcae.cltr.authority import *` is not the
  intended usage pattern and is not what the module's `__all__` (if
  declared) would optimize for.

## 29. Error model

Future error categories (planned; the concrete exception classes are a
Group 1 deliverable, not created by this phase):

| Category | Trigger | Behavior |
|---|---|---|
| `StrictJsonParseError` | malformed raw bytes | reused unchanged from `pcae.schema_runtime.errors` — occurs upstream of typed-model construction entirely |
| `SchemaValidationError` | payload fails executable-schema validation | reused unchanged from `pcae.schema_runtime.errors` — occurs upstream |
| `TypedModelConstructionError` | [NEW, this package] a schema-valid payload nonetheless fails a typed-model-layer check (enum re-validation, digest-shape re-validation, reference-shape re-validation, absent/null misuse outside the one named relaxation) | raised, never downgraded to a warning |
| `UnsupportedSchemaVersionError` | [NEW] `from_dict`/`from_json` called with a `schema_version` the model class does not recognize | raised, no fallback to "latest assumed" |
| `UnknownModelFamilyError` | [NEW] a dispatcher (if one is later built) is asked to construct a family with no registered model class | raised |
| `AbsentNullMismatchError` | [NEW] a payload supplies `null` for a field where the schema forbids null but permits absence (or vice versa), outside `CutoverRequest`'s named exception | raised |
| `OpaqueValuePreservationError` | [NEW] internal invariant failure — an opaque field's round-trip produced a value unequal to its input (should be unreachable in a correct implementation; exists as a defensive internal-consistency check, not a user-facing validation path) | raised |
| `SerializationError` | [NEW] `to_dict`/`to_canonical_bytes` encounters an internal state inconsistency (e.g. a required field somehow holds `ABSENT`, which construction should have already prevented) | raised, defensive only |
| `RoundTripMismatchError` | [NEW, test-only, not a production error a caller would encounter in normal use — exists to make round-trip test assertions produce a specific, named failure rather than a bare `AssertionError`] | raised only within the test suite's own helper assertions |
| `TypedModelInternalInvariantError` | [NEW] a `__post_init__` structural check (Section 20) fails on a payload that passed schema validation — indicates either a genuine malformed input the schema itself under-constrains, or (rarer) a plan/schema drift bug | raised, never silently downgraded |

**Existing `src/pcae/schema_runtime/errors.py` reused unchanged** for
every Layer 1/2 concern (strict-parse, schema-validation); a **separate**
typed-model error hierarchy (`errors.py` in the new package, all
subclassing one `TypedModelError` base) is required for Layer 3 concerns,
because the existing hierarchy's exception classes are scoped to schema-
validation failures and do not (and should not) know about absent/null
sentinels, opaque-value preservation, or schema-version dispatch — a
Layer-3-specific concept set the Layer-1/2 hierarchy was never designed
to express.

Errors never: repair input, downgrade a failure to a warning silently,
create a default value in place of the failure, mutate repository state,
disclose secret-like field contents in their message text, or claim
authority truth in their message text.

## 30. Security and safe representation

- **No automatic logging of full model contents**: no model implements
  `__str__`/logging integration that dumps every field; `__repr__`
  (dataclass default) is acceptable for debugging but is not wired into
  any logging call by this plan.
- **Safe repr**: dataclass default `__repr__` is used as-is; no field is
  specifically masked, since this package handles no credential-bearing
  fields (`principal_identifier` is a non-secret identifier per
  `identity.schema.json`'s own description, not a credential).
- **No credential dumping into exceptions**: exception messages reference
  field *names* and *validation outcomes*, never raw field *values*,
  where a value could plausibly be sensitive (extension-map contents in
  particular are never echoed verbatim into an exception message).
- **No telemetry, no network, no environment-variable expansion, no URL
  fetching, no command interpretation**: none of these exist anywhere in
  the construction/serialization pipeline (Section 16/17); this is also
  covered by the instrumented no-side-effect tests of Section 25.
- **No secret-detection claim**: this plan does not implement or claim
  `_extensions`/opaque-field secret scanning (Section 10); a future phase
  would need to explicitly design and disclose such a feature before it
  could be claimed.
- **No redaction during canonical serialization**: `to_dict()`/
  `to_canonical_bytes()` never redact wire data — redaction would break
  fidelity (Section 8). If a future *display*-only helper is ever added
  (explicitly out of scope for this plan), it must be a wholly separate
  function from canonical serialization, never a mode/flag on the same
  function.

## 31. Performance considerations

- **Construction cost**: dominated by field-by-field validation
  (enum/digest/reference shape re-checks); expected O(field count) per
  record, no algorithmic concern at the record sizes this contract
  defines (bounded arrays, `maxProperties: 32` on `_extensions`, bounded
  free-text lengths throughout Section 8's shared components).
- **Deep-copy cost**: `_extensions`/opaque-field deep copies at both
  construction and access are bounded by the same `maxProperties`/
  length limits; no unbounded-size field exists anywhere in this
  contract's shared-core definitions.
- **Immutable-collection cost**: `tuple`/`MappingProxyType` construction
  is linear in collection size, negligible at these bounds.
- **Serialization cost**: linear in record size; canonical-byte
  production reuses the already-performance-reviewed
  `pcae.cltr.canonicalization` module unchanged.
- **Memory overhead**: one Python object per nested value (frozen
  dataclasses, not compact tuples) is a deliberate trade of a small
  per-instance memory overhead for type-safety and readability,
  consistent with the existing `src/pcae/cltr/models.py` precedent's own
  choice.
- **Repeated schema-validation cost**: `from_json` performs Layer 1+2+3
  validation on every call; a caller constructing many instances from
  already-schema-validated data should call `from_dict` directly
  (skipping re-parse, not re-validation — Section 16 still re-validates
  enum/digest/reference shape at Layer 3 regardless, deliberately, per
  contract §44's "not deferred" instruction).
- **Caching**: **none introduced**. No memoization of constructed model
  instances by ID/digest is planned, since any such cache would risk
  changing authority, freshness, or identity semantics by returning a
  stale cached instance instead of faithfully representing the payload
  actually supplied — explicitly prohibited by the operator prompt.
- **No benchmark implementation required or performed this phase** —
  performance risk here is assessed as low given the bounded field counts
  and array sizes this contract defines throughout; a future phase may
  add benchmarks if a real bottleneck is observed, not preemptively.

## 32. Finding dispositions

| Finding | Effect on model inventory | Effect on model field types | Effect on serialization | Effect on round-trip fidelity | Effect on implementation grouping | Contract repair required first? | Opaque handling sufficient? | Becomes Blocking during implementation? |
|---|---|---|---|---|---|---|---|---|
| NON-BLOCKING-136N-7 | None — `CutoverCandidate` model still built | `stage2_generation_reference` typed as generic, unrestricted `RecordReference` (Section 13) | None | None | None — stays in Group 4 | No | Yes — generic reference type is the sufficient disposition | No, provided no future group invents a "generation" family restriction the schema does not have |
| DEFERRED-136T-1 | None — `FinalizationReceiptAuthorityBinding` model still built | `staleness_check` typed `OpaqueJsonValue` (Section 11) | Verbatim `{}` round-trip only, until erratum | Provable at current `{}`-only shape | None — stays in Group 7 | No (soft limitation; erratum optional before *operationalizing* the field, not before typing it opaquely) | Yes, at current shape | **Yes, if a future phase begins runtime-authority work before an erratum exists** (136X's own explicit warning, restated here) — not Blocking for this plan or the planned implementation groups |
| repaired BLOCKING-136U-1 | None (already repaired, regression-tested, not reintroduced — confirmed by this phase's own fresh grep, Section 33) | None | None | None | None | No | N/A | No |
| NON-BLOCKING-136V-1 | None | None (informational — a documentation-scoping-tension finding about `phase_id`/`transition_id` exemption text, not a field-shape finding) | None | None | None | No | N/A | No |
| NON-BLOCKING-136V-2 | None — `CompatibilityState` model still built | local `role` field typed as a bare 2-value enum (`compatibility`/`historical`), distinct from the shared 7-value `AuthorityRole` type used for `authority_disclosure.authority_role` on the same record (Section 4) | None | None | None | No | N/A | No |
| NON-BLOCKING-136V-3 | None | None — confirms the `Sec.16` conditional applies to `authority_disclosure.authority_role`, not the local `role` field; the `__post_init__` invariant (Section 20) is written against the correct field per this disposition | None | None | None | No | N/A | No |
| NON-BLOCKING-136V-4 | None | `allowed_reads`/`component` inherit the executable schema's locally-decided bounds (no change at the typed-model layer beyond re-validating the same bound) | None | None | None | No | N/A | No |
| NON-BLOCKING-136V-5 | None — `QuarantineRecord` model still built | `reason_code` only; **no `quarantine_reason` alias** accepted by the canonical model (Section 13/33) | Serializes only as `reason_code` | None | None | No (cosmetic contract-text erratum only, does not block typing) | N/A | No |
| NON-BLOCKING-136V-6 | None — `QuarantineRecord` model still built | `object_reference` typed as generic, unrestricted `RecordReference` (Section 13, mirrors 136N-7's disposition) | None | None | None | No | Yes | No |
| DEFERRED-136V-1 | None — `CompatibilityState` model still built | `retirement_state` typed `OpaqueJsonValue` (Section 11) | Verbatim `{}` round-trip only, until erratum | Provable at current `{}`-only shape | None — stays in Group 8 | No (soft limitation, same reasoning as `DEFERRED-136T-1`) | Yes, at current shape | **Yes, under the identical condition as `DEFERRED-136T-1`** — not Blocking for this plan |
| CONFIRMED-136W-1 | None (contract-text-only, §9 file-count self-inconsistency) | None | None | None | None | No | N/A | No |
| CONFIRMED-136W-2 | None (confirms intentional group-numbering convention, informs Section 4/23's own group mapping directly) | None | None | None | Directly informs this plan's own Section 23 group table | No | N/A | No |
| NON-BLOCKING-136W-3 (full-suite stall) | None to model *design* | None | None | None | Section 33 defines per-group test-cadence handling; does not gate any group | No | N/A | No, low direct risk per 136X's own classification, re-confirmed this phase |
| All new 136X findings (README staleness correction, Groups-6/7-numbering clarification) | None — both are documentation/numbering clarifications already resolved by 136X itself, directly informing this plan's Section 1/4/23 framing | None | None | None | None | No (already resolved) | N/A | No |

No finding above is carried forward without an explicit implementation
consequence, per the operator prompt's instruction; `CONFIRMED-136W-1`
and `NON-BLOCKING-136V-1` are the two findings with the least direct
model-layer consequence, disclosed above as exactly that ("None" across
every column) rather than omitted.

## 33. Full-suite evidence limitation

The full unmarked suite has stalled four independently observed times
(136W ×3, 136X ×1, per 136X Sec.11). This phase's own regression evidence
(Section 36) adds a fifth observation, consistent with the prior four.
**This plan does not become a repair phase for that instability** — no
test-infrastructure investigation is performed here, matching the
operator prompt's explicit boundary.

For every future typed-model implementation/verification phase (Section
24), this plan requires the following test cadence, run and disclosed
exactly as it behaves (never described as "passed" if it stalls):

1. **Focused model tests** — the specific implementation group's own
   fixture-based unit tests (Section 25).
2. **Schema-runtime regressions** — the existing `cltr_cutover`/
   `schema_runtime` filtered suite (the same ~2062-test filter 136X used),
   re-run fresh, not reused from a prior phase's cached result.
3. **Fast Green** (`-m fast_green -n auto`) — the existing baseline
   (4391 passed as of 136X), re-run fresh.
4. **Bounded full-suite diagnostic** — attempted fresh under a hard time
   bound (240 seconds, matching 136X's own bound, unless a future phase
   has independent justification to change it); if it does not complete,
   this is disclosed as a non-blocking, expected, pre-existing condition,
   never claimed as a completed or passed run.
5. **Isolated package tests** — the Section 25/28 installed-wheel smoke
   test, once it exists (from Group 1 onward).

**A dedicated test-infrastructure stabilization phase is recommended, not
scheduled, by this plan** — consistent with 136X's own disposition —
**unless** a future group's own verification work becomes genuinely
unable to trust its results because of the stall (e.g. if the stall ever
began intersecting the new package's own test files specifically, rather
than remaining confined to the unrelated ~22,000-test broad collection).
That trigger condition, not a fixed phase number, is the gating criterion
this plan specifies for when such a phase becomes necessary.

## 34. Acceptance criteria

All of the following are met by this phase (each independently checked
before finalization, Section 36):

- Complete typed-model inventory derived (Section 4: 16 schema-backed
  models across 8 implementation groups; Group 9 explicitly excluded by
  design, not silently omitted).
- Every executable schema mapped to a model or explicitly excluded
  (Section 4's table; the exclusion is `HistoricalAuthorityReference`,
  documented as out of this plan's schema-backed scope, not silently
  dropped).
- Shared typed components identified (Section 5).
- Implementation technology selected and justified, zero new production
  dependency (Section 6).
- Wire fidelity fully specified (Section 8).
- Absent/null handling explicit (Section 9).
- `_extensions` preservation explicit (Section 10).
- `staleness_check` handling explicit (Section 11, `DEFERRED-136T-1`).
- `retirement_state` handling explicit (Section 11, `DEFERRED-136V-1`).
- Reason-field conflict has a model-level rule: `reason_code` only, no
  `quarantine_reason` alias, no convenience acceptance of both names
  (Section 13, Section 32's `NON-BLOCKING-136V-5` row).
- Enum behavior explicit (Section 12).
- Identifier/reference behavior explicit (Section 13).
- Digest behavior explicit (Section 14).
- Timestamp behavior explicit (Section 15).
- Construction/serialization pipelines explicit (Sections 16-17).
- Model immutability explicit (Section 18).
- Layer 3 boundaries explicit (Section 21).
- Runtime isolation explicit (Section 22).
- Implementation groups dependency-ordered (Section 23).
- Implementation/verification cadence defined (Section 24).
- Every future group has acceptance criteria (Section 23's table).
- No typed model implemented (confirmed, Section 36).
- No new production dependency introduced (confirmed, Section 36).
- No runtime behavior changes; no authority changes; runtime remains
  Observed / observe / unavailable (confirmed, Section 36).

## 35. No-go boundaries

Not implemented by this phase, confirmed by direct repository inspection
before finalization (Section 36): model classes, dataclasses, Pydantic
models, attrs models, serializers, parsers, factories, model fixtures,
cross-record validators, repositories, derived views, persistence,
authority resolution, compatibility resolution, quarantine execution,
publication execution, recovery execution, notification dispatch, marker
creation, receipt creation, lifecycle mutation, authority activation,
legacy demotion, legacy retirement, execution capability. No production
schema was changed (no genuine Blocking contract defect was independently
proven that would justify one — this phase found none).

The plan does not assign shapes to `staleness_check`/`retirement_state`
beyond "opaque JSON, currently constrained to `{}` by the frozen
executable schema" (Section 11). The plan does not propose auto-resolving
references, auto-verifying digests outside `pcae.cltr.digest` delegation,
or any authority-selection logic (Section 13, Section 14, Section 21 —
all explicitly excluded, Layer 6 out of scope).

## 36. Exact recommended next phase

**Recommended next phase: `136Z — Stage 3 Typed Authority Model Shared
Core Implementation`** (Section 23's Group 1, Section 24's sequence
table), because: this plan's own model inventory (Section 4) and shared-
component inventory (Section 5) are now bounded and dependency-ordered;
the technology decision (Section 6) requires no further architecture
work; the two deferred fields (Section 11) are safely typeable as opaque
JSON today, not a blocker to beginning Group 1; and the operator prompt's
own acceptance criteria for *this* phase (Section 34) are fully met
without requiring a contract-repair phase first (no Blocking finding
exists anywhere in Section 32's disposition table).

This phase does not begin 136Z.

---

## Verdict

**TYPED AUTHORITY MODEL IMPLEMENTATION PLAN COMPLETE — READY FOR FIRST
BOUNDED IMPLEMENTATION GROUP**

## Regression evidence (fresh, this phase)

See `.pcae/phase-completion-report.md` for the full disclosure; summary:
136X review-related and 136W independent-verification-related focused
tests, the complete `cltr_cutover`/`schema_runtime` filtered suite,
manifest/registry tests, packaging tests, and Fast Green were all
re-run fresh as evidence for this planning phase (no source code changed,
so no regression was possible in principle, but fresh re-runs were
performed rather than assumed, per the operator prompt's instruction).
The full unmarked-suite bounded diagnostic was attempted fresh and, as
expected and previously disclosed (`NON-BLOCKING-136W-3`), did not
complete within the bound — disclosed exactly as it behaved, not claimed
as passed. Grep-based no-model/no-validator/no-view/no-resolver checks
confirmed zero implementation hits (only disclosure prose), and no
`src/pcae/cltr/authority/` directory exists.

## No-go confirmation

No production schema was changed by this phase. No typed record model,
dataclass, or Pydantic model was implemented. No serializer, parser,
semantic validator, cross-record repository, or derived view was
implemented. No persistence, authority-state storage, or authority
pointer was implemented or changed. No compatibility resolver,
quarantine coordinator, publication coordinator, or recovery coordinator
was implemented. No current-authority or historical-authority lookup was
implemented. No cryptographic verification, runtime execution, or
lifecycle mutation occurred. No authority epoch changed; no legacy
authority was demoted or retired; no CLTR authority was created. No new
production dependency was introduced. Legacy lifecycle remains the sole
production authority; CLTR remains derivative; runtime remains Observed,
maximum capability remains observe, and execution availability remains
unavailable.
