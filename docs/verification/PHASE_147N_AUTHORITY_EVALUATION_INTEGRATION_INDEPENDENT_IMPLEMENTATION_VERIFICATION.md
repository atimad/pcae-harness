# Phase 147N — Authority Evaluation Integration Independent Implementation Verification

**Phase ID:** 147N
**Mode:** Independent Implementation Verification
**Implementation baseline:** Phase 147M (`src/pcae/aesic/**`)
**Normative contract:** AESIC-001 v1.3 (`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`, 2930 lines, AESIC-REQ-001 through AESIC-REQ-131)
**Architecture baseline:** Phase 147J
**Contract verification baseline:** Phase 147L.6
**Verification-only phase.** No production repair, no contract amendment, no schema change, no runtime-capability change.

---

## 1. Executive Summary

This phase independently re-verifies the Phase 147M implementation of AESIC-001
v1.3 — the Authority Evaluation Service (AES) integration surface — by
reconstructing the contract's requirements from source, inspecting the
production code directly, and executing a freshly authored, adversarial test
suite (`tests/test_phase_147n_authority_evaluation_integration_independent_verification.py`,
64 tests, independently designed, not derived from Phase 147M's own test
file) against real filesystem persistence, real concurrency, and real
source-boundary inspection.

**Overall verdict: AUTHORITY EVALUATION INTEGRATION VERIFIED WITH NON-BLOCKING
FINDINGS.**

The implementation is architecturally sound: the pure evaluator
(`pcae.authority_evaluation`) is confirmed byte-for-byte unchanged since
Phase 147H by direct `git diff`; AES is confirmed the sole orchestrator with
no leakage into Publication, Interactive Workflow, or the Registry adapter;
Stage 1 is confirmed advisory and non-persistent; Stage 2 is confirmed to
always perform a fresh evaluation and never trust caller-supplied Stage 1
content; idempotency, multi-generation supersession, AER immutability,
post-crash recovery, and concurrent-write safety were all independently
reproduced against real storage. One **Major** finding (a canonical-pointer
cross-key confusion gap, AESIC-N-01) and two **Informational** findings were
newly, independently discovered during this phase (not disclosed in the
Phase 147M implementation report) and are documented in §29. None is
Blocking.

## 2. Verification Method

Per this phase's own §2 discipline, the contract and Phase 147J architecture
were read and the implementation independently reconstructed **before**
consulting Phase 147M's implementation report or traceability matrix. The
sequence actually followed:

1. Read `docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md` (v1.3, full).
2. Read every file in `src/pcae/aesic/**` (2049 lines across 9 modules) and
   `src/pcae/authority_evaluation/**` (656 lines across 6 modules) directly,
   without reference to the 147M report.
3. Traced the four integration call sites named in `PROJECT_STATUS.md`:
   `interactive_workflow/publication_handoff/{models,handoff}.py`,
   `interactive_workflow/application/session_service.py`,
   `governance/publication/record.py`.
4. Searched the whole `src/pcae` tree for `aesic`/`AuthorityEvaluation`
   references (`grep -rl`) to independently derive the actual import graph,
   rather than trusting the architecture-edge list in the phase prompt.
5. Reproduced one candidate defect live against the real
   `AuthorityEvaluationRecordStore` (§16 below) before writing any test, to
   confirm it was real and not a misreading.
6. Authored 64 independent, adversarial tests exercising real filesystem
   persistence (`tmp_path`), real thread concurrency, `ast`-based static
   import-graph checks, and `git diff` against the Phase 147H commit.
7. Ran the new suite alone, then combined with the three pre-existing
   Authority Evaluation suites, then the full `fast_green` gate.
8. Only after all of the above did this document cross-reference Phase
   147M's own implementation report (`docs/implementation/PHASE_147M_AUTHORITY_EVALUATION_INTEGRATION_IMPLEMENTATION.md`) and its disclosed
   non-blocking findings (§28 below).

## 3. Primary-Source Reconstruction

Independently re-derived understanding of the contract, prior to consulting
Phase 147M's report:

- **AES (§5)** is the sole orchestrator: sole reader of `Session.owner_identity`
  for evaluation, sole resolver of Decision Templates, sole caller of
  `AuthorityRegistry.resolve()`, sole invoker of the frozen `evaluate()`.
  Confirmed in `src/pcae/aesic/service.py`: `AuthorityEvaluationService`
  owns a `DecisionTemplateResolution` instance internally and is the only
  production caller of `evaluate()` found by `grep -rn "evaluate(" src/pcae`.
- **Stage 1 (§9.1)** is advisory, optional, non-persistent, produces a
  `Stage1EvaluationResult` value object the caller may discard.
- **Stage 2 (§9.3)** always performs a fresh Registry lookup and fresh
  `evaluate()` call — a caller-supplied Stage 1 result is validated
  structurally (session/identity/template agreement) but its *outcome* is
  never trusted as Stage 2's own result.
- **AER (§8)** is an immutable, digested, compound-keyed
  (`package_id`, `evaluation_id`) record; a separate, package_id-keyed
  **canonical pointer** (§12.1) provides mutable current-effective
  indirection with its own digest.
- **Idempotency (AESIC-REQ-023/121)**: a Stage 2 result substantively equal
  to the current canonical AER (all fields except `evaluation_id`/
  `evaluated_at`, plus Stage 1 evidence equivalence) is a no-op; anything
  else creates a new, distinct AER and advances the pointer.
- **CHGR integration (§14/§22)**: only `citation_text` — never the full AER,
  never `evaluation_result` — flows into `authority_basis_claimed`, and only
  when both `authority_evaluation_ref` and `citation_text` are present on
  the `PublicationReadinessPackage`.
- **Disclosure-only, non-gating (§19)**: no evaluation outcome may block,
  authorize, or execute anything; Publication Coordinator's own execute()
  transaction is untouched.

This reconstruction was then checked against the actual code (§5–§8 below)
before any test was written.

## 4. Requirement Verification Matrix

All 131 requirements (AESIC-REQ-001–131) were independently accounted for.
Requirements are grouped by the production module/behavior that governs them;
each row cites production evidence (file/symbol) and independent test
evidence (this phase's own suite, file `tests/test_phase_147n_…verification.py`,
abbreviated **147N**) rather than Phase 147M's own classification.

| Req range | Area | Production evidence | Verification method | 147N test evidence | Result |
|---|---|---|---|---|---|
| 001, 005, 006, 016, 017 | AES sole-orchestrator ownership | `service.py` `AuthorityEvaluationService` | Static import-graph + runtime | `TestArchitecturalLeakage.*`, `TestAesOwnership.*` | Independently Verified |
| 002–004, 007–009, 011–015 | AES construction/statelessness/general prose obligations | `service.py.__init__` (constructor-injected `registry`, `aer_store`) | Source inspection, runtime instantiation with distinct instances | `TestAesOwnership.test_aes_constructor_takes_no_ambient_global_state` | Independently Verified |
| 010 | Closed integration-error taxonomy, no bare `Exception` | `errors.py` | Class hierarchy inspection | `TestErrorTaxonomyDistinctness.*` | Independently Verified |
| 018, 020–022, 024–026 | Registry ABC shape / general resolution prose | `authority_evaluation/registry.py` (frozen, unchanged) | `git diff` since 147H; source read | `TestArchitecturalLeakage.test_evaluator_package_byte_for_byte_unchanged_since_phase_147h` | Independently Verified |
| 027–039 | Decision Template Resolution: internal-only, no cache/retry, one Registry call, exact-pair resolution, ordering before `evaluate()` | `resolution.py` | Source read + monkeypatch-assertion (Registry/store must not be touched before validation elsewhere) | `TestDecisionTemplateResolutionAttacks.*`, `TestStage2Ordering.test_stage_1_handoff_validation_happens_before_any_registry_or_store_access` | Independently Verified |
| 040–049 | Registry: one abstract method, pure function, no duplicate scan, restart-durable, no git read, immutable-write convenience only | `registry_filesystem.py` | Real filesystem attacks | `TestRegistryAttacks.*` | Independently Verified |
| 050, 052, 053, 057, 060–063, 065, 066, 068–079, 081, 084, 085, 087–090, 092–094, 096, 099–108, 110–117, 125, 128 | Broader behavioral/prose obligations (naming, documentation-shape, evidentiary-completeness, non-authorization framing) not individually re-cited in production docstrings | Cross-cutting: `models.py`, `service.py`, `records.py`, all Stage 1/Stage 2 code paths | Holistic behavioral testing (these requirements are satisfied as emergent properties of the mechanisms independently tested in the adjacent, explicitly-cited rows, not as separately pinpointable code branches) | Covered by `TestStage1AdvisorySemantics`, `TestStage2Ordering`, `TestNonGating`, `TestChgrCitationOnlyBoundary`, and the pre-existing 147M suite (242 tests) re-run in combination (§35) | Independently Verified (behavioral/emergent — see note below) |
| 051, 054–056, 082, 083, 086, 118, 119, 122 | AER/pointer shape, digest ownership, storage layout | `records.py`, `storage.py` | Real persistence, digest tamper, truncation | `TestAerCorruption.*`, `TestCanonicalPointerIntegrity.*` | Independently Verified |
| 058, 059, 067, 109 | CHGR citation-only integration, Stage 2 outside publication transaction, byte-for-byte no-op when unconfigured | `record.py`, `session_service.py` | Real CHGR record construction | `TestChgrCitationOnlyBoundary.*`, `TestNonGating.*` | Independently Verified |
| 064, 080 | Stage1EvaluationResult never independently persisted | `records.py` (no store method accepts it standalone) | Source read; store API surface enumeration | `TestStage1AdvisorySemantics.test_stage_1_creates_no_aer_and_no_pointer` | Independently Verified |
| 091, 095, 097 | Non-gating advisory Stage 1; diagnostics read-only | `session_service.py`, `diagnostics.py` | Source read + dynamic non-gating test | `TestWorkflowIntegrationSurface.*`, `TestDiagnosticsAreReadOnlyAndNeverGate.*` | Independently Verified |
| 098 | `evaluation_id` per-invocation uniqueness | `service.py._new_evaluation_id` (uuid4) | Repeated invocation | `TestIdempotencyMatrix.test_evaluation_id_and_evaluated_at_excluded_from_equivalence` | Independently Verified |
| 120 | Disclosed last-write-wins pointer concurrency | `storage.py.write_pointer` docstring + `_write_atomic_json` (no CAS) | Real concurrent threads | `TestConcurrency.*` | Independently Verified |
| 121, 129 | Idempotency-equivalence field set | `service.py._outcome_fields_equal`, `records.py.stage_1_evidence_equivalent` | Exhaustive matrix of field-by-field variation | `TestIdempotencyMatrix.*` (6 tests) | Independently Verified |
| 123, 124 | Stage 1 handoff validation, ordering | `service.py._validate_stage_1_handoff` | Forged/cross-session/malformed evidence | `TestAesOwnership.test_evaluate_stage_2_ignores_out_of_band_stage_1_outcome_field_tampering`, `TestStage2Ordering.*` | Independently Verified |
| 126, 127, 130, 131 | Canonical pointer digest verification, fail-closed corruption handling, `CanonicalPointerUpdateFailedError` | `storage.py.read_canonical/read_pointer`, `service.py.evaluate_stage_2` | Real digest tamper, real pointer-write failure injection | `TestCanonicalPointerIntegrity.*`, `TestCrashRecovery.*` | **Partially Verified — one gap found (AESIC-N-01, §29)** |

**Note on the aggregated band (050–117 etc.):** AESIC-001 v1.3's 131
requirements are not uniformly one-behavior-per-requirement; a substantial
minority are definitional, evidentiary-completeness, or documentation-shape
obligations (e.g., "the outcome SHALL carry a human-readable field named
X") that are necessarily exercised together whenever the owning mechanism
(Stage 1, Stage 2, AER shape, CHGR citation) is exercised at all, rather than
individually branchable. This phase verified them by exhaustively exercising
the owning mechanisms (both via this phase's own 64 tests and by re-running
the pre-existing 147G/147H/147M suites, 306 tests total, in combination —
§35) rather than fabricating one synthetic test per prose clause. No
requirement in this band was found to be violated, contradicted, or
unreachable during that exercise. This is disclosed as a methodological
limitation of this verification pass, not asserted as equivalent in rigor to
the individually-adversarial rows above.

## 5. Package and Ownership Analysis

Verified via `ast`-based static import-graph inspection
(`TestArchitecturalLeakage`), not prose claims:

- `src/pcae/authority_evaluation/*.py` (excluding its own `__init__.py`/
  `registry.py`) imports neither `pcae.aesic` nor its own `registry` module
  — confirmed by parsing every file's import statements.
- `src/pcae/governance/publication/coordinator.py` has **zero** references
  to `aesic`, `AuthorityEvaluationService`, or `evaluation_result` anywhere
  in its source text (substring search, not just import statements).
- Exactly one file in `src/pcae/interactive_workflow/**`
  (`application/session_service.py`) imports `pcae.aesic`; every other file
  in that package tree was enumerated and confirmed clean.
- `registry_filesystem.py` (the concrete `AuthorityRegistry` adapter)
  contains no reference to `evaluate_stage_1`, `evaluate_stage_2`,
  `write_record`, `write_pointer`, or `AuthorityEvaluationRecord` — it
  cannot orchestrate lifecycle even accidentally.
- `DecisionTemplateResolution` is not re-exported from `aesic/__init__.py`
  — it is not part of the package's public surface, consistent with
  AESIC-REQ-027's "internal to AES" requirement.

No architectural leakage was found.

## 6. Evaluator Purity

`git diff f6142750..HEAD -- src/pcae/authority_evaluation/` (f6142750 being
the Phase 147H close-out commit) produces **empty output** — independently
re-derived confirmation that the package is byte-for-byte unchanged since
Phase 147H, not merely trusted from Phase 147M's report. Additionally
verified at runtime: `evaluate()` is deterministic across 25 repeated calls
with identical input, and performs no filesystem access (`builtins.open`
patched to raise; `evaluate()` still succeeds without calling it).

## 7. AES Verification

`AuthorityEvaluationService.__init__` takes `registry` and `aer_store` as
constructor arguments (no ambient singleton); two independently constructed
service instances backed by different registries/stores were confirmed to
never cross-contaminate (`TestAesOwnership.test_aes_constructor_takes_no_ambient_global_state`).
Attempted to bypass Stage 2's fresh-evaluation guarantee by handing it a
forged, internally-consistent `Stage1EvaluationResult` claiming ELIGIBLE for
an actually-ineligible identity — Stage 2 still produced the true
INELIGIBLE outcome, confirming AES never trusts embedded Stage 1 content as
its own Stage 2 result.

## 8. Resolution and Registry

`DecisionTemplateResolution.resolve()` reads exactly one template document
and makes exactly one Registry call per invocation, no caching, no "latest"
fallback (`resolution.py`, verified by direct source read). Attacked:
malformed templates (missing `eligible_authority`), templates whose
embedded identity disagrees with their storage path, empty/whitespace
citations, and requests for a template version that was never registered —
all fail closed via `DecisionTemplateResolutionFailedError`. Registry
attacks: embedded-identity/storage-path disagreement, corrupt JSON, and a
completely absent Registry root directory (which correctly yields
`INDETERMINATE`, not an error, per AESIC-REQ-044). Restart equivalence was
confirmed by constructing a fresh `FilesystemAuthorityRegistry` +
`AuthorityEvaluationRecordStore` instance and confirming an idempotent
Stage 2 retry from that fresh instance collapses to the same AER.

## 9. Stage 1

Confirmed Stage 1 creates no AER and no pointer entry
(`TestStage1AdvisorySemantics.test_stage_1_creates_no_aer_and_no_pointer`).
Confirmed a Registry-unavailable Stage 1 failure (simulated via `chmod 000`
on the Registry file, a real OS-level failure, not a mock) has no lasting
effect on a subsequent, independent Stage 2 success. Confirmed a stale
ELIGIBLE Stage 1 result, computed before eligibility was revoked, never
becomes the effective citation — the subsequent Stage 2 call independently
re-evaluates and correctly returns INELIGIBLE.

## 10. Stage1EvaluationResult

Confirmed frozen-dataclass immutability (attribute assignment raises),
required-field enforcement (missing `session_id` raises `TypeError` at
construction), empty-string rejection, and wrong-type `outcome` rejection —
all via direct construction attempts, not mocks.

## 11. Stage 2

Independently traced the ordering in `service.py.evaluate_stage_2` by
reading the source directly (line-by-line, §13 of this document's own
authorizing spec): Stage 1 handoff validation (`_validate_stage_1_handoff`)
executes strictly before any Registry or store access — proven, not just
read, by monkeypatching both `FilesystemAuthorityRegistry.resolve` and
`AuthorityEvaluationRecordStore.write_record` to raise `AssertionError` if
called, then confirming an invalid Stage 1 handoff fails via
`Stage1HandoffInvalidError` without tripping either guard
(`TestStage2Ordering.test_stage_1_handoff_validation_happens_before_any_registry_or_store_access`).
Confirmed zero state mutation (`store.list_evaluation_ids`/`read_pointer`
both empty) on a Stage 2 validation failure.

## 12. Idempotency

Built an independent equivalence matrix distinct from Phase 147M's own
(`TestIdempotencyMatrix`, 6 tests): fully-equivalent retry (no-op, verified
the SAME `record_id`/`evaluation_id` is returned, not merely an equal-content
new record); Stage 1 absent→present and present→absent (both correctly NOT
equivalent, both grow history by one); a template-version bump (correctly
not equivalent, correctly re-cites the new version's text); a changed
session identity (correctly not equivalent); and confirmed
`evaluation_id`/`evaluated_at` are excluded from the comparison (an
idempotent retry reuses the *original* AER's `evaluation_id` verbatim — the
freshly-generated `evaluation_id` for the retry's own internal comparison is
computed but discarded, never persisted).

## 13. AER

Attacked digest integrity directly against real persisted JSON: changing
`outcome.evaluation_result` without recomputing `record_digest` is caught by
`read_record` (`AuthorityEvaluationRecordCorruptError`); truncating the file
mid-content is caught; a differing-content write under the same compound key
is rejected (`AuthorityEvaluationRecordConflictError`); an identical-content
duplicate write is a safe no-op. All corruption fails closed, no case was
found where corrupted content was silently accepted.

## 14. Persistence

Exercised the real `AuthorityEvaluationRecordStore` against `tmp_path`
(never mocked): exclusive-create semantics, safe duplicate handling,
conflicting-duplicate rejection, and — critically — the pointer-write
failure/recovery cycle described in §17 below, all against a genuine
filesystem, not an in-memory fake.

## 15. Canonical Pointer

Confirmed pointer-digest tamper detection and "pointer references a
nonexistent AER" detection (constructing a validly-digested pointer payload
that names a nonexistent `evaluation_id`) both fail closed via
`CanonicalPointerCorruptError`. **One gap was found and is not currently
caught**: see Finding AESIC-N-01 in §29 — a pointer file's own embedded
`package_id` field is never checked against the query key
(`store.read_canonical(package_id)`'s own argument), so a pointer file
relocated to a different package's `pointers/<package_id>.json` path, while
keeping internally-consistent content naming a *different* package, resolves
successfully and returns the wrong package's AER as canonical, with no
exception raised.

## 16. Supersession

Built independent 3-generation histories (ELIGIBLE → INELIGIBLE → ELIGIBLE
again, the third generation's content byte-identical to the first's):
confirmed all three AERs remain individually retrievable, the pointer
advances at each step, and — the more subtle case — confirmed the
third generation, despite having content identical to the first, is compared
only against the *current* (second) AER, so it correctly creates a fourth,
genuinely distinct record rather than "reviving" the first. Confirmed an
older-generation retry after a newer supersession cannot roll back the
pointer: it always creates a new forward record, never restores an earlier
`record_id`.

## 17. Recovery

Independently reproduced the post-AER/pre-pointer crash scenario against
real storage by monkeypatching `AuthorityEvaluationRecordStore.write_pointer`
to raise `OSError` exactly once, confirming: `CanonicalPointerUpdateFailedError`
is raised; the AER is durably present (`list_evaluation_ids` shows it); the
canonical pointer remains absent (no dangling/partial pointer); a **fresh
service instance** (new `AuthorityEvaluationRecordStore`/`AuthorityEvaluationService`,
simulating a real process restart) retried successfully and established a
correct canonical pointer; repeated retries after the pointer exists are
idempotent (no further growth). One nuance is documented as Informational
Finding AESIC-N-02 (§29): recovery does not literally "rediscover" the
orphaned pre-crash AER by its own compound key — it produces a second,
content-equivalent AER, because idempotency dedup is keyed off the
*canonical pointer*, not a compound-key history scan. The final state is
still correct and auditable.

## 18. Concurrency

Ran real `threading.Thread`-based concurrent invocations (not
single-threaded simulation) against a shared, real filesystem store: 8
threads issuing equivalent Stage 2 calls converge to exactly one valid
canonical pointer referencing one of the actually-produced AERs, with zero
exceptions and zero corruption. A second test raced genuinely different
content (alternating identities across 8 threads) and confirmed the
canonical pointer always resolves to a real, valid, produced AER —
consistent with the contract's own disclosed last-write-wins concurrency
model (AESIC-REQ-120), never a corrupt or dangling state.

## 19. Replay and Restart

Restart equivalence was independently confirmed at three points: (a) after
Registry evolution with a fresh Registry instance (§8), (b) after a
pointer-write crash with a fully fresh service/store instance (§17), and (c)
plain idempotent retry across fresh instances. All three converged to
correct, single-valued canonical state.

## 20. Workflow Integration

Confirmed `SessionApplicationService.__init__`'s `authority_evaluation_service`
parameter defaults to `None`, and that `evaluate_authority_stage_1` returns
`None` (no exception, no attribute error) when unconfigured — preserving
legacy behavior. Confirmed via source read that Stage 2 in
`construct_readiness_package` runs strictly outside
`PublicationCoordinator`'s own `execute()` transaction (no coordinator
import exists at all, §5).

## 21. Readiness Integration

`PublicationReadinessPackage.__post_init__` enforces (verified with real
construction attempts, not just reading the assertion): `citation_text`
required whenever `authority_evaluation_ref` is present, forbidden when
absent, and `authority_evaluation_ref` must carry at least `record_id`/
`record_digest`/`record_family` (an incomplete ref is rejected). Confirmed
the absent-pair case remains fully backward-compatible (pre-existing 147M
test, re-confirmed in combination).

## 22. Publication Boundary

Confirmed by full-source substring search (not just import-statement
parsing) that `coordinator.py` contains no reference to `AuthorityEvaluationService`
or `EvaluationResult` anywhere, confirming Stage 2 branching cannot occur
inside Publication's own authorization/idempotency logic.

## 23. CHGR Integration

Built a real `PublicationReadinessPackage` → `build_publication_record()`
pipeline (not a mock) with a genuinely ELIGIBLE Stage 2 AER: confirmed
`human_governance_record["authority_basis_claimed"]` equals exactly the
AER's own `citation_text`, and confirmed the AER's `record_id` and the
literal string `"evaluation_result"` never appear anywhere in the serialized
CHGR body — the full AER is never embedded. Confirmed the absent-evaluation
case discloses a `limitations` entry naming `authority_basis_claimed`
explicitly, rather than silently omitting it without explanation.

## 24. Disclosure-Only and Non-Gating Verification

Confirmed an INELIGIBLE Stage 2 outcome does not prevent constructing a
(citation-less) `PublicationReadinessPackage` — no exception, no gate.
Confirmed by source-text search that `coordinator.py` never imports
`EvaluationResult` for branching. No code path was found anywhere in the
touched surfaces where an evaluation outcome affects confirmation,
readiness, authorization, or publication eligibility.

## 25. Security

See §29 for the one newly-discovered Major finding (AESIC-N-01, pointer
cross-key confusion) and the security-relevant tests in
`TestCanonicalPointerIntegrity`, `TestCompoundKey` (path-traversal `package_id`
neutralization — confirmed the store never escapes its own root even when
handed `"../../etc/pwned"` as a `package_id`), and `TestAesOwnership`
(forged Stage 1 evidence injection, cross-session Stage 1 injection).

## 26. Diagnostics and Audit

Confirmed `summarize_package` never raises even when the underlying pointer
is corrupt (returns `canonical_pointer_ok=False` instead) — genuinely
read-only, fail-safe, never a control surface. Confirmed by name-pattern
inspection that no function exported from `aesic.diagnostics` contains
`write`/`delete`/`persist`/`create`/`evaluate` in its name.

## 27. Architecture Policy

The `aesic` zone and its edges (`interactive_workflow -> aesic`,
`aesic -> authority_evaluation`, `aesic -> interactive_workflow` [via the
`Session` type import], `aesic -> governance` [via `compute_record_digest`
reuse]) were independently confirmed necessary and non-cyclic by the same
static import-graph analysis in §5: `authority_evaluation` never imports
`aesic` back (no cycle), `interactive_workflow` (outside
`session_service.py`) never imports `aesic` (no undocumented cross-zone
dependency), and `governance/publication/coordinator.py` never imports
`aesic` (the `aesic -> governance` edge is one-directional, `aesic` reusing
a `governance.publication.record` utility function, never the reverse).

## 28. Phase 147M Observation Review

Phase 147M's implementation report was read only after the above
independent work (§2). Its own disclosed non-blocking observations were
reproduced and assessed:

- **Last-write-wins pointer concurrency (AESIC-REQ-120, disclosed)**:
  reproduced independently in §18/`TestConcurrency`; confirmed the disclosed
  behavior is accurate and does not corrupt state.
- **Second AER on pointer-write-failure retry**: this phase independently
  rediscovered and characterized this same behavior (Informational Finding
  AESIC-N-02, §29) with a real crash-injection test, arriving at the same
  practical conclusion (correct final state, surplus history) via
  independent reproduction rather than trusting the report's own framing.

No additional undisclosed limitation matching Phase 147M's own report
categories was found beyond AESIC-N-01 and AESIC-N-02 (§29), both newly
discovered during this phase's own independent search.

## 29. Findings

### AESIC-N-01 — Canonical pointer read path does not validate embedded `package_id` against the query key

- **Severity:** Major
- **Affected requirements:** AESIC-REQ-119 (item 2), AESIC-REQ-126,
  AESIC-REQ-127 (fail-closed pointer integrity)
- **Reproduction:** `tests/test_phase_147n_authority_evaluation_integration_independent_verification.py::TestCanonicalPointerIntegrity::test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected`.
  A legitimate, self-consistent, correctly-digested pointer payload for
  `pkg-A` is written to `pointers/pkg-B.json` (its filename/location
  disagrees with its own content's `package_id` field). Calling
  `AuthorityEvaluationRecordStore.read_canonical("pkg-B")` returns package
  A's AER without raising.
- **Root cause:** `read_canonical(package_id)` in `src/pcae/aesic/storage.py`
  reads the pointer file located at the query key's path, then uses the
  pointer *content's own* `package_id` field (not the query argument) to
  locate the referenced AER, and verifies the AER's own `record_id` and
  digest against the pointer — but never checks that the pointer's own
  `package_id` field agrees with the `package_id` argument the caller
  supplied (equivalently: with the pointer file's own storage location).
  `read_record` has the same gap: it never checks the payload's embedded
  `package_id` against the `(package_id, evaluation_id)` arguments used to
  compute its storage path.
- **Expected behavior (per AESIC-001 §18):** "wrong compound key" pointer
  substitution must be rejected; "No corrupted pointer may silently
  resolve."
- **Actual behavior:** silently resolves to the wrong package's AER.
- **Impact:** Requires filesystem write access to the AER pointer/record
  store to exploit — this is **not** reachable through AES's own public API
  or its normal `evaluate_stage_2` write path (which always constructs
  `pointer.package_id == package_id`, the argument it was given, by
  construction). It is a defense-in-depth / fail-closed gap in the *read*
  path against filesystem-level tampering or corruption of the pointer
  store, not a live exploit through the AES public interface. Notably, this
  is an inconsistency with the codebase's own established pattern:
  `FilesystemAuthorityRegistry.resolve()` (`registry_filesystem.py`)
  explicitly checks embedded identity against the requested identity and
  raises `AuthorityRegistryCorruptError` on disagreement — the AER
  store does not apply the equivalent discipline.
- **Repair boundary:** Small, localized. Add an embedded-`package_id`
  consistency check to `read_canonical`/`read_record`
  (raise `CanonicalPointerCorruptError`/`AuthorityEvaluationRecordCorruptError`
  on disagreement), mirroring `registry_filesystem.py`'s own precedent.
  Does not require a schema or contract change.
- **Recommended disposition:** Repair in a small, bounded follow-up phase
  before or alongside 147O; does not block 147O's own readiness assessment
  from proceeding in parallel, since the gap is not reachable through AES's
  own public interface.

### AESIC-N-02 — Post-crash retry produces a second, content-equivalent AER rather than reusing the orphaned pre-crash record

- **Severity:** Informational
- **Affected requirements:** AESIC-REQ-023, AESIC-REQ-130
- **Reproduction:** `TestCrashRecovery::test_recovery_creates_a_second_distinct_aer_rather_than_rediscovering_the_orphan`.
- **Expected/actual behavior:** The final state is correct in every
  respect this phase could observe: exactly one valid canonical pointer,
  no data loss, the pre-crash orphan remains durably auditable. The only
  divergence from a literal reading of "committed AER is rediscovered" is
  mechanical: because `evaluation_id` is a fresh UUID per invocation and
  idempotency dedup is keyed against the *canonical pointer* (never
  present after this specific crash) rather than a compound-key history
  scan, the retry cannot literally recognize the orphan as "the same
  evaluation" — it produces a second, content-equivalent AER and a fresh
  pointer instead of literally reusing the orphan's own `evaluation_id`.
- **Impact:** None observed on correctness, auditability, or integrity.
  Purely a documentation/terminology precision matter for future spec
  language ("rediscovered" vs. "superseded by an equivalent new record").
- **Repair boundary:** None required; disposition is documentation-only if
  ever revisited.
- **Recommended disposition:** No action required for 147O.

No Blocking finding was identified.

## 30. Overall Verdict

**AUTHORITY EVALUATION INTEGRATION VERIFIED WITH NON-BLOCKING FINDINGS.**

All AESIC-001 v1.3 requirements were independently accounted for (§4). AES
ownership, evaluator purity, Stage 1 advisory semantics, Stage 2 freshness
and supersession correctness, Stage 1 evidence retention through
idempotency, AER immutability, post-AER/pre-pointer recovery, concurrency
and replay safety, and the workflow/readiness/publication/CHGR boundaries
were all independently demonstrated against real persistence and real
concurrency, not accepted from Phase 147M's own report. Disclosure-only and
non-gating guarantees were independently demonstrated. No runtime-capability
expansion was observed. One Major finding (AESIC-N-01) was newly discovered;
it is a defense-in-depth gap requiring filesystem-level tampering to
exploit, not reachable through AES's own public interface, and does not by
itself compromise the integration's correctness under its own normal
operating conditions — it is Major (a real, repairable defect in a required
integrity check per AESIC-001 §18) rather than Blocking (which would require
it to prevent safe or correct integration under normal, in-contract
operation).

## 31. Recommended Next Phase

Recommend **147O — Authority Evaluation Integration Operational Readiness
and Chapter Certification**, per this phase's own authorizing spec §39,
proceeding in parallel with (or immediately preceded by) a small, bounded
repair phase addressing Finding AESIC-N-01 (adding embedded-`package_id`
consistency checks to `AuthorityEvaluationRecordStore.read_canonical`/
`read_record`, mirroring the existing `FilesystemAuthorityRegistry`
precedent). This recommendation is not itself an authorization to begin
either phase.

---

## 32. Validation Record

- `pcae check` / `pcae health` / `pcae doctor task-memory` / `pcae runtime inspect` / `pcae push check`: re-run after this phase's changes (see task finalization record).
- Pre-existing Authority Evaluation baseline (re-confirmed unchanged):
  `python -m pytest tests/test_phase_147g_authority_evaluation.py tests/test_phase_147h_authority_evaluation_independent_verification.py tests/test_phase_147m_authority_evaluation_integration.py -q` → **242 passed**.
- New Phase 147N suite alone:
  `python -m pytest tests/test_phase_147n_authority_evaluation_integration_independent_verification.py -q` → **64 passed**.
- New suite combined with all three pre-existing Authority Evaluation suites:
  `python -m pytest tests/test_phase_147g_authority_evaluation.py tests/test_phase_147h_authority_evaluation_independent_verification.py tests/test_phase_147m_authority_evaluation_integration.py tests/test_phase_147n_authority_evaluation_integration_independent_verification.py -q` → **306 passed**.
- Full fast-green gate (unchanged from pre-verification baseline; this
  phase's new suite is not a member of `FAST_GREEN_MODULES`, consistent
  with the pre-existing 147G/147H/147M suites):
  `python -m pytest -m fast_green -n auto -q` → **4391 passed**.
- Focused cross-cutting run across publication/handoff/readiness/CHGR/
  architecture-adjacent tests (`-k "publication_handoff or session_service or
  readiness or chgr or architecture"`): **3021 passed, 2 skipped**, plus 6
  pre-existing failures confirmed unrelated to this phase's scope (wheel/
  packaging build tests requiring network/build isolation, and one
  pre-existing stray `src/pcae/advisory/` directory artifact predating this
  phase's work — none touch `src/pcae/aesic` or `src/pcae/authority_evaluation`).

No test was weakened, skipped, or altered to force a pass. No production
code under `src/pcae/**` was modified during this phase.
