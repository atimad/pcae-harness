# Phase 135I — Production CLTR Schema, Canonicalization, and Versioning Contract Freeze

**Phase class:** Contract Freeze (Track 135, tenth substantive phase)
**Scope:** Freeze the complete production wire schema and serialization contract for the Canonical Lifecycle Transition Record. Documentation and contract only. No production implementation, no shadow integration, no authority migration, no lifecycle behavior change, no prototype expansion.
**Predecessor:** 135H.2 — Lifecycle Recovery Hardening & Exactly-Once Promotion (production code; unrelated production-safety hardening, not a Track 135 architecture phase).
**Architecture predecessors this phase derives from:** CLTR-001 (135B, contract), 135C (independent verification of CLTR-001), 135D (Cross-Representation Invariant Architecture & State-Machine Verification), 135G (Read-Only Prototype Independent Verification), 135H (Production Integration & Legacy Authority Retirement Plan).
**Non-goal:** Begin 135J (Production CLTR Schema Contract Independent Verification) or any later Track 135 phase.

**Schema identifier declared by this document:** **CLTR-SCHEMA-001**, version **1.0.0**. This is a new identifier, distinct from CLTR-001. CLTR-001 remains the binding semantic contract; CLTR-SCHEMA-001 is the wire-format contract that satisfies it. Both are frozen and both remain in force; neither supersedes the other.

---

## 0. Reading this document

Every normative clause below is tagged with exactly one of three labels, per the assignment's explicit instruction to distinguish these:

- **[CLARIFICATION]** — restates or makes mechanically explicit a requirement CLTR-001, 135D, 135G, or 135H already established. No new semantic obligation is created.
- **[ENCODING]** — a production wire-format decision (field name, type, enum value, serialization rule) made by this phase to satisfy a semantic requirement that CLTR-001 deliberately left unencoded (per CLTR-001 §6.1, §6.3, §15.2). This is new, but it is a *representation* choice, not a *behavior* change.
- **[GUIDANCE]** — non-binding advice for a future implementation phase (135K+). Guidance clauses never gate conformance and never contradict a CLARIFICATION or ENCODING clause.

CLTR-001's own semantics are never modified by this document. Where this document appears to add a requirement CLTR-001 did not state, it is either traced to 135D/135G/135H (cited inline) or explicitly marked [ENCODING] as a wire-level choice within CLTR-001's already-frozen semantic envelope.

---

## 1. Schema identity

### 1.1 Identifiers [ENCODING]

| Field | Value | Immutable? |
|---|---|---|
| `schema_id` | `CLTR-SCHEMA-001` | Yes — never reassigned to a different schema family |
| `schema_family` | `pcae.cltr` | Yes — the dotted namespace root for every CLTR wire type |
| `schema_version` | `1.0.0` | No — bumped per §2; `1.0.0` itself, once published, is immutable in content |
| `contract_version` | `CLTR-001/1.0` | Yes for this schema version — the exact CLTR-001 version this schema conforms to; a future CLTR-001 version bump requires a new `schema_version`, never a silent reinterpretation under the same `schema_version` |
| `compatibility_id` | `pcae.cltr.v1` | No — bumped only on a breaking change (§2.3); distinct from `schema_version` so additive `1.x.y` releases can share one `compatibility_id` |
| `canonical_namespace` | `pcae.cltr.v1` | Same value as `compatibility_id` for `1.x`; kept as a separate field because a future major version's namespace and compatibility identifier could diverge (e.g., a namespace rename without a compatibility break, or vice versa) |

### 1.2 Immutability rule [CLARIFICATION]

Per CLTR-001 §5.2/§5.3 (identifier normalization discipline, generalized from the record's own identifiers to the schema's own identity): `schema_id` and `schema_family` are immutable for the life of this contract family. `schema_version` and `compatibility_id` are versioned per §2 below, but every published value, once released, is itself immutable — a released `schema_version` string is never reused for different content (CLTR-001 §14.1 item 2's "immutable once certified" principle, applied to the schema artifact itself).

### 1.3 Every record's identity binding [ENCODING]

Every produced CLTR record carries `schema_id`, `schema_version`, and `contract_version` as top-level fields (already required semantically by CLTR-001 §6.2 items 1–2; this section only fixes their field names and values). A record whose `schema_id` does not equal `CLTR-SCHEMA-001` is not a CLTR record under this contract and must be rejected before any further parsing is attempted (§4.4).

---

## 2. Versioning

### 2.1 Strategy [ENCODING]

Semantic versioning (`MAJOR.MINOR.PATCH`) applied to `schema_version`:

- **MAJOR** — any change that is not forward- or backward-compatible under §2.2 (field removal, type change, enum value removal, required-field addition to an existing state). Bumping MAJOR always bumps `compatibility_id`.
- **MINOR** — additive-only change (new optional field, new enum value that old readers can safely treat as unknown per §2.6, new representation binding). Never bumps `compatibility_id`.
- **PATCH** — clarifying documentation change to this schema contract with zero wire-format effect (e.g., fixing a typo in a field description). Never bumps `compatibility_id`, never requires a new reader/writer behavior.

### 2.2 Forward and backward compatibility [ENCODING]

- **Forward compatibility** (an older reader encountering a newer-MINOR record): the reader must successfully parse every field it recognizes and must preserve, but need not interpret, every field it does not recognize (§2.6). It must never fail solely because of the presence of additional recognized-family fields.
- **Backward compatibility** (a newer reader encountering an older, still-supported record): the reader must correctly interpret the older record's fields as they were defined at that `schema_version`, without requiring the older record to be rewritten. A newer reader must not silently assume a MINOR-added field's default meaning was already true of older records — absence is absence, not "false" or "empty" by inference (§6 below).
- Both directions are scoped to the same MAJOR version. Cross-MAJOR compatibility is never implicit (§2.7).

### 2.3 Additive fields [ENCODING]

A MINOR release may add: (a) a new optional field to an existing representation, (b) a new enumeration value to an existing enum where the enum's own evolution policy allows it (§9), (c) a new representation binding not previously defined. A MINOR release may never make a previously optional field required, never change an existing field's type, and never repurpose an existing field name for different semantics.

### 2.4 Deprecated fields [ENCODING]

A field may be marked `deprecated_since: <schema_version>` in this contract's field catalog without being removed. A deprecated field remains present in produced records for at least one full MAJOR version cycle, is still validated when present, and its removal is always a MAJOR change (§2.5). No field defined by this v1.0.0 baseline is deprecated as of this freeze.

### 2.5 Removed fields [ENCODING]

Field removal is always MAJOR. A removed field's name is never reused for a different meaning within the same schema family (`pcae.cltr`) — a retired field name is permanently retired, matching CLTR-001 §5.2 item 4's no-alias-reuse discipline applied to schema evolution.

### 2.6 Unknown field handling [ENCODING]

Unknown top-level and nested fields encountered during deserialization must be **preserved verbatim** (not discarded, not merged into a catch-all without provenance) and must **never be treated as authoritative** by the reader — this generalizes CLTR-001 §12.3's no-independent-reconstruction rule to the wire layer: an unrecognized field cannot silently become a new fact a consumer relies on. This matches 135G's prototype repair (§2.2 of the research: unknown fields "fail reconstruction instead of disappearing silently" was itself a Blocking repair, B-5) — the production contract adopts the *post-repair* behavior (preserve-and-ignore for genuinely unknown fields under the same MAJOR version; §2.7 governs unknown *versions*).

### 2.7 Unknown versions fail closed [ENCODING]

A record whose `schema_version`'s MAJOR component is not one this reader implementation declares support for (§2.8) must be **rejected outright** — not partially parsed, not best-effort interpreted. This is the schema-layer restatement of the assignment's explicit instruction ("Unknown versions must fail closed") and of CLTR-001 §14.1 item 9 (cross-transition/version substitution rejection). A record with a *recognized* MAJOR but an unrecognized MINOR/PATCH is parsed under §2.6's unknown-field rule, not rejected — MINOR/PATCH are additive by construction (§2.3), so a recognized-MAJOR record can never contain a MINOR/PATCH-only change the reader cannot safely partially understand.

### 2.8 Minimum supported version [ENCODING]

As of this freeze, the minimum supported `schema_version` is `1.0.0` (there is no prior production schema — this is the first). A future phase that ships `2.0.0` must explicitly declare its own minimum-supported floor for `1.x` records; this document does not pre-commit that floor, since no `1.x` production data exists yet to make that decision meaningful.

### 2.9 Future migration expectations [GUIDANCE]

A future MAJOR bump should ship a documented field-by-field migration map (old field/type → new field/type) and, where feasible, a read-adapter capable of upgrading an old-MAJOR record's *observable facts* into new-MAJOR shape for comparison purposes only (never silently rewriting the historical record itself, per CLTR-001 §14.1). Migration tooling is explicitly out of scope for 135I (no implementation).

---

## 3. Lifecycle model encoding

### 3.1 States [ENCODING, values only — semantics per CLARIFICATION]

The 14 states — 12 spine + 2 orthogonal — are frozen as the enum `lifecycle_state` with exactly these string values (source: CLTR-001 §7.2/§7.3, independently re-confirmed unchanged by 135D §3.3):

```
PROPOSED, CERTIFYING, CERTIFIED, PROMOTING, PROMOTED,
NOTIFYING, NOTIFIED, NOTIFIED_UNCONFIRMED,
TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL,
FAILED_PRE_CERT, FAILED_POST_CERT,
QUARANTINED, SUPERSEDED   [orthogonal overlay values]
```

`lifecycle_state` is a single required field carrying exactly one of the 12 spine values. `QUARANTINED` and `SUPERSEDED` are never spine values in this field (per CLTR-001 §7.3's "orthogonal, does not re-enter the spine" classification, 135D §3.3) — they are carried in a separate `overlay_flags` array field (§3.4) that composes with, and never replaces, `lifecycle_state`.

### 3.2 Transitions [ENCODING, values only]

The 16 transitions are frozen as the enum `transition_type` with exactly these string values (source: 135D §5, independently confirmed as T1–T16):

```
propose_transition, begin_certification, certify, certification_fail,
begin_promotion, promote_succeed, promote_fail,
begin_notification, notify_confirm, notify_unconfirmed, notify_retry,
reconcile_receipt, close_success, close_partial,
quarantine, supersede
```

`quarantine` and `supersede` are the two orthogonal transitions (apply to any CERTIFIED-or-later record without moving spine state). Each transition event recorded in a record's event history (§13) carries exactly one `transition_type` value plus a timestamp (§14) and, where applicable, the resulting `lifecycle_state`.

### 3.3 Forbidden transitions [CLARIFICATION]

The 14 forbidden transitions (F1–F14, 135D §6) are not separately enumerated as wire values — a forbidden transition is, by construction, simply the absence of a corresponding entry in the permitted-next-state table (CLTR-001 §7.3's "Permitted next" / "Forbidden next" columns, restated as a lookup table in §3.5 below). A conforming writer must never emit an event whose `(current_state, transition_type)` pair is not in that table; a conforming reader/verifier must classify any such event as an invariant violation (CLTR-INVAR-STATE, §12) and quarantine the record, never silently accept it. This closes 135G's finding that F8 (SUPERSEDED→active) and F9 (QUARANTINED→TERMINAL_SUCCESS-without-review) were originally unenforced in the disposable prototype (135G §6/§18, finding B-3) — the production schema contract makes the lookup table itself the enforcement surface, not implementation discretion.

### 3.4 Terminal, retry, and recovery classifications [ENCODING]

Three derived boolean/enum fields, computed deterministically from `lifecycle_state` (never independently declared — this is a D-role fact per CLTR-001 §3.1):

- `terminal_classification`: one of `non_terminal`, `terminal`, `terminal_partial` — `TERMINAL_SUCCESS` → `terminal`; `TERMINAL_PARTIAL_EXTERNAL` → `terminal_partial`; `FAILED_PRE_CERT`/`FAILED_POST_CERT` → `terminal` (terminal for *this record*; a new record may retry per CLTR-001 §16.3); all other spine states → `non_terminal`.
- `retry_classification`: one of `retryable_from_scratch` (PROPOSED, FAILED_PRE_CERT), `retryable_via_new_record` (FAILED_POST_CERT, per CLTR-001 §16.3), `not_retryable_terminal` (TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL), `not_retryable_in_progress` (CERTIFYING, PROMOTING, NOTIFYING — must observe before any retry decision, CLTR-001 §16.4), `retryable_reconciliation_only` (NOTIFIED_UNCONFIRMED — receipt-modeling retry only, never delivery retry, CLTR-001 §16.2).
- `recovery_classification`: one of `none_required`, `resume_safe` (CERTIFIED, before PROMOTING started), `observe_required` (crash mid-PROMOTING or mid-NOTIFYING), `reconciliation_required` (NOTIFIED_UNCONFIRMED). Directly encodes CLTR-001 §16.3's recovery-by-record-state table as a queryable field rather than requiring a reader to re-derive it from `lifecycle_state` alone — this is an [ENCODING] convenience field, not a new fact; it must always be recomputable from `lifecycle_state` and, where it disagrees with that recomputation, the record is malformed (fails §12's cross-field consistency invariant).

### 3.5 Permitted-next-state lookup table [CLARIFICATION, restated as a wire artifact]

This table is CLTR-001 §7.3 plus 135D §6, restated for direct machine consumption. It is not new content:

| From state | Permitted `transition_type` values | Resulting state(s) |
|---|---|---|
| PROPOSED | `begin_certification` | CERTIFYING |
| CERTIFYING | `certify`, `certification_fail` | CERTIFIED, FAILED_PRE_CERT |
| CERTIFIED | `begin_promotion` | PROMOTING |
| PROMOTING | `promote_succeed`, `promote_fail` | PROMOTED, FAILED_POST_CERT |
| PROMOTED | `begin_notification` | NOTIFYING |
| NOTIFYING | `notify_confirm`, `notify_unconfirmed`, `notify_retry` | NOTIFIED, NOTIFIED_UNCONFIRMED, NOTIFYING (self, retry) |
| NOTIFIED | `close_success` | TERMINAL_SUCCESS |
| NOTIFIED_UNCONFIRMED | `reconcile_receipt` (→ NOTIFIED via `notify_confirm` if reconciled), `close_partial` | NOTIFIED or TERMINAL_PARTIAL_EXTERNAL |
| TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_PRE_CERT, FAILED_POST_CERT | none (spine-terminal) | — |
| Any CERTIFIED-or-later state | `quarantine`, `supersede` (orthogonal, do not change `lifecycle_state`) | same `lifecycle_state`, `overlay_flags` gains `QUARANTINED`/`SUPERSEDED` |

Any `(from_state, transition_type)` pair not listed above is forbidden (§3.3).

---

## 4. Authority model encoding

### 4.1 Canonical authority [CLARIFICATION]

The CLTR record is the canonical authority for every S-role and D-role fact per CLTR-001 §3.2. This schema does not weaken that: no representation binding in §5 grants any derivative independent authority over a fact the record itself classifies S or D.

### 4.2 Representation ownership and role [ENCODING]

Every representation binding in §5 carries a mandatory `authority_role` field with one of the five CLTR-001 §3.1 role codes: `S` (sole), `R` (reference), `D` (deterministic derivative), `E` (immutable evidence reference), `V` (verification-only observation). This is the wire-level tag that lets a consumer or verifier programmatically confirm a representation is not overreaching its role — e.g., a consumer encountering a report file must see `authority_role: R` for its content-digest binding and must not treat report prose as an independent source of `lifecycle_state`.

### 4.3 Representation inheritance rule [ENCODING]

Every representation binding's `authority_role` is inherited from, and must never exceed, the role CLTR-001 §3.2 assigns to the underlying fact it presents. A representation may present a fact at a *lower* apparent authority than the record does (e.g., a human-readable summary may hedge language) but the wire binding itself may never claim `S` for a fact CLTR-001 classifies `D`, `R`, `E`, or `V`. Conformance checking (§18) rejects any representation instance whose declared `authority_role` exceeds its catalog entry.

### 4.4 No independent lifecycle truth [CLARIFICATION]

Restating CLTR-001 §4 (sole-authority invariant) as a schema-conformance rule: a representation instance that carries its own `lifecycle_state`-shaped field diverging from its bound record's `lifecycle_state` is non-conformant by construction (§18, class `incompatible`), never treated as a competing signal to be reconciled by picking a side.

---

## 5. Representation bindings

For each representation family named in the assignment, this section freezes: the production field carrying its binding, its `authority_role` (§4.2), required identity fields, and digest binding where applicable. Source: CLTR-001 §12.1 (10 rows) + 135D's implicit 15-kind enumeration (135G NB-1) + 135H §1/§2's explicit retirement table (11 named families). This document reconciles the differing counts: **15 representation kinds are frozen**, matching 135G/135H's count, by splitting CLTR-001's "Promoted latest report/metadata" row into its two constituent kinds and adding "Repository transition view" and "Git attribution view" as CLTR-001 §12.1 already lists them as separate rows.

| # | Representation kind | `authority_role` | Identity binding field | Digest field | Required? |
|---|---|---|---|---|---|
| 1 | Canonical phase report | R | `report_id` | `report_digest` | Required at CERTIFIED-or-later |
| 2 | Completion metadata | R | `metadata_id` | `metadata_digest` | Required at CERTIFIED-or-later |
| 3 | Architecture Status | D | `transition_id` (no own identity) | none (regenerable, not separately sealed) | Required derivable at CERTIFIED-or-later; absent before |
| 4 | Immutable snapshot | E | `snapshot_id` | `snapshot_digest` | Required at CERTIFIED-or-later |
| 5 | Checkpoint | E | `checkpoint_id` | none (persistence mechanism, not separately digested, per CLTR-001 §12.1) | Required only while in-progress (PROPOSED through PROMOTING); absent from CERTIFIED-or-later's own field set, retained only in event history |
| 6 | Promoted generation (report) | D, carrying R-role content | `report_id` (same as #1) | `report_digest` (same as #1) | Required at PROMOTED-or-later |
| 7 | Promoted generation (metadata) | D, carrying R-role content | `metadata_id` (same as #2) | `metadata_digest` (same as #2) | Required at PROMOTED-or-later |
| 8 | Notification payload | R + E | `notification_id` (array, §14.4) | `notification_evidence_digest` | Required at NOTIFYING-or-later; may be plural |
| 9 | Marker | D | `marker_id` | reference to `record_digest` (staleness check only, never a separate seal) | Optional always — CLTR-001 §19: never blocks correctness if absent |
| 10 | Receipt | E | `receipt_id` | none (receipts are their own immutable event class, CLTR-001 §12.1) | Required at NOTIFIED or NOTIFIED_UNCONFIRMED; absent before |
| 11 | Repository transition view | V, presenting S+V fields | `transition_id` (no own identity) | none | Regenerable at will; never persisted as a sealed artifact |
| 12 | Git attribution view | V, presenting S+V fields | `transition_id` (no own identity) | none | Regenerable at will |
| 13 | Compatibility/legacy-format view | D (compatibility-only, §19) | `transition_id` | none | Optional; only produced when a compatibility adapter is invoked |
| 14 | Diagnostic envelope | D | `transition_id` when known, else absent | none | Emitted per §20, not persisted as record content |
| 15 | Reconciliation view (pcae phase-report reconcile-equivalent) | V, read-only cross-check of marker+checkpoint+receipt | `transition_id` | none | Regenerable at will; never mutates (§17.5) |

### 5.1 Required bindings summary [CLARIFICATION]

No representation kind above may be produced without its identity-binding field populated with a value that resolves, exactly, to the CLTR record it derives from (CLTR-001 §5.2 item 5's byte-for-byte equality rule, applied to every binding in this table).

---

## 6. State-dependent field requirements

### 6.1 General rule [ENCODING]

Every field defined in §13 (required fields) and §14 (temporal fields) below carries a `presence` classification per lifecycle state: `mandatory`, `optional`, or `prohibited`. §6.2 freezes the master table. A field is `prohibited` at a state if its presence there would misrepresent the transition's actual progress (e.g., `promotion_id` present while `lifecycle_state = CERTIFIED` would falsely imply promotion occurred).

### 6.2 Master presence table [ENCODING]

| Field | PROPOSED | CERTIFYING | CERTIFIED | PROMOTING | PROMOTED | NOTIFYING | NOTIFIED / NOTIFIED_UNCONFIRMED | Terminal states |
|---|---|---|---|---|---|---|---|---|
| `transition_id`, `phase_id`, `repository_identity`, `branch_identity` | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `task_id` | optional (nullable) | optional | optional | optional | optional | optional | optional | optional |
| `source_revision` | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `final_revision` | prohibited | prohibited | conditional (§23.4-derived staged binding — mandatory once resolvable, else explicitly `pending`) | mandatory | mandatory | mandatory | mandatory | mandatory |
| `prior_state` | mandatory (or explicit `none`) | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `projected_state` | prohibited | mandatory (advisory) | mandatory (sealed) | mandatory | mandatory | mandatory | mandatory | mandatory |
| `certified_state` | prohibited | prohibited | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `record_digest` | prohibited | prohibited | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| declared commit set + classification | mandatory (declared; classification not yet complete) | mandatory (classification completing) | mandatory (classification complete, three-outcome) | mandatory | mandatory | mandatory | mandatory | mandatory |
| test/governance evidence references | optional (may be declared) | mandatory (unless declared no-test-required, CLTR-001 §6.2 item 15) | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `report_id`, `report_digest` | prohibited | prohibited | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `metadata_id`, `metadata_digest` | prohibited | prohibited | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `snapshot_id`, `snapshot_digest` | prohibited | prohibited | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `checkpoint_id` | mandatory | mandatory | mandatory | mandatory | optional (historical) | optional | optional | optional |
| `promotion_id` | prohibited | prohibited | prohibited | conditional (present once promotion begins, i.e. mid-PROMOTING; `pending` before that) | mandatory | mandatory | mandatory | mandatory |
| `notification_id` (array) | prohibited | prohibited | prohibited | prohibited | prohibited | mandatory (≥1 entry) | mandatory | mandatory |
| `marker_id` | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | optional | optional |
| `receipt_id` | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | mandatory | mandatory |
| `predecessor_transition_id` | optional (if this is a retry/correction) | same | same | same | same | same | same | same |
| `successor_transition_id` | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | optional (populated only if superseded, via `overlay_flags`) |
| `failure_classification` | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | prohibited | mandatory if `FAILED_*` or `TERMINAL_PARTIAL_EXTERNAL`, else prohibited |
| `retry_classification`, `recovery_classification`, `terminal_classification` | mandatory (derived, §3.4) | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| `compatibility_metadata` | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |

### 6.3 CERTIFIED-or-later certified-content requirement [CLARIFICATION]

**Every CERTIFIED-or-later state shall contain certified content.** This is explicitly a clarification, not a new semantic requirement: CLTR-001 §7.3's CERTIFIED-row "Canonical-state effect" column already states "Record digest fixed; evidence bindings immutable," and 135D §7.1/§7.6/§7.8 independently re-derive the complete certified-content field set (identity, repository/branch/revision, classified commits, evidence references, `prior_state`, `projected_state`, report/metadata bindings, `record_digest`) as what becomes sealed at CERTIFIED and never re-derivable afterward. 135G §4 states this was already enforced at the prototype-validation level ("135G strengthened record validation so every CERTIFIED-or-later state must carry certified content"), and 135H §15 explicitly instructs that a schema-freeze phase make this a mechanical conditional. §6.2's table above is that mechanical expression: every field 135D's §7.1 lists as bound-at-certification is `mandatory` from `CERTIFIED` onward in §6.2, with no exceptions, and `prohibited` before CERTIFYING completes (i.e., under PROPOSED, and for the sealed-only fields, under CERTIFYING itself while certification is still in progress).

### 6.4 Prohibited-field violation handling [ENCODING]

A record instance containing a value in a field classified `prohibited` for its current `lifecycle_state` fails validation as a distinct, named defect class (`CLTR-VALIDATE-PRESENCE`, §18) — this is never silently ignored or treated as harmless extra data, because a prohibited-but-present field is exactly the shape of a premature-authority claim CLTR-001 §4.2 forbids (e.g., a `promotion_id` present at CERTIFIED would misrepresent that promotion had begun).

---

## 7. Required fields catalog

[ENCODING unless noted] Consolidated from CLTR-001 §6.2's 30-item semantic list, §5.1's 11 identifier types, and 135D's certified-content set. Each entry: field name, type, source.

| Field | Type | Source |
|---|---|---|
| `schema_id`, `schema_version`, `contract_version`, `compatibility_id` | string | §1 |
| `transition_id` | string, opaque, one-segment ASCII (per 135G persistence-safety repair B-1, §8 below) | CLTR-001 §5.1 |
| `transition_type` | enum, §3.2 (per-event, not top-level) | 135D §5 |
| `phase_id`, `task_id` (nullable) | string | CLTR-001 §5.1 |
| `repository_identity`, `branch_identity` | string | CLTR-001 §5.1/§3.2 |
| `source_revision`, `final_revision` | string (VCS revision identifier) | CLTR-001 §3.2/§23 |
| `prior_state` | object reference (`transition_id` of prior record, or explicit `"none"`) | CLTR-001 §3.2 |
| `projected_state`, `certified_state` | object, §3.4-shaped projection payload | CLTR-001 §9 |
| `lifecycle_state` | enum, §3.1 | CLTR-001 §7 |
| `overlay_flags` | array of enum (`QUARANTINED`, `SUPERSEDED`) | CLTR-001 §7.3 |
| `phase_commit_ownership` | array of commit-classification objects (§11) | CLTR-001 §10 |
| changed-file evidence | object (binding to `source_revision`/`final_revision`, never a stored diff copy) | CLTR-001 §3.2 item "Files changed" |
| test evidence references, governance evidence references | array of reference objects (§12) | CLTR-001 §6.2 items 14–15 |
| `report_id`, `report_digest` | string, string (hex SHA-256) | CLTR-001 §6.2 item 16 |
| `metadata_id`, `metadata_digest` | string, string | CLTR-001 §6.2 item 17 |
| Architecture Status binding | implicit (derivable from `transition_id` + `projected_state`/`certified_state`; no separate field) | CLTR-001 §6.2 item 18 |
| `snapshot_id`, `snapshot_digest` | string, string | CLTR-001 §6.2 item 19 |
| `checkpoint_id` | string | CLTR-001 §6.2 item 20 |
| `promotion_id` | string | CLTR-001 §6.2 item 21 |
| `notification_id` | array of string | CLTR-001 §6.2 item 22 |
| `marker_id` | string | CLTR-001 §6.2 item 23 |
| `receipt_id` | string | CLTR-001 §6.2 item 24 |
| `timestamps` | object, §14 | CLTR-001 §6.2 item 25 |
| `failure_classification` | enum, §17 | CLTR-001 §6.2 item 26 |
| `retry_classification`, `recovery_classification`, `terminal_classification` | enum, §3.4 | CLTR-001 §6.2 item 27, 135D derivation |
| `predecessor_transition_id`, `successor_transition_id` | string (nullable) | CLTR-001 §6.2 item 28 |
| `compatibility_metadata` | object, §21 | CLTR-001 §6.2 item 29 |
| `record_digest` | string (hex SHA-256) | CLTR-001 §6.2 item 30 |
| `event_history` | array of event objects (§3.2/§13.6 below) | 135A hybrid model, cross-referenced by 135C §8 as the fuller-than-`timestamps` requirement |

### 7.1 Actor/session provenance — explicitly not added [CLARIFICATION]

135C §8 flagged actor/session/agent provenance binding as a genuine but non-blocking omission from CLTR-001's own §6.2, explicitly scoping it as "a distinct, already-existing PCAE concern" (agent lock/session continuity machinery) rather than a CLTR defect. 135D §37 #6 confirms this remains explicitly out of scope. This schema **does not add** an actor/session field to the required-fields catalog — doing so would be a scope expansion beyond CLTR-001's own frozen purpose (§2.1), not a legitimate schema encoding of an existing requirement. A future phase may propose this as an amendment to CLTR-001 itself; 135I does not do so silently by adding the field here.

---

## 8. Optional fields

### 8.1 Presence vs. absence vs. null [ENCODING]

Three distinct wire states are frozen for every optional field, and no field may use fewer than the two that apply to it:

1. **Absent** — the key does not appear in the serialized record at all. Used when the fact is not yet applicable to the record's current `lifecycle_state` (e.g., `promotion_id` absent before PROMOTING begins) — this is the `prohibited`/not-yet-`mandatory` case from §6.
2. **Explicit `null`** — the key is present with JSON `null` (or the equivalent in the canonical serialization, §15) when the fact is applicable and has been explicitly resolved to "no value" (e.g., `task_id: null` for a phase-only transition — the absence of a task was itself declared, not merely unrecorded).
3. **Populated** — the key is present with a concrete value.

**Rule**: absent and explicit-`null` are never interchangeable and a conformant writer must never use one where the contract specifies the other. §6.2's presence table uses `optional (nullable)` to mark fields that may be either absent (not yet applicable) or explicit-`null` (applicable, explicitly empty) depending on lifecycle stage; fields marked plain `optional` without "(nullable)" use absent-only semantics — they are omitted, never null.

### 8.2 Conditions for presence/omission [ENCODING]

| Field | Present when | Absent when |
|---|---|---|
| `task_id` | The transition is task-scoped | The transition is phase-only (explicit `null`, per §8.1 state 2 — the record positively knows there is no task, it did not merely fail to record one) |
| `checkpoint_id` | Transition is PROPOSED through PROMOTING (in-progress) | Transition has reached a state where checkpoint is purely historical (§6.2) — retained in `event_history`, not the top-level field |
| `marker_id` | A marker derivative has actually been generated for this transition | No marker was ever generated (never blocks correctness per CLTR-001 §19) |
| `predecessor_transition_id` | This record is a retry or correction of a prior record for the same `phase_id`/`task_id` | This is the first transition for this phase/task (absent, not null — there is no predecessor to null out) |
| `successor_transition_id` | `overlay_flags` includes `SUPERSEDED` and the superseding record's identity is known | Not superseded (absent) |
| `failure_classification` | `lifecycle_state` is `FAILED_PRE_CERT`, `FAILED_POST_CERT`, or `overlay_flags` includes `QUARANTINED`, or `lifecycle_state` is `TERMINAL_PARTIAL_EXTERNAL` | Any other state (prohibited per §6, not merely absent) |

---

## 9. Enumerations

[ENCODING, values only; semantics per CLARIFICATION as cited] Every production enum, frozen in full:

- **`lifecycle_state`** — 12 values, §3.1.
- **`overlay_flags`** members — `QUARANTINED`, `SUPERSEDED` (§3.1).
- **`transition_type`** — 16 values, §3.2.
- **`authority_role`** — `S`, `R`, `D`, `E`, `V` (CLTR-001 §3.1).
- **`representation_kind`** — the 15 values of §5's table column 2 (machine-safe slugs: `canonical_report`, `completion_metadata`, `architecture_status`, `immutable_snapshot`, `checkpoint`, `promoted_report`, `promoted_metadata`, `notification_payload`, `marker`, `receipt`, `repository_transition_view`, `git_attribution_view`, `compatibility_view`, `diagnostic_envelope`, `reconciliation_view`).
- **`certification_state`** (per-fact, within `phase_commit_ownership` and evidence bindings) — `verified`, `contaminated`, `unverifiable` (CLTR-001 §10.4, exactly three, mutually exclusive per 135C §13's independent re-verification).
- **`conformance_state`** — 7 values (135G §17, independently confirmed distinct): `conformant`, `conformant_with_legacy_adapter`, `incomplete`, `conflicting`, `unverifiable`, `quarantined`, `superseded`.
- **`retry_classification`** — 5 values, §3.4.
- **`failure_classification`** — 17 values, one per CLTR-001 §18's failure-class table (135C §21 independently confirmed exact 1:1, non-overlapping): `identity_resolution_failure`, `commit_ownership_conflict`, `semantic_mismatch`, `evidence_unavailable`, `certification_check_failure`, `snapshot_seal_failure`, `promotion_dispatch_failure`, `promotion_outcome_unconfirmed`, `notification_dispatch_failure`, `notification_outcome_unconfirmed`, `receipt_modeling_failure`, `atomic_visibility_failure`, `duplicate_conflicting_replay`, `cross_phase_replay`, `stale_pointer_detected`, `quarantine_integrity_failure`, `repository_state_mismatch`. (Exact slugs are this schema's [ENCODING] naming of CLTR-001 §18's rows; the *set* and its non-overlap are [CLARIFICATION].)
- **`notification_state`** — `not_attempted`, `attempting`, `confirmed`, `unconfirmed`, `failed` (CLTR-001 §21, 135D §21 item 8's four-outcome receipt refinement plus the pre-attempt state needed for a complete field).
- **`marker_state`** — `absent`, `present_fresh`, `present_stale`, `present_fabricated_rejected` (CLTR-001 §19's four adversarial outcomes, 135C §22 independently confirmed).
- **`receipt_state`** — `confirmed`, `best_effort_incomplete`, `failed`, `unknown` (135D §21 item 8, explicitly labeled a derived clarification, not a new requirement — four genuinely distinct values).
- **`terminal_classification`** — `non_terminal`, `terminal`, `terminal_partial` (§3.4).
- **`recovery_classification`** — `none_required`, `resume_safe`, `observe_required`, `reconciliation_required` (§3.4).
- **`commit_relationship_classification`** — capability-only enum per CLTR-001 §10.2 item 3 / 135D §17 items 13–14, values: `own_source_change`, `own_documentation_only`, `own_repair`, `own_verification_only`, `own_finalization_commit`, `unclassified`. The *capability* to represent this is required now; the exact enumeration is this schema's [ENCODING] choice satisfying that capability requirement — a future MINOR release may add values additively (§2.3) without breaking conformance.

---

## 10. Commit ownership encoding

### 10.1 Fields [ENCODING]

Each entry in `phase_commit_ownership` (an array, never a scalar, per CLTR-001 §10.1 item 6) carries:

```
commit_hash: string
repository_identity: string   (must equal the record's own repository_identity)
branch_identity: string       (must equal the record's own branch_identity)
certification_state: enum     (verified | contaminated | unverifiable)
commit_relationship: enum     (commit_relationship_classification, §9; optional — capability present, value may be unclassified)
contamination_evidence: string, optional (populated only when certification_state = contaminated; the commit subject or other signal that triggered the classification)
```

### 10.2 Explicit prohibition on git-history reconstruction [CLARIFICATION]

Per the assignment's explicit instruction and CLTR-001 §4.2 items 6–7: `phase_commit_ownership` is never derived from `git log --oneline -N` recency, never from commit-subject parsing as identity proof (subject text may populate `contamination_evidence` as a *signal*, never as the classification itself). An empty array is a valid, first-class declaration for no-commit phases (CLTR-001 §10.2 item 1) — never silently defaulted by falling through to a `git log` scan.

### 10.3 Branch-reachability and rewritten-history extension [CLARIFICATION]

135D §17 item 4 / 135C §13 flagged that a hash unreachable from the declared branch, or one predating a force-push rewrite, is not explicitly named as a classification input by CLTR-001. This schema resolves it the way 135C's own recommendation anticipated: such a hash classifies as `unverifiable` (§9's existing three-value enum already covers "cannot be resolved against the bound repository identity/revision" — branch-unreachability and rewritten-history are refinements of *how* unverifiability is evaluated, not a fourth value). No new enum value is added; this is [CLARIFICATION] of evaluation procedure, not a schema change.

### 10.4 Blocking-vs-warning policy remains deferred [CLARIFICATION]

Per CLTR-001 §10.4 and 135D §17.1 (explicitly reaffirmed as a deferred governance-policy question, not an architecture question): this schema freezes the field and enum needed to *represent* `contaminated`/`unverifiable`, and does not decide whether either blocks certification. That decision remains deferred to a future governance-policy phase.

---

## 11. Evidence references

### 11.1 Fields [ENCODING]

An evidence reference object (used for test evidence, governance-check evidence, and any future R-role evidence class) carries:

```
evidence_id: string          (opaque identifier for this specific evidence entry)
evidence_kind: string        (e.g., "test_suite", "governance_check", "runtime_snapshot")
reference: string            (structured pointer — suite name + run ID, or check name + result ID; never free narrative prose as the sole content, per CLTR-001 §11.2)
outcome_summary: object      (structured pass/fail counts or check status; never prose-only)
captured_at: timestamp       (§14)
```

### 11.2 Integrity expectations [CLARIFICATION]

Evidence is read-only once bound (CLTR-001 §11, §14.1 item 6: "no rewriting of past evidence"). An evidence reference's `reference` field must resolve to the same content at verification time as it did at CERTIFYING time, or the record fails the evidence-integrity check (§18, `evidence_unavailable` or a digest-mismatch case under `atomic_visibility_failure`'s sibling checks) — never silently re-pointed at newer content.

### 11.3 Prose prohibition [CLARIFICATION]

Restating CLTR-001 §11.2 exactly: report prose may explain or contextualize an evidence reference; it may never be the sole record of a fact classified R or E.

---

## 12. Invariant encoding

### 12.1 Frozen count and crosswalk [CLARIFICATION]

**37 invariants** are frozen, matching 135G's independently re-derived unique-ID count (135D's own prose stated 36 due to an arithmetic error — `33 + 3` — compounding an earlier miscount in CLTR-001's own prose of 33 against its actual 34-row table; 135G's direct recount of unique IDs across CLTR-001 + 135D's table + the working prototype registry is treated as authoritative here, per 135H NB-3's explicit instruction that 135I "must contain a normative 37-ID crosswalk"). This document does not correct CLTR-001's or 135D's prose — that would be an amendment outside 135I's scope — it records the discrepancy and adopts 37 as the schema's own invariant count, sourced from the table enumeration (which both 135D and 135G's independent recount agree contains 37 distinct entries), not from either document's summary arithmetic.

### 12.2 Encoding per invariant [ENCODING]

Every invariant is represented as an object with:

```
invariant_id: string       (e.g., "CLTR-ID-1", "CLTR-SAFE-3" — the exact IDs from CLTR-001 §26 / 135D §11)
category: string            (identity | authority | state | ordering | derivation | commit | evidence | persistence | retry | notify | marker | receipt | compat | safety)
evaluation_result: enum     (pass | fail | inapplicable — three values only, per 135G §8's "explicit unavailable-input model": missing external comparison input is explicitly inapplicable, never pass)
blocking_classification: enum (blocking | non_blocking — all 37 are Blocking per 135D §11.1's table; this field exists for schema extensibility, §12.3, not because any current invariant is non-blocking)
explanatory_text: string    (human-readable statement of what was evaluated and why the result holds)
```

### 12.3 Future extensibility [GUIDANCE]

New invariants may be added additively (new `invariant_id`, MINOR version) without renumbering or removing existing IDs. An invariant is never silently removed; retiring one is a MAJOR change requiring explicit deprecation (§2.4's field-deprecation discipline applied to invariant IDs) with a stated rationale.

### 12.4 No semantic redefinition [CLARIFICATION]

This schema does not restate what each of the 37 invariants asserts — that remains CLTR-001 §26 and 135D §11's normative text, referenced by `invariant_id`. The schema's role is solely to define how an evaluation result is carried on the wire.

---

## 13. Temporal fields

### 13.1 Named timestamps [ENCODING]

The `timestamps` object carries, at minimum:

```
proposed_at, certified_at, checkpointed_at, promoted_at, notified_at, terminal_at
```

matching CLTR-001 §6.2 item 25's minimum list. Per CLTR-001's own text this list is a minimum, not exhaustive — 135C §8 flagged that the fuller "hybrid" event-plus-state model (135A's original architecture decision) is the actual source of full ordering information, and that §6.2's `timestamps` field is only "the semantic anchor" for it, not a restatement of the full stage-transition history.

### 13.2 Event history as the fuller ordering record [CLARIFICATION]

This schema resolves 135C §8's non-blocking observation explicitly: `event_history` (§7's catalog) is a required array of `{transition_type, from_state, to_state, occurred_at, invariants_evaluated}` entries, one per actual transition (§3.2), and is the authoritative source for full stage-by-stage ordering. `timestamps` remains a required convenience projection of the six named milestones out of `event_history`, and must always be reproducible by filtering `event_history` for its six corresponding transition types — if the two disagree, the record fails cross-field consistency validation (§18).

### 13.3 UTC behavior [ENCODING]

Every timestamp field is UTC, expressed with an explicit `Z` (or `+00:00`) offset designator — never a naive/unzoned timestamp, and never a non-UTC offset.

### 13.4 Precision [ENCODING]

Microsecond precision (`YYYY-MM-DDTHH:MM:SS.ffffffZ`), matching the microsecond-bound filename discipline already used in production for quarantine artifacts (135H.2 §9) and providing sufficient resolution to distinguish rapid successive retries.

### 13.5 Ordering guarantees [CLARIFICATION]

Within one record, `event_history` entries are strictly non-decreasing in `occurred_at` (matching CLTR-001 §8's mandatory ordering and 135D's ORDER invariants) — a record whose event timestamps are out of order relative to its own declared transition order fails validation (`CLTR-VALIDATE-ORDER`, §18). Across records for the same `phase_id`, a successor's `proposed_at` must not precede its declared `predecessor_transition_id`'s `terminal_at` (or `FAILED_*` equivalent) — this generalizes CLTR-001 §17 (duplicate/replay contract) to a checkable temporal rule.

---

## 14. Serialization

### 14.1 Canonical form [ENCODING]

UTF-8 encoded, compact JSON (no insignificant whitespace), object keys sorted lexicographically (byte-wise ASCII ordering) at every nesting level. This matches 135G's prototype canonicalization (§10 of the research report) and is adopted here as the production baseline rather than re-derived from scratch, since 135G's approach was independently verified to satisfy CLTR-001 §15.1's determinism requirement.

### 14.2 Deterministic ordering [ENCODING]

Object key order: sorted, as above. This applies recursively to every nested object, including within array elements.

### 14.3 Collection ordering [ENCODING]

Two distinct rules, matching 135G's prototype finding (§10 research): (a) **set-like collections** (`phase_commit_ownership`, `notification_id` where treated as an unordered set of attempts) are sorted by their own natural key (commit hash lexicographically; notification ID lexicographically) before serialization — CLTR-001 §10.1 item 6 explicitly frames declared commits as "a set, not a scalar," with no ownership-relevant ordering claim. (b) **sequence-like collections** (`event_history`, and any array whose semantic meaning is its order — e.g., a sequence of receipt-reconciliation attempts) preserve their actual chronological/semantic order and are never re-sorted.

### 14.4 Unicode normalization [ENCODING]

All string fields are normalized to Unicode NFC before serialization. This applies to identifiers, evidence text, and explanatory text alike — a field compared for equality (e.g., identity matching, CLTR-001 §5.2 item 5) is always compared post-NFC-normalization, never on raw code points that could differ only by normalization form.

### 14.5 Numeric representation [ENCODING]

Integers (counts, e.g., test pass/fail counts) are serialized as JSON numbers without a decimal point or exponent. No field in this schema requires floating-point representation; if a future MINOR addition needs one, it must specify exact precision and rounding behavior at that time (not pre-committed here).

### 14.6 Boolean representation [ENCODING]

JSON `true`/`false` literals only — never `"true"`/`"false"` strings, never `0`/`1`.

### 14.7 Timestamp formatting [ENCODING]

ISO 8601 extended format with explicit UTC designator, per §13.3–§13.4: `YYYY-MM-DDTHH:MM:SS.ffffffZ`.

### 14.8 Equivalent-content determinism [CLARIFICATION]

Restating CLTR-001 §15.1 item 1 as a schema-conformance test: two logically identical records, constructed via different code paths or dictionary-insertion orders, must produce byte-identical canonical serialization. This is directly testable against 135G's prototype behavior, which the production schema adopts (§14.1's citation).

---

## 15. Digest contract

### 15.1 Algorithm [ENCODING]

SHA-256, hex-encoded lowercase, matching CLTR-001 §15.1 item 2's default (no future phase has yet justified a different algorithm).

### 15.2 Coverage [ENCODING]

`record_digest` covers every serialized top-level field of the canonical form (§14.1) **except** `record_digest` itself (self-exclusion, CLTR-001 §15.1 item 3). This includes `event_history`, all identity fields, all evidence bindings, all classification fields, `overlay_flags`, `timestamps`, and `compatibility_metadata`.

### 15.3 Excluded fields [ENCODING]

Only `record_digest` itself is excluded from digest input. No other field is excluded — CLTR-001 §15.1 item 4 requires full-content binding across every S/R/E-role field, and this schema does not create a partial-coverage exception for any field, including derived (D-role) fields, since a D-role field's presence and value are still part of what a tamper-detection check must catch (a tampered D-role field, even though recomputable, signals record corruption if it disagrees with what §15's digest sealed).

### 15.4 Canonical hashing order [ENCODING]

The digest input is exactly the canonical serialization bytes (§14.1's sorted-key compact JSON, with `record_digest` field omitted from the object being serialized for digest purposes) — not a separately concatenated field list. This avoids a second, parallel canonicalization rule that could drift from §14's.

### 15.5 Verification expectations [CLARIFICATION]

A verifier recomputes `record_digest` from the record's other fields (per §15.2–§15.4) and compares byte-for-byte to the stored value; any mismatch is tamper/corruption evidence and triggers quarantine classification (CLTR-001 §15.1 item 6–7), never a silent acceptance or a "best guess" repair.

---

## 16. Persistence contract

### 16.1 Generation directory structure [ENCODING]

Adopts 135H §8's recommended mechanism, made concrete, and 135G's proven-safe persistence primitives:

```
<cltr_root>/generations/<transition_id>/
    record.json              (the canonical CLTR record)
    manifest.json             (exact allow-listed file list + per-file digest + record_digest + manifest_digest)
    <bound derivative files>  (report, metadata, snapshot payload, etc., per §5's bindings)
<cltr_root>/current           (pointer file or symlink-equivalent, see §16.3)
```

### 16.2 Immutable generation naming [ENCODING]

The directory segment is exactly `transition_id` — a single-segment, ASCII-only, non-path-traversing string (per 135G's B-1 repair: no `..`, no absolute path, no slash/backslash, no leading dot component, no Unicode lookalike path separators). Once published (§16.4), a generation directory's contents are never modified in place; a correction is always a new `transition_id` and a new generation directory (CLTR-001 §14.1).

### 16.3 Current pointer naming and update rules [ENCODING]

`current` is a single file whose content is a small JSON object: `{"transition_id": ..., "generation_id": ..., "record_digest": ..., "manifest_digest": ...}` (135H §8 step 7's exact four-field pointer content). The pointer is updated only by atomic replacement (§17), never by in-place edit of its content.

### 16.4 Publication visibility [CLARIFICATION]

A generation directory is not "published" (visible to ordinary readers) until its manifest and record digest have been verified and the pointer has been atomically switched to reference it (§17) — matching 135G's B-2 repair (files must not be written directly into the final, externally-visible directory; a staging-then-atomic-publish sequence is required). Readers must validate the pointer's referenced `manifest_digest`/`record_digest` against the generation directory's actual contents before trusting it (135H §8's "readers validate pointer + manifest before use").

---

## 17. Atomic publication (specification only — no implementation)

### 17.1 Nine-step sequence [CLARIFICATION]

Restating 135H §8's frozen ordering exactly, as the production expectation this schema's persistence contract (§16) must satisfy once implemented:

1. Persist in-progress CLTR state/event durably (§16, checkpoint mechanism).
2. Generate all derivatives from the sealed record and bound evidence.
3. Verify record digest, derivative digests, manifest allow-list, identities, versions, and all applicable invariants (§12).
4. fsync files and the generation directory as required by the target filesystem.
5. Atomically publish the immutable generation (rename staging directory into place, same filesystem).
6. Durably record promotion success in the CLTR event history.
7. Atomically switch the `current` pointer (§16.3).
8. Only then begin notification; record the attempt before send, record the observation after send.
9. Emit marker cache and receipt binding from CLTR state.

### 17.2 Crash consistency requirements [CLARIFICATION]

Per 135H §8 and 135G's proven fault-injection results: a crash before step 5 leaves no visible generation and no pointer change (safe, fully recoverable by discarding the incomplete staging directory). A crash between step 5 and step 7 leaves a complete, immutable, but not-yet-pointed-to generation — safe and recoverable (the pointer can be corrected by a subsequent verified switch, or the generation can be discarded if superseded). A crash during step 7 itself must never leave the pointer in a partially-written state — the pointer switch is itself an atomic filesystem operation (rename or equivalent), never a partial write; a reader encountering a missing or unreadable pointer falls back to reconstructing the latest complete generation from immutable history (CLTR-001 §13.3 item 6).

### 17.3 No implementation performed [CLARIFICATION]

This section specifies expectations only. No code implementing this sequence is introduced by 135I.

---

## 18. Failure contract

### 18.1 Encoding [ENCODING]

Every failure/quarantine/supersession/recovery case is represented via the combination of `lifecycle_state` + `overlay_flags` + `failure_classification` (§9) — never via a separate, potentially-disagreeing "status" string. This directly forecloses the exact competing-authority pattern CLTR-001 §4.2 forbids (report/metadata status fields as independent authority).

### 18.2 Case-by-case mapping [CLARIFICATION]

| Case | Encoding |
|---|---|
| Incomplete transition | `lifecycle_state` remains at its last-reached in-progress value; `recovery_classification = observe_required` or `resume_safe` per §3.4; no `failure_classification` (not yet a terminal failure) |
| Rejected transition | Recorded as a `FAILED_PRE_CERT` record (no side effects occurred, CLTR-001 §7.3) — or, for a resume-boundary rejection (duplicate/conflicting replay), never persisted as a new record at all; the rejection itself is reported via the diagnostic envelope (§20), referencing the existing terminal record |
| Quarantined candidate | `overlay_flags` includes `QUARANTINED`; `failure_classification = quarantine_integrity_failure` (or the specific triggering class); content is retained, never deleted (CLTR-001 §14.1 item 3-5) |
| Superseded candidate | `overlay_flags` includes `SUPERSEDED`; `successor_transition_id` populated (§8.2); original record's other fields unchanged |
| Recovery candidate | `recovery_classification` per §3.4; no separate "candidate" record type — recovery operates on the existing record's own state |
| Replay prevention | Enforced at the write/verification boundary (§17.9's decision table, CLTR-001) — a conflicting or duplicate write attempt is rejected before it becomes a persisted record, never persisted-then-flagged |
| Reconciliation state | Represented via `receipt_state` (§9) and the read-only reconciliation view (§5, kind #15) — matches 135H.2 §7's `pcae phase-report reconcile` pattern exactly: `reconciled`, `delivery_recorded_bookkeeping_incomplete`, `promotion_outcome_unconfirmed`, `not_delivered`, `conflict` are the five reconciliation outcomes, frozen here as the `reconciliation_outcome` enum |

### 18.3 `reconciliation_outcome` enum [ENCODING]

`reconciled`, `delivery_recorded_bookkeeping_incomplete`, `promotion_outcome_unconfirmed`, `not_delivered`, `conflict` — adopted directly from 135H.2 §7's production-proven reconciliation surface, which independently evaluates marker/checkpoint/receipt agreement without ever treating the marker alone as sufficient for `reconciled` (135H.2 Executive Summary line 36, §7).

### 18.4 No ambiguous failure encoding [CLARIFICATION]

Every failure/recovery case above maps to exactly one combination of `lifecycle_state`/`overlay_flags`/`failure_classification`/`reconciliation_outcome` — no case is left representable in two different ways, matching CLTR-001 §18's requirement that every failure class have a defined, non-overlapping encoding (135C §21 independently confirmed non-overlap for the semantic classes; this section confirms the wire encoding preserves that non-overlap).

---

## 19. Notification bindings

### 19.1 Fields [ENCODING]

Each entry in the `notification_id` array binds to a notification attempt object:

```
notification_id: string
attempted_at: timestamp
notification_state: enum       (§9: not_attempted | attempting | confirmed | unconfirmed | failed)
sink: string                   (e.g., "telegram" — presentation-layer detail, per CLTR-001 §21.2's "reference-heavy, not copy-heavy" principle, not a duplicate of PFN-001's own payload structure)
receipt_state: enum             (§9, populated once receipt modeling completes for this attempt)
```

### 19.2 Notification attempt vs. completion vs. uncertainty [CLARIFICATION]

An attempt is recorded (`attempted_at` + `notification_state: attempting`) **before** dispatch is invoked (135H §8 step 8's explicit ordering: "record attempt before send, observation after send"). Completion (`confirmed`/`failed`) is recorded only from an **observation** of actual delivery outcome, never inferred from having invoked the dispatch call (CLTR-001 §16.4's observation discipline). Uncertainty (`unconfirmed`) is the wire encoding of `NOTIFIED_UNCONFIRMED` (§3.1) — delivery is treated as already-occurred/irreversible; only the receipt bookkeeping is incomplete (CLTR-001 §16.2).

### 19.3 Notification suppression [CLARIFICATION]

A suppressed notification (e.g., a no-notify-required transition type) is represented by the complete absence of any `notification_id` array entry, combined with an explicit `notification_suppressed: true` flag on the record (an [ENCODING] addition needed to distinguish "no notification occurred because none was required" from "no notification occurred because it failed silently" — the latter is never a valid state under CLTR-001, so this flag exists to make the former unambiguous).

### 19.4 Exactly-once relationship [CLARIFICATION]

This schema's `notification_id` array plus §17's atomic-publication ordering directly encode the exactly-once guarantee 135H.2 §4 implemented in production: a durable `attempting` entry is written before the adapter is invoked; a retry that observes an existing `attempting`-or-later entry for the same transition never invokes the adapter again, resolving instead to `promotion_outcome_unconfirmed` (§18) or the existing `notification_state`. PFN-001 itself is unamended (§0, preserved throughout).

---

## 20. Marker and receipt bindings

### 20.1 Required linkage [ENCODING]

`marker_id` (when present) and `receipt_id` (mandatory at NOTIFIED/NOTIFIED_UNCONFIRMED) both carry a mandatory `transition_id` field equal to the owning record's own `transition_id`. Neither may exist without this binding — an orphaned marker or receipt (one whose `transition_id` does not resolve to an existing CLTR record) is non-conformant (§18, `quarantine_integrity_failure`).

### 20.2 Marker/receipt creation ordering [CLARIFICATION]

135D §16 item 7 found that marker/receipt creation order is narrative-default only (CLTR-001 §8.1's numbered list), not a binding precondition — either may be written first or concurrently, so long as each independently satisfies its own creation-timing rule (marker only from NOTIFIED/NOTIFIED_UNCONFIRMED, CLTR-001 §8.2 invariant 4; receipt only reflecting actually-reached stages, CLTR-001 §8.2 invariant 5). This schema does not impose an ordering constraint beyond each field's own individual precondition in §6.2.

### 20.3 Preventing orphaned representations [CLARIFICATION]

Every representation kind in §5's table carries an identity-binding field resolving to `transition_id` (or to a sub-identity that is itself bound to `transition_id`, e.g., `report_id`). A verifier (§18) rejects any representation instance whose binding field does not resolve to an existing, non-superseded-without-annotation CLTR record.

---

## 21. Compatibility adapters

### 21.1 Adapter output contract [ENCODING]

Per 135G's NB-1 finding and 135H §12's elaboration: production requires one adapter per representation kind (§5's 15 kinds), each classified into exactly one comparison mode:

```
adapter_comparison_mode: enum (exact_identity_digest | normalized_semantic | observational | presentation_only | unsupported)
```

- `exact_identity_digest` — byte-exact comparison, used where the schema promises canonical bytes (report/metadata/pointer digests, §15).
- `normalized_semantic` — field-aware comparison after normalization (Architecture Status projection, notification result, receipt content, historical/legacy formats).
- `observational` — comparison against a live-measured V-role fact (repository transition view, Git attribution view) — never treated as retroactively binding.
- `presentation_only` — no comparison performed; the representation is a rendering convenience with no independently checkable content (e.g., human-readable summary text).
- `unsupported` — the adapter explicitly declines comparison and reports `unverifiable` (§9's `conformance_state`) rather than fabricating a result.

### 21.2 Determinism [CLARIFICATION]

Every adapter, given the same CLTR record and the same target representation instance, must produce the same `adapter_comparison_mode` result and the same pass/fail/unverifiable outcome on every invocation — matching 135G's "disposable comparator... safely reports unsupported inline semantics as `unverifiable`, never strengthens authority" finding, adopted here as the production baseline behavior (never optimistic, never a silent upgrade from `unverifiable` to a stronger result).

### 21.3 Cutover cannot occur until complete [GUIDANCE]

Per 135H §12 NB-1: a future implementation phase may not treat production cutover as ready until every one of the 15 representation kinds has a fully specified adapter (not merely `unsupported` placeholders). This is guidance for that future phase, not a gate 135I itself enforces (135I has no implementation to gate).

---

## 22. Conformance

### 22.1 Classes [ENCODING]

The `conformance_state` enum (§9) is the production conformance classification, adopted unchanged from 135G's 7-value set (independently verified distinct, 135G §17):

- **`conformant`** — every applicable invariant (§12) evaluates `pass`; every applicable adapter comparison (§21) succeeds.
- **`conformant_with_legacy_adapter`** — conformant, but one or more representations were reconciled only via a compatibility adapter's `normalized_semantic` path rather than native `exact_identity_digest` comparison.
- **`incomplete`** — required fields for the record's current `lifecycle_state` are missing (§6 violation) but no invariant has evaluated `fail`.
- **`conflicting`** — a Blocking invariant evaluates `fail`, or an adapter comparison finds a genuine mismatch (never silently resolved by picking one side, per CLTR-001 §4).
- **`unverifiable`** — a required comparison input is unavailable (§12.2's `inapplicable` result propagated up) — never treated as `conformant` by omission.
- **`quarantined`** — `overlay_flags` includes `QUARANTINED` (§18).
- **`superseded`** — `overlay_flags` includes `SUPERSEDED` (§18).

### 22.2 Differentiation from lifecycle state [CLARIFICATION]

`conformance_state` is never collapsed into `lifecycle_state` — per 135G §17's explicit confirmation, "terminal success may coexist honestly with unverifiable commit evidence" (a record may be `TERMINAL_SUCCESS` and simultaneously `conformance_state: unverifiable` if, say, a commit hash could not be resolved at verification time). Neither field may be inferred from the other.

---

## 23. Limitations

### 23.1 Encoded limitations [ENCODING]

A record's `compatibility_metadata` object (§7) carries a `limitations` array of structured entries, each: `{limitation_id, description, affects_representation_kinds, since_schema_version}`. As of this v1.0.0 freeze, the following limitations are declared:

1. Final-revision grace-period bound is an unspecified quantitative parameter (135D §32/§37 #5) — a future phase must freeze a concrete numeric value; until then, `final_revision`'s `pending` state (§6.2) may persist for an implementation-defined duration.
2. Branch-reachability/rewritten-history evaluation procedure (§10.3) is specified at the classification level only; the exact algorithm for detecting these cases at verification time is deferred to implementation.
3. Actor/session/agent provenance is not part of this schema (§7.1) — a record does not answer "who proposed this transition."
4. NOTIFIED_UNCONFIRMED naming imprecision (CLTR-001 §7.3's "or is believed to have occurred" hedge, 135C §10) is preserved verbatim in this schema's `notification_state: unconfirmed` value — the schema does not attempt to resolve the naming question, only to carry the value CLTR-001 already defined.

### 23.2 Limitations never strengthen authority [CLARIFICATION]

Per the assignment's explicit instruction: no limitation entry may be read as granting a derivative or adapter additional authority over a fact — a documented limitation narrows what the schema claims to guarantee, it never widens what any representation may claim on its own.

---

## 24. Migration

### 24.1 Shadow integration expectations [GUIDANCE]

A future shadow-integration phase (135N per 135H §17) should write CLTR records alongside existing production artifacts without granting them authority, and should compare shadow-written records against production's existing behavior using the `unsupported`/`observational` adapter modes (§21) until every representation kind has a complete adapter. This is forward guidance only; 135I performs no shadow write.

### 24.2 Historical verification expectations [GUIDANCE]

A future phase verifying historical (pre-CLTR) transitions against this schema should expect `conformance_state: conformant_with_legacy_adapter` or `unverifiable` for most historical data, never `conformant` in the native `exact_identity_digest` sense, since historical artifacts were never produced against this schema.

### 24.3 Future authority migration expectations [GUIDANCE]

Authority migration (production artifacts ceding sole/reference authority to a native CLTR record) should follow 135H §6's nine-stage retirement order (freeze adapters → verify historical reads → shadow CLTR → CLTR-bindable native derivatives → atomic bound-generation publication → centralize resume → cut over read authority → cut over write authority → demote marker/checkpoint/latest inspection → remove redundant native inference), each stage separated by independent verification per 135H §7's nine cutover gates.

### 24.4 No migration implemented [CLARIFICATION]

Per the assignment's explicit instruction, this phase implements none of §24.1–§24.3.

---

## 25. Diagnostic envelope (resolving 135H NB-2)

### 25.1 Standardized structure [ENCODING]

Per 135H §12 NB-2's explicit instruction that this contract "must be frozen with the schema," every diagnostic output (success, validation failure, parser failure, unsupported version, missing record, quarantine) carries:

```
envelope_version: string        (this schema's schema_version)
authority_mode: enum            (shadow | authoritative | compatibility)
mutation_performed: boolean
schema_version, contract_version: string  (§1)
transition_id: string, nullable  (present when known, explicit null when a record was sought but not resolvable, absent only when no transition context applies at all — e.g., a schema-version-level rejection before any transition_id could be parsed)
conformance_state: enum, nullable (§22; null when conformance could not be evaluated)
limitations: array              (§23, echoed from the record when applicable)
diagnostic_kind: enum           (success | validation_failure | parse_failure | unsupported_version | missing_record | quarantine)
detail: string
```

### 25.2 No raw exception leakage [CLARIFICATION]

Per 135G §14 (NB-2's original finding — "some malformed-input errors use raw parser/exception output rather than the structured envelope"): a conformant production implementation must route every diagnostic path, including malformed-input and parse-failure cases, through §25.1's envelope. This is forward guidance for the implementation phase that builds the parser (135I freezes the contract; it does not build the parser).

---

## 26. Cross-Reference Matrix

Every section of this document traces to at least one of CLTR-001 (135B), 135D, 135G, or 135H. This is a summary index; inline citations throughout the document are the authoritative traceability record.

| §§ of this document | CLTR-001 (135B) | 135D | 135G | 135H |
|---|---|---|---|---|
| 1 Schema identity | §1, §5.1 | §11 (invariant-count context) | — | — |
| 2 Versioning | §27 (referenced precedent), §15.2 | — | — | §14 (staged gates) |
| 3 Lifecycle model | §7 | §3, §5, §6 | §2.1 | §1 |
| 4 Authority model | §3, §4 | §14 | — | §1 (authority boundary) |
| 5 Representation bindings | §12.1 | (15-kind count, via 135G) | NB-1 | §1, §2 |
| 6 State-dependent fields | §6.2, §7.3 | §7.1, §7.6, §7.8 | §4 | §15 |
| 7 Required fields | §6.2, §5.1 | §7.1 | §2.1 | — |
| 8 Optional fields | §5.1, §5.2 | — | §2.2 (unknown-field repair) | — |
| 9 Enumerations | §7.2, §10.4, §18, §19, §21 | §6, §11, §17, §20-23 | §8, §17 | — |
| 10 Commit ownership | §10 | §17 | §2.3 (B-8) | §7.1, §13, §16 |
| 11 Evidence references | §11 | §12.1 | — | — |
| 12 Invariant encoding | §26 | §11 | §8 | §12 NB-3 |
| 13 Temporal fields | §6.2 item 25 | — | — | — |
| 14 Serialization | §15.2 | — | §10 | — |
| 15 Digest contract | §15 | — | §10 | — |
| 16 Persistence contract | §13 | §20 | §13 | §8 |
| 17 Atomic publication | §13 | §20 | §13 (fault injection) | §8 |
| 18 Failure contract | §18, §17.9 | §21 item 8 | — | — |
| 19 Notification bindings | §21 | §21 | — | §8 step 8 |
| 20 Marker/receipt bindings | §19, §20 | §16 item 7, §22, §23 | — | — |
| 21 Compatibility adapters | §12.2, §12.3 | — | NB-1 | §12 |
| 22 Conformance | — | §28.1 (referenced) | §17 | — |
| 23 Limitations | §32 (referenced) | §37 | §18 | §13 |
| 24 Migration | §33.2 (referenced) | §41 | §22 recommendation | §6, §7, §17 |
| 25 Diagnostic envelope | — | — | NB-2 | §12 NB-2 |

**No section of this document lacks a traceable architectural origin.**

---

## 27. Explicit non-goals (confirmed satisfied)

Per the assignment's explicit instruction, none of the following occurred in this phase:

- Production CLTR implementation.
- Production lifecycle modification.
- Shadow integration implementation.
- Schema parser implementation.
- Serializer implementation.
- Persistence introduction.
- Notification flow modification.
- Finalization modification.
- Report generation modification.
- Legacy authority retirement.
- Runtime behavior change.
- Execution capability introduction.
- Prototype behavior modification.

This document is text only. No file under `src/`, `tests/`, or any runtime-governance path was created or modified by this phase.

---

## 28. Governance boundary

This document grants no execution authorization. It does not alter Runtime state (remains Observed / observe / execution unavailable), does not alter PFN-001, does not alter PFR-001, and does not alter CLTR-001. Where this document appears to state a requirement more specifically than CLTR-001, that specificity is either [CLARIFICATION] (already required, now made mechanical) or [ENCODING] (a wire-format choice within a semantic space CLTR-001 deliberately left open, per CLTR-001 §6.1/§6.3/§15.2/§13.2). No clause in this document authorizes command execution (CLTR-SAFE-1), infers missing authority (CLTR-SAFE-2), or reconstructs provenance heuristically (CLTR-SAFE-3).

---

## 29. Recommended next phase

**135J — Production CLTR Schema and Integration Contract Verification.**

This phase (135I) does not begin 135J. Independent verification of this schema contract — re-deriving each [CLARIFICATION]/[ENCODING]/[GUIDANCE] tag, checking the 37-invariant crosswalk, checking the 15-representation-kind adapter contract for completeness, and adversarially testing the versioning/compatibility rules — is explicitly deferred to that future phase.
