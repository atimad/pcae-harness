# Runtime / Provider Adapter Contract

## Contract identity and status

**Contract:** RPAC-001  
**Version:** 1.0  
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3Q — Runtime Surface Reconciliation and
Runtime / Provider Adapter Contract Freeze

RPAC-001 v1.0 defines the future, provider-neutral boundary between PCAE's
governed control plane and replaceable runtime adapters. It is specification
only. It does not add an adapter, loader, subprocess, network call, credential,
positive permission decision, Runtime Enforcement consumer, or execution
availability.

The current runtime posture is unchanged:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**
- Runtime registry: **0 plugins / 0 capabilities**

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, and **MAY**
are normative. Requirement identifiers are stable, never reused, and have the
form `RPAC-REQ-###`. This document is the public contract; implementations
MUST NOT depend on undocumented Python internals.

## 1. Scope and architecture

RPAC-REQ-001: PCAE SHALL remain the authority-owning control plane. A future
adapter SHALL be a replaceable transport and result-normalization component,
not a governance authority.

RPAC-REQ-002: The canonical future flow SHALL be:

```text
authoritative task/session
  -> governed PromptArtifact and InvocationRequest
  -> human invocation approval
  -> explicit RuntimeTarget resolution and capability/status preflight
  -> Permission Broker dispatch/effect permission
  -> final Runtime Enforcement decision
  -> durable attempt record
  -> selected adapter transport
  -> normalized RuntimeInvocationResult
  -> producer-neutral intake
  -> review/governance/promotion
```

RPAC-REQ-003: The adapter SHALL NOT own human authority, Permission Broker
policy, Runtime Enforcement policy, repository/task authority, intake
acceptance, review, promotion, commit, push, or the final task outcome.

RPAC-REQ-004: RPAC-001 SHALL support deterministic mock/dry adapters, local
CLI adapters, API/provider adapters, and constrained third-party adapters
without provider-specific fields in the common intake boundary.

RPAC-REQ-005: Contract conformance alone SHALL NOT authorize implementation or
execution. Every implementation and every activation requires a separately
governed phase.

## 2. Identity model

RPAC-REQ-006: The following identities SHALL remain distinct:

| Identity | Meaning | Authority semantics |
|---|---|---|
| `AgentIdentity` | PCAE session/collaboration label such as `codex-local` | Descriptive; never selects or authorizes a runtime |
| `ProducerIdentity` | Claimed/derived origin of returned material | Provenance only; untrusted until intake |
| `AdapterIdentity` | Installed adapter implementation and version | Transport implementation identity; no authority |
| `RuntimeTargetIdentity` | Explicit configured target selected for one invocation | Binding target reference; no authority by itself |
| `ProviderIdentity` | Optional external service/account/endpoint domain | Descriptive/configuration identity; no authority |
| `ModelIdentity` | Optional concrete or provider-defined model | Descriptive/configuration identity; no authority |
| `ExecutionPrincipal` | Local OS/service/credential principal used at effect time | Audited effect principal; cannot supply human authority |
| `InvocationIdentity` | Logical invocation plus uniquely identified attempts | Idempotency/audit identity; no authority |

RPAC-REQ-007: `agent_id != runtime_target_id`, `agent_id != provider_id`,
`agent_id != model_id`, and `producer provenance != runtime identity` SHALL be
preserved in every request, record, result, CLI, and report.

RPAC-REQ-008: `codex-ox` SHALL remain an `AgentIdentity` and possible producer
claim only. It SHALL NOT imply OpenRouter, Codex CLI, a model, a configured
target, authentication, capability, permission, authorization, or execution.

RPAC-REQ-009: A convenience mapping from an agent identity to a suggested
target MAY exist in future configuration, but it SHALL be non-authoritative,
visible, and resolved to an explicit target before approval. It SHALL NOT be a
silent fallback.

RPAC-REQ-010: Provider and model identities SHALL be optional because some
local tools abstract them. When PCAE does not select or observe one, the value
SHALL be absent or explicitly `unspecified`; it SHALL NOT be inferred from an
agent, adapter, executable, or marketing name.

## 3. Runtime descriptor, target configuration, and live status

RPAC-REQ-011: A `RuntimeDescriptor` SHALL contain immutable descriptive facts:

- `contract_version`, `adapter_id`, adapter implementation version/digest;
- adapter class (`mock_dry`, `local_cli`, `api_provider`, or
  `external_bridge`) and transport kind;
- declared supported capabilities and result formats;
- execution effect (`none`, `local_process`, or `remote_request`);
- locality, network requirement, supported platforms;
- cancellation mode (`supported`, `cooperative`, or `unsupported`); and
- test/simulation namespace flag.

RPAC-REQ-012: A descriptor SHALL NOT contain live availability, current
health, credential values, permission, approval, authorization, or task state.

RPAC-REQ-013: A `RuntimeTargetConfiguration` SHALL minimally contain:

- immutable `runtime_target_id`, config version/digest, and `adapter_id`;
- adapter-class-specific command descriptor or endpoint reference;
- optional `provider_id`, optional `model_id`, and optional opaque
  `credential_ref`;
- environment, working-directory, filesystem, network, sandbox, and process
  supervision profile references; and
- capability constraints and target enablement state.

RPAC-REQ-014: Configuration SHALL contain references, not credential values.
Environment-variable names alone are not a credential-reference abstraction.

RPAC-REQ-015: `RuntimeStatus` SHALL contain dynamic, timestamped facts:
registration, implementation installation, configuration, authentication (or
`not_required`), availability, health (including `unknown`), observed
capabilities, status source, and observation time.

RPAC-REQ-016: Runtime status SHALL NOT contain or imply human approval,
Permission Broker permission, Runtime Enforcement authorization, or actual
dispatch.

## 4. Capability semantics

RPAC-REQ-017: These terms SHALL be independently represented:

| Term | Frozen meaning |
|---|---|
| registered | A descriptor has been admitted to the canonical catalog |
| installed | The pinned adapter implementation is present and verifiable |
| configured | A complete target configuration exists |
| authenticated | Required credentials/account access were verified, or authentication is explicitly `not_required` |
| available | The target is launchable/reachable now under its status probe |
| capable | The target supports the exact requested operation and effect profiles |
| permitted | Permission Broker returned the required scoped `ALLOW` decision(s) |
| authorized | Runtime Enforcement made the final positive pre-dispatch decision from all bound evidence |
| executed | The effect boundary was actually crossed |

RPAC-REQ-018: No state in RPAC-REQ-017 SHALL imply any later state. In
particular, permission is not capability; capability is not authorization;
authorization is not execution.

RPAC-REQ-019: Capability matching SHALL include the requested result format,
network/filesystem/process effects, cancellation requirements, and platform,
not only a vocabulary string such as `execute`.

## 5. PromptArtifact and invocation approval

RPAC-REQ-020: Future machine dispatch SHALL use a lightweight, immutable
`PromptArtifact`; the current untyped bootstrap string alone is insufficient
for target-bound replay and audit.

RPAC-REQ-021: `PromptArtifact` SHALL contain: artifact/schema version,
artifact ID, prompt content or content reference, SHA-256 content digest,
generation method/version, repository/task/phase binding, creation timestamp,
provenance/derivation references, and whether human edits changed the
generated content. A target-agent hint MAY be carried but SHALL be
non-binding.

RPAC-REQ-022: Approval SHALL NOT be embedded as mutable state in the prompt.
A human `InvocationApproval` SHALL bind the exact prompt digest, repository and
task, selected runtime target/config digest, requested effect profiles,
resource budget, expiry, and authorized attempt limit.

RPAC-REQ-023: One invocation approval MAY encompass approval of the prompt;
RPAC-001 does not require a second standalone PromptApproval artifact.
Changing prompt content, target, repository/task binding, or effects SHALL
invalidate the invocation approval.

RPAC-REQ-024: Human copy/paste remains an implicit manual authority boundary
today but is not machine-verifiable dispatch approval. Automated dispatch
SHALL require the explicit binding in RPAC-REQ-022.

## 6. Governed InvocationRequest

RPAC-REQ-025: A canonical `InvocationRequest` SHALL contain:

- `contract_version`, logical `invocation_id`, unique `attempt_id`, and
  `idempotency_key`;
- repository fingerprint/root identity, base commit, active `task_id`, and
  phase/session identity when applicable;
- requester `AgentIdentity` as descriptive provenance;
- explicit `runtime_target_id`, expected `adapter_id`, descriptor digest, and
  target-config digest;
- optional expected provider/model identity snapshot;
- PromptArtifact reference and digest;
- InvocationApproval reference and digest;
- requested capabilities and expected terminal result format;
- repository-bound working-directory policy;
- environment, filesystem, network, sandbox, and process-effect profiles;
- a finite timeout and required cancellation behavior; and
- optional structured token/cost limits under `resource_budget`.

RPAC-REQ-026: The trusted PCAE kernel SHALL construct and validate the request.
An adapter or runtime response SHALL NOT choose or rewrite repository, task,
target, prompt, authority, effect scope, timeout, or budget fields.

RPAC-REQ-027: `network_allowed` SHALL default to false. Filesystem write and
outside-repository access SHALL default to none. Absence of a budget for a
metered target SHALL mean no paid use is authorized, not unlimited spend.

RPAC-REQ-028: Provider/model values resolved from target configuration SHALL be
snapshotted in the request when known. A mismatch at dispatch SHALL fail
closed; an adapter SHALL NOT silently switch provider, model, endpoint, or
target.

## 7. DispatchEnvelope and adapter interface

RPAC-REQ-029: Only the trusted kernel SHALL mint a `DispatchEnvelope` after all
gates pass. It SHALL contain the immutable InvocationRequest, fresh target
status digest, approval digest, Permission Broker decision digest(s), Runtime
Enforcement decision digest, durable record reference, and expiration.

RPAC-REQ-030: An adapter SHALL reject a missing, expired, unsupported-version,
or digest-inconsistent envelope. This syntactic check SHALL NOT turn the
adapter into an authority owner.

RPAC-REQ-031: The conceptual v1 adapter interface SHALL provide exactly these
operations:

```text
describe() -> RuntimeDescriptor
preflight(InvocationRequest) -> AdapterPreflightResult
dispatch(DispatchEnvelope) -> DispatchReceipt
collect(attempt_id) -> RuntimeInvocationResult | PendingObservation
cancel(attempt_id) -> RuntimeCancellationResult
```

RPAC-REQ-032: `describe` SHALL be side-effect-free. `preflight` SHALL collect
facts only and SHALL NOT dispatch. `dispatch` SHALL cross at most the effect
boundary authorized by the envelope. `collect` SHALL normalize status/output
without accepting changes. `cancel` SHALL report supported, cooperative,
unsupported, completed, or unknown outcomes.

RPAC-REQ-033: RPAC-001 v1.0 freezes terminal result collection, not a streaming
event schema. An adapter MAY buffer provider streaming internally, but PCAE
SHALL NOT rely on provider-specific stream events under v1.0.

RPAC-REQ-034: The trusted kernel, not the adapter, SHALL own record persistence,
gate ordering, retry authority, and intake submission. Process/API mechanics,
capture, cancellation, timeout enforcement, and normalized transport results
belong to the adapter under kernel-supplied constraints.

## 8. RuntimeInvocationResult

RPAC-REQ-035: `RuntimeInvocationResult` SHALL contain:

- contract version, invocation/attempt/idempotency identities;
- exact runtime target, adapter, descriptor, and config identities/digests;
- declared and observed provider/model identities when available;
- adapter acceptance, dispatch, start, completion, and capture observations;
- accepted/started/completed/captured timestamps;
- terminal outcome and transport/process/provider status;
- bounded stdout/stderr/content or immutable references plus digests;
- optional structured response reference/digest;
- changed-file manifest and optional patch/diff references/digests;
- usage/token/cost observations when available;
- runtime/adapter/execution-principal provenance;
- observed filesystem/network/sandbox/process facts;
- normalized error category, retryability hint, ambiguity flag, and sanitized
  diagnostic details; and
- optional intake candidate/intake record references added by PCAE, never by
  the external runtime.

RPAC-REQ-036: Adapter acceptance, completion, a zero exit status, provider
success, or a well-formed result SHALL NOT mean PCAE accepted the output,
accepted a change, promoted a change, or completed the task.

RPAC-REQ-037: Output SHALL be treated as untrusted. Secret-bearing output SHALL
be redacted/quarantined before ordinary display or audit persistence.

RPAC-REQ-038: Provider-specific response data MAY be preserved as an opaque,
bounded attachment, but common consumers SHALL rely only on normalized RPAC
fields.

## 9. Semantic state model

RPAC-REQ-039: The conceptual lifecycle SHALL preserve these distinct states:

| State | Owner | Meaning |
|---|---|---|
| `PREPARED` | PCAE governance | Prompt/request is immutable and repository/task bound |
| `APPROVED` | Human authority | Exact invocation scope was approved |
| `CAPABLE` | Runtime status/preflight | Selected target can satisfy the request now |
| `PERMITTED` | Permission Broker | Required policy decision(s) are `ALLOW` |
| `AUTHORIZED` | Runtime Enforcement | Final pre-dispatch conjunction is positive |
| `DISPATCHED` | PCAE/adapter observation | Effect boundary may have been crossed |
| `ACCEPTED` | Adapter/runtime observation | Target acknowledged the attempt |
| `RUNNING` | Adapter/runtime observation | Target reports work in progress |
| `COMPLETED` | Adapter/runtime observation | Target reached a terminal technical state |
| `RESULT_CAPTURED` | PCAE/adapter observation | A normalized terminal result was durably captured |
| `INGESTED` | Generic intake | Result changes were submitted and accepted as evidence |

RPAC-REQ-040: State transitions SHALL be append-only observations. They SHALL
NOT be collapsed into one success flag. Skipped runtime observations SHALL be
represented explicitly when a transport cannot observe them.

RPAC-REQ-041: A mock/dry adapter SHALL use a simulation namespace and
`simulation_only=true`. Its simulated dispatch/completion SHALL NOT populate
real `DISPATCHED`/`COMPLETED` state or alter production execution availability.

## 10. Gate ordering and governance integrations

RPAC-REQ-042: The normative future gate order SHALL be:

1. resolve authoritative repository/task/session and create PromptArtifact;
2. construct immutable request and explicit target selection;
3. obtain human InvocationApproval;
4. resolve descriptor/config and perform fact-only status/capability preflight;
5. obtain Permission Broker permission for adapter dispatch and each requested
   effect class;
6. revalidate mutable status/config/HEAD facts for freshness;
7. obtain the final Runtime Enforcement decision immediately before dispatch;
8. durably create the attempt record and atomically mark dispatch intent;
9. call the one selected adapter;
10. capture result and submit any proposed changes through generic intake.

RPAC-REQ-043: A failure or stale fact at any pre-dispatch step SHALL fail
closed and SHALL NOT call the adapter.

RPAC-REQ-044: The existing Permission Broker action/execution-class vocabulary
(`adapter_invocation`/`backend_invocation`; `adapter`/`backend`) is a useful
starting point but insufficient for RPAC dispatch because its request does not
bind target, adapter, prompt digest, repository, effects, network/filesystem,
credentials, budget, or idempotency. That contract gap SHALL be closed in a
separate future phase without changing policy in 3Q.

RPAC-REQ-045: Runtime Enforcement SHALL be the final whether-to-invoke gate,
after human approval, target facts, and Permission Broker permission, and
before any adapter effect. The current evidence-only, non-authorizing,
zero-consumer implementation SHALL NOT be treated as that future gate.

RPAC-REQ-046: Runtime Enforcement SHALL evaluate the complete bound request,
all effect-specific permission decisions, target/status freshness,
repository/task/HEAD freshness, approval validity, and no-go evidence. A
positive decision SHALL expire and SHALL be single-attempt scoped.

RPAC-REQ-047: Runtime Enforcement determines **whether** invocation may happen.
Shell Gate or an equivalent local process policy constrains **how** a local
command is constructed/launched. Neither substitutes for the other.

RPAC-REQ-048: For a local CLI adapter, fixed argv SHALL receive adapter-specific
validation plus enforcing process policy. Any shell text, expansion, pipeline,
or `shell=True` form SHALL require an enforcing Shell Gate/equivalent; because
today's Shell Gate is simulation-only and non-intercepting, such real dispatch
is forbidden now.

RPAC-REQ-049: HATP is not a generic adapter-contract prerequisite. A later
policy MAY require hardware-backed human authority for a particular effect,
but existing HATP artifacts SHALL NOT be reinterpreted as generic invocation
permission.

## 11. Registry, discovery, selection, and inspect

RPAC-REQ-050: PCAE SHALL have one canonical runtime catalog. The existing
`RuntimeRegistry` remains the metadata/introspection foundation and valid empty
state; future callable resolution SHALL be a trusted-kernel extension composed
with it, not a competing authoritative backend/adapter registry.

RPAC-REQ-051: The existing Plugin Model is metadata/introspection-only and
SHALL NOT be silently overloaded as a loader. Callable implementation
resolution, lifecycle, isolation, and pinning require explicit future
contracted code.

RPAC-REQ-052: Adapter IDs SHALL be unique in the canonical catalog. Duplicate
IDs, ambiguous descriptors, digest drift, or unsupported contract major
versions SHALL fail closed.

RPAC-REQ-053: Selection SHALL require one explicit `runtime_target_id` and
matching descriptor/config digest. There SHALL be no priority fallback,
provider fallback, model fallback, environment-dependent fallback, or
agent-name fallback.

RPAC-REQ-054: Initial discovery SHALL allow trusted built-ins and explicit
pinned configuration. Future Python entry points or external executable
descriptors MAY be supported only through a separately governed admission
mechanism; ambient import-path scanning SHALL NOT auto-enable adapters.

RPAC-REQ-055: An empty registry SHALL remain valid and SHALL report execution
unavailable. A future mock/dry registration SHALL declare `execution_effect =
none`, `simulation_only = true`, and a simulation capability, never the real
`execute` capability; it SHALL NOT change canonical execution availability.

RPAC-REQ-056: A future `pcae runtime inspect` MAY add registered adapters,
descriptors, configured targets, and timestamped status. Static registration
and dynamic status SHALL be displayed separately, and the existing 0/0/
unavailable output SHALL remain backward compatible until an actual governed
runtime is registered and activated.

## 12. Transport-specific profiles

RPAC-REQ-057: A local CLI target SHALL define a resolved/pinned executable,
fixed argv construction without shell interpolation, repository-bound cwd,
sanitized allowlisted environment, prompt transfer method, output limits,
finite timeout, process-group/tree ownership, termination escalation,
cancellation behavior, exit-status mapping, platform profile, filesystem and
network confinement, and result normalization.

RPAC-REQ-058: A local adapter SHALL NOT inherit the full PCAE process
environment. Credential values SHALL be resolved just in time by a future
secret resolver, exposed only to the narrow child context, omitted from
records, and redacted from captured output.

RPAC-REQ-059: An API/provider target SHALL define provider/endpoint identity,
TLS/egress policy, opaque credential reference, request/response schema,
finite connection and total timeouts, rate-limit handling, cancellation,
ambiguous-delivery handling, output limits, usage/cost collection, and result
normalization.

RPAC-REQ-060: API streaming is optional transport behavior. Under v1.0 it
SHALL be reduced to status observations and one normalized terminal result.

RPAC-REQ-061: Filesystem scope SHALL separately represent repository read,
repository write, controlled temporary write, and outside-repository access.
Outside-repository access SHALL default to denied. A mock/dry adapter SHALL
require no broad filesystem access and SHALL not mutate the repository.

RPAC-REQ-062: Working directory SHALL be selected by PCAE as the canonical
repository/worktree root or a normalized allowlisted descendant. The adapter
or runtime output SHALL NOT supply cwd. Symlink/realpath escape SHALL fail
closed.

RPAC-REQ-063: Core fields SHALL be platform-neutral. OS-specific executable,
signal, process-tree, and sandbox behavior SHALL live in declared adapter
platform profiles supporting at least macOS development and Linux deployment.

## 13. Invocation identity, record, idempotency, and retry

RPAC-REQ-064: PCAE SHALL create an opaque, stable logical `invocation_id` from
cryptographically strong random identity before approval. It SHALL NOT derive
identity from a mutable timestamp alone. Each dispatch try SHALL have a unique
`attempt_id` linked to the logical invocation.

RPAC-REQ-065: The `idempotency_key` SHALL be a SHA-256 digest of canonical,
versioned request content excluding timestamps and attempt-specific mutable
observations, including repository/task/base, prompt digest, target/config,
effects, approval scope, and budget.

RPAC-REQ-066: The same invocation ID and identical canonical content SHALL
return/resume the existing record without redispatch. The same invocation ID
with different content SHALL be a hard collision and fail closed.

RPAC-REQ-067: Before any real adapter exists, PCAE SHALL implement a persistent,
append-only `RuntimeInvocationRecord`. Its conceptual minimum fields are:
record/schema version, invocation and attempt IDs, idempotency key, request and
artifact digests/references, repository/task/phase binding, target/descriptor/
config snapshot, identity snapshots, approvals and gate decisions with
digests/times, state-transition log, dispatch receipt, result digest/reference,
intake references, failure/ambiguity, retry lineage, audit times, and record
integrity digest.

RPAC-REQ-068: Restart before dispatch SHALL resume validation without dispatch.
Restart after a dispatch-intent/receipt boundary with unknown outcome SHALL
record `ambiguous_outcome` and SHALL NOT automatically redispatch.

RPAC-REQ-069: Duplicate completion with the same result digest SHALL be an
idempotent replay. A conflicting completion for the same attempt SHALL be
quarantined as an integrity failure.

RPAC-REQ-070: Result-ingestion replay SHALL use a deterministic candidate
identity derived from invocation ID, attempt ID, and result digest so existing
generic intake collision/replay semantics remain effective.

RPAC-REQ-071: Retryable classes MAY include unavailability before dispatch,
rate limiting with confirmed non-acceptance, transient transport failure with
confirmed non-delivery, and timeout before the effect boundary. Unknown
delivery, runtime mutation, malformed conflicting completion, and ambiguous
process termination SHALL NOT retry automatically.

RPAC-REQ-072: Every retry requires a new attempt ID, fresh capability/status,
fresh Permission Broker and Runtime Enforcement decisions, and human
authorization when the prior approval's attempt limit/expiry does not cover
it. A changed prompt, target, provider/model, repository/task, effects, or
budget requires a new logical invocation and approval.

## 14. Failure taxonomy

RPAC-REQ-073: Every terminal failure SHALL use at least one of these stable
categories:

| Category | Meaning |
|---|---|
| `no_adapter_configured` | explicit target/adapter configuration missing |
| `unsupported_capability` | descriptor/status cannot satisfy the request |
| `unauthenticated` | required authentication absent or invalid |
| `unavailable` | selected target currently not launchable/reachable |
| `permission_denied` | Permission Broker did not return required `ALLOW` |
| `enforcement_denied` | Runtime Enforcement did not authorize dispatch |
| `dispatch_error` | adapter could not establish the effect boundary |
| `timeout` | finite deadline exceeded |
| `runtime_failure` | target accepted/ran but returned technical failure |
| `malformed_result` | normalized result is missing, invalid, or inconsistent |
| `result_ingestion_failure` | generic intake rejected or could not persist result changes |

RPAC-REQ-074: Implementations MAY add `canceled`, `rate_limited`,
`ambiguous_outcome`, `integrity_failure`, and transport-specific subcodes, but
shall map them to stable common semantics. Existing legacy categories SHALL be
mapped, not silently reused with incompatible meanings.

RPAC-REQ-075: Adapter-provided `retryable` is advice only. The trusted kernel
and human/policy authority own retry authorization.

## 15. Audit, provenance, and generic intake

RPAC-REQ-076: Audit evidence SHALL answer: who requested; which human approved;
which prompt/context/repository/task/base was bound; which target, adapter,
provider/model, principal, and config were used; what status/capability was
observed; what PB and Runtime Enforcement decided; whether/when dispatch was
attempted, accepted, completed, canceled, or became ambiguous; what was
captured; and what intake/review/promotion disposition followed.

RPAC-REQ-077: Audit SHALL reuse existing immutable digest, phase-report,
provenance, and generic-intake patterns where compatible. Legacy backend-
specific audit stores SHALL not become parallel authority sources.

RPAC-REQ-078: The kernel SHALL derive authoritative repository/task binding
from the current governed repository, active task contract, phase/session,
and HEAD. A runtime-returned repository/task claim is untrusted evidence only.

RPAC-REQ-079: `ProducerIdentity` SHALL record both the descriptive producer
claim and the observed chain: requesting agent, selected target, adapter,
provider/model if known, execution principal, and result digest. None is
permission. An agent-lock-derived producer remains descriptive, consistent
with current intake semantics.

RPAC-REQ-080: Proposed file changes SHALL enter the existing producer-neutral
intake contract. The kernel SHALL transform a normalized changed-file
manifest/content/patch into an intake candidate bound to the authoritative
task, repository fingerprint, and base commit. There SHALL be no Codex-,
Claude-, or provider-specific intake path.

RPAC-REQ-081: Text-only results MAY remain invocation result artifacts and need
not fabricate a file-change candidate. `INGESTED` applies only when a valid
intake submission exists.

## 16. Security invariants

RPAC-REQ-082: An adapter SHALL NOT self-authorize, change human approval,
change a Permission Broker decision, change a Runtime Enforcement decision,
choose repository/task authority, broaden cwd/environment/network/filesystem/
process scope, or exceed a budget.

RPAC-REQ-083: Runtime output is untrusted until normalized, integrity checked,
and, for changes, accepted by generic intake. Runtime completion is not an
accepted change; an accepted change is not promotion; runtime completion is
not successful PCAE task completion.

RPAC-REQ-084: Credentials SHALL never be embedded in descriptors, requests,
results, audit records, prompts, diffs, or repository configuration. PCAE has
no adequate general credential-reference/resolution implementation today;
that is an explicit blocker for a real authenticated adapter.

RPAC-REQ-085: Network, subprocess, shell, filesystem mutation, outside-repo
access, paid usage, and provider selection SHALL each be explicit and default
denied. One granted effect SHALL not imply another.

RPAC-REQ-086: Adapter code and descriptors are supply-chain inputs. Future
admission SHALL pin implementation identity/digest and fail closed on drift;
an adapter SHALL not mutate its own descriptor or status evidence during an
attempt.

RPAC-REQ-087: A durable pre-dispatch record and a one-attempt authority envelope
SHALL exist before the effect boundary, preventing an adapter from converting
an observation, stale decision, or duplicate call into execution.

## 17. Deterministic mock/dry conformance target

RPAC-REQ-088: The first implementation target SHALL be a built-in,
deterministic mock/dry adapter in an explicit test/simulation namespace.

RPAC-REQ-089: It SHALL exercise descriptor registration, explicit target
selection, request validation, PromptArtifact/approval binding, simulated gate
outcomes, semantic transition recording, dispatch-receipt/result
normalization, cancellation modes, failure taxonomy, idempotent replay, and
generic-intake linkage.

RPAC-REQ-090: It SHALL use fixed local fixtures, make no subprocess or network
call, use no provider/model/credential, perform no repository mutation, and
write only controlled PCAE test/artifact records expressly scoped by its
implementation phase.

RPAC-REQ-091: Because current Permission Broker and Runtime Enforcement cannot
authorize real execution, mock positive paths SHALL use explicitly labeled
simulation decisions or test doubles. They SHALL NOT mint production `ALLOW`,
`AUTHORIZED`, `DISPATCHED`, or `COMPLETED` claims and SHALL NOT make `pcae
runtime inspect` report real execution availability.

## 18. Compatibility and evolution

RPAC-REQ-092: RPAC-001 v1.0 preserves all current consumers that expect zero
runtime plugins, zero capabilities, and unavailable execution. Freezing the
contract changes no CLI or runtime behavior.

RPAC-REQ-093: Patch releases MAY clarify prose without changing semantics.
Minor releases MAY add optional fields, capabilities, status values, or
failure subcodes while preserving v1 behavior. New required fields, changed
gate order, weaker security invariants, changed authority ownership, or
changed identity equivalences require a new major version.

RPAC-REQ-094: Implementations SHALL declare the contract versions they support,
reject unknown major versions, preserve unknown optional fields when safely
round-tripping, and fail closed when a field affects authority or effects but
is not understood.

RPAC-REQ-095: The first post-mock process-bound implementation SHOULD be a
generic, fixed-argv external executable adapter tested with a deterministic
non-AI fixture. The first named AI target SHOULD then be an explicit Codex CLI
RuntimeTarget—not `codex-local`/`codex-ox` identity inference—after process
supervision, credential, PB, Runtime Enforcement, and Shell Gate dependencies
are independently satisfied. Claude-local and API providers follow the same
contract and receive no legacy-path exemption.

## 19. Explicit non-authorization

RPAC-REQ-096: This freeze SHALL NOT add or register a mock or real adapter,
invoke an external runtime, create a subprocess/network path, add credentials,
change Permission Broker policy, activate Runtime Enforcement or Shell Gate,
alter agent identities, change HATP/HMIC/Class-B/CLTR, or mutate another
machine.

RPAC-REQ-097: All existing public legacy invocation paths remain historical
execution surfaces, not RPAC-conformant adapters. Before any real activation,
they SHALL be retired, disabled, or routed through one RPAC-conformant kernel
and SHALL not be grandfathered as alternate dispatch authorities.

## Frozen verdict

**RUNTIME / PROVIDER ADAPTER CONTRACT: FROZEN — RPAC-001 v1.0.**  
**CURRENT EXECUTION: UNAVAILABLE.**  
**IMPLEMENTATION AUTHORITY: NOT GRANTED.**
