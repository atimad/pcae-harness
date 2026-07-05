# PCAE Repository Skills

## Purpose

Repository Skills are the future evidence-provider architecture for
PCAE repository decisions. Phase 115A defines the contract only. No
runtime implementation, plugin loading, command integration, lifecycle
mutation, or execution capability is introduced.

## Skill Contract

A Repository Skill collects deterministic evidence for the Repository
Decision Framework.

A skill:

- collects evidence
- reports evidence source, category, confidence, and freshness
- is deterministic for the same repository state and transition
- is model-independent
- is read-only unless a later phase explicitly designs a separate,
  governed mutation system

A skill never:

- never mutates repository state
- never authorizes transitions
- votes on decisions
- overrides another skill
- never promotes artifacts
- never sends notifications
- never bypasses the Repository Transition Validator
- invokes runtime execution
- changes lifecycle commands
- depends on model identity

## Initial Skills

| Skill | Evidence Responsibility |
| --- | --- |
| Git Skill | branch, dirty tree, commit identity, diff scope, push state |
| Task Skill | active task, task status, allowed files, forbidden files |
| Report Skill | phase report identity, completeness, recommended next phase |
| Architecture Skill | architecture boundary claims, invariant references, status docs |
| Runtime Skill | runtime state, execution availability, maximum plugin capability |
| Notification Skill | notification eligibility, idempotency, delivery markers |
| Governance Skill | `pcae health`, `pcae check`, task-memory, push-check readiness |

## Future Skills

Future Repository Skills may include:

- Static Analysis Skill
- Security Skill
- Performance Skill
- Documentation Skill
- Dependency Skill
- AI Review Skill
- Model Review Skill

These future skills still produce evidence only. For example, an AI
Review Skill may summarize a code review finding into structured
evidence, but it cannot accept or reject a transition. A Security Skill
may flag a credential leak as blocking evidence, but the centralized
Decision Framework decides the transition verdict.

## Skill Composition

Skills compose by contributing evidence to a shared evaluation set. They
do not compose by priority, voting, quorum, or override.

If two skills produce conflicting evidence, the conflict itself becomes
evidence. The centralized framework evaluates the conflict against
invariants and severity rules. Conflict may produce Reject, Quarantine,
or Requires Human Review; it is never settled by giving one skill hidden
authority over another.

## Relationship To Kernel Primitives

Repository Skills are not kernel primitives. They sit before Decision
Evaluation and disappear after evidence is collected.

```
Repository State -> Repository Skills -> Evidence -> Decision Framework
```

The four frozen kernel primitives remain Repository State, Repository
Transition, Repository Artifact, and Repository Event. Repository
Decision remains a computation. Evidence remains evaluation-scoped.
Skills remain evidence producers.

## Future Enablement

The skill architecture enables DeepSeek, Claude, Codex, GLM, future SLMs,
humans, and automation without architectural change because all actors
consume the same explanations and all providers produce deterministic
evidence independent of actor identity.

Execution capability remains unavailable.
