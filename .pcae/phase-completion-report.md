# Phase 149O.20L.7O.3Q Complete — Runtime Surface Reconciliation and Runtime / Provider Adapter Contract Freeze

**Status: completed. Completeness: complete. Human decision required.**

Phase-entry commit:
`a52561954b78f1e195715baf4feb7db0e88fdebb`. Substantive contract commits:
`4c9332ec44b8417ca4d5f53d72e7528753bf166f` and
`8bc27726861e6221781402b7680dec9ed75f4148`, pushed to `origin/main`.

## Public and runtime state

- Latest public release: `v0.4.3`, still resolving to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`; unchanged.
- Runtime status/state/capability:
  `not_implemented / Observed / unavailable / observe`.
- Runtime Registry current truth: valid empty, process-local metadata registry;
  0 plugins, 0 capabilities, no loader/resolver/callable target.
- Current execution: **UNAVAILABLE**.
- Production source modified: **NO**.
- Execution activation: **NO**.
- External runtime invocation: **NONE**.

## Reconciled surfaces

Current source was re-derived across Runtime Registry, Runtime Context,
Runtime Snapshot, runtime inspect, Plugin Model, agent and agent-config
registries, session AgentLock, session/phase backend locks and registries,
backend preflight, legacy backend and adapter contracts, provider/model hints,
producer provenance, execution principal gap, capability vocabulary,
invocation approval, Permission Broker, Runtime Enforcement, Shell Gate,
generic intake, process/environment/network/filesystem controls, and every
material legacy real-runtime path identified by 3P.

Key reconciliation:

- Runtime Registry is the single future declarative catalog foundation, not a
  callable container today.
- Plugin Model is metadata/introspection-only: no loader, implementation
  resolver, lifecycle callback, or execution hook.
- Backend preflight validates task/prompt/hash/file scope but is bootstrap
  evidence, not target resolution, capability, dispatch, or authorization.
- Legacy backend and adapter registries are overlapping historical metadata,
  not competing future authorities.
- Legacy subprocess surfaces do not conform to RPAC and must be retired,
  disabled, or routed through the one governed kernel before real activation.
- Generic intake is already producer-neutral and is the return path for
  proposed changes.

## Identity conclusion

Frozen identity layers:

```text
AgentIdentity
ProducerIdentity / provenance
AdapterIdentity
RuntimeTargetIdentity
ProviderIdentity (optional)
ModelIdentity (optional)
ExecutionPrincipal
InvocationIdentity (logical invocation + attempts)
```

They are non-equivalent. In particular:

```text
agent_id != runtime target
agent_id != provider
agent_id != model
producer provenance != runtime identity
```

Agent identity is descriptive coordination/session provenance; it carries no
runtime authority. Producer provenance is untrusted descriptive lineage.
RuntimeTarget is one explicit versioned adapter configuration. Provider/model
are optional and never inferred. ExecutionPrincipal is the observed OS/service
credential principal at effect time. InvocationIdentity provides audit and
idempotency, not authority.

**Codex-Ox conclusion:** `codex-ox` remains a first-class PCAE session/producer
identity only. It does not imply OpenRouter, Codex CLI selection, a model, a
configured target, authentication, capability, permission, authorization, or
execution.

## Selected adapter architecture and frozen contract

Architecture: **trusted PCAE governance kernel plus replaceable RuntimeAdapter
transports**.

Contract: **Runtime / Provider Adapter Contract, RPAC-001 v1.0 — FROZEN**.

The kernel owns authoritative repo/task/prompt/target binding, human authority,
Permission Broker consumption, final Runtime Enforcement, durable invocation
state, retry authority, audit, result quarantine, generic-intake submission,
review and promotion linkage. An adapter owns only target-specific transport,
process/API lifecycle, bounded capture, timeout/cancellation mapping, status
observation, and normalized result production. It cannot authorize itself or
accept/promote output.

Conceptual interface:

```text
describe() -> RuntimeDescriptor
preflight(InvocationRequest) -> AdapterPreflightResult
dispatch(DispatchEnvelope) -> DispatchReceipt
collect(attempt_id) -> RuntimeInvocationResult | PendingObservation
cancel(attempt_id) -> RuntimeCancellationResult
```

Streaming is deferred; v1 exposes status observations plus one terminal
result. Cancellation capability is explicit and may be supported,
cooperative, or unsupported.

## Request contract

The governed InvocationRequest binds contract version; logical invocation,
attempt, and idempotency identities; repository fingerprint/root, base commit,
active task and relevant phase/session; descriptive requester agent; explicit
target/adapter/descriptor/config digests; optional provider/model snapshot;
PromptArtifact reference/hash; InvocationApproval reference/hash; exact
capabilities/result format; repository-bound cwd policy; environment,
filesystem, network, sandbox, and process profiles; finite timeout;
cancellation requirement; and optional structured resource budget.

Network, write, outside-repo access, and paid usage default denied. Runtime
output cannot rewrite request authority.

## Result contract

RuntimeInvocationResult binds invocation/attempt/idempotency; exact target,
adapter, descriptor/config, and optional declared/observed provider/model;
dispatch/accept/start/complete/capture observations and timestamps; terminal,
process/transport/provider status; bounded stdout/stderr/content references and
digests; structured response; changed-file manifest and patch/diff references;
usage/cost; runtime/adapter/principal provenance; observed confinement facts;
sanitized common failure, retry hint, and ambiguity; plus PCAE-owned intake
references.

Raw/provider-specific data may be an opaque bounded attachment. Result is
untrusted. Completion does not mean accepted change, promotion, or successful
PCAE task.

## Runtime descriptor, status, and registry contract

RuntimeDescriptor is immutable: adapter contract/identity/version/digest,
class/transport, declared capabilities/result formats, effect type, locality,
network requirement, platforms, cancellation mode, and simulation flag. It
contains no live health, credentials, permission, or task state.

RuntimeStatus is dynamic and timestamped: registered, installed, configured,
authenticated or not-required, available, health/unknown, observed
capabilities, source, and observation time. It contains no authority.

Registry contract: unique registration, descriptor enumeration/lookup,
capability candidate lookup, status association, explicit target resolution,
no fallback, fail-closed drift/ambiguity/version handling, and a valid empty
state. Future callable resolution belongs to trusted kernel code composed with
the registry, never ambient plugin auto-execution.

A future mock/dry entry declares no execution effect and simulation capability;
it cannot make runtime inspect claim real execution availability. Current 0/0/
unavailable consumers remain compatible.

## Invocation identity, states, idempotency, and retry

PCAE creates a stable cryptographically random logical invocation ID before
approval and a unique attempt ID per try. Canonical versioned request content
produces the SHA-256 idempotency key; timestamps alone never identify an
invocation.

State model:

```text
PCAE governance: PREPARED -> APPROVED -> PERMITTED -> AUTHORIZED
runtime fact:    CAPABLE (preflight and freshness recheck)
runtime observe: DISPATCHED -> ACCEPTED -> RUNNING -> COMPLETED -> RESULT_CAPTURED
intake:          INGESTED
```

Same ID/same content resumes without redispatch; same ID/different content is a
hard collision. Pre-dispatch restart resumes validation. Possible post-dispatch
restart becomes ambiguous and never auto-retries. Same-digest completion is
idempotent; conflicting completion is quarantined. Intake replay uses a
deterministic invocation/attempt/result-digest candidate identity.

Every retry gets a new attempt, fresh facts/PB/enforcement decisions, and fresh
human authority when approval attempt/expiry bounds require it. A changed
prompt, target, repo/task, effects, provider/model, or budget creates a new
logical invocation. Adapter retryability is advisory only.

## Permission, enforcement, and trust relationships

**Permission Broker:** existing `adapter_invocation`/`backend_invocation` and
adapter/backend execution-class vocabulary can express dispatch conceptually.
The current request lacks exact target, prompt, repo/effects/network/
filesystem/credential/budget/idempotency binding, and real execution remains
categorically denied. This is a contract gap; PB policy was not changed.

**Runtime Enforcement:** future final whether-to-invoke gate after human
approval, target capability/status, and PB permission, immediately before the
durable effect boundary. Current Runtime Enforcement is evidence-only,
negative-only, non-authorizing, and has zero production dispatch consumers; a
separate amendment/implementation is required.

**Shell Gate:** future constraint on how local command/process launch occurs.
Fixed argv requires adapter/process-policy validation; shell text/expansion
requires an enforcing Shell Gate/equivalent. Current Shell Gate only
classifies/audits simulations and remains non-enforcing. Runtime Enforcement
answers whether; Shell Gate/process policy answers how.

**HATP:** no generic adapter dependency. Current HATP is bound to specific
hardware-backed trust/rollback/deployment domains and is not provider auth or
general dispatch permission. Any later hardware-backed invocation requirement
must be separately contracted.

**Prompt approval:** a lightweight immutable PromptArtifact is required for
machine dispatch. One exact InvocationApproval can encompass prompt approval
and binds prompt hash, repo/task/base, selected target/config, effect profiles,
budget, expiry, and attempts. Existing copy/paste is an implicit human boundary
but not machine-verifiable. Older `approved_agents` is not runtime approval.

**Dispatch permission:** human approval, runtime capability, PB permission,
Runtime Enforcement authorization, and actual dispatch remain separate.

## Gate ordering

```text
authoritative task/session + PromptArtifact
  -> immutable request + explicit target
  -> human InvocationApproval
  -> descriptor/config/status/capability preflight
  -> Permission Broker dispatch/effect permission
  -> HEAD/config/status/approval freshness recheck
  -> Runtime Enforcement final single-attempt authorization
  -> durable attempt record + dispatch intent
  -> selected adapter only
  -> normalized result capture
  -> generic intake
  -> existing review/promotion lifecycle
```

Permission != capability; capability != authorization; authorization !=
execution. Every failed/stale pre-dispatch gate means no adapter call.

## Runtime configuration and dependencies

- Selection: explicit `runtime_target_id`; no silent agent/config/provider/
  model/environment fallback.
- Discovery: trusted built-ins and explicit pinned config initially; future
  entry points/executable descriptors require governed admission; no ambient
  auto-enable.
- Credentials: opaque refs only; PCAE currently lacks a general secret resolver
  and least-privilege injector. This blocks authenticated real adapters.
- Network: explicit default-deny capability/effect, even for local CLI;
  endpoint/TLS/DNS/proxy/egress enforcement required before real use.
- Local process: fixed argv, pinned executable, repo cwd, minimal env, bounded
  capture, timeout, process tree, signals, cancellation, containment, and
  restart reconciliation required.
- Filesystem: separate repo read/write/temp/outside scopes; write/outside
  default none; cwd kernel-selected and realpath-contained.
- API: endpoint/provider, secret ref, schema, timeouts, rate limits,
  cancellation, ambiguous delivery, usage/cost, and normalized result required.
- Budget: optional v1 extension for mock propagation; required before metered
  real use. Missing means no paid use.
- Portability: common fields are OS-neutral; macOS/Linux mechanics remain
  declared adapter platform profiles.

## Invocation record, audit, provenance, and intake

A persistent append-only RuntimeInvocationRecord is required before real
execution and should be exercised by mock/dry. It binds request/artifact/
config digests, repo/task/phase, all identities, approval, status, PB/
enforcement, transition log, dispatch receipt, result, failures/ambiguity,
retry lineage, intake references, timestamps, and integrity digest. No schema
was implemented in 3Q.

Audit must answer who requested/approved, what prompt/context/repo/task/base,
which target/adapter/provider/model/principal, which facts and decisions, what
dispatch/runtime/cancel/ambiguity occurred, what was captured, and how intake/
review/promotion ended.

Producer provenance records requesting agent, producer claim, target, adapter,
provider/model if known, principal, attempt, and result digest but remains
descriptive. Repository/task authority always comes from current governed PCAE
state, never runtime claims.

Generic intake is reused unchanged as the return path: the kernel maps a
normalized change result into a producer-neutral task/repo/base-bound
candidate; intake validates paths/scope/hashes/idempotency and emits evidence,
not execution or promotion. No Codex-/Claude-specific intake is permitted.

## Failure taxonomy

Frozen minimum:

```text
no_adapter_configured
unsupported_capability
unauthenticated
unavailable
permission_denied
enforcement_denied
dispatch_error
timeout
runtime_failure
malformed_result
result_ingestion_failure
```

Additive: canceled, rate_limited, ambiguous_outcome, integrity_failure.

## Security invariants

- adapter cannot self-authorize or alter human/PB/Runtime Enforcement decisions;
- adapter cannot choose repo/task authority or broaden cwd/env/network/
  filesystem/process/budget scope;
- identities remain non-equivalent; no agent-to-runtime inference;
- credentials are refs only and never persisted in contract/audit/output;
- network, subprocess, shell, mutation, outside-repo and paid effects default
  denied and are separately authorized;
- adapter implementation/digest is pinned and drift fails closed;
- durable record precedes dispatch and ambiguous outcomes never auto-retry;
- runtime output remains untrusted until normalization/intake;
- runtime completion != accepted change != promotion != successful PCAE task.

## First implementation and first real adapter sequencing

First implementation: **deterministic mock/dry adapter**, built-in and explicit,
using fixed fixtures, no subprocess, network, model, provider, credential, or
repo mutation. It exercises registration, selection, request/approval,
simulated gates, state/record/result, cancellation/failures, idempotency, and
generic intake. Its positive path remains a simulation and never changes real
runtime availability.

After independent mock verification: generic fixed-argv local executable
adapter against a deterministic non-AI fixture; then the first named AI target
should be an explicitly configured **Codex CLI RuntimeTarget**, never inferred
from `codex-local` or `codex-ox`. Claude-local follows without legacy-path
exemption. API providers wait for secret/network/budget controls.

## Contract verification and checks

- RPAC static verification: PASS — 65 required phase sections, matrices A-F,
  RPAC-REQ-001 through RPAC-REQ-097 sequential; 0 failed.
- Cross-check: Runtime Architecture/Plugin Model, Permission Broker, Runtime
  Enforcement, Shell Gate, generic intake, agent identities, Codex-Ox, backend
  preflight, HATP, legacy invocations, runtime inspect — PASS; all gaps have an
  explicit fail-closed disposition.
- `git diff --check`: passed after formatting normalization.
- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings only for longstanding historical
  `tasks/DONE.md` synchronization debt, unrelated to 3Q.
- `pcae push check`: passed for governed pushes.
- `pcae runtime inspect`: unchanged Observed/observe/unavailable, 0/0.
- `pcae notify status`: configured, enabled, ready.
- Full Fast Green: not run; the governing brief calls for source inspection,
  contract cross-checks, and static consistency for this architecture/contract
  phase, and no production/test/schema/version/build file changed.

## No-Go confirmation

Production source modified = **NO**. Execution activation = **NO**. External
runtime invocation = **NONE**. No adapter implementation or registration; no
Claude/Codex/Codex-Ox/OpenRouter/provider/model call; no subprocess runtime
path; no network; no credentials/secrets; no PB policy change; no Runtime
Enforcement or Shell Gate activation; no agent identity change; no HATP/HMIC/
Class-B/CLTR change; no Dell mutation; no release/version/build change.

Article remains **STOPPED and untouched**. Private
`~/repos/pcae-deepseek-research` remains **untouched, uninspected, not imported,
and not relied upon**.

## Verdict and next phase

```text
RUNTIME SURFACE RECONCILIATION: COMPLETE
RUNTIME / PROVIDER ADAPTER CONTRACT: FROZEN — RPAC-001 v1.0
CURRENT EXECUTION: UNAVAILABLE
AGENT IDENTITY: SEPARATE FROM RUNTIME TARGET
PRODUCER PROVENANCE: SEPARATE FROM RUNTIME IDENTITY
RUNTIME REGISTRY: VALID EMPTY STATE
ADAPTER SELECTION: EXPLICIT / NO SILENT FALLBACK
PERMISSION: SEPARATE FROM CAPABILITY
RUNTIME ENFORCEMENT: FUTURE PRE-DISPATCH GATE
GENERIC INTAKE: REUSED AS RETURN PATH
FIRST IMPLEMENTATION: DETERMINISTIC MOCK/DRY ADAPTER
REAL PROVIDER EXECUTION: NOT IMPLEMENTED
EXECUTION ACTIVATION: NOT PERFORMED
```

Exact next phase: **149O.20L.7O.3R — Deterministic Mock/Dry Runtime Adapter
Implementation Plan**.

Human decision is required to accept RPAC-001 v1.0 and begin 3R. 3R has not
begun. Phase 3Q stops here.
