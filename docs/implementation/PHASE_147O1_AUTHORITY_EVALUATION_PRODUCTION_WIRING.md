# Phase 147O.1: Authority Evaluation Production Wiring

## 1. Executive Summary

Phase 147O found the Authority Evaluation Integration chapter (147G–147N)
structurally complete and independently verified, but not operationally
reachable: no production PCAE lifecycle path ever constructed or invoked
`AuthorityEvaluationService` (AES). This finding, **AESIC-O-01**, blocked
chapter certification.

This phase closes AESIC-O-01. `pcae.commands.decision_session.
build_application_context` — the sole production `SessionApplicationService`
composition site — now constructs a real AES from persistent, filesystem-derived
configuration and threads it through Stage 1 (`decision-session confirm`) and
Stage 2 (`decision-session readiness`, already implemented by Phase 147M but
previously dead code on every production path). Real AER and canonical-pointer
persistence now occurs; CHGR's `authority_basis_claimed` is now populated from a
real, current-effective Stage 2 citation end-to-end through
`governance-record publish`.

One genuine, previously-latent defect was found and repaired in-scope:
`pcae.interactive_workflow.serialization.publication_handoff_schema` never
serialized `authority_evaluation_ref`/`citation_text` — fields Phase 143O/145F's
own `PublicationReadinessPackage` model already defined, but which stayed dead
in every persisted artifact because nothing before this phase ever populated
them in production. This was discovered by running the real end-to-end CLI path
(not merely unit-testing the service layer in isolation) and is now repaired,
additively, preserving every pre-existing on-disk package's digest exactly.

**Overall Verdict: AUTHORITY EVALUATION PRODUCTION WIRING IMPLEMENTED WITH
NON-BLOCKING FINDINGS.**

## 2. Scope

In scope: one composition root, one enablement model, Stage 1/Stage 2
production wiring, the publication-handoff serialization repair, minimal
diagnostics, `.pcae/policy.toml`'s one additive edge, and focused tests.

Out of scope (per this phase's authorization): AESIC-001/AEM-001/AEMIC-001/
IWC-001/IWPC-001/PEC-001/CHGR-001 amendment, AES redesign, moving evaluation
into `PublicationCoordinator`, authority/execution gating, runtime-capability
expansion, AESIC-N-01 repair (reviewed for reachability only, §24), broad CLI
expansion, chapter certification.

## 3. AESIC-O-01 Reconstruction

Re-derived directly from the production call graph, not from Phase 147O's
prose: `build_application_context` (`src/pcae/commands/decision_session.py`,
pre-phase line 208) called `SessionApplicationService(session_coordinator)`
with no `authority_evaluation_service` argument — the only production
instantiation site of that class anywhere in the repository. A repo-wide
search confirmed `AuthorityEvaluationService(`/`FilesystemAuthorityRegistry(`/
`AuthorityEvaluationRecordStore(` were constructed only inside
`tests/test_phase_147m_*.py`/`tests/test_phase_147n_*.py`. Stage 1/Stage 2 were
fully implemented and independently verified as *methods*, but had zero real
callers.

## 4. Existing Production Gap

Confirmed, additionally, that even had AES been constructed, two further gaps
would have prevented a real end-to-end path:

1. **No Stage 1 call site.** `SessionApplicationService.evaluate_authority_stage_1`
   existed (Phase 147M) but no CLI handler called it.
2. **No persistence path for Stage 2's own output.** `construct_readiness_package`
   already built `authority_evaluation_ref`/`citation_text` correctly in
   memory (Phase 147M), but `publication_handoff_schema.py`'s `to_payload`/
   `from_payload` never carried them — so even after wiring composition, a
   persisted-then-reread readiness package would have silently lost this data
   (discovered by this phase's own end-to-end reproduction, §18).

## 5. Composition Root

`build_application_context()` (`src/pcae/commands/decision_session.py`) is
reused unchanged as the one composition root — no second container was
introduced. It now calls `pcae.aesic.composition.build_authority_evaluation_service()`
and passes the result as `SessionApplicationService(coordinator,
authority_evaluation_service=...)`. This mirrors the existing idiom exactly:
plain constructor calls, default-argument `.pcae/`-relative `Path` roots, no
config file, no environment variable, constructed fresh per CLI invocation
(no module-level singleton).

`pcae.commands.aesic_status` (the new diagnostics command) is the only other
caller of `pcae.aesic.composition`; it never constructs AES itself, only reads
`describe_authority_evaluation_configuration()`.

## 6. Configuration Model

No config file, no environment variable — consistent with AES's own contract
(§7's Registry: "no git I/O", restart-durable, `.pcae/`-relative) and with
every other collaborator `build_application_context` already constructs.
Three filesystem roots, all pre-existing defaults owned by Phase 147M/147N's
own modules:

| Concern | Root (default) |
|---|---|
| Decision Templates | `.pcae/authority-evaluation/templates/` |
| Authority Registry | `.pcae/authority-evaluation/registry/` |
| AER + canonical pointer | `.pcae/authority-evaluation/records/` |

Persistent (ordinary files under `.pcae/`, survive process/subshell
boundaries), inspectable (`pcae aesic status`), deterministic (same
filesystem state → same decision, every call), channel-agnostic, no secret
material, safe when absent (§7), fail-closed on malformed input at read time
(pre-existing AES/Registry/store behavior, unchanged).

## 7. Enablement Semantics

**Model: automatically enabled when complete configuration exists.**
Enablement is a single, filesystem-derived signal: at least one Decision
Template file (`*.json`) exists under the template root.

Rationale: deploying a Decision Template is the one action an operator must
take before *any* evaluation can succeed even once AES is wired in
(`DecisionTemplateResolution.resolve` raises `DecisionTemplateNotFoundError`
for every `(template_ref, template_version)` with no deployed template — this
is unconditional and applies to *every* session, since no repository ships
with pre-existing templates). Gating on Registry population instead was
rejected: an empty/absent Registry is already a fully safe, contractually
defined "no declaration" outcome (`FilesystemAuthorityRegistry.resolve`
returns `None`, never raises, for a missing file — AESIC-REQ-041), so gating
on it would be over-conservative and inconsistent with the contract's own
distinction between "no declaration" (safe, non-fatal) and "no template"
(hard failure).

| State | Reason | Behavior |
|---|---|---|
| Template root absent | `template_root_absent` | Disabled (`None`, pre-147O.1 default) |
| Template root empty | `template_root_empty` | Disabled |
| Template root exists, not a directory | `template_root_not_a_directory` | Disabled, safe (never a crash) |
| Template root unreadable (`OSError`) | `template_root_unreadable` | Disabled, safe |
| ≥1 template file present | `template_root_populated` | Enabled — AES constructed for real |

Default (absent configuration) preserves every pre-147O.1 workflow exactly
(AESIC-REQ-109). Partial configuration (a template exists for some
`(template_ref, template_version)` pairs but not others) is *not* separately
gated at the composition level — once enabled, a session whose specific
template is undeployed hits the pre-existing, already-certified Stage
2-failure path (§20; unchanged, not this phase's to alter). Upgrade/rollback
for existing repositories: disabled by default (no templates ship), so
upgrading to this phase changes nothing until an operator deliberately
deploys a template — an explicit, auditable, reversible (delete the
directory) opt-in, not an automatic behavior change.

## 8. Registry Provisioning

Unchanged from Phase 147M: `FilesystemAuthorityRegistry(root=".pcae/authority-evaluation/registry")`,
one file per `(template_ref, template_version)` at
`<root>/<template_ref>/<template_version>.json`. Missing directory/file →
`None` (no declaration, safe). Malformed JSON/shape → `AuthorityRegistryCorruptError`
(propagates through AES's own translated exception, unchanged, fail-closed).
No fabrication: the composition root never authors declarations; that remains
`FilesystemAuthorityRegistry.write_declaration`'s authoring-side-only
responsibility, never called by production wiring.

## 9. Decision Template Provisioning

Unchanged from Phase 147M: `.pcae/authority-evaluation/templates/<template_ref>/<template_version>.json`,
read by `DecisionTemplateResolution`/`read_template`. Missing → `DecisionTemplateNotFoundError`.
Malformed → `DecisionTemplateMalformedError`. Empty `eligible_authority` →
`DecisionTemplateCitationEmptyError`. All three propagate through AES's own
closed translation (`DecisionTemplateResolutionFailedError`); this phase adds
no new template-store behavior, only the enablement check that reads its
*presence* (§7), never its content, at composition time.

## 10. AER and Pointer Storage

Unchanged from Phase 147M: `AuthorityEvaluationRecordStore(root=".pcae/authority-evaluation/records")`,
two-tier layout (`records/<package_id>/<evaluation_id>.json` immutable,
`pointers/<package_id>.json` atomic-replace). This phase adds no new storage
behavior — only real production callers.

## 11. Stage 1 Wiring

`run_decision_session_confirm` (`src/pcae/commands/decision_session.py`) now
calls `context.session_service.evaluate_authority_stage_1(session_id)` before
`record_confirmation`, satisfying AESIC-REQ-062/063 ("at or before
Confirmation"). Advisory-only: the result is disclosed in the command's
output (`authority_evaluation_stage_1: eligible|ineligible|indeterminate|
not_configured|evaluation_failed`) and otherwise discarded — it is never
consulted before calling `record_confirmation`, so it cannot gate the
transition. A raised `AuthorityEvaluationIntegrationError` (any Stage 1
evaluation failure — missing Registry, malformed template, etc.) is caught at
this CLI layer specifically (not inside `SessionApplicationService`, which
already leaves that decision to its caller by design), logged, and confirmed
regardless. Session transitions are otherwise untouched.

## 12. Stage 1 Result Transport

Confirmed and preserved: AESIC-001 v1.3 intentionally permits Stage 1 result
loss across a process boundary (AESIC-REQ-122/125's restart matrix — "after
Stage 1, before Confirmation" is an explicitly non-error state). Since every
`pcae decision-session confirm` and every `pcae decision-session readiness`
invocation is its own OS process (`ApplicationContext` is "constructed fresh
per CLI invocation", per its own docstring), `stage_1_result` cannot and does
not survive from `confirm` to `readiness` under real CLI usage — it is
computed, disclosed, and discarded within a single process. `readiness`
therefore always calls `evaluate_stage_2(..., stage_1_result=None)`, a fully
contract-compliant path, not a gap. No new durable Stage-1-only artifact was
introduced.

## 13. Readiness Wiring

Unchanged: `SessionApplicationService.construct_readiness_package` (Phase
147M) already built `authority_evaluation_ref` (`record_id`, `record_digest`,
`record_family`) and `citation_text` reference-only, never embedding the full
AER, with default-`None` fields when AES is absent or the outcome is not
`ELIGIBLE`. This phase makes the block reachable (real `self._authority_evaluation_service`)
and repairs the one gap that prevented it from surviving to disk (§4 item 2,
§15).

## 14. Stage 2 Wiring

Unchanged: `evaluate_stage_2` runs inside `construct_readiness_package`,
strictly after Confirmed-state/orchestration-completeness checks, strictly
before `PublicationHandoff().build_package(...)`, and strictly outside
`PublicationCoordinator.execute()`'s own transaction (§16). Handles
idempotent no-op reuse, supersession, and `CanonicalPointerUpdateFailedError`
exactly as Phase 147M/147N implemented and 147N independently verified — this
phase changes none of that logic, only makes it reachable.

## 15. Publication Handoff

**Repaired** (§4 item 2): `pcae.interactive_workflow.serialization.
publication_handoff_schema.to_payload`/`from_payload` now serialize
`authority_evaluation_ref`/`citation_text`. Additive and digest-stable: the
two keys are included in the payload dict *only* when at least one is
non-`None`; a package with neither (every legacy package, and every package
built for a session where Authority Evaluation stayed disabled) produces the
byte-identical payload dict — and therefore the byte-identical digest — as
before this phase existed. `from_payload` defaults both to `None` via
`.get()`, so a legacy on-disk file (missing the keys entirely) deserializes
unchanged. No `schema_version` bump: this is a strict superset of the
existing wire format, not a new version. Regression-tested (§27).

## 16. Publication Coordinator Boundary

Verified unchanged and untouched by this phase: `PublicationCoordinator`
(`src/pcae/governance/publication/coordinator.py`) imports nothing from
`pcae.aesic`/`pcae.authority_evaluation` (AST-verified in
`TestProductionReachability::test_publication_coordinator_never_touches_aesic`).
It constructs no AES, invokes no evaluator, resolves no Registry entry,
validates no Stage 1 evidence, persists no AER, updates no pointer, and makes
no publication decision based on evaluation outcome — all validated
integration data is prepared by `construct_readiness_package` *before*
`PublicationCoordinator.execute()` is ever called.

## 17. CHGR Wiring

Unchanged: `build_publication_record`
(`src/pcae/governance/publication/record.py`) already populated
`authority_basis_claimed` from `package.citation_text` whenever
`authority_evaluation_ref` is also present, else omits the field with a
documented limitation string. This phase makes it reachable in production,
tested both with (`TestProductionReachability::test_chgr_receives_current_effective_citation`)
and without (`TestBackwardCompatibility::test_publish_succeeds_without_authority_evaluation_configured`)
Authority Evaluation configured.

## 18. Supported End-to-End Path

Manually reproduced through the real CLI, single-process-per-command, with no
manual AES object assembly beyond authoring one Decision Template and one
Registry declaration (the operator-side, out-of-AES-scope authoring actions
themselves, per AESIC-001 §6.4/§7's own carve-out):

1. `.pcae/authority-evaluation/templates/demo-template/1.0.json` deployed →
   `pcae aesic status --json` reports `enabled: true`.
2. `pcae decision-session create/evidence/select/preview` → ordinary,
   unaffected by this phase.
3. `pcae decision-session confirm` → `authority_evaluation_stage_1: eligible`
   (Registry declaration present) in the command's own output; session
   transitions to `Confirmed` regardless.
4. `pcae decision-session readiness` → Stage 2 runs; `pcae aesic status
   --package-id <id> --json` shows a real, persisted `AuthorityEvaluationRecord`
   (`canonical_evaluation_result: eligible`).
5. `pcae governance-record publish <package-id> --operator-id <id>` succeeds;
   the resulting CHGR artifact's `authority_basis_claimed` equals the
   Decision Template's `eligible_authority` text verbatim.
6. Restart/retry: `ensure_readiness_package`/`resume_publication`'s existing
   idempotent-by-key logic (Phase 145F/145H.2, unmodified) is what a second
   CLI invocation (a fresh process, fresh composition root) exercises — this
   phase adds no new state to reconcile.

This exceeds "a test calling the AES class directly": every step above is a
separate `pcae` CLI invocation exercised as a real command, not an in-process
method call on a hand-assembled object.

## 19. Backward Compatibility

Verified, all in isolated `tmp_path` repositories with no Authority
Evaluation configured (the pre-147O.1 default):
`decision-session confirm` still succeeds and reports
`authority_evaluation_stage_1: not_configured`;
`decision-session readiness`/`governance-record publish` still succeed
end-to-end with `authority_basis_claimed` absent from the resulting CHGR;
legacy-shaped persisted `PublicationReadinessPackage` payloads (missing the
two new keys entirely) deserialize with both fields `None`
(`TestBackwardCompatibility::test_legacy_stored_payload_deserializes_with_none_evaluation_fields`);
round-tripping a package with no evaluation data produces an
idempotent, byte-identical payload
(`test_round_trip_payload_idempotent_for_legacy_shaped_package` — the exact
regression this phase's own serialization repair, §15, guards against). No
migration was introduced or required.

## 20. Failure Semantics

| Condition | Behavior |
|---|---|
| Configuration absent/empty/non-directory/unreadable | AES not constructed (`None`); every workflow unaffected (§7) |
| Registry unavailable/corrupt | Propagates through AES's translated errors at Stage 1 (caught, logged, confirm proceeds) or Stage 2 (propagates to `internal_error`, unchanged pre-existing Stage 2 semantics — readiness fails closed, matching 147M/147N's already-certified behavior) |
| Decision Template missing/malformed | Same as above — Stage 1: caught/logged/non-gating; Stage 2: fails closed (tested: `TestFailureSemantics`) |
| AER store unavailable | Unchanged `OSError`/store-layer behavior (147M/147N) |
| Pointer update failure | Unchanged `CanonicalPointerUpdateFailedError`, AER already durably committed, safe retry (147M/147N) |
| Pointer corruption | Unchanged `CanonicalPointerCorruptError`, fail-closed (147M/147N) |
| CHGR citation unavailable | Unchanged: field omitted with a documented limitation string, never fabricated (144C/145F) |

Stage 1 failures never propagate past the CLI's confirm handler (non-gating,
§11). Stage 2 failures are *not* newly softened by this phase — they retain
the existing, already-certified fail-closed behavior (readiness construction
raises, `governance-record`/`decision-session` CLI layers map it to a
governed `internal_error`, never a raw traceback, never misleading citation
data). Retry is safe in every case (idempotent-by-key, unmodified).

## 21. Diagnostics and Audit

`pcae aesic status [--package-id <id>] [--json]` (new, `src/pcae/commands/aesic_status.py`):
reports `enabled`, `reason`, `template_root`, `registry_root`, `aer_store_root`,
a static Stage 1 disclosure note (§12: not persisted, by design), and, when
`--package-id` is given, the package's current-effective Stage 2 summary via
the pre-existing (never-wired) `pcae.aesic.diagnostics.summarize_package`
(Phase 147M/147N). Read-only, mutation-free (tested:
`TestDiagnostics::test_status_never_mutates`); no sensitive content exposed
(template/registry/store paths and evaluation *results* only, never raw
declaration/template content).

## 22. Security

No untrusted configuration path traversal (all roots are fixed, code-level
defaults — no path is ever accepted from CLI input or environment). No
symlink-following changes. No cross-repository state reuse (all paths
`.pcae/`-relative, resolved against CWD exactly like every sibling store). No
cross-session Stage 1 substitution introduced (Stage 1 never leaves its
originating process, §12). No Registry/template substitution (fixed default
roots, unchanged resolution logic). No pointer cross-key exposure introduced
(§24). No broad file-permission assumptions beyond what 147M/147N already
required. No ambient environment injection (zero `os.environ`/`getenv` calls
anywhere in `pcae.aesic.composition`/`pcae.commands.aesic_status`). No silent
fallback to mutable/temporary storage — enablement failure means "disabled",
never "fall back to `/tmp`". Disclosure-only semantics preserved throughout
(§20).

## 23. Concurrency and Restart

Each CLI invocation is a fresh process with a fresh composition root
(`build_application_context`, unmodified discipline) — `build_authority_evaluation_service`
re-derives its enablement decision from current filesystem state on every
call, with no caching and no process-global singleton, so a Stage 1 in one
process and Stage 2 in a later process, or two processes racing Stage 2 for
the same `package_id`, reconstruct identical dependencies and hit the
unmodified idempotent-no-op/supersession/last-write-wins pointer semantics
Phase 147M/147N already implemented and 147N already stress-tested (fresh-process
reproduction, multi-generation supersession, crash-between-AER-and-pointer
recovery — see `tests/test_phase_147n_*.py`'s `TestCrashRecovery`/
`TestConcurrency`/`TestSupersessionMultiGeneration`). This phase introduces no
new concurrency surface; it only makes the existing, already-verified surface
reachable.

## 24. AESIC-N-01 Containment

Reviewed against the exact question this phase's authorization poses: does
production wiring introduce a new caller able to supply mismatched compound
`(package_id, evaluation_id)` keys to `read_canonical`/`read_record`?

- `AuthorityEvaluationRecordStore.read_canonical(self, package_id: str)` takes
  exactly one key, verified by signature introspection
  (`TestAesicN01Containment::test_diagnostics_read_canonical_call_is_single_key_only`)
  — no caller of this method, old or new, can supply two independently
  chosen keys through its public signature.
- AES's own `evaluate_stage_2` call (`src/pcae/aesic/service.py:248`) is
  unchanged — still calls `read_canonical(package_id)` with its own method
  argument, never storage read-back data.
- The one new caller this phase adds, `pcae aesic status --package-id`, makes
  the identical single-argument call via `summarize_package` — verified by
  source inspection that neither `pcae.aesic.composition` nor
  `pcae.commands.aesic_status` calls `write_pointer`/`write_record` at all
  (`TestAesicN01Containment`'s remaining two tests).

**Conclusion: production wiring does not increase AESIC-N-01's reachability.**
It remains reachable only via direct filesystem tampering with a stored
pointer file's *embedded* content (unchanged from 147N/147O's own
disposition). No repair was performed in this phase; repair remains
recommended as a separately authorized 147O.2-adjacent follow-up, consistent
with 147O's own recommendation.

## 25. Architecture Policy

`.pcae/policy.toml`: one additive edge, `commands = [..., "aesic"]`, narrowly
scoped and documented in-place (comment explains exactly which two modules —
`pcae.commands.decision_session`, `pcae.commands.aesic_status` — use it and
exactly which `pcae.aesic.*` symbols they import). No other zone rule
changed. Matched against actual imports (`test_policy.py` passes unchanged;
97 tests including this phase's own architectural-boundary tests all pass).
Enforcement mode remains `advisory`, unchanged.

## 26. Requirement Traceability

| AESIC-O-01 obligation | AESIC-001 requirement(s) | Production entry point | Implementation | Test evidence | Status |
|---|---|---|---|---|---|
| AES constructed automatically | REQ-014/015/017/048/109 | `decision_session.build_application_context` | `pcae/aesic/composition.py` | `TestComposition` | Closed |
| Stage 1 reachable, advisory-only | REQ-062/063/091 | `decision-session confirm` | `decision_session.py::run_decision_session_confirm` | `TestProductionReachability`, `TestNonGating`, `TestFailureSemantics` | Closed |
| Stage 1 transport (no cross-process persistence) | REQ-122/123/125 | n/a (in-process only) | same as above | §12 reasoning, `test_stage_1_unreachable_without_configuration` | Closed |
| Readiness reference-only integration | REQ-058/059 | `decision-session readiness` | `session_service.py::construct_readiness_package` (unmodified) + serialization repair | `TestProductionReachability::test_stage_2_reachable_and_aer_persisted` | Closed |
| Stage 2 reachable, real persistence | REQ-019/054/086/119/120/130/131 | `decision-session readiness` | `service.py::evaluate_stage_2` (unmodified, now reachable) | `TestProductionReachability` | Closed |
| Publication handoff carries integration output | (implementation gap, not a numbered REQ) | `publication_handoff_schema.py` | `to_payload`/`from_payload` additive repair | `TestBackwardCompatibility` | Closed |
| Publication Coordinator isolation preserved | REQ-025/026 | n/a (negative requirement) | `coordinator.py` (unmodified) | `test_publication_coordinator_never_touches_aesic` | Closed |
| CHGR citation-only | REQ-058 | `governance-record publish` | `record.py::build_publication_record` (unmodified, now reachable) | `test_chgr_receives_current_effective_citation` | Closed |
| Backward compatibility | REQ-109 | all commands | composition default `None`, additive serialization | `TestBackwardCompatibility` | Closed |
| AESIC-N-01 non-expansion | (147N/147O disposition) | `pcae aesic status` | `aesic_status.py`, `composition.py` | `TestAesicN01Containment` | Closed, unrepaired (deferred) |

## 27. Tests

`tests/test_phase_147o1_authority_evaluation_production_wiring.py` — 27
tests: `TestComposition` (6), `TestProductionReachability` (6),
`TestBackwardCompatibility` (4), `TestNonGating` (2), `TestFailureSemantics`
(2), `TestDiagnostics` (4), `TestAesicN01Containment` (3). All construct
dependencies exclusively through `build_application_context`/CLI handlers —
no test bypasses the composition root to hand-assemble AES for a production
code path (the one place `AuthorityEvaluationService` is imported directly,
`TestComposition::test_enabled_when_template_deployed`, only asserts
non-`None`, never substitutes for the composition root itself).

Baselines re-run, exact counts:

- `python -m pytest -m fast_green -n auto -q`: **4391 passed** (matches
  pre-phase baseline exactly).
- `python -m pytest tests/test_phase_147g_*.py tests/test_phase_147h_*.py
  tests/test_phase_147m_*.py tests/test_phase_147n_*.py -q`: **306 passed**
  (matches pre-phase baseline exactly).
- Combined with this phase's own suite: **333 passed**.
- Focused cross-cutting sweep (`interactive_workflow`, `readiness`,
  `publication`, `chgr`, `decision_session`, `governance_record`, `145g`,
  `145h`, `policy`, `architecture` keyword filter): **4259 passed, 3 skipped,
  10 failed** — all 10 failures independently reproduced as pre-existing and
  unrelated on unmodified `main` (wheel/sdist packaging tests requiring a
  full `python -m build`, plus one stray pre-existing `src/pcae/advisory/`
  directory-count assertion), identical to the failure set 147O itself
  already disclosed.

## 28. Limitations

- `docs/COMMANDS.md` is a hand-maintained document (not argparse-introspected)
  and does not yet list `pcae aesic status` — consistent with the
  pre-existing, disclosed gap that `pcae authority` (Phase 137K) was never
  added either. Not repaired here (broad CLI-documentation sweep is out of
  this phase's narrow scope); regenerating via `pcae docs commands --force`
  produced no diff, confirming the generator does not introspect these
  commands at all.
- Stage 2 failure semantics (Registry/template failures during
  `construct_readiness_package`) remain exactly as fail-closed as Phase
  147M/147N already certified — this phase does not soften them, meaning an
  operator who enables Authority Evaluation repo-wide but has not deployed
  templates for every `(template_ref, template_version)` pair their sessions
  use will see `readiness` fail closed for the undeployed ones. This is
  disclosed, intended, pre-existing behavior, not a new defect.
- AESIC-N-01 remains unrepaired (deferred, per authorization, to a
  separately authorized follow-up — §24).
- Concurrency was validated via the pre-existing Phase 147N test suite
  (unit-level, in-process); this phase did not add new multi-process
  concurrency tests beyond the manual end-to-end reproduction (§18), matching
  147N's own disclosed single-process-concurrency-test limitation.

## 29. No-Go Confirmations

No amendment to AESIC-001, AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or
CHGR-001. No AES redesign — `AuthorityEvaluationService`, `DecisionTemplateResolution`,
`FilesystemAuthorityRegistry`, and `AuthorityEvaluationRecordStore` are
byte-for-byte unchanged from Phase 147M. No Registry lookup moved into the
evaluator. No move of Stage 2 into `PublicationCoordinator.execute()`
(verified, §16/§24). No confirmation/readiness/publication/execution gating
introduced (verified, §11/§19/§20). No runtime-execution capability enabled
(`pcae runtime inspect` unchanged: Observed / observe / unavailable, verified
before and after). No unrelated CLI commands added — the one new command,
`pcae aesic status`, is exactly this phase's own required diagnostics
surface. No broad runtime plugins. No unnecessary AER/pointer storage
rewrite (unchanged). No chapter certification claimed by this phase.

## 30. Overall Verdict

**AUTHORITY EVALUATION PRODUCTION WIRING IMPLEMENTED WITH NON-BLOCKING
FINDINGS.**

All required success criteria are met: one supported production composition
path exists and was exercised end-to-end through real CLI invocations; AES is
constructed automatically from persistent, filesystem-derived configuration;
Stage 1 is reachable through Interactive Workflow (`confirm`); Stage 2 is
reachable through the publication lifecycle (`readiness`); real AER and
canonical-pointer persistence is used and verified; CHGR receives
current-effective citation data end-to-end; legacy workflows remain
compatible (verified with dedicated regression tests); missing configuration
behaves safely (disabled, unchanged default); restart reconstructs
dependencies (fresh composition root per process, verified against 147N's
existing restart/crash-recovery suite); disclosure-only and non-gating
guarantees remain intact; runtime remains Observed / observe / unavailable;
AESIC-N-01 is demonstrably contained, not repaired (deferred per
authorization); comprehensive tests pass (4391 fast_green + 306 chapter + 27
new = all green, plus a clean cross-cutting sweep against only pre-existing,
unrelated failures).

Non-blocking findings: the publication-handoff serialization gap (§4 item 2,
§15) was discovered and repaired within this phase's own scope, as required
to make Stage 2's already-implemented output actually reach disk — disclosed
here rather than treated as silent scope creep. `docs/COMMANDS.md` staleness
(§28) is disclosed and deferred.

## 31. Recommended Next Phase

**147O.2 — Authority Evaluation Production Wiring Independent Verification.**
Verification-only, per this phase's own authorization: independently
re-derive and confirm supported production entry-point reachability,
composition-root correctness, persistent configuration, Registry/template
provisioning, Stage 1 invocation through Interactive Workflow, Stage 1
transport to Stage 2, Stage 2 invocation through the publication lifecycle,
AER/canonical-pointer persistence, restart/recovery across fresh processes,
CHGR citation-only integration, backward compatibility, non-gating behavior,
runtime preservation, and AESIC-N-01 containment (or, if a separately
authorized repair phase intervenes first, the repair). Only after a
successful 147O.2 should operational readiness and chapter certification be
reassessed, in 147O.3.
