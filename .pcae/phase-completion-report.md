# Phase 115P Complete — Advisory Repository Skills Architecture

- **Phase ID:** `115P`
- **Status:** completed
- **Report completeness:** complete
- **Missing trust fields:** none
- **Files changed:** 8
- **Tests run:** 240 (focused architecture/documentation suite)
- **Commits:** e0ecb920, d956359e
- **Pushed:** pushed
- **origin/main..HEAD:** 0

## Summary

Phase 115P designs Advisory Repository Skills as model-backed,
evidence-only Repository Skills — the concrete pipeline, model
boundary, and default-mode rule that 115H Section 4 and 115L Section 8
both anticipated but did not specify. Architecture and design only;
zero implementation added.

## Core Principle

Advisory models may produce evidence. PCAE decides.

## Advisory Pipeline

```
Repository State -> Prompt Builder -> Current Model -> Raw Response
    -> Normalizer -> Evidence Builder -> EvidenceCollection
    -> Decision Evaluation -> Repository Transition Validator
```

The Normalizer is the sole boundary converting untrusted model output
into a validated intermediate shape (or failing closed);
EvidenceCollection merges via the existing
`RepositorySkillRegistry.merge_evidence()` point (115J, unchanged);
Decision Evaluation and the Repository Transition Validator are
unmodified and source-agnostic.

## Model Boundary

A model never returns a trusted PCAE object directly. Raw Response is
plain text/JSON only; the model has no tool-call authority, no
file-write access, and no `pcae` command invocation ability.

## Default Same-Model Mode

The current acting model may be the advisory model by default — no
new configuration file, CLI flag, environment variable, or model
registry entry required.

## Future Split-Model Mode

Documented, not implemented: a writer model (performs the session's
changes) vs. an advisory model (reviews them), to reduce same-model
blind-spot risk. No schema, selection logic, or adapter added.

## Safety Rules

Probabilistic by default, model-produced (existing `Evidence.provenance`/
`RepositorySkillManifest.model_produced` fields), never sole authority
for Accept, may trigger human review, may suggest repair
(`InvariantResult.suggested_repair`), must include non-empty
`limitations`, must cite references where possible. No new field,
enum value, or type required.

## Failure Behavior

`UNKNOWN`-freshness evidence or an explicit `RepositorySkillResult`
failure; never blocks deterministic checks by itself; never silently
succeeds.

## First Future Pilot Scope

Repository consistency review, documentation consistency review,
report consistency review only. Excludes code execution, lifecycle
authority, and commit/push/finalize authority.

## Wire Diagram Summary

Two Mermaid diagrams: the advisory pipeline itself, and how an
Advisory Repository Skill plugs into the existing Repository Skills
wire diagram alongside deterministic skills, both merging into one
undifferentiated `EvidenceCollection`.

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

### Planned

- 115Q — Advisory Repository Skills Contract Freeze

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

- **focused_architecture_documentation_tests:** 240/240 (passed)
- **report_notification_tests:** present_in_canonical_metadata (present)
- **bootstrap_session_reporting_tests:** present_in_canonical_metadata (present)
- **fast_green:** 4390/4390 (passed; carried forward from 115N, unaffected by this architecture-only phase)

## No-Go Confirmations

- No Advisory Repository Skill implemented.
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

115Q — Advisory Repository Skills Contract Freeze

## Report Consistency

- **Canonical report:** present
- **Metadata:** present
- **Status:** consistent

---
*Report generated for PCAE Phase 115P. Schema version 1.0.*
