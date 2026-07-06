# Phase 115Q — Advisory Repository Skills Contract Freeze

## Status

Completed. Contract/design only: no Advisory Repository Skill
implemented, no Advisory Provider implemented, no model call
implemented, no DeepSeek/GLM/Claude/Codex/Qwen/OpenAI/local-SLM/any-
backend integration, no model configuration added, no Repository
Skills runtime modified, no Evidence Provider modified, no Decision
Evaluation modified, no Repository Transition Validator modified, no
lifecycle command modified. No execution, authorization, Permission
Broker enforcement, plugin, Telegram inbound, REST, Web UI, or
Dashboard capability introduced.

## Purpose

Freeze the backend-agnostic contract for Advisory Repository Skills
before any advisory skill implementation or model invocation: the
`AdvisoryRepositorySkill` interface, the `AdvisoryProvider` abstraction
(so no skill ever depends directly on a specific model backend), the
prompt/response/evidence boundaries, the default same-model mode, the
deferred split-model mode, the failure contract, the safety rules, and
a narrow first pilot scope.

Canonical contract document:

- `docs/PCAE_ADVISORY_REPOSITORY_SKILLS_CONTRACT.md`

## Core Principle

Advisory Repository Skills produce evidence. They never decide.

## Advisory Contract Summary

The `AdvisoryRepositorySkill` interface requires every conforming
skill to declare advisory capability, evidence categories produced,
probabilistic determinism by default, and a model-produced evidence
boundary; to build a prompt/request, consume a normalized advisory
response, and produce `EvidenceCollection`; and is exhaustively
forbidden from decision making, repository mutation, lifecycle
authority, commit, push, finalize, notification dispatch, artifact
promotion, execution, authorization, and validator bypass.

## Advisory Provider Abstraction

Four contract-only types are frozen: `AdvisoryProvider`
(`provider_id`, `backend_kind`, `determinism`, single `invoke()`
operation), `AdvisoryRequest` (`bounded_context`, `question`,
`response_schema_hint`, `timeout_seconds`), `RawAdvisoryResponse`
(`raw_content`, `provider_id`, `succeeded`), and
`NormalizedAdvisoryResponse` (`findings`, `confidence_signal`,
`references`, `limitations`, `normalization_status`). An Advisory
Repository Skill talks only to the `AdvisoryProvider` interface —
current acting model (default), DeepSeek, Claude, Codex, GLM/Z.ai,
Qwen, OpenAI, local SLM, external review service, and deterministic
mock are named as *possible* future providers, none implemented.

## Prompt Boundary

The Prompt Builder must receive bounded repository context and an
explicit task/question, include no secrets, no unrestricted command
capability, and no execution request, and produce an advisory request
only.

## Response Normalization Boundary

Raw model output (`RawAdvisoryResponse`) is never trusted directly. It
must pass through the Normalizer (producing a validated
`NormalizedAdvisoryResponse`, rejecting malformed/unauthorized content
outright) and then the Evidence Builder. Only canonical `Evidence`
enters PCAE.

## Evidence Builder Contract

Evidence Builder output must be probabilistic by default,
model-produced if applicable, advisory only, confidence-labelled,
limitation-labelled, provenance-preserving, and never sole authority
for Accept — reusing existing `Evidence`/`RepositorySkillManifest`
fields, no schema change.

## Failure Contract

Every advisory failure (provider timeout/error, Normalizer rejection,
or an Evidence Builder unable to construct valid `Evidence`) must
produce exactly one of two outcomes: `UNKNOWN`-freshness evidence
(115D's pattern) or an explicit advisory failure result (115I's
two-outcome `RepositorySkillResult` contract) — never silently
succeeding, and never hiding a partially-normalized response's dropped
findings.

## Same-Model Default

The default `AdvisoryProvider` is, conceptually, the current acting
model — an architecture rule, not an implementation. No separate
configuration is required for default mode.

## Split-Model Future Mode

Documented, not implemented: a writer model and a distinct advisory
model may diverge later; configuration is only needed for that
split-model mode, never for default mode.

## Safety Rules

Advisory Repository Skills must never execute commands, request shell
access, mutate the repository, authorize transitions, override
deterministic evidence, override the validator, produce final
lifecycle decisions, send notifications, or access secrets — an
exhaustive restatement gathered from the Section 1/5/6/8 prohibitions
already frozen individually.

## First Pilot Scope

A future first pilot should be narrowly scoped to exactly one of:
repository consistency review, documentation consistency review, or
report consistency review — never all three at once, and never code
execution, security authorization, lifecycle control, or autonomous
repair.

## Wire Diagram Summary

Two Mermaid diagrams: the full pipeline (Repository State through
Repository Transition Validator, now including the Advisory Provider
abstraction and its Raw/Normalized response stages), and a swappable-
backend diagram showing the `AdvisoryProvider` interface with the
current-acting-model default and every other named provider as
dotted, unimplemented future branches.

## Tests

`tests/test_phase_115q_advisory_repository_skills_contract_freeze.py`
(new): architecture/documentation verification only. Verifies both new
docs exist and contain: the advisory contract, the Advisory Provider
abstraction and its four types, the default same-model mode, the
split-model future mode, the prompt boundary, the response
normalization boundary, the Evidence Builder contract, the failure
behavior, the safety rules, the first pilot scope, both Mermaid
diagrams, and explicit "no implementation"/"execution capability
remains unavailable" confirmations. No implementation-claim strings
are asserted to exist — the tests confirm none were added.

## Validation

- focused contract/architecture tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115Q`: see final report

## Governance

No Advisory Repository Skill implemented, no Advisory Provider
implemented, no model call implemented, no DeepSeek/GLM/Claude/Codex/
Qwen/OpenAI/local-SLM/any-backend integration, no model configuration
added, no Repository Skills runtime, Evidence Provider, Decision
Evaluation, Repository Transition Validator, or lifecycle command
modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115R — Advisory Repository Skills Prototype
