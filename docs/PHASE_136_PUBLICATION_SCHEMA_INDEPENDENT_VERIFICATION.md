# Phase 136Q: Publication Schema Independent Verification

## Status

VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR RECOVERY SCHEMA IMPLEMENTATION

## 0. Purpose and scope

Phase 136Q independently re-derives, from primary sources, and attempts to
falsify the exact Implementation Group 5 (`PublicationAttempt`,
`PublicationEvidence`) executable-schema implementation delivered by Phase
136P (commit `2eb79b9f`), against CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0's
frozen primary contract (`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`).
This phase does not trust 136P's own tests, prose, field interpretation, or
finding dispositions — every claim below was independently re-derived and,
where feasible, adversarially re-tested against a freshly built package
(wheel + isolated venv), not merely 136P's own in-repo test suite.

Legacy lifecycle remains the sole production authority. CLTR remains
derivative.

## 1. Methodology

1. Re-read the frozen contract's §46 (implementation groups), §24
   (`CASExpectation`), §25 (`PublicationAttempt`), §26 (`PublicationEvidence`)
   directly from `PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`,
   without reading 136P's own summary of those sections first.
2. Independently listed the on-disk schema/manifest inventory (`find`,
   `grep`, `python3 -m json.tool`) and cross-checked counts against the
   contract's own text, not against 136P's self-reported counts.
3. Read the two new schema files
   (`records/publication_attempt.schema.json`,
   `records/publication_evidence.schema.json`) and the shared
   `cas_expectation` `$def` directly, and manually diffed every field against
   the contract's own field tables.
4. Rebuilt the `$ref` dependency graph from scratch with independently
   written Python (not 136P's graph code) and checked for cycles across all
   16 Group 1–5 schema files.
5. Built a fresh wheel and sdist, installed the wheel into a clean, isolated
   virtualenv (no repository working-tree paths), and exercised the
   installed package's registry construction and record validation there —
   not inside the repository's own dev environment.
6. Authored a fresh, independently-derived adversarial test module,
   `tests/test_cltr_cutover_136q_publication_schema_independent_verification.py`
   (70 tests), that does not import fixtures or assertions from 136P's own
   `tests/test_cltr_cutover_136p_publication_schema.py`.
7. Ran the full regression matrix (per-group implementation and
   independent-verification suites, schema-runtime suite, Fast Green, full
   unmarked suite) and independently classified every failure.
8. Built an isolated `git worktree` at the pre-136P commit (`077e4e64`,
   136O's close) to compare the composition of the 21 unmarked-suite
   failures against a pre-Group-5 baseline, rather than trusting 136P's
   "21 inherited failures" claim at face value.

## 2. Section 46 group assignment — independently re-derived

The frozen contract's §46 table (`CONTRACT_FREEZE.md` lines 1650–1675) reads,
verbatim:

```
| 7 | publication_attempt.schema.json, publication_evidence.schema.json | 1–6 | yes |
| 8 | concurrency_conflict.schema.json, recovery_journal_entry.schema.json | 1–7 | yes |
```

Independently confirmed: the contract's own group containing the two
publication files (its own numbering: **group 7**) is **exactly**
`{PublicationAttempt, PublicationEvidence}`. `ConcurrencyConflict` and
`RecoveryJournalEntry` are a separate, later table row (the contract's own
**group 8**), atomically paired with each other, sharing prerequisite groups
1–7 — i.e. requiring the publication group to close first.

**A separate, non-authoritative document — the implementation plan
(`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`,
§9.4, lines 909–997 and its file table lines 522–533) — groups the
*scheduling* phases differently**, bundling `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournalEntry`, and
`QuarantineRecord` under one *local phase-numbering* label, "Group 5 — CAS,
publication, recovery, and quarantine," mapped to phases 136P/136Q. This is
the origin of the task prompt's expectation that `ConcurrencyConflict`
belongs in this phase. **The frozen contract's §46 table governs, not the
implementation plan's own scheduling label** — this is not a new
interpretation invented by 136Q; it is the same conclusion 136P's own
implementation document independently reached and disclosed (`PHASE_136_PUBLICATION_SCHEMA_IMPLEMENTATION.md`
§2, "Contract/task discrepancies"). 136Q independently re-derived this from
the contract text itself (§1 above) before reading 136P's disclosure, and
confirms it: **CONTRACT-CONFORMANT, not a defect.**

`ConcurrencyConflict`'s correct contract-defined group is **group 8**,
paired atomically with `RecoveryJournalEntry`, per `CSCH-EXEC-REQ-062`'s
per-group atomicity rule (splitting the pair to satisfy the plan's looser
"Group 5" label would itself have violated `CSCH-EXEC-REQ-062`).

Independently confirmed: no `concurrency_conflict.schema.json` or
`recovery_journal_entry.schema.json` file exists on disk, in the manifest,
in the registry, in fixtures, or in the built wheel.

## 3. Exact inventory and manifest counts — independently verified

Directly enumerated via `find`, `python3 -m json.tool`, and a Python script
over `manifest.json`:

| Item | Independently confirmed count |
|---|---|
| Shared resource files | 7 (`envelope`, `enums`, `identity`, `digest`, `references`, `failures`, `limitations`) |
| Production record schema files | 9 (`authority_epoch`, `authority_state`, `cutover_request`, `readiness_package`, `human_authorization`, `cutover_candidate`, `certification`, `publication_attempt`, `publication_evidence`) |
| Total manifest entries | 16 (7 shared + 9 records) |
| Manifest entries tagged `implementation_group: 5` | 2 — exactly `publication_attempt`, `publication_evidence` |
| Group 6+ record schema files | 0 |
| `ConcurrencyConflict` schema files | 0 |
| Standalone `CASExpectation` schema files | 0 |
| `bindings/` directory | absent |
| `views/` directory | absent |
| Duplicate `schema_id` or `file_path` entries | 0 |
| Manifest entries whose `file_path` is missing on disk | 0 |

**Re-evaluated inherited finding NON-BLOCKING-136M-2** (manifest authoring
metadata): the manifest's own `implementation_group` integer field uses the
**5-phase local authoring sequence** (136H/J/L/N/P → groups 1–5), not the
frozen contract's own §46 11-group numbering (where publication is group 7).
This is confirmed, unchanged, and still non-blocking for Group 5's two new
entries — it is descriptive authoring metadata, not contract-authoritative
grouping, and is not treated as authority truth by this verification.

## 4. `PublicationAttempt` field verification (§25)

Every field in the contract's §25 table was independently reconstructed and
diffed against `records/publication_attempt.schema.json`:

| Field | Contract | Schema | Verdict |
|---|---|---|---|
| `attempt_id` | required, deterministic digest of bound-field tuple | required, `record_identity` shape, description discloses determinism is Layer 4 | conformant |
| `request_reference`, `candidate_reference`, `certification_reference` | required, all three | required, family-restricted `allOf` refs with mandatory `schema_id`/`schema_version` | conformant |
| `cas_expectation` | required, embedded | required, `$ref` to shared `$def` | conformant |
| `source_authority_reference`, `target_authority_reference` | required, both | required, family-restricted to `authority_epoch` | conformant |
| `attempt_sequence` | required, monotonic integer | required, `integer, minimum: 0`; monotonicity documented as Layer 4 | conformant |
| `temporary_pointer_reference` | conditional ("present only during in-flight publication") | freely optional — **no if/then trigger** since §16 names no enum value that structurally gates it | **NON-BLOCKING-136P-1 (re-confirmed, unchanged)** |
| `state` | required, `PublicationState` | required, `$ref` shared enum | conformant |
| `uncertainty` | conditional (`state == publication_uncertain`) | enforced via `if`/`then`/`else` | conformant (independently re-tested) |
| `created_at` | required, documentation only | required, explicit non-identity disclosure | conformant |
| `failure_classification` | conditional (`state` in `{gate_rejected, conflict}`) | enforced via `if`/`then`/`else` | conformant (independently re-tested) |
| `limitations` | required | required, shared array | conformant |
| `digest` (envelope `record_digest`) | required | required (universal envelope field) | conformant |

No omitted field, no invented field, no extra Group 6+ field found.

## 5. `PublicationEvidence` field verification (§26)

| Field | Contract | Schema | Verdict |
|---|---|---|---|
| `attempt_reference` | required, → `publication_attempt` | required, family-restricted `allOf` ref | conformant |
| `outcome` | required, 8-value `PublicationOutcome` | required, record-local `enum` with the exact 8 values | conformant (independently re-tested against all 8 + 4 invalid values) |
| `uncertainty_detail` | conditional (`outcome == publication_uncertain`) | enforced via `if`/`then`/`else` | conformant (independently re-tested) |
| `target_readback` | conditional (`outcome == published_and_verified`) | enforced via `if`/`then`/`else` | conformant (independently re-tested) |
| `authoritative_generation` | conditional (same trigger), enables permitted `authority_role: authoritative` | enforced via `if`/`then`/`else`; typed as `generation_reference` (id+digest only, no family tag, since "generation" is not itself a `record_family` value) | **NON-BLOCKING-136P-2 (re-confirmed, unchanged)** — documented, precedent-consistent typing choice, not an invented field |
| `limitations` | required | required | conformant |
| `digest` | required | required (universal envelope field) | conformant |

`is_authoritative` remains `const: false` unconditionally, even when
`authority_role: "authoritative"` is the schema-permitted value under the
`published_and_verified` gate — independently re-tested and confirmed: a
document attempting to override `is_authoritative` to `true` is rejected.

## 6. Attempt/Evidence separation and wrong-family substitution

Independently re-tested (fresh fixtures, not 136P's): a `PublicationEvidence`
document is rejected against the `PublicationAttempt` schema and vice versa;
`certification_reference` cannot be substituted for `candidate_reference`
(and the reverse); `authority_state`-family references are rejected where
`publication_attempt`-family is required; a record with the correct field
present but the wrong `record_family` const is rejected (proves the
restriction is enforced structurally, not merely that the field exists).
**No family collapse found.**

## 7. `ConcurrencyConflict` exclusion — independently confirmed

Repository-wide `grep` across `src/`, `tests/`, `docs/` confirms:
`ConcurrencyConflict` appears only in documentation (contract text,
disclosed-scope-exclusion statements, other groups' scope guards) and in
other phases' *forbidden-inventory* test lists (asserting its absence) — no
schema file, manifest entry, registry resource, or fixture defines it.
Conflict detection, classification, resolution, retry decision,
winning-authority selection, and reconciliation remain unimplemented, as
required. Its correct contract group is **8** (see §2).

## 8. `CASExpectation` verification (§24)

Independently diffed `shared/references.schema.json#/$defs/cas_expectation`
against the contract's §24 table: **all 11 fields present, all 11
unconditionally required, `additionalProperties: false`, no optional field**
— independently re-confirmed via a direct schema introspection assertion
(`set(required) == set(properties)`), not merely a fixture test.

**Three embedding sites independently confirmed** by `grep` over every file
in `records/`: `cutover_candidate.schema.json`, `certification.schema.json`,
`publication_attempt.schema.json` — no fourth site, no missing site. No
standalone `CASExpectation`/`cas_expectation.schema.json` file exists. A
schema-valid `cas_expectation` object does not itself prove a CAS was
attempted or would succeed (Layer 5, out of this contract's scope).

## 9. Dependency graph verification

An independently authored Python script (not 136P's graph code) built the
`$ref` graph over all 16 Group 1–5 schema files and found **no cycle** —
self, mutual, or hidden through shared `$defs`. `publication_attempt.schema.json`
contains no textual reference to `publication_evidence` anywhere in its
content; `publication_evidence.schema.json` references `publication_attempt`
only via its family-restricted `attempt_reference` `$def` (one-directional).
The only valid creation order — `PublicationAttempt` before
`PublicationEvidence` — is the order enforced by the schema shapes
themselves; no cycle through candidate, certification, or CAS expectation
references was found.

## 10. Strictness, enums, and local-shape-vs-semantic-truth boundary

Both files are Tier 1 (`additionalProperties: false`, no `_extensions`
escape hatch) — independently confirmed by direct inspection, not assumed
from ReadinessPackage's Tier 2 precedent. Unknown top-level fields,
misspelled fields, and unsupported enum values are all independently
re-tested and rejected. Locally invalid state/outcome combinations
(`state == conflict` without `failure_classification`; `outcome ==
published_and_verified` without `target_readback`/`authoritative_generation`)
are structurally rejected by JSON Schema `if`/`then`. Cross-record or
temporal truths — CAS success, publication success, evidence truthfulness,
authority currency, concurrency truth, recovery eligibility — are **not**,
and were independently confirmed not to be, asserted anywhere in either
schema; both files' own descriptions explicitly disclaim each of these.

## 11. Packaging, isolated-wheel, no-network, no-authority, no-execution verification

- Built a fresh wheel and sdist (`python -m build`) from a clean state;
  confirmed the wheel contains exactly the 7 shared + 9 record schema files,
  `manifest.json`, `manifest.schema.json`, and `README.md` — no
  `bindings/`, `views/`, Group 6+ file, or `ConcurrencyConflict`.
- Installed the wheel into a clean, isolated virtualenv with no
  repository-working-tree paths; exercised offline registry construction,
  valid/invalid `PublicationAttempt` and `PublicationEvidence` validation
  there (13/13 independently-authored adversarial checks passed after
  correcting two errors in the *test fixtures themselves*, not the schema —
  see the fixture-shape corrections for `authority_disclosure` and
  `expected_compatibility_mode` during this verification's own drafting).
- Blocked `socket.socket`/`socket.create_connection` before registry
  construction in the isolated venv; construction succeeded with no network
  access attempted.
- Repository-wide search found no `subprocess`, `socket.`, `urllib`,
  `requests.`, or `http.client` usage anywhere in `schema_resources` or
  `schema_runtime`; no authority-resolver, publication-coordinator, or
  CAS-execution module exists anywhere in `src/`; no `.pcae/cltr-authority/`
  directory exists.
- `pcae runtime inspect` confirms: runtime state `Observed`, maximum
  capability `observe`, execution availability `unavailable` — unchanged.

No publication, CAS, authority-pointer mutation, or execution capability
exists anywhere in this phase's scope.

## 12. Secret-like value review

Free-text disclosure fields (`uncertainty.reason`,
`uncertainty_detail.last_known_state`) are opaque strings at the schema
level — plausible secret-shaped strings (AWS-style access-key prefix,
`postgresql://user:pass@host` URL, PEM private-key header) are neither
specially rejected nor specially detected; this is disclosed, not claimed as
a mitigation the schema does not provide. No real secret exists in any
schema file, fixture, or test authored by this phase or by 136P.

## 13. Fresh regression evidence

| Suite | Result |
|---|---|
| 136Q independent tests (this phase, freshly authored) | 70 / 70 passed |
| 136P Group 5 implementation tests | 129 / 129 passed (re-run) |
| Combined Groups 1–5 + schema-runtime suite (incl. 136Q's new module) | 1316 / 1316 passed |
| Fast Green (`pytest -m fast_green -n auto`) | 4391 / 4391 passed — matches 136P's self-reported count exactly |
| Full unmarked suite (`pytest -n auto`, no markers) | 21303 passed, 21 failed |

**Full-suite failure classification (independently re-derived, not
assumed):** none of the 21 failing node IDs touch `cltr_cutover`,
`schema_runtime`, `publication`, `136p`, or `136q` (confirmed by grepping
the failure list). All 21 are pre-existing failures in unrelated
subsystems: `test_advisory_runtime_contract`/`_architecture`,
`test_phase_reports`, `test_rendering_134e5`,
`test_architecture_status_generation_independent_verification_134e8v`,
`test_finalization_transaction_134e10` (5 cases),
`test_cltr_migration_135p_verification` (4 parametrized cases),
`test_risk_register`, `test_bootstrap_todo_consistency` (2 cases),
`test_cltr_135o_integration` (3 cases). **Zero new Group 5 regressions.**

**Baseline comparison (isolated `git worktree` at pre-136P commit
`077e4e64`, per this phase's own instruction to prefer a worktree over
`git stash`):** running the identical 21 node IDs against the 136O-era
worktree produced only **6** failures, not 21 — `test_advisory_runtime_contract`,
`test_advisory_runtime_architecture`, `test_rendering_134e5`,
`test_architecture_status_generation_independent_verification_134e8v`, and
both `test_bootstrap_todo_consistency` cases. The other 15 node IDs
(`test_phase_reports`, all 5 `test_finalization_transaction_134e10` cases,
all 4 `test_cltr_migration_135p_verification` cases, `test_risk_register`,
all 3 `test_cltr_135o_integration` cases) **passed** at the 136O-era
baseline.

**This is a genuine, disclosed observation, not a Group 5 regression**: all
15 tests that newly fail read *live* repository state — `tasks/TODO.md`,
`PROJECT_STATUS.md`, phase-completion metadata, migration-evidence
directories — that legitimately changes as each governed phase commits its
own lifecycle artifacts. None of the 15 reference `cltr_cutover`,
`schema_runtime`, `publication_attempt`, or `publication_evidence` in any
form. The "21 inherited failures" figure that 136P (and this phase)
observed at `HEAD` is **not a stable, frozen list of node IDs across
phases** — its composition shifts as the repository's own governed-lifecycle
state advances, while happening to still total 21 at this point in time.
Disclosed as **NON-BLOCKING-136Q-1**: future phases should not assume the
21 failing node IDs are fixed; each phase's own full-suite run should
re-derive which failures are live-state-dependent versus genuinely
code-level regressions, exactly as this phase did via the isolated-worktree
comparison.

## 14. Findings table

| ID | Description | Classification |
|---|---|---|
| NON-BLOCKING-136P-1 | `temporary_pointer_reference` has no `if`/`then` trigger condition (§16 names none) | Re-confirmed, unchanged, non-blocking |
| NON-BLOCKING-136P-2 | `authoritative_generation` typed as `generation_reference` (id+digest, no family tag) rather than a literal §24 "record_reference" | Re-confirmed, unchanged, non-blocking (precedent-consistent) |
| NON-BLOCKING-136M-2 | Manifest `implementation_group` field uses local 5-phase numbering, not contract §46's 11-group numbering | Re-confirmed for Group 5's two new entries, unchanged, non-blocking |
| NON-BLOCKING-136Q-1 (new) | The unmarked full-suite's "21 inherited failures" is not a stable frozen node-ID set across phases; its composition shifts with live governed-lifecycle state while the count happens to remain 21 at this point | Disclosed, non-blocking — no Group 5 code implicated |
| CONTRACT-CONFORMANT | Task-prompt-suggested Group 5 inventory (including `ConcurrencyConflict`) diverges from the frozen contract's own §46 group 7; 136P correctly followed the frozen contract | Confirmed independently, not a defect |

**No Blocking finding was found or reproduced.** No repair was necessary or
performed; this phase's file changes are limited to its own governed
artifacts (task contract, this document, the new test module, and
finalization metadata).

## 15. Required confirmations

Legacy lifecycle remains the sole production authority.
CLTR remains derivative.
136Q independently verified the exact Group 5
PublicationAttempt and PublicationEvidence executable-schema
implementation against the frozen primary contract.
Section 46 assigns exactly PublicationAttempt and
PublicationEvidence to Group 5 (the contract's own group 7).
ConcurrencyConflict is not part of Group 5 and was not
implemented.
The Section 24 cas_expectation definition remains an embedded
shared definition and not a standalone record family.
No ConcurrencyConflict, RecoveryJournalEntry,
ReconciliationResult, QuarantineRecord, notification binding,
marker binding, receipt binding, CompatibilityState,
HistoricalAuthorityReference, or derived record-view schema
was implemented.
No Stage 3 typed record model or broad cross-record semantic
validator was implemented.
No cryptographic verification, authorization evaluator,
certification evaluator, publication evaluator, concurrency
resolver, authority resolver, authority-state persistence, or
authority pointer was implemented or changed.
No runtime PublicationAttempt or PublicationEvidence object
was created or persisted.
No publication, compare-and-swap operation, pointer mutation,
authority activation, recovery, reconciliation, or conflict
resolution occurred.
Schema validity does not establish authorization truth,
certification authenticity, candidate eligibility, CAS
correctness, publication success, evidence truth,
concurrency truth, recovery truth, current authority, or
lifecycle authority.
No authority epoch changed.
No CLTR authority was created.
No legacy authority was demoted.
No legacy authority was retired.
No production lifecycle behavior changed.
No execution capability was introduced.
Runtime remains Observed, maximum capability remains observe,
and execution availability remains unavailable.

## 16. Limitations and deferred work

- Section 16's local-conditional table does not name an explicit trigger for
  `temporary_pointer_reference`'s "in-flight-only" requirement
  (NON-BLOCKING-136P-1); enforcing it is deferred to a future semantic
  validator (Layer 4).
- Secret-shaped free-text values are neither rejected nor detected at Layer
  2 (§12 above); this is a documented limitation, not a mitigation gap this
  phase introduces or is required to close.
- The composition of the unmarked full-suite's inherited-failure set is not
  frozen (NON-BLOCKING-136Q-1); future phases should re-derive it via an
  isolated-worktree baseline rather than assuming a fixed count or fixed
  node-ID list.

## 17. Verification verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR RECOVERY SCHEMA
IMPLEMENTATION.**

## 18. Recommended next phase

**136R — Recovery Schema Implementation**, scoped to the frozen contract's
own §46 group 8: `ConcurrencyConflict` (`concurrency_conflict.schema.json`)
and `RecoveryJournalEntry` (`recovery_journal_entry.schema.json`), paired
atomically per `CSCH-EXEC-REQ-062`. `QuarantineRecord` belongs to the
contract's own group 11 (partial, depending on groups 2–8), not group 8 —
its inclusion or exclusion from 136R is left to that phase's own governed
scoping, not assumed here. Phase 136Q does not begin 136R.
