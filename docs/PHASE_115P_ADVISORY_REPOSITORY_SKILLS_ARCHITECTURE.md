# Phase 115P — Advisory Repository Skills Architecture

## Status

Completed. Architecture and design only: no Advisory Repository Skill
implemented, no model call implemented, no DeepSeek/GLM/Claude/Codex/
Qwen/OpenAI/local-SLM/any-backend integration, no model configuration
added, no Repository Skills runtime modified, no Evidence Provider
modified, no Decision Evaluation modified, no Repository Transition
Validator modified, no lifecycle command modified. No execution,
authorization, Permission Broker enforcement, plugin, Telegram inbound,
REST, Web UI, or Dashboard capability introduced.

## Purpose

Design Advisory Repository Skills as model-backed, evidence-only
Repository Skills — the concrete pipeline, model boundary, and
default-mode rule that 115H Section 4 (Advisory skill class) and 115L
Section 8 (Future AI Insertion Point) both anticipated but did not
specify.

Canonical architecture document:

- `docs/PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md`

## Core Principle

**Advisory models may produce evidence. PCAE decides.**

## Advisory Architecture Summary

An Advisory Repository Skill is a Repository Skill (115H, unchanged)
whose evidence-production mechanism is a model invocation. It inherits
every deterministic-skill prohibition (115H Section 7) and every
Advisory-class guarantee 115H Section 4 already named: uses a model
only as an evidence producer, produces `EvidenceCollection`, never
decides, never mutates, never authorizes, never promotes artifacts,
never notifies, never commits, never pushes, never finalizes.

## Advisory Pipeline

```
Repository State -> Prompt Builder -> Current Model -> Raw Response
    -> Normalizer -> Evidence Builder -> EvidenceCollection
    -> Decision Evaluation -> Repository Transition Validator
```

Each stage's trust level and responsibility is frozen: Repository
State is authoritative; Prompt Builder is deterministic given the same
inputs and includes no secrets; Current Model and Raw Response are
untrusted; Normalizer is the sole boundary converting untrusted output
into a validated intermediate shape (or failing closed); Evidence
Builder produces ordinary 115C `Evidence` items labelled
`PROBABILISTIC`/model-produced; EvidenceCollection merges via the
existing `RepositorySkillRegistry.merge_evidence()` point (115J,
unchanged); Decision Evaluation and the Repository Transition Validator
are unmodified and source-agnostic.

## Model Boundary

The model never returns a trusted PCAE object directly. Raw Response
is plain text/JSON only; the Normalizer is the sole permitted
conversion point and rejects malformed/out-of-schema/unauthorized-field
output outright rather than coercing it. The model has no tool-call
authority, no file-write access, and no `pcae` command invocation
ability during its call.

## Default Same-Model Mode

The current acting model may be the advisory model by default — no
new configuration file, CLI flag, environment variable, or model
registry entry is required. Rationale: a model reviewing its own prior
work is still only producing Evidence, never a decision; the
never-sole-authority-for-Accept rule (Section 6) holds identically
whether one model or two are involved, so requiring a second
configured model for this case would add no safety benefit.

## Future Split-Model Mode

Documented, not implemented: a future configuration may distinguish a
writer model (performs the session's changes) from an advisory model
(reviews them), to reduce same-model blind-spot risk and keep
provenance unambiguous. No schema, selection logic, or adapter is
added by this phase.

## Safety Rules

Advisory evidence must be probabilistic by default
(`EvidenceDeterminism.PROBABILISTIC`), model-produced (labelled via
existing `Evidence.provenance`/`RepositorySkillManifest.model_produced`
fields — no schema change), never sole authority for Accept, may
trigger human review (existing `InvariantStatus`/severity mechanism),
may suggest repair (existing `InvariantResult.suggested_repair`), must
include non-empty `limitations`, and must cite references where
possible (`Evidence.references`/`EvidenceReference`). No new field,
enum value, or type is required anywhere in `core/evidence.py`,
`core/decision_evaluation.py`, or `core/repository_skills.py`.

## Failure Behavior

A failed advisory model invocation must produce `UNKNOWN`-freshness
evidence (115D's pattern) or an explicit `RepositorySkillResult`
failure (115I/115J's two-outcome contract) — never blocking
deterministic checks by itself, and never silently succeeding.

## First Future Pilot Scope

Narrowly scoped to repository consistency review, documentation
consistency review, and report consistency review — each a
probabilistic softening of an existing 115H deterministic skill
concept. Explicitly excludes code execution, lifecycle authority, and
commit/push/finalize authority.

## Wire Diagram Summary

Two Mermaid diagrams: the advisory pipeline itself (Repository State
through Repository Transition Validator), and how an Advisory
Repository Skill plugs into the existing Repository Skills wire
diagram alongside deterministic skills, both merging into one
undifferentiated `EvidenceCollection`.

## Tests

`tests/test_phase_115p_advisory_repository_skills_architecture.py`
(new): architecture/documentation verification only. Verifies both new
docs exist and contain: the Advisory Repository Skill definition, the
frozen advisory pipeline (all seven stages), the model boundary, the
default same-model mode, the future split-model mode, the seven safety
rules, failure behavior, the first future pilot scope (in-scope and
out-of-scope), both Mermaid diagrams, and explicit "no implementation"/
"execution capability remains unavailable" confirmations. No
implementation-claim strings are asserted to exist — the tests confirm
none were added.

## Validation

- focused architecture/documentation tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115P`: see final report

## Governance

No Advisory Repository Skill implemented, no model call implemented,
no DeepSeek/GLM/Claude/Codex/Qwen/OpenAI/local-SLM/any-backend
integration, no model configuration added, no Repository Skills
runtime, Evidence Provider, Decision Evaluation, Repository Transition
Validator, or lifecycle command modified.

Execution capability remains unavailable. Runtime state remains
Observed. Maximum plugin capability remains `observe`.

## Recommended Next Phase

115Q — Advisory Repository Skills Contract Freeze
