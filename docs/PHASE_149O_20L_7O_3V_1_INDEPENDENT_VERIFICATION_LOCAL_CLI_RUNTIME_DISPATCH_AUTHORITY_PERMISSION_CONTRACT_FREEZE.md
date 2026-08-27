# Phase 149O.20L.7O.3V.1 — Independent Verification of Local-CLI Runtime Dispatch Authority and Permission Contract Freeze

## Objective

Independently verify the four normative artifacts frozen by Phase
149O.20L.7O.3V against their primary contract and production authorities,
without implementing, repairing, or activating real dispatch.

This verification was required to conclude `CONTRACT FREEZE: NOT VERIFIED`
if any semantic contradiction existed. Two blocking contradictions were found.
The 3V artifacts remain unchanged for a dedicated repair phase.

## Independence

This phase did not accept the 3V phase document, canonical report, or its own
static-verification claims as proof. It reconstructed the contract system from:

- RPAC-001 v1.0;
- the 3T prerequisite plan and 3U architecture;
- Permission Broker Foundation, PBPA/PBPC contracts, and current PB source;
- Runtime Enforcement evidence/decision/coordinator contracts and source;
- Phase 99 Governed Execution Attempt Boundary;
- Typed Authority Model contracts;
- CHGR contract/schema-family disclaimer;
- Interactive Workflow Confirmation and Confirmation-separation rules;
- the current production dry-runtime consumer; and
- repository schema/versioning precedent.

Fresh verification tests were authored independently. No 3V test existed to
reuse, and no production code was modified.

## Baseline

| Fact | Entry result |
|---|---|
| Verification baseline | `60de4bda64af32e94a29039d10fdd96a811350dd` |
| `HEAD` / `origin/main` | Both verification baseline |
| `origin/main..HEAD` | `0` |
| Worktree | Clean before governed phase startup |
| 3V phase-entry SHA | `934e1f07fac798417c1b5a25d5b06214a5f62ab3` |
| 3V contract-freeze SHA | `2060ebd411df664aac97e3987a922c77cb05ef6f` |
| Release | `v0.4.3` unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime | `Observed` / `observe` / `unavailable` |
| Registry | 0 plugins / 0 capabilities |
| Health/check/coherence | healthy / passed / coherent |
| Push check | clean; nothing to push |
| Telegram | configured / enabled / outbound-ready |
| Governed phase | 3V.1 task opened through PCAE task transition |

`pcae doctor task-memory` reported only the established historical
`tasks/DONE.md` synchronization warnings. They predate and are unrelated to
3V.1.

## 3V close-evidence discrepancy

The immutable latest 3V report says both `completed` / `complete` and:

```text
pcae_health: healthy at entry; final close check required
telegram_runtime: configured ... at entry; final status required
```

Independent evidence shows the final checks did run:

- `.pcae/phase-completion-metadata.json` records `healthy at final close`, a
  clean push check, unchanged runtime, and successful final Telegram delivery;
- `.pcae/phase-completion-report.md` records clean governed publication, zero
  ahead, unchanged release/runtime, and successful notification delivery;
- `.pcae/provenance-history.json` records final `phase_completed` and
  `agent_released` events at `2026-08-27T09:25:28Z`; and
- commit `60de4bda` is the explicit final governance-evidence synchronization.

Classification:

```text
STALE REPORT WORDING ONLY
```

This is `NON-BLOCKING NB-3V1-001`, a report-quality defect. The immutable 3V
history was not rewritten. Future report generation must not leave
`final ... required` placeholders in a completed/complete report after final
evidence exists.

## 3V delta

The exact contract-freeze delta is
`934e1f07...2060ebd4`. It added the four contract artifacts and the 3V phase
document and changed governance/project/task metadata. It changed no file
under `src/pcae/**`, `src/pcae/schema_resources/**`, production tests, runtime
adapter source, PB source, Runtime Enforcement source, runtime inspect, or
version/build configuration.

The complete 3V commit sequence after entry was:

1. `2060ebd4` — freeze four contracts;
2. `53bb5fe0` — completion metadata;
3. `79339073` — canonical report;
4. `f0c87d7c` — normalize static evidence;
5. `eea64469` — clear completed TODO;
6. `8025db5a` — close task / decision hold; and
7. `60de4bda` — synchronize final governance evidence.

## Frozen artifact inventory

### Matrix A — Frozen contracts

| Contract | File | Version | Completeness | Verdict |
|---|---|---:|---|---|
| RIHAC-001 | `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` | 1.0 | Complete for its stated authority scope | `COMPLETE` |
| PBRD-001 | `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | 1.0 | Exact 12 declared facts exist, but RPAC-required attempt/idempotency binding is absent | `INCOMPLETE — BLOCKING` |
| RDGO-001 | `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` | 1.0 | Internally complete 11-gate model, but order contradicts RPAC-001 v1.0 | `CONTRADICTORY — BLOCKING` |
| RIASC-001 | `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` | 1.0 | Complete normative embedded Draft 2020-12 shape | `COMPLETE` |

Artifact SHA-256 values at verification baseline:

| Contract | SHA-256 |
|---|---|
| RIHAC-001 | `e721c6c85c24989e634c32b357b66f54bb1498c4d63f99b194f557aaae084c98` |
| PBRD-001 | `48974ed9101fa50e98f8a812db688ba492cf979f1c7f965f30fa34a781263de7` |
| RDGO-001 | `514b3f68d23537a17172f4df29e7e29f3f4c92157281dc9448cbc3749be53baa` |
| RIASC-001 | `9263ff0a4d4ab66d66f5c9b7ffdeea62f524a23c3a86639adc4e3dcd55910d27` |

## Contract provenance/versioning

The four artifacts were introduced together at `2060ebd4`. Each declares
`FROZEN`, `v1.0`, and local-CLI-only scope. Repository search found no second
competing normative copy of any contract. RIHAC is semantic authority for
RIASC; PBRD and RDGO link rather than absorb the approval artifact.

All four use `MAJOR.MINOR`; unknown versions fail closed. Their additive and
incompatible-change rules are internally coherent. However, RPAC-REQ-093 is
the pre-existing higher-level versioning constraint: a changed gate order
requires a new RPAC major version. RDGO cannot silently override that rule by
declaring its own v1.0.

## RIHAC reconstruction

RIHAC-001 governs one identified human's explicit authority for one bounded
future local-CLI invocation attempt. It defines authority source, subject,
binding, provenance, freshness, invalidation, expiry, storage, validation,
consumption, crash behavior, retry, trust, and fail-closed behavior.

It does not grant PB permission, capability, Runtime Enforcement approval,
process/filesystem/network/credential permission, dispatch completion,
accepted change, or task completion.

## One-shot semantics

The rule is exact:

```text
one RuntimeInvocationApproval -> one bounded invocation attempt
```

Both `attempt_limit` and `dispatch_limit` equal `1`. No phase-, session-, or
task-wide standing approval exists. This is consistent across RIHAC, RIASC,
PBRD, and RDGO.

## Subject binding

The exact subject is:

```text
(invocation_id, runtime_target_id, prompt_hash, repository_identity, task_id)
```

### Matrix B — Subject binding

| Fact | RIHAC | RIASC | PBRD | RDGO | Consistent? |
|---|---|---|---|---|---|
| Invocation ID | `subject.invocation_id` | required `inv-<32-hex>` | `invocation_id` | gates 4–11 / durable item 1 | Yes |
| Repository | `subject.repository_identity` | required 64-hex | `repository_identity` | gates 5/8/9 / item 2 | Yes |
| Task | `subject.task_id` + snapshot | required bounded string | `task_id` | gates 5/8/9 / item 2 | Yes |
| Runtime target | `subject.runtime_target_id` | required exact string | `runtime_target_id` | gates 2–11 / item 3 | Yes |
| Prompt | `subject.prompt_hash` | required 64-hex | `prompt_hash` | gates 1/5/8/9 / item 4 | Yes |
| Approval | sibling `approval_id`/digest | required ID/digest | `human_authority_binding` | gates 4/5/9 / item 5 | Yes |
| PB decision | explicitly not authority | absent | request/decision evidence | gates 6/7/9 / item 6 | Yes |
| RE decision | explicitly not authority | absent | projection only | gates 7/9 / item 7 | Yes |

The five subject fields have no naming drift. This matrix does not cure the
separate missing attempt/idempotency request binding in Finding B-2.

## Repo/task/target/prompt binding

- Repository identity is the existing git root-history fingerprint, never a
  path. A moved checkout remains the same lineage; a sibling with different
  roots or changed root history fails closed. A copied artifact grants nothing.
- Task identity comes from the active PCAE task contract. Task A cannot
  authorize task B. Phase is bound for governed work; session is conditional.
- Target selection is exact, with no alias, normalization, nearest match, or
  fallback.
- `pcae.prompt-semantic.v1` normalizes Unicode NFC and line endings, preserves
  all other delivered semantic content/order/whitespace, excludes only truly
  display-only nondelivered material, serializes compact sorted-key JSON, and
  hashes SHA-256 lower-hex. Ambiguous exclusion fails closed.

## Approval provenance

RIASC records approving human, approval time, identity-evidence kind,
dedicated mechanism, approval-preview digest, and trusted producer component.
Approving human and producer are separate concepts. Producer identity cannot
stand in for the human.

## Freshness/invalidation

The exact seven rules are:

1. HEAD changes — approval stale; fresh approval required.
2. Task state/contract changes — approval stale; fresh approval required.
3. Prompt changes — subject mismatch; fresh invocation/approval required.
4. Runtime target changes — subject mismatch; no fallback; fresh
   invocation/approval required.
5. Adapter configuration changes — approval stale; fresh approval required.
6. Policy version changes — cached PB/RE decisions invalid; re-evaluate both;
   fresh approval is not required solely for policy drift unless scope changes.
7. Timeout/expiry — approval expired; fresh approval required.

The adapter executable is descriptor-pinned but not a human-authority subject
member; it is re-resolved and verified at live preflight. This resolves the
3U prose tension between a human-facing stable adapter identity and mandatory
configuration freshness without weakening either check.

## Expiry/revocation

V1 requires both one-shot consumption and an explicit `expires_at`, with no
arbitrary duration invented by 3V. The immutable artifact has no mutable
revocation flag or required revoke CLI. Cancellation/expiry can make an
unconsumed approval unusable; a future explicit early revocation must be a
separate append-only digest-bound artifact and contract amendment.

## Consumption/crash/retry

Consumption occurs atomically with gate 9's durable `dispatch_attempted`
transition. It does not occur at prompt creation, static preflight, validation,
PB ALLOW, RE ALLOW, or containment; it also cannot wait until after spawn.

- Before gate 9, proven absence of a marker permits reuse only after complete
  revalidation and fresh PB/RE/live-preflight evaluation.
- After gate 9 but with proof spawn never began, state is
  `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`; approval remains consumed.
- If dispatch may have happened, state is `DISPATCH_UNCERTAIN`; no replay.
- Captured results are `RESULT_CAPTURED_UNTRUSTED`.
- There is no automatic retry. A new post-marker attempt requires new
  invocation identity and fresh approval.

This honestly offers at-most-once attempt where PCAE can prove state and
explicit uncertainty where it cannot. It does not claim exactly-once.

## RIASC schema

RIASC-001 embeds one normative JSON Schema Draft 2020-12 object with recursive
closed-field objects. Its exact 16 top-level required fields are:

1. `schema_id`
2. `schema_version`
3. `contract_version`
4. `record_type`
5. `approval_id`
6. `record_digest`
7. `created_at`
8. `expires_at`
9. `subject`
10. `governance_context`
11. `prompt_hash_profile`
12. `approval_scope`
13. `adapter_binding`
14. `freshness_snapshot`
15. `provenance`
16. `attempt_limit`

Fresh tests verified with `jsonschema` Draft 2020-12:

- schema validity;
- one positive canonical instance;
- rejection of every missing required field;
- rejection of unknown fields;
- wrong-type and malformed-version rejection;
- rejection of `approved`, `authorized`, `permission`, `pb_allow`, and
  `execution_available` shortcuts; and
- independent mismatch detection for each of the five subject members.

Result: 40 fresh tests passed.

## Normative-vs-production distinction

```text
SCHEMA CONTRACT: FROZEN
PRODUCTION VALIDATOR: NOT IMPLEMENTED
```

RIASC is normative Markdown contract text only. There is no executable schema
package, manifest registration, validator, store, writer, CLI, or production
consumer under `src/pcae/schema_resources/**`. Static validation of the
embedded schema proves its contract shape, not production enforcement and not
human authority.

## PBRD reconstruction

PBRD selects future `action_type=runtime_dispatch` with existing
`execution_class=adapter`. It defines a local-CLI-only bounded dispatch
permission, twelve immutable facts, approval-evidence projection,
POL-004/HUMAN_REVIEW behavior, precedence, POL-005 evolution conditions,
effect walls, RE projection, and backward/dry compatibility.

It is contract-only. Current source has no `runtime_dispatch` constant and
POL-006 would reject that unknown action today, in addition to POL-005 denying
every truthful non-simulation request.

## `runtime_dispatch` semantics

PBRD ALLOW means only that current PCAE policy permits attempting the one
bounded local-CLI dispatch described by that exact immutable request, subject
to every independent remaining gate. It does not confer human approval,
runtime capability, RE approval, arbitrary subprocess permission, filesystem
mutation, network, credentials, trusted output, acceptance, or task completion.

## `execution_class`

The selected class is `adapter`. Direct source verification confirms it is an
existing PB class and keeps POL-004 applicable. The action is future-only and
not present in `KNOWN_ACTION_TYPES`.

## 12 request facts

### Matrix C — PB request

| Field | Contract meaning | Current-source compatibility | Verdict |
|---|---|---|---|
| `invocation_id` | Exact coordinator-generated logical invocation | No current PB field | Future-compatible |
| `repository_identity` | Git lineage fingerprint, not path | No current PB field | Future-compatible |
| `task_id` | Exact active task | Existing current PB field | Compatible |
| `lifecycle_context` | Required phase plus conditional session | Current `phase_id` only; no closed object/session | Additive evolution needed |
| `runtime_target_id` | Exact selected target, no fallback | No current PB field | Future-compatible |
| `adapter_descriptor_binding` | Adapter ID, descriptor version/digest, config digest | No current PB field | Future-compatible |
| `prompt_hash` | Exact semantic instruction digest | No current PB field | Future-compatible |
| `requested_capability` | Requested capability, not capability proof | Existing current PB field | Compatible |
| `transport_type` | Const `local_cli` | No current PB field | Future-compatible |
| `network_requirement` | Const false, grants no network | No current PB field | Future-compatible |
| `filesystem_scope_ref` | Declared scope ref, grants no mutation | Current `requested_resource` is not equivalent | Additive evolution needed |
| `human_authority_binding` | Approval ID/digest plus validator projection digest | Current boolean is insufficient | Additive evolution needed |

All twelve declared facts exist and match RIHAC/RDGO vocabulary. They are not,
however, a complete RPAC-conformant dispatch binding because `attempt_id` and
`idempotency_key` are missing (Finding B-2).

## Request exclusions

PBRD correctly excludes raw credentials/secrets, universal provider/model
fields, mandatory provider-budget fields for local CLI v1, raw approval
content, and caller-controlled executable/shell strings. `network_requirement`
is fixed false. Process limits may be bound through the separately governed
containment profile; paid/provider budget work remains outside local CLI v1.

## Approval evidence

PB receives both `(approval_id, record_digest)` and a minimal validator-owned
projection digest bound to the same request. Only successful RIHAC validation
can let the trusted builder derive `approval_present=true`. Raw approval prose,
arbitrary paths, or caller-supplied booleans are not authority.

## POL-004/HUMAN_REVIEW

Current source independently confirms `MissingHumanApprovalRule` applies to
`adapter`. If trusted approval validation derives `approval_present=true`,
POL-004 does not trigger. This removes only POL-004's missing-approval review;
it does not globally satisfy every current or future HUMAN_REVIEW-producing
policy. Without valid approval, POL-004 may return HUMAN_REVIEW, but no real
dispatch occurs and HUMAN_REVIEW is not authorization.

## Precedence

Current composition remains exactly:

```text
DENY > HUMAN_REVIEW > ALLOW
```

Fresh direct-source tests confirmed DENY wins when DENY and HUMAN_REVIEW rules
trigger together.

## POL-005 boundary

PBRD does not remove or relax POL-005. The current universal rule denies every
truthful `simulation_only=false` request. PBRD lists bounded prerequisite
conditions for a future narrow eligibility evolution and prohibits universal
bypass/deletion. Current production behavior is unchanged.

## Simulation compatibility

The production dry path remains:

```text
action_type=adapter_invocation
execution_class=adapter
simulation_only=true
```

Source tracing confirms `runtime_adapter.py` constructs exactly that request,
and contains no `runtime_dispatch` string. The compact dry CLI remains explicit
two-part opt-in with no fallback. No existing rollback, push, publication, or
mutation action is reclassified.

## Process/filesystem/network/credential walls

- `runtime_dispatch ALLOW != arbitrary process execution permission`;
  executable/argv/env/cwd/children/limits/supervision belong to containment.
- `runtime_dispatch ALLOW != filesystem mutation authority`; existing
  mutation/intake/review governance remains separate.
- `runtime_dispatch ALLOW != network permission`; local CLI v1 requires
  network false and the API path remains blocked.
- `runtime_dispatch ALLOW != credential access`; credential architecture is
  not part of the request or this freeze.

These walls are complete and mutually consistent.

## RDGO reconstruction

RDGO defines eleven mandatory gates, their owners, inputs, outputs, failures,
first-effect boundary, durable evidence, static/live preflight split, RE
projection, Phase 99 mapping, TOCTOU, identifiers, crash states, retry, and
security invariants.

Its internal sequence is precise. Its relationship to RPAC is not valid
because gate 3/4 ordering contradicts the still-frozen RPAC order.

## 11 gates

### Matrix D — Gate ordering

| # | Gate | Authority effect? | External effect? | Verified? |
|---:|---|---|---|---|
| 1 | Prompt preparation | None | No | Internally verified |
| 2 | Explicit target selection | None | No | Internally verified |
| 3 | Static preflight | None | No | Structurally verified; order conflicts with RPAC |
| 4 | Human authority creation | Creates human authority only | No | Structurally verified; order conflicts with RPAC |
| 5 | Approval validation | Validates; creates no new authority | No | Verified |
| 6 | Permission Broker | PB permission only | No | Verified |
| 7 | Runtime Enforcement | Single-attempt final whether-to-invoke decision | No | Contract-only |
| 8 | Process containment + live preflight | Process permission/readiness only | No dispatch | Contract-only |
| 9 | Durable pre-dispatch record | Consumes approval; no effect proof | No process effect | Verified structurally |
| 10 | Adapter dispatch | No new authority | **Yes, first external effect** | Verified structurally |
| 11 | Result capture/intake | No authority; result stays untrusted | Prior effect only | Verified structurally |

Every gate has an owner, input, output, and fail-closed rule in RDGO. The
blocking issue is the relative position of gates 3 and 4, not a missing row.

## Static/live preflight

Static preflight is descriptor/config/capability/transport/scope inspection
without execution. Live preflight re-resolves exact config/executable,
verifies installation/hash/current availability, rechecks mutable facts and
current PB/RE decisions, and establishes containment immediately before the
durable/effect boundary. No fact is trusted solely from static preflight when
it can drift before effect.

## 8 durable items

The exact eight RDGO items are:

1. invocation identity and attempt ID where used;
2. repository/task/HEAD/phase/conditional-session binding;
3. target/adapter/config/live-executable observations;
4. prompt hash/profile;
5. approval ID/digest/validation digest plus atomic consumption;
6. PB request/decision/policy evidence;
7. RE decision/expiry/evaluated-input evidence; and
8. containment reference plus `dispatch_attempted` and timestamp.

Items 2–8 are coherent. Item 1's `attempt_id where used` is insufficient
against RPAC's unconditional unique-attempt identity requirement and is part of
Finding B-2.

## 7 TOCTOU facts

### Matrix E — TOCTOU

| Fact | Frozen rule | Cross-contract consistency | Verdict |
|---|---|---|---|
| HEAD | Snapshot at approval; recheck before PB and dispatch | RIHAC/RIASC/RDGO agree | Pass |
| Task state/contract | Freshness-bound; recheck before PB and dispatch | Agree | Pass |
| Prompt | Subject hash; recheck twice | Agree | Pass |
| Runtime target | Subject target; recheck twice; no fallback | Agree | Pass |
| Adapter configuration | Snapshot-bound; recheck twice; drift stales approval | Agree | Pass |
| Adapter executable identity | Descriptor-pinned; exact live check before spawn | Agree | Pass |
| Policy version | Not human-act-bound; current PB/RE before effect | Agree | Pass |

Freshness scenarios produce the expected result: HEAD/task/config drift stales
approval; prompt/target/repository mismatch changes subject; executable drift
blocks live preflight and late decisions; policy drift invalidates cached PB/RE
and forces re-evaluation.

## Freshness scenarios

| Scenario | Frozen authority/decision result |
|---|---|
| Approval created, then HEAD changes | Approval stale; no dispatch; fresh approval |
| Approval created, then task closes or contract changes | Approval stale; no dispatch; fresh approval |
| Delivered prompt changes | Five-member subject mismatch; new invocation/approval |
| Selected target changes | Five-member subject mismatch; no fallback |
| Adapter configuration changes | Approval stale; fresh approval |
| Executable bytes/version drift while descriptor remains named | Live preflight fails; no dispatch; refresh late decisions after repair |
| PB policy version changes | Prior PB/RE decisions invalid; re-evaluate; no approval erasure solely from policy drift |

## EAB compatibility

Phase 99 and COMP-002 remain explicitly design-only, non-executing, and
non-authorizing. RDGO's mapping—gates 1–6 before attempt decision, gate 7 as
the final decision, gates 8–9 as pre-effect preparation, gate 10 as first
effect, gate 11 as capture—is compatible with Phase 99 in isolation and does
not activate its future-only states.

Overall EAB compatibility cannot be certified while RDGO's preflight/approval
order contradicts RPAC-001, the canonical runtime adapter contract. The
Phase-99 mapping itself is not a third blocking finding; it is transitively
blocked by Finding B-1.

## Confirmation/CHGR boundaries

Interactive Workflow Confirmation remains a distinct workflow/governance
act and cannot automatically source, populate, or satisfy a
`RuntimeInvocationApproval`. RIHAC's mechanism string
`interactive_local_cli_confirmation` names a dedicated runtime-invocation
human act and explicitly disclaims IWC/CHGR/TAM equivalence. A future UI must
retain that qualification and avoid exposing a bare `confirmation` token as
if it were runtime approval.

CHGR remains schema/artifact representation only. Its own README says schema
validity does not prove a valid/current/authorized human act and that runtime
consumption/authority resolution are unimplemented. RIHAC stores its artifact
in a separate `.pcae/runtime-invocation-approvals/` family and does not
reinterpret CHGR.

## Typed Authority compatibility

Typed Authority Model contracts preserve the rule that representation,
schema validity, registry membership, or record existence never establishes
authority, approval, authorization, or runtime permission. RIHAC uses those
terms in a separate, exact invocation subject and similarly requires a human
act plus current validation. It is not a TAM record or resolver input. No
conflicting subject meaning was found.

## Identifier interoperability

Invocation, repository, task, phase/session, target, prompt, approval, PB,
and RE vocabulary is internally consistent across the four 3V artifacts.
References/digests are used instead of duplicating authority/decision objects.

The identifier matrix is nevertheless incomplete at the RPAC layer because
no cross-contract row/binding exists for mandatory `attempt_id` and
`idempotency_key`. That is the substance of Finding B-2, not mere vocabulary
style.

## Terminology audit

The contracts consistently reserve:

- approval/human authority for the identified human act/artifact;
- approval validation for current usability proof;
- permission for PB;
- capability/availability for runtime facts;
- Runtime Enforcement approval/decision for the final whether-to-invoke gate;
- containment/process permission for launch constraints;
- dispatch for the gate-10 external effect;
- result capture for untrusted evidence;
- acceptance for intake/review/promotion; and
- completion for task lifecycle.

No `consent` shortcut exists. The qualified mechanism word `confirmation` is
the only terminology risk and is non-blocking because the contracts explicitly
exclude IWC/CHGR Confirmation and define the dedicated act.

## Security invariants

The following are frozen and internally enforced by contract prose:

| Invariant | Owner | Failure behavior |
|---|---|---|
| No valid approval | RIHAC/RDGO | No real dispatch |
| Stale/expired approval | RIHAC | No dispatch; fresh approval |
| Subject mismatch | RIHAC/RIASC | No rebinding/fallback |
| PB DENY/failure | PBRD | Stop |
| HUMAN_REVIEW without satisfied authority | PBRD | Stop; not authorization |
| PB ALLOW without valid authority | RDGO/RE | RE must deny/fail |
| Approval without PB ALLOW | RDGO | Stop at PB |
| RE deny/failure | RDGO | Stop |
| Runtime unavailable | RDGO preflight | Stop; no fallback |
| Target/prompt/repo/task mismatch | RIHAC/RDGO | Stop |
| Containment missing | RDGO | Stop |
| Durable marker unavailable | RDGO | Stop before effect |
| Adapter self-authorizes | RPAC/RDGO | Reject/security failure |
| Runtime result | RPAC/RDGO | Untrusted intake evidence only |

## Cross-gate adversarial scenarios

### Matrix G — Security scenarios

| Scenario | Required result | Contract result | Verdict |
|---|---|---|---|
| A: approval exists, PB DENY | No dispatch | Gate 6 stops | Pass |
| B: PB ALLOW, approval missing | No dispatch | Gate 5 cannot project authority; RE cannot infer it | Pass |
| C: approval + PB ALLOW, RE DENY | No dispatch | Gate 7 stops | Pass |
| D: all permission gates pass, runtime unavailable | No dispatch | Gate 8 live preflight stops | Pass |
| E: result claims authorization | Claim remains untrusted | Gate 11 cannot create authority/permission/completion | Pass |

These scenario results are sound but do not repair the two RPAC-level
contract contradictions.

## Artifact separation

The approval artifact, PB request/decision, RE decision, containment evidence,
and invocation record remain distinct and have distinct provenance/lifecycles.
They link by immutable IDs/digests. No combined `approved-and-allowed` artifact
or boolean shortcut is permitted.

## At-most-once/retry

The approval-consumption point, durable-before-effect marker, explicit
uncertain state, and no-auto-retry rule are consistent across RIHAC/RDGO.
The stricter v1 choice—new invocation and approval after a consumed attempt—is
compatible with RPAC's safety floor. Exactly-once is never promised.

Implementation planning must still restore RPAC's mandatory `attempt_id` and
`idempotency_key` semantics before these guarantees are implementable.

## API/network exclusion

All four artifacts are scoped to local CLI v1. Network requirement is false;
provider/model, credentials, SDKs, OpenRouter, network egress, API retries,
and paid-provider budget fields are not universalized.

```text
API-PROVIDER CONTRACT FREEZE: NOT AUTHORIZED / NOT READY
```

Reason: Network Egress Permission Architecture remains unresolved. This phase
does not solve it.

## Two MUST-FIX findings

Recovered verbatim in substance and exact operative wording from the primary
3S.2.1 verification document:

1. **Malformed adapter result crashes uncaught instead of failing closed
   cleanly.** `simulate_invocation` calls `store.write_result(...)` on whatever
   `adapter.collect()` returns; a nonconforming object raises uncaught
   `AttributeError` instead of yielding `FAILURE_MALFORMED_RESULT`. Current
   mock-only production reachability remains none. **BLOCKING BEFORE the first
   non-mock adapter implementation or registration/availability claim.**
2. **`RuntimeInvocationStore` does not sanitize `invocation_id` against path
   traversal.** Raw identity joins the store root without confinement. Current
   public dry entry points do not accept invocation ID and generate it
   internally. **BLOCKING BEFORE any externally influenced invocation-ID,
   resume, retry, or storage-lookup surface, and no later than real-invocation
   persistence hardening.**

Neither finding is repaired here. The new contracts do not make either current
production path reachable, but both are prerequisites to implementation at the
named latest-safe points.

## Runtime inspect limitation

Disposition remains:

```text
TRUTHFUL_WITH_LIMITATION
```

No current field is false, but the dry consumer's transient per-call registry
is disconnected from the persisted registry queried by `pcae runtime inspect`.
Repair is mandatory before the first real adapter registration or availability
claim. None of the four contracts assumes that current inspect already exposes
a real adapter.

## Contract completeness

RIHAC and RIASC are complete within scope. PBRD is incomplete against
RPAC-REQ-025/044/064–068 because its future PB request and durable binding omit
mandatory attempt/idempotency identity. RDGO is internally complete but
contradicts RPAC-REQ-042/093 on static-preflight versus approval ordering.

Therefore the four-artifact system is not jointly complete or implementable
without inventing/choosing normative semantics during implementation.

## Normative-vs-implemented matrix

### Matrix F — Normative vs implemented

| Capability | Contract | Production implementation | Current state |
|---|---|---|---|
| Human approval semantics | RIHAC-001 frozen | No creator/consumer | Contract only |
| Approval schema | RIASC-001 frozen Markdown | No executable schema/validator | Contract only |
| Approval store | RIHAC path/pattern frozen | Not implemented | Unavailable |
| Approval validator/projection | RIHAC order frozen | Not implemented | Unavailable |
| `runtime_dispatch` PB action | PBRD-001 frozen but incomplete | No source constant/request support | Unknown action / denied |
| POL-004 validated projection | PBRD semantics frozen | Caller boolean only today | Not implemented |
| POL-005 bounded evolution | Preconditions described | Universal deny unchanged | Execution denied |
| Real RE projection/positive gate | RDGO/PBRD described | Current RE is design-only/non-authorizing | Not implemented |
| Process containment/Shell Gate | RDGO prerequisite | Classifier only/non-intercepting | Not implemented |
| Durable real-attempt state | RDGO described but ID gap found | Mock store only | Not implemented |
| Real local adapter | RPAC future | None | Unavailable |
| Dry adapter consumer | RPAC mock/dry | Implemented/verified/production-consumed | Unchanged |

## Implementation readiness

Question: Are the local-CLI authority/permission contracts sufficiently
precise that implementation planning can proceed without inventing new
authority semantics?

```text
NO — CONTRACT REPAIR REQUIRED
```

The human-authority semantics themselves are precise, but implementation
planning cannot choose a valid gate order or complete request identity without
first reconciling RPAC with RDGO/PBRD. Starting implementation now would force
the implementer to silently pick which frozen contract to violate.

## Findings

### BLOCKING B-149O.20L.7O.3V.1-1 — RDGO gate order contradicts RPAC

RPAC-REQ-042 freezes:

```text
3. obtain human InvocationApproval
4. resolve descriptor/config and perform fact-only status/capability preflight
```

RDGO freezes:

```text
3. static preflight
4. human authority creation
```

This is a direct relative-order reversal. RPAC-REQ-093 states that changed gate
order requires a new major version. Neither RPAC was amended nor a major
migration declared. 3U/3V's efficiency rationale for preflight-before-human is
reasonable but cannot override RPAC-001 v1.0 silently.

Required repair: choose and normatively reconcile one order, amend/version the
authoritative contracts consistently, update EAB mapping if needed, and
independently reverify. No code implementation may begin first.

### BLOCKING B-149O.20L.7O.3V.1-2 — PB/durable request identity is incomplete

RPAC-REQ-025 requires every canonical `InvocationRequest` to carry logical
`invocation_id`, unique `attempt_id`, and `idempotency_key`. RPAC-REQ-044
explicitly says the PB request's missing idempotency binding is part of the gap
that must be closed. RPAC-REQ-064–068 make attempt identity/idempotency central
to collision, resume, and ambiguous-dispatch safety.

PBRD's exact twelve facts contain `invocation_id` but neither `attempt_id` nor
`idempotency_key`. RDGO durable item 1 weakens attempt identity to
`attempt_id where used` and never binds idempotency. The cross-contract matrix
also omits both concepts. This prevents the frozen request/decision from
proving which single attempt it permits and from binding PB/RE evidence to the
canonical request identity RPAC requires.

Required repair: restore unconditional attempt identity and canonical
idempotency binding across PBRD request, RDGO durable/RE projection, identifier
matrices, and any affected RIHAC/RIASC language. If the declared count changes
from twelve, update it honestly; do not hide required identity inside an
unidentified digest.

### MUST-FIX (pre-existing, not caused by 3V.1)

- malformed adapter result fail-closed repair at the first non-mock adapter
  implementation boundary;
- invocation-store path confinement before any externally influenced ID or
  real persistence/resume/retry surface.

### NON-BLOCKING

- `NB-149O.20L.7O.3V.1-001`: stale final-check wording in the completed 3V
  report; final evidence exists.
- `NB-149O.20L.7O.3V.1-002`: the dedicated approval mechanism includes the
  qualified word `confirmation`; future UI/CLI design must preserve the
  explicit non-IWC/non-CHGR qualification to avoid terminology regression.

## Final verdict

```text
INDEPENDENT VERIFICATION: COMPLETE
LOCAL-CLI REAL-RUNTIME AUTHORITY/PERMISSION CONTRACT FREEZE: NOT VERIFIED
RIHAC-001 v1.0: COMPLETE
RIASC-001 v1.0: COMPLETE AS NORMATIVE SCHEMA; PRODUCTION VALIDATOR NOT IMPLEMENTED
PBRD-001 v1.0: INCOMPLETE — BLOCKING
RDGO-001 v1.0: CONTRADICTORY WITH RPAC-001 — BLOCKING
ONE-SHOT AUTHORITY: INTERNALLY VERIFIED
FIVE-MEMBER SUBJECT: INTERNALLY VERIFIED
SEVEN FRESHNESS RULES: INTERNALLY VERIFIED
TWELVE DECLARED PB FACTS: PRESENT, BUT NOT SUFFICIENTLY COMPLETE
ELEVEN RDGO GATES: PRESENT, BUT ORDER NOT CERTIFIED
EIGHT DECLARED DURABLE ITEMS: PRESENT, BUT ATTEMPT/IDEMPOTENCY BINDING INCOMPLETE
SEVEN TOCTOU FACTS: VERIFIED
SECURITY WALLS: VERIFIED
DRY PATH: UNCHANGED
POL-005: UNCHANGED
API/NETWORK CONTRACT: NOT FROZEN
REAL EXECUTION: UNAVAILABLE
EXECUTION ACTIVATION: NOT PERFORMED
PRODUCTION SOURCE MODIFIED: NO
EXTERNAL RUNTIME INVOCATION: NONE
RUNTIME: Observed / observe / unavailable
RELEASE v0.4.3: UNCHANGED
ARTICLE: STOPPED
PRIVATE RESEARCH: UNTOUCHED
IMPLEMENTATION READINESS: NO — CONTRACT REPAIR REQUIRED
```

## Recommended next phase

Exactly one next phase is recommended:

**149O.20L.7O.3V.1R — Local-CLI Runtime Dispatch Authority and Permission
Contract Reconciliation and Repair.**

Its scope should be contract-only: reconcile RPAC/RDGO preflight/approval
ordering and restore attempt/idempotency binding across PBRD/RDGO and the
identifier/projection matrices. It must preserve RIHAC's one-shot authority,
all semantic walls, dry behavior, POL-005, runtime unavailability, and the API
network boundary. It must not implement dispatch.

## Human decision required

**YES.** Human authorization is required before the recommended 3V.1R repair
phase. This independent verification does not authorize repair,
implementation planning, source changes, POL-005 evolution, Runtime
Enforcement/Shell Gate activation, adapter registration, execution, API/network
architecture, article work, or private-research access. Stop after 3V.1.
