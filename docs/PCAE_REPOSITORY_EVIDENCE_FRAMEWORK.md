# PCAE Repository Evidence Framework

## Purpose

This document freezes the Repository Evidence Framework contract
introduced in Phase 115A. Evidence informs Repository Decisions; it does
not decide, mutate repository state, promote artifacts, send
notifications, authorize execution, or become a Repository State Kernel
primitive. Evidence does not become a Repository State Kernel primitive.

Phase 115B is architecture and contract only. It implements no runtime
behavior, no Repository Transition Validator behavior changes, no
lifecycle command changes, no Notification Policy changes, no Repository
Skills, no execution, no authorization, no Permission Broker enforcement,
no plugins, no Telegram inbound, no REST, no Web UI, and no Dashboard.

## Evidence Contract

An Evidence item is a deterministic or explicitly classified observation
available during one decision evaluation.

Required fields:

| Field | Required Semantics |
| --- | --- |
| `evidence_id` | Stable identifier within one evaluation. May be cited by explanations. |
| `source` | Human-readable subsystem/source name, such as Git or Runtime Inspect. |
| `category` | One frozen category from the Evidence Category set. |
| `producer` | Provider or actor that produced the evidence item. |
| `timestamp_utc` | UTC timestamp for collection or assertion time. |
| `freshness` | One of `current`, `stale`, `expired`, or `unknown`. |
| `confidence` | Confidence level derived from source quality and collection method. |
| `determinism` | One of the frozen determinism classes. |
| `scope` | Repository path, transition, phase, command, or invariant scope. |
| `references` | Related commit hashes, file paths, report paths, event IDs, or prior evidence IDs. |
| `observed_value` | Structured observed fact. |
| `expected_value` | Structured expected fact when applicable; may be `none`. |
| `explanation` | Deterministic summary of what the evidence means. |
| `limitations` | Known caveats, missing inputs, or boundaries for use. |

Evidence must be structured enough that a future explanation can cite it
without relying on conversational context or AI-generated prose.

## Evidence Identity

Evidence IDs are stable within one evaluation. Stability means the same
provider run within the same evaluation must refer to the same evidence
item with the same `evidence_id`, so explanations can cite it reliably.

Evidence IDs are not global permanent repository IDs unless they are
persisted inside a Repository Artifact or another future durable record.
Until persistence exists, evidence identity is evaluation-local.

Examples:

```
E-git-001
E-metadata-002
E-runtime-003
E-ai-review-004
```

## Evidence Categories

Frozen minimum category set:

| Category | Meaning |
| --- | --- |
| `git` | Branch, dirty tree, commit identity, diff, or git-derived state. |
| `task` | Active task, task scope, acceptance criteria, or task lifecycle state. |
| `phase` | Phase identity, phase ordering, or phase lifecycle facts. |
| `report` | Phase report content, completeness, trust, or canonical status. |
| `metadata` | Structured metadata files or declared metadata values. |
| `architecture` | Architecture docs, boundaries, invariants, or status claims. |
| `runtime` | Runtime state, execution availability, or plugin capability. |
| `push_state` | Live or declared push cleanliness and origin/main comparison. |
| `notification` | Notification eligibility, dispatch marker, or delivery result. |
| `governance` | `pcae health`, `pcae check`, task-memory, push-check, or similar governance result. |
| `test_result` | Test command, result, count, or failure classification. |
| `security` | Security scanner, secret scan, dependency risk, or safety finding. |
| `documentation` | Documentation coverage, doc freshness, or doc drift. |
| `ai_review` | SLM/LLM/model-produced review evidence. |
| `unknown` | Evidence that cannot safely be assigned a more specific category. |

`unknown` is a containment category, not a shortcut. Unknown-category
evidence should lower confidence or require human review when it matters
to a blocking decision.

## Determinism Levels

| Level | Semantics | Examples |
| --- | --- | --- |
| `deterministic` | Same repository state and same inputs produce the same observed value. | Git evidence, Runtime Inspect output, parsed metadata. |
| `reproducible_external` | Reproducible when the same external tool/version/input is available. | Security scanner, dependency scanner, static analysis tool. |
| `probabilistic` | Output may vary across runs even with similar inputs. | SLM/LLM review, heuristic model scoring. |
| `human_asserted` | Human-provided assertion or approval note. | Human approval note, manual review statement. |
| `unknown` | Determinism cannot be classified safely. | Unlabeled imported evidence. |

Determinism class is declared by the provider and may be used by the
Decision Framework when choosing Accept, Reject, Quarantine, or Requires
Human Review. Determinism never lets evidence bypass invariants.

## Confidence Semantics

Confidence describes trust in the evidence item, not trust in the
transition.

Frozen confidence levels:

| Level | Semantics |
| --- | --- |
| `high` | Source is authoritative for the scoped fact and collection succeeded. |
| `medium` | Source is relevant but indirect, partial, or dependent on external conditions. |
| `low` | Source is weak, stale-adjacent, incomplete, or only advisory. |
| `unknown` | Confidence cannot be determined safely. |

Confidence must not override hard invariants. A high-confidence failure
of a blocking invariant still blocks. A low-confidence positive signal
does not authorize acceptance. Low-confidence evidence may require human
review. Probabilistic evidence may never alone authorize canonical
mutation. Probabilistic evidence may never alone authorize canonical mutation.

## Freshness Semantics

| Freshness | Semantics |
| --- | --- |
| `current` | Collected from current repository state or explicitly tied to the evaluated transition. |
| `stale` | Collected from an older state, older commit, older report, or outdated metadata. |
| `expired` | Past a defined validity window or invalidated by newer repository state. |
| `unknown` | Freshness cannot be determined safely. |

Stale evidence is preserved and labelled. It is never silently discarded
or chosen over current evidence. Stale evidence can downgrade confidence,
block canonical promotion, trigger quarantine, or require human review
depending on the invariant and severity.

## Conflict Semantics

When evidence items conflict:

- preserve both evidence items
- mark the conflict explicitly
- do not silently choose one item
- do not let a provider resolve the conflict by priority or vote
- evaluate the conflict centrally in the Decision Framework

Example conflict:

```
E-metadata-002: pushed_status = not_pushed
E-git-001: live origin/main..HEAD = 0
Conflict: declared push state disagrees with live push state
```

The Decision Framework decides whether this conflict is acceptable,
quarantine-worthy, rejected, or requires human review.

## Explanation References

Decision explanations must be able to cite Evidence IDs. References are
structured links from an explanation to the evidence that caused or
supported the result.

Example:

```
Decision: Reject
Reason: invariant phase_identity_consistency failed
Evidence Used:
  - E-git-001
  - E-metadata-002
Invariant(s):
  - phase_identity_consistency
```

Explanations may summarize evidence, but the authoritative link is the
evidence ID reference.

## Persistence Boundary

Evidence is transient during evaluation. It is not a kernel primitive and
is not automatically persisted.

Evidence may be summarized or referenced inside a Transition Result or a
Repository Artifact. Raw evidence persistence is future work and is not
implemented by Phase 115B. Raw evidence persistence is not implemented by Phase 115B.
If future phases persist raw evidence, they must define
artifact format, lifecycle, redaction, retention, and identity rules
explicitly.

## SLM / AI Evidence Boundary

Future SLM/LLM evidence is advisory only and probabilistic by default
unless a later phase deliberately designs a stronger contract.

SLM/AI evidence:

- is advisory only
- is `probabilistic` by default
- is never sole authority for Accept
- may trigger Requires Human Review
- may suggest repairs
- must be labelled model-produced if used
- must declare producer, model/source label, limitations, and scope

SLM/LLM evidence may help explain likely risk or suggest repair, but it
cannot alone authorize canonical mutation, artifact promotion,
notification, execution, or lifecycle transition.

No SLM integration is implemented here.

## Frozen Boundaries

This framework freezes the contract only. It does not add an Evidence
class, provider registry, storage backend, validator integration, runtime
execution, Repository Skill implementation, plugin loading, Permission
Broker enforcement, Telegram inbound, REST, Web UI, Dashboard, or any
lifecycle command behavior.

Execution capability remains unavailable.
