# PCAE Advisory Runtime Contract

**Frozen by**: Phase 113B | **Status**: contract/freeze only — no
advisory runtime implementation, advisory execution, command
authorization, command denial, Permission Broker enforcement, runtime
execution, plugin loading, plugin instantiation, plugin invocation,
dependency injection, shell mediation, backend invocation, adapter
invocation, execution enablement, execution capability, automatic
apply, audit persistence, rollback execution, Telegram inbound, REST
server, web UI, daemon, or background workers is performed by this
document or this phase.

## Purpose

113A designed the Advisory Runtime — a five-stage pipeline (Runtime
Snapshot → Analysis → Recommendation → Advisory Result → Presentation)
and a nine-field `AdvisoryResult` sketch — but froze no contract for
it: nothing yet said exactly which fields are required, how a result
explains itself, how evidence is referenced, what reproducibility
means precisely, or what "additive" means for this specific model.
Before any advisory implementation begins (113C), this document
freezes that contract, extending 113A's nine-field model only where
justified, never silently.

## New Principle

```
Explainability precedes trust.
```

Restated from this phase's own architectural principles list: a human
cannot be expected to trust a recommendation they cannot verify. Every
`AdvisoryResult` must therefore explain itself completely enough that
a human could, in principle, re-derive it from the referenced Runtime
Snapshot without needing to trust the Advisory Runtime's internal
reasoning as a black box. This is the direct analytical-layer
counterpart to "Visibility precedes authority" (111A) — that principle
governs whether a human can *see* Runtime state; this one governs
whether a human can *verify* a recommendation about it.

## 1. Advisory Result Contract (Frozen)

**Starting point: 113A's nine fields, extended by five, with one name
reconciled.** The brief for this phase suggested `recommendation` as a
field name; 113A already froze `recommended_action` for the identical
concept. This document does not add a duplicate — `recommendation`
is realized as `recommended_action`, unchanged from 113A, avoiding two
fields for one idea.

| # | Field | Frozen since | Meaning |
|---|---|---|---|
| 1 | `advisory_id` | 113A | Stable, never-reused identifier, mirroring `COMP-NNN`/`INT-NNN`/`ISP-NNN` discipline (107B/109C/110B). |
| 2 | `category` | 113A | One of §4's advisory categories (open taxonomy). |
| 3 | `severity` | 113A | One of §5's four severity levels. |
| 4 | `confidence` | 113A | One of §5's four confidence levels (reused verbatim from this codebase's own capability-discovery vocabulary). |
| 5 | `recommended_action` | 113A | Free-text description of what a human might consider doing. Never executable. |
| 6 | `rationale` | 113A | Free-text explanation of why this recommendation was produced — the fuller, detailed explanation. |
| 7 | `evidence_references` | 113A, structure frozen here (§3) | A tuple of `EvidenceReference` records (§3), each a dot-path pointer into the Runtime Snapshot fields that produced this finding. |
| 8 | `affected_runtime_objects` | 113A | A tuple of identifiers naming which already-identified Runtime/Context/Registry objects this result concerns, reusing 112B's own frozen identity formats. |
| 9 | `timestamp` | 113A | ISO 8601 timestamp of production, matching `.pcae/session.json`'s own convention. |
| 10 | `source_snapshot_reference` | **New, 113B** | A reference to the exact Runtime Snapshot this result was derived from (e.g. its `context.session_id` plus production `timestamp`, since Runtime Snapshot itself is never persisted, 112F §7's "no mutable internal references" combined with 112E's own non-persistence) — the field the reproducibility rule (§2) anchors to. |
| 11 | `reasoning_summary` | **New, 113B** | A short, single-line synthesis of "what was observed and why it matters" — the concise counterpart to the fuller `rationale`, mirroring 112F §5's own "default output concise, verbose output detailed" discipline for Runtime Snapshot's human-readable rendering, applied here to one field's own two levels of detail. |
| 12 | `alternative_considerations` | **New, 113B** | A tuple of free-text alternative interpretations or actions considered and not recommended, and why — required by "Explainability precedes trust": a recommendation that hides the alternatives it rejected is less verifiable than one that names them. |
| 13 | `remediation` | **New, 113B** | Free-text, concrete, mechanical steps a human could take — distinct from `recommended_action` (the higher-level suggested course of action). Never executable, exactly as `recommended_action` is never executable. |
| 14 | `implementation_status` | **New, 113B** | Reuses this codebase's own existing field convention verbatim (`PermissionBrokerDecision.implementation_status`, 108A) — unconditionally `"execution_unavailable"` today, on every `AdvisoryResult`, since no advisory implementation exists yet. |

**Justification standard applied to every new field.** Each of the
five new fields traces directly to one of objective 2's eight required
explainability facets (§2) or to the new "Explainability precedes
trust" / reproducibility principles — none was added merely because
the brief suggested it was possible; `recommendation` was specifically
*not* added as a fifteenth field because it would have duplicated
`recommended_action` without adding information.

**No implementation.** No field above is a concrete Python type — a
future implementation phase (113C, prototype; a later phase, contract
freeze of the concrete type) chooses the representation, exactly as
112A's twelve objects were frozen as a field list before 112B/112C
gave them one.

## 2. Explainability Contract (Frozen)

Every `AdvisoryResult` must explain all eight of the following, each
mapped to a specific field or a fixed, universal invariant (not a
per-instance field, since it never varies):

| Explains | Realized by |
|---|---|
| What was observed | `reasoning_summary` (concise) + `rationale` (full) |
| Why it matters | `severity` + `rationale` |
| What evidence supports it | `evidence_references` |
| What Runtime Snapshot fields were used | `evidence_references`' own `field_path` (§3) + `source_snapshot_reference` |
| What recommendation was made | `recommended_action` |
| What remediation is suggested | `remediation` |
| Why this is advisory only | A fixed, universal invariant restated identically on every result (below) — never a per-instance field, since it is always true |
| Why no authorization or execution follows | Same fixed invariant |

**The fixed invariant** (restated verbatim on every `AdvisoryResult`,
in whatever presentation renders it, per §7): *"This is an advisory
recommendation only. No execution or authorization follows
automatically from it — a human decides, per 'Recommendation precedes
authorization' (113A) and 'Explainability precedes trust' (113B)."*
This is a contract-level constant, not a fourteenth field, because a
field that never varies belongs in the contract's prose, not in every
instance's payload — the same reasoning `runtime_snapshot.py` (112E)
already applies to constants like `EXECUTION_AVAILABILITY`.

**Reproducibility principle (frozen):**

```
Every recommendation must be reproducible from the Runtime Snapshot.
```

Given the exact Runtime Snapshot named by `source_snapshot_reference`
and the same (future) Analysis logic version, re-running Analysis must
produce the identical `AdvisoryResult` (identical `category`/`severity`/
`confidence`/`recommended_action`, though `advisory_id`/`timestamp`
may differ per production event). This restates 110A §6's already-
frozen "Deterministic" Runtime Principle ("for a given intent and a
given set of plugin responses, the Runtime's sequencing and state
transitions must be reproducible") for the Advisory Runtime
specifically: the *given input* is a Runtime Snapshot, and the
*required determinism* is Analysis's own output. This does not require
storing every Runtime Snapshot ever produced (§3 explicitly forbids an
evidence database) — it requires that Analysis, as a function, is pure
and deterministic given an equivalent snapshot.

## 3. Evidence Model (Frozen)

**No evidence database. No audit persistence.** Evidence is referenced,
never stored durably — the same discipline 112F §7 already applies to
Runtime Snapshot's own "no mutable internal references" rule, and the
same reasoning 112A §7 gave for Broker Decision/Observation state
remaining session-only: an evidence *store* would be a new persistence
mechanism, explicitly out of this phase's hard boundary.

**`EvidenceReference` (frozen field sketch, architecture only):**

| Field | Meaning |
|---|---|
| `domain` | One of Runtime Snapshot's nine frozen top-level domains (112F §2: `runtime`/`registry`/`plugins`/`capabilities`/`health`/`governance`/`state`/`version`/`context`). |
| `object_id` | Optional — a context object ID (`session_id`/`task_id`), a registry/plugin/capability ID, present only when the evidence concerns a specific identified object rather than a domain-wide fact. |
| `field_path` | A dot-path string into the named domain (e.g. `"health.plugin_count"`, `"context.session_id"`, `"registry.registered_plugin_count"`) — never a copy of the value itself, mirroring 112B §2's identity-reference discipline (a `BrokerDecisionContext` references a decision, never copies it). |
| `evidence_summary` | A short, human-readable gloss of what the referenced value was, at production time (e.g. `"plugin_count = 0"`) — the one piece of the evidence that *is* captured directly in the `AdvisoryResult`, since the underlying Runtime Snapshot itself is never persisted (§2's reproducibility principle) and a bare field path alone would be unverifiable after the fact without it. |

`governance status`, `health status`, and `observation integration id`
(named in this phase's own brief as example evidence concepts) are
each realized as a `domain`+`field_path` pair, not a distinct
`EvidenceReference` shape of their own — e.g. governance status is
`domain="governance"`, `field_path="governance.broker_implementation_status"`;
an observation integration ID is `domain="context"`,
`field_path="context.observation.consulted_integrations"`,
`object_id` naming the specific `INT-NNN` entry. One frozen shape
covers every evidence concept objective 3 named; inventing a
per-concept shape for each would duplicate the same information across
multiple record types.

## 4. Advisory Categories (Frozen, Extension Rules Added)

113A's eight categories are the frozen baseline, unchanged:

| Category | Meaning |
|---|---|
| Runtime Health | `health` domain conditions |
| Governance | `governance` domain conditions |
| Context Consistency | `context` domain conditions |
| Registry | `registry` domain conditions |
| Plugin Compatibility | `plugins`/`capabilities` domain conditions |
| Configuration | Policy/config-shaped conditions |
| Operational Readiness | Cross-domain conditions spanning more than one Snapshot domain |
| *(Future extensibility)* | Reserved placeholder, not a real category |

**Extension rule (new, 113B):** the taxonomy remains open (113A §4) —
new categories may be added freely by a future phase without a
contract-breaking change. However, **an existing category's *meaning*
is frozen** once published in this document: redefining what
"Governance" or "Registry" means (as opposed to adding a ninth
category alongside them) is a breaking change requiring the same
deliberate, documented decision 112F §3 requires for a Runtime
Snapshot key rename. Addition is free; redefinition is not.

## 5. Severity and Confidence Semantics (Frozen)

**Severity (113A's four levels, meanings frozen here):**

| Level | Meaning |
|---|---|
| `info` | Worth noting; no action expected. |
| `advisory` | Worth considering; a human may reasonably act or not. |
| `warning` | Should be addressed reasonably soon; a human should not ignore this indefinitely. |
| `critical` | Significant risk to Runtime operation or governance; warrants prompt human attention. |

None of the four ever blocks, denies, or authorizes anything — `severity`
is a hint to a human's attention, never an enforcement signal, exactly
as 113A already distinguished this vocabulary from `dry_run.py`'s
enforcement-flavored `simulation_severity`.

**Confidence (113A's four levels, reused verbatim from
`src/pcae/core/agent.py`'s own capability-discovery vocabulary,
meanings frozen here in the advisory context):**

| Level | Meaning in Advisory Runtime |
|---|---|
| `unknown` | Analysis could not establish this finding's grounding with any real evidence. |
| `observed` | Grounded in at least one real Runtime Snapshot field, not independently cross-checked. |
| `validated` | Grounded in multiple, mutually-consistent Runtime Snapshot fields. |
| `proven` | Grounded in a Runtime Snapshot field that is itself a frozen, already-verified contract value (e.g. `health.execution_availability`, always `"unavailable"`). |

**Severity and confidence are orthogonal, never conflated.** A finding
may be `critical` severity with `unknown` confidence (something looks
very wrong, but the grounding is weak) or `info` severity with `proven`
confidence (a routine, well-established fact) — both axes must be
reported independently on every `AdvisoryResult`; no future
implementation may collapse them into one combined score.

**Uncertainty and ambiguity, handled fail-closed (110A §6's own "Fail-
closed" principle, applied here):** when Analysis cannot confidently
resolve to one interpretation, the correct response is to lower
`confidence`, populate `alternative_considerations` with the competing
interpretations, or emit multiple lower-confidence `AdvisoryResult`
records — never to silently pick one interpretation and report it at
an inflated confidence level. Fabricating certainty is a fail-open
failure mode this contract forbids.

## 6. Advisory Lifecycle (Frozen, Contract Only)

A fourth, distinct lifecycle vocabulary in this codebase — not to be
conflated with 110A §8's Runtime State Model (an intent's pipeline
progression), 110B §4's Plugin Lifecycle (a plugin's existence), or
112A §4's Context Lifecycle (a Context object's existence). Six stages
frozen:

| Stage | Meaning | Status today |
|---|---|---|
| `produced` | The `AdvisoryResult` has been created by the Advisory Result stage (113A §2). | Contract only — no implementation exists to produce one. |
| `presented` | The result has been rendered by a Presentation consumer (§7). | Contract only. |
| `acknowledged` *(future)* | A human has confirmed they have seen this result. | Not implemented — no mechanism exists anywhere in this codebase. |
| `superseded` *(future)* | A later `AdvisoryResult` has replaced this one's relevance (e.g. the underlying condition changed). | Not implemented. |
| `resolved` *(future)* | The underlying condition this result described no longer holds. | Not implemented. |
| `dismissed` *(future)* | A human has explicitly chosen to disregard this result. | Not implemented. |

**Current implementation status: contract only.** No lifecycle
mechanism, storage, or transition logic exists. `produced`/`presented`
are the only two stages any real (future) code path could reach today,
since neither requires anything beyond the pipeline (113A §2) this
document doesn't implement either. The four future stages are named,
exactly as 112A §3 named `ExecutionContext`/`AuditContext`/
`RollbackContext` as stubs before any implementation existed, so a
future phase has a frozen vocabulary to design against.

## 7. Presentation Contract (Frozen)

Restated from 113A §7, frozen as a contract rather than a design
intent: `AdvisoryResult` records may later be rendered by CLI,
Telegram, REST, Dashboard, or AI agents (113A's own five named
consumers) — **every consumer must render the same underlying
`AdvisoryResult` model**, unchanged, exactly as 112F §1/§6 already
froze this rule for Runtime Snapshot's own consumers. A consumer may
choose *how much* detail to show (e.g. `reasoning_summary` only in a
compact view, full `rationale`/`alternative_considerations` in a
detailed view — mirroring 112F §5's concise-default/detailed-verbose
split) but may never show a *different* fact than another consumer
would for the same `AdvisoryResult`. No presentation implementation is
added by this phase.

## 8. Safety Rules (Frozen, Absolute — Extended from 113A's Seven)

`AdvisoryResult`s, and the Advisory Runtime that would produce them,
must never, unconditionally:

1. **Execute** (113A).
2. **Authorize** (113A).
3. **Deny** (**new, 113B** — an `AdvisoryResult` is never itself a
   denial either; it recommends, it never blocks).
4. **Mutate Runtime Snapshot** (113A).
5. **Mutate Runtime Context** (113A).
6. **Invoke Permission Broker** (113A).
7. **Invoke shell/backend/adapters** (113A, restated as one item here;
   113A froze shell and adapters as two separate rules — unchanged in
   substance, combined in this list's own numbering only).
8. **Imply approval** (**new, 113B** — no `AdvisoryResult` field or
   presentation may be worded or rendered in a way a human could
   mistake for an approval already having been granted; this is the
   direct, testable form "Recommendation precedes authorization"
   (113A) takes for this specific contract).
9. **Bypass human review** (**new, 113B** — no future mechanism may
   act on an `AdvisoryResult` without an explicit human decision
   in between; this restates 110A §6's "Human-controlled" principle
   for the advisory layer specifically).
10. **Bypass future audit** (**new, 113B** — once `COMP-007` (Audit
    Boundary) exists, any future mechanism that acts on an
    `AdvisoryResult` must still produce its own evidence record;
    nothing about an `AdvisoryResult` existing may be used to justify
    skipping that future requirement).

## 9. Compatibility Rules (Frozen)

Directly mirroring 112F §3/§4's own Runtime Snapshot compatibility
discipline, applied to the Advisory Result contract instead of the
Snapshot JSON schema:

1. **Additive-only changes within the same contract major version.** A
   new field, or a new category (§4), may be added without a version
   bump.
2. **Breaking changes require a major version bump.** Removing a
   field, renaming a field, or changing an existing category's
   *meaning* (§4) requires a major version increment, mirroring 112F
   §3 rule 3 exactly.
3. **Consumer expectations.** Every future consumer (§7) must ignore
   unknown fields it doesn't recognize — the same rule 112F §3
   already froze for Runtime Snapshot's own consumers, restated here
   for `AdvisoryResult`.
4. **Unknown field handling.** Identical to rule 3: an unrecognized
   field in a later, compatible contract version must never cause a
   consumer to fail closed on the *entire* result — only a missing
   *required* field triggers that.
5. **Reproducibility expectations.** Restated from §2: a consumer
   receiving two `AdvisoryResult` records with the same
   `source_snapshot_reference` and the same contract major version may
   expect their `category`/`severity`/`confidence`/`recommended_action`
   to agree, if produced by the same (future) Analysis logic version.

**No versioning field is added by this phase.** Consistent with 112F
§4's own decision for Runtime Snapshot (no `snapshot_schema_version`
field implemented during a freeze phase), this document does not add
an `advisory_contract_version` field to the `AdvisoryResult` sketch —
doing so would require an implementation this phase's hard boundary
forbids. The contract above governs whichever future phase implements
`AdvisoryResult` for the first time.

## No-Go Confirmations

No advisory runtime implementation. No advisory execution. No command
authorization. No command denial. No Permission Broker enforcement. No
runtime execution. No plugin loading. No plugin instantiation. No
plugin invocation. No dependency injection. No shell mediation. No
backend invocation. No adapter invocation. No execution enablement. No
execution capability. No automatic apply. No audit persistence. No
rollback execution. No Telegram inbound. No REST server. No web UI. No
daemon. No background workers. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision and on every (future) `AdvisoryResult`. Current maximum
runtime state remains `Observed` (110A §8, unchanged). Current maximum
plugin capability remains `observe` (110B §3, unchanged). `v0.1.0-rc1`
remains non-executing by design. v0.2 remains the autonomy target
(Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and branch
protection on `main` are unchanged. No new tag. No new GitHub Release.
No PyPI/GitHub Packages publication.

## Recommended Next Phase

**113C — Advisory Runtime Prototype (Observation-Only).**
