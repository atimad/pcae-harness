# Phase 115T — Advisory Provider Verification & Compatibility

## Status

Completed. Verification only: no new provider implemented, no
DeepSeek added, no GLM added, no Codex-specific integration added, no
provider selection added, no model configuration added, no lifecycle
command modified, no Decision Evaluation modified, no Repository
Transition Validator modified, no Repository Skills runtime modified.
No execution, authorization, Permission Broker enforcement, plugin,
Telegram inbound, REST, Web UI, or Dashboard capability introduced.

## Purpose

Verify that 115S's first real Advisory Provider integration
(`CurrentActingModelAdvisoryProvider`) is safely contained,
behavior-compatible, failure-isolated, and portable to future
providers — without implementing any of those future providers.

## Core Principle (Restated, Unchanged)

The advisory provider may produce evidence. PCAE remains the
authority.

## Containment Verification Summary

Confirmed the advisory provider and skill expose no
decide/authorize/commit/push/finalize/notify/mutate/execute/approve/
reject public method; `RawAdvisoryResponse` carries no verdict or
authorization field; the advisory skill never mutates a real,
git-initialized repository (file listing and git log identical before
and after `invoke()`); neither advisory module imports
`repository_transition_validator`/`TransitionVerdict`/`validate_transition`;
the validator module never references either advisory module.
Directly proved advisory-only evidence resolves **zero** invariants to
`PASS` when fed alone into `evaluate()`, and that mixing advisory
evidence with deterministic evidence never changes the deterministic
evaluation's `blocking_failures` — advisory evidence cannot override a
deterministic disagreement.

## Boundary Verification

Confirmed `AdvisoryProvider.invoke()` returns exactly
`RawAdvisoryResponse` (`type() is` check, not just `isinstance`);
`normalize_advisory_response()` returns exactly
`NormalizedAdvisoryResponse`; `build_evidence_from_normalized()`
returns exactly `EvidenceCollection` of `Evidence` items;
`EvaluationContext` rejects a non-`EvidenceCollection` evidence
argument; `core/decision_evaluation.py` has no import referencing
either advisory module; `validate_transition` still resolves ACCEPT/
REJECT/QUARANTINE from `RepositoryState` fields alone, unaware advisory
evidence exists.

## Failure Isolation

Tested six distinct malformed/unavailable scenarios (provider
unavailable, malformed JSON, missing confidence, missing limitations,
unexpected extra content fields, empty findings) — each either
normalizes successfully while ignoring unrecognized extras, or
produces exactly one `UNKNOWN`-freshness, `UNKNOWN`-or-`LOW`-confidence
evidence item. No scenario ever raises out of `RepositoryConsistencyAdvisorySkill.invoke()`.
No scenario ever produces `HIGH`/`MEDIUM` confidence from a failure
path. Mixing a failed advisory scenario with real deterministic
evidence leaves the deterministic evaluation's `blocking_failures` and
`warnings` completely unchanged.

## Nondeterminism Containment

Across five varied raw advisory contents (different finding counts,
confidence values, malformed entries mixed with valid ones, a
non-numeric confidence signal), every `NormalizedAdvisoryResponse`
conforms to its frozen schema (`findings` a tuple of strings,
`confidence_signal` `None` or numeric, `references` a tuple,
non-empty `limitations`, a valid `normalization_status`); every
resulting `Evidence` item is `PROBABILISTIC` and carries
`deterministic_origin=False` provenance referencing
`current_acting_model_advisory_provider`; confidence, limitations, and
provenance are always present; and advisory evidence never alone
resolves any invariant to `PASS`, across every variation tested.

## Backend Portability

Documented and proven with test-local stand-ins only (never real
integrations, never added to `src/`): a fake provider parametrized
over `backend_kind` values `current_acting_model`, `deepseek`,
`glm_zai`, `qwen`, `codex`, and `local_slm` plugs into the unmodified
`RepositoryConsistencyAdvisorySkill` and produces valid evidence
identically regardless of `backend_kind` — Decision Evaluation
resolves the same zero-`PASS` result across all three sampled kinds.
Confirmed no real backend name (DeepSeek/GLM/Qwen/Codex/local SLM/
Anthropic/OpenAI) appears anywhere in either advisory module's
executable code, and that neither `core/decision_evaluation.py` nor
`core/repository_transition_validator.py` reference `backend_kind` at
all — portability requires zero change to either.

## Pilot Scope Verification

Confirmed the only supported advisory question remains "Is the
repository state internally consistent?"
(`RepositoryConsistencyAdvisorySkill.objective ==
"repository_consistency_review"`); no code-review, architecture-review,
security-review, planning-advice, autonomous-repair, refactoring-advice,
or bug-finding scope string appears anywhere in either advisory
module; the prototype helper and skill constructor expose no
question/objective override parameter; exactly one concrete
`AdvisoryRepositorySkill` subclass exists
(`RepositoryConsistencyAdvisorySkill`).

## No Hidden Configuration

Confirmed no provider-registry class, no backend-selection function
(`select_provider`/`choose_provider`/`get_provider`/any
`*select*backend*` name), no API-key/secret/environment-variable
reference, no split-model configuration
(`writer_model`/`split_model`/`advisory_model_config`), and no
network-specific configuration (`base_url`/`endpoint`/`host=`/`port=`/
`timeout_ms`) exists in either advisory module. `.pcae/policy.toml`
carries no advisory-provider or DeepSeek reference.

## No Execution Capability

The real repository's `E-runtime-002` evidence (via the unmodified
115M skills-integration path) is still `"unavailable"`; the
`runtime_execution_unavailable` invariant still evaluates `PASS`
against skill-path evidence; neither advisory module contains any
execution primitive (`subprocess`, `os.system`, `Popen`, `exec`,
`eval`); `build_default_registry()` still returns exactly 115J's four
deterministic skills.

## Remaining Limitations

- Still no live, automated model-invocation mechanism — a real caller
  must still supply the current acting model's answer as a string;
  this phase verifies the existing plumbing, it does not add one.
- Backend portability is proven structurally with test-only stand-ins
  only; no real DeepSeek/GLM/Qwen/Codex/local-SLM provider has been
  implemented or exercised against a live backend.
- Not wired into any registry a real evaluation consumes; still an
  opt-in, separately constructed skill.

## Tests

`tests/test_advisory_provider_verification_115t.py` (new, 66 tests):
provider containment, raw/normalized/evidence boundaries, failure
isolation, malformed response handling, `UNKNOWN` evidence,
probabilistic/model-produced evidence, advisory evidence cannot
authorize Accept alone, pilot scope restriction, no hidden backend
config, no execution capability.

## Validation

- focused advisory/repository-skills/evidence/decision-evaluation tests: see final report
- runtime/contract/autonomy/plugin suites: see final report
- fast_green: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115T`: see final report

## Governance

No new provider implemented, no DeepSeek, no GLM, no Codex-specific
integration, no provider selection, no model configuration, no
lifecycle command modified, no Decision Evaluation modified, no
Repository Transition Validator modified, no Repository Skills
runtime modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115U — Second Advisory Provider Pilot Planning
