# Phase 115F — Repository Decision Evaluation Integration

## Status

Completed. Behavior-preserving explanation-enrichment integration
only: no Repository Skills, no execution, no authorization, no
Repository Transition Validator behavior changes, no lifecycle command
changes, no Notification Policy changes, no Canonical Artifact
Promotion changes, no Push-State Reconciliation changes, no Post-Push
Canonicalization changes, no Telegram changes, no REST, no Dashboard,
no plugins, no SLM/LLM integration.

## Purpose

Integrate 115E's Decision Evaluation with the Repository Transition
Validator (`core/repository_transition_validator.py`) in a
behavior-preserving way. Core rule: **same decisions, better
explanations**. The validator's own invariant checks (113U, unchanged)
remain the sole source of `TransitionVerdict`; Decision Evaluation is
wired in strictly as optional, additive enrichment of the returned
`TransitionResult`.

## Integration Scope

`src/pcae/core/repository_transition_validator.py` is the **only**
implementation file changed:

- Two new imports: `pcae.core.decision_evaluation` (`EvaluationContext`,
  `EvaluationResult`, `evaluate`) and `pcae.core.evidence` (`Evidence`,
  `EvidenceCollection`, and the frozen enums/`EvidenceProvenance`).
- `TransitionResult` gains one new field: `explanation: EvaluationResult
  | None = None`.
- A new adapter, `build_evidence_from_repository_state(state) ->
  EvidenceCollection`, maps already-computed `RepositoryState` fields
  into 115C `Evidence` items, reusing 115D's own Evidence IDs so 115E's
  invariant evaluators run completely unmodified.
- A new private helper, `_build_explanation(state) -> EvaluationResult |
  None`, calls the adapter then `decision_evaluation.evaluate(...)`,
  wrapped in `try`/`except Exception: return None` so enrichment
  failure can never break `validate_transition`.
- `validate_transition`'s own verdict-computing logic (`checks`,
  `violations`, `blocking`) is **unchanged, line for line** — only the
  three `return TransitionResult(...)` statements gained an
  `explanation=explanation` keyword argument.

Zero changes to `repository_transition_integration.py` (the real
`pcae phase complete`/`pcae task finish --commit` adapter, Phase
113Y/113Z), `commands/phase.py`, `commands/task.py`, or any
notification/push code. `handle_phase_report_transition_result` (the
function that prints validator diagnostics for those two real commands)
never reads `TransitionResult.explanation` — confirmed by grep in
`TestLifecycleCommandBehaviorUnchanged`.

`decision_evaluation.py` itself is **unchanged except for one bug fix
and a docstring update**:

- Bug fix: `evaluate_canonical_promotion_eligibility` treated "only one
  of its two required inputs present" as evaluable (defaulting the
  missing one to "not ok" and returning `FAIL`), rather than
  `NOT_APPLICABLE`. Found while designing the adapter (which
  legitimately has only `report_completeness` evidence to offer, never
  `report_consistency`) — always failing this invariant for a
  structural reason unrelated to real repository state would have been
  a misleading "better explanation." Fixed to require both inputs
  present to jointly evaluate; otherwise `NOT_APPLICABLE`. No existing
  115E test exercised the "one of two present" case, so this fix
  changes no previously-tested behavior.
- Docstring update: reflects that the validator now imports this
  module (one-directional) instead of claiming total isolation.

## Behavior-Preserving Guarantee

`validate_transition`'s verdict-computing code (the `checks` tuple and
the accept/reject/quarantine branching) is byte-for-byte unchanged from
113U. The explanation is computed once, after `violations` is already
final, and attached to whichever branch fires — it is never read by
any of the branching logic. Verified directly:

- All 36 pre-existing tests in `tests/test_repository_transition_validator.py`
  pass unmodified.
- `tests/test_repository_transition_validator_decision_evaluation_integration.py`
  re-runs 12 representative 113U scenarios (accept, phase-identity
  reject, missing-recommended-next-phase reject, partial-completeness
  quarantine, missing-evidence reject, blocked/certified canonical
  promotion, notify-ineligible reject, execution-available reject,
  agent-identity-in-payload no-op, determinism-across-repeated-calls,
  and both `notification_eligible`/`promotion_allowed` helpers) and
  asserts identical verdicts.
- The real lifecycle integration test suites —
  `tests/test_repository_transition_validator_phase_complete_integration.py`
  and `tests/test_repository_transition_validator_task_finish_integration.py`
  — pass completely unmodified, proving `pcae phase complete`/`pcae
  task finish --commit`'s actual printed output and behavior are
  unaffected.

## Verdict Compatibility Summary

| Scenario | Pre-115F verdict | Post-115F verdict |
| --- | --- | --- |
| Fully consistent state | Accept | Accept (unchanged) |
| Phase identity mismatch | Reject | Reject (unchanged) |
| Missing `recommended_next_phase` | Reject | Reject (unchanged) |
| Partial report completeness | Quarantine | Quarantine (unchanged) |
| Missing evidence (no tests/commits) | Reject | Reject (unchanged) |
| Blocked artifact -> Canonical | Reject | Reject (unchanged) |
| Certified artifact -> Canonical | Accept | Accept (unchanged) |
| Notify transition, ineligible state | Reject | Reject (unchanged) |
| Execution available | Reject | Reject (unchanged) |
| Agent identity in transition payload | No effect | No effect (unchanged) |

`TransitionVerdict.REQUIRES_HUMAN_REVIEW` remains unreachable from
`validate_transition`'s own structural checks, exactly as in 113U (the
verdict exists as a first-class value; only
`repository_transition_integration.py`'s separate human-review override
path constructs it, and that path was not touched).

## Explanation/Evidence Reference Summary

`TransitionResult.explanation`, when populated, is a full 115E
`EvaluationResult`: `invariant_results`, `summary`,
`blocking_failures`/`warnings`/`informational`, and
`explanation_reference` (deduplicated Evidence ID citations). Example,
for a fully-consistent `RepositoryState`:

```
verdict: ACCEPT
explanation.summary: "6 invariants evaluated: 3 pass, 0 fail, 0 unknown, 3 not_applicable."
explanation.blocking_failures: ()
explanation.explanation_reference: [E-report-002, E-metadata-002, E-report-003, E-runtime-002]
```

`push_state_consistency`, `metadata_consistency`, and (whenever only
`report_completeness` is available) `canonical_promotion_eligibility`
resolve `NOT_APPLICABLE` through this adapter — see Limitations below.

## Limitations

- **The adapter cannot produce cross-source conflicts.**
  `push_state_consistency`/`metadata_consistency` compare two
  *independently sourced* observations (e.g. git-derived vs
  declared-metadata pushed status); `RepositoryState` carries only one
  already-reconciled `pushed_status`/`origin_main_head_count` pair by
  the time it reaches the validator, so these two invariants always
  resolve `NOT_APPLICABLE` via this adapter. Conflict preservation
  itself is inherited unmodified from 115E and is proven still intact
  by `TestConflictingEvidencePreserved` (constructing evidence directly,
  the same shape a real dual-source provider would produce).
- **`canonical_promotion_eligibility` needs `E-report-005` (report
  consistency), which this adapter never provides** (`RepositoryState`
  has no equivalent field) — it resolves `NOT_APPLICABLE` whenever only
  `report_completeness` is known.
- **The evidence-based `phase_identity_consistency`/`report_completeness`
  explanations do not perfectly mirror the validator's own, more
  detailed structural checks.** The validator's
  `_check_phase_identity_consistency` compares three sources
  (`active_task_phase_id`, `metadata_phase_id`,
  `lifecycle_current_phase_id`); the adapter's evidence-based version
  compares two (`phase_id`, `metadata_phase_id`). The validator's
  `_check_report_completeness` also falls back to checking
  `test_results`/`commits` presence; the adapter's version reads only
  the `report_completeness` string. These are documented, intentional
  simplifications of the *explanation*, not of the *verdict* — the
  verdict is always driven by the validator's own, unsimplified checks.
- **`evaluation_timestamp`/`repository_snapshot_reference` are
  deterministic placeholders**, not live timestamps — `validate_transition`
  is documented as a pure function (same input always produces the same
  output, including `explanation`), so injecting wall-clock time would
  have broken that guarantee for no benefit.
- No `EvaluationResult` is ever attached to the human-review override
  path in `repository_transition_integration.py`
  (`validate_phase_report_transition`'s own direct `TransitionResult`
  construction) — that path was not touched and remains
  `explanation=None`.

## Future Repository Skills Integration

This phase deliberately implements enrichment only. A future phase
(not 115F) could:

- Replace the narrow `RepositoryState`-based adapter with real 115D
  Evidence Providers, once a lifecycle command is prepared to pay the
  cost of live git/runtime/report/metadata collection at validation
  time (currently avoided per Objective 5's "no broad new I/O").
- Let Repository Skills (115A's architecture, still unimplemented)
  contribute additional Evidence to the same `EvidenceCollection` this
  adapter builds, without changing verdict authority.
- Surface `TransitionResult.explanation` in `pcae phase complete`/`pcae
  task finish --commit`'s printed diagnostics, once there's an actual
  product need for humans to see it (a lifecycle command change,
  explicitly out of scope here).

## Tests

- `tests/test_repository_transition_validator_decision_evaluation_integration.py`
  (32 new tests): verdict preservation, explanation presence, evidence
  references, UNKNOWN-never-passes, conflict preservation, backward
  compatibility, lifecycle-command non-interference, no execution
  capability introduced.
- `tests/test_decision_evaluation.py`: 2 tests updated
  (`TestNoValidatorIntegration`) to reflect the new, intentional
  one-directional dependency (validator imports decision_evaluation;
  decision_evaluation never imports the validator, still verified).
- All existing suites pass unmodified (see Validation).

## Validation

- `python -m pytest tests/test_decision_evaluation.py
  tests/test_repository_transition_validator*.py tests/test_evidence*.py
  -n auto -q -ra --durations=100` — see final report.
- `python -m pytest tests/test_task*.py tests/test_*task* tests/test_*phase*
  tests/test_phase_reports.py tests/test_phase_reports_cli.py -n auto
  -q -ra --durations=100` — see final report (includes the two known-slow
  `test_phase85_integration.py`/`test_phase87_integration.py` files, a
  pre-existing environmental performance issue, unrelated to this
  phase).
- `python -m pytest tests/test_*runtime* tests/test_*contract*
  tests/test_*autonomy* tests/test_*plugin* -n auto -q -ra
  --durations=100` — see final report.
- `python -m pytest -m "fast_green" -n auto -ra --durations=100` — see
  final report.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae agent verify-handoff` / `pcae session bootstrap
  --compact --profile implementation` / `pcae runtime inspect --json` /
  `pcae notify status` — see final report.
- `pcae skill invoke phase-finalization 115F` — see final report.

## Governance

No Repository Transition Validator *behavior* change, no lifecycle
command changes, no Notification Policy changes, no Canonical Artifact
Promotion changes, no Push-State Reconciliation changes, no Post-Push
Canonicalization changes, no Telegram changes, no REST, no Dashboard,
no plugins, no SLM/LLM integration. Execution capability remains
unavailable. Runtime state remains Observed. Maximum plugin capability
remains `observe`.

## Recommended Next Phase

115G — Repository Decision Evaluation Verification & Compatibility
