# Phase 115A — Repository Decision & Explainability Framework

## Status

Completed. Architecture and contract only: no runtime implementation, no
execution capability, no Repository Transition Validator changes, no
Notification Policy changes, no lifecycle command changes, no Permission
Broker changes, no plugins, no Telegram inbound, no REST, no Web UI, and
no Dashboard.

## Purpose

Design and freeze the framework by which PCAE explains why every
repository transition is accepted, rejected, quarantined, or requires
human review.

Canonical architecture documents:

- `docs/PCAE_DECISION_FRAMEWORK.md`
- `docs/PCAE_REPOSITORY_SKILLS.md`

## Decision Framework Summary

Phase 115A defines the canonical flow:

```
Repository State
        |
        v
Repository Transition
        |
        v
Evidence Collection
        |
        v
Decision Evaluation
        |
        v
Transition Result
        |
        v
Repository Artifact
        |
        v
Repository Event
```

Repository Decision remains a computation, not a fifth Repository State
Kernel primitive. It is the centralized evaluation result over state,
transition, evidence, and invariants, materialized today as
`TransitionResult`.

## Evidence Architecture

Evidence is a first-class architectural concept but not a kernel
primitive. It exists only during evaluation and must be deterministic,
structured, reproducible, and model-independent.

The framework defines:

- Evidence
- Evidence Source
- Evidence Category
- Evidence Confidence
- Evidence Freshness

Examples include Git, Reports, Metadata, Tasks, Architecture, Runtime,
Push State, Notification, Governance, and Tests.

## Evidence Providers

Evidence Providers produce evidence and never decide. Initial providers:

- Git Provider
- Task Provider
- Report Provider
- Architecture Provider
- Runtime Provider
- Notification Provider
- Governance Provider

Future providers may include Static Analysis, Security, Performance,
Documentation, Dependency, AI Review, and Model Review. They remain
evidence-only.

## Decision Evaluation

The frozen pipeline is:

```
Evidence -> Invariant Evaluation -> Decision -> Explanation -> Transition Result
```

Decisions remain deterministic because the same repository state,
transition, provider contracts, evidence set, and invariant set produce
the same verdict and explanation. Providers never vote and never
override one another.

## Explainability Model

Every Transition Result must be explainable. Required explanation fields:

- Decision
- Reason
- Evidence Used
- Invariant(s)
- Severity
- Suggested Repair
- Confidence

No AI-generated prose is required. Explanations are structured data that
can be rendered later for humans or agents.

## Verdict Review

Accept is appropriate when all blocking invariants pass and evidence is
fresh enough for canonical promotion.

Reject is appropriate when a blocking invariant fails and the transition
cannot safely be preserved as a quarantined artifact.

Quarantine is appropriate when the proposed artifact can be preserved for
inspection but must not become canonical.

Requires Human Review is appropriate when deterministic evidence
indicates a transition may be valid but policy requires explicit human
judgment.

## Repository Skills Architecture

Repository Skills are future evidence-provider packages. A skill
collects evidence and never mutates state, authorizes transitions,
promotes artifacts, sends notifications, bypasses the validator, invokes
runtime execution, or depends on model identity.

Skills compose by contributing evidence only. Conflicting evidence is
represented as evidence and evaluated centrally.

## Canonical Wire Diagram

The new canonical Mermaid diagram is in
`docs/PCAE_DECISION_FRAMEWORK.md`. It shows:

Repository State -> Evidence Providers -> Evidence -> Decision Framework
-> Transition Validator -> Transition Result -> Repository Artifact ->
Repository Event -> Notification Policy -> Consumers.

## Future Architecture

This framework enables DeepSeek, Claude, Codex, GLM, future SLMs, humans,
and automation without architectural change. The actor proposing a
transition is not an evidence category and does not alter the decision.
The explanation is derived from repository facts, evidence providers,
and centralized invariant evaluation.

## Validation

Validation completed:

- focused architecture/documentation tests: see final report
- `pcae health`: see final report
- `pcae check`: see final report
- `pcae doctor task-memory`: see final report
- `pcae push check`: see final report
- `pcae agent verify-handoff`: see final report
- `pcae session bootstrap --compact --profile implementation`: see final report
- `pcae runtime inspect --json`: see final report
- `pcae notify status`: see final report
- `pcae skill invoke phase-finalization 115A`: see final report

## Governance

No runtime behavior changed. No source runtime, lifecycle, validator,
notification, Permission Broker, plugin, Telegram inbound, REST, Web UI,
or Dashboard code was changed.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Recommended Next Phase

115B — Repository Evidence Framework Contract Freeze
