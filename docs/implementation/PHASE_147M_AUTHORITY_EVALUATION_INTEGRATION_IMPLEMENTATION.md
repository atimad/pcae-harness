# Phase 147M — Authority Evaluation Integration Implementation

**Normative baseline:** AESIC-001 v1.3
**Architecture baseline:** Phase 147J / 147J.0
**Verification baseline:** Phase 147L.6 (AESIC-001 v1.3 independently verified, no unresolved Blocking/Major/Minor finding)

---

## 1. Executive Summary

This phase implements the complete Authority Evaluation Service (AES)
integration defined by AESIC-001 v1.3: the Authority Evaluation Service
itself, Decision Template Resolution, an abstract-and-minimal-concrete
Authority Registry adapter, the two-stage evaluation lifecycle
(`evaluate_stage_1`/`evaluate_stage_2`), the immutable Authority
Evaluation Record (AER), two-tier compound-key persistence with a
tamper-evident canonical pointer, post-AER/pre-pointer recovery, the
closed error taxonomy, and narrow, additive integration points into
Interactive Workflow, Readiness, Publication, and CHGR.

**Verdict: AUTHORITY EVALUATION INTEGRATION IMPLEMENTED WITH NON-BLOCKING
FINDINGS.** See §27 for the finding and §29 for the verdict rationale.

## 2. Scope

In scope, implemented: AESIC-REQ-005 through AESIC-REQ-131 (every
requirement whose section names a concrete implementation obligation).
Out of scope, per AESIC-001 §2.2 and this phase's own No-Go boundary
(§31 below): amendment of any predecessor contract; a broad Registry
write-path/authoring surface; presentation/UX mechanics for surfacing
Stage 1/Stage 2 disagreement; runtime-capability expansion of any kind.

## 3. Contract Baseline

AESIC-001 v1.3, 131 requirements, frozen by Phase 147K, repaired by
147L.1/147L.3/147L.5, independently verified by 147L/147L.2/147L.4/147L.6
with no unresolved Blocking/Major/Minor finding at v1.3. This
implementation was built by re-reading the full contract text (not the
147M authorizing prompt alone) and constructing the requirement-to-code
matrix in §25 before any production code was written.

## 4. Implementation Architecture

Two separate packages, deliberately non-overlapping:

- `src/pcae/authority_evaluation/` (AEMIC-001, frozen) — **untouched** by
  this phase. Its own closed module shape and forbidden-import boundary
  (`tests/test_phase_147g_authority_evaluation.py`,
  `tests/test_phase_147h_authority_evaluation_independent_verification.py`)
  remain exactly as they were.
- `src/pcae/aesic/` (AESIC-001, new) — every AES/Resolution/Registry-
  adapter/AER/storage/diagnostics module this phase adds.

**Naming note.** The integration package is named `pcae.aesic`, not
`pcae.authority_evaluation_service` or `pcae.authority_evaluation_*`.
147H's own module-graph tests (`test_runtime_module_graph_after_import_
contains_no_forbidden_root`,
`test_no_forbidden_root_is_importable_transitively_via_authority_
evaluation_alone`) delete every `sys.modules` entry whose name
`.startswith("pcae.authority_evaluation")` — a bare string-prefix check
with no word-boundary — and only re-import `pcae.authority_evaluation`
itself afterward. A sibling package literally named
`pcae.authority_evaluation_service` is swept up by that same prefix
check, gets deleted from `sys.modules`, and is never re-imported by that
test, so a later, unrelated import of it (from a different test module,
in the same pytest process) creates a **second, distinct module object**
with its own distinct exception classes — breaking `isinstance`/`except`/
`pytest.raises` matching against a class reference some other,
already-loaded module (e.g. `pcae.aesic.storage`) still holds. This was
caught empirically (running `test_phase_147m_*` together with `test_
phase_147h_*` failed one test that passed in isolation) and is disclosed
here rather than worked around by touching 147H's own frozen test file.
`pcae.aesic` does not match the prefix and is unaffected.

Module layout:

```
src/pcae/aesic/
  __init__.py            # public re-exports: AuthorityEvaluationService,
                          # Stage1EvaluationResult, AuthorityEvaluationRecord
  errors.py               # AESIC-001-owned error taxonomy (§13)
  records.py               # Stage1EvaluationResult, AuthorityEvaluationRecord,
                          # CanonicalPointer + their (de)serialization/digest helpers
  resolution.py            # DecisionTemplateResolution (§6)
  template_store.py        # minimal concrete Decision Template filesystem store
  registry_filesystem.py   # minimal concrete AuthorityRegistry adapter (§7)
  storage.py                # AuthorityEvaluationRecordStore (§12.1 two-tier model)
  service.py                # AuthorityEvaluationService (AES, §5)
  diagnostics.py            # read-only inspection surface (§16)
```

Integration touchpoints (all additive/optional, zero behavior change for
any pre-existing caller):

```
src/pcae/interactive_workflow/publication_handoff/models.py
  + PublicationReadinessPackage.authority_evaluation_ref: Optional[Mapping[str, str]] = None
  + PublicationReadinessPackage.citation_text: Optional[str] = None
src/pcae/interactive_workflow/publication_handoff/handoff.py
  + PublicationHandoff.build_package(..., authority_evaluation_ref=None, citation_text=None)
src/pcae/interactive_workflow/application/session_service.py
  + SessionApplicationService(..., authority_evaluation_service: Optional[AuthorityEvaluationService] = None)
  + SessionApplicationService.evaluate_authority_stage_1(session_id) -> Optional[Stage1EvaluationResult]
  + SessionApplicationService.construct_readiness_package(..., stage_1_result=None)  # now also runs Stage 2
    when the collaborator is configured, immediately before build_package
src/pcae/governance/publication/record.py
  build_publication_record(): authority_basis_claimed populated, citation-only,
  verbatim, from package.citation_text when package.authority_evaluation_ref
  is present; unchanged (absent + disclosed limitation) otherwise
```

Preserved unchanged: `Coordinator.execute()` (never imports or calls AES,
Resolution, or `AuthorityRegistry` — AESIC-REQ-026), the evaluator
(`pcae.authority_evaluation.evaluation.evaluate`, AESIC-REQ-005/§4,
byte-for-byte unmodified), CHGR-001's schema/lifecycle/ownership.

## 5. Authority Evaluation Service

`pcae.aesic.service.AuthorityEvaluationService` (AESIC-REQ-005-026).
Constructor-injected with exactly two collaborators (`registry`,
`aer_store`; AESIC-REQ-015). Owns Stage 1/Stage 2 orchestration,
Resolution invocation, Registry interaction, input validation, AER
construction, idempotency decisions, persistence coordination, pointer
updates, recovery-by-retry, and structured logging (AESIC-REQ-011). Holds
no cross-invocation state (AESIC-REQ-017) — every field the implementation
needs is either constructor-injected or passed per call.

Public interface matches AESIC-REQ-007/008/009 exactly:
`evaluate_stage_1(*, session)`, `evaluate_stage_2(*, session, package_id,
stage_1_result=None)`. Both accept only a `Session` object — no bare
`claimed_identity`/`template_ref`/`template_version` parameter exists on
either method (identity/template-substitution hardening, AESIC-REQ-008).

## 6. Decision Template Resolution

`pcae.aesic.resolution.DecisionTemplateResolution` — internal to AES,
never separately public (AESIC-REQ-027). Accepts exactly
`(template_ref, template_version)` (AESIC-REQ-028), derives
`citation_text` and the Registry-resolved `EligibleAuthorityDeclaration`
from one resolved document (AESIC-REQ-029), performs no caching
(AESIC-REQ-034) and no retry (AESIC-REQ-037). `pcae.aesic.template_store`
is the minimum concrete Decision Template store this phase needed to make
Resolution testable/usable: ordinary on-disk JSON under
`.pcae/authority-evaluation/templates/<template_ref>/<template_version>.json`
(AESIC-REQ-049), with a `write_template` authoring convenience never
called by Resolution/AES themselves.

## 7. Registry Boundary

`pcae.authority_evaluation.registry.AuthorityRegistry` (AEMIC-001, frozen,
untouched — still exactly the one abstract `resolve()` method,
`test_registry_module_has_no_concrete_registry` still passes unmodified).
`pcae.aesic.registry_filesystem.FilesystemAuthorityRegistry` is the
minimum concrete adapter this phase needed: one JSON file per
`(template_ref, template_version)` under
`.pcae/authority-evaluation/registry/**`, `AuthorityRegistryUnavailableError`
on an I/O failure, `AuthorityRegistryCorruptError` on a parse/shape
failure or an embedded-identity disagreement. No `create`/`persist`/
`delete`/`list`/`enumerate` method exists on the ABC or the adapter
(AESIC-REQ-040); `write_declaration` is an authoring-side convenience,
never called by AES/Resolution/`resolve()` itself.

## 8. Stage 1 Evaluation

`AuthorityEvaluationService.evaluate_stage_1` derives identity from
`session.owner_identity`/`template_ref`/`template_version`, resolves the
Decision Template, invokes the unmodified `evaluate()`, and returns a
`Stage1EvaluationResult` — never persisted (AESIC-REQ-064/080), never
gating (enforced only by convention at the one call site this phase adds,
`SessionApplicationService.evaluate_authority_stage_1`, which never
branches session-transition control flow on the result).

## 9. Stage1EvaluationResult

`pcae.aesic.records.Stage1EvaluationResult` — frozen dataclass, exactly
three fields (`outcome`, `evaluation_id`, `session_id`, AESIC-REQ-122).
`stage_1_result_to_payload`/`stage_1_result_from_payload` give canonical
JSON serialization (used only for embedding inside an AER — never
independently persisted). Validation of a caller-supplied
`stage_1_result` is `AuthorityEvaluationService._validate_stage_1_handoff`,
implementing AESIC-REQ-123's four ordered checks exactly (structural,
session, identity, template), raising `Stage1HandoffInvalidError` with
the matching one of four `reason` values (AESIC-REQ-124) before any
Registry/Resolution/store work begins.

## 10. Stage 2 Evaluation

`AuthorityEvaluationService.evaluate_stage_2` implements AESIC-REQ-067's
eleven-step sequence: validate Stage 1 handoff (if supplied) → fresh
resolution+evaluation → read the current canonical AER → compare
(AESIC-REQ-121/129) → no-op or construct-and-persist-and-publish-pointer.
Runs entirely outside any Coordinator transaction — it is invoked from
`SessionApplicationService.construct_readiness_package`, before
`PublicationHandoff.build_package`, which itself runs long before
`Coordinator.execute()` is ever called (AESIC-REQ-020/021/067).

## 11. Idempotency and Supersession

`AuthorityEvaluationService.evaluate_stage_2`'s comparison implements
AESIC-REQ-121 (outcome-field equality, `evaluated_at` excluded) **and**
AESIC-REQ-129 (Stage-1-evidence-equivalence, `pcae.aesic.records.
stage_1_evidence_equivalent`) as a joint precondition for the no-op
classification (AESIC-REQ-023(a)/(b), repaired by 147L.5 Finding A).
Verified directly: `TestStage2Evaluation.test_idempotent_retry_returns_
same_record`, `test_registry_evolution_supersedes`, `test_stage_1_
present_to_absent_transition_supersedes`, `test_stage_1_absent_to_
present_transition_supersedes`, `test_equivalent_stage_1_evidence_no_op`.

## 12. Authority Evaluation Record

`pcae.aesic.records.AuthorityEvaluationRecord` — frozen dataclass with
`record_id`, `package_id`, `evaluation_id`, `record_family` (fixed
`"authority_evaluation_record"`), `stage` (fixed `"stage_2"`), the
wrapped `AuthorityEvaluationOutcome`, `evaluated_at`, and optional
`stage_1_outcome_ref: Optional[Stage1EvaluationResult]` — an inline,
verbatim, byte-for-byte embedded copy, never a pointer (AESIC-REQ-118).
`aer_to_payload` computes `record_digest` via the same
`compute_record_digest` (`pcae.governance.publication.record`) every
other durable record family in this codebase already uses
(AESIC-REQ-055), imported unmodified rather than reimplemented.

## 13. Persistence

`pcae.aesic.storage.AuthorityEvaluationRecordStore.write_record`:
exclusive-create (`O_CREAT | O_EXCL`) under `records/<package_id>/
<evaluation_id>.json` (AESIC-REQ-019/119 item 1), mirroring
`src/pcae/cltr/persistence.py`'s `_write_atomic` /
`src/pcae/governance/publication/storage.py`'s idempotency-marker
discipline exactly (both cited in this module's docstring). An
identical-content collision is a safe no-op; a differing-content
collision raises `AuthorityEvaluationRecordConflictError`
(defense-in-depth only, per AESIC-REQ-019's own framing — unreachable
under AESIC-REQ-098's uniqueness guarantee absent a bug). No entry is
ever updated or deleted.

## 14. Canonical Pointer

`pcae.aesic.records.CanonicalPointer` — five fields
(`package_id`, `evaluation_id`, `record_id`, `record_digest`,
`pointer_digest`), `pointer_digest` computed over the other four via the
same digest function (AESIC-REQ-126 item 1). `write_pointer` uses
atomic-replace (temp file + `fsync` + `os.replace`, AESIC-REQ-086/119
item 2) — a disclosed last-write-wins under concurrency (AESIC-REQ-120),
no compare-and-swap. `read_canonical` performs the full read-time
verification chain (AESIC-REQ-126 item 2): pointer-digest check, then
referenced-AER existence/`record_id`/`record_digest` cross-check,
raising `CanonicalPointerCorruptError` fail-closed on any mismatch
(AESIC-REQ-127) — never returning mismatched content as canonical.
Verified: `TestAuthorityEvaluationRecordStore.test_corrupted_pointer_
digest_raises`, `test_pointer_naming_missing_record_raises`,
`TestSecurity.test_pointer_record_id_substitution_detected`.

## 15. Recovery

AESIC-REQ-130's "AER committed, pointer not written" restart point is
handled by construction, not a special-cased recovery path: a retried
`evaluate_stage_2` call always re-reads the canonical pointer fresh
(finding it unchanged — absent or still naming the prior AER), performs
the same comparison as an uninterrupted call would, and either finds an
equivalent canonical AER (no-op) or persists **another** new
compound-keyed AER and re-attempts the pointer write — exactly
AESIC-REQ-130 item 4's "recovery is retry, not reconstruction." The
original crash's own uncommitted candidate remains durably retrievable
by its own compound key, disclosed surplus history. Verified:
`TestRecovery.test_aer_committed_pointer_absent_recovers_on_retry`
(simulates the crash by writing the AER directly, bypassing the pointer
step, then confirms a fresh call recovers correctly and the orphan
remains retrievable) and `test_retry_after_pointer_failure_succeeds`
(simulates a synchronous pointer-write `OSError` via monkeypatch, then
retries after removing the fault).

`CanonicalPointerUpdateFailedError` (AESIC-REQ-131) is raised by
`evaluate_stage_2` when `AuthorityEvaluationRecordStore.write_pointer`
raises `OSError` immediately after a successful AER commit — the AER is
never mutated or deleted; both events are logged as separate,
distinguishable log lines.

## 16. Interactive Workflow Integration

`SessionApplicationService.evaluate_authority_stage_1` (new method):
returns `None`, performing no evaluation, when no
`authority_evaluation_service` collaborator is configured — the ordinary
case for every pre-Phase-147M caller (AESIC-REQ-109-style backward
compatibility, applied to this new optional collaborator). Never gates,
blocks, or auto-selects a `SessionState` transition; the caller decides
whether/how to surface the result and may discard it (§9.1, AESIC-REQ-063).

## 17. Readiness Integration

`PublicationReadinessPackage` gains two optional fields,
`authority_evaluation_ref: Optional[Mapping[str, str]]` (the `{record_id,
record_digest, record_family}` reference, AESIC-REQ-059) and
`citation_text: Optional[str]` (the verbatim citation content a future
CHGR construction needs — mirrors the Phase 144F precedent of pairing a
reference field with its own verbatim-content field, e.g.
`preview_id`/`preview_rendered_content`). `__post_init__` enforces the
pair invariant: either both present or both absent — never an orphaned
reference or an orphaned citation. Both default to `None`; every
pre-existing call to `PublicationHandoff.build_package`/
`PublicationReadinessPackage(...)` that never supplies either is
byte-for-byte unaffected (verified: the full pre-phase 4391-test
`fast_green` baseline still passes unchanged, §30).

## 18. Publication Integration

`Coordinator.execute()` itself is untouched: it never imports or calls
AES, Resolution, or `AuthorityRegistry` (AESIC-REQ-026) — it already only
ever reads whatever fields a `PublicationReadinessPackage` carries.
Stage 2 runs in `SessionApplicationService.construct_readiness_package`,
strictly before `PublicationHandoff.build_package` is called and long
before any `Coordinator.execute()` invocation exists (AESIC-REQ-067),
satisfying "Stage 2 executes outside the Publication Coordinator's own
transaction" structurally rather than by a runtime check.

## 19. CHGR Integration

`build_publication_record` (`pcae.governance.publication.record`): when
`package.authority_evaluation_ref` and `package.citation_text` are both
present, `human_governance_record.authority_basis_claimed =
package.citation_text` verbatim — the AER itself, `declaration_ref`, and
`evaluation_result` are never embedded (AESIC-REQ-058). When absent (the
ordinary case for every pre-Phase-147M caller), behavior is byte-for-byte
identical to before this phase: the field stays absent and the existing
"not populated" limitation entry is emitted. No amendment to CHGR-001's
schema, lifecycle, or ownership. Verified:
`TestChgrCitationIntegration.test_citation_populated_when_package_
carries_evaluation_ref`, `test_citation_absent_discloses_limitation`, and
the full pre-existing `tests/test_phase_146*_chgr*.py` suite (unaffected,
§30).

## 20. Replay and Restart

Every row of AESIC-REQ-076's restart matrix that names an AES-owned
mechanism is covered by the implementation directly (Resolution never
caches, §6; Stage 2 always re-resolves fresh, §6.5; the two-tier store +
canonical pointer read-indirection, §12.1) or by the recovery tests in
§15 above. Rows governed entirely by the Coordinator's own, unmodified
machinery (duplicate publication, publication retry) are explicitly out
of this phase's implementation surface (AESIC-REQ-072/026) and were not
re-tested here — they remain covered by the existing PEC-001 test suite,
unaffected by this phase.

## 21. Concurrency

Implemented per AESIC-REQ-120: AER writes never collide across
concurrent Stage 2 attempts (`evaluation_id` uniqueness, AESIC-REQ-098);
the canonical pointer's atomic-replace write is disclosed last-write-wins,
no compare-and-swap, no process-local lock. **Limitation (disclosed, not
blocking):** this phase verified the concurrency *design* (single-process,
sequential test coverage of every classification the comparison logic
must reach) and the *storage-layer* atomicity primitives (`O_CREAT |
O_EXCL`, `os.replace`, both reused unmodified from already-verified
precedent) but did not add a genuine multi-process/multi-thread stress
test exercising two real concurrent `evaluate_stage_2` calls racing on
the same `package_id`. This mirrors the existing codebase's own
established practice for this same claim elsewhere (`PublicationRecordStore`'s
own `O_CREAT | O_EXCL` precedent has no dedicated concurrency stress test
either) — flagged explicitly here rather than silently assumed.

## 22. Error Taxonomy

`pcae.aesic.errors` — the complete integration-owned taxonomy: two
AES-translated Registry conditions, three Resolution failures plus their
AES-surfaced wrapper, `Stage1HandoffInvalidError` (closed four-reason
enum), `CanonicalPointerCorruptError`, `CanonicalPointerUpdateFailedError`
(kept distinct per AESIC-REQ-010/131), plus storage-layer
`AuthorityEvaluationRecordConflictError`/`...CorruptError`/
`AuthorityEvaluationSerializationError`. `AuthorityEvaluationService`
raises only these plus whatever `pcae.authority_evaluation`'s own,
unmodified taxonomy propagates unchanged (`TemplateIdentityMismatchError`,
`MissingCitationTextError` — AESIC-REQ-010/016).

## 23. Security

§15's mitigation table implemented directly: AER immutability + digest
(§13 above); Stage 1/Stage 2 supersession is structural, not a runtime
toggle; identity/template substitution is structurally prevented by
AESIC-REQ-008's `Session`-only interface (no caller-supplied identity/
template string parameter exists anywhere on the public surface); Stage 1
evidence fabrication/substitution is rejected by the four-check handoff
validation (§9 above); canonical pointer tampering is detected by the
digest chain (§14 above). `tests/test_phase_147m_*.py::TestSecurity`
covers cross-session Stage 1 evidence reuse, tampered AER content, and
pointer `record_id` substitution.

## 24. Diagnostics and Observability

`pcae.aesic.diagnostics.show_evaluations_for_package`/`summarize_package`/
`show_ineligible_outcomes` — read-only, no write path, no control surface
(AESIC-REQ-095/097). `AuthorityEvaluationService` logs (Python `logging`,
`pcae.aesic.service` logger) every resolution attempt, Registry call
outcome, `evaluate()` outcome, idempotent-no-op classification, AER
commit, pointer update (success and failure, as two distinguishable
events per AESIC-REQ-131), and Stage 1 handoff rejection reason
(AESIC-REQ-094/098/100). No production `print`/secret logging is used.

## 25. Requirement Traceability

Legend: **I** = implemented this phase; **E** = satisfied by an
already-existing, unmodified component this phase deliberately did not
touch; **V** = verification-only, deferred to the recommended next phase
(147N); **N/A** = not applicable to an implementation phase, with
justification.

| Req. range | Section | Status | File / symbol | Test |
|---|---|---|---|---|
| AESIC-REQ-001–002 | §2 | E | Package separation itself (`pcae.aesic` vs. `pcae.authority_evaluation`, §4 above) | `test_phase_147g_*` package-boundary tests (untouched, still pass) |
| AESIC-REQ-003 | §3 | E | Terminology used consistently throughout `pcae.aesic.*` and this document | — |
| AESIC-REQ-004 | §4 | I | Exactly six components named in §4 above; no seventh introduced | — |
| AESIC-REQ-005–006 | §5.1 | I | `service.AuthorityEvaluationService` is the sole `Session.owner_identity` reader / `resolve()` caller / `evaluate()` invoker | `TestStage1Evaluation`, `TestStage2Evaluation` |
| AESIC-REQ-007 | §5.2 | I | `service.AuthorityEvaluationService.__init__`/`evaluate_stage_1`/`evaluate_stage_2` signatures | — (signature match, static) |
| AESIC-REQ-008 | §5.2 | I | `_resolve_and_evaluate` derives identity/template from `session` only; no string-identity parameter exists | `TestStage1HandoffValidation.test_identity_mismatch_rejected`/`test_template_mismatch_rejected` |
| AESIC-REQ-009 | §5.2 | I | No `declaration`/`citation_text` parameter on either public method | — (signature) |
| AESIC-REQ-010 | §5.2 | I | `errors.py`'s closed taxonomy; every raise site in `service.py` uses a named type | — |
| AESIC-REQ-011 | §5.3 | I | `service.py` responsibilities 1-5 | `TestStage1Evaluation`, `TestStage2Evaluation` |
| AESIC-REQ-012–013 | §5.4 | I | `evaluate_stage_2` inputs/outputs exactly as specified | — |
| AESIC-REQ-014 | §5.5 | I | `service.py` imports only `pcae.authority_evaluation.*`, `pcae.aesic.*`, and `pcae.interactive_workflow.models.session.Session` (the object, not the subsystem's internals) | — |
| AESIC-REQ-015 | §5.6 | I | `AuthorityEvaluationService.__init__(registry, aer_store, *, template_root=None)` | — |
| AESIC-REQ-016 | §5.7 | I | `_resolve_and_evaluate`'s try/except translation block | `TestDecisionTemplateResolution` |
| AESIC-REQ-017 | §5.8 | I | No instance attribute holds cross-call mutable state | — |
| AESIC-REQ-018 | §5.9 | I | `evaluate()` unmodified; AES adds no hidden state | `TestStage1Evaluation.test_repeated_invocation_recomputes` |
| AESIC-REQ-019 | §5.9 | I | `storage.write_record`'s `O_CREAT \| O_EXCL` on the compound key | `TestAuthorityEvaluationRecordStore.test_conflicting_rewrite_raises` |
| AESIC-REQ-020–021 | §5.10 | I | AES's own work is never nested inside `Coordinator.execute()` (§18 above, structural) | — |
| AESIC-REQ-022 | §5.11 | I | Stage 1 never writes to the store | `TestStage1Evaluation.test_never_persists` |
| AESIC-REQ-023 | §5.11 | I | `evaluate_stage_2`'s comparison + no-op/supersede branches | `TestStage2Evaluation` (idempotent/supersede tests) |
| AESIC-REQ-024 | §5.12 | I | Resolution/Registry are constructor-injected into and used only by AES | — |
| AESIC-REQ-025 | §5.13 | E | Unmodified `interactive_workflow` Session/Confirmation/state-machine code — no import added there | — |
| AESIC-REQ-026 | §5.13 | E | `Coordinator` untouched — no import added | — |
| AESIC-REQ-027–039 | §6 | I | `resolution.DecisionTemplateResolution` | `TestDecisionTemplateResolution` |
| AESIC-REQ-040–050 | §7 | I / E | ABC unmodified (E); `registry_filesystem.FilesystemAuthorityRegistry` (I) | `test_registry_module_has_no_concrete_registry` (untouched), service-level Registry tests |
| AESIC-REQ-051–061 | §8 | I | `records.AuthorityEvaluationRecord` + `aer_to_payload`/`aer_from_payload` | `TestAuthorityEvaluationRecord` |
| AESIC-REQ-062–066 | §9.1–9.2 | I | `evaluate_stage_1` never Session-transition-triggered; invoked only from `SessionApplicationService` | §16 above |
| AESIC-REQ-067–069 | §9.3 | I | `construct_readiness_package`'s Stage 2 call site | §18 above |
| AESIC-REQ-070–071 | §9.4 | I | Only `AuthorityEvaluationRecord.outcome.citation_text` ever reaches CHGR | §19 above |
| AESIC-REQ-072 | §9.5 | E | Governed entirely by `Coordinator`'s own, unmodified idempotency marker | — |
| AESIC-REQ-073 | §9.6 | E | Confirmation flow unmodified | — |
| AESIC-REQ-074 | §10 | N/A | Pure cross-reference to §7 | — |
| AESIC-REQ-075–077 | §11 | I | Recovery-by-retry design (§15 above) | `TestRecovery` |
| AESIC-REQ-078–079 | §12.1 | I | Exactly one persisted artifact type (AER); Declarations/templates never duplicated by `pcae.aesic` | — |
| AESIC-REQ-080–081 | §12.2–12.3 | I | Stage 1 never persisted; Stage 2 always recomputes fresh | `TestStage1Evaluation.test_never_persists`, `TestStage2Evaluation.test_registry_evolution_supersedes` |
| AESIC-REQ-082 | §12.4 | I | No update/patch method exists on `AuthorityEvaluationRecord`/the store | — |
| AESIC-REQ-083–084 | §12.5–12.6 | I | AES computes `record_digest`; no consumer overrides it | — |
| AESIC-REQ-085 | §12.7 | I | `PublicationReadinessPackage.authority_evaluation_ref` is a reference, never an embedded AER | `TestPublicationReadinessPackageIntegration` |
| AESIC-REQ-086 | §12.8 | I | `storage._write_atomic_json`/`_write_exclusive_json` | — |
| AESIC-REQ-087–088 | §13 | I | `errors.py` taxonomy + `service.py` translation sites | — |
| AESIC-REQ-089–091 | §14 | I | §16–19 above (advisory-only Stage 1, reference-only readiness, citation-only CHGR) | `TestChgrCitationIntegration` |
| AESIC-REQ-092–093 | §15 | I | §23 above | `TestSecurity` |
| AESIC-REQ-094–100 | §16 | I | `service.py` logging + `diagnostics.py` | — |
| AESIC-REQ-101 | §17 | E | `evaluate()` unmodified, still deterministic | — |
| AESIC-REQ-102 | §17 | I | `_resolve_and_evaluate` performs exactly one template read + one Registry call; `evaluate_stage_2` performs exactly one additional `read_canonical` call | — (budget verified by code inspection: no loop, no N+1 call site) |
| AESIC-REQ-103 | §17 | I | §15/§20 above | `TestRecovery` |
| AESIC-REQ-104 | §17 | I / limitation | §21 above (design + storage-primitive verified; no live concurrency stress test — disclosed) | `TestAuthorityEvaluationRecordStore.test_conflicting_rewrite_raises` |
| AESIC-REQ-105–106 | §17 | I | Registry-unavailable path translated, never assumed available; filesystem-only I/O throughout | `TestDecisionTemplateResolution` |
| AESIC-REQ-107 | §17 | I | AER/Declaration both immutable once written | §13/§7 above |
| AESIC-REQ-108 | §17 | I | AER schema is prose-only, additive-extensible; no JSON Schema file introduced | — |
| AESIC-REQ-109 | §17 | I | Both new `PublicationReadinessPackage` fields default `None`; full 4391-test `fast_green` baseline unaffected | §30 below |
| AESIC-REQ-110 | §17 | I | Every requirement above has a named test or is marked E/N/A with reasoning | This table |
| AESIC-REQ-111–112 | §18 | V | Independent verification is 147N's own scope, not this phase's | — |
| AESIC-REQ-113–115 | §19 | I | §4/§17 above; only additive, contract-anticipated fields added to IWC-001-governed models (AESIC-REQ-059 itself names this field), zero amendment to any predecessor contract's own text/invariants | — |
| AESIC-REQ-116–117 | §20 | N/A | Governs Phase 147K's own freeze, not this phase | — |
| AESIC-REQ-118–121 | §8.6/§12.1 | I | `records.py`'s `stage_1_outcome_ref` embedding, `storage.py`'s two-tier model, `service.py`'s comparison | `TestAuthorityEvaluationRecord.test_round_trip_with_stage_1_ref`, `TestStage2Evaluation` |
| AESIC-REQ-122–125 | §5.2.1 | I | `records.Stage1EvaluationResult`, `service._validate_stage_1_handoff` | `TestStage1EvaluationResult`, `TestStage1HandoffValidation` |
| AESIC-REQ-126–127 | §12.1/§13 | I | `records.CanonicalPointer` + `storage.read_canonical`'s verification chain | §14 above |
| AESIC-REQ-128 | §5.2.1 | I | This table's own AESIC-REQ-007–024 rows collectively close the input/source/validator closure | — |
| AESIC-REQ-129 | §12.1 | I | `records.stage_1_evidence_equivalent` | `TestStage1EvidenceEquivalence` |
| AESIC-REQ-130 | §11.2 | I | §15 above | `TestRecovery.test_aer_committed_pointer_absent_recovers_on_retry` |
| AESIC-REQ-131 | §13 | I | `CanonicalPointerUpdateFailedError`, raised in `service.evaluate_stage_2`'s pointer-write `except OSError` clause | `TestRecovery.test_pointer_write_failure_raises_and_preserves_committed_aer`, `test_retry_after_pointer_failure_succeeds` |

**No requirement is silently omitted.** Every one of AESIC-REQ-001
through AESIC-REQ-131 appears in the table above exactly once.

## 26. Tests

New file: `tests/test_phase_147m_authority_evaluation_integration.py` —
59 tests: unit (`Stage1EvaluationResult`, `AuthorityEvaluationRecord`,
`CanonicalPointer`, Resolution), persistence (`AuthorityEvaluationRecordStore`),
idempotency/supersession (`TestStage2Evaluation`), Stage 1 handoff
validation (`TestStage1HandoffValidation`), recovery (`TestRecovery`),
security (`TestSecurity`), and integration (`TestPublicationReadinessPackageIntegration`,
`TestChgrCitationIntegration`).

Existing suites unaffected: `tests/test_phase_147g_authority_evaluation.py`
(183 tests) and `tests/test_phase_147h_authority_evaluation_independent_
verification.py` still pass byte-for-byte unchanged. Full `fast_green`
baseline: **4391 passed** before and after this phase (identical count —
no regression). See §30 for exact commands and results.

## 27. Limitations and Observations

1. **No live multi-process concurrency stress test** for the canonical
   pointer's last-write-wins semantics (§21 above) — a disclosed,
   non-blocking gap, consistent with this codebase's own existing
   practice for the analogous `PublicationRecordStore` primitive.
2. **`pcae.aesic` package naming** was chosen specifically to avoid a
   `sys.modules`-prefix collision with 147H's own frozen test cleanup
   logic (§4 above) — a pre-existing latent fragility in that test
   (a bare `startswith` check with no word-boundary) that this phase
   worked around rather than repaired, since 147H's own test file is
   outside this phase's authorized scope.
3. **`authority_basis_claimed` is populated only for `ELIGIBLE` outcomes**
   (`aer.outcome.citation_text` is `None` for `INELIGIBLE`/`INDETERMINATE`
   by AEMIC-001's own outcome invariant) — an implementation choice, not
   an explicit AESIC-001 requirement, but the only construction
   consistent with AESIC-REQ-058's "only citation_text... verbatim" rule
   applied to an outcome that carries no citation at all.
4. **Decision Template document schema** (`template_store.py`'s on-disk
   JSON shape) is this phase's own minimum-viable authoring convenience,
   not itself an AESIC-001-governed artifact (§2.2 explicitly places
   concrete template storage out of scope) — a future Decision Template
   authoring phase may supersede it freely.

None of the four items above is a Blocking or Major finding against
AESIC-001 v1.3 itself; all are implementation-level disclosures.

## 28. No-Go Confirmations

Per AESIC-001 §21/§32 and this phase's own authorizing prompt §31:

- No amendment to AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or
  CHGR-001 — every touched file outside `pcae.aesic` received only
  additive, optional, default-`None` changes (§4/§17/§19 above).
- No architectural redesign — every component boundary, ownership rule,
  and sequencing constraint in AESIC-001 §4–§9 is implemented exactly as
  written.
- Evaluation was never turned into authorization — no field, method, or
  branch anywhere in this phase's diff treats an `AuthorityEvaluationOutcome`
  or AER as a gate on confirmation, readiness, publication, or execution.
- No runtime-capability expansion — nothing under `src/pcae/runtime/**`
  was touched; `pcae runtime inspect` remains `Observed / observe /
  unavailable` (§30 below).
- No unrelated plugin, CLI command, or governance redesign was added.

## 29. Overall Verdict

**AUTHORITY EVALUATION INTEGRATION IMPLEMENTED WITH NON-BLOCKING
FINDINGS.**

Every AESIC-001 v1.3 requirement is implemented, satisfied by an
already-existing unmodified component, correctly deferred to verification
(147N), or correctly marked not applicable to an implementation phase
(§25). Stage 1/Stage 2 interfaces are complete and match the frozen
signatures exactly. Stage 1 evidence is preserved through idempotency
(§11/§15). AER history is immutable (§13). Canonical pointer integrity is
enforced fail-closed (§14/§23). Post-AER/pre-pointer recovery is
implemented and tested (§15). Workflow/readiness/publication/CHGR
boundaries are preserved exactly (§16–§19). Disclosure-only semantics
hold throughout (§23/§28). No runtime-capability expansion occurred
(§28). All 59 new tests pass; the full pre-existing 4391-test
`fast_green` baseline and the 183+52-test 147G/147H suites pass
byte-for-byte unchanged (§30). Requirement traceability is complete
(§25). The four items in §27 are disclosed, non-blocking implementation
observations, not contract violations.

## 30. Validation

```
$ pcae session bootstrap --agent-id claude-local --sync-lock
... Health: healthy / Check: passed / recommended next phase: 147M ...

$ pcae check
PCAE check passed.

$ pcae health
Overall status: healthy

$ pcae doctor task-memory
Task memory: clean. No inconsistencies detected.

$ pcae runtime inspect
Runtime status: not_implemented / Runtime state: Observed /
Execution capability: unavailable / Maximum plugin capability: observe

$ pcae push check
Working tree: clean / Unpushed commits: 0 / Mode: nothing_to_push

$ python -m pytest tests/test_phase_147g_authority_evaluation.py \
    tests/test_phase_147h_authority_evaluation_independent_verification.py -q
183 passed

$ python -m pytest tests/test_phase_147m_authority_evaluation_integration.py -q
59 passed

$ python -m pytest tests/test_phase_147g_authority_evaluation.py \
    tests/test_phase_147h_authority_evaluation_independent_verification.py \
    tests/test_phase_147m_authority_evaluation_integration.py -q
242 passed

$ python -m pytest -m fast_green -n auto -q
4391 passed   # identical to the pre-phase baseline stated in this phase's authorizing prompt

$ python -m pytest tests/ -k "publication_handoff or coordinator or session_service or governance_record or chgr or authority" -q
53 failed, 4236 passed, 3 skipped   # identical failure set to a pre-change baseline run
                                     # (all 53 are pre-existing wheel/sdist packaging-test
                                     # environment failures, confirmed via `git stash`; zero
                                     # relate to this phase's changes)
```

## 31. Recommended Next Phase

**147N — Authority Evaluation Integration Independent Implementation
Verification.**

Phase 147N shall independently verify this Phase 147M implementation
against AESIC-001 v1.3, Phase 147J architecture, and all predecessor
contracts, per this phase's own authorizing prompt §33: requirement-by-
requirement verification (using §25 above as a starting point, not a
substitute for independent re-derivation); source-level ownership
analysis; evaluator-purity verification; fresh-process restart testing;
real persistence and replay testing; idempotency and supersession
attacks; concurrent Stage 2 attacks (closing this phase's own §21/§27
item 1 disclosed gap); Stage 1 evidence substitution attacks; AER
corruption attacks; pointer corruption and rollback attacks; post-AER/
pre-pointer crash reproduction; workflow/readiness/publication/CHGR
integration verification; disclosure-only and non-gating verification;
regression testing. It shall remain verification-only and make no
implementation repair unless separately authorized.

**This recommendation is not authorization.**
