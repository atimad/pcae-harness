# Phase 135F — Canonical Transition Record Read-Only Prototype

**Phase class:** Prototype Implementation (Track 135, seventh phase)
**Predecessor:** 135E — Canonical Transition Record Prototype Plan (COMPLETE; verdict A — READY FOR PROTOTYPE IMPLEMENTATION).
**Scope:** Implementation of 135E's Stages 1-6 plan: a fixture-driven generator, a standalone offline verifier, a read-only cross-representation comparator, prototype-only atomic persistence under `.pcae/cltr-prototypes/`, a minimal `pcae cltr-prototype` CLI, 15 fixtures, and a focused test suite.
**Non-goal:** Integrate CLTR into production finalization; modify any production entry point; repair any Track 134/135A/135D-disclosed production gap; begin 135G.

---

## 1. Prototype boundary

The implemented package (`src/pcae/cltr_prototype/`) has zero coupling to production finalization:

- No module in `src/pcae/core/` or `src/pcae/commands/` (other than the new `commands/cltr_prototype.py`) imports anything from `cltr_prototype`.
- No module in `cltr_prototype` imports `finalization_transaction.py`, `canonical_artifact_promotion.py`, any notification sink, `decision_log`, or `repository_intelligence`.
- The only write path in the entire package is `persistence.py`, whose write prefix is a hardcoded module constant: `PROTOTYPE_DIR_NAME = ".pcae/cltr-prototypes"`. No caller can supply a different output path.
- No module executes a shell command, opens a socket, or performs an HTTP call (`tests/test_cltr_prototype_safety.py` verifies this by import-graph inspection across every module in the package).

These are the same structural guarantees 135E §3.5-§3.7 and §25 required, re-verified here (not merely asserted) by `tests/test_cltr_prototype_safety.py`.

## 2. Module structure

| Module | Responsibility |
|---|---|
| `models.py` | Enums (`SpineState`, `OrthogonalFlag`, `TransitionType`, `RetryClassification`, `ConformanceClassification`, `AuthorityRole`, `CommitOwnershipClassification`, `InvariantResultOutcome`, `EvidenceType`, `RepresentationKind`, `FailureClassification`, etc.) and the frozen `TransitionRecord`/`Identity`/`EvidenceRef`/`CommitDeclaration` dataclasses. No I/O. |
| `identity.py` | `resolve_identity()` — explicit-only identity resolution, reusing `PHASE_ID_RE` from `src/pcae/core/architecture_status.py:51` verbatim. Zero title/filename/commit-subject/Git-history code path. |
| `state_machine.py` | One function per named transition (`t1_propose_transition` … `t16_supersede`). No generic `set_state`. |
| `invariants.py` | One evaluator function per invariant ID (37 — see §9 below for the 36-vs-37 discrepancy this resolves honestly). |
| `canonicalization.py` | `canonicalize()`/`record_to_dict()`/`record_from_dict()` — deterministic JSON canonical form and its inverse. |
| `digest.py` | SHA-256 `digest()`, `seal()`, `verify()`, `verify_self()`. |
| `generator.py` | `generate(bundle)` — fixture-driven orchestration: identity resolution → state-machine sequence → commit classification → invariant evaluation → digest sealing. |
| `verifier.py` | `verify_record()`/`verify_record_object()` — standalone re-check: manifest consistency, digest integrity, invariant re-evaluation, conformance classification. |
| `compatibility.py` | `classify_legacy_artifact()` — read-only adapters for legacy/current artifacts; the only module permitted to parse a narrative title, and only for comparison/disclosure. |
| `comparison.py` | `compare()` — read-only cross-representation comparison against an explicit target bundle; mixed-generation detection. |
| `persistence.py` | `persist()`/`read_latest()`/`read_generation()`/`list_generations()` — atomic, prototype-only writes. |
| `commands/cltr_prototype.py` | CLI wiring: `generate`, `show`, `verify`, `compare`, `list`. |

## 3. Data model

`TransitionRecord` is a frozen dataclass carrying: `schema_version`/`contract_version`; `identity` (`transition_id`, `phase_id`, `task_id`, `repository_identity`, `branch_identity`); `source_revision`/`final_revision`(+provisional flag); `prior_state`/`projected_state`/`certified_state`; `spine_state`; `quarantined`/`superseded`/`superseded_by` (orthogonal flags, not spine values — see §4); `declared_commits`/`commit_classifications`; `evidence_refs` plus nine named bindings (`report_binding` … `architecture_status_binding`, each an `EvidenceRef`); `timestamps`; `failure_classification`; `limitations`; `compatibility_metadata`; `record_digest`.

State-dependent required-field validation is enforced structurally rather than by a separate validator pass: `TransitionRecord.__post_init__` raises if a `CERTIFIED`-or-later record lacks `certified_state`, and `state_machine.py`'s transition functions refuse to enter a state without the fields that state requires (e.g. `t3_certify` requires `certified_state`; `t9_notify_confirm` requires `notification_binding`). No production JSON Schema is frozen — this remains prototype-local per 135E §5's explicit deferral.

Transitions never mutate a record in place — every `tN_*` function returns a `TransitionResult{outcome, new_record, transition_type, timestamp}` wrapping a brand-new immutable value (`TransitionRecord.with_updates()`).

## 4. State-machine implementation

All 14 states from 135D §3.3 are represented: `SpineState` (12 members: `PROPOSED`, `CERTIFYING`, `CERTIFIED`, `PROMOTING`, `PROMOTED`, `NOTIFYING`, `NOTIFIED`, `NOTIFIED_UNCONFIRMED`, `TERMINAL_SUCCESS`, `TERMINAL_PARTIAL_EXTERNAL`, `FAILED_PRE_CERT`, `FAILED_POST_CERT`) plus `OrthogonalFlag` (2 members: `QUARANTINED`, `SUPERSEDED`), matching 135D's own modeling that a record can be simultaneously `TERMINAL_SUCCESS` on the spine and flagged `SUPERSEDED`.

All 16 permitted transitions (T1-T16) are implemented as separate, named functions in `state_machine.py`, each checking its own precondition and raising `PreconditionError`/`ForbiddenTransitionError` rather than silently no-opping. There is no `set_state(record, new_state)` function anywhere in the module (verified by `test_no_generic_set_state_function_exists`).

All 14 forbidden transitions (F1-F14) are exercised by `tests/test_cltr_prototype_state_machine.py` — each attempted via the one state-machine function whose precondition it violates (e.g. F1/F12 via `t5_begin_promotion` called against a `PROPOSED` record), and each raises `ForbiddenTransitionError` carrying the matched forbidden-transition ID(s).

Terminal states (`TERMINAL_SUCCESS`, `TERMINAL_PARTIAL_EXTERNAL`, `FAILED_PRE_CERT`, `FAILED_POST_CERT`) reject ordinary replay (F7/F14); the two orthogonal transitions (`t15_quarantine`, `t16_supersede`) remain available on a terminal record without consuming the spine position. Exact replay is deterministic (`generate()` over identical inputs yields byte-identical digests — `test_generate_deterministic_same_input_same_digest`); conflicting replay is rejected at the persistence layer (`persistence.persist()` raises `ImmutableGenerationExistsError` for a different-content generation with the same `transition_id` — `test_persist_conflicting_replay_rejected`).

`NOTIFIED_UNCONFIRMED` follows CLTR-001/135D exactly: `t10_notify_unconfirmed` is the only entry, `t12_reconcile_receipt` is a constrained self-loop (never re-dispatches), and `t14_close_partial` is its only exit, to `TERMINAL_PARTIAL_EXTERNAL`. `retry_classification()` returns `REPAIR_DERIVATIVE_ONLY` for this state — the resume-terminal classification CLTR-RETRY-1 requires.

The retry/resume table (135D §24) is implemented as a pure lookup (`_RETRY_TABLE` in `state_machine.py`), not ad hoc logic, with `QUARANTINED`/`SUPERSEDED` flags overriding the table to `REQUIRE_HUMAN_REVIEW`/`REJECT_SUPERSEDED_REDIRECT` respectively.

State-machine transition functions perform **no lifecycle side effects** — they return a proposed/evaluated record value only; `persistence.py` is the only module that writes anything.

## 5. Invariant engine

`invariants.py` implements one evaluator per invariant ID named in 135D §11's table. **135D §11's own table names 37 distinct IDs** (2 ID + 2 AUTH + 4 STATE + 7 ORDER + 2 DERIVE + 3 COMMIT + 1 EVID + 3 PERSIST + 3 RETRY + 2 NOTIFY + 2 MARKER + 1 RECEIPT + 2 COMPAT + 3 SAFE = 37), even though 135D §11.1's own prose states "36 (33 original + 3 closure entries)". This prototype implements an evaluator for every ID that actually appears as a row in the table (37) rather than silently dropping one to force-fit the prose count. **This is a pre-existing arithmetic inconsistency in the frozen 135D source**, not something 135F invents or resolves; `INVARIANT_COUNT = 37` is asserted by test and documented here per the task's instruction to classify (not silently absorb) a gap of this kind.

Every evaluator:
- first checks lifecycle applicability against the record's current `spine_state` (per 135D §11's "States" column), returning `inapplicable` — never `pass` — when the invariant does not yet apply;
- when applicable but the necessary external evaluation input (a `comparison_bundle`) was not supplied, also returns `inapplicable` with an explicit detail string naming what was missing — this is a **documented interpretation**, not an invented policy choice: 135E §10 specifies the three-way `pass|fail|inapplicable` outcome shape but does not specify which of the three applies when an invariant is applicable-in-principle but unevaluable for lack of external data. This prototype resolves that gap by treating "applicable but unevaluable" as `inapplicable`-with-disclosed-reason, since `fail` would misrepresent an actual violation and silent `pass` is explicitly forbidden by 135E §10 ("do not automatically convert missing evidence into pass");
- returns a full `InvariantResult{invariant_id, category, outcome, severity, detail, evidence_used, failure_reason, conformance_effect, retry_effect, quarantine_recommendation}`.

`evaluate_invariants()` always returns exactly `INVARIANT_COUNT` (37) results, in a fixed order — `test_evaluate_invariants_returns_37_results_always` and `test_no_applicable_invariant_silently_skipped_proposed_state` assert this holds even for a minimal `PROPOSED`-only record. All severities are `"Blocking"`, surfaced as data per 135E §10 (the engine does not itself act on severity — e.g. it never auto-quarantines).

Many invariants (`CLTR-ID-1/2`, `CLTR-MARKER-1`, `CLTR-ORDER-6/7`, `CLTR-PERSIST-2`) are fully self-contained — evaluable from the record's own bound `EvidenceRef` objects (each of which carries its own `transition_id`/`phase_id`) without requiring an external comparison bundle at all. Others (`CLTR-STATE-1/2`, `CLTR-PERSIST-1/3`, `CLTR-COMMIT-1`, `CLTR-DERIVE-1/2`, `CLTR-COMPAT-1/2`, `CLTR-SAFE-1/3`) genuinely require external context (an Architecture Status projection, a latest-pointer bundle, two independent regenerations, etc.) and report `inapplicable` honestly when it is not supplied.

## 6. Authority-role enforcement

The S/R/D/E/V model (CLTR-001 §3.1) is enforced structurally, not by runtime checks:

- **S (sole)**: only `TransitionRecord` carries spine-authority fields; it is a frozen dataclass, and no derivative module (`comparison.py`, `compatibility.py`, `verifier.py`) has a code path that constructs one — they only ever *consume* an existing record.
- **R (reference)**: `EvidenceRef` never embeds copied content — only identity, digest, source path/revision, and an honest `verification_status`/`limitation`.
- **D (derivative)**: `comparison.py`/`compatibility.py` take a `TransitionRecord` or artifact path as read-only input and produce a separate result value; nothing feeds back into `generator.py`.
- **E (immutable event)**: bindings such as `notification_binding`/`receipt_binding` are set once, at the transition that creates them, never edited in place (immutability is structural via frozen dataclasses).
- **V (verification-only)**: `verifier.py` always re-measures (recomputes the digest, re-evaluates invariants) rather than trusting a cached prior verification result.

`evaluate_cltr_auth_1`/`evaluate_cltr_marker_2`/`evaluate_cltr_safe_2` are **structural** evaluators — they assert the code-shape property directly (e.g. "no marker-presence-based terminal-state code path exists in this module") rather than checking record content, since these are design-time guarantees the engine re-confirms rather than facts the engine computes.

## 7. Commit-ownership model

`generator.classify_commits()` implements the frozen three-outcome model literally: every declared commit is classified `verified`/`contaminated`/`unverifiable` from an **explicit** caller-supplied hint dict; a declared commit with **no** hint is classified `unverifiable` by default — never silently `verified` (the exact CLTR-COMMIT-3 requirement, and the direct prototype-level rehearsal of avoiding today's production `phase_reports.py` silent-`continue` gap, which is not touched or repaired here). Fixtures cover: zero commits (`pre_certification_failure.json`), one verified commit (`successful_transition.json`), a fabricated/unhinted hash (`fabricated_commit_hash.json`), an explicit `contaminated` hint (`contaminated_commit_ownership.json`), and an explicit `unverifiable` hint (`unverifiable_ownership.json`, kept distinct from the fabricated-hash fixture per 135E §17's own instruction, so the fixture set has an explicit example of the *classification path*, not only the *default-to-unverifiable path*).

The generator makes **no policy decision** about whether `unverifiable`/`contaminated` blocks certification — this remains explicitly deferred by CLTR-001 §10.4 and 135D §17.1, and the prototype only surfaces the classification as data on the record.

## 8. Evidence references

`EvidenceRef` carries `evidence_id`, `evidence_type`, `transition_id`, `phase_id`, `verification_status` (`bound`/`unavailable`/`stale`/`unavailable_structured`), plus optional `source_path`, `digest`, `source_revision`, `observation_timestamp`, `limitation`. No report prose is ever treated as sole evidence for an R/E-role fact: `compatibility.py`'s narrative adapter explicitly tags narrative-only findings `identity_confidence: narrative_parsed_comparison_only`, never `explicit_declared`.

## 9. Canonicalization and digest

`canonicalization.record_to_dict()` produces a plain dict with: keys sorted lexicographically at every level (via `json.dumps(..., sort_keys=True)`); compact separators; UTF-8; enum values emitted as their exact string identifiers; fields not yet reached (e.g. `promotion_binding` before `PROMOTED`) omitted entirely rather than emitted as `null`; an explicitly-declared empty list (`declared_commits: []`) retained, not omitted; string collections sorted for output determinism (never claimed as semantic ordering).

`digest.digest()` computes SHA-256 over the canonicalized form with `record_digest` itself excluded from its own input (self-exclusion). `digest.seal()` is idempotent (`test_digest_excludes_itself_from_input`: sealing an already-sealed record twice produces the same digest). `verify_self()` recomputes independently and compares byte-for-byte; any single-field mutation changes the digest (`test_digest_changes_on_mutation`), and cross-transition substitution (a different `transition_id`'s record) never collides (`test_cross_transition_substitution_changes_digest`).

`canonicalization.record_from_dict()` is the exact inverse, used by `verifier.py` and the CLI to reconstruct a `TransitionRecord` from persisted JSON for independent re-verification — round-trip fidelity (including digest match) is tested directly.

## 10. Generator

`generator.generate(bundle)` consumes an explicit fixture bundle dict (`schema_version`, `contract_version`, `identity`, `source_revision`, optional `declared_commits`/`commit_classifications`/`evidence_refs`, and an ordered `steps` list naming one of the 16 transition types plus its kwargs per step). It: resolves identity via `identity.resolve_identity()`; classifies commits; executes the step sequence against `state_machine.py`'s functions; seals the digest once `certified_state` exists; evaluates all 37 invariants. It raises `MissingInputAuthorityError`/`UnsupportedStateError`/`UnsupportedSchemaVersionError`/`UnsupportedContractVersionError` for structurally invalid input, never partially constructs a record. It performs no filesystem read, no directory scan, no subprocess call (`generator.py` imports neither `os` nor `subprocess` — verified by `test_generate_never_reads_live_repository_state`).

## 11. Verifier

`verifier.verify_record(transition_id)` reads only `.pcae/cltr-prototypes/generations/<transition_id>/`, checks manifest-file-digest consistency first, reconstructs the record via `record_from_dict()`, independently recomputes the digest, re-evaluates all 37 invariants, and classifies conformance (`classify_conformance()`) into one of the seven 135E §23 values. It never repairs — `test_tampered_record_fails_verification` confirms a byte-level mutation to a persisted `record.json` is caught as both `manifest_consistent=False` and `digest_valid=False`, and the record itself is left untouched on disk.

## 12. Comparator

`comparison.compare(record, targets)` accepts a dict of `{RepresentationKind.value: path-or-inline-dict}`. File-backed targets (`canonical_report`, `completion_metadata`, `checkpoint`, `marker`, `receipt`, `promoted_report`, `promoted_metadata`) are read via `compatibility.classify_legacy_artifact()`; inline dict targets (e.g. a fixture-supplied notification payload) are compared directly against the record's own identity. Mixed-generation detection: if any two targets in the same comparison call disclose different `transition_id`s, `mixed_generation_detected=True` is set on the `ComparisonReport` (`test_mixed_derivative_generation_detected`). `compare()` never writes to any target (`test_comparison_never_writes_to_targets`).

## 13. Persistence

Layout exactly as 135E §15 specifies:

```
.pcae/cltr-prototypes/
  generations/<transition-id>/{record.json,verification.json,manifest.json}
  latest.json   # {"<phase_id>": {"transition_id","digest","written_at"}}
```

Writes use `tempfile.mkstemp()` in the target directory, `os.fsync()`, then `os.replace()` — the same atomic pattern used elsewhere in this repository. A re-run for the same `transition_id` with identical content no-ops (idempotent); different content for the same `transition_id` raises `ImmutableGenerationExistsError` (never silently overwritten). `read_latest()` first trusts `latest.json`, then falls back to scanning `generations/` for the most recent manifest-consistent generation belonging to the requested `phase_id` if the pointer is missing, corrupt, or points at an incomplete generation (`test_stale_pointer_recovers_from_history`, `test_missing_pointer_recovers_from_history`). A prior generation's bytes are never touched by a later `persist()` call for a different `transition_id` (`test_prior_generation_unchanged_after_new_generation`). No production path (`.pcae/canonical-reports/`, `.pcae/phase-completion-metadata.json`, `.pcae/finalization-transactions/`, `.pcae/delivery-receipts/`, `.pcae/phase-completion-report.md`) is ever written — `test_no_production_paths_touched` and `test_full_run_touches_no_production_artifact` assert this directly.

## 14. CLI

```
pcae cltr-prototype generate --input <fixture.json> [--json]
pcae cltr-prototype show --record <transition_id> [--json]
pcae cltr-prototype verify --record <transition_id> [--json]
pcae cltr-prototype compare --record <transition_id> --against <targets.json> [--json]
pcae cltr-prototype list [--json]
```

No `repair`, `promote`, `complete`, `notify`, `commit`, or `push` subcommand exists — this is a structural fact of the argparse wiring in `commands/cltr_prototype.py` (`test_cli_has_no_repair_promote_complete_notify_commands` enumerates the exact five-command set). Every text-mode response prints an explicit boundary disclosure block first: "PROTOTYPE ONLY … NOT a canonical phase report, NOT an authorization to proceed, and does not mutate any production lifecycle artifact." JSON output additionally carries `prototype_only: true, canonical: false, authorization: false` on every payload. `generate`/`verify`/`compare` return exit code `2` (not `0`) when an invariant fails, a digest is invalid, or a mixed-generation conflict is detected — `0` is reserved for a genuinely clean result, distinct from the `1` used for a malformed invocation.

## 15. Fixture inventory

15 scenario fixtures under `tests/fixtures/cltr_prototype/` (plus 2 companion artifacts consumed by them):

| # | File | Scenario |
|---|---|---|
| 1 | `successful_transition.json` | Full spine, `PROPOSED→TERMINAL_SUCCESS` |
| 2 | `pre_certification_failure.json` | `CERTIFYING→FAILED_PRE_CERT` |
| 3 | `promoted_notification_uncertainty.json` | `PROMOTED→NOTIFYING→NOTIFIED_UNCONFIRMED→TERMINAL_PARTIAL_EXTERNAL` |
| 4 | `exact_replay.json` | Identical content to #1, exercises idempotent re-persist |
| 5 | `conflicting_replay.json` | Same `transition_id` as #1, different evidence — must be rejected |
| 6 | `identity_mismatch.json` | Declared vs. embedded-artifact identity disagreement |
| 7 | `stale_report.json` + `stale_report.md` | Narrative report predating the declared transition (135D.1 rehearsal) |
| 8 | `mixed_derivative_generations.json` | Report/metadata targets belonging to two different `transition_id`s |
| 9 | `fabricated_commit_hash.json` | No classification hint → default-to-`unverifiable` path |
| 10 | `contaminated_commit_ownership.json` | Explicit `contaminated` hint |
| 11 | `unverifiable_ownership.json` | Explicit `unverifiable` hint (distinct from #9's default path) |
| 12 | `tampered_record.json` | Persisted then byte-mutated, for digest-tamper detection |
| 13 | `stale_pointer.json` | Corrupt `latest.json` entry, recovery-from-history |
| 14 | `superseded_transition.json` | Original + corrective transition pairing |
| 15 | `legacy_artifact_no_transition_id.json` + `legacy_metadata_no_transition_id.json` | Track-134-style artifact with no `transition_id` |

Every fixture is hermetic (no live-repository dependency) and fixes its own timestamps literally (never `datetime.now()`), per 135E §7/§17.

## 16. 135D.1 incident protections

- `identity.py` has zero title/filename/commit-subject parsing code (`test_identity_module_has_no_title_parsing_code_path`, an AST-based check of the module's *executable* statements, excluding its own descriptive docstrings).
- `compatibility.py` is the **only** module permitted to parse a narrative title, and only for disclosure/comparison — its output is tagged `identity_confidence: narrative_parsed_comparison_only`, never fed into `generator.py`.
- A declared-vs-embedded identity disagreement (`identity.check_identity_conflict()`) and a declared-vs-artifact disagreement (`compatibility.classify_legacy_artifact(..., declared_identity=...)`) both produce a **conflict result**, never a silent repair in either direction — this prototype has no repair module at all.
- `comparison.compare()` never mutates either side of a comparison (`test_comparison_never_writes_to_targets`, `test_never_mutates_source_artifact`).

## 17. Architecture Status grouping observation (item 20)

Inspection confirms the currently-generated Architecture Status still shows "Whole-Lifecycle Independent Verification (135A–135D, 4 phases)" for the completed portion of Track 135, even though 135E (and now 135F) are complete. Classification:

- This is **stale chapter-level presentation only** — a grouping label produced by `architecture_status.py`'s rendering of completed-phase ranges, not a field this prototype reads or writes.
- It does **not** affect prototype input selection: `generator.py` accepts only explicit fixture-bundle identity, never Architecture Status text of any kind.
- It **could** be mistaken for identity authority by a human reader, but not by any code path in this package — `identity.py` has no Architecture Status read at all, and `compatibility.py`'s Architecture Status adapter (where implemented via the `architecture_status_binding`/`ARCHITECTURE_STATUS` representation kind) is explicitly comparison-only.
- It belongs to a later, dedicated Architecture Status grouping-repair phase, not 135F. No repair was attempted here, consistent with the task's explicit instruction not to let this presentation issue expand 135F's scope.

## 18. Compatibility behavior

`compatibility.classify_legacy_artifact()` returns `conformant_with_legacy_adapter` when the only missing field is `transition_id` (the expected shape of every pre-135 artifact), `incomplete` for other missing structured fields, `conflicting` when a declared identity disagrees with the artifact's own disclosed identity (structured or narrative), and `unverifiable` when the artifact path does not exist or cannot be parsed. `missing_fields` is always disclosed explicitly; nothing is invented to fill a gap (`test_legacy_artifact_never_invents_transition_id`).

## 19. Safety boundaries

`tests/test_cltr_prototype_safety.py` (30 tests) independently re-derives, rather than trusts, every structural claim above:

- no module imports `subprocess`, `socket`, `requests`, `httpx`, or `urllib`;
- no module imports `finalization_transaction`/`canonical_artifact_promotion`;
- production `finalization_transaction.py` does not import `cltr_prototype`;
- no module imports a Telegram/notification-sink/notification-config module;
- no module imports `decision_log`/`decision_evaluation`;
- no module imports `repository_intelligence`;
- no module other than `persistence.py` contains a file-write indicator (`open(`, `.write_text(`, `.write_bytes(`, `os.replace`, `mkstemp`, `NamedTemporaryFile`);
- `persistence.PROTOTYPE_DIR_NAME` is the hardcoded literal `.pcae/cltr-prototypes`;
- a full generate-and-persist run creates no path matching any production-artifact name fragment;
- no module defines an `may_execute`/`authorize_execution` name.

## 20. Known limitations

- Several invariants (`CLTR-STATE-1/2`, `CLTR-PERSIST-1/3`, `CLTR-COMMIT-1`, `CLTR-DERIVE-1/2`, `CLTR-COMPAT-1/2`, `CLTR-SAFE-1/3`) require an explicit `comparison_bundle` to evaluate past `inapplicable`; the prototype does not synthesize this bundle from a live repository scan (by design — 135E §3.7 forbids default "scan the repo" behavior), so exercising these invariants past `inapplicable` requires a caller (test or future integration-fixture mode) to supply the bundle explicitly.
- Branch-reachability / rewritten-history detection for commit-ownership verification remains unimplemented, exactly as 135D §12.1 #1 classifies it (implementation-level refinement of the existing three-outcome taxonomy, not a contract gap) — `classify_commits()` never claims to detect this and always falls back to `unverifiable` for anything it cannot resolve from an explicit hint.
- The 36-vs-37 invariant-count discrepancy in 135D's own text (§5 above) is documented, not resolved — this prototype implements evaluators for all 37 IDs the 135D table actually names.
- Integration-fixture mode (135E §3.2/§17: reconstructing a candidate record from named, real, already-committed repository artifacts) is not implemented in this phase; only the fixture-driven generator and the file-backed comparison targets (which do read real, explicitly-named files) are implemented. This is a scope reduction consistent with "smallest coherent prototype," not a silently dropped requirement — 135E §3.1 frames the integration-fixture mode as supporting comparison/compatibility testing (which is implemented), not as a second generation pathway required for the acceptance criteria in 135E §28.

## 21. Deferred integration work

Unchanged from 135E §20/§32: no integration into `finalization_transaction.py`, no legacy-authority retirement, no production schema freeze. The recommended next phase remains **135G — Canonical Transition Record Prototype Independent Verification**, per 135E §32's staged sequence.
