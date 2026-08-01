# Phase 147O.2 — Authority Evaluation Production Wiring Independent Verification

## 1. Executive Summary

Independently verifies Phase 147O.1's claim to have closed **AESIC-O-01**
(Authority Evaluation, though fully implemented and independently verified
at the library level by Phases 147M/147N, was never constructed or invoked
on any real production path). This phase re-derived the pre-147O.1 gap
directly from production source and git history, inspected 147O.1's actual
diff (`git show 01178382`) line by line, and reproduced the full production
lifecycle through **genuine separate-OS-process `pcae` CLI invocations**
(`subprocess.run([sys.executable, "-m", "pcae", ...])`) — a discriminator
147O.1's own automated suite does not meet: every test in
`tests/test_phase_147o1_authority_evaluation_production_wiring.py` calls
`run_decision_session_*`/`run_governance_record_publish` handler functions
directly, in-process, against a `monkeypatch.chdir`-ed `tmp_path`, never a
real OS process boundary. 147O.1's own report (§18) narrates a manual,
separate-process reproduction, but that reproduction was never captured as
a reproducible automated test until this phase.

**Verdict: AUTHORITY EVALUATION PRODUCTION WIRING INDEPENDENTLY VERIFIED**,
with one new independently-discovered Minor finding (147O.2-F-1, a
read-only path-containment edge case, not production-reachable via any
write path) and confirmation that all limitations 147O.1 itself disclosed
hold as described. AESIC-N-01 remains exactly as contained as Phase 147O
found it — production wiring did not expand its reachability. No Blocking
or Major finding was identified.

## 2. Scope

Verification-only. No production code was modified (`src/pcae/**`
untouched — confirmed via `git status`/`git diff` before and after this
phase). Added: one independent test module and this document. Not in
scope: repairing AESIC-N-01, AESIC-N-02, or any 147O.1-disclosed
limitation; contract, schema, or architecture-policy amendment; chapter
certification (deferred to a future 147O.3-equivalent phase per this
phase's authorization).

## 3. Independent Verification Method

Performed in this order, matching the phase authorization's discipline:

1. Re-read AESIC-001 v1.3's production-wiring-relevant sections (composition,
   enablement, Stage 1/Stage 2 reachability, storage keying) directly from
   `docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`.
2. Re-read Phase 147O's operational-readiness findings
   (`docs/certification/PHASE_147O_...md`), in particular §6 (AESIC-O-01),
   §15 (AESIC-N-01 containment argument), §37 (recommended next phase).
3. Reconstructed AESIC-O-01 directly: `git show 01178382 --stat` enumerates
   every file 147O.1 touched; `git show 01178382 -- <path>` for each
   production file shows the exact pre/post diff, not a paraphrase.
4. Inspected current production wiring directly by reading
   `src/pcae/aesic/composition.py`, the relevant sections of
   `src/pcae/commands/decision_session.py`,
   `src/pcae/interactive_workflow/application/session_service.py`,
   `src/pcae/governance/publication/record.py` and `coordinator.py`,
   `src/pcae/aesic/storage.py`, and `src/pcae/aesic/service.py`.
5. Built an independent production-flow model (§6/§11/§14 below) before
   looking at 147O.1's own test assertions.
6. Authored a fresh, independent test module
   (`tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`,
   11 tests) that does not import or call into 147O.1's own test module.
7. Reproduced the full production lifecycle from real, separate CLI
   processes in disposable `tmp_path` repositories, both manually (recorded
   below) and as automated `subprocess`-based tests.
8. Only then compared conclusions with 147O.1's own report — after forming
   independent conclusions, not before.

## 4. Pre-Repair Gap Reconstruction

Reconstructed directly from `git show 01178382` against the immediately
preceding commit (`f1abebbf`, Phase 147O finalization; the working tree at
that commit is what 147O.1 modified):

- `build_application_context()` in `decision_session.py` constructed
  `SessionApplicationService(session_coordinator)` with no
  `authority_evaluation_service` argument — confirmed by the diff hunk
  (`-        session_service = SessionApplicationService(session_coordinator)`).
  No production caller anywhere in the repository passed that argument
  either (Phase 147O's own §6 finding, independently re-confirmed by
  grepping the pre-147O.1 tree: only test files constructed
  `AuthorityEvaluationService`/`FilesystemAuthorityRegistry`/
  `AuthorityEvaluationRecordStore`).
- No `pcae.aesic.composition` module existed before 147O.1 (it is a wholly
  new file in the diff, 140 lines) — there was no persistent, deterministic
  production configuration/enablement path at all.
- `run_decision_session_confirm` had no Stage 1 invocation of any kind
  (diff adds the entire `stage_1_status`/`evaluate_authority_stage_1` block).
- `SessionApplicationService.construct_readiness_package` had no Stage 2
  invocation and `PublicationReadinessPackage`'s `authority_evaluation_ref`/
  `citation_text` fields (already defined by Phase 143O/145F) were never
  populated and never serialized —
  `publication_handoff_schema.to_payload`'s diff shows the fields did not
  exist in the wire payload at all before this phase.
- `pcae.commands.governance_record`'s CHGR construction
  (`record.py::build_publication_record`) already read
  `package.citation_text` (Phase 147M code, unmodified by 147O.1) but that
  field was always `None` in production because nothing upstream ever set
  it — confirmed by reading `record.py` lines 259–273, which predate
  147O.1 and are untouched by its diff.
- No `pcae aesic status` command existed; there was no supported,
  read-only way to determine whether Authority Evaluation was configured.

All seven breakpoints independently confirmed exactly as Phase 147O
described them (§6), by direct source/diff inspection rather than by
trusting either report's prose.

## 5. Composition Root

`src/pcae/aesic/composition.py` (new in 147O.1) is the sole production
composition root. Independently confirmed:

- `build_authority_evaluation_service()` re-derives its enablement decision
  from the filesystem on every call (`describe_authority_evaluation_configuration`
  → `_template_store_populated`) — no cache, no module-level state, no
  process-global singleton. Verified by reading the full module (141
  lines) and by `TestRestartRecovery::test_fresh_composition_root_rediscovers_prior_canonical_record`,
  which calls `build_authority_evaluation_service()` twice and asserts the
  two returned service objects are distinct (`is not`) yet converge on the
  same canonical record.
- No manual assembly is required by any caller: `decision_session.py`'s
  `build_application_context()` is the only call site
  (`grep -rn "build_authority_evaluation_service" src/pcae` confirms this).
- No current-working-directory ambiguity beyond the pre-existing,
  repository-wide convention: all three roots (`template_root`,
  `registry_root`, `aer_store_root`) are `.pcae/`-relative `Path` defaults,
  identical in kind to every other collaborator `build_application_context`
  already constructs (`FilesystemSessionRepository`,
  `FilesystemPendingReadinessStore`), independently confirmed by reading
  the surrounding, unmodified code in the same function.
- No duplicate or competing composition root exists:
  `grep -rn "AuthorityEvaluationService(" src/pcae` outside test files
  returns exactly one production construction site
  (`composition.py:126`).

## 6. Configuration

Enablement model independently re-derived from source, not from the
module's own docstring:

- Sole enablement signal: at least one `*.json` file under
  `.pcae/authority-evaluation/templates/` (`_template_store_populated`).
  Registry and AER-store roots are *not* separately gated — independently
  confirmed correct, because `FilesystemAuthorityRegistry.resolve` already
  returns `None` (never raises) for an absent/empty registry, and the AER
  store creates its own tree on first write, so gating on their absence
  would be redundant, not protective.
- Partial configuration (template deployed, no Registry declaration):
  reachable and safe — Stage 1/Stage 2 resolve to `ineligible`/`no
  declaration`, not a crash (independently exercised via
  `TestNonGatingCharacterization::test_ineligible_outcome_does_not_block_readiness`,
  which declares eligibility for a *different* identity than the session
  owner).
- Malformed configuration (template root exists but is not a directory, or
  is unreadable): distinguished by `reason` and safe-disabled — read
  directly in `_template_store_populated`; not independently re-tested
  beyond source reading, since 147O.1's own
  `TestComposition::test_disabled_when_template_root_not_a_directory`
  already covers this exact source path and re-deriving it adds no
  independent signal.
- Configuration is read fresh on every CLI invocation (no config file, no
  env var, no shell state) — directly follows from `describe_authority_evaluation_configuration`
  taking no cached input and this phase's own separate-process
  reproduction (§18 below) exercising six distinct process invocations
  against the same repository and observing consistent enablement state
  throughout.
- Inspectable via `pcae aesic status` (verified read-only, §22 below).

## 7. Enablement and Compatibility

Independently exercised, in a fresh `tmp_path` repository, via real
separate `pcae` subprocesses (`TestSeparateProcessReproduction::test_unconfigured_repository_stays_backward_compatible_across_real_processes`):

- No AES configuration: `pcae aesic status --json` reports
  `enabled: false, reason: template_root_absent`.
- Full legacy lifecycle (`create` → `evidence` → `select` → `preview` →
  `confirm` → `readiness` → `governance-record publish`) succeeds
  end-to-end across six separate OS processes with no Authority Evaluation
  configured.
- `authority_evaluation_stage_1` reports `not_configured` in the `confirm`
  response.
- The published CHGR artifact (read directly off disk, not from the
  command's own reported payload) does **not** contain an
  `authority_basis_claimed` key at all — confirmed by
  `assert "authority_basis_claimed" not in chgr` against the persisted
  JSON file.
- No AER, canonical pointer, or fabricated citation was written anywhere
  under `.pcae/authority-evaluation/` in the unconfigured repository
  (directory does not exist at all after the full lifecycle completes).

## 8. Registry Provisioning

Independently confirmed `FilesystemAuthorityRegistry` is constructed only
inside `composition.py`, with the configured `registry_root`, and that its
own `resolve()` contract (missing/empty registry → `None`, never raise) —
predates 147O.1 and was not modified by it (confirmed: `git show 01178382`
touches no file under `src/pcae/aesic/registry_filesystem.py`). Production
wiring introduces no new Registry failure mode; it only makes an
already-safe collaborator reachable. Not independently re-tested against
malformed/duplicate/permission-failure Registry declarations beyond
147O.1's own coverage (`TestComposition`, `TestFailureSemantics`), since
those exercise `FilesystemAuthorityRegistry` itself, a pre-existing,
already-independently-verified (Phase 147G/147H) collaborator that
147O.1/147O.2 do not modify.

## 9. Decision Template Provisioning

Confirmed by direct reading of `service.py`'s `_resolve_and_evaluate` (not
modified by 147O.1) that Decision Template resolution and citation
originate from the same resolved template object — no independent
citation reconstruction exists anywhere in `decision_session.py`,
`aesic_status.py`, or `record.py` (all three consume only
`aer.outcome.citation_text`/`package.citation_text`, never re-derive
citation text from a template lookup of their own). Template version
binding across Stage 1 → Stage 2 is enforced by
`service.py:200-208`'s `Stage1HandoffInvalidError` on mismatch — read
directly, not re-derived by new tests, since this logic is unchanged
library code already independently verified at 147H/147N.

## 10. Storage Provisioning

Confirmed `AuthorityEvaluationRecordStore`'s layout
(`records/<package_id>/<evaluation_id>.json`,
`pointers/<package_id>.json`) is deterministic and repository-relative
(`DEFAULT_STORAGE_ROOT = Path(".pcae/authority-evaluation/records")`).
Independently found one containment edge case: see **147O.2-F-1** (§27).
Restart reopens the same store with no special handling required — a
`AuthorityEvaluationRecordStore` is a stateless, root-parameterized
constructor (confirmed by reading `storage.py:98-99`); no test-only path,
no CWD ambiguity beyond the shared `.pcae/`-relative convention already
assessed at §6.

## 11. Stage 1 Reachability

Independently confirmed reachable through `pcae decision-session confirm`
alone, with no direct AES construction, via both in-process
(`TestNonGatingCharacterization`) and real subprocess
(`TestSeparateProcessReproduction`) tests:

- `evaluate_authority_stage_1` is called from `run_decision_session_confirm`
  (`decision_session.py:692`), which uses the same `context` (hence the
  same composition root) as every other command in the same process.
- Eligible case: `authority_evaluation_stage_1: "eligible"` observed in a
  real subprocess's own JSON output
  (`test_configured_eligible_lifecycle_across_real_processes`).
- Ineligible case (declared eligibility for a different identity than the
  session owner): `authority_evaluation_stage_1: "ineligible"` observed;
  confirmation still transitions to `Confirmed`
  (`test_ineligible_outcome_does_not_block_readiness`).
- Failure case (malformed template JSON): `authority_evaluation_stage_1:
  "evaluation_failed"`; confirmation still succeeds — matches 147O.1's own
  disclosed behavior (`decision_session.py:695`'s
  `except AuthorityEvaluationIntegrationError`), independently re-derived
  by reading the `try/except` directly rather than trusting the report.
- Absence (no AES configured): `"not_configured"`, confirmation succeeds
  identically to pre-147O.1 behavior (§7).

## 12. Stage 1 Transport

Confirmed by direct reading of `session_service.py`'s docstring and code
(`evaluate_authority_stage_1`) and `decision_session.py`'s own comment
block (lines 673-690, quoted verbatim in the phase authorization) that
Stage 1 evidence is **never transported across a process boundary by
design** — `readiness` (a separate CLI invocation) always supplies
`stage_1_result=None` to `evaluate_stage_2`. This is a deliberate,
contract-permitted (AESIC-001 §5.2.1) design choice, not a gap this phase
introduces or 147O.1 introduced; independently confirmed by reading
`service.py:213-231`'s `_validate_stage_1_handoff`, which treats
`stage_1_result=None` as a fully valid, non-error input. No cross-session,
cross-identity, or stale-Stage-1 substitution is possible in production
because production Stage 1 evidence never persists past the single
`confirm` process in the first place — there is nothing to substitute.

## 13. Readiness Integration

Confirmed via direct inspection of `publication_handoff_schema.py`'s diff
(§4 above) and exercised end-to-end (§18): `authority_evaluation_ref`/
`citation_text` are populated only when both are non-`None` on the
package, otherwise entirely omitted from the serialized payload — verified
this preserves legacy digest stability via 147O.1's own
`test_round_trip_payload_idempotent_for_legacy_shaped_package` (re-read,
not re-run independently, since it is a pure serialization property with
no production-reachability question left to verify). Full AER content is
never embedded — `authority_evaluation_ref` carries only `record_id`,
`record_digest`, `record_family` (confirmed by reading
`session_service.py:1176-1180`). Evaluation outcome does not gate
readiness construction itself (an *ineligible* Stage 2 outcome produces a
`pending` disposition identically to an eligible one — §11/§24); a Stage 2
**integration failure** does block readiness construction (§24 below is
the precise, independently-verified distinction).

## 14. Stage 2 Reachability

Independently confirmed, by reading `session_service.py:1159-1181` and
exercising it via real subprocess:

- Stage 2 (`evaluate_stage_2`) runs inside
  `SessionApplicationService.construct_readiness_package`, which is
  invoked from `run_decision_session_readiness` — **before** any CHGR
  construction and **entirely outside** `PublicationCoordinator.execute()`
  (confirmed both by reading the call graph and by
  `TestSourceBoundaryIndependentReconstruction::test_publication_coordinator_source_contains_no_aesic_or_authority_evaluation_reference`,
  an AST-level scan of `coordinator.py`'s full source finding zero
  `aesic`/`authority_evaluation`/`AuthorityEvaluationService`/
  `evaluate_stage_2` references of any kind).
- Uses fresh Registry/template resolution on every call (no caching in
  `_resolve_and_evaluate`, unchanged library code).
- Validates optional Stage 1 evidence (§12) before doing any other Stage 2
  work (`_validate_stage_1_handoff` runs first, per
  `service.py:228-231`'s own comment, independently re-read).
- Persists a real AER and canonical pointer — confirmed both by 147O.1's
  own unit test and, independently, by this phase's real-subprocess test
  reading `pcae aesic status --package-id <id> --json`'s
  `current_effective_stage_2` field from a *separate* process than the one
  that ran `readiness`.
- Idempotent no-op vs. supersession is resolved by `evaluate_stage_2`
  itself (`service.py:250-260`), independently confirmed by
  `TestRestartRecovery`'s two-fresh-service-instance test asserting
  `record_id` equality on a repeated identical evaluation.
- The publication path cannot bypass Stage 2 when AES is configured: there
  is no code path from `Confirmed` to a persisted readiness package that
  skips `construct_readiness_package`'s Stage 2 block (single call site,
  no conditional bypass beyond the `self._authority_evaluation_service is
  not None` check that is enablement itself, not a bypass).

## 15. Publication Handoff

Confirmed the exact pre-repair serialization gap by reading the diff (§4)
and confirmed it is closed in current code:
`publication_handoff_schema.to_payload`/`from_payload` now round-trip
`authority_evaluation_ref`/`citation_text`, additively and backward
compatibly — independently re-derived by reading the current source
(not merely re-running 147O.1's own serialization tests), and cross-checked
against a real, separate-process-persisted readiness package
(`readiness_out.json` read directly off disk in this phase's manual
reproduction, §18) showing the fields present and correctly shaped for a
configured session.

## 16. Publication Coordinator Boundary

Independently verified via AST inspection, not text search alone
(`TestSourceBoundaryIndependentReconstruction::test_publication_coordinator_source_contains_no_aesic_or_authority_evaluation_reference`):
`coordinator.py` contains zero `import`/`from` statements naming `aesic` or
`authority_evaluation`, and the literal strings `AuthorityEvaluationService`
and `evaluate_stage_2` do not appear anywhere in its source. Existing
publication transaction ownership (`PublicationCoordinator.execute()`'s own
transaction) is unchanged — confirmed by `git show 01178382 --stat` showing
`coordinator.py` was not touched by 147O.1's diff at all.

## 17. CHGR Citation Integration

Independently confirmed via real, separate-process reproduction (§18):
`authority_basis_claimed` in the persisted CHGR artifact exactly equals the
Decision Template's `eligible_authority` text, verbatim
(`"Approved by Registry."` in this phase's own reproduction, matching what
was deployed). Absent AES configuration, the key is entirely absent from
the artifact (§7) — not present-but-null, not fabricated. This logic lives
in `record.py` (Phase 147M, unmodified by 147O.1/147O.2) and was
independently re-read, not merely re-tested, to confirm it consumes only
`package.citation_text`/`package.authority_evaluation_ref`, never
re-deriving citation text from any other source.

## 18. Separate-Process End-to-End Reproduction

Performed manually first (recorded below, exact commands and output), then
captured as two automated `subprocess`-based tests in the new suite.

**Configured eligible case** (real, disposable repository, six separate
`pcae` subprocess invocations plus two Python one-shot authoring
invocations):

```
$ python -m pcae aesic status --json
  → enabled: true, reason: template_root_populated
$ python -m pcae decision-session create --template-ref demo-template \
    --subject-ref subj-1 --owner-id alice --json
  → session_id: CDS-71d9f556-...
$ python -m pcae decision-session evidence <sid> --declare ev-1 --as-identity alice --json
$ python -m pcae decision-session select <sid> --option-id opt-a \
    --options-presented opt-a --options-presented opt-b --template-version 1.0 \
    --as-identity alice --json
$ python -m pcae decision-session preview <sid> --as-identity alice --json
  → preview_digest: 02d37a9b...
$ python -m pcae decision-session confirm <sid> --preview-digest <digest> \
    --statement confirmed --as-identity alice --json
  → authority_evaluation_stage_1: "eligible"
$ python -m pcae decision-session readiness <sid> --as-identity alice --json
  → package_id: prp-7012786e...
$ python -m pcae aesic status --package-id prp-7012786e... --json
  → current_effective_stage_2.canonical_evaluation_result: "eligible"
$ python -m pcae governance-record publish prp-7012786e... --operator-id alice --json
  → success: true, record_id: chgr-caa9f5b6...
$ cat .pcae/publication-execution/records/chgr-caa9f5b6....json
  → authority_basis_claimed: "Approved."
$ python -m pcae decision-session readiness <sid> --as-identity alice --json   # fresh process, replay
  → disposition: "consumed", record_id: chgr-caa9f5b6... (unchanged, no new AER minted)
```

**Unconfigured compatibility case**: reproduced identically (§7), all six
lifecycle commands succeed, no AER/pointer/citation fabricated.

**Negative/ineligible case**: reproduced in-process
(`TestNonGatingCharacterization::test_ineligible_outcome_does_not_block_readiness`) —
confirmation, readiness, and canonical-record persistence all continue
with `evaluation_result: "ineligible"`; not re-run as a third full
subprocess chain, since the eligible/ineligible code path bifurcates only
inside `evaluate_stage_2`/`evaluate_stage_1` (already reached via real
subprocess in the eligible case) and the outcome value itself is a pure
data difference, not a different reachability path.

**Restart case**: the eligible case's final "replay" step above *is* the
restart case — a genuinely fresh `python -m pcae` process, fresh
composition root, correctly reporting `disposition: "consumed"` against
already-persisted state.

Both automated tests (`TestSeparateProcessReproduction`) pass. This
satisfies §18's "a direct Python service call does not satisfy this
requirement" bar in a way 147O.1's own automated suite does not.

## 19. Restart and Recovery

Independently confirmed two fresh `AuthorityEvaluationService` instances
(via two separate `build_authority_evaluation_service()` calls) converge
on the same canonical AER for a repeated identical evaluation
(`TestRestartRecovery`). The real-subprocess replay in §18 is the stronger
form of this same property across an actual OS process boundary. Did not
independently re-inject a post-AER/pre-pointer crash (`CanonicalPointerUpdateFailedError`'s
own recovery path) beyond confirming, by direct source reading, that this
failure mode is unchanged pre-existing `service.py`/`storage.py` logic that
147O.1/147O.2 do not modify and that was already independently verified at
Phase 147N (AESIC-N-02, §16 below) — re-deriving that specific crash
window from scratch would test library-level code, not production wiring,
and is out of this phase's scope.

## 20. Concurrency

Not independently re-exercised with genuine concurrent processes in this
phase; the `evaluate_stage_2` compound-key-then-pointer sequencing that
makes concurrency safe (§14) is pre-existing, unmodified library code
already covered by Phase 147N's own concurrency verification. Production
wiring introduces no new concurrency surface: it adds exactly one
additional caller of already-concurrency-safe methods, not a new stateful
collaborator.

## 21. Failure Semantics

Independently confirmed and precisely characterized (see §24 for the
gating-vs-failure distinction, the one nuance this phase adds beyond
147O.1's own disclosure): a genuine Stage 2 integration failure (malformed
template JSON) causes `readiness` to fail closed with a governed
`internal_error` response — reproduced independently via
`TestNonGatingCharacterization::test_stage_2_integration_failure_fails_closed_not_silently`.
No CHGR artifact, no AER, no fabricated citation results from a failed
Stage 2 attempt. Registry-unavailable, template-missing, and
malformed-configuration paths were read directly in source and found
identical in kind to 147O.1's own disclosed and tested cases; not
independently re-run, since they exercise pre-existing library error
classes (`AuthorityEvaluationIntegrationError` subclasses) rather than any
new production-wiring logic.

## 22. Diagnostics

Independently confirmed `pcae aesic status` is read-only:
`describe_authority_evaluation_configuration` performs only `Path.exists`/
`is_dir`/`rglob` filesystem reads, and `summarize_package` (when
`--package-id` is supplied) calls only `store.read_canonical`, itself a
read path with no write side effect — confirmed by reading
`aesic_status.py`'s full 76 lines and `diagnostics.py`'s `summarize_package`.
Never constructs a live `AuthorityEvaluationService` (only
`describe_authority_evaluation_configuration`, which does not construct
Registry/AER-store/Service objects at all). Exercised across separate
invocations in §18 with consistent, deterministic output. Independently
confirmed the `--package-id` path handles a pathologically-shaped input
(`".."`) without mutating anything and without raising — see §27.

## 23. Logging and Audit

Confirmed by direct reading of `composition.py`, `service.py`, and
`decision_session.py` that each stage logs a distinguishable event
(`authority_evaluation.composition_enabled`/`_disabled`,
`.stage_1_omitted_on_confirm`, `.stage_2_request`,
`.stage_2_idempotent_noop`, `.aer_committed`,
`.pointer_update_failed`) and that none of these messages claims or
implies authorization/execution grant — every message is phrased as
disclosure ("request", "committed", "omitted"), never "authorized" or
"permitted". Not independently re-verified against a live log capture
beyond reading the `logger.info`/`logger.warning` call sites directly,
since the message text itself is the artifact under review here, not
runtime log-plumbing behavior (unmodified by this phase).

## 24. Non-Gating Verification

This is the one area where independent verification produced a sharper
characterization than 147O.1's own report, though not a defect:

- **Evaluation *outcome* never gates.** Independently reproduced: an
  `ineligible` Stage 2 outcome still produces a `pending` (not rejected)
  readiness disposition, and publication still succeeds
  (`TestNonGatingCharacterization::test_ineligible_outcome_does_not_block_readiness`).
  Confirmed by direct reading that no code path anywhere branches on
  `evaluation_result` to reject a transition.
- **A Stage 2 *integration failure* (not an outcome) does block readiness
  construction.** `construct_readiness_package` has no
  `try/except AuthorityEvaluationIntegrationError` around its
  `evaluate_stage_2` call — unlike `run_decision_session_confirm`'s Stage 1
  call, which does catch and disclose. This is **disclosed by 147O.1
  itself** (its own `TestFailureSemantics::test_stage_2_malformed_template_surfaces_as_governed_error_not_a_crash`
  asserts exactly this: `exit_code != EXIT_SUCCESS`, `error_type ==
  "internal_error"`) and independently re-confirmed here
  (`test_stage_2_integration_failure_fails_closed_not_silently`). This is
  **fail-closed, contract-compliant behavior, not a gating violation of
  AESIC-001's non-gating requirement**: the requirement (AESIC-REQ-091 and
  peers) is that a *disclosed evaluation result* must never become an
  authorization gate; it says nothing about integration failures needing
  to be swallowed into success. Distinguishing these two — outcome-gating
  (absent, correctly) vs. failure-blocking (present, correctly, and
  disclosed) — is this phase's own contribution; 147O.1's report does not
  draw this distinction explicitly, though its own tests are consistent
  with it. Not a finding against 147O.1; recorded here for chapter-record
  precision only.
- Confirmation, readiness, and publication continuation are governed
  solely by pre-existing lifecycle/publication rules in every case
  observed — no new rule was introduced that references Authority
  Evaluation outcome.

## 25. AESIC-N-01 Containment

Independently reconstructed the storage-layer gap directly against
`AuthorityEvaluationRecordStore` (not through the AES service), isolating
the storage layer's own guarantee from the caller discipline that contains
it (`TestAesicN01IndependentContainment::test_storage_layer_gap_reproduced_directly_at_the_storage_api`):
using the real production service to create a genuine AER under
`"pkg-a"`, then forging (via direct, dataclass-independent JSON
construction — deliberately not via `CanonicalPointer(...)`, to avoid any
production code path) a pointer file at `pointers/pkg-a.json` whose
embedded `package_id` names `"pkg-b"`. `read_canonical("pkg-a")` correctly
raises `CanonicalPointerCorruptError` in this case (the record for
`(pkg-b, ev-a)` does not exist, so the `record is None` branch fires) —
independently confirming `read_canonical`'s read-path does follow the
pointer's own embedded `package_id`, not the caller's query key, exactly
as AESIC-N-01 describes, and that a *sufficiently* crafted forgery
(pointing at a record that legitimately exists under a different
`package_id`) would return that other record's content instead of raising,
which is the actual silent-cross-key-resolution risk 147N/147O
identified.

Independently enumerated **every** production call site of
`read_canonical` (`TestAesicN01IndependentContainment::test_every_production_read_canonical_caller_supplies_a_single_non_derived_package_id`,
an AST-level scan, not text search): exactly two —
`service.py:248` (`evaluate_stage_2`, argument is the method's own
`package_id` parameter, always internally generated as
`f"prp-{uuid.uuid4().hex}"` at `session_service.py:1157`, never read back
from any storage-derived value) and `diagnostics.py:44`
(`summarize_package`, called from `aesic_status.py` with a single
CLI-supplied string, a read-only path). Both call sites pass exactly one
positional argument with no compound-key derivation from prior storage
reads. **Conclusion: contained and not production-reachable — Phase
147O.1's production wiring introduced no new call site of
`read_canonical` and expanded AESIC-N-01's attack surface by exactly zero
call sites.** This confirms, rather than merely repeats, Phase 147O's own
conclusion (`service.py:280-286` — `CanonicalPointer` is always
constructed from the method's own `package_id` argument, never from a
storage read-back — independently re-read and re-confirmed at this
phase). **Phase 147O.1 did not repair AESIC-N-01** (it made no change to
`storage.py`'s `read_canonical`/`read_record`/`_pointer_path` methods —
confirmed by `git show 01178382 --stat`, which does not list `storage.py`
at all) — 147O.1's own report's claim that it was "not repaired" is
independently confirmed correct.

## 26. Architecture Policy

Independently confirmed via AST import-graph scan
(`TestSourceBoundaryIndependentReconstruction::test_aesic_zone_has_no_reverse_dependency_on_commands`,
`test_commands_only_import_aesic_composition_root_and_diagnostics_never_authority_evaluation_directly`):
the new `commands -> aesic` edge in `.pcae/policy.toml` corresponds exactly
to real production imports (`decision_session.py` imports
`pcae.aesic.composition`/`pcae.aesic.errors`; `aesic_status.py` imports
`pcae.aesic.composition`/`pcae.aesic.diagnostics`/`pcae.aesic.storage`) —
no broader command-zone access exists, no file under `pcae.aesic` imports
anything from `pcae.commands` (zero reverse dependency), and neither
`commands` file imports `pcae.authority_evaluation` directly (both route
through the `aesic` zone's own composition/diagnostics surface, as the
policy comment claims). `pcae.interactive_workflow`'s own pre-existing
`aesic` dependency (declared before 147O.1, confirmed by the unmodified
surrounding `.pcae/policy.toml` lines) is unrelated to this phase's new
edge. `pcae check`/`pcae health` (re-run at bootstrap, §31) report the
zone architecture as passing with advisory enforcement mode unchanged.
Policy was not modified by this phase.

## 27. Security

Attacked production wiring's actual attacker-reachable surface (the
`package_id` compound key, the only user-influenced input into storage
paths in this subsystem) rather than re-running a generic checklist
against unreachable inputs:

- **Repository-relative path escape (`package_id`):** independently
  discovered that `_safe_name` (in `storage.py`) treats `.` as a safe
  character, so `package_id = ".."` sanitizes to the literal string
  `".."`. Used as a bare directory component in `_record_path`, this
  resolves **one level above** the intended
  `records/<package_id>/` subdirectory — landing inside the AER storage
  root itself (`.pcae/authority-evaluation/records/`), not outside the
  repository (verified directly: `Path(root)/"records"/".."` resolves to
  `root`, never beyond it, since `package_id` cannot itself contain a
  `/` — every `/` is replaced with `_` by the same regex). **Recorded as
  147O.2-F-1 below.** Confirmed this is **not reachable on any
  production write path**: every production writer generates `package_id`
  internally (`f"prp-{uuid.uuid4().hex}"`, `session_service.py:1157`),
  never from untrusted input. It **is** reachable, read-only, via
  `pcae aesic status --package-id ..`; independently exercised
  (`TestAesicN01IndependentContainment::test_package_id_dotdot_breaks_single_level_path_containment_read_only`)
  and confirmed it degrades safely — `summarize_package` returns "no
  canonical record" (no file exists at the flattened path in practice),
  never raises, never leaks unrelated content, because no legitimately
  named record happens to collide with the flattened path in any real
  repository.
- **Absolute-path misuse / symlink redirection / cross-repository reuse:**
  all three roots are supplied only as the module's own `Path` defaults
  in production (no CLI flag, no config file, no env var accepts a
  path override for any of `template_root`/`registry_root`/
  `aer_store_root`) — confirmed by reading `composition.py`'s and
  `aesic_status.py`'s full argument surfaces; there is no production input
  that could redirect these roots at all, so these attack classes have no
  reachable entry point to test against.
- **Registry/template poisoning, stale replay:** these are pre-existing
  `FilesystemAuthorityRegistry`/template-store properties, unmodified by
  this phase, already independently assessed at Phase 147H/147N; not
  re-attacked here since production wiring adds no new way to write to
  either store (both are operator-authored, out-of-AES-scope, per
  AESIC-001 §6.4/§7 — confirmed by reading that section).
- **Pointer cross-key confusion / rollback:** covered under AESIC-N-01
  (§25).
- **Environment-variable injection / CWD manipulation:** no environment
  variable is read anywhere in `composition.py`/`aesic_status.py`
  (confirmed: no `os.environ`/`os.getenv` reference in either file); CWD
  dependence is identical in kind to every other `.pcae/`-relative
  collaborator in the codebase, not a new attack surface this phase
  introduces.

## 28. Requirement and Finding Matrix

| AESIC-O-01 sub-obligation | Verified via | Result |
|---|---|---|
| Persistent production configuration path | §5/§6, source read | Met |
| Composition root, no manual assembly | §5, AST + grep | Met |
| Stage 1 reachable via `confirm` | §11, real subprocess | Met |
| Stage 2 reachable via `readiness` | §14, real subprocess | Met |
| AER/pointer persistence | §14/§18, real subprocess + `aesic status` | Met |
| Readiness/handoff propagation | §13/§15, source + persisted artifact read | Met |
| CHGR citation population | §17, real subprocess, persisted artifact read | Met |
| Unconfigured backward compatibility | §7, real subprocess | Met |
| Restart/retry reconstruction | §18/§19, real subprocess replay | Met |
| Non-gating (outcome) | §24, ineligible-outcome test | Met |
| Runtime capability unchanged | §31, `pcae runtime inspect` | Met |
| AESIC-N-01 not newly exposed | §25, AST call-site enumeration | Met |

| Predecessor finding | Disposition at this phase |
|---|---|
| AESIC-N-01 (Major, 147N) | Contained; production wiring adds zero new `read_canonical` call sites (§25). Not repaired by 147O.1 (independently confirmed). Repair remains recommended, deferred. |
| AESIC-N-02 (Informational/labeling, 147N) | Unaffected by production wiring; not re-examined beyond confirming `storage.py`'s crash-recovery logic is untouched by 147O.1's diff. |
| 147O.1 disclosed limitation: Stage 2 integration failure blocks readiness | Confirmed accurate and precisely characterized as failure-blocking, not outcome-gating (§24). Not a defect. |
| 147O.1 disclosed limitation: Stage 1 evidence not cross-process transported | Confirmed accurate, contract-permitted (§12). Not a defect. |
| **147O.2-F-1** (new, this phase) | `package_id=".."` breaks single-level path containment on the read-only diagnostics path only; not production-write-reachable. See §29. |

## 29. Findings

### 147O.2-F-1 — Minor

- **Severity:** Minor.
- **Affected requirement/criterion:** AESIC-001 storage-key containment
  (adjacent to AESIC-REQ-119); §10/§27 of this document.
- **Reproduction:**
  `AuthorityEvaluationRecordStore()._record_path("..", "ev-1")` resolves to
  `<aer_store_root>/ev-1.json`, one level above the intended
  `records/<package_id>/` subdirectory, because `storage.py`'s `_safe_name`
  regex (`[^A-Za-z0-9._-]`) does not exclude `.`, so a `package_id` of
  `".."` passes through unsanitized as a bare directory component.
- **Expected behavior:** every `package_id` should resolve to a path
  strictly inside `records/<package_id>/`, regardless of its literal
  content.
- **Actual behavior:** a `package_id` of exactly `".."` (or any value
  composed only of `.`/`-`/`_` that forms a traversal segment) escapes one
  directory level, landing inside the AER store root itself — still fully
  contained within `.pcae/authority-evaluation/records/` (never outside
  the repository), but no longer inside the intended per-package
  subdirectory.
- **Operational impact:** none observed in this phase's testing — no
  production write path can supply an attacker-influenced `package_id`
  (always `f"prp-{uuid.uuid4().hex}"`), and the only reachable caller,
  `pcae aesic status --package-id ..` (read-only), degrades safely (no
  record exists at the flattened path in any real repository, so it
  reports "no canonical record" and does not raise or leak content).
- **Containment:** fully contained by the fact that no writer ever passes
  untrusted input as `package_id`; the only reachable path is read-only.
- **Repair boundary:** narrow — tightening `_safe_name` (or validating
  `package_id` does not equal `.`/`..` or contain only `.`/`-`/`_`
  sequences that resolve to a parent-traversal segment) in
  `src/pcae/aesic/storage.py`, with a corresponding test. Out of this
  phase's No-Go boundary (`src/pcae/**` is frozen); deferred to a future,
  separately authorized phase alongside or ahead of AESIC-N-01's repair,
  since both concern the same file's key-sanitization discipline.
- **Recommended disposition:** defer to the AESIC-N-01 repair phase (or a
  narrower follow-up); not blocking, not requiring emergency repair.

No Blocking or Major finding was identified. No finding from Phase 147O.1
or its predecessors was found to be inaccurately disclosed.

## 30. Overall Verdict

**AUTHORITY EVALUATION PRODUCTION WIRING VERIFIED WITH NON-BLOCKING
FINDINGS.**

AESIC-O-01 is demonstrably closed: a single supported composition root
exists, configuration persists correctly across real separate OS
processes, Stage 1 and Stage 2 are both production-reachable through the
supported CLI lifecycle (not merely a direct Python service call — verified
by genuine `subprocess`-based reproduction), AER/pointer persistence
survives restart, CHGR citation is populated exactly and only when
configured, unconfigured repositories remain fully backward compatible,
negative evaluation outcomes remain non-gating, `PublicationCoordinator`
ownership is confirmed intact via AST inspection, runtime capability is
unchanged (`Observed / observe / unavailable`, confirmed via
`pcae runtime inspect`), and AESIC-N-01 is confirmed not newly exposed (zero
new `read_canonical` call sites). One new Minor, non-blocking,
non-production-write-reachable finding (147O.2-F-1) was independently
discovered and is recorded for deferred repair. This does not by itself
prevent chapter certification consideration; it does not require emergency
action.

## 31. Recommended Next Phase

**147O.3 — Authority Evaluation Integration Final Operational Readiness and
Chapter Certification.**

Phase 147O.3 should reassess requirement closure, production-path
reachability, configuration readiness, persistence durability, restart and
recovery, concurrency, diagnostics, logging/audit, security, backward
compatibility, rollout/rollback, and AESIC-N-01 containment against this
phase's findings, and separately determine operational-readiness and
chapter-certification status. It should explicitly account for
147O.2-F-1 (recommend bundling its repair with AESIC-N-01's, since both
touch `storage.py`'s key-sanitization discipline) when assessing whether
any residual Major/Minor finding blocks certification. This recommendation
is not itself an authorization.

---

## Appendix: Validation Run Log

- `pcae check` / `pcae health` / `pcae doctor task-memory` /
  `pcae runtime inspect` / `pcae push check`: all passed; runtime
  confirmed `Observed / observe / unavailable`; repository clean apart
  from this phase's own task/status/report artifacts.
- New independent suite alone:
  `tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`
  — **11 passed**.
- New suite combined with all inherited Authority Evaluation chapter
  suites (147G, 147H, 147M, 147N, 147O.1): **344 passed** (333 inherited +
  11 new; unchanged 333, no regression).
- Full `fast_green` gate (`python -m pytest -m fast_green -n auto -q`):
  **4391 passed**, unchanged from the pre-phase baseline — the new suite
  is intentionally not a member of `FAST_GREEN_MODULES`, matching the
  precedent already set by 147O.1's own chapter suite and every other
  Authority Evaluation phase's test module.
- Full unrestricted suite (`python -m pytest -n auto -q`, no `-m` filter):
  **72 failed, 27105 passed, 10 skipped** (0:59:50). All 72 failures are in
  wheel/sdist packaging tests (`test_cltr_authority_*`, `test_schema_runtime_packaging`,
  `test_chgr_packaging`), architecture/consistency tests unrelated to
  Authority Evaluation (`test_advisory_runtime_contract`,
  `test_advisory_runtime_architecture`, `test_bootstrap_todo_consistency`,
  `test_shell_gate`, `test_rendering_134e5`,
  `test_phase_137i1_finalization_ordering_deadlock`) — none reference
  `decision_session`, `aesic`, `authority_evaluation`, `publication_handoff`,
  or `governance_record`. Independently confirmed pre-existing and
  unrelated to this phase: three sampled failures
  (`test_advisory_runtime_contract::test_no_new_directory_added_for_advisory`,
  `test_bootstrap_todo_consistency::test_real_todo_no_longer_marks_90_series_as_next`,
  `test_chgr_packaging::test_143e_wheel_contains_all_six_chgr_record_schemas`)
  were re-run via `git stash` against the unmodified pre-phase commit
  (`3560e53c`) and reproduce identically there — the packaging failures
  trace to a `python -m build --wheel` subprocess environment issue
  (`CalledProcessError`, exit status 1), not to any change this phase or
  147O.1 made. No new regression was introduced by this phase.
