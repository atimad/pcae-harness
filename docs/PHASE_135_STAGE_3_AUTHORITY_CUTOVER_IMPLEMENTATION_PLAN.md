# Phase 135Y — Stage 3 Authority-Cutover Implementation Plan

## Status

Planning-only. No implementation performed. No production, test, or schema source
changed by this phase.

## Relationship to prior artifacts

This plan translates **CLTR-CUTOVER-001 v1.0** (frozen in Phase 135W,
`docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md`, independently verified
in Phase 135X, `docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_INDEPENDENT_VERIFICATION.md`)
into an implementable, staged, dependency-aware sequence. It is bound by, and does not
amend, **CLTR-001** (`docs/PHASE_135_CANONICAL_LIFECYCLE_TRANSITION_RECORD_CONTRACT.md`),
**CLTR-SCHEMA-001 v1.0.1**
(`docs/PHASE_135_PRODUCTION_CLTR_SCHEMA_AND_VERSIONING_CONTRACT.md`), **PFN-001**
(`docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`), and **PFR-001**
(`docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_CONTRACT.md`). It also relies on
the Stage 3 readiness architecture (135V,
`docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_READINESS_ARCHITECTURE.md`) and on the
verified Stage 1 (135K/135L/135M/135N), Stage 2 (135Q/135R/135S/135T), and rollback
(135U) implementation and evidence.

This plan performs none of the work it describes. It is itself the only artifact
produced by 135Y.

---

## 1. Planning scope

135Y plans implementation of **CLTR-CUTOVER-001 only**. It distinguishes eleven
categories of future work, all unperformed by this phase:

| Category | Performed in 135Y? |
|---|---|
| Prerequisite contracts (schema minor revision, typed-model contract) | No — planned in §6–7, executed in 135Z |
| Prerequisite schema work | No — planned only |
| Inactive infrastructure (resolver, persistence, CAS) | No — planned only |
| Inactive authority resolution | No — planned only |
| Inactive cutover evidence (readiness package, certification) | No — planned only |
| Inactive authority publication | No — planned only |
| Cutover rehearsal (Stage-3-specific, not Stage 2) | No — planned only |
| Activation | No — planned only, gated behind a separate future phase |
| Post-activation verification | No — planned only |
| Legacy demotion | No — planned only |
| Legacy retirement | No — planned only |

135Y produces exactly one artifact: this document, plus the governed status/task/report
updates required to close the phase.

---

## 2. Current-state baseline

Verified live via the read-only commands run in this phase's initial inspection
(see "Required validation" below) and via inherited evidence from 135K–135X:

- **Legacy lifecycle is the sole production authority.** `pcae runtime inspect` reports
  `Runtime state: Observed`, `Execution capability: unavailable`,
  `Maximum plugin capability: observe`. No Stage 3 code path is reachable from any
  production entry point.
- **CLTR is derivative.** The `src/pcae/cltr/` package (shadow observation, Stage 1
  dual derivation, Stage 2 rehearsal, rollback rehearsal) writes only to non-production
  namespaces (shadow records, `.pcae/cltr-migration/epochs/<epoch>/...`, the
  `current-rehearsal` pointer). None of it is read by any of the four production entry
  points as an authority source.
- **Stage 1 dual derivation** (135K–135N): implemented and verified; shadow/dual
  records are constructed identically at all four entry points, non-authoritative.
- **Stage 2 forward rehearsal** (135Q/135R/135S/135T): implemented and verified;
  isolated `current-rehearsal` pointer, atomic replace, crash matrix, non-authoritative.
- **Stage 2 rollback rehearsal** (135U): implemented and verified; 43/43 + 26/26 tests;
  11-step atomic reversal sequence; confined to the rehearsal namespace; never touches
  production.
- **No Stage 3 implementation exists.** No production authority resolver, no Stage 3
  authority pointer, no typed authority-epoch implementation (current epoch encoding is
  the string-prefix format `"legacy|<stage>|<epoch>|<schema_id>|<schema_version>"`), no
  cutover request implementation, no readiness-package implementation, no
  human-authorization implementation, no production CAS/serialization implementation.
- **Test baseline (inherited, not re-executed by 135Y):** `fast_green` 4391/4391,
  inherited from 135U/135V/135W and carried through 135X without re-execution. 135Y
  performs no test source changes and does not re-run the full suite as a planning
  deliverable; test execution is scoped to implementation phases.
- **Governance baseline (this phase, freshly executed):** `pcae health` healthy,
  `pcae check` passed, `pcae status coherence` coherent, `pcae doctor task-memory`
  clean, `pcae push check` clean/nothing-to-push, `pcae runtime inspect` Observed /
  observe / execution unavailable, Telegram notification runtime configured and
  enabled for outbound delivery only.

---

## 3. Contract-to-component decomposition

Each CLTR-CUTOVER-001 section maps to one or more implementation components. For each
component: purpose, inputs, outputs, authority role, persistence, dependencies, side
effects, failure modes, verification evidence, and activation stage.

| # | Component | CLTR-CUTOVER-001 §§ | Purpose | Authority role | Persistence | Activation stage |
|---|---|---|---|---|---|---|
| 1 | Typed authority model | §6 | Replace string-prefix epoch encoding with typed kind/epoch/stage/state enums | None (types only) | N/A | Layer 1 |
| 2 | Authority epoch model | §6 | Monotonic, comparable epoch identity distinct from migration epoch | Read-only reference | Companion schema record | Layer 1 |
| 3 | Authority resolver | §4 | Single function all four entry points call to determine current authority | Read-only; legacy-preserving by default | None (pure function over persisted state) | Layer 2 |
| 4 | Authority-state persistence | §13, §16 | Durable record of current authority pointer/epoch/generation | Reference for resolver | New namespace (§9) | Layer 2 |
| 5 | Cutover request | §7 | Operator-issued request to attempt a cutover | Non-authoritative until certified | Request namespace | Layer 3/6 |
| 6 | Human authorization record | §8 | Durable, bound, one-time authorization evidence | Gate input | Authorization namespace | Layer 3/7 |
| 7 | Readiness evidence package | §9 | Deterministic aggregation of Stage 1/2/rollback/security/schema/concurrency evidence | Gate input | Readiness namespace | Layer 3 |
| 8 | Pre-cutover gate | §10 | Pure eligible/ineligible/uncertain/conflict evaluator | Decision, non-authoritative | None (pure function) | Layer 3 |
| 9 | Cutover candidate | §11 | Assembled candidate authoritative generation (pre-certification) | Non-authoritative | Candidate namespace | Layer 4 |
| 10 | Certification | §12 | Immutable step verifying request+readiness+authorization+target+CAS-expectation | Non-authoritative evidence | Certification namespace | Layer 4 |
| 11 | Authority publication | §13, §14 | CAS-guarded atomic pointer replacement | **Authoritative once activated** | Authority pointer namespace | Layer 5 (mechanism) / Layer 9 (activation) |
| 12 | Compare-and-swap | §14 | Expected-current check + atomic replace + readback | Enforcement mechanism | Authority pointer namespace | Layer 5 |
| 13 | Repository-level serialization | §15 | Cross-process lock preventing concurrent publication | Enforcement mechanism | Lock namespace | Layer 5 |
| 14 | Conflict evidence | §14, §16 | Durable record of stale-writer rejection / CAS mismatch | Diagnostic | Conflict namespace | Layer 5 |
| 15 | Recovery journal | §18 | Durable per-step state for resumable cutover | Recovery source of truth | Journal namespace | Layer 5 |
| 16 | Reconciliation | §18 | Read-only reconstruction of terminal state from journal + evidence | Diagnostic / recovery | None (reads existing namespaces) | Layer 5 |
| 17 | Report adapter | §20 | Derive canonical report from authoritative generation | Presentation (derivative) | Existing report namespace | Layer 6 |
| 18 | Metadata adapter | §20 | Derive completion metadata from authoritative generation | Presentation (derivative) | Existing metadata namespace | Layer 6 |
| 19 | Architecture Status adapter | §21 | Presentation-only status view | Presentation (derivative), never authority | Existing Architecture Status namespace | Layer 6 |
| 20 | Checkpoint adapter | §22 | Operational checkpoint distinct from authority publication | Operational, non-authoritative | Existing checkpoint namespace | Layer 6 |
| 21 | Promotion adapter | §22 | Compatibility-mode wrapper over existing `canonical_artifact_promotion.py` | Compatibility | Existing promotion namespace | Layer 6/Layer 10 |
| 22 | Notification-intent adapter | §23 | Derive dispatch intent from authoritative generation only | Gate for dispatch | None (in-memory derivation) | Layer 7 |
| 23 | Dispatch authorization | §23, §19 | Ensures no dispatch from non-authoritative generation | Enforcement | Existing PFN-001 marker | Layer 7 |
| 24 | Marker adapter | §24 | Bind marker identity to one authoritative generation + epoch | Compatibility / evidence | Existing marker namespace | Layer 7 |
| 25 | Receipt adapter | §25 | Bind receipt identity to one authoritative generation + epoch | Compatibility / evidence | Existing receipt namespace | Layer 7 |
| 26 | Compatibility layer | §32 | Legacy-format reads over new authority state | Compatibility, non-authoritative | N/A (adapter only) | Layer 6/Layer 10 |
| 27 | Migration status CLI | existing `pcae cltr migration status` | Read-only Stage 1/2 status | Diagnostic | N/A | Existing (135O) |
| 28 | Cutover status CLI | §33 (observability) | Read-only Stage 3 authority/readiness/certification/publication status | Diagnostic | N/A | Layer 2–5 (incremental) |
| 29 | Cutover reconciliation CLI | §18, §33 | Read-only reconciliation of Stage 3 journal state | Diagnostic | N/A | Layer 5 |
| 30 | Quarantine | §29 | Isolate suspect certification/publication artifacts | Containment | Quarantine namespace | Layer 4/5 |
| 31 | Historical reader | §14 (immutable history) | Read-only access to superseded authority generations | Diagnostic | Existing generation namespace | Layer 2 |
| 32 | Observability and audit | §33 | Durable per-decision audit record | Diagnostic | Audit namespace | All layers (cross-cutting) |

---

## 4. Implementation layers

No layer depends on a later layer. Layers 9–11 are separately governed phases, not
sub-steps of an implementation phase.

- **Layer 1 — Types, schemas, identities, and immutable records.** Typed authority
  model (§7), companion schema additions (§6), deterministic identity rules for every
  new record kind.
- **Layer 2 — Read-only authority resolution and status.** Authority resolver (§8) in
  legacy-preserving read-only mode; authority-state persistence (read path only);
  cutover/migration status CLI extensions; historical reader.
- **Layer 3 — Readiness package and gate evaluation.** Readiness evidence package
  (§13); pre-cutover gate (§14) as a pure evaluator with no side effects.
- **Layer 4 — Certification and inactive publication machinery.** Cutover request,
  human authorization, cutover candidate, certification (§15); quarantine.
- **Layer 5 — Concurrency, CAS, journaling, and recovery.** Repository-level CAS
  (§10); cross-process serialization; recovery journal (§11); reconciliation.
- **Layer 6 — Derived production representation adapters.** Report, metadata,
  Architecture Status, checkpoint, promotion adapters (§18); compatibility layer.
- **Layer 7 — External-effect authorization and exactly-once migration.**
  Notification-intent adapter, dispatch authorization, marker/receipt adapters (§19,
  §20).
- **Layer 8 — Inactive end-to-end cutover rehearsal.** Stage-3-specific rehearsal
  exercising Layers 1–7 in an isolated namespace, no production effect (§25).
- **Layer 9 — Authority activation.** Separately governed phase; not part of any
  implementation phase in this plan (§26).
- **Layer 10 — Legacy demotion and compatibility-only operation.** Separately governed
  phase(s), gated on Layer 9 verification (§28).
- **Layer 11 — Legacy retirement.** Separately governed phase, gated on sustained
  Layer 10 evidence (§29).

---

## 5. Prerequisite classification

Definitive table combining 135V findings, 135W's Prerequisite Register (§34), and
135X's findings register.

| ID | Source | Description | Category | Blocks planning? | Blocks impl.? | Blocks rehearsal? | Blocks activation? | Blocks demotion? | Blocks retirement? | Proposed phase | Acceptance evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PREREQ-1 | 135W §34 / 135V F-135V-1 | Typed authority-epoch model (string-prefix insufficient) | Type model | No | Yes | Yes | Yes | No | No | 135Z | Model tests, comparison/ordering tests |
| PREREQ-2 | 135W §34 / 135V F-135V-2 | Genuine compare-and-swap on production authority pointer | Concurrency | No | Yes | Yes | Yes | No | No | 136H | CAS unit tests + concurrent-writer fault injection |
| PREREQ-3 | 135W §34 / 135V F-135V-3 | Wire adapter comparison sources at real production call sites | Integration | No | No | Yes | Yes | No | No | 136L+ | All-four-entry-point integration tests |
| PREREQ-4 | 135W §34 / 135V F-135V-4 | Additive CLTR-SCHEMA-001 minor revision (cutover-certification / authority-epoch-transition / stale-writer fields) | Schema | No | Yes | Yes | Yes | No | No | 135Z | Schema contract freeze + independent verification |
| PREREQ-5 | 135W §34 | Atomic writes for Stage-3-authoritative report/metadata/marker | Persistence | No | Yes | Yes | Yes | No | No | 136L (adapters) | Crash-matrix tests on adapters |
| PREREQ-6 | 135W §34 / 135V F-135V-6 | Architecture Status must not be an authority source once active | Architecture | No | No | No | Yes | No | No | 136A (verification gate) | Source inspection confirming presentation-only derivation |
| PREREQ-7 | 135W §34 | Two-person cutover authorization (optional) | Governance | No | No | No | No (optional) | No | No | Deferred indefinitely | N/A |
| PREREQ-8 | 135W §34 | Authorization freshness/expiration window | Governance | No | No | No | No | No | No | Resolved in 135W (24h default) | Contract text |
| PREREQ-9 | 135W §34 | Disaster-recovery mechanism for corrupted pointer/store | Recovery | No | No | No | No | No | No | Out of scope, deferred | N/A |
| PREREQ-10 | 135W §34 | `_ENTRY_POINT_RECOVERY_CLASSIFICATION` fallback gap (`phase_report_create`/`notify_send_report` fall back to `"ordinary_finalization"`) | Recovery classification | No | No | No | No | No | No | Deferred, non-blocking, tracked for 136B | Source citation only |
| PREREQUISITE-135X-1 | 135X §39 | §15 concurrency model assumes checkpoint-level serialization that does not exist (`_save_checkpoint` is atomic-write, not CAS) | Concurrency | No | Yes (with PREREQ-2) | Yes | Yes | No | No | 136H | Same evidence as PREREQ-2 |
| PREREQUISITE-135X-2 | 135X §39 | §29 quarantine lacks explicit cross-reference to authority state when an already-authoritative generation is quarantined post-publication | Documentation/contract clarity | No | Yes | No | Yes | No | No | 135Z (schema/contract clarification) | Updated §29 cross-reference in the schema/typed-model contract |
| NONBLOCKING-135X-6 | 135X §39 | §30 schema-readiness table omits human-authorization/§8 fields from schema-gap analysis (covered in principle) | Documentation | No | No | No | No | No | No | 135Z | Updated schema-gap table |

Also included as named prerequisites per the phase-objective checklist (all traced
above or newly classified here):

| Item | Disposition |
|---|---|
| Authority-generation companion schema | PREREQ-4 (135Z) |
| Cutover request schema | PREREQ-4 (135Z), instance data in 136F |
| Certification schema | PREREQ-4 (135Z), instance data in 136F |
| Readiness package schema | PREREQ-4 (135Z), instance data in 136D |
| Authorization schema | PREREQ-4 (135Z) + PREREQUISITE-135X (schema-gap table fix), instance data in 136F |
| Publication evidence schema | PREREQ-4 (135Z), instance data in 136J |
| Concurrency/conflict schema | PREREQ-4 (135Z), instance data in 136H |
| Recovery journal schema | PREREQ-4 (135Z), instance data in 136H |
| Marker/receipt binding schema | PREREQ-4 (135Z), instance data in 136M+ |
| Repository-level CAS | PREREQ-2 / PREREQUISITE-135X-1 (136H) |
| Cross-process serialization | PREREQ-2 (136H) |
| Stale-writer rejection | PREREQ-2 (136H) |
| Cross-epoch reconciliation | Deferred per 135V §10 / 135U disposition — planned but not implemented before activation unless a concrete cross-epoch scenario is identified in 136H |
| Rollback/roll-forward policy implementation | Planned §30 below, implemented in 136H/136J boundary |
| Concurrent rollback-vs-forward hardening | Planned §30, implemented alongside PREREQ-2 |
| Production notification migration | Planned §19, implemented in 136M+ (own bounded sub-track) |
| All-four-entry-point resolver integration | PREREQ-3 (136L+) |
| Production derivative migration | Planned §18, implemented across 136L+ in bounded per-adapter phases |
| Human authorization storage | Planned §12, implemented in 136F |
| Platform durability assumptions | Planned §32, verified in a dedicated durability phase before 136H closes |

No prerequisite is hidden inside an implementation phase without being named in this
table.

---

## 6. Schema plan

No schema is modified by 135Y. This section proposes the sequence for the future
135Z schema revision (PREREQ-4), which must remain an **additive minor revision** of
CLTR-SCHEMA-001 (no MAJOR bump; §21/§38 of 135W confirm a minor revision implementing
PREREQ-4 does not itself require a CLTR-CUTOVER-001 version bump).

| Schema | Version target | Authority role | Canonicalization | Digest coverage | Compatibility | Unknown-field policy | Milestone |
|---|---|---|---|---|---|---|---|
| Authority-state record | CLTR-SCHEMA-001 1.1.0 (companion kind) | Read-reference only until Layer 9 | Same canonical JSON rules as existing CLTR representations | Full record | Additive-only, forward-compatible | Reject unknown required, ignore unknown optional (existing CLTR-SCHEMA-001 §2 policy) | 135Z contract / 136B implementation |
| Cutover request | 1.1.0 | Non-authoritative | Same | Full record | Additive-only | Same policy | 135Z / 136F |
| Readiness package | 1.1.0 | Gate input, non-authoritative | Same | Full record + per-source-evidence digests | Additive-only | Same policy | 135Z / 136D |
| Human authorization | 1.1.0 | Gate input | Same | Full record, digest-bound to request | Additive-only | Same policy | 135Z / 136F |
| Certification | 1.1.0 | Non-authoritative evidence | Same | Full record, binds request+readiness+authorization+target digests | Additive-only | Same policy | 135Z / 136F |
| Authority-publication evidence | 1.1.0 | Authoritative once Layer 9 activates | Same | Full record | Additive-only | Same policy | 135Z / 136J |
| Concurrency conflict | 1.1.0 | Diagnostic | Same | Full record | Additive-only | Same policy | 135Z / 136H |
| Recovery journal | 1.1.0 | Recovery source of truth | Same | Per-step digest | Additive-only | Same policy | 135Z / 136H |
| Cutover reconciliation result | 1.1.0 | Diagnostic | Same | Full record | Additive-only | Same policy | 135Z / 136H |

135Z must also close PREREQUISITE-135X-2 (explicit §29 quarantine/authority-state
cross-reference) and NONBLOCKING-135X-6 (schema-gap table completeness for §8 fields)
as part of the same contract revision, not as separate phases.

---

## 7. Typed authority model plan

Replace the current string-prefix epoch encoding
(`"legacy|<stage>|<epoch>|<schema_id>|<schema_version>"`) with typed models, planned
(not implemented) as:

- **Authority kind** — enum: `legacy`, `cltr_shadow`, `cltr_dual`, `cltr_rehearsal`,
  `cltr_cutover_candidate`, `cltr_authoritative`.
- **Authority epoch** — a comparable, monotonic identity distinct from
  `PCAE_CLTR_MIGRATION_EPOCH`; ordering must be total and independent of wall-clock
  time.
- **Migration stage** — enum mirroring the existing Stage 0–5 model (135M), typed
  rather than encoded as a free-form stage string.
- **Generation role** — enum: `shadow`, `dual`, `rehearsal`, `rollback`, `candidate`,
  `certified`, `authoritative`, `superseded`, `quarantined`.
- **Authority state** — the resolved output of the resolver: which kind is currently
  authoritative, at which epoch, over which generation.
- **Publication state** — enum: `not_attempted`, `preparing`, `cas_pending`,
  `published`, `readback_verified`, `conflict`, `quarantined`.
- **Cutover state** — enum spanning request → gate → certification → publication →
  post-verification.
- **Recovery state** — one value per recovery-journal state (§11 below).
- **Compatibility mode** — enum: `native`, `adapter`, `legacy_only`.

Migration from existing values is planned as pure, lossless conversion functions
(string-prefix → typed) with no change to what is currently produced; the first
implementation (135Z/136B) must remain legacy-authoritative and must not alter any
byte written to a production artifact.

---

## 8. Authority resolver plan

One shared resolver, planned for 136B:

- **Module location:** `src/pcae/cltr/authority.py` (new; parallel to existing
  `src/pcae/cltr/persistence.py`, `src/pcae/cltr/inspection.py`).
- **API boundary:** a single pure function, e.g. `resolve_authority(context) ->
  AuthorityState`, taking only durable state as input (no entry-point-specific
  branching, per CLTR-CUTOVER-001 §4).
- **Input state:** legacy pointer state, Stage 1/2 evidence (read-only), the new
  authority-state persistence namespace (§9 below) if present, current authority
  epoch.
- **Output object:** typed `AuthorityState` (authority kind, epoch, generation
  reference, compatibility mode).
- **Verification:** resolver output must be independently comparable against legacy
  derivation for every call, in shadow/dual mode, before any caller trusts it.
- **Fail-closed errors:** any ambiguity (e.g., corrupt or partially-written authority
  pointer) must raise, never silently default to an unverified state.
- **Compatibility handling:** legacy mode (`authority kind = legacy`) is the default
  and only mode until Layer 9 activation.
- **Legacy mode / inactive CLTR mode / active CLTR mode / recovery mode:** four
  explicit resolver output modes, all implemented in 136B, but only `legacy mode` may
  be *load-bearing* for production behavior before activation.
- **Unsupported ambiguity behavior:** raise a typed `AuthorityAmbiguityError`; no
  fallback derivation from Git history, filenames, or narrative parsing (forbidden per
  CLTR-001 §4.2).

Current callers that must eventually use the resolver: the four entry points in
§24 below. Caller migration is explicitly **not** planned before the resolver itself
is independently verified (136C) — per the phase objective's ordering principle.

---

## 9. Persistence namespace plan

No storage is implemented by 135Y. Proposed namespaces, non-colliding with existing
Stage 1 (`.pcae/cltr-migration/epochs/<epoch>/dual/...`) and Stage 2
(`.pcae/cltr-migration/epochs/<epoch>/rehearsals/<transition-id>/...`, pointer
`current-rehearsal`) namespaces:

| Concept | Candidate path (proposed only) |
|---|---|
| Authority state | `.pcae/cltr-authority/state/` |
| Authority generations | `.pcae/cltr-authority/generations/<generation-id>/` |
| Cutover requests | `.pcae/cltr-authority/requests/<request-id>/` |
| Readiness packages | `.pcae/cltr-authority/readiness/<package-id>/` |
| Authorizations | `.pcae/cltr-authority/authorizations/<authorization-id>/` |
| Certifications | `.pcae/cltr-authority/certifications/<certification-id>/` |
| Publication attempts | `.pcae/cltr-authority/publications/<attempt-id>/` |
| Recovery journal | `.pcae/cltr-authority/journal/` |
| Conflicts | `.pcae/cltr-authority/conflicts/<conflict-id>/` |
| Quarantine | `.pcae/cltr-authority/quarantine/<item-id>/` |
| Reconciliation | `.pcae/cltr-authority/reconciliation/` |
| Current authority pointer | `.pcae/cltr-authority/current-authoritative` (per 135V §21 proposal, distinct from legacy `latest.*` and Stage 2 `current-rehearsal`) |

Requirements carried into implementation phases: repository-contained (no paths
outside the repo root); traversal-safe and symlink-safe (mirroring existing
`cltr/persistence.py` containment checks); immutable finalized records (write-once,
one file per generation/request/certification); atomic pointer publication (via
`os.replace`, mirroring the existing Stage 2 `pointer.py` atomic-replace primitive);
no collision with Stage 1/Stage 2 namespaces (verified by path-prefix inspection in
136B); historical preservation (no deletion of superseded generations); explicit
authority disclosures (every resolver output must state which mode produced it).

Exact paths above are candidates only, consistent with 135V §21's proposal and
existing repository conventions (`.pcae/cltr-migration/...`); they are confirmed or
revised in the 135Z schema/typed-model contract, not fixed by this plan.

---

## 10. Concurrency and CAS implementation plan

Planned for 136H, addressing PREREQ-2 and PREREQUISITE-135X-1.

Must address expected-current checks (pointer digest, authority epoch, generation,
migration epoch, legacy authority state) before any write; a cross-process lock
distinct from in-process locking; stale-writer rejection (reject a write whose
expected-current no longer matches); compare-and-swap on the authority pointer;
lock recovery after abandoned locks; process-crash handling; conflicting concurrent
cutover requests; concurrent legacy finalization during a cutover attempt; concurrent
Stage 2 publication (must remain structurally non-colliding, per 135V §21's separate-
pointer architecture); concurrent rollback; and operator retry.

135X's PREREQUISITE-135X-1 finding is explicit that the existing checkpoint
persistence (`_save_checkpoint` in the finalization transaction) is an atomic
**write**, not a CAS — it does not check an expected-current value before replacing.
136H must implement a genuine expected-current check, not reuse checkpoint semantics.

Mechanism candidates to evaluate in 136H (decision deferred to that phase, not fixed
here): advisory file locking (`fcntl`/`flock`, POSIX-only — a durability limitation
per §32), a lock file plus an ownership record (PID + timestamp + digest), a journaled
CAS (write-ahead journal entry, then atomic pointer replace, then journal
completion), or a directory-rename protocol (stage in a temp directory, then
`os.rename` the finalized directory into place). Process-local locks alone are
explicitly insufficient — 136H must specify and test a mechanism that serializes
across separate OS processes, not just separate threads or async tasks in one
process.

Testing on macOS (development platform) and in temporary test filesystems (`tmp_path`
fixtures) must both be exercised in 136H/136I: macOS/APFS `os.replace` and `flock`
semantics differ subtly from Linux, and CI test filesystems may not preserve all
POSIX guarantees (e.g., some CI sandboxes disallow `fcntl` locks) — 136H must record
which primitives are verified-durable per platform, per §32.

---

## 11. Recovery-journal plan

Planned for 136H. Per-step journal states: request accepted; gate evaluation;
authorization verified; certification; publication preparation; CAS attempt; pointer
replacement; post-publication verification; derivative generation; notification
authorization; delivery uncertainty; marker; receipt; terminal reconciliation;
conflict; quarantine.

| State | Durable evidence | Retry | Replay | Operator review | Rollback/roll-forward | Resolver behavior |
|---|---|---|---|---|---|---|
| Request accepted | Request record | Yes | Yes | No | Rollback (cancel) | Legacy |
| Gate evaluation | Gate result record | Yes | Yes | No | Rollback | Legacy |
| Authorization verified | Authorization record | No (one-time use) | No | Yes if expired | Rollback | Legacy |
| Certification | Certification record | No (immutable once issued) | Read-only | Yes if stale | Rollback | Legacy |
| Publication preparation | Prep record | Yes | Yes | No | Rollback | Legacy |
| CAS attempt | Attempt record + expected-current | Yes (with new expected-current) | No | Yes on repeated conflict | Rollback | Legacy |
| Pointer replacement | Publication evidence | No (terminal write) | No | No | Roll-forward only past this point | Transitioning |
| Post-publication verification | Verification record | Yes (re-verify) | Yes | Yes on failure | Roll-forward | Active (pending verification) |
| Derivative generation | Adapter output digests | Yes | Yes | No | Roll-forward | Active |
| Notification authorization | Intent record | No | No | Yes if denied | Roll-forward | Active |
| Delivery uncertainty | PFN-001 marker (existing mechanism) | Yes (per PFN-001) | No | Yes | Roll-forward | Active |
| Marker | Marker record | No | No | No | Roll-forward | Active |
| Receipt | Receipt record | No | No | No | Roll-forward | Active |
| Terminal reconciliation | Reconciliation record | N/A | Read-only | No | N/A | Active |
| Conflict | Conflict record | Manual only | No | Yes | Manual decision | Held at prior state |
| Quarantine | Quarantine record | No | No | Yes | Manual decision | Held at prior state |

No journal state relies on filenames, timestamps, or latest-directory inference, per
CLTR-001 §4.2 item 9. Every state is a durable, digest-bound record read by
reconciliation, mirroring the existing Stage 2 rehearsal reconciliation design
(`src/pcae/cltr/migration/rehearsal/reconciliation.py`, `recovery.py`).

---

## 12. Human authorization implementation plan

Planned for 136F. Provider interface: a pluggable `AuthorizationProvider` abstraction
(local-file-backed implementation first; not implemented in 135Y). Local authorization
record: operator identity, request binding (digest of the cutover request), digest
binding (bound to the specific candidate generation, not reusable across candidates),
expiry/freshness (24-hour default window per 135W §34 PREREQ-8 resolution), revocation
(explicit revoke record), one-time use (consumed on certification, cannot re-authorize
a second certification), replay protection (authorization digest bound to a single
certification attempt), audit (durable record of every authorization decision,
granted or denied), inactive testing mode (fixture-only authorization for rehearsal,
clearly marked non-production), and a documented extension point for a future
multi-party authorization scheme (PREREQ-7, deferred indefinitely, not designed here
beyond the extension point).

Environment variables alone must never authorize a cutover — this is an explicit
CLTR-CUTOVER-001 requirement and one of the inactive-mode controls in §17 below.
Authorization storage must be implemented and independently verified in 136F/136G
before certification (§15) may consume it.

---

## 13. Readiness-package implementation plan

Planned for 136D. Assembles verified Stage 1 dual-derivation evidence, Stage 2
forward-rehearsal evidence, Stage 2 rollback-rehearsal evidence, security evidence
(§31), schema evidence (§6), concurrency evidence (§10), recovery evidence (§11), and
migration-status evidence into one deterministic package.

Plan: deterministic package identity (digest of the bound evidence set, not a
timestamp); source-evidence verification (each input evidence record's own digest is
re-verified, not merely referenced); common phase/transition/epoch binding (the
package is scoped to one migration epoch and one candidate generation); digest over
the full package; stale-evidence rejection (if any bound evidence has been superseded,
the package is ineligible, not silently stale); explicit limitations section (mirrors
the disclosed-limitation pattern already used in 135Q/135T); prerequisite status
(references the table in §5); gate consumption (read by the pre-cutover gate in §14);
and a read-only CLI (`pcae cltr-authority readiness show`, name illustrative). The
package remains derivative and non-activating — it never itself changes authority
state.

---

## 14. Pre-cutover gate implementation plan

Planned for 136D as a pure evaluator, implemented before any publication machinery.
Returns one of `eligible`, `ineligible`, `uncertain`, `conflict`. Input model: the
readiness package, the cutover request, the current resolved authority state.
Output model: the verdict plus a list of blocker IDs and referenced evidence records;
no side effects (the gate never writes authority state, only reads and returns a
decision). Deterministic result: identical inputs always produce the identical
verdict. Test matrix: one test per blocker condition in §41 (no-go criteria) plus
combinations of simultaneous blockers. CLI visibility: read-only gate-evaluation
command. Integration point: consumed only by certification (§15) and by the
observability CLI (§33); never wired into any production entry point directly.
Activation is prohibited from consuming the gate directly until Layer 9 — the gate's
existence does not itself enable activation. The gate must be independently verified
(136E) before certification (§15) may be implemented against it.

---

## 15. Certification implementation plan

Planned for 136F, as a separate immutable step after the gate (§14) is independently
verified. Verifies: the cutover request (identity, integrity); the readiness package
(gate verdict `eligible`, evidence digests intact); the human authorization (bound,
unexpired, unrevoked, unused); the target (candidate generation identity and digest);
the authority-source (current authority is the expected legacy/CLTR state); and binds
an explicit CAS expectation (expected-current pointer digest and epoch) into the
certification record so that publication (§16) cannot certify against one state and
publish against another. Produces a deterministic-identity, digest-bound
certification record. Failure states: any verification failure produces a rejected
certification (not an error thrown away — a durable rejection record) or, for
suspicious mismatches, a quarantine entry (§30). Certification has **no publication
side effect** — it is purely an evidence-producing step, independently verified
(136G) before authority publication (§16) may consume it.

---

## 16. Authority-publication implementation plan

Planned for 136J, without activating it (see §17 for the mechanical inactive-mode
guarantee). Defines: the current authority pointer (§9); a temporary pointer
(write-then-rename, mirroring Stage 2's atomic-replace pattern); the target certified
generation (from §15); the CAS check (§10) against the certification's bound
expected-current; atomic replacement (`os.replace`); durability assumptions (§32);
readback (re-read the pointer immediately after replace and verify it matches the
intended target); generation verification (confirm the readback generation's digest
matches the certified generation's digest); authority-state verification (confirm the
resolver, called fresh, now reports the new state — only true once Layer 9 is active);
uncertainty handling (if readback fails or times out, the attempt is recorded as
`uncertain`, never silently treated as success or failure); result evidence (durable
publication-attempt record); reconciliation (read by §11's reconciliation); and a
test-only inactive mode (the mechanism is exercised in rehearsal, §25, without ever
being reachable from a production entry point).

The initial implementation (136J) must remain **available in code but unable to
activate production authority**. This is guaranteed mechanically, not only by
documentation, via the two independent controls specified in §17.

---

## 17. Inactive-mode architecture

At least two independent controls, both implemented before 136J closes:

1. **No activation CLI and no activation configuration exist.** There is no
   command, flag, or environment variable in 136B–136J that can invoke
   `publish_authority(...)` from outside a test fixture — the function is
   reachable only from the test suite and from the rehearsal harness (§25), not
   from any of `src/pcae/commands/*.py`.
2. **A contract-version / explicit-flag gate.** Publication requires an explicit
   `activation_supported=True` marker that does not exist anywhere in the codebase
   until the separately governed activation phase (§26) adds it — its absence is a
   fail-closed guard, not an opt-out flag defaulting to a safe value.

Additional layered controls (implemented across 136B–136J, not substitutes for the
two above): the authority resolver is forced to legacy mode by default (§8); the
publication API is inaccessible from the production finalization transaction (no call
site in `finalization_transaction.py` until the activation phase adds one); the human
authorization provider has no production-configured backend until 136F/the activation
phase explicitly wires one; and any attempted publication call from a non-test,
non-rehearsal context raises a fail-closed `ActivationNotSupportedError` rather than
silently no-op'ing.

---

## 18. Production derivative adapter plan

Planned across bounded per-adapter phases starting at 136L, each independently
checkpointed rather than migrated in one phase:

| Adapter | Source authoritative generation | Current legacy implementation | Migration step | Retirement stage |
|---|---|---|---|---|
| Canonical report | Certified authoritative generation (post-activation) | `src/pcae/core/phase_reports.py` | Add CLTR-sourced derivation path behind compatibility mode; verify byte-for-byte parity with legacy derivation before switching default | Layer 10 |
| Completion metadata | Same | `phase_reports.py` completion-metadata path | Same pattern | Layer 10 |
| Architecture Status | Same | `src/pcae/core/architecture_status.py` | Confirm presentation-only (PREREQ-6); no authority read added | Layer 10 |
| Checkpoint | Same | Existing checkpoint save/load in `finalization_transaction.py` | Compatibility-mode wrapper only (§23) | Layer 10 |
| Promoted report representation | Same | `src/pcae/core/canonical_artifact_promotion.py` | Compatibility-mode wrapper; Gap B (non-atomic `latest.*` writes) tracked as F-135V-5, deferred to before 136A per 135V, not required for 135Y | Layer 10 |
| Notification intent | Same | PFN-001 mechanism (`notification_certification.py`) | See §19 (own bounded sub-track) | Layer 10 |
| Marker | Same | Existing marker mechanism | See §20 | Layer 10 |
| Receipt | Same | `delivery_receipt.py` | See §20 | Layer 10 |
| Repository transition view | Same | `pcae cltr migration status` / `pcae phase-report reconcile` | Extend read-only views, do not replace | Layer 6 (additive), no retirement needed |
| Commit attribution | N/A | Git commit metadata (never an authority source, per CLTR-001 §4.2 item 6/7) | No migration — commit attribution is never authoritative | N/A |

Each adapter migration requires its own independent checkpoint (parity verification
against the legacy derivation) before the next adapter begins; no single 136-series
phase migrates more than one or two closely-related adapters.

---

## 19. Notification migration plan

Preserves PFN-001. Separated into: intent derivation (from the authoritative
generation only, never from a non-authoritative candidate); payload generation
(existing report-rendering logic, unchanged in content contract per PFR-001); the new
authorization step (§7's dispatch authorization component, verifying the generation
producing the notification is genuinely the current authority); the dispatch adapter
(wraps the existing Telegram/sink dispatch, no sink-level change); attempt identity
(existing `.pcae/phase-reports/.last-notified.json` marker mechanism, extended with an
authority-epoch field, not replaced); uncertainty handling (existing PFN-001
ATTEMPTED/SENT/SKIPPED_WITH_REASON/FAILED_WITH_REASON outcomes, unchanged); retry
(existing retry semantics, unchanged); marker (§20); reconciliation (existing
`certify_notification_transition()` reconciliation, extended to cross-check authority
epoch); and receipt (§20).

Guarantees carried into 136M+: no dispatch from a non-authoritative generation (the
dispatch adapter checks the resolver before every send); exactly one ordinary
terminal delivery (unchanged PFN-001 invariant); no duplicate during recovery
(existing idempotency marker, extended); legacy delivery code becomes adapter-only
before legacy authority is demoted (Layer 10 precondition, not a Layer 7
precondition); and notification migration is independently verified (its own 136-
series verification phase) before activation (§26) may proceed. Notification migration
is scheduled as its own bounded phase or sub-track, not folded into the general
adapter migration of §18.

---

## 20. Marker and receipt migration plan

For each of marker and receipt: identity (existing deterministic identity rules,
unchanged); source generation (bound to the authoritative generation, not to
whichever generation happened to run last); digest (existing digest mechanism,
extended to include the authority-epoch field); authority epoch (new field, additive);
lifecycle transition (existing CLTR-001 §7 state-machine states, unchanged); external-
effect state (existing PFN-001 outcome states, unchanged); conflict behavior (a
marker/receipt bound to a superseded epoch is treated as historical, never
reactivating); recovery (existing reconciliation, extended to check epoch
consistency); compatibility (old markers/receipts, written before this migration,
remain readable under the compatibility layer, §26); independent verification (own
136-series verification phase).

Old markers or receipts must never reactivate legacy authority — enforced by the
resolver's fail-closed design (§8): the resolver only ever reads the current authority
pointer, never infers authority from marker/receipt presence, per CLTR-001 §4.2 items
4–5.

---

## 21. Report and metadata migration plan

Deterministic derivation from the authoritative generation, addressing: visibility
sequencing (report and metadata become visible together, not independently, avoiding
a window where one reflects the new authority and the other the old); atomic or
coherent publication (both derived and written before either is considered
"published," mirroring the existing dual-write coherence pattern already used for
report+metadata pairs); `latest` compatibility (existing `latest.md`/`latest.json`
readers continue to work under the compatibility layer, §26, until Layer 10);
historical reports (never rewritten, per CLTR-001 §14 immutable-history contract);
PFR-001 (unchanged — the 13-section structure and completeness contract apply
identically regardless of derivation source, per PFR-001's own note that only the
input source changes post-cutover, not the contract); recovery after partial
derivative publication (recovery journal §11 states `derivative generation` and
`post-publication verification` cover this explicitly); the old report-promotion
mechanism (compatibility-wrapped, §18); phase-report reconciliation (existing
`pcae phase-report reconcile` extended to read the new namespace, not replaced); and
the Telegram report source (unchanged dispatch adapter, §19).

Scheduled after inactive authoritative-generation machinery (Layers 1–6) is verified,
and before authority activation (Layer 9) — i.e., within the 136L+ adapter-migration
range, gated by its own independent verification.

---

## 22. Architecture Status migration plan

Architecture Status remains presentation-only, per PREREQ-6 and 135V F-135V-6.
Generation binding: Architecture Status reads the authoritative generation's phase-
identity fields only for display; authority epoch: displayed as metadata, never
consulted to *determine* authority; chapter grouping: unchanged existing logic
(`src/pcae/core/architecture_status.py`); completed/current/planned derivation:
unchanged; long-title handling: unchanged; historical compatibility: unchanged
rendering of pre-CLTR phases; no fallback authority: Architecture Status must never
be read by the resolver (§8) as an authority source — this is the specific hazard
135V §17 identified as "the one confirmed live authority-adjacent hazard," and PREREQ-6
requires this be independently confirmed (source inspection, not just a documentation
assertion) before activation (136A verification gate). Recovery: no recovery role —
Architecture Status is regenerated from the authoritative generation on demand, never
itself a durable authority reference.

---

## 23. Checkpoint and promotion migration plan

Existing checkpoint (`_save_checkpoint`/`_load_checkpoint` in
`finalization_transaction.py`) and report-promotion
(`canonical_artifact_promotion.py`) mechanisms become explicitly derivative /
compatibility operations, not a hidden second authority. Operational checkpoint
states: unchanged (resumability within one finalization transaction); authority
publication state: a distinct concept (§16), never conflated with a checkpoint;
compatibility promotion: `promote_artifact()` becomes a compatibility-mode wrapper
that reads from the authoritative generation once active, unchanged in its atomic-
write behavior (aside from the disclosed Gap B `latest.*` non-atomicity, tracked
separately as F-135V-5); recovery checkpoint: unchanged; pointer relationships: the
checkpoint pointer and the authority pointer (§9) remain structurally separate files,
per 135V §21's architectural reasoning for keeping Stage 2's `current-rehearsal` and
production's `latest.*` unmerged — the same reasoning applies to `current-
authoritative`; migration ordering: this migration happens within Layer 6, after
adapters (§18) are independently verified, before activation (Layer 9); independent
verification: own 136-series phase, explicitly confirming checkpoint/promotion is not
a second authority source (a fresh adversarial check against CLTR-001 §4.2's 9
forbidden patterns).

---

## 24. All-four-entry-point migration plan

The four entry points, identified from source (not from phase-brief prose), confirmed
identically by 135V §12, 135W §4/§26, and 135X §4/§25:

1. `run_phase_complete` — `src/pcae/commands/phase.py` — CLI: `pcae phase complete`
2. `run_task_finish` — `src/pcae/commands/task.py` — CLI: `pcae task finish` (plus
   recovery variant `run_task_finish_recover`)
3. `run_phase_report_create` — `src/pcae/commands/phase_reports.py` — CLI:
   `pcae phase-report create`
4. `run_notify_send_report` — `src/pcae/commands/notifications.py` — CLI:
   `pcae notify send-report`

All four converge on `run_finalization_transaction(entry_point=...)` in
`src/pcae/core/finalization_transaction.py`.

Per-entry-point migration stages (all four must move together at each stage — no
caller-by-caller authority activation):

1. **Observe resolver output** (136B/Layer 2) — all four entry points call the
   resolver in shadow mode; output is logged/compared, never consumed.
2. **Compare legacy and resolver decisions** (136C, part of independent
   verification) — automated comparison across a representative sample of
   finalization runs; mismatches are Blocking findings, not silently accepted.
3. **Consume resolver in legacy-only mode** (136L range) — entry points begin
   calling the resolver for informational fields only; behavior is provably
   identical to pre-migration behavior (parity tests).
4. **Consume certified generation in inactive mode** (Layer 8 rehearsal, §25) — all
   four entry points exercise the certified-generation path inside the rehearsal
   harness only, never in production.
5. **Cut over to active authority** (Layer 9, §26) — all four entry points switch
   together, in the same activation phase, to reading the authority resolver's
   output as load-bearing.
6. **Disable legacy authority reads** (Layer 10, §28) — all four entry points stop
   reading legacy pointer state, only after post-activation verification (§27)
   passes.

Shared integration tests (introduced starting 136C) cover ordinary finalization and
at least one recovery path (`run_task_finish_recover`) per entry point, per the
existing 135M requirement that all-four-entry-point + recovery-path coverage is
independently gating, never averaged.

`_ENTRY_POINT_RECOVERY_CLASSIFICATION`'s two-key gap (PREREQ-10) is closed no later
than stage 3 above (136B range), since consuming the resolver for recovery-path
entry points requires the classification to be complete first.

---

## 25. Cutover rehearsal plan

Planned as Layer 8, its own phase (136-series, after Layers 1–7 are independently
verified), before any activation planning proceeds. Constructs a real Stage 3
request/evidence/certification (not synthetic stand-ins); exercises CAS and
concurrency (§10) against the rehearsal-namespace copy of the authority pointer
mechanism; assembles authoritative-generation candidates through the full pipeline
(§9 candidate → §15 certification → §16 publication logic); generates all derivatives
(§18–§22) from the candidate; simulates authority publication in an isolated
namespace (a rehearsal-scoped authority pointer, structurally distinct from both the
production `current-authoritative` path and Stage 2's `current-rehearsal`, to avoid
conflating rehearsal-of-Stage-3 with rehearsal-of-Stage-2); simulates recovery (replays
the recovery journal, §11, against injected faults); simulates rollback/roll-forward
decisions (§30); performs no production authority change; performs no external
delivery (notification dispatch is stubbed/mocked, never live); creates no production
markers or receipts.

This rehearsal is Stage-3-specific and does not reuse Stage 2's rehearsal harness
as-is — Stage 2 rehearsed atomic publication of a *rehearsal* generation with no
certification, authorization, or CAS-against-expected-current-authority step; Stage 3
rehearsal must add those steps as new, independently verified evidence, not represent
them as already covered by 135S/135T. This rehearsal phase has its own independent
verification phase (a 136-series pair, implementation + verification, following the
established 135-series pattern).

---

## 26. Activation plan

Authority activation (Layer 9) is a separate, later, separately governed phase, not
part of any phase in this plan's roadmap (§35). It may proceed only after: all
Layers 1–8 are implemented; each has its own independent implementation verification;
the Layer 8 cutover rehearsal has passed; the rehearsal has its own independent
verification; all Blocking and Prerequisite-classified findings from §5 are closed
(or explicitly re-classified as non-blocking-for-activation with documented
justification); explicit human authorization (§12) is granted for the specific
activation attempt; and a final readiness review re-confirms the readiness package
(§13) is not stale.

Activation is narrowly scoped: it performs the single CAS-guarded publication (§16)
that first makes a CLTR generation authoritative, and nothing else. It must not
include legacy code deletion, broad refactoring, unrelated cleanup, or execution-
capability enablement (runtime remains Observed/observe/execution-unavailable — Stage
3 authority is orthogonal to the separate Runtime/Permission-Broker execution-capability
track).

Go/no-go checkpoints: readiness-package freshness check; gate re-evaluation
immediately before publication; authorization re-verification; CAS expected-current
re-check against the live pointer (not a cached value); and an explicit operator
go/no-go confirmation step. Abort conditions: any checkpoint failing halts activation
with no partial state change (the CAS mechanism guarantees this structurally — either
the full atomic replace succeeds or the prior authoritative pointer is untouched).

---

## 27. Post-activation verification plan

Immediately after activation, a dedicated verification phase (following the
established independent-verification pattern) must confirm: exactly one authority;
exactly one authority epoch; exactly one current generation; all four entry points
(§24) now consistently resolve the same authority; production reports, metadata,
Architecture Status, checkpoint/promotion, notification, marker, and receipt all
reflect the new authoritative generation; recovery and reconciliation correctly
identify the new authority after a simulated crash; compatibility reads (old-format
readers) still function; stale legacy processes (a process holding a pre-activation
in-memory reference) are rejected by the fail-closed resolver rather than silently
using stale authority; and no execution capability was introduced as a side effect of
activation.

No further legacy demotion (§28) proceeds until this verification phase passes.

---

## 28. Legacy demotion plan

Planned in stages, each its own governed phase, after successful post-activation
verification:

1. **Legacy authority reads disabled** — the resolver stops treating legacy pointer
   state as a valid fallback; acceptance: all four entry points pass their test
   suite with legacy reads structurally removed, not merely unused.
2. **Legacy outputs retained as compatibility derivatives** — `latest.*` and similar
   legacy-format outputs continue to be written, now as a compatibility adapter over
   the CLTR-authoritative generation, per §18/§26.
3. **Legacy fallback disabled** — any remaining "if CLTR unavailable, use legacy"
   branch is removed; acceptance: fault-injection tests confirm no silent fallback
   occurs.
4. **Legacy recovery authority disabled** — the recovery journal (§11) no longer
   accepts legacy-derived recovery state as authoritative.
5. **Legacy implementation retained but unreachable** — legacy derivation code
   remains in the repository (for historical/compatibility reads, §26) but is no
   longer on any authority-determining code path.

Each stage requires an explicit phase, documented acceptance criteria, independent
verification, an explicit rollback/roll-forward decision for that stage (can this
stage be reversed, and how), and historical-compatibility proof (old reports/markers/
receipts remain readable).

---

## 29. Legacy retirement plan

Planned separately from demotion, requiring: sustained stable CLTR authority (a
minimum evidence window, to be set by the retirement-planning phase itself, not fixed
here — mirroring 135M's own deferral of exact thresholds to a later phase); no legacy
authority reads (§28 stage 1 complete); no legacy fallback (§28 stage 3 complete);
historical compatibility (§26 compatibility layer verified against real historical
data, not only synthetic fixtures); migration documentation (a retirement-specific
document, not this plan); a removal inventory (exact files/modules proposed for
deletion, enumerated explicitly); a regression baseline (full test suite green
immediately before and after removal); independent verification; and a release note
describing upgrade implications for any external consumer of legacy-format artifacts.

Legacy code is **not** retired within Track 135 unless a future phase explicitly
justifies doing so with its own governed contract — this plan does not schedule
retirement within the 135/136 phase range.

---

## 30. Rollback and roll-forward implementation plan

Distinguishes: **Stage 2 rollback** (135U, already implemented — rehearsal-namespace
only, unrelated to Stage 3 authority); **Stage 3 pre-activation cancellation**
(cutover request or certification is simply abandoned before publication — no special
mechanism needed beyond the request/certification lifecycle itself); **Stage 3
rehearsal rollback** (within Layer 8's isolated rehearsal namespace, reusing the CAS
mechanism to reverse a simulated publication); **pre-external-effect authority
rollback** (after production publication but before any notification/marker/receipt
has been produced — a genuine CAS-guarded reversal to the prior authoritative
generation is possible and planned for 136H); **post-external-effect compensating
roll-forward** (after notification/marker/receipt exist — reversal is not assumed
valid; the plan requires a roll-forward, not a rollback, since undoing a delivered
notification is impossible — this must never assume pointer rollback is valid after
notification dispatch, per the phase objective's explicit instruction); and **disaster
recovery** (out of scope, PREREQ-9, deferred).

Implementation milestones (136H unless noted): cross-epoch reconciliation (deferred
per §5, addressed only if a concrete scenario is identified during 136H); concurrent
rollback-versus-forward (must be mutually exclusive via the same CAS/serialization
mechanism as §10 — a rollback attempt and a roll-forward attempt on the same
generation must not both succeed); expected-current CAS (§10, reused here); no-
current-authority prohibition (rollback must never leave the pointer unset — mirrors
135V §10's disposition that "no pointer" is a legitimate rehearsal-namespace state but
forbidden in production; a rollback that would leave no authority must instead default
explicitly to legacy, by convention, matching 135V's stated default); historical-epoch
reactivation prohibition (rollback may only target the immediately prior generation,
never an arbitrary historical one, without a separate, explicitly justified disaster-
recovery phase); operator-visible recovery (every rollback/roll-forward decision is
surfaced via the observability CLI, §33).

---

## 31. Security implementation plan

Planned for implementation and testing starting in 136B and re-verified before both
Layer 8 rehearsal and Layer 9 activation (two distinct security-verification gates,
not one). Covers: path traversal and symlink escape (extending the existing
containment checks already present in `src/pcae/cltr/persistence.py` to the new
namespaces in §9); pointer substitution (an attacker or bug replacing
`current-authoritative` with an attacker-controlled path — mitigated by the
containment checks plus CAS digest verification); generation substitution (swapping
the target of a certified generation after certification — mitigated by certification
binding the target digest, §15); manifest substitution; schema substitution (rejecting
records that don't validate against the frozen additive schema, §6); authorization
substitution (replay of a stale or foreign authorization record — mitigated by §12's
binding and one-time-use); readiness-package substitution (stale-evidence rejection,
§13); stale writer (§10's expected-current check); race conditions (§10's
serialization); quarantine bypass (§30 component, ensuring quarantined items cannot
re-enter the eligible path without explicit operator review); compatibility-pointer
confusion (ensuring the compatibility layer, §26, never mistakes a legacy-format read
for an authority determination); historical-generation confusion (ensuring the
historical reader, §3 item 31, is always clearly marked non-authoritative); wrong
authority epoch; wrong migration epoch; wrong final revision; and conflicting replay.

Security verification occurs before Layer 8 inactive rehearsal begins (verifying
Layers 1–7 are safe to rehearse against) and again before Layer 9 activation
(verifying the rehearsal itself surfaced no new gaps) — two gates, not a single
end-of-track review.

---

## 32. Platform durability plan

Documents filesystem/platform assumptions, to be verified in a dedicated durability-
verification phase before 136H closes (not asserted by documentation alone):

| Assumption | Classification |
|---|---|
| macOS/APFS `os.replace` atomicity | Required; verified for existing Stage 2 pointer mechanism (135S/135T); re-verification required for the new authority-pointer namespace |
| Linux filesystem `os.replace` atomicity (ext4, on CI runners if applicable) | Required where CI targets Linux; unverified until a dedicated CI-platform test run |
| Directory/file `fsync` before pointer replace | Required for crash-consistency claims; unverified in the current Stage 2 implementation per available evidence — must be confirmed or explicitly disclosed as a gap in 136H |
| Advisory file locking (`fcntl`/`flock`) | Required if chosen as the CAS mechanism (§10); POSIX-only, unsupported on non-POSIX platforms — disclosed limitation, not a blocker for this repository's macOS/Linux-only development and CI targets |
| Crash consistency across process kill (`SIGKILL`) | Required; verified via the existing crash-matrix pattern (135S/135T) extended to the new namespace |
| Network filesystems (NFS, etc.) | Unsupported; explicitly out of scope — the repository's containment model already assumes a local, non-networked filesystem |
| CI/test-environment filesystem limitations (tmpfs quirks, sandboxed lock restrictions) | Unverified until 136H's test suite runs in the actual CI environment; must be verified, not assumed, before CAS is declared implementation-complete |

---

## 33. Observability and audit plan

Read-only commands (all additive to the existing `pcae cltr migration ...` /
`pcae phase-report ...` CLI families, not replacements), implemented incrementally
across Layers 2–5: authority status; readiness status; cutover request status;
certification status; publication state; conflict state; recovery state; current
authority; historical authorities; reconciliation; compatibility state. All commands
are read-only unless a future, explicitly governed phase adds a cutover action —
135Y proposes no such command. Durable audit records: every authority-relevant
decision (resolver output, gate verdict, certification issuance/rejection,
publication attempt, rollback/roll-forward decision) is written to a durable,
digest-bound audit record, mirroring the existing provenance-event pattern already
used elsewhere in this repository's governance tooling.

---

## 34. Test strategy

| Test layer | Phase introduced | Isolation | Baseline | Independent verifier required? | Blocking criteria |
|---|---|---|---|---|---|
| Model tests | 135Z/136B | Isolated worktree | New (no prior baseline) | Yes | Any model round-trip failure |
| Schema tests | 135Z | Isolated worktree | New | Yes | Any schema-validation gap |
| Identity tests | 136B/136F | Isolated worktree | New | Yes | Non-deterministic identity |
| Canonicalization tests | 136B | Isolated worktree | New | Yes | Non-canonical digest mismatch |
| Resolver tests | 136B | Isolated worktree | New | Yes (136C) | Any legacy/resolver mismatch |
| Gate tests | 136D | Isolated worktree | New | Yes (136E) | Any incorrect verdict |
| Certification tests | 136F | Isolated worktree | New | Yes (136G) | Any certification issued against invalid input |
| CAS tests | 136H | Isolated worktree, concurrent-process harness | New | Yes (136I) | Any stale write accepted |
| Concurrency tests | 136H | Concurrent-process harness | New | Yes (136I) | Any race condition reproduced |
| Crash/fault-injection tests | 136H | Isolated worktree | New | Yes (136I) | Any unrecoverable state after crash |
| Containment tests | 136B/136H | Isolated worktree | New | Yes | Any traversal/symlink escape |
| Recovery tests | 136H | Isolated worktree | New | Yes (136I) | Any journal state unresolvable |
| Adapter tests | 136L+ | Isolated worktree | Parity against legacy | Yes (per-adapter) | Any parity mismatch |
| All-four-entry-point tests | 136B–136L | Full integration | New | Yes | Any entry-point-specific divergence |
| Notification exactly-once tests | 136M+ | Full integration, mocked sink | Existing PFN-001 baseline | Yes | Any duplicate or missing dispatch |
| Marker/receipt tests | 136M+ | Full integration | Existing baseline | Yes | Any cross-epoch reactivation |
| Compatibility tests | Layer 10 phases | Full integration | Historical fixture data | Yes | Any historical-read failure |
| Cutover rehearsal tests | 136 (Layer 8) | Isolated rehearsal namespace | New | Yes | Any production-effect leak |
| Activation verification tests | Activation phase (Layer 9) | Production (governed, single attempt) | New | Yes | Any post-activation inconsistency (§27) |
| Legacy-demotion tests | Layer 10 phases | Full integration | Pre-demotion baseline | Yes | Any silent fallback |

Isolated worktrees are used for baseline classification throughout, consistent with
this repository's existing test-isolation conventions.

---

## 35. Phase roadmap

Derived from the dependency graph (§36) and the prerequisite table (§5), not assumed
from convenient lettering:

- **135Z** — Stage 3 Companion Schemas and Typed Authority Model Contract Freeze
  (closes PREREQ-1, PREREQ-4, PREREQUISITE-135X-2, NONBLOCKING-135X-6)
- **136A** — Stage 3 Schema and Typed Authority Contract Independent Verification
- **136B** — Authority Resolver and Read-Only Authority-State Implementation (Layer 2;
  entry-point stage 1 observation, §24)
- **136C** — Authority Resolver Independent Verification (entry-point stage 2
  comparison, §24)
- **136D** — Readiness Package and Pre-Cutover Gate Implementation (Layer 3)
- **136E** — Readiness Package and Gate Independent Verification
- **136F** — Cutover Request, Human Authorization, and Certification Implementation
  (Layer 4)
- **136G** — Cutover Request and Certification Independent Verification
- **136H** — CAS, Concurrency, and Recovery-Journal Implementation (Layer 5; closes
  PREREQ-2, PREREQUISITE-135X-1; includes durability verification, §32; includes
  rollback/roll-forward implementation, §30)
- **136I** — CAS and Recovery Independent Verification
- **136J** — Inactive Authority-Publication Implementation (Layer 5/6 boundary;
  guarantees inactive-mode controls, §17)
- **136K** — Inactive Authority-Publication Independent Verification
- **136L** — Production Derivative Adapter Migration Plan and First Bounded Adapter
  (entry-point stage 3, §24; closes PREREQ-3, PREREQ-5)
- **136M+** — Bounded per-adapter implementation and verification phases (one adapter
  or tightly related group per phase: report/metadata, Architecture Status +
  PREREQ-6 confirmation, checkpoint/promotion, notification (own sub-track per §19),
  marker/receipt), each with its own independent verification
- **136-Layer-8** — Stage 3 Cutover Rehearsal Implementation (entry-point stage 4,
  §24) and its own Independent Verification (paired phases)
- **Activation phase** (unnumbered here; scheduled only after every phase above
  passes independent verification and all Blocking/Prerequisite findings in §5 are
  closed) — Authority Activation (Layer 9, entry-point stage 5) and Post-Activation
  Verification (§27)
- **Demotion phases** (Layer 10, §28) — one phase per demotion stage, each
  independently verified, only after activation verification passes
- **Retirement phase** (Layer 11, §29) — separately justified, not scheduled within
  Track 135/136

This is the recommended sequence; exact numbering beyond 135Z may shift as later
phases discover additional prerequisites, consistent with 135M §53's existing
disclaimer that phase letters are non-binding while ordering discipline is binding.

---

## 36. Phase dependency graph

```
135Z (schema/typed-model contract)
  └─▶ 136A (verification)
        └─▶ 136B (resolver, read-only)
              └─▶ 136C (verification) ──────────────┐
                    └─▶ 136D (readiness+gate)        │  entry-point
                          └─▶ 136E (verification)     │  stages 1-2
                                └─▶ 136F (request/auth/certification)
                                      └─▶ 136G (verification)
                                            └─▶ 136H (CAS/concurrency/recovery/rollback)
                                                  └─▶ 136I (verification)
                                                        └─▶ 136J (inactive publication)
                                                              └─▶ 136K (verification)
                                                                    └─▶ 136L (adapters begin, entry-point stage 3)
                                                                          └─▶ 136M+ (bounded adapters, each independently
                                                                                     verified; notification is its own
                                                                                     parallel sub-track off 136L)
                                                                                └─▶ Layer-8 rehearsal impl (entry-point stage 4)
                                                                                      └─▶ Layer-8 rehearsal verification
                                                                                            └─▶ [ACTIVATION GATE: all above
                                                                                                 independently verified +
                                                                                                 all Blocking/Prerequisite
                                                                                                 findings closed]
                                                                                                  └─▶ Activation phase
                                                                                                        (entry-point stage 5)
                                                                                                        └─▶ Post-activation
                                                                                                             verification (§27)
                                                                                                              └─▶ [DEMOTION GATE]
                                                                                                                    └─▶ Demotion
                                                                                                                         stage 1..5
                                                                                                                         (§28, entry-
                                                                                                                         point stage 6
                                                                                                                         at stage 1)
                                                                                                                          └─▶ [RETIREMENT
                                                                                                                               GATE:
                                                                                                                               sustained
                                                                                                                               evidence]
                                                                                                                                └─▶ Retirement
                                                                                                                                     (§29, separately
                                                                                                                                     justified)
```

Parallelizable: 136M+'s per-adapter phases (report/metadata, Architecture Status,
checkpoint/promotion, marker/receipt) may proceed in parallel with each other once
136L closes, provided each has an independent checkpoint; the notification sub-track
(§19) may also proceed in parallel with the adapter phases, since it depends only on
136J (inactive publication) and the dispatch-authorization component, not on the
report/metadata adapters. Strict ordering elsewhere as shown. No activation phase
depends on unverified implementation. No demotion phase precedes post-activation
verification.

---

## 37. Commit strategy

Future implementation phases should prefer: one implementation commit; one focused
test/verification-repair commit where necessary (mirroring the pattern already used
in 135R, 135S/135T, and 135U); and one governed completion commit (metadata + report,
mirroring every 135-series phase to date). Commit counts are not mandated where scope
genuinely differs (e.g., 136H's concurrency work may reasonably need more than one
implementation commit given its cross-cutting nature). Explicit phase-commit
ownership remains required for every future phase — ownership is never inferred from
recent Git history, consistent with CLTR-001 §4.2 item 6's prohibition on treating
Git history as commit authority.

---

## 38. Feature configuration rollout

Configuration stages, none of which may jump directly from `unavailable` to `active
CLTR authority`:

`unavailable` (no Stage 3 code reachable; today's state) →
`available but inactive` (136B: resolver exists, forced legacy mode) →
`readiness-only` (136D: gate/readiness package exist, non-consuming) →
`rehearsal-only` (Layer 8: full pipeline exercised in isolated namespace only) →
`activation-authorized` (Layer 9 precondition: human authorization granted for a
specific attempt, not a standing flag) →
`active CLTR authority` (Layer 9: publication succeeded, resolver now load-bearing) →
`recovery-only` (a degraded mode entered only via the recovery journal, §11, never
via configuration) →
`legacy compatibility` (Layer 10: legacy retained as compatibility-only) →
`legacy retired` (Layer 11).

Each transition requires contract-bound evidence (readiness package, gate verdict,
certification, or post-activation verification, as applicable) and governance (an
independently verified phase), never a bare environment-variable flip. This mirrors
the existing pattern already enforced for Stage 2 (`RehearsalConfiguration`'s
`_RESERVED_STAGE3_ENV_VARS` fail-closed rejection of any reserved Stage-3 variable
today).

---

## 39. Migration and compatibility strategy

Pre-CLTR historical phases, shadow-era phases (135K/135L), Stage 1 phases
(135M/135N), Stage 2 rehearsal evidence (135Q–135T), post-cutover phases, old reports,
old metadata, old markers, old receipts, old Architecture Status snapshots, and old
checkpoints are all read exclusively through explicit compatibility adapters (§26),
never by rewriting history. Historical Git attribution is never treated as an
authority source (CLTR-001 §4.2 item 6, unchanged by this plan). No history rewrite of
any kind is planned or permitted by any phase in this roadmap.

---

## 40. Acceptance criteria by milestone

| Milestone | Acceptance criteria |
|---|---|
| Schema readiness (135Z/136A) | Additive-only revision frozen; independently verified; PREREQUISITE-135X-2 and NONBLOCKING-135X-6 closed |
| Resolver readiness (136B/136C) | Resolver produces identical output to legacy derivation across a representative sample of finalization runs, in shadow mode, across all four entry points including recovery paths |
| Gate readiness (136D/136E) | Gate is a pure function; full no-go test matrix (§41) passes; no side effects observed |
| Certification readiness (136F/136G) | Certification correctly rejects every fault-injected invalid input; no publication side effect observed |
| Concurrency readiness (136H/136I) | CAS rejects every stale-writer scenario; cross-process serialization verified on macOS and in CI test filesystems; recovery journal resolves every injected crash point |
| Inactive publication readiness (136J/136K) | Both independent inactive-mode controls (§17) verified present; publication mechanism functionally correct in test/rehearsal contexts only |
| Derivative migration readiness (136L+) | Each adapter achieves byte-for-byte or field-for-field parity with legacy derivation before being considered migrated |
| Rehearsal readiness (Layer 8) | Full pipeline exercised with zero production-effect leaks; independently verified |
| Activation readiness | All prior milestones independently verified; all Blocking/Prerequisite findings closed; human authorization granted for the specific attempt |
| Post-activation verification | All items in §27 confirmed; no execution capability introduced |
| Demotion readiness (per stage) | Stage-specific acceptance criteria in §28 met; independently verified |
| Retirement readiness | All items in §29 met; independently verified; separately justified |

No single aggregate "Stage 3 complete" criterion exists — each milestone is judged
independently.

---

## 41. No-go criteria by milestone

| Milestone | No-go criteria |
|---|---|
| Implementation (any 136-series phase) | Unresolved Blocking defect in the phase's own scope; unresolved schema gap affecting that phase's records |
| Inactive rehearsal (Layer 8) | Ambiguous authority observed in any resolver output; more than one code path capable of resolving authority; absent CAS; absent cross-process serialization; incomplete recovery journal for any in-scope state |
| Activation | Any of: unresolved Blocking defects anywhere in Layers 1–8; unresolved schema gaps; ambiguous authority; multiple resolver paths; absent CAS; absent cross-process serialization; incomplete recovery journal; stale-writer acceptance observed in testing; notification exactly-once uncertainty; marker/receipt mismatch risk; all-four-entry-point inconsistency; missing human authorization; missing cutover rehearsal; missing independent verification of any Layer 1–8 phase; unsupported filesystem durability for the target deployment platform; unclear post-cutover roll-forward policy |
| Demotion (any stage) | Post-activation verification (§27) has not passed; any legacy-fallback path still reachable for the specific behavior being demoted |
| Retirement | Insufficient sustained-stability evidence window; any remaining legacy authority read; any remaining legacy fallback; historical-compatibility proof incomplete |

---

## 42. Risk register

| Risk | Probability | Impact | Detection | Prevention | Mitigation | Owner phase | Latest acceptable closure |
|---|---|---|---|---|---|---|---|
| Dual authority (two sources both claim authoritative) | Low | Critical | Resolver comparison tests (136C) | Single-authority invariant (§8), fail-closed resolver | Immediate rollback via CAS reversal | 136B/136C | Before 136L |
| No authority (pointer unset in production) | Low | Critical | Resolver ambiguity error | Explicit legacy-default convention (§30) | Fail-closed to legacy | 136H | Before Layer 9 |
| Split-brain (concurrent conflicting writers) | Medium | Critical | CAS conflict evidence (§10) | Cross-process serialization | Conflict record + operator review | 136H/136I | Before Layer 9 |
| Stale process (in-memory reference outlives activation) | Medium | High | Post-activation verification (§27) | Fail-closed resolver, no caching of authority state across calls | Reject stale reads | 136B, re-verified 136C | Before Layer 9 |
| Concurrent cutover requests | Medium | High | Certification target-verification (§15) | CAS expected-current binding | Reject second request, quarantine if suspicious | 136F/136H | Before Layer 9 |
| Concurrent legacy finalization during cutover | Medium | High | Structural separate-pointer architecture (§9, §21) | Distinct pointer files, no shared write path | No collision possible by construction | 136H | Before Layer 9 |
| Publication uncertainty (readback ambiguous) | Low | High | §16 readback verification | Explicit `uncertain` outcome, never silent success/failure | Reconciliation resolves from journal | 136H/136J | Before Layer 9 |
| Recovery-journal corruption | Low | Critical | Digest verification per journal entry | Digest-bound, immutable journal entries | Quarantine + manual review | 136H | Before Layer 9 |
| Readiness-evidence staleness | Medium | Medium | Package digest/staleness check (§13) | Deterministic package identity bound to evidence digests | Gate returns `ineligible` | 136D | Before Layer 9 |
| Authorization replay | Low | High | One-time-use + digest binding (§12) | Bound, expiring, one-time authorization records | Reject reused authorization | 136F | Before Layer 9 |
| Notification duplication | Low | High | Existing PFN-001 idempotency marker, extended | Dispatch-authorization gate (§19) | Existing PFN-001 recovery semantics | 136M+ | Before Layer 9 |
| Report/marker/receipt mismatch | Medium | Medium | Cross-checking epoch fields (§20) | Shared authority-epoch binding across all three | Reconciliation flags mismatch | 136M+ | Before Layer 9 |
| Legacy fallback leakage | Medium | High | Fault-injection tests (§28 stage 3) | Explicit fallback removal, not just disuse | Independent verification per demotion stage | Layer 10 | Before demotion stage 3 closes |
| Historical compatibility failure | Low | Medium | Compatibility tests against real historical fixtures | Explicit compatibility adapters (§26), no history rewrite | Adapter repair | Layer 10 | Before retirement |
| Filesystem containment failure | Low | Critical | Containment tests (§31) | Reuse of existing `cltr/persistence.py` containment checks, extended | Fail-closed rejection | 136B/136H | Before 136L |
| Platform durability gap | Medium | High | Durability verification (§32) | Explicit per-platform classification, no unverified assumption | Disclosed limitation or additional test | 136H | Before 136H closes |
| Operator error (wrong go/no-go decision) | Medium | High | Explicit checkpoint list (§26) | Structured go/no-go checklist, not ad hoc judgment | Abort-and-retry, no partial state (CAS guarantee) | Activation phase | At activation |
| Implementation-plan drift (later phases deviate from this plan without justification) | Medium | Medium | Phase-report cross-reference to this plan | Each future phase must cite which layer/section it implements | Plan amendment via a governed update, not silent deviation | All future phases | Ongoing |

---

## 43. Independent verification requirements

Every authority-relevant implementation phase in the roadmap (§35) has a paired
independent verification phase. Each verification phase must: re-derive requirements
from the frozen contracts (CLTR-CUTOVER-001, CLTR-001, CLTR-SCHEMA-001), not from the
implementation phase's own report; add fresh adversarial tests beyond the
implementation phase's own test suite; use isolated baselines (fresh worktrees, per
§34); reproduce any reported failures rather than trusting the implementation phase's
characterization; inspect source and call paths directly (matching the standard
already set by 135L/135N/135R/135T/135X); verify production side effects (confirming,
for every phase before Layer 9, that no production behavior changed); classify
findings using the CONFIRMED/NON-BLOCKING/BLOCKING/PREREQUISITE/DEFERRED taxonomy
(§ "Required findings classification" below); repair only within the verification
phase's own scope (not silently expand into new implementation); and stop before the
next implementation phase begins. No phase combines multiple unverified authority-
bearing implementations — each Layer's implementation is verified before the next
Layer's implementation phase starts.

---

## 44. Final planning verdict

**IMPLEMENTATION PLAN COMPLETE — READY FOR PREREQUISITE EXECUTION**

"Ready for prerequisite execution" means 135Z (the first prerequisite contract phase)
may begin next. It does **not** mean Stage 3 is ready for activation — activation
remains gated behind the full roadmap in §35, the dependency graph in §36, and the
activation-milestone criteria in §26/§27/§40/§41.

---

## Findings classification

| ID | Title | Source | Affected component | Affected milestone | Authority impact | Concurrency impact | Recovery impact | Exactly-once impact | Schema impact | Implementation phase | Verification phase | Latest acceptable resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PREREQUISITE-135Y-1 | Typed authority-epoch model required before any Stage 3 code | 135W/135V (PREREQ-1) | Typed authority model (§7) | Schema readiness | High (ambiguous string-prefix comparison today) | None | None | None | Yes | 135Z | 136A | Before 136B |
| PREREQUISITE-135Y-2 | Genuine CAS required; checkpoint save is atomic-write only | 135X (PREREQUISITE-135X-1), 135V (F-135V-2) | CAS/concurrency (§10) | Concurrency readiness | High | High | Medium | None | Medium | 136H | 136I | Before Layer 9 |
| PREREQUISITE-135Y-3 | Adapter comparison sources not yet wired at production call sites | 135V (F-135V-3), 135W (PREREQ-3) | All-four-entry-point plan (§24) | Derivative migration readiness | Medium | None | None | None | None | 136L | Per-adapter verification | Before Layer 9 |
| PREREQUISITE-135Y-4 | CLTR-SCHEMA-001 additive minor revision required for Stage 3 record kinds | 135V (F-135V-4), 135W (PREREQ-4) | Schema plan (§6) | Schema readiness | Medium | None | None | None | High | 135Z | 136A | Before 136B |
| PREREQUISITE-135Y-5 | Atomic writes required for Stage-3-authoritative report/metadata/marker | 135W (PREREQ-5) | Derivative adapter plan (§18) | Derivative migration readiness | Medium | Low | Medium | Low | None | 136L | Per-adapter verification | Before Layer 9 |
| PREREQUISITE-135Y-6 | Architecture Status must be independently confirmed presentation-only before activation | 135V (F-135V-6), 135W (PREREQ-6) | Architecture Status migration (§22) | Activation readiness | High (if violated) | None | None | None | None | N/A (verification-only) | 136A verification gate | Before Layer 9 |
| NON-BLOCKING-135Y-1 | §29 quarantine/authority-state cross-reference gap | 135X (PREREQUISITE-135X-2) | Quarantine (§3 item 30) | Schema readiness | Low | None | Low | None | Low | 135Z | 136A | Before 136B |
| NON-BLOCKING-135Y-2 | Schema-gap table omitted §8 authorization fields | 135X (NONBLOCKING-135X-6) | Schema plan (§6) | Schema readiness | Low | None | None | None | Low | 135Z | 136A | Before 136B |
| DEFERRED-135Y-1 | Two-person cutover authorization | 135W (PREREQ-7) | Human authorization (§12) | Activation readiness | Low | None | None | None | None | Not scheduled | N/A | Indefinite |
| DEFERRED-135Y-2 | Disaster-recovery mechanism for corrupted pointer/store | 135W (PREREQ-9) | Recovery journal (§11) | Recovery readiness | Low | None | Medium | None | None | Not scheduled | N/A | Indefinite |
| DEFERRED-135Y-3 | `_ENTRY_POINT_RECOVERY_CLASSIFICATION` two-key gap | 135W (PREREQ-10) | All-four-entry-point plan (§24) | Resolver readiness | Low | None | Low | None | None | 136B (closed no later than entry-point stage 3) | 136C | Before 136L |
| DEFERRED-135Y-4 | Legacy `latest.*` non-atomic writes (Gap B) | 135V (F-135V-5) | Promotion adapter (§18) | Derivative migration readiness | Low | None | Low | None | None | Before 136A per 135V; tracked here as non-blocking for 135Y itself | 136A | Before 136A |
| PREREQUISITE-135Y-7 | Concurrent rollback-vs-forward mutual exclusion not yet designed at implementation level | This phase (§30) | Rollback/roll-forward plan (§30) | Concurrency readiness | Medium | High | Medium | None | Low | 136H | 136I | Before Layer 9 |
| PREREQUISITE-135Y-8 | Platform durability assumptions (fsync, POSIX locking) unverified | This phase (§32) | Durability plan (§32) | Concurrency readiness | Low | Medium | Medium | None | None | 136H | 136I | Before 136H closes |

No Blocking finding is raised by 135Y itself — all findings above are Prerequisite,
Non-Blocking, or Deferred, consistent with 135X's own finding that no Blocking
contract-level gap exists in CLTR-CUTOVER-001.

---

## No-implementation proof

- No production source changed by 135Y.
- No test source changed by 135Y.
- No schema changed by 135Y.
- No Stage 3 implementation occurred.
- No authority resolver was implemented.
- No authority pointer was implemented or changed.
- No cutover request was created or executed.
- No authority epoch changed.
- No CLTR authority was created.
- No legacy authority was demoted.
- No legacy authority was retired.
- No production behavior changed.
- No execution capability was introduced.

Runtime remains **Observed**, maximum capability remains **observe**, execution
availability remains **unavailable**.

Legacy lifecycle remains the sole production authority. CLTR remains derivative.
CLTR-CUTOVER-001 remains a future-behavior contract only. 135Y produced an
implementation plan only.

---

## Recommended next phase

**135Z — Stage 3 Companion Schemas and Typed Authority Model Contract Freeze**

This is the smallest prerequisite contract phase that unlocks Layer 2 (the read-only
authority resolver, 136B) — it closes PREREQ-1, PREREQ-4, PREREQUISITE-135X-2, and
NONBLOCKING-135X-6, all of which block implementation but none of which block
planning. No phase after 135Z may skip ahead of the roadmap in §35 without
identifying, in that phase's own contract, why an intervening prerequisite is no
longer blocking.
