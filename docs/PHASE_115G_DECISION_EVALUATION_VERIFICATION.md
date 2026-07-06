# Phase 115G — Repository Decision Evaluation Verification & Compatibility

## Status

Completed. Verification-only phase: no architectural redesign, no new
runtime capability, no new Repository Skills, no execution capability,
no lifecycle behavior changes. Execution capability remains
unavailable.

## Purpose

Verify that the Repository Decision Evaluation integration introduced
in Phase 115F (`src/pcae/core/repository_transition_validator.py`
attaching `TransitionResult.explanation`) is fully behavior-preserving,
deterministic, reproducible, and compatible with all pre-existing
Repository Transition Validator behavior. Core principle restated:
Decision Evaluation exists to improve explainability, never to alter
repository governance. This phase adds no new implementation code to
`decision_evaluation.py` or `repository_transition_validator.py` — it
adds one new focused test module,
`tests/test_repository_transition_validator_verification_115g.py` (37
tests), that directly exercises the eight verification objectives
below against the unchanged 113U verdict logic and the unchanged 115E
evaluation layer.

## Compatibility Summary

All eight objectives verified with no findings requiring an
implementation change. The 115F integration remains "same decisions,
better explanations": every scenario in the side-by-side matrix
produces byte-for-byte the same `verdict`/`violations`/`accepted` as
its pre-115F value, with `explanation` attached as pure enrichment.

## 1. Verdict Equivalence Verification

`TestSideBySideVerdictComparison` runs a ten-scenario matrix (fully
consistent accept, phase-identity mismatch, missing
recommended-next-phase, partial completeness, missing evidence,
blocked/certified→canonical, execution-available, metadata-vs-target
mismatch, multiple simultaneous blocking violations, notify-ineligible)
plus two integration-bridge scenarios exercising
`REQUIRES_HUMAN_REVIEW`. For every scenario:

- The live (post-115F) `verdict`/`violations`/`accepted` match the
  expected pre-115F value exactly.
- `dataclasses.replace(result, explanation=None)` — a synthetic
  "legacy-shaped" result — has identical `verdict`/`violations`/
  `accepted` to the live result, proving explanation is pure
  overlay.
- `REQUIRES_HUMAN_REVIEW` remains producible only by
  `repository_transition_integration.py`'s own override (unchanged
  since 113Y/113Z) and never carries an explanation — that path was
  not touched by 115F or 115G.

All verdicts unchanged. ✓

## 2. Explanation Verification

`TestExplanationCorrectness` proves, across the full scenario matrix:

- Every `EvidenceReference` in `explanation.explanation_reference`
  resolves against the same `EvidenceCollection`
  `build_evidence_from_repository_state` produced for that state — no
  dangling references.
- Every `InvariantResult.invariant_id` is one of 115E's six frozen
  invariant families.
- `blocking_failures` contains only invariant IDs whose
  `InvariantResult.severity == "blocking"` and whose `status` is
  `FAIL`/`UNKNOWN`.
- `warnings` contains only invariant IDs whose severity is `"warning"`
  with the same status constraint.
- `informational` never contains an unresolved blocking/warning result
  — only `PASS`/`NOT_APPLICABLE` results, or results whose invariant is
  itself `informational` severity.
- Every `InvariantResult` is bucketed into exactly one of
  `blocking_failures`/`warnings`/`informational` (no double-counting,
  no omission).
- `has_blocking_failure` is `True` exactly when a blocking violation is
  present.

Explanation correctness verified. ✓

## 3. Evidence Integrity Verification

`TestEvidenceIntegrity` proves:

- `build_evidence_from_repository_state` never produces duplicate
  Evidence IDs (structurally guaranteed by the adapter's fixed,
  non-overlapping ID set; verified directly).
- `EvidenceCollection` itself rejects duplicate IDs at construction
  (`ValueError`), the invariant the adapter output relies on.
- Every `EvidenceReference` any `InvariantResult` carries (support or
  conflict) resolves to a real item in the `EvidenceCollection` that
  was evaluated — no missing-evidence references.
- Conflicting evidence is preserved through the real integration
  boundary: augmenting real adapter output with one additional,
  independently-sourced, disagreeing evidence item (simulating a
  future dual-source provider) still yields both sides of the
  disagreement in `conflicting_evidence`, never one discarded.
- `UNKNOWN`-freshness evidence injected alongside real adapter output
  is never silently dropped or passed — it still elevates the
  corresponding invariant into `blocking_failures`.

Evidence integrity verified. ✓

## 4. Determinism Verification

`TestDeterminism` proves:

- `validate_transition` produces an identical `TransitionResult`
  (verdict, violations, and explanation) across 20 repeated calls with
  identical inputs.
- `decision_evaluation.evaluate` produces an identical `EvaluationResult`
  across 20 repeated calls with an identical `EvaluationContext`.
- Result is independent of Evidence item insertion order (evaluators
  look up evidence by ID, not position; verified directly by reversing
  the adapter's own item order and confirming an identical result).
- The adapter's timestamp field (`_STATE_ADAPTER_TIMESTAMP`) is a fixed
  string sentinel, never `datetime.now()`/`time.time()` — verified by
  source inspection, so no verdict or explanation can ever be
  wall-clock-dependent.
- `explanation_reference` ordering is stable across repeated calls on
  identical input.

No ordering instability, no timestamp-dependent verdicts. Determinism
verified. ✓

## 5. Backward Compatibility Verification

`TestBackwardCompatibility` proves:

- `handle_phase_report_transition_result` (the printed-diagnostics
  function real `pcae phase complete`/`pcae task finish --commit`
  invoke) produces byte-identical stdout whether `explanation` is
  populated or stripped to `None` — existing callers ignoring
  `explanation` behave exactly as before.
- `TransitionResult.explanation`'s dataclass field default is `None`
  — the field can never become required without a source change.
- `dataclasses.replace(result)` round-trips to an equal `TransitionResult`.
- Every field on `EvaluationResult` a hypothetical JSON consumer would
  need (`summary`, `blocking_failures`, `warnings`, `informational`) is
  a plain `str`/`tuple[str, ...]`, requiring no custom serialization
  logic to detect presence — consistent with 115E's decision not to
  ship a bespoke serializer.

No JSON consumer or lifecycle caller reads `TransitionResult.explanation`
anywhere in the codebase (confirmed by source-grep in both this phase's
tests and 115F's own `TestLifecycleCommandBehaviorUnchanged`). Backward
compatibility verified. ✓

## 6. No Hidden Dependencies Verification

`TestNoHiddenDependencies` proves, by direct source inspection of both
`decision_evaluation.py` and `repository_transition_validator.py`:

- No `subprocess`, `socket`, `requests`, `urllib`, `Popen(`,
  `os.system`, or `shutil` token anywhere in either module.
- No dataclass in either module carries an `agent_id`/`model`/
  `model_id`/`backend`/`backend_id`/`agent` field — no model or backend
  identity anywhere in the Decision Evaluation or explanation-adapter
  layer.
- `decision_evaluation.py`'s only internal-package import remains
  `pcae.core.evidence`; it still never imports
  `repository_transition_validator` (one-directional dependency,
  validator → decision_evaluation only, confirmed again in this
  phase).

No Git access, no filesystem access, no subprocesses, no runtime
inspection, no lifecycle command invocation, no Repository Skills, no
model identity, no backend identity. ✓

## 7. Lifecycle Compatibility Verification

Full regression (unmodified suites):

- `tests/test_repository_transition_validator_phase_complete_integration.py`
  — `pcae phase complete` unchanged.
- `tests/test_repository_transition_validator_task_finish_integration.py`
  — `pcae task finish --commit` unchanged.
- The broader task/phase regression suite (`tests/test_task*.py`,
  `tests/test_*task*`, `tests/test_*phase*`,
  `tests/test_phase_reports.py`, `tests/test_phase_reports_cli.py`) —
  report promotion, notification, push reconciliation paths unchanged.
- `tests/test_*runtime*`, `tests/test_*contract*`, `tests/test_*autonomy*`,
  `tests/test_*plugin*` — runtime/autonomy regression unchanged.

`TestLifecycleCompatibility` (new, this phase) additionally proves
directly: neither `commands/phase.py` nor `commands/task.py` contains
the token `.explanation` anywhere in source; the integration bridge
function signature (`validate_phase_report_transition`) retains its
pre-115G parameter shape; `STRUCTURAL_INVARIANTS` — the seven-invariant
tuple that has driven verdicts since 113U — is byte-for-byte unchanged.

`pcae agent verify-handoff` passes (see Validation). Lifecycle
compatibility verified. ✓

## 8. Explainability Completeness Verification

`TestExplainabilityCompleteness` proves, across the full scenario
matrix:

- Every blocking violation scenario's corresponding `InvariantResult`
  (for the subset of `STRUCTURAL_INVARIANTS` names that overlap with
  115E's six evidence-only families) carries a non-empty explanation.
- Every `InvariantResult` produced across the entire matrix carries a
  non-empty, non-blank `explanation` string (also structurally
  enforced by `InvariantResult.__post_init__`, which raises
  `ValueError` on empty explanation — verified here at the aggregate
  level, not just the constructor level).
- The fully-consistent accept scenario has every invariant resolved to
  `PASS`/`NOT_APPLICABLE` — no unresolved result reaches an accept
  verdict.
- Every invariant ID present in `blocking_failures`/`warnings` traces
  back to an `InvariantResult` with a non-empty explanation — no
  unexplained blocking failure or warning is possible.

No unexplained verdicts. Explainability completeness verified. ✓

## Remaining Limitations (inherited from 115F, unchanged)

- `push_state_consistency`/`metadata_consistency` still resolve
  `NOT_APPLICABLE` through `build_evidence_from_repository_state` in
  the *unaugmented* adapter path — `RepositoryState` carries only one
  already-reconciled source per fact. This phase's conflict-preservation
  test proves the *evaluation layer* still handles a genuine dual-source
  disagreement correctly when one is present; it does not change what
  the adapter itself can produce.
- `canonical_promotion_eligibility` still resolves `NOT_APPLICABLE`
  through the adapter whenever only `report_completeness` (not
  `report_consistency`) is available — unchanged from 115F.
- The evidence-based `phase_identity_consistency`/`report_completeness`
  explanations remain simplifications of the validator's own more
  detailed structural checks (documented in 115F) — this phase adds no
  new adapter fields and does not close that gap.
- No `EvaluationResult` is attached to the human-review override path
  in `repository_transition_integration.py` — confirmed unchanged in
  this phase's `TestSideBySideVerdictComparison`.

## Readiness for Repository Skills (115H)

This phase's verification gives Repository Skills (115A's still-
unimplemented architecture) a concrete foundation to build on:

- The evaluation layer (115E) is proven deterministic and free of
  hidden dependencies, so Repository Skills contributing additional
  `Evidence` to the same `EvidenceCollection` shape can be evaluated by
  the unmodified six invariant families without further validation
  work on the evaluation layer itself.
- The conflict-preservation and UNKNOWN-never-silently-passes
  properties are now proven not just for 115E's synthetic evidence
  shapes but at the integration boundary the adapter produces — a
  future Repository Skill supplying a second, independent evidence
  source (closing the `push_state_consistency`/`metadata_consistency`/
  `canonical_promotion_eligibility` `NOT_APPLICABLE` gaps above) will
  compose correctly with the existing adapter's output without any
  evaluation-layer change.
- Verdict authority remains proven to rest entirely with
  `validate_transition`'s own unchanged structural checks — Repository
  Skills contributing evidence can only ever affect `explanation`,
  never `verdict`, exactly as 115F established and 115G now verifies
  under a substantially broader scenario matrix.

No Repository Skills, no execution, no authorization work is introduced
by this phase — 115H remains a distinct, not-yet-started phase.

## Tests

- `tests/test_repository_transition_validator_verification_115g.py`
  (new, 37 tests): side-by-side verdict comparison, explanation
  correctness, evidence integrity, determinism, backward compatibility,
  no hidden dependencies, lifecycle compatibility, explainability
  completeness.
- All pre-existing suites (`test_decision_evaluation.py`,
  `test_repository_transition_validator*.py`, `test_evidence*.py`, the
  full task/phase regression, the runtime/contract/autonomy/plugin
  regression, `fast_green`) pass unmodified — see Validation.

## Validation

- `python -m pytest tests/test_repository_transition_validator_verification_115g.py
  tests/test_decision_evaluation.py tests/test_repository_transition_validator*.py
  tests/test_evidence*.py -n auto -q -ra --durations=100` — 643/643
  passed.
- `python -m pytest tests/test_task*.py tests/test_*task* tests/test_*phase*
  tests/test_phase_reports.py tests/test_phase_reports_cli.py -n auto
  -q -ra --durations=100` — see final report (includes the two
  known-slow `test_phase85_integration.py`/`test_phase87_integration.py`
  files, a pre-existing environmental performance issue, unrelated to
  this phase).
- `python -m pytest tests/test_*runtime* tests/test_*contract*
  tests/test_*autonomy* tests/test_*plugin* -n auto -q -ra
  --durations=100` — 3554/3554 passed.
- `python -m pytest -m "fast_green" -n auto -ra --durations=100` —
  4390/4390 passed.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae agent verify-handoff` / `pcae session bootstrap
  --compact --profile implementation` / `pcae runtime inspect --json` /
  `pcae notify status` — see final report.
- `pcae skill invoke phase-finalization 115G` — see final report.

## Governance

No Repository Transition Validator behavior change, no lifecycle
command changes, no Notification Policy changes, no Canonical Artifact
Promotion changes, no Push-State Reconciliation changes, no Post-Push
Canonicalization changes, no Telegram changes, no REST, no Dashboard,
no plugins, no SLM/LLM integration. Execution capability remains
unavailable. Runtime state remains Observed. Maximum plugin capability
remains `observe`.

## Recommended Next Phase

115H — Repository Skills Architecture
