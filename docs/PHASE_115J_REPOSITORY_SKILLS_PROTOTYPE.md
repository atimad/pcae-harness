# Phase 115J — Repository Skills Prototype

## Status

Completed. Implementation prototype only: no AI/SLM/LLM skills, no
DeepSeek integration, no lifecycle command changes, no Decision
Evaluation integration, no Repository Transition Validator
integration, no Notification Policy changes, no execution capability.

## Purpose

Implement the first Repository Skills framework on top of 115I's
frozen contract (`docs/PCAE_REPOSITORY_SKILLS_CONTRACT.md`), using
only deterministic skills that wrap 115D's existing Evidence Providers
unmodified.

Implementation: `src/pcae/core/repository_skills.py`.

## Repository Skills Prototype Summary

Repository Skills produce evidence. Repository Skills do not decide.
This phase implements the frozen `RepositorySkill` contract as running
code for the first time, with four deterministic skills, each a thin
wrapper around one 115D Evidence Provider: no new evidence-collection
logic was written — every skill delegates its `collect()`-equivalent
work to the existing provider and returns that provider's
`EvidenceCollection` unchanged.

## Skill Interface Summary

### RepositorySkillCapability

The frozen eight-value enum from 115I Section 2, implemented verbatim:
`git_analysis`, `runtime_analysis`, `architecture_analysis`,
`documentation_analysis`, `report_analysis`, `metadata_analysis`,
`dependency_analysis`, `ai_review`.

### RepositorySkillManifest

A frozen dataclass implementing 115I Section 3's field set exactly:
`skill_id`, `name`, `version`, `capabilities`, `determinism`,
`confidence_policy`, `evidence_categories`, `required_inputs`,
`optional_inputs`, `timeout_seconds`, `failure_policy`,
`side_effect_policy`, `model_produced`, `experimental`. Validates at
construction that `side_effect_policy` is always `"none"` and
`failure_policy` is one of the two frozen values — a skill manifest
claiming any other side effect or failure policy cannot be
constructed. No model/agent/backend/vendor identity field exists on
this shape.

### RepositorySkillContext

Mirrors 115D's `EvidenceProviderContext` exactly: `root: HarnessPath`
(read-only) and `strict: bool = False`.

### RepositorySkillResult

A frozen dataclass with `skill_id`, `status`
(`RepositorySkillStatus.SUCCESS`/`FAILED`), `evidence:
EvidenceCollection`, and `failure_reason: str | None`. Enforces at
construction that a `FAILED` result always carries a non-empty
`failure_reason` — the two-outcome failure contract (115I Section 5)
is structurally impossible to violate via this type.

### RepositorySkill

An abstract base class declaring one class-level `manifest:
RepositorySkillManifest` and one abstract method, `invoke(context) ->
RepositorySkillResult`. A skill never mutates `context.root`, decides,
votes, authorizes, promotes an artifact, sends a notification,
bypasses the Repository Transition Validator, or invokes execution.

## Deterministic Skills Implemented

| Skill | Wraps | Capability | Categories | Evidence IDs |
| --- | --- | --- | --- | --- |
| `GitRepositorySkill` | `GitEvidenceProvider` | `git_analysis` | `git`, `push_state` | `E-git-001`..`005` |
| `RuntimeRepositorySkill` | `RuntimeEvidenceProvider` | `runtime_analysis` | `runtime` | `E-runtime-001`..`003` |
| `ReportRepositorySkill` | `ReportEvidenceProvider` | `report_analysis` | `report` | `E-report-001`..`005` |
| `MetadataRepositorySkill` | `MetadataEvidenceProvider` | `metadata_analysis` | `metadata` | `E-metadata-001`..`005` |

Each skill's `invoke()` constructs an `EvidenceProviderContext` from
its own `RepositorySkillContext`, calls the wrapped provider's
`collect()` unmodified, and returns a `SUCCESS` result carrying that
provider's `EvidenceCollection` verbatim — no evidence ID rewriting,
no re-derivation, no new observation logic. The four wrapped
providers' Evidence IDs are already disjoint namespaces (established
in 115D), so no collision handling was needed to merge their output.

## Registry Summary

`RepositorySkillRegistry` implements:

- `register(skill)` — raises `ValueError` on a duplicate `skill_id`
- `get(skill_id)` — returns the skill or `None`
- `list_skills()` / `list_manifests()`
- `filter_by_capability(capability)` / `filter_by_category(category)`
- `invoke(skill_id, context)` — returns a `FAILED` result (never
  raises) for an unregistered `skill_id`
- `invoke_many(skill_ids, context)` / `invoke_all(context)`
- `merge_evidence(results)` — combines every `SUCCESS` result's
  evidence into one `EvidenceCollection`; `FAILED` results contribute
  no evidence; a genuine Evidence ID collision across skills would
  surface as `EvidenceCollection`'s own existing duplicate-ID
  `ValueError`, never a silent drop

`build_default_registry()` is a convenience constructor registering
all four skills above — not itself wired into any lifecycle command,
Decision Evaluation, or the Repository Transition Validator.

## Evidence Produced

Verified live against this real repository during implementation: the
four default skills collectively produce 18 `Evidence` items
(5 + 3 + 5 + 5) when invoked against a real git working tree with a
canonical phase report and phase-completion metadata present, merging
cleanly into one 18-item `EvidenceCollection` with no ID collisions.

## Failure Behavior

Every skill failure produces exactly one of 115I's two frozen
outcomes:

1. **Honest `UNKNOWN` evidence** — when the wrapped 115D provider
   itself degrades gracefully (e.g. no git repository, no
   `origin/main` remote, missing `latest.json`), the skill still
   reports `SUCCESS` (it *did* produce evidence) and that evidence
   carries `EvidenceFreshness.UNKNOWN`/`EvidenceConfidence.UNKNOWN` —
   verified directly by running `GitRepositorySkill` against a
   directory with no git repository at all.
2. **Explicit failure outcome** — when the skill invocation itself
   cannot complete (verified by monkeypatching a provider's
   `collect()` to raise), the skill returns `RepositorySkillResult(
   status=FAILED, failure_reason=...)` with empty evidence in
   non-strict mode, or re-raises in `strict=True` mode.

No silent success: a `FAILED` result can never carry evidence (the
dataclass doesn't prevent it structurally, but no code path in this
module ever constructs one that way), and `RepositorySkillResult`
itself refuses to construct a `FAILED` status without a
`failure_reason`.

## No-Integration Confirmation

`src/pcae/core/repository_skills.py`'s only internal imports are
`pcae.core.evidence`, `pcae.core.evidence_providers`, and
`pcae.core.paths.HarnessPath`. It is not imported by, and does not
import from:

- Decision Evaluation (`core/decision_evaluation.py`)
- The Repository Transition Validator
  (`core/repository_transition_validator.py`)
- Any lifecycle command (`commands/phase.py`, `commands/task.py`,
  `commands/push.py`)
- Notification Policy / `core/notification_certification.py`

No AI/SLM/LLM-backed skill is registered by `build_default_registry()`
— all four default skills declare `EvidenceDeterminism.DETERMINISTIC`
and `model_produced=False`. The `ai_review` capability (115I Section
2) has zero skills declaring it; `RepositorySkillCapability.AI_REVIEW`
exists only as an enum value, matching 115I's frozen minimum
capability set, not an implemented skill.

## Tests

`tests/test_repository_skills.py` (new, 53 tests): skill contract,
manifest validation, registry registration/duplicate-rejection/
lookup/filtering, deterministic skills returning
`EvidenceCollection`, multi-skill invocation, evidence merging,
failure behavior (both outcomes), no-mutation, no-AI/SLM/LLM-skill,
no-lifecycle-integration, and execution-unavailable confirmations.

Two pre-existing 115H/115I architecture-verification tests
(`test_no_new_implementation_module_added` in
`tests/test_phase_115h_repository_skills_architecture.py` and
`tests/test_phase_115i_repository_skills_contract_freeze.py`) asserted
that `src/pcae/core/repository_skills.py` did not yet exist — accurate
at the time those phases were written, since implementing it was
explicitly 115J's own later mandate, not theirs. Both were updated to
drop that one path from their forbidden-path list (with a comment
explaining why), while continuing to guard against the *other*
speculative implementation filenames (`skills.py`,
`skill_registry.py`, `skill_manifest.py`) that still do not exist.

## Validation

- Focused: `python -m pytest tests/test_repository_skills.py
  tests/test_evidence*.py -n auto -q -ra --durations=100` — see final
  report.
- Regression: `python -m pytest tests/test_*runtime* tests/test_*contract*
  tests/test_*autonomy* tests/test_*plugin* -n auto -q -ra
  --durations=100` — see final report.
- Fast-green: `python -m pytest -m "fast_green" -n auto -ra
  --durations=100` — see final report.
- `pcae health` / `pcae check` / `pcae doctor task-memory` / `pcae push
  check` / `pcae agent verify-handoff` / `pcae session bootstrap
  --compact --profile implementation` / `pcae runtime inspect --json` /
  `pcae notify status` — see final report.
- `pcae skill invoke phase-finalization 115J` — see final report.

## Governance

No Decision Evaluation, Repository Transition Validator, lifecycle
command, or Notification Policy behavior changed. No AI/SLM/LLM-backed
skill, no DeepSeek integration implemented.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115K — Repository Skills Verification & Compatibility
