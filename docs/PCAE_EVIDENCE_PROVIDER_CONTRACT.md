# PCAE Evidence Provider Contract

## Purpose

Evidence Providers are future read-only producers of Evidence for the
Repository Decision Framework. Phase 115B freezes their contract without
implementing providers.

Evidence Providers collect evidence. They never decide.

## Provider Contract

An Evidence Provider must declare:

| Declaration | Meaning |
| --- | --- |
| Provider ID | Stable provider identifier within the future provider registry. |
| Producer label | Human-readable producer label used in Evidence `producer`. |
| Determinism class | Default determinism class for emitted evidence. |
| Evidence categories produced | Frozen categories the provider may emit. |
| Required repository inputs | Files, command outputs, metadata, or repository facts needed to collect evidence. |
| Scope | Repository paths, phase scope, transition type, or subsystem covered. |
| Limitations | Known caveats and unsupported cases. |

## Provider Responsibilities

A provider:

- collects evidence
- emits required Evidence fields
- declares determinism class
- declares evidence categories produced
- declares required repository inputs
- preserves conflicting observations when visible
- labels stale, expired, or unknown freshness
- labels probabilistic or human-asserted evidence correctly

## Provider Prohibitions

A provider never:

- decides a transition
- votes on a transition
- mutates repository state
- never mutates repository state
- promotes artifacts
- sends notifications
- bypasses the Repository Transition Validator
- never bypasses the Repository Transition Validator
- authorizes execution
- invokes runtime execution
- changes lifecycle command behavior
- overrides another provider
- hides conflicting evidence

## Provider Examples

| Provider | Categories | Determinism |
| --- | --- | --- |
| Git Provider | `git`, `push_state` | `deterministic` |
| Task Provider | `task`, `governance` | `deterministic` |
| Phase Provider | `phase`, `metadata` | `deterministic` |
| Report Provider | `report`, `metadata`, `documentation` | `deterministic` |
| Architecture Provider | `architecture`, `documentation` | `deterministic` |
| Runtime Provider | `runtime` | `deterministic` |
| Notification Provider | `notification`, `metadata` | `deterministic` |
| Governance Provider | `governance`, `test_result` | `deterministic` |
| Static Analysis Provider | `security`, `documentation`, `test_result` | `reproducible_external` |
| AI Review Provider | `ai_review`, `documentation`, `security` | `probabilistic` |

## Conflict Handling

Providers do not resolve conflicts. If a provider can see two conflicting
facts, it emits both or emits an explicit conflict evidence item. If
separate providers emit conflicting evidence, the Decision Framework
preserves both items and evaluates the conflict centrally.

## Persistence Boundary

Providers produce transient evidence for one evaluation. They do not own
raw evidence persistence. Future persistence must be defined by a
separate Repository Artifact contract.

## AI Provider Boundary

An AI Review Provider is advisory and probabilistic by default. It may
produce repair suggestions and risk observations, but it must never be
the sole authority for Accept, artifact promotion, notification,
execution, or lifecycle mutation.

No Evidence Provider implementation is added by Phase 115B.

Execution capability remains unavailable.
