# Phase 149O.20L.7O.3V — Local-CLI Runtime Dispatch Authority and Permission Contract Freeze

## 1. Objective

Freeze, without implementation, the four separate normative artifacts needed
for a future transition from deterministic dry-runtime simulation toward one
human-authorized real local-CLI dispatch:

1. `RIHAC-001 v1.0` — Runtime Invocation Human Authority Contract;
2. `PBRD-001 v1.0` — PB Runtime Dispatch Extension Contract;
3. `RDGO-001 v1.0` — Runtime Dispatch Gate Ordering Contract; and
4. `RIASC-001 v1.0` — `RuntimeInvocationApproval` Schema Contract.

Real execution is not implemented or activated. The article remains stopped.
The private research repository was not inspected, modified, imported, or
relied upon.

## 2. Baseline

Phase-entry repository evidence:

| Fact | Result |
|---|---|
| Branch/worktree | `main`, clean before governed startup |
| Phase-entry SHA | `934e1f07fac798417c1b5a25d5b06214a5f62ab3` |
| `origin/main` | Same SHA |
| `origin/main..HEAD` | `0` |
| Latest release | `v0.4.3` |
| Release commit | `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime state | `Observed` |
| Maximum capability | `observe` |
| Execution availability | `unavailable` |
| Runtime registry | 0 plugins / 0 capabilities |
| Existing RPAC | RPAC-001 v1.0, FROZEN |
| Existing dry adapter | IMPLEMENTED / VERIFIED / PRODUCTION-CONSUMED |
| Production dry entry | `pcae session bootstrap --compact --dry-runtime --runtime-target <id>` |
| Real runtime ready | NO |

Baseline `pcae health`, `pcae check`, `pcae status coherence`, `pcae
doctor task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae
notify status`, and latest canonical phase-report inspection completed.
Health/check/coherence/push/runtime/notification prerequisites passed. Task
memory reported only the repository's pre-existing historical
`tasks/DONE.md` synchronization debt. No active governed phase existed;
agent custody had already transferred to `codex-local`, and the 3V active
task was opened through `pcae task transition`. A duplicate `pcae phase
start` correctly refused because the transferred agent lock was already held;
no force or lock clearing was used.

## 3. Scope

The contract scope is **LOCAL CLI RUNTIME v1**: one exact local external
process invocation, one exact invocation/target/prompt/repository/task, one
human approval, and no automatic retry.

Excluded: API providers, OpenRouter, provider SDKs, network egress,
provider/model universal fields, credential architecture, parallel
invocations, automatic retries, background execution, unattended execution,
multi-repository execution, unrestricted shell, arbitrary child-process
trees, and multiple external dispatches.

## 4. 3U decisions

Direct primary-source re-reading confirmed, rather than merely restating 3U:

- human authority is a dedicated one-shot `RuntimeInvocationApproval`;
- CHGR extension and phase/session-wide implicit approval remain rejected;
- PB uses additive `action_type=runtime_dispatch`;
- `execution_class=adapter` is reused;
- mode-enum reuse of `adapter_invocation` and composite per-effect PB
  permissions remain rejected for v1;
- local CLI only is ready for freeze;
- API/provider scope remains blocked on unresolved network-egress permission;
- approval consumption is atomic with durable `dispatch_attempted`; and
- the eleven-gate order remains prompt -> target -> static preflight -> human
  authority -> approval validation -> PB -> Runtime Enforcement ->
  containment/live preflight -> durable record -> dispatch -> result intake.

No primary source contradicted the one-shot architecture. Had one done so,
this phase would have stopped.

## 5. RPAC relationship

The freeze preserves RPAC-001 v1.0 and follows the hard serial spine from 3T:

```text
RPAC-044 -> RPAC-045/046 -> RPAC-047 -> RPAC-048 -> RPAC-057 -> RPAC-095
```

It freezes the RPAC-044 permission/request and RPAC-045/046 authority/
enforcement contract shape only. It does not implement those requirements,
relax POL-005, activate Runtime Enforcement, implement Shell Gate, register a
local-CLI adapter, or advance to RPAC-095.

## 6. Human Authority Contract

`docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` freezes
RIHAC-001 v1.0. Its purpose is to record an identified human's exact,
time-bounded, one-attempt authority. The human act is distinct from artifact
production, schema validity, PB permission, capability, Runtime Enforcement,
containment, execution, result acceptance, and task completion.

## 7. One-shot authority

```text
one RuntimeInvocationApproval -> one bounded invocation attempt
```

`attempt_limit=1` and `dispatch_limit=1`. No phase-wide, session-wide, or
task-wide reusable runtime-invocation authority exists in v1.

## 8. Approval subject

The exact five-tuple recovered verbatim from 3U is:

```text
(invocation_id, runtime_target, prompt_hash, repo_identity, task_id)
```

The canonical wire names are:

```text
(invocation_id, runtime_target_id, prompt_hash, repository_identity, task_id)
```

Changing any member creates a different subject and invalidates the approval.

### Matrix A — Approval subject binding

| Fact | Source | Approval-bound? | Revalidation point | Invalidation behavior |
|---|---|---:|---|---|
| `invocation_id` | Trusted invocation coordinator | Yes, subject | Gates 5/9/10/11 | Mismatch: no dispatch; new invocation/approval |
| `repository_identity` | Existing git-root fingerprint helper | Yes, subject | Gates 5 and 8 | Mismatch/drift: no dispatch; fresh approval |
| `task_id` | Active task lifecycle | Yes, subject | Gates 5 and 8 | Different task: no dispatch; fresh approval |
| `runtime_target_id` | Explicit target selector | Yes, subject | Gates 5 and 8 | Mismatch: no fallback; fresh invocation/approval |
| `prompt_hash` | `pcae.prompt-semantic.v1` | Yes, subject | Gates 5 and 8 | Semantic drift: no dispatch; fresh invocation/approval |
| `phase_id` | Governed phase state | Context-bound | Gates 5 and 8 | Mismatch: no dispatch |
| `session_id` | Interactive session state | Conditional context binding | Gates 5 and 8 when applicable | Missing/mismatch when applicable: no dispatch |
| HEAD | Git | Freshness snapshot | Gates 5/6 and 8 | Drift: approval stale; fresh approval |
| Task state/contract digest | Active task contract | Freshness snapshot | Gates 5/6 and 8 | Drift/closure/reassignment: fresh approval |
| Adapter descriptor/config | Registry/config owner | Scope/freshness-bound | Gates 5/6 and 8 | Drift: fresh approval |
| Policy version | PB/RE policy owners | Decision freshness, not subject | Gates 6/7 and 8 | Cached decisions invalid; reevaluate |
| Expiry | Trusted clock + artifact | Yes | Gates 5 and 8 | Expired: no dispatch; fresh approval |

## 9. Repository binding

Repository identity uses the existing `compute_repo_fingerprint` mechanism:
SHA-256 of sorted git root-commit hashes. A path alone is never trusted.

- Artifact copy alone grants nothing; destination context must independently
  match all bindings.
- Checkout rename/move alone does not invalidate.
- Different-history sibling repository fails closed.
- Changed root-history identity fails closed.
- Same-history clones share this lineage identity by design; multi-repository
  execution remains excluded and task/invocation/HEAD/storage/consumption
  checks still bind the one permitted context.
- Missing/unverifiable fingerprint fails closed.

## 10. Task binding

The active PCAE task contract is the sole task authority source. `task_id`,
task-contract digest, and active state are resolved by trusted lifecycle code,
not supplied by adapter/runtime data. Phase ID is bound when phase-scoped;
session ID only when genuinely session-scoped.

## 11. Runtime target binding

Approval binds the exact target ID. No fallback, alias, case/whitespace
repair, provider/model inference, or target substitution is permitted.

## 12. Prompt binding

`pcae.prompt-semantic.v1` hashes an ordered semantic-component document after
Unicode NFC and line-ending normalization, preserving all other content and
whitespace. Compact UTF-8 JSON uses recursively ASCII-sorted keys and
delivery-order arrays, then SHA-256 lower-hex. Display-only ANSI/wrapping and
non-delivered ephemeral metadata are excluded; anything delivered or
behaviorally operative is included. Ambiguity fails closed.

The existing dry raw-content digest remains unchanged.

## 13. Invocation identity

PCAE generates opaque `inv-<32-hex>` before the approval preview. The same ID
appears in approval, PB request, RE projection, invocation record, dispatch,
receipt, and result. The runtime cannot choose it. Approval remains a sibling
artifact referenced by ID/digest, never embedded in the invocation record.

## 14. Provenance

The artifact records approver ID, identity-evidence kind, approval timestamp,
approval mechanism, exact preview digest, and trusted producer component.
Approving human identity is distinct from producer identity.

## 15. Freshness

All seven mandatory v1 conditions are frozen:

1. HEAD change;
2. task state/contract change;
3. prompt change;
4. runtime target change;
5. adapter configuration change;
6. policy version change; and
7. timeout/expiry.

Conditions 1–5 and 7 invalidate approval usability and require fresh approval.
Condition 6 invalidates cached PB/RE decisions and blocks dispatch until
current reevaluation; policy drift alone does not erase the historical human
act unless the approved scope/meaning changes.

## 16. Expiry

V1 uses both one-shot consumption and explicit `expires_at`. No arbitrary
duration is invented here. Future creation must present the exact expiry and
apply separately governed bounds.

## 17. Revocation

The approval is immutable and v1 freezes no mutable revocation field or
mandatory revocation CLI. Before consumption, cancellation or expiry makes it
unusable. A future explicit early revocation must be a separate append-only,
digest-bound artifact and contract amendment. Missing/deleted evidence fails
closed but deletion is not audit-preserving revocation.

## 18. Storage

Canonical pattern:

```text
.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json
```

Create-only, atomic, canonical, immutable, symlink/traversal rejecting, and
looked up by ID rather than caller path. Not CHGR, not embedded in
`RuntimeInvocationRecord`, not arbitrary temp storage.

## 19. Schema

`docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` freezes
RIASC-001 v1.0 as a complete normative Draft 2020-12 shape in Markdown.
Repository convention makes `src/pcae/schema_resources/**` plus manifest/
validator wiring production behavior, so no executable schema was added.

Required top-level fields: schema/contract/record identity, approval ID,
record digest, creation/expiry times, five-member subject, governance
context, prompt-hash profile, approval scope, adapter binding, freshness
snapshot, provenance, and attempt limit.

## 20. Trust

Trust is the conjunction of strict schema, exact binding, identified-human
provenance, canonical lookup, SHA-256 canonical-record tamper detection, and
current freshness/consumption checks. No cryptographic signature is required
for v1. No authority-like boolean is accepted.

## 21. Validation

Frozen order:

```text
resolve canonical reference
-> load exactly one artifact
-> schema/version/closed-field validation
-> digest and provenance validation
-> repo/task/phase/conditional-session binding
-> invocation/target binding
-> prompt/profile binding
-> scope/adapter binding
-> seven-condition freshness validation
-> expiry validation
-> consumption-state validation
-> validated-authority projection
```

No step creates PB ALLOW.

## 22. Missing/stale/mismatch behavior

No valid approval, stale/expired approval, mismatch, tamper, unsupported
version, unknown field, ambiguous state, or consumed approval all yield no
real dispatch. No auto-refresh, fallback, permissive default, or rebinding.

## 23. Consumption point

Consumption is atomic with gate 9's durable `dispatch_attempted` write. It is
not consumed at prompt creation, preflight, validation, PB ALLOW, RE ALLOW, or
containment, and does not wait until after spawn.

## 24. Crash semantics

Before gate 9, canonical proof of no marker permits reuse of the same
unexpired approval only after every freshness/PB/RE/live-preflight check is
rerun. After gate 9, the approval is consumed even if trusted evidence proves
spawn never began. If dispatch may have happened, state is
`DISPATCH_UNCERTAIN`; no replay. Captured output is
`RESULT_CAPTURED_UNTRUSTED`.

## 25. Retry

No automatic retry. At/after gate 9, a new attempt always requires a new
invocation ID and fresh human approval. Before gate 9, identical resume is
permitted only with proof of non-consumption and complete revalidation.

## 26. PB Extension Contract

`docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` freezes PBRD-001
v1.0. It is additive contract text only; PB source remains unchanged.

## 27. `runtime_dispatch` semantics

PB ALLOW means PCAE policy permits attempting the one exact bounded local-CLI
dispatch described by the request, subject to every remaining independent
gate. It means none of human authorization, capability, RE, process/network/
filesystem/credential permission, completion, trust, acceptance, or task
completion.

## 28. `execution_class`

The existing exact class is `adapter`. No new class is introduced. This keeps
POL-004 applicable to runtime dispatch.

## 29. Request fields

### Matrix B — PB request

| Field | Source | Required? | Trust owner | Meaning |
|---|---|---:|---|---|
| `invocation_id` | Trusted invocation coordinator | Yes | PCAE coordinator | Exact logical invocation |
| `repository_identity` | Git-root fingerprint helper | Yes | Repository context resolver | Repository lineage, not path |
| `task_id` | Active task contract | Yes | Task lifecycle | Exact task |
| `lifecycle_context` | Phase/session lifecycle | Yes; session conditional | Lifecycle/session owners | Required phase plus conditional session |
| `runtime_target_id` | Explicit selection | Yes | Target selector/registry | Exact target, no fallback |
| `adapter_descriptor_binding` | Registry/config preflight | Yes | Registry/config owner | Adapter ID, descriptor version/digest, config digest |
| `prompt_hash` | Semantic prompt canonicalizer | Yes | Prompt builder | Exact semantic prompt identity |
| `requested_capability` | Governed request | Yes | Integration contract/coordinator | Requested, not possessed, capability |
| `transport_type` | Contract-fixed | Yes | PBRD integration | Const `local_cli` |
| `network_requirement` | Descriptor/static preflight | Yes | Registry/preflight | Const false; grants no network |
| `filesystem_scope_ref` | Scope owner | Yes | Filesystem governance | Declared scope ID/digest; grants no mutation |
| `human_authority_binding` | RIHAC validator | Yes | Authority validator | Approval ID/digest + validation projection digest |

Base PB envelope/control fields remain Foundation-owned and are not part of
the twelve-fact count.

## 30. Request exclusions

No raw credentials/secrets, universal provider/model fields, mandatory budget
fields, raw approval content, or untrusted executable/shell strings. No
caller-supplied approval/authorization/permission shortcut.

## 31. Approval reference

PB receives both the approval ID/digest and a minimal validator-owned evidence
projection digest bound to the exact request. It does not receive raw approval
prose and does not trust `approval_present` independently.

## 32. `approval_present`

Only successful RIHAC validation can cause the trusted builder to project
`approval_present=true`. The boolean remains derived Foundation input, not
authority and not caller-settable.

## 33. HUMAN_REVIEW

With valid approval, POL-004 is applicable but not triggered; no automatic
second human ceremony exists. Without valid approval, HUMAN_REVIEW may remain
the PB outcome, but no dispatch occurs and HUMAN_REVIEW is not authorization.
Other policy review outcomes retain force.

## 34. PB precedence

Unchanged:

```text
DENY > HUMAN_REVIEW > ALLOW
```

## 35. POL-005 evolution boundary

POL-005 remains universal and unchanged, so every truthful real
`simulation_only=false` request is denied. A future narrowly scoped eligibility
change requires independently verified approval creation/validation/storage,
all twelve PB facts, real positive RE, local executable pinning, containment,
durable state/recovery, the applicable MUST-FIX repairs, runtime-inspect
repair, and independent verification. Deleting POL-005 or adding a universal
non-simulation exception is forbidden.

## 36. Backward compatibility

Rollback, push, publication, existing mutation/backend/adapter actions, policy
precedence, and applicability semantics are unchanged.

## 37. Simulation compatibility

Current dry behavior remains `adapter_invocation` +
`execution_class=adapter` + `simulation_only=true`. It is not migrated to
`runtime_dispatch`; the production dry entry remains untouched.

## 38. Local CLI effect scope

One bounded local external process dispatch only. No API request, network
permission, arbitrary shell/child tree, multiple dispatch, parallelism,
background work, or automatic retry.

## 39. Process distinction

PB ALLOW is not process permission. Executable identity, argv, environment,
cwd, child policy, limits, and supervision belong to Shell Gate/equivalent.

## 40. Filesystem distinction

PB ALLOW is not arbitrary filesystem-mutation permission. Existing mutation
governance and isolated scope remain separate.

## 41. Network distinction

`network_requirement=false` is mandatory and grants nothing. API/provider
work is not eligible until a Network Egress Permission Architecture exists.

## 42. Credential distinction

PB ALLOW is not credential access. Credential architecture remains future
work and no credential is part of this request.

## 43. Gate Ordering Contract

`docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` freezes
RDGO-001 v1.0.

## 44. Gate 1–11

### Matrix C — Gate ordering

| # | Gate | Owner | Input | Output | External effect? |
|---:|---|---|---|---|---|
| 1 | Prompt preparation | Trusted prompt builder | Task instructions/context | Prompt artifact/hash | No |
| 2 | Explicit target selection | Target selector | Exact human-selected ID | One target ID | No |
| 3 | Static preflight | Registry/preflight coordinator | Descriptor/config/request draft | Static capability evidence | No |
| 4 | Human authority creation | Human + approval coordinator | Exact approval preview | RIASC approval | No |
| 5 | Approval validation | RIHAC validator | Approval ref/current state | Validated authority evidence | No |
| 6 | Permission Broker | PB | `runtime_dispatch` request | ALLOW/DENY/HUMAN_REVIEW | No |
| 7 | Runtime Enforcement | RE coordinator | Full projection | Final whether-to-invoke decision | No |
| 8 | Containment/live preflight | Shell Gate/equivalent | Executable/config/cwd/env/limits | Established containment evidence | No dispatch |
| 9 | Durable pre-dispatch | Invocation coordinator/store | Eight bound items | `dispatch_attempted`; approval consumed | No process effect |
| 10 | Adapter dispatch | Selected adapter | Bound envelope/containment | Spawn/receipt/uncertainty | **Yes, first effect** |
| 11 | Result capture/intake | Collector + intake | Attempt/output | Untrusted normalized result/evidence | Effect already occurred |

## 45. Static/live preflight

Static gate 3 checks descriptor/config/capability/transport/scope shape before
human attention and performs no live execution. Live gate 8 resolves and
hashes the exact executable, checks installation/availability, revalidates all
mutable facts/current policy decisions, and establishes containment
immediately before the durable/effect boundary.

## 46. RE projection

Minimum projection: full twelve-fact bound request; PB decision/policy IDs/
version/digest; validated approval reference and freshness-verdict digest; and
static/current target-status facts. References/digests suffice; raw artifacts
are not duplicated. RE independently evaluates and cannot infer a gate.

## 47. Execution Attempt Boundary

Gates 1–6 precede the Phase 99 attempt decision; gate 7 is the final
whether-to-invoke decision point; gates 8–9 are pre-effect preparation; gate
10 is the first effect; gate 11 is untrusted capture. COMP-002 and Phase 99
remain otherwise unchanged and non-implemented.

## 48. Durable-before-effect

The exact eight frozen items are:

1. invocation identity;
2. repository/task/phase/conditional-session binding;
3. target/adapter/config/executable observation binding;
4. prompt hash/profile;
5. approval ref/digest/validation digest and atomic consumption;
6. PB request/decision/policy evidence;
7. RE decision/expiry/evaluated-input evidence; and
8. containment reference plus durable `dispatch_attempted` marker/time.

No process effect occurs before all eight are atomically durable.

## 49. TOCTOU

### Matrix E — TOCTOU

| Mutable fact | Snapshot-bound? | Recheck before PB | Recheck before dispatch | Failure |
|---|---:|---:|---:|---|
| HEAD | Yes | Yes | Yes | Stale approval; no dispatch; fresh approval |
| Task state/contract | Freshness-bound | Yes | Yes | Stale approval; no dispatch; fresh approval |
| Prompt | Yes, subject hash | Yes | Yes | Subject mismatch; new invocation/approval |
| Runtime target | Yes, subject | Yes | Yes | Subject mismatch; no fallback |
| Adapter configuration | Yes | Yes | Yes | Stale approval; fresh approval |
| Adapter executable identity | Descriptor-pinned, not approval-bound | N/A beyond descriptor | Yes | No dispatch; repin/reselect and refresh decisions |
| Policy version | Not human-act-bound | Yes | Yes | Cached PB/RE invalid; reevaluate |

## 50. Repository/task/prompt/target freshness

HEAD or task-contract/state drift makes approval stale. Prompt or target drift
changes the exact subject. Repository fingerprint mismatch changes subject.
No condition silently continues and no target fallback exists.

Adapter configuration drift invalidates approval. Executable identity drift
is a live-preflight/supply-chain failure rather than an approval-subject
member, but still blocks dispatch and invalidates late-gate decisions.

## 51. Policy/RE freshness

Policy change invalidates cached PB and RE decisions; both are freshly
evaluated under current policy. RE decisions are single-attempt and cannot be
cached across any relevant request, approval, target/status, repository/task/
HEAD, prompt, config, executable, or policy change.

## 52. Versioning

All four contracts are v1.0 and use `MAJOR.MINOR`. RIASC wire schema is
`1.0`. Additive non-authority-widening evolution may use MINOR; subject,
one-shot, required-field, trust, precedence, effect-boundary, or gate-order
weakening is MAJOR/incompatible. Unknown versions fail closed and old
artifacts are never retrospectively widened.

## 53. Interoperability

### Matrix D — Cross-contract identifiers

| Concept | Authority contract | PB contract | Gate contract | Invocation record |
|---|---|---|---|---|
| Invocation ID | `subject.invocation_id` | `invocation_id` | Gates 4–11 | durable item 1 |
| Repository | `subject.repository_identity` | `repository_identity` | Gates 5/8/9 | item 2 |
| Task | `subject.task_id` + snapshot | `task_id` | Gates 5/8/9 | item 2 |
| Phase/session | `governance_context` | `lifecycle_context` | Gates 5/8/9 | item 2 |
| Target | `subject.runtime_target_id` | `runtime_target_id` | Gates 2–11 | item 3 |
| Prompt | `subject.prompt_hash` | `prompt_hash` | Gates 1/5/8/9 | item 4 |
| Approval | `approval_id`/`record_digest` | `human_authority_binding` | Gates 4/5/9 | item 5 reference |
| PB request/decision | Separate/non-authority | digests + decision | Gates 6/7/9 | item 6 |
| RE decision | Separate/non-authority | projected evidence | Gates 7/9 | item 7 |

No identifier or vocabulary drift was found across the four artifacts.

## 54. Naming

- **human approval/authority**: the identified human act and RIHAC artifact;
- **approval validation**: current proof the artifact is usable, not PB;
- **confirmation**: the deliberate gate-4 act only, not IWC/CHGR
  Confirmation;
- **permission**: PB decision only;
- **capability/availability**: runtime target facts only;
- **Runtime Enforcement**: final whether-to-invoke gate;
- **process containment**: how the process may be created;
- **dispatch**: gate-10 external effect;
- **result capture**: untrusted evidence intake;
- **acceptance**: existing review/promotion governance; and
- **completion**: explicit task lifecycle only.

`approval`, `authorization`, `confirmation`, `permission`, and `consent` are
not interchangeable.

## 55. Security invariants

### Matrix F — Security invariants

| Invariant | Contract owner | Failure behavior |
|---|---|---|
| No valid approval -> no real dispatch | RIHAC/RDGO | Stop before dispatch |
| Stale approval -> no real dispatch | RIHAC | Fail closed; fresh approval |
| Mismatched approval -> no real dispatch | RIHAC | No rebinding/fallback |
| PB DENY -> no real dispatch | PBRD | Stop |
| PB failure -> no real dispatch | PBRD | Stop |
| PB HUMAN_REVIEW without satisfied authority -> no real dispatch | PBRD | Stop; not authorization |
| PB ALLOW without valid authority -> no real dispatch | RDGO/RE | RE denies/fails |
| Runtime Enforcement deny/failure -> no dispatch | RDGO | Stop |
| Runtime unavailable -> no dispatch | RDGO preflight | Stop |
| Target mismatch -> no dispatch | RIHAC/RDGO | Stop; no fallback |
| Prompt mismatch -> no dispatch | RIHAC/RDGO | New subject required |
| Repository/task mismatch -> no dispatch | RIHAC/RDGO | Stop |
| Containment missing -> no dispatch | RDGO | Stop |
| Durable marker unavailable -> no dispatch | RDGO | Stop |
| Adapter cannot self-authorize | RPAC/RDGO | Reject/security failure |
| PB ALLOW grants no process/filesystem/network/credential authority | PBRD | Separate gate/permission required |
| Runtime result remains untrusted | RPAC/RDGO | Intake/review only |
| Runtime result != task completion | Task lifecycle | Explicit completion required |

## 56. Cross-gate separation

Explicit clauses in every new contract prohibit approval-as-PB, PB-as-human,
RE-as-both, capability-as-permission, and containment-as-completion. No gate
can infer or mint a missing earlier/later gate.

## 57. Artifact separation

The approval artifact, PB request/decision, RE decision, containment evidence,
and RuntimeInvocationRecord are separate. References/digests link them. Raw
duplication and combined authority/permission provenance are forbidden.

## 58. Crash/retry/at-most-once

Minimum states: pre-consumption, approval validated, PB evaluated, RE
evaluated, dispatch attempted, proven not started after marker, dispatch
uncertain, and result captured untrusted. Before gate 9, identical resume is
possible only after proof and total revalidation. After gate 9, no automatic
retry and fresh approval/new invocation are required. Exactly-once is not
promised; at-most-once applies where durable evidence proves state, with
explicit uncertainty otherwise.

## 59. MUST-FIX findings

Recovered verbatim from 3S.2.1 §62:

> 1. **Malformed adapter result crashes uncaught instead of failing closed
> cleanly.** `simulate_invocation` (`runtime_adapter.py` line ~501) calls
> `store.write_result(...)` on whatever `adapter.collect()` returns,
> without validating it is a `RuntimeInvocationResult` first; a
> non-conforming return value (e.g. a plain `dict`) raises an uncaught
> `AttributeError` inside `RuntimeInvocationStore.write_result`
> (`runtime_invocation.py` line ~923) rather than producing a
> `FAILURE_MALFORMED_RESULT` `SimulationOutcome`. **Effect on trust:**
> none observed — no `result.json` or `intake-handoff.json` is ever
> persisted when this occurs (verified empirically), so no false-success
> state is reachable. **Reachability:** none in current production —
> `_run_with_context` only ever instantiates `MockDryRuntimeAdapter()`,
> which always returns a well-formed `RuntimeInvocationResult`; this gap
> only matters for a future, non-mock adapter implementation.
>
> 2. **`RuntimeInvocationStore` does not sanitize `invocation_id` against
> path traversal.** `_invocation_dir`/`_write_create_only` join the raw
> `invocation_id` string onto the store root with no normalization or
> confinement check; a crafted ID (e.g. containing `../../..`) resolves
> completely outside `.pcae/runtime-invocations/mock-v1/`, demonstrated
> directly against the store. **Reachability:** none in current
> production — both public entry points
> (`run_production_dry_invocation`, `resolve_dry_consumer_context`) take
> no `invocation_id` parameter; it is always internally generated via
> `new_invocation_id()` (confirmed via `inspect.signature`,
> `test_production_entry_point_never_lets_caller_choose_invocation_id`).
> Recorded as defense-in-depth debt for any future caller of the store
> that might ever relay this field from less-trusted input.

Disposition after the 3V freeze:

1. The new contracts do not make malformed output reachable through the
   current mock-only production consumer. **BLOCKING BEFORE IMPLEMENTATION**
   of, or registration/availability claim for, the first non-mock adapter;
   repair no later than that implementation.
2. The new contracts preserve trusted ID generation and do not make the
   traversal defect reachable. Exact latest safe repair point: before any
   externally influenced invocation-ID/resume/retry/storage-lookup surface is
   implemented, and no later than real-invocation persistence hardening.

Neither finding is repaired in 3V.

## 60. Runtime inspect limitation

Disposition remains `TRUTHFUL_WITH_LIMITATION`: no reported field is false,
but the dry consumer's transient per-call registry is disconnected from the
persisted registry inspected by `pcae runtime inspect`. This must be repaired
before the first real adapter registration or availability claim. No runtime-
inspect modification occurs in 3V.

## 61. API/network boundary

```text
API-PROVIDER CONTRACT FREEZE: NOT AUTHORIZED / NOT READY
```

Reason: network-egress permission architecture is unresolved. API/provider,
OpenRouter, SDK, credential, and provider/model contracts are not frozen.

## 62. Contract consistency

Static cross-reading found the four artifacts consistent with RPAC-001, the
PB Foundation/current implementation, PBPA/PBPC semantics, Runtime
Enforcement's non-authorizing current state, Phase 99 Execution Attempt
Boundary, Typed Authority neutrality, CHGR/IWC confirmation separation,
repository schema/versioning conventions, and the unchanged dry path.

No contradiction remains in invocation ID, repository/task/phase/session,
target, prompt hash, approval reference, PB request, RE projection, durable
state, or terminology. The policy-version nuance is explicit: it invalidates
cached PB/RE decisions, not the historical human act, while still preventing
dispatch until current evaluation succeeds.

## 63. Verification result

Contract/static verification scope:

- parse the embedded RIASC Draft 2020-12 JSON;
- verify RIASC required/subject counts and closed-object policy;
- verify 12 PB facts, 11 gates, 8 durable items, and 7 TOCTOU facts;
- verify cross-contract identifiers and prohibited authority shortcuts;
- verify only allowed documentation/governance paths changed;
- verify `src/pcae` and production tests untouched;
- verify dry entry/source unchanged by diff;
- verify runtime and release tag unchanged; and
- run the governed closing health/coherence/task-memory/push/runtime/notify
  checks.

Final command evidence is recorded in canonical completion metadata/report.

## 64. Final verdict

```text
LOCAL-CLI REAL-RUNTIME AUTHORITY/PERMISSION CONTRACTS: FROZEN
REAL EXECUTION: UNAVAILABLE
HUMAN AUTHORITY: DEDICATED ONE-SHOT RuntimeInvocationApproval
PB REAL-DISPATCH ACTION: runtime_dispatch
AUTHORITY: SEPARATE FROM PERMISSION
PERMISSION: SEPARATE FROM CAPABILITY
RUNTIME ENFORCEMENT: SEPARATE PRE-DISPATCH GATE
APPROVAL SUBJECT: EXACT INVOCATION / REPO / TASK / TARGET / PROMPT BINDING
PB REQUEST: 12 IMMUTABLE BOUND FACTS
GATE ORDER: 11 GATES FROZEN
TOCTOU: 7 MUTABLE FACTS BOUND/REVALIDATED
DURABLE BEFORE EFFECT: 8 ITEMS FROZEN
SIMULATION PATH: UNCHANGED
POL-005: UNCHANGED IN PRODUCTION
API/NETWORK CONTRACT: NOT FROZEN
RUNTIME: Observed / observe / unavailable
EXECUTION ACTIVATION: NOT PERFORMED
```

Production source modified: NO. External runtime invocation: NONE. Article:
STOPPED. Private research: UNTOUCHED. v0.4.3: UNCHANGED.

## 65. Recommended next phase

Exactly one next phase is recommended:

**149O.20L.7O.3V.1 — Independent Verification of Local-CLI Runtime Dispatch
Authority and Permission Contract Freeze.**

It must independently re-derive all four contracts, counts, bindings,
freshness, crash/retry, PB semantics, and compatibility from primary sources
without trusting 3V's self-report. Implementation must not begin directly
after this self-authored freeze.

## 66. Human decision required

A human must decide whether to authorize the exact independent verification
phase above. This freeze does not authorize 3V.1 or any implementation,
execution activation, API/network design, real adapter registration, or
external runtime invocation.
