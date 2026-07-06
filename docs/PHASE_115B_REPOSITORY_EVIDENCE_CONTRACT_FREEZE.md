# Phase 115B — Repository Evidence Framework Contract Freeze

## Status

Completed. Architecture and contract only: no runtime implementation, no
Repository Transition Validator behavior changes, no lifecycle command
changes, no Notification Policy changes, no Repository Skills
implementation, no execution, no authorization, no Permission Broker
enforcement, no plugins, no Telegram inbound, no REST, no Web UI, and no
Dashboard.

## Purpose

Freeze the exact structure, semantics, and constraints for Evidence used
by PCAE decisions.

Canonical contract documents:

- `docs/PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md`
- `docs/PCAE_EVIDENCE_PROVIDER_CONTRACT.md`

## Evidence Contract Summary

Evidence informs decisions. Evidence does not decide. Evidence does not
mutate repository state. Evidence does not become a kernel primitive.

Required Evidence fields are frozen:

- `evidence_id`
- `source`
- `category`
- `producer`
- `timestamp_utc`
- `freshness`
- `confidence`
- `determinism`
- `scope`
- `references`
- `observed_value`
- `expected_value`
- `explanation`
- `limitations`

## Evidence Identity

Evidence IDs are stable within one evaluation and may be cited by
explanations. They are not global permanent repository IDs unless a
future phase persists them inside a Repository Artifact.

## Evidence Categories

The frozen minimum category set is:

`git`, `task`, `phase`, `report`, `metadata`, `architecture`, `runtime`,
`push_state`, `notification`, `governance`, `test_result`, `security`,
`documentation`, `ai_review`, and `unknown`.

## Determinism Model

Frozen determinism levels:

- `deterministic`
- `reproducible_external`
- `probabilistic`
- `human_asserted`
- `unknown`

Git and Runtime Inspect evidence are deterministic. Security scanners are
reproducible_external. SLM/LLM review is probabilistic. Human approval
notes are human_asserted.

## Confidence Model

Confidence levels are `high`, `medium`, `low`, and `unknown`.
Confidence describes trust in the evidence item, not permission to accept
a transition. Confidence must not override hard invariants. Low
confidence evidence may require human review. Probabilistic evidence may
never alone authorize canonical mutation.

## Freshness Model

Freshness levels are `current`, `stale`, `expired`, and `unknown`.
Stale evidence is preserved and labelled. It may downgrade confidence,
block canonical promotion, trigger quarantine, or require human review.
It is never silently chosen over current evidence.

## Evidence Provider Contract Summary

Providers collect evidence and never decide. Providers must declare
their determinism class, evidence categories produced, required
repository inputs, scope, and limitations. Providers never mutate state,
promote artifacts, send notifications, bypass the validator, authorize
execution, invoke runtime execution, override other providers, or hide
conflicts.

## Conflict Semantics

Conflicting evidence is preserved. PCAE marks the conflict and evaluates
it centrally in the Decision Framework. Providers never silently choose
one conflicting item, vote, or override one another.

## Explanation Reference Model

Decision explanations must be able to cite Evidence IDs:

```
Rejected because invariant phase_identity_consistency failed.
Evidence:
- E-git-001
- E-metadata-002
```

The Evidence ID is the stable explanation reference within the
evaluation.

## Persistence Boundary

Evidence is transient during evaluation. Evidence may be summarized or
referenced inside Transition Result or Repository Artifact. Raw evidence
persistence is future work and is not implemented by Phase 115B.

## SLM / AI Evidence Boundary

Future SLM/LLM evidence is advisory only, probabilistic by default, never
sole authority for Accept, may trigger human review, may suggest repairs,
and must be labelled model-produced if used. No SLM integration is
implemented.

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
- `pcae skill invoke phase-finalization 115B`: see final report

## Governance

No runtime behavior changed. No source runtime, lifecycle, validator,
notification, Permission Broker, plugin, Telegram inbound, REST, Web UI,
or Dashboard code was changed.

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Recommended Next Phase

115C — Repository Evidence Framework Prototype
