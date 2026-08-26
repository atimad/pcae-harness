# Phase 149O.20L.7O.3Q — Runtime Surface Reconciliation and Runtime / Provider Adapter Contract Freeze

**Phase ID:** 149O.20L.7O.3Q
**Type:** architecture / contract freeze only
**Status:** COMPLETE
**Completeness:** complete for the stated architecture/contract scope
**Phase-entry commit:** `a52561954b78f1e195715baf4feb7db0e88fdebb`
**Public release:** `v0.4.3` at
`63580893b1de4782a694ab802ff7bdebdf29b0e6` — unchanged
**Frozen contract:** RPAC-001 v1.0,
`docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
**Production source modified:** NO
**Execution activation:** NO
**External runtime invocation:** NONE

## 1. Objective

Reconstruct the present public runtime, agent, backend, provider, prompt,
permission, enforcement, process, and intake surfaces from current primary
source; reconcile their overlapping identities and responsibilities; then
freeze the narrowest provider-neutral adapter boundary that can later support a
deterministic mock/dry adapter, local CLIs, APIs, and constrained third-party
runtimes without weakening PCAE governance.

The result is **RPAC-001 v1.0**, a documentation-only contract. The phase did
not implement, register, load, configure, or invoke any adapter.

## 2. v0.4.3 baseline

Phase entry established:

| Check | Entry truth |
|---|---|
| Worktree | clean before governed startup |
| Branch | `main...origin/main` |
| `origin/main..HEAD` | 0 commits |
| `HEAD` / `origin/main` | `a52561954b78f1e195715baf4feb7db0e88fdebb` |
| `v0.4.3^{commit}` | `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| `pcae health` | healthy; idle placeholder before startup; lock available |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | longstanding historical `DONE.md` sync warnings only |
| `pcae push check` | nothing to push; trust/identity checks passed |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins, 0 capabilities |
| `pcae notify status` | configured, enabled, ready |
| latest phase report | 3P complete; 3Q recommended; no governed phase active |

The idle placeholder was closed, the 3Q task contract was created, and
`pcae phase start --agent-id codex-local` established the governed lifecycle.
The `codex-local` lock is a session identity, not runtime selection or
execution authority.

## 3. 3P conclusions

The complete 3P architecture document was re-read as historical evidence. It
identified:

- a production bootstrap prompt whose final delivery is manual copy/paste;
- a canonical Runtime Registry that is empty and metadata-only;
- several descriptive agent/backend registries with inconsistent names;
- Permission Broker vocabulary for backend/adapter effects but no sufficiently
  bound dispatch request;
- design-only Runtime Enforcement models with zero production dispatch
  consumers;
- legacy public subprocess paths outside one canonical runtime boundary;
- no common process/API supervisor, secret reference, network enforcer, or
  persistent invocation record;
- producer-neutral intake as a reusable return path; and
- a preferred architecture of trusted PCAE kernel plus replaceable transport
  bridges, tested first with deterministic mock/dry behavior.

3P compared direct CLI, API-only, external provider gateway, and hybrid kernel
plus external bridges. It recommended the hybrid model, then a deterministic
mock/dry adapter, local-CLI contract/probe, one real local CLI, API later, and
provider gateway only if multiple providers justify it.

3Q did not assume that conclusion was correct. Each relevant claim was
re-derived below from current public source. The reconstruction confirms the
shape while tightening identity, registry, state, idempotency, and gate
contracts.

## 4. Runtime surface inventory

| Surface | Primary current source | Current truth | Future disposition |
|---|---|---|---|
| Runtime Registry | `core/runtime_registry.py` | In-memory immutable metadata; no loader/callable/persistence | Reuse as canonical declarative catalog foundation |
| Runtime Context | `core/runtime_context.py` | Compositional, session-scoped, observation-only | Reuse for observed task/session context; do not make authority |
| Runtime Snapshot | `core/runtime_snapshot.py` | Canonical read model composing introspection + context | Evolve read-only to show descriptor/status separation |
| Runtime inspect | `commands/runtime_inspect.py` | Constructs a new empty registry; reports Observed/observe/unavailable | Preserve behavior until adapters are actually governed and activated |
| Plugin Registry | `RuntimeRegistry` + plugin docs | Descriptor/introspection only | Do not silently overload as a loader |
| Backend registry | `backend_invocations.get_default_registry()` | Legacy metadata for Claude/DeepSeek/Codex/Qwen/mock | Migrate metadata; never retain as competing authority |
| Backend adapter registry | `backend_invocations.py` | Mock/preflight-only/disabled design contracts | Historical input only; not callable RPAC interface |
| Backend preflight | `core/backend_preflight.py` | Task/prompt/hash/scope checks; always non-authorizing | Keep separate; reuse compatible validation facts |
| Agent Registry | `core/agent.py:MULTI_AGENT_REGISTRY` | Descriptive session/workload labels | Preserve as `AgentIdentity` source only |
| Agent config registry | `core/agent.py:AGENT_CONFIG_REGISTRY` | Agent-to-adapter-type/executable hints | Treat mapping as advisory migration input only |
| Session agent identity | `AgentLock`, session bootstrap | Coordination lock with arbitrary `agent_id` | Preserve; never infer target/provider/model |
| Backend lock | session/phase `.pcae/agent-locks` code | Separate, inconsistent backend name maps and PATH facts | Do not treat as canonical target authority |
| Producer identity | `core/intake.py:derive_producer_provenance` | Descriptive agent-lock/candidate provenance | Reuse, enriched with invocation lineage; remains untrusted |
| Execution principal | Legacy subprocess/API environment | Not canonically represented | Add audited, non-authoritative identity before real adapter |
| Capability vocabulary | Runtime Registry + agent/backend descriptors | Multiple advisory vocabularies; runtime forbids declaring execute/enforce | Define exact target capability separately; no current capability change |
| Invocation authorization | legacy approval/preflight artifacts | Fragmented; no single target-bound authority bundle | Freeze InvocationApproval + DispatchEnvelope |
| Permission Broker | `permission_broker_foundation.py` | Action vocabulary exists; real execution denied; request under-bound | Future dispatch/effect permission owner after contract amendment |
| Runtime Enforcement | `backend_invocations.py`, safety constants | Evidence-only, non-authorizing, zero consumer | Future final whether-to-dispatch gate after explicit amendment |
| Shell Gate | `core/shell_gate.py` | Command classifier/audit simulation; no interception/enforcement | Future process-construction constraint, not dispatch authority |
| Generic intake | `core/intake.py` | Production, producer-neutral, task/repo/base/scope/hash validated | Reuse as normalized changes return path |
| Legacy real invocation | remote, execution-activation, capture/retry paths | Direct purpose-specific subprocess execution outside canonical registry/PB/RE | Retire, disable, or route through RPAC kernel before activation |
| Legacy shell pilots | runtime execution/output/audit commands | Each runs a fixed local command independently | Replace with record/result consumers; not runtime adapters |
| Agent discovery probes | `core/agent.py` | Runs CLI `--help`/`--version` for some agent labels | Separate explicit diagnostic probe from passive runtime inspect |

The inventory re-confirms the critical 3P finding: canonical runtime
unavailability is truthful for the canonical runtime but is not a
repository-wide interlock over historical executable commands.

## 5. Identity vocabulary reconciliation

### Matrix A — Identity reconciliation

| Identity | Current source | Meaning | Authority | Runtime binding | Future role |
|---|---|---|---|---|---|
| `claude-local` | Multi-Agent and Agent Config registries | Local-session agent label; executable hint `claude` | None | Advisory hint only | `AgentIdentity`; explicit target must be separate |
| `codex-local` | Multi-Agent and Agent Config registries | Local Codex-oriented session label | None; `runtime_execution` string is descriptive only | Advisory hint `codex` | `AgentIdentity`; may suggest but never select a target |
| `codex-ox` | Multi-Agent/Agent Config + intake tests | Distinct session/producer label for externally configured Codex/Ox use | None | Same executable hint as Codex; provider/model external | `AgentIdentity`/producer claim only |
| custom agent IDs | Agent lock accepts arbitrary IDs | Session coordination identity | Lock ownership only, not effect authority | None | Preserve opaque `AgentIdentity` |
| `pcae-native` | Agent Registry | PCAE governance-role label | No external invocation authority | Native descriptive configuration | Agent identity only |
| `claude`, `codex`, `qwen`, `mock` | legacy backend registry | Backend product/type names | None | Static artifact-only/preflight metadata | Migration aliases, not canonical targets |
| `claude-deepseek`, `claude-kimi` | backend/preflight/session maps | Mixed wrapper/provider/model-ish backend names | None | Inconsistent CLI name assumptions | Do not perpetuate composite identity |
| provider/model identifiers | Codex-Ox notes and legacy env-key metadata | External service/model settings, mostly outside PCAE | None | Not canonically bound | Optional `ProviderIdentity`/`ModelIdentity` |
| plugin IDs | `PluginDescriptor.plugin_id` | Registered metadata identity | None | No callable binding | Future adapter descriptor ID in canonical catalog |
| adapter IDs | legacy `BackendAdapterContract` | Preflight contract labels such as `adapter-codex` | None | No callable implementation | Canonical `AdapterIdentity` after RPAC implementation |
| runtime target IDs | absent | Configured executable/API destination | N/A | Missing | New explicit `RuntimeTargetIdentity` |
| producer kind | generic intake | Descriptive source claim or agent-lock derivation | None | None | Preserve and attach invocation lineage |
| execution principal | absent | OS/service/credential principal at effect time | N/A | Missing | New observed audit identity |
| invocation ID | multiple path-specific IDs | Request/artifact IDs with incompatible semantics | None | Partial | New stable logical ID plus unique attempts |

The same strings currently cross layers without one canonical meaning. That is
not proof of equivalence; it is the reconciliation problem RPAC resolves.

## 6. Agent identity

`AgentIdentity` is necessary because PCAE sessions, locks, workload
recommendations, and producer derivation already use it. It remains descriptive
and coordination-oriented. It may identify who prepared or requested an
invocation, but cannot select, configure, authenticate, permit, authorize, or
prove the runtime that eventually produced a result.

Frozen inequalities:

```text
agent_id != runtime_target_id
agent_id != provider_id
agent_id != model_id
agent capability label != runtime capability fact
```

## 7. Runtime target identity

`RuntimeTargetIdentity` is necessary and currently missing. It identifies one
explicit, versioned configuration binding an adapter to a concrete target. A
target can be a mock fixture, fixed local executable profile, API endpoint, or
constrained external bridge. Selection is by target ID plus descriptor/config
digests, never by an agent/backend name alone.

`AdapterIdentity` is separately necessary because many configured targets may
use one adapter implementation, and an implementation may be upgraded without
changing a human-facing target name.

## 8. Provider/model identity

`ProviderIdentity` and `ModelIdentity` are optional, separate identities.
Provider is needed for API endpoints, account/egress policy, and provenance.
Model is needed only when PCAE selects or reliably observes it. Local tools
that abstract model choice may leave it explicitly unspecified. Neither is
inferred from `codex`, `claude`, `codex-ox`, executable path, or credential
name.

Provider/model support constraints belong in the descriptor; defaults and
configured values belong in target configuration; the immutable expected
snapshot belongs in the request; declared and observed facts belong in the
result.

## 9. Backend-preflight reconciliation

`backend_preflight.py` recognizes `claude`, `claude-deepseek`,
`claude-kimi`, `codex`, and `subagent`. It validates known backend/action,
active task, prompt presence/hash, requested files, and allowed task scope. It
always requires human review and sets policy/authorization/execution false.

Incompatibilities:

- it assumes one backend name is enough to identify the check target;
- its names do not match the Agent Registry or backend-lock registries;
- it has no repository fingerprint/base binding, target config, provider,
  model, auth, status, network, environment, process, budget, or idempotency;
- it performs no dispatch, output capture, normalized result, or intake; and
- it is consumed by bootstrap/preflight/report flows, not a universal effect
  boundary.

Decision: keep it separate. Its prompt/hash/task/scope checks may feed future
request preparation, but it is neither the RuntimeAdapter preflight operation
nor a target resolver and will not be generalized in 3Q.

## 10. Runtime registry

`RuntimeRegistry` is the right canonical catalog foundation because it already
owns plugin IDs, immutable descriptors, capability lookup, health, and empty
state semantics. It is process-local and contains metadata only. It cannot
load, instantiate, configure, resolve, select, probe, authorize, or call an
adapter.

Future design uses one catalog, not a fourth competing registry:

- Runtime Registry owns admitted descriptor metadata and lookup;
- trusted kernel owns pinned implementation resolution/instantiation;
- target configuration binds descriptor to an explicit destination; and
- Runtime Status owns dynamic facts.

Legacy backend and backend-adapter registries are migration evidence, not
future authorities.

## 11. Plugin model

Current Runtime Architecture and Plugin Model documents describe a broader
future direction, but current source implements metadata/introspection only.
There is no callable provider, import/factory binding, lifecycle hook,
execution callback, dependency resolver, isolation, or persistence. The
`Execution Adapter` category is conceptual; `execute` and `enforce` are
currently undeclarable capabilities.

Decision: do not silently overload the Plugin Model. Future implementation
must explicitly add a trusted callable-resolution layer composed with the
registry and preserve passive `runtime inspect` semantics.

### Matrix B — Existing surface reuse

| Future need | Existing component | Reuse | Missing gap |
|---|---|---|---|
| Canonical catalog | Runtime Registry | Reuse metadata/uniqueness/lookup/empty state | Callable resolver, persistence, target config |
| Operational read model | Runtime Snapshot/inspect | Reuse composition and observation semantics | Adapter descriptor/status views |
| Task/repo scope | Task contracts + generic intake | Reuse active task, allowed paths, fingerprint/base checks | Request-time immutable binding |
| Prompt generation | `build_bootstrap_prompt` | Reuse content generation | Typed artifact, hash, target/effect approval |
| Prompt approval patterns | older ApprovedPromptArtifact store | Reuse immutable human-decision concepts | Bootstrap integration; exact target/effect binding |
| Dispatch permission | Permission Broker Foundation | Reuse centralized decision semantics and adapter vocabulary | Rich dispatch request and positive consumer contract |
| Final no-go evaluation | Runtime Enforcement models | Reuse evidence/digest/no-go concepts after amendment | Positive, production, pre-dispatch consumer |
| Command constraint | Shell Gate classifier | Reuse classification/redaction concepts | Interception/enforcement and argv-oriented contract |
| Result return | Generic intake | Reuse producer-neutral validation/idempotency | Mechanical result-to-candidate mapping |
| Human provenance | Agent lock / HATP domain patterns | Reuse descriptive lock; domain-specific trust only where applicable | Invocation-specific human approval provenance |
| Secrets | Provider env-name metadata | Do not treat as sufficient | Opaque secret reference/resolver/injector |
| Process/API supervision | Purpose-specific subprocess calls | Reuse no authority | One durable supervisor/cancellation/restart boundary |

## 12. Adapter boundary

The stable boundary is a `RuntimeAdapter` controlled by the trusted PCAE
kernel. It accepts only a post-gate `DispatchEnvelope` and returns transport
observations normalized into `DispatchReceipt` and
`RuntimeInvocationResult`. It does not consume raw user intent or decide
governance.

The architecture selected is:

```text
trusted PCAE kernel
  + canonical declarative runtime catalog
  + explicit RuntimeTarget configuration/status
  + replaceable transport adapter
```

This supports local, remote, and mock classes without making “provider” or
“agent” the common abstraction.

## 13. Adapter responsibilities

The adapter owns transport-specific target invocation, request/argv mapping,
process/API lifecycle, bounded capture, timeout, cancellation mapping, status
observation, and result normalization.

It must not own human authority, PB/Runtime Enforcement policy, task/repo
authority, runtime selection, automatic fallback, retry authorization, generic
intake acceptance, review, promotion, commit, push, or final task success.

## 14. Invocation request

RPAC-001 requires a versioned `InvocationRequest` with logical invocation and
attempt identities; idempotency key; authoritative repo/task/base/phase
binding; descriptive requester agent; explicit target/adapter/config digests;
optional provider/model snapshot; PromptArtifact and approval digests;
capabilities and expected result format; repository-bound cwd policy;
environment/network/filesystem/sandbox/process profiles; finite timeout;
cancellation requirement; and optional structured budget.

Fields are included because each binds authority, effect, replay safety, or
provider-neutral normalization. Arbitrary prose metadata, raw credentials, and
mutable live status are excluded.

## 15. Invocation result

The normalized result contains invocation/attempt identity; exact target,
adapter, descriptor/config and optional provider/model facts; acceptance,
dispatch/start/completion/capture observations; timestamps; terminal and
transport/exit/provider status; bounded output or hashed references;
structured response; changed-file/patch/diff references; usage/cost facts;
runtime and execution-principal provenance; observed confinement facts;
sanitized error classification; ambiguity/retry hints; and PCAE-added intake
references.

Provider-specific bodies may be opaque attachments. Generic consumers rely on
RPAC fields. Completion is never intake acceptance or task success.

## 16. Semantic state model

The frozen distinctions are:

```text
PCAE governance: PREPARED -> APPROVED -> PERMITTED -> AUTHORIZED
runtime fact:    CAPABLE (checked before permission, revalidated before authorization)
runtime observe: DISPATCHED -> ACCEPTED -> RUNNING -> COMPLETED -> RESULT_CAPTURED
intake:          INGESTED
```

Not every transport can observe `ACCEPTED` or `RUNNING`; it records them as
unobserved, not inferred. Failures may terminate between any states. A mock/dry
adapter uses a distinct simulation namespace and does not assert production
runtime transitions.

## 17. Prompt artifact

The bootstrap string is useful content but insufficient as a dispatch unit.
The contract introduces a deliberately light `PromptArtifact`: version, ID,
content/reference, SHA-256, generation method/version, repository/task/phase
binding, timestamp, provenance/derivation, and human-edit indicator. Target
agent hints remain non-binding.

This avoids adopting the older heavy Phase-45 proposal/roadmap/agent-adaptation
model as production truth while preserving its useful immutability and lineage
ideas.

## 18. Prompt approval

Approval is first-class for invocation but need not be a separate second
prompt-only decision. One immutable `InvocationApproval` can approve the exact
prompt digest and bind repository/task/base, selected target/config, effect
profiles, budget, expiry, and attempt count.

Current human copy/paste is implicit human approval/delivery but cannot support
machine replay. Older `approved_agents` does not mean approved runtime target.
Initial automatic dispatch policy must require explicit human approval for
every invocation.

## 19. Dispatch permission

Current PB vocabulary does support the *concept* of dispatch through
`adapter_invocation`/`backend_invocation` and adapter/backend execution
classes. It does not support a sufficiently bound positive real dispatch:
target, adapter, prompt digest, repository, effect profiles, network,
filesystem, credential reference, budget, and idempotency are absent; real
`simulation_only=false` remains categorically denied because execution is
unavailable.

Verdict: reuse the action vocabulary where possible and record a material
request/consumer gap. PB policy is unchanged in 3Q.

## 20. Runtime capability

Registered, installed, configured, authenticated, available, capable,
permitted, authorized, and executed are separate facts/states. Authentication
may be `not_required`; health may be `unknown`; capability must match exact
effects/result/platform, not only a string. None implies the next.

## 21. Runtime Enforcement

The exact future integration point is the final whether-to-invoke decision
after approval, capability/status, and PB permission, immediately before the
durable dispatch boundary. It must consume the whole immutable binding and
fresh facts. Current Runtime Enforcement is evidence-only, non-authorizing,
negative-only, and has no production consumer. A separately governed contract
amendment and implementation are prerequisites.

## 22. Gate ordering

### Matrix C — Gate ordering

| Gate | Owner | Input | Output | Can authorize? | Failure behavior |
|---|---|---|---|---|---|
| Prepare/bind | PCAE kernel | task/session/HEAD + prompt | immutable request | No | no request |
| Human approval | Human authority workflow | exact prompt/target/effects/budget | InvocationApproval | Yes, human scope only | stop; no PB request |
| Target resolve/preflight | Registry/resolver/adapter fact probe | request + target config | descriptor/status/capability facts | No | `no_adapter_configured`, unauthenticated, unavailable, unsupported |
| Dispatch/effect permission | Permission Broker | bound request + approval/evidence | scoped decision(s) | Can permit, not final-authorize | deny/human review; no adapter call |
| Freshness recheck | PCAE kernel | HEAD/config/status/approval | fresh evidence bundle | No | fail closed |
| Runtime Enforcement | PCAE trusted boundary | all bound facts/decisions | single-attempt authorization | Future final authorization only | enforcement denied; no adapter call |
| Durable dispatch intent | Invocation record owner | authorized envelope | persisted attempt state | No | no dispatch unless durable |
| Transport dispatch | Selected adapter | DispatchEnvelope | receipt | No | dispatch error/ambiguous outcome |
| Result intake | Generic intake | normalized change result | accepted/rejected evidence | No execution authority | quarantine/reject; task unchanged |

The ordering preserves permission != capability, capability != authorization,
and authorization != execution.

## 23. Selection

V1 selection is explicit human-visible `runtime_target_id`, captured before
approval. Config, task binding, or agent mapping may propose a choice, never
silently select or fall back. Target/provider/model changes require a new
approval and generally a new logical invocation.

## 24. Discovery

Trusted built-ins and explicit pinned configuration are the initial discovery
mechanisms. Python entry points and external executable descriptors may be
future admission sources only with separately contracted provenance, pinning,
and isolation. Ambient import scanning, PATH-driven auto-enable, or provider
fallback is forbidden.

## 25. Configuration

Minimum target configuration: target ID/version/digest, adapter ID, fixed
command descriptor or endpoint reference, optional provider/model,
`credential_ref`, environment/cwd/filesystem/network/sandbox/process profiles,
capability constraints, and explicit enablement. Descriptor is static;
configuration is deployment-specific; status is live.

## 26. Credential references

Credentials are opaque references only, never embedded secrets. Existing
environment-key lists, Telegram credentials, and HATP stores are domain
specific and do not provide a general provider secret-reference/resolution
abstraction. A least-privilege resolver/injector, account binding, redaction,
rotation, revocation, and audit contract is an explicit prerequisite for any
authenticated real adapter. None was implemented or accessed.

## 27. Local CLI semantics

A local CLI adapter requires a resolved/pinned executable, fixed argv without
shell interpolation, repository-bound cwd, minimal allowlisted environment,
defined stdin/file/argument prompt transfer, bounded stdout/stderr, finite
timeout, process-group/tree ownership, cancellation and signal escalation,
exit classification, descendant cleanup, filesystem/network confinement, and
normalized result mapping.

Inherited full environment, arbitrary runtime-supplied cwd, `shell=True`,
unbounded output, and unsupervised descendants are non-conformant.

## 28. API-provider semantics

An API adapter requires explicit provider/endpoint, TLS/egress policy, opaque
credential ref, bounded request/response schema, connection/total timeouts,
rate-limit handling, cancellation, ambiguous-delivery reconciliation,
usage/cost capture, and result normalization. Streaming is transport-local in
v1 and collapses into status plus a terminal result.

## 29. Mock/dry adapter

The first implementation target is a built-in deterministic mock/dry adapter.
It exercises registration, explicit selection, request/approval validation,
simulated gates, semantic state recording, dispatch receipt, terminal result,
cancellation/failures, idempotency, and generic intake linkage without a
process, network, model, credential, broad filesystem access, or repo mutation.

It is superior to starting with Codex/Claude because it falsifies the control
contract before transport, secret, cost, network, and process risks obscure
contract errors.

## 30. Invocation identity

A canonical logical invocation ID is required to prevent duplicate dispatch.
PCAE creates an opaque cryptographically strong random ID before approval; it
is not a timestamp or mutable-content hash. Each try receives a unique attempt
ID. The canonical content digest provides idempotency; identity and content
digest serve different purposes.

## 31. Idempotency

- Same invocation ID + identical content: return/resume the existing record;
  never redispatch.
- Same invocation ID + different content: hard collision.
- Restart before dispatch: resume validation, no effect assumed.
- Restart after dispatch intent/receipt with unknown outcome: mark ambiguous;
  no automatic retry.
- Duplicate same-digest completion: idempotent replay.
- Conflicting completion: quarantine integrity failure.
- Intake replay: deterministic candidate ID from invocation/attempt/result
  digest uses existing intake collision semantics.

## 32. Retry

Potential retry classes are pre-effect unavailability, confirmed non-delivery,
and rate-limit/transient errors with evidence of non-acceptance. Ambiguous
delivery, mutation, conflicting completion, and unknown process termination do
not auto-retry. Each retry has a new attempt ID, fresh target facts, fresh PB
and enforcement decisions, and fresh human authority if the approval does not
cover the attempt. Changed prompt/target/repo/effects/budget means a new logical
invocation.

## 33. Failure taxonomy

The minimum frozen categories are:

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

Additive categories include canceled, rate_limited, ambiguous_outcome, and
integrity_failure. Existing legacy failure names map into these semantics; an
adapter's retryable flag is advice, never retry authority.

## 34. Invocation record

A persistent append-only `RuntimeInvocationRecord` is mandatory before real
execution and should be exercised by the mock adapter. It contains identities,
request/artifact/config digests, repo/task binding, approval and gate evidence,
transition log, dispatch receipt, result reference/digest, failure/ambiguity,
retry lineage, intake references, timestamps, and record integrity digest.

3Q specifies this concept only. It creates no production schema or store.

## 35. Audit

Audit must reconstruct requester and human approver; prompt/context and
repo/task/base identity; selected target/adapter/provider/model/principal;
status/capability observations; PB and Runtime Enforcement decisions;
dispatch/accept/run/complete/cancel/ambiguity; captured output/result digest;
and intake/review/promotion disposition. Existing digest, provenance, report,
and intake patterns are reusable. Backend-specific stores are not alternate
authorities.

## 36. Generic intake handoff

The adapter returns a normalized result; the trusted kernel converts proposed
file changes to a producer-neutral intake candidate. Existing intake validates
active task, repository fingerprint, base commit, path safety, task scope,
operation/content hashes, idempotency, and then emits accepted evidence with no
execution/promotion authority. No provider-specific intake branch is needed.

Text-only results remain invocation artifacts rather than fake file-change
candidates.

## 37. Producer provenance

Producer provenance stays separate from runtime identity. The future chain
records descriptive requesting agent, producer claim, explicit target,
adapter, optional provider/model, execution principal, attempt, and result
digest. Current agent-lock-derived producer kind remains descriptive and
non-authenticating. Runtime claims cannot override authoritative binding.

## 38. Repository/task binding

PCAE derives repository identity/fingerprint, active task ID/contract digest,
base HEAD, and applicable phase/session from the current governed repository.
Those fields are bound before approval and checked again before dispatch and
intake. Runtime-returned repository/task claims are untrusted evidence and
cannot select authority.

## 39. Working directory

PCAE selects the canonical repository/worktree root or normalized allowlisted
descendant. The adapter receives that resolved binding; model/provider output
cannot supply it. Realpath/symlink escape and arbitrary absolute cwd fail
closed.

## 40. Environment

Default environment is minimal/sanitized, not inherited wholesale. Required
non-secret variables are allowlisted by profile. Governance variables are
explicit. Credential refs resolve just in time into the narrow child/request
context, are never persisted, and are redacted from output. Exact executable
resolution must not depend on an uncontrolled PATH.

## 41. Network

Network requirement is a static descriptor/target fact; network permission is
an explicit request/effect decision. Default is denied. A CLI may require
network even without an API endpoint, so “local” does not mean offline.
Provider/endpoint allowlisting, TLS identity, DNS/proxy/egress constraints, and
audited enforcement are dependencies for real network use.

## 42. Filesystem

Scope distinguishes repo read, repo write, controlled temp write, and outside-
repo access. Write and outside access default to none. Runtime changes are
untrusted until intake. A mock adapter needs no broad access and must not
mutate the repo. Real write capability later requires separately governed
confinement and mutation permission.

## 43. Shell Gate

Shell Gate currently classifies/redacts/audits proposed command text and calls
a prototype broker; it explicitly does not execute, intercept, install
wrappers, or enforce. Fixed argv still needs adapter/process-policy validation;
Shell Gate is defense-in-depth there. Shell text, expansion, pipelines, or
`shell=True` require an enforcing Shell Gate/equivalent and are forbidden while
the existing gate is non-enforcing.

Responsibility split:

```text
Runtime Enforcement = whether this exact invocation may cross the effect boundary
Shell Gate/process policy = how local command construction and launch are constrained
```

## 44. HATP relationship

Basic runtime dispatch has no current HATP dependency. HATP/Class-B is bound to
specific hardware-backed human/rollback/deployment trust domains, not provider
auth or general runtime lifecycle. A future policy may explicitly require a
hardware-backed approval for some dispatch effect, but RPAC does not import or
reinterpret HATP authority.

## 45. Provider/model fields

Descriptor: supported constraints only. Target config: defaults and exact
deployment binding. Request: immutable expected snapshot when known. Result:
declared plus observed provider/model facts. Both are optional for abstracting
local tools; unknown is explicit, never inferred.

## 46. Budget

V1 reserves a structured optional `resource_budget` extension. Mock/dry can
validate propagation with zero cost. Before any metered real target,
token/request/currency cost ceilings and retry/concurrency limits become
required. Missing budget means no paid use, not unlimited use.

## 47. Streaming

V1 does not freeze a public streaming event schema. Adapters may internally
consume streams but expose status observations and one bounded terminal
result. A later additive contract can standardize events if evidence requires
them.

## 48. Cancellation

The interface includes `cancel(attempt_id)`. Descriptor declares supported,
cooperative, or unsupported cancellation. Result distinguishes requested,
acknowledged, completed-before-cancel, unsupported, and unknown. Cancellation
does not prove external effects stopped. Mock/dry must exercise the interface.

## 49. Portability

Core identities, requests, results, states, and failure categories are OS-
neutral. Executable discovery, signals, process groups/trees, sandboxing, and
path mechanics live in declared platform profiles. The contract supports
macOS development and Linux deployment without embedding one OS's controls in
common fields.

## 50. Adapter interface

RPAC-001 freezes:

```text
describe() -> RuntimeDescriptor
preflight(InvocationRequest) -> AdapterPreflightResult
dispatch(DispatchEnvelope) -> DispatchReceipt
collect(attempt_id) -> RuntimeInvocationResult | PendingObservation
cancel(attempt_id) -> RuntimeCancellationResult
```

This receipt/collect split permits CLI and API supervision plus cancellation
without prematurely freezing streaming. The kernel owns persistence/gates;
the adapter owns transport and normalization.

## 51. Runtime descriptor

Immutable fields: contract and adapter identity/version/digest; class and
transport; supported capabilities/result formats; effect type; locality;
network requirement; platforms; cancellation mode; simulation namespace.
Descriptor contains no live health, credentials, permission, or task state.

## 52. Runtime status

Dynamic timestamped fields: registered, installed, configured, authenticated
or not-required, available, healthy/unknown, observed capabilities, source,
and observation time. Status is evidence, not authority, and must be refreshed
at the final boundary.

## 53. Registry contract

The registry provides unique registration, enumeration, descriptor lookup,
capability candidate lookup, status association, and explicit target
resolution with no fallback. Empty is valid. Duplicate IDs, drift, ambiguous
matches, and unknown major contract versions fail closed. Callable resolution
lives in the trusted kernel, not ambient plugin imports.

### Matrix D — Adapter contract

| Concern | Request | Descriptor | Status | Result | External concern |
|---|---|---|---|---|---|
| Identity | invocation/attempt/target/config | adapter/version/digest | installed observation | exact identities + provenance | human and execution principal |
| Provider/model | expected snapshot | supported constraints | observed reach/auth | declared/observed values | provider account/catalog |
| Capability | exact requested effects/result | declared support | live capable fact | actual observed effects | PB/RE authority |
| Prompt | artifact ref/hash | supported transfer formats | N/A | prompt hash echo | human approval |
| Repo/task/cwd | authoritative binding | platform/cwd constraints | resolved facts | observed cwd/change manifest | task authority/intake |
| Environment/secrets | profile refs only | required profile classes | configured/auth facts | sanitized observations | secret resolver |
| Network/filesystem | exact requested scopes | requirement/support | enforcement availability | observed use | OS/network control |
| Timeout/cancel | finite deadline/mode | cancellation support | currently available | timeout/cancel outcome | process/API supervisor |
| Budget | exact ceiling or no paid use | metering support | quota/rate fact | usage/cost | budget authority |
| Governance | approval/gate digests via envelope | none | none | none | human/PB/RE/kernel |
| Intake | expected result format | result formats | none | changes/diff/content refs | generic intake acceptance |

## 54. Runtime inspect evolution

Future inspect may add adapters, descriptors, targets, and timestamped status,
clearly separating static registration from live configured/authenticated/
available/capable facts. A mock appears as simulation-only/no-effect. Until
actual adapters are implemented and separately activated, current output stays
Observed/observe/unavailable and 0/0.

## 55. Backward compatibility

Contract freeze changes no CLI, source behavior, registry content, or
capability. Current 0-plugin/0-capability/unavailable consumers remain valid.
Unknown v1 optional fields can be preserved; unknown authority/effect fields
fail closed. Major semantic/gate/authority changes require a new major version.

### Matrix E — Runtime class comparison

| Criterion | Mock/Dry | Local CLI | API Provider |
|---|---|---|---|
| Effect | simulation only; none | local process, possibly network/filesystem | remote request, network |
| Secrets | none | optional opaque ref | normally opaque ref required |
| Process supervision | none/fixture state | mandatory tree, timeout, signals, capture | request/session lifecycle |
| Network | forbidden | explicit; may be required | mandatory explicit endpoint/egress |
| Filesystem | no broad access/no repo mutation | explicit read/write/temp scopes | normally none except controlled result artifacts |
| Prompt transfer | fixed fixture/in-memory | stdin/file/fixed argv | structured request |
| Output | deterministic normalized fixture | bounded stdout/stderr + changes | bounded response + provider metadata |
| Cancellation | deterministic modes | signal/process-tree semantics | provider/API cancel/abandon semantics |
| Cost | zero | optional/possibly metered | metered budget required |
| First use | contract-control verification | fixed-argv fixture then named CLI | after secrets/network/budget controls |

## 56. Security invariants

### Matrix F — Security invariants

| Threat | Contract invariant | Existing control | Future implementation dependency |
|---|---|---|---|
| Adapter self-authorizes | Adapter cannot create/change approval, PB, or RE decision | Current models are non-authorizing | trusted envelope verification |
| Agent name selects provider | agent/runtime/provider/model identities are unequal | Codex-Ox source comment is descriptive | explicit target resolver/UI |
| Stale target/HEAD | status/config/repo facts revalidated immediately before dispatch | repo HEAD/fingerprint helpers | freshness/digest binding |
| Duplicate external effect | durable record before dispatch; idempotent IDs; ambiguous outcome blocks retry | intake candidate replay checks | atomic invocation store |
| Secret leakage | opaque refs only; minimal injection; redaction before persistence | scattered redaction/env-name metadata | canonical secret resolver |
| Environment leakage | no full inherited environment | none general | environment allowlist builder |
| Shell injection | fixed argv; shell text needs enforcing Shell Gate/equivalent | classifier only | enforced argv/process policy |
| Network escape | explicit default-deny network effect | no general egress enforcement | network policy/enforcer |
| Filesystem escape | repo-bound cwd; explicit scopes; outside denied | task scope + intake validation/post-hoc checks | OS confinement/sandbox |
| Malicious output | untrusted result; generic intake validates changes | producer-neutral intake | quarantine/normalizer |
| Supply-chain adapter drift | pinned adapter identity/digest; no ambient auto-enable | descriptor uniqueness only | admission/resolver verification |
| Runtime claims task authority | kernel derives repo/task; runtime claim ignored | task and intake authority | request/envelope builder |
| Completion treated as success | completion != intake != promotion != task completion | intake/promotion separation | status/UI discipline |
| Retry duplicates effect | no automatic retry after possible dispatch | no common record today | supervisor/reconciliation |

Additional frozen invariants: adapter output cannot alter PB or Runtime
Enforcement decisions; one permission does not imply network/process/write;
the adapter cannot broaden cwd/environment/budget; and a registry entry cannot
make itself available or authorized.

## 57. Prompt-dispatch closed loop

Exact future interfaces:

```text
Task/Session authority
  --(ContextPack + bootstrap content)--> PromptArtifact builder
  --(hash/repo/task binding)-----------> InvocationRequest builder
  --(exact scope)----------------------> Human InvocationApproval
  --(explicit target)------------------> Registry + target resolver
  --(facts)----------------------------> Adapter preflight / RuntimeStatus
  --(effect request)-------------------> Permission Broker
  --(bound conjunction)----------------> Runtime Enforcement
  --(durable intent + envelope)--------> selected RuntimeAdapter
  --(receipt/collect)------------------> RuntimeInvocationRecord/result
  --(change mapping)-------------------> generic producer-neutral intake
  --(accepted evidence)----------------> existing review/promotion lifecycle
```

No provider-specific interface is permitted between normalized result and
intake.

## 58. First implementation recommendation

Implement RPAC-001 first as a deterministic mock/dry adapter and control-plane
test harness. It should prove request validation, explicit selection, gate
simulation, persistent identity/state, result normalization, idempotency,
cancellation/failure behavior, and intake linkage. It must remain in a test/dry
namespace and leave runtime inspect's real execution unavailable.

Do not start with Codex or Claude: either would add process, provider, secret,
network, and identity variables before the common contract is empirically
validated.

## 59. First real adapter sequencing

After independently verifying mock/dry behavior:

1. build the generic fixed-argv local executable adapter against a
   deterministic non-AI fixture, initially non-executing/preflight then under a
   separately authorized confined pilot;
2. make the first named AI target an explicit **Codex CLI RuntimeTarget** after
   PB, Runtime Enforcement, process supervision, secrets, environment,
   filesystem/network, and Shell Gate dependencies are ready;
3. add Claude-local by explicit target rather than grandfathering its legacy
   execution paths; and
4. add an API provider only after secret, egress, budget, rate-limit, and
   ambiguous-delivery contracts exist.

Codex is selected ahead of Claude for the first named runtime because current
source already proves multiple Codex session identities can share one CLI;
forcing explicit target binding directly validates the central non-equivalence
in this phase. This is sequencing advice, not implementation authority.

## 60. Contract versioning

Name/version: **Runtime / Provider Adapter Contract, RPAC-001 v1.0**. Patch
revisions clarify without semantics; minor revisions add backward-compatible
optional fields/status/failure values; new required fields, identity collapse,
gate-order changes, weakened invariants, or authority ownership changes require
a major version. Implementations pin supported versions, reject unknown majors,
and fail closed on unknown authority/effect semantics.

## 61. Contract verification

Static cross-check against current source produced:

| Surface | Verification result | Contradiction/disposition |
|---|---|---|
| Runtime Architecture | Conforms to Runtime-orchestrates / Registry-resolves / Plugin-implements direction | Current source does not implement resolve/call; RPAC states future dependency |
| Plugin Model | Conforms only as metadata foundation | No callable lifecycle; silent overload forbidden |
| Permission Broker | Existing adapter/backend vocabulary reusable | Request and positive dispatch contract incomplete; no policy change |
| Runtime Enforcement | Natural final conjunction point | Current form non-authorizing/zero-consumer; amendment required |
| Shell Gate | Responsibilities non-overlapping | Current classifier non-enforcing; real shell text forbidden |
| Generic intake | Fully compatible producer-neutral return path | Adapter result needs mechanical mapping; no provider branches |
| Agent identities | RPAC preserves existing descriptive use | Existing config hints not authoritative target mapping |
| Codex-Ox | Source expressly says provider/model external, execution not granted | RPAC freezes non-equivalence |
| Backend preflight | Compatible as request-preparation evidence | Not target preflight/dispatch boundary |
| HATP | No generic dispatch dependency | Remains domain-specific |
| Legacy invocations | Non-conformant parallel effect paths | Must be retired/disabled/routed before real activation |
| Runtime inspect | Backward-compatible | Contract-only change leaves 0/0/unavailable |

Contract structure verification confirms `RPAC-REQ-001` through
`RPAC-REQ-097` are unique and sequential, every required matrix is present,
and all 65 required phase sections exist. Repository static checks confirm no
production/test/schema/version/build file changed.

## 62. Findings

1. **F-3Q-001 — identity fragmentation:** agent, backend, adapter, provider,
   model, producer, and target labels are not interchangeable; current name
   overlaps are legacy vocabulary, not authority.
2. **F-3Q-002 — missing runtime target:** no current type binds an explicit
   configured executable/API destination to immutable request authority.
3. **F-3Q-003 — registry is a valid empty catalog:** it is the correct metadata
   foundation but has no callable resolution or live status.
4. **F-3Q-004 — Plugin Model is introspection-only:** no hooks/callbacks/loader
   exist; execution cannot be implied by category metadata.
5. **F-3Q-005 — backend preflight is bootstrap validation:** useful task/prompt/
   scope evidence, not runtime resolution or authorization.
6. **F-3Q-006 — dispatch permission contract gap:** PB vocabulary is adequate
   in concept but its current request cannot bind RPAC dispatch.
7. **F-3Q-007 — enforcement integration gap:** Runtime Enforcement is the right
   future final gate but cannot currently authorize or enforce anything.
8. **F-3Q-008 — legacy bypasses:** real subprocess paths exist outside one
   canonical runtime kernel; unavailable runtime is not a repo-wide interlock.
9. **F-3Q-009 — prompt binding gap:** production bootstrap content lacks typed,
   target/effect-bound identity; old approval models do not close it.
10. **F-3Q-010 — secret/supervision/network gaps:** no canonical secret resolver,
    safe process owner, environment allowlist, or network enforcer exists.
11. **F-3Q-011 — intake is reusable:** its producer-neutral task/repo/base/scope/
    hash/idempotency contract is the correct return boundary.
12. **F-3Q-012 — persistent record required:** no safe real dispatch exists
    without durable attempt identity, ambiguity handling, and replay control.

## 63. Final verdict

```text
RUNTIME SURFACE RECONCILIATION:
COMPLETE
RUNTIME / PROVIDER ADAPTER CONTRACT:
FROZEN — RPAC-001 v1.0
CURRENT EXECUTION:
UNAVAILABLE
AGENT IDENTITY:
SEPARATE FROM RUNTIME TARGET
PRODUCER PROVENANCE:
SEPARATE FROM RUNTIME IDENTITY
RUNTIME REGISTRY:
VALID EMPTY STATE
ADAPTER SELECTION:
EXPLICIT / NO SILENT FALLBACK
PERMISSION:
SEPARATE FROM CAPABILITY
RUNTIME ENFORCEMENT:
FUTURE PRE-DISPATCH GATE
GENERIC INTAKE:
REUSED AS RETURN PATH
FIRST IMPLEMENTATION:
DETERMINISTIC MOCK/DRY ADAPTER
REAL PROVIDER EXECUTION:
NOT IMPLEMENTED
EXECUTION ACTIVATION:
NOT PERFORMED
```

Contract verification: **PASS, no contradiction left unresolved inside the
frozen scope.** Every positive real execution dependency remains explicit and
unsatisfied.

## 64. Recommended next phase

Exact next phase:

**149O.20L.7O.3R — Deterministic Mock/Dry Runtime Adapter Implementation
Plan.**

3R should convert RPAC-001 into an implementation/test plan, define fixtures,
record-store and simulated-gate boundaries, migration/coverage for legacy
runtime surfaces, and independent acceptance evidence. It should remain
non-executing and must not prototype a real provider automatically.

## 65. Human decision required

Human authorization is required to begin 3R. This phase does not authorize it.
The decision is whether to accept RPAC-001 v1.0 and proceed with the
non-executing deterministic mock/dry implementation plan. If not accepted,
remain idle with execution unavailable.

## Completion boundary

- production source modified: **NO**
- runtime/plugin registration changed: **NO**
- execution availability changed: **NO**
- external runtime/provider invocation: **NONE**
- subprocess runtime path created/invoked: **NO**
- network/provider/credential access: **NONE**
- Permission Broker policy changed: **NO**
- Runtime Enforcement/Shell Gate activated: **NO**
- HATP/HMIC/Class-B/CLTR changed: **NO**
- Dell mutated: **NO**
- public `v0.4.3` changed: **NO**
- article: **STOPPED and untouched**
- private research repository: **untouched and not inspected**

Phase 3Q stops here. No implementation phase has begun.
