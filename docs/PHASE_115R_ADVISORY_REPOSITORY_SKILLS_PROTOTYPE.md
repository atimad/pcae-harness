# Phase 115R — Advisory Repository Skills Prototype

## Status

Completed. Implements the framework 115P designed and 115Q froze,
using only a deterministic `MockAdvisoryProvider`. No real model
backend implemented or invoked: no DeepSeek, Claude API, OpenAI, GLM,
Qwen, Codex backend, local SLM, network call, subprocess model
execution, or MCP model invocation. No Decision Evaluation modified,
no Repository Transition Validator modified, no lifecycle command
modified, no Repository Skills runtime (115J's four deterministic
skills / `build_default_registry()`) modified. No execution capability.

## Purpose

Validate the architecture 115P designed and the contract 115Q froze by
implementing them end-to-end against a mock backend only: build the
framework, do not build AI integration.

Canonical reference document:

- `docs/PCAE_ADVISORY_REPOSITORY_SKILLS_PROTOTYPE.md`

## Framework Summary

New module `src/pcae/core/advisory_repository_skills.py` implements the
full 115Q pipeline: `AdvisoryRequest` -> `AdvisoryProvider.invoke()` ->
`RawAdvisoryResponse` -> `normalize_advisory_response()` ->
`NormalizedAdvisoryResponse` -> `build_evidence_from_normalized()` ->
`EvidenceCollection`, wired together by a new
`AdvisoryRepositorySkill` base class and its first concrete subclass,
`RepositoryConsistencyAdvisorySkill`.

## Advisory Request Summary

`AdvisoryRequest` is a frozen dataclass with exactly 115Q's four
frozen fields (`bounded_context`, `question`, `response_schema_hint`,
`timeout_seconds`), validating non-empty context/question and a
positive timeout at construction.

## Prompt Builder Summary

`build_advisory_request()` assembles an `AdvisoryRequest` from bounded,
deterministic repository context, requested evidence categories, and
an explicit objective — never a raw filesystem dump, never secrets,
never an open-ended prompt. It takes no `AdvisoryProvider` parameter,
proving the Prompt Builder does not know which provider will answer
its request.

## Mock Provider Summary

`MockAdvisoryProvider` is the only concrete `AdvisoryProvider`: a pure,
in-memory lookup from `AdvisoryRequest.question` to a canned
`RawAdvisoryResponse`, declaring `backend_kind="deterministic_mock"`
and `EvidenceDeterminism.DETERMINISTIC` (explicitly permitted by 115Q
for this one provider kind). No randomness, network I/O, filesystem
write, or execution of any kind. Supports deterministic failure
scenarios by construction (a canned `succeeded=False` or
malformed-content response).

## Normalizer Summary

`normalize_advisory_response()` rejects provider failures, unparseable
JSON, non-object payloads, missing/empty findings, and responses
claiming any unauthorized field (`verdict`, `commit`, `push`,
`authorized`, `execute`, `finalize`) outright as
`normalization_status="failed"`. Partially valid findings normalize to
`"partial"`, dropping invalid entries. Missing confidence/limitations
degrade honestly rather than being fabricated.

## Evidence Builder Summary

`build_evidence_from_normalized()` produces one `Evidence` item per
finding for a succeeded/partial normalization (probabilistic,
confidence-labelled from the signal, provenance-preserving, category
`AI_REVIEW`), or exactly one `UNKNOWN`-freshness item for a failed
normalization — never a fabricated passing observation.

## End-to-End Pipeline Summary

`RepositoryConsistencyAdvisorySkill` (defaults to `MockAdvisoryProvider()`)
wires the full pipeline through `RepositorySkill.invoke()`, proven
deterministic across repeated invocations and never mutating a
real, git-initialized synthetic repository.

## Deterministic Failure Handling

Three distinct failure paths proven: provider-level failure and
malformed raw content both degrade to one `UNKNOWN` evidence item with
an overall `SUCCESS` skill result (the skill ran; the evidence is
honestly unknown); a provider invocation exception yields an explicit
`RepositorySkillResult(status=FAILED, failure_reason=...)` with zero
evidence — never silent success, never hidden partial output.

## Tests

`tests/test_advisory_repository_skills_prototype_115r.py` (new, 77
tests): `AdvisoryRequest`, Prompt Builder, `MockAdvisoryProvider`,
deterministic outputs, Response Normalizer, Evidence Builder,
end-to-end advisory pipeline, deterministic failures, `UNKNOWN`
evidence, Repository Skill integration, no model invocation, no
network, no execution, no lifecycle wiring.

## Validation

- focused advisory framework tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115R`: see final report

## Governance

No Decision Evaluation modified, no Repository Transition Validator
modified, no lifecycle command modified, no Repository Skills runtime
modified (`build_default_registry()` still returns exactly 115J's four
deterministic skills). No DeepSeek/Claude/OpenAI/GLM/Qwen/Codex/local
SLM/any real backend implemented or invoked. No network access, no
execution capability.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115S — First Advisory Provider Integration (Current Acting Model)
