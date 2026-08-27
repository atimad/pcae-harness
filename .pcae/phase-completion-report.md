# Phase 149O.20L.7O.3V Complete — Local-CLI Runtime Dispatch Authority and Permission Contract Freeze

**Verdict: COMPLETE CONTRACT FREEZE. LOCAL-CLI ONLY. NO PRODUCTION
IMPLEMENTATION. EXECUTION REMAINS UNAVAILABLE.**

Phase 149O.20L.7O.3V froze exactly four separate normative contracts for a
future human-authorized real local-CLI runtime dispatch. It did not implement
or activate that dispatch.

## Canonical identity and baseline

- **Phase ID:** `149O.20L.7O.3V`
- **Status/completeness:** completed / complete after governed publication
- **Phase-entry SHA:** `934e1f07fac798417c1b5a25d5b06214a5f62ab3`
- **Release:** `v0.4.3`, unchanged at
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`
- **Runtime:** `Observed` / `observe` / `unavailable`
- **RPAC:** RPAC-001 v1.0, FROZEN
- **Scope:** LOCAL CLI RUNTIME v1 only
- **Dry runtime:** implemented, verified, production-consumed, unchanged

Baseline was clean, zero ahead, with no active governed phase before startup.
The complete 3U architecture and current primary contracts/source were read
before freezing; no decision was copied from summary prose alone.

## Frozen artifacts

1. **RIHAC-001 v1.0** — Runtime Invocation Human Authority Contract.
2. **PBRD-001 v1.0** — PB Runtime Dispatch Extension Contract.
3. **RDGO-001 v1.0** — Runtime Dispatch Gate Ordering Contract.
4. **RIASC-001 v1.0** — RuntimeInvocationApproval Schema Contract.

All four are FROZEN. They are separate artifacts and may link only by
immutable IDs/digests. Their provenance is never combined.

## Human authority contract

V1 authority is a dedicated, explicit, one-shot
`RuntimeInvocationApproval`:

```text
one RuntimeInvocationApproval -> one bounded invocation attempt
```

There is no task-, phase-, or session-wide reusable authority. The exact 3U
approval subject is:

```text
(invocation_id, runtime_target, prompt_hash, repo_identity, task_id)
```

The consistent schema vocabulary is:

```text
(invocation_id, runtime_target_id, prompt_hash, repository_identity, task_id)
```

The trusted PCAE coordinator creates the invocation ID before approval; the
external runtime and adapter cannot choose or rewrite it. The approval,
request, Runtime Enforcement projection, invocation record, dispatch, and
result bind the same ID.

Repository identity reuses `compute_repo_fingerprint`: SHA-256 over sorted git
root-commit hashes. A path is not identity. A rename/move alone does not
invalidate, an artifact copy grants nothing, a different-history sibling or
changed root identity fails closed, and a same-history clone has the same
lineage identity while all task/invocation/HEAD/storage/one-shot checks still
apply. Multi-repository execution remains excluded.

Task authority comes from the exact active task contract. Task A never
authorizes task B. Phase is bound when governed-phase scoped; session is bound
only when actually session scoped. The exact runtime target is bound with no
fallback, alias repair, provider/model inference, or substitution.

`pcae.prompt-semantic.v1` hashes the behaviorally delivered semantic document:
Unicode NFC, CRLF/CR to LF, preserved semantic whitespace/order/case, compact
UTF-8 JSON, recursively ASCII-sorted object keys, array delivery order, then
SHA-256 lowercase hex. Display-only ANSI/wrapping and genuinely non-delivered
ephemeral presentation metadata are excluded. Anything delivered or
behaviorally operative is included. Semantic drift invalidates authority.

## Freshness, expiry, revocation, storage, and trust

All seven 3U v1 conditions are frozen:

1. HEAD change — approval stale; fresh approval required.
2. Task state/contract change — approval stale; fresh approval required.
3. Prompt change — different subject; fresh invocation/approval required.
4. Runtime-target change — different subject; no fallback; fresh authority.
5. Adapter-configuration change — approval stale; fresh approval required.
6. Policy-version change — cached PB/RE decisions invalid; current
   re-evaluation required; fresh approval additionally required if scope
   changes.
7. Timeout/expiry — approval expired; fresh approval required.

V1 requires both one-shot consumption and explicit wall-clock expiry. No
arbitrary duration was invented. Explicit mutable revocation is deferred; an
unconsumed workflow may be cancelled or allowed to expire, and any later
revocation design must be a separate append-only digest-bound artifact.

Canonical approval storage is:

```text
.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json
```

It is create-only, immutable, atomically stored, loaded by canonical ID, and
not CHGR, not embedded in `RuntimeInvocationRecord`, and not an arbitrary temp
file. V1 trust requires strict schema validation, exact subject/scope binding,
identified-human provenance distinct from producer provenance, canonical
storage resolution, digest tamper detection, and current freshness/consumption
validation. No cryptographic signature is required for v1.

Validation order is canonical reference resolution; single artifact load;
schema/version/closed-field validation; digest and provenance validation;
repo/task/phase/conditional-session binding; invocation/target binding; prompt
binding; scope/adapter/config binding; freshness; trusted-clock expiry; durable
consumption-state check; immutable validated-evidence projection. Missing,
stale, expired, mismatched, tampered, duplicated, consumed, or indeterminate
authority means no real dispatch. There is no auto-refresh or rebinding.

## Approval schema result

RIASC-001 is a closed Draft 2020-12 schema contract with sixteen required
top-level fields and a closed five-member subject. Unknown fields fail closed.
It rejects authority shortcuts such as `approved=true`, `authorized=true`, or
`permission=ALLOW`. Cross-field validation binds time, digest, subject, scope,
freshness, provenance, canonical storage, and prior durable state.

The schema was frozen normatively in Markdown. No executable
`src/pcae/schema_resources` schema/manifest/validator was added because that
would be production behavior and is not authorized in 3V.

## Consumption, crash, retry, and at-most-once

Approval consumption occurs atomically with gate 9's durable
`dispatch_attempted` transition—not at prompt preparation, preflight, approval
validation, PB ALLOW, Runtime Enforcement ALLOW, or post-dispatch completion.

- Before gate 9, the same unexpired approval may be resumed only when durable
  state proves no attempt marker and every authority, preflight, PB, and RE
  check is repeated successfully.
- After the marker but proven before spawn, state is
  `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`; no effect is claimed, but the
  approval is consumed.
- When dispatch may have happened, state is `DISPATCH_UNCERTAIN`; no blind
  replay or completion claim is permitted.
- Captured output is `RESULT_CAPTURED_UNTRUSTED`, never accepted change or task
  completion.

Any new post-consumption attempt or retry gets a new invocation ID and fresh
human approval. No automatic retry exists. The honest guarantee is at-most-once
where PCAE can prove state, with explicit uncertainty where it cannot; exactly
once is not promised.

## PB runtime-dispatch extension

PBRD-001 freezes:

```text
action_type = runtime_dispatch
execution_class = adapter
```

PB `ALLOW` means only that PCAE policy permits attempting the exact bounded
external local-CLI runtime dispatch described by the immutable request. It
does not mean the human authorized, the target is capable/available, Runtime
Enforcement allowed, process execution is unrestricted, network or filesystem
mutation is permitted, credentials are accessible, output is trusted, or work
is accepted/complete.

The twelve immutable request-binding facts are:

1. `invocation_id`
2. `repository_identity`
3. `task_id`
4. `lifecycle_context` (`phase_id`, conditional `session_id`)
5. `runtime_target_id`
6. `adapter_descriptor_binding` (adapter identity, descriptor version/digest,
   target-config digest)
7. `prompt_hash`
8. `requested_capability`
9. `transport_type=local_cli`
10. `network_requirement=false`
11. `filesystem_scope_ref`
12. `human_authority_binding` (approval ID/digest plus validated-evidence
    projection digest)

The request excludes raw credentials/secrets, universal or mandatory
provider/model fields, mandatory budget fields, arbitrary untrusted executable
or shell strings, raw approval content, and caller-supplied authority flags.
PB receives both approval reference/hash and the minimal independently
verifiable validation projection. It never trusts `approval_present=true`
from a caller.

Only successful RIHAC validation lets the trusted builder derive
`approval_present=true`. With valid approval, POL-004
`MissingHumanApprovalRule` is not triggered; `HUMAN_REVIEW` is not an
automatic second ceremony for the same request. Without valid approval, PB
may return `HUMAN_REVIEW`, but no real dispatch occurs and `HUMAN_REVIEW` is
never authorization. Other policy results still apply. Precedence remains:

```text
DENY > HUMAN_REVIEW > ALLOW
```

POL-005 remains unchanged and still denies every non-simulation request.
Future implementation may make exact `runtime_dispatch` eligible only after
the action/class, twelve facts, validated authority projection, current policy
evaluation, Runtime Enforcement, process containment, live preflight, and
durable-before-effect state all exist and are independently verified. This is
not permission to delete POL-005 or weaken it universally.

Rollback, push, publication, existing mutation actions, and current
`adapter_invocation` behavior are unchanged. The dry
`adapter_invocation`/`simulation_only=true` path is not migrated.

One dispatch is one bounded local external process. It excludes API requests,
network permission, unrestricted shell, arbitrary child-process trees, and
multiple external dispatches. PB ALLOW is not arbitrary process authority,
filesystem mutation authority, network authority, or credential authority.

## Eleven-gate order

1. Prompt preparation — produces semantic prompt/hash; no authority/effect.
2. Explicit target selection — exact target, no fallback; no authority/effect.
3. Static preflight — descriptor/scope plausibility; no live execution,
   authority, or effect.
4. Human authority creation — creates RIHAC artifact; not PB permission.
5. Approval validation — creates validated authority evidence; not PB ALLOW.
6. Permission Broker — evaluates `runtime_dispatch`; no inferred authority or
   capability.
7. Runtime Enforcement — evaluates complete projection; final whether gate;
   no real effect yet.
8. Process containment/live preflight — exact executable/cwd/argv/environment,
   no child tree/network/credential widening; no dispatch before success.
9. Durable pre-dispatch record — persists effect-bound evidence and atomically
   consumes approval with `dispatch_attempted`; no external effect.
10. Adapter dispatch — first external execution effect.
11. Result capture/intake — records untrusted output; never automatic
    acceptance or task completion.

Unavailable targets fail before human approval when static facts permit;
dynamic capability and executable identity are revalidated immediately before
effect. Runtime Enforcement receives the complete immutable request, PB
decision/policy/no-go evidence, validated approval reference/freshness
projection, and live target/status/preflight facts. Whole artifacts need not
be duplicated when immutable references/digests suffice.

Phase 99/COMP-002 is extended compatibly, not redefined: gates 1–6 are
pre-attempt; gate 7 is the final whether-to-invoke decision; gates 8–9 are
post-decision/pre-effect; gate 10 is first effect; gate 11 is untrusted
aftermath. COMP-002 remains not implemented.

## Eight durable-before-effect items

1. Invocation identity and attempt identity when used.
2. Repository/HEAD/task/phase/conditional-session binding.
3. Exact target, adapter descriptor/config, and live executable observation.
4. Semantic prompt hash and profile.
5. Approval ID/digest and validated-evidence digest, atomically consumed.
6. PB request/decision digest, outcome, policy version, policy/no-go IDs.
7. RE decision ID/digest, verdict, expiry, and evaluated-input digest.
8. Containment evidence plus `dispatch_attempted` state/timestamp.

## Seven TOCTOU mutable facts

1. HEAD — snapshot at approval; recheck before PB and dispatch.
2. Task state/contract — freshness bound; recheck before PB and dispatch.
3. Prompt — subject hash; recompute before PB and dispatch.
4. Runtime target — subject bound; exact recheck, no fallback.
5. Adapter configuration — snapshot; recheck before PB and dispatch.
6. Adapter executable identity — descriptor-pinned; exact live hash before
   spawn.
7. Policy version — current PB/RE evaluation before PB and dispatch.

Drift fails closed. A policy change invalidates cached PB and RE decisions;
Runtime Enforcement is never cached across relevant request, approval,
repository/task/HEAD, prompt, target/configuration/executable, status, or
policy change.

## Versioning, interoperability, and semantic walls

All contracts use `MAJOR.MINOR`. Additive, non-authority-widening evolution may
increment MINOR. Subject relaxation, trust weakening, one-shot relaxation,
gate/effect-boundary change, or incompatible field/meaning change requires a
new MAJOR, explicit migration, and independent verification. Unknown versions
fail closed and no future reader retrospectively widens old authority.

Invocation, repository, task/lifecycle, target, prompt, approval, PB, RE, and
dispatch-state identifiers agree across all four artifacts and the future
invocation record. Terminology is fixed: human authority, confirmation,
validation, PB permission, capability/availability, Runtime Enforcement,
process containment, dispatch, capture, acceptance, and completion are not
interchangeable.

```text
human approval != PB permission
PB ALLOW != runtime capability
runtime capability != Runtime Enforcement approval
Runtime Enforcement ALLOW != process permission
process permission != dispatch completion
dispatch completion != accepted change
runtime result != task completion
```

Fail-closed security invariants include missing/stale/mismatched approval; PB
DENY/failure/unresolved HUMAN_REVIEW; PB ALLOW without authority; RE deny;
runtime unavailable; target/prompt/repository/task/configuration mismatch;
containment/durable-state failure; adapter self-authorization; and untrusted
runtime results. Every case means no real dispatch or no acceptance, as
applicable.

## Existing findings and boundaries

Both Phase 3S.2.1 MUST-FIX findings were recovered verbatim in the phase
document and remain unrepaired:

1. malformed non-mock adapter results can reach an uncaught `AttributeError`
   before normalization;
2. unsanitized `invocation_id` can traverse the invocation-store path.

They remain unreachable in the dry-only runtime today, but are **BLOCKING
BEFORE IMPLEMENTATION** and must be repaired no later than the latest safe
points recorded in the phase document, before the first non-mock adapter or
production approval/dispatch path becomes reachable.

Runtime inspect remains `TRUTHFUL_WITH_LIMITATION`; it must be repaired before
the first real adapter registration or availability claim. It was not changed
in 3V.

```text
API-PROVIDER CONTRACT FREEZE: NOT AUTHORIZED / NOT READY
```

Network-egress permission architecture remains unresolved. OpenRouter,
provider SDK/API, credentials, provider/model universal fields, and API
dispatch remain out of scope and not frozen.

## Verification and governance result

- Draft 2020-12 metaschema: valid.
- Valid approval example: accepted.
- Unknown fields and authority shortcuts: rejected.
- Required schema fields: 16.
- Exact approval subject members: 5.
- PB immutable facts: 12.
- Gate order: 11.
- Durable-before-effect items: 8.
- TOCTOU mutable facts: 7.
- Required phase sections: 1–66 present.
- Matrices A–F: present and consistent.
- `git diff --stat -- src/pcae tests`: empty.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- Task-memory warnings: historical `tasks/DONE.md` synchronization debt only;
  no 3V-attributable error.
- Full Fast Green: not required because production code/tests did not change.
- Contract consistency: PASSED.
- Production source modified: NO.
- Execution activated: NO.
- External runtime invocation: NONE.
- Dry path: UNCHANGED.
- Runtime: `Observed` / `observe` / `unavailable`.
- v0.4.3: UNCHANGED.
- Article: STOPPED.
- Private research: UNTOUCHED.

Phase-owned commits begin with:

- `2060ebd4` — freeze local CLI runtime authority and permission contracts.
- `53bb5fe0` — add completion evidence metadata.

Final governed publication requires and records a clean push, zero
`origin/main..HEAD`, unchanged runtime/release state, and complete canonical
report evidence. No force, no `--no-verify`, and no history rewrite are used.

## Final verdict

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

## Recommended next phase and human decision

Exactly one independent verification phase is recommended:

**149O.20L.7O.3V.1 — Independent Verification of Local-CLI Runtime Dispatch
Authority and Permission Contract Freeze.**

Human decision is required. Do not begin implementation automatically.
