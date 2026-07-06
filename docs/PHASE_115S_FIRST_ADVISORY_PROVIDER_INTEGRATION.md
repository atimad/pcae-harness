# Phase 115S — First Advisory Provider Integration (Current Acting Model)

## Status

Completed. Tightly scoped advisory pilot: no backend selection, no
model configuration, no DeepSeek/GLM-specific integration, no provider
registry, no multi-model mode, no execution capability. No Decision
Evaluation modified, no Repository Transition Validator modified, no
lifecycle command modified, no Repository Skills runtime modified
(`build_default_registry()` still returns exactly 115J's four
deterministic skills).

## Purpose

Integrate the first real (non-mock) `AdvisoryProvider` — the current
acting model — as a one-shot, stateless evidence producer for exactly
one bounded pilot question. Core rule: the model produces advisory
evidence only; PCAE decides.

## Pilot Scope

Exactly one advisory question: **"Is the repository state internally
consistent?"** — operationalized, without modifying 115R's frozen
code, as `RepositoryConsistencyAdvisorySkill.objective ==
"repository_consistency_review"` (115R's own first Advisory Repository
Skill, reused unmodified). Explicitly excludes code review,
architecture review, planning, refactoring advice, bug finding,
security review, and autonomous repair.

## Same-Model Default

There is no live model API call, no network invocation, no subprocess,
and no MCP tool call anywhere in the new module. "The current acting
model" means whichever agent is operating a PCAE session at the moment
one bounded `AdvisoryRequest` is answered — that answer is supplied
once, at construction time, exactly as a human operator would type one
in. Integration means plumbing: shepherding that single supplied
answer through 115R's unmodified Normalizer and Evidence Builder,
never bypassing either. This matches 115Q's frozen default same-model
mode: no new configuration file, CLI flag, environment variable, or
model registry entry required.

## Provider Boundary

`CurrentActingModelAdvisoryProvider` conforms to 115R's
`AdvisoryProvider` interface unmodified (`provider_id="current_acting_model_advisory_provider"`,
`backend_kind="current_acting_model"`, `determinism=PROBABILISTIC`,
single `invoke()`). `invoke()` returns `RawAdvisoryResponse` only —
never a PCAE `Evidence` object, never any other trusted PCAE type.
Stateless and single-use: a second `invoke()` call on the same
instance raises `RuntimeError` rather than silently returning a second
answer or retrying — "one request / one response", "no retries", and
"no multi-turn conversation" are enforced structurally by this guard,
not by convention.

## Normalization Boundary

The raw response passes through 115R's existing
`normalize_advisory_response()` completely unmodified — no bespoke
normalization logic exists in the new module. Malformed content,
unparseable JSON, and unauthorized-field claims are rejected exactly
as they are for `MockAdvisoryProvider`.

## Evidence Boundary

Evidence is built via 115R's existing `build_evidence_from_normalized()`
completely unmodified: probabilistic (`EvidenceDeterminism.PROBABILISTIC`),
model-produced (provenance references
`current_acting_model_advisory_provider`, `deterministic_origin=False`),
advisory only (`EvidenceCategory.AI_REVIEW`), confidence-labelled from
the supplied confidence signal, limitations-labelled (never empty),
and provenance-preserving. **Never sole authority for Accept**: advisory
evidence carries no Evidence ID any of Decision Evaluation's six frozen
invariant families look up, so it cannot influence
`phase_identity_consistency`, `push_state_consistency`,
`metadata_consistency`, `report_completeness`,
`runtime_execution_unavailable`, or `canonical_promotion_eligibility`
on its own, regardless of confidence — proven directly by feeding this
pilot's evidence alone into `evaluate()` and confirming zero invariants
resolve `PASS`.

## Safety Summary

The provider never executes commands, mutates files, commits, pushes,
finalizes, notifies, authorizes, bypasses the validator, or accesses
secrets — verified structurally: no network/execution primitive in the
module's code, no backend-specific import or identifier
(DeepSeek/Claude/OpenAI/GLM/Qwen/Codex/MCP/Anthropic), and no
reference to any lifecycle command, Notification Policy,
handoff-verification, post-push-canonicalization, Decision Evaluation,
or the Repository Transition Validator anywhere in the new module.

## Failure Behavior

If the current-model advisory is unavailable (`succeeded=False`) or
malformed (unparseable/out-of-schema content), the pipeline produces
exactly one `UNKNOWN`-freshness, `UNKNOWN`-confidence `Evidence` item
— never a fabricated passing observation, and never silently
succeeding. A provider invocation exception (e.g. reuse after
exhaustion) becomes an explicit
`RepositorySkillResult(status=FAILED, failure_reason=...)` with zero
evidence when the skill runs non-strict, or propagates directly under
`context.strict=True` — matching 115R's established two-outcome
failure contract exactly, reused unmodified.

## No Lifecycle Integration

Not wired into `pcae phase complete`, `pcae task finish`, `pcae push`,
`pcae notify`, `pcae agent verify-handoff`, or `pcae runtime inspect`
as an authority — confirmed by source-level checks across every
lifecycle, notification, handoff, and runtime-inspect module. Invoked
only by tests and the explicit
`build_repository_consistency_skill_with_current_model()` prototype
helper.

## Remaining Limitations

- No live model invocation exists — a real caller must still supply
  the current acting model's answer as a string at construction time;
  there is no automated "ask the model" mechanism in this codebase and
  none is added here.
- No split-model configuration (115Q Section 4) — still entirely
  deferred.
- This provider is single-use per instance by design; a caller needing
  to answer the pilot question again must construct a new instance —
  there is no batching or session-reuse mechanism.
- Not wired into any registry a real evaluation consumes; a future
  integration phase decides if/how that happens, mirroring 115M/115N's
  staged migration for deterministic skills.

## Tests

`tests/test_current_acting_model_advisory_provider_115s.py` (new, 48
tests): conforms to `AdvisoryProvider`, one request/one response/one
`EvidenceCollection`, raw response normalization, Evidence Builder
output, malformed response handling, unavailable provider handling, no
execution, no mutation, no lifecycle authority, no backend-specific
dependency, advisory evidence never sole authority for Accept, and
pilot scope (exactly one bounded question).

## Validation

- focused advisory provider tests: see final report
- fast_green: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115S`: see final report

## Governance

No backend selection, no model configuration, no DeepSeek/GLM-specific
integration, no provider registry, no multi-model mode implemented.
No Decision Evaluation, Repository Transition Validator, lifecycle
command, or Repository Skills runtime modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115T — Advisory Provider Verification & Compatibility
