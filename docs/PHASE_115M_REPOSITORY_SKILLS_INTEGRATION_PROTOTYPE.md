# Phase 115M — Repository Skills Integration Prototype

## Status

Completed. Behavior-preserving integration prototype only: no Evidence
Provider removed or modified, no Decision Evaluation modified, no
Repository Transition Validator modified, no lifecycle command
modified, no Notification Policy modified, no Canonical Artifact
Promotion modified, no Push-State Reconciliation modified, no
Post-Push Canonicalization modified, no AI/SLM/LLM skill, no DeepSeek
integration, no execution capability.

## Purpose

Implement Stage 3 of 115L's frozen migration strategy
(`docs/PCAE_REPOSITORY_SKILLS_INTEGRATION_ARCHITECTURE.md` Section 6):
Repository Skills (115H design, 115I contract freeze, 115J prototype,
115K verification) become an available evidence-acquisition path for
Decision Evaluation, alongside — not instead of — 115D's Evidence
Provider path. Core rule: **same evidence, same decisions, better
architecture**.

## Integration Summary

A new module, `src/pcae/core/repository_skills_integration.py`, is the
concrete Stage 3 adapter 115L's architecture document anticipated. It
sits above Repository Skills, Evidence Providers, Evidence, and
Decision Evaluation, exposing two symmetric acquisition paths:

```
RepositoryState
      |
      v
RepositorySkillRegistry
      |
      v
RepositorySkills
      |
      v
EvidenceCollection
      |
      v
DecisionEvaluation
```

- `collect_evidence_via_repository_skills(root, *, strict=False,
  registry=None)` — the 115M path. Delegates exclusively to a
  `RepositorySkillRegistry` (`build_default_registry()` unless a
  caller supplies its own), invoking all registered skills and merging
  their `EvidenceCollection` via `RepositorySkillRegistry.
  merge_evidence`. This caller never constructs, discovers, or calls
  an Evidence Provider directly — every provider call happens inside
  a `RepositorySkill`.
- `build_evaluation_context_from_repository_skills(...)` — wraps the
  above into a ready-to-evaluate `EvaluationContext` for Decision
  Evaluation.

No code in this module is imported by `core/decision_evaluation.py`,
`core/repository_skills.py`, or `core/repository_transition_validator.
py` — 115L's frozen "Integration Boundary" (Section 2) and "Dependency
Direction" (Section 7) hold exactly as before this phase.

## Skill Evidence Acquisition Summary

`collect_evidence_via_repository_skills` uses only 115J's four
deterministic skills (`GitRepositorySkill`, `RuntimeRepositorySkill`,
`ReportRepositorySkill`, `MetadataRepositorySkill`) via
`build_default_registry()`. No advisory skill, no AI/SLM skill, and no
model-produced evidence is used. Every item the path returns declares
`EvidenceDeterminism.DETERMINISTIC`.

## Provider Compatibility Summary

`collect_evidence_via_evidence_providers(root, *, strict=False)` is
preserved as the pre-115M path: it instantiates 115D's four Evidence
Providers directly, in the same fixed order `build_default_registry()`
registers its wrapping skills, and merges their output. Nothing about
`core/evidence_providers.py` changed; direct provider usage (as 115D's
and 115J's own test suites already exercise) continues to work
unmodified.

## Evidence Equivalence Result

`tests/test_repository_skills_integration_115m.py`'s
`TestEvidenceEquivalence` proves, against both a synthetic `tmp_path`
repository and the real project root, that
`collect_evidence_via_evidence_providers` and
`collect_evidence_via_repository_skills` return the same set of
Evidence IDs, and that every item is semantically equal (same
category, producer, freshness, confidence, determinism, scope,
references, observed/expected value, explanation, limitations, and
provenance producer/produced_from/deterministic_origin) — differing
only in the two wall-clock timestamp fields each path's independent
`datetime.now()` call legitimately produces. **Result: equivalent.**

## Decision Evaluation Equivalence Result

`TestDecisionEvaluationEquivalence` builds an `EvaluationContext` from
each path (same `evaluation_id`/`evaluation_timestamp`/
`repository_snapshot_reference`/`evaluation_version`) and asserts
`evaluate(provider_context) == evaluate(skill_context)` — full
dataclass equality, not just a subset of fields, since neither
`EvaluationResult` nor `InvariantResult` carry a per-item timestamp.
Verified against a synthetic repository and the real project root.
**Result: identical.**

## Validator Verdict Compatibility Result

`TestValidatorVerdictCompatibility` re-runs 113U/115F's own regression
scenarios (fully consistent state accepts, identity mismatch rejects,
partial report completeness quarantines, execution-available rejects)
verbatim — unchanged, since no line of
`core/repository_transition_validator.py` was touched. A further test
proves the "equivalent Evidence IDs" acceptance criterion directly:
every Evidence ID the validator's own 115F adapter
(`build_evidence_from_repository_state`) cites (`E-report-002`,
`E-metadata-002`, `E-report-003`, `E-runtime-002`) is a subset of the
richer `collect_evidence_via_repository_skills` output for the same
repository. **Result: unchanged verdicts, equivalent Evidence IDs.**

## No-Integration / No-AI Confirmation

`TestNoLifecycleBehaviorChange` and
`TestNoAiIntegrationAndExecutionUnavailable` assert:

- `pcae.core.decision_evaluation`, `pcae.core.repository_skills`,
  `pcae.core.repository_transition_validator`,
  `pcae.core.repository_transition_integration`, `pcae.commands.phase`,
  `pcae.commands.task`, `pcae.commands.push`,
  `pcae.core.notification_certification`,
  `pcae.core.handoff_verification`,
  `pcae.core.post_push_canonicalization`, and
  `pcae.commands.runtime_inspect` never reference
  `repository_skills_integration`.
- `core/decision_evaluation.py` still imports only
  `pcae.core.evidence`.
- `repository_skills_integration.py` itself never imports
  `pcae.commands`, `notification_certification`,
  `handoff_verification`, `post_push_canonicalization`,
  `repository_transition_validator`, or
  `repository_transition_integration`.
- No DeepSeek/GLM/Qwen/GPT/Codex import or skill ID exists anywhere in
  the new path; `build_default_registry()` still registers only the
  four deterministic skills.
- The real repository's `E-runtime-002` evidence (both paths) is
  `"unavailable"`, and the `runtime_execution_unavailable` invariant
  still evaluates to `PASS` when fed skill-path evidence. Execution
  capability remains unavailable.

## Old Path Retained

`collect_evidence_via_evidence_providers` and
`build_evaluation_context_from_evidence_providers` remain available,
unchanged in behavior, as compatibility functions for callers not
(yet) adopting Repository Skills — nothing before 115M was deleted or
disabled.

## Skill Path Added

`collect_evidence_via_repository_skills` and
`build_evaluation_context_from_repository_skills` are new in this
phase. Neither is wired into `pcae phase complete`, `pcae task
finish`, `pcae push`, `pcae notify`, or any other lifecycle command —
they exist for explicit opt-in callers (today, only
`tests/test_repository_skills_integration_115m.py`).

## Remaining Future Work

Stage 4 of 115L's migration strategy (`docs/
PCAE_REPOSITORY_SKILLS_INTEGRATION_ARCHITECTURE.md` Section 6) is not
started: Evidence Providers are not yet a fully encapsulated
implementation detail, and no lifecycle command has been changed to
prefer the Repository Skills path over 115F's `RepositoryState`
adapter. That decision — if ever made — is out of scope for this
prototype phase and requires its own explicitly authorized future
phase.

## Tests

`tests/test_repository_skills_integration_115m.py` (new, 41 tests):
skill-based evidence acquisition, provider-path compatibility,
evidence equivalence, Decision Evaluation equivalence, validator
verdict compatibility, no-lifecycle-integration, no-AI/DeepSeek
confirmation, and execution-unavailable confirmation.

## Validation

- focused prototype/equivalence tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115M`: see final report

## Governance

No Evidence Provider modified, no Decision Evaluation modified, no
Repository Transition Validator modified, no lifecycle command
modified, no Notification Policy modified, no Canonical Artifact
Promotion modified, no Push-State Reconciliation modified, no
Post-Push Canonicalization modified, no AI/SLM/LLM skill, no DeepSeek
integration.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115N — Repository Skills Integration Verification & Compatibility
