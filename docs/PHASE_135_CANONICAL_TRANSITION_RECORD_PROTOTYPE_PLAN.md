# Phase 135E — Canonical Transition Record Prototype Plan

**Phase class:** Prototype Plan (Track 135, sixth phase)
**Scope:** Planning and documentation only. No implementation, no production source code, no tests, no JSON schema, no CLI commands, no prototype artifacts, no finalization-behavior change, no production entry-point integration, no Track 134 structural-gap repair.
**Predecessor:** 135D.1 — Metadata-Repair Incident Investigation and Staleness Guard (COMPLETE; canonical report repaired; staleness guard live in `run_phase_metadata_repair()`, `src/pcae/commands/phase.py:827-874`).
**Non-goal:** Begin 135F or any later Track 135 phase; implement any module named below; write any prototype artifact under `.pcae/cltr-prototypes/`.

---

## 0. Planning methodology

This plan is produced by re-deriving a prototype boundary from first principles against four frozen/verified inputs, not by copying any one of them wholesale:

1. **135A** (Canonical Lifecycle State Authority Architecture) — the authority model, 14-state candidate machine, derivation architecture, persistence requirements, identity architecture, commit-ownership architecture.
2. **CLTR-001 v1.0** (135B, frozen; 135C, verified — "B. VERIFIED, zero Blocking findings," 10 non-blocking deferred questions) — the binding contract: authority roles (S/R/D/E/V), sole-authority invariant, identity contract, state-machine contract (12 spine + 2 orthogonal states), transition-order contract, projected-state contract, commit-ownership contract, evidence-binding contract, derived-representation contract, atomic-visibility contract, immutable-history contract, digest contract, retry/resume contract, duplicate/replay contract, failure contract, marker/receipt/notification/Architecture-Status/repository-final-state/compatibility/legacy-authority contracts, 33 (now 36) invariants, versioning contract, conformance model, forbidden claims, §32 deferred-decisions table.
3. **135D** (Cross-Representation Invariant Architecture and State-Machine Verification) — the full formal model: 14 states, 16 permitted transitions, 14 forbidden transitions, 8-category irreversibility model, 16-row cross-representation model (see §1 note on the assignment's "15" figure), representation-state matrix, 36 invariants (33 original + CLTR-ORDER-5/6/7 closing 135C finding #7), determinism proof (9 equivalence classes, 4 permitted nondeterminism sources), reachability analysis, terminal-state analysis, safety proof — verdict **"B. VERIFIED WITH NON-BLOCKING DEFERRED QUESTIONS,"** and its own explicit recommendation that 135E be a *plan* for a **read-only, retroactive-reconstruction prototype**, justified because schema/serialization/migration work is premature before empirical validation against real data.
4. **135D.1** (Metadata-Repair Incident Investigation) — root cause (a stale, hand-authored, un-refreshed `.pcae/phase-completion-report.md` silently outranking already-correct metadata for three phases) and the resulting staleness guard, which cross-checks canonical-report identity against `PROJECT_STATUS.md`'s "Current Phase" line before permitting an overwrite, and refuses (fails closed, no mutation) on disagreement.

**Note on the 135D representation count.** The task text asks this plan to build on "a 15-representation cross-representation model." Direct inspection of 135D §9 finds **16 rows**, not 15 (the sixteenth being the canonical transition record itself, listed as row 1, with the other 15 rows being its derivatives/projections/verification targets). This plan treats the record itself as the anchor and the **other 15 rows as the cross-representation set the record must be compared against** — which reconciles the assignment's "15" with 135D's literal 16-row table without asserting a discrepancy in 135D. §14 below enumerates these 15 comparison targets exactly.

Re-derivation, not adoption, governs every choice below: where 135D or CLTR-001 left a question deferred, this plan either resolves it at the *prototype* level (never amending CLTR-001 itself) or explicitly carries the deferral forward to §30.

---

## 1. Prototype purpose

### 1.1 What the prototype must prove

1. **CLTR semantic fields can be represented deterministically** — a concrete (prototype-local) data structure can hold every field CLTR-001 §6.2 requires, and two independent runs over identical inputs produce byte-identical serialized output.
2. **State-machine state can be derived from explicit inputs** — given an explicit set of observed facts about a historical or fixture transition, the 14-state/16-transition model (135D §5) can be mechanically evaluated to produce exactly one current state, never an ambiguous or multi-valued answer.
3. **Identities can be bound exactly** — `transition_id`, `phase_id`, `task_id`, `repository_id`, and the other CLTR-001 §5.1 identifiers can be bound from explicit declared sources only, with zero reliance on title parsing, filename convention, or recent-Git inference (the exact 135D.1 failure class).
4. **Evidence can be referenced without strengthening** — test/governance/report/metadata bindings can be represented as references (identity + digest + limitation), never as copies that would let the prototype claim more certainty than the underlying evidence supports.
5. **Derivatives can be compared against one record** — a candidate record, once generated, can be mechanically compared field-by-field against the current production representations it corresponds to (report, metadata, Architecture Status, marker, receipt) and produce a structured agreement/disagreement result.
6. **Invariant outcomes can be reported** — all 36 formal invariants from 135D §11 can be evaluated against a candidate record and its bound evidence, each producing an individual pass/fail/inapplicable outcome, never a silently skipped invariant.
7. **Retry and terminal classifications can be computed** — given a sequence of observed transition attempts for one phase/task, the prototype can classify each as idempotent re-entry, duplicate, conflicting replay, or genuine retry, per CLTR-001 §16-§17.
8. **Digest verification can detect tampering** — mutating any field of a sealed candidate record changes its digest, and the verifier detects the mismatch.
9. **Historical compatibility can be modeled** — a legacy artifact with no `transition_id` (e.g., a Track 134 phase report) can be classified through a read-only adapter as `conformant_with_legacy_adapter` or `incomplete`, disclosing exactly which required fields are unavailable, never inventing them.
10. **No existing lifecycle authority is replaced** — throughout, the prototype demonstrably has zero write path into any production canonical artifact, entry point, or finalization behavior.

### 1.2 What the prototype does not prove

- That the record, once integrated, will behave correctly under concurrent/multi-agent access (135A §8.2's non-atomicity gap is analyzed, not fixed, and the prototype is explicitly single-threaded/offline).
- That the final production schema, serialization format, or storage mechanism is correct or final (135B §6.3, §13.2, §15.2 all explicitly defer these; the prototype's choices are prototype-local, per §6-§7 below).
- That legacy artifacts can be safely and fully migrated into canonical records (135A §14/§25's legacy-authority retirement is out of scope; §20 below).
- That commit-ownership policy questions CLTR-001 defers (blocking/warning/informational treatment of `unverifiable`, §10.4) are resolved — the prototype surfaces the three-outcome classification deterministically but makes no policy choice.
- That the prototype's CLI, if any, is a production interface — it is a development/verification aid only (§16).
- Performance, scale, or storage-growth characteristics of a real (non-fixture) history.

---

## 2. Prototype scope

### 2.1 Scope selection

The smallest scope that exercises the essential CLTR architecture is **a record generator plus a standalone verifier, driven by fixtures plus one designated read-only integration mode against real repository history** — not a live shadow generator wired into the finalization transaction. Rationale:

- A **shadow generator** hooked into `finalization_transaction.py` would, even if strictly read-only in intent, create a coupling point inside production code before the record model itself is empirically validated — directly contrary to 135D §41.3's own recommendation and to the "smallest safe prototype" objective. It is rejected as *not* the smallest boundary.
- A **generator + standalone verifier**, consuming either (a) frozen fixtures or (b) an explicit, read-only "reconstruct a candidate record from named existing artifacts" mode, proves every item in §1.1 without touching a single production entry point. It is the boundary selected here (frozen in §3).

### 2.2 Transition slice coverage (minimum required, per the assignment's enumeration)

| # | Scenario | Purpose |
|---|---|---|
| 1 | Normal success (PROPOSED→…→NOTIFIED→TERMINAL_SUCCESS) | Proves the full spine, all §1.1 items 1-3 |
| 2 | Failure before certification (CERTIFYING→FAILED_PRE_CERT) | Proves terminal/no-side-effect classification |
| 3 | Failure after promotion / notification uncertainty (PROMOTED→NOTIFYING→NOTIFIED_UNCONFIRMED→TERMINAL_PARTIAL_EXTERNAL) | Proves the 135D.1-adjacent, 134F-central resume gap is structurally closed in the model |
| 4 | Exact replay (identical evidence resubmitted, no newer record) | Proves idempotent re-entry (CLTR-001 §17.1, §17.3) |
| 5 | Conflicting replay (different evidence, same `transition_id`) | Proves rejection (§17.4) |
| 6 | Tamper detection (sealed record's bound evidence digest mismatch) | Proves §15's digest contract |
| 7 | Identity mismatch (declared phase_id disagrees with a bound artifact's own identity) | Proves §9 identity architecture, directly encodes the 135D.1 lesson |
| 8 | Commit-ownership contamination / unverifiable | Proves the three-outcome model (CLTR-001 §10.4) |
| 9 | Mixed derivative generation identity (a comparison target whose report/metadata pair belongs to two different transitions) | Proves invariant CLTR-STATE / atomic-visibility-adjacent detection (135A §8.2, CLTR-001 §13) |

A complete state-machine fixture set (all 14 states, all 16 permitted transitions, representative instances of all 14 forbidden transitions rejected) is **also required**, but is treated as the fixture-authoring deliverable of §17, not a tenth scenario — it is the exhaustive superset that scenarios 1-3 are drawn from as narrative examples.

### 2.3 What is deliberately not built

No production integration scope, no schema freeze, no multi-agent concurrency scenario, no performance/load scenario, no real notification dispatch, no CLI beyond the minimal read/verify/compare surface in §16.

---

## 3. Prototype boundary

### 3.1 Selected model

**Generator + standalone offline verifier**, fixture-driven by default, with one explicit read-only "reconstruct from named live artifacts" mode for integration-style fixtures (§17.3). This is the smallest of the candidates listed in the assignment that still exercises comparison against real historical representations (§1.1 item 5, item 9) — a purely fixture-only prototype could not prove compatibility against actual Track 134/135 artifacts, which §1.1 item 9 requires.

### 3.2 Inputs

- Frozen JSON/text fixtures under a prototype-only fixtures directory (§17).
- Optionally, for the integration-fixture mode only: explicit, named, existing repository paths (e.g., a specific `.pcae/canonical-reports/<phase>/report.md`, a specific `.pcae/phase-completion-metadata.json` snapshot, a specific `.last-notified.json`) passed as explicit CLI arguments — never a live directory scan, never "the latest."

### 3.3 Outputs

- A candidate CLTR record (prototype-local serialization, §7) written only under `.pcae/cltr-prototypes/` (§15).
- A verification result (invariant outcomes, conformance classification).
- A comparison result (candidate record vs. named current representations).
- Human-readable and JSON renderings of the above.

### 3.4 Side effects (explicit allow-list)

Writes are permitted **only** under `.pcae/cltr-prototypes/`. Reads of explicitly named files anywhere in the repository are permitted (never directory scans, never "latest" globbing, never `git log` without an explicit bound revision range supplied by the caller).

### 3.5 Prohibited side effects (restated as binding, not aspirational)

The prototype must not, under any invocation:

- change any canonical report, completion metadata, Architecture Status, checkpoint, receipt, or marker;
- create a production checkpoint or perform production promotion;
- send any notification (Telegram or otherwise);
- write any production marker or receipt;
- alter active-task state or `.pcae/phase-completion-report.md`;
- authorize, gate, or influence completion of any real phase;
- execute any shell command beyond bounded, read-only `git` inspection of explicitly supplied revisions/hashes (`git log -1 <hash>`, `git cat-file`, `git rev-parse` equivalents) — no `git commit`, `git push`, `git checkout`, or mutation of any kind.

### 3.6 Relationship to production finalization and current canonical artifacts

Zero coupling. `finalization_transaction.py` and the four entry points are not imported by, do not import, and are not modified by any prototype module. The prototype's only relationship to current canonical artifacts is **read-only, by explicit reference**, for the compatibility-adapter and comparison functions (§14, §19).

### 3.7 Live-repository reads

Permitted **only** through explicit paths/hashes supplied by the caller (§3.2). No default "scan the repo" behavior exists anywhere in the design.

---

## 4. Proposed module architecture

All modules below are prototype-only unless explicitly marked otherwise; none is imported by production code (`src/pcae/core/`, `src/pcae/commands/` production command modules) at this phase. A future integration phase (135H-class) would decide whether any module graduates.

| Module | Responsibility | Allowed dependencies | Prohibited responsibilities | Public API (sketch) | Error model | Test boundary |
|---|---|---|---|---|---|---|
| `cltr_prototype/models.py` | Data classes for the record and its sub-structures (identity, classification, evidence-reference, temporal fields) | stdlib only | No I/O, no validation logic, no state-machine logic | `TransitionRecord`, `Identity`, `EvidenceRef`, `Timestamps` (all frozen/immutable dataclasses) | Raises `ValueError` only on structurally impossible construction (e.g., missing required field) | Unit only |
| `cltr_prototype/identity.py` | Parse and validate declared identities per CLTR-001 §5, reject inference | stdlib `re`; no filesystem, no Git | No fallback resolution, no title/filename parsing as authority | `resolve_identity(declared: dict) -> Identity \| IdentityError` | Structured `IdentityError` enum (ambiguous, malformed, truncated, alias-without-declaration) | Unit + adversarial |
| `cltr_prototype/state_machine.py` | Encode the 14-state/16-transition/14-forbidden-transition model (135D §5-§6) | `models.py` only | No implicit "set state" escape hatch, no I/O | `apply_transition(record, transition_id, evidence) -> TransitionResult` | `ForbiddenTransitionError`, `PreconditionError` | Unit (all 16 permitted + all 14 forbidden) |
| `cltr_prototype/invariants.py` | Evaluate all 36 invariants (135D §11) against a record + bound evidence | `models.py`, `state_machine.py` | No silent skip of an applicable invariant; no policy decisions (e.g., no deciding `unverifiable` is blocking) | `evaluate_invariants(record, evidence) -> list[InvariantResult]` | Each result carries pass/fail/inapplicable — never an exception for a normal fail | Unit (one test per invariant minimum) + integration |
| `cltr_prototype/canonicalization.py` | Deterministic canonical form for digesting (key ordering, encoding rules, §7-§8) | stdlib `json` | No business logic | `canonicalize(record) -> bytes` | Raises only on non-serializable input | Unit (determinism-focused) |
| `cltr_prototype/digest.py` | SHA-256 digest computation and verification | `canonicalization.py` | No storage, no state logic | `digest(record) -> str`, `verify(record, expected_digest) -> bool` | N/A — pure functions | Unit (tamper-detection focused) |
| `cltr_prototype/generator.py` | Orchestrate identity resolution + state derivation + invariant evaluation into one candidate record | `identity.py`, `state_machine.py`, `invariants.py`, `digest.py`, `models.py` | No writes outside `persistence.py`'s API, no live directory scans | `generate(inputs: FixtureBundle | ExplicitBundle) -> TransitionRecord` | Aggregates and surfaces the first blocking error from any dependency, never partially constructs a record | Integration |
| `cltr_prototype/verifier.py` | Standalone re-check of a persisted candidate record: digest, invariants, state validity | `digest.py`, `invariants.py`, `state_machine.py` | No mutation of the record it verifies | `verify_record(path) -> VerificationReport` | Structured, never raises for an ordinary verification failure | Integration + adversarial |
| `cltr_prototype/compatibility.py` | Read-only adapters classifying legacy/current artifacts against the record's expected fields (§19) | Reads named files only; `models.py` | Never manufactures a missing field; never mutates source artifacts | `classify_legacy_artifact(path, kind) -> CompatibilityResult` | Discloses missing-field list explicitly | Unit + integration fixtures |
| `cltr_prototype/comparison.py` | Compare a candidate record against named current representations (§14) | `compatibility.py`, `models.py` | Read-only; never writes to any compared artifact | `compare(record, targets: dict[str, Path]) -> ComparisonReport` | Structured conflict/uncertain/match per field | Integration |
| `cltr_prototype/persistence.py` | Atomic write of generation directories + pointer under `.pcae/cltr-prototypes/` only | stdlib `os`, `pathlib`, `tempfile` | Never writes anywhere else; never reused for production paths | `persist(record) -> Path`, `read_latest() -> TransitionRecord \| None` | `PointerCorruptError`, `PartialWriteError` | Integration + crash-simulation |
| `commands/cltr_prototype.py` | Minimal CLI wiring (§16) | All of the above | No phase completion, no promotion, no notification, no metadata write | argparse subcommands: `generate`, `show`, `verify`, `compare`, `list` | Exit codes only; no side effects beyond `persistence.py`'s allow-listed writes | Integration (CLI-level) |

This is not a required exact layout — a future implementation phase may merge or split modules — but the responsibility/dependency/prohibition boundaries above are the acceptance criterion any layout must satisfy.

---

## 5. Record data model plan

Per CLTR-001 §6.2, translated into required/conditional/derived/state-dependent classification (no production schema is frozen here):

| Field group | Required at | Conditional / state-dependent | Derived |
|---|---|---|---|
| `schema_version`, `contract_version` | PROPOSED | — | — (both always present) |
| `transition_id`, `phase_id` | PROPOSED | `task_id` conditional (nullable for phase-only transitions) | — |
| `repository_identity`, `branch_identity` | PROPOSED | — | — |
| `source_revision` | PROPOSED | `final_revision` conditional — provisional marker permitted at CERTIFIED, must resolve before TERMINAL_SUCCESS (CLTR-001 §23.4) | files-changed evidence is derived from the (source, final) pair, never stored |
| `prior_state`, `projected_state` | CERTIFYING (advisory) → CERTIFIED (frozen) | — | Architecture Status "what changed"/"what's active" derivatives |
| `certified_state` | CERTIFIED only | Absent before CERTIFIED — never defaulted | — |
| `transition_status` (spine state) | Always present from PROPOSED onward | Value constrained to the 14-state enumeration | Completion/active-inactive derivatives |
| `phase_commit_ownership` | PROPOSED (declared) | Verification outcome (verified/contaminated/unverifiable) attached per-commit at CERTIFYING | Files-changed, Git-attribution-view derivatives |
| changed-file evidence | — | Computable only once both revisions are non-provisional | Fully derived, never stored as a copy |
| test / governance evidence references | Required for CERTIFIED unless transition type is explicitly declared no-test-required | — | Report "Test/Governance Results" sections |
| report / metadata / snapshot / checkpoint / promotion / notification / marker / receipt bindings | Bound at the state each first becomes meaningful (CERTIFIED, CERTIFIED, CERTIFIED, PROPOSED-through-CERTIFYING, PROMOTED, NOTIFYING, NOTIFIED/NOTIFIED_UNCONFIRMED, NOTIFIED/NOTIFIED_UNCONFIRMED respectively) | Absent before that state is reached — never populated early | Corresponding derivative artifacts |
| Architecture Status binding | CERTIFIED | — | The rendered Architecture Status document |
| timestamps | Incrementally, one per spine state reached | `final` timestamp only at a terminal state | — |
| failure classification | Only on FAILED_PRE_CERT / FAILED_POST_CERT / NOTIFIED_UNCONFIRMED | — | — |
| retry classification | Always present from PROPOSED onward | Value depends on current state (§9 of this plan) | — |
| conformance classification | Computed at verification time, not stored as record-authoritative | Always a verifier output, never a generator-declared field | — |
| supersession | Absent until a later record for the same phase/task exists | — | — |
| compatibility metadata | PROPOSED | — | — |
| record digest | Computed last, at CERTIFIED and re-computed at every subsequent seal point | Excludes itself from its own input (CLTR-001 §15.1 item 3) | — |

This plan does not freeze field names, types, or a production schema — per CLTR-001 §6.3, that remains explicitly out of scope until a dedicated schema-design phase.

---

## 6. Serialization plan

- **Format**: JSON, prototype-local only. Not claimed as a permanent production format — CLTR-001 §6.3 and §15.2 explicitly leave wire format open, and this prototype's serialization is scoped to `.pcae/cltr-prototypes/` only.
- **Canonical key ordering**: keys sorted lexicographically (ASCII) at every nesting level, both for on-disk output and for digest input (§7).
- **String encoding**: UTF-8, no BOM.
- **Optional-field behavior**: a field absent because its state has not been reached yet is omitted entirely (never emitted as `null`) — `null` is reserved for fields that are explicitly, meaningfully empty (e.g., `task_id: null` for a phase-only transition, a declared-empty commit set is `[]` not omitted).
- **Enum representation**: state names and classification values are emitted as their exact string identifiers (e.g., `"CERTIFIED"`, `"verified"`, `"unverifiable"`), never integers.
- **List ordering**: commit sets are serialized as a sorted list (by hash, ascending) despite being semantically a set (CLTR-001 §10.1 item 6) — sorting is a serialization convenience for determinism, not a semantic ordering claim.
- **Timestamp format**: ISO 8601, UTC, with explicit `Z` suffix (e.g., `2026-07-13T08:16:01Z`), matching the pattern already used in `.pcae/phase-metadata-repairs.log` and elsewhere in the repo.
- **Digest-field exclusion**: the `record_digest` field itself is never included in the bytes passed to the digest function (§7).
- **Unknown-field handling**: the prototype's own reader ignores and preserves unrecognized top-level fields on round-trip (forward-compatibility rehearsal, per CLTR-001 §27 item 4) rather than raising — this is a rehearsal for the *future* production versioning contract, not a claim that this prototype schema itself is versioned for real consumers.
- **Version field**: every prototype record carries `schema_version: "cltr-prototype-0.1"` and `contract_version: "CLTR-001/1.0"` — distinct fields, per CLTR-001 §27 item 2 — making clear this is prototype-local, not a CLTR-001 schema release.
- **Determinism requirement**: two `generate()` calls over identical inputs (including identical fixture timestamps where fixtures fix them) must produce byte-identical JSON output.

Distinguishing prototype serialization from a future production schema: **this format is disposable.** A production schema-design phase may choose an entirely different wire format, embedded structure, or storage layout; nothing here binds that future decision beyond the semantic content requirements of CLTR-001 §6.2.

---

## 7. Canonicalization and digest plan

- **Canonicalization algorithm**: recursively sort all object keys, use compact separators (no extraneous whitespace), UTF-8 encode, encode floats as absent (no floating-point fields exist in this model — all numeric fields are integers or absent).
- **Digest algorithm**: SHA-256 (per CLTR-001 §15.1 item 2's default, no deviation justified for the prototype).
- **Digest coverage**: the digest is computed over the canonicalized form of every S, R, and E-role field bound into the record at the time of sealing (CLTR-001 §15.1 item 4) — i.e., everything except the digest field itself and any V-role field explicitly marked as excluded (see below).
- **Excluded fields**: the `record_digest` field itself (self-exclusion, §15.1 item 3). Live V-role re-measurements taken *after* the transition's own terminal point (e.g., a `pcae health` check run long after TERMINAL_SUCCESS) are never folded into the sealed digest — only the point-in-time V-role bindings captured at CERTIFYING/terminal-verification are included, exactly as CLTR-001 §23.3 requires.
- **Treatment of timestamps**: included in the digest input (they are part of the sealed record's content, not incidental to it) — but the four permitted-nondeterminism sources from 135D §33.1 (event timestamps, wall-clock V-role values, storage-representation choices, freshly generated attempt IDs) are exactly why fixtures must **fix** their own timestamps explicitly rather than reading `datetime.now()`, so that determinism tests (§18) are not spuriously flaky.
- **Treatment of terminal extensions**: the §23.4 "terminal verification event" (resolving a provisional `final_revision`) is itself digested as a separate, appended immutable entry with its own digest — it never retroactively changes the CERTIFIED record's original digest, matching CLTR-001 §23.4 item 3 ("never mutates the sealed CERTIFIED content").
- **Cross-file binding**: if the prototype's persistence layer (§15) spans more than one file per generation, every digest-bearing derivative must carry both the digest **and** the `transition_id` (CLTR-001 §15.1 item 5) — a digest alone is never sufficient.
- **Transition/repository/phase identity binding**: the digest input includes the full identity block (§5) — a record from one transition can never produce the same digest as a record from another, even with otherwise-identical evidence.
- **Verification behavior**: `verifier.py` recomputes the digest from the persisted record's canonicalized content and compares byte-for-byte against the stored `record_digest`; any mismatch is reported as `tamper_detected`, never silently accepted.
- **Tamper behavior**: any single-byte mutation to a persisted record's bound-evidence fields must change the digest (tested explicitly in §18's adversarial suite).
- **Stale substitution behavior**: a comparison target whose own digest reference does not match the candidate record's digest is reported as `conflict`, never silently preferred.
- **Cross-transition substitution behavior**: a derivative claiming digest D but a different `transition_id` than the record that produced D is rejected outright (CLTR-001 §14.1 item 9; this is the direct prototype-level rehearsal of the 135D.1 identity-vs-narrative lesson generalized to digests).

---

## 8. Identity-resolution plan

### 8.1 Explicit-only inputs

The prototype accepts identity exclusively via explicit, named fields in the fixture or explicit-bundle input (§3.2) — a Python `dict`/JSON object with required keys (`phase_id`, `transition_type`, `repository_identity`, etc.), never inferred from any of: titles, Architecture Status labels, report prose, filenames alone, commit subjects, latest-file presence, or recent Git history. This directly operationalizes CLTR-001 §5.2-§5.3 and generalizes the 135D.1 lesson (§21 below).

### 8.2 Validation rules by identifier type

- **Dotted phase IDs** (e.g., `135A`): validated against the existing generalized grammar `^(\d+)([A-Za-z])((?:\.\d+[A-Za-z]?)*)$` (from `architecture_status.py:51`, confirmed current) — reused as a *reference regex for validation only*, applied exactly once at `identity.py:resolve_identity()`, never re-implemented at any other prototype call site (135A §9.2's central lesson).
- **Multi-dotted IDs** (e.g., `134E.10.1V.1`): the same grammar handles arbitrary dotted depth; validation confirms no trailing component is silently dropped (explicit length round-trip check: `str(parsed) == input_string`).
- **Verification suffixes** (`...V.1`) and **corrective suffixes**: recognized as valid trailing segments by the same grammar; the prototype does not need a separate suffix-specific grammar, only a check that they round-trip.
- **Task IDs**: validated with the same no-inference discipline; explicitly nullable; when present, bound to its declaring `phase_id` (never independently resolved).
- **Transition IDs**: the new identity primitive (CLTR-001 §5.1) — for the prototype, generated as a stable deterministic function of `(phase_id, task_id, attempt_ordinal)` supplied explicitly by the caller/fixture, never auto-incremented from a mutable counter that could collide across runs.
- **Repository IDs**: validated as an explicit string the caller declares (e.g., a canonical remote URL or repo-root path) — the prototype never assumes "the current working directory."
- **Representation IDs** (`report_id`, `metadata_id`, `snapshot_id`, etc.): each validated as present-or-absent per the state-dependent rules in §5, never defaulted.

### 8.3 Rejected identity sources (explicit, enforced by test, §18)

Prefix inference, regex truncation, commit-subject-as-authority, recent-Git fallback (`git log --oneline -N` with no explicit hash/range), report-field-presence-as-proof, and ambiguous aliases are all explicitly rejected — `identity.py` has no code path that reads any of these as an identity source.

### 8.4 135D.1 lesson incorporated directly

`compatibility.py` and `comparison.py` (which are the only prototype modules that touch narrative text such as `.pcae/phase-completion-report.md`) must never let a parsed narrative title override or repair an already-resolved explicit identity. Where a comparison shows the narrative disagrees with the explicit identity, the result is `conflict`, never a silent "repair" — repair, if any, is out of scope for this prototype (§21).

---

## 9. State-machine implementation plan

Per state (all 14) and per transition (all 16 permitted, 14 forbidden), the plan is:

- **Representation strategy**: `transition_status` is a Python `enum.Enum` (or equivalent frozen string-literal type) with exactly the 14 members named in 135D §3.3 (12 spine + `QUARANTINED` + `SUPERSEDED` tracked as a separate orthogonal-flags set, not mutually exclusive with the spine value — a record can be simultaneously, e.g., `TERMINAL_SUCCESS` on the spine and flagged `SUPERSEDED`).
- **Transition function**: exactly one function per named transition (T1-T16 from 135D §5), each taking `(record, evidence) -> TransitionResult`. There is **no generic `set_state(record, new_state)` function** — this is a binding design rule, not an implementation detail, directly closing the "no implicit transitions... no generic set-state escape hatch" requirement.
- **Precondition checks**: each transition function checks its own entry conditions (135D §7.3-equivalent per-state table) before mutating anything; failing a precondition raises `PreconditionError`, never silently no-ops.
- **Invariant checks**: applicable invariants (per each invariant's declared "lifecycle applicability," 135D §11) are checked immediately after a transition succeeds, before the function returns — a transition that would violate an applicable invariant is rejected, not applied-then-flagged.
- **Return model**: `TransitionResult` is a small frozen structure: `{new_state, invariant_results, timestamp}` — never a bare mutation of the input record (records are immutable value objects; a transition produces a new record value).
- **Failure model**: forbidden transitions (any of F1-F14 from 135D §6) raise `ForbiddenTransitionError` carrying which forbidden-transition ID matched.
- **Idempotency**: re-invoking the same transition function with the same `(record, evidence)` for a record already in the target state is a no-op returning the existing state (not an error) — this is the prototype-level rehearsal of CLTR-001 §17.1.
- **Retry behavior**: encoded per §16.3's table (from CLTR-001), not as ad hoc logic — each state's retry classification is a lookup, not a computation.
- **Terminal behavior**: `is_terminal(state) -> bool` is a pure lookup against the six terminal/terminal-ish states (135D §35); no transition function may be invoked on a record already in a terminal state except the two orthogonal transitions (`quarantine`, `supersede`).
- **Constrained repair behavior**: the two designed self-loops (`NOTIFYING→NOTIFYING` via `notify_retry`, and the `NOTIFIED_UNCONFIRMED` reconciliation path via `reconcile_receipt`) are the *only* cyclic transitions in the graph (135D §34's reachability conclusion) and are each implemented as their own named, narrowly-scoped function — never a generic retry mechanism applicable to arbitrary states.

---

## 10. Invariant engine plan

For each of the 36 invariants (135D §11: CLTR-ID-1/2; CLTR-AUTH-1/2; CLTR-STATE-1..4; CLTR-ORDER-1..7; CLTR-DERIVE-1/2; CLTR-COMMIT-1..3; CLTR-EVID-1; CLTR-PERSIST-1..3; CLTR-RETRY-1..3; CLTR-NOTIFY-1/2; CLTR-MARKER-1/2; CLTR-RECEIPT-1; CLTR-COMPAT-1/2; CLTR-SAFE-1..3):

- **Required inputs**: the candidate record plus, where the invariant's evaluation inputs (per 135D §11's per-row column) name external evidence (e.g., a comparison target's own digest for CLTR-DERIVE checks), the explicitly-referenced evidence — never a live scan.
- **Evaluator location**: one function per invariant in `invariants.py`, named after its ID (e.g., `evaluate_cltr_id_1(record, evidence)`).
- **Lifecycle applicability**: each evaluator first checks whether the invariant applies at the record's current state (e.g., CLTR-ORDER invariants about promotion sequencing are inapplicable to a record still in CERTIFYING) — an inapplicable invariant returns `inapplicable`, never `pass` (passing-by-vacuous-inapplicability would hide the distinction the assignment explicitly requires the engine to preserve).
- **Pass/fail result**: `{invariant_id, outcome: pass|fail|inapplicable, detail}`.
- **Severity**: all 36 invariants are `Blocking` per 135D §11's own severity column — the prototype's engine surfaces this as data (not as a hardcoded behavior), so a future phase can revisit severity without changing the engine's shape.
- **Failure consequence / conformance effect**: recorded per-invariant (matching 135D §11's "failure consequence"/"quarantine consequence" columns) but **the engine does not itself act on these** (e.g., does not auto-quarantine) — §23 keeps conformance/lifecycle-state as separate dimensions, and invariant failure feeds conformance classification, not state transitions, directly.
- **Output format**: `evaluate_invariants()` returns the full list of 36 results every time — **the engine must not silently skip an applicable invariant**; a missing result for an applicable invariant is itself treated as an engine bug (tested explicitly, §18).
- **Grouping**: the CLI's `verify` output groups results by category (ID, AUTH, STATE, ORDER, DERIVE, COMMIT, EVID, PERSIST, RETRY, NOTIFY, MARKER, RECEIPT, COMPAT, SAFE) for readability, but the underlying data structure is always the flat 36-item list — grouping is presentation only.

---

## 11. Authority-role plan

Mapping S/R/D/E/V (CLTR-001 §3.1) to code-level enforcement:

| Role | Enforcement mechanism in the prototype |
|---|---|
| S (sole) | Fields so classified (identity, transition status, etc.) exist **only** on `TransitionRecord`; no derivative class (`ComparisonReport`, `CompatibilityResult`) has a settable field of the same name — they only have a *read* of the record's value, enforced by Python-level immutability (frozen dataclasses) and by `comparison.py` never constructing a `TransitionRecord` itself, only consuming one |
| R (reference) | Represented as `EvidenceRef{identity, digest, limitation}` value objects — never as a copy of the referenced content; `generator.py` never inlines evidence content into these fields |
| D (derivative) | Derivative-producing functions (`comparison.py`, `compatibility.py`, Architecture-Status-style renderers if ever added) take a `TransitionRecord` as a read-only input and have no code path that "redefines" a fact the record already carries — enforced by simply never passing a mutable record reference to these functions (they receive frozen values) |
| E (immutable event) | Represented as append-only lists on the record (e.g., `notification_attempts: list[NotificationEvent]`) — no removal or in-place edit API exists |
| V (verification-only) | Represented as `Observation{value, measured_at}` — always paired with a timestamp, and `comparison.py`/`invariants.py` never treat a V-role field's absence of a fresh re-measurement as equivalent to "still true" |

Concretely, this prevents: a derivative setting authoritative fields (no derivative class has a constructor path that produces a `TransitionRecord`); evidence becoming authority (evidence references never carry a `status` field the record itself would read back as ground truth); observations redefining certified state (`CompatibilityResult`/`ComparisonReport` are one-way outputs, never fed back into `generator.py`); markers proving completion (the prototype has no marker-reading code path in `state_machine.py` at all — markers are compatibility-adapter inputs only, §19); receipts inventing outcomes (`compatibility.py`'s receipt adapter discloses limitation text, never asserts an outcome the receipt itself doesn't contain); mutable "latest" files proving certification (`comparison.py` treats a `latest.json`/`latest.md` pair purely as a comparison *target*, never as an input to `generator.py`); Git history establishing commit ownership by recency (identity.py/§8.3 above never calls `git log -N` without an explicit hash).

---

## 12. Commit-ownership plan

- **Explicit owned commits**: represented as `frozenset[str]` of hashes, declared explicitly in the fixture/bundle — never computed.
- **Zero-commit phases**: `frozenset()` is a valid, first-class value (CLTR-001 §10.2 item 1) — `generator.py` has no special-casing for the empty set; it is the same code path as a non-empty set.
- **One or multiple commits, ordering**: represented as a set, not a list — no ordering claim (CLTR-001 §10.1 item 6); serialization sorts only for output determinism (§6).
- **Repository existence / identity binding / branch-revision relationship**: each declared hash is checked, in the *integration-fixture mode only* (§3.2), via a bounded `git log -1 <hash>` (or `git cat-file -e <hash>`) against the declared `repository_identity`/`branch_identity` — never an unbounded scan.
- **Prior-phase / unrelated commits**: the three-outcome classifier (§12.1 below) is the only mechanism that may flag a commit as not belonging to this transition; nothing infers this from recency.
- **Fabricated / unverifiable hashes**: a hash that cannot be resolved against the bound repository/revision context is classified `unverifiable` — **never** silently treated as `verified` (directly closing, at the prototype-model level, the exact silent-`continue` gap CLTR-001 §10.3 describes in current production `phase_reports.py` — the prototype does not repair that production code, it simply never repeats the gap in its own model).
- **Rewritten history**: out of scope for detection in this prototype (branch-reachability is explicitly one of 135C's ten non-blocking deferred findings, #2, still deferred by 135D) — the prototype's `unverifiable` outcome is the closest available classification and is used honestly rather than inventing a fourth outcome.
- **Completion commits**: classified via an explicit `commit_role` tag the fixture/caller declares (`source_change`, `documentation`, `repair`, `verification_only`) — the prototype does not infer role from message text.

### 12.1 Three-outcome model (frozen from CLTR-001 §10.4, implemented literally)

```
verified       — hash exists, resolves in bound repo/revision context, subject doesn't contradict phase identity
contaminated   — hash exists, subject/metadata names a different phase
unverifiable   — hash cannot be resolved against the bound repository identity/revision
```

The prototype **does not decide** whether `unverifiable` blocks, warns, or is informational (CLTR-001 §32.3 item 2, explicitly deferred to 135D and still deferred by 135D itself) — it surfaces the classification and lets the verifier's conformance output (§23) carry the ambiguity forward as data, not as a policy default.

---

## 13. Evidence-reference plan

Each evidence reference (`EvidenceRef`) carries:

- **artifact path** (explicit, as supplied);
- **artifact identity** (e.g., `report_id`);
- **digest** (SHA-256 of the artifact's own content at reference time);
- **observation timestamp** (when the reference was bound);
- **source revision** (which repository state the artifact reflects, where applicable);
- **evidence type** (`test_suite_result`, `governance_check_result`, `report`, `metadata`, `runtime_snapshot`, etc.);
- **limitation** (free-text but explicitly optional and never authoritative — e.g., "hermetic fixture, no live repository state" or "narrative summary only, no structured pass/fail count available");
- **verification status** (`bound`, `unavailable`, `stale`).

No report prose becomes sole evidence for any R/E-role fact (CLTR-001 §11.2) — where only narrative prose is available (a legacy artifact), the `compatibility.py` adapter (§19) records `evidence_type: narrative_only` and `verification_status: unavailable_structured`, explicitly disclosing the weakness rather than promoting the prose to structured-evidence status.

---

## 14. Cross-representation comparison plan

`comparison.py` compares a candidate record against the **15 comparison targets** (135D §9 rows 2-16, the record's own row 1 excluded as the comparison anchor):

1. Canonical phase report
2. Completion metadata
3. Architecture Status
4. Immutable snapshot
5. Checkpoint
6. Promoted report
7. Promoted metadata
8. Mutable latest pointer
9. Notification payload
10. Notification result
11. Completion marker
12. Finalization receipt
13. Git attribution view
14. Repository transition view
15. Terminal repository-state observations

For each target, the comparison classifies every relevant field as:

- **exact-match field** — must compare byte-identical (e.g., `phase_id`, `transition_id` where present);
- **digest-bound field** — compares via digest equality, not full-content diff (e.g., report content vs. the record's `report_id`+digest binding);
- **derived field** — recomputed from the record and compared against the target's own claimed value (e.g., files-changed);
- **presentation-only field** — never compared for equality, only presence (e.g., prose formatting, human-readable summaries);
- **tolerated legacy absence** — a field the target cannot be expected to carry because it predates Track 135 (e.g., no `transition_id` on a Track 134 report) — recorded as `absent_legacy`, not `conflict`;
- **conflict** — an exact-match or digest-bound field disagrees;
- **unverifiable condition** — the target cannot be read/parsed at all;
- **quarantine recommendation** — emitted (as a recommendation, never an automatic action) when a conflict involves a Blocking invariant's bound field (per §10's severity data).

Comparison is strictly read-only: `comparison.py` never writes to any of the 15 targets, and returns a `ComparisonReport` value object only.

---

## 15. Persistence plan

```text
.pcae/cltr-prototypes/
  generations/
    <transition-id>/
      record.json
      verification.json
      manifest.json
  latest.json
```

- **Immutable generation directory**: once written, a `generations/<transition-id>/` directory is never modified — a re-run for the same `transition_id` either no-ops (idempotent, §9) or is rejected as a conflicting replay (§2.2 scenario 5), never overwritten in place.
- **Current pointer behavior**: `latest.json` holds `{transition_id, digest, written_at}` for whichever generation was most recently produced **per phase/task** (the prototype may maintain one pointer per phase_id, or a single global pointer — this plan selects **one pointer per `phase_id`**, i.e. `latest.json` is a map, since comparing across unrelated phases at once has no use case here).
- **Atomic write approach**: write to a temp file in the same directory (`tempfile.NamedTemporaryFile(dir=..., delete=False)`), fsync, then `os.replace()` onto the final path — the same pattern already proven in production (`finalization_transaction.py`'s checkpoint write) and explicitly not a departure from it.
- **Temporary file handling**: temp files use a `.tmp-<random>` suffix within the same target directory (never `/tmp`) so `os.replace` remains atomic on the same filesystem.
- **Rename behavior**: `os.replace()` (POSIX atomic rename), never a copy-then-delete.
- **Partial-write cleanup**: on any exception during generation, the temp file is removed; the final path is never partially written (write-then-rename means a reader never observes a half-written file).
- **Fsync expectations**: `os.fsync(fd)` called before `os.replace()` for `record.json` and `latest.json` — matching the durability discipline CLTR-001 §8's persistence architecture calls for, at prototype scale.
- **Manifest completeness**: `manifest.json` lists the digest of every file in the generation directory, so a reader can detect a directory that is present but incomplete (e.g., crash between writing `record.json` and `verification.json`).
- **Digest verification**: `verifier.py`'s first check is always: does `manifest.json` agree with the actual files present and their digests?
- **Historical immutability**: no code path in `persistence.py` deletes or edits a `generations/<transition-id>/` directory once its manifest is complete.
- **Crash recovery**: `read_latest()` first tries `latest.json`; if it is missing, corrupt, or points at a `transition_id` whose generation directory is incomplete (manifest mismatch), it falls back to scanning `generations/` for the most recently *complete* (manifest-consistent) generation — this exercises, at prototype scale, the exact "latest-pointer recovery from immutable history" requirement of CLTR-001 §8/§13.3 item 6, **without** claiming to solve the production `latest.md`/`latest.json` non-atomicity gap (135A §8.2) — that gap remains explicitly unrepaired in production (§20).

This path is deliberately disjoint from every production canonical path (`.pcae/canonical-reports/`, `.pcae/phase-completion-metadata.json`, `.pcae/finalization-transactions/`, `.pcae/delivery-receipts/`) — no shared prefix, no shared filename, to make path confusion structurally unlikely (risk R9, §31).

---

## 16. CLI plan

Minimal surface, justified only by the need to drive the prototype manually during its own future verification phase (135F/135G):

```text
pcae cltr-prototype generate --input <fixture-or-explicit-bundle.json>
pcae cltr-prototype show --record <path>
pcae cltr-prototype verify --record <path>
pcae cltr-prototype compare --record <path> --against <target-manifest.json>
pcae cltr-prototype list
```

- `generate` invokes `generator.py` and persists via `persistence.py`.
- `show` renders a persisted record human-readably (no mutation).
- `verify` invokes `verifier.py` (digest + invariants + state validity).
- `compare` invokes `comparison.py` against a small JSON manifest naming the 15 target paths/kinds (§14) — never a directory scan.
- `list` lists generation directories under `.pcae/cltr-prototypes/generations/`.

The command name is deliberately namespaced `cltr-prototype`, distinct from any eventual production `pcae cltr ...` command family, so no user or script could mistake it for a production interface. It must not: complete phases, promote artifacts, send notifications, update metadata, repair production state, change task state, or authorize execution — none of these capabilities exist anywhere in the module graph (§4), so this is a structural guarantee, not a policy on top of a capable implementation.

Whether this CLI is built before or alongside the fixtures (§17) is a Stage 4 implementation-sequencing question (§26), not resolved here beyond "minimal and last."

---

## 17. Fixture strategy

Deterministic, hermetic-by-default fixtures (JSON), one file per scenario, under a prototype-only fixtures directory (e.g., `tests/fixtures/cltr_prototype/` if/when tests are added in a later phase — no fixtures are created *in this planning phase*):

1. `successful_transition.json` — full spine, PROPOSED→TERMINAL_SUCCESS.
2. `pre_certification_failure.json` — CERTIFYING→FAILED_PRE_CERT.
3. `promoted_notification_uncertainty.json` — PROMOTED→NOTIFYING→NOTIFIED_UNCONFIRMED→TERMINAL_PARTIAL_EXTERNAL.
4. `exact_replay.json` — a second submission identical to fixture 1's evidence.
5. `conflicting_replay.json` — a second submission with the same `transition_id` as fixture 1 but different evidence.
6. `identity_mismatch.json` — declared `phase_id` disagrees with a bound artifact's own embedded identity.
7. `stale_report.json` — a narrative report whose title is older than the declared current phase (the direct 135D.1 rehearsal).
8. `mixed_derivative_generations.json` — a comparison-target bundle where the "report" and "metadata" targets belong to two different `transition_id`s.
9. `fabricated_commit_hash.json` — a declared commit hash that does not resolve.
10. `contaminated_commit_ownership.json` — a declared hash whose subject names a different phase.
11. `unverifiable_ownership.json` — same shape as 9, exercised specifically through the three-outcome classifier's `unverifiable` path (kept distinct from 9 so the fixture set has an explicit example of the *classification*, not just the raw failure).
12. `tampered_record.json` — a persisted record whose stored digest no longer matches its (deliberately mutated) content.
13. `stale_pointer.json` — a `latest.json` pointing at a `transition_id` with an incomplete/missing generation directory.
14. `superseded_transition.json` — an original record plus a later correcting record for the same phase/task.
15. `legacy_artifact_no_transition_id.json` — a Track 134-style report/metadata pair with no `transition_id` at all, exercised only through `compatibility.py`.

Fixtures are hermetic by default (no live repository dependency) **except** an explicitly separate `integration/` subset (§3.2's explicit-bundle mode) which is allowed to name real, existing repository paths — but even those are pinned to specific, named, already-committed files, never "whatever is currently latest." All fixture timestamps are fixed literal values (§7), never `datetime.now()`.

---

## 18. Test plan

Test creation itself is out of scope for this planning phase (explicit non-goal); this section defines what a future implementation phase must plan to write, categorized:

**Unit**
- Deterministic generation (same input twice → byte-identical record).
- Stable serialization (canonicalization round-trips).
- Stable digest (same content → same digest, run-to-run and machine-to-machine).
- State transition validity (each of the 16 permitted transitions succeeds under valid preconditions).
- Forbidden transition rejection (each of the 14 forbidden transitions raises `ForbiddenTransitionError`).
- Identity preservation (round-trip of dotted/multi-dotted/suffixed IDs).
- No title-based identity inference (a test asserting `identity.py` has no code path reading report titles).
- No recent-Git-attribution fallback (a test asserting no unbounded `git log` call exists).
- Commit-ownership three-outcome classification (one test per outcome).
- Retry/resume classification per §16.3's table (one test per row).
- Terminal behavior (no transition function accepts a record already in a terminal state, except the two orthogonal transitions).

**Integration**
- Exact replay (fixture 4 resolves to fixture 1's existing state, not a new record).
- Conflicting replay (fixture 5 is rejected).
- NOTIFIED_UNCONFIRMED end-to-end (fixture 3 reaches TERMINAL_PARTIAL_EXTERNAL, never silently upgraded to TERMINAL_SUCCESS).
- Mixed-generation detection (fixture 8 is flagged by `comparison.py`).
- Atomic prototype publication (a simulated crash mid-write leaves no partial file visible to a reader).
- Stale-pointer detection and recovery (fixture 13 recovers from `generations/`).
- Immutable history (an attempt to overwrite an existing generation directory is rejected).
- Compatibility classification (fixture 15 produces an honest `incomplete`/`conformant_with_legacy_adapter` result, never a fabricated field).
- No production side effects (a test that snapshots every file under `.pcae/` outside `.pcae/cltr-prototypes/` before and after a full prototype run and asserts zero diff).

**Adversarial**
- Digest tamper detection (fixture 12).
- Fabricated/unverifiable hash handling (fixtures 9, 11).
- Identity mismatch rejection (fixture 6, and the 135D.1-pattern stale-narrative-vs-explicit-identity case, fixture 7).
- Cross-transition digest substitution rejection (§7's requirement).

**Determinism**
- Repeated generation across process restarts produces identical output (no reliance on in-memory state, PID, or hash-seed-dependent ordering — Python's `PYTHONHASHSEED` sensitivity is explicitly tested against, since dict/set iteration order must never leak into output ordering; `canonicalization.py`'s explicit sort is what must be relied on, not incidental ordering).

---

## 19. Compatibility plan

Read-only adapters in `compatibility.py`, one per legacy/current artifact kind:

| Artifact | Classification behavior |
|---|---|
| Current canonical reports (post-134B) | Most fields resolvable; `transition_id` absent pre-135 implementation → `conformant_with_legacy_adapter` |
| Current completion metadata | Same pattern |
| Architecture Status | Read-only render inspection only; never treated as authoritative for any S-role fact (directly enforcing CLTR-001 §4.2 item 3) |
| Immutable snapshots | Digest-comparable if the snapshot format is stable; disclosed as `narrative_only` for any prose-only sections |
| Checkpoints (`.pcae/finalization-transactions/*.json`) | Read for historical/integration-fixture purposes only; never written to |
| Latest files (`latest.md`/`latest.json`) | Treated purely as comparison targets (§14 row 8), explicitly never as generator input |
| Markers (`.last-notified.json`) | Same — comparison target only, per CLTR-001 §19's marker-is-cache principle |
| Receipts (`.pcae/delivery-receipts/`) | Read as immutable evidence; classified `bound` if resolvable, `unavailable` otherwise |
| Git attribution | Bounded, explicit-hash-only reads; never a recency scan |
| Historical artifacts lacking transition IDs (pre-135 phases) | Always `conformant_with_legacy_adapter` at best, explicitly disclosing the absent `transition_id`/`repository_identity` fields — never inventing a retroactive `transition_id` |

All adapters must: disclose missing fields explicitly (a structured `missing_fields: list[str]`); preserve uncertainty (no forced binary conformant/non-conformant collapse — `incomplete` and `unverifiable` are first-class outcomes); never manufacture authority (an adapter's output is always `D`-role relative to the source artifact, never promoted to `S`); never rewrite history (read-only, enforced structurally — no adapter module imports any write-capable function); never mutate source artifacts (same); classify incomplete/unverifiable evidence honestly (no adapter ever silently upgrades `unavailable` to `bound`).

---

## 20. Migration boundary

Explicitly, this prototype and this plan do **not**:

- integrate the record into `finalization_transaction.py` or any of the four production entry points;
- retire any current legacy authority (marker-as-terminal-check, checkpoint-as-separate-file, etc. all remain exactly as they are in production);
- replace any current canonical report or metadata file with a record-derived equivalent;
- convert any historical Track 134/135 artifact into a newly authoritative CLTR record — compatibility adapters (§19) classify and disclose, they do not upgrade;
- repair 135A §8.2's `latest.md`/`latest.json` non-atomicity gap, the fabricated-hash gap (CLTR-001 §10.3), or the NOTIFIED_UNCONFIRMED resume gap in *production* code — all three remain exactly as 134F/135A/135D found them; the prototype only demonstrates that its own model does not repeat these gaps.

A later phase (135H-class, per §32) may plan integration, but **only after** an independent prototype-verification phase (135G-class, §29) confirms this plan's acceptance criteria (§28) were actually met by an implementation.

---

## 21. 135D.1 incident protections

Explicit safeguards this plan bakes in, each traced to the 135D.1 finding:

1. **Explicit identity beats narrative identity** — `identity.py` never reads any narrative title; `compatibility.py`'s narrative-report adapter is read-only and comparison-only, never an input to `generator.py` (§8.1, §8.4).
2. **Stale narrative reports cannot overwrite current metadata** — the prototype has no "repair" capability at all (§20); the closest analogous operation, `comparison.py`, only ever *reports* a conflict, never resolves one in either direction.
3. **Compatibility extraction discloses source age and identity** — every `compatibility.py` result carries the source artifact's own claimed identity and, where determinable, its last-modified/authored signal, explicitly surfaced rather than silently trusted (directly modeled on the exact gap 135D.1 found: a file with "no recency check" of its own).
4. **Source disagreement produces a conflict result** — `comparison.py`'s `conflict` outcome (§14) is the structural equivalent of the staleness guard's refusal — disagreement is surfaced, never silently arbitrated in favor of either source.
5. **Repair is separate from verification** — this prototype has no repair module at all; `verifier.py` and `comparison.py` are read-only observers, matching the 135D.1-repaired production function's own principle ("one direction only... never the reverse") by having *no* direction at the prototype layer.
6. **Prototype comparison never mutates either source** — enforced structurally (§3.5, §14, §19 — no adapter or comparison function imports a write path).
7. **Stale report age or revision is detectable** — fixture 7 (`stale_report.json`, §17) and the `compatibility.py` disclosure requirement (item 3 above) together exercise this directly.
8. **Report title parsing cannot establish canonical phase identity** — `identity.py` has zero title-parsing code; only `compatibility.py`'s narrative adapter parses titles, and only for comparison/disclosure, never for identity resolution (§8.4 restates this precisely).

---

## 22. Error model

Structured, machine-readable errors (each a distinct exception class or result-variant tag, never a bare string):

| Error | Trigger |
|---|---|
| `MissingInputAuthorityError` | A required declared field (identity, evidence reference) is absent from the input bundle |
| `IdentityConflictError` | Two declared identity sources disagree, or an identity fails round-trip validation |
| `UnsupportedStateError` | An input names a `transition_status` value outside the 14-state enumeration |
| `ForbiddenTransitionError` | Any of F1-F14 attempted |
| `InvariantFailureError` (only where the calling context requires fail-closed; ordinarily invariant failures are data, not exceptions, per §10) | Used only by `generator.py` when an applicable Blocking invariant fails *during* generation itself, before a record can be sealed |
| `DigestFailureError` | `verifier.py` finds a digest mismatch |
| `CommitContaminationError` (data-tagged, not always raised — see §12.1; raised only if a caller requests fail-closed mode) | A commit resolves `contaminated` |
| `CommitUnverifiableError` (same pattern) | A commit resolves `unverifiable` |
| `EvidenceAbsentError` | A required evidence reference cannot be bound at CERTIFIED |
| `StaleRepresentationError` | `comparison.py` finds a target's digest predates the candidate record's own |
| `MixedGenerationError` | `comparison.py` finds two targets in the same comparison set belonging to different `transition_id`s |
| `PointerFailureError` | `persistence.py`'s `latest.json` is corrupt or points at an incomplete generation |
| `CompatibilityLimitationError` (data-tagged, not raised) | A legacy artifact is missing required fields — surfaced as `missing_fields`, not an exception, since this is an expected, honest outcome, not a bug |
| `UnsupportedContractVersionError` | A record declares a `contract_version` the prototype doesn't recognize |
| `UnsupportedSchemaVersionError` | Same, for `schema_version` |

All errors are deterministic (same input always produces the same error) and carry structured fields (never only a human-readable message) so a future test suite or CLI `--json` mode can assert on them precisely.

---

## 23. Conformance output plan

Conformance is a **separate dimension from lifecycle state** (per §10's design and CLTR-001 §30) — collapsing them would lose the information that, e.g., a record can be `TERMINAL_SUCCESS` on the spine while its commit ownership is `unverifiable` (CLTR-001 §32.3 item 2's still-deferred policy question).

Defined conformance outputs:

- **conformant** — all applicable invariants pass; all bound evidence resolves; no comparison conflicts.
- **conformant_with_legacy_adapter** — all applicable invariants pass, but one or more fields were only resolvable via a compatibility adapter (§19) rather than natively (e.g., no `transition_id` on a pre-135 artifact).
- **incomplete** — one or more required evidence bindings are absent (not necessarily a failure, if the record's own state hasn't reached the point where they're required yet).
- **conflicting** — one or more comparison targets disagree with the candidate record on an exact-match or digest-bound field.
- **unverifiable** — one or more commit-ownership or evidence references could not be resolved.
- **quarantined** — an applicable Blocking invariant failed, or a digest mismatch was found.
- **superseded** — a later record exists for the same phase/task.

`lifecycle_state` (the 14-value spine+orthogonal enum) and `conformance` (the seven-value classification above) are always reported as two separate fields in `VerificationReport`/`ComparisonReport` — never merged into one status string.

---

## 24. Observability and reporting plan

The prototype's own reports (`show`, `verify`, `compare` output) include: record identity (all bound identifiers); current lifecycle state; the transition history (which states were reached, when); the full 36-item invariant result list; the conformance classification (§23); all evidence references with their verification status; explicitly disclosed limitations (from compatibility adapters, §19); retry classification; terminality; the record digest; compatibility findings (per target, §14); and no-go confirmations (an explicit checklist mirroring §3.5/§20's prohibited-action list, each confirmed absent).

**These prototype reports are not canonical phase reports.** They satisfy none of PFR-001's twelve required sections and must never be mistaken for, substituted for, or promoted to canonical-report status — this is enforced by naming convention (`verification.json`/`manifest.json` under `.pcae/cltr-prototypes/`, never `.pcae/canonical-reports/`) and will be restated as an explicit no-go confirmation in 135E's own completion report (§33).

---

## 25. Security and safety plan

The prototype module graph (§4) has **no code path** to:

- shell execution beyond the explicitly bounded, read-only `git log -1 <hash>`/`git cat-file -e <hash>`/`git rev-parse` calls named in §8.2/§12 (no `subprocess` call with unbounded arguments, no shell=True, no arbitrary command construction from input data);
- backend invocation (the prototype has no network client, no RPC, no plugin/runtime invocation — `pcae runtime inspect`'s own output is only ever read as a static evidence reference, §13, never invoked);
- network calls (no `requests`/`httpx`/socket usage anywhere in `cltr_prototype/`);
- Telegram delivery (no import of any notification-sink module);
- phase completion (no import of `finalization_transaction.py` or any entry point);
- commit (`git commit` never invoked);
- push (`git push` never invoked);
- file mutation outside `.pcae/cltr-prototypes/` (enforced by `persistence.py` being the *only* module with write capability, and its write path being hardcoded to that prefix — no caller-suppliable output path escapes it);
- Decision Evaluation (no import of, or call into, any Decision Evaluation module);
- execution authorization (the prototype produces reports and comparisons, never a "may proceed" signal consumed by any gate);
- Repository Intelligence authority (no import of Repository Intelligence query/service modules; the prototype's own compatibility/comparison logic is self-contained, not a Repository Intelligence consumer or contributor).

This is a structural claim (verifiable by import-graph inspection and a `grep` for `subprocess`/`socket`/`requests` in the module list), not merely a stated intention — a future implementation phase's own completion report should re-confirm it exactly as 135D §36 did for the state-machine model.

---

## 26. Implementation stages

Derived from dependency order (each stage depends only on the prior), not assumed from the assignment's example verbatim — cross-checked against §4's dependency column:

**Stage 1 — Foundation (no state machine yet)**
`models.py` (data classes); `canonicalization.py`; `digest.py`. Acceptance: deterministic serialization and digesting of a hand-constructed record, no generation logic yet.

**Stage 2 — Identity and state machine**
`identity.py`; `state_machine.py`. Acceptance: all 16 permitted transitions succeed and all 14 forbidden transitions are rejected against hand-constructed inputs, independent of any generator.

**Stage 3 — Invariants**
`invariants.py`. Acceptance: all 36 invariants are evaluable (even if many trivially `inapplicable` against minimal test records) with no silent skips.

**Stage 4 — Generation and persistence**
`generator.py`; `persistence.py`. Acceptance: a full fixture-driven record can be generated and durably persisted, with crash-simulated partial-write tests passing.

**Stage 5 — Verification and comparison**
`verifier.py`; `compatibility.py`; `comparison.py`. Acceptance: a persisted record can be independently re-verified and compared against named targets, including at least one real (integration-fixture) Track 135 artifact.

**Stage 6 — CLI and full fixture set**
`commands/cltr_prototype.py`; all 15 fixtures (§17). Acceptance: every scenario in §2.2 is drivable end-to-end via the CLI.

**Stage 7 — Adversarial and determinism verification**
The full adversarial/determinism test categories of §18. Acceptance: acceptance criteria (§28) are all met.

This sequence is not assumed to be rigid — Stage 3 (invariants) could in principle proceed in parallel with Stage 2 once `models.py` is stable, since `invariants.py` depends on `state_machine.py`'s types but not its transition functions until integration testing. The dependency graph, not the stage numbering, is the actual constraint a future implementation phase must respect.

---

## 27. File-by-file implementation plan

| File | Create/modify | Responsibility | Dependencies | Test file | Imported by production? | Prototype-only? |
|---|---|---|---|---|---|---|
| `src/pcae/cltr_prototype/__init__.py` | Create | Package marker | — | — | No | Yes |
| `src/pcae/cltr_prototype/models.py` | Create | Data classes | stdlib | `tests/test_cltr_prototype_models.py` | No | Yes |
| `src/pcae/cltr_prototype/identity.py` | Create | Identity resolution | `models.py` | `tests/test_cltr_prototype_identity.py` | No | Yes |
| `src/pcae/cltr_prototype/state_machine.py` | Create | State/transition logic | `models.py` | `tests/test_cltr_prototype_state_machine.py` | No | Yes |
| `src/pcae/cltr_prototype/invariants.py` | Create | 36-invariant engine | `models.py`, `state_machine.py` | `tests/test_cltr_prototype_invariants.py` | No | Yes |
| `src/pcae/cltr_prototype/canonicalization.py` | Create | Canonical serialization | stdlib | `tests/test_cltr_prototype_canonicalization.py` | No | Yes |
| `src/pcae/cltr_prototype/digest.py` | Create | Digest compute/verify | `canonicalization.py` | `tests/test_cltr_prototype_digest.py` | No | Yes |
| `src/pcae/cltr_prototype/generator.py` | Create | Orchestration | all of the above | `tests/test_cltr_prototype_generator.py` | No | Yes |
| `src/pcae/cltr_prototype/verifier.py` | Create | Standalone verification | `digest.py`, `invariants.py`, `state_machine.py` | `tests/test_cltr_prototype_verifier.py` | No | Yes |
| `src/pcae/cltr_prototype/compatibility.py` | Create | Legacy/current adapters | `models.py` | `tests/test_cltr_prototype_compatibility.py` | No | Yes |
| `src/pcae/cltr_prototype/comparison.py` | Create | Cross-representation comparison | `compatibility.py`, `models.py` | `tests/test_cltr_prototype_comparison.py` | No | Yes |
| `src/pcae/cltr_prototype/persistence.py` | Create | Atomic prototype-path persistence | stdlib | `tests/test_cltr_prototype_persistence.py` | No | Yes |
| `src/pcae/commands/cltr_prototype.py` | Create | CLI wiring | all of the above | `tests/test_cltr_prototype_cli.py` | Only via `pcae`'s own CLI dispatch table (not by production lifecycle code) | Yes (command surface only) |
| `tests/fixtures/cltr_prototype/*.json` | Create (15 files) | Fixtures per §17 | — | (consumed by the test files above) | No | Yes |

No existing production file (`finalization_transaction.py`, the four entry points, `phase_reports.py`, `canonical_artifact_promotion.py`, `architecture_status.py`) is modified by this plan's implementation stages. This table is itself a plan artifact, not a commitment made by 135E — no file listed here is created in this phase.

---

## 28. Acceptance criteria

An implementation satisfies this plan when, at minimum:

1. Deterministic output for equivalent inputs (byte-identical across repeated runs and process restarts).
2. Stable digest (same content → same digest; any single-field mutation → different digest).
3. Full identity preservation (dotted/multi-dotted/suffixed IDs round-trip exactly).
4. No implicit transitions (no `set_state`-style escape hatch exists in the code).
5. All 36 formal invariants are evaluable against every fixture, with no silent skip of an applicable invariant.
6. All 14 forbidden transitions are rejected under test.
7. Exact replay is deterministic (resolves to the existing record, never re-executes PROMOTING-equivalent logic).
8. Conflicting replay is rejected.
9. Commit ownership is classified into exactly one of the three outcomes for every declared commit, with no silent default to `verified`.
10. Mixed-generation comparison targets are detected.
11. Tampering is detected via digest mismatch.
12. Historical/legacy compatibility is disclosed honestly (missing fields named, never invented).
13. No production lifecycle mutation occurs at any point (verified by the before/after `.pcae/` snapshot test, §18).
14. No external notification is ever sent.
15. No execution capability exists (verified by import-graph/`subprocess`-grep inspection, §25).
16. All planned tests (§18) pass.
17. Governance remains clean (`pcae health`/`pcae check`/`pcae doctor task-memory`/`pcae push check` all pass with the prototype code present).

---

## 29. Prototype verification criteria

Before any future integration-planning phase may begin, an independent verification phase (135G-class) must confirm, by re-derivation rather than by trusting the implementation phase's own report:

1. Every acceptance criterion in §28 was actually met, not merely claimed.
2. The module graph genuinely has no production coupling (re-derive §25's structural claim independently, e.g., via a fresh import-graph trace).
3. All 36 invariants were genuinely exercised by at least one fixture each (not merely present as dead code).
4. The 15 fixtures in §17 genuinely cover the 9 required scenarios in §2.2 with no scenario silently thinned out during implementation.
5. No prototype persistence path collides with, or could be confused for, any production canonical path.
6. The digest and canonicalization scheme is genuinely deterministic across at least two different process invocations (not just within one interpreter session).
7. The identity-resolution module genuinely has zero code path reading titles, filenames, or recent Git history (re-derive, don't trust, the §8.3/§25 claims).
8. The 135D.1 protections (§21) are genuinely present in the implementation, not merely referenced in comments.

---

## 30. Deferred decisions

| Decision | Classification |
|---|---|
| Which atomic-visibility mechanism (CLTR-001 §13.2) production ultimately adopts | Must remain deferred until integration planning (135H-class) |
| Whether `unverifiable` commit ownership blocks/warns/informs (CLTR-001 §10.4, §32.3 item 2) | Must remain deferred until integration planning — the prototype surfaces the classification but makes no policy choice |
| Whether `transition_id` subsumes `(report_digest, finalization_snapshot_id)` (CLTR-001 §5.1, §32.3 item 3) | May resolve during prototype implementation without changing CLTR-001 semantics — this is a prototype-local identity-generation detail (§8.2) |
| Exact byte-level canonical serialization for a future *production* digest (CLTR-001 §15.2, §32.3 item 4) | Must remain deferred until a dedicated schema-design phase — the prototype's own canonicalization (§7) is disposable and does not bind this |
| Exact event schema for the hybrid current-state/event-log model (§32.3 item 5) | Must remain deferred until schema-design |
| Exact bound on how long a provisional `final_revision` may remain unresolved (CLTR-001 §23.4 item 4, §32.3 item 6) | May resolve during prototype implementation without changing CLTR-001 semantics (a prototype-local constant, not a contract amendment) |
| Whether/how to backfill historical records for pre-Track-135 transitions (§32.3 item 7) | Must remain deferred until 135H-class integration/migration planning |
| Exact migration sequencing for legacy-authority retirement (CLTR-001 §25, §32.3 item 8) | Must remain deferred until 135H-class planning |
| CLTR-001 §37/§39's own carried-forward findings (branch-reachability not modeled; NOTIFIED_UNCONFIRMED naming/conflation; the third non-atomic write site at `canonical_artifact_promotion.py`'s `quarantine_artifact`; actor/session/agent provenance not bound) | Outside CLTR-001/this prototype's scope entirely — carried forward as-is, not re-opened |
| Exact module layout (§4's "not required exactly") | May resolve during prototype implementation without changing CLTR semantics |
| CLI command surface naming beyond `cltr-prototype` namespacing (§16) | May resolve during prototype implementation |

---

## 31. Risk register

| Risk | Likelihood | Impact | Mitigation | Verification method |
|---|---|---|---|---|
| Accidental production coupling | Low | High | No prototype module imports `finalization_transaction.py` or any entry point (§3.6, §25); enforced by module-graph design, not just intention | Import-graph inspection in 135F/135G |
| Derivative becoming authority | Low | High | S/R/D/E/V enforcement via type design (§11) — derivatives structurally cannot construct authoritative records | Unit tests asserting no derivative class has a `TransitionRecord`-producing constructor |
| Compatibility adapter strengthening evidence | Medium | Medium | Adapters always disclose `missing_fields`/`limitation`; never default-fill (§19) | Adversarial fixture 15 |
| Serialization instability | Medium | Medium | Explicit canonicalization rules (§6, §7), determinism tests (§18) | Cross-process determinism test |
| Digest ambiguity | Low | High | SHA-256 over fully canonicalized content, self-exclusion, transition-ID co-binding (§7, §15.1 item 5) | Tamper-detection adversarial tests |
| State-machine drift from CLTR-001/135D | Medium | High | Direct 1:1 mapping of the 16 permitted / 14 forbidden transitions (§9), no generic transition escape hatch | Full transition-table test coverage (§18) |
| Implicit transitions | Low | High | No `set_state()` function exists anywhere in the design (§9, §26 Stage 2 acceptance) | Code-review/grep check in a future implementation phase |
| Live-repository non-hermetic tests | Medium | Medium | Fixtures hermetic by default; integration fixtures explicitly separated and pinned to named files (§17) | Test-suite audit for any un-pinned live read |
| Prototype path confusion with canonical paths | Low | High | Disjoint path prefix (`.pcae/cltr-prototypes/` vs. `.pcae/canonical-reports/` etc., §15) | Path-prefix assertion tests |
| Stale source selection | Medium | Medium | Explicit-bundle mode requires named files only, never "latest" (§3.2, §3.7) | Adversarial fixture 7 (stale report) |
| Commit-verification policy leakage (prototype accidentally deciding a policy CLTR-001 defers) | Medium | Medium | Three-outcome classifier surfaces data only; no blocking/warning default is hardcoded (§12.1) | Code review + explicit test asserting no policy branch exists |
| Terminal-state replay bugs | Low | High | Terminal-state lookup is a pure function against the six terminal states; no transition function accepts a terminal-state input except the two orthogonal ones (§9) | Full terminal-state test matrix |
| Atomic pointer failure | Low | Medium | Write-temp-then-fsync-then-rename, manifest-based completeness check, history-based recovery (§15) | Crash-simulation integration tests |
| Overbuilding before proof | Medium | Medium | Staged plan (§26) explicitly sequences the smallest foundation first; CLI is deliberately last (§16, §26 Stage 6) | Stage-by-stage acceptance gating in a future implementation phase |

---

## 32. Phase sequence recommendation

The smallest next sequence after 135E:

- **135F** — Canonical Transition Record Read-Only Prototype (implementation of this plan's Stages 1-6).
- **135G** — Canonical Transition Record Prototype Verification (independent re-derivation against §29's criteria).
- **135H** — Lifecycle Integration and Legacy Authority Retirement Plan (a *plan*, not an implementation, for wiring the record into production and retiring legacy authorities — only after 135G's verdict).

These titles are illustrative, not binding — a future phase may split or rename them as long as the ordering (implement → independently verify → only then plan integration) is preserved.

**No separate executable schema-freeze phase is required before 135F.** CLTR-001 (135B, frozen and 135C-verified) already freezes every semantic requirement a schema must satisfy (§6.2's field list, §5's identity rules, §15.1's digest requirements), and 135D's formal model (14 states, 16/14 transitions, 36 invariants) already freezes every state-machine and invariant requirement. What remains open (exact wire bytes, exact storage mechanism) is explicitly and repeatedly deferred by CLTR-001 itself (§6.3, §13.2, §15.2) to be resolved empirically, which is exactly what a prototype is for — freezing a production schema *before* building this prototype would risk freezing decisions this prototype exists to inform, inverting 135D §41.3's own stated rationale for recommending a plan-then-prototype (not schema-then-prototype) sequence.

---

## 33. Planning verdict

## **A. READY FOR PROTOTYPE IMPLEMENTATION**

Justification against the stated criteria:

- No lifecycle semantics remain unresolved at the level this plan requires: the 14-state/16-transition/14-forbidden-transition model, the 36 invariants, the authority-role table, and the identity/commit-ownership rules are all already frozen (CLTR-001) and verified (135C, 135D) — this plan only translates them into a prototype-scoped implementation plan, inventing nothing beyond prototype-local, non-semantic choices (serialization bytes, module layout, fixture file names — all explicitly flagged as such in §30).
- The serialization plan (§6) is deterministic and explicitly disposable, with no claim of production finality.
- The state-machine implementation path (§9) is explicit: one function per transition, no generic escape hatch, direct 1:1 mapping to 135D's frozen transition inventory.
- All 36 invariants are evaluable by design (§10) — the engine's contract is to never silently skip an applicable one.
- The prototype boundary (§3) is isolated: no production import, no production write path, explicit-input-only reads, a disjoint persistence prefix.
- The test plan (§18) is complete relative to the required scenarios (§2.2) and the acceptance criteria (§28).
- No production integration is required or attempted anywhere in this plan (§20).

Remaining open items (§30) are, without exception, either prototype-local details safely resolvable during implementation without touching CLTR-001 semantics, or explicitly and correctly deferred to a later integration-planning phase (135H) — none of them concern authority, identity, state, ordering, terminality, retry behavior, or safety, so none of them would have justified verdict B ("ready with non-blocking implementation decisions") over A, and none rises to verdict C.

---

## Files changed by this phase

- `docs/PHASE_135_CANONICAL_TRANSITION_RECORD_PROTOTYPE_PLAN.md` (new — this document)
- `PROJECT_STATUS.md` (governed completion sync only)
- `CHANGELOG.md` (governed completion sync only)
- `tasks/DONE.md` (governed completion sync only)
- Active task contract, canonical phase report, completion metadata (governed completion artifacts only)

No source file, test file, or JSON schema is created or modified by this phase.

## Confirmations

- No implementation occurred. No prototype module, fixture, or CLI command was created.
- No runtime behavior changed. No production entry point, finalization transaction, or metadata-repair tool was touched.
- No execution capability was introduced. This document contains no code that runs.
- No CLTR-001 amendment occurred; no clause of CLTR-001 is weakened, narrowed, or reinterpreted by this plan.
- No JSON schema was frozen.
- No Track 134 structural gap (non-atomic `latest.*` pair; fabricated-hash silent-continue; NOTIFIED_UNCONFIRMED-equivalent resume classification in production) was repaired.
- No Repository Intelligence, Advisory, or Decision Evaluation authority was expanded or changed.
- PFN-001 and PFR-001 are unchanged.
- Phase 135F was not begun.

## Recommended next phase

135F — Canonical Transition Record Read-Only Prototype (implementation of §26's staged plan, subject to this plan's acceptance criteria, §28).
