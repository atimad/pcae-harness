# Phase 115Q Complete — Advisory Repository Skills Contract Freeze

- **Phase ID:** `115Q`
- **Status:** completed
- **Report completeness:** complete
- **Missing trust fields:** none
- **Files changed:** 8
- **Tests run:** 259 (focused architecture/documentation suite)
- **Commits:** 27fb2e93, 2fb57b3f
- **Pushed:** pushed
- **origin/main..HEAD:** 0

## Summary

Phase 115Q freezes the backend-agnostic contract for Advisory
Repository Skills before any implementation or model call: the
`AdvisoryRepositorySkill` interface, the `AdvisoryProvider` abstraction,
the prompt/response/evidence boundaries, the default same-model mode,
the deferred split-model mode, the failure contract, an exhaustive
safety-rule checklist, and a narrow first pilot scope. Contract/design
only; zero implementation added.

## Advisory Contract Summary

`AdvisoryRepositorySkill` requires every conforming skill to declare
advisory capability, evidence categories produced, probabilistic
determinism by default, and a model-produced evidence boundary; to
build a prompt/request, consume a normalized advisory response, and
produce `EvidenceCollection`; and is exhaustively forbidden from
decision making, repository mutation, lifecycle authority, commit,
push, finalize, notification dispatch, artifact promotion, execution,
authorization, and validator bypass.

## Advisory Provider Abstraction

Four contract-only types: `AdvisoryProvider` (`provider_id`,
`backend_kind`, `determinism`, single `invoke()`), `AdvisoryRequest`
(`bounded_context`, `question`, `response_schema_hint`,
`timeout_seconds`), `RawAdvisoryResponse` (`raw_content`,
`provider_id`, `succeeded`), `NormalizedAdvisoryResponse` (`findings`,
`confidence_signal`, `references`, `limitations`,
`normalization_status`). Current acting model (default), DeepSeek,
Claude, Codex, GLM/Z.ai, Qwen, OpenAI, local SLM, external review
service, and deterministic mock named as possible future providers —
none implemented.

## Prompt Boundary

Bounded repository context, explicit task/question, no secrets, no
unrestricted command capability, no execution request, advisory
request only.

## Response Normalization Boundary

Raw model output never trusted directly — must pass through the
Normalizer (producing a validated `NormalizedAdvisoryResponse`) then
the Evidence Builder. Only canonical `Evidence` enters PCAE.

## Evidence Builder Contract

Probabilistic by default, model-produced if applicable, advisory
only, confidence-labelled, limitation-labelled, provenance-preserving,
never sole authority for Accept — reusing existing
`Evidence`/`RepositorySkillManifest` fields, no schema change.

## Same-Model Default

The default `AdvisoryProvider` is, conceptually, the current acting
model — an architecture rule, not an implementation. No new
configuration required.

## Split-Model Future Mode

Documented, not implemented: writer model vs. advisory model,
configuration only needed for that split-model mode.

## Safety Rules

Advisory Repository Skills must never execute commands, request shell
access, mutate the repository, authorize transitions, override
deterministic evidence, override the validator, produce final
lifecycle decisions, send notifications, or access secrets.

## First Pilot Scope

Exactly one of repository/documentation/report consistency review —
never all three at once, and never code execution, security
authorization, lifecycle control, or autonomous repair.

## Wire Diagram Summary

Two Mermaid diagrams: the full pipeline including the Advisory
Provider abstraction and Raw/Normalized response stages, and a
swappable-backend diagram showing the `AdvisoryProvider` interface
with current-acting-model default and every other named provider as
dotted, unimplemented future branches.

## PCAE Architecture Status

*Generated conceptually from canonical project state. Never manually
maintained as runtime state.*

### Completed

- Repository Decision & Explainability Framework through Phase 115A
- Repository Evidence Framework Contract Freeze through Phase 115B
- Repository Evidence Framework Prototype through Phase 115C
- Repository Evidence Provider Prototype through Phase 115D
- Repository Decision Evaluation Prototype through Phase 115E
- Repository Decision Evaluation Integration through Phase 115F
- Repository Decision Evaluation Verification & Compatibility through Phase 115G
- Repository Skills Architecture through Phase 115H
- Repository Skills Contract Freeze through Phase 115I
- Repository Skills Prototype through Phase 115J
- Repository Skills Verification & Compatibility through Phase 115K
- Repository Skills Integration Design through Phase 115L
- Repository Skills Integration Prototype through Phase 115M
- Repository Skills Integration Verification & Compatibility through Phase 115N
- Advisory Repository Skills Architecture through Phase 115P
- Advisory Repository Skills Contract Freeze through Phase 115Q

### Planned

- 115R — Advisory Repository Skills Prototype

### Current Runtime State

- **State:** Observed
- **Maximum Capability:** observe
- **Execution Availability:** unavailable

## Governance Results

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_doctor_task_memory:** clean
- **pcae_push_check:** clean (pushed, origin/main..HEAD == 0)
- **pcae_agent_verify_handoff:** pass
- **pcae_session_bootstrap_compact:** completed
- **pcae_runtime_inspect:** execution unavailable, Observed, observe
- **telegram_runtime:** loaded, configured, enabled
- **phase_finalization_skill:** resolved, target completed

## Test Results

- **focused_architecture_documentation_tests:** 259/259 (passed)
- **report_notification_tests:** present_in_canonical_metadata (present)
- **bootstrap_session_reporting_tests:** present_in_canonical_metadata (present)
- **fast_green:** 4390/4390 (passed; carried forward from 115P, unaffected by this contract-freeze-only phase)

## No-Go Confirmations

- No Advisory Repository Skill implemented.
- No Advisory Provider implemented.
- No model call implemented.
- No DeepSeek integration.
- No GLM integration.
- No Claude skill.
- No Codex skill.
- No Qwen integration.
- No OpenAI integration.
- No local SLM integration.
- No model configuration added.
- No Repository Skills runtime modified.
- No Evidence Provider modified.
- No Decision Evaluation modified.
- No Repository Transition Validator modified.
- No lifecycle command modified.
- No execution.
- No authorization.
- No Permission Broker enforcement.
- No plugins.
- No Telegram inbound.
- No REST.
- No Web UI.
- No Dashboard.
- No raw git commit.
- No raw git push.
- No force push.
- No tags.
- No releases.
- No package publication.

## Recommended Next Phase

115R — Advisory Repository Skills Prototype

## Report Consistency

- **Canonical report:** present
- **Metadata:** present
- **Status:** consistent

---
*Report generated for PCAE Phase 115Q. Schema version 1.0.*
