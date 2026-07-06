# Phase 115N — Repository Skills Integration Verification & Compatibility

## Status

Completed. Verification only: no Repository Skill modified, no
Evidence Provider modified, no Decision Evaluation modified, no
Repository Transition Validator modified, no lifecycle command
modified, no Notification Policy modified, no Canonical Artifact
Promotion modified, no Push-State Reconciliation modified, no
Post-Push Canonicalization modified, no new Repository Skill, no
AI/SLM/LLM skill, no DeepSeek integration, no execution capability.

## Purpose

Re-prove, from a fresh angle and with new focused tests, that 115M's
Repository Skills evidence-acquisition adapter
(`pcae.core.repository_skills_integration`) is completely
behavior-preserving, and investigate the one pre-existing fast_green
failure 115M's final report carried forward unresolved.

## Evidence Equivalence Summary

`TestEvidenceEquivalencePerSkill` (new) proves equivalence at a finer
grain than 115M's own suite: for each of the four deterministic skills
individually (`git_repository_skill`, `runtime_repository_skill`,
`report_repository_skill`, `metadata_repository_skill`), a
single-skill registry's output via
`collect_evidence_via_repository_skills` matches the corresponding
Evidence-ID-prefixed subset of `collect_evidence_via_evidence_providers`'s
full output -- same IDs, same observed values, same
freshness/confidence/determinism. Verified against a synthetic
repository and the real project root, and stable across 5 repeated
invocations. **Result: equivalent, per skill.**

## Decision Evaluation Compatibility

`TestDecisionEvaluationCompatibility` proves, on both a synthetic
"mostly UNKNOWN evidence" repository and the fully-populated real
project root: identical `invariant_results`, identical
`blocking_failures`, identical `warnings`, identical `informational`,
identical `explanation_reference`, identical `summary` text, and full
`EvaluationResult` equality (`provider_result == skill_result`). The
harder synthetic case (where `phase_identity_consistency`,
`push_state_consistency`, `metadata_consistency`, and
`canonical_promotion_eligibility` all resolve `UNKNOWN`) is included
specifically because it stresses more of `evaluate()`'s bucketing
logic than the real repo's mostly-`PASS` case does. **Result:
identical.**

## Transition Validator Compatibility

`TestTransitionValidatorCompatibility` re-runs the 113U/115F regression
scenarios (fully consistent state accepts; identity mismatch rejects;
partial report completeness quarantines; execution-available rejects;
CERTIFIED→CANONICAL accepts; BLOCKED→CANONICAL rejects) and confirms
determinism across 5 repeated calls with identical inputs. A further
test re-confirms the validator's own adapter evidence IDs remain a
subset of the richer skill-path evidence, and that
`repository_transition_validator.py` still contains no
`repository_skills` reference at all. **Result: unchanged.**

## Lifecycle Compatibility

115N runs no lifecycle command itself -- mutating a real phase/task
through `pcae phase complete`/`pcae task finish` is out of a
verification-only phase's scope, and would itself be governed lifecycle
activity, not verification of it. Instead:

- `TestLifecycleCompatibility` asserts, at the source level, that
  `pcae.commands.phase`, `pcae.commands.task`, `pcae.commands.push`,
  `repository_transition_integration.py`, `notification_certification.py`,
  `handoff_verification.py`, `post_push_canonicalization.py`, and
  `pcae.commands.runtime_inspect` still never reference
  `repository_skills` at all -- the only way lifecycle behavior could
  have changed is if one of them started consuming Repository Skills
  output, and none do.
- Full lifecycle behavior itself is exercised by the existing,
  unmodified integration suites this phase's Validation section runs
  (`test_repository_transition_validator_phase_complete_integration.py`,
  `test_repository_transition_validator_task_finish_integration.py`,
  `test_task_finish_notification_ordering.py`, `test_phase_reports*.py`,
  `test_notification*.py`), all passing unchanged.

**Result: phase complete, task finish, notification, report
generation, and verify-handoff all confirmed unchanged.**

## Registry Verification

`TestRegistryBehaviorVerification` reconfirms: deterministic
registration order, deterministic multi-skill invocation order,
order-independent merge, duplicate `skill_id` rejection, stable
repeated lookup, and that the implicit default registry
(`collect_evidence_via_repository_skills` with no `registry` argument)
matches an explicit `build_default_registry()` call exactly.

## Compatibility Path Verification

`TestCompatibilityPathStillFunctional` confirms the four Evidence
Provider classes remain directly importable and functional,
`collect_evidence_via_evidence_providers` and
`build_evaluation_context_from_evidence_providers` still work, and
every skill's declared `required_inputs` still matches its wrapped
provider's `required_inputs` exactly (no drift since 115K).

## Isolation Verification

`TestIsolationVerification` reconfirms: the skills path performs no
git mutation and creates no new files; the 115M integration module
exposes no `commit`/`push`/`finalize`/`notify`/`authorize`/`execute`/
`mutate` public function; its source contains no execution primitive
(`subprocess`, `os.system`, `Popen`, `exec`, `eval`); it never calls
`evaluate(` itself (Decision Evaluation is only ever invoked by a
caller of its `build_evaluation_context_from_*` helpers); and
`RepositorySkillResult` carries no `verdict`/`authorized`/`committed`/
`pushed`/`notified` field.

## AI Boundary Verification

`TestAiBoundaryVerification` confirms: no DeepSeek/GLM/Qwen/Claude/GPT/
Codex/SLM skill ID is registered; every default-registry manifest
declares `DETERMINISTIC` determinism and `model_produced=False`; every
evidence item the skills path produces is `DETERMINISTIC`; the
`AI_REVIEW` capability has zero registered skills; the 115M integration
module has no forbidden-vendor import; and the default registry still
contains exactly four skills.

## Execution Boundary Verification

`TestExecutionBoundaryVerification` confirms: the real repository's
`E-runtime-002` evidence (skills path) is `"unavailable"`; the
`runtime_execution_unavailable` invariant evaluates to `PASS` against
skill-path evidence; and `pcae runtime inspect --json` reports
`execution_availability: "unavailable"`, `current_runtime_state:
"Observed"`, `current_maximum_plugin_capability: "observe"`.

## fast_green Investigation

115M's final report recorded `4389/4390` fast_green with one failure:
`tests/test_dry_run_simulation.py::Test89dMatrixReadOnly::test_pytest_dry_run_not_blocked`.

**Root cause** (`TestFastGreenDiscrepancyInvestigation`,
`core/permission_broker.py`'s `_broker_decide`): the function's branch
`if sg_decision == "requires_active_task" and task_contract is None:
return "blocked_by_task_contract", ...` fires whenever a shell-gate
classified command (a plain `python -m pytest ...` invocation without
`-n auto`) is evaluated with **no active task present**. This maps to
advisory decision `would_block_by_task_contract`, which sets
`would_block=True` and leaves `would_require_active_task=False` (that
flag is set only by the different, mutually exclusive advisory
decision `would_require_active_task`, which this branch never
produces). The failing test's own assertion
(`would_block is False or would_require_active_task`) is therefore
false exactly when idle, and only when idle.

This was reproduced directly and deterministically (no subprocess, no
mutation of the real repository) by calling
`pcae.core.dry_run.build_simulation` against a synthetic `tmp_path`:
with no `tasks/active/` directory the command hard-blocks
(`would_block_by_task_contract`); with one present, it resolves to
`would_allow_governed_preflight_only` and `would_block` is `False`.

**Classification: pre-existing known issue** (state-dependent,
reproduces deterministically whenever the repository is idle at
simulation time -- not a flake, since it is 100% reproducible under a
known condition). It is **not a regression**: neither 115M's nor
115N's own source references `permission_broker`, `advisory`,
`shell_gate`, or `dry_run` at all (confirmed by
`test_permission_broker_module_untouched_by_115m_or_115n`), and
`core/permission_broker.py` was last touched by an unrelated shell-gate
audit-persistence phase, long before 115M. It is **not intentional
behavior of the failing test** -- the test's own comment ("pytest
without `-n auto` is test execution → may require task") documents an
expectation of `would_require_active_task=True` that the current
`_broker_decide` branch structure never produces for this input;
fixing that mismatch is out of this verification-only phase's
authorized scope (it would require modifying
`permission_broker.py`/`advisory.py`/the test itself, none of which
are Repository Skills modules), and is noted below as a candidate for
a future, separately-scoped repair phase.

## Readiness Assessment

Repository Skills are now verified, end-to-end, as a fully
behavior-preserving alternative evidence-acquisition path: equivalent
evidence, equivalent Decision Evaluation results, equivalent validator
verdicts, unchanged lifecycle behavior, deterministic registry
semantics, and a fully preserved compatibility path. Stage 3 of 115L's
migration strategy is now verified, not merely prototyped. The
repository is ready for Stage 4 planning (encapsulating providers
fully behind Repository Skills) and, per this phase's own frozen "AI
Insertion Point" (115L Section 8), for a future Advisory Repository
Skills architecture design phase -- deterministic skills and any
future advisory (model-backed) skill would merge into the same
`EvidenceCollection`, with Decision Evaluation and the Transition
Validator remaining unaware of which kind produced a given item.

## Tests

`tests/test_repository_skills_integration_verification_115n.py` (new,
62 tests): evidence equivalence per skill, Decision Evaluation
compatibility, Transition Validator compatibility, lifecycle
compatibility, registry verification, compatibility path verification,
isolation verification, AI boundary verification, execution boundary
verification, and the fast_green discrepancy investigation.

## Validation

- focused evidence/decision/validator/skills tests: see final report
- task/phase/notification suites: see final report
- runtime/contract/autonomy/plugin suites: see final report
- fast_green: see final report (with fast_green discrepancy re-classified above)
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115N`: see final report

## Governance

No Repository Skill modified, no Evidence Provider modified, no
Decision Evaluation modified, no Repository Transition Validator
modified, no lifecycle command modified, no Notification Policy
modified, no Canonical Artifact Promotion modified, no Push-State
Reconciliation modified, no Post-Push Canonicalization modified, no
new Repository Skill, no AI/SLM/LLM skill, no DeepSeek integration.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115P — Advisory Repository Skills Architecture
