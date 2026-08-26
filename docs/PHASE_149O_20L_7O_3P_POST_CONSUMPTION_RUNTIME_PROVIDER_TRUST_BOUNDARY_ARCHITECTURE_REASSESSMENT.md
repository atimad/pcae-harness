# Phase 149O.20L.7O.3P — Post-Consumption Runtime / Provider / Trust-Boundary Architecture Reassessment

## Objective

Reconstruct PCAE's public runtime, provider, identity, permission, enforcement,
process, and producer-neutral intake architecture directly from current source;
use the production bootstrap-prompt handoff as the concrete probe; and select the
smallest safe architecture and next contract phase for replaceable external
runtimes. This is a read-only architecture phase. It grants no execution or
implementation authority.

## v0.4.3 baseline

Phase entry was clean and synchronized:

- phase-entry commit: `83af9b3b1b1485fa3acdf4d6eebcef95f692113e`;
- `HEAD == origin/main`, with `origin/main..HEAD = 0`;
- public `v0.4.3` still resolves to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`;
- `pcae health`, `pcae check`, and `pcae status coherence` reported
  healthy/passed/coherent;
- task-memory warnings were historical synchronization debt only;
- `pcae push check` reported nothing to push;
- `pcae runtime inspect` reported `not_implemented / Observed / unavailable /
  observe`, with an empty registry; and
- notification runtime was configured.

The previous phase report was complete and no governed phase was active before
3P startup. The public release remains `v0.4.3`. No release action was performed.

## Strategic transition

The mature S/M capability-consumption program remains:

```text
MATURE S/M CAPABILITY CONSUMPTION PROGRAM:
EXHAUSTED
```

Prompt creation is not reopened as a missing-generation capability.
`build_bootstrap_prompt()` is production-consumed. What remains is a new class of
problem: governed dispatch across a runtime/provider/trust boundary and safe
return of untrusted results.

## Current runtime architecture

The public source does not contain one coherent executable runtime. It contains
four distinct strata:

```text
Governed session/task state
  -> ContextPack + deterministic bootstrap-prompt rendering
  -> stdout / human copy-paste boundary

Runtime introspection
  -> fresh in-memory RuntimeRegistry
  -> RuntimeSnapshot
  -> Observed / observe / unavailable

Design-only execution governance
  -> backend preflight / Permission Broker foundation
  -> execution-attempt and Runtime Enforcement evidence models
  -> no production dispatch consumer

Legacy command-specific invocation surfaces
  -> remote execute / execution-activation / phase capture / shell pilot
  -> bespoke subprocess calls and bespoke artifacts
  -> not selected, authorized, or reported by the canonical Runtime Registry

External or already-created changes
  -> generic producer-neutral intake candidate
  -> task/repository/path/hash validation
  -> review and separately governed promotion
```

Primary source anchors are `core/context.py`, `core/runtime_registry.py`,
`core/runtime_introspection.py`, `core/runtime_snapshot.py`,
`commands/runtime_inspect.py`, `core/agent.py`, `core/backend_preflight.py`,
`core/backend_invocations.py`, `core/permission_broker_foundation.py`,
`core/shell_gate.py`, and `core/intake.py`.

### Consequential architecture finding

The canonical runtime is unavailable, but that statement is not currently a
repository-wide execution interlock. Public command paths still contain real
subprocess invocation:

- `pcae remote execute JOB --invoke` can build and run Claude, Codex, or Kimi
  CLI argv; its writable form changes CLI sandbox/permission flags and detects
  file changes after the process;
- `pcae execution-activation invoke` can invoke `claude-local` from an approved
  prompt and execution-authorization artifact inside a git-worktree sandbox;
- phase-specific real captured-task commands can invoke locked Claude-family
  backends; and
- the runtime execution pilot invokes an allowlisted local shell command.

Those paths do not consume the canonical Runtime Registry, Permission Broker
foundation, or Runtime Enforcement Coordinator as a common final boundary.
Therefore the verbose `runtime inspect` sentence that no invocation exists
"anywhere" is too broad when read repository-wide. The correct, narrower truth
is: **the canonical Runtime/Plugin architecture has no runnable target or
invocation path; separate legacy CLI paths exist outside that authority model.**
This split is a blocker to real runtime work and must be reconciled before a real
adapter is designed or enabled.

## Runtime registry truth

`RuntimeRegistry` is a process-local dictionary of immutable
`PluginDescriptor` metadata. Descriptors have no callable, class, module, import
path, transport, or factory. The registry can register metadata, list entries,
list/find declared capabilities, return metadata, and report metadata health and
consistency. It cannot load, instantiate, resolve a live provider, select a
target, poll live health, manage lifecycle, or invoke anything.

`pcae runtime inspect` constructs a new registry for each invocation. No
persistence or shared composition root populates it. Its current exact state is:

- registry state: `empty`;
- registered plugins: `0`;
- registered capabilities: `0`;
- current runtime state: `Observed`;
- maximum plugin capability: `observe`;
- execution availability: `unavailable`.

Zero is a current implementation/configuration consequence, not an abstract
requirement that future registries remain empty. The stronger present invariant
is that no descriptor may declare `enforce` or `execute`, and no implementation
status may claim `implemented`. Existing capability vocabulary is `observe`,
`advise`, `approve`, `deny`, `enforce`, `execute`, `audit`, `notify`, `store`, and
`rollback_prepare`; `enforce` and `execute` are undeclarable. `Execution Adapter`
is already a plugin category, but only as metadata taxonomy.

There is no selection or fallback algorithm. `find_capability()` returns all
declaring metadata without compatibility, health, or lifecycle resolution.
There is no current executable runtime in the canonical registry.

## Agent vs runtime identity

Identity must remain factored. A label in one column cannot silently confer a
property in another.

| Identity axis | Current representation | Current trust/meaning |
|---|---|---|
| Agent/session identity | `MULTI_AGENT_REGISTRY`; `.pcae/agent-lock.json` | Descriptive coordination identity. The lock accepts an agent ID; it is not authentication or execution authority. |
| Producer provenance | intake `producer.kind` derived from core lock or explicit input | Descriptive and consistency-checked, not authenticated. |
| Runtime/backend identity | `AGENT_CONFIG_REGISTRY`, backend registries, legacy backend lock | Transport/configuration labels with inconsistent vocabularies; not a canonical live target. |
| Provider identity | Configuration notes and environment-key names | No authenticated provider-account/service-endpoint model. |
| Model identity | Mostly external configuration or descriptive prose | Not canonically bound or authenticated. |
| Execution principal | Inherited OS process/user/credential environment | Implicit; no first-class record or attestation. |

Current `MULTI_AGENT_REGISTRY` identities are available `claude-local`,
`codex-local`, `codex-ox`, `pcae-native`, and `kimi-local`, plus declared
`deepseek-local`, `gemini-local`, `grok-local`, and `perplexity-local`.
Availability in that advisory registry is not runtime availability.

`claude-local` is a descriptive agent with a CLI configuration hint and is also
recognized by legacy real invocation paths. `codex-local` is a descriptive
agent with a Codex CLI hint and even a `runtime_execution` capability label, but
that label does not make the canonical runtime executable. `codex` is a separate
backend/preflight/legacy-lock name. The split between `codex` and `codex-local`
is unresolved vocabulary, not a deliberate target resolver.

The core session lock is distinct from `.pcae/agent-locks/latest.json`. Session
and phase commands also use different lockable-backend sets: notably,
`codex-local` is absent from the session backend vocabulary while `codex` and
`codex-ox` appear, and phase handoff lock synchronization uses another narrower
set. A session can therefore be owned by one descriptive identity while the
legacy backend-lock artifact remains stale or names another identity. Neither
lock authenticates a provider, model, or OS principal.

## Codex-Ox position

Current source confirms the historical posture:

- first-class, available PCAE agent/session identity;
- generic producer-intake compatibility through the same producer-neutral path;
- a Codex CLI executable hint shared with `codex-local`;
- no `runtime_execution` capability claim;
- provider/model configuration explicitly external to PCAE;
- no OpenRouter transport, provider authentication, model authentication, or
  canonical runtime-registry entry; and
- no `_build_invoke_command` branch in the existing real remote-job path.

`agent_id=codex-ox` must not imply a provider, model, or runtime. To become a
target it would need an explicit identity-to-target mapping, selected runtime
configuration, provider endpoint and model binding, authenticated credential
reference, live capability/health facts, network policy, Permission Broker and
Runtime Enforcement bindings, supervision/confinement, normalized result
handling, and a link to generic intake. No such layer was added in 3P.

## Bootstrap prompt path

The exact production generation path is:

```text
pcae session bootstrap --compact
  -> _run_compact_bootstrap(...)
  -> build_context_pack(root)
  -> handoff / audit / prompt metadata + resolved profile
  -> build_bootstrap_prompt(pack, profile, handoff, audit, prompt)
  -> deterministic text on stdout
  -> human copies text into a separately selected agent/runtime session
```

Inputs include active task goal/contract, governance health/check/session and
core agent-lock state, policy/orchestration and provenance, project roadmap and
recommended phase, TODO staleness, handoff/audit/prompt metadata, IRG context,
rules/validation, and architecture memory. Repository and task information are
included through the context pack. The prompt builder itself is vendor-neutral
and does not receive `agent_id`.

Non-compact `session bootstrap --agent-id ...` acquires or rehydrates session
state; it does not call `build_bootstrap_prompt`. `phase handoff` builds a
separate, simpler continuation prompt and explicitly prints manual steps.
Compact bootstrap output is not persisted as an immutable prompt artifact.
`context export` can persist a context pack, but bootstrap does not use that
path. Older PromptArtifact/ApprovedPromptArtifact models in `core/agent.py` are
not wired to this production bootstrap output.

The human currently performs four implicit acts in one gesture: views content,
accepts it, selects a target application/account/model, and dispatches it. The
external runtime then executes outside PCAE, and any return enters PCAE only
through a separate intake operation.

## Prompt handoff requirements

Automatic handoff needs more than a string-returning prompt builder:

1. materialize and hash the prepared prompt with task/repository/base-commit
   binding;
2. keep human content approval separate from target selection and dispatch
   permission;
3. resolve one explicit configured target with provider/model facts and no
   silent fallback;
4. verify live capability, configuration, authentication, environment,
   sandbox, network, and resource constraints;
5. obtain a Permission Broker decision for the dispatch effect;
6. have Runtime Enforcement verify the complete, mutually bound evidence set
   immediately before a single atomic dispatch boundary;
7. supervise the call, persist state transitions, support bounded cancellation,
   and normalize terminal outcomes;
8. quarantine returned text/change artifacts and bind them to the invocation;
   and
9. translate proposed changes into the generic producer-neutral intake shape,
   without provider-specific promotion logic.

Prompt generation, approval, dispatch, runtime acceptance, execution,
completion, intake, and promotion remain non-equivalent.

## Semantic gates

The proposed future order is:

```text
prepare and persist prompt
  -> human approves content and explicit target
  -> resolve target + capability/config/auth preflight
  -> Permission Broker evaluates dispatch/network effects
  -> Runtime Enforcement verifies all bound facts and decisions
  -> atomic dispatch boundary creates durable attempt state
  -> transport bridge invokes runtime/provider
  -> supervised result capture + terminal audit
  -> generic intake (separate acceptance boundary)
```

Capability is a fact, not authority, so it can be checked before asking the
broker; it must be rechecked or cryptographically bound at the final dispatch
boundary to prevent time-of-check/time-of-use drift. Human approval is an input
to permission and enforcement evaluation, not a substitute for either.

## Permission Broker relationship

Provider/runtime dispatch is a permission-relevant external effect. Existing
canonical vocabulary already has `backend_invocation` and
`adapter_invocation`, with corresponding execution classes. A new action type is
therefore not yet proven necessary. Network egress, and any filesystem/shell
effect, are independent permissions and cannot be smuggled inside an adapter
allow.

The broker should govern whether dispatch may occur. It should not determine
whether a runtime is installed, healthy, capable, or authenticated. Current
`PermissionBrokerRequest` cannot adequately bind runtime/provider/model
identity, prepared-prompt digest, approval artifact, repository digest,
credential reference, network/sandbox/resource profiles, idempotency key, or
invocation record. Non-simulation execution also remains categorically denied
and every decision reports `execution_unavailable`. Thus the action vocabulary
is reusable, while its request/consumer contract has a material gap.

## Runtime Enforcement relationship

The execution-attempt, no-go, evidence-bundle, Runtime Enforcement Decision,
and Coordinator models in `core/backend_invocations.py` were designed around a
future execution-attempt boundary. They validate referenced evidence,
authorization/safety flags, approval, audit, rollback/reporting, identity,
scope, and unsupported requests. They are design-only, non-authorizing, and
explicitly deny backend, adapter, subprocess, shell, and network requests under
today's contract.

No production dispatcher consumes the Coordinator as a final gate. Provider
dispatch is the natural future consumer only after a deliberate, versioned
contract amendment; the current negative-only contract cannot be treated as a
latent positive authorizer. The engine can and should remain dormant while the
runtime is unavailable.

## Execution Attempt Boundary

`GovernedExecutionAttemptBoundary` is evidence-only. Its authorization fields
must remain false; backend, adapter, subprocess, shell, network, mutation,
apply, rollback, commit, and push requests are denial reasons. It currently
proves refusal, not safe execution.

The future boundary should be a narrow trusted-kernel operation that atomically:

- verifies prompt, task, repository, target, approval, preflight, broker, and
  enforcement bindings;
- creates or resumes a durable invocation identity;
- refuses ambiguous replay;
- passes a constrained request to exactly one transport bridge; and
- records whether dispatch did not occur, may have occurred, was accepted, or
  reached a known terminal state.

Exact authority ordering is: human content/target approval -> Permission Broker
effect permission -> Runtime Enforcement final conjunction -> dispatch. Runtime
capability/configuration facts are prerequisites bound into that conjunction,
not sources of authority.

## Backend preflight

`core/backend_preflight.py` recognizes `claude`, `claude-deepseek`,
`claude-kimi`, `codex`, and `subagent`, plus an action vocabulary containing
`backend_invocation`. It checks name/action recognition, active task contract,
prompt presence/hash, requested files, and task scope. It always requires human
review and reports `backend_allowed_by_policy=false` and
`authorization_granted=false`/`execution_authorized=false`.

It does not discover an executable, select a provider/model, verify a live
runtime, authenticate, make network calls, invoke, capture output, perform
intake, or intercept shell use. Its direct consumers are CLI preflight/report
paths. Its prompt/task/scope checks are reusable as inputs, but it cannot serve
as a target resolver or dispatch boundary unchanged; its backend vocabulary
also does not line up with the agent/runtime labels.

## Provider abstractions

| Abstraction | Production? | Real implementation? | Caller | Network? | Auth? | Execution? |
|---|---|---|---|---|---|---|
| Runtime Registry / Snapshot | Production introspection | Metadata only; fresh empty registry | `pcae runtime inspect` | No | No | No |
| Multi-Agent / Agent Config registries | Production descriptive CLI data | Static entries and executable hints | agent/session/remote commands | No discovery call | No | Not by registry |
| Session/phase backend-lock registries | Production artifact writers | Static, inconsistent name maps; PATH probe | bootstrap/handoff/backend-lock commands | No | No | No authority |
| `core/backend_preflight.py` | Production preflight | Static task/prompt/scope checks | backend preflight CLI flows | No | No | No |
| `backend_invocations.get_default_registry()` | Production-exposed legacy design | Metadata for Claude, Claude-DeepSeek, Codex, Qwen, mock | `pcae backend ...` | No | Env-key names only | No real execution |
| BackendAdapter contracts | Production-exposed design/prototype | mock only; real adapters preflight-only, custom disabled | backend CLI/report flows | No | Presence/redaction metadata | No real execution |
| Advisory Provider protocol | Production advisory | Local provider implementation over RuntimeSnapshot | advisory command | No | No | No |
| Remote job path | Production CLI | Real Claude/Codex/Kimi subprocess path | `pcae remote execute --invoke` | Indirect/uncontrolled | Inherited CLI state | Yes, outside canonical runtime |
| Execution Activation path | Production CLI | Real `claude -p` in worktree | `pcae execution-activation invoke` | Not isolated | Inherited CLI state | Yes, separately gated |
| Phase capture path | Production CLI | Real Claude-family subprocess | phase `...backend-capture --execute` | Indirect/uncontrolled | Inherited CLI state | Yes, phase-specific |
| Runtime execution pilot | Production CLI/prototype | Allowlisted local shell command | `pcae runtime-execution-pilot` | Command-specific | Inherited environment | Local shell only |

No current abstraction provides authenticated provider identity, model routing,
network mediation, or a canonical provider transport.

## External wrapper/process supervision

PCAE has many purpose-specific `subprocess.run` calls, not a safe common agent
subprocess wrapper. Existing agent invocation paths generally provide argv,
captured stdout/stderr, an exit code, and a wall-clock timeout. The execution-
activation path adds a git-worktree workspace and output/change artifacts.

There is no shared process owner with a durable process identity, process group
or tree tracking, PTY/terminal integration, streaming contract, cancellation
handle, signal escalation policy, detached-descendant cleanup, crash/restart
reconciliation, bounded environment, or authoritative in-flight record.

A future local-CLI bridge needs: fixed argv construction; explicit cwd;
allowlisted environment; stdout/stderr framing and caps; start/accept/exit
timestamps; exit/signal classification; process-group ownership; graceful then
forced cancellation; timeout; descendant containment; partial-result handling;
and restart reconciliation from a durable invocation record. API bridges need a
parallel request/session owner, response streaming, cancellation, and ambiguous
delivery treatment rather than OS process-tree mechanics.

## Environment/sandbox

Current reusable controls are task allowed/forbidden paths, repository
fingerprint and base-commit binding in intake, clean-tree checks, post-hoc git
diff/status checks, and a git-worktree sandbox in Execution Activation.

The worktree is workspace isolation only. Source explicitly reports
`network_isolation=false`, `process_isolation=false`, shared git object storage,
and `production_containment_ready=false`; absolute paths, symlinks, inherited
credentials, or descendants can cross that boundary. Other legacy real paths
run in the repository or inherited current directory and rely mainly on
post-hoc mutation checks.

There is no general environment allowlist, secrets broker, OS filesystem
confinement, network namespace/egress allowlist, or process sandbox. Architecture
must distinguish declared sandbox profile, verified platform capability, active
enforcement, and post-hoc detection.

## Shell Gate relationship

`core/shell_gate.py` classifies commands and can produce/redact evidence; it does
not intercept or execute commands and is non-enforcing. A fixed-argv local CLI
bridge does not require a global general-purpose shell interceptor, but it does
require equivalent command/argv validation and process policy. Shell Gate is
therefore optional defense-in-depth for fixed non-shell bridges and a strict
prerequisite for any custom adapter that accepts shell text or shell expansion.
An HTTP/API bridge is not dependent on Shell Gate; it instead requires network,
endpoint, credential, and request-shape enforcement. Shell Gate remains dormant.

## HATP/trust relationship

HATP/Class-B proves trusted human provenance for specifically bound rollback
operations. It is not a runtime lifecycle, provider authentication mechanism,
or general execution capability. Prompt approval and runtime dispatch do not
automatically require HATP under current contracts. A future policy may require
hardware-backed human approval for a defined dispatch class, but that would be a
new explicit authority decision; it must not overload existing rollback
bindings. Runtime invocation trust, provider authentication, human signing, and
deployment binding remain separate. Existing trust blocks are unchanged.

## Credentials/secrets

Backend metadata names environment variables such as provider API keys, and
preflight/artifact code can report presence and redact likely secrets. CLI paths
inherit whatever login/session/environment the child process sees. Codex-Ox
configuration is explicitly external. Telegram and HATP have domain-specific
credential handling, but neither is a general provider-secret abstraction.

PCAE currently has no canonical secret reference, provider credential store,
least-privilege environment injector, rotation/revocation state, or proof of
which account authenticated an invocation. Future adapters need opaque
credential references, never embedded values; strict environment allowlists;
provider/account binding; redaction before persistence; and revocation/error
semantics. No secrets were accessed in 3P.

## Prompt approval

The current copy/paste step is an **implicit human boundary**: the human sees the
prompt, selects a destination, and initiates delivery. It is not a durable,
machine-verifiable approval. The older ApprovedPromptArtifact concept is not
wired to bootstrap output.

Future automatic dispatch should require an independently persisted approval
binding the exact prompt digest, task/repository/base commit, selected target,
scope, expiry, and permitted attempt count. Initial policy should require human
approval for every invocation. A later contract could define bounded
auto-approval, but 3P neither invents nor grants that authority.

## Dispatch authorization

Human approval answers "is this content/target acceptable?" Permission Broker
answers "may PCAE create this external effect under policy?" Runtime Enforcement
answers "are all required, mutually bound facts and permissions present now?"
The bridge answers none of those questions. Existing
`backend_invocation`/`adapter_invocation` action vocabulary can express the
effect, but its positive execution semantics and production consumer are
missing.

## Cost/resource governance

Existing pieces offer isolated wall-clock timeouts, output caps in some paths,
and context-character budgets. There is no canonical provider token budget,
monetary cost cap, per-model/provider allowlist bound to dispatch, concurrency
limit, or retry budget. A real API or metered CLI call requires all of these to
be expressed as pre-dispatch constraints and measured in the terminal record.
A mock adapter can validate their propagation with zero spend.

## Network governance

PCAE classifies some shell/network indicators but does not enforce process or
API egress. A CLI may use network without the shell classifier seeing the
underlying traffic. Every networked target therefore needs explicit network
permission, endpoint/provider allowlisting, TLS/identity expectations, proxy
and DNS policy, and denial when enforcement is unavailable. Network permission
is separate from adapter dispatch permission. No network was enabled in 3P.

## Runtime output contract

A future normalized result envelope should include at minimum:

- invocation/attempt identity and idempotency lineage;
- selected runtime/adapter/provider/model identity as declared and, where
  possible, observed;
- prompt hash and task/repository/base-commit binding;
- start, accepted, end, and capture timestamps;
- technical terminal status, exit/signal/transport/provider status;
- bounded stdout/stderr or content-addressed references and hashes;
- structured result, patch/diff, and changed-file manifest where applicable;
- usage/token/cost accounting;
- sandbox, environment, network, and supervision profile references;
- partial/ambiguous outcome and retry classification; and
- provenance, audit, and downstream intake reference.

It must never equate technical completion with governance acceptance. Raw
provider output remains untrusted. Secret-bearing payloads must not be stored
unredacted.

## Generic intake return path

The current inbound path is:

```text
external producer files/change descriptions
  -> build_intake_candidate_from_files / intake candidate
  -> producer + task + repo fingerprint + base commit binding
  -> operation/path/content-hash validation and idempotency
  -> accepted evidence with execution_allowed=false,
     promotion_executed=false
  -> separate review/promotion lifecycle
```

This is producer-neutral and accepts arbitrary descriptive producer kinds,
including Codex-Ox. A future bridge should translate proposed changes into this
existing candidate format or a contract-compatible generic candidate; it must
not create Claude/Codex/provider-specific intake branches. Runtime success is
not intake acceptance, and intake acceptance is not promotion.

## Closed-loop architecture

| Loop element | Existing piece | Missing edge |
|---|---|---|
| Task/session | Governed task contract, session snapshot, locks | Unified authenticated execution identity |
| Context/prompt | ContextPack and production bootstrap generator | Immutable prompt artifact and approval binding |
| Target | Descriptive agent/backend/plugin registries | Canonical configured target resolver and live capability/auth facts |
| Permission | PB action vocabulary | Dispatch-specific request binding and universal consumer |
| Enforcement | Design-only attempt/decision/coordinator | Amended positive contract and atomic production boundary |
| Invocation | Several legacy subprocess paths | One supervised bridge interface and canonical record |
| Result | Path-specific stdout/change artifacts | Normalized result envelope and tamper-evident invocation linkage |
| Intake | Generic producer-neutral candidate validation | Mechanical result-to-candidate adapter |
| Review/promotion | Existing governed lifecycle | No new provider-specific path required |

Target loop:

```text
PCAE task/session
  -> governed context and immutable prompt
  -> human approval + explicit target
  -> capability/preflight + PB + Runtime Enforcement
  -> trusted dispatch boundary
  -> replaceable external transport bridge
  -> untrusted normalized result
  -> generic intake candidate
  -> existing review/governance/promotion
```

## Runtime-neutral adapter design

The stable abstraction should be a **runtime target plus transport bridge**:

- the trusted PCAE kernel owns selection, identity/task/repository/prompt
  binding, authority, policy, final enforcement, invocation state, audit,
  result quarantine, and intake linkage;
- a target descriptor owns declarative capabilities, platform constraints,
  provider/model/configuration references, and health-probe contract; and
- a replaceable bridge owns only transport-specific mechanics: fixed CLI argv
  or API request construction, provider authentication injection, stream/
  cancellation mapping, and conversion into a normalized result envelope.

"Provider adapter" is too narrow for local CLI. "Agent adapter" confuses
descriptive agent identity with execution target. "Execution driver" is too
broad and risks moving authority into an extension. "Runtime adapter" is usable
at the orchestration edge if its provider transport remains a subordinate,
untrusted implementation detail.

## Local CLI vs API

| Concern | Local CLI runtime | API/provider runtime |
|---|---|---|
| Process supervision | Required: process group/tree, signals, exit status | No child process; request/session lifecycle required |
| Network | Often indirect and otherwise invisible | Direct, explicit endpoint/egress requirement |
| Credentials | Existing CLI login or inherited environment | Token/OAuth/account credential injection |
| Streaming | stdout/stderr framing or PTY if deliberately supported | Protocol events/chunks |
| Cancellation | Signals plus descendant cleanup | Request/session cancel and ambiguous-delivery handling |
| Output capture | Text streams and filesystem diff | Structured response/tool events plus declared artifacts |
| Sandboxing | OS process/filesystem/network confinement | Keep provider from direct filesystem access; quarantine output |
| Cost | Often weak or indirect telemetry | Usage/token/cost typically explicit but must be normalized |
| Result normalization | CLI/version-specific parsing | Schema/protocol-specific parsing |
| Portability | Binary/version/flags/signals/platform differ | HTTP stack is portable; endpoint/auth policies still vary |

Neither class is integrated or authorized by this phase.

## Codex future path

A future Codex CLI bridge needs explicit mapping from a selected target—not
from `agent_id` alone—to a pinned executable/version/argv contract, declared
sandbox support, working directory, bounded environment, authenticated account
and model configuration, network posture, capability probe, process
supervision, normalized output, and generic intake conversion. `codex` versus
`codex-local` naming must be reconciled first. Codex-Ox must be a separate
configured target sharing a bridge implementation only if its provider/model
binding is explicit; it must never be inferred from the agent label.

## Claude-local future path

Current registration represents an available descriptive agent, CLI executable
hint, and several legacy executable code paths. It is not a canonical Runtime
Registry target. A future Claude bridge has the same fixed-argv, cwd,
environment, identity, network, supervision, confinement, result, and intake
requirements. Existing real Claude paths are evidence to reconcile and reuse
selectively, not a safe foundation to activate as-is.

## Generic custom runtime

A custom runtime must provide a versioned target descriptor and bridge that can
report configuration/capability/health; accept only a fully bound invocation
request; obey environment/network/sandbox/resource constraints; support the
declared cancellation and ambiguity model; emit a normalized result; and never
authorize itself or promote its own output. Unknown/custom targets are disabled
until explicitly installed, configured, pinned, and selected. Shell-text custom
adapters require an enforcing Shell Gate or equivalent boundary.

## Plugin-model relationship

The plugin model is applicable as discovery metadata and vocabulary. It is not
an executable extension system today. Making `RuntimeRegistry` itself load and
run arbitrary Python callables would expand the most trusted component and turn
metadata registration into code authority.

The recommended architecture keeps registry metadata under PCAE control while
placing real transport mechanics behind constrained bridges. The registry may
eventually point to a bridge declaration; it must not become the permission
decision point or silently import third-party code into the kernel.

## Runtime registry evolution

Future target state must distinguish:

```text
defined -> registered -> installed -> configured -> authenticated
        -> healthy -> available -> capable
```

These are lifecycle/fact states. `permitted` and `authorized` remain
invocation-scoped governance states and must never be folded into target
lifecycle. Existing registry vocabulary covers defined/registered/configured/
healthy/available/disabled/failed/retired but lacks installed/authenticated,
live checks, persistence, and resolution. Any extension requires a contract
before code.

## Selection semantics

Initial selection should be explicit human selection from configured,
policy-visible candidates. Task configuration may propose a default, descriptive
agent identity may provide an advisory mapping, and capability/policy may filter
candidates, but none may silently dispatch. There is no fallback to another
provider/model. A retry stays on the exact approved target unless a new approval
and permission decision binds a changed target.

## Identity mapping

`agent_id` describes who/what owns or produced work; it does not identify a
runtime instance. A future explicit mapping should be:

```text
descriptive agent identity
  -> optional target recommendation
  -> human-selected runtime_target_id
  -> adapter_id + provider/account/model configuration refs
  -> observed execution principal
```

Each arrow is inspectable. `codex-ox` may recommend an Ox-configured target but
cannot imply one automatically.

## Failure semantics

Required distinct outcomes include:

- `not_configured`, `unavailable`, `capability_mismatch`;
- `auth_missing`, `auth_failed`;
- `dispatch_denied`, `enforcement_denied`;
- `dispatch_transport_failed`, `rejected_by_runtime`;
- `timeout`, `canceled`, `crashed`, `network_failure`, `rate_limited`;
- `malformed_result`, `partial_result`, `ambiguous_dispatch`;
- `completed_no_changes`, `completed_with_changes`;
- `intake_rejected`, `result_ingested`; and
- a separate later promotion disposition.

The older backend-adapter vocabulary for missing environment, unavailable,
authentication failure, rate limit, timeout, missing/malformed output, and
interruption is reusable, but it is not wired to a canonical invocation.

## Retry/idempotency

Pre-dispatch failures may be retried after prerequisites change without risking
duplicate provider work. Once dispatch may have occurred, an unknown outcome is
not automatically replayable. The operator or an explicit future policy must
authorize retry after inspecting the invocation record/provider status.

Use a stable logical invocation/idempotency key where the provider supports it,
with a new attempt ID for every transport attempt under one lineage. Bind target,
prompt hash, task/repo, authority artifacts, and budgets. Cap attempts and total
cost/time. A restart resumes record reconciliation, not blind execution.

## Invocation record

A canonical `RuntimeInvocationRecord` or equivalent is necessary. Its purpose is
to make authority, effects, ambiguity, retry, and result lineage durable. Minimum
binding is: invocation and attempt IDs/idempotency key; task/repository/base
commit; prompt artifact/hash; selected runtime/adapter/provider/model identities;
capability/preflight snapshot; approval/PB/Runtime-Enforcement references and
digests; sandbox/environment/network/resource profile references; timestamps and
state transitions; process/request/provider IDs; exit/transport status; bounded
output/result references and hashes; usage/cost; changed-file manifest; retry
lineage; and intake ID. The record is append-only state, contains no secret
values, and is not defined or schema-frozen by 3P.

## Audit/explainability

Audit must link prepared prompt -> approval -> explicit selection -> preflight ->
PB decision -> Runtime Enforcement decision -> dispatch attempt -> normalized
result -> intake disposition. Existing digest/evidence/audit idioms are reusable,
but there is no unified runtime audit consumer.

The operator must be able to answer: Why this runtime/provider/model? Why this
prompt? Who approved exactly what? Which policy permitted which effects? Which
capability and sandbox facts were observed? Did dispatch occur? What happened to
the process/request? What output was captured, transformed, ingested, rejected,
or promoted? Ambiguity must be shown, never rounded into success or failure.

## Human interaction model

Likely future UX, without defining commands:

```text
handoff state reached
  -> PCAE prepares immutable prompt and shows target candidates
  -> human inspects prompt, target, policy, budget, and sandbox summary
  -> human selects target and approves exact content/attempt bounds
  -> PCAE displays capability/preflight, PB, and enforcement outcome
  -> human performs an explicit dispatch action
  -> PCAE shows live/terminal invocation record
  -> human separately submits/reviews the normalized change candidate
```

Policy-defined bounded automation may be considered only in a later authority
contract. It is not implicit in this architecture.

## Prompt-dispatch use case

Current:

```text
session bootstrap --compact
  -> ContextPack
  -> build_bootstrap_prompt
  -> stdout text
  -> human copy/paste + external target selection
  -> external agent (outside PCAE)
```

Target:

```text
session bootstrap / governed handoff
  -> immutable prompt artifact + task/repo binding
  -> explicit content approval + target selection
  -> capability/config/auth preflight
  -> PB dispatch/network permission
  -> Runtime Enforcement final gate
  -> trusted invocation record + external bridge
  -> runtime/provider acceptance and execution states
  -> quarantined normalized result
  -> generic producer-neutral intake
  -> existing review/promotion
```

Missing pieces are artifact persistence, approval binding, target resolution,
live capability/auth, permission consumer, positive-but-still-disabled
enforcement contract, atomic dispatch, supervision/confinement, normalized
result, invocation record, and automatic generic-intake linkage.

## Execution activation boundary

Architecture readiness is not execution activation. 3P changes no executable
surface, policy, authorization flag, registry entry, credential, network rule,
or runtime state. End state remains:

```text
State: Observed
Maximum Capability: observe
Execution Availability: unavailable
Execution activation: NO
```

The legacy execution surfaces are a reason to fail closed and reconcile, not a
reason to reinterpret the canonical state as executable.

## Phased implementation roadmap

1. **3Q — Runtime Surface Reconciliation and Runtime / Provider Adapter
   Contract Freeze.** Inventory every executable public path; freeze canonical
   ownership/fencing, identity terms, target/bridge interface, lifecycle and
   capability facts, invocation/result records, PB/enforcement/intake bindings,
   and failure/retry semantics. Architecture/contract only.
2. **Independent contract verification.** Re-derive coverage of every legacy
   path and prove the frozen contract neither activates nor bypasses execution.
3. **Trusted-kernel skeleton plus deterministic mock bridge.** Implement
   selection, bound prompt/approval test fixtures, records, gates, normalized
   result, and intake linkage with no subprocess/network/provider call.
4. **Independent mock end-to-end verification.** Exercise denial, ambiguity,
   duplicate/restart, malicious-output, and intake-rejection paths.
5. **One local-CLI bridge contract and non-executing capability probe.** Add
   platform-specific supervision/confinement requirements, still no prompt
   dispatch.
6. **Separately authorized real-runtime pilot.** Only after trust gaps and
   legacy-path reconciliation are independently closed; one explicit target,
   human approval, no automatic promotion.
7. **Independent controlled-execution verification and later activation
   decision.** Activation remains a separate human decision.

## First adapter recommendation

Use a deterministic mock/dry bridge first. It maximizes validation of the new
architecture—selection, prompt and authority bindings, invocation state,
denials, result normalization, retry/idempotency, audit, and generic intake—at
minimal trust risk and with no provider, network, credential, process, or cost
effect. Do not start with Codex or Claude while execution authority remains
fragmented.

## Mock/dry adapter

Value: **very high** for governance/control-plane end-to-end validation;
**zero** as evidence of provider authentication, network control, process
containment, or real CLI behavior. It should return deterministic success,
failure, partial, malformed, delayed/canceled, and replay scenarios and be
incapable of spawning a process or opening a network connection. Existing mock
backend concepts may be reused after the new contract is frozen, but their
current safety defaults do not themselves prove the target architecture.

## Mac/Linux portability

The contract should be platform-neutral; bridges and confinement providers are
platform-specific. Every target must declare supported OS/architecture,
executable discovery/version/flag expectations, path/cwd behavior, signal and
process-group support, and sandbox/network enforcement capability. A passing
macOS development probe cannot imply Ubuntu readiness. Dell remains the Linux
deployment target but was not contacted or mutated in 3P.

## Distribution/discovery

Begin with a built-in deterministic mock. Later adapters may be discovered from
explicit configuration and pinned packages/entry points, but there must be no
ambient auto-discovery or auto-enable. A third-party package should register
declarative metadata through a controlled entry point while its transport runs
as a constrained external executable/service rather than imported arbitrary
code in the trusted kernel by default. Record package/version/digest. Installed
does not mean configured, authenticated, healthy, available, capable, permitted,
or authorized.

## Threat model

The primary threat is not merely a malicious model. It is authority confusion:
a descriptive identity, registry entry, human approval, policy ALLOW, process
exit zero, or accepted intake item being mistaken for permission or acceptance
at another boundary. Legacy executable paths that bypass the canonical runtime
make this threat concrete. Secondary threats are hostile prompt/context,
provider output, filesystem/process/network escape, inherited credentials,
tampering/replay, and unbounded cost.

## Trust-gap matrix

| Threat/Concern | Existing PCAE control | Missing control | Required before real execution? |
|---|---|---|---|
| Prompt injection | Deterministic context/prompt construction; task scope; human currently sees text | Trust labeling, immutable prompt artifact, content approval, least-privilege target context | Yes |
| Malicious provider output | Generic intake validates paths, hashes, repo/task binding; promotion separate | Quarantine and authenticated invocation-to-result binding | Yes |
| Filesystem mutation | Task paths, clean-tree checks, worktree prototype, post-hoc diff | OS confinement and pre-effect write controls across every path | Yes |
| Shell escape | Fixed argv in some paths; Shell Gate classifier | Common argv policy/process confinement; enforcing gate for shell-capable custom adapters | Yes for local CLI |
| Network exfiltration | Classification only | Enforced egress/endpoint policy and explicit network permission | Yes for networked targets |
| Secrets exposure | Redaction heuristics; env-key metadata | Secret references, allowlisted injection, account binding, rotation/revocation | Yes |
| Detached processes | Timeout on parent in some paths | Process-group/tree ownership and cleanup | Yes for local CLI |
| Result tampering | Hash/digest and intake evidence patterns | Durable invocation-result binding and protected append-only transitions | Yes |
| Identity spoofing | Agent-lock consistency | Authenticated runtime/provider/model/principal identities | Yes |
| Replay/duplicate | Intake idempotency; limited legacy anti-reexecution | Canonical invocation key, attempt lineage, ambiguous-dispatch recovery | Yes |
| Cost abuse | Some timeouts/output caps | Token/money/concurrency/retry budgets and measured usage | Yes for metered targets |
| Provider authentication | Env-key presence metadata | Credential broker/reference and authenticated account/endpoint proof | Yes |
| Capability spoofing | Validated inert descriptors | Live target-owned probe bound to dispatch | Yes |
| Authority bypass | PB/enforcement contracts exist | Universal consumer; reconcile/fence every legacy invocation path | **Yes; critical** |

## Existing-component reuse matrix

| Future need | Existing PCAE capability | Reusable? | Gap |
|---|---|---|---|
| Prompt generation | `build_bootstrap_prompt` + ContextPack | Yes | Persist/hash and bind approval/target |
| Task/repo context | Task contract, session snapshot, repo fingerprint/base commit | Yes | Bind same snapshot atomically to dispatch |
| Agent identity | Registry and core lock | Partially | Descriptive only; separate target/provider/principal |
| Permission Broker | Backend/adapter action vocabulary, reason chains | Partially | Request fields, positive contract, universal dispatcher consumer |
| Runtime Enforcement | Attempt/evidence/decision/coordinator design | Partially | Currently negative-only, dormant, no production consumer |
| Runtime Registry | Plugin/capability/lifecycle metadata | Partially | Persistence, target schema, live facts, resolver; must stay non-authorizing |
| Backend preflight | Prompt/task/scope checks | Partially | Name mismatch, no live capability/auth/config or dispatch semantics |
| Generic intake | Producer-neutral candidate and validation | Yes | Normalized result-to-candidate link |
| Audit | Digest/evidence/provenance idioms | Yes | One invocation ledger connecting every boundary |
| Human governance | Current copy/paste; approval artifacts elsewhere | Partially | Explicit prompt/target approval for bootstrap handoff |
| Session state | Session snapshot and core lock | Partially | Durable invocation lifecycle and authenticated principal |

## Missing-edge matrix

| Edge | Current state | Missing abstraction | Contract needed? | Authority risk |
|---|---|---|---|---|
| Prompt -> runtime | Human copy/paste | Bound target selection + dispatch boundary | Yes | Critical |
| Runtime -> result | Bespoke stdout/files | Normalized result envelope | Yes | High |
| Result -> intake | Manual/provider-specific handling | Generic result-to-candidate conversion | Yes | High |
| Agent identity -> runtime selection | Labels/hints and inconsistent maps | Explicit advisory mapping + selected target ID | Yes | High |
| Permission -> dispatch | PB vocabulary, no canonical consumer | Bound PB request/decision consumed atomically | Yes | Critical |
| Runtime capability -> execution attempt | Caller-supplied metadata/static preflight | Live capability/config/auth snapshot | Yes | High |
| Runtime availability -> legacy CLI paths | No relationship | Canonical ownership/fencing of all real surfaces | **Yes, first** | **Critical** |
| Dispatch -> supervision | Bespoke blocking subprocess | Process/request supervisor | Yes | Critical |
| Provider -> credentials/network | Inherited/external | Secret and egress policies | Yes | Critical |
| Invocation -> audit/retry | Path-specific artifacts | Canonical invocation/attempt record | Yes | High |

## Semantic-state matrix

| State | Meaning | Authority? | Persisted? | Existing/New |
|---|---|---|---|---|
| PREPARED | Exact prompt and bindings materialized | No | Not for bootstrap today; must be | Existing generation, new bound state |
| APPROVED | Human accepts exact content, target, scope, and attempt bounds | Human authority only | Not for bootstrap today; must be | Implicit today; explicit state new |
| DISPATCH-PERMITTED | Policy permits stated external effects | System permission, not capability | PB artifacts exist only as unavailable/simulation for this use | Contract evolution |
| RUNTIME-CAPABLE | Target is configured/authenticated/healthy and supports request | No authority | No live canonical state today | New fact state |
| DISPATCHED | One external effect was initiated | Records effect; grants none | Legacy path-specific only | New canonical state |
| ACCEPTED-BY-RUNTIME | Provider/process acknowledged the job | No governance acceptance | No canonical state | New |
| EXECUTING/RUNNING | Process/request is in progress | No | No canonical state | New |
| COMPLETED | Technical terminal outcome captured | No intake/promotion acceptance | Legacy ERR/path artifacts only | New canonical state |
| RESULT-INGESTED | Result/change candidate passed generic intake validation | Evidence acceptance only | Yes, current intake | Existing path, new linkage |

## Runtime class comparison

| Criterion | Local CLI | API Provider | Mock/Dry Adapter |
|---|---|---|---|
| Complexity | High | High | Low |
| Trust risk | High: OS process, filesystem, inherited env, indirect network | High: secrets, network, remote processing, cost | Low if structurally unable to spawn/connect |
| Portability | Medium/low; binaries and sandbox differ | Medium/high; protocol portable, auth/policy vary | High |
| Supervision | Process group/tree, signals, stdout/stderr | Request/session, streaming, cancellation | Deterministic in-process state |
| Secrets | CLI login/inherited env | API/OAuth token | None |
| Network | Often implicit | Explicit | None |
| E2E value | High for real local behavior | High for provider behavior | Very high for control-plane semantics; none for real containment |
| First-adapter suitability | No, until reconciliation/confinement | No, until secrets/network/cost contracts | **Yes** |

## Architecture Option A

**Runtime plugin adapters inside the existing PCAE plugin model.** Extend
`PluginDescriptor`/`RuntimeRegistry` into a loader/resolver/executor and place
CLI/API implementations inside it.

- Reuse: highest superficial reuse of plugin taxonomy and lifecycle names.
- Effort: medium-to-high because persistence, loading, live health, resolution,
  authority, and execution are all absent.
- Trust: poor; arbitrary plugin code would enter the trusted process and an
  inert registry would gain selection/execution authority.
- Extensibility: high mechanically, but unsafe without a new isolation model.
- Sequence: evolve registry -> loader -> authority integration -> adapters.
- Finding: **not recommended**; it conflates metadata discovery with trusted
  execution and leaves legacy surfaces unreconciled.

## Architecture Option B

**Runtime-neutral outer adapter/service layer.** Create a standalone dispatcher
outside the current Runtime Registry; PCAE calls it after governance and it owns
provider/runtime integration.

- Reuse: ContextPack, PB/enforcement vocabulary, and intake can be reused.
- Effort: medium-to-high.
- Trust: medium; a separate process can isolate transports, but risks becoming a
  second control plane with duplicate selection/permission/state.
- Extensibility: high through a service protocol.
- Sequence: service contract -> service implementation -> PCAE client -> target
  adapters.
- Finding: viable only if the service is strictly subordinate. As a fully outer
  layer it duplicates existing registries and execution prototypes.

## Architecture Option C

**Hybrid trusted PCAE kernel plus replaceable external runtime bridges.** Keep
governance, selection, final gating, invocation identity, audit, quarantine, and
intake binding in a small PCAE kernel. Keep transport/provider mechanics behind
constrained bridge processes/services. Use Runtime Registry evolution for
declarative discovery, not invocation authority.

- Reuse: strongest semantic reuse of prompt generation, task/repo binding, PB,
  enforcement evidence, registry metadata, audit patterns, and generic intake.
- Effort: highest initial reconciliation/contract effort, then bounded adapter
  implementations.
- Trust: best separation; bridges cannot approve themselves or promote output.
- Extensibility: high; CLI/API/custom transports share one narrow protocol.
- Sequence: reconcile surfaces and freeze contract -> verify -> mock bridge ->
  verify -> one non-executing real bridge -> separately authorize pilot.
- Finding: **recommended**.

## Recommended architecture

Choose Option C: a hybrid trusted PCAE kernel with replaceable external runtime
bridges. The thesis that PCAE should remain the governance/control plane holds,
but current source adds a crucial condition: PCAE must first make that control
plane authoritative over every executable public path. The registry remains a
metadata/discovery service; Permission Broker remains the policy decision point;
Runtime Enforcement becomes the final bound-evidence verifier only after a
contract amendment; bridges perform transport only; untrusted results return
through generic intake.

The architecture is blocked from real execution by fragmented legacy invocation
authority, lack of supervision/confinement/network/secrets controls, and absence
of a canonical invocation/result record. It is not blocked from contract work or
from a later deterministic mock implementation.

## Next-phase recommendation

Exact proposed next phase, subject to human decision:

```text
149O.20L.7O.3Q — Runtime Surface Reconciliation and Runtime / Provider
Adapter Contract Freeze
```

3Q must remain architecture/contract-only and non-executing. It should:

- inventory every public real or purported execution surface and decide which
  is retired, fenced, or routed through one canonical boundary;
- freeze identity terms and explicit agent-to-target mapping semantics;
- freeze target/bridge responsibilities, lifecycle/capability facts, selection,
  failure/retry/idempotency, invocation/result records, and portability;
- freeze PB, Runtime Enforcement, Shell Gate conditionality, audit, and generic
  intake bindings; and
- specify a deterministic mock/dry bridge as the first later implementation.

Do not begin 3Q automatically.

## Release implications

No release was prepared or published in 3P. `v0.4.3` remains current. The new
runtime/provider chapter is plausibly v0.5.0-scale, but no version is frozen.

## Method, checks, and scope controls

The reassessment used read-only source inspection (`rg`, `sed`, CLI help and
inspect/status commands) plus normal governance/status-file maintenance. It did
not use external documentation because the question was the architecture
implemented in this repository. No full Fast Green run was warranted: production
and test source are byte-unchanged. Baseline and final governance checks are
recorded in the canonical phase-completion report.

No `src/pcae/**`, test, contract, schema, version, or build-configuration file
was modified. No runtime/provider was invoked; no network was enabled; no
credential was accessed; Runtime Enforcement and Shell Gate remained dormant;
HATP/HMIC/Class-B and CLTR were unchanged; Dell was not contacted; the private
research repository was neither inspected nor used; the article remained
stopped.

## Human decision required

Human approval is required to accept or revise Option C and to begin 3Q. No
adapter, provider call, credential, network access, execution activation,
Runtime Enforcement activation, Shell Gate activation, HATP/Class-B change,
CLTR cutover, Dell mutation, private-research access, or article work was
performed. The article remains STOPPED.

## Phase verdict

```text
POST-CONSUMPTION RUNTIME / PROVIDER ARCHITECTURE:
COMPLETE

CURRENT RUNTIME:
Observed / observe / unavailable

PROMPT GENERATION:
PRODUCTION-CONSUMED

PROMPT DISPATCH:
NOT IMPLEMENTED IN THE CANONICAL RUNTIME
— RUNTIME / PROVIDER / TRUST-BOUNDARY GAP

LEGACY EXECUTION SURFACES:
PRESENT OUTSIDE THE CANONICAL RUNTIME — RECONCILIATION REQUIRED

GENERIC INTAKE:
REUSABLE RETURN PATH

RUNTIME REGISTRY:
IN-MEMORY METADATA ONLY; 0 PLUGINS; 0 CAPABILITIES; NO EXECUTABLE TARGET

RECOMMENDED ARCHITECTURE:
HYBRID TRUSTED PCAE KERNEL + REPLACEABLE EXTERNAL RUNTIME BRIDGES

FIRST ADAPTER:
DETERMINISTIC MOCK/DRY BRIDGE

EXECUTION ACTIVATION:
NOT PERFORMED

NEXT PHASE:
149O.20L.7O.3Q — RUNTIME SURFACE RECONCILIATION AND RUNTIME / PROVIDER
ADAPTER CONTRACT FREEZE

HUMAN DECISION:
REQUIRED
```
