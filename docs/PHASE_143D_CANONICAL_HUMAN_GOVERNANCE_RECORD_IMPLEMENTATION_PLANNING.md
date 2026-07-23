# Phase 143D — Canonical Human Governance Record Implementation Planning

**Status:** Complete (implementation-planning-stage document only; no
schema implemented, no CLI implemented, no storage created, no legacy
import performed, no human decision created/repeated/simulated, no
governance contract modified, no `src/pcae/` or `tests/` file touched)
**Mode:** Implementation planning, translating Phase 143A's architecture
and CHGR-001 v1.0's frozen contract — as independently re-verified by
Phase 143C — into a bounded, testable, dependency-aware blueprint for the
first CHGR implementation increment.
**Governing authority:** Phase 143A, CHGR-001 v1.0
(`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`), Phase
143C independent verification, GLP-001 v1.0, GAC-001 v1.0, PGP-001 v1.1,
PPA-001 v1.0, AGOC-001 v1.0, GPC6-001 v1.0, GPC6R-001 v1.0, GPC6C-001 v1.0,
GPC6-REQ-040, GPC6-REQ-075(b),
`docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`, TAMC-001 v1.0, TAMPC-001
v1.1.
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Deliverable:** this document, this phase report.

---

## 0. Method Statement

This plan was derived by independently re-reading, in full or at every
cited provision: Phase 143A's architecture
(`docs/PHASE_143A_CANONICAL_HUMAN_GOVERNANCE_RECORD_ARCHITECTURE.md`);
CHGR-001 v1.0 in full (all 25 sections, all 193 `CHGR-REQ-###`
requirements, extracted programmatically to confirm section boundaries —
see §25 below); Phase 143C's independent verification in full, including
its complete NB-1 and NB-2 text, its 7 Observations, and its Repair
Disposition (§21); `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`; and
the existing repository implementation surface that any CHGR
implementation would need to sit beside without collapsing into: the
Stage 3 Companion Executable Schema family
(`src/pcae/schema_resources/cltr_cutover/` — `manifest.json` +
`manifest.schema.json` + `records/*.schema.json` + `shared/*.schema.json`
+ `schema_runtime/` loader/validator/registry), the Typed Authority Model
production consumer (`src/pcae/cltr/authority/authority_core.py`,
`src/pcae/cltr/authority_inspection.py`,
`src/pcae/commands/authority_inspect.py`), canonical artifact promotion
(`src/pcae/core/canonical_artifact_promotion.py`,
`src/pcae/core/post_push_canonicalization.py`), and canonical phase-report
machinery (`src/pcae/core/phase_reports.py`,
`src/pcae/core/phase_report_trust.py`, `src/pcae/core/phase_report_view.py`,
`src/pcae/commands/phase_reports.py`). `PROJECT_STATUS.md` was treated as
authoritative over any stale task/TODO material per this phase's own
instruction; no conflict was found between it and the sources above.

This plan does not assume a prior suggested implementation layout (e.g.
the illustrative CLI command names or the illustrative increment sequence
in the governing prompt) is correct; each is independently evaluated below
and either adopted, adapted, or rejected with reasons (§4, §8).

---

## 1. Required Initial Action — NB-1 and NB-2 Disposition

Per this phase's own governing instruction, NB-1 and NB-2 (Phase 143C §20)
are reproduced and dispositioned before any planning below relies on
CHGR-001's text.

### 1.1 NB-1 — §20 Governance Responsibility citation imprecision

**Finding (143C §20, verbatim substance).** CHGR-001 §20's "Human
selection" row claims to reuse "the same 'Human Authority' concept
GPC6-REQ-040 already defines," but GPC6-REQ-040's own table (and its own
source, GLP-001 §8) define a narrower, `GLP-PILOT-C6`-scoped /
GLP-initiative-stage-progression-scoped role, not a fully generic role
spanning every Human Governance Act class 143A §1.2 lists. **Impact per
143C:** none to CHGR-001's operative correctness, since §6/CHGR-REQ-051
independently requires each Decision Template to name its own eligible
authority — no template can rely on the imprecise §20 citation in
practice.

**143D disposition: not Blocking; addressed through implementation design,
not a contract change.** This plan (§10, §21 below) treats
CHGR-REQ-051's per-Decision-Template eligibility-naming requirement, not
GPC6-REQ-040's table, as the sole operative authority-eligibility
mechanism a Decision Template Controller (§8) or Decision Template
Governance process (§10) may implement against. No implementation
component in this plan resolves "who may confirm this decision" by
generically consulting GPC6-REQ-040 or GLP-001 §8; every component
resolves it by reading the specific Decision Template's own named
eligibility field. This makes NB-1's citation imprecision inert at the
implementation-design level without touching CHGR-001's text. The
citation-text repair itself (§20's prose pointing to GLP-001 §8 instead of
GPC6-REQ-040, per 143C's own recommendation) remains a documentation-only,
non-substantive contract amendment properly performed by a future governed
Contract Freeze revision under CHGR-001 §22's Amendment Contract — not by
this planning phase, which has no authority to edit a frozen contract
(Mandatory Boundaries, "No frozen contract shall be modified").

### 1.2 NB-2 — Self-referential citation at CHGR-REQ-154

**Finding (143C §20, verbatim substance).** CHGR-REQ-154's own "see also"
parenthetical lists CHGR-REQ-154 itself. **Impact per 143C:** none — "see
also" carries no normative force under CHGR-001 §0; a drafting typo whose
correct intended target cannot be confidently reconstructed.

**143D disposition: not Blocking; purely cosmetic; deferred to a future
contract revision.** No implementation component in this plan depends on
CHGR-REQ-154's "see also" list for correctness — §19 (Security and
Threat-Model Planning) and §13 (Verification Engine Planning) below cite
CHGR-REQ-154 by its normative sentence only (the requirement governing
stale/expired decision-maker eligibility), never by its non-normative
cross-reference list. No implementation-planning decision in this document
is affected by which requirement CHGR-REQ-154's "see also" was meant to
name. The cosmetic repair is deferred, exactly as 143C recommended, to a
future dedicated contract-revision phase under CHGR-001 §22.

### 1.3 Blocking-defect check

Neither NB-1 nor NB-2 "demonstrates a Blocking defect in the frozen
contract" per this phase's own stop condition — 143C itself classified
both as Non-Blocking with no operative impact, and independent re-reading
above confirms no planning decision below is required to rely on either
defective citation to be correct. **This phase proceeds to plan
implementation against CHGR-001 v1.0 as frozen; no governed repair phase
is recommended ahead of implementation planning.** Both findings are
carried into the Requirement Traceability disposition (§25) rather than
silently dropped.

---

## 2. Implementation Scope

**Central boundary restated (governs every scope decision below):** PCAE
may structure, display, validate, preserve, and publish a human governance
act, but it may never choose, infer, reinterpret, broaden, narrow, or
confirm the substantive human decision.

| Category | In scope |
|---|---|
| **Required — first increment** | Executable schema family for `DecisionTemplate`, `HumanGovernanceRecord`, `HumanConfirmationEvidence`, `GovernanceRecordProvenance`, `GovernanceRecordIntegrity`, `GovernanceRecordIndexEntry` (§4); canonical storage boundary and staging/quarantine/atomic-promotion reuse (§6); `pcae governance record inspect` and `pcae governance record verify` (read-only, non-authoritative); deterministic Markdown rendering; digest/provenance construction; a minimal interactive `create`→`preview`→`confirm`→`publish` CLI flow at assurance level L0/L1 only |
| **Required — same increment, non-interactive path** | `pcae governance template inspect` (read-only template display, no authoring UI yet) |
| **Optional follow-on** | `pcae governance record list`; richer template-authoring workflow; `pcae governance record resume` for abandoned sessions |
| **Explicitly deferred** | Legacy election import (§12); suspension/supersession/revocation lifecycle transitions (§11); any assurance level above L1 (signing, hardware-backed, external IdP, multi-party — L2–L5); any runtime consumer of a CHGR as authority; any authority resolver |
| **Prohibited (this phase and the first implementation increment alike)** | Runtime enforcement or authority resolution of any kind; consuming a CHGR to gate, unlock, or authorize any PCAE behavior; re-election or re-confirmation of GPC6-REQ-075(b); any executable schema, CLI command, storage directory, or code change performed **by this planning phase itself** |

The first increment is deliberately bounded to **recording, publishing,
inspecting, and verifying** — never consuming — matching the governing
prompt's own framing and CHGR-001 §17's Runtime Consumption Contract,
which freezes only the *future* consumption boundary and authorizes no
runtime implementation now.

---

## 3. Capability Decomposition

| Component | Responsibility | Depends on | CHGR-001 basis |
|---|---|---|---|
| Decision-template representation | Load/validate a `DecisionTemplate` record | Schema family (§4) | §6, §23.6 |
| Interactive decision-session controller | Drive the staged CLI workflow, hold in-progress state | Template representation, no-default enforcement | §5, §23.5 |
| Substantive human-choice capture | Record the human's literal selection, verbatim, unmodified | Session controller | §4, §23.4 |
| Neutral explanatory/boundary rendering | Render consequence/non-effect statements verbatim from template, no paraphrase | Template representation | §4, §5, §6 |
| Preview generation | Deterministically render exact final content pre-confirmation | Record-construction (draft state) | §5, §7, §23.5/23.7 |
| Explicit confirmation capture | Bind confirmation to exact previewed content; no replay | Preview generation | §7, §23.7 |
| Canonical record construction | Assemble the immutable `HumanGovernanceRecord` payload | Choice capture, confirmation capture | §3, §23.3 |
| Deterministic human-readable rendering | Produce canonical Markdown view from canonical data, never the reverse | Record construction | §3 invariant 4 |
| Provenance construction | Assemble `GovernanceRecordProvenance` (template, options, choice, preview, confirmation, repo/commit context) | Record construction | §10, §23.10 |
| Integrity evidence | Compute/store digests over canonical payload | Record construction | §10, §21 |
| Atomic publication | Stage → validate → atomically promote, reusing `canonical_artifact_promotion.py` patterns | Record + provenance + integrity | §8, §23.8 |
| Canonical indexing/registration | Maintain a `GovernanceRecordIndexEntry` manifest (mirrors `cltr_cutover/manifest.json`) | Publication | §9, §23.9 |
| Inspection | Non-authoritative read/display of a published record's full state | Storage | §21, §23.21 |
| Verification | Deterministic, fail-closed structural/provenance/integrity check | Schema, storage, index | §13(planning)/§23 various |
| Lifecycle state representation | Model the 8-state model (§13.4) as schema enum + `GovernanceRecordLifecycleEvent` | Schema | §13, §23.13 |
| Legacy import support | Deferred (§12); planned only, not built this increment | Record construction, provenance | §14, §23.14 |
| Suspension/supersession/revocation planning | Deferred (§11); planned only | Lifecycle state model | §13, §23.13 |

Ownership of each component is mapped to existing PCAE roles in §21;
no component here introduces a new role.

---

## 4. Implementation Increment Strategy

The governing prompt's illustrative six-step sequence (schemas → storage
→ CLI → legacy import → lifecycle → verification) is **not adopted
automatically**, per its own instruction. Independent evaluation:

- **Legacy import first is rejected.** Importing before the schema family
  and publication path exist has no target to import into, and risks
  designing the schema *around* the one legacy record's shape rather than
  around CHGR-001's general contract — inverting the correct dependency
  direction.
- **CLI before schema is rejected.** A CLI cannot construct a record whose
  shape is undefined; this would force informal, later-formalized shape
  decisions into CLI code, the opposite of "schema-first" discipline
  already established by the Stage 3 Companion Executable Schema
  precedent (Track 136).
- **Lifecycle transitions (suspend/supersede/revoke) before a first
  published record exists is rejected** — nothing to transition yet, and
  building transition logic first risks over-designing before the
  Published-state shape is validated by actual use.
- **Verification as a final, separate step is rejected as *sole*
  placement.** Verification must exist test-by-test alongside schema and
  publication work (fail-closed validation is worthless if bolted on
  after publication already works informally) but a *dedicated
  independent verification phase*, mirroring 143C's own relationship to
  143B, is still the right *closing* increment for the whole first
  implementation phase.

**Recommended single bounded increment (143E, see §29):** schema family +
canonical model + storage/publication/verification, as one coherent phase,
covering:

1. Executable schema family (§4 below) for the six required-first-scope
   types, reusing `schema_runtime/` loader/validator/registry unchanged.
2. Canonical storage/publication/quarantine wiring reusing
   `canonical_artifact_promotion.py` patterns (§6).
3. A minimal, safe interactive CLI limited to `create → preview → confirm
   → publish → inspect → verify` (§8), explicitly excluding
   `list`/`resume`/`suspend`/`supersede`/`revoke`/`import`.
4. Verification (`pcae governance record verify`) built alongside
   publication, not deferred to a later phase, satisfying fail-closed
   discipline from the start.

This is the "smallest coherent implementation boundary" required by the
governing prompt: it produces independently useful, testable behavior (a
human can record and later verify a real decision), preserves contract
compliance end-to-end, creates no partial-authority semantics (nothing
consumes the record as authority), can be independently verified on its
own (143F, mirroring 143C's relationship to 143B), and requires no
runtime enforcement.

Legacy import, lifecycle transitions beyond Draft→Published, and richer
CLI ergonomics (`list`, `resume`) are explicitly **deferred to later,
separately governed increments** (§29), each individually smaller than
this first increment and each independently verifiable.

---

## 5. Schema Planning

Following the `cltr_cutover` precedent (`manifest.schema.json` + per-record
`records/*.schema.json` + shared building blocks in `shared/`), the CHGR
schema family should live at `src/pcae/schema_resources/chgr/` with its
own `manifest.json`/`manifest.schema.json` and reuse — not duplicate — the
existing `shared/digest.schema.json`, `shared/envelope.schema.json`,
`shared/identity.schema.json`, `shared/references.schema.json`,
`shared/limitations.schema.json`, `shared/failures.schema.json`,
`shared/enums.schema.json` where their shapes already fit (digest and
envelope in particular are directly reusable; identity/references need
CHGR-specific extension, planned not built here).

| Type | Purpose | Required fields (representative, not exhaustive) | Optional fields | Identity/versioning | Class |
|---|---|---|---|---|---|
| `DecisionTemplate` | Neutral, versioned template a session is driven from | `template_id`, `version`, `decision_subject_schema_ref`, `options[]` (each: id, label, consequence text, non-effect text, no `default: true` field permitted), `eligible_authority` (per CHGR-REQ-051) | rationale/conditions prompts (optional-marked), deprecation notice | template_id + semver; supersession pointer | Authoritative (governs session shape) |
| `DecisionSession` | Ephemeral in-progress state; never itself a CHGR | `session_id`, `template_ref`, `state` (draft/awaiting-confirmation/abandoned), timestamps | rationale text so far | session_id, not portable/referenceable by other records | Operational (not published) |
| `HumanGovernanceRecord` | The canonical, immutable act record | `record_id`, `template_ref`+version, `decision_subject`, `selected_option_id` (verbatim), `rationale`(optional, human-authored only), `assurance_level`, `lifecycle_state`, provenance ref, integrity ref | conditions, predecessor/successor links | globally unique `record_id`, portable, path-independent (§8 below) | Authoritative |
| `HumanConfirmationEvidence` | Binds confirmation to exact previewed content | `confirmed_content_digest`, `confirmation_timestamp`, `confirmer_identity_evidence` (per achieved assurance level, honestly disclosed), `preview_rendering_digest` | — | embedded in / referenced from the record's provenance | Evidentiary |
| `GovernanceRecordProvenance` | What happened, in order, to produce the record | template used+version, options presented, choice, rationale/conditions given, exact preview shown, confirmation event, repo/commit provenance | — | referenced by record_id | Evidentiary |
| `GovernanceRecordIntegrity` | Digest evidence over the canonical payload and its rendering | payload digest, rendering digest, digest algorithm | — | referenced by record_id | Evidentiary |
| `GovernanceRecordLifecycleEvent` | One state transition | `record_id`, `from_state`, `to_state`, `initiating_actor`, `evidence_ref`, timestamp | linked governance act ref (for supersession) | append-only, own event id | Evidentiary (planned, not built this increment beyond Draft→Published) |
| `GovernanceRecordIndexEntry` | Manifest/registry row | `record_id`, `subject`, `current_state`, `digest`, `path` | — | one row per record_id, mirrors `cltr_cutover/manifest.json` shape | Derivative/operational |
| `LegacyRecordImportEvidence` | Wraps a legacy source without altering it | source path, source digest, source commit, import timestamp, disclosed-unavailable-metadata list | — | referenced by the imported record's own `record_id` | Evidentiary (planned only, §12) |

No `DecisionSession` is ever itself publishable; only a
`HumanGovernanceRecord` reaches canonical storage — this is the load-bearing
distinction preventing an abandoned session from being mistaken for a
decision (CHGR-REQ-043-adjacent, §23.5).

Nine types is the minimum found necessary; no further proliferation is
planned. `GovernanceRecordProvenance` and `GovernanceRecordIntegrity` are
kept as two types, not one, mirroring the existing
`publication_evidence.schema.json` vs. digest-only-evidence separation
already present in `cltr_cutover/records/`, since provenance answers "what
happened" and integrity answers "is this exact payload unaltered" — two
independently falsifiable questions.

Compatibility with existing typed-authority schemas: none of the nine
types subclass, wrap, or extend `human_authorization.schema.json` or any
other `cltr_cutover/records/*` type (§16 below elaborates why).

---

## 6. Canonical Identity Planning

- **Namespace:** `record_id` values are namespaced (`chgr-<uuid4>` or
  similar), distinct from `cltr_cutover` record ids and from phase-report
  identifiers, so no collision is possible even if directories were ever
  merged.
- **Uniqueness/collision handling:** allocated at Draft-session creation
  time, checked against the index (`GovernanceRecordIndexEntry`) before
  publication; publication fails closed on collision (never silently
  reassigns).
- **Allocation:** locally generated (no central registry needed at L0/L1
  assurance); UUID4 gives effectively-unique allocation without a
  network dependency, consistent with the "unavailable" execution/runtime
  posture.
- **Portability/path independence:** `record_id` never encodes a
  filesystem path, date, or agent identity — mirrors CHGR-REQ-076/077
  class requirements (§23.9) and the existing `cltr_cutover` convention
  of digest/id-based, not path-based, reference.
- **Subject binding:** `decision_subject` is a separate field from
  `record_id`; multiple records may reference the same subject (e.g.
  supersession chains), so subject is never treated as a unique key.
- **Predecessor/successor linkage:** carried in the record itself (a
  `predecessor_record_id` / future `successor_record_id` optional field),
  not inferred from filename ordering or timestamps.
- **Record ID vs. lifecycle-event ID:** distinct id spaces —
  `GovernanceRecordLifecycleEvent` rows have their own event id and
  reference a `record_id`, so an event never overwrites or reuses the
  record's own identity.
- **Imported legacy record identity:** the legacy election gets a newly
  allocated `record_id` at import time (never derives one from its
  existing file path or commit hash, both of which are provenance facts,
  not identity — §12 below).
- **Why identity ≠ authority (must be stated explicitly per the governing
  prompt):** `record_id` uniqueness, presence in the index, or
  well-formedness proves only that *a record exists and can be
  referred to* — never that the act it records was made by an eligible
  authority, in scope, or is still current. This mirrors TAMC-REQ-036's
  identical discipline for Typed Authority Model records (§16 below) and
  CHGR-001 §11's Authority Contract exhaustive list of facts that never
  establish authority alone.

---

## 7. Storage and Publication Planning

**Directory layout (planned, not created this phase):**
`.pcae/governance-records/` (confirmed absent from the repository by 143C
§22) as the canonical root, mirroring the `cltr_cutover` split:
- `.pcae/governance-records/manifest.json` — the index
  (`GovernanceRecordIndexEntry` rows)
- `.pcae/governance-records/records/<record_id>.json` — canonical
  machine-readable payload
- `.pcae/governance-records/records/<record_id>.md` — deterministic
  rendered view, generated from the JSON, never hand-edited
- `.pcae/governance-records/provenance/<record_id>.json` — provenance
  evidence
- `.pcae/governance-records/staging/` — pre-promotion working area
- `.pcae/governance-records/quarantine/` — failed-validation landing zone,
  reusing the existing quarantine pattern already proven by
  `.pcae/phase-reports/quarantine/` and `canonical_artifact_promotion.py`

**Reuse, not reimplementation:** `canonical_artifact_promotion.py`'s
stage→validate→atomic-rename promotion primitive and
`post_push_canonicalization.py`'s crash-safe patterns are the intended
reuse targets; this plan does not invent a new atomic-publication
mechanism where a working one already exists in the repository, provided
independent review during implementation confirms its promotion
primitive is generic enough not to assume phase-report semantics (a
concrete implementation-time verification step, not assumed true here).

- **Registry/manifest:** one `manifest.json`, append-only rows, keyed by
  `record_id`, updated atomically alongside publication (same transaction
  boundary as the record write).
- **Publication staging → quarantine → atomic promotion:** a record is
  written to `staging/`, validated against schema + provenance + integrity
  checks, and only then atomically promoted into `records/`; any
  validation failure routes to `quarantine/` with a sanitized failure
  reason, never partially into `records/`.
- **Rollback:** a quarantined or interrupted publication leaves no trace
  in `manifest.json` — rollback is "never indexed," not "undo an index
  entry."
- **Crash recovery:** publication is designed so that a crash mid-write
  leaves either nothing in `records/` (safe) or a fully-written-but-
  unindexed file (safe, since the index, not file presence, is the
  authoritative "is this published" signal) — never a half-written file
  presented as published.
- **Duplicate publication:** a second publish attempt with the same
  `record_id` fails closed (index already contains that id); a second
  attempt with different content for the same `decision_subject` is
  **not** rejected outright (multiple records may legitimately concern one
  subject over time via supersession) but is surfaced as inspectable via
  §22's observability planning, addressing 143C's OBS-5 gap at the
  planning level even though CHGR-001 imposes no detection requirement.
- **Concurrent publication:** the same file-lock/atomic-rename discipline
  `canonical_artifact_promotion.py` already uses for concurrent
  phase-report writes is the planned reuse target; two processes racing
  to publish distinct `record_id`s never collide (different target
  files), and a race on the *same* `record_id` is prevented by the
  uniqueness check in §6 running inside the same locked promotion step.

---

## 8. Interactive CLI Planning

**Command surface (derived from existing PCAE conventions, not adopted
verbatim from the governing prompt's illustrative list):** existing
`pcae` subcommands are one flat module per top-level noun under
`src/pcae/commands/` (e.g. `authority_inspect.py`, `phase_reports.py`,
`decision_log.py`). Following that convention, and noting a
`src/pcae/commands/decision_log.py` already exists for an unrelated
concern, the CHGR command family is planned as a new top-level noun,
`governance`, implemented as `src/pcae/commands/governance_record.py`
(and, if template inspection warrants separation, a second
`governance_template.py`), exposing:

- `pcae governance template inspect <template_id>` — read-only
- `pcae governance record create --template <id>` — starts a
  `DecisionSession`, staged locally, not yet published
- `pcae governance record preview <session_id>` — deterministic exact
  rendering of what would be confirmed
- `pcae governance record confirm <session_id>` — explicit confirmation,
  binds to the exact preview digest (§9)
- `pcae governance record publish <session_id>` — atomic promotion (§7)
- `pcae governance record inspect <record_id>` — read-only, published
  records only
- `pcae governance record verify <record_id>` — runs the verification
  engine (§13)

`list`, `resume`, `suspend`, `supersede`, `revoke`, `import` are named as
**planned command surface for later increments** (§29) — not implemented
in the first increment, consistent with §2's scope table.

**Safety behaviors, mapped to concrete CLI mechanics:**
- No option is pre-selected: the prompt renders all `options[]` from the
  template with no highlighted/default entry; the underlying input
  primitive must require an explicit index/id token, never accept bare
  Enter as a value.
- Enter alone re-prompts with the same neutral rendering rather than
  accepting any value — enforced by the session controller rejecting an
  empty selection token before it ever reaches record construction, not
  by a UI hint alone (defends CHGR-REQ-021/022/043).
- Rationale/conditions are explicitly marked optional in the prompt text
  and the schema (`required` never includes them).
- Consequence/non-effect text is rendered byte-for-byte from the
  template's own fields — the CLI performs no summarization, wrapping
  aside, of that text.
- `preview` renders the exact final payload (including rationale as
  literally typed) before any confirmation prompt appears.
- `confirm` requires a distinct, explicit token (not a re-use of the
  selection input) and computes/stores a digest over exactly what was
  previewed (§9).
- Cancellation (`Ctrl-C` or an explicit `--abandon`) at any point before
  `publish` leaves the session in `abandoned` state, never auto-published,
  never treated as a decision, and excluded from the manifest.
- A resumed-later increment (`resume`) must re-render the same preview
  content before allowing confirmation, so a stale session can never be
  confirmed against content the human did not just see.

---

## 9. Human Confirmation Planning

- **Assurance disclosure:** the first increment implements assurance
  level **L0** (explicit typed confirmation, e.g. typing a literal
  confirmation phrase or record id) as the default, and **L1**
  (authenticated local-user confirmation, e.g. OS user identity captured
  alongside the confirmation event) as an optional stronger mode if OS
  identity is cheaply available — never claiming more than what actually
  occurred, per CHGR-REQ-102-class honesty requirements (§23.12).
- **Exact-content binding:** `HumanConfirmationEvidence.confirmed_content_digest`
  is computed over the literal preview payload; `confirm` refuses to
  proceed if the session's content has changed since the last `preview`
  call (forces a fresh preview before confirming altered content — defends
  scenario 6/7 in §28).
- **No replay:** the confirmation event is single-use — once a session
  reaches `awaiting-confirmation` → `confirmed`, re-running `confirm`
  against the same session is rejected (idempotency is "already
  confirmed," not "confirm again").
- **Identity evidence at achieved level only:** at L0, the confirmer
  identity evidence is whatever the local environment can honestly assert
  (OS user, hostname, timestamp) — explicitly not represented as
  cryptographic identity.
- **No overclaiming:** the schema's `assurance_level` enum is the only
  place assurance is asserted; nothing else in the record, provenance, or
  rendering may imply a higher level.
- **Extension points, not implementations:** the schema's
  `assurance_level` enum already reserves L2–L5 (§4, unchanged from
  143A §10.1/CHGR-001 §12); `HumanConfirmationEvidence.confirmer_identity_evidence`
  is planned as a discriminated-union-shaped field so a future signing or
  external-IdP integration adds a new evidence variant without altering
  existing L0/L1 records' shape or meaning.

---

## 10. Decision Template Governance Planning

- **Authoring:** templates are authored as versioned JSON files under
  `src/pcae/schema_resources/chgr/templates/` (packaged, not
  user-writable at runtime in the first increment — user-authored
  templates are explicitly deferred).
- **Review/approval:** template content changes go through the same PR
  review discipline as any other packaged resource; no new approval
  role is invented (mirrors the existing schema-change review path for
  `cltr_cutover`).
- **Versioning:** semver per template id, immutable once referenced by
  any published record (a published record's `template_ref` pins an
  exact version).
- **Storage:** packaged resource, discovered via the same
  `schema_runtime` resource-loading mechanism already used for
  `cltr_cutover` schemas — no new discovery mechanism.
- **Validation:** `manifest.schema.json`-style structural validation plus
  a template-specific linter rule set enforcing the neutrality
  constraints below.
- **Deprecation/supersession:** a `deprecated_by` pointer field, never a
  deletion — old templates remain resolvable so old records referencing
  them remain interpretable.
- **Inspection:** `pcae governance template inspect` renders the full
  template, including deprecation status.
- **Neutrality enforcement (mechanical, not just editorial policy):** the
  template schema forbids a `default`/`preselected` field on any option
  entry; the linter rejects options presented in an order keyed to any
  field other than the template author's explicit `options[]` array
  order (preventing accidental "most likely" ordering bias from creeping
  in via later automated tooling); consequence/non-effect text fields are
  required (non-empty) for every option, preventing silent
  consequence-omission; rationale/condition prompt fields, if present,
  are schema-marked `optional: true` and the CLI (§8) must render them as
  visibly optional.
- **Eligibility mapping (resolves NB-1, §1.1 above):** `eligible_authority`
  is a required, template-specific field; template review is where the
  actual authority-eligibility judgment is made per decision class, not a
  generic role lookup.

---

## 11. Record Lifecycle Planning

| Transition | Initiating actor | Required evidence | Mutation model | Resulting artifact | Failure behavior | Non-effects |
|---|---|---|---|---|---|---|
| (none) → Draft | Human, via `create` | template ref | new `DecisionSession`, not yet a record | session file (staging only) | invalid template ref fails closed | no authority, no runtime effect |
| Draft → Awaiting Confirmation | Human, via `preview`+selection | selection + preview render | append-only session update | rendered preview | — | — |
| Awaiting Confirmation → Confirmed | Human, via `confirm` | confirmation evidence (§9) | append-only | `HumanConfirmationEvidence` | replay/staleness rejected (§9) | still not published |
| Confirmed → Published | Human, via `publish` | record+provenance+integrity complete | atomic promotion, no in-place edit ever again | canonical record + index entry | validation failure → quarantine, never partial publish | publication has no authority effect by itself (§11 Authority Contract) |
| Published → Suspended | Human Authority (per template's `eligible_authority`) | new `GovernanceRecordLifecycleEvent` + linked governance act | append-only event, original record untouched | lifecycle event, updated index `current_state` | — | **planned only, not built this increment** |
| Published → Superseded | same | new record + supersession link + lifecycle event | append-only | new record + lifecycle event | — | **planned only, not built this increment** |
| Published/Suspended → Revoked | same | new lifecycle event with evidence | append-only | lifecycle event | — | **planned only, not built this increment** |

Published records are never edited in place — every state change after
Published is represented as a new `GovernanceRecordLifecycleEvent` (and,
for supersession, a new `HumanGovernanceRecord`), never a mutation of the
original file, satisfying CHGR-REQ-109/110/111/156-class immutability
requirements (§23.13, §23.16). Suspend/supersede/revoke are **designed at
the schema/event level in this phase (§4/§13-schema fields exist) but
their CLI commands and their authority-check plumbing are explicitly
deferred** — this plan intentionally does not build "who is allowed to
revoke" logic in the first increment, since that logic sits directly on
top of the NB-1-adjacent eligibility question this plan resolves only at
the template level (§10), and a revocation authority check needs a
render-and-confirm workflow of its own (deferred to §29's later
increment) rather than a same-increment bolt-on.

---

## 12. Legacy Election Import Planning

Target: `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`.

**Boundary between artifact classes (required explicit definition):**
- **Legacy source record** — the existing Markdown file itself, untouched,
  forever the authoritative original text.
- **Import evidence** — a new `LegacyRecordImportEvidence` object: source
  path, source digest (SHA-256 of the file bytes at import time), source
  commit hash, import timestamp, and an explicit list of metadata fields
  CHGR-001 would want but which the legacy file cannot supply (e.g. no
  machine-readable `assurance_level` field existed at authoring time —
  disclosed as L0, per CHGR-001 §12's own instruction that the existing
  election "is, and must remain represented as, L0").
- **Canonical wrapper** — a `HumanGovernanceRecord` whose
  `decision_subject`/`selected_option_id`-equivalent fields are populated
  from the legacy file's actual text (byte-preserving quotation, not
  paraphrase), referencing the import evidence, with a `template_ref`
  pointing to a purpose-built "legacy import" template rather than
  forcing the historical election into an unrelated later template's
  shape.
- **Deterministic rendered representation** — regenerated Markdown from
  the canonical wrapper, kept clearly distinguishable from the original
  source file (e.g. explicit "imported representation of
  `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`, see source for the
  original" banner), never replacing or modifying the original.

**Constraints (all planning-level; import itself not performed):**
byte-for-byte source preservation (no edit to the original file, ever);
source digest retained in import evidence; commit provenance retained
(`git log` hash at import time); original wording quoted verbatim into the
canonical wrapper, not summarized; original timestamp preserved where the
source discloses one, else explicitly marked unavailable; no assurance
level stronger than L0 assigned; the import process performs no new
election — it is defined as a read-and-wrap operation with zero
decision-making content of its own; treating "import succeeded" as
"authority granted" is explicitly named as prohibited (mirrors §11's
identity≠authority discipline, §6 above).

This import is planned in full shape here but **not performed in 143D**,
and is recommended as a later, small, independently bounded increment
(§29) — it should not be bundled into the first schema/storage/CLI
increment, since it depends on that increment's record shape already
being stable and independently verified.

---

## 13. Provenance and Integrity Planning

Provenance (`GovernanceRecordProvenance`) and integrity
(`GovernanceRecordIntegrity`) are kept as two artifact classes (§4), and
this plan differentiates the five concepts the governing prompt requires
throughout:

- **Provenance** — what happened, in order, to produce this record
  (template, options shown, choice, rationale, exact preview, confirmation
  event, repo/commit context, and — for imports — source provenance).
- **Integrity** — is the stored payload the same bytes now as when
  published (digest evidence, checked by `verify`).
- **Identity** — who/what asserted the confirmation, at whatever assurance
  level actually applies (§9); never conflated with authority.
- **Authority** — whether the confirming party was actually eligible per
  the template's `eligible_authority` field (§10) and the applicable
  scope; a fact resolved by CHGR-001 §11 policy, never by this plan's
  technical evidence alone.
- **Applicability** — whether a record's subject/scope still matches a
  later situation a reader might apply it to; a reading-time judgment this
  plan's tooling only *displays evidence for* (§22), never resolves
  automatically.

**No technical evidence alone grants authority** — provenance completeness
and integrity validity are necessary but never sufficient conditions;
`pcae governance record verify` (§13 below) explicitly reports "structurally
valid and internally consistent," never "authorized" or "valid decision."

---

## 14. Verification Engine Planning

`pcae governance record verify <record_id>` is planned as deterministic
and fail-closed, checking (minimum set, mirrors CHGR-001 §21's nine
audit facts plus structural checks):

1. schema validity of the canonical payload against the packaged schema
   version referenced by the record;
2. template validity (does `template_ref` resolve, is it deprecated —
   surfaced as a warning, not a failure);
3. record identity well-formedness and index-registration consistency
   (§6);
4. reference integrity (provenance/integrity/index entries all
   cross-reference the same `record_id` consistently);
5. digest integrity (stored digest matches recomputed digest over the
   canonical payload and over the rendered Markdown);
6. provenance completeness (every field §13 requires is present and
   non-empty);
7. confirmation binding (the confirmation evidence's digest matches the
   record's actual content — detects post-confirmation tampering, §17
   scenario 7);
8. lifecycle consistency (recorded state matches the derived state from
   the lifecycle-event chain, once that chain exists — §11);
9. current-state derivation (Published vs. Superseded vs. Revoked, from
   event chain, not from a mutable field on the original record);
10. supersession/revocation status (explicit, not inferred from absence);
11. assurance-level truthfulness (declared level matches what the
    confirmation-evidence shape actually supports — e.g. an L2+ claim
    with no signature evidence fails closed);
12. legacy-import preservation (for imported records only — source
    digest still matches the live source file, §12);
13. artifact/rendering consistency (the Markdown rendering, if
    regenerated, matches the stored rendering byte-for-byte);
14. registry/manifest consistency (index entry matches the record file).

**Error categories (stable, sanitized):** `SCHEMA_INVALID`,
`DIGEST_MISMATCH`, `PROVENANCE_INCOMPLETE`, `CONFIRMATION_UNBOUND`,
`LIFECYCLE_INCONSISTENT`, `REGISTRY_MISMATCH`, `ASSURANCE_OVERCLAIM`,
`TEMPLATE_UNRESOLVABLE`, `IMPORT_SOURCE_DRIFT` — mirrors the existing
`schema_runtime/errors.py` convention of a small closed error-code set
rather than free-text failures.

Verification never determines substantive policy (it does not decide
"was this the right decision") and never invents authority (a
structurally perfect record with an ineligible confirmer still verifies
as *structurally valid*; whether it was *authoritative* is outside
verification's job, per §13 above).

---

## 15. Phase-Report Separation Planning

A CHGR publication and a canonical phase report remain structurally
disjoint artifact classes:

- Different storage roots: `.pcae/governance-records/` vs.
  `.pcae/phase-completion-report.md` / `.pcae/phase-reports/`.
- Different identity spaces: `record_id` vs. `phase_id`.
- Different triggering commands: `pcae governance record publish` vs.
  `pcae phase complete`.
- `governance record publish` never writes to
  `.pcae/phase-completion-metadata.json` or
  `.pcae/phase-completion-report.md`, never advances a phase, and never
  sends a phase notification.
- `pcae phase complete` is not modified by this plan at all — no shared
  code path is altered.

**Shared low-level infrastructure, and why reuse doesn't collapse the
classes:** both artifact families are planned to reuse
`canonical_artifact_promotion.py`'s generic stage→validate→atomically-promote
primitive (§7) and a common digest-computation utility. Reuse is
justified because both primitives are already artifact-agnostic (they
operate on "a payload, a target directory, a validator function," not on
phase-report-specific fields) — confirmed by inspection of
`canonical_artifact_promotion.py`'s existing signature, not assumed.
Sharing a generic promotion primitive does not collapse the classes any
more than two different file types sharing an OS's `rename()` syscall
collapses them; the artifact *shape*, *identity space*, and *triggering
command* remain fully separate, which is the actual boundary CHGR-001 §15
protects.

---

## 16. Typed Authority Compatibility Planning

Independent analysis, consistent with 143A's and 143B's (independently
re-confirmed) conclusion and CHGR-001 §19.1's citations (TAMC-REQ-005,
TAMC-REQ-036, TAMC-REQ-024/025, TAMPC-REQ-002/010/011):

- CHGR remains a **wholly separate artifact family** from the Typed
  Authority Model's sixteen frozen record families (including
  `human_authorization`). It is not reused, wrapped, or specialized from
  any `cltr_cutover/records/*.schema.json` type.
- `human_authorization.schema.json` records are token-scoped,
  non-authoritative, execution-permission artifacts for a specific
  technical cutover attempt (per TAMC-001's own text) — structurally the
  opposite of a CHGR, which is authoritative by construction of a human
  act, never a technical execution token.
- Both families independently share the same *meta-principle* (record
  existence/validity never alone implies authority — TAMC-REQ-036 for
  TAM, CHGR-001 §11 for CHGR) but implement it as two separate schema
  families, not a shared base type, because their subject matter
  (execution permission vs. human governance act) is categorically
  different, and forcing a shared base type risks smuggling
  execution-permission semantics into governance-act records or vice
  versa.
- A typed representation (CHGR's own schema) never establishes authority
  merely by existing — restated explicitly here as this plan's own
  instance of CHGR-001 §11 and TAMC-REQ-036's shared discipline.
- **Conclusion: unchanged from 143A/143B — no reuse, no wrapping, no
  subclassing. Separate artifact families, permanently.**

---

## 17. Security and Threat-Model Planning

| Threat | Prevention | Detection | Evidence | Fail-closed behavior | Deferred dependency |
|---|---|---|---|---|---|
| AI selects the human choice | CLI selection input requires a token from the actual TTY session driven by the human; no programmatic-selection API is exposed in the first increment | provenance shows selection event without a matching interactive session | provenance §13 | record construction refuses to proceed | — |
| AI writes rationale altering meaning | rationale field is stored byte-for-byte as typed, never regenerated/summarized by tooling | verify checks rationale field is unmodified since confirmation (digest binding, §9) | confirmation evidence | verify fails (`CONFIRMATION_UNBOUND`) | — |
| Preselected substantive option | schema forbids a `default`/`preselected` option field (§10) | template linter (§10) | template validation report | template fails validation, cannot be packaged | — |
| Enter-key default acceptance | empty token explicitly rejected before reaching record construction (§8) | — | — | re-prompt, no state change | — |
| Inactivity treated as consent | no timeout auto-confirms; session stays `abandoned`/`draft` indefinitely until explicit action | — | session state never reaches `confirmed` without explicit `confirm` | — | — |
| Fabricated human identity | identity evidence honestly scoped to achieved assurance level (§9); no claim beyond OS-user-level at L0/L1 | verify's `ASSURANCE_OVERCLAIM` check | confirmation evidence shape | verify fails | stronger identity (L2+) deferred |
| Forged confirmation | confirmation bound to content digest (§9), computed locally at confirm time | verify recomputes digest | integrity evidence | verify fails (`DIGEST_MISMATCH`) | cryptographic non-repudiation deferred to L2+ |
| Replayed confirmation | single-use confirmation state transition (§9) | session state machine | session state | second `confirm` call rejected | — |
| Altered decision after confirmation | publish reads from the confirmed, digest-locked payload only | verify's confirmation-binding check | integrity + confirmation evidence | verify fails, publish itself also re-checks digest before promoting | — |
| Template substitution | `template_ref` pins exact version; published record is immutable | verify's template-validity check | record's template_ref | verify flags if resolved template no longer matches referenced version content | — |
| Record substitution | atomic promotion, immutable published files, digest-checked | verify | integrity evidence | verify fails | — |
| Duplicate record identity | uniqueness check at publish time (§6) | index lookup | manifest | publish fails closed | — |
| Conflicting records (same subject) | not blocked (legitimate over time), but surfaced via inspection (§22), addressing 143C OBS-5 at planning level | observability tooling | index query by subject | — (advisory only) | detection tooling for automatic conflict flags deferred |
| Stale/revoked-record reuse | lifecycle-event-derived current state (§11), never a cached flag | verify's current-state derivation | lifecycle events | verify reports non-Published state explicitly | full suspend/supersede/revoke CLI deferred (§11) |
| Repository injection (a Markdown file dropped directly into `records/`) | canonical directory is populated only via atomic promotion from staging; a manually-dropped file has no index entry and no matching digest/provenance | verify / index cross-check | manifest absence | verify fails (`REGISTRY_MISMATCH`), inspection tools ignore unindexed files | — |
| Legacy-import semantic alteration | byte-preservation + verbatim quotation (§12) | import verification (`IMPORT_SOURCE_DRIFT`) | source digest comparison | import verify fails | import itself deferred |
| False assurance claims | assurance level constrained to what evidence shape supports (§9, §14) | verify's assurance-truthfulness check | confirmation evidence | verify fails | — |
| Publication without confirmation | schema/state machine requires `Confirmed` state before `publish` is accepted | state-machine check at publish time | session state | publish refuses | — |
| Agent self-authorization | no programmatic confirm API; confirm requires the same interactive-session evidence as selection | provenance/session-origin check | provenance | record construction refuses | stronger non-agent-provable identity deferred to L2+/external IdP |
| Phase-report/CHGR confusion | separate storage roots, identity spaces, commands (§15) | structural (different directories) | — | N/A — structurally prevented, not just detected | — |
| Compromised local session | out of scope for L0/L1 (host-security assumption, same as any local CLI tool); disclosed, not solved | — | — | — | stronger assurance (signing, hardware-backed) deferred |
| Unauthorized suspension/supersession/revocation | eligibility-check plumbing deferred along with the commands themselves (§11) — **no capability exists yet to misuse in the first increment** | — | — | — | deferred entirely to a later increment |

---

## 18. Failure and Recovery Planning

| Scenario | Behavior |
|---|---|
| Interrupted decision session | session remains in its last-written state (`draft`/`awaiting-confirmation`); never auto-advances; resumable in a later increment, safely re-preview-able even now via `preview` re-run |
| Interrupted confirmation | confirmation evidence write is atomic; a half-written confirmation is treated as "not confirmed," never as confirmed |
| Interrupted publication | staging→promote is atomic (§7); a crash mid-promotion leaves either nothing or a complete, unindexed file — never a partially-indexed record |
| Partial artifact writes | never index an entry until every required artifact (record, provenance, integrity, rendering) is written; write-then-index ordering, not index-then-write |
| Digest mismatch | `verify` fails closed (`DIGEST_MISMATCH`); record is flagged, never silently treated as valid |
| Registry mismatch | `verify` fails closed (`REGISTRY_MISMATCH`) |
| Duplicate publication | rejected at the uniqueness check (§6/§7) before any write |
| Stale expected state | publish re-validates session state immediately before promotion, not just at `confirm` time, closing a TOCTOU gap |
| Concurrent publication | file-lock/atomic-rename discipline reused from `canonical_artifact_promotion.py` (§7) |
| Malformed templates | rejected at packaging/validation time, never reach a live session |
| Unavailable identity evidence | confirmation proceeds at the lower assurance level the available evidence actually supports, honestly labeled — never fabricated to fill a gap |
| Failed legacy import | import evidence records the failure explicitly (planned artifact shape only, §12); the legacy source file itself is never touched regardless of import outcome |
| Unsupported schema/template version | `verify`/`inspect` report `SCHEMA_INVALID`/`TEMPLATE_UNRESOLVABLE` rather than guessing at a best-effort interpretation |

No ambiguous state is ever surfaced as "published" or "authoritative" —
every failure path above resolves to an explicit, named error state, per
CHGR-001's fail-closed core invariant (§3, invariant 12).

---

## 19. Testing Strategy

| Category | Representative cases |
|---|---|
| Schema validation | valid/invalid payloads per type; boundary cases (empty options array rejected; missing `eligible_authority` rejected) |
| Deterministic rendering | same canonical payload → byte-identical Markdown across repeated runs and across machines |
| Human-authorship boundary | no code path constructs a `selected_option_id` without an interactive session's explicit input |
| No-default | template with a `default`-shaped field fails packaging validation; CLI rejects empty selection token |
| Explicit-confirmation | `publish` without prior `confirm` fails; `confirm` without prior `preview` of current content fails |
| Cancellation/abandonment | `Ctrl-C`/`--abandon` never reaches `confirmed`; abandoned sessions never appear in the index |
| Confirmation-content binding | altering session content after `preview` invalidates a pending `confirm` |
| Atomic publication | crash-injection test interrupting staging→promote leaves no partial index entry (reuses existing `canonical_artifact_promotion.py` test patterns) |
| Crash recovery | simulated interruption at each write step; resulting state always resolves to either fully-absent or fully-valid |
| Concurrent publication | two processes publishing distinct/same `record_id` concurrently — distinct succeeds both, same collides deterministically |
| Immutable publication | attempted in-place edit of a published record file is rejected/detected by `verify` |
| Lifecycle transitions | Draft→Published happy path; illegal transitions (e.g. Draft→Published skipping Confirmed) rejected |
| Supersession/revocation | schema-level round-trip tests only this increment (no CLI yet) |
| Provenance | every required provenance field present after a full happy-path run |
| Assurance-honesty | confirmation evidence shape at L0 never permits an L2+ claim |
| Legacy-import preservation | (test-plan only, §12) — byte-identical source, correct digest, no election performed |
| Phase-separation | `governance record publish` leaves phase-completion files byte-identical before/after |
| Typed-authority compatibility | no CHGR schema imports/extends any `cltr_cutover` schema; independent JSON-Schema `$ref` audit |
| Packaging | wheel/sdist include the new schema resources; `schema_runtime` resolves them post-install |
| Registry/manifest | index entry count matches `records/` file count after any test sequence |
| CLI usability | `--help` text for every new command; error messages are actionable, not stack traces |
| Security/adversarial | one test per §17 threat row with a concrete exploit attempt |
| Regression | full existing `fast_green` tier stays green with the new module added (governance record tests marked appropriately, not added to the quick tier — per this repository's own known [[feedback_acceptance_check_timeout]] guidance) |

---

## 20. Packaging and Distribution Planning

- **Package location:** `src/pcae/schema_resources/chgr/` (schemas +
  templates), `src/pcae/commands/governance_record.py` (+
  `governance_template.py` if split), a new `src/pcae/governance/` package
  for the session controller, record-construction, provenance, integrity,
  and verification logic (mirrors the existing `src/pcae/cltr/` /
  `src/pcae/core/` separation of concerns — CLI-thin, logic-in-package).
- **Schema packaging:** `pyproject.toml`'s
  `[tool.hatch.build.targets.wheel] packages = ["src/pcae"]` already
  captures any new subpackage under `src/pcae/` with no change needed;
  resource discovery reuses whatever mechanism `schema_runtime/loader.py`
  already uses for `cltr_cutover` (to be confirmed unchanged at
  implementation time, not assumed here).
- **Installation verification:** extend the existing packaging smoke test
  (the one that caught the Phase 106D sdist-scope issue, per
  `pyproject.toml`'s own comment) to assert the new schema directory is
  present in both wheel and sdist builds.
- **Offline verification:** no network dependency introduced (UUID4
  allocation, local file storage) — offline installability is preserved
  by construction.
- **Registry/manifest inclusion:** the CHGR manifest (`.pcae/governance-records/manifest.json`)
  is a *runtime* artifact (created by use), not a packaged resource — not
  included in the wheel/sdist, same treatment as `.pcae/phase-reports/`.
- **Editable vs. installed execution:** resource loading must resolve
  correctly under both `pip install -e .` and a built wheel — the same
  constraint `schema_runtime` already satisfies for `cltr_cutover`,
  reused rather than re-solved.
- **Versioning/migration boundaries:** CHGR schema family gets its own
  version field independent of the package's own SemVer (mirrors
  `manifest.schema.json`'s existing versioning approach), so a package
  patch release never forces a schema version bump and vice versa.

---

## 21. Responsibility and Ownership Planning

Mapped to GPC6-REQ-040's existing role table (GLP-001 §8) — **no new role
introduced**, addressing NB-1 (§1.1) by explicitly not relying on
GPC6-REQ-040's narrower scope for anything beyond what it already covers:

| Responsibility | Owning role | Basis |
|---|---|---|
| Schema ownership | a future Stage 3 Implementer | GLP-001 §8 (Implementers), same pattern as §2/§3/§4 of GLP_PILOT_C6_STAGE2_CONTRACT |
| Template ownership/authoring | a future Stage 3 Implementer, reviewed via normal PR process | GLP-001 §8 |
| CLI implementation | a future Stage 3 Implementer | GLP-001 §8 |
| Publication custody | the implementation itself (mechanical, no human role — publication is an act of recording, not authorizing) | CHGR-001 §8 |
| Confirmation capture | the human performing the governance act, per each Decision Template's own `eligible_authority` field (§10) — **not** a generic "Human Authority" role per GPC6-REQ-040's table, resolving NB-1 | CHGR-REQ-051; §10 above |
| Verification | Independent Contract/Implementation Verifier pattern, mirroring 143C's own role, for a future dedicated verification phase (§29) | GLP-001 §6.1 Stage 4 pattern |
| Audit | any reader, via `inspect`/`verify` — non-role-gated, since inspection carries no authority (§14, §22) | CHGR-001 §21 |
| Import (planned, not built) | a future Stage 3 Implementer for the mechanism; the *decision* to import is not itself a new election (§12) | — |
| Suspension/supersession/revocation (planned, not built) | initiating actor named per-transition (§11), resolved at implementation time of that later increment, using each Decision Template's own `eligible_authority`, never a generic role | §10, §11 above |
| Future runtime consumption | **explicitly preserved as unresolved**, per 143A §20 and CHGR-001 §20.5's own disclosed judgment call — this plan does not assign it, since doing so would invent authority CHGR-001 has no basis to invent (identical reasoning to 143B's own §20.5 disposition) | CHGR-001 §20.5 |

---

## 22. Observability and Audit Planning

`pcae governance record inspect <record_id>` (non-authoritative, read-only)
surfaces: record identity; subject; the human's literal decision;
decision-maker identity evidence at its actual assurance level; the
authority basis *claimed* by the record (i.e. which `eligible_authority`
the referenced template names) — explicitly labeled as a claim, not a
verified grant; assurance level; template id+version; publication
timestamp; current lifecycle state (derived from the event chain, §11);
supersession/revocation status; provenance completeness (from `verify`);
integrity status (from `verify`); and an explicit "limitations" block
listing anything `verify` could not confirm (e.g. "no cryptographic
signature; assurance level L0/L1 only").

`inspect` never itself evaluates or grants authority — it only displays
what `verify` already independently determined and what the record itself
declares, with declared-vs-verified always visually distinguished.

Auditability depends only on files under `.pcae/governance-records/` —
no conversation history, session memory, or AI recollection is ever a
required input to `inspect` or `verify`, satisfying the governing prompt's
explicit requirement.

`pcae governance record list --subject <x>` (deferred command, §2) is the
planned home for surfacing 143C's OBS-5 gap (unlinked conflicting records
on one subject) as an advisory flag — planned here, not built this
increment.

---

## 23. Compatibility and Migration Strategy

| Context | Behavior |
|---|---|
| Current repo, no CHGR storage yet | `inspect`/`verify`/`list` report "no governance records found," never an error; `.pcae/governance-records/` is created lazily on first `publish`, mirroring how `.pcae/phase-reports/` already comes into existence |
| Repo with only the legacy election, pre-import | fully compatible — the legacy file is inert to CHGR tooling until a future, separately governed import runs (§12); no automatic detection/import is ever triggered implicitly |
| Future CHGR schema versions | each record embeds its own schema version; `verify` fails closed (`SCHEMA_INVALID`) on an unrecognized version rather than guessing compatibility |
| Future signing systems | assurance-level extension points (§9) absorb this without a breaking schema change to existing L0/L1 records |
| Future external identity providers | same extension-point mechanism (§9) |
| Future runtime consumers | explicitly out of scope (§17 Runtime Consumption Contract) — this plan defines no consumption API; a future contract must define the consumption boundary before any consumer is built |
| Older PCAE installations | an older install with no `governance` command simply lacks the feature; no compatibility shim needed since no prior version ever wrote to `.pcae/governance-records/` |
| Unknown record/template versions | fail-closed: `verify`/`inspect` report the version as unrecognized rather than attempting best-effort parsing |

**Fail-closed vs. read-only:** version mismatches and structural anomalies
always fail closed for `verify` (a definitive pass/fail signal) but remain
read-only-inspectable via `inspect` (which shows *what's there* even when
`verify` cannot confirm it), so a human is never blocked from looking at a
record just because automated verification cannot fully validate it.

---

## 24. Implementation File Map

*(Planned; no file below is created by this phase.)*

| File | Purpose | Owner | Depends on | CHGR-001 basis | Verification coverage |
|---|---|---|---|---|---|
| `src/pcae/schema_resources/chgr/manifest.json` / `.schema.json` | schema family index | Stage 3 Implementer | `schema_runtime` | §6, §23.6 | schema tests |
| `src/pcae/schema_resources/chgr/records/*.schema.json` (9 types, §4) | type definitions | Stage 3 Implementer | shared/* | §3–§14, §23.3–23.14 | schema tests |
| `src/pcae/schema_resources/chgr/templates/*.json` | packaged decision templates | Stage 3 Implementer + review | template schema | §6, §23.6 | template validation tests |
| `src/pcae/governance/session.py` | `DecisionSession` controller | Stage 3 Implementer | schema | §5, §23.5 | session tests |
| `src/pcae/governance/record.py` | record construction/rendering | Stage 3 Implementer | session, schema | §3–§4 | rendering/authorship tests |
| `src/pcae/governance/provenance.py` | provenance/integrity construction | Stage 3 Implementer | record | §10, §23.10 | provenance tests |
| `src/pcae/governance/publication.py` | staging/promotion/index | Stage 3 Implementer | `core/canonical_artifact_promotion.py` | §8–§9, §23.8/23.9 | publication/crash-recovery tests |
| `src/pcae/governance/verification.py` | verification engine | Stage 3 Implementer | schema, storage | §21, §23 various | security/adversarial tests |
| `src/pcae/commands/governance_record.py` | CLI surface | Stage 3 Implementer | governance/* | §5, §7, §23.5/23.7 | CLI usability tests |
| `src/pcae/commands/governance_template.py` | template inspect CLI | Stage 3 Implementer | governance/session | §6 | CLI tests |
| `tests/governance/*` | full test matrix (§19) | Stage 3 Implementer | all above | all | itself |
| `docs/contracts/` (no new file this increment) | — | — | — | — | — |
| `docs/PHASE_143E_...md` | future phase's own report | future Implementer | this plan | — | — |

---

## 25. Requirement Traceability

All 193 `CHGR-REQ-###` requirements were independently re-extracted from
the frozen contract (programmatic extraction against
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`, confirming
143C's own count and the same 22 contiguous, gap-free, non-overlapping
`§23.x` ranges). Every requirement is dispositioned below by its §23
subsection — no requirement is silently omitted, since every requirement
falls inside exactly one of the 22 ranges below and every range has an
explicit disposition row.

| §23.x | Range | Planned component/artifact | Test category | Increment | Deferred? |
|---|---|---|---|---|---|
| 23.1 Purpose | REQ-001–005 | schema+doc identity fields, §15 separation | schema/phase-separation tests | 1st | no |
| 23.2 Definitions | REQ-006–018 | schema field naming, template/session/record split (§4) | schema tests | 1st | no |
| 23.3 Core Invariants | REQ-019–030 | authorship boundary (§8/§17), rendering (§4), identity (§6), publication (§7), fail-closed (§13/§18) | authorship/no-default/rendering/atomic-publication tests | 1st | no |
| 23.4 Human Authorship | REQ-031–038 | session controller, rationale field handling (§3/§8) | human-authorship-boundary tests | 1st | no |
| 23.5 Interactive Decision | REQ-039–048 | CLI staged workflow (§8) | no-default, cancellation, confirmation-binding tests | 1st | no |
| 23.6 Decision Template | REQ-049–058 | template schema+linter (§10) | template validation tests | 1st | no |
| 23.7 Confirmation | REQ-059–066 | confirmation evidence (§9) | confirmation-content-binding tests | 1st | no |
| 23.8 Publication | REQ-067–074 | atomic publication (§7) | atomic-publication, crash-recovery tests | 1st | no |
| 23.9 Canonical Identity | REQ-075–082 | record id scheme (§6) | identity/collision tests | 1st | no |
| 23.10 Provenance | REQ-083–089 | provenance construction (§13) | provenance tests | 1st | no |
| 23.11 Authority | REQ-090–097 | eligibility field, identity≠authority discipline (§6/§13/§21) | security/adversarial tests (identity-forgery rows) | 1st | no |
| 23.12 Assurance | REQ-098–105 | L0/L1 model, extension points (§9) | assurance-honesty tests | 1st (L0/L1); L2–L5 deferred | partially |
| 23.13 Record Lifecycle | REQ-106–117 | 8-state schema/event model (§11) | lifecycle-transition tests (Draft→Published only, 1st increment) | 1st (schema+Draft→Published); suspend/supersede/revoke deferred | partially |
| 23.14 Legacy Import | REQ-118–127 | import boundary design (§12) | legacy-import preservation tests (test-plan only) | deferred (later increment) | yes |
| 23.15 Phase Separation | REQ-128–134 | separate storage/identity/commands (§15) | phase-separation tests | 1st | no |
| 23.16 Proposal Separation | REQ-135–141 | five-artifact-class boundary respected throughout (§2, §15) | phase-separation, typed-authority tests | 1st | no |
| 23.17 Runtime Consumption | REQ-142–149 | explicitly no consumer built (§2, §23) | N/A — negative requirement, satisfied by absence | n/a — non-implementation is the compliance | no (satisfied by non-action) |
| 23.18 Security | REQ-150–163 | threat table (§17) | security/adversarial test matrix | 1st (L0/L1 threats); stronger-assurance threats deferred | partially |
| 23.19 Compatibility | REQ-164–171 | typed-authority separation (§16), packaging/migration (§20/§23) | typed-authority compatibility, packaging tests | 1st | no |
| 23.20 Governance Responsibility | REQ-172–179 | responsibility table (§21), NB-1 disposition (§1.1) | n/a (documentation/planning correctness, reviewed not unit-tested) | 1st (planning-level) | no |
| 23.21 Audit | REQ-180–188 | inspection tooling (§22) | observability/audit tests | 1st | no |
| 23.22 Amendment | REQ-189–193 | not implemented; contract-evolution process only, no code | n/a | n/a — CHGR-001 itself is unmodified by any implementation increment | no (satisfied by non-modification) |

**NB-1/NB-2 in traceability:** NB-1 falls within 23.20's range and is
dispositioned at the planning level (§1.1, §21) — no code implements
GPC6-REQ-040's imprecise citation; CHGR-REQ-051 (23.6) is the operative
mechanism. NB-2 falls within 23.18's range (CHGR-REQ-154) and is
dispositioned as cosmetic-only (§1.2) with no implementation dependency
on its "see also" list. Both remain open, Non-Blocking, contract-text
items for a future dedicated repair phase — this plan neither hides nor
resolves them by silent implementation-side workaround beyond what §1.1
and §1.2 explicitly state.

---

## 26. Exit Criteria

Implementation authorization for the recommended next phase (§29) requires
all of the following, independently checkable against this document and
its future implementation:

1. All 193 requirements mapped (§25 — done, this phase).
2. NB-1 and NB-2 explicitly dispositioned (§1 — done, this phase).
3. No unresolved Blocking finding (§1.3 — confirmed, this phase).
4. Minimum implementation boundary defined (§2, §4 — done, this phase).
5. Schema and artifact families planned (§4 — done, this phase; not yet
   implemented).
6. CLI safety behavior planned (§8 — done, this phase; not yet
   implemented).
7. Publication and recovery behavior planned (§7, §18 — done, this phase;
   not yet implemented).
8. Legacy import planned without re-election (§12 — done, this phase; not
   yet performed).
9. Tests planned (§19 — done, this phase; not yet written).
10. Packaging planned (§20 — done, this phase; not yet implemented).
11. Authority and phase separation preserved (§15, §16, §21 — done, this
    phase; must be independently re-verified once implemented).
12. No runtime-enforcement capability included (§2, §23.17 — confirmed by
    this plan's own scope; must remain true through implementation).
13. Independent verification phase defined (§29 below names 143F as the
    verification phase following the 143E implementation increment).

Criteria 1–4 and 9–10 are satisfied **by this document**. Criteria 5–8 and
11–13 are satisfied **only once implemented and independently verified**
— this document alone does not authorize implementation to begin (§29).

---

## 27. Required Adversarial Planning Exercises

| # | Scenario | Prevention | Detection | Evidence | Failure state | Deferred dependency |
|---|---|---|---|---|---|---|
| 1 | AI supplies the selection | no programmatic selection API; interactive-session-origin requirement (§17) | provenance/session-origin mismatch | provenance | record construction refused | — |
| 2 | Substantive option preselected | schema forbids `default` field; template linter (§10) | template validation | validation report | template packaging fails | — |
| 3 | Enter without choosing | empty token rejected pre-construction (§8) | — | — | re-prompt, no state change | — |
| 4 | Session times out | no auto-confirm on timeout; session stays draft/awaiting (§18) | — | session state | resumable, never auto-decided | resume CLI deferred |
| 5 | Session abandoned | explicit `abandoned` state, excluded from index (§8/§11) | — | session file | never published | — |
| 6 | Confirmation replayed against different content | content-digest binding, refuses if content changed since preview (§9) | verify's confirmation-binding check | integrity/confirmation evidence | `confirm` refused / `verify` fails | — |
| 7 | Record changes after confirmation | immutable post-publish files, digest re-check at publish (§7/§9) | verify | integrity evidence | verify fails (`DIGEST_MISMATCH`) | — |
| 8 | Publication crashes halfway | atomic staging→promote (§7) | index absence | manifest | no partial record ever indexed | — |
| 9 | Two processes publish same record | uniqueness check inside locked promotion step (§6/§7) | index collision | manifest | second publish fails closed | — |
| 10 | Two current records conflict for one subject | not blocked (legitimate over time), surfaced via `list --subject` (§22, deferred command) | manual/tooling inspection | index query | advisory only, no automatic resolution | detection tooling deferred |
| 11 | Revoked record supplied to future consumer | lifecycle state derived from event chain, never cached (§11) | verify's current-state derivation | lifecycle events | verify reports non-Published explicitly | runtime consumer itself out of scope (§2) |
| 12 | Markdown file inserted directly into canonical storage | index absence for unindexed files (§17) | verify/inspect ignore/flag unindexed files | manifest cross-check | `REGISTRY_MISMATCH` | — |
| 13 | Imported legacy record missing metadata | explicit disclosed-unavailable-metadata list, never fabricated (§12) | import evidence inspection | import evidence | disclosed, not hidden | import itself deferred |
| 14 | Import logic normalizes wording, changing meaning | verbatim quotation requirement, no paraphrase (§12) | source-digest comparison | `IMPORT_SOURCE_DRIFT` | import verify fails | import itself deferred |
| 15 | Signature exists but signer lacks authority | identity (signature) and authority (eligibility) kept distinct (§13, §21); no signing implemented yet in this increment | eligibility check against template's `eligible_authority` | template + confirmation evidence | inspect labels authority basis as "claimed," never "verified" | signing itself deferred to L2+ |
| 16 | Valid human record applied outside its scope | `decision_subject`/scope fields are explicit and inspectable (§4, §22); scope-matching judgment left to the reader, never automated | inspection displays scope explicitly | record fields | no automatic gating exists to be bypassed (§2 scope) | scope-matching automation is a future, separately governed runtime-consumption concern |
| 17 | CHGR mistaken for a phase report | separate storage roots/identity/commands (§15) | structural | — | N/A — structurally prevented | — |
| 18 | Phase report mistaken for a CHGR | same as above, symmetric | structural | — | N/A | — |
| 19 | Agent tries to create and confirm its own authority | no programmatic confirm API; confirmation requires the same interactive-session evidence as selection (§9/§17) | provenance/session-origin check | provenance | record construction refused | — |
| 20 | Repository commit treated as consent | commit provenance is stored as *evidence of when/where*, never as *evidence of what was decided*; a commit alone never satisfies the confirmation-evidence requirement (§9/§13) | verify's provenance-completeness check | provenance | `PROVENANCE_INCOMPLETE` if confirmation evidence is missing regardless of commit presence | — |

---

## 28. Validation Requirements

Confirmed for this phase itself:

- **No production behavior changed:** no file under `src/pcae/` created,
  modified, or deleted.
- **No executable schema created:** no file under
  `src/pcae/schema_resources/` (new or existing) touched.
- **No CHGR storage created:** `.pcae/governance-records/` confirmed
  absent from the repository, same as at 143C's own check.
- **No legacy import performed:**
  `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` re-read only for
  planning purposes (§12), not written.
- **No human decision modified:** no election, authorization, or GAC-001
  §9 decision made, simulated, or presumed by this phase.
- **No frozen contract modified:** `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
  byte-identical to its 143C-verified state; NB-1/NB-2 dispositioned
  without editing the contract text (§1).
- **No authority granted:** this document is a plan, not an approval; §26
  explicitly states this document alone does not authorize implementation.
- **No phase lifecycle changed:** this phase touches only its own report,
  `docs/PHASE_143D_...md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, and
  `tasks/`, per its task contract's Allowed Files/Zones.
- **No runtime state changed:** `pcae runtime inspect` unchanged,
  Observed / observe / unavailable before and after.
- **No execution capability introduced:** no new command, code path, or
  dependency added.
- **Applicable validation run:** `git status`/`git diff` confirmed the
  change set is limited to the allowed files (§ below, "No-Go");
  documentation/governance consistency checks performed by direct
  re-reading of CHGR-001, 143A, 143C, and the election document rather
  than by a code-level test suite, since this phase adds no code.

---

## 29. Expected Outcome / Recommended Next Phase

This plan preserves the central boundary throughout every one of its 24
component/deliverable sections above: PCAE may structure, display,
validate, preserve, and publish a human governance act, but it may never
choose, infer, reinterpret, broaden, narrow, or confirm the substantive
human decision.

The governing prompt's own suggested next-phase title —
**143E — Canonical Human Governance Record Schema and Artifact Foundation
Implementation** — is **independently confirmed as the correct next
phase**, not merely assumed: §4's increment-strategy analysis
independently arrived at the same "schema + storage/publication +
verification, as one coherent phase" boundary before this section
compared it against the prompt's suggestion, and rejected each
alternative ordering (import-first, CLI-first, lifecycle-first,
verification-as-a-separate-later-step) on independent grounds (§4).

**Recommended: 143E — Canonical Human Governance Record Schema and
Artifact Foundation Implementation**, scoped exactly to §4's first
increment: the nine-type schema family (§4), canonical storage/publication
reusing `canonical_artifact_promotion.py` (§7), the bounded
`create/preview/confirm/publish/inspect/verify` CLI (§8), assurance levels
L0/L1 only (§9), and verification built alongside publication (§13) — with
`list`, `resume`, `suspend`, `supersede`, `revoke`, and `import`
explicitly out of scope for 143E and left to later, separately governed
increments (a plausible **143F — Canonical Human Governance Record
Implementation Independent Verification**, mirroring 143C's relationship
to 143B, followed by later, smaller increments for lifecycle transitions
and legacy import).

**This recommendation does not authorize 143E.** It does not implement
any schema, does not create any storage, does not perform the legacy
import, and does not itself constitute governance approval of anything
CHGR-001, Phase 143A, or Phase 143C describes.

---

## 30. No-Go — Confirmed Not Done By This Phase

- No governance contract (GLP-001, GAC-001, PGP-001, PPA-001, AGOC-001,
  TAMC-001, TAMPC-001, GPC6-001, GPC6R-001, GPC6C-001, CHGR-001) was
  modified.
- `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` was not modified,
  reinterpreted, or re-elected.
- No new human governance decision, election, or authorization act was
  made, simulated, or presumed by this phase.
- NB-1 and NB-2 were not repaired in CHGR-001's text — both remain
  disclosed, Non-Blocking, open items for a future dedicated repair
  phase (§1).
- No schema, CLI, storage, migration, or signing mechanism was
  implemented.
- No runtime enforcement or authority-resolution behavior was implemented
  or changed; runtime remains Observed / observe / unavailable.
- No file under `src/pcae/` or `tests/` was touched.
- No new role, responsibility, or authority was introduced beyond
  GPC6-REQ-040's existing table (§21).
- `GLP-PILOT-C6` was not advanced, authorized, or evaluated by this
  phase; this phase is orthogonal to that pilot's own lifecycle.
